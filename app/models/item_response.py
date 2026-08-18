from datetime import datetime
from pydantic import BaseModel, ConfigDict, HttpUrl


class ScrapedItemResponse(BaseModel):
    """Response model for persisted scraped items.

    Uses Pydantic v2 ConfigDict(from_attributes=True) to support
    model validation/serialization from SQLAlchemy ORM objects.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    url: HttpUrl
    scraped_at: datetime
