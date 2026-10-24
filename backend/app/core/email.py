"""Sending emails (for now only the password reset code, contract #5).

EMAIL_MODE in .env decides what happens:
- "log" (default, for our own computers): the email is NOT sent, it is written to the backend's log,
  so you can test "forgot password" without an email account. Never use "log" on the real server.
- "resend": sent with Resend (https://resend.com/docs/api-reference/emails/send-email),
  using RESEND_API_KEY and EMAIL_FROM. The key is a secret: only in .env, never in code or commits.

Sending never raises: if it fails, the user just asks for a new code. The reason goes to the log,
without the email address or the message, so the log holds no personal data or codes.
"""

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"
TIMEOUT_SECONDS = 10


def send_email(to: str, subject: str, text: str) -> None:
    mode = os.environ.get("EMAIL_MODE", "log")
    if mode == "log":
        logger.warning("EMAIL_MODE=log, email NOT sent (development only).\nTo: %s\nSubject: %s\n%s", to, subject, text)
        return
    if mode != "resend":
        logger.error("Unknown EMAIL_MODE %r, email not sent", mode)
        return

    body = {"from": os.environ.get("EMAIL_FROM", ""), "to": [to], "subject": subject, "text": text}
    req = urllib.request.Request(
        RESEND_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {os.environ.get('RESEND_API_KEY', '')}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as res:
            res.read()
    except urllib.error.HTTPError as e:
        logger.error("Resend refused the email: HTTP %s", e.code)
    except (urllib.error.URLError, TimeoutError) as e:
        logger.error("Could not reach Resend: %s", type(e).__name__)
