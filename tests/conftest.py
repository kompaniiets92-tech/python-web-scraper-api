"""Shared pytest fixtures.

Tests use a temporary SQLite database file instead of PostgreSQL so the
suite can run without any external services. The app code itself is
database-agnostic (plain SQLAlchemy), so this is a faithful functional
test of the API logic, duplicate-protection behavior, and validation.

DATABASE_URL must be set before app.db.session is imported anywhere,
since that module raises RuntimeError at import time if it's missing.
This file sets it as the very first thing pytest does (conftest.py is
imported before test modules), so it's safe to import the app normally
in test files.
"""
import os
import tempfile
from pathlib import Path

import pytest

# --- Set DATABASE_URL before any app module is imported ---
_tmp_dir = tempfile.mkdtemp(prefix="scraper_api_tests_")
_db_path = Path(_tmp_dir) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.models.database import Base, ScrapedItemDB  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """Create all tables once for the whole test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db():
    """Ensure every test starts with an empty scraped_items table."""
    with engine.begin() as conn:
        conn.execute(ScrapedItemDB.__table__.delete())
    yield


@pytest.fixture
def client():
    """FastAPI TestClient for making requests against the app."""
    return TestClient(app)
