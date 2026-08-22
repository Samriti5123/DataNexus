# DataLens – Interactive Data Analysis & Business Intelligence Platform

**DataLens** is an end-to-end data exploration, cleaning, visualization, and strategic AI intelligence platform designed for data scientists, analysts, and business executives.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────────┐
│  1. Ingest   │ ──> │   2. Clean   │ ──> │   3. Analyze │ ──> │ 4. Visualize │ ──> │ 5. AI Insights │
│  CSV/XLSX/JSON│    │  Audit & Prep│     │ EDA & Pivots │     │ Multi-Charts │     │ Executive Rep. │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └────────────────┘
```

---

## Key Features

### 1. Ingestion & Previews
- **Multi-Format Ingestion**: Drag & drop support for CSV, TSV, Excel (`.xlsx`, `.xls`), and JSON.
- **Auto-Detection**: Automatic delimiter sniffing (`,`, `\t`, `;`, `|`) and multi-encoding fallback (`utf-8`, `latin-1`, `cp1252`).
- **5 Built-in Enterprise Sample Datasets**:
  - *Superstore Retail & Sales* (650 orders with Sales, Profit, Discount, Region)
  - *Telecom Customer Churn* (600 accounts with tenure, charges, tickets & churn flags)
  - *HR Workforce & Attrition* (550 employees tracking satisfaction, salary, department)
  - *FinTech Fraud & Risk* (600 transactions with risk scores and foreign payments)
  - *SaaS Product & MRR Metrics* (500 SaaS accounts analyzing tiers, MRR, usage)

### 2. Data Health Audit & Interactive Cleaning Studio
- **Data Health Score (0-100%)**: Evaluates Completeness, Uniqueness, and Consistency with actionable alert notifications.
- **Missing Value Studio**: Mean, Median, Mode, Constant, Forward Fill, Backward Fill, and Drop strategies.
- **Outlier Studio**: IQR (1.5x/3x) and Z-score outlier detection with Clip (Winsorize) or Remove actions.
- **Deduplication**: Match exact records or custom column subsets.
- **Type Converter**: Cast strings to float, integer, datetime, categorical, boolean.
- **Text Normalizer**: Trim whitespace, lowercase, uppercase, title case, and regex replacement.
- **Calculated Columns**: Multi-column arithmetic, ratios, condition-based tagging, and binning.
- **ETL Recipe Generator**: Instant 1-click export of the full transformation history as a reproducible Python script (`cleaning_recipe.py`).
- **Full History**: Multi-level Undo, Redo, and Reset to Raw Data.

### 3. Exploratory Data Analysis (EDA)
- **Column Profiling**: Distribution summaries, quantiles (Q1, Median, Q3), skewness, zero counts, and mini distribution histograms.
- **Correlation Heatmap**: Pearson and Spearman correlation matrices with top correlated pair ranking cards.
- **Dynamic Pivot Sandbox**: Multi-dimensional cross-tabulation and GroupBy aggregations.

### 4. Multi-Dimensional Visualization Studio
- **10 Chart Types**: Bar, Stacked Bar, Horizontal Bar, Line, Area, Scatter, Bubble, Pie, Donut, Histogram, Boxplot.
- **Studio Controls**: Custom metrics, aggregation functions (`sum`, `mean`, `median`, `min`, `max`, `count`), sort direction, top limit, and color palettes (*Emerald*, *Cyber Indigo*, *Sunset Warmth*).
- **High-Res Export**: 1-click PNG image download.

### 5. Automated AI Business Insights & Executive Reports
- **Executive KPI Cards**: Instant calculation of total volumes, averages, peak values, and spreads.
- **Machine-Learned Key Driver Analysis**: Uses Random Forest & Decision Trees to determine what variables drive target business KPIs (e.g., *Profit*, *Churn*, *Risk Score*).
- **Cohort Analysis**: Automated discovery of top-performing vs under-performing segments.
- **C-Suite Strategic Recommendations**: Actionable bullet points tailored for leadership decisions.
- **"Ask DataLens AI" Natural Language Assistant**: Query your data in plain English (e.g. *"Top 5 category by sales"* or *"Average discount by region"*).
- **Executive HTML / PDF Report**: Printable, standalone intelligence report.

---

## Quickstart & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Install Backend Dependencies
```bash
pip install fastapi uvicorn pandas numpy scipy scikit-learn openpyxl python-multipart pydantic jinja2
```

### 2. Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### 3. Launch Both Servers
Run the 1-click starter script:
```bash
python run_app.py
```

- **Frontend Application**: [http://localhost:5173](http://localhost:5173)
- **Backend API & Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Running Tests
Run the backend test suite:
```bash
python backend/test_backend.py
```
Build the frontend:
```bash
cd frontend && npm run build
```
