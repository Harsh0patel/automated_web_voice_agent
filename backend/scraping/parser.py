"""
Component Parser - extracts typed, structured components from rendered HTML.

Uses configuration-driven selectors (via site_config) and generic heuristics
to auto-discover common patterns like cards, profiles, FAQ items, etc.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bs4 import BeautifulSoup

from backend.app.logger import get_logger
from backend.scraping import site_config

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Component type definitions (site-agnostic)
# ---------------------------------------------------------------------------

COMPONENT_TYPES = {
    "hero": "Hero / banner section at the top of a page",
    "service": "A service or feature card with title and description",
    "doctor": "Staff / team profile card with name, specialty, bio",
    "testimonial": "Review or testimonial with quote, name, rating",
    "stat": "A numeric statistic with value and label",
    "cta": "Call-to-action section promoting an action",
    "blog_post": "A blog / article card",
    "job": "A job / career listing",
    "insurance_plan": "A pricing or plan card with features",
    "medication": "A product listing card with name and price",
    "pharmacy_service": "A service offering card",
    "milestone": "A company history milestone",
    "value": "A core value / principle card",
    "faq": "FAQ item with question and answer",
    "contact_info": "Contact information (address, phone, email, hours)",
    "coverage_item": "A coverage or category card",
    "benefit": "A benefits or perk card",
    "why_choose": "A 'why choose us' selling point",
    "feature_list": "A list of features or bullet points",
    "heading": "Generic section heading (h1-h6)",
    "paragraph": "Generic text paragraph",
    "list_item": "Generic list item",
    "link": "A hyperlink with text",
}

# Generic CSS class heuristics for auto-discovery of common patterns
_GENERIC_HEURISTICS: list[tuple[str, str, str]] = [
    ("[class*=\"card\"]",           "service",        "cards"),
    ("[class*=\"Card\"]",           "service",        "cards"),
    ("[class*=\"profile\"]",        "doctor",         "profiles"),
    ("[class*=\"Profile\"]",        "doctor",         "profiles"),
    ("[class*=\"testimonial\"]",    "testimonial",    "testimonials"),
    ("[class*=\"Testimonial\"]",    "testimonial",    "testimonials"),
    ("[class*=\"faq\"]",            "faq",            "faqs"),
    ("[class*=\"Faq\"]",            "faq",            "faqs"),
    ("[class*=\"FAQ\"]",            "faq",            "faqs"),
    ("[class*=\"blog\"]",           "blog_post",      "blog"),
    ("[class*=\"Blog\"]",           "blog_post",      "blog"),
    ("[class*=\"job\"]",            "job",            "jobs"),
    ("[class*=\"Job\"]",            "job",            "jobs"),
    ("[class*=\"stat\"]",           "stat",           "stats"),
    ("[class*=\"Stat\"]",           "stat",           "stats"),
    ("[class*=\"price\"]",          "insurance_plan", "pricing"),
    ("[class*=\"Price\"]",          "insurance_plan", "pricing"),
    ("[class*=\"plan\"]",           "insurance_plan", "plans"),
    ("[class*=\"Plan\"]",           "insurance_plan", "plans"),
    ("[class*=\"medication\"]",     "medication",     "medications"),
    ("[class*=\"Medication\"]",     "medication",     "medications"),
    ("[class*=\"product\"]",        "medication",     "products"),
    ("[class*=\"Product\"]",        "medication",     "products"),
    ("[class*=\"value\"]",          "value",          "values"),
    ("[class*=\"Value\"]",          "value",          "values"),
    ("[class*=\"benefit\"]",        "benefit",        "benefits"),
    ("[class*=\"Benefit\"]",        "benefit",        "benefits"),
    ("[class*=\"milestone\"]",      "milestone",      "timeline"),
    ("[class*=\"Milestone\"]",      "milestone",      "timeline"),
    ("[class*=\"coverage\"]",       "coverage_item",  "coverage"),
    ("[class*=\"Coverage\"]",       "coverage_item",  "coverage"),
    ("[class*=\"contact\"]",        "contact_info",   "contact"),
    ("[class*=\"Contact\"]",        "contact_info",   "contact"),
]


@dataclass
class Component:
    """A single extracted component from a page."""
    type: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"type": self.type, "content": self.content, "metadata": self.metadata}


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _get_clean_text(el, default: str = "") -> str:
    if el is None:
        return default
    return el.get_text(strip=True) or default


def _find_els(container, field_config) -> list:
    if isinstance(field_config, list):
        for sel in field_config:
            els = container.select(sel)
            if els:
                return els
        return []
    if isinstance(field_config, dict):
        return container.select(field_config.get("selector", ""))
    return container.select(field_config)


def _find_el(container, field_config):
    els = _find_els(container, field_config)
    return els[0] if els else None


def _parse_generic_card(card, comp_type: str, section: str, page_url: str, page_title: str) -> Component | None:
    text = _get_clean_text(card)
    if not text:
        return None
    title_el = card.find(["h1", "h2", "h3", "h4", "h5", "h6", "strong", "b"])
    title = _get_clean_text(title_el) if title_el else text[:100]
    desc_el = card.find("p")
    desc = _get_clean_text(desc_el)

    attrs = {}
    link_el = card.find("a")
    if link_el:
        attrs["link"] = link_el.get("href", "")

    features = []
    ul = card.find("ul")
    if ul:
        features = [_get_clean_text(li) for li in ul.find_all("li") if _get_clean_text(li)]
    if features:
        attrs["features"] = features

    return Component(type=comp_type, content=title, metadata={
        "description": desc, "page_url": page_url, "page_title": page_title,
        "section": section, "attributes": attrs,
    })


def _parse_service_card(card, section: str, page_url: str, page_title: str) -> Component | None:
    parser_config = site_config.get_component_parsers()
    fields = parser_config.get("service_fields", {})
    title_el = _find_el(card, fields.get("title", ["h3", "h4"]))
    title = _get_clean_text(title_el) or _get_clean_text(card.find(["h3", "h4"]))
    if not title:
        title = _get_clean_text(card)[:80]
    if not title:
        return None
    desc_el = _find_el(card, fields.get("description", "p"))
    desc = _get_clean_text(desc_el)
    icon_config = fields.get("icon", [])
    icon_el = _find_el(card, icon_config) if icon_config else None
    icon = _get_clean_text(icon_el)

    features = []
    feature_selector = fields.get("features", "ul li")
    if isinstance(feature_selector, str):
        features = [_get_clean_text(li) for li in card.select(feature_selector) if _get_clean_text(li)]

    link_el = _find_el(card, fields.get("link", "a"))
    link = link_el.get("href", "") if link_el else ""

    attrs = {"icon": icon}
    if features:
        attrs["features"] = features
    if link:
        attrs["link"] = link

    return Component(type="service", content=title, metadata={
        "description": desc, "page_url": page_url, "page_title": page_title,
        "section": section, "attributes": attrs,
    })


def _parse_doctor_card(card, section: str, page_url: str, page_title: str) -> Component | None:
    parser_config = site_config.get_component_parsers()
    fields = parser_config.get("doctor_fields", {})
    name_el = _find_el(card, fields.get("name", []))
    name = _get_clean_text(name_el)
    if not name:
        name_el = card.find(["h3", "h4"])
        name = _get_clean_text(name_el)
    if not name:
        return None
    specialty_el = _find_el(card, fields.get("specialty", []))
    exp_el = _find_el(card, fields.get("experience", []))
    desc_el = _find_el(card, fields.get("description", []))
    return Component(type="doctor", content=name, metadata={
        "specialty": _get_clean_text(specialty_el),
        "experience": _get_clean_text(exp_el),
        "description": _get_clean_text(desc_el),
        "page_url": page_url, "page_title": page_title, "section": section,
    })


def _parse_testimonial_card(card, section: str, page_url: str, page_title: str) -> Component | None:
    parser_config = site_config.get_component_parsers()
    fields = parser_config.get("testimonial_fields", {})
    text_el = _find_el(card, fields.get("text", []))
    text = _get_clean_text(text_el)
    if not text:
        return None
    name_el = _find_el(card, fields.get("author", []))
    name = _get_clean_text(name_el) if name_el else ""
    stars_el = _find_el(card, fields.get("stars", []))
    rating_text = _get_clean_text(stars_el)
    role_el = _find_el(card, fields.get("role", ["small"]))
    role = _get_clean_text(role_el)
    rating = 0
    if "★" in rating_text:
        rating = rating_text.count("★")
    elif rating_text.isdigit():
        rating = int(rating_text)
    return Component(type="testimonial", content=text.strip("\"'"), metadata={
        "name": name, "role": role, "rating": rating,
        "page_url": page_url, "page_title": page_title, "section": section,
    })


def _parse_stat_item(card, section: str, page_url: str, page_title: str) -> Component | None:
    parser_config = site_config.get_component_parsers()
    fields = parser_config.get("stat_fields", {})
    value_el = _find_el(card, fields.get("value", [".stat-value"]))
    label_el = _find_el(card, fields.get("label", [".stat-label"]))
    value = _get_clean_text(value_el)
    if not value:
        return None
    return Component(type="stat", content=f"{value} {_get_clean_text(label_el)}", metadata={
        "value": value, "label": _get_clean_text(label_el),
        "page_url": page_url, "page_title": page_title, "section": section,
    })


def _parse_plan_card(card, section: str, page_url: str, page_title: str) -> Component | None:
    parser_config = site_config.get_component_parsers()
    fields = parser_config.get("insurance_plan_fields", {})
    name_el = _find_el(card, fields.get("name", []))
    name = _get_clean_text(name_el)
    if not name:
        return None
    price_el = _find_el(card, fields.get("price", []))
    period_el = _find_el(card, fields.get("period", []))
    desc_el = _find_el(card, fields.get("description", []))
    badge_el = _find_el(card, fields.get("badge", []))
    features = []
    feature_selector = fields.get("features", "li")
    if isinstance(feature_selector, str):
        features = [_get_clean_text(li) for li in card.select(feature_selector) if _get_clean_text(li)]
    return Component(type="insurance_plan", content=name, metadata={
        "price": _get_clean_text(price_el) + _get_clean_text(period_el),
        "description": _get_clean_text(desc_el), "features": features,
        "popular": bool(badge_el),
        "page_url": page_url, "page_title": page_title, "section": section,
    })


def _parse_faq_item(card, section: str, page_url: str, page_title: str) -> Component | None:
    """Parse a FAQ item with question and answer."""
    parser_config = site_config.get_component_parsers()
    fields = parser_config.get("faq_fields", {})
    q_el = _find_el(card, fields.get("question", ".faq__question"))
    a_el = _find_el(card, fields.get("answer", ".faq__answer"))
    question = _get_clean_text(q_el)
    if not question:
        btn = card.find("button")
        if btn:
            question = _get_clean_text(btn)
    answer = _get_clean_text(a_el)
    if not question:
        return None
    return Component(type="faq", content=question, metadata={
        "answer": answer, "page_url": page_url, "page_title": page_title, "section": section,
    })


def _parse_fallback(el, page_url: str, page_title: str, section: str) -> Component | None:
    text = _get_clean_text(el)
    if not text:
        return None
    tag = el.name or ""
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return Component(type="heading", content=text, metadata={"level": tag, "page_url": page_url, "page_title": page_title, "section": section})
    elif tag == "p":
        return Component(type="paragraph", content=text, metadata={"page_url": page_url, "page_title": page_title, "section": section})
    elif tag == "li":
        return Component(type="list_item", content=text, metadata={"page_url": page_url, "page_title": page_title, "section": section})
    elif tag == "a":
        href = el.get("href", "")
        if text and href and not href.startswith("#"):
            return Component(type="link", content=text, metadata={"href": href, "page_url": page_url, "page_title": page_title, "section": section})
    return None


def _get_semantic_selectors() -> list[tuple[str, str, str]]:
    config_selectors = site_config.get_semantic_selectors()
    all_selectors = list(config_selectors)
    config_selector_strings = {s[0] for s in all_selectors}
    for sel, ctype, section in _GENERIC_HEURISTICS:
        if sel not in config_selector_strings:
            all_selectors.append((sel, ctype, section))
    return all_selectors


def extract_scrollable_sections(soup: BeautifulSoup, url: str, max_sections: int = 200) -> list[dict]:
    """Extract all scrollable section identifiers from the page.
    
    Increased max_sections from 50 to 200 for more comprehensive coverage.
    """
    sections = []

    for el in soup.find_all(id=True):
        el_id = el.get("id", "")
        if el_id and not el_id.startswith("_"):
            tag = el.name or "div"
            heading = el.find(["h1", "h2", "h3", "h4", "h5", "h6"])
            label = _get_clean_text(heading) if heading else el_id.replace("-", " ").replace("_", " ").title()
            sections.append({"selector": f"#{el_id}", "type": "id", "tag": tag, "label": label})

    section_tags = ["section", "div", "article", "main", "header", "footer"]
    for tag_name in section_tags:
        for el in soup.find_all(tag_name, class_=True):
            classes = el.get("class", [])
            for cls in classes:
                if cls and not cls.startswith("_") and len(cls) > 2:
                    heading = el.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                    label = _get_clean_text(heading) if heading else cls.replace("-", " ").replace("_", " ").title()
                    if not any(s["selector"] == f".{cls}" for s in sections):
                        sections.append({"selector": f".{cls}", "type": "class", "tag": tag_name, "label": label})
                        break

    config_sections = site_config.get_scrollable_sections()
    for selector, label in config_sections.items():
        if not any(s["selector"] == selector for s in sections):
            sections.append({"selector": selector, "type": "config", "tag": "section", "label": label})

    if len(sections) > max_sections:
        sections = sections[:max_sections]

    return sections


def analyze_form_fields(soup: BeautifulSoup, url: str) -> list[dict]:
    """Analyze form fields on a page and generate a query parameter schema."""
    form_fields = []
    forms = soup.find_all("form")
    if not forms:
        return []

    for form in forms:
        form_id = form.get("id", "")
        for inp in form.find_all(["input", "select", "textarea"]):
            field_name = inp.get("name", "") or inp.get("id", "")
            if not field_name:
                continue
            field_type = inp.name
            input_type = inp.get("type", "text") if field_type == "input" else "text"
            is_required = inp.get("required") is not None
            field_info = {
                "name": field_name,
                "type": input_type if field_type == "input" else field_type,
                "selector": f"#{inp.get('id', '')}" if inp.get("id") else f"[name=\"{field_name}\"]",
                "required": is_required,
                "form_id": form_id or "",
            }
            if inp.name == "select":
                options = []
                for opt in inp.find_all("option"):
                    opt_val = opt.get("value", "")
                    opt_text = _get_clean_text(opt)
                    if opt_val:
                        options.append({"value": opt_val, "text": opt_text or opt_val})
                if options:
                    field_info["options"] = options
            form_fields.append(field_info)

    return form_fields


def categorize_page(soup: BeautifulSoup, url: str) -> str:
    """Categorize a page by its purpose using heuristics.
    
    Returns: 'form_page', 'listing_page', 'detail_page', or 'info_page'
    """
    url_lower = url.lower()
    patterns = site_config.get_navigation_patterns()
    for url_path in patterns.get("form_pages", []):
        if url_path in url_lower:
            return "form_page"
    for url_path in patterns.get("listing_pages", []):
        if url_path in url_lower:
            return "listing_page"
    for url_path in patterns.get("detail_pages", []):
        if url_path in url_lower:
            return "detail_page"
    for url_path in patterns.get("info_pages", []):
        if url_path in url_lower:
            return "info_page"

    if soup.find("form"):
        return "form_page"
    card_elements = soup.select("[class*=\"card\"], [class*=\"Card\"], [class*=\"item\"], [class*=\"Item\"]")
    if len(card_elements) >= 3:
        return "listing_page"
    if soup.find("article") and not soup.find_all("article", recursive=False):
        return "detail_page"
    return "info_page"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_page(html: str, url: str, title: str | None = None) -> list[dict]:
    """Parse rendered HTML into a list of structured components."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()

    if not title:
        title = _get_clean_text(soup.title) if soup.title else url

    components: list[Component] = []
    seen: set[tuple[str, str]] = set()

    semantic_selectors = _get_semantic_selectors()
    for selector, comp_type, section in semantic_selectors:
        for el in soup.select(selector):
            text = _get_clean_text(el)
            if not text:
                continue
            comp = None
            if comp_type == "service":
                comp = _parse_service_card(el, section, url, title)
            elif comp_type == "doctor":
                comp = _parse_doctor_card(el, section, url, title)
            elif comp_type == "testimonial":
                comp = _parse_testimonial_card(el, section, url, title)
            elif comp_type == "stat":
                comp = _parse_stat_item(el, section, url, title)
            elif comp_type == "insurance_plan":
                comp = _parse_plan_card(el, section, url, title)
            elif comp_type == "faq":
                comp = _parse_faq_item(el, section, url, title)
            else:
                comp = _parse_generic_card(el, comp_type, section, url, title)

            if comp:
                key = (comp.type, comp.content)
                if key not in seen:
                    components.append(comp)
                    seen.add(key)

    main = soup.find("main") or soup.find("article") or soup.find("body") or soup
    for el in main.descendants:
        if el.name not in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "a"):
            continue
        parent_selectors = [s[0] for s in semantic_selectors]
        if any(el.find_parent(sel) for sel in parent_selectors):
            continue
        text = _get_clean_text(el)
        if not text:
            continue
        comp = _parse_fallback(el, url, title, "main")
        if comp:
            key = (comp.type, comp.content)
            if key not in seen:
                components.append(comp)
                seen.add(key)

    return [c.to_dict() for c in components]


def format_components_for_llm(components: list[dict], max_chars: int = 10000) -> str:
    """Format a list of components into an LLM-friendly context string.

    Increased max_chars from 3000 to 10000 to include more context.
    """
    if not components:
        return ""

    grouped: dict[str, list[dict]] = {}
    for comp in components:
        t = comp.get("type", "unknown")
        grouped.setdefault(t, []).append(comp)

    lines: list[str] = []
    total = 0

    priority = [
        "service", "doctor", "testimonial", "faq", "insurance_plan",
        "blog_post", "job", "medication", "stat", "milestone",
        "value", "hero", "contact_info", "cta",
    ]

    def add_section(type_name: str, items: list[dict]) -> int:
        nonlocal total
        count = 0
        label = type_name.replace("_", " ").title()
        section_lines = [f"\n--- {label} ---"]

        for item in items:
            content = item.get("content", "")
            meta = item.get("metadata", {})
            desc = meta.get("description", "")
            extras = []

            if type_name == "doctor":
                extras = [f"  Specialty: {meta.get('specialty', '')}", f"  Experience: {meta.get('experience', '')}"]
            elif type_name == "service" and meta.get("attributes", {}).get("features"):
                extras = [f"  Features: {', '.join(meta['attributes']['features'][:5])}"]
            elif type_name == "testimonial":
                extras = [f"  - {meta.get('name', '')} ({meta.get('role', '')})"]
            elif type_name == "faq":
                extras = [f"  Answer: {meta.get('answer', '')[:200]}"]
            elif type_name == "insurance_plan":
                extras = [f"  {meta.get('price', '')} - {meta.get('description', '')}"]
            elif type_name == "blog_post":
                extras = [f"  {meta.get('excerpt', '')[:150]}"]
            elif type_name == "job":
                extras = [f"  {meta.get('description', '')[:150]}"]
            elif type_name == "stat":
                desc_part = f" - {desc}" if desc else ""
                extras = [f" {desc_part}"]
            elif type_name == "milestone":
                extras = [f"  {meta.get('description', '')[:200]}"]

            if desc and not extras:
                extras = [f"  {desc[:200]}"]

            page_url = meta.get("page_url", "")
            if page_url:
                extras.append(f"  (page: {page_url})")

            item_lines = [f"  * {content}"]
            item_lines.extend(extras)
            item_str = "\n".join(item_lines)

            if total + len("\n".join(section_lines)) + len(item_str) + 2 > max_chars:
                break

            section_lines.append(item_str)
            count += 1

        block = "\n".join(section_lines)
        if count > 0 and total + len(block) + 2 <= max_chars:
            lines.append(block)
            total += len(block)
        return count

    for t in priority:
        if t in grouped:
            add_section(t, grouped[t])

    for t, items in grouped.items():
        if t not in priority:
            add_section(t, items)

    return "\n".join(lines).strip()
