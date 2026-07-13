"""
REST routes for scraping websites and storing content in MongoDB.
"""
from fastapi import APIRouter

from backend.core import database as db
from backend.core.component_parser import parse_page
from backend.core.logger import get_logger
from backend.core.scraper import scrape_url
from backend.core.scraper_site import scrape_site

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

    # Store raw page content
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

    # Parse and store components from the HTML
    components_stored = 0
    try:
        raw_html = scraped.get("raw_html", "")
        if raw_html:
            components = parse_page(raw_html, scraped["url"], scraped["title"])
            components_stored = await db.store_components(scraped["url"], scraped["title"], components)
    except Exception as comp_err:
        logger.warning("Component parsing/storage failed: %s", comp_err)

    return {
        "id": doc_id,
        "url": scraped["url"],
        "title": scraped["title"],
        "content_preview": scraped["content"][:300] + ("..." if len(scraped["content"]) > 300 else ""),
        "components_stored": components_stored,
    }


@router.get("/pages")
async def list_pages():
    """List all scraped pages stored in MongoDB."""
    pages = await db.get_all_pages()
    logger.info("Listed %d pages from DB", len(pages))
    return {"pages": pages, "count": len(pages)}


@router.post("/scrape-site")
async def scrape_site_endpoint(url: str, max_concurrency: int = 3):
    """
    Scrape an entire website in one shot.

    Uses Playwright (headless browser) to render JavaScript SPAs like React,
    discovers all internal links, and scrapes each page.

    Args:
        url: Base URL of the site to scrape (e.g. http://localhost:5174).
        max_concurrency: Max parallel page renders (default 3).

    Returns:
        Dict with scraped pages, total count, and any errors.
    """
    logger.info("Site scrape requested: %s (concurrency=%d)", url, max_concurrency)

    if not url or not url.startswith(("http://", "https://")):
        return {"error": "Invalid URL. Must start with http:// or https://"}

    result = await scrape_site(url, max_concurrency=max_concurrency)

    if result.get("errors"):
        logger.warning("Site scrape had %d errors", len(result["errors"]))

    # Store all scraped pages and components in MongoDB
    stored = []
    failed = []
    total_components = 0
    for page in result["pages"]:
        if not page.get("content") or page["content"].startswith("[Render failed"):
            failed.append(page["url"])
            continue
        try:
            doc_id = await db.store_page(
                url=page["url"],
                title=page["title"],
                content=page["content"],
                metadata={"source": "playwright", "base_url": url},
            )
            # Parse and store components from the rendered HTML
            raw_html = page.get("raw_html", "")
            if raw_html:
                components = parse_page(raw_html, page["url"], page["title"])
                comp_count = await db.store_components(page["url"], page["title"], components)
                total_components += comp_count

            stored.append({
                "id": doc_id,
                "url": page["url"],
                "title": page["title"],
                "content_preview": page["content"][:200] + ("..." if len(page["content"]) > 200 else ""),
            })
        except Exception as db_err:
            logger.warning("Failed to store %s: %s", page["url"], db_err)
            failed.append(page["url"])

    return {
        "stored": len(stored),
        "failed": len(failed),
        "pages": stored,
        "failed_urls": failed,
        "errors": result.get("errors", []),
        "total_components_stored": total_components,
    }


# ──────────────────────────────────────────────
#  Component Registry Endpoints
# ──────────────────────────────────────────────

@router.get("/components")
async def list_components(limit: int = 50):
    """List all stored components in the registry."""
    components = await db.get_all_components(limit=limit)
    types = await db.get_component_types()
    logger.info("Listed %d components (%d types)", len(components), len(types))
    return {"components": components, "count": len(components), "types": types}


@router.get("/components/types")
async def list_component_types():
    """Get all distinct component types in the registry."""
    types = await db.get_component_types()
    return {"types": types, "count": len(types)}


@router.get("/components/search")
async def search_components(query: str = "", type: str = "", limit: int = 15):
    """Search components by text, optionally filtered by type."""
    component_type = type if type else None
    results = await db.search_components(query, component_type=component_type, limit=limit)
    return {"results": results, "count": len(results)}


# ──────────────────────────────────────────────
#  Clear / Reset Endpoints
# ──────────────────────────────────────────────

@router.delete("/pages")
async def clear_pages():
    """Delete all scraped pages (for testing/cleanup)."""
    count = await db.delete_all_pages()
    logger.warning("Deleted all pages from DB: %d removed", count)
    return {"deleted": count, "message": f"Deleted {count} pages"}


@router.delete("/components")
async def clear_components():
    """Delete all stored components (for testing/cleanup)."""
    count = await db.delete_all_components()
    logger.warning("Deleted all components from DB: %d removed", count)
    return {"deleted": count, "message": f"Deleted {count} components"}


@router.delete("/all")
async def clear_all():
    """Delete all pages and components (full reset)."""
    pages = await db.delete_all_pages()
    components = await db.delete_all_components()
    logger.warning("Full reset: deleted %d pages and %d components", pages, components)
    return {"pages_deleted": pages, "components_deleted": components, "message": "All data cleared"}
