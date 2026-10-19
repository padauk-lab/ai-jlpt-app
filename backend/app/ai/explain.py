"""'Why?' button (contract endpoint 28): explain why the correct answer is right
and why the student's answer is wrong.

The backend route checks the cache (AIExplanation) first, and saves what this returns.
This file never touches the database.
"""

import json
from pathlib import Path
from typing import Any

from app.ai.llm import AIUnavailableError, generate_json, model_name
from app.models import Question

PROMPT = (Path(__file__).parent / "prompts" / "explain.txt").read_text(encoding="utf-8")
OPTION_IDS = ("a", "b", "c", "d")


def _ruby_to_text(ruby: list[dict[str, Any]]) -> str:
    """[{"text": "彼の"}, {"text": "意志力", "reading": "いしりょく"}] -> "彼の意志力" """
    return "".join(piece["text"] for piece in ruby)


def _build_input(question: Question, selected_option_id: str, passage_text: str | None) -> str:
    """Turn the database question into the JSON the prompt expects."""
    data = {
        "type": question.type,
        "prompt": _ruby_to_text(question.prompt_ruby),
        "underline": question.underline,
        "passage": passage_text,
        "options": {option["id"]: option["text"] for option in question.options},
        "correct": question.correct_option_id,
        "selected": selected_option_id,
    }
    return json.dumps(data, ensure_ascii=False)


def _clean_text(value: Any) -> str:
    """An explanation must be real text, not empty and not a number."""
    if not isinstance(value, str) or not value.strip():
        raise AIUnavailableError("AI answer is missing an explanation")
    return value.strip()


def _check_answer(raw: str, correct: str, selected: str) -> dict[str, Any]:
    """Never trust the AI: check every field against the rules of contract endpoint 28."""
    try:
        answer = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AIUnavailableError("AI answer is not valid JSON") from e
    if not isinstance(answer, dict):
        raise AIUnavailableError("AI answer is not a JSON object")

    why_correct = _clean_text(answer.get("why_correct_my"))

    if selected == correct:
        why_wrong = None  # the rule says null, whatever the AI wrote
    else:
        why_wrong = _clean_text(answer.get("why_selected_wrong_my"))

    # Only the options that are neither correct nor selected. Extra keys from the AI are ignored.
    expected = [option for option in OPTION_IDS if option not in (correct, selected)]
    others = answer.get("other_options_my")
    if not isinstance(others, dict) or any(option not in others for option in expected):
        raise AIUnavailableError("AI answer is missing a note for an option")
    other_options = {option: _clean_text(others[option]) for option in expected}

    return {
        "why_correct_my": why_correct,
        "why_selected_wrong_my": why_wrong,
        "other_options_my": other_options,
    }


def explain_answer(question: Question, selected_option_id: str, passage_text: str | None = None) -> dict[str, Any]:
    """Return the fields for an AIExplanation row. Raises AIUnavailableError if the AI fails."""
    if selected_option_id not in OPTION_IDS:
        raise ValueError("selected_option_id must be a, b, c or d")
    raw = generate_json(PROMPT, _build_input(question, selected_option_id, passage_text))
    result = _check_answer(raw, question.correct_option_id, selected_option_id)
    result["model"] = model_name()
    return result