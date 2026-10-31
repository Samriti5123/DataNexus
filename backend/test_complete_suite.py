import sys
import os
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.sample_data import get_superstore_sales_dataset
from backend.services.query_service import QueryService
from backend.services.visualize_service import VisualizeService

def run_tests():
    print("=" * 70)
    print("  DataNexus Complete AI Query & Feature Test Suite")
    print("=" * 70)

    # 1. Load HR Dataset
    hr_csv_path = os.path.join(os.path.dirname(__file__), 'data', 'WA_Fn-UseC_-HR-Employee-Attrition.csv')
    assert os.path.exists(hr_csv_path), f"HR CSV not found at {hr_csv_path}"
    hr_df = pd.read_csv(hr_csv_path)
    print(f"\n[OK] Loaded HR Dataset: {len(hr_df)} rows, {len(hr_df.columns)} columns.")

    # 2. Load Sales Dataset
    sales_df = get_superstore_sales_dataset()
    print(f"[OK] Loaded Superstore Sales: {len(sales_df)} rows, {len(sales_df.columns)} columns.")

    print("\n--- Testing PART 2: General Question Types (8 Categories) ---")

    # 1. Count
    q_counts = [
        (hr_df, "How many employees by Department?"),
        (hr_df, "Count by JobRole."),
        (sales_df, "Count by Category."),
        (sales_df, "Count by Region.")
    ]
    for df, q in q_counts:
        res = QueryService.execute_query(df, q)
        assert len(res["data"]) > 0, f"Failed for '{q}'"
        assert res.get("explanation"), f"No explanation for '{q}'"
        print(f"  [PASS] Count: '{q}' -> {len(res['data'])} rows. Explanation: {res['explanation'][:65]}...")

    # 2. Average, Sum, Min, Max, Median
    q_aggs = [
        (hr_df, "Average MonthlyIncome by Department."),
        (hr_df, "Maximum Age."),
        (hr_df, "Median YearsAtCompany by JobRole."),
        (hr_df, "Sum of MonthlyIncome by Department."),
        (sales_df, "Average Sales by Category.")
    ]
    for df, q in q_aggs:
        res = QueryService.execute_query(df, q)
        assert len(res["data"]) > 0, f"Failed for '{q}'"
        assert res.get("explanation"), f"No explanation for '{q}'"
        print(f"  [PASS] Aggregation: '{q}' -> Result: {res['data'][0]} | Exp: {res['explanation'][:65]}...")

    # 3. Top N and Bottom N
    q_topn = [
        (hr_df, "Top 5 by MonthlyIncome."),
        (hr_df, "Bottom 5 by Age."),
        (sales_df, "Top 5 by Profit."),
        (sales_df, "Bottom 5 by Sales.")
    ]
    for df, q in q_topn:
        res = QueryService.execute_query(df, q)
        assert len(res["data"]) == 5, f"Expected 5 rows for '{q}', got {len(res['data'])}"
        assert res.get("explanation"), f"No explanation for '{q}'"
        print(f"  [PASS] Top/Bottom N: '{q}' -> {len(res['data'])} records.")

    # 4. Rate and Percentage
    q_rates = [
        (hr_df, "Attrition rate by Department."),
        (hr_df, "Percentage of Attrition by OverTime."),
        (hr_df, "Percentage of employees by Department.")
    ]
    for df, q in q_rates:
        res = QueryService.execute_query(df, q)
        assert len(res["data"]) > 0, f"Failed for '{q}'"
        assert res.get("explanation"), f"No explanation for '{q}'"
        print(f"  [PASS] Rate/Pct: '{q}' -> {len(res['data'])} groups.")

    # 5. Multiple-condition Filters
    q_filters = [
        (hr_df, "Filter Age > 40 and OverTime = Yes."),
        (hr_df, "Show employees where Department = Sales and Age > 35."),
        (sales_df, "Show records where Profit > 100 and Region = East.")
    ]
    for df, q in q_filters:
        res = QueryService.execute_query(df, q)
        assert res["total_results"] >= 0, f"Failed for '{q}'"
        assert res.get("explanation"), f"No explanation for '{q}'"
        print(f"  [PASS] Multi-Filter: '{q}' -> {res['total_results']} matching records.")

    # 6. Highest and Lowest Groups
    q_groups = [
        (hr_df, "Which Department has the highest average MonthlyIncome?"),
        (hr_df, "Which JobRole has the most Attrition?"),
        (sales_df, "Which Category has the highest average Sales?")
    ]
    for df, q in q_groups:
        res = QueryService.execute_query(df, q)
        assert len(res["data"]) > 0, f"Failed for '{q}'"
        assert res.get("explanation"), f"No explanation for '{q}'"
        print(f"  [PASS] Group Ranking: '{q}' -> {res['explanation']}")

    # 7. Correlation
    q_corrs = [
        (hr_df, "Correlation between Age and MonthlyIncome."),
        (sales_df, "Correlation between Sales and Profit.")
    ]
    for df, q in q_corrs:
        res = QueryService.execute_query(df, q)
        assert len(res["data"]) == 1, f"Failed for '{q}'"
        assert res.get("explanation"), f"No explanation for '{q}'"
        print(f"  [PASS] Correlation: '{q}' -> {res['data'][0]} | Exp: {res['explanation']}")

    # 8. Distribution
    q_dists = [
        (hr_df, "Distribution of JobSatisfaction."),
        (hr_df, "Distribution of Department."),
        (sales_df, "Distribution of Region.")
    ]
    for df, q in q_dists:
        res = QueryService.execute_query(df, q)
        assert len(res["data"]) > 0, f"Failed for '{q}'"
        assert res.get("explanation"), f"No explanation for '{q}'"
        print(f"  [PASS] Distribution: '{q}' -> {len(res['data'])} buckets.")

    print("\n--- Testing PART 3: HR Employee Attrition Questions (All 15) ---")
    hr_15 = [
        ("1. Overall Attrition Rate", "What is the overall attrition rate?"),
        ("2. Employees Left", "How many employees left the company?"),
        ("3. Employees Stayed", "How many employees stayed?"),
        ("4. Highest Attrition Dept", "Which department has the highest attrition?"),
        ("5. Highest Attrition Role", "Which job role has the highest attrition?"),
        ("6. Rate by Department", "What is the attrition rate by department?"),
        ("7. Left from each Department", "How many employees left from each department?"),
        ("8. Overtime Impact", "Does overtime affect attrition?"),
        ("9. Average Salary of Left", "What is the average salary of employees who left?"),
        ("10. Average Age of Left", "What is the average age of employees who left?"),
        ("11. Age Group Highest Attrition", "Which age group has the highest attrition?"),
        ("12. Rate by Gender", "What is the attrition rate by gender?"),
        ("13. Low Satisfaction Left", "How many employees with low job satisfaction left?"),
        ("14. Frequent Travel Attrition", "What is the attrition rate among employees who travel frequently?"),
        ("15. Comparison Left vs Stayed", "Compare employees who left and employees who stayed.")
    ]

    for label, q in hr_15:
        res = QueryService.execute_query(hr_df, q)
        assert "data" in res and len(res["data"]) > 0, f"Failed for {label}: '{q}'"
        assert res.get("explanation"), f"Missing explanation for {label}"
        print(f"  [PASS] {label}:")
        print(f"         Query: \"{q}\"")
        print(f"         Table Columns: {res['columns']}")
        print(f"         Explanation: {res['explanation']}")

    print("\n--- Testing PART 4: Dynamic Suggestion Chips ---")
    hr_chips = QueryService.get_suggestion_chips(hr_df)
    print(f"  [PASS] HR Dataset Chips ({len(hr_chips)}): {hr_chips}")
    assert len(hr_chips) == 6, f"Expected 6 chips, got {len(hr_chips)}"
    for chip in hr_chips:
        c_res = QueryService.execute_query(hr_df, chip)
        assert len(c_res.get("data", [])) > 0, f"Chip '{chip}' failed to return data!"

    sales_chips = QueryService.get_suggestion_chips(sales_df)
    print(f"  [PASS] Sales Dataset Chips ({len(sales_chips)}): {sales_chips}")
    assert len(sales_chips) == 6, f"Expected 6 chips, got {len(sales_chips)}"
    for chip in sales_chips:
        c_res = QueryService.execute_query(sales_df, chip)
        assert len(c_res.get("data", [])) > 0, f"Chip '{chip}' failed to return data!"

    print("\n--- Testing PART 1 & 7: Visualize Service Modern Blue Palettes ---")
    chart = VisualizeService.build_chart_data(sales_df, 'bar', 'Category', 'Sales', palette_name='modern_blue')
    assert len(chart['datasets']) > 0
    assert chart['datasets'][0]['backgroundColor'].startswith('rgba(59, 130, 246')
    print("  [PASS] modern_blue default palette correctly rendered.")

    print("\n" + "=" * 70)
    print("  ALL 8 QUESTION TYPES + ALL 15 HR ATTRITION TESTS PASSED!")
    print("=" * 70)

if __name__ == '__main__':
    run_tests()
