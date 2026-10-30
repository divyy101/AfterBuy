"""
AfterBuy – Data Validation Script
===================================

Validates the generated synthetic datasets for:
    - Correct record counts
    - Missing values
    - Duplicate IDs
    - Invalid foreign key references
    - Date consistency (claim after purchase, etc.)
    - Negative prices or repair costs
    - Warranty validity consistency

Usage:
    python backend/validate_data.py
"""

import os
import sys
from datetime import datetime

import pandas as pd

# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

EXPECTED_COUNTS = {
    "products.csv": 100,
    "sales.csv": 1000,
    "warranty_claims.csv": 400,
    "repairs.csv": 300,
    "defects.csv": 500,
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_csv(filename):
    """Load a CSV file from the data directory."""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  ✗ MISSING FILE: {filepath}")
        return None
    # keep_default_na=False prevents pandas from converting "N/A" strings to NaN.
    # In our defects dataset, "N/A" is a valid value meaning "no linked claim".
    return pd.read_csv(filepath, keep_default_na=False)


def print_header(title):
    """Print a formatted section header."""
    print()
    print(f"── {title} ──")


def check_pass(description):
    """Print a passing check."""
    print(f"  ✓ PASS: {description}")


def check_fail(description, details=""):
    """Print a failing check."""
    print(f"  ✗ FAIL: {description}")
    if details:
        print(f"         {details}")


# ============================================================
# VALIDATION CHECKS
# ============================================================

def validate_file_existence():
    """Check that all expected CSV files exist."""
    print_header("1. File Existence Check")

    all_exist = True
    for filename in EXPECTED_COUNTS:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            check_pass(f"{filename} exists")
        else:
            check_fail(f"{filename} not found")
            all_exist = False

    return all_exist


def validate_record_counts(datasets):
    """Check that each dataset has the expected number of records."""
    print_header("2. Record Count Check")

    all_correct = True
    for filename, expected in EXPECTED_COUNTS.items():
        df = datasets.get(filename)
        if df is None:
            check_fail(f"{filename}: could not load")
            all_correct = False
            continue

        actual = len(df)
        if actual == expected:
            check_pass(f"{filename}: {actual} records (expected {expected})")
        else:
            check_fail(f"{filename}: {actual} records (expected {expected})")
            all_correct = False

    return all_correct


def validate_missing_values(datasets):
    """Check for missing values in all datasets."""
    print_header("3. Missing Values Check")

    all_clean = True
    for filename, df in datasets.items():
        if df is None:
            continue

        # For defects, claim_id can be "N/A" (not linked) — that's valid
        missing = df.isnull().sum()
        cols_with_missing = missing[missing > 0]

        if len(cols_with_missing) == 0:
            check_pass(f"{filename}: no missing values")
        else:
            check_fail(
                f"{filename}: missing values found",
                str(cols_with_missing.to_dict())
            )
            all_clean = False

    return all_clean


def validate_duplicate_ids(datasets):
    """Check for duplicate primary key IDs."""
    print_header("4. Duplicate ID Check")

    id_columns = {
        "products.csv": "product_id",
        "sales.csv": "sale_id",
        "warranty_claims.csv": "claim_id",
        "repairs.csv": "repair_id",
        "defects.csv": "defect_id",
    }

    all_unique = True
    for filename, id_col in id_columns.items():
        df = datasets.get(filename)
        if df is None:
            continue

        duplicates = df[id_col].duplicated().sum()
        if duplicates == 0:
            check_pass(f"{filename}.{id_col}: all unique")
        else:
            check_fail(
                f"{filename}.{id_col}: {duplicates} duplicates found"
            )
            all_unique = False

    return all_unique


def validate_foreign_keys(datasets):
    """Check that all foreign keys reference valid records."""
    print_header("5. Foreign Key Integrity Check")

    products = datasets.get("products.csv")
    sales = datasets.get("sales.csv")
    claims = datasets.get("warranty_claims.csv")
    repairs = datasets.get("repairs.csv")
    defects = datasets.get("defects.csv")

    all_valid = True

    # Sales -> Products
    if sales is not None and products is not None:
        valid_products = set(products["product_id"])
        invalid = sales[~sales["product_id"].isin(valid_products)]
        if len(invalid) == 0:
            check_pass("sales.product_id → products.product_id: all valid")
        else:
            check_fail(
                f"sales.product_id: {len(invalid)} invalid references"
            )
            all_valid = False

    # Claims -> Sales
    if claims is not None and sales is not None:
        valid_sales = set(sales["sale_id"])
        invalid = claims[~claims["sale_id"].isin(valid_sales)]
        if len(invalid) == 0:
            check_pass("claims.sale_id → sales.sale_id: all valid")
        else:
            check_fail(
                f"claims.sale_id: {len(invalid)} invalid references"
            )
            all_valid = False

    # Claims -> Products
    if claims is not None and products is not None:
        invalid = claims[~claims["product_id"].isin(valid_products)]
        if len(invalid) == 0:
            check_pass("claims.product_id → products.product_id: all valid")
        else:
            check_fail(
                f"claims.product_id: {len(invalid)} invalid references"
            )
            all_valid = False

    # Repairs -> Claims
    if repairs is not None and claims is not None:
        valid_claims = set(claims["claim_id"])
        invalid = repairs[~repairs["claim_id"].isin(valid_claims)]
        if len(invalid) == 0:
            check_pass("repairs.claim_id → claims.claim_id: all valid")
        else:
            check_fail(
                f"repairs.claim_id: {len(invalid)} invalid references"
            )
            all_valid = False

    # Repairs -> Products
    if repairs is not None and products is not None:
        invalid = repairs[~repairs["product_id"].isin(valid_products)]
        if len(invalid) == 0:
            check_pass("repairs.product_id → products.product_id: all valid")
        else:
            check_fail(
                f"repairs.product_id: {len(invalid)} invalid references"
            )
            all_valid = False

    # Defects -> Products
    if defects is not None and products is not None:
        invalid = defects[~defects["product_id"].isin(valid_products)]
        if len(invalid) == 0:
            check_pass("defects.product_id → products.product_id: all valid")
        else:
            check_fail(
                f"defects.product_id: {len(invalid)} invalid references"
            )
            all_valid = False

    # Defects -> Claims (only where claim_id != "N/A")
    if defects is not None and claims is not None:
        linked_defects = defects[defects["claim_id"] != "N/A"]
        valid_claims = set(claims["claim_id"])
        invalid = linked_defects[~linked_defects["claim_id"].isin(valid_claims)]
        if len(invalid) == 0:
            check_pass("defects.claim_id → claims.claim_id: all valid (excluding N/A)")
        else:
            check_fail(
                f"defects.claim_id: {len(invalid)} invalid references"
            )
            all_valid = False

    return all_valid


def validate_dates(datasets):
    """Check date consistency across datasets."""
    print_header("6. Date Consistency Check")

    sales = datasets.get("sales.csv")
    claims = datasets.get("warranty_claims.csv")
    products = datasets.get("products.csv")

    all_valid = True

    # Claims must be after purchase date
    if claims is not None and sales is not None:
        # Merge claims with sales to compare dates
        merged = claims.merge(
            sales[["sale_id", "purchase_date"]],
            on="sale_id",
            how="left"
        )
        merged["claim_date"] = pd.to_datetime(merged["claim_date"])
        merged["purchase_date"] = pd.to_datetime(merged["purchase_date"])

        invalid_dates = merged[merged["claim_date"] < merged["purchase_date"]]

        if len(invalid_dates) == 0:
            check_pass("All claim dates are after purchase dates")
        else:
            check_fail(
                f"{len(invalid_dates)} claims have dates before purchase"
            )
            all_valid = False

    # Sales must be after product launch date
    if sales is not None and products is not None:
        merged = sales.merge(
            products[["product_id", "launch_date"]],
            on="product_id",
            how="left"
        )
        merged["purchase_date"] = pd.to_datetime(merged["purchase_date"])
        merged["launch_date"] = pd.to_datetime(merged["launch_date"])

        invalid_dates = merged[merged["purchase_date"] < merged["launch_date"]]

        if len(invalid_dates) == 0:
            check_pass("All purchase dates are after product launch dates")
        else:
            check_fail(
                f"{len(invalid_dates)} sales have dates before product launch"
            )
            all_valid = False

    return all_valid


def validate_no_negatives(datasets):
    """Check that prices, costs, and durations are non-negative."""
    print_header("7. Non-Negative Values Check")

    all_valid = True

    # Products: price
    products = datasets.get("products.csv")
    if products is not None:
        negatives = (products["price"] < 0).sum()
        if negatives == 0:
            check_pass("products.price: all non-negative")
        else:
            check_fail(f"products.price: {negatives} negative values")
            all_valid = False

    # Sales: selling_price
    sales = datasets.get("sales.csv")
    if sales is not None:
        negatives = (sales["selling_price"] < 0).sum()
        if negatives == 0:
            check_pass("sales.selling_price: all non-negative")
        else:
            check_fail(f"sales.selling_price: {negatives} negative values")
            all_valid = False

    # Repairs: repair_cost
    repairs = datasets.get("repairs.csv")
    if repairs is not None:
        negatives = (repairs["repair_cost"] < 0).sum()
        if negatives == 0:
            check_pass("repairs.repair_cost: all non-negative")
        else:
            check_fail(f"repairs.repair_cost: {negatives} negative values")
            all_valid = False

        # Repairs: repair_duration_days
        negatives = (repairs["repair_duration_days"] < 0).sum()
        if negatives == 0:
            check_pass("repairs.repair_duration_days: all non-negative")
        else:
            check_fail(
                f"repairs.repair_duration_days: {negatives} negative values"
            )
            all_valid = False

    return all_valid


def validate_warranty_consistency(datasets):
    """Check that warranty_valid matches actual warranty period."""
    print_header("8. Warranty Validity Consistency Check")

    claims = datasets.get("warranty_claims.csv")
    sales = datasets.get("sales.csv")
    products = datasets.get("products.csv")

    if claims is None or sales is None or products is None:
        check_fail("Cannot validate — missing dataset(s)")
        return False

    # Merge claims with sales and products
    merged = claims.merge(
        sales[["sale_id", "purchase_date"]],
        on="sale_id",
        how="left"
    )
    merged = merged.merge(
        products[["product_id", "warranty_months"]],
        on="product_id",
        how="left"
    )

    merged["claim_date"] = pd.to_datetime(merged["claim_date"])
    merged["purchase_date"] = pd.to_datetime(merged["purchase_date"])

    # Calculate expected warranty validity
    merged["warranty_end"] = (
        merged["purchase_date"]
        + pd.to_timedelta(merged["warranty_months"] * 30, unit="D")
    )
    merged["expected_valid"] = merged.apply(
        lambda row: "Yes" if row["claim_date"] <= row["warranty_end"] else "No",
        axis=1
    )

    mismatches = (merged["warranty_valid"] != merged["expected_valid"]).sum()

    if mismatches == 0:
        check_pass("All warranty_valid flags match calculated warranty periods")
    else:
        check_fail(f"{mismatches} warranty_valid values are inconsistent")

    return mismatches == 0


# ============================================================
# MAIN – Run all validations
# ============================================================

def main():
    """Run all validation checks and print a summary."""

    print("=" * 60)
    print("AfterBuy – Data Validation Report")
    print("=" * 60)
    print(f"Data directory: {DATA_DIR}")

    # Check files exist first
    if not validate_file_existence():
        print()
        print("✗ Some files are missing. Run generate_data.py first.")
        sys.exit(1)

    # Load all datasets
    datasets = {}
    for filename in EXPECTED_COUNTS:
        datasets[filename] = load_csv(filename)

    # Run all validation checks
    results = []
    results.append(("Record Counts", validate_record_counts(datasets)))
    results.append(("Missing Values", validate_missing_values(datasets)))
    results.append(("Duplicate IDs", validate_duplicate_ids(datasets)))
    results.append(("Foreign Keys", validate_foreign_keys(datasets)))
    results.append(("Date Consistency", validate_dates(datasets)))
    results.append(("Non-Negative Values", validate_no_negatives(datasets)))
    results.append(("Warranty Consistency", validate_warranty_consistency(datasets)))

    # Summary
    print()
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    total_checks = len(results)
    passed = sum(1 for _, result in results if result)
    failed = total_checks - passed

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print()
    print(f"  Total: {total_checks} checks | "
          f"Passed: {passed} | Failed: {failed}")
    print()

    if failed == 0:
        print("✓ ALL VALIDATIONS PASSED — Data is clean and consistent.")
    else:
        print(f"✗ {failed} VALIDATION(S) FAILED — Review the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
