"""Parts shared by quiz files (quiz_schema.py) and mock test files (mock_schema.py).

Both use the same JLPT N1 Language Knowledge questions: the same types, the same 4 options a to d,
the same underline rules. Keeping them in one place means a rule fixed here is fixed for both.
"""

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
OPTION_IDS = ["a", "b", "c", "d"]

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
OptionId = Literal["a", "b", "c", "d"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PromptPiece(Strict):
    """A piece of Japanese text. A reading is optional (tests may hide readings on purpose),
    and only allowed on pieces with kanji. Up to 2000 characters, for reading passages."""

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


class ShortPromptPiece(PromptPiece):
    """The same, but at most 500 characters: for question sentences."""

    text: Annotated[str, StringConstraints(min_length=1, max_length=500)]


class Option(Strict):
    id: OptionId
    text: Text


Options = Annotated[list[Option], Field(min_length=4, max_length=4)]


def check_type(part: str, type_: str) -> None:
    if type_ not in TYPES_BY_PART[part]:
        allowed = ", ".join(sorted(TYPES_BY_PART[part]))
        raise ValueError(f"type '{type_}' is not a {part} type (use one of: {allowed})")


def check_options(options: list[Option]) -> None:
    if [o.id for o in options] != OPTION_IDS:
        raise ValueError("options must be a, b, c, d in that order")
    if len({o.text for o in options}) != 4:
        raise ValueError("the 4 options must all be different")


def check_underline(type_: str, underline: str | None, prompt_ruby: list[PromptPiece], options: list[Option]) -> None:
    """The underline rules, and the kanji_reading rules that keep the answer hidden."""
    if type_ in NEEDS_UNDERLINE and underline is None:
        raise ValueError(f"{type_} questions need underline (the part being tested)")
    if underline is not None:
        matches = [p for p in prompt_ruby if p.text == underline]
        if len(matches) != 1:
            raise ValueError(f"underline '{underline}' must be exactly one piece of prompt_ruby")
        if type_ == "kanji_reading" and matches[0].reading is not None:
            raise ValueError("kanji_reading: the tested word must not show its reading, that gives the answer away")
    if type_ == "kanji_reading" and not all(HIRAGANA_ONLY.match(o.text) for o in options):
        raise ValueError("kanji_reading: every option must be a reading in hiragana")
