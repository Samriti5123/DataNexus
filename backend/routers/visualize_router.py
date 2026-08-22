from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from backend.services.data_service import DataService
from backend.services.visualize_service import VisualizeService

router = APIRouter(prefix="/api/visualize", tags=["visualize"])

class ChartRequest(BaseModel):
    chart_type: str = "bar"  # bar, stacked_bar, horizontal_bar, line, area, scatter, bubble, pie, donut, histogram, boxplot
    x_axis: str
    y_axis: Optional[str] = None
    y_axes: Optional[List[str]] = None
    group_by: Optional[str] = None
    size_axis: Optional[str] = None
    aggregation: str = "sum"  # sum, mean, count, median, min, max
    sort_by: str = "none"  # none, value_desc, value_asc, label_asc
    limit: int = 15
    palette: str = "modern_emerald"

def get_valid_session(session_id: str):
    session = DataService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset session not found.")
    return session

@router.get("/options/{session_id}")
def get_chart_options(session_id: str):
    session = get_valid_session(session_id)
    return VisualizeService.get_chart_options(session.current_df)

@router.post("/chart/{session_id}")
def generate_chart(session_id: str, req: ChartRequest):
    session = get_valid_session(session_id)
    try:
        data = VisualizeService.build_chart_data(
            df=session.current_df,
            chart_type=req.chart_type,
            x_axis=req.x_axis,
            y_axis=req.y_axis,
            y_axes=req.y_axes,
            group_by=req.group_by,
            size_axis=req.size_axis,
            aggregation=req.aggregation,
            sort_by=req.sort_by,
            limit=req.limit,
            palette_name=req.palette
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate chart: {str(e)}")
