"""Load mock test files from data/mock_tests/ into the database.

Usage (from the repo root). Load the units first: a mock test belongs to a session that must exist.
    Check only, change nothing:
        docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_mock_tests --check /data/mock_tests
    Check and load:
        docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_mock_tests /data/mock_tests

Safe to run again: questions keep their id (matched by "number"), passages by their length.
- A question whose text, options or answer changed loses its saved "Why?" explanations.
  If a passage's text changed, all of its questions lose them.
- Once anyone has started this mock test, its questions can be fixed but not removed (the load is refused).
Nothing is saved unless EVERY file passes every check.
"""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import delete, exists, select
from sqlalchemy.orm import Session

from app.content.mock_schema import FILE_NAME, KnowledgeQuestion, MockTestFile
from app.db import SessionLocal
from app.models import AIExplanation, MockAttempt, MockTest, Question, ReadingPassage, StudySession, Unit, Word


def read_mock_files(folder: Path) -> tuple[list[tuple[Path, MockTestFile]], list[str]]:
    mocks: list[tuple[Path, MockTestFile]] = []
    problems: list[str] = []
    for path in sorted(folder.glob("*.json")):
        name = FILE_NAME.match(path.name)
        if not name:
            problems.append(f"{path.name}: file name must look like s01_mock.json")
            continue
        try:
            mock = MockTestFile.model_validate(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError as exc:
            problems.append(f"{path.name}: not valid JSON (line {exc.lineno}): {exc.msg}")
            continue
        except ValidationError as exc:
            for err in exc.errors():
                where = ".".join(str(part) for part in err["loc"])
                problems.append(f"{path.name}: {where}: {err['msg']}")
            continue
        if mock.session_number != int(name.group(1)):
            problems.append(f"{path.name}: session_number inside does not match the file name")
            continue
        mocks.append((path, mock))
    return mocks, problems


def _session(db: Session, number: int) -> StudySession | None:
    return db.scalar(select(StudySession).where(StudySession.number == number))


def _word_link(db: Session, session: StudySession, q: KnowledgeQuestion) -> tuple[int | None, str | None]:
    """Find the word a vocabulary question tests, if the file says which one. Returns (word_id, problem)."""
    if q.word_position is None:
        return None, None
    word = db.scalar(
        select(Word).join(Unit, Unit.id == Word.unit_id)
        .where(Unit.session_id == session.id, Unit.number == q.unit_number, Word.position == q.word_position)
    )
    if word is None:
        return None, f"word {q.word_position} of unit {q.unit_number} is not in the database"
    if q.type == "kanji_reading" and q.underline == word.word:
        correct = next(o.text for o in q.options if o.id == q.correct_option_id)
        if correct != word.furigana:
            return None, f"the correct option '{correct}' is not the reading of {word.word} in the unit ({word.furigana})"
    return word.id, None


def check_against_database(db: Session, mocks: list[tuple[Path, MockTestFile]]) -> list[str]:
    problems = []
    for path, mock in mocks:
        session = _session(db, mock.session_number)
        if session is None:
            problems.append(f"{path.name}: session {mock.session_number} is not in the database yet (load its units first)")
            continue
        for q in mock.questions:
            if q.unit_number is not None and db.scalar(
                select(Unit.id).where(Unit.session_id == session.id, Unit.number == q.unit_number)
            ) is None:
                problems.append(f"{path.name}: question {q.number}: unit {q.unit_number} is not in the database")
                continue
            _, problem = _word_link(db, session, q)
            if problem:
                problems.append(f"{path.name}: question {q.number}: {problem}")
    return problems


class LoadRefused(Exception):
    pass


def _clear_why_answers(db: Session, question: Question) -> None:
    db.execute(delete(AIExplanation).where(AIExplanation.question_id == question.id))


def save_mock_test(db: Session, mock: MockTestFile) -> None:
    session = _session(db, mock.session_number)
    mock_row = db.scalar(select(MockTest).where(MockTest.session_id == session.id))
    if mock_row is None:
        mock_row = MockTest(session_id=session.id)
        db.add(mock_row)
    mock_row.time_limit_seconds = mock.time_limit_minutes * 60
    db.flush()

    existing = {q.number: q for q in db.scalars(select(Question).where(Question.mock_test_id == mock_row.id))}
    passages = {p.length: p for p in db.scalars(select(ReadingPassage).where(ReadingPassage.mock_test_id == mock_row.id))}
    in_file: set[int] = set()

    def upsert(number, part, type_, prompt, underline, options, correct, passage_id=None, word_id=None, passage_changed=False):
        in_file.add(number)
        row = existing.get(number)
        if row is None:
            row = Question(mock_test_id=mock_row.id, number=number)
            db.add(row)
        elif passage_changed or (row.prompt_ruby, row.options, row.correct_option_id, row.underline) != (prompt, options, correct, underline):
            _clear_why_answers(db, row)
        row.part, row.type, row.prompt_ruby, row.underline = part, type_, prompt, underline
        row.options, row.correct_option_id = options, correct
        row.passage_id, row.word_id, row.grammar_id = passage_id, word_id, None

    def dump(pieces):
        return [piece.model_dump(exclude_none=True) for piece in pieces]

    for q in mock.questions:
        word_id, _ = _word_link(db, session, q)
        upsert(q.number, q.part, q.type, dump(q.prompt_ruby), q.underline, [o.model_dump() for o in q.options],
               q.correct_option_id, word_id=word_id)

    for position, p in enumerate(mock.passages, start=1):
        text = dump(p.text_ruby)
        row = passages.get(p.length)
        changed = row is not None and row.text_ruby != text
        if row is None:
            row = ReadingPassage(mock_test_id=mock_row.id, length=p.length)
            db.add(row)
        row.position, row.text_ruby = position, text
        db.flush()
        for q in p.questions:
            upsert(q.number, "reading", f"reading_{p.length}", dump(q.prompt_ruby), None,
                   [o.model_dump() for o in q.options], q.correct_option_id, passage_id=row.id, passage_changed=changed)

    removed = [row for number, row in existing.items() if number not in in_file]
    if removed:
        started = db.scalar(select(exists().where(MockAttempt.mock_test_id == mock_row.id)))
        if started:
            numbers = ", ".join(str(r.number) for r in sorted(removed, key=lambda r: r.number))
            raise LoadRefused(
                f"session {mock.session_number} mock test: question(s) {numbers} were removed from the file, "
                "but users have already started this mock test. Put them back (you may fix their text)."
            )
        for row in removed:
            db.delete(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check and load mock test files into the database.")
    parser.add_argument("folder", type=Path, help="folder with mock test files, e.g. /data/mock_tests")
    parser.add_argument("--check", action="store_true", help="only check the files, do not change the database")
    args = parser.parse_args()

    if not args.folder.is_dir():
        print(f"Folder not found: {args.folder}")
        return 1

    mocks, problems = read_mock_files(args.folder)
    with SessionLocal() as db:
        if not problems:
            problems = check_against_database(db, mocks)
        if problems:
            print(f"Found {len(problems)} problem(s). Nothing was saved. Fix these and run again:")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        if not mocks:
            print("No mock test files found.")
            return 1

        print(f"All {len(mocks)} mock test file(s) passed the checks.")
        if args.check:
            return 0

        db.rollback()  # end the read-only checks, then save everything in one new transaction
        try:
            with db.begin():
                for path, mock in mocks:
                    save_mock_test(db, mock)
                    total = len(mock.questions) + sum(len(p.questions) for p in mock.passages)
                    print(f"  saved {path.name} ({total} questions, 3 passages)")
        except LoadRefused as exc:
            print(f"Nothing was saved: {exc}")
            return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
