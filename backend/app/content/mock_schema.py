"""The shape of one mock test file (data/mock_tests/sNN_mock.json), with every rule checked.

Format guide for the content team: docs/mock-test-format.md
One mock test per session, in the JLPT N1 Language Knowledge format (contract, Mock test rules):
- 45 language knowledge questions (vocabulary and grammar), numbered 1 to 45
- 3 reading passages (short, medium, long), each with its own questions, numbered after 45

Note: PromptPiece and Option repeat the quiz file's rules (app/content/quiz_schema.py, in another
pull request). Once both are merged, they move to one shared place.
"""

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.content.schema import HIRAGANA_ONLY, KANJI

LANGUAGE_KNOWLEDGE_QUESTIONS = 45
PASSAGE_LENGTHS = ["short", "medium", "long"]
TYPES_BY_PART = {
    "vocabulary": {"kanji_reading", "context", "paraphrase", "usage"},
    "grammar": {"grammar_form", "sentence_order"},
}
NEEDS_UNDERLINE = {"kanji_reading", "paraphrase", "usage"}
OPTION_IDS = ["a", "b", "c", "d"]

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
FILE_NAME = re.compile(r"^s(\d{2})_mock\.json$")


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PromptPiece(Strict):
    """A reading is optional, and only allowed on pieces with kanji."""

    text: Annotated[str, StringConstraints(min_length=1, max_length=2000)]
    reading: str | None = None

    @model_validator(mode="after")
    def reading_rules(self) -> "PromptPiece":
        if self.reading is not None:
            if not KANJI.search(self.text):
                raise ValueError(f"'{self.text[:20]}' has no kanji, so it must not have a reading")
            if not HIRAGANA_ONLY.match(self.reading):
                raise ValueError(f"reading '{self.reading}' must be hiragana only")
        return self


class Option(Strict):
    id: Literal["a", "b", "c", "d"]
    text: Text


def _check_options(options: list[Option]) -> None:
    if [o.id for o in options] != OPTION_IDS:
        raise ValueError("options must be a, b, c, d in that order")
    if len({o.text for o in options}) != 4:
        raise ValueError("the 4 options must all be different")


Prompt = Annotated[list[PromptPiece], Field(min_length=1, max_length=50)]
Options = Annotated[list[Option], Field(min_length=4, max_length=4)]


class KnowledgeQuestion(Strict):
    """Vocabulary or grammar question (numbers 1 to 45)."""

    number: Annotated[int, Field(ge=1, le=LANGUAGE_KNOWLEDGE_QUESTIONS)]
    part: Literal["vocabulary", "grammar"]
    type: str
    unit_number: Annotated[int, Field(ge=1, le=10)] | None = None  # optional: which unit it tests, for review
    word_position: Annotated[int, Field(ge=1, le=20)] | None = None  # optional, vocabulary only
    prompt_ruby: Prompt
    underline: Text | None = None
    options: Options
    correct_option_id: Literal["a", "b", "c", "d"]

    @model_validator(mode="after")
    def rules(self) -> "KnowledgeQuestion":
        if self.type not in TYPES_BY_PART[self.part]:
            allowed = ", ".join(sorted(TYPES_BY_PART[self.part]))
            raise ValueError(f"type '{self.type}' is not a {self.part} type (use one of: {allowed})")
        if self.word_position is not None and (self.part != "vocabulary" or self.unit_number is None):
            raise ValueError("word_position is only for vocabulary questions, together with unit_number")
        _check_options(self.options)
        if self.type in NEEDS_UNDERLINE and self.underline is None:
            raise ValueError(f"{self.type} questions need underline (the part being tested)")
        if self.underline is not None:
            matches = [p for p in self.prompt_ruby if p.text == self.underline]
            if len(matches) != 1:
                raise ValueError(f"underline '{self.underline}' must be exactly one piece of prompt_ruby")
            if self.type == "kanji_reading" and matches[0].reading is not None:
                raise ValueError("kanji_reading: the tested word must not show its reading, that gives the answer away")
        if self.type == "kanji_reading" and not all(HIRAGANA_ONLY.match(o.text) for o in self.options):
            raise ValueError("kanji_reading: every option must be a reading in hiragana")
        return self


class ReadingQuestion(Strict):
    number: Annotated[int, Field(ge=LANGUAGE_KNOWLEDGE_QUESTIONS + 1, le=100)]
    prompt_ruby: Prompt
    options: Options
    correct_option_id: Literal["a", "b", "c", "d"]

    @model_validator(mode="after")
    def rules(self) -> "ReadingQuestion":
        _check_options(self.options)
        return self


class Passage(Strict):
    length: Literal["short", "medium", "long"]
    text_ruby: Annotated[list[PromptPiece], Field(min_length=1, max_length=2000)]
    questions: Annotated[list[ReadingQuestion], Field(min_length=1, max_length=10)]


class MockTestFile(Strict):
    session_number: Annotated[int, Field(ge=1, le=10)]
    time_limit_minutes: Annotated[int, Field(ge=1, le=180)] = 30
    questions: Annotated[list[KnowledgeQuestion], Field(min_length=LANGUAGE_KNOWLEDGE_QUESTIONS, max_length=LANGUAGE_KNOWLEDGE_QUESTIONS)]
    passages: Annotated[list[Passage], Field(min_length=3, max_length=3)]

    @model_validator(mode="after")
    def file_rules(self) -> "MockTestFile":
        if [q.number for q in self.questions] != list(range(1, LANGUAGE_KNOWLEDGE_QUESTIONS + 1)):
            raise ValueError(f"language knowledge questions must be numbered 1 to {LANGUAGE_KNOWLEDGE_QUESTIONS}, in order")
        if [p.length for p in self.passages] != PASSAGE_LENGTHS:
            raise ValueError("passages must be short, medium and long, in that order")
        reading_numbers = [q.number for p in self.passages for q in p.questions]
        expected = list(range(LANGUAGE_KNOWLEDGE_QUESTIONS + 1, LANGUAGE_KNOWLEDGE_QUESTIONS + 1 + len(reading_numbers)))
        if reading_numbers != expected:
            raise ValueError(f"reading questions must continue the numbers: {expected[0]} to {expected[-1]}, in order")
        for part in TYPES_BY_PART:
            if not any(q.part == part for q in self.questions):
                raise ValueError(f"the mock test needs some {part} questions")
        return self
