# AfterBuy – Product Reliability & Warranty Intelligence System

A data analytics web application that analyzes product reliability, warranty claims, repair performance, and recurring product defects. Built with Python backend, Firebase infrastructure, and interactive Plotly.js visualizations.

---

## Project Overview

AfterBuy helps businesses gain actionable insights from their after-sales data. It transforms raw warranty claims, repair records, and defect reports into interactive dashboards and intelligent analytics — enabling better product quality decisions.

### Key Capabilities

- **Executive Dashboard** — High-level KPIs and trend summaries at a glance.
- **Product Reliability Analytics** — Failure rate analysis, MTBF calculations, and reliability curves.
- **Warranty Intelligence** — Warranty claim patterns, cost analysis, and expiry tracking.
- **Repair Analytics** — Repair turnaround times, success rates, and technician performance.
- **Defect Intelligence** — Recurring defect detection, root cause patterns, and defect clustering.
- **Smart Insights** — AI-driven anomaly detection and automated recommendations.
- **Data Explorer** — Flexible data filtering, sorting, and export capabilities.

---

## Technology Stack

| Layer                    | Technology                                            |
|--------------------------|-------------------------------------------------------|
| Interactive BI Dashboard | Streamlit, Plotly                                     |
| Backend Analytics Engine | Python 3.11+, Pandas, NumPy                           |
| Database Layer           | Google Cloud Firestore Enterprise (MongoDB-compatible)|
| Database Driver          | PyMongo, Python-Dotenv                                |
| Static Web Frontend      | HTML5, Vanilla CSS, JavaScript                        |

---

## Project Structure

```
AfterBuy/
├── app.py              # Streamlit Interactive Analytics Dashboard
├── backend/            # Python backend modules & scripts
│   ├── database.py     # Firestore MongoDB connection module
│   ├── analytics.py    # Core analytics engine (Pandas/NumPy)
│   ├── generate_data.py# Synthetic dataset generator
│   ├── validate_data.py# Dataset integrity validation script
│   ├── upload_data.py  # Idempotent CSV-to-Firestore upload script
│   ├── verify_database.py # Live database verification suite
│   └── test_analytics.py # Comprehensive analytics test suite (29 tests)
│
├── data/               # Validated synthetic datasets (5 CSVs, 2,300 records)
│   ├── products.csv    # 100 products catalog
│   ├── sales.csv       # 1,000 sales transactions
│   ├── warranty_claims.csv # 400 warranty claims
│   ├── repairs.csv     # 300 repair service logs
│   └── defects.csv     # 500 defect records
│
├── docs/               # Architecture & specification documentation
│   ├── project_requirements.md # Comprehensive requirements document
│   └── data_dictionary.md      # Full schema & relational data dictionary
│
├── frontend/           # Static web assets
├── .env.example        # Environment variable template
├── .gitignore          # Git exclusion rules (secrets, venv, cache)
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

---

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git
- A Google account (for Firebase — setup later)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AfterBuy
```

### 2. Create a Python Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment:

- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database Connection

Create a `.env` file in the project root:

```bash
FIRESTORE_MONGO_URI='your-firestore-mongodb-connection-string'
```

### 5. Launch the Streamlit Business Intelligence Dashboard

Run the interactive dashboard locally:

```bash
streamlit run app.py
```

Then open your browser at `http://localhost:8501`.

The dashboard features 6 interactive modules:
- **Executive Overview:** High-level KPIs, fleet reliability score, revenue vs. warranty expenditures.
- **Product Reliability:** Product scoring (0-100), category failure rates, top/least reliable products, interactive category filters.
- **Warranty Intelligence:** Claims approval breakdown, longitudinal filing trends, warranty cost by product category, and Warranty Cost Index (WCI).
- **Defect Intelligence:** Defect category ranking, severity distribution, monthly trends, and category-defect cross-tabulation matrix.
- **Repair Analytics:** Turnaround benchmarks, repair cost averages, repeat repair rates, and recurring failure models.
- **Smart Business Insights:** Prescriptive operational recommendations with priority badges and statistical outlier detection.

### 6. Run Test Suites & Verification

```bash
# Verify local synthetic CSV datasets
python backend/validate_data.py

# Verify live Firestore MongoDB collections & relational integrity
python backend/verify_database.py

# Run comprehensive analytics test suite (29 tests)
python backend/test_analytics.py
```

---

## Development Guidelines

- **Beginner-friendly** — Code is written with clarity and thorough comments.
- **Modular architecture** — Frontend and backend are fully separated.
- **No React or Node.js** — Pure HTML/CSS/JS frontend.
- **No paid APIs** — All functionality uses free-tier services or local processing.
- **Synthetic data first** — The app ships with generated sample data for development and demos.

---

## License

This project is for educational and portfolio purposes.
