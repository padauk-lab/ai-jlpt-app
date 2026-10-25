"""Group 1: users and login tables. See docs/database-design.md."""

from datetime import date, datetime, time

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Text, Time, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    """One row per account."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="email_lowercase"),
        CheckConstraint("username ~ '^[a-z0-9_]{3,20}$'", name="username_format"),
        CheckConstraint("login_method IN ('email', 'google')", name="login_method"),
        CheckConstraint("password_hash IS NOT NULL OR google_sub IS NOT NULL", name="has_login"),
        CheckConstraint("current_round >= 1", name="current_round_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True)
    username: Mapped[str] = mapped_column(Text, unique=True)
    password_hash: Mapped[str | None] = mapped_column(Text)
    google_sub: Mapped[str | None] = mapped_column(Text, unique=True)
    login_method: Mapped[str] = mapped_column(Text)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    current_round: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())


class RefreshToken(Base):
    """'Stay logged in' tokens. Only the hash is stored, never the token."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PasswordResetToken(Base):
    """One-time 'Forgot password' links. Only the hash is stored."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Device(Base):
    """Phones and browsers registered for push notifications."""

    __tablename__ = "devices"
    __table_args__ = (CheckConstraint("platform IN ('ios', 'android', 'web')", name="platform"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    push_token: Mapped[str] = mapped_column(Text, unique=True)
    platform: Mapped[str] = mapped_column(Text)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NotificationSettings(Base):
    """One row per user. user_id is also the primary key (one to one)."""

    __tablename__ = "notification_settings"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    daily_reminder: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    reminder_time: Mapped[time] = mapped_column(Time, server_default=text("'20:00'"))
    proverb_notification: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    timezone: Mapped[str] = mapped_column(Text, server_default=text("'Asia/Tokyo'"))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())


class NotificationLog(Base):
    """One row per notification sent: at most one of each kind per user per day.

    The primary key makes this safe even if two servers (or two loops) run at the same time:
    only the first one can add the row, and only that one sends.
    """

    __tablename__ = "notification_log"
    __table_args__ = (CheckConstraint("kind IN ('daily_reminder')", name="kind"),)

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    kind: Mapped[str] = mapped_column(Text, primary_key=True)
    local_date: Mapped[date] = mapped_column(Date, primary_key=True)  # the day in the user's own timezone
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
