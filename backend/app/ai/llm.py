"""Calls the LLM service (Gemini). This is the only file that talks to the AI provider.

Settings come from the environment (.env), never from code:
- LLM_API_KEY: the API key (never commit it)
- LLM_MODEL: the exact model name, for example gemini-3.8-flash
"""

import json
import os
import time
import urllib.error
import urllib.request

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# A user is waiting on the screen, so give up quickly: at most 20s + 5s wait + 20s = 45 seconds.
# The app then shows "try again later" (503). Slow test scripts set their own longer timeout.
RETRIES = 2            # 1 try + 1 retry on 503 (waits 5s)
TIMEOUT_SECONDS = 20


class AIUnavailableError(Exception):
    """The AI did not give a usable answer. The route returns 503 "Try again later"."""


def model_name() -> str:
    return os.environ["LLM_MODEL"]


def generate_json(system: str, user: str) -> str:
    """Send one prompt and return the AI's answer (JSON text)."""
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    req = urllib.request.Request(
        GEMINI_URL.format(model=model_name()),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["LLM_API_KEY"]},
    )
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as res:
                data = json.loads(res.read())
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code == 503 and attempt < RETRIES - 1:
                time.sleep(5 * 2**attempt)  # server busy: wait, then try again
                continue
            raise AIUnavailableError(f"LLM returned HTTP {e.code}") from e
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError) as e:
            raise AIUnavailableError(f"LLM call failed: {type(e).__name__}") from e
    raise AIUnavailableError("LLM still busy after retries")