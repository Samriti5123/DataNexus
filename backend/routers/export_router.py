import io
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import HTMLResponse
from backend.services.data_service import DataService
from backend.services.cleaning_service import CleaningService
from backend.services.eda_service import EdaService
from backend.services.insights_service import InsightsService
from backend.services.report_service import ReportService

router = APIRouter(prefix="/api/export", tags=["export"])

def get_valid_session(session_id: str):
    session = DataService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset session not found.")
    return session

@router.get("/csv/{session_id}")
def export_csv(session_id: str):
    session = get_valid_session(session_id)
    csv_bytes = session.current_df.to_csv(index=False).encode('utf-8')
    filename = f"DataLens_Cleaned_{session.name.replace(' ', '_')}.csv"
    
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/excel/{session_id}")
def export_excel(session_id: str):
    session = get_valid_session(session_id)
    out = io.BytesIO()
    with io.BytesIO() as buffer:
        session.current_df.to_excel(buffer, index=False, engine='openpyxl')
        excel_bytes = buffer.getvalue()
        
    filename = f"DataLens_Cleaned_{session.name.replace(' ', '_')}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/report/{session_id}", response_class=HTMLResponse)
def export_executive_report(session_id: str):
    session = get_valid_session(session_id)
    df = session.current_df
    
    eda_sum = EdaService.get_dataset_summary(df)
    health = CleaningService.audit_data_health(df)
    insights = InsightsService.generate_business_insights(df)
    
    html = ReportService.generate_html_report(
        dataset_name=session.name,
        df=df,
        eda_summary=eda_sum,
        health_audit=health,
        insights=insights
    )
    return HTMLResponse(content=html)
