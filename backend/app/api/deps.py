"""Shared building blocks for endpoints, used with FastAPI's Depends()."""

from typing import Annotated

from fastapi import Depends, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.security import read_access_token
from app.db import get_db
from app.models import User

# auto_error=False: we send our own contract-style 401 instead of FastAPI's default.
_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    """The logged-in user, from the "Authorization: Bearer <access_token>" header. Otherwise 401."""
    user_id = read_access_token(credentials.credentials) if credentials else None
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise ApiError(401, "not_logged_in", "Please log in again.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


# An id in the URL, like /units/{unit_id}. The limits match the database's BIGINT,
# so a huge or negative number gets a clean 422 instead of a database error.
PathId = Annotated[int, Path(ge=1, le=9_223_372_036_854_775_807)]
