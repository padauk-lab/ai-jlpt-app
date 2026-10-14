"""Section 3: Quiz and mock test. Contract endpoints #19 to #26 (docs/api-contract.md).

PLACEHOLDER: every endpoint returns the contract's example JSON.
There is no database and no login check yet. Each endpoint is replaced with real logic later.

Security rule for the real version: correct answers are NEVER sent before the user answers.
Only #20 (after answering), #22, #25 and #26 (after finishing) may include correct_option_id.
"""

from typing import Any, Literal

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(tags=["3. Quiz and mock test"])

OPTIONS_PLACEHOLDER: list[dict[str, str]] = [
    {"id": "a", "text": "..."},
    {"id": "b", "text": "..."},
    {"id": "c", "text": "..."},
    {"id": "d", "text": "..."},
]

KANJI_OPTIONS: list[dict[str, str]] = [
    {"id": "a", "text": "いしりょく"},
    {"id": "b", "text": "いしりき"},
    {"id": "c", "text": "いしょく"},
    {"id": "d", "text": "いじりょく"},
]

# --- Example data, copied from the contract ---

EXAMPLE_QUIZ_START: dict[str, Any] = {
    "attempt_id": 880,
    "quiz_id": 5,
    "total_questions": 20,
    "questions": [
        {
            "id": 3101,
            "number": 1,
            "type": "kanji_reading",
            "prompt_ruby": [{"text": "彼の"}, {"text": "意志力"}, {"text": "には驚かされる。"}],
            "underline": "意志力",
            "options": KANJI_OPTIONS,
        }
    ],
}

EXAMPLE_QUIZ_REVIEW: dict[str, Any] = {
    "attempt_id": 880,
    "score": 75,
    "passed": True,
    "finished_at": "2026-10-13T10:10:00Z",
    "questions": [
        {
            "id": 3101,
            "number": 1,
            "prompt_ruby": [{"text": "彼の意志力には驚かされる。"}],
            "options": KANJI_OPTIONS,
            "selected_option_id": "b",
            "correct_option_id": "a",
            "is_correct": False,
        }
    ],
}

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
    question_id: int
    selected_option_id: Literal["a", "b", "c", "d"]


# --- Endpoints ---
# Inputs (ids, request bodies) are not used yet. They are declared so /docs shows them.


@router.post("/quizzes/{quiz_id}/attempts", status_code=status.HTTP_201_CREATED, summary="#19 Start a quiz")
def start_quiz(quiz_id: int) -> dict[str, Any]:
    return EXAMPLE_QUIZ_START


@router.post("/quiz-attempts/{attempt_id}/answers", summary="#20 Answer one quiz question")
def answer_quiz_question(attempt_id: int, body: AnswerRequest) -> dict[str, Any]:
    return {
        "question_id": 3101,
        "is_correct": False,
        "selected_option_id": "b",
        "correct_option_id": "a",
        "answered": 1,
        "correct_so_far": 0,
    }


@router.post("/quiz-attempts/{attempt_id}/finish", summary="#21 Finish a quiz")
def finish_quiz(attempt_id: int) -> dict[str, Any]:
    return {
        "attempt_id": 880,
        "score": 75,
        "correct": 15,
        "total": 20,
        "passed": True,
        "pass_mark": 70,
        "best_score": 75,
        "wrong_questions": [3104, 3109, 3112, 3115, 3120],
    }


@router.get("/quiz-attempts/{attempt_id}", summary="#22 Review a finished quiz")
def get_quiz_attempt(attempt_id: int) -> dict[str, Any]:
    return EXAMPLE_QUIZ_REVIEW


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
