"""Import every model here, so Alembic can find all tables in one place."""

from app.models.content import Example, Grammar, Proverb, StudySession, Unit, Word
from app.models.plan import ExamDate, Plan, StudySettings
from app.models.users import Device, NotificationSettings, PasswordResetToken, RefreshToken, User

__all__ = [
    # Group 1: users and login
    "Device",
    "NotificationSettings",
    "PasswordResetToken",
    "RefreshToken",
    "User",
    # Group 2: study setup and plan
    "ExamDate",
    "Plan",
    "StudySettings",
    # Group 3: learning content
    "Example",
    "Grammar",
    "Proverb",
    "StudySession",
    "Unit",
    "Word",
]
