"""Compare fugashi + unidic-lite (code, reads the whole sentence) with our human-checked furigana.
Eval only: fugashi is NOT an app dependency."""

import json
from pathlib import Path

from fugashi import Tagger

HERE = Path(__file__).parent
ROOT = HERE.parents[2]


def to_hiragana(text):
    """Katakana -> hiragana, so both sides are compared the same way."""
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in text)


def fugashi_kana(tagger, sentence):
    """Reading of the whole sentence. Words without a reading (punctuation) keep their text."""
    return to_hiragana("".join(word.feature.kana or word.surface for word in tagger(sentence)))


tagger = Tagger()
total = ok = 0
problems = []
for path in sorted((ROOT / "data" / "units").glob("*.json")):
    unit = json.loads(path.read_text(encoding="utf-8"))
    examples = [ex for word in unit["words"] for ex in word["examples"]] + unit["grammar"]["examples"]
    for ex in examples:
        sentence = "".join(piece["text"] for piece in ex["ruby"])
        got = fugashi_kana(tagger, sentence)
        want = to_hiragana("".join(piece.get("reading") or piece["text"] for piece in ex["ruby"]))
        total += 1
        if got == want:
            ok += 1
        else:
            problems.append({"sentence": sentence, "fugashi": got, "expected": want})

print(f"Reading OK: {ok}/{total}")
(HERE / "furigana_fugashi.json").write_text(json.dumps(problems, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Problems saved: furigana_fugashi.json ({len(problems)} problems)")