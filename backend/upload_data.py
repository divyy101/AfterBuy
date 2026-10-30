"""
AfterBuy – CSV to Database Upload Script
==========================================

Reads the five CSV datasets from the data/ directory and
uploads them into separate MongoDB collections in Firestore.

Collections created:
    - products         (from products.csv)
    - sales            (from sales.csv)
    - warranty_claims  (from warranty_claims.csv)
    - repairs          (from repairs.csv)
    - defects          (from defects.csv)

Duplicate Prevention:
    Before uploading, the script checks if each collection
    already has documents. If a collection is non-empty, it
    is skipped to prevent duplicate uploads. Use --force to
    drop and re-upload all collections.

Usage:
    python backend/upload_data.py            # Safe upload (skips existing)
    python backend/upload_data.py --force    # Drop and re-upload all
    python backend/upload_data.py --test     # Test connection only

Prerequisites:
    Set the FIRESTORE_MONGO_URI environment variable:
        $env:FIRESTORE_MONGO_URI = 'your-connection-string'
"""

import os
import sys
import argparse
from datetime import datetime

import pandas as pd

# Add the backend directory to the path so we can import database.py
sys.path.insert(0, os.path.dirname(__file__))

from database import get_database, test_connection, close_connection


# ============================================================
# CONFIGURATION
# ============================================================

# Path to the data directory (relative to the project root)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Mapping: CSV filename -> MongoDB collection name
CSV_TO_COLLECTION = {
    "products.csv":         "products",
    "sales.csv":            "sales",
    "warranty_claims.csv":  "warranty_claims",
    "repairs.csv":          "repairs",
    "defects.csv":          "defects",
}

# Primary key column for each collection (used for reference)
PRIMARY_KEYS = {
    "products":         "product_id",
    "sales":            "sale_id",
    "warranty_claims":  "claim_id",
    "repairs":          "repair_id",
    "defects":          "defect_id",
}

# Date columns that should be stored as proper date types
DATE_COLUMNS = {
    "products":         ["launch_date"],
    "sales":            ["purchase_date"],
    "warranty_claims":  ["claim_date"],
    "repairs":          ["repair_date"],
    "defects":          ["defect_date"],
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_csv(filename):
    """
    Load a CSV file from the data directory.

    Args:
        filename (str): Name of the CSV file.

    Returns:
        pd.DataFrame: The loaded dataframe, or None if file not found.
    """
    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        print(f"  [ERROR] File not found: {filepath}")
        return None

    # keep_default_na=False preserves "N/A" strings as literal values
    # (used in defects.csv for unlinked claim_id entries)
    df = pd.read_csv(filepath, keep_default_na=False)
    return df


def prepare_documents(df, collection_name):
    """
    Convert a DataFrame into a list of dictionaries ready
    for MongoDB insertion.

    - Converts date string columns to Python datetime objects
      so they are stored as proper BSON Date types in MongoDB.
    - Converts numpy int64/float64 to native Python types
      for clean BSON serialization.

    Args:
        df (pd.DataFrame): The source dataframe.
        collection_name (str): Name of the target collection.

    Returns:
        list[dict]: List of documents ready for insertion.
    """
    # Convert date columns to datetime objects
    date_cols = DATE_COLUMNS.get(collection_name, [])
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])

    # Convert the dataframe to a list of dictionaries
    documents = df.to_dict(orient="records")

    # Convert numpy types to native Python types
    cleaned_documents = []
    for doc in documents:
        cleaned = {}
        for key, value in doc.items():
            # Convert numpy integers to Python int
            if hasattr(value, "item"):
                cleaned[key] = value.item()
            # Convert pandas Timestamp to Python datetime
            elif isinstance(value, pd.Timestamp):
                cleaned[key] = value.to_pydatetime()
            else:
                cleaned[key] = value
        cleaned_documents.append(cleaned)

    return cleaned_documents


# ============================================================
# UPLOAD FUNCTIONS
# ============================================================

def upload_collection(db, csv_filename, collection_name):
    """
    Upload a single CSV file into a MongoDB collection with duplicate prevention.

    Checks primary key IDs against existing records in the collection:
    - If all records exist, skips insertion safely without error.
    - If new records exist, inserts only the missing ones.
    - Preserves all existing records (never drops or deletes).

    Args:
        db: The pymongo Database instance.
        csv_filename (str): Name of the CSV file to upload.
        collection_name (str): Target collection name.

    Returns:
        tuple[bool, int, int]: (success, newly_inserted_count, total_count)
    """
    collection = db[collection_name]
    pk_col = PRIMARY_KEYS.get(collection_name)

    # --- Load CSV ---
    df = load_csv(csv_filename)
    if df is None:
        return False, 0, 0

    # --- Prepare documents ---
    documents = prepare_documents(df, collection_name)
    total_csv_records = len(documents)

    if total_csv_records == 0:
        print(f"  [WARN] '{csv_filename}' is empty. Nothing to upload.")
        return True, 0, 0

    # --- Duplicate Prevention Check ---
    try:
        # Retrieve set of existing primary keys from collection
        existing_ids = set()
        if pk_col:
            cursor = collection.find({}, {pk_col: 1, "_id": 0})
            existing_ids = {doc[pk_col] for doc in cursor if pk_col in doc}

        # Filter out records that are already present in the collection
        new_documents = [
            doc for doc in documents
            if doc.get(pk_col) not in existing_ids
        ]

        if len(new_documents) == 0:
            existing_count = collection.count_documents({})
            print(f"  [EXISTS] '{collection_name}': All {total_csv_records} records "
                  f"already exist in database (no duplicates added).")
            return True, 0, existing_count

        # Insert only missing/new records
        result = collection.insert_many(new_documents)
        newly_inserted = len(result.inserted_ids)
        total_count = collection.count_documents({})
        print(f"  [OK] '{collection_name}': {newly_inserted} new documents uploaded "
              f"({total_count} total in collection).")
        return True, newly_inserted, total_count

    except Exception as e:
        print(f"  [ERROR] Failed to upload '{collection_name}': {e}")
        return False, 0, collection.count_documents({})


def create_indexes(db):
    """
    Create indexes on primary key columns for faster lookups.

    These indexes improve query performance when filtering
    or joining by ID fields.

    Args:
        db: The pymongo Database instance.
    """
    print()
    print("Creating indexes...")

    for collection_name, pk_column in PRIMARY_KEYS.items():
        try:
            db[collection_name].create_index(pk_column, unique=True)
            print(f"  [OK] Index on '{collection_name}.{pk_column}'")
        except Exception as e:
            print(f"  [WARN] Could not create index on "
                  f"'{collection_name}.{pk_column}': {e}")


def verify_upload(db):
    """
    Verify the upload by counting documents in each collection.

    Args:
        db: The pymongo Database instance.
    """
    print()
    print("Verifying upload...")

    total = 0
    for collection_name in CSV_TO_COLLECTION.values():
        count = db[collection_name].count_documents({})
        print(f"  {collection_name}: {count} documents")
        total += count

    print(f"  Total: {total} documents across "
          f"{len(CSV_TO_COLLECTION)} collections")

    return total


# ============================================================
# MAIN
# ============================================================

def main():
    """Parse arguments and run the upload process."""

    # --- Parse command-line arguments ---
    parser = argparse.ArgumentParser(
        description="Upload AfterBuy CSV data to Firestore (MongoDB)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Drop existing collections and re-upload all data"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test the database connection only (no upload)"
    )
    args = parser.parse_args()

    # --- Header ---
    print("=" * 55)
    print("AfterBuy - CSV to Database Upload")
    print("=" * 55)
    print()

    # --- Test connection ---
    print("Testing database connection...")
    if not test_connection():
        print()
        print("Upload aborted. Fix the connection and try again.")
        sys.exit(1)

    # If --test flag, stop here
    if args.test:
        close_connection()
        sys.exit(0)

    # --- Get database handle ---
    db = get_database()

    # --- Upload each CSV ---
    print()
    print("Uploading datasets...")
    if args.force:
        print("  (--force mode: existing data will be replaced)")
    print()

    success_count = 0
    total_newly_inserted = 0
    for csv_filename, collection_name in CSV_TO_COLLECTION.items():
        success, newly_inserted, total_count = upload_collection(
            db, csv_filename, collection_name
        )
        if success:
            success_count += 1
            total_newly_inserted += newly_inserted

    # --- Create indexes ---
    create_indexes(db)

    # --- Verify ---
    total_docs = verify_upload(db)

    # --- Summary ---
    print()
    print("=" * 55)
    total = len(CSV_TO_COLLECTION)
    if success_count == total:
        print(f"UPLOAD COMPLETE: {success_count}/{total} collections "
              f"processed successfully.")
    else:
        failed = total - success_count
        print(f"UPLOAD FINISHED WITH ERRORS: {failed}/{total} "
              f"collections failed.")

    print(f"Total documents in database: {total_docs}")
    print("=" * 55)

    # --- Cleanup ---
    close_connection()


if __name__ == "__main__":
    main()
