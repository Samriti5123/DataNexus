from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from backend.services.data_service import DataService
from backend.services.eda_service import EdaService

router = APIRouter(prefix="/api/eda", tags=["eda"])

class PivotReq(BaseModel):
    rows: List[str]
    columns: Optional[List[str]] = None
    values: Optional[str] = None
    aggfunc: str = "sum"

def get_valid_session(session_id: str):
    session = DataService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset session not found.")
    return session

@router.get("/summary/{session_id}")
def get_eda_summary(session_id: str):
    session = get_valid_session(session_id)
    return EdaService.get_dataset_summary(session.current_df)

@router.get("/profiles/{session_id}")
def get_column_profiles(session_id: str):
    session = get_valid_session(session_id)
    return {"profiles": EdaService.get_column_profiles(session.current_df)}

@router.get("/correlation/{session_id}")
def get_correlations(
    session_id: str,
    method: str = Query("pearson", regex="^(pearson|spearman)$"),
    min_corr: float = Query(0.0, ge=0.0, le=1.0)
):
    session = get_valid_session(session_id)
    return EdaService.get_correlation_matrix(session.current_df, method=method, min_corr=min_corr)

@router.post("/pivot/{session_id}")
def compute_pivot(session_id: str, req: PivotReq):
    session = get_valid_session(session_id)
    res = EdaService.get_pivot_aggregation(
        df=session.current_df,
        rows=req.rows,
        columns=req.columns,
        values=req.values,
        aggfunc=req.aggfunc
    )
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res
