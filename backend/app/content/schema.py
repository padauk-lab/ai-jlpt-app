"""The shape of one unit file (data/units/sNN_uMM.json), with every rule checked.

A unit file that breaks any rule is refused with a clear message, so broken content
never reaches the database or the app.
"""

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

KANJI = re.compile(r"[㐀-䶿一-鿿々]")  # kanji, plus 々
HIRAGANA_ONLY = re.compile(r"^[ぁ-ゟー]+$")
MYANMAR = re.compile(r"[က-႟]")

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class Strict(BaseModel):
    # Unknown fields are refused, so a typo like "meanning_my" is caught instead of silently ignored.
    model_config = ConfigDict(extra="forbid")


def _burmese(value: str) -> str:
    if not MYANMAR.search(value):
        raise ValueError("must be written in Burmese (Myanmar Unicode)")
    return value


class RubyPiece(Strict):
    text: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    reading: str | None = None

    @model_validator(mode="after")
    def reading_only_for_kanji(self) -> "RubyPiece":
        has_kanji = bool(KANJI.search(self.text))
        if has_kanji and not self.reading:
            raise ValueError(f"'{self.text}' has kanji, so it needs a reading")
        if not has_kanji and self.reading is not None:
            raise ValueError(f"'{self.text}' has no kanji, so it must not have a reading")
        if self.reading is not None and not HIRAGANA_ONLY.match(self.reading):
            raise ValueError(f"reading '{self.reading}' must be hiragana only")
        return self


Ruby = Annotated[list[RubyPiece], Field(min_length=1)]


class Example(Strict):
    ruby: Ruby
    translation_my: Text

    _check_burmese = field_validator("translation_my")(_burmese)


class Word(Strict):
    position: Annotated[int, Field(ge=1, le=20)]
    word: Text
    furigana: Text
    ruby: Ruby
    meaning_my: Text
    examples: Annotated[list[Example], Field(min_length=2, max_length=3)]

    _check_burmese = field_validator("meaning_my")(_burmese)

    @field_validator("furigana")
    @classmethod
    def furigana_is_hiragana(cls, value: str) -> str:
        if not HIRAGANA_ONLY.match(value):
            raise ValueError("must be hiragana only")
        return value

    @model_validator(mode="after")
    def ruby_matches_word(self) -> "Word":
        if "".join(piece.text for piece in self.ruby) != self.word:
            raise ValueError(f"ruby text does not spell the word '{self.word}'")
        return self


class Grammar(Strict):
    pattern: Text
    meaning_my: Text
    how_to_use: Text
    how_to_use_my: Text
    note_my: Text | None = None
    examples: Annotated[list[Example], Field(min_length=2, max_length=3)]

    _check_burmese = field_validator("meaning_my", "how_to_use_my")(_burmese)

    @field_validator("note_my")
    @classmethod
    def note_is_burmese(cls, value: str | None) -> str | None:
        return _burmese(value) if value is not None else None


class UnitFile(Strict):
    session_number: Annotated[int, Field(ge=1, le=20)]
    unit_number: Annotated[int, Field(ge=1, le=10)]
    words: Annotated[list[Word], Field(min_length=20, max_length=20)]
    grammar: Grammar

    @model_validator(mode="after")
    def positions_are_1_to_20(self) -> "UnitFile":
        if sorted(word.position for word in self.words) != list(range(1, 21)):
            raise ValueError("word positions must be 1 to 20, each used once")
        return self
