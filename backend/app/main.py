from fastapi import FastAPI

from app.api.v1 import api_router
from app.core.errors import register_error_handlers

# The order of this list is the order of the groups in /docs.
TAGS = [
    {"name": "1. Onboarding", "description": "Contract endpoints #1 to #10"},
    {"name": "2. Dashboard, sessions and units", "description": "Contract endpoints #11 to #18"},
    {"name": "3. Quiz and mock test", "description": "Contract endpoints #19 to #26"},
    {"name": "4. AI and settings", "description": "Contract endpoints #27 to #37"},
]

app = FastAPI(title="AI JLPT App API", openapi_tags=TAGS)
register_error_handlers(app)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
