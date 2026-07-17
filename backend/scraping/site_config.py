"""
Site Configuration Loader.

Loads site-specific settings from sites/site_config.json and provides
a unified API for all modules to access selectors, mappings, and patterns.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.logger import get_logger

logger = get_logger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_SITES_DIR = _PROJECT_ROOT / "sites"
_DEFAULT_CONFIG = _SITES_DIR / "site_config.json"

_cache: dict[str, Any] | None = None


def load_site_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load the site configuration JSON file. Results are cached."""
    global _cache
    path = Path(config_path) if config_path else _DEFAULT_CONFIG
    if _cache is not None:
        return _cache
    if not path.exists():
        logger.warning("Site config not found at %s - using empty defaults", path)
        _cache = {}
        return _cache
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache = data
        return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to load site config from %s: %s", path, exc)
        _cache = {}
        return _cache


def reload_site_config() -> dict[str, Any]:
    """Force reload the site configuration."""
    global _cache
    _cache = None
    return load_site_config()


def get_semantic_selectors() -> list[tuple[str, str, str]]:
    """Get semantic selectors as (selector, component_type, section) tuples."""
    config = load_site_config()
    raw = config.get("semantic_selectors", {})
    result = []
    for selector, info in raw.items():
        if isinstance(info, dict):
            comp_type = info.get("type", "unknown")
            section = info.get("section", "main")
        else:
            comp_type = str(info)
            section = "main"
        result.append((selector, comp_type, section))
    return result


def get_section_classes() -> dict[str, str]:
    """Get section/region detection classes."""
    config = load_site_config()
    return config.get("section_classes", {})


def get_page_mappings() -> dict[str, str]:
    """Get keyword to URL path mappings."""
    config = load_site_config()
    return config.get("page_mappings", {})


def get_scrollable_sections() -> dict[str, str]:
    """Get scrollable section selectors with display names."""
    config = load_site_config()
    return config.get("scrollable_sections", {})


def get_action_buttons() -> dict[str, str]:
    """Get named action button selectors."""
    config = load_site_config()
    return config.get("action_buttons", {})


def get_form_params() -> dict[str, str]:
    """Get form field name to CSS selector mappings."""
    config = load_site_config()
    return config.get("form_params", {})


def get_component_parsers() -> dict[str, Any]:
    """Get component parser field selectors."""
    config = load_site_config()
    return config.get("component_parsers", {})


def get_navigation_patterns() -> dict[str, list[str]]:
    """Get navigation pattern categorization."""
    config = load_site_config()
    return config.get("navigation_patterns", {})


def get_site_name() -> str:
    """Get the site name for the system prompt."""
    config = load_site_config()
    return config.get("name", "[Site Name]")


def get_base_url() -> str:
    """Get the base URL of the site."""
    config = load_site_config()
    return config.get("base_url", "http://localhost:5174")
