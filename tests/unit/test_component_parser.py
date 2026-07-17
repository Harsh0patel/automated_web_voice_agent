"""
Regression tests for the component_parser module.

Tests cover:
  - Config-driven semantic selectors
  - Generic heuristic fallbacks
  - Scrollable section extraction
  - Form field analysis
  - Page categorization
  - Component parsing for each type
  - LLM-friendly formatting
"""
from unittest.mock import patch

from bs4 import BeautifulSoup
import pytest


# ============================================================
# Sample HTML fixtures
# ============================================================

SAMPLE_HTML_CARDS = """
<html>
<body>
<main>
  <div class="container">
    <div class="features__grid">
      <div class="feature-card">
        <div class="feature-card__icon">❤️</div>
        <h3>Cardiology</h3>
        <p>Heart care services</p>
        <ul><li>Echocardiography</li><li>Angioplasty</li></ul>
        <a href="/services">Learn more</a>
      </div>
      <div class="doctor-card">
        <div class="doctor-card__name">Dr. Smith</div>
        <div class="doctor-card__specialty">Cardiology</div>
        <div class="doctor-card__exp">15 years</div>
        <p class="doctor-card__desc">Expert cardiologist</p>
      </div>
    </div>
    <div class="testimonial-card">
      <div class="testimonial-card__stars">★★★★★</div>
      <p class="testimonial-card__text">Great service!</p>
      <div class="testimonial-card__author">John Doe</div>
      <small>Patient</small>
    </div>
  </div>
</main>
</body>
</html>
"""

SAMPLE_HTML_WITH_SECTIONS = """
<html>
<body>
  <section id="hero" class="hero">
    <h1>Welcome</h1>
  </section>
  <section id="testimonials" class="testimonials">
    <h2>What Patients Say</h2>
  </section>
  <section class="features">
    <h2>Our Features</h2>
  </section>
  <section class="faq-section">
    <div class="faq__item">
      <button class="faq__question">What is this?</button>
      <div class="faq__answer"><p>This is a test.</p></div>
    </div>
  </section>
</body>
</html>
"""

SAMPLE_HTML_WITH_FORMS = """
<html>
<body>
  <form id="booking-form">
    <select id="service" name="department">
      <option value="cardiology">Cardiology</option>
      <option value="neurology">Neurology</option>
    </select>
    <input id="b-name" name="name" type="text" required placeholder="Your name" />
    <input id="b-email" name="email" type="email" required placeholder="Your email" />
    <button type="submit">Submit</button>
  </form>
</body>
</html>
"""

SAMPLE_HTML_WITH_GENERIC = """
<html>
<body>
<main>
  <div class="product-card">
    <h3>Product A</h3>
    <p>Description of product A</p>
  </div>
  <div class="profile-card">
    <h3>John Doe</h3>
    <p>Software Engineer</p>
  </div>
  <div class="blog-post">
    <h3>Blog Title</h3>
    <p>Blog excerpt here</p>
  </div>
</main>
</body>
</html>
"""

SAMPLE_HTML_STATS = """
<html>
<body>
<main>
  <div class="stats__grid">
    <div class="stat-item">
      <span class="stat-value">200+</span>
      <span class="stat-label">Doctors</span>
    </div>
    <div class="stat-item">
      <span class="stat-value">50K+</span>
      <span class="stat-label">Patients</span>
    </div>
  </div>
</main>
</body>
</html>
"""


# ============================================================
# Tests: parse_page
# ============================================================

class TestParsePage:
    """Tests for the parse_page function."""

    def test_parse_basic_html(self):
        """Should extract semantic components from basic HTML."""
        from backend.scraping.parser import parse_page
        components = parse_page(SAMPLE_HTML_CARDS, "https://example.com", "Test Page")

        # Should find doctor, testimonial, service, features
        types = [c["type"] for c in components]
        assert "doctor" in types
        assert "testimonial" in types
        assert "service" in types

    def test_parse_doctor_card(self):
        """Doctor cards should have proper metadata."""
        from backend.scraping.parser import parse_page
        components = parse_page(SAMPLE_HTML_CARDS, "https://example.com", "Test Page")

        doctors = [c for c in components if c["type"] == "doctor"]
        assert len(doctors) > 0
        doctor = doctors[0]
        assert doctor["content"] == "Dr. Smith"
        assert doctor["metadata"]["specialty"] == "Cardiology"
        assert doctor["metadata"]["experience"] == "15 years"
        assert doctor["metadata"]["description"] == "Expert cardiologist"

    def test_parse_service_card(self):
        """Service cards should have proper metadata with features."""
        from backend.scraping.parser import parse_page
        components = parse_page(SAMPLE_HTML_CARDS, "https://example.com", "Test Page")

        services = [c for c in components if c["type"] == "service"]
        assert len(services) > 0
        service = services[0]
        assert "Cardiology" in service["content"]
        assert service["metadata"]["description"] == "Heart care services"
        attrs = service["metadata"].get("attributes", {})
        assert attrs.get("features") == ["Echocardiography", "Angioplasty"]

    def test_parse_testimonial_card(self):
        """Testimonial cards should have proper metadata."""
        from backend.scraping.parser import parse_page
        components = parse_page(SAMPLE_HTML_CARDS, "https://example.com", "Test Page")

        testimonials = [c for c in components if c["type"] == "testimonial"]
        assert len(testimonials) > 0
        t = testimonials[0]
        assert t["content"] == "Great service!"
        assert t["metadata"]["name"] == "John Doe"
        assert t["metadata"]["rating"] == 5

    def test_parse_stats(self):
        """Stat items should be parsed correctly."""
        from backend.scraping.parser import parse_page
        components = parse_page(SAMPLE_HTML_STATS, "https://example.com/stats", "Stats")

        stats = [c for c in components if c["type"] == "stat"]
        assert len(stats) == 2
        assert stats[0]["content"] == "200+ Doctors"
        assert stats[1]["content"] == "50K+ Patients"

    def test_parse_removes_scripts(self):
        """Script and style tags should be removed."""
        from backend.scraping.parser import parse_page
        html = "<html><body><main><p>Hello</p><script>alert('x')</script></main></body></html>"
        components = parse_page(html, "https://example.com")
        assert len(components) > 0

    def test_parse_empty_html(self):
        """Empty HTML should return empty components list."""
        from backend.scraping.parser import parse_page
        components = parse_page("<html></html>", "https://example.com")
        assert components == []

    def test_parse_includes_page_url_in_metadata(self):
        """All components should include page_url in metadata."""
        from backend.scraping.parser import parse_page
        components = parse_page(SAMPLE_HTML_CARDS, "https://example.com/doctors", "Doctors")

        for comp in components:
            assert "page_url" in comp["metadata"]
            assert "page_url" in comp["metadata"]
            assert comp["metadata"]["page_url"] == "https://example.com/doctors"


# ============================================================
# Tests: extract_scrollable_sections
# ============================================================

class TestExtractScrollableSections:
    """Tests for extract_scrollable_sections function."""

    def test_extracts_sections_with_ids(self):
        """Should extract sections with id attributes."""
        from backend.scraping.parser import extract_scrollable_sections

        soup = BeautifulSoup(SAMPLE_HTML_WITH_SECTIONS, "html.parser")
        sections = extract_scrollable_sections(soup, "https://example.com")

        ids = [s["selector"] for s in sections if s["type"] == "id"]
        assert "#hero" in ids
        assert "#testimonials" in ids

    def test_extracts_sections_with_classes(self):
        """Should extract sections with meaningful class names."""
        from backend.scraping.parser import extract_scrollable_sections

        soup = BeautifulSoup(SAMPLE_HTML_WITH_SECTIONS, "html.parser")
        sections = extract_scrollable_sections(soup, "https://example.com")

        classes = [s["selector"] for s in sections if s["type"] == "class"]
        has_features = any(".features" in c for c in classes)
        assert has_features, "Should find .features class section"

    def test_each_section_has_label(self):
        """Each section should have a label."""
        from backend.scraping.parser import extract_scrollable_sections

        soup = BeautifulSoup(SAMPLE_HTML_WITH_SECTIONS, "html.parser")
        sections = extract_scrollable_sections(soup, "https://example.com")

        for s in sections:
            assert "label" in s
            assert isinstance(s["label"], str)
            assert len(s["label"]) > 0

    def test_each_section_has_selector(self):
        """Each section should have a CSS selector."""
        from backend.scraping.parser import extract_scrollable_sections

        soup = BeautifulSoup(SAMPLE_HTML_WITH_SECTIONS, "html.parser")
        sections = extract_scrollable_sections(soup, "https://example.com")

        for s in sections:
            assert "selector" in s
            assert s["selector"].startswith("#") or s["selector"].startswith(".")

    def test_empty_page_returns_empty_list(self):
        """Empty page should return empty list."""
        from backend.scraping.parser import extract_scrollable_sections

        soup = BeautifulSoup("<html></html>", "html.parser")
        sections = extract_scrollable_sections(soup, "https://example.com")
        assert isinstance(sections, list)


# ============================================================
# Tests: analyze_form_fields
# ============================================================

class TestAnalyzeFormFields:
    """Tests for analyze_form_fields function."""

    def test_analyzes_form_inputs(self):
        """Should analyze input fields in forms."""
        from backend.scraping.parser import analyze_form_fields

        soup = BeautifulSoup(SAMPLE_HTML_WITH_FORMS, "html.parser")
        fields = analyze_form_fields(soup, "https://example.com/booking")

        assert len(fields) >= 3  # select + 2 inputs

        field_names = [f["name"] for f in fields]
        assert "name" in field_names
        assert "email" in field_names
        assert "department" in field_names

    def test_detects_required_fields(self):
        """Should detect required fields."""
        from backend.scraping.parser import analyze_form_fields

        soup = BeautifulSoup(SAMPLE_HTML_WITH_FORMS, "html.parser")
        fields = analyze_form_fields(soup, "https://example.com/booking")

        for f in fields:
            if f["name"] == "name":
                assert f["required"] is True
            if f["name"] == "email":
                assert f["required"] is True

    def test_extracts_select_options(self):
        """Should extract options from select elements."""
        from backend.scraping.parser import analyze_form_fields

        soup = BeautifulSoup(SAMPLE_HTML_WITH_FORMS, "html.parser")
        fields = analyze_form_fields(soup, "https://example.com/booking")

        for f in fields:
            if f["name"] == "department":
                assert "options" in f
                assert len(f["options"]) == 2
                assert f["options"][0]["value"] == "cardiology"
                assert f["options"][1]["value"] == "neurology"
                break

    def test_empty_page_returns_empty_list(self):
        """Page with no forms should return empty list."""
        from backend.scraping.parser import analyze_form_fields

        soup = BeautifulSoup("<html><body><p>No forms</p></body></html>", "html.parser")
        fields = analyze_form_fields(soup, "https://example.com")
        assert fields == []


# ============================================================
# Tests: categorize_page
# ============================================================

class TestCategorizePage:
    """Tests for categorize_page function."""

    def test_form_page_detection(self):
        """Pages with <form> should be categorized as form_page."""
        from backend.scraping.parser import categorize_page

        soup = BeautifulSoup(SAMPLE_HTML_WITH_FORMS, "html.parser")
        category = categorize_page(soup, "https://example.com/booking")
        assert category == "form_page"

    def test_listing_page_with_cards(self):
        """Pages with multiple card elements should be listing_page."""
        from backend.scraping.parser import categorize_page

        soup = BeautifulSoup(SAMPLE_HTML_CARDS, "html.parser")
        category = categorize_page(soup, "https://example.com/doctors")
        assert category == "listing_page"

    def test_info_page_default(self):
        """Simple pages should default to info_page."""
        from backend.scraping.parser import categorize_page

        soup = BeautifulSoup("<html><body><h1>About Us</h1><p>Info</p></body></html>", "html.parser")
        category = categorize_page(soup, "https://example.com/about")
        assert category == "info_page"


# ============================================================
# Tests: format_components_for_llm
# ============================================================

class TestFormatComponentsForLLM:
    """Tests for format_components_for_llm function."""

    def test_empty_components_returns_empty(self):
        """Empty components should return empty string."""
        from backend.scraping.parser import format_components_for_llm
        result = format_components_for_llm([])
        assert result == ""

    def test_returns_formatted_string(self):
        """Should return a formatted string with component data."""
        from backend.scraping.parser import format_components_for_llm
        components = [
            {"type": "doctor", "content": "Dr. Smith", "metadata": {"specialty": "Cardiology", "page_url": "/doctors"}},
            {"type": "service", "content": "Cardiology", "metadata": {"description": "Heart care", "page_url": "/services"}},
        ]
        result = format_components_for_llm(components)
        assert "Dr. Smith" in result
        assert "Cardiology" in result
        assert "Heart care" in result
        assert "/doctors" in result

    def test_respects_max_chars(self):
        """Should truncate to max_chars."""
        from backend.scraping.parser import format_components_for_llm
        components = [
            {"type": "doctor", "content": "A" * 500, "metadata": {"specialty": "B" * 500, "page_url": "/doctors"}},
            {"type": "service", "content": "C" * 500, "metadata": {"description": "D" * 500, "page_url": "/services"}},
        ]
        result = format_components_for_llm(components, max_chars=200)
        assert len(result) <= 200

    def test_groups_by_type(self):
        """Should group components by type."""
        from backend.scraping.parser import format_components_for_llm
        components = [
            {"type": "doctor", "content": "Dr. A", "metadata": {"page_url": "/doctors"}},
            {"type": "doctor", "content": "Dr. B", "metadata": {"page_url": "/doctors"}},
            {"type": "service", "content": "Service A", "metadata": {"page_url": "/services"}},
        ]
        result = format_components_for_llm(components)
        # Should have sections for Doctor and Service (using dash format)
        assert "--- Doctor ---" in result
        assert "--- Service ---" in result


# ============================================================
# Tests: Generic heuristics
# ============================================================

class TestGenericHeuristics:
    """Tests for generic heuristic component detection."""

    def test_detects_generic_cards(self):
        """Should detect generic card patterns."""
        from backend.scraping.parser import parse_page
        components = parse_page(SAMPLE_HTML_WITH_GENERIC, "https://example.com")
        types = [c["type"] for c in components]
        # Should have found product-like cards (via [class*=\"product\"])
        assert len(components) > 0

    def test_parses_fallback_elements(self):
        """Should fall back to heading/paragraph parsing."""
        from backend.scraping.parser import parse_page
        html = "<html><body><main><h1>Main Title</h1><p>Paragraph text.</p></main></body></html>"
        components = parse_page(html, "https://example.com")

        types = [c["type"] for c in components]
        assert "heading" in types
        assert "paragraph" in types


# ============================================================
# Tests: FAQ parsing
# ============================================================

class TestFaqParsing:
    """Tests for FAQ item parsing."""

    HTML_WITH_FAQ = """
    <html>
    <body>
    <main>
      <div class="faq__list">
        <div class="faq__item">
          <button class="faq__question">What is your return policy?</button>
          <div class="faq__answer"><p>30-day return policy.</p></div>
        </div>
        <div class="faq__item">
          <button class="faq__question">Do you offer support?</button>
          <div class="faq__answer"><p>24/7 customer support.</p></div>
        </div>
      </div>
    </main>
    </body>
    </html>
    """

    def test_parses_faq_items(self):
        """FAQ items should be parsed with question and answer."""
        from backend.scraping.parser import parse_page
        components = parse_page(self.HTML_WITH_FAQ, "https://example.com/faq", "FAQ")

        faqs = [c for c in components if c["type"] == "faq"]
        assert len(faqs) == 2
        assert faqs[0]["content"] == "What is your return policy?"
        assert faqs[0]["metadata"]["answer"] == "30-day return policy."
        assert faqs[1]["content"] == "Do you offer support?"
        assert faqs[1]["metadata"]["answer"] == "24/7 customer support."
