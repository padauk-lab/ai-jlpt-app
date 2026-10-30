"""The AI study tip on the plan (#9, #10, #29, #37 and app/plan/tip.py). The AI is always a fake here."""

import threading
import time

import pytest

from app.ai.llm import AIUnavailableError
from app.plan import tip
from tests.test_auth import API
from tests.test_onboarding import fixed_today, login_header, onboard  # noqa: F401  (fixed_today is a fixture)

TIP = "နေ့တိုင်း အချိန်တစ်ခုတည်းမှာ စာကျက်ပါ။"


class FakeAI:
    """Counts the calls, and can be slow or broken."""

    def __init__(self, answer=TIP, delay=0.0, broken=False):
        self.answer, self.delay, self.broken = answer, delay, broken
        self.calls: list[tuple[dict, str]] = []
        self.finished = threading.Event()

    def __call__(self, plan, last_level):
        self.calls.append((plan, last_level))
        try:
            time.sleep(self.delay)
            if self.broken:
                raise AIUnavailableError("down")
            return self.answer
        finally:
            self.finished.set()


@pytest.fixture
def ai(monkeypatch) -> FakeAI:
    fake = FakeAI()
    monkeypatch.setattr(tip, "ai_tip", fake)
    return fake


def get_plan(client, headers):
    return client.get(f"{API}/plan", headers=headers).json()


def wait_for_background():
    """Let any tip that is still being written finish."""
    for future in list(tip._running.values()):
        future.result(timeout=5)


def test_setup_answers_with_the_tip(client, ai):
    headers = login_header(client)
    body = onboard(client, headers).json()
    assert body["ai_tip_my"] == TIP
    assert get_plan(client, headers)["ai_tip_my"] == TIP  # saved
    assert len(ai.calls) == 1


def test_the_ai_gets_the_plan_and_the_level(client, ai):
    onboard(client, login_header(client), last_level="N1", last_score=95)
    plan, level = ai.calls[0]
    assert level == "N1"
    assert {"days_left", "units_per_day", "units_done", "units_total"} <= plan.keys()


def test_a_broken_ai_never_stops_the_plan(client, ai):
    ai.broken = True
    headers = login_header(client)
    response = onboard(client, headers)
    assert response.status_code == 201
    assert response.json()["ai_tip_my"] is None
    assert get_plan(client, headers)["units_per_day"] >= 1


def test_a_slow_ai_answers_later(client, ai, monkeypatch):
    monkeypatch.setattr(tip, "TIP_WAIT_SECONDS", 0.2)
    ai.delay = 0.6
    headers = login_header(client)
    assert onboard(client, headers).json()["ai_tip_my"] is None  # the user doesn't wait for a slow AI
    wait_for_background()
    assert get_plan(client, headers)["ai_tip_my"] == TIP  # it shows next time


def test_opening_the_plan_does_not_call_the_ai_when_there_is_a_tip(client, ai):
    headers = login_header(client)
    onboard(client, headers)
    for _ in range(3):
        get_plan(client, headers)
    assert len(ai.calls) == 1


def test_missing_tip_is_retried_at_most_once_an_hour(client, ai, monkeypatch):
    ai.broken = True
    headers = login_header(client)
    onboard(client, headers)
    get_plan(client, headers)
    get_plan(client, headers)
    wait_for_background()
    assert len(ai.calls) == 1  # failed once, not asked again right away

    ai.broken = False
    monkeypatch.setattr(tip, "RETRY_AFTER_SECONDS", 0)  # an hour later
    assert get_plan(client, headers)["ai_tip_my"] is None  # asked in the background, not waited for
    wait_for_background()
    assert get_plan(client, headers)["ai_tip_my"] == TIP
    assert len(ai.calls) == 2


def test_new_settings_get_a_new_tip(client, ai):
    headers = login_header(client)
    onboard(client, headers)
    ai.answer = "အသစ် အကြံပြုချက်"
    body = {"last_level": "N1", "last_score": 90, "exam_date": "2026-12-06"}
    changed = client.put(f"{API}/me/study-settings", json=body, headers=headers).json()
    assert changed["ai_tip_my"] == "အသစ် အကြံပြုချက်"
    assert get_plan(client, headers)["ai_tip_my"] == "အသစ် အကြံပြုချက်"


def test_new_settings_with_a_broken_ai_remove_the_old_tip(client, ai):
    headers = login_header(client)
    onboard(client, headers)
    ai.broken = True
    body = {"last_level": "N1", "last_score": 90, "exam_date": "2026-12-06"}
    assert client.put(f"{API}/me/study-settings", json=body, headers=headers).json()["ai_tip_my"] is None


def test_reset_gets_a_new_tip(client, ai):
    headers = login_header(client)
    onboard(client, headers)
    ai.answer = "စတင်ကြရအောင်"
    body = client.post(f"{API}/me/reset-progress", json={"confirm": "RESET"}, headers=headers).json()
    assert body["plan"]["ai_tip_my"] == "စတင်ကြရအောင်"


def test_a_new_plan_replaces_a_tip_that_came_late(client, ai, monkeypatch):
    monkeypatch.setattr(tip, "TIP_WAIT_SECONDS", 0.1)
    headers = login_header(client)
    ai.delay, ai.answer = 0.6, "အဟောင်း"  # slow tip for the first plan
    onboard(client, headers)
    wait_for_background()
    ai.delay, ai.answer = 0.0, "အသစ်"
    body = {"last_level": "N1", "last_score": 90, "exam_date": "2026-12-06"}
    client.put(f"{API}/me/study-settings", json=body, headers=headers)
    assert get_plan(client, headers)["ai_tip_my"] == "အသစ်"


def test_old_tip_is_not_saved_after_the_plan_changed(client, ai):
    """The direct check: a tip written for an old version of the plan is thrown away."""
    from datetime import UTC, datetime

    headers = login_header(client)
    ai.broken = True
    onboard(client, headers)
    ai.broken = False
    from app.db import SessionLocal
    from app.models import Plan

    with SessionLocal() as db:
        user_id = db.query(Plan).one().user_id
    old_version = datetime(2020, 1, 1, tzinfo=UTC)
    assert tip._write_and_save(user_id, {}, "N2", old_version) is None
    assert get_plan(client, headers)["ai_tip_my"] is None


def test_saving_the_tip_does_not_change_updated_at(client, ai, monkeypatch):
    monkeypatch.setattr(tip, "TIP_WAIT_SECONDS", 0.1)
    ai.delay = 0.4
    headers = login_header(client)
    first = onboard(client, headers).json()["updated_at"]
    wait_for_background()
    plan = get_plan(client, headers)
    assert plan["ai_tip_my"] == TIP
    assert plan["updated_at"] == first
