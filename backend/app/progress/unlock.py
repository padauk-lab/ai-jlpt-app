"""Unlock rules: what a user may open, decided only by the server (contract Section 2).

The rules:
1. Session 1 is open. Every next session opens after the mock test of the previous one is submitted (any score).
2. Units open in order. Units 6 to 10 also need Quiz 1 passed.
3. Quiz 1 opens after units 1 to 5 are done. Quiz 2 opens after units 6 to 10 are done.
4. The mock test opens after Quiz 2 is passed.
Everything counts only in the user's current round (a progress reset starts a new round).

The rules are plain functions over "facts", with no database, so they are easy to test.
load_session_facts() collects the facts from the database. Before that, it submits mock test
attempts whose time is up (see progress/mock.py), so the facts never show a finished test as running.
"""

from dataclasses import dataclass, field

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import MockAttempt, MockTest, Quiz, QuizAttempt, StudySession, Unit, UnitProgress, User
from app.progress import mock as mock_clock

UNITS_PER_SESSION = 10


@dataclass(frozen=True)
class QuizFacts:
    id: int
    number: int  # 1 or 2
    first_unit: int
    last_unit: int
    best_score: int | None  # percent, finished attempts only
    passed: bool
    finished_attempts: int


@dataclass(frozen=True)
class MockFacts:
    id: int
    submitted_attempts: int
    best_score: int | None  # percent
    last_score: int | None  # percent
    in_progress: bool


@dataclass(frozen=True)
class SessionFacts:
    id: int
    number: int
    unlocked: bool
    units: list[tuple[int, int]]  # (unit id, unit number), sorted by number
    completed: set[int] = field(default_factory=set)  # unit numbers done in this round
    quizzes: dict[int, QuizFacts] = field(default_factory=dict)  # by quiz number
    mock: MockFacts | None = None


# --- The rules (no database) ---


def quiz_passed(facts: SessionFacts, number: int) -> bool:
    quiz = facts.quizzes.get(number)
    return quiz is not None and quiz.passed


def _all_done(facts: SessionFacts, first: int, last: int) -> bool:
    return all(n in facts.completed for n in range(first, last + 1))


def unit_status(facts: SessionFacts, number: int) -> str:
    if number in facts.completed:
        return "completed"
    if not facts.unlocked or not _all_done(facts, 1, number - 1):
        return "locked"
    if number > 5 and not quiz_passed(facts, 1):
        return "locked"
    return "available"


def quiz_status(facts: SessionFacts, quiz: QuizFacts) -> str:
    if not facts.unlocked or not _all_done(facts, quiz.first_unit, quiz.last_unit):
        return "locked"
    if quiz.number == 2 and not quiz_passed(facts, 1):
        return "locked"
    if quiz.passed:
        return "passed"
    if quiz.finished_attempts > 0:
        return "failed"
    return "available"


def mock_status(facts: SessionFacts) -> str:
    if facts.mock is None or not facts.unlocked or not quiz_passed(facts, 2):
        return "locked"
    if facts.mock.in_progress:
        return "in_progress"
    if facts.mock.submitted_attempts > 0:
        return "completed"
    return "available"


# --- Collecting the facts from the database ---


def _percent(correct, total):
    return func.round(correct * 100.0 / func.nullif(total, 0))


def mock_submitted(db: Session, user: User, session_id: int) -> bool:
    """Has the user submitted this session's mock test in the current round?"""
    mock_test_id = db.scalar(select(MockTest.id).where(MockTest.session_id == session_id))
    if mock_test_id is not None:
        mock_clock.submit_expired(db, user.id, mock_test_id)  # time up counts as submitted
    query = (
        select(MockAttempt.id)
        .join(MockTest, MockTest.id == MockAttempt.mock_test_id)
        .where(
            MockTest.session_id == session_id,
            MockAttempt.user_id == user.id,
            MockAttempt.round == user.current_round,
            MockAttempt.submitted_at.is_not(None),
        )
        .limit(1)
    )
    return db.scalar(query) is not None


def session_unlocked(db: Session, user: User, session: StudySession) -> bool:
    if session.number == 1:
        return True
    previous_id = db.scalar(select(StudySession.id).where(StudySession.number == session.number - 1))
    return previous_id is not None and mock_submitted(db, user, previous_id)


def load_session_facts(db: Session, user: User, session: StudySession) -> SessionFacts:
    units = [(row.id, row.number) for row in db.execute(
        select(Unit.id, Unit.number).where(Unit.session_id == session.id).order_by(Unit.number)
    )]
    completed = set(db.scalars(
        select(Unit.number)
        .join(UnitProgress, UnitProgress.unit_id == Unit.id)
        .where(Unit.session_id == session.id, UnitProgress.user_id == user.id, UnitProgress.round == user.current_round)
    ))

    quizzes: dict[int, QuizFacts] = {}
    for quiz in db.scalars(select(Quiz).where(Quiz.session_id == session.id)):
        stats = db.execute(
            select(
                func.max(QuizAttempt.score),
                func.coalesce(func.bool_or(QuizAttempt.passed), False),
                func.count(QuizAttempt.id),
            ).where(
                QuizAttempt.quiz_id == quiz.id,
                QuizAttempt.user_id == user.id,
                QuizAttempt.round == user.current_round,
                QuizAttempt.finished_at.is_not(None),
            )
        ).one()
        quizzes[quiz.number] = QuizFacts(quiz.id, quiz.number, quiz.first_unit, quiz.last_unit, stats[0], bool(stats[1]), stats[2])

    mock = None
    mock_test = db.scalar(select(MockTest).where(MockTest.session_id == session.id))
    if mock_test is not None:
        mock_clock.submit_expired(db, user.id, mock_test.id)  # an attempt whose time is up is not "in progress"
        mine = (
            MockAttempt.mock_test_id == mock_test.id,
            MockAttempt.user_id == user.id,
            MockAttempt.round == user.current_round,
        )
        submitted = MockAttempt.submitted_at.is_not(None)
        count, best, open_count = db.execute(
            select(
                func.count(MockAttempt.id).filter(submitted),
                func.max(_percent(MockAttempt.correct, MockAttempt.total)).filter(submitted),
                func.count(case((MockAttempt.submitted_at.is_(None), 1))),
            ).where(*mine)
        ).one()
        last = db.scalar(
            select(_percent(MockAttempt.correct, MockAttempt.total))
            .where(*mine, submitted)
            .order_by(MockAttempt.submitted_at.desc())
            .limit(1)
        )
        mock = MockFacts(
            mock_test.id, count, int(best) if best is not None else None, int(last) if last is not None else None, open_count > 0
        )

    return SessionFacts(
        id=session.id,
        number=session.number,
        unlocked=session_unlocked(db, user, session),
        units=units,
        completed=completed,
        quizzes=quizzes,
        mock=mock,
    )
