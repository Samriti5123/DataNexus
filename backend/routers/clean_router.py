from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from backend.services.data_service import DataService
from backend.services.cleaning_service import CleaningService

router = APIRouter(prefix="/api/clean", tags=["cleaning"])

class MissingReq(BaseModel):
    columns: List[str]
    strategy: str  # drop_rows, drop_cols, mean, median, mode, constant, ffill, bfill
    custom_value: Optional[Any] = None

class OutlierReq(BaseModel):
    columns: List[str]
    method: str = "iqr"  # iqr, zscore
    action: str = "clip"  # clip, remove
    threshold: float = 1.5

class DeduplicateReq(BaseModel):
    subset: Optional[List[str]] = None
    keep: str = "first"

class CastReq(BaseModel):
    conversions: Dict[str, str]  # col -> type (integer, float, datetime, boolean, category, string)

class NormalizeReq(BaseModel):
    columns: List[str]
    operation: str  # trim, lowercase, uppercase, titlecase, replace, remove_special
    search_term: Optional[str] = None
    replace_term: Optional[str] = ""

class CalcColumnReq(BaseModel):
    new_col_name: str
    calc_type: str  # arithmetic, binning, conditional
    col_a: str
    operator: Optional[str] = None
    col_b_or_val: Optional[Any] = None
    bins: Optional[int] = 4
    bin_labels: Optional[List[str]] = None

class FilterReq(BaseModel):
    conditions: List[Dict[str, Any]]
    match_all: bool = True

class ManageColsReq(BaseModel):
    renames: Optional[Dict[str, str]] = None
    drops: Optional[List[str]] = None

def get_valid_session(session_id: str):
    session = DataService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset session not found.")
    return session

@router.get("/audit/{session_id}")
def audit_dataset_health(session_id: str):
    session = get_valid_session(session_id)
    return CleaningService.audit_data_health(session.current_df)

@router.post("/missing/{session_id}")
def clean_missing_values(session_id: str, req: MissingReq):
    session = get_valid_session(session_id)
    before_count = len(session.current_df)
    new_df = CleaningService.handle_missing(session.current_df, req.columns, req.strategy, req.custom_value)
    desc = f"Handled missing in {', '.join(req.columns) if req.columns else 'all columns'} with '{req.strategy}' strategy"
    session.commit_change(new_df, desc)
    
    return {
        "success": True,
        "action": desc,
        "rows_before": before_count,
        "rows_after": len(new_df),
        "total_rows": len(new_df),
        "total_columns": len(new_df.columns)
    }

@router.post("/outliers/{session_id}")
def clean_outliers(session_id: str, req: OutlierReq):
    session = get_valid_session(session_id)
    before_count = len(session.current_df)
    new_df = CleaningService.handle_outliers(session.current_df, req.columns, req.method, req.action, req.threshold)
    desc = f"{req.action.capitalize()} outliers in {', '.join(req.columns) if req.columns else 'all numeric columns'} using {req.method.upper()} (threshold {req.threshold})"
    session.commit_change(new_df, desc)

    return {
        "success": True,
        "action": desc,
        "rows_before": before_count,
        "rows_after": len(new_df),
        "total_rows": len(new_df),
        "total_columns": len(new_df.columns)
    }

@router.post("/deduplicate/{session_id}")
def remove_duplicates(session_id: str, req: DeduplicateReq):
    session = get_valid_session(session_id)
    before_count = len(session.current_df)
    new_df = CleaningService.remove_duplicates(session.current_df, req.subset, req.keep)
    removed = before_count - len(new_df)
    desc = f"Removed {removed} duplicate rows (keep: {req.keep})"
    session.commit_change(new_df, desc)

    return {
        "success": True,
        "action": desc,
        "duplicates_removed": removed,
        "total_rows": len(new_df),
        "total_columns": len(new_df.columns)
    }

@router.post("/cast/{session_id}")
def cast_types(session_id: str, req: CastReq):
    session = get_valid_session(session_id)
    new_df = CleaningService.cast_column_types(session.current_df, req.conversions)
    desc = f"Type cast applied to: {', '.join([f'{k}->{v}' for k, v in req.conversions.items()])}"
    session.commit_change(new_df, desc)

    return {
        "success": True,
        "action": desc,
        "total_rows": len(new_df),
        "total_columns": len(new_df.columns)
    }

@router.post("/normalize/{session_id}")
def normalize_text(session_id: str, req: NormalizeReq):
    session = get_valid_session(session_id)
    new_df = CleaningService.normalize_text(session.current_df, req.columns, req.operation, req.search_term, req.replace_term)
    desc = f"Normalized text on {', '.join(req.columns)} with '{req.operation}'"
    session.commit_change(new_df, desc)

    return {
        "success": True,
        "action": desc,
        "total_rows": len(new_df),
        "total_columns": len(new_df.columns)
    }

@router.post("/calculated-column/{session_id}")
def add_calculated_column(session_id: str, req: CalcColumnReq):
    session = get_valid_session(session_id)
    new_df = CleaningService.create_calculated_column(
        session.current_df,
        req.new_col_name,
        req.calc_type,
        req.col_a,
        req.operator,
        req.col_b_or_val,
        req.bins,
        req.bin_labels
    )
    desc = f"Added calculated column '{req.new_col_name}' ({req.calc_type})"
    session.commit_change(new_df, desc)

    return {
        "success": True,
        "action": desc,
        "total_rows": len(new_df),
        "total_columns": len(new_df.columns)
    }

@router.post("/filter/{session_id}")
def filter_rows(session_id: str, req: FilterReq):
    session = get_valid_session(session_id)
    before_count = len(session.current_df)
    new_df = CleaningService.filter_rows(session.current_df, req.conditions, req.match_all)
    desc = f"Filtered rows ({len(req.conditions)} conditions, {before_count} -> {len(new_df)} rows)"
    session.commit_change(new_df, desc)

    return {
        "success": True,
        "action": desc,
        "rows_before": before_count,
        "rows_after": len(new_df),
        "total_rows": len(new_df),
        "total_columns": len(new_df.columns)
    }

@router.post("/manage-columns/{session_id}")
def manage_columns(session_id: str, req: ManageColsReq):
    session = get_valid_session(session_id)
    new_df = CleaningService.manage_columns(session.current_df, req.renames, req.drops)
    desc = f"Managed columns (Renamed: {len(req.renames or {})}, Dropped: {len(req.drops or [])})"
    session.commit_change(new_df, desc)

    return {
        "success": True,
        "action": desc,
        "total_rows": len(new_df),
        "total_columns": len(new_df.columns)
    }

@router.post("/undo/{session_id}")
def undo_transformation(session_id: str):
    session = get_valid_session(session_id)
    if session.undo():
        return {
            "success": True,
            "message": "Step undone successfully.",
            "current_action": session.action_history[-1],
            "total_rows": len(session.current_df),
            "total_columns": len(session.current_df.columns)
        }
    raise HTTPException(status_code=400, detail="Cannot undo: Already at initial state.")

@router.post("/redo/{session_id}")
def redo_transformation(session_id: str):
    session = get_valid_session(session_id)
    if session.redo():
        return {
            "success": True,
            "message": "Step redone successfully.",
            "current_action": session.action_history[-1],
            "total_rows": len(session.current_df),
            "total_columns": len(session.current_df.columns)
        }
    raise HTTPException(status_code=400, detail="Cannot redo: At most recent state.")

@router.post("/reset/{session_id}")
def reset_dataset(session_id: str):
    session = get_valid_session(session_id)
    session.reset()
    return {
        "success": True,
        "message": "Dataset reset to original raw state.",
        "total_rows": len(session.current_df),
        "total_columns": len(session.current_df.columns)
    }

@router.get("/recipe/{session_id}")
def export_recipe_script(session_id: str):
    session = get_valid_session(session_id)
    script_text = CleaningService.generate_python_script(session.action_history)
    return {
        "filename": "cleaning_recipe.py",
        "script": script_text,
        "steps_count": len(session.action_history) - 1
    }
