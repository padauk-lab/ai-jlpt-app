"""Load the proverb list (data/proverbs/proverbs.json) into the database.

Format guide for the content team: docs/content-format.md
Usage (from the repo root):
    Check only, change nothing:
        docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_proverbs --check /data/proverbs/proverbs.json
    Check and load:
        docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_proverbs /data/proverbs/proverbs.json

Safe to run again: a proverb is matched by its Japanese text, so it keeps its id.
A proverb removed from the file is switched off (not deleted), so it simply stops appearing.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Annotated

from pydantic import Field, ValidationError, field_validator, model_validator
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.content.files import read_content_json
from app.content.schema import Ruby, Strict, Text, _burmese
from app.db import SessionLocal
from app.models import Proverb


class ProverbItem(Strict):
    ruby: Ruby
    meaning_my: Text
    explanation_my: Text

    _check_burmese = field_validator("meaning_my", "explanation_my")(_burmese)

    @property
    def japanese(self) -> str:
        return "".join(piece.text for piece in self.ruby)


class ProverbFile(Strict):
    proverbs: Annotated[list[ProverbItem], Field(min_length=1, max_length=1000)]

    @model_validator(mode="after")
    def no_duplicates(self) -> "ProverbFile":
        seen = set()
        for number, item in enumerate(self.proverbs, start=1):
            if item.japanese in seen:
                raise ValueError(f"proverb {number} ({item.japanese}) is in the list twice")
            seen.add(item.japanese)
        return self


def read_proverb_file(path: Path) -> tuple[ProverbFile | None, list[str]]:
    try:
        return ProverbFile.model_validate(read_content_json(path)), []
    except json.JSONDecodeError as exc:
        return None, [f"not valid JSON (line {exc.lineno}): {exc.msg}"]
    except ValidationError as exc:
        return None, [".".join(str(p) for p in err["loc"]) + f": {err['msg']}" for err in exc.errors()]


def save_proverbs(db: Session, data: ProverbFile) -> tuple[int, int]:
    """Returns (proverbs saved, proverbs switched off)."""
    existing = {"".join(p["text"] for p in row.ruby): row for row in db.scalars(select(Proverb))}
    kept_ids = []
    for item in data.proverbs:
        row = existing.get(item.japanese)
        if row is None:
            row = Proverb()
            db.add(row)
        row.ruby = [piece.model_dump(exclude_none=True) for piece in item.ruby]
        row.meaning_my = item.meaning_my
        row.explanation_my = item.explanation_my
        row.is_active = True
        db.flush()
        kept_ids.append(row.id)
    switched_off = db.execute(
        update(Proverb).where(Proverb.id.not_in(kept_ids), Proverb.is_active.is_(True)).values(is_active=False)
    ).rowcount
    return len(kept_ids), switched_off


def main() -> int:
    parser = argparse.ArgumentParser(description="Check and load the proverb list into the database.")
    parser.add_argument("file", type=Path, help="the proverb file, e.g. /data/proverbs/proverbs.json")
    parser.add_argument("--check", action="store_true", help="only check the file, do not change the database")
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"File not found: {args.file}")
        return 1
    data, problems = read_proverb_file(args.file)
    if problems:
        print(f"Found {len(problems)} problem(s). Nothing was saved. Fix these and run again:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"All {len(data.proverbs)} proverb(s) passed the checks.")
    if args.check:
        return 0
    with SessionLocal() as db, db.begin():
        saved, switched_off = save_proverbs(db, data)
    print(f"Saved {saved} proverb(s). Switched off {switched_off} that are no longer in the file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
