"""Section 1: Onboarding. Contract endpoints #1 to #10 (docs/api-contract.md). #8 was removed in contract v0.2.

PLACEHOLDER: every endpoint returns the contract's example JSON.
There is no database and no login check yet. Each endpoint is replaced with real logic later.
"""

from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, status
from pydantic import BaseModel

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

EXAMPLE_PLAN: dict[str, Any] = {
    "exam_date": "2026-12-06",
    "days_left": 54,
    "units_total": 200,
    "units_done": 0,
    "units_per_day": 4,
    "finish_by": "2026-11-29",
    "ai_tip_my": "Burmese text: focus on reading practice on weekends.",
    "updated_at": "2026-10-13T09:30:00Z",
}


# --- Request shapes (what the app sends) ---


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleLoginRequest(BaseModel):
    id_token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class OnboardingRequest(BaseModel):
    last_level: Literal["N1", "N2", "not_taken"]
    last_score: int | None = None
    exam_date: date | None = None


# --- Endpoints ---
# The request bodies are not used yet. They are declared so /docs shows what the app must send.


@router.get("/me", summary="#1 Who is logged in")
def get_me() -> dict[str, Any]:
    return EXAMPLE_USER


@router.post("/auth/register", status_code=status.HTTP_201_CREATED, summary="#2 Create an account")
def register(body: RegisterRequest) -> dict[str, Any]:
    return EXAMPLE_LOGIN


@router.post("/auth/login", summary="#3 Log in with email and password")
def login(body: LoginRequest) -> dict[str, Any]:
    return EXAMPLE_LOGIN


@router.post("/auth/google", summary="#4 Log in or sign up with Google")
def login_google(body: GoogleLoginRequest) -> dict[str, Any]:
    return EXAMPLE_LOGIN


@router.post("/auth/forgot-password", summary="#5 Send a password reset email")
def forgot_password(body: ForgotPasswordRequest) -> dict[str, Any]:
    return {"message": "If this email is registered, a reset link has been sent."}


@router.post("/auth/reset-password", summary="#6 Set a new password")
def reset_password(body: ResetPasswordRequest) -> dict[str, Any]:
    return {"message": "Password updated. Please log in."}


@router.post("/auth/refresh", summary="#7 Get a new access token")
def refresh(body: RefreshRequest) -> dict[str, Any]:
    return {"access_token": "eyJhbGciOi...", "refresh_token": "a91f3c77b2..."}


@router.post("/onboarding", status_code=status.HTTP_201_CREATED, summary="#9 Save setup answers and create the plan")
def save_onboarding(body: OnboardingRequest) -> dict[str, Any]:
    return EXAMPLE_PLAN


@router.get("/plan", summary="#10 Current study plan")
def get_plan() -> dict[str, Any]:
    return EXAMPLE_PLAN
