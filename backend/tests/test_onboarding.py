"""#9 POST /onboarding and #10 GET /plan, including inputs that must be refused."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.plan import service
from tests.test_auth import API, auth_header, error_code, register

TODAY = date(2026, 10, 13)


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    """Every test in this file runs as if today were Oct 13, 2026, so the numbers never change."""
    monkeypatch.setattr(service, "today", lambda: TODAY)


def login_header(client: TestClient, email: str = "htet@example.com", username: str = "htetpai") -> dict[str, str]:
    return auth_header(register(client, email=email, username=username)["access_token"])


def onboard(client: TestClient, headers: dict[str, str], **answers):
    body = {"last_level": "N2", "last_score": 112, "exam_date": "2026-12-06", **answers}
    return client.post(f"{API}/onboarding", json=body, headers=headers)


# --- Happy paths ---


def test_onboarding_creates_the_plan(client):
    headers = login_header(client)
    response = onboard(client, headers)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body.pop("updated_at").endswith("Z")
    # 54 days left. Not N1, so 14 review days: 100 units / 40 days = 3 per day (rounded up), done by Nov 15.
    assert body == {
        "exam_date": "2026-12-06",
        "days_left": 54,
        "units_total": 100,
        "units_done": 0,
        "units_per_day": 3,
        "finish_by": "2026-11-15",
        "ai_tip_my": None,
    }


def test_plan_shows_the_same_numbers_and_me_says_onboarding_done(client):
    headers = login_header(client)
    created = onboard(client, headers).json()
    plan = client.get(f"{API}/plan", headers=headers)
    assert plan.status_code == 200
    assert plan.json() == created
    assert client.get(f"{API}/me", headers=headers).json()["onboarding_completed"] is True


def test_n1_gets_fewer_review_days(client):
    headers = login_header(client)
    body = onboard(client, headers, last_level="N1", last_score=95).json()
    # 7 review days: 100 units / 47 days = 3 per day (rounded up).
    assert body["units_per_day"] == 3
    assert body["finish_by"] == "2026-11-15"


def test_no_exam_date_uses_the_default_pace(client):
    headers = login_header(client)
    response = onboard(client, headers, last_level="not_taken", last_score=None, exam_date=None)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["exam_date"] is None
    assert body["days_left"] is None
    assert body["finish_by"] is None
    assert body["units_per_day"] == 3


def test_score_can_be_left_out_when_not_taken(client):
    headers = login_header(client)
    response = client.post(f"{API}/onboarding", json={"last_level": "not_taken"}, headers=headers)
    assert response.status_code == 201, response.text


# --- Rules the server enforces ---


def test_onboarding_twice_is_refused(client):
    headers = login_header(client)
    assert onboard(client, headers).status_code == 201
    second = onboard(client, headers, exam_date="2027-07-04")
    assert second.status_code == 409
    assert error_code(second) == "onboarding_already_done"
    # The first plan is unchanged.
    assert client.get(f"{API}/plan", headers=headers).json()["exam_date"] == "2026-12-06"


def test_plan_before_onboarding_is_404(client):
    headers = login_header(client)
    response = client.get(f"{API}/plan", headers=headers)
    assert response.status_code == 404
    assert error_code(response) == "onboarding_not_done"


def test_both_endpoints_need_login(client):
    assert client.get(f"{API}/plan").status_code == 401
    response = client.post(f"{API}/onboarding", json={"last_level": "not_taken"})
    assert response.status_code == 401
    assert error_code(response) == "not_logged_in"


def test_users_only_see_their_own_plan(client):
    first = login_header(client)
    onboard(client, first)
    second = login_header(client, email="other@example.com", username="other")
    assert client.get(f"{API}/plan", headers=second).status_code == 404


@pytest.mark.parametrize(
    ("answers", "bad_field"),
    [
        ({"exam_date": "2026-10-13"}, "exam_date"),  # today is not "after today"
        ({"exam_date": "2026-10-01"}, "exam_date"),  # past
        ({"exam_date": 1797000000}, "exam_date"),  # a number, not a date
        ({"exam_date": "2026-12-06T00:00:00"}, "exam_date"),  # a time is not allowed
        ({"exam_date": "06/12/2026"}, "exam_date"),
        ({"last_level": "N3"}, "last_level"),  # the app is N1 only; N3 is not an answer
        ({"last_score": 181}, "last_score"),
        ({"last_score": -1}, "last_score"),
        ({"last_score": True}, "last_score"),
        ({"last_score": "112"}, "last_score"),
        ({"last_score": 112.5}, "last_score"),
        ({"last_score": None}, "last_score"),  # N2 needs a score
        ({"last_level": "not_taken", "last_score": 50}, "last_score"),  # no score without a test
        ({"is_admin": True}, "is_admin"),  # unknown fields are refused
    ],
)
def test_bad_answers_are_refused(client, answers, bad_field):
    headers = login_header(client)
    response = onboard(client, headers, **answers)
    assert response.status_code == 422, response.text
    assert error_code(response) == "validation_error"
    assert bad_field in response.json()["error"]["fields"]
    # Nothing was saved.
    assert client.get(f"{API}/plan", headers=headers).status_code == 404
