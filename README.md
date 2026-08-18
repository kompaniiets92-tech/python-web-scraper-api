# Python Web Scraper & Data API — FastAPI, Playwright, PostgreSQL

A small, production-style web scraping application that scrapes Hacker News and exposes the collected items through a REST API.

- The scraper uses Playwright (synchronous API) to fetch Hacker News front page stories and validates each item with Pydantic v2.
- Validated items are persisted to PostgreSQL via SQLAlchemy and exposed from a simple FastAPI application.

This README documents the current implementation, API endpoints, local setup, and example requests.

---

## Architecture

- Scraper layer
  - app/scraper/scraper.py
  - Uses Playwright (synchronous) to fetch https://news.ycombinator.com/ and extract story title and URL.
  - Returns a list of validated Pydantic `ScrapedItem` objects and does NOT perform persistence.

- Validation layer
  - app/models/item.py
  - Pydantic v2 model `ScrapedItem` enforces a non-empty title and a valid HTTP/HTTPS URL.

- Persistence layer
  - app/models/database.py (SQLAlchemy ORM model `ScrapedItemDB`)
  - app/db/session.py provides the SQLAlchemy engine and `get_session()` context manager.
  - Database-level duplicate protection: a UNIQUE constraint named `uq_scraped_items_url` is defined on `scraped_items.url`.

- API layer
  - app/api/items.py exposes two endpoints:
    - GET /api/items — paginated read of persisted items
    - POST /api/scrape — run the scraper, validate results, insert only new URLs
  - app/main.py registers the router and provides GET /health.

Duplicate protection strategy
- The POST /api/scrape endpoint first queries the database for existing URLs (single SELECT with WHERE url IN (...)) and inserts only the non-existing ones.
- The database UNIQUE(url) constraint (`uq_scraped_items_url`) is the final safety net against races/duplicates. The API handles IntegrityError to respond sensibly if a race occurs.

---

## Tech stack

- Python 3.x
- FastAPI
- Playwright (synchronous API)
- PostgreSQL
- SQLAlchemy (ORM)
- Pydantic v2

---

## API Endpoints (current implementation)

### GET /health
- Method: GET
- Path: `/health`
- Purpose: Simple health check
- Example response (200):

{
  "status": "ok"
}

---

### GET /api/items
- Method: GET
- Path: `/api/items`
- Query parameters:
  - `limit` (int): default 20, minimum 1, maximum 100
  - `offset` (int): default 0, minimum 0
- Behavior:
  - Returns persisted `ScrapedItemResponse` objects ordered by `id` descending (newest first).
  - Pagination is implemented via `offset` and `limit` and applied in the SQL query using `offset()` and `limit()`.
- Response model: list of objects with fields `id`, `title`, `url`, `scraped_at` (ISO datetime).

Example response (200):

[
  {
    "id": 42,
    "title": "Example Hacker News story",
    "url": "https://example.com/article",
    "scraped_at": "2026-08-18T12:34:56.789Z"
  }
]

---

### POST /api/scrape
- Method: POST
- Path: `/api/scrape`
- Query parameters:
  - `limit` (int): default 10, minimum 1, maximum 50
- Behavior:
  - Calls the scraper function `scrape_news_hackernews(limit)` (synchronous Playwright scraper).
  - Validates scraped items with the Pydantic `ScrapedItem` model.
  - Checks which scraped URLs already exist (single SELECT WHERE url IN (...)).
  - Inserts only the new URLs in a single transaction; commits once after adding all new items.
  - If a race causes a duplicate at insert time, the code catches `IntegrityError`, rolls back, recomputes counts, and returns the appropriate result.
- Response model: `ScrapeResult` with fields:
  - `scraped` (int) — number of valid items returned by the scraper
  - `saved` (int) — number of new rows actually inserted
  - `skipped` (int) — number of scraped URLs already present (scraped - saved)
  - `items` (list) — list of newly inserted items (each has `id`, `title`, `url`, `scraped_at`)

Example response (201/200):

{
  "scraped": 5,
  "saved": 3,
  "skipped": 2,
  "items": [
    {
      "id": 101,
      "title": "A newly scraped story",
      "url": "https://example.com/new-article",
      "scraped_at": "2026-08-19T00:10:00.123Z"
    }
  ]
}

Note: if the scraper returns zero items the endpoint returns `scraped=0, saved=0, skipped=0, items=[]`.

---

## Duplicate protection (how it works now)

1. Application-level check: POST /api/scrape collects all scraped URLs and queries the database once to find existing URLs. Only items whose URL is not in that result set are inserted.

2. Database-level safety: `scraped_items.url` has a UNIQUE constraint (`uq_scraped_items_url`) defined in `app/models/database.py`. This is the final protection against duplicates in concurrent scenarios.

3. Race handling: the insertion loop is wrapped to catch `sqlalchemy.exc.IntegrityError`. If an IntegrityError occurs (another worker inserted the same URL concurrently), the transaction is rolled back, the endpoint recomputes saved/skipped counts and returns the newly present rows. This behavior is implemented in the current POST /api/scrape handler.

---

## Local setup (Windows / PowerShell)

1. Clone the repository

   git clone <repo-url>
   cd python-web-scraper-api

2. Create and activate a virtual environment (PowerShell)

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   (If using CMD.exe)
   .\.venv\Scripts\activate.bat

3. Install Python dependencies

   pip install -r requirements.txt

4. Install Playwright browsers (Chromium is required by the scraper)

   python -m playwright install chromium

5. Configure the database connection

   The application reads `DATABASE_URL` from the environment. You may create a `.env` file at the project root for local development. An example file is provided in `.env.example`.

   Example (do NOT commit real credentials):
   - Create a `.env` file based on `.env.example` and set:
     DATABASE_URL=postgresql://username:password@host:5432/dbname

   Alternatively set the environment variable in PowerShell:

   $env:DATABASE_URL = "postgresql://username:password@host:5432/dbname"

   Note: `app/db/session.py` will raise a RuntimeError if `DATABASE_URL` is not set.

---

## Running the API (development)

Start the FastAPI app with Uvicorn (reload mode useful during development):

PowerShell:

.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

Or (if python on PATH):

python -m uvicorn app.main:app --reload

The API will be available at http://127.0.0.1:8000 by default.

---

## Example requests (PowerShell)

GET /health

$response = Invoke-RestMethod -Method GET -Uri http://127.0.0.1:8000/health
$response | ConvertTo-Json -Depth 5

Example response:

{
  "status": "ok"
}


GET /api/items?limit=5

$response = Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/api/items?limit=5"
$response | ConvertTo-Json -Depth 5

Example response:

[
  {
    "id": 42,
    "title": "Example Hacker News story",
    "url": "https://example.com/article",
    "scraped_at": "2026-08-18T12:34:56.789Z"
  }
]


GET /api/items?limit=5&offset=0

$response = Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/api/items?limit=5&offset=0"
$response | ConvertTo-Json -Depth 5

(Same response shape as above)


POST /api/scrape?limit=5

$response = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/scrape?limit=5"
$response | ConvertTo-Json -Depth 5

Example response (one possible outcome):

{
  "scraped": 5,
  "saved": 2,
  "skipped": 3,
  "items": [
    {
      "id": 101,
      "title": "A newly scraped story",
      "url": "https://example.com/new-article",
      "scraped_at": "2026-08-19T00:10:00.123Z"
    },
    {
      "id": 102,
      "title": "Another new story",
      "url": "https://example.com/another",
      "scraped_at": "2026-08-19T00:10:01.456Z"
    }
  ]
}

Note: actual numbers depend on current database contents.

---

## API documentation

FastAPI provides interactive API docs when the application is running:

- OpenAPI UI (Swagger): http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

These endpoints are available by default when running the app locally with Uvicorn.

---

## Project structure (important files)

- app/
  - main.py            # FastAPI app and /health
  - api/
    - items.py         # GET /api/items, POST /api/scrape
  - scraper/
    - scraper.py       # Playwright-based synchronous scraper (returns Pydantic objects)
  - models/
    - item.py          # Pydantic ScrapedItem
    - item_response.py # Pydantic response model for persisted items
    - scrape_response.py # Pydantic model for POST /api/scrape responses
    - database.py      # SQLAlchemy model (ScrapedItemDB) with UNIQUE(url)
  - db/
    - session.py       # DATABASE_URL-driven SQLAlchemy engine and get_session()

- scripts/              # helper scripts (create tables, add constraints, verify DB)
- requirements.txt
- .env.example
- README.md

---

## Notes and limitations

- The scraper is synchronous and uses Playwright; ensure browsers are installed (`python -m playwright install chromium`).
- The scraper function is intentionally pure: it only scrapes and validates items. Database persistence is performed by the API layer.
- The project does not include Dockerfiles, CI/CD, or deployment configuration in this repository.
- The database connection must be provided via the `DATABASE_URL` environment variable or a `.env` file at project root. `app/db/session.py` raises a `RuntimeError` at import time if `DATABASE_URL` is missing.

---

## Changes made to README.md

- Replaced the placeholder README with a comprehensive, accurate description of the current implementation, including architecture, endpoints, setup, and examples.

---

If anything in the README appears inconsistent with your local setup after pulling the repository, please run the application locally and report the output; I can update the README accordingly.
