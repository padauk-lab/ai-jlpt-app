"""Rate limits on login and sign up: password guessing and mass sign-ups must be stopped."""

import pytest

from app.core import rate_limit
from app.core.rate_limit import LOGIN_FAILS_PER_EMAIL, LOGIN_PER_IP, REGISTER_PER_IP, RateLimiter, limiter
from tests.test_auth import API, PASSWORD, error_code, register


class FakeClock:
    """A clock we can move forward by hand, so tests don't have to wait 15 minutes."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock(monkeypatch) -> FakeClock:
    fake = FakeClock()
    monkeypatch.setattr(limiter, "clock", fake)
    return fake


def login(client, email: str = "htet@example.com", password: str = "wrong-password"):
    return client.post(f"{API}/auth/login", json={"email": email, "password": password})


# --- Login: wrong passwords per email ---


def test_too_many_wrong_passwords_locks_that_email(client, clock):
    register(client)
    limit, _ = LOGIN_FAILS_PER_EMAIL
    for _ in range(limit):
        assert login(client).status_code == 401

    blocked = login(client, password=PASSWORD)  # even the right password is refused now
    assert blocked.status_code == 429
    assert error_code(blocked) == "too_many_requests"
    assert int(blocked.headers["Retry-After"]) > 0


def test_lock_ends_after_the_window(client, clock):
    register(client)
    limit, window = LOGIN_FAILS_PER_EMAIL
    for _ in range(limit):
        login(client)
    assert login(client, password=PASSWORD).status_code == 429

    clock.now += window + 1
    assert login(client, password=PASSWORD).status_code == 200


def test_correct_login_resets_the_count(client, clock):
    register(client)
    limit, _ = LOGIN_FAILS_PER_EMAIL
    for _ in range(limit - 1):
        login(client)
    assert login(client, password=PASSWORD).status_code == 200
    for _ in range(limit - 1):
        assert login(client).status_code == 401  # counting started again from zero


def test_lock_is_per_email(client, clock):
    register(client)
    register(client, email="other@example.com", username="other")
    limit, _ = LOGIN_FAILS_PER_EMAIL
    for _ in range(limit):
        login(client)
    assert login(client, email="other@example.com", password=PASSWORD).status_code == 200


def test_email_case_does_not_bypass_the_lock(client, clock):
    register(client)
    limit, _ = LOGIN_FAILS_PER_EMAIL
    for i in range(limit):
        login(client, email="HTET@example.com" if i % 2 else "htet@example.com")
    assert login(client, email="Htet@Example.com", password=PASSWORD).status_code == 429


def test_unknown_email_is_limited_the_same_way(client, clock):
    """Otherwise the limit would reveal which emails have accounts."""
    limit, _ = LOGIN_FAILS_PER_EMAIL
    for _ in range(limit):
        assert login(client, email="nobody@example.com").status_code == 401
    assert login(client, email="nobody@example.com").status_code == 429


# --- Login: all attempts per network address ---


def test_many_logins_from_one_address_are_limited(client, clock):
    limit, _ = LOGIN_PER_IP
    for i in range(limit):
        # A different email each time, so the per-email lock never triggers.
        assert login(client, email=f"user{i}@example.com").status_code == 401
    blocked = login(client, email="new@example.com")
    assert blocked.status_code == 429
    assert error_code(blocked) == "too_many_requests"


# --- Sign up ---


def test_many_signups_from_one_address_are_limited(client, clock):
    limit, window = REGISTER_PER_IP
    for i in range(limit):
        register(client, email=f"user{i}@example.com", username=f"user{i}")
    blocked = client.post(f"{API}/auth/register", json={"email": "x@example.com", "username": "xuser", "password": PASSWORD})
    assert blocked.status_code == 429
    assert error_code(blocked) == "too_many_requests"

    clock.now += window + 1
    register(client, email="x@example.com", username="xuser")  # allowed again after the window


# --- The limiter itself ---


def test_memory_stays_bounded(monkeypatch):
    monkeypatch.setattr(rate_limit, "MAX_KEYS", 100)
    small = RateLimiter(clock=lambda: 0.0)
    for i in range(1000):
        small.record(f"key{i}", 60)
    assert len(small._hits) <= 100
