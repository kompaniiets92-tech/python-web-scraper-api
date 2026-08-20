import pytest
from pydantic import ValidationError

from app.models.item import ScrapedItem


def test_valid_item_passes_validation():
    item = ScrapedItem(title="A valid story title", url="https://example.com/article")

    assert item.title == "A valid story title"
    assert str(item.url) == "https://example.com/article"


def test_empty_title_is_rejected():
    with pytest.raises(ValidationError):
        ScrapedItem(title="", url="https://example.com/article")


def test_invalid_url_is_rejected():
    with pytest.raises(ValidationError):
        ScrapedItem(title="Some title", url="not-a-valid-url")


def test_non_http_scheme_is_rejected():
    with pytest.raises(ValidationError):
        ScrapedItem(title="Some title", url="ftp://example.com/file")
