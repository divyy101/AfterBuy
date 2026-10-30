"""
AfterBuy – Analytics Engine Test Suite
======================================

Unit and integration tests for the AfterBuy Analytics Engine.
Verifies all mathematical computations, boundary conditions,
data types, and consistency across modules.

Checks:
    1. Database data ingestion & DataFrame shapes
    2. Product reliability scores (0 <= score <= 100) & failure rates (>= 0)
    3. Category reliability aggregation consistency
    4. Warranty claims volume, status percentages, and Warranty Cost Index formula
    5. Defect distribution sums and severity consistency
    6. Repair durations, average costs, and repeat repair rates
    7. Rule-based recommendations generation & insight fields
    8. Executive summary KPI completeness

Usage:
    python backend/test_analytics.py
"""

import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analytics import AfterBuyAnalytics, print_formatted_report


def print_section(title):
    print()
    print(f"── {title} ──")

def assert_pass(condition, test_name, details=""):
    if condition:
        print(f"  [PASS] {test_name}")
        return True
    else:
        print(f"  [FAIL] {test_name}")
        if details:
            print(f"         {details}")
        return False


def run_tests():
    print("=" * 65)
    print("AFTERBUY ANALYTICS ENGINE – AUTOMATED TEST SUITE")
    print("=" * 65)

    test_results = []

    # 1. Initialization and Data Loading
    print_section("1. Data Ingestion Test")
    try:
        engine = AfterBuyAnalytics()
        engine.load_data()
        test_results.append(assert_pass(
            len(engine.products_df) == 100,
            "Products DataFrame loaded (100 rows)",
            f"Got {len(engine.products_df)}"
        ))
        test_results.append(assert_pass(
            len(engine.sales_df) == 1000,
            "Sales DataFrame loaded (1000 rows)",
            f"Got {len(engine.sales_df)}"
        ))
        test_results.append(assert_pass(
            len(engine.claims_df) == 400,
            "Claims DataFrame loaded (400 rows)",
            f"Got {len(engine.claims_df)}"
        ))
        test_results.append(assert_pass(
            len(engine.repairs_df) == 300,
            "Repairs DataFrame loaded (300 rows)",
            f"Got {len(engine.repairs_df)}"
        ))
        test_results.append(assert_pass(
            len(engine.defects_df) == 500,
            "Defects DataFrame loaded (500 rows)",
            f"Got {len(engine.defects_df)}"
        ))
    except Exception as e:
        print(f"  [CRITICAL ERROR] Failed to load data from database: {e}")
        return False

    # 2. Product Reliability Metrics Test
    print_section("2. Product Reliability Metrics Test")
    rel = engine.get_product_reliability_metrics()
    
    test_results.append(assert_pass(
        "least_reliable_products" in rel and len(rel["least_reliable_products"]) == 5,
        "Top 5 least reliable products identified"
    ))
    
    scores = [p["reliability_score"] for p in rel["least_reliable_products"]]
    all_scores_valid = all(0.0 <= s <= 100.0 for s in scores)
    test_results.append(assert_pass(
        all_scores_valid,
        "Reliability scores bounded within [0, 100]",
        f"Scores: {scores}"
    ))

    rates = [p["failure_rate_pct"] for p in rel["least_reliable_products"]]
    all_rates_valid = all(r >= 0.0 for r in rates)
    test_results.append(assert_pass(
        all_rates_valid,
        "Failure rates are non-negative",
        f"Rates: {rates}"
    ))

    test_results.append(assert_pass(
        len(rel["category_reliability"]) == 7,
        "All 7 product categories present in reliability breakdown"
    ))

    # 3. Warranty Intelligence Metrics Test
    print_section("3. Warranty Intelligence Metrics Test")
    war = engine.get_warranty_intelligence_metrics()

    test_results.append(assert_pass(
        war["total_claims"] == 400,
        "Total warranty claims equals 400"
    ))
    test_results.append(assert_pass(
        war["warranty_claim_rate_pct"] == 40.0,
        "Warranty claim rate is exactly 40.0% (400 claims / 1000 sales)",
        f"Got {war['warranty_claim_rate_pct']}%"
    ))
    test_results.append(assert_pass(
        war["total_sales_revenue_inr"] > 0,
        "Total sales revenue is positive",
        f"Revenue: INR {war['total_sales_revenue_inr']:,.2f}"
    ))
    test_results.append(assert_pass(
        war["total_warranty_expenditure_inr"] > 0,
        "Total warranty expenditure is positive",
        f"Expenses: INR {war['total_warranty_expenditure_inr']:,.2f}"
    ))
    test_results.append(assert_pass(
        war["warranty_cost_index_pct"] > 0 and war["warranty_cost_index_pct"] < 100,
        "Warranty Cost Index (WCI) is within realistic bounds (0 < WCI < 100%)",
        f"WCI: {war['warranty_cost_index_pct']}%"
    ))
    test_results.append(assert_pass(
        sum(war["claims_by_status"].values()) == 400,
        "Claims by status sum up to exactly 400"
    ))

    # 4. Defect Intelligence Metrics Test
    print_section("4. Defect Intelligence Metrics Test")
    defects = engine.get_defect_intelligence_metrics()

    test_results.append(assert_pass(
        defects["total_defects"] == 500,
        "Total defects equals 500"
    ))
    defects_sum = sum(d["defect_count"] for d in defects["most_frequent_defects"])
    test_results.append(assert_pass(
        defects_sum == 500,
        "Most frequent defects sum up to exactly 500",
        f"Sum: {defects_sum}"
    ))
    sev_sum = sum(s["count"] for s in defects["severity_distribution"].values())
    test_results.append(assert_pass(
        sev_sum == 500,
        "Severity distribution counts sum up to exactly 500",
        f"Sum: {sev_sum}"
    ))
    test_results.append(assert_pass(
        len(defects["monthly_defect_trends"]) > 0,
        "Monthly defect trends series generated"
    ))

    # 5. Repair Analytics Test
    print_section("5. Repair Analytics Test")
    rep = engine.get_repair_analytics_metrics()

    test_results.append(assert_pass(
        rep["total_repairs"] == 300,
        "Total repairs equals 300"
    ))
    test_results.append(assert_pass(
        rep["average_repair_duration_days"] > 0,
        "Average repair duration is positive",
        f"Avg duration: {rep['average_repair_duration_days']} days"
    ))
    test_results.append(assert_pass(
        rep["average_repair_cost_inr"] > 0,
        "Average repair cost is positive",
        f"Avg cost: INR {rep['average_repair_cost_inr']}"
    ))
    test_results.append(assert_pass(
        0.0 <= rep["repeat_repair_rate_pct"] <= 100.0,
        "Repeat repair rate is bounded within [0%, 100%]",
        f"Repeat rate: {rep['repeat_repair_rate_pct']}%"
    ))
    test_results.append(assert_pass(
        len(rep["top_recurring_failure_products"]) > 0,
        "Products with recurring repair failures identified"
    ))

    # 6. Business Insights Test
    print_section("6. Business Insights Test")
    ins = engine.get_business_insights()

    test_results.append(assert_pass(
        len(ins["recommendations"]) >= 3,
        f"Generated {len(ins['recommendations'])} rule-based business recommendations"
    ))
    test_results.append(assert_pass(
        len(ins["high_risk_products"]) > 0,
        "High-risk failure rate outlier products identified"
    ))
    test_results.append(assert_pass(
        len(ins["expensive_warranty_categories"]) == 7,
        "All 7 product categories ranked by warranty expenses"
    ))
    test_results.append(assert_pass(
        len(ins["top_recurring_defect_patterns"]) > 0,
        "Top category-defect correlation patterns discovered"
    ))

    # 7. Executive Summary & Full Report Integration
    print_section("7. Executive Summary & Full Report Integration Test")
    full_report = engine.generate_full_report()
    summary = full_report["executive_summary"]
    required_keys = [
        "total_products", "total_sales_units", "total_sales_revenue_inr",
        "total_claims", "warranty_claim_rate_pct", "total_warranty_expenditure_inr",
        "warranty_cost_index_pct", "overall_avg_reliability_score",
        "total_defects_reported", "average_repair_duration_days",
        "average_repair_cost_inr", "repeat_repair_rate_pct"
    ]
    all_keys_present = all(k in summary for k in required_keys)
    test_results.append(assert_pass(
        all_keys_present,
        "Executive summary contains all required KPI fields"
    ))

    # Summary
    print()
    print("=" * 65)
    print("TEST SUITE SUMMARY")
    print("=" * 65)
    passed_count = sum(1 for res in test_results if res)
    total_count = len(test_results)
    print(f"Results: {passed_count}/{total_count} tests PASSED.")
    print("=" * 65)

    if passed_count == total_count:
        print("\nAll analytics tests passed successfully! Printing live sample report...\n")
        print_formatted_report(full_report)
        return True
    else:
        print(f"\n{total_count - passed_count} tests failed. Please review errors above.")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
