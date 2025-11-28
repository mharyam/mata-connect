"""
Load enriched community data from SQLite database to MongoDB.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List

from pymongo import MongoClient
from pymongo.errors import BulkWriteError

import sys
from pathlib import Path
from config import (
    MONGODB_URI,
    MONGODB_DATABASE,
    MONGODB_COLLECTION,
    validate_config,
)
from enricher.database import get_connection, DB_PATH


# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def transform_community_data(sqlite_data: Dict[str, Any], url: str) -> Dict[str, Any]:
    """
    Transform SQLite community data to MongoDB document format.

    Args:
        sqlite_data: Community data from SQLite (parsed JSON)
        url: Original URL of the community

    Returns:
        Transformed document ready for MongoDB
    """
    # Handle language - convert list to string if needed, or keep as list
    language = sqlite_data.get("language")
    if isinstance(language, list):
        # If it's a list, join with comma or take first item
        language = language[0] if language else None
    elif not language:
        language = None

    # Determine if virtual based on country/city
    is_virtual = sqlite_data.get("country") is None and sqlite_data.get("city") is None

    # Normalize pricing model to uppercase
    pricing_model = sqlite_data.get("pricing_model")
    if pricing_model:
        pricing_model = pricing_model.upper()
        if pricing_model in ["FREE", "FREEMIUM", "PAID"]:
            pass  # Keep as is
        elif "free" in pricing_model.lower():
            pricing_model = "FREE"
        else:
            pricing_model = "PAID"
    else:
        pricing_model = None

    # Get current date for timestamps
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_timestamp = datetime.now().isoformat()

    # Build MongoDB document
    mongo_doc = {
        "name": sqlite_data.get("name", ""),
        "description": sqlite_data.get("description"),
        "website": sqlite_data.get("website", url),
        "tags": sqlite_data.get("tags", []),
        "focus_areas": sqlite_data.get("focus_areas") or "",
        "country": sqlite_data.get("country"),
        "city": sqlite_data.get("city"),
        "language": language,
        "contact_email": sqlite_data.get("contact_email"),
        "is_virtual": is_virtual,
        "social_links": sqlite_data.get("social_links", {}),
        "community_info": sqlite_data.get("community_info", {}),
        "pricing_model": pricing_model,
        "topics_supported": [],
        "audience_type": [],
        "event_types": [],
        "year_founded": None,
        "verified": False,
        "embedding": [],
        "data_source": url,
        "created_at": current_date,
        "updated_at": current_date,
        "last_verified_at": current_timestamp,
        "member_count": sqlite_data.get("member_count"),
    }

    return mongo_doc


def load_sqlite_to_mongodb(db_path: str = DB_PATH, batch_size: int = 100) -> None:
    """
    Load all communities from SQLite database to MongoDB.

    Args:
        db_path: Path to SQLite database file
        batch_size: Number of documents to insert in each batch
    """
    # Validate configuration
    validate_config()

    # Connect to MongoDB
    try:
        mongo_client = MongoClient(MONGODB_URI)
        collection = mongo_client[MONGODB_DATABASE][MONGODB_COLLECTION]
        logger.info(
            f"Connected to MongoDB database: {MONGODB_DATABASE}, collection: {MONGODB_COLLECTION}"
        )
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

    # Connect to SQLite
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Get all communities from SQLite
    cursor.execute("SELECT url, enriched_data FROM communities")
    rows = cursor.fetchall()
    conn.close()

    total_communities = len(rows)
    logger.info(f"Found {total_communities} communities in SQLite database")

    if total_communities == 0:
        logger.warning("No communities found in SQLite database")
        return

    documents: List[Dict[str, Any]] = []
    processed = 0
    failed = 0

    for idx, (url, json_data) in enumerate(rows, 1):
        try:
            # Parse JSON data from SQLite
            sqlite_data = json.loads(json_data)

            # Transform to MongoDB format
            mongo_doc = transform_community_data(sqlite_data, url)
            documents.append(mongo_doc)

            # Batch insert when batch_size is reached
            if len(documents) >= batch_size:
                try:
                    result = collection.insert_many(documents)
                    processed += len(result.inserted_ids)
                    logger.info(
                        f"Inserted batch: {processed}/{total_communities} communities"
                    )
                    documents = []
                except BulkWriteError as e:
                    # Handle duplicate key errors or other bulk write errors
                    failed += len(documents) - len(e.details.get("writeErrors", []))
                    logger.warning(f"Batch insert had errors: {e.details}")
                    documents = []

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for URL {url}: {e}")
            failed += 1
        except Exception as e:
            logger.error(f"Failed to process URL {url}: {e}")
            failed += 1

    # Insert remaining documents
    if documents:
        try:
            result = collection.insert_many(documents)
            processed += len(result.inserted_ids)
            logger.info(
                f"Inserted final batch: {processed}/{total_communities} communities"
            )
        except BulkWriteError as e:
            failed += len(documents) - len(e.details.get("writeErrors", []))
            logger.warning(f"Final batch insert had errors: {e.details}")

    # Print summary
    logger.info("=" * 50)
    logger.info("📊 Loading Summary:")
    logger.info(f"   Total communities: {total_communities}")
    logger.info(f"   ✅ Successfully loaded: {processed}")
    logger.info(f"   ❌ Failed: {failed}")
    logger.info("=" * 50)

    mongo_client.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Get database path if provided
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default to communities.db in project root
        project_root = Path(__file__).parent.parent
        db_path = project_root / "communities.db"

    if not Path(db_path).exists():
        logger.error(f"SQLite database not found: {db_path}")
        sys.exit(1)

    # Load to MongoDB
    load_sqlite_to_mongodb(str(db_path))
