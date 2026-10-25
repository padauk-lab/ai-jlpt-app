"""The full-width tilde ～ is turned into the wave dash 〜 while content files are read."""

import json

from app.content import load_mock_tests, load_proverbs, load_quizzes, load_units
from app.content.files import normalize
from tests.test_load_mock_tests import make_mock
from tests.test_load_quizzes import make_quiz, make_unit
from tests.test_proverbs import make_file as make_proverbs

TILDE, WAVE = "～", "〜"


def write(path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_normalize_reaches_every_text():
    data = {"a": f"{TILDE}ならでは", "b": [f"x{TILDE}", {"c": TILDE}], "n": 3, "none": None}
    assert normalize(data) == {"a": f"{WAVE}ならでは", "b": [f"x{WAVE}", {"c": WAVE}], "n": 3, "none": None}


def test_unit_file_with_tilde_loads_with_wave_dash(tmp_path):
    unit = make_unit(1, 1)
    unit["grammar"]["pattern"] = f"{TILDE}ならでは"
    unit["grammar"]["note_my"] = f"မြန်မာ ({TILDE}ならでは)"
    write(tmp_path / "s01_u01.json", unit)
    units, problems = load_units.read_unit_files(tmp_path)
    assert problems == []
    grammar = units[0][1].grammar
    assert grammar.pattern == f"{WAVE}ならでは"
    assert TILDE not in grammar.note_my


def test_escaped_tilde_is_fixed_too(tmp_path):
    """Written as \\uff5e in the file: still found, because the fix runs after reading the JSON."""
    unit = make_unit(1, 1)
    unit["grammar"]["pattern"] = "PATTERN"
    text = json.dumps(unit, ensure_ascii=False).replace("PATTERN", "\\uff5eならでは")
    (tmp_path / "s01_u01.json").write_text(text, encoding="utf-8")
    units, _ = load_units.read_unit_files(tmp_path)
    assert units[0][1].grammar.pattern == f"{WAVE}ならでは"


def test_quiz_mock_and_proverb_loaders_fix_it_too(tmp_path):
    quiz = make_quiz()
    quiz["questions"][-1]["options"][0]["text"] = f"{TILDE}ならでは"
    (tmp_path / "q").mkdir()
    write(tmp_path / "q" / "s01_q1.json", quiz)
    quizzes, _ = load_quizzes.read_quiz_files(tmp_path / "q")
    assert quizzes[0][1].questions[-1].options[0].text == f"{WAVE}ならでは"

    mock = make_mock()
    mock["questions"][-1]["options"][0]["text"] = f"{TILDE}ならでは"
    (tmp_path / "m").mkdir()
    write(tmp_path / "m" / "s01_mock.json", mock)
    mocks, _ = load_mock_tests.read_mock_files(tmp_path / "m")
    assert mocks[0][1].questions[-1].options[0].text == f"{WAVE}ならでは"

    proverbs = make_proverbs()
    proverbs["proverbs"][0]["explanation_my"] = f"မြန်မာ {TILDE}"
    write(tmp_path / "proverbs.json", proverbs)
    data, _ = load_proverbs.read_proverb_file(tmp_path / "proverbs.json")
    assert TILDE not in data.proverbs[0].explanation_my
