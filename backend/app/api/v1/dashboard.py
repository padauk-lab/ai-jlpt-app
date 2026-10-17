"""Section 2: Dashboard, sessions and units. Contract endpoints #11 to #18 (docs/api-contract.md).

REAL: #13 (session), #14 (unit) and #15 (mark a unit as done).
PLACEHOLDER: #11, #12 and #16 to #18 still return the contract's example JSON.

Security notes:
- The unlock rules live in app/progress/unlock.py and are checked here on the server.
  A locked session or unit returns 403 even if someone calls the API directly.
- Progress is always the logged-in user's own, in their current round.
"""

from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.api.deps import CurrentUser, DbSession, PathId
from app.core.errors import ApiError
from app.models import Bookmark, Example, Grammar, StudySession, Unit, UnitProgress, User, Word
from app.progress import unlock

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


# --- Helpers for #13 to #15 ---


def _find_session(db: DbSession, session_id: int) -> StudySession:
    session = db.get(StudySession, session_id)
    if session is None:
        raise ApiError(404, "not_found", "Session not found.")
    return session


def _unit_and_facts(db: DbSession, user: User, unit_id: int) -> tuple[Unit, StudySession, unlock.SessionFacts]:
    unit = db.get(Unit, unit_id)
    if unit is None:
        raise ApiError(404, "not_found", "Unit not found.")
    session = _find_session(db, unit.session_id)
    return unit, session, unlock.load_session_facts(db, user, session)


def _examples_json(examples: list[Example]) -> list[dict[str, Any]]:
    return [{"ruby": e.ruby, "translation_my": e.translation_my} for e in sorted(examples, key=lambda e: e.position)]


def _next_step(facts: unlock.SessionFacts, number: int) -> dict[str, Any] | None:
    """What the app should show after this unit: the next unit, a quiz, or nothing yet."""
    if number in (5, 10):
        quiz = facts.quizzes.get(1 if number == 5 else 2)
        return {"type": "quiz", "id": quiz.id} if quiz else None
    next_unit = dict((n, uid) for uid, n in facts.units).get(number + 1)
    return {"type": "unit", "id": next_unit} if next_unit else None


# --- Endpoints #13 to #15 ---


@router.get("/sessions/{session_id}", summary="#13 One session: units, quizzes and mock test")
def get_session(session_id: PathId, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    facts = unlock.load_session_facts(db, user, _find_session(db, session_id))
    if not facts.unlocked:
        raise ApiError(403, "session_locked", "This session is locked.")

    mock = None
    if facts.mock is not None:
        mock = {
            "id": facts.mock.id,
            "status": unlock.mock_status(facts),
            "best_score": facts.mock.best_score,
            "last_score": facts.mock.last_score,
            "attempts": facts.mock.submitted_attempts,
        }
    return {
        "id": facts.id,
        "number": facts.number,
        "units_done": len(facts.completed),
        "units": [{"id": uid, "number": n, "status": unlock.unit_status(facts, n)} for uid, n in facts.units],
        "quizzes": [
            {
                "id": q.id,
                "covers_units": [q.first_unit, q.last_unit],
                "status": unlock.quiz_status(facts, q),
                "best_score": q.best_score,
            }
            for q in sorted(facts.quizzes.values(), key=lambda q: q.number)
        ],
        "mock_test": mock,
    }


@router.get("/units/{unit_id}", summary="#14 One unit: 20 words and 1 grammar pattern")
def get_unit(unit_id: PathId, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    unit, session, facts = _unit_and_facts(db, user, unit_id)
    status_ = unlock.unit_status(facts, unit.number)
    if status_ == "locked":
        raise ApiError(403, "unit_locked", "This unit is locked.")

    words = list(db.scalars(select(Word).where(Word.unit_id == unit.id).order_by(Word.position)))
    word_ids = [w.id for w in words]
    grammar = db.scalar(select(Grammar).where(Grammar.unit_id == unit.id))

    # Load all examples and bookmarks in two queries, not one query per word.
    examples_by_word: dict[int, list[Example]] = {}
    grammar_examples: list[Example] = []
    example_filter = Example.word_id.in_(word_ids)
    if grammar is not None:
        example_filter = example_filter | (Example.grammar_id == grammar.id)
    for example in db.scalars(select(Example).where(example_filter)):
        if example.word_id is not None:
            examples_by_word.setdefault(example.word_id, []).append(example)
        else:
            grammar_examples.append(example)
    bookmarked = set(db.scalars(select(Bookmark.word_id).where(Bookmark.user_id == user.id, Bookmark.word_id.in_(word_ids))))

    return {
        "id": unit.id,
        "session_number": session.number,
        "number": unit.number,
        "status": status_,
        "words": [
            {
                "id": w.id,
                "ruby": w.ruby,
                "meaning_my": w.meaning_my,
                "examples": _examples_json(examples_by_word.get(w.id, [])),
                "bookmarked": w.id in bookmarked,
            }
            for w in words
        ],
        "grammar": None
        if grammar is None
        else {
            "id": grammar.id,
            "pattern": grammar.pattern,
            "meaning_my": grammar.meaning_my,
            "how_to_use": grammar.how_to_use,
            "how_to_use_my": grammar.how_to_use_my,
            "note_my": grammar.note_my,
            "examples": _examples_json(grammar_examples),
        },
    }


@router.post("/units/{unit_id}/complete", summary="#15 Mark a unit as done")
def complete_unit(unit_id: PathId, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    unit, _, facts = _unit_and_facts(db, user, unit_id)
    if unlock.unit_status(facts, unit.number) == "locked":
        raise ApiError(403, "unit_locked", "This unit is locked.")

    # ON CONFLICT DO NOTHING: tapping "Mark as done" twice (or two taps at once) is safe.
    db.execute(
        insert(UnitProgress)
        .values(user_id=user.id, unit_id=unit.id, round=user.current_round)
        .on_conflict_do_nothing()
    )
    db.commit()
    return {"unit_id": unit.id, "status": "completed", "next": _next_step(facts, unit.number)}


@router.get("/bookmarks", summary="#16 Saved words")
def get_bookmarks(search: str | None = None) -> dict[str, Any]:
    return EXAMPLE_BOOKMARKS


@router.post("/bookmarks", status_code=status.HTTP_201_CREATED, summary="#17 Save a word")
def add_bookmark(body: BookmarkRequest) -> dict[str, Any]:
    return {"word_id": 501, "bookmarked": True}


@router.delete("/bookmarks/{word_id}", status_code=status.HTTP_204_NO_CONTENT, summary="#18 Remove a saved word")
def remove_bookmark(word_id: int) -> None:
    return None
