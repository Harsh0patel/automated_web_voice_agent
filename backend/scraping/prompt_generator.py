"""
Dynamic System Prompt Generator.

Analyzes scraped page data (URLs, titles, categories, form fields) to
auto-generate navigation mappings, scrollable sections, and form schemas
for the LLM system prompt.
"""
from __future__ import annotations

from typing import Any

from backend.app.logger import get_logger
from backend.scraping import site_config

logger = get_logger(__name__)


def generate_navigation_mappings(pages: list[dict]) -> dict[str, str]:
    """Auto-generate keyword to URL path mappings from scraped pages.

    Args:
        pages: List of scraped page dicts with url, title, content, page_category.

    Returns:
        Dict mapping lowercase keywords to URL paths.
    """
    mappings: dict[str, str] = {}
    config_mappings = site_config.get_page_mappings()
    mappings.update(config_mappings)

    for page in pages:
        url = page.get("url", "")
        title = page.get("title", "")
        path = _extract_path(url)
        if not path or path == "/":
            continue
        title_lower = title.lower()
        title_words = set(title_lower.split())

        keywords = {
            "booking": ["booking", "appointment", "book", "schedule", "reserve", "visit"],
            "doctors": ["doctor", "doctors", "physician", "physicians", "specialist", "team"],
            "services": ["service", "services", "treatment", "treatments", "what we do"],
            "contact": ["contact", "reach", "get in touch", "support"],
            "about": ["about", "our story", "mission", "who we are"],
            "insurance": ["insurance", "plan", "plans", "coverage"],
            "blog": ["blog", "article", "articles", "news", "health tips"],
            "pharmacy": ["pharmacy", "medication", "medications", "drug", "prescription", "rx"],
            "careers": ["career", "careers", "job", "jobs", "join our team"],
            "faq": ["faq", "faqs", "frequently asked", "questions"],
        }
        for keyword, trigger_words in keywords.items():
            if keyword in mappings:
                continue
            for trigger in trigger_words:
                if trigger in title_lower or trigger in path.lower():
                    mappings[keyword] = path
                    break

    return mappings


def generate_scrollable_sections(pages: list[dict]) -> dict[str, str]:
    """Auto-generate scrollable section selectors from scraped pages."""
    sections: dict[str, str] = {}
    config_sections = site_config.get_scrollable_sections()
    sections.update(config_sections)

    for page in pages:
        for sec in page.get("scrollable_sections", []):
            selector = sec.get("selector", "")
            label = sec.get("label", "")
            if selector and selector not in sections:
                sections[selector] = label

    return sections


def generate_form_schemas(pages: list[dict]) -> list[dict]:
    """Generate form field schemas from scraped pages.

    Increased limit from 10 to 30 form schemas per prompt.
    """
    all_schemas: list[dict] = []
    seen: set[str] = set()

    for page in pages:
        for field in page.get("form_fields", []):
            field_name = field.get("name", "")
            if field_name and field_name not in seen:
                seen.add(field_name)
                all_schemas.append({
                    "page_url": _extract_path(page.get("url", "")),
                    "field_name": field_name,
                    "field_type": field.get("type", "text"),
                    "required": field.get("required", False),
                    "options": field.get("options", []),
                })

    return all_schemas


def build_system_prompt(pages: list[dict], site_name: str | None = None) -> str:
    """Build a complete system prompt with dynamic navigation mappings."""
    if not site_name:
        site_name = site_config.get_site_name()

    nav_mappings = generate_navigation_mappings(pages)
    scroll_sections = generate_scrollable_sections(pages)
    form_schemas = generate_form_schemas(pages)

    mapping_lines = [f"   - {k} -> {v}" for k, v in sorted(nav_mappings.items())]
    scroll_lines = [f"   - {s} - {l}" for s, l in sorted(scroll_sections.items())]

    form_lines = []
    for schema in form_schemas[:30]:
        field = schema.get("field_name", "")
        ftype = schema.get("field_type", "text")
        required = " (required)" if schema.get("required") else ""
        options = schema.get("options", [])
        if options:
            option_texts = ", ".join(f"{o.get('text','')}={o.get('value','')}" for o in options[:5])
            form_lines.append(f"   - ?{field}={option_texts}{required} (page: {schema.get('page_url', '')})")
        else:
            form_lines.append(f"   - ?{field}=<{ftype}> (page: {schema.get('page_url', '')})")

    prompt = f"""You are a helpful, conversational AI assistant for {site_name}. You answer user questions using context from the site's knowledge base when relevant.

## Guidelines
- Use the provided context to answer accurately and conversationally.
- If the user sends a greeting or small talk (hello, hi, thanks, how are you), respond warmly and briefly.
- If the context contains relevant information, summarize it naturally.
- If no relevant context is available, say you don't have that information.
- Keep responses concise - 1-4 sentences.
- Never mention "sources" or "knowledge base".
- Use the navigation mappings to take the user where they want. NEVER say "I can't".
- For actions you truly can't perform (e.g. processing payments), explain how the user can do it themselves.

CRITICAL: Respond with ONLY a single valid JSON object, no other text, no markdown.

## Response Format
Always include a "message" field. Optionally, include an "action" (single) or "actions" (array) field.

### Single action (simple):
{{"message": "Your response", "action": {{"type": "navigate", "path": "/page-name"}}}}

### Multi-step sequence (complex):
{{"message": "Let me help you with that.", "actions": [
  {{"type": "navigate", "path": "/page-name"}},
  {{"type": "wait", "delay": 1500}},
  {{"type": "fill", "selector": "#field-id", "value": "Some value"}},
  {{"type": "submit", "selector": "#form-id"}}
]}}

### Available action types:
- {{"type": "navigate", "path": "/page-url"}} - Navigate to a page
- {{"type": "scroll", "selector": "#section-id"}} - Scroll to a section
- {{"type": "submit", "selector": "#form-id"}} - Submit a form
- {{"type": "wait", "delay": 1000}} - Wait N ms (after navigation)
- {{"type": "focus", "selector": "#input-id"}} - Focus an input
- {{"type": "click", "selector": ".btn"}} - Click any element
- {{"type": "fill", "selector": "input#id", "value": "text"}} - Fill a form field
- {{"type": "select", "selector": "select#id", "value": "option"}} - Select a dropdown
- {{"type": "check", "selector": "input#id", "checked": true}} - Check/uncheck a box
"""

    if nav_mappings:
        prompt += f"""
### Auto-Discovered Navigation Mappings
{chr(10).join(mapping_lines) if mapping_lines else '   (auto-discovered from context)'}

### Dynamic Action Rules:
1. **Use page_url from context** - Navigate to the page_url found in context
2. **Current page awareness** - Use scroll for current page, navigate for other pages
3. **Query parameters from context** - Add filter params from context when applicable
4. **Form pre-filling** - Navigate with query params to pre-fill fields using form schemas
"""

    if form_schemas:
        prompt += f"""
### Known Form Fields (for constructing query params):
{chr(10).join(form_lines) if form_lines else '   (discover from page context)'}
"""

    prompt += f"""
### Known scrollable sections:
{chr(10).join(scroll_lines[:30]) if scroll_lines else '   (auto-discovered from page)'}

## Format
{{"message": "Your response", "action": {{"type": "navigate", "path": "/page-name"}}}}
"""
    return prompt


def _extract_path(url: str) -> str:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.path.rstrip("/") or "/"
