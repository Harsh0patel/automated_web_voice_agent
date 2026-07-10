"""
MongoDB connection manager for storing and searching scraped website data.
"""
from motor.motor_asyncio import AsyncIOMotorClient

from backend.core import config as cfg
from backend.core.logger import get_logger

logger = get_logger(__name__)

# Global client instance
_client: AsyncIOMotorClient | None = None


def _get_client() -> AsyncIOMotorClient:
    """Get or create the MongoDB client singleton."""
    global _client
    if _client is None:
        mongo_uri = cfg.MONGO_URI
        if not mongo_uri:
            logger.error("MONGO_URI not set")
            raise ValueError(
                "MONGO_URI is not set. "
                "Set the MONGO_URI environment variable (e.g. mongodb://localhost:27017)."
            )
        _client = AsyncIOMotorClient(mongo_uri)
        # Safely log URI without exposing credentials
        if "@" in mongo_uri:
            _, host = mongo_uri.split("@", 1)
            safe_uri = f"mongodb://***@{host}"
        else:
            safe_uri = mongo_uri
        logger.info("MongoDB client created — %s", safe_uri)
    return _client


def get_db():
    """Get the scraped-data database."""
    client = _get_client()
    return client.scraped_data


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
    result = await db.pages.delete_many({})
    logger.warning("Deleted %d pages from DB", result.deleted_count)
    return result.deleted_count


async def ping() -> bool:
    """Check if MongoDB is reachable."""
    try:
        client = _get_client()
        await client.admin.command("ping")
        logger.debug("MongoDB ping successful")
        return True
    except Exception as e:
        logger.warning("MongoDB ping failed: %s", e)
        return False


async def close():
    """Close the MongoDB connection."""
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")
        _client = None
