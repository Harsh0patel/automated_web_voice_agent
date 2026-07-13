"""
Component Parser — extracts typed, structured components from rendered HTML.

Instead of storing raw scraped text, this parser identifies semantic components
(services, doctors, testimonials, stats, etc.) and returns structured data
that the LLM can query directly without having to parse raw text.

This makes responses faster and more accurate since the LLM gets clean,
tagged data instead of messy text blobs.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from bs4 import BeautifulSoup

from backend.core.logger import get_logger

logger = get_logger(__name__)


# ──────────────────────────────────────────────
#  Component type definitions
# ──────────────────────────────────────────────

COMPONENT_TYPES = {
    "hero": "Hero / banner section at the top of a page",
    "service": "A medical service or feature card",
    "doctor": "Doctor / staff profile with name, specialty, bio",
    "testimonial": "Patient testimonial with quote, name, rating",
    "stat": "A numeric statistic (e.g. 200+ Doctors)",
    "cta": "Call-to-action section promoting an action",
    "blog_post": "A blog / article card",
    "job": "A job / career listing",
    "insurance_plan": "An insurance plan card with features",
    "medication": "A medication / pharmacy product listing",
    "pharmacy_service": "A pharmacy service card",
    "milestone": "A company history milestone",
    "value": "A core value / principle card",
    "faq": "FAQ item with question and answer",
    "contact_info": "Contact information (address, phone, email, hours)",
    "coverage_item": "An insurance coverage category",
    "benefit": "An employee benefit card",
    "why_choose": "A 'why choose us' selling point",
    "feature_list": "A list of features or bullet points",
    "heading": "Generic section heading (h1-h6)",
    "paragraph": "Generic text paragraph",
    "list_item": "Generic list item",
    "link": "A hyperlink with text",
}


# ──────────────────────────────────────────────
#  Semantic selectors — CSS-class → component type
#  These map the MediCare+ site's class naming
#  conventions to semantic component types.
# ──────────────────────────────────────────────

_SEMANTIC_SELECTORS: list[tuple[str, str, str]] = [
    # --- High-specificity semantic cards ---
    (".feature-card",                 "service",          "features"),
    (".service-card",                 "service",          "services_page"),
    (".doctor-card",                  "doctor",           "doctors_page"),
    (".testimonial-card",             "testimonial",      "testimonials"),
    (".stat-item",                    "stat",             "stats"),
    (".plan-card",                    "insurance_plan",   "insurance_plans"),
    (".blog-card",                    "blog_post",        "blog"),
    (".job-card",                     "job",              "jobs"),
    (".med-card",                     "medication",       "medications"),
    (".pharm-service-card",          "pharmacy_service", "pharmacy_services"),
    (".timeline__item",               "milestone",        "timeline"),
    (".value-card",                   "value",            "values"),
    (".faq__item",                    "faq",              "faqs"),
    (".contact-info-card",            "contact_info",     "contact"),
    (".coverage__card",               "coverage_item",    "coverage"),
    (".benefit-card",                 "benefit",          "benefits"),
    (".why-choose__card",             "why_choose",       "why_choose"),
    (".feature-card__link",           "link",             "features"),
    ("section.hero",                  "hero",             "hero"),
    (".cta-banner",                   "cta",              "cta"),
]

# Section/region detection by CSS class on parent containers
_SECTION_CLASSES = {
    "features__grid":  "features",
    "services-page__grid": "services_page",
    "doctors__grid":   "doctors_page",
    "testimonials__grid": "testimonials",
    "stats__grid":     "stats",
    "plans__grid":     "insurance_plans",
    "blog__grid":      "blog",
    "jobs__list":      "jobs",
    "meds__grid":      "medications",
    "pharm-services__grid": "pharmacy_services",
    "timeline":        "timeline",
    "values__grid":    "values",
    "faq__list":       "faqs",
    "coverage__grid":  "coverage",
    "benefits__grid":  "benefits",
    "why-choose__grid": "why_choose",
}


# ──────────────────────────────────────────────
#  Component data structure
# ──────────────────────────────────────────────

@dataclass
class Component:
    """A single extracted component from a page."""
    type: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata,
        }


# ──────────────────────────────────────────────
#  Parsing helpers
# ──────────────────────────────────────────────

def _get_clean_text(el, default: str = "") -> str:
    """Get stripped inner text from a BeautifulSoup element."""
    if el is None:
        return default
    return el.get_text(strip=True) or default


def _parse_service_card(card, section: str, page_url: str, page_title: str) -> Component | None:
    """Parse a service/feature card."""
    title_el = card.find(["h3", "h4"])
    title = _get_clean_text(title_el)
    if not title:
        return None
    desc_el = card.find("p")
    desc = _get_clean_text(desc_el)
    icon_el = card.find(class_=["feature-card__icon", "service-card__icon"])
    icon = _get_clean_text(icon_el)

    # Check for feature list items
    features = []
    ul = card.find("ul")
    if ul:
        features = [_get_clean_text(li) for li in ul.find_all("li") if _get_clean_text(li)]

    link_el = card.find("a")
    link = link_el.get("href", "") if link_el else ""

    attrs = {"icon": icon}
    if features:
        attrs["features"] = features
    if link:
        attrs["link"] = link

    return Component(
        type="service",
        content=title,
        metadata={
            "description": desc,
            "page_url": page_url,
            "page_title": page_title,
            "section": section,
            "attributes": attrs,
        },
    )


def _parse_doctor_card(card, section: str, page_url: str, page_title: str) -> Component | None:
    """Parse a doctor profile card."""
    name_el = card.find(class_="doctor-card__name")
    name = _get_clean_text(name_el)
    if not name:
        return None
    specialty_el = card.find(class_="doctor-card__specialty")
    exp_el = card.find(class_="doctor-card__exp")
    desc_el = card.find(class_="doctor-card__desc")

    return Component(
        type="doctor",
        content=name,
        metadata={
            "specialty": _get_clean_text(specialty_el),
            "experience": _get_clean_text(exp_el),
            "description": _get_clean_text(desc_el),
            "page_url": page_url,
            "page_title": page_title,
            "section": section,
        },
    )


def _parse_testimonial_card(card, section: str, page_url: str, page_title: str) -> Component | None:
    """Parse a testimonial card."""
    text_el = card.find(class_="testimonial-card__text")
    text = _get_clean_text(text_el)
    if not text:
        return None
    name_el = card.find(class_="testimonial-card__author")
    name = _get_clean_text(name_el) if name_el else ""
    stars_el = card.find(class_="testimonial-card__stars")
    rating = _get_clean_text(stars_el)
    role_el = card.find("small")
    role = _get_clean_text(role_el)

    return Component(
        type="testimonial",
        content=text.strip("\"'"),
        metadata={
            "name": name,
            "role": role,
            "rating": rating.count("★") if "★" in rating else 0,
            "page_url": page_url,
            "page_title": page_title,
            "section": section,
        },
    )


def _parse_stat_item(card, section: str, page_url: str, page_title: str) -> Component | None:
    """Parse a stat item."""
    value_el = card.find(class_="stat-value")
    label_el = card.find(class_="stat-label")
    value = _get_clean_text(value_el)
    if not value:
        return None
    return Component(
        type="stat",
        content=f"{value} {_get_clean_text(label_el)}",
        metadata={
            "value": value,
            "label": _get_clean_text(label_el),
            "page_url": page_url,
            "page_title": page_title,
            "section": section,
        },
    )


def _parse_plan_card(card, section: str, page_url: str, page_title: str) -> Component | None:
    """Parse an insurance plan card."""
    name_el = card.find(class_="plan-card__name")
    name = _get_clean_text(name_el)
    if not name:
        return None
    price_el = card.find(class_="plan-card__amount")
    period_el = card.find(class_="plan-card__period")
    desc_el = card.find(class_="plan-card__desc")
    features = [_get_clean_text(li) for li in card.find_all("li") if _get_clean_text(li)]
    is_popular = bool(card.find(class_="plan-card__badge"))

    return Component(
        type="insurance_plan",
        content=name,
        metadata={
            "price": _get_clean_text(price_el) + _get_clean_text(period_el),
            "description": _get_clean_text(desc_el),
            "features": features,
            "popular": is_popular,
            "page_url": page_url,
            "page_title": page_title,
            "section": section,
        },
    )


def _parse_blog_post(card, section: str, page_url: str, page_title: str) -> Component | None:
    """Parse a blog post card."""
    title_el = card.find(class_="blog-card__title")
    title = _get_clean_text(title_el)
    if not title:
        return None
    excerpt_el = card.find(class_="blog-card__excerpt")
    meta_el = card.find(class_="blog-card__meta")
    author_el = card.find(class_="blog-card__author")
    cat_el = card.find(class_="blog-card__category")
    read_time_el = card.find(class_="blog-card__meta")

    return Component(
        type="blog_post",
        content=title,
        metadata={
            "excerpt": _get_clean_text(excerpt_el),
            "author": _get_clean_text(author_el),
            "category": _get_clean_text(cat_el),
            "meta": _get_clean_text(meta_el),
            "page_url": page_url,
            "page_title": page_title,
            "section": section,
        },
    )


def _parse_job_card(card, section: str, page_url: str, page_title: str) -> Component | None:
    """Parse a job listing card."""
    title_el = card.find(class_="job-card__title")
    title = _get_clean_text(title_el)
    if not title:
        return None
    desc_el = card.find(class_="job-card__desc")
    tags = [_get_clean_text(t) for t in card.find_all(class_="job-card__tag") if _get_clean_text(t)]

    return Component(
        type="job",
        content=title,
        metadata={
            "description": _get_clean_text(desc_el),
            "tags": tags,
            "page_url": page_url,
            "page_title": page_title,
            "section": section,
        },
    )


def _parse_faq_item(card, section: str, page_url: str, page_title: str) -> Component | None:
    """Parse an FAQ item."""
    q_el = card.find(class_="faq__question")
    a_el = card.find(class_="faq__answer")
    question = _get_clean_text(q_el)
    if not q_el:
        # Try <button> inside faq__question
        btn = card.find("button")
        if btn:
            question = _get_clean_text(btn)
    answer = _get_clean_text(a_el)
    if not question:
        return None

    return Component(
        type="faq",
        content=question,
        metadata={
            "answer": answer,
            "page_url": page_url,
            "page_title": page_title,
            "section": section,
        },
    )


def _parse_medication(card, section: str, page_url: str, page_title: str) -> Component | None:
    """Parse a medication listing card."""
    name_el = card.find(class_="med-card__name")
    name = _get_clean_text(name_el)
    if not name:
        return None
    desc_el = card.find(class_="med-card__desc")
    price_el = card.find(class_="med-card__price")
    cat_el = card.find(class_="med-card__category")

    return Component(
        type="medication",
        content=name,
        metadata={
            "description": _get_clean_text(desc_el),
            "price": _get_clean_text(price_el),
            "category": _get_clean_text(cat_el),
            "page_url": page_url,
            "page_title": page_title,
            "section": section,
        },
    )


def _parse_fallback(el, page_url: str, page_title: str, section: str) -> Component | None:
    """Generic fallback: extract heading, paragraph, list_item, or link."""
    text = _get_clean_text(el)
    if not text:
        return None

    tag = el.name or ""
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return Component(
            type="heading",
            content=text,
            metadata={"level": tag, "page_url": page_url, "page_title": page_title, "section": section},
        )
    elif tag == "p":
        return Component(
            type="paragraph",
            content=text,
            metadata={"page_url": page_url, "page_title": page_title, "section": section},
        )
    elif tag == "li":
        return Component(
            type="list_item",
            content=text,
            metadata={"page_url": page_url, "page_title": page_title, "section": section},
        )
    elif tag == "a":
        href = el.get("href", "")
        if text and href and not href.startswith("#"):
            return Component(
                type="link",
                content=text,
                metadata={"href": href, "page_url": page_url, "page_title": page_title, "section": section},
            )
    return None


# ──────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────

def parse_page(html: str, url: str, title: str | None = None) -> list[dict]:
    """
    Parse rendered HTML into a list of structured components.

    Args:
        html: The full rendered HTML (from Playwright, or httpx+BeautifulSoup).
        url: The source page URL.
        title: Optional page title (extracted from HTML if not provided).

    Returns:
        List of component dicts with keys: type, content, metadata.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements first
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()

    if not title:
        title = _get_clean_text(soup.title) if soup.title else url

    components: list[Component] = []
    seen: set[tuple[str, str]] = set()  # dedup by (type, content)

    # ── Phase 1: Semantic extraction by CSS class ──
    for selector, comp_type, section in _SEMANTIC_SELECTORS:
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
            elif comp_type == "blog_post":
                comp = _parse_blog_post(el, section, url, title)
            elif comp_type == "job":
                comp = _parse_job_card(el, section, url, title)
            elif comp_type == "faq":
                comp = _parse_faq_item(el, section, url, title)
            elif comp_type == "medication":
                comp = _parse_medication(el, section, url, title)
            else:
                # Generic card: use inner text as component content
                attrs = {}
                link = el.find("a")
                if link:
                    attrs["link"] = link.get("href", "")
                comp = Component(
                    type=comp_type,
                    content=text,
                    metadata={
                        "page_url": url,
                        "page_title": title,
                        "section": section,
                        "attributes": attrs,
                        "description": _get_clean_text(el.find("p")),
                    } if el.find("p") else {
                        "page_url": url,
                        "page_title": title,
                        "section": section,
                        "attributes": attrs,
                    },
                )

            if comp:
                key = (comp.type, comp.content)
                if key not in seen:
                    components.append(comp)
                    seen.add(key)

    # ── Phase 2: Generic fallback — extract headings, paragraphs, lists ──
    main = soup.find("main") or soup.find("article") or soup.find("body") or soup
    for el in main.descendants:
        if el.name not in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "a"):
            continue
        # Skip if this element is inside a semantically extracted card
        parent_selectors = [s[0] for s in _SEMANTIC_SELECTORS]
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

    logger.info(
        "Parsed %d components from %s (%d semantic, %d generic)",
        len(components), url,
        sum(1 for c in components if c.type not in ("heading", "paragraph", "list_item", "link")),
        sum(1 for c in components if c.type in ("heading", "paragraph", "list_item", "link")),
    )

    return [c.to_dict() for c in components]


def format_components_for_llm(components: list[dict], max_chars: int = 3000) -> str:
    """
    Format a list of components into a compact, LLM-friendly context string.

    Groups components by type for clean presentation.
    Truncates to max_chars to avoid blowing up the prompt.

    Args:
        components: List of component dicts.
        max_chars: Maximum characters to include.

    Returns:
        Formatted context string.
    """
    if not components:
        return ""

    # Group by type
    grouped: dict[str, list[dict]] = {}
    for comp in components:
        t = comp.get("type", "unknown")
        grouped.setdefault(t, []).append(comp)

    lines: list[str] = []
    total = 0

    # Priority order: semantic types first, then generic
    priority = [
        "service", "doctor", "testimonial", "faq", "insurance_plan",
        "blog_post", "job", "medication", "stat", "milestone",
        "value", "hero", "contact_info", "cta",
    ]

    def add_section(type_name: str, items: list[dict]) -> int:
        """Add a section and return chars added."""
        nonlocal total
        count = 0
        label = type_name.replace("_", " ").title()
        section_lines: list[str] = [f"\n── {label} ──"]

        for item in items:
            content = item.get("content", "")
            meta = item.get("metadata", {})
            desc = meta.get("description", "")
            extras = []

            # Rich metadata per type
            if type_name == "doctor":
                extras = [
                    f"  Specialty: {meta.get('specialty', '')}",
                    f"  Experience: {meta.get('experience', '')}",
                ]
            elif type_name == "service" and meta.get("attributes", {}).get("features"):
                extras = [f"  Features: {', '.join(meta['attributes']['features'][:5])}"]
            elif type_name == "testimonial":
                extras = [
                    f"  — {meta.get('name', '')} ({meta.get('role', '')})",
                ]
            elif type_name == "faq":
                extras = [f"  Answer: {meta.get('answer', '')[:200]}"]
            elif type_name == "insurance_plan":
                extras = [f"  {meta.get('price', '')} — {meta.get('description', '')}"]
            elif type_name == "blog_post":
                extras = [f"  {meta.get('excerpt', '')[:150]}"]
            elif type_name == "job":
                extras = [f"  {meta.get('description', '')[:150]}"]
            elif type_name == "stat":
                desc_part = f" — {desc}" if desc else ""
                extras = [f" {desc_part}"]
            elif type_name == "milestone":
                extras = [f"  {meta.get('description', '')[:200]}"]

            if desc and not extras:
                extras = [f"  {desc[:200]}"]

            item_lines = [f"  • {content}"]
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

    # Add priority types
    for t in priority:
        if t in grouped:
            add_section(t, grouped[t])

    # Add remaining types
    for t, items in grouped.items():
        if t not in priority:
            if add_section(t, items) == 0:
                continue

    result = "\n".join(lines).strip()
    logger.debug("Formatted %d chars of component context from %d components", len(result), len(components))
    return result
