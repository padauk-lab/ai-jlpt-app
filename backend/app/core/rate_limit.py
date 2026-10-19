"""Rate limiting: stop password guessing and mass sign-ups.

How it works: for each key (for example "login-ip:1.2.3.4") we remember the times of recent attempts.
If there are too many inside the time window, the request is refused with 429 and a Retry-After header.

Limits are kept in this server's memory:
- Simple and needs no extra service.
- Counts reset when the server restarts, and are not shared between several server processes.
  When we run more than one process in production, move this to a shared store (for example Redis).
"""

import time
from collections import deque
from collections.abc import Callable
from math import ceil
from threading import Lock

from fastapi import Request

from app.core.errors import ApiError

# (max attempts, window in seconds)
LOGIN_PER_IP = (30, 5 * 60)  # all login attempts from one network
LOGIN_FAILS_PER_EMAIL = (5, 15 * 60)  # wrong passwords for one email; a successful login clears it
REGISTER_PER_IP = (20, 60 * 60)  # sign-ups from one network

MAX_KEYS = 50_000  # memory guard: an attacker sending many different emails can't fill the memory


class RateLimiter:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self.clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = Lock()  # requests run in parallel threads

    def _recent(self, key: str, window: int) -> deque[float]:
        """Attempts for this key inside the window (older ones are forgotten)."""
        hits = self._hits.get(key, deque())
        cutoff = self.clock() - window
        while hits and hits[0] <= cutoff:
            hits.popleft()
        return hits

    def check(self, key: str, limit: int, window: int) -> None:
        """Refuse with 429 if the key already used up its attempts. Does not count this request."""
        with self._lock:
            hits = self._recent(key, window)
            if len(hits) >= limit:
                raise too_many_requests(ceil(hits[0] + window - self.clock()))

    def record(self, key: str, window: int) -> None:
        """Count one attempt for this key."""
        with self._lock:
            hits = self._recent(key, window)
            if key not in self._hits and len(self._hits) >= MAX_KEYS:
                self._forget_oldest()
            hits.append(self.clock())
            self._hits[key] = hits

    def hit(self, key: str, limit: int, window: int) -> None:
        """check() and then record(): for limits that count every attempt."""
        self.check(key, limit, window)
        self.record(key, window)

    def clear(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def reset(self) -> None:
        """Forget everything. Used by the tests."""
        with self._lock:
            self._hits.clear()

    def _forget_oldest(self) -> None:
        # Drop the oldest tenth of the keys. Dicts keep insertion order, so the first keys are the oldest.
        for key in list(self._hits)[: MAX_KEYS // 10]:
            del self._hits[key]


def too_many_requests(wait_seconds: int) -> ApiError:
    wait_seconds = max(1, wait_seconds)
    minutes = ceil(wait_seconds / 60)
    return ApiError(
        429,
        "too_many_requests",
        f"Too many attempts. Please try again in {minutes} minute{'s' if minutes > 1 else ''}.",
        headers={"Retry-After": str(wait_seconds)},
    )


def client_ip(request: Request) -> str:
    # We use the direct connection address. We do NOT trust the X-Forwarded-For header,
    # because anyone can fake it. When we put a proxy in front of the server, configure it there.
    return request.client.host if request.client else "unknown"


limiter = RateLimiter()
