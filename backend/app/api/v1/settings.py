"""Section 4: AI and settings. Contract endpoints #27 to #37 (docs/api-contract.md).
#35 (log out) is real and lives in auth.py.

REAL: #29, #30, #31, #32, #33, #36 and #37 (the Settings screen).
PLACEHOLDER: #27 and #28 (AI, waiting for SWYH's functions) and #34 (change password, it edits the
login code, so it waits until the rate-limit pull request is merged).

Security notes:
- Every real endpoint needs login and only changes the logged-in user's own data.
- Dangerous actions need a typed confirmation ("DELETE", "RESET"), and deleting an email account
  also needs the password.

Rules for the AI endpoints (later):
- The app sends only IDs. The backend looks up the content and passes it to SWYH's AI functions.
- "Why?" (#28) works only for questions the user has already answered or submitted. Otherwise 403.
"""

import re
from datetime import UTC, datetime, time
from functools import cache
from typing import Annotated, Any, Literal
from zoneinfo import available_timezones

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.api.v1.auth import Username, user_json
from app.api.v1.onboarding import OnboardingRequest
from app.core.errors import ApiError
from app.core.security import verify_password
from app.models import Device, NotificationSettings, StudySettings, User
from app.plan import service

router = APIRouter(tags=["4. AI and settings"])

MAX_DEVICES_PER_USER = 10  # older phones are forgotten, so one account can't register thousands of tokens
DEFAULT_NOTIFICATIONS = {"daily_reminder": True, "reminder_time": "20:00", "proverb_notification": True, "timezone": "Asia/Tokyo"}


@cache
def _timezones() -> frozenset[str]:
    return frozenset(available_timezones())


# --- Request shapes (what the app sends) ---


class ExamplesRequest(BaseModel):
    item_type: Literal["word", "grammar"]
    item_id: int


class ExplainRequest(BaseModel):
    question_id: int
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


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


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


@router.post("/ai/examples", summary="#27 More examples (AI)")
def more_examples(body: ExamplesRequest) -> dict[str, Any]:
    return {
        "item_type": "word",
        "item_id": 501,
        "examples": [{"ruby": [{"text": "..."}], "translation_my": "Burmese translation."}],
        "remaining_today": 47,
    }


@router.post("/ai/explain", summary="#28 Why? (AI explanation)")
def explain_answer(body: ExplainRequest) -> dict[str, Any]:
    return {
        "question_id": 3101,
        "correct_option_id": "a",
        "why_correct_my": "Burmese explanation of why (a) is correct.",
        "why_selected_wrong_my": "Burmese explanation of why (b) is wrong.",
        "other_options_my": {"c": "Burmese note on (c).", "d": "Burmese note on (d)."},
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
def change_password(body: ChangePasswordRequest) -> dict[str, Any]:
    return {"message": "Password updated."}


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
