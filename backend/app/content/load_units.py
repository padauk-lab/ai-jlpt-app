"""Load unit files from data/units/ into the database.

Usage (from the repo root):
    Check only, change nothing:
        docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_units --check /data/units
    Check and load:
        docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_units /data/units

Safe to run again: existing words are updated in place (their ids stay the same, so saved words
and quiz questions keep pointing to them). Nothing is saved unless EVERY file passes the checks.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.content.files import read_content_json
from app.content.schema import UnitFile
from app.db import SessionLocal
from app.models import Example, Grammar, StudySession, Unit, Word

FILE_NAME = re.compile(r"^s(\d{2})_u(\d{2})\.json$")


def read_unit_files(folder: Path) -> tuple[list[tuple[Path, UnitFile]], list[str]]:
    """Read and check every unit file. Returns the good units and a list of problems."""
    units: list[tuple[Path, UnitFile]] = []
    problems: list[str] = []
    for path in sorted(folder.glob("*.json")):
        name = FILE_NAME.match(path.name)
        if not name:
            problems.append(f"{path.name}: file name must look like s01_u01.json")
            continue
        try:
            unit = UnitFile.model_validate(read_content_json(path))
        except json.JSONDecodeError as exc:
            problems.append(f"{path.name}: not valid JSON (line {exc.lineno}): {exc.msg}")
            continue
        except ValidationError as exc:
            for err in exc.errors():
                where = ".".join(str(part) for part in err["loc"])
                problems.append(f"{path.name}: {where}: {err['msg']}")
            continue
        if (unit.session_number, unit.unit_number) != (int(name.group(1)), int(name.group(2))):
            problems.append(f"{path.name}: session_number and unit_number inside do not match the file name")
            continue
        units.append((path, unit))
    return units, problems


def save_unit(db: Session, unit: UnitFile) -> None:
    session_row = db.scalar(select(StudySession).where(StudySession.number == unit.session_number))
    if session_row is None:
        session_row = StudySession(number=unit.session_number)
        db.add(session_row)
        db.flush()

    unit_row = db.scalar(select(Unit).where(Unit.session_id == session_row.id, Unit.number == unit.unit_number))
    if unit_row is None:
        unit_row = Unit(session_id=session_row.id, number=unit.unit_number)
        db.add(unit_row)
        db.flush()

    for word in unit.words:
        row = db.scalar(select(Word).where(Word.unit_id == unit_row.id, Word.position == word.position))
        if row is None:
            row = Word(unit_id=unit_row.id, position=word.position)
            db.add(row)
        row.word = word.word
        row.furigana = word.furigana
        row.ruby = [piece.model_dump(exclude_none=True) for piece in word.ruby]
        row.meaning_my = word.meaning_my
        db.flush()
        db.execute(delete(Example).where(Example.word_id == row.id))
        for position, example in enumerate(word.examples, start=1):
            db.add(Example(word_id=row.id, position=position, ruby=_ruby(example.ruby), translation_my=example.translation_my))

    grammar = unit.grammar
    grammar_row = db.scalar(select(Grammar).where(Grammar.unit_id == unit_row.id))
    if grammar_row is None:
        grammar_row = Grammar(unit_id=unit_row.id)
        db.add(grammar_row)
    grammar_row.pattern = grammar.pattern
    grammar_row.meaning_my = grammar.meaning_my
    grammar_row.how_to_use = grammar.how_to_use
    grammar_row.how_to_use_my = grammar.how_to_use_my
    grammar_row.note_my = grammar.note_my
    db.flush()
    db.execute(delete(Example).where(Example.grammar_id == grammar_row.id))
    for position, example in enumerate(grammar.examples, start=1):
        db.add(Example(grammar_id=grammar_row.id, position=position, ruby=_ruby(example.ruby), translation_my=example.translation_my))


def _ruby(pieces) -> list[dict]:
    return [piece.model_dump(exclude_none=True) for piece in pieces]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check and load unit files into the database.")
    parser.add_argument("folder", type=Path, help="folder with unit files, e.g. /data/units")
    parser.add_argument("--check", action="store_true", help="only check the files, do not change the database")
    args = parser.parse_args()

    if not args.folder.is_dir():
        print(f"Folder not found: {args.folder}")
        return 1

    units, problems = read_unit_files(args.folder)
    if problems:
        print(f"Found {len(problems)} problem(s). Nothing was saved. Fix these and run again:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    if not units:
        print("No unit files found.")
        return 1

    print(f"All {len(units)} unit file(s) passed the checks.")
    if args.check:
        return 0

    with SessionLocal() as db, db.begin():  # one transaction: all units are saved, or none
        for path, unit in units:
            save_unit(db, unit)
            print(f"  saved {path.name}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
