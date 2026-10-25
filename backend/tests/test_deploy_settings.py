"""Settings for running online (docs/deploy.md): the real user address behind Render's proxy, and database URLs."""

import pytest
from starlette.requests import Request

from app.core.rate_limit import client_ip
from app.db import _database_url


def request(forwarded: str | None, peer: str = "10.9.8.7") -> Request:
    headers = [(b"x-forwarded-for", forwarded.encode())] if forwarded is not None else []
    return Request({"type": "http", "headers": headers, "client": (peer, 1234)})


def test_on_our_computers_the_header_is_ignored(monkeypatch):
    monkeypatch.delenv("PROXY_HOPS", raising=False)
    assert client_ip(request("1.2.3.4")) == "10.9.8.7"  # anyone could fake the header


def test_behind_one_proxy_the_last_address_is_used(monkeypatch):
    monkeypatch.setenv("PROXY_HOPS", "1")
    assert client_ip(request("203.0.113.5")) == "203.0.113.5"


def test_fake_addresses_at_the_start_are_ignored(monkeypatch):
    monkeypatch.setenv("PROXY_HOPS", "1")
    # The user sent "6.6.6.6, 7.7.7.7"; the proxy added the real address at the end.
    assert client_ip(request("6.6.6.6, 7.7.7.7, 203.0.113.5")) == "203.0.113.5"


def test_two_proxies(monkeypatch):
    monkeypatch.setenv("PROXY_HOPS", "2")
    assert client_ip(request("6.6.6.6, 203.0.113.5, 198.51.100.1")) == "203.0.113.5"


def test_missing_header_falls_back_to_the_connection(monkeypatch):
    monkeypatch.setenv("PROXY_HOPS", "1")
    assert client_ip(request(None)) == "10.9.8.7"
    assert client_ip(request("")) == "10.9.8.7"


def test_bad_setting_stops_with_a_clear_message(monkeypatch):
    monkeypatch.setenv("PROXY_HOPS", "yes")
    with pytest.raises(RuntimeError, match="PROXY_HOPS"):
        client_ip(request("1.2.3.4"))


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("postgresql://u:p@db:5432/jlpt", "postgresql+psycopg://u:p@db:5432/jlpt"),
        ("postgres://u:p@ep-x.neon.tech/jlpt?sslmode=require", "postgresql+psycopg://u:p@ep-x.neon.tech/jlpt?sslmode=require"),
        ("postgresql+psycopg://u:p@db/jlpt", "postgresql+psycopg://u:p@db/jlpt"),
    ],
)
def test_database_urls_from_any_host_work(monkeypatch, given, expected):
    monkeypatch.setenv("DATABASE_URL", given)
    assert _database_url() == expected
