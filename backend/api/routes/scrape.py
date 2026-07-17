"""
REST routes for scraping websites and storing content in MongoDB.

All default limits have been increased to allow complete data capture.
"""
import traceback

from bs4 import BeautifulSoup
from fastapi import APIRouter

from backend.app import database as db
from backend.app.logger import get_logger
from backend.scraping.browser import scrape_site, discover_navigation_patterns
from backend.scraping.fetcher import scrape_url
from backend.scraping.parser import parse_page, extract_scrollable_sections, analyze_form_fields, categorize_page
from backend.scraping.prompt_generator import build_system_prompt, generate_navigation_mappings

logger = get_logger(__name__)

router = APIRouter()


@router.post("/scrape")
async def scrape_and_store(url: str):
    """Scrape a single URL, extract components, and store in MongoDB."""
    if not url or not url.startswith(("http://", "https://")):
        return {"error": "Invalid URL. Must start with http:// or https://"}

    scraped = await scrape_url(url)

    try:
        doc_id = await db.store_page(
            url=scraped["url"],
            title=scraped["title"],
            content=scraped["content"],
            metadata=scraped.get("metadata"),
        )
    except (ConnectionError, Exception) as db_err:
        return {
            "error": f"Scraped successfully but DB storage failed: {db_err}",
            "url": scraped["url"],
            "title": scraped["title"],
            "content_preview": scraped["content"][:300] + ("..." if len(scraped["content"]) > 300 else ""),
        }

    components_stored = 0
    try:
        raw_html = scraped.get("raw_html", "")
        if raw_html:
            components = parse_page(raw_html, scraped["url"], scraped["title"])
            components_stored = await db.store_components(scraped["url"], scraped["title"], components)

            soup = BeautifulSoup(raw_html, "html.parser")
            scroll_sections = extract_scrollable_sections(soup, scraped["url"])
            form_fields = analyze_form_fields(soup, scraped["url"])
            page_category = categorize_page(soup, scraped["url"])

            if scroll_sections or form_fields:
                await db.store_page_analysis(
                    url=scraped["url"],
                    page_category=page_category,
                    scroll_sections=scroll_sections,
                    form_fields=form_fields,
                )
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
    return {"pages": pages, "count": len(pages)}


@router.post("/scrape-site")
async def scrape_site_endpoint(url: str, max_pages: int = 0):
    """Scrape an entire website in one shot. max_pages=0 means no limit."""
    if not url or not url.startswith(("http://", "https://")):
        return {"error": "Invalid URL. Must start with http:// or https://"}

    try:
        result = await scrape_site(url, max_pages=max_pages)
    except Exception:
        tb = traceback.format_exc()
        return {
            "error": "Internal error during site scrape",
            "detail": tb,
            "hint": "Ensure Playwright browsers are installed: pip install playwright && playwright install chromium",
        }

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
                metadata={"source": "playwright", "base_url": url, "page_category": page.get("page_category", "info_page")},
            )
            raw_html = page.get("raw_html", "")
            if raw_html:
                components = parse_page(raw_html, page["url"], page["title"])
                comp_count = await db.store_components(page["url"], page["title"], components)
                total_components += comp_count

                soup = BeautifulSoup(raw_html, "html.parser")
                scroll_sections = extract_scrollable_sections(soup, page["url"])
                form_fields = analyze_form_fields(soup, page["url"])
                if scroll_sections or form_fields:
                    await db.store_page_analysis(
                        url=page["url"],
                        page_category=page.get("page_category", "info_page"),
                        scroll_sections=scroll_sections,
                        form_fields=form_fields,
                    )

            stored.append({
                "id": doc_id,
                "url": page["url"],
                "title": page["title"],
                "page_category": page.get("page_category", "info_page"),
                "scrollable_sections": len(page.get("scrollable_sections", [])),
                "form_fields": len(page.get("form_fields", [])),
                "content_preview": page["content"][:200] + ("..." if len(page["content"]) > 200 else ""),
            })
        except Exception as db_err:
            logger.warning("Failed to store %s: %s", page["url"], db_err)
            failed.append(page["url"])

    generated_prompt = build_system_prompt(result["pages"])

    return {
        "stored": len(stored),
        "failed": len(failed),
        "pages": stored,
        "failed_urls": failed,
        "errors": result.get("errors", []),
        "total_components_stored": total_components,
        "navigation_patterns": result.get("navigation_patterns", {}),
        "generated_system_prompt": generated_prompt,
    }


@router.post("/discover-navigation")
async def discover_navigation(url: str):
    """Discover navigation intent patterns without storing anything."""
    if not url or not url.startswith(("http://", "https://")):
        return {"error": "Invalid URL. Must start with http:// or https://"}

    try:
        patterns = await discover_navigation_patterns(url)
        all_pages = []
        for category, pages in patterns.items():
            all_pages.extend(pages)
        mappings = generate_navigation_mappings(all_pages)
        return {"patterns": patterns, "mappings": mappings, "total_pages": len(all_pages)}
    except Exception:
        tb = traceback.format_exc()
        return {"error": "Navigation discovery failed", "detail": tb}


@router.get("/generate-prompt")
async def generate_prompt_endpoint():
    """Generate a system prompt from all stored pages."""
    pages = await db.get_all_pages(limit=200)
    pages_data = []
    for p in pages:
        pages_data.append({"url": p.get("url", ""), "title": p.get("title", ""), "content": p.get("content_preview", "")})
    prompt = build_system_prompt(pages_data)
    return {"prompt": prompt, "total_pages": len(pages_data)}


# ---------------------------------------------------------------------------
# Component Registry Endpoints
# ---------------------------------------------------------------------------

@router.get("/components")
async def list_components(limit: int = 500):
    """List all stored components in the registry."""
    components = await db.get_all_components(limit=limit)
    types = await db.get_component_types()
    return {"components": components, "count": len(components), "types": types}


@router.get("/components/types")
async def list_component_types():
    """Get all distinct component types in the registry."""
    types = await db.get_component_types()
    return {"types": types, "count": len(types)}


@router.get("/components/search")
async def search_components(query: str = "", type: str = "", limit: int = 100):
    """Search components by text, optionally filtered by type."""
    component_type = type if type else None
    results = await db.search_components(query, component_type=component_type, limit=limit)
    return {"results": results, "count": len(results)}


@router.get("/page-analysis")
async def get_page_analysis(url: str = ""):
    """Get analysis data for a page."""
    if not url:
        return {"error": "Missing url parameter"}
    results = await db.get_page_analysis(url)
    return {"url": url, "analysis": results}


@router.get("/scroll-targets")
async def get_scroll_targets():
    """Get all scrollable sections across all pages."""
    results = await db.get_all_scroll_targets()
    return {"scroll_targets": results, "count": len(results)}


@router.delete("/pages")
async def clear_pages():
    """Delete all scraped pages."""
    count = await db.delete_all_pages()
    return {"deleted": count, "message": f"Deleted {count} pages"}


@router.delete("/components")
async def clear_components():
    """Delete all stored components."""
    count = await db.delete_all_components()
    return {"deleted": count, "message": f"Deleted {count} components"}


@router.delete("/page-analysis")
async def clear_page_analysis():
    """Delete all page analysis data."""
    count = await db.delete_all_page_analysis()
    return {"deleted": count, "message": f"Deleted {count} page analysis records"}


@router.delete("/all")
async def clear_all():
    """Delete all pages, components, and analysis (full reset)."""
    pages = await db.delete_all_pages()
    components = await db.delete_all_components()
    analysis = await db.delete_all_page_analysis()
    return {
        "pages_deleted": pages,
        "components_deleted": components,
        "analysis_deleted": analysis,
        "message": "All data cleared",
    }
