from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import Optional
from backend.services.data_service import DataService
from backend.sample_data import DATASET_GENERATORS

router = APIRouter(prefix="/api", tags=["upload"])

@router.get("/samples")
def list_sample_datasets():
    samples = []
    for key, info in DATASET_GENERATORS.items():
        samples.append({
            "key": key,
            "name": info["name"],
            "category": info["category"],
            "description": info["description"]
        })
    return {"samples": samples}

@router.post("/samples/{dataset_key}")
def load_sample(dataset_key: str):
    try:
        session = DataService.load_sample_dataset(dataset_key)
        return {
            "session_id": session.session_id,
            "name": session.name,
            "rows": len(session.current_df),
            "columns": len(session.current_df.columns),
            "column_names": list(session.current_df.columns),
            "message": f"Successfully loaded '{session.name}' dataset."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload")
async def upload_dataset_file(file: UploadFile = File(...), dataset_name: Optional[str] = Form(None)):
    try:
        contents = await file.read()
        filename = file.filename or "uploaded_dataset.csv"
        df = DataService.parse_uploaded_file(filename, contents)
        
        name = dataset_name.strip() if dataset_name and dataset_name.strip() else filename
        session = DataService.create_session_from_df(name, df)

        return {
            "session_id": session.session_id,
            "name": session.name,
            "rows": len(session.current_df),
            "columns": len(session.current_df.columns),
            "column_names": list(session.current_df.columns),
            "message": f"Successfully uploaded and parsed '{name}' ({len(session.current_df):,} rows)."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")

@router.get("/preview/{session_id}")
def get_dataset_preview(
    session_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=5, le=200),
    sort_by: Optional[str] = None,
    sort_ascending: bool = True,
    search: Optional[str] = None
):
    session = DataService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset session not found.")

    preview = DataService.serialize_dataframe_preview(
        df=session.current_df,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_ascending=sort_ascending,
        search=search
    )
    preview["session_name"] = session.name
    preview["action_history"] = session.action_history
    preview["can_undo"] = len(session.history) > 1
    preview["can_redo"] = len(session.redo_stack) > 0

    return preview

@router.get("/sessions")
def list_sessions():
    return {"sessions": DataService.list_sessions()}
