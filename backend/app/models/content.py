"""Group 3: learning content tables. Same for every user. See docs/database-design.md."""

from typing import Any

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, SmallInteger, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

# Japanese text with readings, in the contract's format:
# [{"text": "継続", "reading": "けいぞく"}, {"text": "は"}]
Ruby = list[dict[str, Any]]


class StudySession(Base):
    """One of the 10 sessions (the database allows up to 20). Named StudySession so it is not confused with a database session."""

    __tablename__ = "sessions"
    __table_args__ = (CheckConstraint("number BETWEEN 1 AND 20", name="number_range"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    number: Mapped[int] = mapped_column(SmallInteger, unique=True)


class Unit(Base):
    """10 units per session."""

    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint("session_id", "number"),
        CheckConstraint("number BETWEEN 1 AND 10", name="number_range"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sessions.id", ondelete="RESTRICT"))
    number: Mapped[int] = mapped_column(SmallInteger)


class Word(Base):
    """20 words per unit."""

    __tablename__ = "words"
    __table_args__ = (
        UniqueConstraint("unit_id", "position"),
        CheckConstraint("position BETWEEN 1 AND 20", name="position_range"),
        CheckConstraint("jsonb_typeof(ruby) = 'array'", name="ruby_is_array"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    unit_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("units.id", ondelete="RESTRICT"))
    position: Mapped[int] = mapped_column(SmallInteger)
    word: Mapped[str] = mapped_column(Text)  # plain text for search, e.g. 意志力
    furigana: Mapped[str] = mapped_column(Text)  # reading for search, e.g. いしりょく
    ruby: Mapped[Ruby] = mapped_column(JSONB)  # for display
    meaning_my: Mapped[str] = mapped_column(Text)


class Grammar(Base):
    """1 grammar pattern per unit."""

    __tablename__ = "grammar"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    unit_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("units.id", ondelete="RESTRICT"), unique=True)
    pattern: Mapped[str] = mapped_column(Text)  # e.g. 〜というよりも
    meaning_my: Mapped[str] = mapped_column(Text)
    how_to_use: Mapped[str] = mapped_column(Text)
    how_to_use_my: Mapped[str] = mapped_column(Text)
    note_my: Mapped[str | None] = mapped_column(Text)


class Example(Base):
    """Example sentences, for either a word or a grammar pattern (never both)."""

    __tablename__ = "examples"
    __table_args__ = (
        CheckConstraint("(word_id IS NULL) <> (grammar_id IS NULL)", name="word_or_grammar"),
        CheckConstraint("jsonb_typeof(ruby) = 'array'", name="ruby_is_array"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    word_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("words.id", ondelete="RESTRICT"), index=True)
    grammar_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("grammar.id", ondelete="RESTRICT"), index=True)
    position: Mapped[int] = mapped_column(SmallInteger)
    ruby: Mapped[Ruby] = mapped_column(JSONB)
    translation_my: Mapped[str] = mapped_column(Text)


class Proverb(Base):
    """Proverb of the day."""

    __tablename__ = "proverbs"
    __table_args__ = (CheckConstraint("jsonb_typeof(ruby) = 'array'", name="ruby_is_array"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ruby: Mapped[Ruby] = mapped_column(JSONB)
    meaning_my: Mapped[str] = mapped_column(Text)
    explanation_my: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
