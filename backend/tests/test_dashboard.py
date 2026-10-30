"""#11 GET /dashboard: progress, today's goal, "continue", and all 20 sessions on the map."""

from datetime import date, datetime, timedelta

from sqlalchemy import update

from app.models import UnitProgress
from app.plan import service
from tests.test_auth import API, auth_header, register
from tests.test_onboarding import onboard
from tests.test_study import add_mock_attempt, add_quiz_attempt, complete_units, content, user_header  # noqa: F401


def dashboard(client, headers) -> dict:
    response = client.get(f"{API}/dashboard", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_new_user(client, content):
    body = dashboard(client, user_header(client))
    assert body["overall_progress"] == 0
    assert body["pass_prediction"] is None  # no mock test yet
    assert body["pass_prediction_warning"] is None
    assert body["today"] == {"units_done": 0, "units_goal": 3}  # no setup yet: the default pace
    assert body["continue"] == {"session_id": content["s1"], "unit_id": content["units"][1], "label": "Session 1, Unit 1"}

    sessions = body["sessions"]
    assert [s["number"] for s in sessions] == list(range(1, 11))  # always all 10, in order
    assert sessions[0] == {"id": content["s1"], "number": 1, "progress": 0, "status": "available"}
    assert sessions[1] == {"id": content["s2"], "number": 2, "progress": 0, "status": "locked"}
    # Sessions whose content isn't loaded yet: locked and without an id.
    assert all(s == {"id": None, "number": s["number"], "progress": 0, "status": "locked"} for s in sessions[2:])


def test_progress_and_continue_follow_the_units(client, content):
    headers = user_header(client)
    complete_units(client, headers, content, range(1, 4))
    body = dashboard(client, headers)
    assert body["overall_progress"] == 3  # 3 of 100 units
    assert body["today"]["units_done"] == 3
    assert body["continue"]["unit_id"] == content["units"][4]
    assert body["continue"]["label"] == "Session 1, Unit 4"
    assert body["sessions"][0] == {"id": content["s1"], "number": 1, "progress": 30, "status": "in_progress"}


def test_continue_is_empty_while_waiting_for_quiz_1(client, content):
    headers = user_header(client)
    complete_units(client, headers, content, range(1, 6))
    assert dashboard(client, headers)["continue"] is None  # unit 6 needs Quiz 1 passed

    add_quiz_attempt(content["quiz1"], 85)
    assert dashboard(client, headers)["continue"]["label"] == "Session 1, Unit 6"


def test_finished_session_opens_the_next_one(client, content):
    headers = user_header(client)
    complete_units(client, headers, content, range(1, 6))
    add_quiz_attempt(content["quiz1"], 85)
    complete_units(client, headers, content, range(6, 11))
    add_quiz_attempt(content["quiz2"], 75)

    body = dashboard(client, headers)
    assert body["sessions"][0]["progress"] == 100
    assert body["sessions"][0]["status"] == "in_progress"  # the mock test is still to do
    assert body["continue"] is None

    add_mock_attempt(content["mock"], correct=30)
    body = dashboard(client, headers)
    assert body["sessions"][0]["status"] == "completed"
    assert body["sessions"][1] == {"id": content["s2"], "number": 2, "progress": 0, "status": "available"}
    assert body["continue"] == {"session_id": content["s2"], "unit_id": content["s2_units"][1], "label": "Session 2, Unit 1"}
    assert body["overall_progress"] == 10  # 10 of 100 units


def test_failed_quiz_counts_as_in_progress(client, content):
    headers = user_header(client)
    complete_units(client, headers, content, range(1, 6))
    add_quiz_attempt(content["quiz1"], 40)
    assert dashboard(client, headers)["sessions"][0]["status"] == "in_progress"


def test_today_counts_only_units_done_since_midnight_in_japan(client, content):
    headers = user_header(client)
    complete_units(client, headers, content, range(1, 4))

    from app.db import SessionLocal

    # Move one unit to yesterday (Japan time).
    yesterday = datetime.combine(service.today(), datetime.min.time(), tzinfo=service.JAPAN_TIME) - timedelta(minutes=1)
    with SessionLocal() as db, db.begin():
        db.execute(update(UnitProgress).where(UnitProgress.unit_id == content["units"][1]).values(completed_at=yesterday))

    body = dashboard(client, headers)
    assert body["today"]["units_done"] == 2
    assert body["overall_progress"] == 3  # still counts all 3


def test_goal_comes_from_the_study_plan(client, content, monkeypatch):
    monkeypatch.setattr(service, "today", lambda: date(2026, 10, 13))
    headers = user_header(client)
    assert onboard(client, headers).status_code == 201  # exam Dec 6: 3 units per day
    plan = client.get(f"{API}/plan", headers=headers).json()
    assert dashboard(client, headers)["today"]["units_goal"] == plan["units_per_day"] == 3


def test_progress_is_per_user_and_per_round(client, content):
    headers = user_header(client)
    complete_units(client, headers, content, range(1, 4))

    other = auth_header(register(client, email="other@example.com", username="other")["access_token"])
    assert dashboard(client, other)["overall_progress"] == 0
    assert dashboard(client, other)["sessions"][0]["progress"] == 0

    from app.db import SessionLocal
    from app.models import User

    with SessionLocal() as db, db.begin():
        db.execute(update(User).where(User.email == "htet@example.com").values(current_round=User.current_round + 1))
    body = dashboard(client, headers)
    assert body["overall_progress"] == 0
    assert body["today"]["units_done"] == 0
    assert body["continue"]["label"] == "Session 1, Unit 1"


def test_no_content_loaded_yet(client):
    body = dashboard(client, user_header(client))
    assert body["continue"] is None
    assert len(body["sessions"]) == 10
    assert all(s["id"] is None and s["status"] == "locked" for s in body["sessions"])


def test_needs_login(client):
    assert client.get(f"{API}/dashboard").status_code == 401

