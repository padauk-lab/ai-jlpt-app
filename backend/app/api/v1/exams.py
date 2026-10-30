"""Section 3: Quiz and mock test. Contract endpoints #19 to #26 (docs/api-contract.md).

REAL: #19 to #22 (quiz) and #23 to #26 (mock test).

Security rules:
- Correct answers are NEVER sent before the user answers. Only #20 (after answering one question),
  #22, #25 and #26 (after finishing) include correct_option_id.
- A locked quiz can't be started (403), and an attempt can only be used by its owner (403).
- Each question can be answered once per attempt, and only questions that belong to the attempt.
- The score is calculated here on the server. The app never sends a score.
- The mock test clock is the server's: ends_at is set here, answers after it are refused, and an
  attempt whose time is up is submitted automatically with the answers saved so far (progress/mock.py).
"""

import random
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession, PathId
from app.core.errors import ApiError
from app.models import (
    MockAnswer,
    MockAttempt,
    MockTest,
    Question,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizAttemptQuestion,
    ReadingPassage,
    StudySession,
    User,
)
from app.progress import mock as mock_clock
from app.progress import unlock
from app.progress.prediction import load_prediction

router = APIRouter(tags=["3. Quiz and mock test"])

# --- Request shapes (what the app sends) ---


class AnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: Annotated[int, Field(strict=True, ge=1, le=9_223_372_036_854_775_807)]
    selected_option_id: Literal["a", "b", "c", "d"]


# --- Quiz helpers ---


def _utc_text(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _own_attempt(db: DbSession, user: User, attempt_id: int, lock: bool = False) -> QuizAttempt:
    """The user's own attempt. Locking the row makes answering and finishing happen one at a time."""
    attempt = db.get(QuizAttempt, attempt_id, with_for_update=lock, populate_existing=lock)
    if attempt is None:
        raise ApiError(404, "not_found", "Quiz attempt not found.")
    if attempt.user_id != user.id:
        raise ApiError(403, "not_your_attempt", "This quiz attempt belongs to someone else.")
    return attempt


def _attempt_questions(db: DbSession, attempt: QuizAttempt) -> list[tuple[int, Question]]:
    """(position, question) pairs of this attempt, in order."""
    rows = db.execute(
        select(QuizAttemptQuestion.position, Question)
        .join(Question, Question.id == QuizAttemptQuestion.question_id)
        .where(QuizAttemptQuestion.attempt_id == attempt.id)
        .order_by(QuizAttemptQuestion.position)
    ).all()
    return [(position, question) for position, question in rows]


def _answers(db: DbSession, attempt: QuizAttempt) -> dict[int, QuizAnswer]:
    return {a.question_id: a for a in db.scalars(select(QuizAnswer).where(QuizAnswer.attempt_id == attempt.id))}


def _best_score(db: DbSession, user: User, quiz_id: int) -> int | None:
    return db.scalar(
        select(func.max(QuizAttempt.score)).where(
            QuizAttempt.user_id == user.id,
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.round == user.current_round,
            QuizAttempt.finished_at.is_not(None),
        )
    )


def _finish_json(db: DbSession, user: User, attempt: QuizAttempt, quiz: Quiz) -> dict[str, Any]:
    answers = _answers(db, attempt)
    wrong = [q.id for _, q in _attempt_questions(db, attempt) if not (q.id in answers and answers[q.id].is_correct)]
    return {
        "attempt_id": attempt.id,
        "score": attempt.score,
        "correct": attempt.correct,
        "total": len(wrong) + attempt.correct,
        "passed": attempt.passed,
        "pass_mark": quiz.pass_mark,
        "best_score": _best_score(db, user, quiz.id),
        "wrong_questions": wrong,
    }


# --- Endpoints #19 to #22: quiz ---


@router.post("/quizzes/{quiz_id}/attempts", status_code=status.HTTP_201_CREATED, summary="#19 Start a quiz")
def start_quiz(quiz_id: PathId, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise ApiError(404, "not_found", "Quiz not found.")
    facts = unlock.load_session_facts(db, user, db.get(StudySession, quiz.session_id))
    if unlock.quiz_status(facts, facts.quizzes[quiz.number]) == "locked":
        raise ApiError(403, "quiz_locked", "This quiz is locked.")

    bank = list(db.scalars(select(Question.id).where(Question.quiz_id == quiz.id)))
    if not bank:
        raise ApiError(404, "not_found", "This quiz has no questions yet.")

    # Starting again throws away an unfinished attempt of this quiz, so only one is ever open.
    db.execute(delete(QuizAttempt).where(
        QuizAttempt.user_id == user.id, QuizAttempt.quiz_id == quiz.id, QuizAttempt.finished_at.is_(None)
    ))
    attempt = QuizAttempt(user_id=user.id, quiz_id=quiz.id, round=user.current_round)
    db.add(attempt)
    db.flush()

    # A random mix from the question bank, so every retake is different.
    picked = random.sample(bank, min(quiz.question_count, len(bank)))
    for position, question_id in enumerate(picked, start=1):
        db.add(QuizAttemptQuestion(attempt_id=attempt.id, question_id=question_id, position=position))
    db.commit()

    questions = []
    for position, q in _attempt_questions(db, attempt):
        item = {"id": q.id, "number": position, "type": q.type, "prompt_ruby": q.prompt_ruby, "options": q.options}
        if q.underline is not None:
            item["underline"] = q.underline
        questions.append(item)  # never correct_option_id here
    return {"attempt_id": attempt.id, "quiz_id": quiz.id, "total_questions": len(questions), "questions": questions}


@router.post("/quiz-attempts/{attempt_id}/answers", summary="#20 Answer one quiz question")
def answer_quiz_question(attempt_id: PathId, body: AnswerRequest, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    attempt = _own_attempt(db, user, attempt_id, lock=True)
    if attempt.finished_at is not None:
        raise ApiError(400, "attempt_finished", "This quiz is already finished.")

    question = db.scalar(
        select(Question)
        .join(QuizAttemptQuestion, QuizAttemptQuestion.question_id == Question.id)
        .where(QuizAttemptQuestion.attempt_id == attempt.id, Question.id == body.question_id)
    )
    if question is None:
        raise ApiError(400, "question_not_in_attempt", "This question is not part of this quiz attempt.")

    is_correct = body.selected_option_id == question.correct_option_id
    # RETURNING gives back the row only if it was really saved (not when it already existed).
    saved = db.execute(
        insert(QuizAnswer)
        .values(attempt_id=attempt.id, question_id=question.id, selected_option_id=body.selected_option_id, is_correct=is_correct)
        .on_conflict_do_nothing()
        .returning(QuizAnswer.question_id)
    ).first()
    if saved is None:
        raise ApiError(400, "already_answered", "This question is already answered.")
    db.commit()

    answers = _answers(db, attempt)
    return {
        "question_id": question.id,
        "is_correct": is_correct,
        "selected_option_id": body.selected_option_id,
        "correct_option_id": question.correct_option_id,  # allowed now: the user has answered
        "answered": len(answers),
        "correct_so_far": sum(1 for a in answers.values() if a.is_correct),
    }


@router.post("/quiz-attempts/{attempt_id}/finish", summary="#21 Finish a quiz")
def finish_quiz(attempt_id: PathId, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    attempt = _own_attempt(db, user, attempt_id, lock=True)
    quiz = db.get(Quiz, attempt.quiz_id)
    if attempt.finished_at is None:  # finishing twice is safe and returns the same result
        total = len(_attempt_questions(db, attempt))
        correct = sum(1 for a in _answers(db, attempt).values() if a.is_correct)  # unanswered counts as wrong
        attempt.correct = correct
        attempt.score = round(correct * 100 / total) if total else 0
        attempt.passed = attempt.score >= quiz.pass_mark
        attempt.finished_at = datetime.now(UTC)
        db.commit()
    return _finish_json(db, user, attempt, quiz)


@router.get("/quiz-attempts/{attempt_id}", summary="#22 Review a finished quiz")
def get_quiz_attempt(attempt_id: PathId, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    attempt = _own_attempt(db, user, attempt_id)
    if attempt.finished_at is None:
        raise ApiError(400, "attempt_not_finished", "Finish the quiz first.")
    answers = _answers(db, attempt)
    questions = []
    for position, q in _attempt_questions(db, attempt):
        answer = answers.get(q.id)
        questions.append({
            "id": q.id,
            "number": position,
            "prompt_ruby": q.prompt_ruby,
            "options": q.options,
            "selected_option_id": answer.selected_option_id if answer else None,
            "correct_option_id": q.correct_option_id,
            "is_correct": bool(answer and answer.is_correct),
        })
    return {
        "attempt_id": attempt.id,
        "score": attempt.score,
        "passed": attempt.passed,
        "finished_at": _utc_text(attempt.finished_at),
        "questions": questions,
    }


# --- Mock test helpers ---

PART_ORDER = ("vocabulary", "grammar", "reading")


def _own_mock_attempt(db: DbSession, user: User, attempt_id: int, lock: bool = False) -> MockAttempt:
    """The user's own mock attempt, already submitted if its time is up."""
    attempt = db.get(MockAttempt, attempt_id, with_for_update=lock, populate_existing=lock)
    if attempt is None:
        raise ApiError(404, "not_found", "Mock test attempt not found.")
    if attempt.user_id != user.id:
        raise ApiError(403, "not_your_attempt", "This mock test attempt belongs to someone else.")
    mock_clock.submit_if_time_is_up(db, attempt)
    return attempt


def _mock_questions(db: DbSession, mock_test_id: int) -> list[Question]:
    return list(db.scalars(select(Question).where(Question.mock_test_id == mock_test_id).order_by(Question.number)))


def _mock_answers(db: DbSession, attempt: MockAttempt) -> dict[int, str]:
    rows = db.execute(select(MockAnswer.question_id, MockAnswer.selected_option_id).where(MockAnswer.attempt_id == attempt.id))
    return dict(rows.all())


def _question_json(q: Question, with_type: bool) -> dict[str, Any]:
    item: dict[str, Any] = {"id": q.id, "number": q.number}
    if with_type:
        item["type"] = q.type
    item["prompt_ruby"] = q.prompt_ruby
    if q.underline is not None:
        item["underline"] = q.underline
    item["options"] = q.options
    return item  # never correct_option_id here


def _start_json(db: DbSession, attempt: MockAttempt) -> dict[str, Any]:
    questions = _mock_questions(db, attempt.mock_test_id)
    passages = list(db.scalars(
        select(ReadingPassage).where(ReadingPassage.mock_test_id == attempt.mock_test_id).order_by(ReadingPassage.position)
    ))
    return {
        "attempt_id": attempt.id,
        "mock_test_id": attempt.mock_test_id,
        "started_at": _utc_text(attempt.started_at),
        "ends_at": _utc_text(attempt.ends_at),
        "server_time": _utc_text(mock_clock.now()),
        "sections": [
            {
                "part": "language_knowledge",
                "questions": [_question_json(q, with_type=True) for q in questions if q.passage_id is None],
            },
            {
                "part": "reading",
                "passages": [
                    {
                        "id": p.id,
                        "length": p.length,
                        "text_ruby": p.text_ruby,
                        "questions": [_question_json(q, with_type=False) for q in questions if q.passage_id == p.id],
                    }
                    for p in passages
                ],
            },
        ],
        "saved_answers": {str(question_id): option for question_id, option in _mock_answers(db, attempt).items()},
    }


def _result_json(db: DbSession, user: User, attempt: MockAttempt) -> dict[str, Any]:
    questions = _mock_questions(db, attempt.mock_test_id)
    answers = _mock_answers(db, attempt)
    parts: dict[str, list[int]] = {}
    review = []
    for q in questions:
        selected = answers.get(q.id)
        is_correct = selected == q.correct_option_id
        counts = parts.setdefault(q.part, [0, 0])
        counts[0] += is_correct
        counts[1] += 1
        review.append({
            "id": q.id,
            "number": q.number,
            "part": q.part,
            "prompt_ruby": q.prompt_ruby,
            "options": q.options,
            "selected_option_id": selected,
            "correct_option_id": q.correct_option_id,  # allowed now: the test is submitted
            "is_correct": is_correct,
        })
    prediction = load_prediction(db, user)
    limit = int((attempt.ends_at - attempt.started_at).total_seconds())
    used = int((attempt.submitted_at - attempt.started_at).total_seconds())
    return {
        "attempt_id": attempt.id,
        "submitted_at": _utc_text(attempt.submitted_at),
        "submitted_by": attempt.submitted_by,
        "time_used_seconds": max(0, min(used, limit)),
        "time_limit_seconds": limit,
        "score": {"correct": attempt.correct, "total": attempt.total, "percent": mock_clock.percent(attempt.correct, attempt.total)},
        "parts": [
            {"part": part, "correct": parts[part][0], "total": parts[part][1]} for part in PART_ORDER if part in parts
        ],
        # The user's current prediction. Only first attempts count, so a retake leaves it unchanged.
        "pass_prediction": prediction.value if prediction else None,
        "pass_prediction_warning": prediction.warning if prediction else None,
        "counts_for_prediction": attempt.counts_for_prediction,
        "questions": review,
    }


# --- Endpoints #23 to #26: mock test ---


@router.post(
    "/mock-tests/{mock_test_id}/attempts",
    status_code=status.HTTP_201_CREATED,
    summary="#23 Start, resume or retake a mock test",
)
def start_mock_test(mock_test_id: PathId, response: Response, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    mock_test = db.get(MockTest, mock_test_id)
    if mock_test is None:
        raise ApiError(404, "not_found", "Mock test not found.")
    facts = unlock.load_session_facts(db, user, db.get(StudySession, mock_test.session_id))  # also submits timed-out attempts
    if unlock.mock_status(facts) == "locked":
        raise ApiError(403, "mock_locked", "This mock test is locked.")
    if mock_clock.total_questions(db, mock_test.id) == 0:
        raise ApiError(404, "not_found", "This mock test has no questions yet.")

    mine = (MockAttempt.user_id == user.id, MockAttempt.mock_test_id == mock_test.id)
    # An attempt left open from before a progress reset (#37) belongs to an old round: throw it away.
    db.execute(delete(MockAttempt).where(
        *mine, MockAttempt.submitted_at.is_(None), MockAttempt.round != user.current_round
    ))

    running = db.scalar(select(MockAttempt).where(*mine, MockAttempt.submitted_at.is_(None)))
    if running is not None:
        db.commit()
        response.status_code = status.HTTP_200_OK  # resumed: same attempt, the clock kept running
        return _start_json(db, running)

    # Only the first attempt in a round counts for the pass prediction. Retakes are for review.
    earlier = db.scalar(select(func.count()).select_from(MockAttempt).where(*mine, MockAttempt.round == user.current_round))
    started = mock_clock.now()
    attempt = MockAttempt(
        user_id=user.id,
        mock_test_id=mock_test.id,
        round=user.current_round,
        started_at=started,
        ends_at=started + timedelta(seconds=mock_test.time_limit_seconds),  # set by the server, never the app
        counts_for_prediction=earlier == 0,
    )
    db.add(attempt)
    try:
        db.commit()
    except IntegrityError:
        # Two "start" taps at the same moment: the database allows only one open attempt, so resume it.
        db.rollback()
        running = db.scalar(select(MockAttempt).where(*mine, MockAttempt.submitted_at.is_(None)))
        if running is None:
            raise
        response.status_code = status.HTTP_200_OK
        return _start_json(db, running)
    return _start_json(db, attempt)


@router.put("/mock-attempts/{attempt_id}/answers", summary="#24 Save or change one mock test answer")
def save_mock_answer(attempt_id: PathId, body: AnswerRequest, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    attempt = _own_mock_attempt(db, user, attempt_id, lock=True)
    if attempt.submitted_at is not None:
        db.commit()  # keeps the automatic submit if the time just ran out
        raise ApiError(400, "attempt_finished", "Time is up or the test was already submitted.")

    question = db.get(Question, body.question_id)
    if question is None or question.mock_test_id != attempt.mock_test_id:
        raise ApiError(400, "question_not_in_attempt", "This question is not part of this mock test.")

    db.execute(
        insert(MockAnswer)
        .values(attempt_id=attempt.id, question_id=question.id, selected_option_id=body.selected_option_id)
        .on_conflict_do_update(
            index_elements=["attempt_id", "question_id"],
            set_={"selected_option_id": body.selected_option_id, "updated_at": func.now()},
        )
    )
    db.commit()
    answered = db.scalar(select(func.count()).select_from(MockAnswer).where(MockAnswer.attempt_id == attempt.id))
    return {
        "question_id": question.id,
        "saved": True,
        "answered_count": answered,
        "total_questions": mock_clock.total_questions(db, attempt.mock_test_id),
    }


@router.post("/mock-attempts/{attempt_id}/submit", summary="#25 Submit a mock test")
def submit_mock_test(attempt_id: PathId, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    attempt = _own_mock_attempt(db, user, attempt_id, lock=True)
    if attempt.submitted_by == "user":
        raise ApiError(400, "already_submitted", "This mock test was already submitted.")
    if attempt.submitted_at is None:
        mock_clock.submit(db, attempt, "user", mock_clock.now())
    # If the time had run out, the server already submitted it ("timeout"): just show that result.
    db.commit()
    return _result_json(db, user, attempt)


@router.get("/mock-attempts/{attempt_id}/result", summary="#26 Mock test result and review")
def get_mock_result(attempt_id: PathId, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    attempt = _own_mock_attempt(db, user, attempt_id, lock=True)
    db.commit()
    if attempt.submitted_at is None:
        raise ApiError(400, "not_submitted", "This mock test is not submitted yet.")
    return _result_json(db, user, attempt)
