"""'More examples' button (contract endpoint 27): new example sentences with ruby and a Burmese translation.

These examples are not cached and not reviewed by a person, so every part is checked in code.
This file never touches the database: the route passes plain values.
"""

import json
import re
from pathlib import Path
from typing import Any

from app.ai.llm import AIUnavailableError, generate_json

PROMPT = (Path(__file__).parent / "prompts" / "examples.txt").read_text(encoding="utf-8")
COUNT = 3                                  # the contract returns 3 examples
ASK_FOR = COUNT + 1                        # ask for one extra, so one bad example can be dropped
KANJI = re.compile(r"[\u4e00-\u9fff々]")
HIRAGANA = re.compile(r"^[\u3041-\u309f]+$")
BURMESE = re.compile(r"[\u1000-\u109f]")


def _ruby_problem(ruby: Any) -> str | None:
    """Our ruby rules (same as data/units): readings only on kanji, and only hiragana."""
    if not isinstance(ruby, list) or not ruby:
        return "ruby is not a list"
    for piece in ruby:
        if not isinstance(piece, dict) or not isinstance(piece.get("text"), str) or not piece["text"]:
            return "bad piece"
        reading = piece.get("reading")
        has_kanji = bool(KANJI.search(piece["text"]))
        if has_kanji and not isinstance(reading, str):
            return "kanji without reading"
        if not has_kanji and reading:
            return "reading on kana"
        if reading and not HIRAGANA.match(reading):
            return "reading not hiragana"
    return None


def _clean_ruby(ruby: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Keep only "text" and "reading", so the app never gets extra fields."""
    return [{"text": p["text"], "reading": p["reading"]} if p.get("reading") else {"text": p["text"]} for p in ruby]


def _check_examples(raw: str, item_type: str, target: str, existing: list[str]) -> list[dict[str, Any]]:
    """Never trust the AI: keep only examples that pass every check, and we need COUNT of them."""
    try:
        answer = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AIUnavailableError("AI answer is not valid JSON") from e
    examples = answer.get("examples") if isinstance(answer, dict) else None
    if not isinstance(examples, list):
        raise AIUnavailableError("AI answer has no examples list")

    target_kanji = KANJI.findall(target) if item_type == "word" else []
    seen = set(existing)
    good = []
    for ex in examples:
        if not isinstance(ex, dict) or _ruby_problem(ex.get("ruby")):
            continue                                         # 1. ruby rules
        ruby = _clean_ruby(ex["ruby"])
        sentence = "".join(p["text"] for p in ruby)
        translation = ex.get("translation_my")
        if not all(k in sentence for k in target_kanji):
            continue                                         # 2. must use the word being learned
        if sentence in seen:
            continue                                         # 3. not an old or repeated sentence
        if not isinstance(translation, str) or not BURMESE.search(translation):
            continue                                         # 4. the translation must be Burmese
        seen.add(sentence)
        good.append({"ruby": ruby, "translation_my": translation.strip()})
        if len(good) == COUNT:
            break

    if len(good) < COUNT:
        raise AIUnavailableError(f"AI gave only {len(good)} usable examples")
    return good


def generate_examples(item_type: str, target: str, meaning_my: str, existing_sentences: list[str]) -> list[dict[str, Any]]:
    """Return 3 new examples: [{"ruby": [...], "translation_my": "..."}]. Raises AIUnavailableError if the AI fails."""
    if item_type not in ("word", "grammar"):
        raise ValueError("item_type must be word or grammar")
    user = json.dumps(
        {"item_type": item_type, "target": target, "meaning_my": meaning_my,
         "existing": existing_sentences, "count": ASK_FOR},
        ensure_ascii=False,
    )
    return _check_examples(generate_json(PROMPT, user), item_type, target, existing_sentences)