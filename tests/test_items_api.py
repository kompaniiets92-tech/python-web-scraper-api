"""Tests for the /api/items and /api/scrape endpoints.

The Playwright-based scraper (app.scraper.scraper.scrape_news_hackernews)
is monkeypatched in these tests, so no real browser or network access is
needed. This isolates the tests to the API/persistence logic: pagination,
insertion, and — most importantly — the duplicate-URL protection.
"""
from app.models.item import ScrapedItem

FAKE_ITEMS = [
    ScrapedItem(title="First story", url="https://example.com/first"),
    ScrapedItem(title="Second story", url="https://example.com/second"),
]


def _patch_scraper(monkeypatch, items):
    def fake_scrape(limit=10):
        return items[:limit]

    monkeypatch.setattr(
        "app.scraper.scraper.scrape_news_hackernews", fake_scrape
    )


def test_get_items_empty_by_default(client):
    response = client.get("/api/items")

    assert response.status_code == 200
    assert response.json() == []


def test_scrape_saves_new_items(client, monkeypatch):
    _patch_scraper(monkeypatch, FAKE_ITEMS)

    response = client.post("/api/scrape", params={"limit": 5})
    body = response.json()

    assert response.status_code == 200
    assert body["scraped"] == 2
    assert body["saved"] == 2
    assert body["skipped"] == 0
    assert len(body["items"]) == 2
    assert {item["url"] for item in body["items"]} == {
        "https://example.com/first",
        "https://example.com/second",
    }


def test_scraped_items_are_persisted_and_listable(client, monkeypatch):
    _patch_scraper(monkeypatch, FAKE_ITEMS)
    client.post("/api/scrape", params={"limit": 5})

    response = client.get("/api/items")
    body = response.json()

    assert response.status_code == 200
    assert len(body) == 2
    # newest first (ordered by id descending)
    assert body[0]["title"] == "Second story"
    assert body[1]["title"] == "First story"


def test_scraping_same_items_twice_skips_duplicates(client, monkeypatch):
    """This is the core guarantee of the app: re-scraping the same URLs
    must not create duplicate rows, and the response must report the
    right saved/skipped counts."""
    _patch_scraper(monkeypatch, FAKE_ITEMS)

    first = client.post("/api/scrape", params={"limit": 5}).json()
    assert first["saved"] == 2
    assert first["skipped"] == 0

    second = client.post("/api/scrape", params={"limit": 5}).json()
    assert second["scraped"] == 2
    assert second["saved"] == 0
    assert second["skipped"] == 2
    assert second["items"] == []

    # Confirm no duplicate rows were actually written to the database
    items = client.get("/api/items").json()
    assert len(items) == 2


def test_partial_duplicate_scrape_only_saves_new_items(client, monkeypatch):
    _patch_scraper(monkeypatch, FAKE_ITEMS)
    client.post("/api/scrape", params={"limit": 1})  # saves only "First story"

    _patch_scraper(monkeypatch, FAKE_ITEMS)
    result = client.post("/api/scrape", params={"limit": 5}).json()

    assert result["scraped"] == 2
    assert result["saved"] == 1
    assert result["skipped"] == 1
    assert result["items"][0]["title"] == "Second story"


def test_scrape_with_no_items_returns_zero_counts(client, monkeypatch):
    _patch_scraper(monkeypatch, [])

    response = client.post("/api/scrape", params={"limit": 5})
    body = response.json()

    assert response.status_code == 200
    assert body == {"scraped": 0, "saved": 0, "skipped": 0, "items": []}


def test_items_pagination_limit_and_offset(client, monkeypatch):
    many_items = [
        ScrapedItem(title=f"Story {i}", url=f"https://example.com/story-{i}")
        for i in range(5)
    ]
    _patch_scraper(monkeypatch, many_items)
    client.post("/api/scrape", params={"limit": 5})

    page1 = client.get("/api/items", params={"limit": 2, "offset": 0}).json()
    page2 = client.get("/api/items", params={"limit": 2, "offset": 2}).json()

    assert len(page1) == 2
    assert len(page2) == 2
    assert page1[0]["id"] != page2[0]["id"]


def test_scrape_limit_query_param_is_validated(client):
    # limit must be between 1 and 50 per the endpoint's Query constraints
    response = client.post("/api/scrape", params={"limit": 0})
    assert response.status_code == 422

    response = client.post("/api/scrape", params={"limit": 51})
    assert response.status_code == 422


def test_items_limit_query_param_is_validated(client):
    # limit must be between 1 and 100 per the endpoint's Query constraints
    response = client.get("/api/items", params={"limit": 0})
    assert response.status_code == 422

    response = client.get("/api/items", params={"limit": 101})
    assert response.status_code == 422
