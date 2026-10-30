"""#23 to #26: the mock test. The clock is the server's, so tests move a fake clock instead of waiting 30 minutes.

Includes cheating attempts: peeking at answers, answering after the time is up, using someone else's attempt.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select, update

from app.models import MockAttempt, Question, ReadingPassage, User
from app.progress import mock as mock_clock
from tests.test_auth import API, auth_header, error_code, register
from tests.test_study import add_quiz_attempt, complete_units, content, user_header  # noqa: F401  (content is a fixture)

START = datetime(2026, 10, 23, 2, 0, tzinfo=UTC)
OPTIONS = [{"id": i, "text": f"選択{i}"} for i in "abcd"]


class Clock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> datetime:
        return self.now

    def move(self, **delta) -> None:
        self.now += timedelta(**delta)


@pytest.fixture
def clock(monkeypatch) -> Clock:
    fake = Clock()
    monkeypatch.setattr(mock_clock, "now", fake)
    return fake


@pytest.fixture
def mock(content) -> dict:
    """Session 1's mock test: 2 vocabulary, 2 grammar, and 1 short passage with 2 questions.
    Correct answers: a, b, c, d, a, b (by number)."""
    from app.db import SessionLocal

    with SessionLocal() as db, db.begin():
        def add(number, part, passage_id=None, underline=None):
            q = Question(mock_test_id=content["mock"], passage_id=passage_id, number=number, part=part,
                         type="reading_short" if passage_id else f"{part}_type", prompt_ruby=[{"text": f"問{number}"}],
                         underline=underline, options=OPTIONS, correct_option_id="abcd"[(number - 1) % 4])
            db.add(q)
            db.flush()
            return q.id

        ids = {n: add(n, part, underline="下線" if n == 1 else None)
               for n, part in ((1, "vocabulary"), (2, "vocabulary"), (3, "grammar"), (4, "grammar"))}
        passage = ReadingPassage(mock_test_id=content["mock"], length="short", position=1, text_ruby=[{"text": "本文"}])
        db.add(passage)
        db.flush()
        ids.update({n: add(n, "reading", passage_id=passage.id) for n in (5, 6)})
    return {**content, "questions": ids, "passage": passage.id}


RIGHT = {1: "a", 2: "b", 3: "c", 4: "d", 5: "a", 6: "b"}


def ready_user(client, content) -> dict[str, str]:
    """A user who passed Quiz 2, so the mock test is open."""
    headers = user_header(client)
    complete_units(client, headers, content, range(1, 6))
    add_quiz_attempt(content["quiz1"], 80)
    complete_units(client, headers, content, range(6, 11))
    add_quiz_attempt(content["quiz2"], 80)
    return headers


def start(client, headers, mock_id):
    return client.post(f"{API}/mock-tests/{mock_id}/attempts", headers=headers)


def save(client, headers, attempt_id, question_id, option):
    body = {"question_id": question_id, "selected_option_id": option}
    return client.put(f"{API}/mock-attempts/{attempt_id}/answers", json=body, headers=headers)


def submit(client, headers, attempt_id):
    return client.post(f"{API}/mock-attempts/{attempt_id}/submit", headers=headers)


def result(client, headers, attempt_id):
    return client.get(f"{API}/mock-attempts/{attempt_id}/result", headers=headers)


# --- #23 Start ---


def test_locked_until_quiz_2_is_passed(client, mock, clock):
    headers = user_header(client)
    response = start(client, headers, mock["mock"])
    assert response.status_code == 403
    assert error_code(response) == "mock_locked"


def test_start_gives_the_test_without_answers(client, mock, clock):
    headers = ready_user(client, mock)
    response = start(client, headers, mock["mock"])
    assert response.status_code == 201, response.text
    body = response.json()
    assert "correct_option_id" not in response.text  # the most important rule
    assert body["mock_test_id"] == mock["mock"]
    assert body["started_at"] == "2026-10-23T02:00:00Z"
    assert body["ends_at"] == "2026-10-23T02:30:00Z"  # 30 minutes, set by the server
    assert body["server_time"] == "2026-10-23T02:00:00Z"
    assert body["saved_answers"] == {}

    knowledge, reading = body["sections"]
    assert knowledge["part"] == "language_knowledge"
    assert [q["number"] for q in knowledge["questions"]] == [1, 2, 3, 4]
    assert knowledge["questions"][0] == {"id": mock["questions"][1], "number": 1, "type": "vocabulary_type",
                                         "prompt_ruby": [{"text": "問1"}], "underline": "下線", "options": OPTIONS}
    assert reading["part"] == "reading"
    assert len(reading["passages"]) == 1
    passage = reading["passages"][0]
    assert (passage["id"], passage["length"], passage["text_ruby"]) == (mock["passage"], "short", [{"text": "本文"}])
    assert [q["number"] for q in passage["questions"]] == [5, 6]
    assert set(passage["questions"][0]) == {"id", "number", "prompt_ruby", "options"}


def test_starting_again_resumes_with_saved_answers_and_the_same_clock(client, mock, clock):
    headers = ready_user(client, mock)
    first = start(client, headers, mock["mock"]).json()
    save(client, headers, first["attempt_id"], mock["questions"][2], "c")
    clock.move(minutes=10)  # the app was closed for 10 minutes

    response = start(client, headers, mock["mock"])
    assert response.status_code == 200  # resumed, not new
    body = response.json()
    assert body["attempt_id"] == first["attempt_id"]
    assert body["ends_at"] == first["ends_at"]  # the clock kept running
    assert body["server_time"] == "2026-10-23T02:10:00Z"
    assert body["saved_answers"] == {str(mock["questions"][2]): "c"}


def test_mock_test_without_questions_is_404(client, content, clock):
    headers = ready_user(client, content)
    assert start(client, headers, content["mock"]).status_code == 404


def test_unknown_mock_test_is_404(client, clock):
    headers = auth_header(register(client)["access_token"])
    assert start(client, headers, 999_999).status_code == 404


# --- #24 Save answers ---


def test_save_and_change_answers_without_feedback(client, mock, clock):
    headers = ready_user(client, mock)
    attempt = start(client, headers, mock["mock"]).json()["attempt_id"]
    q1 = mock["questions"][1]

    response = save(client, headers, attempt, q1, "d")
    assert response.json() == {"question_id": q1, "saved": True, "answered_count": 1, "total_questions": 6}
    assert "correct" not in response.text  # no feedback before submitting

    assert save(client, headers, attempt, q1, "a").json()["answered_count"] == 1  # changed, not added
    assert start(client, headers, mock["mock"]).json()["saved_answers"] == {str(q1): "a"}


def test_question_from_another_test_is_refused(client, mock, clock):
    from app.db import SessionLocal

    headers = ready_user(client, mock)
    attempt = start(client, headers, mock["mock"]).json()["attempt_id"]
    with SessionLocal() as db, db.begin():
        quiz_question = Question(quiz_id=mock["quiz1"], part="vocabulary", type="kanji_reading",
                                 prompt_ruby=[{"text": "x"}], options=OPTIONS, correct_option_id="a")
        db.add(quiz_question)
        db.flush()
        other_id = quiz_question.id
    response = save(client, headers, attempt, other_id, "a")
    assert response.status_code == 400
    assert error_code(response) == "question_not_in_attempt"


def test_no_answers_after_the_time_is_up(client, mock, clock):
    headers = ready_user(client, mock)
    attempt = start(client, headers, mock["mock"]).json()["attempt_id"]
    clock.move(minutes=29, seconds=59)
    assert save(client, headers, attempt, mock["questions"][1], "a").status_code == 200
    clock.move(seconds=1)  # exactly 30:00
    response = save(client, headers, attempt, mock["questions"][2], "b")
    assert response.status_code == 400
    assert error_code(response) == "attempt_finished"


# --- #25 Submit and #26 Result ---


def test_submit_scores_on_the_server(client, mock, clock):
    headers = ready_user(client, mock)
    attempt = start(client, headers, mock["mock"]).json()["attempt_id"]
    q = mock["questions"]
    for number, option in ((1, "a"), (2, "c"), (3, "c"), (5, "a")):  # 3 right, 1 wrong, 2 skipped
        save(client, headers, attempt, q[number], option)
    clock.move(minutes=27, seconds=40)

    response = submit(client, headers, attempt)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["submitted_at"] == "2026-10-23T02:27:40Z"
    assert body["submitted_by"] == "user"
    assert (body["time_used_seconds"], body["time_limit_seconds"]) == (1660, 1800)
    assert body["score"] == {"correct": 3, "total": 6, "percent": 50}
    assert body["parts"] == [
        {"part": "vocabulary", "correct": 1, "total": 2},
        {"part": "grammar", "correct": 1, "total": 2},
        {"part": "reading", "correct": 1, "total": 2},
    ]
    assert body["pass_prediction"] == 25  # LK 50%, reading 50%: score 50, 10 points under 60
    assert body["pass_prediction_warning"] is None
    assert body["counts_for_prediction"] is True

    review = {item["number"]: item for item in body["questions"]}
    assert review[2] == {"id": q[2], "number": 2, "part": "vocabulary", "prompt_ruby": [{"text": "問2"}], "options": OPTIONS,
                         "selected_option_id": "c", "correct_option_id": "b", "is_correct": False}
    assert review[4]["selected_option_id"] is None and review[4]["is_correct"] is False
    assert result(client, headers, attempt).json() == body  # #26 shows the same


def test_submitting_twice_is_refused(client, mock, clock):
    headers = ready_user(client, mock)
    attempt = start(client, headers, mock["mock"]).json()["attempt_id"]
    submit(client, headers, attempt)
    response = submit(client, headers, attempt)
    assert response.status_code == 400
    assert error_code(response) == "already_submitted"
    assert save(client, headers, attempt, mock["questions"][1], "a").status_code == 400


def test_result_before_submitting_is_refused(client, mock, clock):
    headers = ready_user(client, mock)
    attempt = start(client, headers, mock["mock"]).json()["attempt_id"]
    response = result(client, headers, attempt)
    assert response.status_code == 400
    assert error_code(response) == "not_submitted"
    assert "correct_option_id" not in response.text


def test_time_up_submits_automatically_with_saved_answers(client, mock, clock):
    headers = ready_user(client, mock)
    attempt = start(client, headers, mock["mock"]).json()["attempt_id"]
    save(client, headers, attempt, mock["questions"][1], "a")
    clock.move(hours=5)  # the user closed the app and never came back in time

    body = result(client, headers, attempt).json()
    assert body["submitted_by"] == "timeout"
    assert body["submitted_at"] == "2026-10-23T02:30:00Z"  # at 0, not when we noticed
    assert body["time_used_seconds"] == 1800
    assert body["score"] == {"correct": 1, "total": 6, "percent": 17}
    # Pressing "submit" late shows that result instead of an error.
    assert submit(client, headers, attempt).json() == body


def test_time_up_unlocks_the_next_session_without_opening_the_test(client, mock, clock):
    headers = ready_user(client, mock)
    start(client, headers, mock["mock"])
    session = client.get(f"{API}/sessions/{mock['s1']}", headers=headers).json()
    assert session["mock_test"]["status"] == "in_progress"

    clock.move(minutes=31)
    session = client.get(f"{API}/sessions/{mock['s1']}", headers=headers).json()
    assert session["mock_test"]["status"] == "completed"
    assert session["mock_test"]["attempts"] == 1
    assert client.get(f"{API}/sessions/{mock['s2']}", headers=headers).status_code == 200


def test_submitted_test_shows_on_the_session_screen(client, mock, clock):
    headers = ready_user(client, mock)
    attempt = start(client, headers, mock["mock"]).json()["attempt_id"]
    for number in (1, 2, 3):
        save(client, headers, attempt, mock["questions"][number], RIGHT[number])
    submit(client, headers, attempt)
    session = client.get(f"{API}/sessions/{mock['s1']}", headers=headers).json()
    assert session["mock_test"] == {"id": mock["mock"], "status": "completed", "best_score": 50, "last_score": 50, "attempts": 1}


# --- Retakes ---


def test_retake_is_new_and_does_not_count_for_the_prediction(client, mock, clock):
    headers = ready_user(client, mock)
    first = start(client, headers, mock["mock"]).json()["attempt_id"]
    submit(client, headers, first)

    clock.move(days=1)
    response = start(client, headers, mock["mock"])
    assert response.status_code == 201
    retake = response.json()
    assert retake["attempt_id"] != first
    assert retake["saved_answers"] == {}
    assert retake["ends_at"] == "2026-10-24T02:30:00Z"
    submit(client, headers, retake["attempt_id"])
    assert result(client, headers, retake["attempt_id"]).json()["counts_for_prediction"] is False
    assert result(client, headers, first).json()["counts_for_prediction"] is True


def test_after_a_reset_the_first_attempt_counts_again(client, mock, clock):
    from app.db import SessionLocal

    headers = ready_user(client, mock)
    first = start(client, headers, mock["mock"]).json()["attempt_id"]
    submit(client, headers, first)
    old_open = start(client, headers, mock["mock"]).json()["attempt_id"]  # a retake left open

    with SessionLocal() as db, db.begin():
        db.execute(update(User).values(current_round=User.current_round + 1))
    add_quiz_attempt(mock["quiz1"], 80)
    complete_units(client, headers, mock, range(1, 11))
    add_quiz_attempt(mock["quiz2"], 80)

    fresh = start(client, headers, mock["mock"])
    assert fresh.status_code == 201
    attempt = fresh.json()["attempt_id"]
    assert attempt != old_open
    submit(client, headers, attempt)
    assert result(client, headers, attempt).json()["counts_for_prediction"] is True
    with SessionLocal() as db:
        assert db.get(MockAttempt, old_open) is None  # the open attempt from the old round is gone
        assert db.get(MockAttempt, first) is not None  # finished ones stay as history


# --- Other users ---


def test_someone_elses_attempt_is_403(client, mock, clock):
    headers = ready_user(client, mock)
    attempt = start(client, headers, mock["mock"]).json()["attempt_id"]
    other = auth_header(register(client, email="other@example.com", username="other")["access_token"])
    for response in (
        save(client, other, attempt, mock["questions"][1], "a"),
        submit(client, other, attempt),
        result(client, other, attempt),
    ):
        assert response.status_code == 403
        assert error_code(response) == "not_your_attempt"


def test_unknown_attempt_is_404(client, clock):
    headers = auth_header(register(client)["access_token"])
    assert submit(client, headers, 999_999).status_code == 404


def test_needs_login(client):
    assert client.post(f"{API}/mock-tests/1/attempts").status_code == 401
    assert client.get(f"{API}/mock-attempts/1/result").status_code == 401


# --- Small pieces ---


@pytest.mark.parametrize(("correct", "total", "expected"), [(1, 8, 13), (1, 6, 17), (3, 6, 50), (0, 6, 0), (6, 6, 100), (0, 0, 0)])
def test_percent_rounds_half_up(correct, total, expected):
    assert mock_clock.percent(correct, total) == expected


def test_only_one_open_attempt_in_the_database(client, mock, clock):
    from app.db import SessionLocal

    headers = ready_user(client, mock)
    start(client, headers, mock["mock"])
    start(client, headers, mock["mock"])
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(MockAttempt)) == 1
