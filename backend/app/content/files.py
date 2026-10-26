"""Reading content files (units, quizzes, mock tests, proverbs) the same way everywhere.

Team rule: the wave dash 〜 (U+301C) only. The full-width tilde ～ (U+FF5E) looks almost the same,
so it slips in easily. Instead of asking people to find it, every loader turns ～ into 〜 while reading.
It matters where the code compares text: grammar pattern names, search, and checks that an AI example
really uses the grammar pattern.
"""

import json
from pathlib import Path
from typing import Any

FULLWIDTH_TILDE = "～"  # ～
WAVE_DASH = "〜"  # 〜


def normalize(value: Any) -> Any:
    """The same data, with every ～ in every text replaced by 〜 (also inside lists and objects)."""
    if isinstance(value, str):
        return value.replace(FULLWIDTH_TILDE, WAVE_DASH)
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    return value


def read_content_json(path: Path) -> Any:
    """Read a content JSON file, with the wave dash fixed."""
    return normalize(json.loads(path.read_text(encoding="utf-8")))
