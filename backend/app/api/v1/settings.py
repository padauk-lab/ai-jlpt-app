"""Section 4: AI and settings. Contract endpoints #27 to #37 (docs/api-contract.md).
#35 (log out) is real and lives in auth.py.

REAL: #28 ("Why?"), #29, #30, #31, #32, #33, #36 and #37 (the Settings screen).
REAL: #34 (change password).
PLACEHOLDER: #27 ("More examples", waiting for SWYH's generate_examples()).

Security notes:
- Every real endpoint needs login and only changes the logged-in user's own data.
- Dangerous actions need a typed confirmation ("DELETE", "RESET"), and deleting an email account
  also needs the password.

Rules for the AI endpoints:
- The app sends only IDs. The backend looks up the content and passes it to SWYH's AI functions.
- "Why?" (#28) works only when the user has already seen the correct answer: a quiz question they
  answered or that was in a quiz they finished, or a question of a mock test they submitted. Otherwise 403.
- "Why?" answers are saved per question and choice and reused for everyone, so the AI is asked only once.
"""

import logging
import re
from datetime import UTC, datetime, time
from functools import cache
from typing import Annotated, Any, Literal
from zoneinfo import available_timezones

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, exists, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.api.v1.auth import Password, Username, issue_tokens, user_json
from app.api.v1.onboarding import OnboardingRequest
from app.core.errors import ApiError
from app.core.rate_limit import LOGIN_FAILS_PER_EMAIL, limiter
from app.core.security import hash_password, verify_password
from app.ai import explain as ai_explain
from app.ai.llm import AIUnavailableError
from app.models import (
    AIExplanation,
    Device,
    MockAttempt,
    NotificationSettings,
    Question,
    QuizAnswer,
    QuizAttempt,
    QuizAttemptQuestion,
    ReadingPassage,
    RefreshToken,
    StudySettings,
    User,
)
from app.plan import service

router = APIRouter(tags=["4. AI and settings"])
logger = logging.getLogger(__name__)

MAX_DEVICES_PER_USER = 10  # older phones are forgotten, so one account can't register thousands of tokens
DEFAULT_NOTIFICATIONS = {"daily_reminder": True, "reminder_time": "20:00", "proverb_notification": True, "timezone": "Asia/Tokyo"}


@cache
def _timezones() -> frozenset[str]:
    return frozenset(available_timezones())


# --- Request shapes (what the app sends) ---


class ExplainRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: Annotated[int, Field(strict=True, ge=1, le=9_223_372_036_854_775_807)]
    selected_option_id: Literal["a", "b", "c", "d"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")  # unknown fields are refused


class UpdateMeRequest(Strict):
    username: Username


class NotificationSettingsRequest(Strict):
    daily_reminder: bool
    reminder_time: Annotated[str, Field(pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$")]  # "HH:MM", e.g. "20:00"
    proverb_notification: bool
    timezone: Annotated[str, Field(max_length=64)]  # IANA name, e.g. "Asia/Tokyo"

    @field_validator("timezone")
    @classmethod
    def known_timezone(cls, value: str) -> str:
        # Compared with the official list, so odd values like "../etc" never reach the system.
        if value not in _timezones():
            raise ValueError("Unknown timezone. Use a name like Asia/Tokyo or Asia/Yangon.")
        return value


class DeviceRequest(Strict):
    push_token: Annotated[str, Field(min_length=1, max_length=300)]
    platform: Literal["ios", "android", "web"]


class ChangePasswordRequest(Strict):
    current_password: Annotated[str, Field(max_length=128)]
    new_password: Password  # same rules as sign up: 8 to 128 characters


class DeleteAccountRequest(Strict):
    confirm: Literal["DELETE"]
    password: Annotated[str, Field(max_length=128)] | None = None  # required for email users, not for Google users


class ResetProgressRequest(Strict):
    confirm: Literal["RESET"]


# --- Helpers ---


def _settings_or_404(db: DbSession, user: User) -> StudySettings:
    settings = db.get(StudySettings, user.id)
    if settings is None:
        raise ApiError(404, "onboarding_not_done", "Please finish the setup first.")
    return settings


def _notifications_json(row: NotificationSettings | None) -> dict[str, Any]:
    if row is None:
        return dict(DEFAULT_NOTIFICATIONS)
    return {
        "daily_reminder": row.daily_reminder,
        "reminder_time": row.reminder_time.strftime("%H:%M"),
        "proverb_notification": row.proverb_notification,
        "timezone": row.timezone,
    }


# --- Endpoints ---


def _has_seen_the_answer(db: DbSession, user: User, question: Question) -> bool:
    """True only if the app has already shown this user the correct answer to this question."""
    if question.quiz_id is not None:
        mine = (QuizAttempt.user_id == user.id,)
        answered = exists().where(
            QuizAnswer.attempt_id == QuizAttempt.id, QuizAnswer.question_id == question.id, *mine
        )
        in_finished_quiz = exists().where(  # the review (#22) shows every answer, skipped ones too
            QuizAttemptQuestion.attempt_id == QuizAttempt.id,
            QuizAttemptQuestion.question_id == question.id,
            QuizAttempt.finished_at.is_not(None),
            *mine,
        )
        return bool(db.scalar(select(answered | in_finished_quiz)))
    submitted_mock = exists().where(
        MockAttempt.user_id == user.id,
        MockAttempt.mock_test_id == question.mock_test_id,
        MockAttempt.submitted_at.is_not(None),
    )
    return bool(db.scalar(select(submitted_mock)))


def _passage_text(db: DbSession, question: Question) -> str | None:
    """Reading questions need their passage, or the AI can't explain them."""
    if question.passage_id is None:
        return None
    passage = db.get(ReadingPassage, question.passage_id)
    return "".join(piece["text"] for piece in passage.text_ruby) if passage else None


def _saved_explanation(db: DbSession, question_id: int, selected: str) -> AIExplanation | None:
    return db.scalar(select(AIExplanation).where(
        AIExplanation.question_id == question_id, AIExplanation.selected_option_id == selected
    ))


@router.post("/ai/explain", summary="#28 Why? (AI explanation)")
def explain_answer(body: ExplainRequest, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    question = db.get(Question, body.question_id)
    if question is None:
        raise ApiError(404, "not_found", "Question not found.")
    if not _has_seen_the_answer(db, user, question):
        raise ApiError(403, "not_answered_yet", "Answer this question first.")

    question_id, correct = question.id, question.correct_option_id
    saved = _saved_explanation(db, question_id, body.selected_option_id)
    if saved is None:
        passage = _passage_text(db, question)
        db.expunge(question)  # keep its loaded fields for the AI, without the database
        db.commit()  # end the read transaction, so no database connection waits on the AI
        try:
            result = ai_explain.explain_answer(question, body.selected_option_id, passage)
        except AIUnavailableError as exc:
            logger.warning("Why? failed for question %s, option %s: %s", question_id, body.selected_option_id, exc)
            raise ApiError(503, "ai_unavailable", "The AI is busy. Please try again later.") from None
        # Two users can ask at the same moment: the first answer is kept, the second one is dropped.
        db.execute(
            insert(AIExplanation)
            .values(question_id=question_id, selected_option_id=body.selected_option_id, **result)
            .on_conflict_do_nothing(index_elements=["question_id", "selected_option_id"])
        )
        db.commit()
        saved = _saved_explanation(db, question_id, body.selected_option_id)

    return {
        "question_id": question_id,
        "correct_option_id": correct,
        "why_correct_my": saved.why_correct_my,
        "why_selected_wrong_my": saved.why_selected_wrong_my,
        "other_options_my": saved.other_options_my or {},
    }


@router.put("/me/study-settings", summary="#29 Change study setup and recalculate the plan")
def update_study_settings(body: OnboardingRequest, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    settings = _settings_or_404(db, user)
    settings.last_level = body.last_level
    settings.last_score = body.last_score
    settings.exam_date = body.exam_date
    plan = service.save_plan(db, user, settings)
    plan.ai_tip_my = None  # the old tip was written for the old settings
    db.commit()
    db.refresh(plan)
    return service.plan_json(db, user, settings, plan)


@router.put("/me", summary="#30 Change username")
def update_me(body: UpdateMeRequest, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    username = body.username.lower()
    if username != user.username:
        if db.scalar(select(User.id).where(User.username == username)) is not None:
            raise ApiError(409, "username_taken", "This username is already taken.")
        user.username = username
        try:
            db.commit()  # the unique rule in the database catches two people taking it at the same moment
        except IntegrityError:
            db.rollback()
            raise ApiError(409, "username_taken", "This username is already taken.") from None
    return user_json(user)


@router.get("/me/notifications", summary="#31 Notification settings")
def get_notifications(user: CurrentUser, db: DbSession) -> dict[str, Any]:
    return _notifications_json(db.get(NotificationSettings, user.id))


@router.put("/me/notifications", summary="#32 Change notification settings")
def update_notifications(body: NotificationSettingsRequest, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    row = db.get(NotificationSettings, user.id)
    if row is None:
        row = NotificationSettings(user_id=user.id)
        db.add(row)
    row.daily_reminder = body.daily_reminder
    row.reminder_time = time.fromisoformat(body.reminder_time)
    row.proverb_notification = body.proverb_notification
    row.timezone = body.timezone
    db.commit()
    return _notifications_json(row)


@router.post("/me/devices", status_code=status.HTTP_201_CREATED, summary="#33 Register a phone for notifications")
def register_device(body: DeviceRequest, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    now = datetime.now(UTC)
    device = db.scalar(select(Device).where(Device.push_token == body.push_token))
    if device is None:
        device = Device(push_token=body.push_token)
        db.add(device)
    # A phone belongs to whoever logged in on it last, so notifications never go to the wrong account.
    device.user_id = user.id
    device.platform = body.platform
    device.last_seen_at = now
    db.flush()

    # Keep only the newest devices of this user.
    old = db.scalars(
        select(Device).where(Device.user_id == user.id)
        .order_by(func.coalesce(Device.last_seen_at, Device.created_at).desc(), Device.id.desc())
        .offset(MAX_DEVICES_PER_USER)
    )
    for extra in old:
        db.delete(extra)
    db.commit()
    return {"registered": True}


@router.post("/auth/change-password", summary="#34 Change password")
def change_password(body: ChangePasswordRequest, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    if user.password_hash is None:
        raise ApiError(400, "google_account", "This account logs in with Google and has no password here.")

    # Wrong guesses share the login limit for this email (5 in 15 minutes), so a stolen phone
    # can't be used to guess the password here instead of on the login screen.
    fail_key = f"login-fail:{user.email}"
    limiter.check(fail_key, *LOGIN_FAILS_PER_EMAIL)
    if not verify_password(body.current_password, user.password_hash):
        limiter.record(fail_key, LOGIN_FAILS_PER_EMAIL[1])
        raise ApiError(401, "wrong_password", "Password is incorrect.")
    limiter.clear(fail_key)

    locked_user = db.get(User, user.id, with_for_update=True, populate_existing=True)
    locked_user.password_hash = hash_password(body.new_password)
    # Sign out every device: whoever knew the old password is logged out now.
    # The tokens are deleted, not marked as used. A used token coming back sets off the "stolen token"
    # alarm in #7, which would also sign out the fresh login below the moment another phone tries its old token.
    db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    # This phone gets a fresh login, so the user who just changed the password stays logged in here.
    tokens = issue_tokens(db, locked_user)
    db.commit()
    return {"message": "Password updated.", **tokens}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, summary="#36 Delete the account and all its data")
def delete_me(body: DeleteAccountRequest, user: CurrentUser, db: DbSession) -> None:
    if user.password_hash is not None:  # email account: the password proves it's really the owner
        if not body.password or not verify_password(body.password, user.password_hash):
            raise ApiError(401, "wrong_password", "Password is incorrect.")
    # The database deletes everything that belongs to the user (ON DELETE CASCADE): tokens, progress,
    # attempts, saved words, settings and devices.
    db.delete(user)
    db.commit()


@router.post("/me/reset-progress", summary="#37 Reset all progress (start a new round)")
def reset_progress(body: ResetProgressRequest, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    # Lock the user row, so two quick taps can't skip a round.
    locked_user = db.get(User, user.id, with_for_update=True, populate_existing=True)
    settings = _settings_or_404(db, locked_user)
    # Nothing is deleted: old progress stays in the old round, as history.
    locked_user.current_round += 1
    plan = service.save_plan(db, locked_user, settings)
    db.commit()
    db.refresh(plan)
    return {"round": locked_user.current_round, "plan": service.plan_json(db, locked_user, settings, plan)}
