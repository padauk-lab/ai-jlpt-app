"""The parts shared by quiz and mock test files keep each file's own limits."""

import pytest
from pydantic import ValidationError

from app.content import mock_schema, quiz_schema
from app.content.question_parts import PromptPiece, ShortPromptPiece


def test_both_files_use_the_same_option_and_type_rules():
    assert quiz_schema.check_options is mock_schema.check_options
    assert quiz_schema.check_underline is mock_schema.check_underline


def test_quiz_sentences_stay_at_500_characters():
    ShortPromptPiece(text="あ" * 500)
    with pytest.raises(ValidationError):
        ShortPromptPiece(text="あ" * 501)


def test_passages_may_be_2000_characters():
    PromptPiece(text="あ" * 2000)
    with pytest.raises(ValidationError):
        PromptPiece(text="あ" * 2001)


def test_short_pieces_keep_the_reading_rules():
    with pytest.raises(ValidationError, match="has no kanji"):
        ShortPromptPiece(text="ひらがな", reading="ひらがな")
    with pytest.raises(ValidationError, match="hiragana only"):
        ShortPromptPiece(text="漢字", reading="カンジ")
