"""
AfterBuy – Database Verification Script
=======================================

Verifies that the Google Cloud Firestore Enterprise database (MongoDB-compatible)
contains all required collections, document counts, indexes, and valid relational data.

Checks performed:
    1. Connection test & latency measurement
    2. Existence of all 5 target collections
    3. Document count verification against expected values
    4. Primary key index verification
    5. Schema structure check on sample documents
    6. Relational foreign key integrity check across MongoDB collections

Usage:
    python backend/verify_database.py
"""

import os
import sys
import time

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(__file__))

from database import get_database, test_connection, close_connection

# ============================================================
# EXPECTED METRICS
# ============================================================

EXPECTED_COLLECTIONS = {
    "products": {
        "count": 100,
        "pk": "product_id",
        "sample_fields": ["product_id", "product_name", "brand", "category", "launch_date", "price", "warranty_months"]
    },
    "sales": {
        "count": 1000,
        "pk": "sale_id",
        "sample_fields": ["sale_id", "product_id", "purchase_date", "selling_price", "sales_channel", "customer_region"]
    },
    "warranty_claims": {
        "count": 400,
        "pk": "claim_id",
        "sample_fields": ["claim_id", "sale_id", "product_id", "claim_date", "claim_reason", "claim_status", "warranty_valid"]
    },
    "repairs": {
        "count": 300,
        "pk": "repair_id",
        "sample_fields": ["repair_id", "claim_id", "product_id", "repair_date", "repair_cost", "repair_duration_days", "repair_status"]
    },
    "defects": {
        "count": 500,
        "pk": "defect_id",
        "sample_fields": ["defect_id", "product_id", "claim_id", "defect_category", "severity", "defect_date", "repeat_failure"]
    },
}

# ============================================================
# FORMATTING HELPERS
# ============================================================

def print_header(title):
    print()
    print(f"── {title} ──")

def check_pass(msg):
    print(f"  [PASS] {msg}")

def check_fail(msg, details=""):
    print(f"  [FAIL] {msg}")
    if details:
        print(f"         {details}")

# ============================================================
# VERIFICATION CHECKS
# ============================================================

def verify_connection(db):
    """Test ping and measure roundtrip latency."""
    print_header("1. Database Connection & Latency Check")
    try:
        start_time = time.time()
        db.command("ping")
        latency_ms = (time.time() - start_time) * 1000
        check_pass(f"Connection active (ping response: {latency_ms:.1f}ms)")
        return True
    except Exception as e:
        check_fail("Failed to ping database", str(e))
        return False

def verify_collections_and_counts(db):
    """Verify all 5 collections exist and have exact document counts."""
    print_header("2. Collection Existence & Record Count Check")
    existing_collections = set(db.list_collection_names())
    all_passed = True
    total_docs = 0

    for col_name, config in EXPECTED_COLLECTIONS.items():
        if col_name not in existing_collections:
            check_fail(f"Collection '{col_name}' missing from database")
            all_passed = False
            continue

        count = db[col_name].count_documents({})
        expected = config["count"]
        total_docs += count

        if count == expected:
            check_pass(f"'{col_name}': {count} documents (matches expected {expected})")
        else:
            check_fail(
                f"'{col_name}': count mismatch",
                f"Found {count} docs, expected {expected}"
            )
            all_passed = False

    if all_passed:
        print(f"  --> Total Verified Documents: {total_docs} across {len(EXPECTED_COLLECTIONS)} collections.")

    return all_passed

def verify_indexes(db):
    """Verify that primary key indexes are present on each collection."""
    print_header("3. Primary Key Index Check")
    all_passed = True

    for col_name, config in EXPECTED_COLLECTIONS.items():
        pk = config["pk"]
        try:
            indexes = list(db[col_name].list_indexes())
            index_keys = [list(idx["key"].keys())[0] for idx in indexes if "key" in idx]

            if pk in index_keys:
                check_pass(f"Index on '{col_name}.{pk}' verified")
            else:
                check_fail(f"Index on '{col_name}.{pk}' not found (found: {index_keys})")
                all_passed = False
        except Exception as e:
            check_fail(f"Could not inspect indexes for '{col_name}': {e}")
            all_passed = False

    return all_passed

def verify_schema(db):
    """Inspect sample document from each collection for expected fields."""
    print_header("4. Schema & Field Presence Check")
    all_passed = True

    for col_name, config in EXPECTED_COLLECTIONS.items():
        sample = db[col_name].find_one()
        if not sample:
            check_fail(f"'{col_name}': No sample document available to verify")
            all_passed = False
            continue

        missing_fields = [f for f in config["sample_fields"] if f not in sample]
        if not missing_fields:
            check_pass(f"'{col_name}': all {len(config['sample_fields'])} required fields present")
        else:
            check_fail(f"'{col_name}': missing fields in sample", str(missing_fields))
            all_passed = False

    return all_passed

def verify_relational_integrity(db):
    """Verify relational references across MongoDB collections."""
    print_header("5. Relational Foreign Key Integrity Check")
    all_passed = True

    try:
        # Collect sets of valid keys
        product_ids = set(db["products"].distinct("product_id"))
        sale_ids = set(db["sales"].distinct("sale_id"))
        claim_ids = set(db["warranty_claims"].distinct("claim_id"))

        # 1. Sales -> Products
        sales_product_ids = set(db["sales"].distinct("product_id"))
        invalid_sales_products = sales_product_ids - product_ids
        if not invalid_sales_products:
            check_pass("sales.product_id -> products.product_id: All references valid")
        else:
            check_fail(f"sales.product_id contains {len(invalid_sales_products)} invalid references")
            all_passed = False

        # 2. Claims -> Sales
        claim_sale_ids = set(db["warranty_claims"].distinct("sale_id"))
        invalid_claim_sales = claim_sale_ids - sale_ids
        if not invalid_claim_sales:
            check_pass("warranty_claims.sale_id -> sales.sale_id: All references valid")
        else:
            check_fail(f"warranty_claims.sale_id contains {len(invalid_claim_sales)} invalid references")
            all_passed = False

        # 3. Repairs -> Claims
        repair_claim_ids = set(db["repairs"].distinct("claim_id"))
        invalid_repair_claims = repair_claim_ids - claim_ids
        if not invalid_repair_claims:
            check_pass("repairs.claim_id -> warranty_claims.claim_id: All references valid")
        else:
            check_fail(f"repairs.claim_id contains {len(invalid_repair_claims)} invalid references")
            all_passed = False

        # 4. Defects -> Products
        defect_product_ids = set(db["defects"].distinct("product_id"))
        invalid_defect_products = defect_product_ids - product_ids
        if not invalid_defect_products:
            check_pass("defects.product_id -> products.product_id: All references valid")
        else:
            check_fail(f"defects.product_id contains {len(invalid_defect_products)} invalid references")
            all_passed = False

    except Exception as e:
        check_fail("Error performing relational integrity check", str(e))
        all_passed = False

    return all_passed

# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("AfterBuy – Firestore MongoDB Database Verification Report")
    print("=" * 60)

    try:
        db = get_database()
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Could not initialize database client:\n{e}\n")
        sys.exit(1)

    checks = [
        ("Connection & Latency", verify_connection(db)),
        ("Collections & Record Counts", verify_collections_and_counts(db)),
        ("Primary Key Indexes", verify_indexes(db)),
        ("Document Schema", verify_schema(db)),
        ("Relational Integrity", verify_relational_integrity(db)),
    ]

    print()
    print("=" * 60)
    print("DATABASE VERIFICATION SUMMARY")
    print("=" * 60)

    total_checks = len(checks)
    passed_count = sum(1 for _, passed in checks if passed)
    failed_count = total_checks - passed_count

    for name, passed in checks:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {name}")

    print()
    print(f"Result: {passed_count}/{total_checks} checks passed.")
    print("=" * 60)

    close_connection()

    if failed_count > 0:
        sys.exit(1)
    else:
        print("\nAll database checks PASSED. Ready for analytics and API development.\n")

if __name__ == "__main__":
    main()
