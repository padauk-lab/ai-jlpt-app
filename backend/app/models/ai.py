"""Group 5b: AI tables. See docs/database-design.md."""

from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AIExplanation(Base):
    """Saved 'Why?' answers, one per question and answer choice, reused for every user."""

    __tablename__ = "ai_explanations"
    __table_args__ = (
        UniqueConstraint("question_id", "selected_option_id"),
        CheckConstraint("selected_option_id IN ('a', 'b', 'c', 'd')", name="selected_option_id"),
        CheckConstraint("jsonb_typeof(other_options_my) = 'object'", name="other_options_is_object"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id", ondelete="CASCADE"))
    selected_option_id: Mapped[str] = mapped_column(Text)  # the answer the user picked
    why_correct_my: Mapped[str] = mapped_column(Text)
    why_selected_wrong_my: Mapped[str | None] = mapped_column(Text)  # empty when the pick was correct
    other_options_my: Mapped[dict[str, str] | None] = mapped_column(JSONB)  # {"c": "...", "d": "..."}
    model: Mapped[str] = mapped_column(Text)  # which AI model wrote it
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # set when ANK checks it
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIUsage(Base):
    """How many times a user pressed 'More examples' on one day, for the daily limit."""

    __tablename__ = "ai_usage"
    __table_args__ = (CheckConstraint("examples_count >= 0", name="examples_count_not_negative"),)

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    usage_date: Mapped[date] = mapped_column(Date, primary_key=True)  # in the user's timezone
    examples_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
