"""#34 POST /auth/change-password: the old password must be right, every device is signed out,
and this device gets a fresh login."""

import pytest
from sqlalchemy import select

from app.core.rate_limit import LOGIN_FAILS_PER_EMAIL
from app.core.security import create_access_token
from app.models import User
from tests.test_auth import API, PASSWORD, auth_header, error_code, register
from tests.test_rate_limit import clock  # noqa: F401  (a fixture: the rate limit clock)

NEW_PASSWORD = "a-brand-new-password"


def change(client, headers, current=PASSWORD, new=NEW_PASSWORD):
    return client.post(f"{API}/auth/change-password", json={"current_password": current, "new_password": new}, headers=headers)


def login(client, password):
    return client.post(f"{API}/auth/login", json={"email": "htet@example.com", "password": password})


def refresh(client, token):
    return client.post(f"{API}/auth/refresh", json={"refresh_token": token})


def test_change_password_and_log_in_with_the_new_one(client, clock):
    tokens = register(client)
    response = change(client, auth_header(tokens["access_token"]))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["message"] == "Password updated."
    assert body["access_token"] and body["refresh_token"]

    assert login(client, PASSWORD).status_code == 401  # the old password is gone
    assert login(client, NEW_PASSWORD).status_code == 200


def test_every_old_login_is_signed_out_but_this_device_stays_in(client, clock):
    phone = register(client)
    tablet = login(client, PASSWORD).json()

    body = change(client, auth_header(phone["access_token"])).json()
    assert refresh(client, tablet["refresh_token"]).status_code == 401  # other device: signed out
    assert refresh(client, phone["refresh_token"]).status_code == 401  # the old token of this device too
    # The old tokens coming back must not set off the "stolen token" alarm and sign out the new login.
    assert refresh(client, body["refresh_token"]).status_code == 200  # the new one keeps this device in
    assert client.get(f"{API}/me", headers=auth_header(body["access_token"])).status_code == 200


def test_wrong_current_password_changes_nothing(client, clock):
    tokens = register(client)
    response = change(client, auth_header(tokens["access_token"]), current="not-my-password")
    assert response.status_code == 401
    assert error_code(response) == "wrong_password"
    assert login(client, PASSWORD).status_code == 200
    assert refresh(client, tokens["refresh_token"]).status_code == 200  # nobody was signed out


def test_wrong_guesses_share_the_login_limit(client, clock):
    """5 wrong passwords in 15 minutes, counted together here and on the login screen."""
    headers = auth_header(register(client)["access_token"])
    limit, _ = LOGIN_FAILS_PER_EMAIL
    for _ in range(limit - 1):
        assert change(client, headers, current="guess").status_code == 401
    assert login(client, "guess").status_code == 401  # the 5th wrong try, on the login screen

    blocked = change(client, headers)  # even the right password is refused now
    assert blocked.status_code == 429
    assert error_code(blocked) == "too_many_requests"
    assert login(client, PASSWORD).status_code == 429


def test_google_account_has_no_password_here(client, clock):
    from app.db import SessionLocal

    with SessionLocal() as db, db.begin():
        user = User(email="g@example.com", username="guser", password_hash=None, google_sub="google-123", login_method="google")
        db.add(user)
        db.flush()
        token = create_access_token(user.id)
    response = change(client, auth_header(token))
    assert response.status_code == 400
    assert error_code(response) == "google_account"


@pytest.mark.parametrize(
    "body",
    [
        {"current_password": PASSWORD, "new_password": "short"},  # under 8 characters
        {"current_password": PASSWORD, "new_password": "x" * 129},
        {"current_password": PASSWORD},
        {"current_password": PASSWORD, "new_password": NEW_PASSWORD, "user_id": 1},
    ],
)
def test_bad_new_passwords_are_refused(client, clock, body):
    headers = auth_header(register(client)["access_token"])
    response = client.post(f"{API}/auth/change-password", json=body, headers=headers)
    assert response.status_code == 422
    assert login(client, PASSWORD).status_code == 200


def test_password_is_stored_only_as_a_hash(client, clock):
    from app.db import SessionLocal

    change(client, auth_header(register(client)["access_token"]))
    with SessionLocal() as db:
        stored = db.scalar(select(User.password_hash))
    assert NEW_PASSWORD not in stored and stored.startswith("$argon2")


def test_needs_login(client):
    assert client.post(f"{API}/auth/change-password", json={"current_password": PASSWORD, "new_password": NEW_PASSWORD}).status_code == 401
