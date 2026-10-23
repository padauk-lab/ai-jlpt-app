"""Mock test clock and scoring, shared by the mock test endpoints and the unlock rules.

The clock lives on the server: an attempt ends at ends_at, whatever the phone says.
"Submit automatically at 0" works without a background job: whenever an attempt is looked at
after its time is up, it is submitted here, at ends_at, with the answers saved so far.
That gives the same result as a job running exactly at 0, because answers can't change after ends_at.
"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import MockAnswer, MockAttempt, Question


def now() -> datetime:
    """The server's time. Tests replace this to move the clock."""
    return datetime.now(UTC)


def percent(correct: int, total: int) -> int:
    """Whole percent, .5 rounds up (the same as round() in PostgreSQL, used by the unlock rules)."""
    return (correct * 200 + total) // (2 * total) if total else 0


def total_questions(db: Session, mock_test_id: int) -> int:
    return db.scalar(select(func.count()).select_from(Question).where(Question.mock_test_id == mock_test_id)) or 0


def submit(db: Session, attempt: MockAttempt, by: str, at: datetime) -> None:
    """Score the attempt and close it. Unanswered questions count as wrong."""
    attempt.correct = db.scalar(
        select(func.count())
        .select_from(MockAnswer)
        .join(Question, Question.id == MockAnswer.question_id)
        .where(MockAnswer.attempt_id == attempt.id, MockAnswer.selected_option_id == Question.correct_option_id)
    ) or 0
    attempt.total = total_questions(db, attempt.mock_test_id)
    attempt.submitted_at = at
    attempt.submitted_by = by


def is_over(attempt: MockAttempt) -> bool:
    return attempt.submitted_at is None and attempt.ends_at <= now()


def submit_if_time_is_up(db: Session, attempt: MockAttempt) -> None:
    if is_over(attempt):
        submit(db, attempt, "timeout", attempt.ends_at)


def submit_expired(db: Session, user_id: int, mock_test_id: int) -> None:
    """Submit this user's attempts of this mock test whose time is up. Safe to call any time."""
    expired = db.scalars(
        select(MockAttempt).where(
            MockAttempt.user_id == user_id,
            MockAttempt.mock_test_id == mock_test_id,
            MockAttempt.submitted_at.is_(None),
            MockAttempt.ends_at <= now(),
        ).with_for_update()
    )
    for attempt in expired:
        submit(db, attempt, "timeout", attempt.ends_at)
    db.flush()
