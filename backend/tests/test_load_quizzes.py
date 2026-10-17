"""Quiz files: the format checks, and loading them into the database safely."""

import copy
import json
import sys
from collections.abc import Iterator

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select, text

from app.content import load_quizzes
from app.content.load_units import save_unit
from app.content.quiz_schema import QuizFile
from app.content.schema import UnitFile
from app.models import AIExplanation, Question, Quiz, QuizAttempt, QuizAttemptQuestion, User
from tests.test_auth import register

MY = "မြန်မာ"  # any Burmese text


def make_unit(session: int, unit: int) -> dict:
    example = {"ruby": [{"text": "例文", "reading": "れいぶん"}, {"text": "です。"}], "translation_my": MY}
    return {
        "session_number": session,
        "unit_number": unit,
        "words": [
            {"position": p, "word": "概念", "furigana": "がいねん", "ruby": [{"text": "概念", "reading": "がいねん"}],
             "meaning_my": MY, "examples": [example, example]}
            for p in range(1, 21)
        ],
        "grammar": {"pattern": "〜ならでは", "meaning_my": MY, "how_to_use": "N + ならでは", "how_to_use_my": MY,
                    "examples": [example, example]},
    }


def vocab(n: int, unit: int = 1) -> dict:
    return {
        "number": n, "part": "vocabulary", "type": "kanji_reading", "unit_number": unit, "word_position": 1 + n % 20,
        "prompt_ruby": [{"text": f"問{n}、彼の"}, {"text": "概念"}, {"text": "はあたらしい。"}],
        "underline": "概念",
        "options": [{"id": "a", "text": "がいねん"}, {"id": "b", "text": "がいめん"}, {"id": "c", "text": "かいねん"}, {"id": "d", "text": "かいめん"}],
        "correct_option_id": "a",
    }


def grammar(n: int, unit: int = 1) -> dict:
    return {
        "number": n, "part": "grammar", "type": "grammar_form", "unit_number": unit,
        "prompt_ruby": [{"text": f"問{n}。この"}, {"text": "店", "reading": "みせ"}, {"text": "（　）の味だ。"}],
        "options": [{"id": "a", "text": "ならでは"}, {"id": "b", "text": "ばかり"}, {"id": "c", "text": "だけ"}, {"id": "d", "text": "こそ"}],
        "correct_option_id": "a",
    }


def make_quiz(count: int = 20) -> dict:
    questions = [vocab(n, unit=1 + n % 5) for n in range(1, count - 3)] + [grammar(n, unit=1 + n % 5) for n in range(count - 3, count + 1)]
    return {"session_number": 1, "quiz_number": 1, "questions": questions}


# --- Format checks (no database) ---


def test_a_good_quiz_file_passes():
    QuizFile.model_validate(make_quiz())


def broken(change) -> dict:
    quiz = make_quiz()
    change(quiz)
    return quiz


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda q: q["questions"][0].update(type="grammar_form"), "is not a vocabulary type"),
        (lambda q: q["questions"][0].pop("word_position"), "need word_position"),
        (lambda q: q["questions"][-1].update(word_position=3), "leave out word_position"),
        (lambda q: q["questions"][0].update(underline="あたらしい"), "exactly one piece"),
        (lambda q: q["questions"][0]["prompt_ruby"][1].update(reading="がいねん"), "gives the answer away"),
        (lambda q: q["questions"][0]["options"][1].update(text="ガイネン"), "hiragana"),
        (lambda q: q["questions"][0]["options"][1].update(text="がいねん"), "all be different"),
        (lambda q: q["questions"][0]["options"].reverse(), "a, b, c, d in that order"),
        (lambda q: q["questions"][0].update(correct_option_id="e"), "correct_option_id"),
        (lambda q: q["questions"][0].update(number=99), "each used once"),
        (lambda q: q["questions"][0].update(unit_number=6), "covers units 1 to 5"),
        (lambda q: q["questions"].pop(), "at least 20"),
        (lambda q: q["questions"][1].update(prompt_ruby=copy.deepcopy(q["questions"][0]["prompt_ruby"])), "exactly the same"),
        (lambda q: q.update(questions=[vocab(n) for n in range(1, 21)]), "grammar questions"),
        (lambda q: q["questions"][0].update(is_correct=True), "Extra inputs"),
        (lambda q: q["questions"][0]["prompt_ruby"][2].update(reading="あたら"), "no kanji"),
    ],
)
def test_broken_quiz_files_are_refused(change, message):
    with pytest.raises(ValidationError) as caught:
        QuizFile.model_validate(broken(change))
    assert message in str(caught.value)


def test_file_name_must_match_the_content(tmp_path):
    (tmp_path / "s01_q2.json").write_text(json.dumps(make_quiz()), encoding="utf-8")  # inside says quiz 1
    (tmp_path / "quiz1.json").write_text("{}", encoding="utf-8")
    _, problems = load_quizzes.read_quiz_files(tmp_path)
    assert any("do not match the file name" in p for p in problems)
    assert any("must look like s01_q1.json" in p for p in problems)


# --- Loading into the database ---


@pytest.fixture
def units() -> Iterator[None]:
    """Units 1 to 5 of session 1 in the database. Everything is removed after the test."""
    from app.db import SessionLocal, engine

    with SessionLocal() as db, db.begin():
        for n in range(1, 6):
            save_unit(db, UnitFile.model_validate(make_unit(1, n)))
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE sessions RESTART IDENTITY CASCADE"))


def load(quiz: dict) -> None:
    from app.db import SessionLocal

    with SessionLocal() as db, db.begin():
        load_quizzes.save_quiz(db, QuizFile.model_validate(quiz))


def db_problems(quiz: dict) -> list[str]:
    from pathlib import Path

    from app.db import SessionLocal

    with SessionLocal() as db:
        return load_quizzes.check_against_database(db, [(Path("s01_q1.json"), QuizFile.model_validate(quiz))])


def question_ids() -> dict[int, int]:
    from app.db import SessionLocal

    with SessionLocal() as db:
        return {q.number: q.id for q in db.scalars(select(Question))}


def test_loading_creates_the_quiz_and_links_words_and_grammar(units):
    from app.db import SessionLocal

    load(make_quiz(25))
    with SessionLocal() as db:
        quiz = db.scalar(select(Quiz))
        assert (quiz.number, quiz.first_unit, quiz.last_unit, quiz.question_count, quiz.pass_mark) == (1, 1, 5, 20, 70)
        questions = list(db.scalars(select(Question).order_by(Question.number)))
        assert len(questions) == 25
        assert all(q.word_id is not None and q.grammar_id is None for q in questions if q.part == "vocabulary")
        assert all(q.grammar_id is not None and q.word_id is None for q in questions if q.part == "grammar")
        assert questions[0].prompt_ruby[1] == {"text": "概念"}  # no reading stored on the tested word


def test_loading_again_keeps_question_ids(units):
    load(make_quiz())
    before = question_ids()
    load(make_quiz())
    assert question_ids() == before


def test_changing_a_question_removes_its_saved_why_answers(units):
    from app.db import SessionLocal

    load(make_quiz())
    ids = question_ids()
    with SessionLocal() as db, db.begin():
        for number in (1, 2):
            db.add(AIExplanation(question_id=ids[number], selected_option_id="b", why_correct_my=MY, model="test"))

    quiz = make_quiz()
    quiz["questions"][0]["options"][1]["text"] = "がいじん"  # question 1 changes, question 2 does not
    load(quiz)
    with SessionLocal() as db:
        kept = set(db.scalars(select(AIExplanation.question_id)))
    assert kept == {ids[2]}


def test_removing_an_unused_question_deletes_it(units):
    load(make_quiz(21))
    load(make_quiz(20))
    assert len(question_ids()) == 20


def test_removing_an_answered_question_is_refused(client, units):
    from app.db import SessionLocal

    load(make_quiz(21))
    register(client)
    ids = question_ids()
    with SessionLocal() as db, db.begin():
        user = db.scalar(select(User))
        attempt = QuizAttempt(user_id=user.id, quiz_id=db.scalar(select(Quiz.id)), round=1)
        db.add(attempt)
        db.flush()
        db.add(QuizAttemptQuestion(attempt_id=attempt.id, question_id=ids[21], position=1))

    with pytest.raises(load_quizzes.LoadRefused, match="already answered"):
        load(make_quiz(20))
    assert len(question_ids()) == 21  # nothing changed


def test_database_checks_find_missing_units_and_wrong_answers(units):
    assert db_problems(make_quiz()) == []

    quiz = make_quiz()
    quiz["questions"][0]["correct_option_id"] = "b"  # がいめん is not the reading in the unit
    problems = db_problems(quiz)
    assert len(problems) == 1 and "not the reading of 概念" in problems[0]


def test_quiz_for_units_not_loaded_is_refused():
    problems = db_problems(make_quiz())
    assert problems and "not in the database yet" in problems[0]


def test_command_line_check_mode_changes_nothing(units, tmp_path, monkeypatch, capsys):
    from app.db import SessionLocal

    (tmp_path / "s01_q1.json").write_text(json.dumps(make_quiz(), ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["load_quizzes", "--check", str(tmp_path)])
    assert load_quizzes.main() == 0
    assert "passed the checks" in capsys.readouterr().out
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Question)) == 0

    monkeypatch.setattr(sys, "argv", ["load_quizzes", str(tmp_path)])
    assert load_quizzes.main() == 0
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Question)) == 20
