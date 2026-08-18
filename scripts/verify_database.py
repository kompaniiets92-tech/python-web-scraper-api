"""Verify scraped_items table and uniqueness constraint."""
import sys
from sqlalchemy import text

try:
    from app.db.session import engine
except Exception as exc:
    print("Failed to import engine from app.db.session. Ensure DATABASE_URL is set and dependencies installed.")
    print(exc)
    sys.exit(1)

with engine.connect() as conn:
    # Check table exists
    table_check = conn.execute(text("SELECT to_regclass('public.scraped_items')")).scalar()
    print(f"scraped_items table exists: {bool(table_check)}")

    # Check duplicates
    dup_sql = text(
        "SELECT url, COUNT(*) FROM scraped_items GROUP BY url HAVING COUNT(*) > 1"
    )
    dups = conn.execute(dup_sql).fetchall()
    if not dups:
        print("No duplicate URLs found.")
    else:
        print("Duplicate URLs found:")
        for url, cnt in dups:
            print(f" - {url}: {cnt}")

    # Check unique constraint
    uq_check = conn.execute(text("SELECT 1 FROM pg_constraint c JOIN pg_class t ON c.conrelid = t.oid WHERE t.relname = 'scraped_items' AND c.conname = 'uq_scraped_items_url'"))
    if uq_check.first():
        print("Unique constraint 'uq_scraped_items_url' exists.")
    else:
        print("Unique constraint 'uq_scraped_items_url' NOT found.")

    # Count rows
    cnt = conn.execute(text("SELECT COUNT(*) FROM scraped_items")).scalar()
    print(f"Total rows in scraped_items: {cnt}")
