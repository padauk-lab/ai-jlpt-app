"""Version 1 of the API. Every router here is served under /api/v1."""

from fastapi import APIRouter

from app.api.v1 import dashboard, exams, onboarding, settings

api_router = APIRouter()
api_router.include_router(onboarding.router)
api_router.include_router(dashboard.router)
api_router.include_router(exams.router)
api_router.include_router(settings.router)
