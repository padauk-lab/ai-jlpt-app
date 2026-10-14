"""Section 4: AI and settings. Contract endpoints #27 to #37 (docs/api-contract.md).

PLACEHOLDER: every endpoint returns the contract's example JSON.
There is no database, no AI call and no login check yet. Each endpoint is replaced with real logic later.

Rules for the real version:
- The app sends only IDs. The backend looks up the content and passes it to SWYH's AI functions.
- "Why?" (#28) works only for questions the user has already answered or submitted. Otherwise 403.
"""

from typing import Any, Literal

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.api.v1.onboarding import EXAMPLE_PLAN, EXAMPLE_USER, OnboardingRequest

router = APIRouter(tags=["4. AI and settings"])

EXAMPLE_NOTIFICATIONS: dict[str, Any] = {
    "daily_reminder": True,
    "reminder_time": "20:00",
    "proverb_notification": True,
    "timezone": "Asia/Tokyo",
}


# --- Request shapes (what the app sends) ---


class ExamplesRequest(BaseModel):
    item_type: Literal["word", "grammar"]
    item_id: int


class ExplainRequest(BaseModel):
    question_id: int
    selected_option_id: Literal["a", "b", "c", "d"]


class UpdateMeRequest(BaseModel):
    username: str


class NotificationSettingsRequest(BaseModel):
    daily_reminder: bool
    reminder_time: str  # "HH:MM", e.g. "20:00"
    proverb_notification: bool
    timezone: str  # IANA name, e.g. "Asia/Tokyo"


class DeviceRequest(BaseModel):
    push_token: str
    platform: Literal["ios", "android", "web"]


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class LogoutRequest(BaseModel):
    refresh_token: str


class DeleteAccountRequest(BaseModel):
    confirm: Literal["DELETE"]
    password: str | None = None  # required for email users, not for Google users


class ResetProgressRequest(BaseModel):
    confirm: Literal["RESET"]


# --- Endpoints ---
# Request bodies are not used yet. They are declared so /docs shows what the app must send.


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
def update_study_settings(body: OnboardingRequest) -> dict[str, Any]:
    return EXAMPLE_PLAN


@router.put("/me", summary="#30 Change username")
def update_me(body: UpdateMeRequest) -> dict[str, Any]:
    return {**EXAMPLE_USER, "username": "htet_pai"}


@router.get("/me/notifications", summary="#31 Notification settings")
def get_notifications() -> dict[str, Any]:
    return EXAMPLE_NOTIFICATIONS


@router.put("/me/notifications", summary="#32 Change notification settings")
def update_notifications(body: NotificationSettingsRequest) -> dict[str, Any]:
    return EXAMPLE_NOTIFICATIONS


@router.post("/me/devices", status_code=status.HTTP_201_CREATED, summary="#33 Register a phone for notifications")
def register_device(body: DeviceRequest) -> dict[str, Any]:
    return {"registered": True}


@router.post("/auth/change-password", summary="#34 Change password")
def change_password(body: ChangePasswordRequest) -> dict[str, Any]:
    return {"message": "Password updated."}


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, summary="#35 Log out on this device")
def logout(body: LogoutRequest) -> None:
    return None


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, summary="#36 Delete the account and all its data")
def delete_me(body: DeleteAccountRequest) -> None:
    return None


@router.post("/me/reset-progress", summary="#37 Reset all progress (start a new round)")
def reset_progress(body: ResetProgressRequest) -> dict[str, Any]:
    return {"round": 2, "plan": EXAMPLE_PLAN}
