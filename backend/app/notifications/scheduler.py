"""A small loop inside the backend that checks for due reminders once a minute.

Why inside the backend: a separate scheduled job costs money on Render, and UptimeRobot keeps the
free server awake anyway. It is safe with more than one server, because each reminder is claimed
in the database first (see reminders.py).

It only starts when PUSH_MODE is "log" or "expo", so tests and normal coding never send anything.
"""

import logging
import threading
from collections.abc import Callable

from app.notifications.push import push_mode

logger = logging.getLogger(__name__)

CHECK_EVERY_SECONDS = 60


def _run_once() -> None:
    from app.db import SessionLocal
    from app.notifications.reminders import send_due_reminders

    with SessionLocal() as db:
        count = send_due_reminders(db)
    if count:
        logger.info("Study reminders sent to %d user(s)", count)


def _loop(stop: threading.Event) -> None:
    while not stop.wait(CHECK_EVERY_SECONDS):
        try:
            _run_once()
        except Exception:  # one bad minute must never stop the loop
            logger.exception("Study reminder check failed")


def start_reminder_loop() -> Callable[[], None] | None:
    """Start the loop. Returns a function that stops it, or None when PUSH_MODE is off."""
    if push_mode() == "off":
        return None
    stop = threading.Event()
    thread = threading.Thread(target=_loop, args=(stop,), name="study-reminders", daemon=True)
    thread.start()
    logger.warning("Study reminder loop started (PUSH_MODE=%s)", push_mode())

    def stop_loop() -> None:
        stop.set()
        thread.join(timeout=5)

    return stop_loop
