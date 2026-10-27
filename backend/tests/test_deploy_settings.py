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


def test_spaces_around_the_database_url_are_ignored(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "  postgresql://u:p@db/jlpt \n")
    assert _database_url() == "postgresql+psycopg://u:p@db/jlpt"


# --- CLIENT_IP_HEADER: a header the first proxy (Cloudflare) writes itself ---


def cf_request(cf: str | None, forwarded: str = "6.6.6.6, 203.0.113.5, 198.51.100.1", peer: str = "10.9.8.7") -> Request:
    headers = [(b"x-forwarded-for", forwarded.encode())]
    if cf is not None:
        headers.append((b"cf-connecting-ip", cf.encode()))
    return Request({"type": "http", "headers": headers, "client": (peer, 1234)})


@pytest.fixture
def no_ip_settings(monkeypatch):
    for name in ("CLIENT_IP_HEADER", "PROXY_HOPS", "DEBUG_CLIENT_IP"):
        monkeypatch.delenv(name, raising=False)


def test_client_ip_header_wins_when_set(monkeypatch, no_ip_settings):
    monkeypatch.setenv("CLIENT_IP_HEADER", "CF-Connecting-IP")
    monkeypatch.setenv("PROXY_HOPS", "1")
    assert client_ip(cf_request("203.0.113.9")) == "203.0.113.9"


def test_without_the_setting_the_header_is_never_trusted(monkeypatch, no_ip_settings):
    assert client_ip(cf_request("203.0.113.9")) == "10.9.8.7"  # anyone could send that header


@pytest.mark.parametrize("bad", [None, "", "not-an-address", "1.2.3.4.5"])
def test_missing_or_junk_header_falls_back_to_proxy_hops(monkeypatch, no_ip_settings, bad):
    monkeypatch.setenv("CLIENT_IP_HEADER", "cf-connecting-ip")
    monkeypatch.setenv("PROXY_HOPS", "2")
    assert client_ip(cf_request(bad)) == "203.0.113.5"


def test_ipv6_addresses_work(monkeypatch, no_ip_settings):
    monkeypatch.setenv("CLIENT_IP_HEADER", "cf-connecting-ip")
    assert client_ip(cf_request("2001:db8::1")) == "2001:db8::1"


def test_debug_log_shows_what_the_proxies_sent(monkeypatch, no_ip_settings, caplog):
    import logging

    from app.core import rate_limit

    monkeypatch.setattr(rate_limit.logger, "disabled", False)
    monkeypatch.setenv("DEBUG_CLIENT_IP", "1")
    with caplog.at_level(logging.WARNING, logger="app.core.rate_limit"):
        client_ip(cf_request("203.0.113.9"))
    assert "x-forwarded-for='6.6.6.6, 203.0.113.5, 198.51.100.1'" in caplog.text
    assert "cf-connecting-ip='203.0.113.9'" in caplog.text


def test_no_debug_log_normally(monkeypatch, no_ip_settings, caplog):
    import logging

    with caplog.at_level(logging.WARNING, logger="app.core.rate_limit"):
        client_ip(cf_request("203.0.113.9"))
    assert "DEBUG_CLIENT_IP" not in caplog.text


# --- /health answers uptime checkers ---


def test_health_answers_get_and_head(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.head("/health").status_code == 200
