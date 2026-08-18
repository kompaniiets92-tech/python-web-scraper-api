from typing import List
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError

from app.models.item_response import ScrapedItemResponse
from app.models.scrape_response import ScrapeResult

router = APIRouter()


@router.get("/items", response_model=List[ScrapedItemResponse], summary="List scraped items", description="Return scraped items ordered by newest first. Supports pagination via limit and offset.")
def get_items(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    """Return up to `limit` scraped items ordered by id descending.

    Query parameters:
    - limit: maximum number of items to return (default 20, min 1, max 100)
    - offset: number of items to skip (default 0, min 0)
    """
    # Import DB-related objects inside the handler to avoid import-time DB config checks
    from app.db.session import get_session
    from app.models.database import ScrapedItemDB

    with get_session() as session:
            rows = session.query(ScrapedItemDB).order_by(ScrapedItemDB.id.desc()).offset(offset).limit(limit).all()

    # Convert ORM objects to pydantic response models using from_attributes
    return [ScrapedItemResponse.model_validate(row) for row in rows]


@router.post("/scrape", response_model=ScrapeResult, summary="Run scraper and persist new items", description="Scrape Hacker News up to `limit` items, validate, insert only new URLs, and return counts and newly inserted items.")
def post_scrape(limit: int = Query(10, ge=1, le=50)):
    """Run the scraper, validate items, persist new ones, and return result.

    Parameters:
    - limit: maximum number of items to scrape from the source (default 10, min 1, max 50)

    The endpoint will:
    - scrape up to `limit` items using the existing scraper
    - validate items with the existing Pydantic model
    - insert only items whose URL is not already present in the database
    - commit all new items in a single transaction
    - return counts for scraped, saved (new inserts), skipped (already existing), and the list of newly inserted items
    """
    # Import scraper function and DB-related objects lazily
    from app.scraper.scraper import scrape_news_hackernews
    from app.db.session import get_session
    from app.models.database import ScrapedItemDB

    # Run the scraper (synchronous)
    try:
        scraped_items = scrape_news_hackernews(limit)
    except RuntimeError as rexc:
        # Scraper failed (Playwright or network error)
        raise HTTPException(status_code=502, detail="Scraper error") from rexc

    scraped_count = len(scraped_items)

    if scraped_count == 0:
        return ScrapeResult(scraped=0, saved=0, skipped=0, items=[])

    # Determine existing URLs to avoid inserting duplicates
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError

    try:
        with get_session() as session:
            urls = [str(item.url) for item in scraped_items]
            if urls:
                existing = set(session.execute(select(ScrapedItemDB.url).where(ScrapedItemDB.url.in_(urls))).scalars().all())
            else:
                existing = set()

            new_items = [item for item in scraped_items if str(item.url) not in existing]

            if not new_items:
                # Nothing new to insert
                skipped_count = len(scraped_items)
                return ScrapeResult(scraped=scraped_count, saved=0, skipped=skipped_count, items=[])

            # Insert only new items
            new_urls = [str(item.url) for item in new_items]
            try:
                for item in new_items:
                    session.add(ScrapedItemDB(title=item.title, url=str(item.url)))
                session.commit()
            except IntegrityError as ie:
                # Handle race condition where another process inserted the same URL(s)
                session.rollback()
                # Recompute how many of the scraped URLs are now in the DB
                total_now = set(session.execute(select(ScrapedItemDB.url).where(ScrapedItemDB.url.in_(urls))).scalars().all())
                saved_count = len(total_now - existing)
                skipped_count = scraped_count - saved_count
                # Fetch rows for the newly present URLs
                rows = session.query(ScrapedItemDB).filter(ScrapedItemDB.url.in_(new_urls)).order_by(ScrapedItemDB.id.desc()).all()
                saved_items = [ScrapedItemResponse.model_validate(row) for row in rows]
                return ScrapeResult(scraped=scraped_count, saved=saved_count, skipped=skipped_count, items=saved_items)

            # After successful commit, fetch the rows we just inserted
            rows = session.query(ScrapedItemDB).filter(ScrapedItemDB.url.in_(new_urls)).order_by(ScrapedItemDB.id.desc()).all()
            saved_items = [ScrapedItemResponse.model_validate(row) for row in rows]
            saved_count = len(saved_items)
            skipped_count = scraped_count - saved_count

    except SQLAlchemyError as e:
            # Do not expose internal DB details to clients; return a safe error message
            raise HTTPException(status_code=500, detail="Database error")

    return ScrapeResult(scraped=scraped_count, saved=saved_count, skipped=skipped_count, items=saved_items)
