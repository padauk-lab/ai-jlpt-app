import json
import os 
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent              # backend/scripts/ai_eval
ROOT = HERE.parents[2]                    # ai-jlpt-app

# Load LLM_API_KEY from .env
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())

# Ask Google which models this key can use
req = urllib.request.Request(
    "https://generativelanguage.googleapis.com/v1beta/models?pageSize=100",
    headers={"x-goog-api-key": os.environ["LLM_API_KEY"]},
)
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read())

# Print only Gemini models that can write text
for m in data["models"]:
    if "generateContent" in m.get("supportedGenerationMethods", []) and "gemini" in m["name"]:
        print(m["name"].removeprefix("models/"))