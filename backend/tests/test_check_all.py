"""check_all: every content file is checked in one go, and the database is never changed."""

import json
import sys
from pathlib import Path

from sqlalchemy import func, select

from app.content import check_all
from app.models import Question, StudySession
from tests.test_load_mock_tests import make_mock
from tests.test_load_mock_tests import make_unit as mock_unit
from tests.test_load_quizzes import make_quiz
from tests.test_proverbs import make_file as make_proverbs


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def data_folder(tmp_path: Path, units=range(1, 11), quiz=True, mock=True, proverbs=True) -> Path:
    for n in units:
        write(tmp_path / "units" / f"s01_u{n:02}.json", mock_unit(n))
    if quiz:
        write(tmp_path / "quizzes" / "s01_q1.json", make_quiz())
    if mock:
        write(tmp_path / "mock_tests" / "s01_mock.json", make_mock())
    if proverbs:
        write(tmp_path / "proverbs" / "proverbs.json", make_proverbs())
    return tmp_path


def counts() -> tuple[int, int]:
    from app.db import SessionLocal

    with SessionLocal() as db:
        return (db.scalar(select(func.count()).select_from(StudySession)),
                db.scalar(select(func.count()).select_from(Question)))


def test_everything_good_passes_and_the_database_is_untouched(tmp_path, capsys):
    assert check_all.check_all(data_folder(tmp_path)) == []
    out = capsys.readouterr().out
    assert "Units: 10 file(s)" in out and "Quizzes: 1 file(s)" in out and "Mock tests: 1 file(s)" in out
    assert "Proverbs: 3 passed" in out
    assert counts() == (0, 0)  # the units were only loaded inside a rolled-back transaction


def test_only_units_is_fine(tmp_path, capsys):
    assert check_all.check_all(data_folder(tmp_path, quiz=False, mock=False, proverbs=False)) == []
    out = capsys.readouterr().out
    assert "Quizzes: none yet, skipped." in out and "Proverbs: none yet, skipped." in out


def test_a_broken_quiz_is_reported(tmp_path):
    folder = data_folder(tmp_path, mock=False)
    quiz = make_quiz()
    quiz["questions"][0]["options"][1]["text"] = "がいねん"  # two options the same
    write(folder / "quizzes" / "s01_q1.json", quiz)
    problems = check_all.check_all(folder)
    assert problems and "all be different" in problems[0]


def test_a_wrong_answer_key_is_caught_against_the_unit_files(tmp_path):
    folder = data_folder(tmp_path, quiz=False, proverbs=False)
    mock = make_mock()
    mock["questions"][0]["correct_option_id"] = "b"  # ようせい is not the reading of 抑制
    write(folder / "mock_tests" / "s01_mock.json", mock)
    problems = check_all.check_all(folder)
    assert len(problems) == 1 and "not the reading" in problems[0]
    assert counts() == (0, 0)


def test_a_quiz_for_units_that_dont_exist_is_refused(tmp_path):
    folder = data_folder(tmp_path, units=range(6, 11), mock=False, proverbs=False)  # Quiz 1 needs units 1 to 5
    problems = check_all.check_all(folder)
    assert problems and "not in the database yet" in problems[0]


def test_a_broken_unit_stops_everything(tmp_path):
    folder = data_folder(tmp_path)
    (folder / "units" / "s01_u01.json").write_text("{ not json", encoding="utf-8")
    assert check_all.check_all(folder)


def test_a_broken_proverb_file_is_reported(tmp_path):
    folder = data_folder(tmp_path, quiz=False, mock=False)
    proverbs = make_proverbs()
    proverbs["proverbs"][0]["meaning_my"] = "not Burmese"
    write(folder / "proverbs" / "proverbs.json", proverbs)
    problems = check_all.check_all(folder)
    assert problems and "Burmese" in problems[0]


def test_missing_units_folder(tmp_path):
    assert "Folder not found" in check_all.check_all(tmp_path)[0]


def test_command_line_exit_codes(tmp_path, monkeypatch, capsys):
    folder = data_folder(tmp_path)
    monkeypatch.setattr(sys, "argv", ["check_all", str(folder)])
    assert check_all.main() == 0
    assert "All content files passed the checks." in capsys.readouterr().out

    (folder / "units" / "s01_u01.json").write_text("{}", encoding="utf-8")
    assert check_all.main() == 1
    assert "problem(s)" in capsys.readouterr().out
