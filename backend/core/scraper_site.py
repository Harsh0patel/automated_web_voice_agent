"""
Playwright-based website scraper for JavaScript-rendered pages (e.g. React SPAs).

Handles the full pipeline:
  1. Visit the base URL with a real headless browser
  2. Discover all internal links from the rendered page
  3. Render each discovered page fully (waits for JS to execute)
  4. Extract clean text content from the rendered HTML
  5. Return all results for batch storage
"""
from urllib.parse import urljoin, urlparse

import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from backend.core.logger import get_logger

logger = get_logger(__name__)

_PLAYWRIGHT = None
_BROWSER = None


async def _start() -> None:
    """Start Playwright and launch the shared browser."""
    global _PLAYWRIGHT, _BROWSER
    if _BROWSER is None:
        _PLAYWRIGHT = await async_playwright().start()
        _BROWSER = await _PLAYWRIGHT.chromium.launch(headless=True)
        logger.info("Playwright browser launched")


async def _stop() -> None:
    """Close the shared browser and stop Playwright."""
    global _PLAYWRIGHT, _BROWSER
    if _BROWSER:
        await _BROWSER.close()
        _BROWSER = None
    if _PLAYWRIGHT:
        await _PLAYWRIGHT.stop()
        _PLAYWRIGHT = None
    logger.info("Playwright browser closed")


def _extract_from_html(html: str, url: str) -> dict:
    """
    Extract clean text content from rendered HTML using BeautifulSoup.

    Uses the same extraction logic as the httpx-based scraper
    so the resulting format is identical.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements (navbar, footer, sidebar, etc.)
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()

    # Title
    title = soup.title.string.strip() if soup.title and soup.title.string else url

    # Prefer <main>, then <article>, then <body>
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

    content = "".join(lines).strip()
    if not content:
        content = soup.get_text(separator="\n", strip=True)

    return {"url": url, "title": title, "content": content, "raw_html": html}


async def _discover_links(page, base_url: str) -> list[str]:
    """Extract all internal link URLs from the rendered page."""
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    # Get all anchor hrefs from the rendered DOM (JS-executed)
    hrefs = await page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a[href]'))
            .map(a => a.href)
            .filter(h => h && !h.startsWith('javascript:') && !h.startsWith('mailto:'));
    }""")

    discovered: set[str] = set()
    for href in hrefs:
        parsed = urlparse(href)
        # Only same-origin or protocol-relative links
        if parsed.netloc and parsed.netloc != base_domain:
            continue
        if parsed.scheme and parsed.scheme not in ("http", "https"):
            continue
        full = urljoin(base_url, href)
        full = full.split("#")[0]  # remove fragments
        if full.startswith(("http://", "https://")):
            discovered.add(full)

    result = sorted(discovered)
    logger.info("Discovered %d internal links from %s", len(result), base_url)
    return result


async def render_page(url: str, timeout: int = 30) -> dict:
    """
    Render a single URL with a headless browser and extract content.

    Args:
        url: The full URL to render and scrape.
        timeout: Page load timeout in seconds.

    Returns:
        Dict with keys: url, title, content.
    """
    await _start()
    context = await _BROWSER.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    )
    page_page = await context.new_page()

    try:
        logger.info("Rendering %s with Playwright ...", url)
        await page_page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
        # Extra wait for React deferred rendering / lazy components
        await page_page.wait_for_timeout(2500)

        html = await page_page.content()
        result = _extract_from_html(html, url)
        logger.info(
            "Rendered %s — title=%.60s, content=%d chars",
            url, result["title"], len(result["content"]),
        )
        return result
    except Exception as exc:
        logger.error("Failed to render %s: %s", url, exc)
        return {"url": url, "title": url, "content": f"[Render failed: {exc}]"}
    finally:
        await page_page.close()
        await context.close()


async def scrape_site(base_url: str, max_concurrency: int = 3) -> dict:
    """
    Scrape an entire site in one shot.

    Pipeline:
      1. Render the base URL to discover all internal links
      2. Render every discovered page (up to max_concurrency in parallel)
      3. Return results and any errors

    Args:
        base_url: The starting URL (e.g. http://localhost:5174).
        max_concurrency: Max parallel page renders.

    Returns:
        Dict with:
          - pages: list of {url, title, content}
          - total: number of successfully scraped pages
          - errors: list of error messages
          - base_url: the original base URL
    """
    await _start()

    # ── Step 1: Render base page & discover links ──
    logger.info("Crawl phase — rendering %s to discover pages...", base_url)
    context = await _BROWSER.new_context()
    page_crawl = await context.new_page()

    try:
        await page_crawl.goto(base_url, wait_until="networkidle", timeout=30000)
        await page_crawl.wait_for_timeout(2500)
        all_urls = await _discover_links(page_crawl, base_url)

        # Always include the base URL itself
        base_clean = base_url.rstrip("/")
        if base_clean not in all_urls:
            all_urls.insert(0, base_clean)

        logger.info("Will scrape %d pages from site %s", len(all_urls), base_url)
    except Exception as exc:
        logger.error("Crawl of %s failed: %s", base_url, exc)
        return {"pages": [], "total": 0, "errors": [str(exc)], "base_url": base_url}
    finally:
        await page_crawl.close()
        await context.close()

    # ── Step 2: Scrape all discovered pages in parallel ──
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _scrape_one(u: str) -> dict:
        async with semaphore:
            return await render_page(u)

    tasks = [_scrape_one(u) for u in all_urls]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    pages: list[dict] = []
    errors: list[str] = []
    for r in raw_results:
        if isinstance(r, Exception):
            errors.append(str(r))
        elif isinstance(r, dict):
            pages.append(r)

    logger.info("Site scrape complete: %d pages, %d errors", len(pages), len(errors))

    # Cleanup the browser
    await _stop()

    return {
        "pages": pages,
        "total": len(pages),
        "errors": errors,
        "base_url": base_url,
    }
