import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.nlp_query_service import NLPQueryEngine

def main():
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'WA_Fn-UseC_-HR-Employee-Attrition.csv')
    df = pd.read_csv(csv_path)
    engine = NLPQueryEngine(df)

    test_queries = [
        # Required Examples:
        ("Show employees above 35.", "filter"),
        ("Show Age and Department.", "projection"),
        ("Show employees above 35 working overtime.", "multi-filter"),
        ("Find average income of employees who left.", "aggregation"),
        ("Compare attrition by department.", "comparison"),
        ("Show the top five departments by attrition.", "top_n"),

        # Variations & Edge Cases:
        ("Employees older than 35", "filter variation"),
        ("Staff over 40 with overtime", "multi-filter variation"),
        ("What is the mean salary of employees who left?", "aggregation variation"),
        ("Attrition rate by department", "comparison variation"),
        ("Top 3 departments by attrition", "top_n variation"),
        ("Show employees where age between 25 and 30", "between filter"),
        ("Show employees above 95", "empty filter"),
    ]

    print("=" * 70)
    print("  Testing NLP Query Engine on IBM HR Analytics Dataset")
    print("=" * 70)

    for q, label in test_queries:
        res = engine.process_query(q)
        assert res is not None, f"Failed to understand: '{q}'"
        print(f"\n[PASS] ({label.upper()}) \"{q}\"")
        print(f"       Engine: {res.get('engine')}")
        print(f"       Interpretation: {res.get('interpretation')}")
        print(f"       Total matching: {res.get('total_results')}")
        print(f"       Columns: {res.get('columns')[:5]}")
        print(f"       Explanation: {res.get('explanation')}")

    print("\n" + "=" * 70)
    print("  ALL NLP ENGINE TEST CASES PASSED!")
    print("=" * 70)

if __name__ == '__main__':
    main()
