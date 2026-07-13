"""
Playwright-based website scraper for JavaScript-rendered pages (e.g. React SPAs).

Handles the full pipeline:
  1. Visit the base URL with a real headless browser
  2. Discover all internal links from the rendered page
  3. Render each discovered page fully (waits for JS to execute)
  4. Extract clean text content from the rendered HTML
  5. Return all results for batch storage

Uses Playwright's **sync** API running in a **single dedicated thread**
(ThreadPoolExecutor with max_workers=1). This hybrid approach avoids:

  - Windows NotImplementedError from async_playwright().start() (event loop
    subprocess incompatibility)
  - greenlet.error: Cannot switch to a different thread (caused by calling
    sync_playwright from multiple threads concurrently)

Because the executor has only 1 worker, all Playwright operations are
serialised on that thread, keeping greenlets happy. The asyncio layer
provides the outer orchestration + concurrency via Semaphore (though
actual page rendering is sequential due to the single-thread executor).
"""
from urllib.parse import urljoin, urlparse

import asyncio
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from backend.core.logger import get_logger

logger = get_logger(__name__)

# ── Globals ──
_PLAYWRIGHT = None
_BROWSER = None
_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pw")


# ══════════════════════════════════════════════════════════
#  Low-level sync functions (run inside the executor thread)
# ══════════════════════════════════════════════════════════

def _start_sync() -> None:
    """Start Playwright and launch the shared browser (runs in executor thread)."""
    global _PLAYWRIGHT, _BROWSER
    if _BROWSER is not None:
        return
    _PLAYWRIGHT = sync_playwright().start()
    _BROWSER = _PLAYWRIGHT.chromium.launch(headless=True)
    logger.info("Playwright browser launched (sync thread)")


def _stop_sync() -> None:
    """Close the shared browser and stop Playwright (runs in executor thread)."""
    global _PLAYWRIGHT, _BROWSER
    if _BROWSER:
        _BROWSER.close()
        _BROWSER = None
    if _PLAYWRIGHT:
        _PLAYWRIGHT.stop()
        _PLAYWRIGHT = None
    logger.info("Playwright browser closed (sync thread)")


def _render_page_sync(url: str, timeout: int = 30) -> dict:
    """Render a single page with Playwright (runs in executor thread)."""
    try:
        _start_sync()
        browser = _BROWSER
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
    except Exception as exc:
        logger.error("Failed to initialise browser for %s: %s", url, exc)
        return {"url": url, "title": url, "content": f"[Render failed: {exc}]"}

    try:
        logger.info("Rendering %s with Playwright ...", url)
        # domcontentloaded avoids indefinite hangs on Cloudflare / long-polling
        page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
        page.wait_for_timeout(2000)  # let JS frameworks (React) mount

        html = page.content()
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
        page.close()
        context.close()


def _discover_links_sync(base_url: str) -> list[str]:
    """Render the base page and extract all internal links (runs in executor thread)."""
    _start_sync()
    context = _BROWSER.new_context()
    page = context.new_page()

    try:
        page.goto(base_url, wait_until="domcontentloaded", timeout=30000)

        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc

        hrefs = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]'))
                .map(a => a.href)
                .filter(h => h && !h.startsWith('javascript:') && !h.startsWith('mailto:'));
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
    """Extract clean text content from rendered HTML using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else url

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


# ══════════════════════════════════════════════════════════
#  Public async API (async wrappers over single-thread executor)
# ══════════════════════════════════════════════════════════

async def _start() -> None:
    """Start Playwright (async wrapper)."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(_EXECUTOR, _start_sync)


async def _stop() -> None:
    """Stop Playwright (async wrapper)."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(_EXECUTOR, _stop_sync)


async def render_page(url: str, timeout: int = 30) -> dict:
    """Render a single URL with Playwright (async wrapper)."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_EXECUTOR, _render_page_sync, url, timeout)


async def _discover_links(base_url: str) -> list[str]:
    """Discover all internal links from the base page (async wrapper)."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_EXECUTOR, _discover_links_sync, base_url)


# ══════════════════════════════════════════════════════════
#  Site scraper (full pipeline)
# ══════════════════════════════════════════════════════════

async def scrape_site(
    base_url: str,
    max_pages: int = 25,
    page_timeout: int = 20,
) -> dict:
    """
    Scrape an entire site in one shot.

    Pipeline:
      1. Render the base URL to discover all internal links
      2. Render each discovered page sequentially
      3. Return results and any errors

    Pages are rendered one at a time via a single-thread sync executor
    (avoids Windows NotImplementedError and greenlet thread-switching errors).
    """
    await _start()

    # ── Step 1: Crawl (discover links) ──
    logger.info("Crawl phase — rendering %s to discover pages...", base_url)

    try:
        all_urls = await _discover_links(base_url)
        base_clean = base_url.rstrip("/")
        if base_clean not in all_urls:
            all_urls.insert(0, base_clean)
        logger.info(
            "Discovered %d internal links from %s (capped at max_pages=%d)",
            len(all_urls), base_url, max_pages,
        )
    except Exception as exc:
        logger.error("Crawl of %s failed: %s", base_url, exc)
        return {"pages": [], "total": 0, "errors": [str(exc)], "base_url": base_url}

    # ── Step 2: Limit to max_pages ──
    urls_to_scrape = all_urls[:max_pages]
    logger.info(
        "Scraping %d / %d pages from %s (timeout=%ds)",
        len(urls_to_scrape), len(all_urls), base_url, page_timeout,
    )

    # ── Step 3: Scrape each page (sequentially via single-thread executor) ──
    pages: list[dict] = []
    errors: list[str] = []

    for i, u in enumerate(urls_to_scrape):
        result = await render_page(u, timeout=page_timeout)
        if result.get("content", "").startswith("[Render failed"):
            errors.append(f"{u}: {result['content']}")
        else:
            pages.append(result)
        logger.info(
            "Progress: %d/%d pages scraped from %s",
            len(pages) + len(errors), len(urls_to_scrape), base_url,
        )

    logger.info(
        "Site scrape complete: %d pages, %d errors (from %d discovered)",
        len(pages), len(errors), len(all_urls),
    )

    return {
        "pages": pages,
        "total": len(pages),
        "errors": errors,
        "base_url": base_url,
    }
