"""Create database tables from SQLAlchemy models.

This script imports Base and engine from the existing project and runs
Base.metadata.create_all(bind=engine). It intentionally does not hardcode
any DATABASE_URL; the application reads DATABASE_URL from the environment.

Usage (development):
  # set DATABASE_URL in env or .env at project root
  python scripts\create_tables.py

Note: In this environment a local SQLite file may be used for demonstration.
To create PostgreSQL tables, set DATABASE_URL to a PostgreSQL URL and run the script.
"""
import sys

# Import the project's Base and engine
try:
    from app.models.database import Base
    from app.db.session import engine
except Exception as exc:
    print("Failed to import project modules. Ensure DATABASE_URL is set or .env exists.")
    print(f"Import error: {exc}")
    sys.exit(1)

# Create tables
Base.metadata.create_all(bind=engine)
print("Success: database tables created (if they did not already exist).")
print("Created tables:")
for tbl in Base.metadata.sorted_tables:
    print(f" - {tbl.name}")
