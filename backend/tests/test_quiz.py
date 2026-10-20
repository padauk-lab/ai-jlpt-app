"""#19 to #22: the quiz. Includes cheating attempts (peeking at answers, answering twice, using someone else's attempt)."""

import pytest
from sqlalchemy import func, select

from app.models import Question, QuizAttempt
from tests.test_auth import API, auth_header, error_code, register
from tests.test_study import complete_units, content, user_header  # noqa: F401  (content is a fixture)

OPTIONS = [{"id": i, "text": f"選択{i}"} for i in "abcd"]
BANK_SIZE = 25


@pytest.fixture
def bank(content):
    """25 questions for Quiz 1. The correct answer is 'a' for odd numbers, 'b' for even ones."""
    from app.db import SessionLocal

    with SessionLocal() as db, db.begin():
        for n in range(1, BANK_SIZE + 1):
            db.add(Question(
                quiz_id=content["quiz1"], number=n, part="vocabulary", type="kanji_reading",
                prompt_ruby=[{"text": f"問{n}"}], underline=None, options=OPTIONS,
                correct_option_id="a" if n % 2 else "b",
            ))
    return content


def correct_answers() -> dict[int, str]:
    from app.db import SessionLocal

    with SessionLocal() as db:
        return dict(db.execute(select(Question.id, Question.correct_option_id)).all())


def ready_user(client, content) -> dict[str, str]:
    """A user who finished units 1 to 5, so Quiz 1 is open."""
    headers = user_header(client)
    complete_units(client, headers, content, range(1, 6))
    return headers


def start(client, headers, quiz_id):
    return client.post(f"{API}/quizzes/{quiz_id}/attempts", headers=headers)


def answer(client, headers, attempt_id, question_id, option):
    body = {"question_id": question_id, "selected_option_id": option}
    return client.post(f"{API}/quiz-attempts/{attempt_id}/answers", json=body, headers=headers)


def finish(client, headers, attempt_id):
    return client.post(f"{API}/quiz-attempts/{attempt_id}/finish", headers=headers)


def take_quiz(client, headers, quiz_id, right: int) -> dict:
    """Start a quiz, answer `right` questions correctly and the rest wrongly, and finish."""
    attempt = start(client, headers, quiz_id).json()
    solutions = correct_answers()
    for i, q in enumerate(attempt["questions"]):
        good = solutions[q["id"]]
        bad = "d" if good != "d" else "c"
        answer(client, headers, attempt["attempt_id"], q["id"], good if i < right else bad)
    return finish(client, headers, attempt["attempt_id"]).json()


# --- #19 Start ---


def test_quiz_is_locked_until_units_1_to_5_are_done(client, bank):
    headers = user_header(client)
    response = start(client, headers, bank["quiz1"])
    assert response.status_code == 403
    assert error_code(response) == "quiz_locked"


def test_start_gives_20_random_questions_without_answers(client, bank):
    headers = ready_user(client, bank)
    response = start(client, headers, bank["quiz1"])
    assert response.status_code == 201
    body = response.json()
    assert body["quiz_id"] == bank["quiz1"]
    assert body["total_questions"] == 20
    assert [q["number"] for q in body["questions"]] == list(range(1, 21))
    ids = [q["id"] for q in body["questions"]]
    assert len(set(ids)) == 20 and set(ids) <= set(correct_answers())
    assert "correct_option_id" not in response.text  # the most important rule
    assert set(body["questions"][0]) == {"id", "number", "type", "prompt_ruby", "options"}


def test_quiz_without_questions_is_404(client, content):
    headers = ready_user(client, content)
    assert start(client, headers, content["quiz1"]).status_code == 404


def test_starting_again_throws_away_the_unfinished_attempt(client, bank):
    from app.db import SessionLocal

    headers = ready_user(client, bank)
    first = start(client, headers, bank["quiz1"]).json()
    second = start(client, headers, bank["quiz1"]).json()
    assert first["attempt_id"] != second["attempt_id"]
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(QuizAttempt)) == 1
    assert answer(client, headers, first["attempt_id"], first["questions"][0]["id"], "a").status_code == 404


# --- #20 Answer ---


def test_answer_gives_instant_feedback(client, bank):
    headers = ready_user(client, bank)
    attempt = start(client, headers, bank["quiz1"]).json()
    solutions = correct_answers()
    q1, q2 = attempt["questions"][0]["id"], attempt["questions"][1]["id"]

    right = answer(client, headers, attempt["attempt_id"], q1, solutions[q1]).json()
    assert right == {"question_id": q1, "is_correct": True, "selected_option_id": solutions[q1],
                     "correct_option_id": solutions[q1], "answered": 1, "correct_so_far": 1}

    wrong_pick = "d" if solutions[q2] != "d" else "c"
    wrong = answer(client, headers, attempt["attempt_id"], q2, wrong_pick).json()
    assert wrong["is_correct"] is False
    assert wrong["correct_option_id"] == solutions[q2]
    assert (wrong["answered"], wrong["correct_so_far"]) == (2, 1)


def test_each_question_can_be_answered_only_once(client, bank):
    headers = ready_user(client, bank)
    attempt = start(client, headers, bank["quiz1"]).json()
    q = attempt["questions"][0]["id"]
    assert answer(client, headers, attempt["attempt_id"], q, "c").status_code == 200
    again = answer(client, headers, attempt["attempt_id"], q, correct_answers()[q])
    assert again.status_code == 400
    assert error_code(again) == "already_answered"


def test_only_questions_of_this_attempt_can_be_answered(client, bank):
    headers = ready_user(client, bank)
    attempt = start(client, headers, bank["quiz1"]).json()
    used = {q["id"] for q in attempt["questions"]}
    outside = next(qid for qid in correct_answers() if qid not in used)  # in the bank, but not picked
    response = answer(client, headers, attempt["attempt_id"], outside, "a")
    assert response.status_code == 400
    assert error_code(response) == "question_not_in_attempt"


@pytest.mark.parametrize(
    "body",
    [
        {"question_id": 1, "selected_option_id": "e"},
        {"question_id": "1", "selected_option_id": "a"},
        {"question_id": 1, "selected_option_id": "a", "is_correct": True},
        {"question_id": 1},
    ],
)
def test_bad_answers_are_refused(client, bank, body):
    headers = ready_user(client, bank)
    attempt = start(client, headers, bank["quiz1"]).json()
    response = client.post(f"{API}/quiz-attempts/{attempt['attempt_id']}/answers", json=body, headers=headers)
    assert response.status_code == 422


# --- #21 Finish ---


def test_finish_scores_on_the_server_and_70_percent_passes(client, bank):
    headers = ready_user(client, bank)
    result = take_quiz(client, headers, bank["quiz1"], right=14)
    assert (result["correct"], result["total"], result["score"]) == (14, 20, 70)
    assert result["passed"] is True
    assert result["pass_mark"] == 70
    assert result["best_score"] == 70
    assert len(result["wrong_questions"]) == 6


def test_unanswered_questions_count_as_wrong(client, bank):
    headers = ready_user(client, bank)
    attempt = start(client, headers, bank["quiz1"]).json()
    q = attempt["questions"][0]["id"]
    answer(client, headers, attempt["attempt_id"], q, correct_answers()[q])
    result = finish(client, headers, attempt["attempt_id"]).json()
    assert (result["correct"], result["score"], result["passed"]) == (1, 5, False)
    assert len(result["wrong_questions"]) == 19


def test_finishing_twice_is_safe_and_answering_after_finish_is_refused(client, bank):
    headers = ready_user(client, bank)
    attempt = start(client, headers, bank["quiz1"]).json()
    first = finish(client, headers, attempt["attempt_id"]).json()
    assert finish(client, headers, attempt["attempt_id"]).json() == first
    late = answer(client, headers, attempt["attempt_id"], attempt["questions"][0]["id"], "a")
    assert late.status_code == 400
    assert error_code(late) == "attempt_finished"


def test_best_score_keeps_the_highest(client, bank):
    headers = ready_user(client, bank)
    take_quiz(client, headers, bank["quiz1"], right=18)
    later = take_quiz(client, headers, bank["quiz1"], right=10)
    assert later["score"] == 50
    assert later["best_score"] == 90


# --- #22 Review ---


def test_review_shows_answers_after_finishing(client, bank):
    headers = ready_user(client, bank)
    attempt = start(client, headers, bank["quiz1"]).json()
    early = client.get(f"{API}/quiz-attempts/{attempt['attempt_id']}", headers=headers)
    assert early.status_code == 400
    assert error_code(early) == "attempt_not_finished"

    first_q = attempt["questions"][0]["id"]
    answer(client, headers, attempt["attempt_id"], first_q, correct_answers()[first_q])
    finish(client, headers, attempt["attempt_id"])
    review = client.get(f"{API}/quiz-attempts/{attempt['attempt_id']}", headers=headers).json()
    assert review["score"] == 5 and review["passed"] is False and review["finished_at"].endswith("Z")
    assert [q["id"] for q in review["questions"]] == [q["id"] for q in attempt["questions"]]
    assert review["questions"][0]["is_correct"] is True
    assert review["questions"][1]["selected_option_id"] is None  # not answered
    assert review["questions"][1]["is_correct"] is False
    assert all(q["correct_option_id"] in "abcd" for q in review["questions"])


# --- Unlocking ---


def test_passing_quiz_1_unlocks_unit_6(client, bank):
    headers = ready_user(client, bank)
    take_quiz(client, headers, bank["quiz1"], right=10)  # failed
    session = client.get(f"{API}/sessions/{bank['s1']}", headers=headers).json()
    assert session["quizzes"][0]["status"] == "failed"
    assert session["units"][5]["status"] == "locked"

    take_quiz(client, headers, bank["quiz1"], right=15)  # passed
    session = client.get(f"{API}/sessions/{bank['s1']}", headers=headers).json()
    assert session["quizzes"][0]["status"] == "passed"
    assert session["quizzes"][0]["best_score"] == 75
    assert session["units"][5]["status"] == "available"


def test_quiz_locks_again_after_a_progress_reset(client, bank):
    headers = ready_user(client, bank)
    client.post(f"{API}/onboarding", json={"last_level": "not_taken"}, headers=headers)
    take_quiz(client, headers, bank["quiz1"], right=20)
    client.post(f"{API}/me/reset-progress", json={"confirm": "RESET"}, headers=headers)
    assert start(client, headers, bank["quiz1"]).status_code == 403


# --- Other users and login ---


def test_someone_elses_attempt_cannot_be_used(client, bank):
    owner = ready_user(client, bank)
    attempt = start(client, owner, bank["quiz1"]).json()
    other = auth_header(register(client, email="other@example.com", username="other")["access_token"])
    aid, qid = attempt["attempt_id"], attempt["questions"][0]["id"]
    for response in (
        answer(client, other, aid, qid, "a"),
        finish(client, other, aid),
        client.get(f"{API}/quiz-attempts/{aid}", headers=other),
    ):
        assert response.status_code == 403
        assert error_code(response) == "not_your_attempt"


def test_quiz_needs_login(client, bank):
    assert client.post(f"{API}/quizzes/{bank['quiz1']}/attempts").status_code == 401
    assert client.post(f"{API}/quiz-attempts/1/finish").status_code == 401
    assert client.get(f"{API}/quiz-attempts/1").status_code == 401
