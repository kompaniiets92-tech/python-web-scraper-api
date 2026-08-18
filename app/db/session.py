import os
from contextlib import contextmanager
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Load .env from the project root if present. Do NOT override real environment variables.
# This allows development using a .env file while preserving production env vars.
project_root = Path(__file__).resolve().parents[2]
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path=dotenv_path, override=False)

# Read DATABASE_URL from environment; do not hardcode credentials here
DATABASE_URL = os.getenv("DATABASE_URL")

# Note: the application should set DATABASE_URL in the environment before using the DB.
# Example value (in .env or environment):
# DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/dbname

if not DATABASE_URL:
    # Do not raise at import time in libraries generally, but here we make it explicit
    # to help developers notice the missing configuration early. If you prefer lazy
    # creation, change this behavior.
    raise RuntimeError("DATABASE_URL environment variable is not set")

# Create SQLAlchemy engine using 2.x style (future=True is default in SQLAlchemy 2)
engine = create_engine(DATABASE_URL, future=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True, class_=Session)

@contextmanager
def get_session():
    """Yield a SQLAlchemy Session and ensure it is closed afterwards.

    Usage:
        with get_session() as session:
            # use session
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
