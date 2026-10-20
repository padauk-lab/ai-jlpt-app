"""CORS: which web pages may call this API from a browser.

A browser blocks a page on one address (the web app, e.g. http://localhost:8081) from reading
answers from another address (this API, http://localhost:8000) unless the API says it trusts that page.
The phone apps are not browsers, so CORS does not affect them.

The trusted addresses come from CORS_ORIGINS in .env, comma separated. Empty means no web page is trusted.
"*" (trust everyone) is refused on purpose.
"""

from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Plain http is only allowed for your own computer. Every real address must use https.
LOCAL_HOSTS = {"localhost", "127.0.0.1"}


def parse_origins(value: str) -> list[str]:
    """Turn "http://localhost:8081, https://app.example.com" into a checked list.

    Stops the server with a clear message when a value is wrong, so a typo is found at start-up
    instead of as a confusing "blocked by CORS" error in the browser later.
    """
    origins = []
    for raw in value.split(","):
        origin = raw.strip()
        if not origin:
            continue
        if origin == "*":
            raise RuntimeError("CORS_ORIGINS must list exact addresses. '*' (trust every website) is not allowed.")
        parts = urlsplit(origin)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise RuntimeError(f"CORS_ORIGINS: {origin!r} must look like https://app.example.com or http://localhost:8081")
        if parts.path or parts.query or parts.fragment or parts.username or parts.password:
            raise RuntimeError(f"CORS_ORIGINS: {origin!r} must be only scheme, host and port, with no '/' at the end")
        if parts.scheme == "http" and parts.hostname not in LOCAL_HOSTS:
            raise RuntimeError(f"CORS_ORIGINS: {origin!r} must use https. Plain http is only for localhost")
        if origin not in origins:
            origins.append(origin)
    return origins


def add_cors(app: FastAPI, value: str) -> None:
    """Trust the addresses in value (the CORS_ORIGINS text). Does nothing when it is empty."""
    origins = parse_origins(value)
    if not origins:
        return
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
