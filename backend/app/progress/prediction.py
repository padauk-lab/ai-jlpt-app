"""Pass prediction: how likely the user is to pass JLPT N1, from their mock tests (0 to 100).

Agreed by HP and ANK (Oct 2026). The real N1 needs 100 of 180 points AND at least 19 of 60 in each
section. Our app has no listening, so we use Language Knowledge (vocabulary + grammar) and Reading.

1. Only first attempts count (retakes are for review), and only the latest 2 mock tests, so the
   prediction follows the user's progress instead of old results.
2. With 2 tests, the newer one weighs 60% and the older 40%. Done separately for Language Knowledge
   (LK) and Reading.
3. Score = 70% LK + 30% Reading. LK has many more questions (45 vs 8), so it is the steadier signal.
4. A 60% score means a 50% chance. Each point above or below moves it by 2.5. Kept between 5 and 95:
   a practice test can never promise a sure pass or a sure fail.
5. LK or Reading under 32% (about 19/60, the real section minimum) caps the chance at 15%, with a
   warning, because one weak section fails the real exam whatever the total.

The formula is plain functions over numbers, with no database, so it is easy to test and to explain.
"""

from dataclasses import dataclass
from fractions import Fraction
from math import floor

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import MockAnswer, MockAttempt, Question, User
from app.progress import mock as mock_clock

# Exact fractions, not floats: 59.8 must stay 59.8, not 59.79999, or the rounding goes wrong.
NEWER_WEIGHT = Fraction(6, 10)
LK_WEIGHT = Fraction(7, 10)
EVEN_SCORE = 60  # percent score that means a 50% chance
POINTS_PER_PERCENT = Fraction(5, 2)
LOWEST, HIGHEST = 5, 95
SECTION_MINIMUM = 32  # percent, about 19 of 60
CAP_WHEN_SECTION_LOW = 15


@dataclass(frozen=True)
class MockScore:
    """One mock test result, in percent (0 to 100, may have decimals)."""

    language_knowledge: Fraction | float
    reading: Fraction | float


@dataclass(frozen=True)
class Prediction:
    value: int  # 5 to 95
    warning: str | None  # None, "language_knowledge_low", "reading_low" or "both_low"


def _round(value: Fraction) -> int:
    return floor(value + 0.5)  # .5 rounds up, like the mock test percent


def predict(newest_first: list[MockScore]) -> Prediction | None:
    """The prediction from the latest tests (newest first). None when there is no test yet."""
    if not newest_first:
        return None
    scores = [(Fraction(t.language_knowledge), Fraction(t.reading)) for t in newest_first[:2]]
    if len(scores) == 1:
        lk, reading = scores[0]
    else:
        (newer_lk, newer_reading), (older_lk, older_reading) = scores
        lk = NEWER_WEIGHT * newer_lk + (1 - NEWER_WEIGHT) * older_lk
        reading = NEWER_WEIGHT * newer_reading + (1 - NEWER_WEIGHT) * older_reading

    score = LK_WEIGHT * lk + (1 - LK_WEIGHT) * reading
    chance = _round(50 + POINTS_PER_PERCENT * (score - EVEN_SCORE))
    chance = max(LOWEST, min(HIGHEST, chance))

    lk_low, reading_low = lk < SECTION_MINIMUM, reading < SECTION_MINIMUM
    warning = "both_low" if lk_low and reading_low else "language_knowledge_low" if lk_low else "reading_low" if reading_low else None
    if warning:
        chance = min(chance, CAP_WHEN_SECTION_LOW)
    return Prediction(value=chance, warning=warning)


# --- Reading the scores from the database ---


def _test_score(db: Session, attempt: MockAttempt) -> MockScore:
    is_reading = Question.part == "reading"
    correct = MockAnswer.selected_option_id == Question.correct_option_id
    totals = db.execute(
        select(
            func.count().filter(~is_reading),
            func.count().filter(is_reading),
        ).where(Question.mock_test_id == attempt.mock_test_id)
    ).one()
    rights = db.execute(
        select(
            func.count(case((correct & ~is_reading, 1))),
            func.count(case((correct & is_reading, 1))),
        )
        .select_from(MockAnswer)
        .join(Question, Question.id == MockAnswer.question_id)
        .where(MockAnswer.attempt_id == attempt.id)
    ).one()
    lk = Fraction(100 * rights[0], totals[0]) if totals[0] else Fraction(0)
    reading = Fraction(100 * rights[1], totals[1]) if totals[1] else lk  # a test without reading: use LK
    return MockScore(language_knowledge=lk, reading=reading)


def load_prediction(db: Session, user: User) -> Prediction | None:
    """The user's current prediction (current round). Submits attempts whose time is up first."""
    expired = db.scalars(
        select(MockAttempt.mock_test_id).where(
            MockAttempt.user_id == user.id,
            MockAttempt.submitted_at.is_(None),
            MockAttempt.ends_at <= mock_clock.now(),
        )
    ).all()
    for mock_test_id in set(expired):
        mock_clock.submit_expired(db, user.id, mock_test_id)

    latest = db.scalars(
        select(MockAttempt)
        .where(
            MockAttempt.user_id == user.id,
            MockAttempt.round == user.current_round,
            MockAttempt.counts_for_prediction.is_(True),
            MockAttempt.submitted_at.is_not(None),
        )
        .order_by(MockAttempt.submitted_at.desc(), MockAttempt.id.desc())
        .limit(2)
    ).all()
    return predict([_test_score(db, attempt) for attempt in latest])
