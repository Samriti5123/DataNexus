# DataNexus – Interactive Data Analysis & Business Intelligence Platform

**DataNexus** is an end-to-end data exploration, cleaning, visualization, and strategic intelligence platform designed for data scientists, analysts, and business executives.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────────┐
│  1. Ingest   │ ──> │   2. Clean   │ ──> │   3. Analyze │ ──> │ 4. Visualize │ ──> │ 5. AI Insights │
│  CSV/XLSX/JSON│    │  Audit & Prep│     │ EDA & Pivots │     │ Multi-Charts │     │ Executive Rep. │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └────────────────┘
```

---

## Modern Blue & Cyan Visual Theme

DataNexus features a modern dark theme optimized for analytical readability:
- **Main Background**: Deep Navy (`#0B1220`)
- **Card & Panel Background**: Dark Blue-Grey (`#111C2E`)
- **Primary Accent**: Electric Blue (`#3B82F6`)
- **Secondary Accent**: Cyan Glow (`#06B6D4`)
- **Main Typography**: Crisp White (`#F8FAFC`)
- **Secondary Typography**: Light Slate Grey (`#94A3B8`)
- **Subtle Borders**: Blue-Grey (`#263449`)
- **Status & Health Indicators**: Preserved semantic colours (Emerald for healthy/pass, Amber for warning, Rose for critical/error)

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
- **Studio Controls**: Custom metrics, aggregation functions (`sum`, `mean`, `median`, `min`, `max`, `count`), sort direction, top limit, and modern color palettes (*DataNexus Blue*, *Cyan Glow*, *Cyber Indigo*, *Sunset*).
- **High-Res Export**: 1-click PNG image download.

### 5. Automated AI Business Insights & Natural Language Assistant
- **Executive KPI Cards**: Instant calculation of total volumes, averages, peak values, and spreads.
- **Machine-Learned Key Driver Analysis**: Uses Random Forest & Decision Trees to determine what variables drive target business KPIs (e.g., *Profit*, *Attrition*, *Risk Score*).
- **Cohort Analysis**: Automated discovery of top-performing vs under-performing segments.
- **C-Suite Strategic Recommendations**: Actionable bullet points tailored for leadership decisions.
- **Ask DataNexus AI**: Rule-based natural language assistant supporting:
  1. **Counts**: "How many employees by Department?", "Count by JobRole", "Count by Category"
  2. **Aggregations**: "Average MonthlyIncome by Department", "Maximum Age", "Median YearsAtCompany by JobRole", "Sum of MonthlyIncome by Department", "Average Sales by Category"
  3. **Top N and Bottom N**: "Top 5 by MonthlyIncome", "Bottom 5 by Age", "Top 5 by Profit", "Bottom 5 by Sales"
  4. **Rates and Percentages**: "Attrition rate by Department", "Percentage of Attrition by OverTime", "Percentage of employees by Department"
  5. **Multi-Condition Filters**: "Filter Age > 40 and OverTime = Yes", "Show employees where Department = Sales and Age > 35", "Show records where Profit > 100 and Region = East"
  6. **Highest and Lowest Groups**: "Which Department has the highest average MonthlyIncome?", "Which JobRole has the most Attrition?", "Which Category has the highest average Sales?"
  7. **Correlations**: "Correlation between Age and MonthlyIncome", "Correlation between Sales and Profit"
  8. **Distributions**: "Distribution of JobSatisfaction", "Distribution of Department", "Distribution of Region"
- **Comprehensive HR Employee Attrition Intelligence (15 Questions)**:
  1. What is the overall attrition rate?
  2. How many employees left the company?
  3. How many employees stayed?
  4. Which department has the highest attrition?
  5. Which job role has the highest attrition?
  6. What is the attrition rate by department?
  7. How many employees left from each department?
  8. Does overtime affect attrition?
  9. What is the average salary of employees who left?
  10. What is the average age of employees who left?
  11. Which age group has the highest attrition?
  12. What is the attrition rate by gender?
  13. How many employees with low job satisfaction left?
  14. What is the attrition rate among employees who travel frequently?
  15. Compare employees who left and employees who stayed.
- **Dynamic Suggestion Chips**: 6 automatically generated suggestion chips tailored to uploaded columns.
- **Executive HTML Report**: Printable, standalone executive report.

---

## Windows Setup & Quickstart

### Prerequisites
1. **Python 3.10+**: Ensure `python` and `pip` are added to your Windows PATH.
2. **Node.js 18+ & npm**: Download from [https://nodejs.org/](https://nodejs.org/) and ensure `npm` is in your PATH.

### 1. Install Backend Dependencies
In PowerShell or Command Prompt:
```powershell
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies (One-Time Setup)
```powershell
cd frontend
npm install
cd ..
```

### 3. Launch the Application (1-Click Startup)
Run the startup script:
```powershell
python run_app.py
```

The script will automatically:
1. Start the FastAPI backend on `http://127.0.0.1:8000`.
2. Start the React/Vite development server on `http://localhost:5173`.
3. Probe both health endpoints until both servers are fully initialized.
4. Automatically open your default browser to `http://localhost:5173`.
5. Cleanly shut down all child processes when pressing `Ctrl+C`.

- **Web Application**: [http://localhost:5173](http://localhost:5173)
- **API Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Running Automated Tests

Run the complete backend & query test suite:
```powershell
python backend/test_complete_suite.py
```

Run the unit tests:
```powershell
python backend/test_backend.py
```

Build the frontend bundle (type-checks and generates production build in `dist`):
```powershell
cd frontend
npm run build
```
