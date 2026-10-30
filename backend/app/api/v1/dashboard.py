"""Section 2: Dashboard, sessions and units. Contract endpoints #11 to #18 (docs/api-contract.md).

All real: #11 (dashboard), #13 (session), #14 (unit), #15 (mark a unit as done) and #16 to #18 (saved words).
#12 (proverb of the day) lives in proverbs.py.

Security notes:
- The unlock rules live in app/progress/unlock.py and are checked here on the server.
  A locked session or unit returns 403 even if someone calls the API directly.
- Progress is always the logged-in user's own, in their current round.
- A word from a locked unit can't be saved (403), so saved words never reveal locked content.
"""

from datetime import UTC, datetime, time
from typing import Annotated, Any

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert

from app.api.deps import CurrentUser, DbSession, PathId
from app.core.errors import ApiError
from app.models import Bookmark, Example, Grammar, Plan, StudySession, Unit, UnitProgress, User, Word
from app.plan import service
from app.plan.calculator import DEFAULT_UNITS_PER_DAY, UNITS_TOTAL
from app.progress import unlock
from app.progress.prediction import load_prediction

router = APIRouter(tags=["2. Dashboard, sessions and units"])

# --- Request shapes (what the app sends) ---


class BookmarkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    word_id: Annotated[int, Field(strict=True, ge=1, le=9_223_372_036_854_775_807)]


# --- Endpoints ---


SESSIONS_TOTAL = 10


def _session_status(facts: unlock.SessionFacts) -> str:
    """completed: mock test submitted (that is what opens the next session).
    in_progress: something done. available: open, nothing done yet. locked: not open."""
    if not facts.unlocked:
        return "locked"
    if facts.mock is not None and facts.mock.submitted_attempts > 0:
        return "completed"
    if facts.completed or any(q.finished_attempts for q in facts.quizzes.values()):
        return "in_progress"
    return "available"


def _units_done_today(db: DbSession, user: User) -> int:
    """Units marked as done since midnight in Japan (the same "today" as the study plan)."""
    midnight = datetime.combine(service.today(), time.min, tzinfo=service.JAPAN_TIME)
    query = select(func.count()).select_from(UnitProgress).where(
        UnitProgress.user_id == user.id,
        UnitProgress.round == user.current_round,
        UnitProgress.completed_at >= midnight,
    )
    return db.scalar(query) or 0


@router.get("/dashboard", summary="#11 Everything the Dashboard needs")
def get_dashboard(user: CurrentUser, db: DbSession) -> dict[str, Any]:
    loaded = {s.number: s for s in db.scalars(select(StudySession).order_by(StudySession.number))}

    sessions: list[dict[str, Any]] = []
    next_unit: dict[str, Any] | None = None
    for number in range(1, SESSIONS_TOTAL + 1):
        session = loaded.get(number)
        if session is None:
            # Content for this session isn't loaded yet: shown on the map, but locked and without an id.
            sessions.append({"id": None, "number": number, "progress": 0, "status": "locked"})
            continue
        facts = unlock.load_session_facts(db, user, session)
        sessions.append({
            "id": session.id,
            "number": number,
            "progress": len(facts.completed) * 100 // unlock.UNITS_PER_SESSION,
            "status": _session_status(facts),
        })
        if next_unit is None and facts.unlocked:
            # "Continue" = the first unit the user can study now, in the earliest open session.
            for unit_id, unit_number in facts.units:
                if unlock.unit_status(facts, unit_number) == "available":
                    next_unit = {"session_id": session.id, "unit_id": unit_id, "label": f"Session {number}, Unit {unit_number}"}
                    break

    plan = db.get(Plan, user.id)
    prediction = load_prediction(db, user)
    return {
        "overall_progress": service.count_units_done(db, user) * 100 // UNITS_TOTAL,
        "pass_prediction": prediction.value if prediction else None,
        "pass_prediction_warning": prediction.warning if prediction else None,
        "today": {
            "units_done": _units_done_today(db, user),
            "units_goal": plan.units_per_day if plan is not None else DEFAULT_UNITS_PER_DAY,
        },
        "continue": next_unit,
        "sessions": sessions,
    }


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


# --- Endpoints #16 to #18: saved words ---


def _escape_like(text: str) -> str:
    """Treat % and _ in the search as normal letters, not as wildcards."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("/bookmarks", summary="#16 Saved words")
def get_bookmarks(
    user: CurrentUser,
    db: DbSession,
    search: Annotated[str | None, Query(max_length=50)] = None,
) -> dict[str, Any]:
    query = (
        select(Bookmark.created_at, Word, StudySession.number, Unit.number)
        .join(Word, Word.id == Bookmark.word_id)
        .join(Unit, Unit.id == Word.unit_id)
        .join(StudySession, StudySession.id == Unit.session_id)
        .where(Bookmark.user_id == user.id)
        .order_by(Bookmark.created_at.desc(), Word.id.desc())  # newest first
    )
    if search and search.strip():
        # Matches the word, its reading or its Burmese meaning. Parameters keep it safe from SQL injection.
        pattern = f"%{_escape_like(search.strip())}%"
        query = query.where(or_(
            Word.word.ilike(pattern, escape="\\"),
            Word.furigana.ilike(pattern, escape="\\"),
            Word.meaning_my.ilike(pattern, escape="\\"),
        ))
    rows = db.execute(query).all()
    return {
        "total": len(rows),
        "words": [
            {
                "word_id": word.id,
                "ruby": word.ruby,
                "meaning_my": word.meaning_my,
                "session_number": session_number,
                "unit_number": unit_number,
                "saved_at": saved_at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            for saved_at, word, session_number, unit_number in rows
        ],
    }


@router.post("/bookmarks", status_code=status.HTTP_201_CREATED, summary="#17 Save a word")
def add_bookmark(body: BookmarkRequest, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    word = db.get(Word, body.word_id)
    if word is None:
        raise ApiError(404, "not_found", "Word not found.")
    unit, _, facts = _unit_and_facts(db, user, word.unit_id)
    if unlock.unit_status(facts, unit.number) == "locked":
        raise ApiError(403, "unit_locked", "This word is in a locked unit.")

    # Saving twice (or two taps at once) is safe.
    db.execute(insert(Bookmark).values(user_id=user.id, word_id=word.id).on_conflict_do_nothing())
    db.commit()
    return {"word_id": word.id, "bookmarked": True}


@router.delete("/bookmarks/{word_id}", status_code=status.HTTP_204_NO_CONTENT, summary="#18 Remove a saved word")
def remove_bookmark(word_id: PathId, user: CurrentUser, db: DbSession) -> None:
    removed = db.execute(delete(Bookmark).where(Bookmark.user_id == user.id, Bookmark.word_id == word_id)).rowcount
    if removed == 0:
        raise ApiError(404, "not_found", "This word is not saved.")
    db.commit()
