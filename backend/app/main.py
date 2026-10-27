import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import api_router
from app.core.cors import add_cors
from app.core.errors import register_error_handlers
from app.notifications.scheduler import start_reminder_loop

# The order of this list is the order of the groups in /docs.
TAGS = [
    {"name": "1. Onboarding", "description": "Contract endpoints #1 to #10"},
    {"name": "2. Dashboard, sessions and units", "description": "Contract endpoints #11 to #18"},
    {"name": "3. Quiz and mock test", "description": "Contract endpoints #19 to #26"},
    {"name": "4. AI and settings", "description": "Contract endpoints #27 to #37"},
]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    stop_reminders = start_reminder_loop()  # only runs when PUSH_MODE is log or expo
    yield
    if stop_reminders:
        stop_reminders()


app = FastAPI(title="AI JLPT App API", openapi_tags=TAGS, lifespan=lifespan)
register_error_handlers(app)
add_cors(app, os.environ.get("CORS_ORIGINS", ""))
app.include_router(api_router, prefix="/api/v1")


# GET and HEAD: uptime checkers (UptimeRobot) often send HEAD ("are you there?", no body needed).
@app.api_route("/health", methods=["GET", "HEAD"])
def health() -> dict[str, str]:
    return {"status": "ok"}
