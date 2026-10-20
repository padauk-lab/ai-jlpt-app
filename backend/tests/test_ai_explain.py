"""Tests for explain_answer() ("Why?", contract endpoint 28) and llm.py. They never call the real AI."""

import json
import urllib.error

import pytest

from app.ai import explain, llm
from app.ai.llm import AIUnavailableError
from app.models import Question


def make_question(**changes) -> Question:
    """A kanji reading question like the ones in the database. Correct answer: a."""
    data = {
        "type": "kanji_reading",
        "part": "vocabulary",
        "prompt_ruby": [{"text": "彼の"}, {"text": "意志力", "reading": "いしりょく"}, {"text": "には驚かされる。"}],
        "underline": "意志力",
        "options": [
            {"id": "a", "text": "いしりょく"},
            {"id": "b", "text": "いしりき"},
            {"id": "c", "text": "いしょく"},
            {"id": "d", "text": "いじりょく"},
        ],
        "correct_option_id": "a",
    }
    data.update(changes)
    return Question(**data)


def fake_ai(monkeypatch, answer):
    """Replace the real AI with a fake one that returns `answer`, and remember what it was sent."""
    sent = {}

    def fake_generate_json(system, user):
        sent["user"] = json.loads(user)
        return answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False)

    monkeypatch.setattr(explain, "generate_json", fake_generate_json)
    monkeypatch.setenv("LLM_MODEL", "test-model")
    return sent


GOOD = {
    "why_correct_my": "မှန်တယ်",
    "why_selected_wrong_my": "မှားတယ်",
    "other_options_my": {"c": "c မှားတယ်", "d": "d မှားတယ်"},
}


# --- explain_answer() ---


def test_wrong_pick_returns_all_fields(monkeypatch):
    fake_ai(monkeypatch, GOOD)
    result = explain.explain_answer(make_question(), "b")
    assert result == {**GOOD, "model": "test-model"}


def test_question_is_sent_as_plain_text(monkeypatch):
    sent = fake_ai(monkeypatch, GOOD)
    explain.explain_answer(make_question(), "b")
    assert sent["user"]["prompt"] == "彼の意志力には驚かされる。"
    assert sent["user"]["underline"] == "意志力"
    assert sent["user"]["options"] == {"a": "いしりょく", "b": "いしりき", "c": "いしょく", "d": "いじりょく"}
    assert sent["user"]["correct"] == "a"
    assert sent["user"]["selected"] == "b"


def test_correct_pick_forces_null_even_if_ai_writes_text(monkeypatch):
    fake_ai(monkeypatch, {
        "why_correct_my": "မှန်တယ်",
        "why_selected_wrong_my": "AI wrote this by mistake",
        "other_options_my": {"b": "b", "c": "c", "d": "d"},
    })
    result = explain.explain_answer(make_question(), "a")
    assert result["why_selected_wrong_my"] is None
    assert set(result["other_options_my"]) == {"b", "c", "d"}


def test_extra_option_notes_are_dropped(monkeypatch):
    fake_ai(monkeypatch, {**GOOD, "other_options_my": {"a": "x", "b": "x", "c": "c", "d": "d"}})
    result = explain.explain_answer(make_question(), "b")
    assert set(result["other_options_my"]) == {"c", "d"}


@pytest.mark.parametrize(
    "bad_answer",
    [
        "not json",
        "[1, 2]",
        {**GOOD, "why_correct_my": ""},
        {**GOOD, "why_selected_wrong_my": None},  # a wrong pick needs a reason
        {**GOOD, "other_options_my": {"c": "only c"}},  # note for d is missing
        {**GOOD, "other_options_my": {"c": "c", "d": 5}},  # not text
    ],
)
def test_bad_ai_answers_raise_ai_unavailable(monkeypatch, bad_answer):
    fake_ai(monkeypatch, bad_answer)
    with pytest.raises(AIUnavailableError):
        explain.explain_answer(make_question(), "b")


def test_unknown_option_is_refused(monkeypatch):
    fake_ai(monkeypatch, GOOD)
    with pytest.raises(ValueError):
        explain.explain_answer(make_question(), "e")


# --- llm.py: retry when the AI server is busy ---


class FakeResponse:
    """Looks like the answer from Gemini, with `text` inside."""

    def __init__(self, text):
        self.body = json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}]}).encode()

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def fake_server(monkeypatch, busy_times):
    """The fake server answers 503 `busy_times` times, then works."""
    calls = []

    def fake_urlopen(req, timeout):
        calls.append(1)
        if len(calls) <= busy_times:
            raise urllib.error.HTTPError("https://example.com", 503, "busy", None, None)
        return FakeResponse('{"ok": true}')

    monkeypatch.setenv("LLM_API_KEY", "fake-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setattr(llm.time, "sleep", lambda seconds: None)  # don't really wait in tests
    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    return calls


def test_llm_retries_when_busy(monkeypatch):
    calls = fake_server(monkeypatch, busy_times=llm.RETRIES - 1)  # busy until the last try
    assert llm.generate_json("system", "user") == '{"ok": true}'
    assert len(calls) == llm.RETRIES


def test_llm_gives_up_after_retries(monkeypatch):
    calls = fake_server(monkeypatch, busy_times=99)
    with pytest.raises(AIUnavailableError):
        llm.generate_json("system", "user")
    assert len(calls) == llm.RETRIES