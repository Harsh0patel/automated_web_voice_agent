"""
MongoDB connection manager for storing and searching scraped website data.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

from backend.core import config as cfg
from backend.core.logger import get_logger

logger = get_logger(__name__)

# Global client instance
_client: AsyncIOMotorClient | None = None


def _get_client() -> AsyncIOMotorClient | None:
    """Get or create the MongoDB client singleton. Returns None if unavailable."""
    global _client
    if _client is None:
        mongo_uri = cfg.MONGO_URI
        if not mongo_uri:
            logger.error("MONGO_URI not set — DB features disabled")
            return None
        try:
            _client = AsyncIOMotorClient(
                mongo_uri,
                serverSelectionTimeoutMS=3000,  # fail fast if Mongo is down
                connectTimeoutMS=3000,
            )
            # Safely log URI without exposing credentials
            if "@" in mongo_uri:
                _, host = mongo_uri.split("@", 1)
                safe_uri = f"mongodb://***@{host}"
            else:
                safe_uri = mongo_uri
            logger.info("MongoDB client created — %s", safe_uri)
        except Exception as exc:
            logger.error("Failed to create MongoDB client: %s", exc)
            _client = None
            return None
    return _client


def get_db():
    """Get the scraped-data database. Returns None if MongoDB is unavailable."""
    client = _get_client()
    if client is None:
        return None
    return client.scraped_data


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


async def store_page(url: str, title: str, content: str, metadata: dict | None = None) -> str:
    """
    Store a scraped page in MongoDB.

    Args:
        url: The page URL.
        title: The page title.
        content: The extracted text/markdown content.
        metadata: Optional dict with additional page metadata.

    Returns:
        The inserted document ID as a string.
    """
    db = get_db()
    if db is None:
        logger.warning("MongoDB unavailable — cannot store page '%s'", url)
        raise ConnectionError("MongoDB is not available")

    doc = {
        "url": url,
        "title": title,
        "content": content,
        "metadata": metadata or {},
    }
    result = await db.pages.insert_one(doc)
    doc_id = str(result.inserted_id)
    logger.info("Stored page '%s' (%s) — id=%s, content=%d chars", title, url, doc_id, len(content))

    # Create a text index for full-text search (if not exists)
    try:
        await db.pages.create_index([("content", "text"), ("title", "text")])
        logger.debug("Text index ensured on pages collection")
    except Exception:
        pass

    return doc_id


async def search_pages(query: str, limit: int = 5) -> list[dict]:
    """
    Search scraped pages by text content.

    Uses MongoDB text search to find relevant pages.

    Args:
        query: The search query string.
        limit: Maximum number of results.

    Returns:
        List of matching documents with url, title, content, and relevance score.
    """
    db = get_db()
    if db is None:
        logger.info("MongoDB unavailable — skipping DB search")
        return []

    logger.debug("Searching pages for: %.80s", query)

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

    logger.info("DB search for '%.60s' returned %d results", query, len(results))
    return results


async def get_all_pages(limit: int = 20) -> list[dict]:
    """Get all stored pages (for listing)."""
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
    logger.debug("Listed %d pages from DB", len(results))
    return results


async def delete_all_pages():
    """Delete all stored pages (for testing/cleanup)."""
    db = get_db()
    if db is None:
        return 0
    result = await db.pages.delete_many({})
    logger.warning("Deleted %d pages from DB", result.deleted_count)
    return result.deleted_count


async def ping() -> bool:
    """Check if MongoDB is reachable."""
    client = _get_client()
    if client is None:
        return False
    try:
        await client.admin.command("ping")
        logger.debug("MongoDB ping successful")
        return True
    except Exception as e:
        logger.warning("MongoDB ping failed: %s", e)
        return False


# ──────────────────────────────────────────────
#  Component Registry Functions
# ──────────────────────────────────────────────

async def store_components(
    source_url: str,
    source_title: str,
    components: list[dict],
) -> int:
    """
    Store typed components from a scraped page.

    Deletes any existing components for the same source_url first,
    then bulk-inserts the new ones.

    Args:
        source_url: The page URL these components came from.
        source_title: The page title.
        components: List of component dicts (type, content, metadata).

    Returns:
        Number of components stored.
    """
    db = get_db()
    if db is None:
        raise ConnectionError("MongoDB is not available")

    # Remove old components for this page
    await db.components.delete_many({"metadata.page_url": source_url})

    if not components:
        return 0

    timestamp = _now()
    docs: list[dict[str, Any]] = []
    for comp in components:
        doc = {
            "type": comp.get("type", "unknown"),
            "content": comp.get("content", ""),
            "metadata": {
                **(comp.get("metadata", {})),
                "page_url": source_url,
                "page_title": source_title,
            },
            "created_at": timestamp,
        }
        docs.append(doc)

    result = await db.components.insert_many(docs, ordered=False)

    # Ensure indexes exist (best-effort)
    try:
        await db.components.create_index([("type", 1)])
        await db.components.create_index([("content", "text"), ("metadata.page_title", "text")])
        await db.components.create_index([("metadata.page_url", 1)])
        await db.components.create_index([("created_at", -1)])
    except Exception:
        pass

    logger.info(
        "Stored %d / %d components from '%s' (%s)",
        len(result.inserted_ids), len(components), source_title, source_url,
    )
    return len(result.inserted_ids)


async def search_components(
    query: str,
    component_type: str | None = None,
    limit: int = 15,
) -> list[dict]:
    """
    Search components by text content, optionally filtered by type.

    Args:
        query: The search query.
        component_type: Optional type filter (e.g. "doctor", "service", "faq").
        limit: Max results.

    Returns:
        List of matching component dicts.
    """
    db = get_db()
    if db is None:
        logger.info("MongoDB unavailable — skipping component search")
        return []

    logger.debug("Searching components for: %.80s (type=%s)", query, component_type)

    # Build the query filter
    text_filter = {"$text": {"$search": query}} if query.strip() else {}
    type_filter = {"type": component_type} if component_type else {}

    # Combine filters: use $and if both present
    if text_filter and type_filter:
        db_filter: dict = {"$and": [text_filter, type_filter]}
    elif text_filter:
        db_filter = text_filter
    elif type_filter:
        db_filter = type_filter
    else:
        db_filter = {}

    cursor = db.components.find(
        db_filter,
        {
            "score": {"$meta": "textScore"} if query.strip() else 0,
        },
    )

    # Sort by relevance if searching by text
    if query.strip():
        cursor = cursor.sort([("score", {"$meta": "textScore"})])
    else:
        cursor = cursor.sort([("created_at", -1)])

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

    logger.info(
        "Component search '%.60s' (type=%s) returned %d results",
        query, component_type, len(results),
    )
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


async def get_all_components(limit: int = 50) -> list[dict]:
    """Get all components (for listing)."""
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
            "metadata": {
                "page_title": doc.get("metadata", {}).get("page_title", ""),
                "page_url": doc.get("metadata", {}).get("page_url", ""),
                "section": doc.get("metadata", {}).get("section", ""),
            },
        })
    logger.debug("Listed %d components from DB", len(results))
    return results


async def delete_all_components() -> int:
    """Delete all stored components."""
    db = get_db()
    if db is None:
        return 0
    result = await db.components.delete_many({})
    logger.warning("Deleted %d components from DB", result.deleted_count)
    return result.deleted_count


async def close():
    """Close the MongoDB connection."""
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")
        _client = None
