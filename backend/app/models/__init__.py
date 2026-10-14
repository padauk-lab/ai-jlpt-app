"""Import every model here, so Alembic can find all tables in one place."""

from app.models.ai import AIExplanation, AIUsage
from app.models.content import Example, Grammar, Proverb, StudySession, Unit, Word
from app.models.exams import MockTest, Question, Quiz, ReadingPassage
from app.models.plan import Plan, StudySettings
from app.models.progress import (
    Bookmark,
    MockAnswer,
    MockAttempt,
    QuizAnswer,
    QuizAttempt,
    QuizAttemptQuestion,
    UnitProgress,
)
from app.models.users import Device, NotificationSettings, PasswordResetToken, RefreshToken, User

__all__ = [
    # Group 1: users and login
    "Device",
    "NotificationSettings",
    "PasswordResetToken",
    "RefreshToken",
    "User",
    # Group 2: study setup and plan
    "Plan",
    "StudySettings",
    # Group 3: learning content
    "Example",
    "Grammar",
    "Proverb",
    "StudySession",
    "Unit",
    "Word",
    # Group 4: quizzes and mock tests
    "MockTest",
    "Question",
    "Quiz",
    "ReadingPassage",
    # Group 5: user progress and AI
    "AIExplanation",
    "AIUsage",
    "Bookmark",
    "MockAnswer",
    "MockAttempt",
    "QuizAnswer",
    "QuizAttempt",
    "QuizAttemptQuestion",
    "UnitProgress",
]
