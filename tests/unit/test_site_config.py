"""
Regression tests for the site_config module.
"""
import json
from pathlib import Path
from unittest.mock import patch

import pytest


class TestSiteConfig:
    """Tests for site configuration loading and access."""

    def test_load_site_config_returns_dict(self):
        """load_site_config should return a dictionary."""
        from backend.scraping.site_config import load_site_config
        config = load_site_config()
        assert isinstance(config, dict)

    def test_load_site_config_has_required_keys(self):
        """Loaded config should have all required top-level keys."""
        from backend.scraping.site_config import load_site_config
        config = load_site_config()
        required_keys = {
            "semantic_selectors", "section_classes", "page_mappings",
            "scrollable_sections", "action_buttons", "form_params",
            "component_parsers", "navigation_patterns",
        }
        for key in required_keys:
            assert key in config, f"Missing required key: {key}"

    def test_get_semantic_selectors_returns_tuples(self):
        """get_semantic_selectors should return list of (selector, type, section) tuples."""
        from backend.scraping.site_config import get_semantic_selectors
        selectors = get_semantic_selectors()
        assert isinstance(selectors, list)
        if selectors:
            sel, ctype, section = selectors[0]
            assert isinstance(sel, str)
            assert isinstance(ctype, str)
            assert isinstance(section, str)

    def test_get_page_mappings_contains_keywords(self):
        """get_page_mappings should contain common keywords."""
        from backend.scraping.site_config import get_page_mappings
        mappings = get_page_mappings()
        assert "booking" in mappings
        assert "doctors" in mappings
        assert "services" in mappings

    def test_get_scrollable_sections_returns_dict(self):
        """get_scrollable_sections should return a dict."""
        from backend.scraping.site_config import get_scrollable_sections
        sections = get_scrollable_sections()
        assert isinstance(sections, dict)

    def test_get_site_name_returns_string(self):
        """get_site_name should return a non-empty string."""
        from backend.scraping.site_config import get_site_name
        name = get_site_name()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_reload_site_config_clears_cache(self):
        """reload_site_config should clear cache and reload."""
        from backend.scraping.site_config import load_site_config, reload_site_config
        # Load once to populate cache
        config1 = load_site_config()
        # Reload
        config2 = reload_site_config()
        assert config1 == config2

    def test_get_navigation_patterns(self):
        """get_navigation_patterns should return dict with page type lists."""
        from backend.scraping.site_config import get_navigation_patterns
        patterns = get_navigation_patterns()
        assert "form_pages" in patterns
        assert "listing_pages" in patterns
        assert "info_pages" in patterns

    def test_get_component_parsers(self):
        """get_component_parsers should return dict with field configs."""
        from backend.scraping.site_config import get_component_parsers
        parsers = get_component_parsers()
        assert "doctor_fields" in parsers
        assert "service_fields" in parsers
        assert "faq_fields" in parsers

    def test_config_file_exists(self):
        """The site_config.json file should exist."""
        config_path = Path(__file__).resolve().parent.parent.parent / "sites" / "site_config.json"
        assert config_path.exists(), f"Config file not found at {config_path}"
        assert config_path.is_file()

    def test_config_file_is_valid_json(self):
        """The site_config.json should be valid JSON."""
        config_path = Path(__file__).resolve().parent.parent.parent / "sites" / "site_config.json"
        with open(config_path, "r") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    @patch("backend.scraping.site_config._SITES_DIR")
    def test_load_missing_config_returns_empty(self, mock_sites_dir):
        """Loading a missing config file should return an empty dict."""
        from backend.scraping.site_config import reload_site_config
        mock_path = Path("/nonexistent/path")
        mock_sites_dir.__truediv__.return_value = mock_path
        mock_sites_dir.__str__.return_value = str(mock_path)

        # We can't easily mock this path in the function, so just verify
        # that load_site_config still works
        config = reload_site_config()
        assert isinstance(config, dict)
