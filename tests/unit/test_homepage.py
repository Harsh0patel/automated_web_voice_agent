"""
Unit tests for the homepage REST routes.
"""


class TestHomepage:
    """Tests for the homepage endpoint."""

    def test_homepage_returns_message(self, client):
        """GET / should return the homepage message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "this is backend homepage"

    def test_homepage_has_correct_structure(self, client):
        """The homepage response should have the expected structure."""
        response = client.get("/")
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 1


class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_returns_healthy(self, client):
        """GET /health should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_has_version(self, client):
        """The health response should include api_version."""
        response = client.get("/health")
        data = response.json()
        assert "api_version" in data
        assert data["api_version"] == "1.0.0"

    def test_health_has_status_running(self, client):
        """The health response should indicate running status."""
        response = client.get("/health")
        data = response.json()
        assert data["api_status"] == "running"

    def test_health_has_all_expected_fields(self, client):
        """The health response should have exactly the expected fields."""
        response = client.get("/health")
        data = response.json()
        expected_keys = {"status", "api_version", "api_status"}
        assert set(data.keys()) == expected_keys


class TestNotFound:
    """Tests for 404 handling."""

    def test_unknown_route_returns_404(self, client):
        """An unknown route should return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
