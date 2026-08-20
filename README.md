# Python Web Scraper & Data API

A ready-to-use Python web scraping and REST API starter project built with **FastAPI**, **Playwright**, **PostgreSQL**, **SQLAlchemy**, and **Pydantic v2**.

The project scrapes stories from Hacker News, validates the collected data, stores it in PostgreSQL, and exposes the stored data through a REST API.

## Features

- Automated web scraping with Playwright (synchronous API)
- Data validation with Pydantic v2
- PostgreSQL persistence via SQLAlchemy ORM
- Duplicate URL protection (app-level check + DB-level `UNIQUE` constraint + `IntegrityError` handling)
- Paginated `GET /api/items` endpoint
- Health check endpoint
- Interactive Swagger/OpenAPI docs
- Separated scraping, validation, and persistence layers
- Environment-based database configuration

## What You Get

With this purchase, you get access to the project source code and the complete starter codebase, including:

- FastAPI REST API
- Playwright web scraper
- Pydantic data validation
- PostgreSQL database integration
- SQLAlchemy models and database session management
- Duplicate URL protection
- API pagination
- Health check endpoint
- Database setup scripts
- Automated tests
- `.env.example` configuration template
- Swagger/OpenAPI documentation
- Setup and usage instructions

The project is structured so you can use the existing implementation as a starting point and adapt the scraper, data models, database layer, or API endpoints to your own use case.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.11+ | Application language |
| FastAPI | REST API framework |
| Playwright (sync API) | Web scraping |
| PostgreSQL 14+ | Data storage |
| SQLAlchemy | ORM / database access |
| Pydantic v2 | Data validation |
| Uvicorn | ASGI server |
| Pytest | Testing |

> Exact pinned versions are listed in `requirements.txt`.

## Requirements

Before starting, make sure you have installed:

- Python 3.11 or later
- PostgreSQL 14 or later, running and reachable
- Git

Playwright's Chromium browser is installed separately (see below).

## Architecture

```
Hacker News
     │
     ▼
Playwright Scraper  (app/scraper/scraper.py)
     │
     ▼
Pydantic Validation  (app/models/item.py)
     │
     ▼
Duplicate Check + Persistence  (app/api/items.py, app/models/database.py)
     │
     ▼
PostgreSQL
     │
     ▼
FastAPI REST API  (app/main.py)
```

The scraper only collects and validates data — it never touches the database directly. Persistence is handled entirely by the API layer, keeping concerns separated.

### Scraper layer — `app/scraper/scraper.py`
Uses Playwright (synchronous) to fetch `https://news.ycombinator.com/` and extract story title and URL. Returns a list of validated `ScrapedItem` objects. Does **not** perform persistence.

### Validation layer — `app/models/item.py`
Pydantic v2 model `ScrapedItem` enforces a non-empty title and a valid HTTP/HTTPS URL.

### Persistence layer — `app/models/database.py`, `app/db/session.py`
- `ScrapedItemDB` — SQLAlchemy ORM model
- `get_session()` — context manager providing a DB session
- `scraped_items.url` has a `UNIQUE` constraint named `uq_scraped_items_url`

### API layer — `app/api/items.py`, `app/main.py`
- `GET /api/items` — paginated read of persisted items
- `POST /api/scrape` — run the scraper, validate results, insert only new URLs
- `GET /health` — health check

## Duplicate Protection

1. **Application-level check** — before inserting, the API queries PostgreSQL once for existing URLs (`WHERE url IN (...)`) and inserts only URLs not already present.
2. **Database-level constraint** — `UNIQUE(url)` (`uq_scraped_items_url`) is the final safety net.
3. **Race handling** — insertion is wrapped to catch `sqlalchemy.exc.IntegrityError`. On conflict, the transaction is rolled back, counts are recomputed, and the correct result is returned.

## API Endpoints

### `GET /health`

Simple health check.

```json
{ "status": "ok" }
```

### `GET /api/items`

Returns stored items, newest first.

| Parameter | Type | Default | Limits |
|---|---|---|---|
| `limit` | int | 20 | 1–100 |
| `offset` | int | 0 | ≥ 0 |

Example: `GET /api/items?limit=5&offset=0`

```json
[
  {
    "id": 42,
    "title": "Example Hacker News story",
    "url": "https://example.com/article",
    "scraped_at": "2026-08-18T12:34:56.789Z"
  }
]
```

### `POST /api/scrape`

Runs the scraper and saves new items.

| Parameter | Type | Default | Limits |
|---|---|---|---|
| `limit` | int | 10 | 1–50 |

Example: `POST /api/scrape?limit=5`

```json
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
```

Field meanings:
- `scraped` — number of valid items returned by the scraper
- `saved` — number of new rows actually inserted
- `skipped` — number of scraped URLs already present (`scraped - saved`)
- `items` — newly inserted items

If the scraper returns zero items: `{"scraped": 0, "saved": 0, "skipped": 0, "items": []}`.

## Project Structure

```
python-web-scraper-api/
│
├── app/
│   ├── api/
│   │   └── items.py            # GET /api/items, POST /api/scrape
│   ├── db/
│   │   └── session.py          # DATABASE_URL-driven engine, get_session()
│   ├── models/
│   │   ├── database.py         # SQLAlchemy model, UNIQUE(url)
│   │   ├── item.py             # Pydantic ScrapedItem
│   │   ├── item_response.py    # Response model for persisted items
│   │   └── scrape_response.py  # Response model for POST /api/scrape
│   ├── scraper/
│   │   └── scraper.py          # Playwright-based synchronous scraper
│   └── main.py                 # FastAPI app, /health
│
├── scripts/                    # DB helper scripts (see below)
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/kompaniiets92-tech/python-web-scraper-api.git
cd python-web-scraper-api
```

### 2. Create and activate a virtual environment

**Windows PowerShell**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows CMD**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright's Chromium browser

```bash
python -m playwright install chromium
```

## Database Configuration

The application reads the connection string from the `DATABASE_URL` environment variable.

`.env.example`:
```
DATABASE_URL=postgresql://username:password@localhost:5432/dbname
```

Copy it to `.env` and fill in real values:

```bash
cp .env.example .env   # macOS/Linux
copy .env.example .env # Windows CMD
```

Or set it directly (PowerShell):

```powershell
$env:DATABASE_URL = "postgresql://username:password@localhost:5432/dbname"
```

> If `DATABASE_URL` is not set, `app/db/session.py` raises a `RuntimeError` at import time.

**Never commit real credentials to the repository.**

## Database Setup

The `scripts/` directory contains two helper scripts. Run them in this order after configuring `DATABASE_URL`:

```bash
python scripts/create_tables.py
python scripts/verify_database.py
```

**`create_tables.py`**
Imports `Base` from `app.models.database` and `engine` from `app.db.session`, then runs `Base.metadata.create_all(bind=engine)`. This creates the `scraped_items` table (and its `uq_scraped_items_url` unique constraint, defined on the model) if it doesn't already exist. It reads `DATABASE_URL` from the environment — no connection string is hardcoded.

**`verify_database.py`**
Connects to the database and reports:
- whether the `scraped_items` table exists
- any duplicate URLs currently stored
- whether the `uq_scraped_items_url` unique constraint is present
- the total row count in `scraped_items`

Useful as a quick sanity check after setup or after running the scraper.

## Running the API

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Interactive API Documentation

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Example Requests (PowerShell)

**Health check**
```powershell
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/health" | ConvertTo-Json -Depth 5
```

**Get stored items**
```powershell
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/api/items?limit=5" | ConvertTo-Json -Depth 5
```

**Trigger scraping**
```powershell
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/scrape?limit=5" | ConvertTo-Json -Depth 5
```

## Testing

```bash
pytest
```

## Demo

### Swagger API

The project includes interactive Swagger/OpenAPI documentation at:

```
/docs
```

### Example workflow

1. Configure PostgreSQL
2. Run the database setup script
3. Start the FastAPI application
4. Open `/docs`
5. Run `POST /api/scrape`
6. Retrieve collected data with `GET /api/items`

## Scope

This product is a focused starter codebase, not a hosted scraping service or a universal scraping platform.

It does not currently include:

- hosted infrastructure
- Docker configuration
- CI/CD pipelines
- deployment configuration
- authentication or authorization
- a web frontend
- scheduled scraping
- support for multiple scraping targets out of the box

The included architecture is designed to provide a clean foundation for adding these capabilities.

Additional current limitations:

- The scraper targets Hacker News only.
- Playwright uses the synchronous API.
- Chromium must be installed separately.
- PostgreSQL is required — no SQLite fallback.

## Customization Potential

The layered architecture (scraper → validation → persistence → API) makes it straightforward to extend with:

- additional scraping targets or data fields
- scheduled/background scraping jobs
- authentication
- Docker-based development and deployment
- additional database models and endpoints

## License

This project is distributed under a commercial license.

The purchaser receives a license to use and modify the source code according to the terms of the included license agreement.

Redistribution, resale, or publication of the source code as a standalone product is not permitted unless explicitly authorized by the copyright holder.

## Support

For questions about setup, customization, or extending the project, contact the seller through the platform where this product was purchased.
