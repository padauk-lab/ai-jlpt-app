"""Check ALL content files at once, without changing any database. GitHub runs this on every pull request.

    python -m app.content.check_all /data

What it checks, in the data folder:
- units/           (needed)   the unit files
- quizzes/         (optional) the quiz files, against the units
- mock_tests/      (optional) the mock test files, against the units
- proverbs/proverbs.json (optional)

Quizzes and mock tests are checked against the units (for example "the right answer is the word's reading").
For that, the units from the FILES are put into the database inside one transaction, the checks run,
and the transaction is rolled back at the end. So the database looks exactly the same afterwards,
and a quiz can be checked together with the units of the same pull request.
"""

import argparse
import sys
from pathlib import Path

from app.content import load_mock_tests, load_proverbs, load_quizzes, load_units
from app.db import SessionLocal


def check_all(data: Path) -> list[str]:
    """Every problem found, as text. An empty list means everything is fine."""
    units_folder = data / "units"
    if not units_folder.is_dir():
        return [f"Folder not found: {units_folder}"]
    units, problems = load_units.read_unit_files(units_folder)
    if problems:
        return problems
    if not units:
        return ["No unit files found."]
    print(f"Units: {len(units)} file(s) passed the checks.")

    quizzes: list = []
    mocks: list = []
    if (data / "quizzes").is_dir():
        quizzes, problems = load_quizzes.read_quiz_files(data / "quizzes")
        if problems:
            return problems
    if (data / "mock_tests").is_dir():
        mocks, problems = load_mock_tests.read_mock_files(data / "mock_tests")
        if problems:
            return problems

    if quizzes or mocks:
        with SessionLocal() as db:
            try:
                for _, unit in units:
                    load_units.save_unit(db, unit)
                db.flush()  # visible to the checks below, but never committed
                problems = load_quizzes.check_against_database(db, quizzes) + load_mock_tests.check_against_database(db, mocks)
            finally:
                db.rollback()  # the database stays exactly as it was
        if problems:
            return problems
    print(f"Quizzes: {len(quizzes)} file(s) passed the checks." if quizzes else "Quizzes: none yet, skipped.")
    print(f"Mock tests: {len(mocks)} file(s) passed the checks." if mocks else "Mock tests: none yet, skipped.")

    proverbs = data / "proverbs" / "proverbs.json"
    if proverbs.is_file():
        result, problems = load_proverbs.read_proverb_file(proverbs)
        if problems:
            return problems
        print(f"Proverbs: {len(result.proverbs)} passed the checks.")
    else:
        print("Proverbs: none yet, skipped.")
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Check all content files. Changes nothing in the database.")
    parser.add_argument("folder", type=Path, help="the data folder, e.g. /data")
    problems = check_all(parser.parse_args().folder)
    if problems:
        print(f"Found {len(problems)} problem(s). Fix these and run again:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("All content files passed the checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
