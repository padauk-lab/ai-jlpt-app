"""#27 POST /ai/examples: the "More examples" button (docs/api-contract.md).

How one tap works:
1. Find the word or grammar pattern. Its unit must be open for this user (403 otherwise).
2. Take one tap from today's allowance (default 50 a day, the AI_EXAMPLES_DAILY_LIMIT setting).
   "Today" is the user's own day, in the timezone from their notification settings.
   The tap is counted BEFORE calling the AI, in one database step, so fast repeated taps can't go over the limit.
3. Ask SWYH's generate_examples() with our checked content (the app sends only ids).
   No database connection is held while waiting for the AI.
4. If the AI fails: the tap is given back and the user sees "try again later" (503).

These examples are not saved: each tap gives fresh sentences, which is the point of the button.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Annotated, Any, Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.ai import examples as ai_examples
from app.ai.llm import AIUnavailableError
from app.api.deps import CurrentUser, DbSession
from app.core.errors import ApiError
from app.models import AIUsage, Example, Grammar, NotificationSettings, StudySession, Unit, User, Word
from app.progress import unlock

router = APIRouter(tags=["4. AI and settings"])
logger = logging.getLogger(__name__)

DEFAULT_DAILY_LIMIT = 50
DEFAULT_TIMEZONE = "Asia/Tokyo"


def daily_limit() -> int:
    """A server setting, so the team can change it without changing code."""
    return int(os.environ.get("AI_EXAMPLES_DAILY_LIMIT", DEFAULT_DAILY_LIMIT))


def now() -> datetime:
    """Tests replace this to move the clock."""
    return datetime.now(ZoneInfo("UTC"))


class ExamplesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_type: Literal["word", "grammar"]
    item_id: Annotated[int, Field(strict=True, ge=1, le=9_223_372_036_854_775_807)]


def _item(db: DbSession, body: ExamplesRequest) -> tuple[Word | Grammar, Unit]:
    item = db.get(Word if body.item_type == "word" else Grammar, body.item_id)
    if item is None:
        raise ApiError(404, "not_found", "Word or grammar pattern not found.")
    return item, db.get(Unit, item.unit_id)


def _user_now(db: DbSession, user: User) -> datetime:
    """The current time in the user's own timezone, so "today" ends at their midnight."""
    settings = db.get(NotificationSettings, user.id)
    return now().astimezone(ZoneInfo(settings.timezone if settings else DEFAULT_TIMEZONE))


def _take_one_tap(db: DbSession, user: User, day, limit: int) -> int | None:
    """Count one tap for today. Returns the new count, or None if the limit was already reached.

    One INSERT ... ON CONFLICT statement: two taps at the same moment can't both slip under the limit.
    """
    stmt = insert(AIUsage).values(user_id=user.id, usage_date=day, examples_count=1)
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "usage_date"],
        set_={"examples_count": AIUsage.examples_count + 1},
        where=AIUsage.examples_count < limit,
    ).returning(AIUsage.examples_count)
    return db.execute(stmt).scalar()


def _give_back_one_tap(db: DbSession, user: User, day) -> None:
    db.execute(
        update(AIUsage)
        .where(AIUsage.user_id == user.id, AIUsage.usage_date == day, AIUsage.examples_count > 0)
        .values(examples_count=AIUsage.examples_count - 1)
    )
    db.commit()


@router.post("/ai/examples", summary="#27 More examples (AI)")
def more_examples(body: ExamplesRequest, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    item, unit = _item(db, body)
    facts = unlock.load_session_facts(db, user, db.get(StudySession, unit.session_id))
    if unlock.unit_status(facts, unit.number) == "locked":
        raise ApiError(403, "unit_locked", "This unit is locked.")

    # Everything the AI needs, read now, so nothing is loaded from the database while it works.
    existing = [
        "".join(piece["text"] for piece in e.ruby)
        for e in db.scalars(select(Example).where(
            Example.word_id == item.id if body.item_type == "word" else Example.grammar_id == item.id
        ))
    ]
    if body.item_type == "word":
        target, target_ruby = item.word, item.ruby
    else:
        target, target_ruby = item.pattern, None
    meaning_my = item.meaning_my

    user_now = _user_now(db, user)
    today = user_now.date()
    limit = daily_limit()
    used = _take_one_tap(db, user, today, limit)
    if used is None:
        db.rollback()
        midnight = datetime.combine(today + timedelta(days=1), datetime.min.time(), tzinfo=user_now.tzinfo)
        wait = max(1, int((midnight - user_now).total_seconds()))
        raise ApiError(429, "daily_limit_reached", "You used all of today's examples. Try again tomorrow.",
                       headers={"Retry-After": str(wait)})
    db.commit()  # the tap is counted, and no database connection waits on the AI

    try:
        examples = ai_examples.generate_examples(body.item_type, target, meaning_my, existing, target_ruby)
    except AIUnavailableError as exc:
        logger.warning("More examples failed for %s %s: %s", body.item_type, body.item_id, exc)
        _give_back_one_tap(db, user, today)  # a failed try doesn't use up the allowance
        raise ApiError(503, "ai_unavailable", "The AI is busy. Please try again later.") from None

    return {
        "item_type": body.item_type,
        "item_id": body.item_id,
        "examples": examples,
        "remaining_today": max(0, limit - used),
    }
