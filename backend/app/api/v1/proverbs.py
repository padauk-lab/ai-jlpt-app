"""Contract endpoint #12: proverb of the day (docs/api-contract.md, Section 2).

Kept in its own file so it doesn't overlap with the session and unit work in dashboard.py.
"""

from datetime import date
from typing import Any

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.errors import ApiError
from app.models import Proverb
from app.plan import service

router = APIRouter(tags=["2. Dashboard, sessions and units"])

FIRST_DAY = date(2026, 1, 1)  # day 0 of the rotation; any fixed date works


def proverb_for(day: date, proverb_ids: list[int]) -> int:
    """The same proverb for everyone on the same day, moving to the next one every day."""
    return proverb_ids[(day - FIRST_DAY).days % len(proverb_ids)]


@router.get("/proverbs/today", summary="#12 Proverb of the day")
def get_proverb_today(user: CurrentUser, db: DbSession) -> dict[str, Any]:
    ids = list(db.scalars(select(Proverb.id).where(Proverb.is_active.is_(True)).order_by(Proverb.id)))
    if not ids:
        raise ApiError(404, "not_found", "No proverb yet.")
    proverb = db.get(Proverb, proverb_for(service.today(), ids))
    return {
        "id": proverb.id,
        "ruby": proverb.ruby,
        "meaning_my": proverb.meaning_my,
        "explanation_my": proverb.explanation_my,
    }
