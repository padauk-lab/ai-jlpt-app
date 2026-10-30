"""Study plan with the database: save the plan and build the JSON the app sees.

Used by #9 POST /onboarding, #10 GET /plan, #29 study settings and #37 reset.
The math itself lives in calculator.py and has no database, so it stays easy to test.
"""

from datetime import UTC, date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Plan, StudySettings, UnitProgress, User
from app.plan import tip
from app.plan.calculator import UNITS_TOTAL, calculate_plan

# "Today" is the date in Japan, where the JLPT is held. Japan has no summer time, so a fixed +9 is exact.
JAPAN_TIME = timezone(timedelta(hours=9), "JST")


def today() -> date:
    return datetime.now(JAPAN_TIME).date()


def count_units_done(db: Session, user: User) -> int:
    """Units done in the user's current round (a progress reset starts a new round)."""
    query = select(func.count()).select_from(UnitProgress).where(
        UnitProgress.user_id == user.id,
        UnitProgress.round == user.current_round,
    )
    return db.scalar(query) or 0


def save_plan(db: Session, user: User, settings: StudySettings) -> Plan:
    """Recalculate the plan from the settings and progress, and save it (creates it the first time)."""
    numbers = calculate_plan(today(), settings.exam_date, settings.last_level, count_units_done(db, user))
    plan = db.get(Plan, user.id)
    if plan is None:
        plan = Plan(user_id=user.id)
        db.add(plan)
    plan.units_per_day = numbers.units_per_day
    plan.finish_by = numbers.finish_by
    return plan


def _utc_text(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def plan_json(db: Session, user: User, settings: StudySettings, plan: Plan) -> dict[str, Any]:
    """The plan in the contract's shape (#10). days_left and units_done are always fresh."""
    days_left = max(0, (settings.exam_date - today()).days) if settings.exam_date else None
    return {
        "exam_date": settings.exam_date.isoformat() if settings.exam_date else None,
        "days_left": days_left,
        "units_total": UNITS_TOTAL,
        "units_done": count_units_done(db, user),
        "units_per_day": plan.units_per_day,
        "finish_by": plan.finish_by.isoformat() if plan.finish_by else None,
        "ai_tip_my": plan.ai_tip_my,  # the AI's Burmese tip, or null (see tip.py)
        "updated_at": _utc_text(plan.updated_at),
    }


def plan_json_with_new_tip(db: Session, user: User, settings: StudySettings, plan: Plan) -> dict[str, Any]:
    """For #9, #29 and #37: call after db.commit() and db.refresh(plan). Writes a new tip for the new plan,
    waiting a few seconds for it (the app shows the loading cart meanwhile)."""
    data = plan_json(db, user, settings, plan)
    new_tip = tip.request_tip(user.id, data, settings.last_level, plan.updated_at, wait=True)
    if new_tip:
        data["ai_tip_my"] = new_tip
    return data


def plan_json_for_reading(db: Session, user: User, settings: StudySettings, plan: Plan) -> dict[str, Any]:
    """For #10: the plan as saved. If it has no tip yet, ask for one in the background (at most hourly)."""
    data = plan_json(db, user, settings, plan)
    if plan.ai_tip_my is None and tip.may_retry(user.id):
        tip.request_tip(user.id, data, settings.last_level, plan.updated_at, wait=False)
    return data
