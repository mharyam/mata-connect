"""
Database handler for storing enriched community data.
"""

import sqlite3
from openai_enricher import CommunityInfo


# Default database file path
DB_PATH = "communities.db"


def init_database(db_path: str = DB_PATH) -> None:
    """
    Initialize SQLite database with communities table.

    Args:
        db_path: Path to the SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS communities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            enriched_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Create index on URL for faster lookups
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_url ON communities(url)
    """
    )

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {db_path}")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Get a database connection.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        SQLite connection object
    """
    return sqlite3.connect(db_path)


def url_exists(db_path: str, url: str) -> bool:
    """
    Check if URL already exists in the database.

    Args:
        db_path: Path to the SQLite database file
        url: URL to check

    Returns:
        True if URL exists, False otherwise
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM communities WHERE url = ?", (url,))
    count = cursor.fetchone()[0]

    conn.close()
    return count > 0


def save_community_data(db_path: str, url: str, enriched_data: CommunityInfo) -> None:
    """
    Save enriched community data to the database.

    Args:
        db_path: Path to the SQLite database file
        url: URL of the community
        enriched_data: Enriched community data as CommunityInfo object
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Convert CommunityInfo to JSON string
    json_data = enriched_data.model_dump_json(indent=2)

    cursor.execute(
        """
        INSERT OR REPLACE INTO communities (url, enriched_data, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """,
        (url, json_data),
    )

    conn.commit()
    conn.close()


def get_community_data(db_path: str, url: str) -> str | None:
    """
    Retrieve enriched community data from the database.

    Args:
        db_path: Path to the SQLite database file
        url: URL of the community

    Returns:
        JSON string of enriched data, or None if not found
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT enriched_data FROM communities WHERE url = ?", (url,))
    result = cursor.fetchone()

    conn.close()
    return result[0] if result else None


def get_all_urls(db_path: str = DB_PATH) -> list[str]:
    """
    Get all URLs stored in the database.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        List of URLs
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT url FROM communities")
    urls = [row[0] for row in cursor.fetchall()]

    conn.close()
    return urls
