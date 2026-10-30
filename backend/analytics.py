"""
AfterBuy – Analytics Engine
===========================

Calculates comprehensive product reliability, warranty intelligence,
defect patterns, repair performance, and rule-based business insights
using Pandas and NumPy from live Firestore MongoDB datasets.

Analytical Modules:
    1. Product Reliability Analytics:
       - Product-wise failure rates
       - Product Reliability Score (0-100)
       - Category-wise reliability comparison
       - Least reliable products ranking
    2. Warranty Intelligence:
       - Total claims volume & status breakdown
       - Overall warranty claim rate
       - Total warranty expenditures
       - Warranty Cost Index (WCI = Expenses / Revenue * 100)
    3. Defect Intelligence:
       - Most frequent defect categories
       - Category vs Defect cross-analysis
       - Defect severity distribution
       - Monthly defect volume trends
    4. Repair Analytics:
       - Average and median repair durations
       - Average and total repair costs
       - Repeat repair rate
       - Products with recurring repair failures
    5. Business Insights:
       - High failure rate product flags
       - Expensive warranty categories
       - Recurring defect patterns
       - Rule-based actionable quality recommendations

Usage:
    from analytics import AfterBuyAnalytics

    engine = AfterBuyAnalytics()
    engine.load_data()
    report = engine.generate_full_report()
"""

import os
import sys
from datetime import datetime
import numpy as np
import pandas as pd

# Ensure backend directory is in path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_database


class AfterBuyAnalytics:
    """
    Core analytics engine for AfterBuy.
    Fetches collections from MongoDB and computes all analytical metrics.
    """

    def __init__(self, db=None):
        """
        Initialize the analytics engine.

        Args:
            db: Optional pymongo Database instance. If None, uses get_database().
        """
        self.db = db if db is not None else get_database()
        self.products_df = None
        self.sales_df = None
        self.claims_df = None
        self.repairs_df = None
        self.defects_df = None
        self._data_loaded = False

    def load_data(self):
        """
        Fetch all 5 collections from Firestore MongoDB into Pandas DataFrames.
        Converts datetime columns cleanly and handles data types.
        """
        # Fetch records excluding the MongoDB internal '_id'
        self.products_df = pd.DataFrame(list(self.db["products"].find({}, {"_id": 0})))
        self.sales_df = pd.DataFrame(list(self.db["sales"].find({}, {"_id": 0})))
        self.claims_df = pd.DataFrame(list(self.db["warranty_claims"].find({}, {"_id": 0})))
        self.repairs_df = pd.DataFrame(list(self.db["repairs"].find({}, {"_id": 0})))
        self.defects_df = pd.DataFrame(list(self.db["defects"].find({}, {"_id": 0})))

        # Ensure date columns are proper pandas datetimes
        if not self.products_df.empty and "launch_date" in self.products_df.columns:
            self.products_df["launch_date"] = pd.to_datetime(self.products_df["launch_date"])

        if not self.sales_df.empty and "purchase_date" in self.sales_df.columns:
            self.sales_df["purchase_date"] = pd.to_datetime(self.sales_df["purchase_date"])

        if not self.claims_df.empty and "claim_date" in self.claims_df.columns:
            self.claims_df["claim_date"] = pd.to_datetime(self.claims_df["claim_date"])

        if not self.repairs_df.empty and "repair_date" in self.repairs_df.columns:
            self.repairs_df["repair_date"] = pd.to_datetime(self.repairs_df["repair_date"])

        if not self.defects_df.empty and "defect_date" in self.defects_df.columns:
            self.defects_df["defect_date"] = pd.to_datetime(self.defects_df["defect_date"])

        self._data_loaded = True
        return self

    def _ensure_loaded(self):
        """Helper to ensure data has been loaded before running computations."""
        if not self._data_loaded:
            self.load_data()

    # =========================================================================
    # 1. PRODUCT RELIABILITY ANALYTICS
    # =========================================================================

    def get_product_reliability_metrics(self):
        """
        Compute product reliability metrics:
        - Product-wise failure rate = (claims / units_sold) * 100
        - Product Reliability Score out of 100
        - Category-wise reliability comparison
        - Least reliable products ranking

        Reliability Score Formula:
            Base Score = 100
            Claim Rate Penalty = min(50, failure_rate * 0.8)
            Defect Severity Penalty = weighted average of defect severities (Critical=10, High=6, Med=3, Low=1)
            Repeat Failure Penalty = (repeat_defects / total_defects) * 15
            Reliability Score = max(0, min(100, round(100 - Claim Penalty - Severity Penalty - Repeat Penalty, 1)))

        Returns:
            dict containing:
                - product_reliability_table: list[dict]
                - category_reliability: list[dict]
                - least_reliable_products: list[dict] (top 5 lowest score)
                - overall_avg_reliability_score: float
        """
        self._ensure_loaded()

        # 1. Calculate sales count per product
        sales_per_prod = self.sales_df.groupby("product_id").size().rename("units_sold")

        # 2. Calculate claims count per product
        claims_per_prod = self.claims_df.groupby("product_id").size().rename("total_claims")

        # 3. Calculate defects summary per product (counts, severity score, repeat counts)
        severity_weights = {"Critical": 10.0, "High": 6.0, "Medium": 3.0, "Low": 1.0}
        defects_work = self.defects_df.copy()
        defects_work["sev_weight"] = defects_work["severity"].map(severity_weights).fillna(2.0)
        defects_work["is_repeat"] = (defects_work["repeat_failure"] == "Yes").astype(int)

        defects_summary = defects_work.groupby("product_id").agg(
            total_defects=("defect_id", "count"),
            avg_severity_weight=("sev_weight", "mean"),
            repeat_defect_count=("is_repeat", "sum")
        )

        # 4. Merge onto full products catalog
        prod_metrics = self.products_df.copy()
        prod_metrics = prod_metrics.merge(sales_per_prod, on="product_id", how="left").fillna({"units_sold": 0})
        prod_metrics = prod_metrics.merge(claims_per_prod, on="product_id", how="left").fillna({"total_claims": 0})
        prod_metrics = prod_metrics.merge(defects_summary, on="product_id", how="left").fillna({
            "total_defects": 0,
            "avg_severity_weight": 0.0,
            "repeat_defect_count": 0
        })

        # Cast counts to int
        prod_metrics["units_sold"] = prod_metrics["units_sold"].astype(int)
        prod_metrics["total_claims"] = prod_metrics["total_claims"].astype(int)
        prod_metrics["total_defects"] = prod_metrics["total_defects"].astype(int)
        prod_metrics["repeat_defect_count"] = prod_metrics["repeat_defect_count"].astype(int)

        # 5. Compute Failure Rate (%) = (total_claims / units_sold) * 100
        # If units_sold is 0, failure rate is 0.0% to prevent division by zero
        prod_metrics["failure_rate_pct"] = np.where(
            prod_metrics["units_sold"] > 0,
            np.round((prod_metrics["total_claims"] / prod_metrics["units_sold"]) * 100, 2),
            0.0
        )

        # 6. Compute Reliability Score (0-100)
        def calc_score(row):
            if row["units_sold"] == 0 and row["total_claims"] == 0:
                return 100.0
            claim_penalty = min(50.0, row["failure_rate_pct"] * 0.8)
            sev_penalty = min(30.0, row["avg_severity_weight"] * 2.5)
            repeat_ratio = (row["repeat_defect_count"] / max(1, row["total_defects"]))
            repeat_penalty = repeat_ratio * 15.0 if row["total_defects"] > 0 else 0.0

            raw_score = 100.0 - claim_penalty - sev_penalty - repeat_penalty
            return float(np.round(np.clip(raw_score, 0.0, 100.0), 1))

        prod_metrics["reliability_score"] = prod_metrics.apply(calc_score, axis=1)

        # Sort products by lowest reliability score
        sorted_prods = prod_metrics.sort_values(by=["reliability_score", "failure_rate_pct"], ascending=[True, False])

        # 7. Category-wise reliability comparison
        cat_group = prod_metrics.groupby("category").agg(
            total_products=("product_id", "count"),
            units_sold=("units_sold", "sum"),
            total_claims=("total_claims", "sum"),
            total_defects=("total_defects", "sum"),
            avg_reliability_score=("reliability_score", "mean")
        ).reset_index()

        cat_group["category_failure_rate_pct"] = np.where(
            cat_group["units_sold"] > 0,
            np.round((cat_group["total_claims"] / cat_group["units_sold"]) * 100, 2),
            0.0
        )
        cat_group["avg_reliability_score"] = np.round(cat_group["avg_reliability_score"], 1)
        cat_group = cat_group.sort_values(by="avg_reliability_score", ascending=True)

        # Least reliable 5 products
        least_reliable = sorted_prods.head(5)[[
            "product_id", "product_name", "brand", "category",
            "units_sold", "total_claims", "failure_rate_pct", "reliability_score"
        ]].to_dict(orient="records")

        # Most reliable 5 products (highest scores)
        most_reliable = sorted_prods.sort_values(
            by=["reliability_score", "failure_rate_pct"], ascending=[False, True]
        ).head(5)[[
            "product_id", "product_name", "brand", "category",
            "units_sold", "total_claims", "failure_rate_pct", "reliability_score"
        ]].to_dict(orient="records")

        # Full product reliability table for interactive filtering
        full_table = sorted_prods[[
            "product_id", "product_name", "brand", "category",
            "price", "units_sold", "total_claims", "total_defects",
            "failure_rate_pct", "reliability_score"
        ]].to_dict(orient="records")

        return {
            "least_reliable_products": least_reliable,
            "most_reliable_products": most_reliable,
            "product_reliability_table": full_table,
            "category_reliability": cat_group.to_dict(orient="records"),
            "overall_avg_reliability_score": round(float(prod_metrics["reliability_score"].mean()), 1),
            "total_products_analyzed": len(prod_metrics)
        }

    # =========================================================================
    # 2. WARRANTY INTELLIGENCE
    # =========================================================================

    def get_warranty_intelligence_metrics(self):
        """
        Compute warranty intelligence metrics:
        - Total warranty claims
        - Approved, rejected, pending, under review breakdown
        - Overall Warranty Claim Rate (%) = (Total Claims / Total Sales) * 100
        - Total warranty expenditure = sum of repairs.repair_cost
        - Total sales revenue = sum of sales.selling_price
        - Warranty Cost Index (WCI) = (Warranty Expenses / Sales Revenue) * 100

        Returns:
            dict with warranty metrics, status breakdown, and cost ratios.
        """
        self._ensure_loaded()

        total_claims = len(self.claims_df)
        total_sales = len(self.sales_df)

        # Status distribution
        status_counts = self.claims_df["claim_status"].value_counts().to_dict()
        status_percentages = {
            status: round((count / max(1, total_claims)) * 100, 1)
            for status, count in status_counts.items()
        }

        # Warranty validity distribution (Yes / No)
        validity_counts = self.claims_df["warranty_valid"].value_counts().to_dict()

        # Overall Warranty Claim Rate (%)
        warranty_claim_rate_pct = round(
            (total_claims / max(1, total_sales)) * 100, 2
        ) if total_sales > 0 else 0.0

        # Financial Calculations
        # Total sales revenue from sales table
        total_sales_revenue = float(self.sales_df["selling_price"].sum())

        # Total repair expenses across all repairs
        total_warranty_expenditure = float(self.repairs_df["repair_cost"].sum())

        # Expenditure by claim status (merging repairs with claims)
        repairs_with_claims = self.repairs_df.merge(
            self.claims_df[["claim_id", "claim_status", "warranty_valid"]],
            on="claim_id",
            how="left"
        )
        approved_claims_cost = float(
            repairs_with_claims[repairs_with_claims["claim_status"] == "Approved"]["repair_cost"].sum()
        )

        # Warranty Cost Index (WCI) = (Warranty Expenditure / Sales Revenue) * 100
        warranty_cost_index = round(
            (total_warranty_expenditure / max(1.0, total_sales_revenue)) * 100, 2
        ) if total_sales_revenue > 0 else 0.0

        # Average cost per repair and per claim
        avg_cost_per_repair = round(float(self.repairs_df["repair_cost"].mean()), 2) if len(self.repairs_df) > 0 else 0.0
        avg_cost_per_claim = round(total_warranty_expenditure / max(1, total_claims), 2)

        # Monthly claim trends
        claims_time = self.claims_df.copy()
        claims_time["year_month"] = claims_time["claim_date"].dt.strftime("%Y-%m")
        monthly_claims = claims_time.groupby("year_month").size().rename("claim_count").reset_index()
        monthly_claim_trends = monthly_claims.sort_values(by="year_month").to_dict(orient="records")

        # Warranty cost and claims by product category
        repairs_cat = self.repairs_df.merge(
            self.products_df[["product_id", "category"]],
            on="product_id",
            how="left"
        )
        cat_cost_group = repairs_cat.groupby("category").agg(
            warranty_cost=("repair_cost", "sum"),
            repair_count=("repair_id", "count")
        ).reset_index()

        claims_cat = self.claims_df.merge(
            self.products_df[["product_id", "category"]],
            on="product_id",
            how="left"
        ).groupby("category").size().rename("claim_count").reset_index()

        cat_warranty_df = cat_cost_group.merge(claims_cat, on="category", how="left").fillna(0)
        cat_warranty_df["claim_count"] = cat_warranty_df["claim_count"].astype(int)
        cat_warranty_df = cat_warranty_df.sort_values(by="warranty_cost", ascending=False)
        warranty_cost_by_cat = cat_warranty_df.to_dict(orient="records")

        return {
            "total_claims": total_claims,
            "total_sales": total_sales,
            "warranty_claim_rate_pct": warranty_claim_rate_pct,
            "claims_by_status": status_counts,
            "claims_by_status_pct": status_percentages,
            "warranty_valid_distribution": validity_counts,
            "total_sales_revenue_inr": total_sales_revenue,
            "total_warranty_expenditure_inr": total_warranty_expenditure,
            "approved_claims_expenditure_inr": approved_claims_cost,
            "warranty_cost_index_pct": warranty_cost_index,
            "average_cost_per_repair_inr": avg_cost_per_repair,
            "average_cost_per_claim_inr": avg_cost_per_claim,
            "monthly_claim_trends": monthly_claim_trends,
            "warranty_cost_by_category": warranty_cost_by_cat
        }

    # =========================================================================
    # 3. DEFECT INTELLIGENCE
    # =========================================================================

    def get_defect_intelligence_metrics(self):
        """
        Compute defect intelligence metrics:
        - Most frequent defect categories
        - Defects grouped by product category
        - Defect severity distribution (Critical, High, Medium, Low)
        - Monthly defect volume trends

        Returns:
            dict containing defect analytics and monthly trend tables.
        """
        self._ensure_loaded()

        total_defects = len(self.defects_df)

        # 1. Most frequent defect categories
        cat_counts = self.defects_df["defect_category"].value_counts()
        most_frequent_defects = [
            {
                "defect_category": cat,
                "defect_count": int(count),
                "share_pct": round((count / max(1, total_defects)) * 100, 1)
            }
            for cat, count in cat_counts.items()
        ]

        # 2. Defects by product category
        defects_with_prod = self.defects_df.merge(
            self.products_df[["product_id", "category"]],
            on="product_id",
            how="left"
        )
        prod_cat_breakdown = defects_with_prod.groupby("category").size().rename("defect_count").reset_index()
        prod_cat_breakdown["share_pct"] = np.round(
            (prod_cat_breakdown["defect_count"] / max(1, total_defects)) * 100, 1
        )
        prod_cat_breakdown = prod_cat_breakdown.sort_values(by="defect_count", ascending=False).to_dict(orient="records")

        # 3. Defect severity distribution
        severity_counts = self.defects_df["severity"].value_counts()
        severity_distribution = {
            sev: {
                "count": int(count),
                "share_pct": round((count / max(1, total_defects)) * 100, 1)
            }
            for sev, count in severity_counts.items()
        }

        # 4. Monthly defect trends
        defects_time = self.defects_df.copy()
        defects_time["year_month"] = defects_time["defect_date"].dt.strftime("%Y-%m")
        monthly_trends = defects_time.groupby("year_month").size().rename("defect_count").reset_index()
        monthly_trends = monthly_trends.sort_values(by="year_month").to_dict(orient="records")

        # Top repeating defects
        repeat_counts = self.defects_df["repeat_failure"].value_counts().to_dict()

        # 5. Product Category versus Defect Type Cross-Tabulation
        cat_defect_crosstab = pd.crosstab(
            defects_with_prod["category"],
            defects_with_prod["defect_category"]
        ).reset_index()
        category_vs_defect = cat_defect_crosstab.to_dict(orient="records")

        return {
            "total_defects": total_defects,
            "most_frequent_defects": most_frequent_defects,
            "defects_by_product_category": prod_cat_breakdown,
            "severity_distribution": severity_distribution,
            "monthly_defect_trends": monthly_trends,
            "repeat_failure_counts": repeat_counts,
            "category_vs_defect": category_vs_defect
        }

    # =========================================================================
    # 4. REPAIR ANALYTICS
    # =========================================================================

    def get_repair_analytics_metrics(self):
        """
        Compute repair analytics metrics:
        - Average repair duration (days)
        - Average repair cost (INR)
        - Repeat repair rate (% of claims/products with multiple repairs)
        - Products with recurring repair failures

        Returns:
            dict of repair turnaround times, costs, repeat rates, and recurring products.
        """
        self._ensure_loaded()

        total_repairs = len(self.repairs_df)

        # 1. Duration metrics
        avg_duration = round(float(self.repairs_df["repair_duration_days"].mean()), 1)
        median_duration = round(float(self.repairs_df["repair_duration_days"].median()), 1)
        min_duration = int(self.repairs_df["repair_duration_days"].min())
        max_duration = int(self.repairs_df["repair_duration_days"].max())

        # 2. Cost metrics
        avg_cost = round(float(self.repairs_df["repair_cost"].mean()), 2)
        median_cost = round(float(self.repairs_df["repair_cost"].median()), 2)
        total_cost = int(self.repairs_df["repair_cost"].sum())

        # Breakdown by repair status
        status_breakdown = self.repairs_df.groupby("repair_status").agg(
            count=("repair_id", "count"),
            avg_cost=("repair_cost", "mean"),
            avg_duration_days=("repair_duration_days", "mean")
        ).reset_index()
        status_breakdown["avg_cost"] = np.round(status_breakdown["avg_cost"], 2)
        status_breakdown["avg_duration_days"] = np.round(status_breakdown["avg_duration_days"], 1)
        status_summary = status_breakdown.to_dict(orient="records")

        # 3. Repeat Repair Rate
        # A claim with > 1 repair record indicates a repeat repair
        repairs_per_claim = self.repairs_df.groupby("claim_id").size()
        claims_with_multiple_repairs = int((repairs_per_claim > 1).sum())
        unique_repaired_claims = len(repairs_per_claim)
        repeat_repair_rate_pct = round(
            (claims_with_multiple_repairs / max(1, unique_repaired_claims)) * 100, 2
        )

        # 4. Products with recurring repair failures (>= 2 repairs)
        prod_repairs = self.repairs_df.groupby("product_id").agg(
            repair_count=("repair_id", "count"),
            total_repair_cost=("repair_cost", "sum"),
            avg_duration_days=("repair_duration_days", "mean")
        ).reset_index()

        recurring_prods = prod_repairs[prod_repairs["repair_count"] >= 2].copy()
        recurring_prods = recurring_prods.merge(
            self.products_df[["product_id", "product_name", "brand", "category"]],
            on="product_id",
            how="left"
        )
        recurring_prods["avg_duration_days"] = np.round(recurring_prods["avg_duration_days"], 1)
        recurring_prods = recurring_prods.sort_values(by="repair_count", ascending=False)
        top_recurring_prods = recurring_prods.head(10).to_dict(orient="records")

        return {
            "total_repairs": total_repairs,
            "average_repair_duration_days": avg_duration,
            "median_repair_duration_days": median_duration,
            "duration_range_days": [min_duration, max_duration],
            "average_repair_cost_inr": avg_cost,
            "median_repair_cost_inr": median_cost,
            "total_repair_cost_inr": total_cost,
            "repair_status_summary": status_summary,
            "repeat_repair_rate_pct": repeat_repair_rate_pct,
            "claims_with_multiple_repairs": claims_with_multiple_repairs,
            "products_with_recurring_repairs_count": len(recurring_prods),
            "top_recurring_failure_products": top_recurring_prods
        }

    # =========================================================================
    # 5. BUSINESS INSIGHTS & RULE-BASED RECOMMENDATIONS
    # =========================================================================

    def get_business_insights(self):
        """
        Generate automated rule-based business insights and recommendations:
        - Highlights products with unusually high failure rates (> 1.5 standard deviations above mean)
        - Identifies expensive warranty categories based on cost per unit sold
        - Identifies top recurring defect patterns (Category + Defect Type)
        - Provides prescriptive operational recommendations for quality engineering
        """
        self._ensure_loaded()

        reliability = self.get_product_reliability_metrics()
        warranty = self.get_warranty_intelligence_metrics()
        defects = self.get_defect_intelligence_metrics()
        repairs = self.get_repair_analytics_metrics()

        recommendations = []
        high_risk_products = []
        expensive_categories = []
        defect_patterns = []

        # -------------------------------------------------------------
        # Rule 1: High Failure Rate Anomaly Detection
        # -------------------------------------------------------------
        # Calculate product failure rates
        sales_counts = self.sales_df.groupby("product_id").size()
        claim_counts = self.claims_df.groupby("product_id").size()

        combined = pd.DataFrame({"sales": sales_counts, "claims": claim_counts}).fillna(0)
        combined["failure_rate"] = np.where(
            combined["sales"] > 0,
            (combined["claims"] / combined["sales"]) * 100,
            0.0
        )

        mean_rate = float(combined["failure_rate"].mean())
        std_rate = float(combined["failure_rate"].std())
        threshold_rate = round(mean_rate + 1.5 * std_rate, 1)

        # Outliers exceeding threshold
        outliers = combined[combined["failure_rate"] > threshold_rate].copy()
        outliers = outliers.merge(
            self.products_df[["product_id", "product_name", "brand", "category"]],
            left_index=True,
            right_on="product_id",
            how="left"
        ).sort_values(by="failure_rate", ascending=False)

        for _, row in outliers.iterrows():
            high_risk_products.append({
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "category": row["category"],
                "failure_rate_pct": round(float(row["failure_rate"]), 1),
                "threshold_pct": threshold_rate
            })

        if high_risk_products:
            recommendations.append({
                "module": "Product Reliability",
                "severity": "High",
                "finding": f"{len(high_risk_products)} products exceed statistical failure threshold of {threshold_rate}% (mean: {mean_rate:.1f}%).",
                "recommendation": "Conduct immediate supplier component audits and QA batch inspections on top failing models: "
                                  + ", ".join([p["product_name"] for p in high_risk_products[:3]]) + "."
            })

        # -------------------------------------------------------------
        # Rule 2: Dominant Defect Category Detection
        # -------------------------------------------------------------
        top_defect = defects["most_frequent_defects"][0] if defects["most_frequent_defects"] else None
        if top_defect and top_defect["share_pct"] >= 18.0:
            recommendations.append({
                "module": "Defect Intelligence",
                "severity": "Medium",
                "finding": f"'{top_defect['defect_category']}' defects account for {top_defect['share_pct']}% of all reported issues ({top_defect['defect_count']} incidents).",
                "recommendation": f"Prioritize engineering redesign and stress-testing specifically for {top_defect['defect_category']} modules across next-generation product revisions."
            })

        # -------------------------------------------------------------
        # Rule 3: Expensive Warranty Categories
        # -------------------------------------------------------------
        # Join repairs with products to compute cost per category
        repairs_with_cat = self.repairs_df.merge(
            self.products_df[["product_id", "category"]],
            on="product_id",
            how="left"
        )
        cat_costs = repairs_with_cat.groupby("category")["repair_cost"].sum().rename("category_warranty_cost").reset_index()

        cat_sales = self.sales_df.merge(
            self.products_df[["product_id", "category"]],
            on="product_id",
            how="left"
        ).groupby("category")["selling_price"].sum().rename("category_revenue").reset_index()

        cat_financials = cat_costs.merge(cat_sales, on="category", how="left")
        cat_financials["category_wci_pct"] = np.round(
            (cat_financials["category_warranty_cost"] / np.maximum(1.0, cat_financials["category_revenue"])) * 100, 2
        )
        cat_financials = cat_financials.sort_values(by="category_warranty_cost", ascending=False)

        expensive_categories = cat_financials.to_dict(orient="records")

        top_exp_cat = expensive_categories[0] if expensive_categories else None
        if top_exp_cat:
            recommendations.append({
                "module": "Warranty Intelligence",
                "severity": "Medium",
                "finding": f"'{top_exp_cat['category']}' is the most costly warranty category (₹{int(top_exp_cat['category_warranty_cost']):,} in repairs, WCI: {top_exp_cat['category_wci_pct']}%).",
                "recommendation": f"Review warranty terms and repair service agreements for {top_exp_cat['category']}; consider modular replacement policies to reduce per-incident costs."
            })

        # -------------------------------------------------------------
        # Rule 4: Recurring Defect Patterns (Category + Defect Category)
        # -------------------------------------------------------------
        defects_with_cat = self.defects_df.merge(
            self.products_df[["product_id", "category"]],
            on="product_id",
            how="left"
        )
        pattern_table = defects_with_cat.groupby(["category", "defect_category"]).size().rename("occurrences").reset_index()
        top_patterns = pattern_table.sort_values(by="occurrences", ascending=False).head(5).to_dict(orient="records")
        defect_patterns = top_patterns

        if top_patterns:
            lead_pattern = top_patterns[0]
            recommendations.append({
                "module": "Defect Intelligence",
                "severity": "Low",
                "finding": f"Highest defect cluster: {lead_pattern['category']} + {lead_pattern['defect_category']} with {lead_pattern['occurrences']} cases.",
                "recommendation": f"Coordinate with {lead_pattern['category']} manufacturing partners to inspect {lead_pattern['defect_category']} assembly procedures."
            })

        # -------------------------------------------------------------
        # Rule 5: Repair Turnaround Time & Repeat Rate
        # -------------------------------------------------------------
        if repairs["repeat_repair_rate_pct"] > 10.0:
            recommendations.append({
                "module": "Repair Performance",
                "severity": "Medium",
                "finding": f"Repeat repair rate is {repairs['repeat_repair_rate_pct']}%, exceeding the 10.0% operational target.",
                "recommendation": "Implement mandatory post-repair verification checks and technician diagnostic retraining at service centers."
            })

        return {
            "high_risk_products": high_risk_products,
            "expensive_warranty_categories": expensive_categories,
            "top_recurring_defect_patterns": defect_patterns,
            "recommendations": recommendations
        }

    # =========================================================================
    # 6. EXECUTIVE SUMMARY & CONSOLIDATED REPORT
    # =========================================================================

    def get_executive_summary(self):
        """
        Consolidates top-level KPIs across all modules for dashboard and executive reporting.
        """
        self._ensure_loaded()

        reliability = self.get_product_reliability_metrics()
        warranty = self.get_warranty_intelligence_metrics()
        defects = self.get_defect_intelligence_metrics()
        repairs = self.get_repair_analytics_metrics()
        insights = self.get_business_insights()

        return {
            "total_products": len(self.products_df),
            "total_sales_units": len(self.sales_df),
            "total_sales_revenue_inr": warranty["total_sales_revenue_inr"],
            "total_claims": warranty["total_claims"],
            "warranty_claim_rate_pct": warranty["warranty_claim_rate_pct"],
            "total_warranty_expenditure_inr": warranty["total_warranty_expenditure_inr"],
            "warranty_cost_index_pct": warranty["warranty_cost_index_pct"],
            "overall_avg_reliability_score": reliability["overall_avg_reliability_score"],
            "total_defects_reported": defects["total_defects"],
            "average_repair_duration_days": repairs["average_repair_duration_days"],
            "average_repair_cost_inr": repairs["average_repair_cost_inr"],
            "repeat_repair_rate_pct": repairs["repeat_repair_rate_pct"],
            "total_recommendations": len(insights["recommendations"])
        }

    def generate_full_report(self):
        """
        Computes all modules and returns a structured dictionary containing
        the complete analytics output.
        """
        self._ensure_loaded()

        return {
            "generated_at": datetime.now().isoformat(),
            "executive_summary": self.get_executive_summary(),
            "product_reliability": self.get_product_reliability_metrics(),
            "warranty_intelligence": self.get_warranty_intelligence_metrics(),
            "defect_intelligence": self.get_defect_intelligence_metrics(),
            "repair_analytics": self.get_repair_analytics_metrics(),
            "business_insights": self.get_business_insights()
        }


def print_formatted_report(report=None):
    """
    Utility function to print a clean, beautiful analytics summary report in the console.
    """
    if report is None:
        analytics = AfterBuyAnalytics()
        analytics.load_data()
        report = analytics.generate_full_report()

    summary = report["executive_summary"]
    rel = report["product_reliability"]
    war = report["warranty_intelligence"]
    defects = report["defect_intelligence"]
    rep = report["repair_analytics"]
    ins = report["business_insights"]

    print("=" * 70)
    print("AFTERBUY – PRODUCT RELIABILITY & WARRANTY INTELLIGENCE REPORT")
    print("=" * 70)
    print(f"Generated: {report['generated_at']}")
    print()

    print("── 1. EXECUTIVE DASHBOARD SUMMARY ──")
    print(f"  • Total Products Catalog:      {summary['total_products']:,}")
    print(f"  • Total Units Sold:            {summary['total_sales_units']:,}")
    print(f"  • Total Sales Revenue:         INR {summary['total_sales_revenue_inr']:,.2f}")
    print(f"  • Total Warranty Claims:       {summary['total_claims']:,} (Claim Rate: {summary['warranty_claim_rate_pct']}%)")
    print(f"  • Total Warranty Expenditure:  INR {summary['total_warranty_expenditure_inr']:,.2f}")
    print(f"  • Warranty Cost Index (WCI):   {summary['warranty_cost_index_pct']}% of revenue")
    print(f"  • Fleet Reliability Score:     {summary['overall_avg_reliability_score']} / 100")
    print(f"  • Avg Repair Turnaround:       {summary['average_repair_duration_days']} days (Avg Cost: INR {summary['average_repair_cost_inr']:,.2f})")
    print()

    print("── 2. PRODUCT RELIABILITY ANALYTICS ──")
    print("  Category Comparison:")
    for cat in rel["category_reliability"]:
        print(f"    - {cat['category']:<14}: Failure Rate: {cat['category_failure_rate_pct']:>5.1f}% | "
              f"Reliability Score: {cat['avg_reliability_score']:>5.1f}/100 | "
              f"Sales: {cat['units_sold']:>4} | Claims: {cat['total_claims']:>3}")
    print()
    print("  Top 5 Least Reliable Products:")
    for p in rel["least_reliable_products"]:
        print(f"    - [{p['product_id']}] {p['product_name']:<24} ({p['category']}): "
              f"Score: {p['reliability_score']}/100 | Failure Rate: {p['failure_rate_pct']}% "
              f"(Sales: {p['units_sold']}, Claims: {p['total_claims']})")
    print()

    print("── 3. WARRANTY INTELLIGENCE ──")
    print(f"  • Claims Volume: {war['total_claims']} claims filed across {war['total_sales']} sales")
    print("  • Claim Status Breakdown:")
    for status, count in war["claims_by_status"].items():
        pct = war["claims_by_status_pct"][status]
        print(f"    - {status:<15}: {count:>4} ({pct:>5.1f}%)")
    print(f"  • Warranty Validity: {war['warranty_valid_distribution']}")
    print(f"  • Warranty Cost Index: {war['warranty_cost_index_pct']}% (Warranty Expense: INR {war['total_warranty_expenditure_inr']:,.2f})")
    print()

    print("── 4. DEFECT INTELLIGENCE ──")
    print(f"  • Total Defects Logged: {defects['total_defects']}")
    print("  • Most Frequent Defect Categories:")
    for d in defects["most_frequent_defects"]:
        print(f"    - {d['defect_category']:<14}: {d['defect_count']:>3} defects ({d['share_pct']:>5.1f}% share)")
    print("  • Defect Severity Breakdown:")
    for sev, data in defects["severity_distribution"].items():
        print(f"    - {sev:<10}: {data['count']:>3} ({data['share_pct']:>5.1f}%)")
    print()

    print("── 5. REPAIR ANALYTICS ──")
    print(f"  • Average Duration: {rep['average_repair_duration_days']} days (Median: {rep['median_repair_duration_days']} days)")
    print(f"  • Average Repair Cost: INR {rep['average_repair_cost_inr']:,.2f}")
    print(f"  • Repeat Repair Rate: {rep['repeat_repair_rate_pct']}% ({rep['claims_with_multiple_repairs']} claims with multiple repairs)")
    print(f"  • Products with Recurring Repairs: {rep['products_with_recurring_repairs_count']} products")
    print()

    print("── 6. BUSINESS INSIGHTS & RULE-BASED RECOMMENDATIONS ──")
    for i, rec in enumerate(ins["recommendations"], 1):
        print(f"  [{rec['severity'].upper()}] Recommendation {i} ({rec['module']}):")
        print(f"    Finding:        {rec['finding']}")
        print(f"    Recommendation: {rec['recommendation']}")
        print()
    print("=" * 70)


if __name__ == "__main__":
    print_formatted_report()
