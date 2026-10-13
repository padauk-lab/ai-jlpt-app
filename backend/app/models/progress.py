"""Group 5a: user progress tables. See docs/database-design.md.

Every progress row saves the round it belongs to. "Reset all progress" adds 1 to
users.current_round, so old rows stay as history and the app only reads the current round.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class UnitProgress(Base):
    """Units the user marked as done, per round."""

    __tablename__ = "unit_progress"
    __table_args__ = (CheckConstraint("round >= 1", name="round_positive"),)

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    unit_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("units.id", ondelete="RESTRICT"), primary_key=True, index=True)
    round: Mapped[int] = mapped_column(Integer, primary_key=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Bookmark(Base):
    """Saved words. Not tied to rounds, so a reset keeps them."""

    __tablename__ = "bookmarks"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    word_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("words.id", ondelete="RESTRICT"), primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class QuizAttempt(Base):
    """Each time a user takes a quiz."""

    __tablename__ = "quiz_attempts"
    __table_args__ = (
        Index("ix_quiz_attempts_user_id_quiz_id_round", "user_id", "quiz_id", "round"),
        CheckConstraint("round >= 1", name="round_positive"),
        CheckConstraint("score BETWEEN 0 AND 100", name="score_percent"),
        CheckConstraint("correct >= 0", name="correct_not_negative"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    quiz_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("quizzes.id", ondelete="RESTRICT"), index=True)
    round: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # empty while in progress
    correct: Mapped[int | None] = mapped_column(SmallInteger)
    score: Mapped[int | None] = mapped_column(SmallInteger)  # percent
    passed: Mapped[bool | None] = mapped_column(Boolean)


class QuizAttemptQuestion(Base):
    """The questions picked at random for one quiz attempt, in order."""

    __tablename__ = "quiz_attempt_questions"
    __table_args__ = (
        UniqueConstraint("attempt_id", "position"),
        CheckConstraint("position BETWEEN 1 AND 20", name="position_range"),
    )

    attempt_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), primary_key=True)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id", ondelete="RESTRICT"), primary_key=True, index=True)
    position: Mapped[int] = mapped_column(SmallInteger)


class QuizAnswer(Base):
    """One answer per question per attempt. The primary key makes 'answer only once' automatic."""

    __tablename__ = "quiz_answers"
    __table_args__ = (CheckConstraint("selected_option_id IN ('a', 'b', 'c', 'd')", name="selected_option_id"),)

    attempt_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), primary_key=True)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id", ondelete="RESTRICT"), primary_key=True, index=True)
    selected_option_id: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MockAttempt(Base):
    """Each time a user takes a mock test. The server sets ends_at, never the app."""

    __tablename__ = "mock_attempts"
    __table_args__ = (
        Index("ix_mock_attempts_user_id_mock_test_id_round", "user_id", "mock_test_id", "round"),
        # Only one attempt in progress per user and mock test.
        Index(
            "uq_mock_attempts_one_in_progress",
            "user_id",
            "mock_test_id",
            unique=True,
            postgresql_where=text("submitted_at IS NULL"),
        ),
        # Lets the background job quickly find attempts whose time is up.
        Index("ix_mock_attempts_open_ends_at", "ends_at", postgresql_where=text("submitted_at IS NULL")),
        CheckConstraint("round >= 1", name="round_positive"),
        CheckConstraint("ends_at > started_at", name="ends_after_start"),
        CheckConstraint("submitted_by IN ('user', 'timeout')", name="submitted_by"),
        CheckConstraint("(submitted_at IS NULL) = (submitted_by IS NULL)", name="submitted_together"),
        CheckConstraint("correct >= 0 AND correct <= total", name="correct_range"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    mock_test_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("mock_tests.id", ondelete="RESTRICT"), index=True)
    round: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # empty while in progress
    submitted_by: Mapped[str | None] = mapped_column(Text)
    correct: Mapped[int | None] = mapped_column(SmallInteger)
    total: Mapped[int | None] = mapped_column(SmallInteger)
    counts_for_prediction: Mapped[bool] = mapped_column(Boolean)  # true only for the first attempt in a round


class MockAnswer(Base):
    """Saved mock test answers, changeable until the attempt is submitted."""

    __tablename__ = "mock_answers"
    __table_args__ = (CheckConstraint("selected_option_id IN ('a', 'b', 'c', 'd')", name="selected_option_id"),)

    attempt_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("mock_attempts.id", ondelete="CASCADE"), primary_key=True)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id", ondelete="RESTRICT"), primary_key=True, index=True)
    selected_option_id: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
