"""
Process community URLs from CSV file and enrich them using OpenAI enricher.
Stores results in SQLite database, skipping URLs that already exist.
"""

import os
import sys
import csv
from pathlib import Path
from openai_enricher import OpenAIEnricher
from database import init_database, url_exists, save_community_data, DB_PATH


def read_urls_from_csv(csv_path: str) -> list[str]:
    """
    Read URLs from CSV file.

    Args:
        csv_path: Path to the CSV file

    Returns:
        List of cleaned URLs
    """
    urls = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0].strip():
                # Clean URL - remove trailing comma and any notes
                url = row[0].strip().rstrip(",")
                # Remove any notes after comma (like "keep an eye - not free")
                if "," in url:
                    url = url.split(",")[0].strip()
                if url:
                    urls.append(url)

    return urls


def process_communities(csv_path: str, db_path: str = DB_PATH) -> None:
    """
    Process all URLs from CSV file, enrich them, and store in database.

    Args:
        csv_path: Path to the CSV file containing URLs
        db_path: Path to the SQLite database file
    """
    # Initialize database
    init_database(db_path)

    # Read URLs from CSV
    print(f"📖 Reading URLs from {csv_path}...")
    urls = read_urls_from_csv(csv_path)
    print(f"✅ Found {len(urls)} URLs to process\n")

    # Initialize enricher
    try:
        enricher = OpenAIEnricher()
    except ValueError as e:
        print(f"❌ Error initializing enricher: {e}")
        sys.exit(1)

    # Process each URL
    total = len(urls)
    processed = 0
    skipped = 0
    failed = 0

    for idx, url in enumerate(urls, 1):
        print(f"\n[{idx}/{total}] Processing: {url}")

        # Check if URL already exists
        if url_exists(db_path, url):
            print("⏭️  URL already exists in database, skipping...")
            skipped += 1
            continue

        # Enrich the community
        try:
            print("🔄 Enriching community data...")
            enriched_data = enricher.enrich_community(url)

            # Save to database
            save_community_data(db_path, url, enriched_data)
            print("✅ Successfully enriched and saved to database")
            processed += 1

        except Exception as e:
            print(f"❌ Failed to process {url}: {e}")
            failed += 1
            continue

    # Print summary
    print("\n" + "=" * 50)
    print("📊 Processing Summary:")
    print(f"   Total URLs: {total}")
    print(f"   ✅ Processed: {processed}")
    print(f"   ⏭️  Skipped (already in DB): {skipped}")
    print(f"   ❌ Failed: {failed}")
    print("=" * 50)


if __name__ == "__main__":
    # Get CSV file path
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        # Default to data/mata_connect.csv relative to project root
        project_root = Path(__file__).parent.parent
        csv_path = project_root / "data" / "mata_connect.csv"

    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        sys.exit(1)

    # Process communities
    process_communities(str(csv_path))
