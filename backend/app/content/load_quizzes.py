"""Load quiz question banks from data/quizzes/ into the database.

Usage (from the repo root). Load the units first: a quiz can only test units that are in the database.
    Check only, change nothing:
        docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_quizzes --check /data/quizzes
    Check and load:
        docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_quizzes /data/quizzes

Safe to run again: each question keeps its id (matched by its "number"), so users' past answers stay valid.
- A question whose text, options or answer changed loses its saved "Why?" explanations, so the AI writes new ones.
- A question removed from the file is deleted, unless users already answered it (then the load is refused).
Nothing is saved unless EVERY file passes every check.
"""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import delete, exists, select
from sqlalchemy.orm import Session

from app.content.quiz_schema import FILE_NAME, UNITS_BY_QUIZ, QuizFile, QuizQuestion
from app.db import SessionLocal
from app.models import AIExplanation, Grammar, Question, Quiz, QuizAnswer, QuizAttemptQuestion, StudySession, Unit, Word


def read_quiz_files(folder: Path) -> tuple[list[tuple[Path, QuizFile]], list[str]]:
    """Read and check every quiz file on its own. Returns the good files and a list of problems."""
    quizzes: list[tuple[Path, QuizFile]] = []
    problems: list[str] = []
    for path in sorted(folder.glob("*.json")):
        name = FILE_NAME.match(path.name)
        if not name:
            problems.append(f"{path.name}: file name must look like s01_q1.json")
            continue
        try:
            quiz = QuizFile.model_validate(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError as exc:
            problems.append(f"{path.name}: not valid JSON (line {exc.lineno}): {exc.msg}")
            continue
        except ValidationError as exc:
            for err in exc.errors():
                where = ".".join(str(part) for part in err["loc"])
                problems.append(f"{path.name}: {where}: {err['msg']}")
            continue
        if (quiz.session_number, quiz.quiz_number) != (int(name.group(1)), int(name.group(2))):
            problems.append(f"{path.name}: session_number and quiz_number inside do not match the file name")
            continue
        quizzes.append((path, quiz))
    return quizzes, problems


def _unit(db: Session, session_number: int, unit_number: int) -> Unit | None:
    return db.scalar(
        select(Unit).join(StudySession, StudySession.id == Unit.session_id)
        .where(StudySession.number == session_number, Unit.number == unit_number)
    )


def _links(db: Session, quiz: QuizFile, q: QuizQuestion) -> tuple[int | None, int | None, str | None]:
    """Find the word or grammar a question tests. Returns (word_id, grammar_id, problem)."""
    unit = _unit(db, quiz.session_number, q.unit_number)
    if unit is None:
        return None, None, f"unit {q.unit_number} of session {quiz.session_number} is not in the database yet (load the units first)"
    if q.part == "grammar":
        grammar_id = db.scalar(select(Grammar.id).where(Grammar.unit_id == unit.id))
        if grammar_id is None:
            return None, None, f"unit {q.unit_number} has no grammar in the database"
        return None, grammar_id, None
    word = db.scalar(select(Word).where(Word.unit_id == unit.id, Word.position == q.word_position))
    if word is None:
        return None, None, f"word {q.word_position} of unit {q.unit_number} is not in the database"
    if q.type == "kanji_reading" and q.underline == word.word:
        correct = next(o.text for o in q.options if o.id == q.correct_option_id)
        if correct != word.furigana:
            return None, None, f"the correct option '{correct}' is not the reading of {word.word} in the unit ({word.furigana})"
    return word.id, None, None


def check_against_database(db: Session, quizzes: list[tuple[Path, QuizFile]]) -> list[str]:
    problems = []
    for path, quiz in quizzes:
        for q in quiz.questions:
            _, _, problem = _links(db, quiz, q)
            if problem:
                problems.append(f"{path.name}: question {q.number}: {problem}")
    return problems


class LoadRefused(Exception):
    pass


def save_quiz(db: Session, quiz: QuizFile) -> None:
    session = db.scalar(select(StudySession).where(StudySession.number == quiz.session_number))
    quiz_row = db.scalar(select(Quiz).where(Quiz.session_id == session.id, Quiz.number == quiz.quiz_number))
    if quiz_row is None:
        first, last = UNITS_BY_QUIZ[quiz.quiz_number]
        quiz_row = Quiz(session_id=session.id, number=quiz.quiz_number, first_unit=first, last_unit=last)
        db.add(quiz_row)
        db.flush()

    existing = {q.number: q for q in db.scalars(select(Question).where(Question.quiz_id == quiz_row.id))}
    in_file = set()
    for q in quiz.questions:
        in_file.add(q.number)
        word_id, grammar_id, _ = _links(db, quiz, q)
        prompt = [piece.model_dump(exclude_none=True) for piece in q.prompt_ruby]
        options = [option.model_dump() for option in q.options]

        row = existing.get(q.number)
        if row is None:
            row = Question(quiz_id=quiz_row.id, number=q.number)
            db.add(row)
        elif (row.prompt_ruby, row.options, row.correct_option_id, row.underline) != (prompt, options, q.correct_option_id, q.underline):
            # The question changed, so old "Why?" answers may be wrong now.
            db.execute(delete(AIExplanation).where(AIExplanation.question_id == row.id))
        row.part = q.part
        row.type = q.type
        row.prompt_ruby = prompt
        row.underline = q.underline
        row.options = options
        row.correct_option_id = q.correct_option_id
        row.word_id = word_id
        row.grammar_id = grammar_id

    for number, row in existing.items():
        if number in in_file:
            continue
        used = db.scalar(select(
            exists().where(QuizAttemptQuestion.question_id == row.id) | exists().where(QuizAnswer.question_id == row.id)
        ))
        if used:
            raise LoadRefused(
                f"session {quiz.session_number} quiz {quiz.quiz_number}: question {number} was removed from the file, "
                "but users have already answered it. Put it back (you may fix its text)."
            )
        db.delete(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check and load quiz files into the database.")
    parser.add_argument("folder", type=Path, help="folder with quiz files, e.g. /data/quizzes")
    parser.add_argument("--check", action="store_true", help="only check the files, do not change the database")
    args = parser.parse_args()

    if not args.folder.is_dir():
        print(f"Folder not found: {args.folder}")
        return 1

    quizzes, problems = read_quiz_files(args.folder)
    with SessionLocal() as db:
        if not problems:
            problems = check_against_database(db, quizzes)
        if problems:
            print(f"Found {len(problems)} problem(s). Nothing was saved. Fix these and run again:")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        if not quizzes:
            print("No quiz files found.")
            return 1

        print(f"All {len(quizzes)} quiz file(s) passed the checks.")
        if args.check:
            return 0

        db.rollback()  # end the read-only checks, then save everything in one new transaction
        try:
            with db.begin():  # one transaction: all quizzes are saved, or none
                for path, quiz in quizzes:
                    save_quiz(db, quiz)
                    print(f"  saved {path.name} ({len(quiz.questions)} questions)")
        except LoadRefused as exc:
            print(f"Nothing was saved: {exc}")
            return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
