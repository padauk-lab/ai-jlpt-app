"""Section 3: Quiz and mock test. Contract endpoints #19 to #26 (docs/api-contract.md).

REAL: #19 to #22 (quiz).
PLACEHOLDER: #23 to #26 (mock test) still return the contract's example JSON.

Security rules:
- Correct answers are NEVER sent before the user answers. Only #20 (after answering one question),
  #22, #25 and #26 (after finishing) include correct_option_id.
- A locked quiz can't be started (403), and an attempt can only be used by its owner (403).
- Each question can be answered once per attempt, and only questions that belong to the attempt.
- The score is calculated here on the server. The app never sends a score.
"""

import random
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert

from app.api.deps import CurrentUser, DbSession, PathId
from app.core.errors import ApiError
from app.models import Question, Quiz, QuizAnswer, QuizAttempt, QuizAttemptQuestion, StudySession, User
from app.progress import unlock

router = APIRouter(tags=["3. Quiz and mock test"])

OPTIONS_PLACEHOLDER: list[dict[str, str]] = [
    {"id": "a", "text": "..."},
    {"id": "b", "text": "..."},
    {"id": "c", "text": "..."},
    {"id": "d", "text": "..."},
]

# --- Example data, copied from the contract ---

EXAMPLE_MOCK_START: dict[str, Any] = {
    "attempt_id": 410,
    "mock_test_id": 3,
    "started_at": "2026-10-13T11:00:00Z",
    "ends_at": "2026-10-13T11:30:00Z",
    "server_time": "2026-10-13T11:00:00Z",
    "sections": [
        {
            "part": "language_knowledge",
            "questions": [
                {
                    "id": 9001,
                    "number": 1,
                    "type": "kanji_reading",
                    "prompt_ruby": [{"text": "..."}],
                    "options": OPTIONS_PLACEHOLDER,
                }
            ],
        },
        {
            "part": "reading",
            "passages": [
                {
                    "id": 71,
                    "length": "short",
                    "text_ruby": [{"text": "..."}],
                    "questions": [
                        {
                            "id": 9046,
                            "number": 46,
                            "prompt_ruby": [{"text": "..."}],
                            "options": OPTIONS_PLACEHOLDER,
                        }
                    ],
                }
            ],
        },
    ],
    "saved_answers": {"9001": "c"},
}

EXAMPLE_MOCK_RESULT: dict[str, Any] = {
    "attempt_id": 410,
    "submitted_at": "2026-10-13T11:27:40Z",
    "submitted_by": "user",
    "time_used_seconds": 1660,
    "time_limit_seconds": 1800,
    "score": {"correct": 38, "total": 51, "percent": 75},
    "parts": [
        {"part": "vocabulary", "correct": 22, "total": 25},
        {"part": "grammar", "correct": 12, "total": 20},
        {"part": "reading", "correct": 4, "total": 6},
    ],
    "pass_prediction": 70,
    "counts_for_prediction": True,
    "questions": [
        {
            "id": 9001,
            "number": 1,
            "part": "vocabulary",
            "prompt_ruby": [{"text": "..."}],
            "options": OPTIONS_PLACEHOLDER,
            "selected_option_id": "c",
            "correct_option_id": "a",
            "is_correct": False,
        }
    ],
}


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


# --- Endpoints #23 to #26: mock test (placeholders) ---
# Inputs (ids, request bodies) are not used yet. They are declared so /docs shows them.


@router.post(
    "/mock-tests/{mock_test_id}/attempts",
    status_code=status.HTTP_201_CREATED,
    summary="#23 Start, resume or retake a mock test",
)
def start_mock_test(mock_test_id: int) -> dict[str, Any]:
    # The real version returns 200 instead of 201 when it resumes an attempt in progress.
    return EXAMPLE_MOCK_START


@router.put("/mock-attempts/{attempt_id}/answers", summary="#24 Save or change one mock test answer")
def save_mock_answer(attempt_id: int, body: AnswerRequest) -> dict[str, Any]:
    return {"question_id": 9001, "saved": True, "answered_count": 12, "total_questions": 51}


@router.post("/mock-attempts/{attempt_id}/submit", summary="#25 Submit a mock test")
def submit_mock_test(attempt_id: int) -> dict[str, Any]:
    return EXAMPLE_MOCK_RESULT


@router.get("/mock-attempts/{attempt_id}/result", summary="#26 Mock test result and review")
def get_mock_result(attempt_id: int) -> dict[str, Any]:
    return EXAMPLE_MOCK_RESULT
