"""Forgot password: #5 send a code by email, #6 set a new password with that code (docs/api-contract.md).

Why a 6-digit code and not a link: on a phone, mail apps often don't open app links, and real links
need our own website domain. The user reads the code in the email and types it into the app.

Security notes:
- #5 always gives the same answer, registered email or not, so nobody can find out who has an account.
  The email is sent after the answer (in the background), so the answer time is the same too.
- The code lives 15 minutes and works once. Asking again replaces the old code.
- Only a keyed hash of the code is stored (HMAC with JWT_SECRET), so a copy of the database alone
  can't be used to work out the codes.
- Wrong codes: 5 tries per email in 15 minutes, then 429, and the code stops working.
  A 6-digit code with 5 tries has a 1 in 200,000 chance of being guessed.
- Requests for codes are limited too (per email and per network), so nobody can flood someone's inbox.
- A new password signs out every device (the refresh tokens are deleted, like change password, #34).
"""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select

from app.api.deps import DbSession
from app.api.v1.auth import Password
from app.core.email import send_email
from app.core.errors import ApiError
from app.core.rate_limit import (
    FORGOT_PER_EMAIL,
    FORGOT_PER_IP,
    RESET_FAILS_PER_EMAIL,
    client_ip,
    limiter,
)
from app.core.security import hash_password, keyed_hash
from app.models import PasswordResetToken, RefreshToken, User

router = APIRouter(tags=["1. Onboarding"])

CODE_MINUTES = 15
SENT = "If this email is registered, a reset code has been sent."
WRONG_CODE = "The code is wrong or has expired."

EMAIL_SUBJECT = "Kyugo: စကားဝှက် ပြန်သတ်မှတ်ရန် ကုဒ်"
EMAIL_TEXT = (
    "သင့်စကားဝှက်ကို ပြန်သတ်မှတ်ရန် ကုဒ်: {code}\n\n"
    "ဤကုဒ်ကို app ထဲတွင် ရိုက်ထည့်ပါ။ ၁၅ မိနစ်အတွင်း သက်တမ်းကုန်ပါမည်။\n"
    "သင် မတောင်းဆိုခဲ့ပါက ဤအီးမေးလ်ကို လျစ်လျူရှုနိုင်ပါသည်။ သင့်အကောင့်ကို မည်သူမျှ မပြောင်းလဲနိုင်ပါ။"
)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ForgotPasswordRequest(Strict):
    email: Annotated[str, Field(max_length=254)]


class ResetPasswordRequest(Strict):
    email: Annotated[str, Field(max_length=254)]
    code: Annotated[str, Field(pattern=r"^[0-9]{6}$")]
    new_password: Password  # same rules as sign up: 8 to 128 characters


def _code_hash(user_id: int, code: str) -> str:
    """Keyed hash: without JWT_SECRET, the stored value is useless for guessing codes."""
    return keyed_hash(f"reset-code:{user_id}:{code}")


def _clean_email(email: str) -> str:
    return email.strip().lower()


@router.post("/auth/forgot-password", summary="#5 Send a password reset code by email")
def forgot_password(body: ForgotPasswordRequest, request: Request, background: BackgroundTasks, db: DbSession) -> dict[str, Any]:
    email = _clean_email(body.email)
    limiter.hit(f"forgot-ip:{client_ip(request)}", *FORGOT_PER_IP)
    limiter.hit(f"forgot-email:{email}", *FORGOT_PER_EMAIL)  # the same for unknown emails

    user = db.scalar(select(User).where(User.email == email))
    if user is not None and user.password_hash is not None:  # only accounts that have a password
        code = f"{secrets.randbelow(1_000_000):06d}"
        db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))  # one code at a time
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=_code_hash(user.id, code),
            expires_at=datetime.now(UTC) + timedelta(minutes=CODE_MINUTES),
        ))
        db.commit()
        background.add_task(send_email, user.email, EMAIL_SUBJECT, EMAIL_TEXT.format(code=code))
    return {"message": SENT}


@router.post("/auth/reset-password", summary="#6 Set a new password with the code from the email")
def reset_password(body: ResetPasswordRequest, db: DbSession) -> dict[str, Any]:
    email = _clean_email(body.email)
    fail_key = f"reset-fail:{email}"
    limiter.check(fail_key, *RESET_FAILS_PER_EMAIL)  # checked BEFORE the code, so guessing stops

    now = datetime.now(UTC)
    user = db.scalar(select(User).where(User.email == email))
    token = None
    if user is not None:
        token = db.scalar(
            select(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.token_hash == _code_hash(user.id, body.code),
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
            .with_for_update()  # two taps at the same moment can't both use the code
        )
    if token is None:
        limiter.record(fail_key, RESET_FAILS_PER_EMAIL[1])
        try:
            limiter.check(fail_key, *RESET_FAILS_PER_EMAIL)
        except ApiError:
            if user is not None:  # too many wrong tries: this code is finished, ask for a new one
                db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
                db.commit()
            raise
        raise ApiError(400, "invalid_code", WRONG_CODE)

    user.password_hash = hash_password(body.new_password)
    token.used_at = now
    db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))  # sign out every device
    db.commit()
    limiter.clear(fail_key)
    limiter.clear(f"login-fail:{email}")  # the owner proved who they are: let them log in right away
    return {"message": "Password updated. Please log in."}
