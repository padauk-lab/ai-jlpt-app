"""Daily study reminder (push notifications). Nothing is really sent in tests."""

import json
import urllib.error
from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy import func, select

from app.models import Device, NotificationLog, NotificationSettings, UnitProgress, User
from app.notifications import push, reminders, scheduler
from app.notifications.push import PushMessage
from app.notifications.reminders import due_day, send_due_reminders
from tests.test_study import content  # noqa: F401  (a fixture)

# 2026-10-25 20:00 in Tokyo (UTC+9)
EIGHT_PM_TOKYO = datetime(2026, 10, 25, 11, 0, tzinfo=UTC)
TOKEN = "ExponentPushToken[abc123]"


@pytest.fixture
def outbox(monkeypatch) -> list[PushMessage]:
    """Catches the notifications instead of sending them."""
    sent: list[PushMessage] = []

    def fake_send(messages):
        sent.extend(messages)
        return set()

    monkeypatch.setattr(reminders, "send_push", fake_send)
    return sent


def add_user(name="htet", *, onboarded=True, settings=None, devices=((TOKEN, "ios"),)) -> int:
    from app.db import SessionLocal

    with SessionLocal() as db, db.begin():
        user = User(email=f"{name}@example.com", username=name, password_hash="x", login_method="email", onboarding_completed=onboarded)
        db.add(user)
        db.flush()
        if settings is not None:
            db.add(NotificationSettings(user_id=user.id, **settings))
        for token, platform in devices:
            db.add(Device(user_id=user.id, push_token=token, platform=platform))
        return user.id


def run(now=EIGHT_PM_TOKYO) -> int:
    from app.db import SessionLocal

    with SessionLocal() as db:
        return send_due_reminders(db, now)


# --- When is a reminder due? ---


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (EIGHT_PM_TOKYO, date(2026, 10, 25)),  # on time
        (EIGHT_PM_TOKYO + timedelta(minutes=29), date(2026, 10, 25)),  # a bit late is fine
        (EIGHT_PM_TOKYO + timedelta(minutes=30), None),  # too late: skip today
        (EIGHT_PM_TOKYO - timedelta(minutes=1), None),  # too early
    ],
)
def test_due_day_window(now, expected):
    assert due_day(now, "Asia/Tokyo", time(20, 0)) == expected


def test_late_evening_reminder_still_counts_for_its_own_day():
    ten_past_midnight_tokyo = datetime(2026, 10, 25, 15, 10, tzinfo=UTC)
    assert due_day(ten_past_midnight_tokyo, "Asia/Tokyo", time(23, 50)) == date(2026, 10, 25)


def test_each_user_has_their_own_timezone():
    eight_pm_yangon = datetime(2026, 10, 25, 13, 30, tzinfo=UTC)  # Yangon is UTC+6:30
    assert due_day(eight_pm_yangon, "Asia/Yangon", time(20, 0)) == date(2026, 10, 25)
    assert due_day(eight_pm_yangon, "Asia/Tokyo", time(20, 0)) is None


# --- Sending ---


def test_reminder_is_sent_at_the_chosen_time(outbox):
    add_user(settings={"daily_reminder": True, "reminder_time": time(7, 30), "timezone": "Asia/Tokyo"})
    assert run() == 0
    assert run(datetime(2026, 10, 25, 22, 30, tzinfo=UTC)) == 1  # 07:30 on the 26th in Tokyo
    assert [m.to for m in outbox] == [TOKEN]
    assert outbox[0].data == {"type": "daily_reminder"}


def test_users_who_never_changed_settings_get_the_default_8pm_tokyo(outbox):
    add_user()
    assert run() == 1


def test_only_once_a_day(outbox):
    add_user()
    assert run() == 1
    assert run(EIGHT_PM_TOKYO + timedelta(minutes=1)) == 0
    assert len(outbox) == 1


def test_again_the_next_day(outbox):
    add_user()
    run()
    assert run(EIGHT_PM_TOKYO + timedelta(days=1)) == 1
    assert len(outbox) == 2


def test_every_phone_of_the_user_gets_it(outbox):
    add_user(devices=((TOKEN, "ios"), ("ExponentPushToken[android1]", "android")))
    assert run() == 1
    assert sorted(m.to for m in outbox) == sorted([TOKEN, "ExponentPushToken[android1]"])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"settings": {"daily_reminder": False}},  # turned off in Settings
        {"onboarded": False},  # setup not finished yet
        {"devices": ()},  # no phone registered
        {"devices": (("web-token", "web"),)},  # Expo can't push to the web app
    ],
)
def test_no_reminder(outbox, kwargs):
    add_user(**kwargs)
    assert run() == 0
    assert outbox == []


def test_tokens_that_are_not_expo_tokens_are_never_sent(outbox):
    add_user(devices=(("not-a-real-token", "ios"),))
    run()
    assert outbox == []


def test_no_reminder_if_already_studied_today(outbox, content):
    from app.db import SessionLocal

    user_id = add_user()
    with SessionLocal() as db, db.begin():
        db.add(UnitProgress(user_id=user_id, unit_id=content["units"][1], round=1, completed_at=EIGHT_PM_TOKYO - timedelta(hours=2)))
    assert run() == 0


def test_studying_yesterday_does_not_count(outbox, content):
    from app.db import SessionLocal

    user_id = add_user()
    with SessionLocal() as db, db.begin():
        db.add(UnitProgress(user_id=user_id, unit_id=content["units"][1], round=1, completed_at=EIGHT_PM_TOKYO - timedelta(hours=21)))
    assert run() == 1


def test_dead_phones_are_removed(monkeypatch):
    from app.db import SessionLocal

    add_user()
    monkeypatch.setattr(reminders, "send_push", lambda messages: {TOKEN})
    run()
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Device)) == 0


def test_old_log_rows_are_cleaned_up(outbox):
    from app.db import SessionLocal

    add_user()
    run()
    run(EIGHT_PM_TOKYO + timedelta(days=10))
    with SessionLocal() as db:
        days = db.scalars(select(NotificationLog.local_date)).all()
    assert days == [date(2026, 11, 4)]


# --- The Expo sender ---


class FakeResponse:
    def __init__(self, body: dict):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.body).encode()


def messages(n: int) -> list[PushMessage]:
    return [PushMessage(to=f"ExponentPushToken[t{i}]", title="t", body="b") for i in range(n)]


def test_off_mode_sends_nothing(monkeypatch):
    monkeypatch.delenv("PUSH_MODE", raising=False)
    calls = []
    monkeypatch.setattr(push.urllib.request, "urlopen", lambda *a, **k: calls.append(1))
    push.send_push(messages(1))
    monkeypatch.setenv("PUSH_MODE", "log")
    push.send_push(messages(1))
    assert calls == []


def test_expo_mode_sends_in_batches_of_100(monkeypatch):
    monkeypatch.setenv("PUSH_MODE", "expo")
    monkeypatch.setenv("EXPO_ACCESS_TOKEN", "secret")
    requests = []

    def fake_urlopen(req, timeout):
        body = json.loads(req.data)
        requests.append({"url": req.full_url, "auth": req.get_header("Authorization"), "body": body})
        return FakeResponse({"data": [{"status": "ok", "id": "x"} for _ in body]})

    monkeypatch.setattr(push.urllib.request, "urlopen", fake_urlopen)
    assert push.send_push(messages(150)) == set()
    assert [len(r["body"]) for r in requests] == [100, 50]
    assert requests[0]["url"] == "https://exp.host/--/api/v2/push/send"
    assert requests[0]["auth"] == "Bearer secret"
    assert requests[0]["body"][0] == {"to": "ExponentPushToken[t0]", "title": "t", "body": "b", "data": {}, "sound": "default"}


def test_dead_tokens_are_reported(monkeypatch):
    monkeypatch.setenv("PUSH_MODE", "expo")
    tickets = [
        {"status": "ok", "id": "1"},
        {"status": "error", "message": "gone", "details": {"error": "DeviceNotRegistered"}},
        {"status": "error", "message": "too big", "details": {"error": "MessageTooBig"}},
    ]
    monkeypatch.setattr(push.urllib.request, "urlopen", lambda req, timeout: FakeResponse({"data": tickets}))
    assert push.send_push(messages(3)) == {"ExponentPushToken[t1]"}


def test_network_errors_never_crash(monkeypatch):
    monkeypatch.setenv("PUSH_MODE", "expo")

    def broken(req, timeout):
        raise urllib.error.URLError("no internet")

    monkeypatch.setattr(push.urllib.request, "urlopen", broken)
    assert push.send_push(messages(1)) == set()


def test_expo_token_format():
    assert push.is_expo_token("ExponentPushToken[abc-_123]")
    assert push.is_expo_token("ExpoPushToken[abc]")
    assert not push.is_expo_token("ExponentPushToken[]")
    assert not push.is_expo_token("https://evil.example.com")


# --- The loop ---


def test_loop_does_not_start_when_off(monkeypatch):
    monkeypatch.delenv("PUSH_MODE", raising=False)
    assert scheduler.start_reminder_loop() is None


def test_loop_starts_and_stops(monkeypatch):
    monkeypatch.setenv("PUSH_MODE", "log")
    stop = scheduler.start_reminder_loop()
    assert stop is not None
    stop()
