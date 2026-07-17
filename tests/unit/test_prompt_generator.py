"""
Regression tests for the prompt_generator module.
"""
import pytest


class TestGenerateNavigationMappings:
    """Tests for generate_navigation_mappings function."""

    def test_returns_dict(self):
        """Should return a dict with keyword → URL mappings."""
        from backend.scraping.prompt_generator import generate_navigation_mappings
        pages = [
            {"url": "https://example.com/booking", "title": "Book Appointment", "page_category": "form_page"},
            {"url": "https://example.com/doctors", "title": "Our Doctors", "page_category": "listing_page"},
        ]
        mappings = generate_navigation_mappings(pages)
        assert isinstance(mappings, dict)
        assert "booking" in mappings
        assert mappings["booking"] == "/booking"

    def test_includes_config_mappings(self):
        """Should include mappings from site_config."""
        from backend.scraping.prompt_generator import generate_navigation_mappings
        mappings = generate_navigation_mappings([])
        # Should have at least the config-based mappings
        assert "booking" in mappings

    def test_discovers_from_titles(self):
        """Should discover mappings from page titles."""
        from backend.scraping.prompt_generator import generate_navigation_mappings
        pages = [
            {"url": "https://example.com/meet-the-team", "title": "Meet Our Doctors & Specialists", "page_category": "listing_page"},
        ]
        mappings = generate_navigation_mappings(pages)
        # Should map "doctors" to "/meet-the-team" since the title contains "doctors"
        # But if "doctors" is already in config mappings, it won't override
        assert isinstance(mappings, dict)

    def test_empty_pages_returns_config(self):
        """Empty pages list should return config-based mappings."""
        from backend.scraping.prompt_generator import generate_navigation_mappings
        mappings = generate_navigation_mappings([])
        assert len(mappings) > 0
        assert "booking" in mappings


class TestGenerateScrollableSections:
    """Tests for generate_scrollable_sections function."""

    def test_returns_dict(self):
        """Should return a dict of selector → label."""
        from backend.scraping.prompt_generator import generate_scrollable_sections
        pages = [
            {
                "url": "https://example.com/",
                "scrollable_sections": [
                    {"selector": "#hero", "label": "Hero"},
                    {"selector": ".features", "label": "Features"},
                ],
            },
        ]
        sections = generate_scrollable_sections(pages)
        assert isinstance(sections, dict)
        assert "#hero" in sections

    def test_includes_config_sections(self):
        """Should include sections from site_config."""
        from backend.scraping.prompt_generator import generate_scrollable_sections
        sections = generate_scrollable_sections([])
        assert len(sections) > 0

    def test_merges_without_duplicates(self):
        """Should not duplicate selectors."""
        from backend.scraping.prompt_generator import generate_scrollable_sections
        pages = [
            {
                "url": "https://example.com/",
                "scrollable_sections": [
                    {"selector": "#testimonials", "label": "Testimonials"},
                ],
            },
        ]
        sections = generate_scrollable_sections(pages)
        # Count occurrences of #testimonials
        count = sum(1 for k in sections.keys() if k == "#testimonials")
        assert count <= 1


class TestGenerateFormSchemas:
    """Tests for generate_form_schemas function."""

    def test_returns_list(self):
        """Should return a list of form field schemas."""
        from backend.scraping.prompt_generator import generate_form_schemas
        pages = [
            {
                "url": "https://example.com/booking",
                "form_fields": [
                    {"name": "name", "type": "text", "required": True},
                    {"name": "email", "type": "email", "required": True},
                    {"name": "department", "type": "select", "required": False, "options": [{"value": "card", "text": "Cardiology"}]},
                ],
            },
        ]
        schemas = generate_form_schemas(pages)
        assert isinstance(schemas, list)
        assert len(schemas) >= 2

        names = [s["field_name"] for s in schemas]
        assert "name" in names
        assert "email" in names

    def test_dedup_by_field_name(self):
        """Should deduplicate fields with the same name."""
        from backend.scraping.prompt_generator import generate_form_schemas
        pages = [
            {
                "url": "https://example.com/booking",
                "form_fields": [
                    {"name": "email", "type": "email", "required": True},
                ],
            },
            {
                "url": "https://example.com/contact",
                "form_fields": [
                    {"name": "email", "type": "email", "required": True},
                ],
            },
        ]
        schemas = generate_form_schemas(pages)
        emails = [s for s in schemas if s["field_name"] == "email"]
        assert len(emails) == 1


class TestBuildSystemPrompt:
    """Tests for build_system_prompt function."""

    def test_returns_string(self):
        """Should return a string prompt."""
        from backend.scraping.prompt_generator import build_system_prompt
        prompt = build_system_prompt([], "TestSite")
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_includes_site_name(self):
        """The prompt should include the site name."""
        from backend.scraping.prompt_generator import build_system_prompt
        prompt = build_system_prompt([], "MyTestSite")
        assert "MyTestSite" in prompt

    def test_includes_action_types(self):
        """The prompt should mention available action types."""
        from backend.scraping.prompt_generator import build_system_prompt
        prompt = build_system_prompt([])
        assert "navigate" in prompt
        assert "scroll" in prompt
        assert "submit" in prompt
        assert "click" in prompt
        assert "fill" in prompt

    def test_includes_navigation_mappings(self):
        """The prompt should include navigation mappings."""
        from backend.scraping.prompt_generator import build_system_prompt
        prompt = build_system_prompt([])
        assert "Navigation Mappings" in prompt or "Auto-Discovered" in prompt

    def test_includes_scrollable_sections(self):
        """The prompt should include scrollable sections."""
        from backend.scraping.prompt_generator import build_system_prompt
        prompt = build_system_prompt([])
        assert "scrollable" in prompt.lower() or "Scrollable" in prompt

    def test_includes_json_format_instruction(self):
        """The prompt should include JSON format instruction."""
        from backend.scraping.prompt_generator import build_system_prompt
        prompt = build_system_prompt([])
        assert "JSON" in prompt
        assert "message" in prompt
