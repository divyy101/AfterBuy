"""
AfterBuy – Product Reliability & Warranty Intelligence Dashboard
================================================================
An interactive business intelligence and product analytics web application
built with Streamlit, Plotly, Pandas, NumPy, and Google Cloud Firestore.

Usage:
    streamlit run app.py
"""

import os
import sys
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Ensure backend directory is in python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from analytics import AfterBuyAnalytics
from database import test_connection

# =============================================================================
# STREAMLIT PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="AfterBuy | Reliability & Warranty Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# MODERN DARK THEME CSS
# =============================================================================
CUSTOM_CSS = """
<style>
    /* Global Background and Fonts */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
    }

    /* Metric Cards */
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -2px rgba(0, 0, 0, 0.3);
        margin-bottom: 16px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: #38bdf8;
    }
    .kpi-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.2;
    }
    .kpi-subtitle {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 6px;
    }

    /* Recommendation Cards */
    .rec-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 14px;
        border-left: 5px solid #64748b;
    }
    .rec-card-high {
        border-left-color: #f43f5e;
        background: linear-gradient(90deg, rgba(244, 63, 94, 0.1) 0%, #1e293b 100%);
    }
    .rec-card-medium {
        border-left-color: #fbbf24;
        background: linear-gradient(90deg, rgba(251, 191, 36, 0.1) 0%, #1e293b 100%);
    }
    .rec-card-low {
        border-left-color: #38bdf8;
        background: linear-gradient(90deg, rgba(56, 189, 248, 0.1) 0%, #1e293b 100%);
    }
    .rec-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .badge-high { background-color: #f43f5e; color: #ffffff; }
    .badge-medium { background-color: #fbbf24; color: #0f172a; }
    .badge-low { background-color: #38bdf8; color: #0f172a; }

    /* Chart Container Styling */
    .chart-container {
        background-color: #131d31;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
    }

    /* Headers */
    h1, h2, h3, h4 {
        color: #f8fafc !important;
        font-weight: 700 !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =============================================================================
# DATA FETCHING & CACHING
# =============================================================================
@st.cache_data(ttl=300, show_spinner=False)
def load_analytics_data():
    """
    Fetch and compute full analytics report from Firestore MongoDB.
    Cached for 5 minutes (300 seconds) for fast interactive rendering.
    """
    engine = AfterBuyAnalytics()
    engine.load_data()
    return engine.generate_full_report()

# =============================================================================
# PLOTLY COLOR PALETTES & THEME
# =============================================================================
PLOTLY_THEME = "plotly_dark"
COLOR_PRIMARY = "#38bdf8"    # Sky / Cyan
COLOR_SECONDARY = "#818cf8"  # Indigo
COLOR_SUCCESS = "#34d399"    # Emerald
COLOR_WARNING = "#fbbf24"    # Amber
COLOR_DANGER = "#f43f5e"     # Rose / Red
COLOR_PURPLE = "#a855f7"     # Purple
CHART_BG = "rgba(0,0,0,0)"

def apply_chart_layout(fig, height=380, title=None):
    """Applies clean consistent dark styling to any Plotly figure."""
    fig.update_layout(
        template=PLOTLY_THEME,
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        height=height,
        title=dict(text=title, font=dict(size=15, color="#f8fafc", family="Inter")) if title else None,
        margin=dict(l=20, r=20, t=50 if title else 20, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#cbd5e1")
        ),
        font=dict(color="#94a3b8", family="Inter"),
        xaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155"),
        yaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155")
    )
    return fig

# =============================================================================
# SIDEBAR NAVIGATION & STATUS
# =============================================================================
with st.sidebar:
    st.markdown("## 🛡️ **AfterBuy**")
    st.caption("Product Reliability & Warranty Intelligence")
    st.markdown("---")

    # Navigation Menu
    nav_option = st.radio(
        "Navigation Modules",
        options=[
            "📊 Executive Overview",
            "🛡️ Product Reliability",
            "📜 Warranty Intelligence",
            "🔍 Defect Intelligence",
            "🔧 Repair Analytics",
            "💡 Smart Business Insights"
        ],
        index=0
    )

    st.markdown("---")

    # Refresh Data Button
    if st.button("🔄 Refresh Data", use_container_width=True, help="Clear cache and re-fetch latest records from Firestore"):
        st.cache_data.clear()
        st.rerun()

    # Database Status Widget
    st.markdown("### 🔌 System Status")
    db_ok = test_connection()
    if db_ok:
        st.success("Firestore (MongoDB): **Connected** 🟢", icon="✅")
    else:
        st.error("Firestore: **Disconnected** 🔴", icon="⚠️")

    st.caption("Database: Google Cloud Firestore Enterprise")
    st.caption("Records Loaded: 2,300 across 5 collections")
    st.markdown("---")
    st.caption(f"Last Refreshed: {datetime.now().strftime('%H:%M:%S')}")

# =============================================================================
# LOAD DATA WITH SPINNER & ERROR HANDLING
# =============================================================================
try:
    with st.spinner("Fetching data from Firestore and computing analytics..."):
        report = load_analytics_data()
except Exception as e:
    st.error(f"❌ Failed to load data from Firestore: {e}")
    st.info("Please verify that your `FIRESTORE_MONGO_URI` is configured properly in `.env`.")
    st.stop()

# Extract sections
summary = report["executive_summary"]
rel = report["product_reliability"]
war = report["warranty_intelligence"]
defects = report["defect_intelligence"]
rep = report["repair_analytics"]
ins = report["business_insights"]


# =============================================================================
# 1. EXECUTIVE OVERVIEW MODULE
# =============================================================================
if nav_option == "📊 Executive Overview":
    st.markdown("# 📊 Executive Overview")
    st.markdown("High-level product reliability, warranty financial health, and post-sale operational summary.")
    st.markdown("")

    # Top KPI Row (4 cards)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Products</div>
            <div class="kpi-value">{summary['total_products']:,}</div>
            <div class="kpi-subtitle">Across 7 Categories</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Units Sold</div>
            <div class="kpi-value">{summary['total_sales_units']:,}</div>
            <div class="kpi-subtitle">Revenue: ₹{summary['total_sales_revenue_inr']/1e6:.2f}M</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Warranty Claims</div>
            <div class="kpi-value">{summary['total_claims']:,}</div>
            <div class="kpi-subtitle">Claim Rate: <b style="color: #fbbf24;">{summary['warranty_claim_rate_pct']}%</b></div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Warranty Expenditure</div>
            <div class="kpi-value">₹{summary['total_warranty_expenditure_inr']/1e3:.1f}K</div>
            <div class="kpi-subtitle">WCI: <b style="color: #38bdf8;">{summary['warranty_cost_index_pct']}%</b> of revenue</div>
        </div>
        """, unsafe_allow_html=True)

    # Second KPI Row (3 cards)
    c5, c6, c7 = st.columns(3)
    with c5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Fleet Reliability Score</div>
            <div class="kpi-value">{summary['overall_avg_reliability_score']} <span style="font-size:1.1rem; color:#94a3b8;">/ 100</span></div>
            <div class="kpi-subtitle">Weighted Multi-Factor Health</div>
        </div>
        """, unsafe_allow_html=True)
    with c6:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Avg Repair Turnaround</div>
            <div class="kpi-value">{summary['average_repair_duration_days']} <span style="font-size:1.1rem; color:#94a3b8;">Days</span></div>
            <div class="kpi-subtitle">Avg Repair Cost: ₹{summary['average_repair_cost_inr']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c7:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Repeat Repair Rate</div>
            <div class="kpi-value">{summary['repeat_repair_rate_pct']}%</div>
            <div class="kpi-subtitle">Defects Logged: {summary['total_defects_reported']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # High-level Visuals
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        cat_df = pd.DataFrame(rel["category_reliability"])
        fig_cat = go.Figure()
        fig_cat.add_trace(go.Bar(
            x=cat_df["category"],
            y=cat_df["avg_reliability_score"],
            name="Reliability Score",
            marker_color=COLOR_PRIMARY,
            text=cat_df["avg_reliability_score"],
            textposition="auto"
        ))
        fig_cat.add_trace(go.Scatter(
            x=cat_df["category"],
            y=cat_df["category_failure_rate_pct"],
            name="Failure Rate (%)",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color=COLOR_DANGER, width=3),
            marker=dict(size=8)
        ))
        fig_cat.update_layout(
            yaxis2=dict(
                title="Failure Rate (%)",
                overlaying="y",
                side="right",
                showgrid=False
            ),
            yaxis=dict(title="Score (0-100)", range=[0, 100])
        )
        apply_chart_layout(fig_cat, height=360, title="Category Reliability vs Failure Rate")
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_chart2:
        status_df = pd.DataFrame(list(war["claims_by_status"].items()), columns=["Status", "Count"])
        fig_donut = px.pie(
            status_df,
            names="Status",
            values="Count",
            hole=0.6,
            color="Status",
            color_discrete_map={
                "Approved": COLOR_SUCCESS,
                "Under Review": COLOR_PRIMARY,
                "Pending": COLOR_WARNING,
                "Rejected": COLOR_DANGER
            }
        )
        apply_chart_layout(fig_donut, height=360, title="Warranty Claims Status Breakdown")
        st.plotly_chart(fig_donut, use_container_width=True)


# =============================================================================
# 2. PRODUCT RELIABILITY MODULE
# =============================================================================
elif nav_option == "🛡️ Product Reliability":
    st.markdown("# 🛡️ Product Reliability Analytics")
    st.markdown("Product failure rate analysis, multi-factor reliability scoring, and category benchmarks.")
    st.markdown("")

    # Filter by category
    categories = sorted(list(set(p["category"] for p in rel["product_reliability_table"])))
    selected_cats = st.multiselect(
        "Filter by Product Category:",
        options=categories,
        default=categories
    )

    filtered_prods = [p for p in rel["product_reliability_table"] if p["category"] in selected_cats]
    df_filtered = pd.DataFrame(filtered_prods)

    # Top summary metrics for filtered selection
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Products in View", len(df_filtered))
    with m2:
        avg_score = round(df_filtered["reliability_score"].mean(), 1) if not df_filtered.empty else 0
        st.metric("Avg Reliability Score", f"{avg_score} / 100")
    with m3:
        avg_fail = round(df_filtered["failure_rate_pct"].mean(), 1) if not df_filtered.empty else 0
        st.metric("Avg Failure Rate", f"{avg_fail}%")
    with m4:
        tot_claims = int(df_filtered["total_claims"].sum()) if not df_filtered.empty else 0
        st.metric("Total Claims", tot_claims)

    st.markdown("---")

    # Top 5 Most and Least Reliable Cards
    col_least, col_most = st.columns(2)

    with col_least:
        st.markdown("### ⚠️ Top 5 Least Reliable Products")
        least_df = pd.DataFrame(rel["least_reliable_products"])
        fig_least = px.bar(
            least_df,
            x="reliability_score",
            y="product_name",
            orientation="h",
            color="reliability_score",
            color_continuous_scale=["#f43f5e", "#fbbf24"],
            text="reliability_score",
            labels={"reliability_score": "Score", "product_name": "Product"}
        )
        fig_least.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        apply_chart_layout(fig_least, height=300)
        st.plotly_chart(fig_least, use_container_width=True)

    with col_most:
        st.markdown("### ✅ Top 5 Most Reliable Products")
        most_df = pd.DataFrame(rel["most_reliable_products"])
        fig_most = px.bar(
            most_df,
            x="reliability_score",
            y="product_name",
            orientation="h",
            color="reliability_score",
            color_continuous_scale=["#38bdf8", "#34d399"],
            text="reliability_score",
            labels={"reliability_score": "Score", "product_name": "Product"}
        )
        fig_most.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        apply_chart_layout(fig_most, height=300)
        st.plotly_chart(fig_most, use_container_width=True)

    st.markdown("---")

    # Scatter Chart: Reliability Score vs Failure Rate
    st.markdown("### 🔍 Reliability vs Failure Rate Distribution")
    fig_scatter = px.scatter(
        df_filtered,
        x="failure_rate_pct",
        y="reliability_score",
        color="category",
        size="units_sold",
        hover_data=["product_id", "product_name", "total_claims", "price"],
        labels={
            "failure_rate_pct": "Failure Rate (%)",
            "reliability_score": "Reliability Score (0-100)",
            "category": "Category",
            "units_sold": "Units Sold"
        }
    )
    apply_chart_layout(fig_scatter, height=420, title="Reliability Score vs Failure Rate (Bubble size = Units Sold)")
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Searchable Interactive Table
    with st.expander("📋 View Complete Filtered Product Catalog"):
        st.dataframe(
            df_filtered[[
                "product_id", "product_name", "brand", "category",
                "price", "units_sold", "total_claims", "failure_rate_pct", "reliability_score"
            ]].rename(columns={
                "product_id": "Product ID",
                "product_name": "Product Name",
                "brand": "Brand",
                "category": "Category",
                "price": "Price (₹)",
                "units_sold": "Units Sold",
                "total_claims": "Claims",
                "failure_rate_pct": "Failure Rate (%)",
                "reliability_score": "Score / 100"
            }),
            use_container_width=True,
            hide_index=True
        )


# =============================================================================
# 3. WARRANTY INTELLIGENCE MODULE
# =============================================================================
elif nav_option == "📜 Warranty Intelligence":
    st.markdown("# 📜 Warranty Intelligence")
    st.markdown("Warranty claims status, claims volume timeline, expenditure allocation, and cost index.")
    st.markdown("")

    # Financial KPI Cards
    w1, w2, w3, w4 = st.columns(4)
    with w1:
        st.metric("Total Warranty Claims", f"{war['total_claims']:,}")
    with w2:
        st.metric("Approved Claims Rate", f"{war['claims_by_status_pct'].get('Approved', 0):.1f}%", f"{war['claims_by_status'].get('Approved', 0)} claims")
    with w3:
        st.metric("Total Warranty Cost", f"₹{war['total_warranty_expenditure_inr']:,.0f}")
    with w4:
        st.metric("Warranty Cost Index (WCI)", f"{war['warranty_cost_index_pct']}%", "of Sales Revenue")

    st.markdown("---")

    # Visuals: Trends & Status
    col_trend, col_cost_cat = st.columns(2)

    with col_trend:
        trends_df = pd.DataFrame(war["monthly_claim_trends"])
        fig_trend = px.line(
            trends_df,
            x="year_month",
            y="claim_count",
            markers=True,
            labels={"year_month": "Month", "claim_count": "Claims Filed"},
            line_shape="spline"
        )
        fig_trend.update_traces(line_color=COLOR_PRIMARY, marker=dict(size=6, color="#38bdf8"))
        apply_chart_layout(fig_trend, height=360, title="Monthly Warranty Claim Filing Trends")
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_cost_cat:
        cost_cat_df = pd.DataFrame(war["warranty_cost_by_category"])
        fig_cost_bar = px.bar(
            cost_cat_df,
            x="category",
            y="warranty_cost",
            color="warranty_cost",
            color_continuous_scale=["#38bdf8", "#818cf8"],
            labels={"category": "Product Category", "warranty_cost": "Warranty Expenses (₹)"},
            text_auto=".2s"
        )
        fig_cost_bar.update_layout(coloraxis_showscale=False)
        apply_chart_layout(fig_cost_bar, height=360, title="Warranty Expenses by Product Category")
        st.plotly_chart(fig_cost_bar, use_container_width=True)

    st.markdown("---")

    # Detailed Table of Category Warranty Metrics
    st.markdown("### 📊 Warranty Cost Breakdown by Category")
    st.dataframe(
        cost_cat_df.rename(columns={
            "category": "Category",
            "warranty_cost": "Total Warranty Cost (₹)",
            "repair_count": "Repairs Logged",
            "claim_count": "Claims Filed"
        }),
        use_container_width=True,
        hide_index=True
    )


# =============================================================================
# 4. DEFECT INTELLIGENCE MODULE
# =============================================================================
elif nav_option == "🔍 Defect Intelligence":
    st.markdown("# 🔍 Defect Intelligence")
    st.markdown("Root-cause categorization, severity breakdown, longitudinal defect trends, and category matrix.")
    st.markdown("")

    # KPI Row
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.metric("Total Defects Logged", defects["total_defects"])
    with d2:
        top_defect_name = defects["most_frequent_defects"][0]["defect_category"]
        top_defect_pct = defects["most_frequent_defects"][0]["share_pct"]
        st.metric("Leading Defect Type", top_defect_name, f"{top_defect_pct}% share")
    with d3:
        crit_count = defects["severity_distribution"].get("Critical", {}).get("count", 0)
        crit_pct = defects["severity_distribution"].get("Critical", {}).get("share_pct", 0)
        st.metric("Critical Defects", crit_count, f"{crit_pct}% of total")
    with d4:
        repeat_yes = defects["repeat_failure_counts"].get("Yes", 0)
        st.metric("Repeat Defect Incidents", repeat_yes, f"{round((repeat_yes/500)*100, 1)}% repeat rate")

    st.markdown("---")

    # Charts Row 1: Frequency & Severity
    col_d1, col_d2 = st.columns(2)

    with col_d1:
        freq_df = pd.DataFrame(defects["most_frequent_defects"])
        fig_freq = px.bar(
            freq_df,
            x="defect_count",
            y="defect_category",
            orientation="h",
            color="defect_count",
            color_continuous_scale=["#38bdf8", "#a855f7"],
            labels={"defect_count": "Incidents", "defect_category": "Defect Category"},
            text="defect_count"
        )
        fig_freq.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        apply_chart_layout(fig_freq, height=360, title="Defect Category Frequency Ranking")
        st.plotly_chart(fig_freq, use_container_width=True)

    with col_d2:
        sev_list = [
            {"Severity": k, "Count": v["count"]}
            for k, v in defects["severity_distribution"].items()
        ]
        sev_df = pd.DataFrame(sev_list)
        fig_sev = px.pie(
            sev_df,
            names="Severity",
            values="Count",
            hole=0.55,
            color="Severity",
            color_discrete_map={
                "Critical": COLOR_DANGER,
                "High": "#f97316",    # Orange
                "Medium": COLOR_WARNING,
                "Low": COLOR_SUCCESS
            }
        )
        apply_chart_layout(fig_sev, height=360, title="Defect Severity Distribution")
        st.plotly_chart(fig_sev, use_container_width=True)

    st.markdown("---")

    # Category vs Defect Heatmap
    st.markdown("### 🧬 Product Category vs Defect Type Cross-Tabulation")
    crosstab_df = pd.DataFrame(defects["category_vs_defect"])
    if not crosstab_df.empty:
        crosstab_indexed = crosstab_df.set_index("category")
        fig_heat = px.imshow(
            crosstab_indexed,
            color_continuous_scale="Viridis",
            labels=dict(x="Defect Category", y="Product Category", color="Incidents"),
            text_auto=True,
            aspect="auto"
        )
        apply_chart_layout(fig_heat, height=380, title="Defect Incident Matrix")
        st.plotly_chart(fig_heat, use_container_width=True)


# =============================================================================
# 5. REPAIR ANALYTICS MODULE
# =============================================================================
elif nav_option == "🔧 Repair Analytics":
    st.markdown("# 🔧 Repair Performance Analytics")
    st.markdown("Turnaround duration benchmarks, expense distribution, repeat repair rates, and recurring models.")
    st.markdown("")

    # KPI Row
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.metric("Total Completed Repairs", rep["total_repairs"])
    with r2:
        st.metric("Avg Repair Duration", f"{rep['average_repair_duration_days']} Days", f"Median: {rep['median_repair_duration_days']} d")
    with r3:
        st.metric("Avg Repair Cost", f"₹{rep['average_repair_cost_inr']:,.0f}", f"Median: ₹{rep['median_repair_cost_inr']:,.0f}")
    with r4:
        st.metric("Repeat Repair Rate", f"{rep['repeat_repair_rate_pct']}%", f"{rep['claims_with_multiple_repairs']} multiple repairs")

    st.markdown("---")

    # Visuals: Repair Status Summary & Duration
    col_rep1, col_rep2 = st.columns(2)

    with col_rep1:
        rep_status_df = pd.DataFrame(rep["repair_status_summary"])
        fig_status = px.bar(
            rep_status_df,
            x="repair_status",
            y="count",
            color="avg_cost",
            color_continuous_scale="Blues",
            labels={"repair_status": "Repair Status", "count": "Repairs", "avg_cost": "Avg Cost (₹)"},
            text="count"
        )
        apply_chart_layout(fig_status, height=360, title="Repair Counts and Average Cost by Outcome")
        st.plotly_chart(fig_status, use_container_width=True)

    with col_rep2:
        fig_duration = px.bar(
            rep_status_df,
            x="repair_status",
            y="avg_duration_days",
            color="repair_status",
            color_discrete_sequence=[COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER],
            labels={"repair_status": "Repair Status", "avg_duration_days": "Avg Duration (Days)"},
            text="avg_duration_days"
        )
        apply_chart_layout(fig_duration, height=360, title="Average Turnaround Days by Repair Status")
        st.plotly_chart(fig_duration, use_container_width=True)

    st.markdown("---")

    # Products with Recurring Repairs
    st.markdown("### 🔁 Top Products with Recurring Failures (≥ 2 Repairs)")
    rec_prods_df = pd.DataFrame(rep["top_recurring_failure_products"])
    if not rec_prods_df.empty:
        st.dataframe(
            rec_prods_df[[
                "product_id", "product_name", "brand", "category",
                "repair_count", "total_repair_cost", "avg_duration_days"
            ]].rename(columns={
                "product_id": "Product ID",
                "product_name": "Product Name",
                "brand": "Brand",
                "category": "Category",
                "repair_count": "Repairs Count",
                "total_repair_cost": "Total Repair Cost (₹)",
                "avg_duration_days": "Avg Duration (Days)"
            }),
            use_container_width=True,
            hide_index=True
        )


# =============================================================================
# 6. SMART BUSINESS INSIGHTS MODULE
# =============================================================================
elif nav_option == "💡 Smart Business Insights":
    st.markdown("# 💡 Smart Business Insights & Prescriptive QA")
    st.markdown("Rule-based operational insights, failure rate outlier detection, and action-oriented QA recommendations.")
    st.markdown("")

    # Prescriptive Recommendations Cards
    st.markdown("### 🎯 Quality Engineering & Warranty Action Plan")

    for rec in ins["recommendations"]:
        sev = rec["severity"].lower()
        badge_class = f"badge-{sev}"
        card_class = f"rec-card rec-card-{sev}"

        st.markdown(f"""
        <div class="{card_class}">
            <span class="rec-badge {badge_class}">{rec['severity'].upper()} PRIORITY</span>
            <span style="color: #94a3b8; font-size: 0.85rem; margin-left: 8px;">Module: {rec['module']}</span>
            <div style="margin-top: 8px; font-size: 1rem; color: #f1f5f9;">
                <b>Finding:</b> {rec['finding']}
            </div>
            <div style="margin-top: 6px; font-size: 0.95rem; color: #38bdf8;">
                <b>Recommended Action:</b> {rec['recommendation']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Statistical Outliers Table (Products with failure rates > mean + 1.5*std)
    st.markdown("### 🚨 Statistical Failure Outliers")
    st.caption("Products exceeding the statistical anomaly failure threshold (Mean + 1.5 × Std Dev = 75.1%)")

    outliers_df = pd.DataFrame(ins["high_risk_products"])
    if not outliers_df.empty:
        st.dataframe(
            outliers_df.rename(columns={
                "product_id": "Product ID",
                "product_name": "Product Name",
                "category": "Category",
                "failure_rate_pct": "Failure Rate (%)",
                "threshold_pct": "Threshold (%)"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No statistical outliers currently detected above the threshold.")

    st.markdown("---")

    # Expensive Categories Breakdown
    st.markdown("### 💰 High-Impact Warranty Categories")
    st.caption("Ranked by total repair expenditure and Warranty Cost Index (WCI)")
    exp_df = pd.DataFrame(ins["expensive_warranty_categories"])
    if not exp_df.empty:
        st.dataframe(
            exp_df.rename(columns={
                "category": "Product Category",
                "category_warranty_cost": "Total Warranty Cost (₹)",
                "category_revenue": "Total Category Revenue (₹)",
                "category_wci_pct": "Category WCI (%)"
            }),
            use_container_width=True,
            hide_index=True
        )

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.8rem;'>"
    "AfterBuy – Product Reliability & Warranty Intelligence System | Built with Streamlit, Plotly & Firestore MongoDB"
    "</div>",
    unsafe_allow_html=True
)
