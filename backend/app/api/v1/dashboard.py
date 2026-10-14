"""Section 2: Dashboard, sessions and units. Contract endpoints #11 to #18 (docs/api-contract.md).

PLACEHOLDER: every endpoint returns the contract's example JSON.
There is no database and no login check yet. Each endpoint is replaced with real logic later.
"""

from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(tags=["2. Dashboard, sessions and units"])

# --- Example data, copied from the contract ---

EXAMPLE_DASHBOARD: dict[str, Any] = {
    "overall_progress": 32,
    "pass_prediction": 68,
    "today": {"units_done": 2, "units_goal": 4},
    "continue": {"session_id": 3, "unit_id": 25, "label": "Session 3, Unit 5"},
    "sessions": [
        {"id": 1, "number": 1, "progress": 100, "status": "completed"},
        {"id": 2, "number": 2, "progress": 100, "status": "completed"},
        {"id": 3, "number": 3, "progress": 40, "status": "in_progress"},
        {"id": 4, "number": 4, "progress": 0, "status": "locked"},
    ],
}

EXAMPLE_PROVERB: dict[str, Any] = {
    "id": 7,
    "ruby": [
        {"text": "継続", "reading": "けいぞく"},
        {"text": "は"},
        {"text": "力", "reading": "ちから"},
        {"text": "なり"},
    ],
    "meaning_my": "Burmese translation.",
    "explanation_my": "Burmese explanation of when and why this proverb is used.",
}

EXAMPLE_SESSION: dict[str, Any] = {
    "id": 3,
    "number": 3,
    "units_done": 4,
    "units": [
        {"id": 21, "number": 1, "status": "completed"},
        {"id": 25, "number": 5, "status": "available"},
        {"id": 26, "number": 6, "status": "locked"},
    ],
    "quizzes": [
        {"id": 5, "covers_units": [1, 5], "status": "locked", "best_score": None},
        {"id": 6, "covers_units": [6, 10], "status": "locked", "best_score": None},
    ],
    "mock_test": {"id": 3, "status": "locked", "best_score": None, "last_score": None, "attempts": 0},
}

EXAMPLE_UNIT: dict[str, Any] = {
    "id": 25,
    "session_number": 3,
    "number": 5,
    "status": "available",
    "words": [
        {
            "id": 501,
            "ruby": [{"text": "意志力", "reading": "いしりょく"}],
            "meaning_my": "Burmese meaning.",
            "examples": [
                {
                    "ruby": [
                        {"text": "彼", "reading": "かれ"},
                        {"text": "の"},
                        {"text": "意志力", "reading": "いしりょく"},
                        {"text": "はすごい。"},
                    ],
                    "translation_my": "Burmese translation.",
                }
            ],
            "bookmarked": True,
        }
    ],
    "grammar": {
        "id": 25,
        "pattern": "〜というよりも",
        "meaning_my": "Burmese meaning.",
        "how_to_use": "V/A/N (plain form) + というよりも",
        "how_to_use_my": "Burmese explanation of how and when to use this pattern.",
        "note_my": "Burmese note about a common mistake.",
        "examples": [
            {
                "ruby": [
                    {"text": "彼", "reading": "かれ"},
                    {"text": "は"},
                    {"text": "面白", "reading": "おもしろ"},
                    {"text": "いというよりも、"},
                    {"text": "変", "reading": "へん"},
                    {"text": "だ。"},
                ],
                "translation_my": "Burmese translation.",
            }
        ],
    },
}

EXAMPLE_BOOKMARKS: dict[str, Any] = {
    "total": 12,
    "words": [
        {
            "word_id": 501,
            "ruby": [{"text": "意志力", "reading": "いしりょく"}],
            "meaning_my": "Burmese meaning.",
            "session_number": 3,
            "unit_number": 5,
            "saved_at": "2026-10-12T14:00:00Z",
        }
    ],
}


# --- Request shapes (what the app sends) ---


class BookmarkRequest(BaseModel):
    word_id: int


# --- Endpoints ---
# Inputs (ids, search, request bodies) are not used yet. They are declared so /docs shows them.


@router.get("/dashboard", summary="#11 Everything the Dashboard needs")
def get_dashboard() -> dict[str, Any]:
    return EXAMPLE_DASHBOARD


@router.get("/proverbs/today", summary="#12 Proverb of the day")
def get_proverb_today() -> dict[str, Any]:
    return EXAMPLE_PROVERB


@router.get("/sessions/{session_id}", summary="#13 One session: units, quizzes and mock test")
def get_session(session_id: int) -> dict[str, Any]:
    return EXAMPLE_SESSION


@router.get("/units/{unit_id}", summary="#14 One unit: 20 words and 1 grammar pattern")
def get_unit(unit_id: int) -> dict[str, Any]:
    return EXAMPLE_UNIT


@router.post("/units/{unit_id}/complete", summary="#15 Mark a unit as done")
def complete_unit(unit_id: int) -> dict[str, Any]:
    return {"unit_id": 25, "status": "completed", "next": {"type": "quiz", "id": 5}}


@router.get("/bookmarks", summary="#16 Saved words")
def get_bookmarks(search: str | None = None) -> dict[str, Any]:
    return EXAMPLE_BOOKMARKS


@router.post("/bookmarks", status_code=status.HTTP_201_CREATED, summary="#17 Save a word")
def add_bookmark(body: BookmarkRequest) -> dict[str, Any]:
    return {"word_id": 501, "bookmarked": True}


@router.delete("/bookmarks/{word_id}", status_code=status.HTTP_204_NO_CONTENT, summary="#18 Remove a saved word")
def remove_bookmark(word_id: int) -> None:
    return None
