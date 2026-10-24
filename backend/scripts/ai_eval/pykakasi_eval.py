"""Compare pykakasi (code, no AI) with our human-checked furigana in data/units/.
Eval only: pykakasi is NOT an app dependency."""

import json
from pathlib import Path

import pykakasi

HERE = Path(__file__).parent
ROOT = HERE.parents[2]


def to_hiragana(text):
    """Katakana -> hiragana, so both sides are compared the same way."""
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in text)


def expected_kana(ruby):
    return to_hiragana("".join(piece.get("reading") or piece["text"] for piece in ruby))


kks = pykakasi.kakasi()
total = ok = 0
problems = []
for path in sorted((ROOT / "data" / "units").glob("*.json")):
    unit = json.loads(path.read_text(encoding="utf-8"))
    examples = [ex for word in unit["words"] for ex in word["examples"]] + unit["grammar"]["examples"]
    for ex in examples:
        sentence = "".join(piece["text"] for piece in ex["ruby"])
        got = to_hiragana("".join(item["hira"] for item in kks.convert(sentence)))
        want = expected_kana(ex["ruby"])
        total += 1
        if got == want:
            ok += 1
        else:
            problems.append({"sentence": sentence, "pykakasi": got, "expected": want})

print(f"Reading OK: {ok}/{total}")
(HERE / "furigana_pykakasi.json").write_text(json.dumps(problems, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Problems saved: furigana_pykakasi.json ({len(problems)} problems)")