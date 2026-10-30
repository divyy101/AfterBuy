"""
AfterBuy – Database Connection Module
=======================================

Provides a reusable MongoDB connection to Google Cloud
Firestore (MongoDB-compatible) for the AfterBuy system.

Connection string is read from the FIRESTORE_MONGO_URI
environment variable. Credentials are NEVER hardcoded.

Usage:
    from database import get_database, test_connection

    db = get_database()
    collection = db["products"]
    docs = list(collection.find())
"""

import os
import sys

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Automatically load .env file from the project root if present
_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_env_path = os.path.join(_root_dir, ".env")
if os.path.exists(_env_path):
    load_dotenv(_env_path)


# ============================================================
# CONFIGURATION
# ============================================================

# Name of the environment variable holding the connection string
ENV_VAR_NAME = "FIRESTORE_MONGO_URI"

# Connection timeout in milliseconds
CONNECT_TIMEOUT_MS = 10000

# Server selection timeout in milliseconds
SERVER_SELECTION_TIMEOUT_MS = 10000

# ============================================================
# MODULE-LEVEL CONNECTION (singleton pattern)
# ============================================================

# Keeps a single client instance alive for the process lifetime.
# This avoids creating a new connection for every database call.
_client = None
_database = None


# ============================================================
# CONNECTION FUNCTIONS
# ============================================================

def _get_connection_string():
    """
    Read the MongoDB connection string from the environment.

    Returns:
        str: The connection string.

    Raises:
        EnvironmentError: If the environment variable is not set.
    """
    uri = os.environ.get(ENV_VAR_NAME)

    if not uri:
        raise EnvironmentError(
            f"Environment variable '{ENV_VAR_NAME}' is not set.\n"
            f"Set it with your Firestore MongoDB-compatible connection string.\n"
            f"\n"
            f"  Windows (PowerShell):\n"
            f"    $env:{ENV_VAR_NAME} = 'your-connection-string'\n"
            f"\n"
            f"  Linux / macOS:\n"
            f"    export {ENV_VAR_NAME}='your-connection-string'\n"
        )

    return uri


def get_client():
    """
    Get or create a singleton MongoClient instance.

    The client connects to the Firestore MongoDB-compatible
    endpoint using the URI from the environment variable.

    Returns:
        MongoClient: A connected MongoDB client instance.
    """
    global _client

    if _client is not None:
        return _client

    uri = _get_connection_string()

    _client = MongoClient(
        uri,
        connectTimeoutMS=CONNECT_TIMEOUT_MS,
        serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_MS,
    )

    return _client


def get_database():
    """
    Get the default database from the connection string.

    Firestore with MongoDB compatibility uses the default
    database specified in the connection URI. This function
    returns that database handle.

    Returns:
        Database: A pymongo Database object.
    """
    global _database

    if _database is not None:
        return _database

    client = get_client()

    # Use the default database from the connection string.
    # In Firestore MongoDB-compatible mode, the URI points
    # to the default database automatically.
    _database = client.get_default_database()

    return _database


def close_connection():
    """
    Close the MongoDB client connection.

    Call this when the application is shutting down
    or when you no longer need the database connection.
    """
    global _client, _database

    if _client is not None:
        _client.close()
        _client = None
        _database = None
        print("Database connection closed.")


# ============================================================
# CONNECTION TEST
# ============================================================

def test_connection():
    """
    Test the database connection by sending a ping command.

    Returns:
        bool: True if the connection is successful, False otherwise.
    """
    try:
        client = get_client()
        # The 'ping' command is a lightweight way to test connectivity
        client.admin.command("ping")
        print("[OK] Database connection successful.")
        return True

    except EnvironmentError as e:
        print(f"[ERROR] Configuration error:\n{e}")
        return False

    except ServerSelectionTimeoutError:
        print(
            "[ERROR] Could not connect to the database.\n"
            "  Possible causes:\n"
            "  - Connection string is incorrect\n"
            "  - Network/firewall is blocking the connection\n"
            "  - Firestore service is unavailable"
        )
        return False

    except ConnectionFailure as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False


def get_collection_names():
    """
    List all collection names in the database.

    Returns:
        list: A list of collection name strings.
    """
    db = get_database()
    return db.list_collection_names()


def get_collection_count(collection_name):
    """
    Get the number of documents in a collection.

    Args:
        collection_name (str): Name of the collection.

    Returns:
        int: Number of documents in the collection.
    """
    db = get_database()
    return db[collection_name].count_documents({})


# ============================================================
# MAIN – Run connection test when executed directly
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("AfterBuy - Database Connection Test")
    print("=" * 50)
    print()

    success = test_connection()

    if success:
        print()
        # List existing collections
        try:
            collections = get_collection_names()
            if collections:
                print(f"Collections found ({len(collections)}):")
                for name in sorted(collections):
                    count = get_collection_count(name)
                    print(f"  - {name}: {count} documents")
            else:
                print("No collections found (database is empty).")
        except Exception as e:
            print(f"Could not list collections: {e}")

        close_connection()
    else:
        sys.exit(1)
