# AfterBuy – Project Requirements Document

## 1. Project Overview

**Project Name:** AfterBuy – Product Reliability & Warranty Intelligence System

**Purpose:** AfterBuy is a data analytics web application designed to help businesses analyze and improve product quality through after-sales data. It processes warranty claims, repair records, and defect reports to surface actionable insights via interactive dashboards.

**Target Users:** Product managers, quality assurance teams, warranty administrators, and business executives who need visibility into post-sale product performance.

---

## 2. Project Objectives

1. Provide a centralized dashboard for monitoring product reliability KPIs.
2. Analyze warranty claim patterns to identify cost drivers and high-risk products.
3. Track repair performance including turnaround times and first-time fix rates.
4. Detect recurring defects and cluster them by root cause.
5. Generate automated smart insights and anomaly alerts.
6. Allow flexible data exploration with filtering, sorting, and export.
7. Deliver a responsive, professional UI accessible on desktop and tablet.

---

## 3. Application Modules

### 3.1 Executive Dashboard
- High-level KPI cards (total claims, avg. repair time, defect rate, warranty cost).
- Trend charts showing month-over-month changes.
- Top 5 problematic products and categories.
- Quick navigation to detailed modules.

### 3.2 Product Reliability Analytics
- Product failure rate analysis over time.
- Mean Time Between Failures (MTBF) calculations.
- Reliability curves and survival analysis visualizations.
- Product comparison across categories and brands.

### 3.3 Warranty Intelligence
- Warranty claim volume and cost trends.
- Claim distribution by product, region, and time period.
- Warranty expiry tracking and coverage analysis.
- Cost-per-claim and cost-per-unit metrics.

### 3.4 Repair Analytics
- Repair turnaround time analysis.
- First-time fix rate tracking.
- Repeat repair identification.
- Technician and service center performance metrics.

### 3.5 Defect Intelligence
- Recurring defect pattern detection.
- Defect categorization and severity analysis.
- Root cause clustering and Pareto analysis.
- Defect trend tracking over product generations.

### 3.6 Smart Insights
- Automated anomaly detection in claims and defects.
- Statistical trend analysis and forecasting.
- Rule-based recommendations for quality improvement.
- Summary insights generated from data patterns.

### 3.7 Data Explorer
- Tabular view of all datasets with search and filter.
- Column-level sorting and multi-criteria filtering.
- Data export to CSV format.
- Cross-module data linking.

---

## 4. Technology Stack

### 4.1 Frontend
| Technology   | Purpose                                      |
|--------------|----------------------------------------------|
| HTML5        | Page structure and semantic markup            |
| CSS3         | Styling, layout, responsive design            |
| JavaScript   | Client-side logic, API calls, interactivity   |
| Plotly.js    | Interactive charts and data visualizations     |

### 4.2 Backend
| Technology         | Purpose                                  |
|--------------------|------------------------------------------|
| Python             | Backend logic and data processing         |
| Pandas             | Data manipulation and analysis            |
| NumPy              | Numerical computations                    |
| Firebase Functions | Serverless API endpoints (Python runtime) |

### 4.3 Infrastructure
| Technology          | Purpose                            |
|---------------------|------------------------------------|
| Firebase Firestore  | NoSQL cloud database                |
| Firebase Hosting    | Static frontend hosting             |
| Firebase Functions  | Backend API hosting                 |

---

## 5. Application Architecture

```
┌─────────────────────────────────────────────────────┐
│                    USER (Browser)                    │
│                                                     │
│   ┌─────────────────────────────────────────────┐   │
│   │          Frontend (HTML/CSS/JS)              │   │
│   │   • Dashboard Pages                         │   │
│   │   • Plotly.js Charts                        │   │
│   │   • API Client (fetch)                      │   │
│   └──────────────────┬──────────────────────────┘   │
│                      │ HTTP Requests                 │
└──────────────────────┼──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│          Firebase Cloud Functions (Python)            │
│                                                      │
│   ┌────────────────────────────────────────────┐     │
│   │           API Endpoints                     │     │
│   │   • /api/dashboard                          │     │
│   │   • /api/reliability                        │     │
│   │   • /api/warranty                           │     │
│   │   • /api/repairs                            │     │
│   │   • /api/defects                            │     │
│   │   • /api/insights                           │     │
│   │   • /api/explorer                           │     │
│   └────────────────┬───────────────────────────┘     │
│                    │                                  │
│   ┌────────────────▼───────────────────────────┐     │
│   │        Analytics Engine                     │     │
│   │   • Pandas / NumPy processing               │     │
│   │   • Statistical analysis                    │     │
│   │   • Anomaly detection                       │     │
│   └────────────────┬───────────────────────────┘     │
│                    │                                  │
└────────────────────┼─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│              Firebase Firestore                       │
│                                                      │
│   Collections:                                       │
│   • products         • warranty_claims               │
│   • repairs          • defects                       │
│   • insights_cache   • metadata                      │
└──────────────────────────────────────────────────────┘
```

### Data Flow

1. **User** opens the web app hosted on Firebase Hosting.
2. **Frontend** sends API requests to Firebase Cloud Functions.
3. **Cloud Functions** query Firestore and process data with Pandas/NumPy.
4. **Processed results** are returned as JSON to the frontend.
5. **Frontend** renders interactive charts using Plotly.js.

---

## 6. Data Strategy

### Initial Development
- Use **synthetic (generated) data** for all modules.
- Synthetic data will simulate realistic warranty claims, repair logs, defect records, and product catalogs.
- A Python data generation script will create and seed Firestore with sample data.

### Data Entities
| Entity           | Key Fields                                                    |
|------------------|---------------------------------------------------------------|
| Products         | product_id, name, category, brand, launch_date, price        |
| Warranty Claims  | claim_id, product_id, claim_date, issue, status, cost        |
| Repairs          | repair_id, claim_id, technician, start_date, end_date, status|
| Defects          | defect_id, product_id, defect_type, severity, reported_date  |

---

## 7. Non-Functional Requirements

- **Responsive Design:** Works on desktop (1024px+) and tablet (768px+).
- **Performance:** Dashboard loads within 3 seconds on standard connections.
- **Code Quality:** Beginner-friendly, well-commented, modular code.
- **Security:** No sensitive credentials committed to version control.
- **Scalability:** Architecture supports future feature additions.
- **Browser Support:** Chrome, Firefox, Edge (latest versions).

---

## 8. Development Phases

| Phase | Description                                  | Status      |
|-------|----------------------------------------------|-------------|
| 1     | Project setup and folder structure            | ✅ Complete  |
| 2     | Synthetic data generation                     | 🔲 Pending  |
| 3     | Backend API development                       | 🔲 Pending  |
| 4     | Frontend UI development                       | 🔲 Pending  |
| 5     | Firebase integration and deployment           | 🔲 Pending  |
| 6     | Testing and polish                            | 🔲 Pending  |
