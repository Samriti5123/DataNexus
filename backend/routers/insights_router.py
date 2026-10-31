from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from backend.services.data_service import DataService
from backend.services.insights_service import InsightsService
from backend.services.query_service import QueryService

router = APIRouter(prefix="/api/insights", tags=["insights"])

class QueryReq(BaseModel):
    query: str

def get_valid_session(session_id: str):
    session = DataService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset session not found.")
    return session

@router.get("/generate/{session_id}")
def get_business_insights(session_id: str, target_column: Optional[str] = Query(None)):
    session = get_valid_session(session_id)
    insights = InsightsService.generate_business_insights(session.current_df, target_col=target_column)
    if "error" in insights:
        raise HTTPException(status_code=400, detail=insights["error"])
    return insights

@router.post("/query/{session_id}")
def ask_datanexus_ai(session_id: str, req: QueryReq):
    session = get_valid_session(session_id)
    res = QueryService.execute_query(session.current_df, req.query)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.get("/suggestions/{session_id}")
def get_suggestion_chips(session_id: str):
    session = get_valid_session(session_id)
    chips = QueryService.get_suggestion_chips(session.current_df)
    return {"suggestions": chips}
