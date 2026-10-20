"""CORS: only the web pages listed in CORS_ORIGINS may call the API from a browser."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.cors import add_cors, parse_origins
from app.core.errors import ApiError, register_error_handlers

WEB_APP = "http://localhost:8081"


def make_client(origins: str) -> TestClient:
    """A small app set up the same way as app.main, with one normal route and one 429 route."""
    app = FastAPI()
    register_error_handlers(app)
    add_cors(app, origins)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/busy")
    def busy() -> None:
        raise ApiError(429, "too_many_requests", "Please wait.", headers={"Retry-After": "30"})

    return TestClient(app)


def preflight(client: TestClient, origin: str, method: str = "POST", headers: str = "authorization,content-type"):
    """What the browser asks before a real request: "may this page send this?"."""
    return client.options(
        "/ping",
        headers={"Origin": origin, "Access-Control-Request-Method": method, "Access-Control-Request-Headers": headers},
    )


# --- Reading CORS_ORIGINS ---


def test_origins_are_read_from_comma_separated_text():
    text = " http://localhost:8081 , https://app.example.com,,http://localhost:8081"
    assert parse_origins(text) == ["http://localhost:8081", "https://app.example.com"]


def test_empty_means_no_web_page_is_trusted():
    assert parse_origins("") == []


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("*", "not allowed"),
        ("localhost:8081", "must look like"),
        ("ftp://localhost", "must look like"),
        ("http://localhost:8081/", "no '/' at the end"),
        ("https://app.example.com/login", "no '/' at the end"),
        ("http://app.example.com", "must use https"),
    ],
)
def test_bad_values_stop_the_server(value, message):
    with pytest.raises(RuntimeError, match=message):
        parse_origins(value)


# --- What the browser sees ---


def test_listed_web_page_is_allowed():
    client = make_client(WEB_APP)
    response = client.get("/ping", headers={"Origin": WEB_APP})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == WEB_APP


def test_preflight_allows_the_login_token_header():
    response = preflight(make_client(WEB_APP), WEB_APP)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == WEB_APP
    allowed = response.headers["access-control-allow-headers"].lower()
    assert "authorization" in allowed and "content-type" in allowed


def test_other_web_pages_are_not_trusted():
    client = make_client(WEB_APP)
    response = client.get("/ping", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in response.headers  # the browser blocks the page from reading it
    assert preflight(client, "https://evil.example.com").status_code == 400


def test_cookies_are_never_allowed():
    response = make_client(WEB_APP).get("/ping", headers={"Origin": WEB_APP})
    assert "access-control-allow-credentials" not in response.headers


def test_unlisted_methods_are_refused():
    assert preflight(make_client(WEB_APP), WEB_APP, method="PATCH").status_code == 400


def test_app_can_read_retry_after_on_429():
    response = make_client(WEB_APP).get("/busy", headers={"Origin": WEB_APP})
    assert response.status_code == 429
    assert response.headers["access-control-allow-origin"] == WEB_APP
    assert "retry-after" in response.headers["access-control-expose-headers"].lower()


def test_no_origins_means_no_cors_headers():
    response = make_client("").get("/ping", headers={"Origin": WEB_APP})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
