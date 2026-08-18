# Python Web Scraper & Data API

This project will become a small production-style web scraping application:
Website -> Playwright -> Scraper -> Pydantic -> PostgreSQL -> FastAPI -> REST API -> Docker

First step contents:
- Minimal FastAPI app with GET /health returning {"status": "ok"}
- Project structure with scraper and models placeholders
- requirements.txt with minimal dependencies

Run the app locally:
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
