"""#28 POST /ai/explain ("Why?"): who may ask, the saved answers, and what happens when the AI fails.

The real AI is never called: explain_answer() is replaced by a fake that counts its calls.
"""

import pytest
from sqlalchemy import func, select

from app.ai import explain as ai_explain
from app.ai.llm import AIUnavailableError
from app.models import AIExplanation, Question, ReadingPassage
from tests.test_auth import API, auth_header, error_code, register
from tests.test_quiz import answer, bank, correct_answers, finish, ready_user, start  # noqa: F401  (bank is a fixture)
from tests.test_study import add_mock_attempt, content  # noqa: F401  (content is a fixture)

MY = "မြန်မာ"


@pytest.fixture
def ai(monkeypatch) -> list:
    """A fake AI. Returns the list of calls, so tests can check when the AI was (not) asked."""
    calls: list = []

    def fake_explain_answer(question, selected, passage_text=None):
        calls.append((question.id, selected, passage_text))
        others = {o: f"{MY} {o}" for o in "abcd" if o not in (question.correct_option_id, selected)}
        return {
            "why_correct_my": f"{MY} correct",
            "why_selected_wrong_my": None if selected == question.correct_option_id else f"{MY} wrong",
            "other_options_my": others,
            "model": "test-model",
        }

    monkeypatch.setattr(ai_explain, "explain_answer", fake_explain_answer)
    return calls


def why(client, headers, question_id, option):
    return client.post(f"{API}/ai/explain", json={"question_id": question_id, "selected_option_id": option}, headers=headers)


def answered_question(client, headers, quiz_id) -> tuple[int, str, str]:
    """Start a quiz and answer its first question wrongly. Returns (question id, correct, picked)."""
    attempt = start(client, headers, quiz_id).json()
    question_id = attempt["questions"][0]["id"]
    correct = correct_answers()[question_id]
    wrong = "d" if correct != "d" else "c"
    answer(client, headers, attempt["attempt_id"], question_id, wrong)
    return question_id, correct, wrong


# --- Who may ask ---


def test_before_answering_is_403_so_nobody_gets_answers_early(client, bank, ai):
    headers = ready_user(client, bank)
    attempt = start(client, headers, bank["quiz1"]).json()
    response = why(client, headers, attempt["questions"][0]["id"], "a")
    assert response.status_code == 403
    assert error_code(response) == "not_answered_yet"
    assert "correct_option_id" not in response.text
    assert ai == []  # the AI was never asked


def test_question_not_in_any_of_my_attempts_is_403(client, bank, ai):
    headers = ready_user(client, bank)
    question_id = min(correct_answers())  # exists, but this user never got it
    assert why(client, headers, question_id, "a").status_code == 403


def test_someone_elses_answer_does_not_count(client, bank, ai):
    headers = ready_user(client, bank)
    question_id, _, wrong = answered_question(client, headers, bank["quiz1"])
    other = auth_header(register(client, email="other@example.com", username="other")["access_token"])
    assert why(client, other, question_id, wrong).status_code == 403


def test_unknown_question_is_404(client, ai):
    headers = auth_header(register(client)["access_token"])
    response = why(client, headers, 999_999, "a")
    assert response.status_code == 404
    assert error_code(response) == "not_found"


def test_needs_login(client):
    assert client.post(f"{API}/ai/explain", json={"question_id": 1, "selected_option_id": "a"}).status_code == 401


@pytest.mark.parametrize(
    "body",
    [
        {"question_id": 1, "selected_option_id": "e"},
        {"question_id": "1", "selected_option_id": "a"},
        {"question_id": 0, "selected_option_id": "a"},
        {"question_id": 1, "selected_option_id": "a", "model": "x"},
        {"question_id": 1},
    ],
)
def test_bad_requests_are_refused(client, body, ai):
    headers = auth_header(register(client)["access_token"])
    assert client.post(f"{API}/ai/explain", json=body, headers=headers).status_code == 422


# --- The answer ---


def test_wrong_pick_gets_the_full_explanation(client, bank, ai):
    headers = ready_user(client, bank)
    question_id, correct, wrong = answered_question(client, headers, bank["quiz1"])
    response = why(client, headers, question_id, wrong)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["question_id"] == question_id
    assert body["correct_option_id"] == correct
    assert body["why_correct_my"] == f"{MY} correct"
    assert body["why_selected_wrong_my"] == f"{MY} wrong"
    assert set(body["other_options_my"]) == set("abcd") - {correct, wrong}


def test_correct_pick_has_no_wrong_explanation(client, bank, ai):
    headers = ready_user(client, bank)
    attempt = start(client, headers, bank["quiz1"]).json()
    question_id = attempt["questions"][0]["id"]
    correct = correct_answers()[question_id]
    answer(client, headers, attempt["attempt_id"], question_id, correct)
    body = why(client, headers, question_id, correct).json()
    assert body["why_selected_wrong_my"] is None
    assert len(body["other_options_my"]) == 3


def test_skipped_question_in_a_finished_quiz_is_allowed(client, bank, ai):
    """The review (#22) already shows its answer, so explaining it gives nothing away."""
    headers = ready_user(client, bank)
    attempt = start(client, headers, bank["quiz1"]).json()
    skipped = attempt["questions"][5]["id"]
    assert why(client, headers, skipped, "a").status_code == 403  # not finished yet
    finish(client, headers, attempt["attempt_id"])
    assert why(client, headers, skipped, "a").status_code == 200


def test_mock_test_question_needs_a_submitted_mock_test(client, content, ai):
    from app.db import SessionLocal

    with SessionLocal() as db, db.begin():
        passage = ReadingPassage(mock_test_id=content["mock"], length="short", position=1,
                                 text_ruby=[{"text": "本文", "reading": "ほんぶん"}, {"text": "です。"}])
        db.add(passage)
        db.flush()
        question = Question(mock_test_id=content["mock"], passage_id=passage.id, part="reading", type="reading",
                            number=46, prompt_ruby=[{"text": "問い"}], options=[{"id": i, "text": i} for i in "abcd"],
                            correct_option_id="c")
        db.add(question)
        db.flush()
        question_id = question.id

    headers = auth_header(register(client)["access_token"])
    assert why(client, headers, question_id, "a").status_code == 403
    add_mock_attempt(content["mock"], correct=30)
    assert why(client, headers, question_id, "a").status_code == 200
    assert ai[-1] == (question_id, "a", "本文です。")  # the passage is sent to the AI as plain text


# --- Saved answers ---


def saved_count() -> int:
    from app.db import SessionLocal

    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(AIExplanation))


def test_the_ai_is_asked_only_once_per_question_and_choice(client, bank, ai):
    headers = ready_user(client, bank)
    question_id, _, wrong = answered_question(client, headers, bank["quiz1"])
    first = why(client, headers, question_id, wrong).json()
    second = why(client, headers, question_id, wrong).json()
    assert first == second
    assert len(ai) == 1
    assert saved_count() == 1

    # Another user who finished a quiz with the same question gets the saved answer too.
    other = auth_header(register(client, email="other@example.com", username="other")["access_token"])
    give_finished_attempt("other@example.com", bank["quiz1"], question_id)
    assert why(client, other, question_id, wrong).json() == first
    assert len(ai) == 1


def give_finished_attempt(email: str, quiz_id: int, question_id: int) -> None:
    from datetime import UTC, datetime

    from app.db import SessionLocal
    from app.models import QuizAttempt, QuizAttemptQuestion, User

    with SessionLocal() as db, db.begin():
        user = db.scalar(select(User).where(User.email == email))
        attempt = QuizAttempt(user_id=user.id, quiz_id=quiz_id, round=1, finished_at=datetime.now(UTC),
                              correct=0, score=0, passed=False)
        db.add(attempt)
        db.flush()
        db.add(QuizAttemptQuestion(attempt_id=attempt.id, question_id=question_id, position=1))


def test_a_different_choice_is_a_new_question_for_the_ai(client, bank, ai):
    headers = ready_user(client, bank)
    question_id, correct, wrong = answered_question(client, headers, bank["quiz1"])
    why(client, headers, question_id, wrong)
    why(client, headers, question_id, correct)
    assert len(ai) == 2
    assert saved_count() == 2


# --- When the AI fails ---


def test_ai_failure_is_503_and_nothing_is_saved(client, bank, monkeypatch):
    def broken(*args, **kwargs):
        raise AIUnavailableError("LLM returned HTTP 500")

    monkeypatch.setattr(ai_explain, "explain_answer", broken)
    headers = ready_user(client, bank)
    question_id, _, wrong = answered_question(client, headers, bank["quiz1"])
    response = why(client, headers, question_id, wrong)
    assert response.status_code == 503
    assert error_code(response) == "ai_unavailable"
    assert "HTTP 500" not in response.text  # details stay in the server log
    assert saved_count() == 0


def test_after_a_failure_the_next_try_works(client, bank, ai, monkeypatch):
    headers = ready_user(client, bank)
    question_id, _, wrong = answered_question(client, headers, bank["quiz1"])
    working = ai_explain.explain_answer

    def broken(*args, **kwargs):
        raise AIUnavailableError("busy")

    monkeypatch.setattr(ai_explain, "explain_answer", broken)
    assert why(client, headers, question_id, wrong).status_code == 503
    monkeypatch.setattr(ai_explain, "explain_answer", working)
    assert why(client, headers, question_id, wrong).status_code == 200


def test_works_end_to_end_with_the_real_checks(client, bank, monkeypatch):
    """Only the network call is fake: SWYH's prompt building and output checks really run."""
    import json

    def fake_generate_json(system, user):
        data = json.loads(user)
        others = {o: f"{MY} {o}" for o in "abcd" if o not in (data["correct"], data["selected"])}
        return json.dumps({"why_correct_my": MY, "why_selected_wrong_my": MY, "other_options_my": others}, ensure_ascii=False)

    monkeypatch.setattr(ai_explain, "generate_json", fake_generate_json)
    monkeypatch.setenv("LLM_MODEL", "test-model")
    headers = ready_user(client, bank)
    question_id, _, wrong = answered_question(client, headers, bank["quiz1"])
    assert why(client, headers, question_id, wrong).status_code == 200

    from app.db import SessionLocal

    with SessionLocal() as db:
        assert db.scalar(select(AIExplanation.model)) == "test-model"
