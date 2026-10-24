"""Furigana test: can the AI write ruby as well as our human-checked content?

Takes the checked example sentences in data/units/, removes the readings,
asks the AI to add them again, and compares the readings. Only for deciding, not app code.
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent              # backend/scripts/ai_eval
ROOT = HERE.parents[2]                    # ai-jlpt-app
UNITS = sorted(p.name for p in (Path(__file__).parents[3] / "data" / "units").glob("*.json"))           #unit files in data/units
BATCH = 20                                # sentences per AI call (saves free-tier requests)
KANJI = re.compile(r"[\u4e00-\u9fff々]")
HIRAGANA = re.compile(r"^[\u3041-\u309f]+$")

for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())
MODEL = os.environ["LLM_MODEL"]

PROMPT = """You add furigana to Japanese sentences for JLPT N1 learners.
For each sentence, split it into pieces and return a "ruby" list:
- A piece with kanji has "text" and "reading" (hiragana only, the reading in this sentence).
- Okurigana and kana go in separate pieces with only "text".
  Example: 難しい -> [{"text": "難", "reading": "むずか"}, {"text": "しい"}]
- A word made only of kanji can be one piece. Example: {"text": "世界中", "reading": "せかいじゅう"}
- Joining every "text" must give back the exact sentence.
Return ONLY JSON: {"results": [{"id": <id>, "ruby": [...]}]} with one result for every input id."""


def ask(items):
    """Send a batch of sentences to the AI, retry if the server is busy."""
    body = {
        "systemInstruction": {"parts": [{"text": PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": json.dumps(items, ensure_ascii=False)}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["LLM_API_KEY"]},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=300) as res:
                return json.loads(res.read())["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 3:
                wait = 30 * (attempt + 1) if e.code == 429 else 5 * 2**attempt   # 429: 30s, 60s, 90s
                print(f"  HTTP {e.code}, retry in {wait}s...")
                time.sleep(wait)
                continue
            print("API error:", e.code, e.read().decode("utf-8")[:300])   # Google's reason
            raise

def plain(ruby):
    """The sentence without readings."""
    return "".join(piece["text"] for piece in ruby)


def kana(ruby):
    """The whole sentence as sound: reading where there is one, otherwise the text."""
    return "".join(piece.get("reading") or piece["text"] for piece in ruby)


def rule_problem(ruby, sentence):
    """Return what breaks our ruby rules, or None if everything is fine."""
    if not all(isinstance(p, dict) and isinstance(p.get("text"), str) for p in ruby):
        return "bad piece"
    if plain(ruby) != sentence:
        return "text changed"
    for piece in ruby:
        reading = piece.get("reading")
        if KANJI.search(piece["text"]) and not reading:
            return f"no reading on {piece['text']}"
        if reading and not KANJI.search(piece["text"]):
            return f"reading on kana {piece['text']}"
        if reading and not HIRAGANA.match(reading):
            return f"reading not hiragana: {reading}"
    return None


# 1. Collect the checked sentences
sentences = []
for name in UNITS:
    unit = json.loads((ROOT / "data" / "units" / name).read_text(encoding="utf-8"))
    examples = [ex for word in unit["words"] for ex in word["examples"]] + unit["grammar"]["examples"]
    for ex in examples:
        sentences.append({"id": len(sentences) + 1, "sentence": plain(ex["ruby"]), "expected": ex["ruby"]})

# 2. Ask the AI in batches. Answers are saved after every batch, so a stopped run can continue.
CACHE = HERE / f"furigana_cache_{MODEL}.json"
results = {}
if CACHE.exists():
    results = {int(k): v for k, v in json.loads(CACHE.read_text(encoding="utf-8")).items()}
    print(f"Loaded {len(results)} saved answers")

todo = [s for s in sentences if s["id"] not in results]
for i in range(0, len(todo), BATCH):
    batch = todo[i : i + BATCH]
    start = time.time()
    try:
        answer = json.loads(ask([{"id": s["id"], "sentence": s["sentence"]} for s in batch]))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        print("Stopped (quota or error). Run again later to continue. Scoring what we have now.")
        break
    for r in answer.get("results", []):
        results[r.get("id")] = r.get("ruby")
    CACHE.write_text(json.dumps(results, ensure_ascii=False), encoding="utf-8")   # save point
    print(f"Batch {i // BATCH + 1}: {len(batch)} sentences ({time.time() - start:.1f}s)")

# 3. Compare with the human-checked readings
rules_ok = reading_ok = 0
problems = []
checked = [s for s in sentences if s["id"] in results]
for s in checked:
    ruby = results.get(s["id"])
    problem = "missing" if not isinstance(ruby, list) else rule_problem(ruby, s["sentence"])
    if problem:
        problems.append({"id": s["id"], "sentence": s["sentence"], "problem": problem})
        continue
    rules_ok += 1
    if kana(ruby) == kana(s["expected"]):
        reading_ok += 1
    else:
        problems.append({"id": s["id"], "sentence": s["sentence"], "problem": "reading differs",
                        "ai": kana(ruby), "expected": kana(s["expected"])})

total = len(checked)
print(f"Checked:    {total} of {len(sentences)} sentences")
print(f"Rules OK:   {rules_ok}/{total}")
print(f"Reading OK: {reading_ok}/{total}s")
out = HERE / f"furigana_{MODEL}.json"
out.write_text(json.dumps(problems, ensure_ascii=False, indent=2), encoding="utf-8")
print("Problems saved:", out)