"""Settings screen: #29 study setup, #30 username, #31 #32 notifications, #33 devices, #36 delete account, #37 reset."""

from datetime import date

import pytest
from sqlalchemy import func, select, text

from app.models import Device, RefreshToken, StudySettings, User
from app.plan import service
from tests.test_auth import API, PASSWORD, auth_header, error_code, register

TODAY = date(2026, 10, 13)


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(service, "today", lambda: TODAY)


def new_user(client, email="htet@example.com", username="htetpai", onboard=True) -> dict[str, str]:
    headers = auth_header(register(client, email=email, username=username)["access_token"])
    if onboard:
        body = {"last_level": "N2", "last_score": 112, "exam_date": "2026-12-06"}
        assert client.post(f"{API}/onboarding", json=body, headers=headers).status_code == 201
    return headers


def count(model) -> int:
    from app.db import SessionLocal

    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(model))


# --- #29 Change study setup ---


def test_changing_study_settings_recalculates_the_plan(client):
    headers = new_user(client)
    body = {"last_level": "N1", "last_score": 95, "exam_date": "2027-07-04"}
    response = client.put(f"{API}/me/study-settings", json=body, headers=headers)
    assert response.status_code == 200, response.text
    plan = response.json()
    assert plan["exam_date"] == "2027-07-04"
    assert plan["days_left"] == 264
    assert plan["units_per_day"] == 1  # lots of time: the slowest pace
    assert client.get(f"{API}/plan", headers=headers).json() == plan


def test_study_settings_use_the_same_rules_as_setup(client):
    headers = new_user(client)
    bad = {"last_level": "not_taken", "last_score": 50, "exam_date": None}
    assert client.put(f"{API}/me/study-settings", json=bad, headers=headers).status_code == 422
    past = {"last_level": "N2", "last_score": 100, "exam_date": "2026-01-01"}
    assert client.put(f"{API}/me/study-settings", json=past, headers=headers).status_code == 422


def test_study_settings_before_setup_is_404(client):
    headers = new_user(client, onboard=False)
    response = client.put(f"{API}/me/study-settings", json={"last_level": "not_taken"}, headers=headers)
    assert response.status_code == 404
    assert error_code(response) == "onboarding_not_done"


# --- #30 Username ---


def test_change_username(client):
    headers = new_user(client)
    response = client.put(f"{API}/me", json={"username": "Htet_Pai"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "htet_pai"  # stored lowercase
    assert client.get(f"{API}/me", headers=headers).json()["username"] == "htet_pai"


def test_keeping_the_same_username_is_fine(client):
    headers = new_user(client)
    assert client.put(f"{API}/me", json={"username": "HTETPAI"}, headers=headers).status_code == 200


def test_taken_username_is_refused(client):
    new_user(client, email="other@example.com", username="other")
    headers = new_user(client)
    response = client.put(f"{API}/me", json={"username": "Other"}, headers=headers)
    assert response.status_code == 409
    assert error_code(response) == "username_taken"


@pytest.mark.parametrize("bad", ["ab", "a" * 21, "htet pai", "htet-pai", "ハテ", "'; DROP TABLE users;--"])
def test_bad_usernames_are_refused(client, bad):
    headers = new_user(client, onboard=False)
    assert client.put(f"{API}/me", json={"username": bad}, headers=headers).status_code == 422


def test_only_the_username_can_be_changed(client):
    headers = new_user(client, onboard=False)
    response = client.put(f"{API}/me", json={"username": "newname", "email": "evil@example.com"}, headers=headers)
    assert response.status_code == 422
    assert client.get(f"{API}/me", headers=headers).json()["email"] == "htet@example.com"


# --- #31 #32 Notifications ---


def test_notifications_have_defaults(client):
    headers = new_user(client, onboard=False)
    assert client.get(f"{API}/me/notifications", headers=headers).json() == {
        "daily_reminder": True,
        "reminder_time": "20:00",
        "proverb_notification": True,
        "timezone": "Asia/Tokyo",
    }


def test_change_notifications(client):
    headers = new_user(client, onboard=False)
    body = {"daily_reminder": False, "reminder_time": "07:30", "proverb_notification": True, "timezone": "Asia/Yangon"}
    assert client.put(f"{API}/me/notifications", json=body, headers=headers).json() == body
    assert client.get(f"{API}/me/notifications", headers=headers).json() == body
    body["reminder_time"] = "23:59"
    assert client.put(f"{API}/me/notifications", json=body, headers=headers).json() == body


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("reminder_time", "24:00"),
        ("reminder_time", "7:30"),
        ("reminder_time", "20:00:00"),
        ("timezone", "Mars/Olympus"),
        ("timezone", "../../etc/passwd"),
        ("timezone", "x" * 65),
        ("daily_reminder", "yes please"),
    ],
)
def test_bad_notification_settings_are_refused(client, field, bad):
    headers = new_user(client, onboard=False)
    body = {"daily_reminder": True, "reminder_time": "20:00", "proverb_notification": True, "timezone": "Asia/Tokyo", field: bad}
    response = client.put(f"{API}/me/notifications", json=body, headers=headers)
    assert response.status_code == 422
    assert field in response.json()["error"]["fields"]


# --- #33 Devices ---


def test_register_a_device_twice_keeps_one_row(client):
    headers = new_user(client, onboard=False)
    body = {"push_token": "ExponentPushToken[abc]", "platform": "ios"}
    assert client.post(f"{API}/me/devices", json=body, headers=headers).json() == {"registered": True}
    assert client.post(f"{API}/me/devices", json=body, headers=headers).status_code == 201
    assert count(Device) == 1


def test_a_phone_moves_to_the_account_that_logged_in_last(client):
    from app.db import SessionLocal

    body = {"push_token": "ExponentPushToken[shared]", "platform": "android"}
    client.post(f"{API}/me/devices", json=body, headers=new_user(client, onboard=False))
    client.post(f"{API}/me/devices", json=body, headers=new_user(client, email="b@example.com", username="bbb", onboard=False))
    with SessionLocal() as db:
        owner = db.scalar(select(User.username).join(Device, Device.user_id == User.id))
    assert owner == "bbb"


def test_only_the_newest_10_devices_are_kept(client):
    headers = new_user(client, onboard=False)
    for i in range(12):
        client.post(f"{API}/me/devices", json={"push_token": f"token-{i}", "platform": "web"}, headers=headers)
    assert count(Device) == 10


# --- #36 Delete account ---


def delete_me(client, headers, body):
    return client.request("DELETE", f"{API}/me", json=body, headers=headers)


def test_delete_account_removes_everything(client):
    headers = new_user(client)
    client.post(f"{API}/me/devices", json={"push_token": "t", "platform": "ios"}, headers=headers)
    response = delete_me(client, headers, {"confirm": "DELETE", "password": PASSWORD})
    assert response.status_code == 204
    assert count(User) == count(RefreshToken) == count(StudySettings) == count(Device) == 0
    assert client.get(f"{API}/me", headers=headers).status_code == 401  # the old token stops working


@pytest.mark.parametrize(
    "body",
    [
        {"confirm": "DELETE", "password": "wrong-password"},
        {"confirm": "DELETE"},
    ],
)
def test_delete_needs_the_right_password(client, body):
    headers = new_user(client, onboard=False)
    response = delete_me(client, headers, body)
    assert response.status_code == 401
    assert error_code(response) == "wrong_password"
    assert count(User) == 1


@pytest.mark.parametrize("confirm", ["delete", "YES", ""])
def test_delete_needs_the_typed_confirmation(client, confirm):
    headers = new_user(client, onboard=False)
    assert delete_me(client, headers, {"confirm": confirm, "password": PASSWORD}).status_code == 422
    assert count(User) == 1


def test_deleting_one_account_leaves_others(client):
    new_user(client, email="other@example.com", username="other")
    headers = new_user(client)
    delete_me(client, headers, {"confirm": "DELETE", "password": PASSWORD})
    assert count(User) == 1


# --- #37 Reset progress ---


def test_reset_starts_a_new_round_and_recalculates_the_plan(client):
    from app.db import engine

    headers = new_user(client)
    response = client.post(f"{API}/me/reset-progress", json={"confirm": "RESET"}, headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["round"] == 2
    assert body["plan"]["units_done"] == 0
    assert body["plan"]["exam_date"] == "2026-12-06"  # settings are kept
    assert client.post(f"{API}/me/reset-progress", json={"confirm": "RESET"}, headers=headers).json()["round"] == 3
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT current_round FROM users")) == 3


def test_reset_needs_the_typed_confirmation(client):
    headers = new_user(client)
    assert client.post(f"{API}/me/reset-progress", json={"confirm": "reset"}, headers=headers).status_code == 422
    assert client.post(f"{API}/me/reset-progress", json={}, headers=headers).status_code == 422


def test_reset_before_setup_is_404(client):
    headers = new_user(client, onboard=False)
    assert client.post(f"{API}/me/reset-progress", json={"confirm": "RESET"}, headers=headers).status_code == 404


# --- Login ---


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("PUT", "/me/study-settings"),
        ("PUT", "/me"),
        ("GET", "/me/notifications"),
        ("PUT", "/me/notifications"),
        ("POST", "/me/devices"),
        ("DELETE", "/me"),
        ("POST", "/me/reset-progress"),
    ],
)
def test_all_settings_need_login(client, method, path):
    assert client.request(method, f"{API}{path}", json={}).status_code == 401
