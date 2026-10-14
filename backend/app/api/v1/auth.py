"""Sign up, log in, stay logged in, log out. Contract endpoints #1, #2, #3, #7 and #35.

Security notes:
- Passwords are checked with Argon2 (app/core/security.py) and never stored or logged.
- A wrong email and a wrong password get the SAME 401 message and take about the same time,
  so nobody can find out which emails are registered.
- Refresh tokens work once (rotation). If an old one is used again, someone may have stolen it,
  so every login of that user is signed out.
- All database queries use SQLAlchemy parameters, never strings glued together (no SQL injection).
"""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr, Field, StringConstraints
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.core.errors import ApiError
from app.core.security import (
    burn_time_like_a_password_check,
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.models import RefreshToken, User

router = APIRouter()

WRONG_LOGIN = "Email or password is incorrect."

# --- Request shapes ---

Username = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z0-9_]{3,20}$")]
# Upper limit stops someone from sending a 10 MB "password" to slow the server down.
Password = Annotated[str, Field(min_length=8, max_length=128)]


class RegisterRequest(BaseModel):
    email: EmailStr
    username: Username
    password: Password


class LoginRequest(BaseModel):
    email: Annotated[str, Field(max_length=254)]
    password: Annotated[str, Field(max_length=128)]


class RefreshRequest(BaseModel):
    refresh_token: Annotated[str, Field(max_length=200)]


class LogoutRequest(BaseModel):
    refresh_token: Annotated[str, Field(max_length=200)]


# --- Helpers ---


def user_json(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "login_method": user.login_method,
        "onboarding_completed": user.onboarding_completed,
    }


def issue_tokens(db: DbSession, user: User) -> dict[str, str]:
    """Create a new access token and refresh token. Only the refresh token's hash is saved."""
    refresh_token, refresh_hash = new_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=refresh_hash, expires_at=refresh_token_expiry()))
    return {"access_token": create_access_token(user.id), "refresh_token": refresh_token}


# --- Endpoints ---


@router.get("/me", tags=["1. Onboarding"], summary="#1 Who is logged in")
def get_me(user: CurrentUser) -> dict[str, Any]:
    return user_json(user)


@router.post("/auth/register", status_code=status.HTTP_201_CREATED, tags=["1. Onboarding"], summary="#2 Create an account")
def register(body: RegisterRequest, db: DbSession) -> dict[str, Any]:
    email = body.email.strip().lower()
    username = body.username.lower()

    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise ApiError(409, "email_taken", "This email is already registered.")
    if db.scalar(select(User.id).where(User.username == username)) is not None:
        raise ApiError(409, "username_taken", "This username is already taken.")

    user = User(email=email, username=username, password_hash=hash_password(body.password), login_method="email")
    db.add(user)
    try:
        db.flush()  # get user.id; the unique rules in the database catch two sign-ups at the same moment
    except IntegrityError:
        db.rollback()
        raise ApiError(409, "already_registered", "This email or username is already used.") from None

    tokens = issue_tokens(db, user)
    db.commit()
    return {**tokens, "user": user_json(user)}


@router.post("/auth/login", tags=["1. Onboarding"], summary="#3 Log in with email and password")
def login(body: LoginRequest, db: DbSession) -> dict[str, Any]:
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))

    if user is None or user.password_hash is None:
        burn_time_like_a_password_check()  # same timing as a real check
        raise ApiError(401, "wrong_login", WRONG_LOGIN)
    if not verify_password(body.password, user.password_hash):
        raise ApiError(401, "wrong_login", WRONG_LOGIN)

    tokens = issue_tokens(db, user)
    db.commit()
    return {**tokens, "user": user_json(user)}


@router.post("/auth/refresh", tags=["1. Onboarding"], summary="#7 Get a new access token")
def refresh(body: RefreshRequest, db: DbSession) -> dict[str, str]:
    now = datetime.now(UTC)
    # FOR UPDATE locks the row, so the same token can't be used twice at the same moment.
    row = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(body.refresh_token)).with_for_update()
    )
    if row is None:
        raise ApiError(401, "invalid_refresh_token", "Please log in again.")

    if row.revoked_at is not None:
        # An already-used token came back: it may have been stolen. Sign out every device of this user.
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == row.user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        db.commit()
        raise ApiError(401, "invalid_refresh_token", "Please log in again.")

    if row.expires_at <= now:
        raise ApiError(401, "invalid_refresh_token", "Please log in again.")

    user = db.get(User, row.user_id)
    if user is None:
        raise ApiError(401, "invalid_refresh_token", "Please log in again.")

    row.revoked_at = now  # each refresh token works only once
    tokens = issue_tokens(db, user)
    db.commit()
    return tokens


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["4. AI and settings"], summary="#35 Log out on this device")
def logout(body: LogoutRequest, user: CurrentUser, db: DbSession) -> None:
    db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == hash_refresh_token(body.refresh_token),
            RefreshToken.user_id == user.id,  # a user can only cancel their own tokens
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )
    db.commit()
