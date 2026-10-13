"""Group 2: study setup and plan tables. See docs/database-design.md."""

from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, SmallInteger, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class StudySettings(Base):
    """The onboarding answers. One row per user, changeable in Settings."""

    __tablename__ = "study_settings"
    __table_args__ = (
        CheckConstraint("last_level IN ('N1', 'N2', 'not_taken')", name="last_level"),
        CheckConstraint("last_score BETWEEN 0 AND 180", name="last_score_range"),
        CheckConstraint("last_level <> 'not_taken' OR last_score IS NULL", name="no_score_if_not_taken"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    last_level: Mapped[str] = mapped_column(Text)
    last_score: Mapped[int | None] = mapped_column(SmallInteger)
    exam_date: Mapped[date | None] = mapped_column(Date)  # empty means "not decided yet"
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())


class Plan(Base):
    """The study plan. One row per user, recalculated when settings change or progress is reset."""

    __tablename__ = "plans"
    __table_args__ = (CheckConstraint("units_per_day >= 1", name="units_per_day_positive"),)

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    units_per_day: Mapped[int] = mapped_column(SmallInteger)
    finish_by: Mapped[date | None] = mapped_column(Date)
    ai_tip_my: Mapped[str | None] = mapped_column(Text)  # Burmese tip from the AI
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ExamDate(Base):
    """Official JLPT dates for the dropdown. Shared by everyone."""

    __tablename__ = "exam_dates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    exam_date: Mapped[date] = mapped_column(Date, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
