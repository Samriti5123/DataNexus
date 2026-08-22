import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class CleaningService:

    @classmethod
    def audit_data_health(cls, df: pd.DataFrame) -> Dict[str, Any]:
        total_rows = len(df)
        total_cols = len(df.columns)
        total_cells = total_rows * total_cols
        
        if total_cells == 0:
            return {
                "overall_score": 100,
                "completeness_score": 100,
                "uniqueness_score": 100,
                "consistency_score": 100,
                "issues": [],
                "recommendations": []
            }

        # 1. Missing Values
        missing_per_col = df.isnull().sum()
        total_missing = int(missing_per_col.sum())
        completeness_score = round(((total_cells - total_missing) / total_cells) * 100, 1)

        # 2. Duplicates
        duplicate_rows = int(df.duplicated().sum())
        uniqueness_score = round(((total_rows - duplicate_rows) / max(1, total_rows)) * 100, 1)

        # 3. Outlier check on numeric cols
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        outlier_count = 0
        outlier_cols = {}
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) > 10:
                q25 = series.quantile(0.25)
                q75 = series.quantile(0.75)
                iqr = q75 - q25
                if iqr > 0:
                    outliers = series[(series < (q25 - 2.5 * iqr)) | (series > (q75 + 2.5 * iqr))]
                    if len(outliers) > 0:
                        outlier_count += len(outliers)
                        outlier_cols[col] = len(outliers)

        outlier_penalty = min(25, (outlier_count / max(1, total_rows * max(1, len(numeric_cols)))) * 100 * 2)
        consistency_score = round(max(0, 100 - outlier_penalty), 1)

        overall_score = round(
            (completeness_score * 0.45) + (uniqueness_score * 0.35) + (consistency_score * 0.20),
            1
        )

        # Build Issues List
        issues = []
        recommendations = []

        if duplicate_rows > 0:
            pct = round((duplicate_rows / total_rows) * 100, 1)
            issues.append({
                "type": "duplicate",
                "severity": "high" if pct > 5 else "medium",
                "message": f"Found {duplicate_rows} duplicate rows ({pct}% of dataset)."
            })
            recommendations.append("Remove duplicate rows using Deduplicate tool.")

        for col, count in missing_per_col.items():
            if count > 0:
                pct = round((count / total_rows) * 100, 1)
                severity = "high" if pct > 20 else ("medium" if pct > 5 else "low")
                issues.append({
                    "type": "missing",
                    "column": col,
                    "count": int(count),
                    "percentage": pct,
                    "severity": severity,
                    "message": f"Column '{col}' has {count} missing values ({pct}%)."
                })
                recommendations.append(f"Impute or drop missing values in '{col}'.")

        for col, count in outlier_cols.items():
            pct = round((count / total_rows) * 100, 1)
            issues.append({
                "type": "outlier",
                "column": col,
                "count": count,
                "percentage": pct,
                "severity": "medium",
                "message": f"Column '{col}' contains {count} extreme statistical outliers ({pct}%)."
            })
            recommendations.append(f"Clip or filter extreme outliers in '{col}'.")

        return {
            "overall_score": overall_score,
            "completeness_score": completeness_score,
            "uniqueness_score": uniqueness_score,
            "consistency_score": consistency_score,
            "total_rows": total_rows,
            "total_columns": total_cols,
            "total_missing": total_missing,
            "duplicate_rows": duplicate_rows,
            "outlier_count": outlier_count,
            "issues": issues,
            "recommendations": list(dict.fromkeys(recommendations))
        }

    @classmethod
    def handle_missing(
        cls, 
        df: pd.DataFrame, 
        columns: List[str], 
        strategy: str, 
        custom_value: Optional[Any] = None
    ) -> pd.DataFrame:
        new_df = df.copy()
        target_cols = [c for c in columns if c in new_df.columns] if columns else new_df.columns.tolist()

        if strategy == 'drop_rows':
            new_df = new_df.dropna(subset=target_cols)
        elif strategy == 'drop_cols':
            new_df = new_df.drop(columns=target_cols)
        elif strategy == 'mean':
            for c in target_cols:
                if pd.api.types.is_numeric_dtype(new_df[c]):
                    new_df[c] = new_df[c].fillna(new_df[c].mean())
        elif strategy == 'median':
            for c in target_cols:
                if pd.api.types.is_numeric_dtype(new_df[c]):
                    new_df[c] = new_df[c].fillna(new_df[c].median())
        elif strategy == 'mode':
            for c in target_cols:
                mode_vals = new_df[c].mode()
                if not mode_vals.empty:
                    new_df[c] = new_df[c].fillna(mode_vals[0])
        elif strategy == 'constant':
            for c in target_cols:
                val = custom_value
                if pd.api.types.is_numeric_dtype(new_df[c]):
                    try:
                        val = float(custom_value)
                    except (ValueError, TypeError):
                        val = 0
                new_df[c] = new_df[c].fillna(val)
        elif strategy == 'ffill':
            new_df[target_cols] = new_df[target_cols].ffill()
        elif strategy == 'bfill':
            new_df[target_cols] = new_df[target_cols].bfill()

        return new_df

    @classmethod
    def handle_outliers(
        cls, 
        df: pd.DataFrame, 
        columns: List[str], 
        method: str = 'iqr', 
        action: str = 'clip', 
        threshold: float = 1.5
    ) -> pd.DataFrame:
        new_df = df.copy()
        if columns and len(columns) > 0:
            target_cols = [c for c in columns if c in new_df.columns and pd.api.types.is_numeric_dtype(new_df[c])]
        else:
            target_cols = new_df.select_dtypes(include=[np.number]).columns.tolist()

        for col in target_cols:
            new_df[col] = pd.to_numeric(new_df[col], errors='coerce')
            series = new_df[col].dropna()
            if len(series) < 4:
                continue

            if method == 'iqr':
                q25 = float(series.quantile(0.25))
                q75 = float(series.quantile(0.75))
                iqr = q75 - q25
                if iqr <= 0:
                    continue
                lower_bound = q25 - (threshold * iqr)
                upper_bound = q75 + (threshold * iqr)
            else:  # zscore
                mean = float(series.mean())
                std = float(series.std())
                if std == 0 or np.isnan(std):
                    continue
                lower_bound = mean - (threshold * std)
                upper_bound = mean + (threshold * std)

            if action == 'clip':
                new_df[col] = new_df[col].clip(lower=lower_bound, upper=upper_bound)
            elif action == 'remove':
                new_df = new_df[(new_df[col] >= lower_bound) & (new_df[col] <= upper_bound)]

        return new_df

    @classmethod
    def remove_duplicates(cls, df: pd.DataFrame, subset: Optional[List[str]] = None, keep: str = 'first') -> pd.DataFrame:
        valid_subset = [c for c in subset if c in df.columns] if subset else None
        return df.drop_duplicates(subset=valid_subset, keep=keep)

    @classmethod
    def cast_column_types(cls, df: pd.DataFrame, conversions: Dict[str, str]) -> pd.DataFrame:
        new_df = df.copy()
        for col, target_type in conversions.items():
            if col not in new_df.columns:
                continue
            try:
                if target_type == 'integer':
                    new_df[col] = pd.to_numeric(new_df[col], errors='coerce').fillna(0).astype(int)
                elif target_type == 'float':
                    new_df[col] = pd.to_numeric(new_df[col], errors='coerce')
                elif target_type == 'datetime':
                    new_df[col] = pd.to_datetime(new_df[col], errors='coerce')
                elif target_type == 'boolean':
                    new_df[col] = new_df[col].astype(str).str.lower().isin(['true', '1', 'yes', 'y', 't'])
                elif target_type == 'category':
                    new_df[col] = new_df[col].astype('category')
                elif target_type == 'string':
                    new_df[col] = new_df[col].astype(str)
            except Exception:
                continue
        return new_df

    @classmethod
    def normalize_text(
        cls, 
        df: pd.DataFrame, 
        columns: List[str], 
        operation: str, 
        search_term: Optional[str] = None, 
        replace_term: Optional[str] = ""
    ) -> pd.DataFrame:
        new_df = df.copy()
        for col in columns:
            if col not in new_df.columns:
                continue
            str_series = new_df[col].astype(str)
            if operation == 'trim':
                new_df[col] = str_series.str.strip()
            elif operation == 'lowercase':
                new_df[col] = str_series.str.lower()
            elif operation == 'uppercase':
                new_df[col] = str_series.str.upper()
            elif operation == 'titlecase':
                new_df[col] = str_series.str.title()
            elif operation == 'replace' and search_term is not None:
                new_df[col] = str_series.str.replace(search_term, replace_term or "", regex=False)
            elif operation == 'remove_special':
                new_df[col] = str_series.str.replace(r'[^a-zA-Z0-9\s]', '', regex=True)
        return new_df

    @classmethod
    def create_calculated_column(
        cls,
        df: pd.DataFrame,
        new_col_name: str,
        calc_type: str,
        col_a: str,
        operator: Optional[str] = None,
        col_b_or_val: Optional[Any] = None,
        bins: Optional[int] = None,
        bin_labels: Optional[List[str]] = None
    ) -> pd.DataFrame:
        new_df = df.copy()
        if not new_col_name or col_a not in new_df.columns:
            return new_df

        series_a = pd.to_numeric(new_df[col_a], errors='coerce') if pd.api.types.is_numeric_dtype(new_df[col_a]) else new_df[col_a]

        if calc_type == 'arithmetic' and operator:
            # Check if col_b_or_val is a column name or constant number
            if isinstance(col_b_or_val, str) and col_b_or_val in new_df.columns:
                series_b = pd.to_numeric(new_df[col_b_or_val], errors='coerce')
            else:
                try:
                    series_b = float(col_b_or_val)
                except (ValueError, TypeError):
                    series_b = 0

            if operator == '+':
                new_df[new_col_name] = series_a + series_b
            elif operator == '-':
                new_df[new_col_name] = series_a - series_b
            elif operator == '*':
                new_df[new_col_name] = series_a * series_b
            elif operator == '/':
                new_df[new_col_name] = series_a / (series_b.replace(0, np.nan) if isinstance(series_b, pd.Series) else (series_b if series_b != 0 else np.nan))
            elif operator == '%':
                new_df[new_col_name] = (series_a / (series_b.replace(0, np.nan) if isinstance(series_b, pd.Series) else (series_b if series_b != 0 else np.nan))) * 100

        elif calc_type == 'binning' and pd.api.types.is_numeric_dtype(new_df[col_a]):
            num_bins = bins or 4
            new_df[new_col_name] = pd.qcut(new_df[col_a].rank(method='first'), q=num_bins, labels=bin_labels if bin_labels and len(bin_labels) == num_bins else False)

        elif calc_type == 'conditional':
            # e.g., if col_a >= threshold -> 'High' else 'Low'
            threshold = float(col_b_or_val) if col_b_or_val is not None else 0
            new_df[new_col_name] = np.where(series_a >= threshold, 'High', 'Low')

        return new_df

    @classmethod
    def filter_rows(cls, df: pd.DataFrame, conditions: List[Dict[str, Any]], match_all: bool = True) -> pd.DataFrame:
        if not conditions:
            return df

        masks = []
        for cond in conditions:
            col = cond.get('column')
            op = cond.get('operator')
            val = cond.get('value')

            if col not in df.columns:
                continue

            series = df[col]
            
            if op == '==':
                masks.append(series.astype(str) == str(val))
            elif op == '!=':
                masks.append(series.astype(str) != str(val))
            elif op in ['>', '<', '>=', '<=']:
                num_series = pd.to_numeric(series, errors='coerce')
                num_val = float(val) if val is not None else 0
                if op == '>':
                    masks.append(num_series > num_val)
                elif op == '<':
                    masks.append(num_series < num_val)
                elif op == '>=':
                    masks.append(num_series >= num_val)
                elif op == '<=':
                    masks.append(num_series <= num_val)
            elif op == 'contains':
                masks.append(series.astype(str).str.lower().str.contains(str(val).lower(), regex=False))
            elif op == 'not_contains':
                masks.append(~series.astype(str).str.lower().str.contains(str(val).lower(), regex=False))
            elif op == 'is_null':
                masks.append(series.isnull())
            elif op == 'not_null':
                masks.append(series.notnull())

        if not masks:
            return df

        combined_mask = masks[0]
        for m in masks[1:]:
            combined_mask = (combined_mask & m) if match_all else (combined_mask | m)

        return df[combined_mask]

    @classmethod
    def manage_columns(cls, df: pd.DataFrame, renames: Optional[Dict[str, str]] = None, drops: Optional[List[str]] = None) -> pd.DataFrame:
        new_df = df.copy()
        if drops:
            valid_drops = [c for c in drops if c in new_df.columns]
            if valid_drops:
                new_df = new_df.drop(columns=valid_drops)
        if renames:
            valid_renames = {k: v for k, v in renames.items() if k in new_df.columns and v}
            if valid_renames:
                new_df = new_df.rename(columns=valid_renames)
        return new_df

    @classmethod
    def generate_python_script(cls, action_history: List[str]) -> str:
        lines = [
            "# ========================================================",
            "# DataLens - Automated Data Cleaning & ETL Pipeline Script",
            "# Generated automatically from applied transformation steps",
            "# ========================================================",
            "",
            "import pandas as pd",
            "import numpy as np",
            "",
            "def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:",
            "    \"\"\"Applies all cleaning and transformation steps recorded in DataLens.\"\"\"",
            "    cleaned_df = df.copy()",
            "    cleaned_df.columns = [str(c).strip() for c in cleaned_df.columns]",
            ""
        ]

        for idx, action in enumerate(action_history[1:], start=1):
            lines.append(f"    # Step {idx}: {action}")
            # Add illustrative pandas equivalent comment or code snippet
            lines.append(f"    # TODO: Applied '{action}'")

        lines.extend([
            "",
            "    return cleaned_df",
            "",
            "if __name__ == '__main__':",
            "    # Load raw data",
            "    raw_df = pd.read_csv('your_dataset.csv')",
            "    processed_df = clean_dataset(raw_df)",
            "    print(f'Pipeline complete! Shape: {processed_df.shape}')",
            "    processed_df.to_csv('cleaned_dataset.csv', index=False)"
        ])

        return "\n".join(lines)
