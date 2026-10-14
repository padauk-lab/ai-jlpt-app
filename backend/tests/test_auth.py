"""Sign up, log in, refresh, log out and /me, including attacks that must fail."""

import time

import jwt
from fastapi.testclient import TestClient

API = "/api/v1"
PASSWORD = "my-strong-password"


def register(client: TestClient, email: str = "htet@example.com", username: str = "htetpai") -> dict:
    response = client.post(f"{API}/auth/register", json={"email": email, "username": username, "password": PASSWORD})
    assert response.status_code == 201, response.text
    return response.json()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def error_code(response) -> str:
    return response.json()["error"]["code"]


# --- Sign up ---


def test_register_returns_tokens_and_user(client):
    body = register(client, email="Htet@Example.com", username="HtetPai")
    assert body["access_token"] and body["refresh_token"]
    assert body["user"] == {
        "id": 1,
        "email": "htet@example.com",  # stored lowercase
        "username": "htetpai",
        "login_method": "email",
        "onboarding_completed": False,
    }


def test_register_same_email_in_other_case_is_refused(client):
    register(client)
    response = client.post(f"{API}/auth/register", json={"email": "HTET@example.com", "username": "other", "password": PASSWORD})
    assert response.status_code == 409
    assert error_code(response) == "email_taken"


def test_register_same_username_is_refused(client):
    register(client)
    response = client.post(f"{API}/auth/register", json={"email": "x@example.com", "username": "HTETPAI", "password": PASSWORD})
    assert response.status_code == 409
    assert error_code(response) == "username_taken"


def test_register_rejects_bad_input(client):
    cases = [
        {"email": "not-an-email", "username": "abc", "password": PASSWORD},
        {"email": "a@example.com", "username": "ab", "password": PASSWORD},  # too short
        {"email": "a@example.com", "username": "abc", "password": "short"},
        {"email": "a@example.com", "username": "abc", "password": "x" * 129},  # too long
        {"email": "a@example.com", "username": "a'; DROP TABLE users;--", "password": PASSWORD},
    ]
    for body in cases:
        response = client.post(f"{API}/auth/register", json=body)
        assert response.status_code == 422, body
        assert error_code(response) == "validation_error"


def test_password_is_stored_only_as_argon2_hash(client):
    register(client)
    from sqlalchemy import text

    from app.db import engine

    with engine.connect() as conn:
        stored = conn.scalar(text("SELECT password_hash FROM users"))
    assert stored.startswith("$argon2id$")
    assert PASSWORD not in stored


# --- Log in ---


def test_login_works_with_any_email_case(client):
    register(client)
    response = client.post(f"{API}/auth/login", json={"email": "HTET@Example.com", "password": PASSWORD})
    assert response.status_code == 200
    assert response.json()["user"]["username"] == "htetpai"


def test_wrong_password_and_unknown_email_look_the_same(client):
    register(client)
    wrong_password = client.post(f"{API}/auth/login", json={"email": "htet@example.com", "password": "wrong-password"})
    unknown_email = client.post(f"{API}/auth/login", json={"email": "nobody@example.com", "password": "wrong-password"})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_unknown_email_takes_about_as_long_as_wrong_password(client):
    register(client)
    start = time.perf_counter()
    client.post(f"{API}/auth/login", json={"email": "htet@example.com", "password": "wrong-password"})
    wrong_password_time = time.perf_counter() - start
    start = time.perf_counter()
    client.post(f"{API}/auth/login", json={"email": "nobody@example.com", "password": "wrong-password"})
    unknown_email_time = time.perf_counter() - start
    # Without the timing protection, the unknown email would be many times faster.
    assert unknown_email_time > wrong_password_time * 0.3


def test_sql_injection_in_login_does_nothing(client):
    register(client)
    response = client.post(f"{API}/auth/login", json={"email": "' OR '1'='1' --", "password": "x"})
    assert response.status_code == 401
    assert error_code(response) == "wrong_login"


# --- Who am I (/me) and tokens ---


def test_me_returns_the_logged_in_user(client):
    tokens = register(client)
    response = client.get(f"{API}/me", headers=auth_header(tokens["access_token"]))
    assert response.status_code == 200
    assert response.json()["username"] == "htetpai"


def test_me_refuses_missing_fake_and_wrong_type_tokens(client):
    tokens = register(client)
    bad_headers = [
        {},
        auth_header("abc.def.ghi"),
        auth_header(tokens["refresh_token"]),  # a refresh token is not an access token
        auth_header(tokens["access_token"][:-4] + "abcd"),  # tampered signature
    ]
    for headers in bad_headers:
        response = client.get(f"{API}/me", headers=headers)
        assert response.status_code == 401
        assert error_code(response) == "not_logged_in"


def test_tokens_signed_with_another_secret_or_expired_are_refused(client):
    register(client)
    now = int(time.time())
    forged = jwt.encode({"sub": "1", "type": "access", "iat": now, "exp": now + 60}, "x" * 40, algorithm="HS256")
    import os

    expired = jwt.encode({"sub": "1", "type": "access", "iat": 0, "exp": 1}, os.environ["JWT_SECRET"], algorithm="HS256")
    for token in (forged, expired):
        assert client.get(f"{API}/me", headers=auth_header(token)).status_code == 401


# --- Refresh tokens ---


def test_refresh_gives_new_tokens_and_old_one_stops_working(client):
    tokens = register(client)
    response = client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    new = response.json()
    assert new["refresh_token"] != tokens["refresh_token"]
    assert client.get(f"{API}/me", headers=auth_header(new["access_token"])).status_code == 200


def test_reusing_a_refresh_token_signs_out_everywhere(client):
    tokens = register(client)
    new = client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).json()

    # Someone uses the OLD token again: it may have been stolen.
    reuse = client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reuse.status_code == 401

    # So even the newest token is cancelled now.
    after = client.post(f"{API}/auth/refresh", json={"refresh_token": new["refresh_token"]})
    assert after.status_code == 401


def test_refresh_with_garbage_is_refused(client):
    response = client.post(f"{API}/auth/refresh", json={"refresh_token": "garbage"})
    assert response.status_code == 401
    assert error_code(response) == "invalid_refresh_token"


# --- Log out ---


def test_logout_cancels_the_refresh_token(client):
    tokens = register(client)
    response = client.post(
        f"{API}/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=auth_header(tokens["access_token"]),
    )
    assert response.status_code == 204
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_logout_needs_login(client):
    response = client.post(f"{API}/auth/logout", json={"refresh_token": "anything"})
    assert response.status_code == 401


def test_a_user_cannot_log_out_someone_else(client):
    alice = register(client, email="alice@example.com", username="alice")
    bob = register(client, email="bob@example.com", username="bob")
    client.post(
        f"{API}/auth/logout",
        json={"refresh_token": alice["refresh_token"]},
        headers=auth_header(bob["access_token"]),  # Bob tries to cancel Alice's token
    )
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": alice["refresh_token"]}).status_code == 200
