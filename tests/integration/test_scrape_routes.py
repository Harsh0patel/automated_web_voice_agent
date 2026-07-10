"""Integration tests for the scrape REST endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestScrapeEndpoint:
    """Tests for POST /scrape endpoint."""

    def test_scrape_invalid_url(self, client):
        """Invalid URL should return error response."""
        response = client.post("/scrape?url=invalid")
        data = response.json()
        assert response.status_code == 200
        assert "error" in data
        assert "Invalid URL" in data["error"]

    def test_scrape_empty_url(self, client):
        """Empty URL should return error response."""
        response = client.post("/scrape?url=")
        data = response.json()
        assert "error" in data

    def test_scrape_missing_url_param(self, client):
        """Missing url parameter should return 422."""
        response = client.post("/scrape")
        assert response.status_code == 422

    @patch("backend.routes.scrape.scrape_url")
    @patch("backend.routes.scrape.db.store_page")
    def test_scrape_success(self, mock_store_page, mock_scrape_url, client):
        """Successful scrape should store and return the page."""
        mock_scrape_url.return_value = {
            "url": "https://example.com",
            "title": "Example Page",
            "content": "This is the page content. " * 50,
            "metadata": {"status_code": 200, "content_length": 500},
        }
        mock_store_page.return_value = "doc123"

        response = client.post("/scrape?url=https://example.com")
        data = response.json()

        assert response.status_code == 200
        assert data["id"] == "doc123"
        assert data["url"] == "https://example.com"
        assert data["title"] == "Example Page"
        assert "content_preview" in data
        mock_scrape_url.assert_called_once_with("https://example.com")
        mock_store_page.assert_called_once()

    @patch("backend.routes.scrape.scrape_url")
    def test_scrape_error_propagates(self, mock_scrape_url, app):
        """Errors during scraping should return 500."""
        from fastapi.testclient import TestClient
        client = TestClient(app, raise_server_exceptions=False)
        mock_scrape_url.side_effect = Exception("Scraping failed")

        response = client.post("/scrape?url=https://example.com")
        assert response.status_code == 500


class TestListPagesEndpoint:
    """Tests for GET /pages endpoint."""

    @patch("backend.routes.scrape.db.get_all_pages")
    def test_list_empty(self, mock_get_all, client):
        """GET /pages should return empty list when no pages."""
        mock_get_all.return_value = []

        response = client.get("/pages")
        data = response.json()

        assert response.status_code == 200
        assert data["pages"] == []
        assert data["count"] == 0

    @patch("backend.routes.scrape.db.get_all_pages")
    def test_list_with_pages(self, mock_get_all, client):
        """GET /pages should return stored pages."""
        mock_get_all.return_value = [
            {"id": "1", "url": "https://a.com", "title": "Page A", "content_preview": "..."},
            {"id": "2", "url": "https://b.com", "title": "Page B", "content_preview": "..."},
        ]

        response = client.get("/pages")
        data = response.json()

        assert response.status_code == 200
        assert len(data["pages"]) == 2
        assert data["count"] == 2
        assert data["pages"][0]["title"] == "Page A"

    @patch("backend.routes.scrape.db.get_all_pages")
    def test_list_db_error(self, mock_get_all, app):
        """Database errors should return 500."""
        from fastapi.testclient import TestClient
        client = TestClient(app, raise_server_exceptions=False)
        mock_get_all.side_effect = Exception("DB connection failed")

        response = client.get("/pages")
        assert response.status_code == 500


class TestDeletePagesEndpoint:
    """Tests for DELETE /pages endpoint."""

    @patch("backend.routes.scrape.db.delete_all_pages")
    def test_delete_success(self, mock_delete, client):
        """DELETE /pages should clear all pages."""
        mock_delete.return_value = 3

        response = client.delete("/pages")
        data = response.json()

        assert response.status_code == 200
        assert data["deleted"] == 3
        assert "Deleted 3 pages" in data["message"]

    @patch("backend.routes.scrape.db.delete_all_pages")
    def test_delete_empty(self, mock_delete, client):
        """DELETE /pages with no pages should return 0."""
        mock_delete.return_value = 0

        response = client.delete("/pages")
        data = response.json()

        assert response.status_code == 200
        assert data["deleted"] == 0
