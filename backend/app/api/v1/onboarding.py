"""Section 1: Onboarding. Contract endpoints #4, #9 and #10 (docs/api-contract.md).
#1, #2, #3 and #7 are real and live in auth.py, #5 and #6 (forgot password) in password_reset.py.
#8 was removed in contract v0.2.

REAL: #9 (save setup answers and create the plan) and #10 (current plan).
LATER: #4 Google login, together with Sign in with Apple (App Store rule 4.8). Still a placeholder.

Security notes:
- Both real endpoints need a logged-in user, and only ever read or change that user's own data.
- Every rule is checked here on the server, even though the app checks them too.
"""

import re
from datetime import date
from typing import Annotated, Any, Literal

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field, StrictInt, ValidationInfo, field_validator

from app.api.deps import CurrentUser, DbSession
from app.core.errors import ApiError
from app.models import Plan, StudySettings, User
from app.plan import service

router = APIRouter(tags=["1. Onboarding"])

# --- Example data, copied from the contract ---

EXAMPLE_USER: dict[str, Any] = {
    "id": 42,
    "email": "htet@example.com",
    "username": "htetpai",
    "login_method": "email",
    "onboarding_completed": True,
}

EXAMPLE_LOGIN: dict[str, Any] = {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "def50200a1...",
    "user": {**EXAMPLE_USER, "onboarding_completed": False},
}


# --- Request shapes (what the app sends) ---


class GoogleLoginRequest(BaseModel):
    id_token: str


class OnboardingRequest(BaseModel):
    """Setup answers. Also used by #29 (change them in Settings)."""

    model_config = ConfigDict(extra="forbid")  # unknown fields are refused

    last_level: Literal["N1", "N2", "not_taken"]
    # Strict: only a whole number. true, "112" or 112.5 are refused.
    # validate_default: the level check below also runs when last_score is left out.
    last_score: Annotated[StrictInt, Field(ge=0, le=180)] | None = Field(default=None, validate_default=True)
    exam_date: date | None = None

    @field_validator("last_score")
    @classmethod
    def score_matches_level(cls, score: int | None, info: ValidationInfo) -> int | None:
        level = info.data.get("last_level")
        if level == "not_taken" and score is not None:
            raise ValueError("Must be empty when the last level is not taken.")
        if level in ("N1", "N2") and score is None:
            raise ValueError("Enter your score from 0 to 180.")
        return score

    @field_validator("exam_date", mode="before")
    @classmethod
    def date_text_only(cls, value: Any) -> Any:
        # Only "YYYY-MM-DD" text, as the contract says. No numbers or times.
        if value is not None and not (isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)):
            raise ValueError("Use the format YYYY-MM-DD.")
        return value

    @field_validator("exam_date")
    @classmethod
    def date_in_future(cls, value: date | None) -> date | None:
        if value is not None and value <= service.today():
            raise ValueError("The exam date must be after today.")
        return value


# --- Endpoints ---
# The request bodies are not used yet. They are declared so /docs shows what the app must send.


@router.post("/auth/google", summary="#4 Log in or sign up with Google")
def login_google(body: GoogleLoginRequest) -> dict[str, Any]:
    return EXAMPLE_LOGIN


@router.post("/onboarding", status_code=status.HTTP_201_CREATED, summary="#9 Save setup answers and create the plan")
def save_onboarding(body: OnboardingRequest, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    # Lock this user's row until we finish, so two quick taps can't both create a setup.
    locked_user = db.get(User, user.id, with_for_update=True, populate_existing=True)
    if locked_user is None or locked_user.onboarding_completed:
        raise ApiError(409, "onboarding_already_done", "Setup is already done. Change it in Settings.")

    settings = StudySettings(
        user_id=locked_user.id,
        last_level=body.last_level,
        last_score=body.last_score,
        exam_date=body.exam_date,
    )
    db.add(settings)
    plan = service.save_plan(db, locked_user, settings)
    locked_user.onboarding_completed = True
    db.commit()
    db.refresh(plan)  # load updated_at, which the database sets
    return service.plan_json_with_new_tip(db, locked_user, settings, plan)


@router.get("/plan", summary="#10 Current study plan")
def get_plan(user: CurrentUser, db: DbSession) -> dict[str, Any]:
    settings = db.get(StudySettings, user.id)
    plan = db.get(Plan, user.id)
    if settings is None or plan is None:
        raise ApiError(404, "onboarding_not_done", "Please finish the setup first.")
    return service.plan_json_for_reading(db, user, settings, plan)

# #5 and #6 (forgot password) live in their own file. They are added to this router,
# so /docs lists them in the Onboarding group next to the other log in endpoints.
from app.api.v1 import password_reset  # noqa: E402  (imported here on purpose, after the router exists)

router.include_router(password_reset.router)
