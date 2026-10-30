"""Study plan tip (contract endpoint 10, field ai_tip_my): one short, friendly piece of advice in Burmese.

The numbers in the plan are calculated by backend code. The AI never does the math.
The tip is saved with the plan and shown for weeks, so it must not contain numbers
like "54 days left" that would soon be wrong. The AI gets only rough buckets,
and a tip with any digit is refused.
This file never touches the database. The route calls it after db.commit().
"""

import json
import re
from pathlib import Path
from typing import Any

from app.ai.llm import AIUnavailableError, generate_json
from app.content.schema import MYANMAR

PROMPT = (Path(__file__).parent / "prompts" / "tips.txt").read_text(encoding="utf-8")
MAX_LENGTH = 300
DIGITS = re.compile(r"[0-9０-９၀-၉]")         # western, full-width and Burmese digits


def _time_left(days_left: int | None) -> str:
    if days_left is None:
        return "no_exam_date"
    if days_left < 30:
        return "under_1_month"
    if days_left <= 90:
        return "1_to_3_months"
    return "over_3_months"


def _pace(units_per_day: int) -> str:
    if units_per_day <= 3:
        return "light"
    if units_per_day <= 7:
        return "normal"
    return "heavy"


def _progress(units_done: int, units_total: int) -> str:
    share = units_done / units_total if units_total else 0
    if share == 0:
        return "not_started"
    if share < 0.5:
        return "early"
    if share < 0.9:
        return "past_half"
    return "almost_done"


def _situation(plan: dict[str, Any], last_level: str) -> dict[str, str]:
    """Turn exact numbers into rough buckets, so the AI cannot copy a number into the tip."""
    return {
        "last_level": last_level,
        "time_left": _time_left(plan.get("days_left")),
        "pace": _pace(plan["units_per_day"]),
        "progress": _progress(plan["units_done"], plan["units_total"]),
    }


def _check_tip(raw: str) -> str:
    """Never trust the AI: the tip must be real Burmese text, short, and without numbers."""
    try:
        answer = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AIUnavailableError("AI answer is not valid JSON") from e
    tip = answer.get("tip_my") if isinstance(answer, dict) else None
    if not isinstance(tip, str) or not tip.strip():
        raise AIUnavailableError("AI answer has no tip")
    tip = tip.strip()
    if not MYANMAR.search(tip):
        raise AIUnavailableError("tip is not in Burmese")
    if DIGITS.search(tip):
        raise AIUnavailableError("tip contains a number, which would go stale")
    if len(tip) > MAX_LENGTH:
        raise AIUnavailableError("tip is too long")
    return tip


def plan_tip(plan: dict[str, Any], last_level: str) -> str:
    """Return a Burmese tip for a plan in the shape of contract endpoint 10.

    last_level is "N1", "N2" or "not_taken" (from the study settings).
    Raises AIUnavailableError if the AI fails; the route then keeps ai_tip_my as null.
    """
    if last_level not in ("N1", "N2", "not_taken"):
        raise ValueError("last_level must be N1, N2 or not_taken")
    user = json.dumps(_situation(plan, last_level), ensure_ascii=False)
    return _check_tip(generate_json(PROMPT, user))