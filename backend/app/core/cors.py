"""CORS: which web pages may call this API from a browser.

A browser blocks a page on one address (the web app, e.g. http://localhost:8081) from reading
answers from another address (this API, http://localhost:8000) unless the API says it trusts that page.
The phone apps are not browsers, so CORS does not affect them.

The trusted addresses come from CORS_ORIGINS in .env, comma separated. Empty means no web page is trusted.
"*" (trust everyone) is refused on purpose.
"""

from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import _unexpected_error

# Plain http is only allowed for your own computer. Every real address must use https.
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _clean_origin(origin: str) -> str:
    """Check one address and return it the way a browser sends it (lowercase, no default port)."""
    parts = urlsplit(origin)
    scheme = parts.scheme.lower()
    host = parts.hostname  # already lowercase
    if scheme not in ("http", "https") or not host:
        raise RuntimeError(f"CORS_ORIGINS: {origin!r} must look like https://app.example.com or http://localhost:8081")
    if parts.path or parts.query or parts.fragment or parts.username or parts.password:
        raise RuntimeError(f"CORS_ORIGINS: {origin!r} must be only scheme, host and port, with no '/' at the end")
    try:
        port = parts.port  # a port that is not a number from 0 to 65535 raises ValueError
    except ValueError:
        raise RuntimeError(f"CORS_ORIGINS: {origin!r} has an invalid port") from None
    if scheme == "http" and host not in LOCAL_HOSTS:
        raise RuntimeError(f"CORS_ORIGINS: {origin!r} must use https. Plain http is only for localhost")

    shown_host = f"[{host}]" if ":" in host else host  # IPv6 addresses are written in brackets
    default_port = 80 if scheme == "http" else 443
    return f"{scheme}://{shown_host}" if port in (None, default_port) else f"{scheme}://{shown_host}:{port}"


def parse_origins(value: str) -> list[str]:
    """Turn "http://localhost:8081, https://app.example.com" into a checked list.

    Stops the server with a clear message when a value is wrong, so a typo is found at start-up
    instead of as a confusing "blocked by CORS" error in the browser later.
    """
    origins: list[str] = []
    for raw in value.split(","):
        origin = raw.strip()
        if not origin:
            continue
        if origin == "*":
            raise RuntimeError("CORS_ORIGINS must list exact addresses. '*' (trust every website) is not allowed.")
        cleaned = _clean_origin(origin)
        if cleaned not in origins:
            origins.append(cleaned)
    return origins


class _ServerErrorsInsideCors:
    """Turns an unexpected crash into our normal 500 answer INSIDE the CORS layer.

    Without this, the 500 is made outside CORS, has no CORS headers, and the browser shows
    a misleading "CORS error" instead of the real 500.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False

        async def send_and_watch(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, send_and_watch)
        except Exception as exc:
            if started:  # part of the answer is already sent, nothing better we can do
                raise
            response = await _unexpected_error(Request(scope), exc)  # logs the details, sends the safe message
            await response(scope, receive, send)


def add_cors(app: FastAPI, value: str) -> None:
    """Trust the addresses in value (the CORS_ORIGINS text). Does nothing when it is empty."""
    origins = parse_origins(value)
    if not origins:
        return
    # Added first, so it sits inside the CORS layer (the last middleware added is the outermost).
    app.add_middleware(_ServerErrorsInsideCors)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        # We send the login token in the Authorization header, not in cookies, so cookies stay off.
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        # Lets the app read how long to wait after 429 "too many requests".
        expose_headers=["Retry-After"],
        max_age=600,
    )
