"""Playwright-based scraper for Hacker News (synchronous).

The scraper is intentionally simple: it fetches the Hacker News
front page, extracts story titles and URLs, validates each item
using the project's Pydantic ScrapedItem model, and returns a list
of validated items. It does NOT perform any database operations.
"""
from typing import List
from playwright.sync_api import sync_playwright, Error as PlaywrightError
from pydantic import ValidationError

# Import the Pydantic model (v2) for validation
from app.models.item import ScrapedItem as PydanticScrapedItem


def scrape_news_hackernews(limit: int = 10) -> List[PydanticScrapedItem]:
    """Scrape up to `limit` stories from Hacker News and return validated items.

    Args:
        limit: maximum number of stories to return (must be >= 1)

    Returns:
        List of validated Pydantic ScrapedItem instances.

    Raises:
        ValueError: if limit is less than 1.
        RuntimeError: if Playwright fails to run (original exception chained).
    """
    if limit is None or limit < 1:
        raise ValueError("limit must be >= 1")

    items: List[PydanticScrapedItem] = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context()
                try:
                    page = context.new_page()

                    # Navigate and wait for DOM content to load
                    page.goto(
                        "https://news.ycombinator.com/",
                        wait_until="domcontentloaded",
                        timeout=30_000,
                    )

                    # Wait for the story rows to appear
                    page.wait_for_selector("tr.athing", timeout=10_000)

                    rows = page.locator("tr.athing")
                    total = rows.count()
                    to_process = min(total, limit)

                    for i in range(to_process):
                        row = rows.nth(i)
                        # Resolve a single title link element; use .first to avoid strict-mode errors
                        link = row.locator(".titleline a").first
                        if link.count() == 0:
                            continue
                        # Extract and normalize from the single resolved locator
                        title = (link.inner_text() or "").strip()
                        url = (link.get_attribute("href") or "").strip()

                        if not title:
                            # skip empty titles
                            continue

                        # Validate with Pydantic; skip invalid items
                        try:
                            validated = PydanticScrapedItem.model_validate({"title": title, "url": url})
                            items.append(validated)
                        except ValidationError:
                            continue

                finally:
                    try:
                        context.close()
                    except Exception:
                        pass
            finally:
                try:
                    browser.close()
                except Exception:
                    pass

    except PlaywrightError as exc:
        raise RuntimeError("Playwright error during scraping") from exc
    except Exception as exc:
        # Wrap any other exceptions from Playwright/HTTP/network into RuntimeError
        raise RuntimeError("Unexpected error during scraping") from exc

    return items


if __name__ == "__main__":
    # Simple demonstration: print scraped items to stdout. No DB interaction here.
    import sys

    try:
        results = scrape_news_hackernews(10)
    except Exception as e:
        print(f"Scraper failed: {e}")
        sys.exit(1)

    if not results:
        print("No items scraped.")
        sys.exit(0)

    for idx, item in enumerate(results, start=1):
        print(f"{idx}. {item.title} -> {item.url}")
