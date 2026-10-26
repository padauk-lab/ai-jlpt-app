"""The shape of one quiz file (data/quizzes/sNN_qN.json), with every rule checked.

Format guide for the content team: docs/content-format.md
A quiz file that breaks any rule is refused with a clear message.
"""

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.content.schema import HIRAGANA_ONLY, KANJI

# N1 "Language Knowledge" question types, grouped by part.
TYPES_BY_PART = {
    "vocabulary": {"kanji_reading", "context", "paraphrase", "usage"},
    "grammar": {"grammar_form", "sentence_order"},
}
# Types where the tested part must be marked with "underline".
NEEDS_UNDERLINE = {"kanji_reading", "paraphrase", "usage"}

MIN_QUESTIONS = 20  # one attempt uses 20, so the bank needs at least that many
MAX_QUESTIONS = 100
OPTION_IDS = ["a", "b", "c", "d"]
UNITS_BY_QUIZ = {1: (1, 5), 2: (6, 10)}

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PromptPiece(Strict):
    """Like a unit's ruby piece, but a reading is optional: a quiz may hide readings on purpose."""

    text: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    reading: str | None = None

    @model_validator(mode="after")
    def reading_rules(self) -> "PromptPiece":
        if self.reading is not None:
            if not KANJI.search(self.text):
                raise ValueError(f"'{self.text}' has no kanji, so it must not have a reading")
            if not HIRAGANA_ONLY.match(self.reading):
                raise ValueError(f"reading '{self.reading}' must be hiragana only")
        return self


class Option(Strict):
    id: Literal["a", "b", "c", "d"]
    text: Text


class QuizQuestion(Strict):
    number: Annotated[int, Field(ge=1, le=MAX_QUESTIONS)]  # its place in the bank; never reuse a number for a different question
    part: Literal["vocabulary", "grammar"]
    type: str
    unit_number: Annotated[int, Field(ge=1, le=10)]  # the unit it tests
    word_position: Annotated[int, Field(ge=1, le=20)] | None = None  # vocabulary: which word (1 to 20) of that unit
    prompt_ruby: Annotated[list[PromptPiece], Field(min_length=1, max_length=50)]
    underline: Text | None = None
    options: Annotated[list[Option], Field(min_length=4, max_length=4)]
    correct_option_id: Literal["a", "b", "c", "d"]

    @model_validator(mode="after")
    def rules(self) -> "QuizQuestion":
        if self.type not in TYPES_BY_PART[self.part]:
            allowed = ", ".join(sorted(TYPES_BY_PART[self.part]))
            raise ValueError(f"type '{self.type}' is not a {self.part} type (use one of: {allowed})")

        if self.part == "vocabulary" and self.word_position is None:
            raise ValueError("vocabulary questions need word_position (which word of the unit they test)")
        if self.part == "grammar" and self.word_position is not None:
            raise ValueError("grammar questions test the unit's grammar, so leave out word_position")

        if [o.id for o in self.options] != OPTION_IDS:
            raise ValueError("options must be a, b, c, d in that order")
        texts = [o.text for o in self.options]
        if len(set(texts)) != 4:
            raise ValueError("the 4 options must all be different")

        if self.type in NEEDS_UNDERLINE and self.underline is None:
            raise ValueError(f"{self.type} questions need underline (the part being tested)")
        if self.underline is not None:
            matches = [p for p in self.prompt_ruby if p.text == self.underline]
            if len(matches) != 1:
                raise ValueError(f"underline '{self.underline}' must be exactly one piece of prompt_ruby")
            if self.type == "kanji_reading" and matches[0].reading is not None:
                raise ValueError("kanji_reading: the tested word must not show its reading, that gives the answer away")

        if self.type == "kanji_reading" and not all(HIRAGANA_ONLY.match(t) for t in texts):
            raise ValueError("kanji_reading: every option must be a reading in hiragana")
        return self


class QuizFile(Strict):
    session_number: Annotated[int, Field(ge=1, le=10)]
    quiz_number: Literal[1, 2]
    questions: Annotated[list[QuizQuestion], Field(min_length=MIN_QUESTIONS, max_length=MAX_QUESTIONS)]

    @model_validator(mode="after")
    def file_rules(self) -> "QuizFile":
        numbers = [q.number for q in self.questions]
        if sorted(numbers) != list(range(1, len(numbers) + 1)):
            raise ValueError(f"question numbers must be 1 to {len(numbers)}, each used once")

        first, last = UNITS_BY_QUIZ[self.quiz_number]
        for q in self.questions:
            if not first <= q.unit_number <= last:
                raise ValueError(f"question {q.number}: Quiz {self.quiz_number} covers units {first} to {last}, not unit {q.unit_number}")

        prompts = ["".join(p.text for p in q.prompt_ruby) + "|" + "|".join(o.text for o in q.options) for q in self.questions]
        if len(set(prompts)) != len(prompts):
            raise ValueError("two questions are exactly the same")

        if not any(q.part == "grammar" for q in self.questions):
            raise ValueError("a quiz needs some grammar questions too")
        return self


FILE_NAME = re.compile(r"^s(\d{2})_q([12])\.json$")
