"""Sending push notifications through the Expo push service.

PUSH_MODE (in .env):
- "off" (default): nothing is sent and the reminder loop doesn't run. Tests and normal coding.
- "log": the reminder loop runs, but notifications are only written to the backend log. For testing.
- "expo": real notifications through https://exp.host (the Expo push service, free).

EXPO_ACCESS_TOKEN is optional: only needed if "enhanced push security" is turned on in the Expo account.
Sending errors never crash the backend: they are logged, and the next reminder is tomorrow.
"""

import json
import logging
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
BATCH_SIZE = 100  # Expo accepts at most 100 messages per request
TIMEOUT_SECONDS = 15
# Expo push tokens look like ExponentPushToken[xxxx] (or ExpoPushToken[xxxx]).
EXPO_TOKEN = re.compile(r"^Expo(nent)?PushToken\[[A-Za-z0-9_-]{1,200}\]$")


@dataclass
class PushMessage:
    to: str
    title: str
    body: str
    data: dict = field(default_factory=dict)


def push_mode() -> str:
    mode = os.environ.get("PUSH_MODE", "off").strip().lower()
    return mode if mode in {"off", "log", "expo"} else "off"


def is_expo_token(token: str) -> bool:
    return bool(EXPO_TOKEN.match(token))


def send_push(messages: list[PushMessage]) -> set[str]:
    """Send the messages. Returns the tokens Expo says are dead (the app was deleted, for example),
    so the caller can remove those devices."""
    mode = push_mode()
    if mode == "off" or not messages:
        return set()
    if mode == "log":
        for m in messages:
            # Only the end of the token, so the log never holds a full token.
            logger.warning("Push NOT sent (PUSH_MODE=log) to ...%s: %s / %s", m.to[-8:], m.title, m.body)
        return set()

    dead: set[str] = set()
    for start in range(0, len(messages), BATCH_SIZE):
        dead |= _send_batch(messages[start:start + BATCH_SIZE])
    return dead


def _send_batch(batch: list[PushMessage]) -> set[str]:
    payload = [{"to": m.to, "title": m.title, "body": m.body, "data": m.data, "sound": "default"} for m in batch]
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    access_token = os.environ.get("EXPO_ACCESS_TOKEN", "")
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    request = urllib.request.Request(EXPO_PUSH_URL, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            tickets = json.loads(response.read()).get("data", [])
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        logger.warning("Push sending failed for %d message(s): %s", len(batch), error)
        return set()

    dead: set[str] = set()
    for message, ticket in zip(batch, tickets if isinstance(tickets, list) else [], strict=False):
        if not isinstance(ticket, dict) or ticket.get("status") == "ok":
            continue
        error_code = (ticket.get("details") or {}).get("error")
        if error_code == "DeviceNotRegistered":
            dead.add(message.to)
        else:
            logger.warning("Push refused by Expo: %s", error_code or ticket.get("message"))
    return dead
