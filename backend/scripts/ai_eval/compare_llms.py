import json
import os
import time
import urllib.request
from pathlib import Path
import urllib.error

HERE = Path(__file__).parent              # backend/scripts/ai_eval
ROOT = HERE.parents[2]                    # ai-jlpt-app

PROVIDER = "gemini"                       # "ollama" or "gemini"
MODEL = "gemini-2.5-flash"                # e.g. "qwen2.5:7b" for ollama
VERSION = "v3"                            # prompt version


# 1. Load secrets from .env (never hard-code keys)
def load_env(path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


load_env(ROOT / ".env")

# 2. Read the prompt and the 5 questions
SYSTEM = (HERE / f"prompt_explain_{VERSION}.txt").read_text(encoding="utf-8")
questions = json.loads((HERE / "test_questions.json").read_text(encoding="utf-8"))


# 3. Helper: send JSON to a URL and read the JSON reply (retry if server is busy)
def post_json(url, body, headers, retries=4):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=300) as res:
                return json.loads(res.read())
        except urllib.error.HTTPError as e:
            if e.code == 503 and attempt < retries - 1:
                wait = 5 * 2 ** attempt              # 5s, 10s, 20s
                print(f"  Server busy (503), retry in {wait}s...")
                time.sleep(wait)
            else:
                print("API error:", e.code, e.read().decode("utf-8"))
                raise

# 4a. Local model (Ollama)
def ask_ollama(user_msg):
    body = {
        "model": MODEL,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_msg},
        ],
    }
    data = post_json("http://localhost:11434/api/chat", body, {})
    return data["message"]["content"]


# 4b. Cloud model (Gemini)
def ask_gemini(user_msg):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": user_msg}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    headers = {"x-goog-api-key": os.environ["GEMINI_API_KEY"]}
    data = post_json(url, body, headers)
    return data["candidates"][0]["content"]["parts"][0]["text"]


ask = ask_gemini if PROVIDER == "gemini" else ask_ollama

# 5. Loop over the 5 questions, time each answer
results = []
for q in questions:
    start = time.time()
    answer = ask(json.dumps(q, ensure_ascii=False))
    seconds = round(time.time() - start, 1)
    print(f"Q{q['id']} done ({seconds}s)")
    results.append({"id": q["id"], "model": MODEL, "seconds": seconds, "answer": answer})

# 6. Save the results
out = HERE / f"results_{MODEL.replace(':', '_')}_{VERSION}.json"
out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print("Saved:", out)