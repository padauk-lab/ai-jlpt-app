"""'More examples' button (contract endpoint 27): new example sentences with ruby and a Burmese translation.

These examples are not cached and not reviewed by a person, so every part is checked in code.
The ruby and Burmese rules are the same ones our content files use (app/content/schema.py).
This file never touches the database: the route passes plain values.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.ai.llm import AIUnavailableError, generate_json
from app.content.schema import Example

PROMPT = (Path(__file__).parent / "prompts" / "examples.txt").read_text(encoding="utf-8")
COUNT = 3                                  # the contract returns 3 examples
ASK_FOR = COUNT + 1                        # ask for one extra, so one bad example can be dropped


def _reading_matches(piece_text: str, piece_reading: str, text: str, reading: str) -> bool:
    """Does an AI piece that contains the target kanji read it the same way as our database?"""
    if piece_text == text:
        return piece_reading == reading                  # 抑制 / よくせい
    if piece_text.startswith(text):
        return piece_reading.startswith(reading)         # 顕在化 / けんざいか
    if piece_text.endswith(text):
        return piece_reading.endswith(reading)           # 上昇傾向 / じょうしょうけいこう
    return False


def _uses_target_correctly(example: Example, target_ruby: list[dict[str, Any]]) -> bool:
    """Every kanji part of the target word appears, with the reading from our checked content."""
    for part in target_ruby:
        if not part.get("reading"):
            continue                                     # kana part, like the う in 培う
        pieces = [p for p in example.ruby if p.reading and part["text"] in p.text]
        if not pieces:
            return False
        if not all(_reading_matches(p.text, p.reading, part["text"], part["reading"]) for p in pieces):
            return False
    return True


def _check_examples(raw: str, target_ruby: list[dict[str, Any]] | None, existing: list[str]) -> list[dict[str, Any]]:
    """Never trust the AI: keep only examples that pass every check, and we need COUNT of them."""
    try:
        answer = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AIUnavailableError("AI answer is not valid JSON") from e
    examples = answer.get("examples") if isinstance(answer, dict) else None
    if not isinstance(examples, list):
        raise AIUnavailableError("AI answer has no examples list")

    seen = set(existing)
    good = []
    for item in examples:
        try:
            example = Example.model_validate(item)       # 1. same ruby and Burmese rules as our content
        except ValidationError:
            continue
        if target_ruby and not _uses_target_correctly(example, target_ruby):
            continue                                     # 2. the word being learned, with the right reading
        sentence = "".join(p.text for p in example.ruby)
        if sentence in seen:
            continue                                     # 3. not an old or repeated sentence
        seen.add(sentence)
        good.append(example.model_dump(exclude_none=True))
        if len(good) == COUNT:
            break

    if len(good) < COUNT:
        raise AIUnavailableError(f"AI gave only {len(good)} usable examples")
    return good


def generate_examples(
    item_type: str,
    target: str,
    meaning_my: str,
    existing_sentences: list[str],
    target_ruby: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return 3 new examples: [{"ruby": [...], "translation_my": "..."}].

    For a word, pass its ruby from the database (e.g. [{"text": "抑制", "reading": "よくせい"}]).
    Raises AIUnavailableError if the AI fails.
    """
    if item_type not in ("word", "grammar"):
        raise ValueError("item_type must be word or grammar")
    if item_type == "word" and not target_ruby:
        raise ValueError("a word needs its ruby from the database")
    word_ruby = target_ruby if item_type == "word" else None
    user = json.dumps(
        {"item_type": item_type, "target": target, "target_ruby": word_ruby, "meaning_my": meaning_my,
         "existing": existing_sentences, "count": ASK_FOR},
        ensure_ascii=False,
    )
    return _check_examples(generate_json(PROMPT, user), word_ruby, existing_sentences)