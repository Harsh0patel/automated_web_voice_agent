"""
Integration tests for REST API routes using FastAPI TestClient.
"""


class TestHomepageIntegration:
    """Integration tests for the homepage route."""

    def test_homepage_full_response(self, client):
        """Full integration: GET / should work end-to-end."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_homepage_via_different_methods(self, client):
        """POST / should return 405 Method Not Allowed."""
        response = client.post("/")
        assert response.status_code == 405

        response = client.put("/")
        assert response.status_code == 405

        response = client.delete("/")
        assert response.status_code == 405


class TestHealthCheckIntegration:
    """Integration tests for the health check route."""

    def test_health_endpoint(self, client):
        """GET /health should return valid JSON with expected fields."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        # Health endpoint should always return these
        assert data["status"] in ("healthy", "unhealthy")
        assert isinstance(data["api_version"], str)
        assert isinstance(data["api_status"], str)

    def test_health_content_type(self, client):
        """Health endpoint should return JSON."""
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]


class TestWebSocketEndpointRest:
    """Tests verifying the WebSocket endpoint is reachable via REST doesn't work."""

    def test_ws_endpoint_returns_404_via_get(self, client):
        """GET /ws should return 404 since it's a WebSocket-only route."""
        # WebSocket routes return 404 for regular HTTP requests
        response = client.get("/ws")
        assert response.status_code in (404, 405)
