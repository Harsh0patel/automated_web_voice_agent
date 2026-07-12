"""
REST routes for scraping websites and storing content in MongoDB.
"""
from fastapi import APIRouter

from backend.core import database as db
from backend.core.logger import get_logger
from backend.core.scraper import scrape_url

logger = get_logger(__name__)

router = APIRouter()


@router.post("/scrape")
async def scrape_and_store(url: str):
    """
    Scrape a website URL, extract text content, and store in MongoDB.

    Args:
        url: The full HTTP/HTTPS URL to scrape.

    Returns:
        Dict with the scraped document ID, title, and content preview.
    """
    logger.info("Scrape requested: %s", url)

    if not url or not url.startswith(("http://", "https://")):
        logger.warning("Invalid scrape URL rejected: %s", url)
        return {"error": "Invalid URL. Must start with http:// or https://"}

    scraped = await scrape_url(url)
    logger.info("Scraped %s — title=%.60s, content=%d chars", url, scraped["title"], len(scraped["content"]))

    try:
        doc_id = await db.store_page(
            url=scraped["url"],
            title=scraped["title"],
            content=scraped["content"],
            metadata=scraped.get("metadata"),
        )
        logger.info("Stored scraped page in MongoDB: id=%s", doc_id)
    except (ConnectionError, Exception) as db_err:
        logger.warning("Failed to store scraped page in DB: %s", db_err)
        return {
            "error": f"Scraped successfully but DB storage failed: {db_err}",
            "url": scraped["url"],
            "title": scraped["title"],
            "content_preview": scraped["content"][:300] + ("..." if len(scraped["content"]) > 300 else ""),
        }

    return {
        "id": doc_id,
        "url": scraped["url"],
        "title": scraped["title"],
        "content_preview": scraped["content"][:300] + ("..." if len(scraped["content"]) > 300 else ""),
    }


@router.get("/pages")
async def list_pages():
    """List all scraped pages stored in MongoDB."""
    pages = await db.get_all_pages()
    logger.info("Listed %d pages from DB", len(pages))
    return {"pages": pages, "count": len(pages)}


@router.delete("/pages")
async def clear_pages():
    """Delete all scraped pages (for testing/cleanup)."""
    count = await db.delete_all_pages()
    logger.warning("Deleted all pages from DB: %d removed", count)
    return {"deleted": count, "message": f"Deleted {count} pages"}
