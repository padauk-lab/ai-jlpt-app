"""Version 1 of the API. Every router here is served under /api/v1."""

from fastapi import APIRouter

from app.api.v1 import auth, dashboard, exams, onboarding, proverbs, settings

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(onboarding.router)
# The old #12 placeholder still sits in dashboard.py. It is removed from the dashboard router here,
# so only the real one in proverbs.py answers. (Delete the placeholder and these lines once the
# session and unit pull request is merged, to avoid two pull requests editing dashboard.py at once.)
dashboard.router.routes = [r for r in dashboard.router.routes if getattr(r, "path", None) != "/proverbs/today"]
api_router.include_router(dashboard.router)
api_router.include_router(proverbs.router)  # #12
api_router.include_router(exams.router)
api_router.include_router(settings.router)
