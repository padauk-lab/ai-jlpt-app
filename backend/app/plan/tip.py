"""The AI study tip on the plan (contract #10, field ai_tip_my), written by SWYH's plan_tip().

When a tip is made:
- After the plan is created or changed (#9 setup, #29 study settings, #37 reset), after db.commit(),
  so a slow or failing AI can never stop the plan from being saved.
- When #10 is opened and the plan has no tip yet (for example the AI failed last time).
  At most once an hour per user, so a broken AI is not asked again and again.

How long the user waits: at most TIP_WAIT_SECONDS. The plan screen shows the ox cart meanwhile.
If the AI is slower, the plan is answered without the tip (null), and the tip is saved when it
arrives, so it shows the next time the plan is opened. A tip is only saved if the plan has not
changed in the meantime, so an old tip never lands on a new plan.
"""

import logging
import time
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as WaitTimeout
from datetime import datetime
from threading import Lock
from typing import Any

from sqlalchemy import update

from app.ai import tips
from app.models import Plan

logger = logging.getLogger(__name__)

TIP_WAIT_SECONDS = 8
RETRY_AFTER_SECONDS = 60 * 60

_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="plan-tip")
_lock = Lock()
_running: dict[int, Future] = {}  # user id -> tip being written
_last_try: dict[int, float] = {}  # user id -> when we last asked the AI (time.monotonic)


def ai_tip(plan_json: dict[str, Any], last_level: str) -> str:
    """SWYH's plan_tip(). A separate name, so tests can replace it without touching SWYH's own tests."""
    return tips.plan_tip(plan_json, last_level)


def _write_and_save(user_id: int, plan_json: dict[str, Any], last_level: str, plan_version: datetime) -> str | None:
    """Ask the AI and save the tip. Runs in a background thread with its own database session."""
    from app.db import SessionLocal

    try:
        tip = ai_tip(plan_json, last_level)
    except Exception as error:  # AI down, no key, bad answer: the plan simply has no tip
        logger.warning("Plan tip not written: %s", type(error).__name__)
        return None
    with SessionLocal() as db, db.begin():
        saved = db.execute(
            update(Plan)
            .where(Plan.user_id == user_id, Plan.updated_at == plan_version)  # the plan didn't change meanwhile
            .values(ai_tip_my=tip, updated_at=Plan.updated_at)  # a new tip is not a new plan
        ).rowcount
    return tip if saved else None  # never show a tip that belongs to an older plan


def request_tip(user_id: int, plan_json: dict[str, Any], last_level: str, plan_version: datetime, wait: bool) -> str | None:
    """Start writing a tip (once per user at a time). With wait=True, wait up to TIP_WAIT_SECONDS for it."""
    with _lock:
        future = _running.get(user_id)
        if future is None or future.done():
            _last_try[user_id] = time.monotonic()
            future = _pool.submit(_write_and_save, user_id, plan_json, last_level, plan_version)
            _running[user_id] = future
    if not wait:
        return None
    try:
        return future.result(timeout=TIP_WAIT_SECONDS)
    except WaitTimeout:
        return None  # still writing: it is saved when it arrives


def may_retry(user_id: int) -> bool:
    """True if this user's tip may be asked for again (not asked in the last hour, none running)."""
    with _lock:
        future = _running.get(user_id)
        if future is not None and not future.done():
            return False
        last = _last_try.get(user_id)
        return last is None or time.monotonic() - last >= RETRY_AFTER_SECONDS


def reset_for_tests() -> None:
    with _lock:
        _running.clear()
        _last_try.clear()
