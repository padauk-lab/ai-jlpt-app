"""The shape of one quiz file (data/quizzes/sNN_qN.json), with every rule checked.

Format guide for the content team: docs/content-format.md
A quiz file that breaks any rule is refused with a clear message.
"""

import re
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.content.question_parts import (
    OptionId,
    Options,
    ShortPromptPiece,
    Strict,
    Text,
    check_options,
    check_type,
    check_underline,
)

MIN_QUESTIONS = 20  # one attempt uses 20, so the bank needs at least that many
MAX_QUESTIONS = 100
UNITS_BY_QUIZ = {1: (1, 5), 2: (6, 10)}


class QuizQuestion(Strict):
    number: Annotated[int, Field(ge=1, le=MAX_QUESTIONS)]  # its place in the bank; never reuse a number for a different question
    part: Literal["vocabulary", "grammar"]
    type: str
    unit_number: Annotated[int, Field(ge=1, le=10)]  # the unit it tests
    word_position: Annotated[int, Field(ge=1, le=20)] | None = None  # vocabulary: which word (1 to 20) of that unit
    prompt_ruby: Annotated[list[ShortPromptPiece], Field(min_length=1, max_length=50)]
    underline: Text | None = None
    options: Options
    correct_option_id: OptionId

    @model_validator(mode="after")
    def rules(self) -> "QuizQuestion":
        check_type(self.part, self.type)
        if self.part == "vocabulary" and self.word_position is None:
            raise ValueError("vocabulary questions need word_position (which word of the unit they test)")
        if self.part == "grammar" and self.word_position is not None:
            raise ValueError("grammar questions test the unit's grammar, so leave out word_position")
        check_options(self.options)
        check_underline(self.type, self.underline, self.prompt_ruby, self.options)
        return self


class QuizFile(Strict):
    session_number: Annotated[int, Field(ge=1, le=20)]
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
