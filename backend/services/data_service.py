import io
import uuid
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from backend.sample_data import DATASET_GENERATORS

class DatasetSession:
    def __init__(self, session_id: str, name: str, df: pd.DataFrame):
        self.session_id = session_id
        self.name = name
        self.original_df = df.copy()
        self.current_df = df.copy()
        self.history: List[pd.DataFrame] = [df.copy()]
        self.action_history: List[str] = ["Dataset Initialized"]
        self.redo_stack: List[pd.DataFrame] = []
        self.redo_actions: List[str] = []

    def commit_change(self, new_df: pd.DataFrame, action_desc: str):
        self.history.append(self.current_df.copy())
        self.action_history.append(action_desc)
        self.current_df = new_df.copy()
        self.redo_stack.clear()
        self.redo_actions.clear()

    def undo(self) -> bool:
        if len(self.history) > 1:
            self.redo_stack.append(self.current_df.copy())
            self.redo_actions.append(self.action_history.pop())
            self.current_df = self.history.pop()
            return True
        return False

    def redo(self) -> bool:
        if self.redo_stack:
            self.history.append(self.current_df.copy())
            self.action_history.append(self.redo_actions.pop())
            self.current_df = self.redo_stack.pop()
            return True
        return False

    def reset(self):
        self.history.append(self.current_df.copy())
        self.action_history.append("Reset to Original")
        self.current_df = self.original_df.copy()
        self.redo_stack.clear()
        self.redo_actions.clear()

class DataService:
    _sessions: Dict[str, DatasetSession] = {}

    @classmethod
    def create_session_from_df(cls, name: str, df: pd.DataFrame, session_id: Optional[str] = None) -> DatasetSession:
        sid = session_id or str(uuid.uuid4())
        # Clean column names (strip whitespace)
        df.columns = [str(c).strip() for c in df.columns]
        session = DatasetSession(sid, name, df)
        cls._sessions[sid] = session
        return session

    @classmethod
    def get_session(cls, session_id: str) -> Optional[DatasetSession]:
        return cls._sessions.get(session_id)

    @classmethod
    def list_sessions(cls) -> List[Dict[str, Any]]:
        return [
            {
                "session_id": sid,
                "name": s.name,
                "rows": len(s.current_df),
                "columns": len(s.current_df.columns),
                "steps_applied": len(s.action_history) - 1
            }
            for sid, s in cls._sessions.items()
        ]

    @classmethod
    def load_sample_dataset(cls, dataset_key: str) -> DatasetSession:
        if dataset_key not in DATASET_GENERATORS:
            dataset_key = 'superstore_sales'
        info = DATASET_GENERATORS[dataset_key]
        df = info['fn']()
        return cls.create_session_from_df(info['name'], df)

    @classmethod
    def parse_uploaded_file(cls, filename: str, contents: bytes) -> pd.DataFrame:
        filename_lower = filename.lower()
        
        if filename_lower.endswith(('.xlsx', '.xls')):
            return pd.read_excel(io.BytesIO(contents))
        
        if filename_lower.endswith('.json'):
            try:
                return pd.read_json(io.BytesIO(contents))
            except Exception:
                return pd.read_json(io.BytesIO(contents), orient='records')

        # CSV / TSV with encoding & delimiter auto-detection
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        last_error = None

        for enc in encodings:
            try:
                # Delimiter detection
                sample = contents[:4096].decode(enc, errors='ignore')
                delimiters = [',', '\t', ';', '|']
                counts = {d: sample.count(d) for d in delimiters}
                best_delim = max(counts, key=counts.get)
                if counts[best_delim] == 0:
                    best_delim = ','
                
                df = pd.read_csv(io.BytesIO(contents), encoding=enc, sep=best_delim)
                return df
            except Exception as e:
                last_error = e
                continue
                
        raise ValueError(f"Could not parse uploaded file: {str(last_error)}")

    @classmethod
    def serialize_dataframe_preview(
        cls, 
        df: pd.DataFrame, 
        page: int = 1, 
        page_size: int = 25, 
        sort_by: Optional[str] = None, 
        sort_ascending: bool = True,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        temp_df = df.copy()

        # Global search filter across all columns
        if search and search.strip():
            query = search.strip().lower()
            mask = temp_df.astype(str).apply(lambda col: col.str.lower().str.contains(query, regex=False)).any(axis=1)
            temp_df = temp_df[mask]

        # Sorting
        if sort_by and sort_by in temp_df.columns:
            temp_df = temp_df.sort_values(by=sort_by, ascending=sort_ascending)

        total_rows = len(temp_df)
        total_pages = max(1, (total_rows + page_size - 1) // page_size)
        current_page = max(1, min(page, total_pages))

        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_df = temp_df.iloc[start_idx:end_idx]

        # Convert NaNs / Infs to None for valid JSON serialization
        records = []
        for row in paginated_df.to_dict(orient='records'):
            clean_row = {}
            for k, v in row.items():
                if pd.isna(v) or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
                    clean_row[k] = None
                elif isinstance(v, (np.integer, np.floating)):
                    clean_row[k] = v.item()
                elif isinstance(v, pd.Timestamp):
                    clean_row[k] = v.isoformat()
                else:
                    clean_row[k] = v
            records.append(clean_row)

        column_types = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            if pd.api.types.is_numeric_dtype(df[col]):
                column_types[col] = 'numeric'
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                column_types[col] = 'datetime'
            elif df[col].dtype == 'bool':
                column_types[col] = 'boolean'
            else:
                column_types[col] = 'categorical'

        return {
            "columns": list(df.columns),
            "column_types": column_types,
            "data": records,
            "total_rows": total_rows,
            "page": current_page,
            "page_size": page_size,
            "total_pages": total_pages
        }
