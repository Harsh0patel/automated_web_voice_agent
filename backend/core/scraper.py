"""
Website scraper — fetches a URL, extracts clean text content.
"""
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from backend.core.logger import get_logger

logger = get_logger(__name__)


async def scrape_url(url: str) -> dict:
    """
    Fetch a URL and extract its clean text content.

    Args:
        url: The full HTTP/HTTPS URL to scrape.

    Returns:
        Dict with keys: url, title, content (markdown-style text).
    """
    # Validate URL
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        logger.warning("Invalid URL rejected: %s", url)
        raise ValueError(f"Invalid URL: {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }

    logger.info("Fetching %s ...", url)

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        html = response.text

    logger.info("Fetched %s — status=%d, size=%d bytes", url, response.status_code, len(html))

    # Parse HTML
    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, nav, footer elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()

    # Extract title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # Extract main content (prefer <main>, <article>, or body)
    main = soup.find("main") or soup.find("article") or soup.find("body")
    if main is None:
        main = soup

    # Get text with some structure preservation
    lines = []
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
    logger.info("Extracted %d chars of content from %s", len(content), url)

    return {
        "url": url,
        "title": title,
        "content": content or soup.get_text(separator="\n", strip=True),
        "metadata": {
            "status_code": response.status_code,
            "content_length": len(html),
        },
    }
