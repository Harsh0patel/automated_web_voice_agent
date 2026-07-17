"""
Simple HTTP-based website scraper.

Fetches a URL using httpx, extracts clean text content from the HTML,
and returns structured results. Unlike the Playwright-based browser.py,
this does not execute JavaScript.
"""
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from backend.app.logger import get_logger

logger = get_logger(__name__)


async def scrape_url(url: str) -> dict:
    """Fetch a URL and extract its clean text content.

    Args:
        url: The full HTTP/HTTPS URL to scrape.

    Returns:
        Dict with keys: url, title, content (markdown-style text), raw_html, metadata.
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, "html.parser")

    # Remove only script/style/noscript - keep nav, footer, header for structure
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    main = soup.find("main") or soup.find("article") or soup.find("body")
    if main is None:
        main = soup

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
        elif element.name == "div" or element.name == "span":
            text = element.get_text(strip=True)
            if text and len(text) > 20:
                lines.append(f"{text}\n")
        elif element.name in ("table", "tr"):
            text = element.get_text(strip=True)
            if text and len(text) > 10:
                lines.append(f"{text}\n")

    content = "".join(lines).strip()
    if not content:
        content = soup.get_text(separator="\n", strip=True)

    return {
        "url": url,
        "title": title,
        "content": content or soup.get_text(separator="\n", strip=True),
        "raw_html": html,
        "metadata": {
            "status_code": response.status_code,
            "content_length": len(html),
        },
    }
