import os
import sys
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.query_service import QueryService
from backend.sample_data import get_superstore_sales_dataset

def run_hybrid_tests():
    print("=" * 70)
    print("  Testing DataNexus Hybrid NLP + Rule-Based QA Engine")
    print("=" * 70)

    hr_csv = os.path.join(os.path.dirname(__file__), 'data', 'WA_Fn-UseC_-HR-Employee-Attrition.csv')
    df = pd.read_csv(hr_csv)
    print(f"[OK] Loaded dataset: {len(df)} rows, {len(df.columns)} columns.\n")

    # 1. Six User Core Examples
    core_tests = [
        ("1. Filter Condition", "Show employees above 35.", lambda r: r["total_results"] == 741 and r["engine"] == "nlp"),
        ("2. Column Projection", "Show Age and Department.", lambda r: set(r["columns"]) == {"Age", "Department"} and r["engine"] == "nlp"),
        ("3. Multi-Filter AND", "Show employees above 35 working overtime.", lambda r: r["total_results"] == 218 and r["engine"] == "nlp"),
        ("4. Aggregation with Cohort", "Find average income of employees who left.", lambda r: "4,787" in str(r["explanation"]) and r["engine"] == "nlp"),
        ("5. Group Comparison", "Compare attrition by department.", lambda r: len(r["data"]) == 3 and r["engine"] == "nlp"),
        ("6. Top-N Ranking", "Show the top five departments by attrition.", lambda r: len(r["data"]) == 3 and r["engine"] == "nlp"),
    ]

    for label, q, validator in core_tests:
        res = QueryService.execute_query(df, q)
        assert validator(res), f"Failed {label} on query: '{q}', got: {res}"
        print(f"  [PASS] {label}: \"{q}\"")
        print(f"         Engine: {res.get('engine')} | Rows: {res.get('total_results')} | Columns: {res.get('columns')}")
        print(f"         Answer: {res.get('answer', res.get('explanation'))}\n")

    # 2. Phrasing Variations (NLP flexibility)
    variations = [
        ("Filter phrasing 1", "Show employees older than 45", lambda r: r["total_results"] > 0 and r["engine"] == "nlp"),
        ("Filter phrasing 2", "List workers over 50 with overtime", lambda r: r["total_results"] > 0 and r["engine"] == "nlp"),
        ("Projection phrasing", "Select MonthlyIncome, JobRole, and Department", lambda r: "MonthlyIncome" in r["columns"] and r["engine"] == "nlp"),
        ("Between filter", "Show employees where age between 28 and 32", lambda r: r["total_results"] == 306 and r["engine"] == "nlp"),
        ("Aggregation phrasing", "What is the mean salary of employees who left?", lambda r: "4,787" in str(r["explanation"]) and r["engine"] == "nlp"),
        ("Ranking phrasing", "Top 3 departments by attrition", lambda r: len(r["data"]) == 3 and r["engine"] == "nlp"),
    ]

    print("--- Testing Phrasing Variations ---")
    for label, q, validator in variations:
        res = QueryService.execute_query(df, q)
        assert validator(res), f"Failed {label} on '{q}'"
        print(f"  [PASS] {label}: \"{q}\" -> {res.get('interpretation')} ({res.get('total_results')} results)")

    # 3. Empty Results Handling (Must return 0 records cleanly without fallback)
    print("\n--- Testing Empty Results Handling ---")
    res_empty = QueryService.execute_query(df, "Show employees above 95")
    assert res_empty["engine"] == "nlp", "Expected NLP engine to handle empty result directly"
    assert res_empty["total_results"] == 0, f"Expected 0 results, got {res_empty['total_results']}"
    assert len(res_empty["data"]) == 0
    print(f"  [PASS] Empty filter query returned 0 rows cleanly: {res_empty['explanation']}")

    # 4. Invalid Column / Unsupported Question (Fallback and Guidance)
    print("\n--- Testing Invalid Queries / Fallback Guidance ---")
    res_unsupported = QueryService.execute_query(df, "What is the quantum flux of the galaxy?")
    assert "supported_types" in res_unsupported, "Expected supported types in fallback guidance"
    assert len(res_unsupported["supported_types"]) > 0
    assert len(res_unsupported["examples"]) > 0
    print(f"  [PASS] Unsupported question returned helpful guidance with {len(res_unsupported['supported_types'])} categories and {len(res_unsupported['examples'])} example chips.")

    # 5. Missing Values Safety Check
    print("\n--- Testing Missing Values Safety ---")
    df_with_na = df.copy()
    df_with_na.loc[0:50, 'Age'] = None
    df_with_na.loc[10:30, 'MonthlyIncome'] = None
    res_na = QueryService.execute_query(df_with_na, "Find average income of employees who left.")
    assert "Value" in res_na["data"][0]
    print(f"  [PASS] Missing values handled gracefully: {res_na['explanation']}")

    # 6. Safety against Code Injection
    print("\n--- Testing Code Injection Safety ---")
    malicious_inputs = [
        "__import__('os').system('dir')",
        "Show employees where Age > 30; import sys; sys.exit(0)",
        "eval('1+1')",
        "DROP TABLE employees;"
    ]
    for mal in malicious_inputs:
        res_mal = QueryService.execute_query(df, mal)
        # Should either cleanly fallback or safely handle without throwing any unhandled exceptions
        assert isinstance(res_mal, dict)
        print(f"  [PASS] Safely rejected/handled malicious input: \"{mal}\"")

    print("\n" + "=" * 70)
    print("  ALL HYBRID QA TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == '__main__':
    run_hybrid_tests()
