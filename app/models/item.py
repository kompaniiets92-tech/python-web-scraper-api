from pydantic import BaseModel, Field, HttpUrl


class ScrapedItem(BaseModel):
    """Pydantic model for a scraped item.

    Validation rules:
    - title: non-empty string (min_length=1)
    - url: valid HTTP or HTTPS URL (HttpUrl)
    """

    title: str = Field(..., min_length=1)
    url: HttpUrl
