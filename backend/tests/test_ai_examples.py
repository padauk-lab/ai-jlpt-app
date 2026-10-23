"""Tests for generate_examples() ("More examples", contract endpoint 27). They never call the real AI."""

import json

import pytest

from app.ai import examples
from app.ai.llm import AIUnavailableError

TARGET = "概念"
EXISTING = ["この理論の概念を理解するのは難しい。"]


def good(n: int) -> dict:
    """A valid example that uses 概念. n makes every sentence different."""
    return {
        "ruby": [{"text": "概念", "reading": "がいねん"}, {"text": "は" + "あいうえお"[n] + "。"}],
        "translation_my": f"အယူအဆ {n}",
    }


def sentence(example: dict) -> str:
    return "".join(piece["text"] for piece in example["ruby"])


def fake_ai(monkeypatch, answer):
    """Replace the real AI with a fake one that returns `answer`, and remember what it was sent."""
    sent = {}

    def fake_generate_json(system, user):
        sent["user"] = json.loads(user)
        return answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False)

    monkeypatch.setattr(examples, "generate_json", fake_generate_json)
    return sent


def run(item_type="word", target=TARGET):
    return examples.generate_examples(item_type, target, "အယူအဆ", EXISTING)


# --- Happy path ---


def test_returns_three_examples_from_four(monkeypatch):
    fake_ai(monkeypatch, {"examples": [good(0), good(1), good(2), good(3)]})
    result = run()
    assert result == [good(0), good(1), good(2)]


def test_sends_target_existing_and_one_extra(monkeypatch):
    sent = fake_ai(monkeypatch, {"examples": [good(0), good(1), good(2)]})
    run()
    assert sent["user"]["target"] == TARGET
    assert sent["user"]["existing"] == EXISTING
    assert sent["user"]["count"] == 4


def test_grammar_can_be_conjugated(monkeypatch):
    many = [
        {"ruby": [{"text": "彼", "reading": "かれ"}, {"text": "は" + c + "をものともしなかった。"}],
         "translation_my": "သူသည် ဂရုမစိုက်ခဲ့ပါ။"}
        for c in "あいう"
    ]
    fake_ai(monkeypatch, {"examples": many})
    assert len(run("grammar", "〜をものともせず")) == 3

# --- One bad example is dropped, the good ones are kept ---


@pytest.mark.parametrize(
    "bad",
    [
        {"ruby": [{"text": "概念"}, {"text": "だ。"}], "translation_my": "မှား"},  # kanji without reading
        {"ruby": [{"text": "概念", "reading": "ガイネン"}, {"text": "だ。"}], "translation_my": "မှား"},  # katakana reading
        {"ruby": [{"text": "概念", "reading": "がいねん"}, {"text": "だ。", "reading": "だ"}], "translation_my": "မှား"},  # reading on kana
        {"ruby": [{"text": "それはいい。"}], "translation_my": "မှား"},  # does not use 概念
        {"ruby": [{"text": "この"}, {"text": "理論", "reading": "りろん"}, {"text": "の"},
                  {"text": "概念", "reading": "がいねん"}, {"text": "を"}, {"text": "理解", "reading": "りかい"},
                  {"text": "するのは"}, {"text": "難", "reading": "むずか"}, {"text": "しい。"}],
         "translation_my": "မှား"},  # same as an existing example
        {"ruby": [{"text": "概念", "reading": "がいねん"}, {"text": "だ。"}], "translation_my": "概念です"},  # not Burmese
    ],
)
def test_bad_example_is_dropped(monkeypatch, bad):
    fake_ai(monkeypatch, {"examples": [bad, good(0), good(1), good(2)]})
    result = run()
    assert [sentence(ex) for ex in result] == [sentence(good(n)) for n in range(3)]


def test_extra_fields_are_removed(monkeypatch):
    messy = {
        "ruby": [{"text": "概念", "reading": "がいねん", "color": "red"}, {"text": "だ。", "reading": None}],
        "translation_my": "  အယူအဆ  ",
    }
    fake_ai(monkeypatch, {"examples": [messy, good(0), good(1)]})
    first = run()[0]
    assert first == {"ruby": [{"text": "概念", "reading": "がいねん"}, {"text": "だ。"}], "translation_my": "အယူအဆ"}


# --- Not enough good examples, or a broken answer ---


def test_too_few_good_examples_raise(monkeypatch):
    bad = {"ruby": [{"text": "概念"}], "translation_my": "မှား"}
    fake_ai(monkeypatch, {"examples": [good(0), good(1), bad, bad]})
    with pytest.raises(AIUnavailableError):
        run()


def test_repeated_new_sentences_count_once(monkeypatch):
    fake_ai(monkeypatch, {"examples": [good(0), good(0), good(0), good(1)]})
    with pytest.raises(AIUnavailableError):
        run()


@pytest.mark.parametrize("broken", ["not json", "[]", {"examples": "nope"}, {"nothing": []}])
def test_broken_answers_raise(monkeypatch, broken):
    fake_ai(monkeypatch, broken)
    with pytest.raises(AIUnavailableError):
        run()


def test_unknown_item_type_is_refused(monkeypatch):
    fake_ai(monkeypatch, {"examples": [good(0), good(1), good(2)]})
    with pytest.raises(ValueError):
        run("sentence")