"""
Playwright-based website scraper for JavaScript-rendered pages (e.g. React SPAs).

Uses Playwright's sync API running in a single dedicated thread (ThreadPoolExecutor
with max_workers=1) to avoid Windows async subprocess incompatibilities.

Key improvements over the original scraper_site.py:
  - No maximum page cap (max_pages removed, uses a default high limit if needed)
  - No truncation of discovered links for navigation patterns
  - Navigation content (nav, header, footer) is preserved for richer context
  - Longer JS wait time for better React rendering
"""
from urllib.parse import urljoin, urlparse

import asyncio
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from backend.app.logger import get_logger
from backend.scraping.parser import categorize_page, extract_scrollable_sections, analyze_form_fields

logger = get_logger(__name__)

_PLAYWRIGHT = None
_BROWSER = None
_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pw")


def _start_sync() -> None:
    """Start Playwright and launch the shared browser (runs in executor thread)."""
    global _PLAYWRIGHT, _BROWSER
    if _BROWSER is not None:
        return
    _PLAYWRIGHT = sync_playwright().start()
    _BROWSER = _PLAYWRIGHT.chromium.launch(headless=True)
    logger.info("Playwright browser launched (sync thread)")


def _stop_sync() -> None:
    """Close the shared browser and stop Playwright."""
    global _PLAYWRIGHT, _BROWSER
    if _BROWSER:
        _BROWSER.close()
        _BROWSER = None
    if _PLAYWRIGHT:
        _PLAYWRIGHT.stop()
        _PLAYWRIGHT = None


def _render_page_sync(url: str, timeout: int = 30) -> dict:
    """Render a single page with Playwright."""
    try:
        _start_sync()
        context = _BROWSER.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
    except Exception as exc:
        return {"url": url, "title": url, "content": f"[Render failed: {exc}]"}

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
        page.wait_for_timeout(3000)  # Longer wait for React/framework hydration

        html = page.content()
        result = _extract_from_html(html, url)
        return result
    except Exception as exc:
        return {"url": url, "title": url, "content": f"[Render failed: {exc}]"}
    finally:
        page.close()
        context.close()


def _discover_links_sync(base_url: str) -> list[str]:
    """Render the base page and extract ALL internal links."""
    _start_sync()
    context = _BROWSER.new_context()
    page = context.new_page()

    try:
        page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc

        # Find all links AND buttons with href/data attributes
        hrefs = page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a[href], button[data-href], [data-url]'));
            return links.map(el => {
                if (el.tagName === 'A') return el.href;
                if (el.dataset && el.dataset.href) return el.dataset.href;
                if (el.dataset && el.dataset.url) return el.dataset.url;
                return null;
            }).filter(h => h && !h.startsWith('javascript:') && !h.startsWith('mailto:'));
        }""")

        discovered: set[str] = set()
        for href in hrefs:
            parsed = urlparse(href)
            if parsed.netloc and parsed.netloc != base_domain:
                continue
            if parsed.scheme and parsed.scheme not in ("http", "https"):
                continue
            full = urljoin(base_url, href)
            full = full.split("#")[0]
            if full.startswith(("http://", "https://")):
                discovered.add(full)

        result = sorted(discovered)
        logger.info("Discovered %d internal links from %s", len(result), base_url)
        return result
    finally:
        page.close()
        context.close()


def _extract_from_html(html: str, url: str) -> dict:
    """Extract content from rendered HTML. Preserves nav/header/footer for structure."""
    soup = BeautifulSoup(html, "html.parser")

    # Only remove script, style, noscript - keep nav/header/footer for context
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else url

    page_category = categorize_page(soup, url)
    scrollable_sections = extract_scrollable_sections(soup, url)
    form_fields = analyze_form_fields(soup, url)

    main = soup.find("main") or soup.find("article") or soup.find("body") or soup

    lines: list[str] = []
    for element in main.descendants:
        if element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = element.get_text(strip=True)
            if text:
                prefix = "#" * int(element.name[1])
                lines.append(f"\n{prefix} {text}\n")
        elif element.name == "p":
            text = element.get_text(strip=True)
            if text:
                lines.append(f"{text}\n")
        elif element.name in ("li", "td", "th", "blockquote"):
            text = element.get_text(strip=True)
            if text:
                lines.append(f"  - {text}")
        elif element.name == "br":
            lines.append("\n")
        elif element.name == "a":
            href = element.get("href", "")
            text = element.get_text(strip=True)
            if text and href and not href.startswith("#"):
                lines.append(f"[{text}]({href}) ")
        elif element.name in ("div", "span"):
            text = element.get_text(strip=True)
            if text and len(text) > 20:
                lines.append(f"{text}\n")

    content = "".join(lines).strip()
    if not content:
        content = soup.get_text(separator="\n", strip=True)

    return {
        "url": url,
        "title": title,
        "content": content,
        "raw_html": html,
        "page_category": page_category,
        "scrollable_sections": scrollable_sections,
        "form_fields": form_fields,
    }


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

async def _start() -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(_EXECUTOR, _start_sync)


async def _stop() -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(_EXECUTOR, _stop_sync)


async def render_page(url: str, timeout: int = 30) -> dict:
    """Render a single URL with Playwright (async wrapper)."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_EXECUTOR, _render_page_sync, url, timeout)


async def _discover_links(base_url: str) -> list[str]:
    """Discover all internal links from the base page."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_EXECUTOR, _discover_links_sync, base_url)


async def discover_navigation_patterns(base_url: str) -> dict:
    """Discover navigation intent patterns from a site's pages.
    
    Analyzes ALL discovered pages (no limit) to categorize them by purpose.
    """
    await _start()
    try:
        all_urls = await _discover_links(base_url)
        base_clean = base_url.rstrip("/")
        if base_clean not in all_urls:
            all_urls.insert(0, base_clean)
    except Exception as exc:
        return {"form_pages": [], "listing_pages": [], "detail_pages": [], "info_pages": []}

    patterns = {"form_pages": [], "listing_pages": [], "detail_pages": [], "info_pages": []}

    for url in all_urls:  # No limit - discover ALL pages
        try:
            result = await render_page(url, timeout=15)
            if result.get("content", "").startswith("[Render failed"):
                continue
            category = result.get("page_category", "info_page")
            key = f"{category}_pages" if category.endswith("_page") else f"{category}s"
            if key not in patterns:
                key = "info_pages"
            patterns[key].append({
                "url": url,
                "title": result.get("title", ""),
                "scrollable_sections": result.get("scrollable_sections", []),
                "form_fields": result.get("form_fields", []),
            })
        except Exception as exc:
            logger.warning("Failed to categorize %s: %s", url, exc)

    return patterns


async def scrape_site(base_url: str, max_pages: int = 0, page_timeout: int = 20) -> dict:
    """Scrape an entire site in one shot.

    Pipeline:
      1. Render the base URL to discover all internal links
      2. Render each discovered page
      3. Categorize each page (form, listing, detail, info)
      4. Extract scrollable sections and form fields

    Args:
        base_url: The starting URL to scrape.
        max_pages: Maximum pages to scrape. 0 means no limit (scrape all).
        page_timeout: Timeout per page in seconds.

    Returns:
        Dict with pages, total, errors, navigation_patterns, base_url.
    """
    await _start()

    # Step 1: Crawl
    try:
        all_urls = await _discover_links(base_url)
        base_clean = base_url.rstrip("/")
        if base_clean not in all_urls:
            all_urls.insert(0, base_clean)
    except Exception as exc:
        return {"pages": [], "total": 0, "errors": [str(exc)], "base_url": base_url}

    # Step 2: Apply max_pages only if > 0
    urls_to_scrape = all_urls[:max_pages] if max_pages > 0 else all_urls
    logger.info("Scraping %d / %d pages from %s", len(urls_to_scrape), len(all_urls), base_url)

    # Step 3: Scrape each page
    pages = []
    errors = []

    for i, u in enumerate(urls_to_scrape):
        result = await render_page(u, timeout=page_timeout)
        if result.get("content", "").startswith("[Render failed"):
            errors.append(f"{u}: {result['content']}")
        else:
            pages.append(result)

    # Step 4: Build navigation pattern summary
    navigation_patterns = {"form_pages": [], "listing_pages": [], "detail_pages": [], "info_pages": []}
    for page in pages:
        category = page.get("page_category", "info_page")
        key = f"{category}s" if category.endswith("_page") else f"{category}s"
        if key not in navigation_patterns:
            key = "info_pages"
        navigation_patterns[key].append({
            "url": page.get("url", ""),
            "title": page.get("title", ""),
        })

    logger.info("Site scrape complete: %d pages, %d errors (from %d discovered)",
                len(pages), len(errors), len(all_urls))

    return {
        "pages": pages,
        "total": len(pages),
        "errors": errors,
        "base_url": base_url,
        "navigation_patterns": navigation_patterns,
    }
