"""Unit tests for the website scraper module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestScrapeUrl:
    """Tests for scrape_url function."""

    @pytest.mark.asyncio
    async def test_scrape_basic_html(self):
        """Should extract title and content from basic HTML."""
        from backend.scraping.fetcher import scrape_url

        html = """<html><head><title>Test Page</title></head>
        <body><main><h1>Heading</h1><p>This is a paragraph.</p></main></body></html>"""

        mock_response = MagicMock()
        mock_response.text = html
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await scrape_url("https://example.com")

        assert result["url"] == "https://example.com"
        assert result["title"] == "Test Page"
        assert "Heading" in result["content"]
        assert "This is a paragraph." in result["content"]

    @pytest.mark.asyncio
    async def test_scrape_removes_script_tags(self):
        """JavaScript should be removed from the extracted content."""
        from backend.scraping.fetcher import scrape_url

        html = """<html><body><main>
        <p>Visible text</p>
        <script>alert('hidden')</script>
        <style>.hidden{color:red;}</style>
        </main></body></html>"""

        mock_response = MagicMock()
        mock_response.text = html
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await scrape_url("https://example.com")

        assert "Visible text" in result["content"]
        assert "alert" not in result["content"]
        assert ".hidden" not in result["content"]

    @pytest.mark.asyncio
    async def test_scrape_extracts_links(self):
        """Anchor tags should be extracted as markdown links."""
        from backend.scraping.fetcher import scrape_url

        html = """<html><body><main>
        <p>Visit <a href="https://example.com/page">this page</a> for more.</p>
        </main></body></html>"""

        mock_response = MagicMock()
        mock_response.text = html
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await scrape_url("https://example.com")

        assert "[this page](https://example.com/page)" in result["content"]

    @pytest.mark.asyncio
    async def test_scrape_without_title(self):
        """Should handle pages without a title tag."""
        from backend.scraping.fetcher import scrape_url

        html = "<html><body><main><p>No title here</p></main></body></html>"

        mock_response = MagicMock()
        mock_response.text = html
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await scrape_url("https://example.com")

        assert result["title"] == ""

    @pytest.mark.asyncio
    async def test_invalid_url_rejected(self):
        """Invalid URLs should raise ValueError."""
        from backend.scraping.fetcher import scrape_url

        with pytest.raises(ValueError, match="Invalid URL"):
            await scrape_url("not-a-url")

    @pytest.mark.asyncio
    async def test_invalid_url_no_scheme(self):
        """URLs without scheme should be rejected."""
        from backend.scraping.fetcher import scrape_url

        with pytest.raises(ValueError, match="Invalid URL"):
            await scrape_url("example.com/path")

    @pytest.mark.asyncio
    async def test_http_error_propagates(self):
        """HTTP errors should propagate as exceptions."""
        from backend.scraping.fetcher import scrape_url

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(
            side_effect=Exception("HTTP 404")
        )

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(Exception, match="HTTP 404"):
                await scrape_url("https://example.com/404")

    @pytest.mark.asyncio
    async def test_scrape_uses_correct_headers(self):
        """Should send proper browser-like headers."""
        from backend.scraping.fetcher import scrape_url

        html = "<html><body><main><p>Test</p></main></body></html>"

        mock_response = MagicMock()
        mock_response.text = html
        mock_response.status_code = 200
        # raise_for_status is not needed for header check, but must not fail
        mock_response.raise_for_status = MagicMock()

        # Use the same pattern as the other working tests
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await scrape_url("https://example.com")

        # Check that headers include User-Agent
        call_kwargs = mock_client.__aenter__.return_value.get.await_args.kwargs
        assert "User-Agent" in call_kwargs["headers"]
        assert "Chrome" in call_kwargs["headers"]["User-Agent"]

    @pytest.mark.asyncio
    async def test_scrape_returns_metadata(self):
        """Should return metadata including status code."""
        from backend.scraping.fetcher import scrape_url

        html = "<html><body><main><p>Content</p></main></body></html>"

        mock_response = MagicMock()
        mock_response.text = html
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await scrape_url("https://example.com")

        assert "metadata" in result
        assert result["metadata"]["status_code"] == 200
        assert result["metadata"]["content_length"] > 0
