"""Mock test files: the format checks, and loading them into the database safely."""

import json
import sys
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select, text

from app.content import load_mock_tests
from app.content.load_units import save_unit
from app.content.mock_schema import MockTestFile
from app.content.schema import UnitFile
from app.models import AIExplanation, MockAttempt, MockTest, Question, ReadingPassage, User
from tests.test_auth import register

MY = "မြန်မာ"


def make_unit(unit: int) -> dict:
    example = {"ruby": [{"text": "例文", "reading": "れいぶん"}, {"text": "です。"}], "translation_my": MY}
    return {
        "session_number": 1,
        "unit_number": unit,
        "words": [
            {"position": p, "word": "抑制", "furigana": "よくせい", "ruby": [{"text": "抑制", "reading": "よくせい"}],
             "meaning_my": MY, "examples": [example, example]}
            for p in range(1, 21)
        ],
        "grammar": {"pattern": "〜ならでは", "meaning_my": MY, "how_to_use": "N + ならでは", "how_to_use_my": MY,
                    "examples": [example, example]},
    }


def options(*texts: str) -> list[dict]:
    return [{"id": i, "text": t} for i, t in zip("abcd", texts, strict=True)]


def knowledge(n: int) -> dict:
    if n <= 30:
        return {
            "number": n, "part": "vocabulary", "type": "kanji_reading", "unit_number": 1 + n % 10, "word_position": 1,
            "prompt_ruby": [{"text": f"問{n}、物価の上昇を"}, {"text": "抑制"}, {"text": "する。"}],
            "underline": "抑制",
            "options": options("よくせい", "ようせい", "おくせい", "よくぜい"),
            "correct_option_id": "a",
        }
    return {
        "number": n, "part": "grammar", "type": "grammar_form",
        "prompt_ruby": [{"text": f"問{n}。この"}, {"text": "店", "reading": "みせ"}, {"text": "（　）の味だ。"}],
        "options": options("ならでは", "ばかり", "だけ", "こそ"),
        "correct_option_id": "a",
    }


def reading(n: int) -> dict:
    return {"number": n, "prompt_ruby": [{"text": f"問{n}：筆者の考えは？"}], "options": options("あ", "い", "う", "え"), "correct_option_id": "c"}


def make_mock() -> dict:
    return {
        "session_number": 1,
        "questions": [knowledge(n) for n in range(1, 46)],
        "passages": [
            {"length": "short", "text_ruby": [{"text": "短い文章です。"}], "questions": [reading(46)]},
            {"length": "medium", "text_ruby": [{"text": "中くらいの文章です。"}], "questions": [reading(47), reading(48)]},
            {"length": "long", "text_ruby": [{"text": "長い", "reading": "ながい"}, {"text": "文章です。"}], "questions": [reading(49), reading(50), reading(51)]},
        ],
    }


# --- Format checks (no database) ---


def test_a_good_mock_file_passes():
    mock = MockTestFile.model_validate(make_mock())
    assert mock.time_limit_minutes == 30


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda m: m["questions"].pop(), "at least 45"),
        (lambda m: m["questions"][0].update(number=2), "numbered 1 to 45"),
        (lambda m: m["questions"][0].update(type="grammar_form"), "is not a vocabulary type"),
        (lambda m: m["questions"][0]["prompt_ruby"][1].update(reading="よくせい"), "gives the answer away"),
        (lambda m: m["questions"][0]["options"][1].update(text="ヨウセイ"), "hiragana"),
        (lambda m: m["questions"][40].update(word_position=3), "only for vocabulary"),
        (lambda m: m["questions"][0].pop("unit_number"), "together with unit_number"),
        (lambda m: m.update(questions=[{**knowledge(n), "number": n} for n in range(1, 31)] + [{**knowledge(1), "number": n} for n in range(31, 46)]), "grammar questions"),
        (lambda m: m["passages"].reverse(), "short, medium and long"),
        (lambda m: m["passages"].pop(), "at least 3"),
        (lambda m: m["passages"][0]["questions"][0].update(number=60), "continue the numbers"),
        (lambda m: m["passages"][1].update(questions=[]), "at least 1"),
        (lambda m: m["passages"][0]["questions"][0].update(correct_option_id="e"), "correct_option_id"),
        (lambda m: m["passages"][0]["questions"][0]["options"][1].update(text="あ"), "all be different"),
        (lambda m: m.update(time_limit_minutes=0), "time_limit_minutes"),
        (lambda m: m["questions"][0].update(answer_hint="a"), "Extra inputs"),
    ],
)
def test_broken_mock_files_are_refused(change, message):
    mock = make_mock()
    change(mock)
    with pytest.raises(ValidationError) as caught:
        MockTestFile.model_validate(mock)
    assert message in str(caught.value)


def test_file_name_must_match(tmp_path):
    (tmp_path / "s02_mock.json").write_text(json.dumps(make_mock()), encoding="utf-8")  # inside says session 1
    (tmp_path / "mock1.json").write_text("{}", encoding="utf-8")
    _, problems = load_mock_tests.read_mock_files(tmp_path)
    assert any("does not match the file name" in p for p in problems)
    assert any("must look like s01_mock.json" in p for p in problems)


# --- Loading into the database ---


@pytest.fixture
def units() -> Iterator[None]:
    from app.db import SessionLocal, engine

    with SessionLocal() as db, db.begin():
        for n in range(1, 11):
            save_unit(db, UnitFile.model_validate(make_unit(n)))
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE sessions RESTART IDENTITY CASCADE"))


def load(mock: dict) -> None:
    from app.db import SessionLocal

    with SessionLocal() as db, db.begin():
        load_mock_tests.save_mock_test(db, MockTestFile.model_validate(mock))


def questions() -> dict[int, Question]:
    from app.db import SessionLocal

    with SessionLocal() as db:
        return {q.number: q for q in db.scalars(select(Question))}


def db_problems(mock: dict) -> list[str]:
    from pathlib import Path

    from app.db import SessionLocal

    with SessionLocal() as db:
        return load_mock_tests.check_against_database(db, [(Path("s01_mock.json"), MockTestFile.model_validate(mock))])


def test_loading_creates_the_mock_test_passages_and_questions(units):
    from app.db import SessionLocal

    mock = make_mock()
    mock["time_limit_minutes"] = 35
    load(mock)
    with SessionLocal() as db:
        assert db.scalar(select(MockTest.time_limit_seconds)) == 35 * 60
        passages = list(db.scalars(select(ReadingPassage).order_by(ReadingPassage.position)))
    assert [p.length for p in passages] == ["short", "medium", "long"]
    qs = questions()
    assert len(qs) == 51
    assert qs[1].part == "vocabulary" and qs[1].word_id is not None and qs[1].passage_id is None
    assert qs[40].part == "grammar" and qs[40].word_id is None
    assert qs[46].part == "reading" and qs[46].type == "reading_short" and qs[46].passage_id == passages[0].id
    assert qs[51].passage_id == passages[2].id
    assert qs[1].prompt_ruby[1] == {"text": "抑制"}  # no reading stored on the tested word


def test_loading_again_keeps_ids(units):
    load(make_mock())
    before = {n: q.id for n, q in questions().items()}
    load(make_mock())
    assert {n: q.id for n, q in questions().items()} == before


def test_changed_question_or_passage_loses_its_why_answers(units):
    from app.db import SessionLocal

    load(make_mock())
    qs = questions()
    with SessionLocal() as db, db.begin():
        for n in (1, 2, 46, 47):
            db.add(AIExplanation(question_id=qs[n].id, selected_option_id="b", why_correct_my=MY, model="test"))

    mock = make_mock()
    mock["questions"][0]["options"][1]["text"] = "ようせつ"  # question 1 changes
    mock["passages"][0]["text_ruby"] = [{"text": "新しい短い文章です。"}]  # the short passage changes (question 46)
    load(mock)
    with SessionLocal() as db:
        kept = set(db.scalars(select(AIExplanation.question_id)))
    assert kept == {qs[2].id, qs[47].id}


def test_removing_questions_before_anyone_started_is_fine(units):
    load(make_mock())
    mock = make_mock()
    mock["passages"][2]["questions"].pop()  # remove question 51
    load(mock)
    assert sorted(questions()) == list(range(1, 51))


def test_removing_questions_after_someone_started_is_refused(client, units):
    from app.db import SessionLocal

    load(make_mock())
    register(client)
    now = datetime.now(UTC)
    with SessionLocal() as db, db.begin():
        db.add(MockAttempt(
            user_id=db.scalar(select(User.id)), mock_test_id=db.scalar(select(MockTest.id)), round=1,
            started_at=now, ends_at=now + timedelta(minutes=30), counts_for_prediction=True,
        ))
    mock = make_mock()
    mock["passages"][2]["questions"].pop()
    with pytest.raises(load_mock_tests.LoadRefused, match="already started"):
        load(mock)
    assert len(questions()) == 51


def test_database_checks(units):
    assert db_problems(make_mock()) == []
    mock = make_mock()
    mock["questions"][0]["correct_option_id"] = "b"  # ようせい is not the reading in the unit
    problems = db_problems(mock)
    assert len(problems) == 1 and "not the reading of 抑制" in problems[0]


def test_mock_for_a_session_not_loaded_is_refused():
    problems = db_problems(make_mock())
    assert problems and "not in the database yet" in problems[0]


def test_command_line_check_mode_changes_nothing(units, tmp_path, monkeypatch, capsys):
    from app.db import SessionLocal

    (tmp_path / "s01_mock.json").write_text(json.dumps(make_mock(), ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["load_mock_tests", "--check", str(tmp_path)])
    assert load_mock_tests.main() == 0
    assert "passed the checks" in capsys.readouterr().out
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Question)) == 0
    monkeypatch.setattr(sys, "argv", ["load_mock_tests", str(tmp_path)])
    assert load_mock_tests.main() == 0
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Question)) == 51
