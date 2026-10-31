import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.sample_data import get_superstore_sales_dataset, get_telecom_churn_dataset
from backend.services.data_service import DataService
from backend.services.cleaning_service import CleaningService
from backend.services.eda_service import EdaService
from backend.services.visualize_service import VisualizeService
from backend.services.insights_service import InsightsService
from backend.services.query_service import QueryService
from backend.services.report_service import ReportService

def test_sample_datasets():
    sales_df = get_superstore_sales_dataset()
    assert len(sales_df) == 650
    assert 'Sales' in sales_df.columns
    assert 'Profit' in sales_df.columns

    telco_df = get_telecom_churn_dataset()
    assert len(telco_df) == 600
    assert 'Churn' in telco_df.columns

def test_data_service():
    session = DataService.load_sample_dataset('superstore_sales')
    assert session is not None
    assert len(session.current_df) > 0
    preview = DataService.serialize_dataframe_preview(session.current_df, page=1, page_size=10)
    assert len(preview['data']) == 10
    assert preview['total_rows'] > 0

def test_cleaning_service():
    session = DataService.load_sample_dataset('superstore_sales')
    health = CleaningService.audit_data_health(session.current_df)
    assert 'overall_score' in health
    assert 'issues' in health

    # Impute missing values
    imputed_df = CleaningService.handle_missing(session.current_df, ['Customer_Rating'], 'mean')
    assert imputed_df['Customer_Rating'].isnull().sum() == 0

    # Clip outliers
    clipped_df = CleaningService.handle_outliers(session.current_df, ['Sales'], method='iqr', action='clip')
    assert clipped_df['Sales'].max() < 28000

    # Deduplicate
    dedup_df = CleaningService.remove_duplicates(session.current_df)
    assert len(dedup_df) <= len(session.current_df)

    # Recipe generation
    recipe = CleaningService.generate_python_script(["Dataset Initialized", "Imputed Customer_Rating with mean"])
    assert "def clean_dataset" in recipe

def test_eda_service():
    session = DataService.load_sample_dataset('superstore_sales')
    summary = EdaService.get_dataset_summary(session.current_df)
    assert summary['total_rows'] > 0

    profiles = EdaService.get_column_profiles(session.current_df)
    assert len(profiles) == len(session.current_df.columns)
    
    sales_prof = next(p for p in profiles if p['name'] == 'Sales')
    assert 'stats' in sales_prof
    assert len(sales_prof['stats']['histogram']) == 10

    corr = EdaService.get_correlation_matrix(session.current_df)
    assert 'top_correlations' in corr

    pivot = EdaService.get_pivot_aggregation(session.current_df, rows=['Category'], values='Sales', aggfunc='sum')
    assert 'data' in pivot

def test_visualize_service():
    session = DataService.load_sample_dataset('superstore_sales')
    chart = VisualizeService.build_chart_data(
        df=session.current_df,
        chart_type='bar',
        x_axis='Category',
        y_axis='Sales',
        aggregation='sum'
    )
    assert chart['labels'] is not None
    assert len(chart['datasets']) > 0

def test_insights_and_nlp():
    session = DataService.load_sample_dataset('superstore_sales')
    insights = InsightsService.generate_business_insights(session.current_df, target_col='Profit')
    assert len(insights['kpi_highlights']) > 0
    assert len(insights['key_drivers']) > 0
    assert len(insights['strategic_recommendations']) > 0

    nlp_res = QueryService.execute_query(session.current_df, "top 5 category by sales")
    assert "interpretation" in nlp_res
    assert len(nlp_res['data']) > 0

def test_report_generation():
    session = DataService.load_sample_dataset('superstore_sales')
    df = session.current_df
    eda_sum = EdaService.get_dataset_summary(df)
    health = CleaningService.audit_data_health(df)
    insights = InsightsService.generate_business_insights(df)
    html = ReportService.generate_html_report("Superstore Sales", df, eda_sum, health, insights)
    assert "<!DOCTYPE html>" in html
    assert "DataNexus Executive Intelligence Report" in html

if __name__ == '__main__':
    print("Running backend tests...")
    test_sample_datasets()
    print("[PASS] Sample datasets test passed")
    test_data_service()
    print("[PASS] DataService test passed")
    test_cleaning_service()
    print("[PASS] CleaningService test passed")
    test_eda_service()
    print("[PASS] EdaService test passed")
    test_visualize_service()
    print("[PASS] VisualizeService test passed")
    test_insights_and_nlp()
    print("[PASS] Insights and NLP Query test passed")
    test_report_generation()
    print("[PASS] Report generation test passed")
    print("\nALL BACKEND TESTS PASSED!")
