"""Test setup.

Tests use their OWN database (its name must end with "_test"), so they can never touch real data.
The database is built with our Alembic migrations, and all user data is deleted after every test.
"""

import os
import re
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest

DATABASE_URL = os.environ.get("DATABASE_URL", "")
TEST_DB_NAME = urlsplit(DATABASE_URL).path.lstrip("/")

# Safety lock: refuse to run against anything that isn't a test database.
if not re.fullmatch(r"[a-z0-9_]+_test", TEST_DB_NAME):
    raise RuntimeError(
        f"Refusing to run tests: the database name must end with _test, got {TEST_DB_NAME!r}. "
        "Run tests with: docker compose --profile test run --rm --build tests"
    )

os.environ.setdefault("JWT_SECRET", "test-only-secret-that-is-long-enough-for-the-check")

from alembic import command  # noqa: E402  (imports after the safety lock on purpose)
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _driver_url(url: str) -> str:
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


def _create_test_database() -> None:
    admin_url = urlunsplit(urlsplit(DATABASE_URL)._replace(path="/postgres"))
    engine = create_engine(_driver_url(admin_url), isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME})
        if not exists:
            # A database name can't be a query parameter; it was checked by the regex above.
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def test_database() -> None:
    """Create the test database once and build all tables with Alembic."""
    _create_test_database()
    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")


@pytest.fixture(autouse=True)
def clean_user_data() -> Iterator[None]:
    """Every test starts with no users. Deleting users also deletes all their data (CASCADE)."""
    yield
    from app.db import engine

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))


@pytest.fixture(autouse=True)
def reset_rate_limits() -> Iterator[None]:
    """Every test starts with fresh rate limit counters."""
    from app.core.rate_limit import limiter

    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def client() -> TestClient:
    from app.main import app

    return TestClient(app, raise_server_exceptions=False)
