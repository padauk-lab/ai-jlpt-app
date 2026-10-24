"""#5 and #6: forgot password with a 6-digit code by email. No email is really sent in tests."""

import re
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update

from app.api.v1 import password_reset
from app.core import email
from app.core.rate_limit import FORGOT_PER_EMAIL, RESET_FAILS_PER_EMAIL
from app.models import PasswordResetToken, User
from tests.test_auth import API, PASSWORD, error_code, register
from tests.test_rate_limit import clock  # noqa: F401  (a fixture: the rate limit clock)

NEW_PASSWORD = "a-brand-new-password"
SENT = {"message": "If this email is registered, a reset code has been sent."}


@pytest.fixture
def outbox(monkeypatch) -> list[dict]:
    """Catches the emails instead of sending them."""
    sent: list[dict] = []
    monkeypatch.setattr(password_reset, "send_email", lambda to, subject, text: sent.append({"to": to, "subject": subject, "text": text}))
    return sent


def forgot(client, email_address="htet@example.com"):
    return client.post(f"{API}/auth/forgot-password", json={"email": email_address})


def reset(client, code, email_address="htet@example.com", new_password=NEW_PASSWORD):
    return client.post(f"{API}/auth/reset-password", json={"email": email_address, "code": code, "new_password": new_password})


def login(client, password):
    return client.post(f"{API}/auth/login", json={"email": "htet@example.com", "password": password})


def code_from(mail: dict) -> str:
    return re.search(r"\b\d{6}\b", mail["text"]).group()


def wrong(code: str) -> str:
    return f"{(int(code) + 1) % 1_000_000:06d}"


# --- #5 Forgot password ---


def test_code_is_emailed_and_resets_the_password(client, clock, outbox):
    register(client)
    assert forgot(client).json() == SENT
    assert len(outbox) == 1 and outbox[0]["to"] == "htet@example.com"
    code = code_from(outbox[0])

    response = reset(client, code)
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Password updated. Please log in."}
    assert login(client, PASSWORD).status_code == 401
    assert login(client, NEW_PASSWORD).status_code == 200


def test_unknown_email_gets_the_same_answer_and_no_email(client, clock, outbox):
    response = forgot(client, "nobody@example.com")
    assert response.status_code == 200 and response.json() == SENT
    assert outbox == []


def test_email_is_matched_without_caring_about_capitals(client, clock, outbox):
    register(client)
    forgot(client, "  HTET@Example.com ")
    assert reset(client, code_from(outbox[0]), email_address="Htet@EXAMPLE.com").status_code == 200


def test_only_a_keyed_hash_of_the_code_is_stored(client, clock, outbox):
    from app.db import SessionLocal

    register(client)
    forgot(client)
    code = code_from(outbox[0])
    with SessionLocal() as db:
        stored = db.scalar(select(PasswordResetToken.token_hash))
    assert code not in stored and len(stored) == 64


def test_asking_again_replaces_the_old_code(client, clock, outbox):
    register(client)
    forgot(client)
    forgot(client)
    first, second = code_from(outbox[0]), code_from(outbox[1])
    if first != second:  # (1 in a million they are the same)
        assert reset(client, first).status_code == 400
    assert reset(client, second).status_code == 200


def test_asking_too_often_is_limited(client, clock, outbox):
    register(client)
    limit, _ = FORGOT_PER_EMAIL
    for _ in range(limit):
        assert forgot(client).status_code == 200
    blocked = forgot(client)
    assert blocked.status_code == 429
    assert error_code(blocked) == "too_many_requests"
    assert len(outbox) == limit  # nobody can flood someone's inbox


# --- #6 Reset password ---


def test_code_works_only_once(client, clock, outbox):
    register(client)
    forgot(client)
    code = code_from(outbox[0])
    assert reset(client, code).status_code == 200
    again = reset(client, code, new_password="yet-another-password")
    assert again.status_code == 400
    assert error_code(again) == "invalid_code"


def test_code_expires_after_15_minutes(client, clock, outbox):
    from app.db import SessionLocal

    register(client)
    forgot(client)
    with SessionLocal() as db, db.begin():
        db.execute(update(PasswordResetToken).values(expires_at=datetime.now(UTC) - timedelta(seconds=1)))
    assert reset(client, code_from(outbox[0])).status_code == 400
    assert login(client, PASSWORD).status_code == 200  # nothing changed


def test_code_of_another_user_does_not_work(client, clock, outbox):
    register(client)
    register(client, email="other@example.com", username="other")
    forgot(client, "other@example.com")
    assert reset(client, code_from(outbox[0])).status_code == 400  # htet's account, other's code


def test_five_wrong_codes_block_and_kill_the_code(client, clock, outbox):
    register(client)
    forgot(client)
    code = code_from(outbox[0])
    limit, window = RESET_FAILS_PER_EMAIL
    for _ in range(limit - 1):
        assert reset(client, wrong(code)).status_code == 400
    assert reset(client, wrong(code)).status_code == 429  # the 5th wrong try
    assert reset(client, code).status_code == 429  # even the right code is refused now

    clock.now += window + 1
    assert reset(client, code).status_code == 400  # the code was thrown away: ask for a new one


def test_new_password_signs_out_every_device(client, clock, outbox):
    phone = register(client)
    forgot(client)
    reset(client, code_from(outbox[0]))
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": phone["refresh_token"]}).status_code == 401


def test_reset_lets_a_locked_out_user_log_in_right_away(client, clock, outbox):
    from app.core.rate_limit import LOGIN_FAILS_PER_EMAIL

    register(client)
    for _ in range(LOGIN_FAILS_PER_EMAIL[0]):
        login(client, "wrong-password")
    assert login(client, PASSWORD).status_code == 429
    forgot(client)
    reset(client, code_from(outbox[0]))
    assert login(client, NEW_PASSWORD).status_code == 200


def test_google_only_accounts_get_no_code(client, clock, outbox):
    from app.db import SessionLocal

    with SessionLocal() as db, db.begin():
        db.add(User(email="g@example.com", username="guser", password_hash=None, google_sub="google-1", login_method="google"))
    assert forgot(client, "g@example.com").json() == SENT
    assert outbox == []


@pytest.mark.parametrize(
    "body",
    [
        {"email": "htet@example.com", "code": "12345", "new_password": NEW_PASSWORD},
        {"email": "htet@example.com", "code": "12345a", "new_password": NEW_PASSWORD},
        {"email": "htet@example.com", "code": "123456", "new_password": "short"},
        {"email": "htet@example.com", "code": "123456", "new_password": NEW_PASSWORD, "user_id": 1},
        {"email": "htet@example.com", "new_password": NEW_PASSWORD},
    ],
)
def test_bad_requests_are_refused(client, clock, body):
    assert client.post(f"{API}/auth/reset-password", json=body).status_code == 422


def test_routes_are_in_the_docs_once(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert list(paths[f"{API}/auth/forgot-password"]) == ["post"]
    assert list(paths[f"{API}/auth/reset-password"]) == ["post"]


# --- Sending emails ---


def test_log_mode_does_not_send(monkeypatch):
    monkeypatch.setenv("EMAIL_MODE", "log")
    calls = []
    monkeypatch.setattr(email.urllib.request, "urlopen", lambda *a, **k: calls.append(1))
    email.send_email("a@example.com", "s", "t")
    assert calls == []


def test_resend_mode_sends_the_right_request(monkeypatch):
    import json

    monkeypatch.setenv("EMAIL_MODE", "resend")
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("EMAIL_FROM", "Kyugo <no-reply@example.com>")
    sent = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"id": "x"}'

    def fake_urlopen(req, timeout):
        sent.update(url=req.full_url, auth=req.get_header("Authorization"), body=json.loads(req.data), timeout=timeout)
        return Response()

    monkeypatch.setattr(email.urllib.request, "urlopen", fake_urlopen)
    email.send_email("a@example.com", "Subject", "Text")
    assert sent["url"] == "https://api.resend.com/emails"
    assert sent["auth"] == "Bearer re_test"
    assert sent["body"] == {"from": "Kyugo <no-reply@example.com>", "to": ["a@example.com"], "subject": "Subject", "text": "Text"}


def test_sending_errors_never_crash(monkeypatch):
    import urllib.error

    monkeypatch.setenv("EMAIL_MODE", "resend")

    def broken(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 401, "bad key", None, None)

    monkeypatch.setattr(email.urllib.request, "urlopen", broken)
    email.send_email("a@example.com", "s", "t")  # no exception
