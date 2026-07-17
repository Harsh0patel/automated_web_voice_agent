"""
MongoDB connection manager for storing and searching scraped website data.

All query limits have been increased significantly from their original values
to ensure no data is truncated unnecessarily.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

from backend.app import config as cfg
from backend.app.logger import get_logger

logger = get_logger(__name__)

_client: AsyncIOMotorClient | None = None


def _get_client() -> AsyncIOMotorClient | None:
    """Get or create the MongoDB client singleton."""
    global _client
    if _client is None:
        mongo_uri = cfg.MONGO_URI
        if not mongo_uri:
            logger.error("MONGO_URI not set - DB features disabled")
            return None
        try:
            _client = AsyncIOMotorClient(
                mongo_uri,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
            )
            if "@" in mongo_uri:
                _, host = mongo_uri.split("@", 1)
                safe_uri = f"mongodb://***@{host}"
            else:
                safe_uri = mongo_uri
            logger.info("MongoDB client created - %s", safe_uri)
        except Exception as exc:
            logger.error("Failed to create MongoDB client: %s", exc)
            _client = None
    return _client


def get_db():
    """Get the scraped-data database."""
    client = _get_client()
    if client is None:
        return None
    _ensure_db(client)
    return client.scraped_data


def _ensure_db(client):
    """Ensure the database connection is alive (best-effort ping)."""
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(client.admin.command("ping"))
    except Exception:
        pass


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


async def store_page(url: str, title: str, content: str, metadata: dict | None = None) -> str:
    """Store a scraped page in MongoDB."""
    db = get_db()
    if db is None:
        raise ConnectionError("MongoDB is not available")

    doc = {"url": url, "title": title, "content": content, "metadata": metadata or {}}
    result = await db.pages.insert_one(doc)
    doc_id = str(result.inserted_id)
    logger.info("Stored page '%s' (%s) - id=%s, content=%d chars", title, url, doc_id, len(content))

    try:
        await db.pages.create_index([("content", "text"), ("title", "text")])
    except Exception:
        pass

    return doc_id


async def search_pages(query: str, limit: int = 50) -> list[dict]:
    """Search scraped pages by text content. Increased default limit from 5 to 50."""
    db = get_db()
    if db is None:
        return []

    cursor = db.pages.find(
        {"$text": {"$search": query}},
        {"score": {"$meta": "textScore"}, "url": 1, "title": 1, "content": 1},
    ).sort([("score", {"$meta": "textScore"})]).limit(limit)

    results = []
    async for doc in cursor:
        results.append({
            "id": str(doc["_id"]),
            "url": doc.get("url", ""),
            "title": doc.get("title", ""),
            "content": doc.get("content", ""),
            "score": doc.get("score", 0),
        })

    logger.debug("DB search for '%.60s' returned %d results", query, len(results))
    return results


async def get_all_pages(limit: int = 200) -> list[dict]:
    """Get all stored pages. Increased default limit from 20 to 200."""
    db = get_db()
    if db is None:
        return []
    cursor = db.pages.find().limit(limit)
    results = []
    async for doc in cursor:
        results.append({
            "id": str(doc["_id"]),
            "url": doc.get("url", ""),
            "title": doc.get("title", ""),
            "content_preview": doc.get("content", "")[:200],
        })
    return results


async def delete_all_pages():
    """Delete all stored pages."""
    db = get_db()
    if db is None:
        return 0
    result = await db.pages.delete_many({})
    return result.deleted_count


async def ping() -> bool:
    """Check if MongoDB is reachable."""
    client = _get_client()
    if client is None:
        return False
    try:
        await client.admin.command("ping")
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Component Registry Functions
# ---------------------------------------------------------------------------

async def store_components(source_url: str, source_title: str, components: list[dict]) -> int:
    """Store typed components from a scraped page."""
    db = get_db()
    if db is None:
        raise ConnectionError("MongoDB is not available")

    await db.components.delete_many({"metadata.page_url": source_url})
    if not components:
        return 0

    timestamp = _now()
    docs = []
    for comp in components:
        docs.append({
            "type": comp.get("type", "unknown"),
            "content": comp.get("content", ""),
            "metadata": {**(comp.get("metadata", {})), "page_url": source_url, "page_title": source_title},
            "created_at": timestamp,
        })

    result = await db.components.insert_many(docs, ordered=False)
    try:
        await db.components.create_index([("type", 1)])
        await db.components.create_index([("content", "text"), ("metadata.page_title", "text")])
        await db.components.create_index([("metadata.page_url", 1)])
        await db.components.create_index([("created_at", -1)])
    except Exception:
        pass

    return len(result.inserted_ids)


async def search_components(query: str, component_type: str | None = None, limit: int = 100) -> list[dict]:
    """Search components by text content. Increased default limit from 15 to 100."""
    db = get_db()
    if db is None:
        return []

    text_filter = {"$text": {"$search": query}} if query.strip() else {}
    type_filter = {"type": component_type} if component_type else {}

    if text_filter and type_filter:
        db_filter = {"$and": [text_filter, type_filter]}
    elif text_filter:
        db_filter = text_filter
    elif type_filter:
        db_filter = type_filter
    else:
        db_filter = {}

    cursor = db.components.find(
        db_filter,
        {"score": {"$meta": "textScore"} if query.strip() else 0},
    )
    cursor = cursor.sort([("score", {"$meta": "textScore"})] if query.strip() else [("created_at", -1)])
    cursor = cursor.limit(limit)

    results = []
    async for doc in cursor:
        results.append({
            "id": str(doc["_id"]),
            "type": doc.get("type", "unknown"),
            "content": doc.get("content", ""),
            "metadata": doc.get("metadata", {}),
            "score": doc.get("score", 0),
        })
    return results


async def get_component_types() -> list[str]:
    """Get all distinct component types stored in the registry."""
    db = get_db()
    if db is None:
        return []
    return await db.components.distinct("type")


async def get_components_by_source(source_url: str) -> list[dict]:
    """Get all components from a specific source page."""
    db = get_db()
    if db is None:
        return []
    cursor = db.components.find({"metadata.page_url": source_url})
    results = []
    async for doc in cursor:
        results.append({
            "id": str(doc["_id"]),
            "type": doc.get("type", "unknown"),
            "content": doc.get("content", ""),
            "metadata": doc.get("metadata", {}),
        })
    return results


async def get_all_components(limit: int = 500) -> list[dict]:
    """Get all components. Increased default limit from 50 to 500."""
    db = get_db()
    if db is None:
        return []
    cursor = db.components.find().sort("created_at", -1).limit(limit)
    results = []
    async for doc in cursor:
        results.append({
            "id": str(doc["_id"]),
            "type": doc.get("type", "unknown"),
            "content": doc.get("content", ""),
            "metadata": doc.get("metadata", {}),
        })
    return results


async def delete_all_components() -> int:
    """Delete all stored components."""
    db = get_db()
    if db is None:
        return 0
    result = await db.components.delete_many({})
    return result.deleted_count


# ---------------------------------------------------------------------------
# Page Analysis Functions
# ---------------------------------------------------------------------------

async def store_page_analysis(
    url: str,
    page_category: str = "info_page",
    scroll_sections: list[dict] | None = None,
    form_fields: list[dict] | None = None,
) -> str | None:
    """Store page analysis data."""
    db = get_db()
    if db is None:
        return None

    doc = {
        "url": url,
        "page_category": page_category,
        "scroll_sections": scroll_sections or [],
        "form_fields": form_fields or [],
        "updated_at": _now(),
    }
    result = await db.page_analysis.replace_one({"url": url}, doc, upsert=True)
    try:
        await db.page_analysis.create_index([("url", 1)], unique=True)
        await db.page_analysis.create_index([("page_category", 1)])
    except Exception:
        pass
    return str(result.upserted_id) if result.upserted_id else None


async def get_page_analysis(url: str) -> dict | None:
    """Get analysis data for a specific page."""
    db = get_db()
    if db is None:
        return None
    doc = await db.page_analysis.find_one({"url": url})
    if doc:
        return {
            "url": doc.get("url", ""),
            "page_category": doc.get("page_category", "info_page"),
            "scroll_sections": doc.get("scroll_sections", []),
            "form_fields": doc.get("form_fields", []),
        }
    return None


async def get_all_scroll_targets() -> list[dict]:
    """Get all scrollable sections across all pages."""
    db = get_db()
    if db is None:
        return []
    cursor = db.page_analysis.find({}, {"url": 1, "scroll_sections": 1, "_id": 0})
    results = []
    async for doc in cursor:
        for section in doc.get("scroll_sections", []):
            results.append({
                "page_url": doc.get("url", ""),
                "selector": section.get("selector", ""),
                "label": section.get("label", ""),
            })
    return results


async def delete_all_page_analysis() -> int:
    """Delete all page analysis data."""
    db = get_db()
    if db is None:
        return 0
    result = await db.page_analysis.delete_many({})
    return result.deleted_count


async def close():
    """Close the MongoDB connection."""
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")
        _client = None
