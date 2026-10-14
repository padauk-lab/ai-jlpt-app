"""Study plan math: how many units per day until the exam.

Plain code, no AI and no database, so the numbers are always exact and easy to test.
The AI only writes the short tip (ai_tip_my), never these numbers.

The rules (answers open question #3 in docs/api-contract.md):
1. No exam date: a steady default pace of DEFAULT_UNITS_PER_DAY.
2. With an exam date, the last days before the exam are kept free for review and mock tests:
   - REVIEW_DAYS_N1 if the user already took N1 (they know the format)
   - REVIEW_DAYS_OTHER for N2 or "not taken" (more practice needed)
   Review never takes more than a third of the time left.
3. units per day = units left / study days, rounded UP, between 1 and MAX_UNITS_PER_DAY.
4. The score is saved but does not change the pace yet. We can tune this after real users try it.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil

UNITS_TOTAL = 200  # 20 sessions x 10 units
DEFAULT_UNITS_PER_DAY = 3
MAX_UNITS_PER_DAY = 20
REVIEW_DAYS_N1 = 7
REVIEW_DAYS_OTHER = 14


@dataclass(frozen=True)
class PlanNumbers:
    units_per_day: int
    days_left: int | None  # None when there is no exam date
    finish_by: date | None  # the day the last unit should be done


def calculate_plan(
    today: date,
    exam_date: date | None,
    last_level: str,
    units_done: int,
    units_total: int = UNITS_TOTAL,
) -> PlanNumbers:
    units_left = max(0, units_total - units_done)

    if exam_date is None:
        return PlanNumbers(units_per_day=DEFAULT_UNITS_PER_DAY, days_left=None, finish_by=None)

    days_left = (exam_date - today).days
    if units_left == 0:
        return PlanNumbers(units_per_day=1, days_left=max(0, days_left), finish_by=today)
    if days_left <= 0:
        # Exam day or later: no time to plan around. Show the fastest pace; the user can update the date.
        return PlanNumbers(units_per_day=min(MAX_UNITS_PER_DAY, units_left), days_left=0, finish_by=None)

    review_days = REVIEW_DAYS_N1 if last_level == "N1" else REVIEW_DAYS_OTHER
    review_days = min(review_days, days_left // 3)
    study_days = days_left - review_days

    units_per_day = min(MAX_UNITS_PER_DAY, max(1, ceil(units_left / study_days)))
    days_needed = ceil(units_left / units_per_day)
    finish_by = today + timedelta(days=days_needed - 1)  # today counts as day 1
    return PlanNumbers(units_per_day=units_per_day, days_left=days_left, finish_by=finish_by)
