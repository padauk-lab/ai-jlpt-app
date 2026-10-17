"""#13 GET /sessions/{id}, #14 GET /units/{id} and #15 POST /units/{id}/complete, with the unlock rules."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from app.models import (
    Bookmark,
    Example,
    Grammar,
    MockAttempt,
    MockTest,
    Quiz,
    QuizAttempt,
    StudySession,
    Unit,
    User,
    Word,
)
from app.progress.unlock import SessionFacts, quiz_status, unit_status
from tests.test_auth import API, auth_header, error_code, register

RUBY = [{"text": "意志力", "reading": "いしりょく"}]


@pytest.fixture
def content() -> Iterator[dict]:
    """Session 1 (10 units, 2 quizzes, 1 mock test) and session 2 (1 unit). Removed after the test."""
    from app.db import SessionLocal, engine

    ids: dict = {"units": {}, "s2_units": {}}
    with SessionLocal() as db:
        s1, s2 = StudySession(number=1), StudySession(number=2)
        db.add_all([s1, s2])
        db.flush()
        for n in range(1, 11):
            unit = Unit(session_id=s1.id, number=n)
            db.add(unit)
            db.flush()
            ids["units"][n] = unit.id
        unit_s2 = Unit(session_id=s2.id, number=1)
        db.add(unit_s2)
        db.flush()
        ids["s2_units"][1] = unit_s2.id

        # Unit 1 gets real content: 2 words (examples in the wrong order on purpose) and grammar.
        for position in (2, 1):
            word = Word(unit_id=ids["units"][1], position=position, word=f"w{position}", furigana="x", ruby=RUBY, meaning_my=f"m{position}")
            db.add(word)
            db.flush()
            ids[f"word{position}"] = word.id
            for ex in (2, 1):
                db.add(Example(word_id=word.id, position=ex, ruby=RUBY, translation_my=f"w{position}e{ex}"))
        grammar = Grammar(unit_id=ids["units"][1], pattern="〜ならでは", meaning_my="g", how_to_use="N + ならでは", how_to_use_my="h", note_my=None)
        db.add(grammar)
        db.flush()
        db.add(Example(grammar_id=grammar.id, position=1, ruby=RUBY, translation_my="ge1"))

        q1 = Quiz(session_id=s1.id, number=1, first_unit=1, last_unit=5)
        q2 = Quiz(session_id=s1.id, number=2, first_unit=6, last_unit=10)
        mock = MockTest(session_id=s1.id)
        db.add_all([q1, q2, mock])
        db.commit()
        ids.update(s1=s1.id, s2=s2.id, quiz1=q1.id, quiz2=q2.id, mock=mock.id)

    yield ids

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE sessions RESTART IDENTITY CASCADE"))


def user_header(client) -> dict[str, str]:
    return auth_header(register(client)["access_token"])


def complete(client, headers, unit_id):
    return client.post(f"{API}/units/{unit_id}/complete", headers=headers)


def complete_units(client, headers, content, numbers):
    for n in numbers:
        assert complete(client, headers, content["units"][n]).status_code == 200


def add_quiz_attempt(quiz_id: int, score: int) -> None:
    from app.db import SessionLocal

    with SessionLocal() as db:
        user = db.query(User).one()
        db.add(QuizAttempt(
            user_id=user.id, quiz_id=quiz_id, round=user.current_round,
            finished_at=datetime.now(UTC), correct=score // 5, score=score, passed=score >= 70,
        ))
        db.commit()


def add_mock_attempt(mock_id: int, correct: int, total: int = 50, submitted: bool = True) -> None:
    from app.db import SessionLocal

    now = datetime.now(UTC)
    with SessionLocal() as db:
        user = db.query(User).one()
        db.add(MockAttempt(
            user_id=user.id, mock_test_id=mock_id, round=user.current_round,
            started_at=now - timedelta(minutes=30), ends_at=now,
            submitted_at=now if submitted else None, submitted_by="user" if submitted else None,
            correct=correct if submitted else None, total=total if submitted else None,
            counts_for_prediction=True,
        ))
        db.commit()


# --- #13 Session ---


def test_new_user_sees_session_1_with_only_unit_1_open(client, content):
    headers = user_header(client)
    body = client.get(f"{API}/sessions/{content['s1']}", headers=headers).json()
    assert body["number"] == 1
    assert body["units_done"] == 0
    statuses = [u["status"] for u in body["units"]]
    assert statuses == ["available"] + ["locked"] * 9
    assert [q["status"] for q in body["quizzes"]] == ["locked", "locked"]
    assert body["quizzes"][0]["covers_units"] == [1, 5]
    assert body["mock_test"] == {"id": content["mock"], "status": "locked", "best_score": None, "last_score": None, "attempts": 0}


def test_session_2_is_locked_until_the_mock_test_is_submitted(client, content):
    headers = user_header(client)
    response = client.get(f"{API}/sessions/{content['s2']}", headers=headers)
    assert response.status_code == 403
    assert error_code(response) == "session_locked"
    # Its unit can't be opened or completed either.
    assert client.get(f"{API}/units/{content['s2_units'][1]}", headers=headers).status_code == 403
    assert complete(client, headers, content["s2_units"][1]).status_code == 403


def test_full_path_through_a_session(client, content):
    headers = user_header(client)
    complete_units(client, headers, content, range(1, 6))
    session = client.get(f"{API}/sessions/{content['s1']}", headers=headers).json()
    assert session["quizzes"][0]["status"] == "available"
    assert session["units"][5]["status"] == "locked"  # unit 6 needs Quiz 1 passed

    add_quiz_attempt(content["quiz1"], 60)  # failed
    session = client.get(f"{API}/sessions/{content['s1']}", headers=headers).json()
    assert session["quizzes"][0] == {"id": content["quiz1"], "covers_units": [1, 5], "status": "failed", "best_score": 60}
    assert complete(client, headers, content["units"][6]).status_code == 403

    add_quiz_attempt(content["quiz1"], 85)  # passed
    complete_units(client, headers, content, range(6, 11))
    add_quiz_attempt(content["quiz2"], 70)  # exactly the pass mark
    session = client.get(f"{API}/sessions/{content['s1']}", headers=headers).json()
    assert session["units_done"] == 10
    assert [q["status"] for q in session["quizzes"]] == ["passed", "passed"]
    assert session["mock_test"]["status"] == "available"

    add_mock_attempt(content["mock"], correct=20)  # 40%: any score unlocks the next session
    add_mock_attempt(content["mock"], correct=30)  # retake, 60%
    session = client.get(f"{API}/sessions/{content['s1']}", headers=headers).json()
    assert session["mock_test"] == {"id": content["mock"], "status": "completed", "best_score": 60, "last_score": 60, "attempts": 2}
    assert client.get(f"{API}/sessions/{content['s2']}", headers=headers).status_code == 200


def test_mock_test_in_progress(client, content):
    headers = user_header(client)
    complete_units(client, headers, content, range(1, 6))
    add_quiz_attempt(content["quiz1"], 90)
    complete_units(client, headers, content, range(6, 11))
    add_quiz_attempt(content["quiz2"], 90)
    add_mock_attempt(content["mock"], correct=0, submitted=False)
    session = client.get(f"{API}/sessions/{content['s1']}", headers=headers).json()
    assert session["mock_test"]["status"] == "in_progress"
    # Not submitted yet, so session 2 stays locked.
    assert client.get(f"{API}/sessions/{content['s2']}", headers=headers).status_code == 403


def test_progress_is_per_user(client, content):
    first = user_header(client)
    complete(client, first, content["units"][1])
    second = auth_header(register(client, email="other@example.com", username="other")["access_token"])
    body = client.get(f"{API}/sessions/{content['s1']}", headers=second).json()
    assert body["units_done"] == 0


# --- #14 Unit ---


def test_unit_shows_words_examples_and_grammar_in_order(client, content):
    headers = user_header(client)
    body = client.get(f"{API}/units/{content['units'][1]}", headers=headers).json()
    assert body["session_number"] == 1
    assert body["number"] == 1
    assert body["status"] == "available"
    assert [w["meaning_my"] for w in body["words"]] == ["m1", "m2"]  # by position, not by insert order
    assert [e["translation_my"] for e in body["words"][0]["examples"]] == ["w1e1", "w1e2"]
    assert body["words"][0]["bookmarked"] is False
    assert body["grammar"]["pattern"] == "〜ならでは"
    assert [e["translation_my"] for e in body["grammar"]["examples"]] == ["ge1"]


def test_unit_shows_bookmarks_of_this_user_only(client, content):
    from app.db import SessionLocal

    headers = user_header(client)
    with SessionLocal() as db:
        db.add(Bookmark(user_id=db.query(User).one().id, word_id=content["word2"]))
        db.commit()
    body = client.get(f"{API}/units/{content['units'][1]}", headers=headers).json()
    assert [w["bookmarked"] for w in body["words"]] == [False, True]

    other = auth_header(register(client, email="other@example.com", username="other")["access_token"])
    body = client.get(f"{API}/units/{content['units'][1]}", headers=other).json()
    assert [w["bookmarked"] for w in body["words"]] == [False, False]


def test_locked_unit_is_403_and_shows_no_content(client, content):
    headers = user_header(client)
    response = client.get(f"{API}/units/{content['units'][2]}", headers=headers)
    assert response.status_code == 403
    assert error_code(response) == "unit_locked"
    assert "words" not in response.text


# --- #15 Mark as done ---


def test_complete_returns_the_next_step(client, content):
    headers = user_header(client)
    body = complete(client, headers, content["units"][1]).json()
    assert body == {"unit_id": content["units"][1], "status": "completed", "next": {"type": "unit", "id": content["units"][2]}}
    complete_units(client, headers, content, range(2, 5))
    body = complete(client, headers, content["units"][5]).json()
    assert body["next"] == {"type": "quiz", "id": content["quiz1"]}


def test_completing_twice_is_safe(client, content):
    headers = user_header(client)
    first = complete(client, headers, content["units"][1])
    second = complete(client, headers, content["units"][1])
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert client.get(f"{API}/sessions/{content['s1']}", headers=headers).json()["units_done"] == 1


def test_units_cannot_be_skipped(client, content):
    headers = user_header(client)
    response = complete(client, headers, content["units"][3])
    assert response.status_code == 403
    assert error_code(response) == "unit_locked"


def test_completing_a_unit_updates_the_plan(client, content):
    headers = user_header(client)
    client.post(f"{API}/onboarding", json={"last_level": "not_taken"}, headers=headers)
    complete(client, headers, content["units"][1])
    assert client.get(f"{API}/plan", headers=headers).json()["units_done"] == 1


# --- Bad requests ---


def test_needs_login(client, content):
    assert client.get(f"{API}/sessions/{content['s1']}").status_code == 401
    assert client.get(f"{API}/units/{content['units'][1]}").status_code == 401
    assert complete(client, {}, content["units"][1]).status_code == 401


@pytest.mark.parametrize("bad_id", ["0", "-1", "abc", "99999999999999999999", "1;DROP TABLE users"])
def test_bad_ids_are_refused_cleanly(client, content, bad_id):
    headers = user_header(client)
    for path in (f"/sessions/{bad_id}", f"/units/{bad_id}"):
        response = client.get(f"{API}{path}", headers=headers)
        assert response.status_code == 422, (path, response.text)


def test_unknown_ids_are_404(client, content):
    headers = user_header(client)
    assert client.get(f"{API}/sessions/999999", headers=headers).status_code == 404
    assert client.get(f"{API}/units/999999", headers=headers).status_code == 404
    assert complete(client, headers, 999999).status_code == 404


# --- The rules alone (no database) ---


def test_rules_without_quiz_content_keep_units_6_to_10_locked():
    """Until quiz questions are loaded, nobody can skip Quiz 1."""
    facts = SessionFacts(id=1, number=1, unlocked=True, units=[(i, i) for i in range(1, 11)], completed={1, 2, 3, 4, 5})
    assert unit_status(facts, 6) == "locked"


def test_quiz_2_needs_quiz_1_passed():
    from app.progress.unlock import QuizFacts

    q1 = QuizFacts(1, 1, 1, 5, best_score=50, passed=False, finished_attempts=1)
    q2 = QuizFacts(2, 2, 6, 10, best_score=None, passed=False, finished_attempts=0)
    facts = SessionFacts(id=1, number=1, unlocked=True, units=[], completed=set(range(1, 11)), quizzes={1: q1, 2: q2})
    assert quiz_status(facts, q2) == "locked"
