"""Configuration management for MataConnect data pipeline."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB Configuration
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    f"mongodb+srv://maryammyusuf1802:{MONGODB_PASSWORD}@mataconnectcluster.us9anpd.mongodb.net/?retryWrites=true&w=majority&appName=MataConnectCluster",
)
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "mataconnect")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "communities")


# Validate required environment variables
def validate_config():
    """Validate that all required environment variables are set."""
    required_vars = [
        ("MONGODB_PASSWORD", MONGODB_PASSWORD),
    ]

    missing = [var[0] for var in required_vars if not var[1]]

    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Please set them in your .env file or environment."
        )
