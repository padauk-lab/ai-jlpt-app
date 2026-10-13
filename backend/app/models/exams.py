"""Group 4: quizzes and mock tests. Same for every user. See docs/database-design.md."""

from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, SmallInteger, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.content import Ruby


class Quiz(Base):
    """2 quizzes per session: units 1 to 5 and units 6 to 10. Each has a question bank."""

    __tablename__ = "quizzes"
    __table_args__ = (
        UniqueConstraint("session_id", "number"),
        CheckConstraint("number IN (1, 2)", name="number_range"),
        CheckConstraint("first_unit BETWEEN 1 AND 10 AND last_unit BETWEEN first_unit AND 10", name="unit_range"),
        CheckConstraint("question_count >= 1", name="question_count_positive"),
        CheckConstraint("pass_mark BETWEEN 0 AND 100", name="pass_mark_percent"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sessions.id", ondelete="RESTRICT"))
    number: Mapped[int] = mapped_column(SmallInteger)
    first_unit: Mapped[int] = mapped_column(SmallInteger)
    last_unit: Mapped[int] = mapped_column(SmallInteger)
    question_count: Mapped[int] = mapped_column(SmallInteger, server_default=text("20"))  # per attempt
    pass_mark: Mapped[int] = mapped_column(SmallInteger, server_default=text("70"))  # percent


class MockTest(Base):
    """1 mock test per session."""

    __tablename__ = "mock_tests"
    __table_args__ = (CheckConstraint("time_limit_seconds > 0", name="time_limit_positive"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sessions.id", ondelete="RESTRICT"), unique=True)
    time_limit_seconds: Mapped[int] = mapped_column(Integer, server_default=text("1800"))  # 30 minutes


class ReadingPassage(Base):
    """3 reading passages per mock test: short, medium and long."""

    __tablename__ = "reading_passages"
    __table_args__ = (
        UniqueConstraint("mock_test_id", "length"),
        CheckConstraint("length IN ('short', 'medium', 'long')", name="length"),
        CheckConstraint("jsonb_typeof(text_ruby) = 'array'", name="text_ruby_is_array"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    mock_test_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("mock_tests.id", ondelete="RESTRICT"))
    length: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(SmallInteger)
    text_ruby: Mapped[Ruby] = mapped_column(JSONB)


class Question(Base):
    """Every quiz and mock test question. correct_option_id is never sent before the user answers."""

    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint("(quiz_id IS NULL) <> (mock_test_id IS NULL)", name="quiz_or_mock_test"),
        CheckConstraint("passage_id IS NULL OR (mock_test_id IS NOT NULL AND part = 'reading')", name="passage_only_reading"),
        CheckConstraint("part IN ('vocabulary', 'grammar', 'reading')", name="part"),
        CheckConstraint("jsonb_typeof(prompt_ruby) = 'array'", name="prompt_ruby_is_array"),
        CheckConstraint("jsonb_typeof(options) = 'array' AND jsonb_array_length(options) = 4", name="four_options"),
        CheckConstraint("correct_option_id IN ('a', 'b', 'c', 'd')", name="correct_option_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    quiz_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("quizzes.id", ondelete="RESTRICT"), index=True)
    mock_test_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("mock_tests.id", ondelete="RESTRICT"), index=True)
    passage_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("reading_passages.id", ondelete="RESTRICT"), index=True)
    part: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(Text)  # e.g. kanji_reading, paraphrase
    number: Mapped[int | None] = mapped_column(SmallInteger)  # order in the mock test; quiz order is random
    prompt_ruby: Mapped[Ruby] = mapped_column(JSONB)
    underline: Mapped[str | None] = mapped_column(Text)  # the part of the prompt being tested
    options: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)  # [{"id": "a", "text": "..."}, ...]
    correct_option_id: Mapped[str] = mapped_column(Text)
    word_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("words.id", ondelete="RESTRICT"), index=True)
    grammar_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("grammar.id", ondelete="RESTRICT"), index=True)
