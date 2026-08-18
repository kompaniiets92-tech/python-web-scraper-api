from fastapi import FastAPI

app = FastAPI(title="Python Web Scraper & Data API")


@app.get("/health", summary="Health check", description="Simple health endpoint returning status")
async def health():
    return {"status": "ok"}


# Register API routers
from app.api.items import router as items_router
app.include_router(items_router, prefix="/api")
