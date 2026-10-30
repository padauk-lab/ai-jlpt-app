"""Tests for plan_tip() (study plan tip, contract endpoint 10). They never call the real AI."""

import json

import pytest

from app.ai import tips
from app.ai.llm import AIUnavailableError

GOOD_TIP = "နေ့တိုင်း အချိန်တစ်ခုတည်းမှာ စာကျက်ပါ။"


def make_plan(days_left=54, units_per_day=5, units_done=0, units_total=200) -> dict:
    """A plan in the shape of contract endpoint 10 (only the fields plan_tip() uses)."""
    return {"days_left": days_left, "units_per_day": units_per_day, "units_done": units_done, "units_total": units_total}


def fake_ai(monkeypatch, answer):
    """Replace the real AI with a fake one that returns `answer`, and remember what it was sent."""
    sent = {}

    def fake_generate_json(system, user):
        sent["user"] = user
        return answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False)

    monkeypatch.setattr(tips, "generate_json", fake_generate_json)
    return sent


# --- The AI gets buckets, never numbers ---


def test_ai_gets_buckets_not_numbers(monkeypatch):
    sent = fake_ai(monkeypatch, {"tip_my": GOOD_TIP})
    tips.plan_tip(make_plan(), "N2")
    assert json.loads(sent["user"]) == {
        "last_level": "N2",
        "time_left": "1_to_3_months",
        "pace": "normal",
        "progress": "not_started",
    }
    

@pytest.mark.parametrize(
    ("days_left", "bucket"),
    [(None, "no_exam_date"), (29, "under_1_month"), (30, "1_to_3_months"), (90, "1_to_3_months"), (91, "over_3_months")],
)
def test_time_left_buckets(days_left, bucket):
    assert tips._time_left(days_left) == bucket


@pytest.mark.parametrize(("units_per_day", "bucket"), [(1, "light"), (3, "light"), (4, "normal"), (7, "normal"), (8, "heavy")])
def test_pace_buckets(units_per_day, bucket):
    assert tips._pace(units_per_day) == bucket


@pytest.mark.parametrize(
    ("units_done", "units_total", "bucket"),
    [(0, 200, "not_started"), (1, 200, "early"), (100, 200, "past_half"), (179, 200, "past_half"),
    (180, 200, "almost_done"), (0, 0, "not_started")],
)
def test_progress_buckets(units_done, units_total, bucket):
    assert tips._progress(units_done, units_total) == bucket


# --- The tip is checked ---


def test_good_tip_is_returned_without_spaces(monkeypatch):
    fake_ai(monkeypatch, {"tip_my": f"  {GOOD_TIP}  "})
    assert tips.plan_tip(make_plan(), "N1") == GOOD_TIP


@pytest.mark.parametrize(
    "bad_answer",
    [
        {"tip_my": "စာမေးပွဲ 54 ရက်ပဲ ကျန်ပါတော့တယ်။"},  # western digits
        {"tip_my": "စာမေးပွဲ ５４ ရက်ပဲ ကျန်ပါတော့တယ်။"},  # full-width digits
        {"tip_my": "စာမေးပွဲ ၅၄ ရက်ပဲ ကျန်ပါတော့တယ်။"},  # Burmese digits
        {"tip_my": "Study at the same time every day."},  # not Burmese
        {"tip_my": "   "},  # empty
        {"tip_my": "က" * 301},  # too long
        {"tip": GOOD_TIP},  # wrong key
        "not json",
        "[]",
    ],
)
def test_bad_tips_raise_ai_unavailable(monkeypatch, bad_answer):
    fake_ai(monkeypatch, bad_answer)
    with pytest.raises(AIUnavailableError):
        tips.plan_tip(make_plan(), "N2")

def test_tip_of_max_length_is_ok(monkeypatch):
    fake_ai(monkeypatch, {"tip_my": "က" * 300})
    assert tips.plan_tip(make_plan(), "N2") == "က" * 300


def test_unknown_level_is_refused(monkeypatch):
    sent = fake_ai(monkeypatch, {"tip_my": GOOD_TIP})
    with pytest.raises(ValueError):
        tips.plan_tip(make_plan(), "N3")
    assert sent == {}  # the AI was never called

def test_prompt_is_not_empty():
    assert len(tips.PROMPT) > 50