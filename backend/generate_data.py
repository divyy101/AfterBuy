"""
AfterBuy – Synthetic Dataset Generator
=======================================

This script generates five interconnected CSV datasets
for the Product Reliability & Warranty Intelligence System.

ALL DATA IS SYNTHETIC / SIMULATED.
No real customer information is used.

Datasets Generated:
    1. products.csv      – 100 products
    2. sales.csv         – 1000 sales records
    3. warranty_claims.csv – 400 warranty claims
    4. repairs.csv       – 300 repair records
    5. defects.csv       – 500 defect records

Usage:
    python backend/generate_data.py
"""

import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# ============================================================
# CONFIGURATION
# ============================================================

# Fixed seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Output directory (relative to project root)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Date range for the simulation
DATE_START = datetime(2022, 1, 1)
DATE_END = datetime(2025, 9, 30)

# ============================================================
# REFERENCE DATA – Categories, Brands, Names, etc.
# ============================================================

CATEGORIES = [
    "Laptops",
    "Smartphones",
    "Headphones",
    "Smartwatches",
    "Tablets",
    "Speakers",
    "Monitors",
]

BRANDS = {
    "Laptops":      ["Dell", "HP", "Lenovo", "Asus", "Acer"],
    "Smartphones":  ["Samsung", "OnePlus", "Xiaomi", "Motorola", "Realme"],
    "Headphones":   ["Sony", "JBL", "Boat", "Sennheiser", "Audio-Technica"],
    "Smartwatches": ["Noise", "Fire-Boltt", "Samsung", "Amazfit", "Boat"],
    "Tablets":      ["Samsung", "Lenovo", "Apple", "Xiaomi", "Realme"],
    "Speakers":     ["JBL", "Sony", "Boat", "Marshall", "Bose"],
    "Monitors":     ["LG", "Samsung", "Dell", "BenQ", "Acer"],
}

# Product name templates per category
PRODUCT_NAMES = {
    "Laptops":      ["ProBook", "Vostro", "IdeaPad", "VivoBook", "Aspire",
                     "ThinkPad", "Pavilion", "ZenBook", "Swift", "Nitro"],
    "Smartphones":  ["Galaxy", "Nord", "Redmi", "Edge", "Narzo",
                     "Note", "Ultra", "Pro", "Lite", "Max"],
    "Headphones":   ["WH-1000", "Tune", "Rockerz", "HD-450", "ATH-M50",
                     "FreeBuds", "Airdopes", "Live", "Club", "Elite"],
    "Smartwatches": ["ColorFit", "Ring", "Galaxy Watch", "GTR", "Storm",
                     "Pulse", "Xtend", "Verge", "Bip", "Luna"],
    "Tablets":      ["Tab A", "Tab M", "iPad Air", "Pad 5", "Pad X",
                     "Tab S", "Yoga", "Mini", "Pro Tab", "Slate"],
    "Speakers":     ["Flip", "SRS-XB", "Stone", "Stanmore", "SoundLink",
                     "Charge", "Xtreme", "Revolve", "Acton", "Go"],
    "Monitors":     ["UltraGear", "Odyssey", "UltraSharp", "EW", "Nitro VG",
                     "ProArt", "ViewFinity", "Predator", "EX", "GW"],
}

# Price ranges per category (min, max)
PRICE_RANGES = {
    "Laptops":      (30000, 120000),
    "Smartphones":  (8000, 80000),
    "Headphones":   (1500, 25000),
    "Smartwatches": (2000, 15000),
    "Tablets":      (10000, 60000),
    "Speakers":     (2000, 30000),
    "Monitors":     (8000, 50000),
}

# Warranty months per category (min, max)
WARRANTY_RANGES = {
    "Laptops":      (12, 36),
    "Smartphones":  (12, 24),
    "Headphones":   (6, 12),
    "Smartwatches": (6, 18),
    "Tablets":      (12, 24),
    "Speakers":     (6, 12),
    "Monitors":     (12, 36),
}

SALES_CHANNELS = [
    "Online",
    "Retail Store",
    "Authorized Dealer",
    "Company Website",
    "Marketplace",
]

CUSTOMER_REGIONS = [
    "North",
    "South",
    "East",
    "West",
    "Central",
]

CLAIM_REASONS = [
    "Device not turning on",
    "Battery draining fast",
    "Screen flickering",
    "Overheating issue",
    "Connectivity dropping",
    "Charging port defect",
    "Audio distortion",
    "Software crash",
    "Physical damage claim",
    "Performance degradation",
    "Touchscreen unresponsive",
    "Speaker malfunction",
    "Camera not working",
    "Bluetooth not pairing",
    "Wi-Fi disconnecting",
]

CLAIM_STATUSES = ["Approved", "Rejected", "Pending", "Under Review"]

REPAIR_STATUSES = ["Completed", "In Progress", "Pending Parts", "Returned Unrepaired"]

DEFECT_CATEGORIES = [
    "Battery",
    "Display",
    "Hardware",
    "Software",
    "Connectivity",
    "Charging",
    "Audio",
]

SEVERITY_LEVELS = ["Low", "Medium", "High", "Critical"]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def random_date(start, end):
    """Generate a random date between start and end (inclusive)."""
    delta = (end - start).days
    if delta <= 0:
        return start
    random_days = random.randint(0, delta)
    return start + timedelta(days=random_days)


def round_price(value):
    """Round a price to the nearest 10 for realism."""
    return int(round(value / 10) * 10)


# ============================================================
# 1. GENERATE PRODUCTS (100 records)
# ============================================================

def generate_products(num_products=100):
    """
    Generate a products dataset.

    Each product has a unique ID, name, brand, category,
    launch date, price, and warranty period.
    """
    print(f"Generating {num_products} products...")

    records = []

    for i in range(1, num_products + 1):
        # Pick a category (distribute roughly evenly)
        category = CATEGORIES[i % len(CATEGORIES)]

        # Pick a brand from that category
        brand = random.choice(BRANDS[category])

        # Create a product name: Brand + Template + model number
        name_template = random.choice(PRODUCT_NAMES[category])
        model_number = random.randint(100, 999)
        product_name = f"{brand} {name_template} {model_number}"

        # Launch date: spread across 2022–2024
        launch_date = random_date(
            datetime(2022, 1, 1),
            datetime(2024, 6, 30)
        )

        # Price: realistic for the category
        price_min, price_max = PRICE_RANGES[category]
        price = round_price(np.random.uniform(price_min, price_max))

        # Warranty: category-appropriate
        wmin, wmax = WARRANTY_RANGES[category]
        warranty_months = random.choice(range(wmin, wmax + 1, 6))

        records.append({
            "product_id": f"PROD-{i:04d}",
            "product_name": product_name,
            "brand": brand,
            "category": category,
            "launch_date": launch_date.strftime("%Y-%m-%d"),
            "price": price,
            "warranty_months": warranty_months,
        })

    df = pd.DataFrame(records)
    print(f"  ✓ Products generated: {len(df)} records")
    return df


# ============================================================
# 2. GENERATE SALES (1000 records)
# ============================================================

def generate_sales(products_df, num_sales=1000):
    """
    Generate a sales dataset.

    Each sale references an existing product.
    Purchase date is after the product's launch date.
    Selling price varies slightly from the base price.
    """
    print(f"Generating {num_sales} sales records...")

    records = []

    for i in range(1, num_sales + 1):
        # Pick a random product
        product = products_df.sample(1).iloc[0]
        product_id = product["product_id"]
        base_price = product["price"]
        launch_date = datetime.strptime(product["launch_date"], "%Y-%m-%d")

        # Purchase date: between launch date and simulation end
        purchase_date = random_date(launch_date, DATE_END)

        # Selling price: ±10% of base price (discounts / markups)
        price_variation = np.random.uniform(-0.10, 0.05)
        selling_price = round_price(base_price * (1 + price_variation))
        selling_price = max(selling_price, 500)  # minimum realistic price

        # Sales channel and region
        sales_channel = random.choice(SALES_CHANNELS)
        customer_region = random.choice(CUSTOMER_REGIONS)

        records.append({
            "sale_id": f"SALE-{i:05d}",
            "product_id": product_id,
            "purchase_date": purchase_date.strftime("%Y-%m-%d"),
            "selling_price": selling_price,
            "sales_channel": sales_channel,
            "customer_region": customer_region,
        })

    df = pd.DataFrame(records)
    print(f"  ✓ Sales generated: {len(df)} records")
    return df


# ============================================================
# 3. GENERATE WARRANTY CLAIMS (400 records)
# ============================================================

def generate_warranty_claims(sales_df, products_df, num_claims=400):
    """
    Generate warranty claims.

    Each claim references a valid sale.
    Claim date is always after the purchase date.
    warranty_valid is determined by whether the claim
    falls within the product's warranty period.
    """
    print(f"Generating {num_claims} warranty claims...")

    # Build a lookup: product_id -> warranty_months
    warranty_lookup = dict(
        zip(products_df["product_id"], products_df["warranty_months"])
    )

    # Sample sales to generate claims from (some sales may have claims)
    # We allow multiple claims from different sales, but each claim
    # references one sale.
    sampled_sales = sales_df.sample(n=num_claims, replace=True).reset_index(drop=True)

    records = []

    for i in range(num_claims):
        sale = sampled_sales.iloc[i]
        sale_id = sale["sale_id"]
        product_id = sale["product_id"]
        purchase_date = datetime.strptime(sale["purchase_date"], "%Y-%m-%d")
        warranty_months = warranty_lookup[product_id]

        # Claim date: 7 to 540 days after purchase (some within warranty, some not)
        days_after = random.randint(7, 540)
        claim_date = purchase_date + timedelta(days=days_after)

        # Don't let claim_date exceed our simulation range by too much
        if claim_date > DATE_END + timedelta(days=90):
            claim_date = random_date(purchase_date + timedelta(days=7), DATE_END)

        # Determine if warranty is valid
        warranty_end = purchase_date + timedelta(days=warranty_months * 30)
        warranty_valid = "Yes" if claim_date <= warranty_end else "No"

        # Claim reason and status
        claim_reason = random.choice(CLAIM_REASONS)
        claim_status = random.choice(CLAIM_STATUSES)

        records.append({
            "claim_id": f"CLM-{i + 1:05d}",
            "sale_id": sale_id,
            "product_id": product_id,
            "claim_date": claim_date.strftime("%Y-%m-%d"),
            "claim_reason": claim_reason,
            "claim_status": claim_status,
            "warranty_valid": warranty_valid,
        })

    df = pd.DataFrame(records)
    print(f"  ✓ Warranty claims generated: {len(df)} records")
    return df


# ============================================================
# 4. GENERATE REPAIRS (300 records)
# ============================================================

def generate_repairs(claims_df, num_repairs=300):
    """
    Generate repair records.

    Each repair references an existing warranty claim.
    Repair date is on or after the claim date.
    Repair costs and durations are realistic.
    """
    print(f"Generating {num_repairs} repair records...")

    # Sample claims to create repairs from
    sampled_claims = claims_df.sample(n=num_repairs, replace=True).reset_index(drop=True)

    records = []

    for i in range(num_repairs):
        claim = sampled_claims.iloc[i]
        claim_id = claim["claim_id"]
        product_id = claim["product_id"]
        claim_date = datetime.strptime(claim["claim_date"], "%Y-%m-%d")

        # Repair starts 1–14 days after claim
        days_to_start = random.randint(1, 14)
        repair_date = claim_date + timedelta(days=days_to_start)

        # Repair duration: 1–30 days (most repairs are 1–10 days)
        repair_duration = int(np.random.choice(
            [1, 2, 3, 4, 5, 6, 7, 10, 14, 21, 30],
            p=[0.10, 0.15, 0.15, 0.12, 0.12, 0.08, 0.08, 0.07, 0.06, 0.04, 0.03]
        ))

        # Repair cost: ₹200–₹15000 (skewed towards lower costs)
        repair_cost = round_price(
            int(np.random.lognormal(mean=7.0, sigma=0.8))
        )
        repair_cost = max(200, min(repair_cost, 15000))

        # Repair status
        repair_status = random.choice(REPAIR_STATUSES)

        records.append({
            "repair_id": f"REP-{i + 1:05d}",
            "claim_id": claim_id,
            "product_id": product_id,
            "repair_date": repair_date.strftime("%Y-%m-%d"),
            "repair_cost": repair_cost,
            "repair_duration_days": repair_duration,
            "repair_status": repair_status,
        })

    df = pd.DataFrame(records)
    print(f"  ✓ Repairs generated: {len(df)} records")
    return df


# ============================================================
# 5. GENERATE DEFECTS (500 records)
# ============================================================

def generate_defects(products_df, claims_df, num_defects=500):
    """
    Generate defect records.

    Each defect references an existing product.
    Some defects are linked to warranty claims, some are not.
    Repeat failures are flagged.
    """
    print(f"Generating {num_defects} defect records...")

    records = []

    # Track defects per product to identify repeat failures
    product_defect_count = {}

    for i in range(1, num_defects + 1):
        # Pick a random product
        product = products_df.sample(1).iloc[0]
        product_id = product["product_id"]

        # Track repeat failures
        product_defect_count[product_id] = product_defect_count.get(product_id, 0) + 1
        is_repeat = "Yes" if product_defect_count[product_id] > 1 else "No"

        # Optionally link to a warranty claim (70% chance)
        claim_id = None
        if random.random() < 0.70:
            matching_claims = claims_df[claims_df["product_id"] == product_id]
            if len(matching_claims) > 0:
                claim_id = matching_claims.sample(1).iloc[0]["claim_id"]

        # Defect category and severity
        defect_category = random.choice(DEFECT_CATEGORIES)
        severity = random.choices(
            SEVERITY_LEVELS,
            weights=[30, 40, 20, 10],  # Most defects are Low/Medium
            k=1
        )[0]

        # Defect date: after product launch, within simulation range
        launch_date = datetime.strptime(product["launch_date"], "%Y-%m-%d")
        defect_date = random_date(launch_date, DATE_END)

        records.append({
            "defect_id": f"DEF-{i:05d}",
            "product_id": product_id,
            "claim_id": claim_id if claim_id else "N/A",
            "defect_category": defect_category,
            "severity": severity,
            "defect_date": defect_date.strftime("%Y-%m-%d"),
            "repeat_failure": is_repeat,
        })

    df = pd.DataFrame(records)
    print(f"  ✓ Defects generated: {len(df)} records")
    return df


# ============================================================
# MAIN – Generate all datasets and save to CSV
# ============================================================

def main():
    """Generate all datasets and save them as CSV files."""

    print("=" * 60)
    print("AfterBuy – Synthetic Data Generator")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Random seed: {RANDOM_SEED}")
    print()

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Generate datasets in dependency order ---

    # 1. Products (no dependencies)
    products_df = generate_products(100)

    # 2. Sales (depends on products)
    sales_df = generate_sales(products_df, 1000)

    # 3. Warranty Claims (depends on sales + products)
    claims_df = generate_warranty_claims(sales_df, products_df, 400)

    # 4. Repairs (depends on claims)
    repairs_df = generate_repairs(claims_df, 300)

    # 5. Defects (depends on products + claims)
    defects_df = generate_defects(products_df, claims_df, 500)

    # --- Save all datasets to CSV ---
    print()
    print("Saving datasets to CSV...")

    datasets = {
        "products.csv": products_df,
        "sales.csv": sales_df,
        "warranty_claims.csv": claims_df,
        "repairs.csv": repairs_df,
        "defects.csv": defects_df,
    }

    for filename, df in datasets.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        df.to_csv(filepath, index=False)
        print(f"  ✓ Saved {filename} ({len(df)} rows, {len(df.columns)} columns)")

    # --- Summary ---
    print()
    print("=" * 60)
    print("DATA GENERATION COMPLETE")
    print("=" * 60)
    print()
    print("Summary:")
    print(f"  Products:         {len(products_df):>6} records")
    print(f"  Sales:            {len(sales_df):>6} records")
    print(f"  Warranty Claims:  {len(claims_df):>6} records")
    print(f"  Repairs:          {len(repairs_df):>6} records")
    print(f"  Defects:          {len(defects_df):>6} records")
    print(f"  Total:            {sum(len(df) for df in datasets.values()):>6} records")
    print()
    print("⚠ All data is SYNTHETIC / SIMULATED.")
    print("  No real customer data was used.")


if __name__ == "__main__":
    main()
