from typing import List
from pydantic import BaseModel, ConfigDict
from app.models.item_response import ScrapedItemResponse


class ScrapeResult(BaseModel):
    """Response model for POST /api/scrape."""

    model_config = ConfigDict()

    scraped: int
    saved: int
    skipped: int
    items: List[ScrapedItemResponse]
