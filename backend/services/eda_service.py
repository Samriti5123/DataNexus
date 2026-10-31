import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, List, Optional

class EdaService:

    @classmethod
    def get_dataset_summary(cls, df: pd.DataFrame) -> Dict[str, Any]:
        total_rows = len(df)
        total_cols = len(df.columns)
        total_cells = total_rows * total_cols
        missing_cells = int(df.isnull().sum().sum())
        missing_pct = round((missing_cells / max(1, total_cells)) * 100, 2)
        duplicate_rows = int(df.duplicated().sum())
        duplicate_pct = round((duplicate_rows / max(1, total_rows)) * 100, 2)
        memory_usage_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)

        type_counts = {
            "numeric": int(len(df.select_dtypes(include=[np.number]).columns)),
            "datetime": int(len(df.select_dtypes(include=['datetime', 'datetime64']).columns)),
            "boolean": int(len(df.select_dtypes(include=['bool']).columns)),
            "categorical": int(len(df.select_dtypes(include=['object', 'category', 'string']).columns))
        }

        return {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "total_cells": total_cells,
            "missing_cells": missing_cells,
            "missing_percentage": missing_pct,
            "duplicate_rows": duplicate_rows,
            "duplicate_percentage": duplicate_pct,
            "memory_usage_mb": memory_usage_mb,
            "type_counts": type_counts,
            "columns": list(df.columns)
        }

    @classmethod
    def get_column_profiles(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        profiles = []
        total_rows = len(df)

        for col in df.columns:
            series = df[col]
            missing_count = int(series.isnull().sum())
            missing_pct = round((missing_count / max(1, total_rows)) * 100, 1)
            unique_count = int(series.nunique(dropna=True))
            unique_pct = round((unique_count / max(1, total_rows)) * 100, 1)

            # Determine semantic type
            if pd.api.types.is_numeric_dtype(series):
                semantic_type = 'numeric'
            elif pd.api.types.is_datetime64_any_dtype(series):
                semantic_type = 'datetime'
            elif series.dtype == 'bool':
                semantic_type = 'boolean'
            elif unique_count == total_rows and total_rows > 20:
                semantic_type = 'id'
            else:
                # Check if it might be date string
                semantic_type = 'categorical'

            profile: Dict[str, Any] = {
                "name": col,
                "dtype": str(series.dtype),
                "semantic_type": semantic_type,
                "missing_count": missing_count,
                "missing_percentage": missing_pct,
                "unique_count": unique_count,
                "unique_percentage": unique_pct,
                "sample_values": [str(x) for x in series.dropna().iloc[:5].tolist()]
            }

            # Numerical profiling
            if semantic_type == 'numeric':
                valid_num = series.dropna()
                if len(valid_num) > 0:
                    q25 = float(valid_num.quantile(0.25))
                    q75 = float(valid_num.quantile(0.75))
                    iqr = q75 - q25
                    outliers = valid_num[(valid_num < (q25 - 1.5 * iqr)) | (valid_num > (q75 + 1.5 * iqr))]
                    
                    skew = float(valid_num.skew()) if len(valid_num) > 2 else 0.0
                    kurt = float(valid_num.kurtosis()) if len(valid_num) > 3 else 0.0

                    # Histogram generation (10 bins)
                    counts, bin_edges = np.histogram(valid_num, bins=10)
                    hist_data = []
                    for i in range(len(counts)):
                        b_start = round(float(bin_edges[i]), 2)
                        b_end = round(float(bin_edges[i+1]), 2)
                        hist_data.append({
                            "bin_start": b_start,
                            "bin_end": b_end,
                            "label": f"{b_start} - {b_end}",
                            "count": int(counts[i])
                        })

                    zero_count = int((valid_num == 0).sum())

                    profile["stats"] = {
                        "min": round(float(valid_num.min()), 2),
                        "max": round(float(valid_num.max()), 2),
                        "mean": round(float(valid_num.mean()), 2),
                        "median": round(float(valid_num.median()), 2),
                        "std": round(float(valid_num.std()), 2) if len(valid_num) > 1 else 0.0,
                        "q25": round(q25, 2),
                        "q75": round(q75, 2),
                        "iqr": round(iqr, 2),
                        "skewness": round(skew, 2) if not np.isnan(skew) else 0.0,
                        "kurtosis": round(kurt, 2) if not np.isnan(kurt) else 0.0,
                        "zero_count": zero_count,
                        "zero_percentage": round((zero_count / max(1, len(valid_num))) * 100, 1),
                        "outlier_count": len(outliers),
                        "outlier_percentage": round((len(outliers) / max(1, len(valid_num))) * 100, 1),
                        "histogram": hist_data
                    }
            
            # Categorical / Boolean profiling
            elif semantic_type in ['categorical', 'boolean']:
                val_counts = series.value_counts(dropna=True).head(10)
                top_values = [
                    {
                        "value": str(k),
                        "count": int(v),
                        "percentage": round((int(v) / max(1, total_rows)) * 100, 1)
                    }
                    for k, v in val_counts.items()
                ]
                profile["top_values"] = top_values

            # Datetime profiling
            elif semantic_type == 'datetime':
                valid_dates = pd.to_datetime(series, errors='coerce').dropna()
                if not valid_dates.empty:
                    min_d = valid_dates.min()
                    max_d = valid_dates.max()
                    profile["date_stats"] = {
                        "min_date": str(min_d),
                        "max_date": str(max_d),
                        "timespan_days": int((max_d - min_d).days)
                    }

            profiles.append(profile)

        return profiles

    @staticmethod
    def _is_irrelevant_column(col_name: str, series: pd.Series, total_rows: int) -> bool:
        """Identify columns that are constant, ID fields, or non-informative for analysis."""
        if series.nunique(dropna=True) <= 1:
            return True
        if pd.api.types.is_numeric_dtype(series):
            try:
                if series.std(skipna=True) == 0:
                    return True
            except Exception:
                pass
        col_clean = col_name.strip().lower().replace('_', '')
        if col_clean in ('employeecount', 'standardhours', 'over18'):
            return True
        if col_clean in ('employeenumber', 'employeeid', 'id', 'recordid'):
            return True
        if series.nunique(dropna=True) >= total_rows * 0.98 and total_rows > 20:
            return True
        return False

    @classmethod
    def get_correlation_matrix(cls, df: pd.DataFrame, method: str = 'pearson', min_corr: float = 0.0) -> Dict[str, Any]:
        numeric_df = df.select_dtypes(include=[np.number])
        # Exclude constant & ID columns from correlation
        total_rows = len(df)
        useful_cols = [c for c in numeric_df.columns if not cls._is_irrelevant_column(c, numeric_df[c], total_rows)]
        numeric_df = numeric_df[useful_cols]
        if numeric_df.empty or len(numeric_df.columns) < 2:
            return {"columns": [], "matrix": [], "top_correlations": []}

        corr_matrix = numeric_df.corr(method=method)
        cols = list(corr_matrix.columns)

        matrix_rows = []
        for c in cols:
            row_dict = {"column": c}
            for target_col in cols:
                val = corr_matrix.loc[c, target_col]
                row_dict[target_col] = round(float(val), 3) if not np.isnan(val) else 0.0
            matrix_rows.append(row_dict)

        # Extract top pairs
        pairs = []
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                col1 = cols[i]
                col2 = cols[j]
                val = corr_matrix.loc[col1, col2]
                if not np.isnan(val) and abs(val) >= min_corr:
                    strength = "Strong" if abs(val) >= 0.7 else ("Moderate" if abs(val) >= 0.4 else "Weak")
                    direction = "Positive" if val > 0 else "Negative"
                    pairs.append({
                        "col1": col1,
                        "col2": col2,
                        "correlation": round(float(val), 3),
                        "abs_correlation": round(abs(float(val)), 3),
                        "relationship": f"{strength} {direction}"
                    })

        pairs.sort(key=lambda x: x["abs_correlation"], reverse=True)

        return {
            "columns": cols,
            "matrix": matrix_rows,
            "top_correlations": pairs[:15]
        }

    @classmethod
    def get_pivot_aggregation(
        cls,
        df: pd.DataFrame,
        rows: List[str],
        columns: Optional[List[str]] = None,
        values: Optional[str] = None,
        aggfunc: str = 'sum'
    ) -> Dict[str, Any]:
        valid_rows = [r for r in rows if r in df.columns]
        if not valid_rows:
            return {"error": "At least one valid row dimension is required."}

        val_col = values if values and values in df.columns else None
        
        # Mapping aggfunc string to pandas function
        agg_map = {
            'sum': 'sum',
            'mean': 'mean',
            'count': 'count',
            'median': 'median',
            'min': 'min',
            'max': 'max',
            'std': 'std'
        }
        chosen_agg = agg_map.get(aggfunc, 'sum')

        try:
            if columns and len(columns) > 0 and columns[0] in df.columns and val_col:
                # Pivot Table
                pivot = pd.pivot_table(
                    df,
                    index=valid_rows,
                    columns=columns[0],
                    values=val_col,
                    aggfunc=chosen_agg,
                    fill_value=0,
                    margins=True,
                    margins_name='Total'
                )
                pivot_reset = pivot.reset_index()
                # Clean columns formatting
                pivot_reset.columns = [str(c) for c in pivot_reset.columns]
                
                # Format numbers
                records = []
                for row in pivot_reset.to_dict(orient='records'):
                    clean_row = {}
                    for k, v in row.items():
                        if isinstance(v, (float, np.floating)):
                            clean_row[k] = round(float(v), 2)
                        else:
                            clean_row[k] = v
                    records.append(clean_row)

                return {
                    "type": "pivot",
                    "columns": list(pivot_reset.columns),
                    "data": records[:100]
                }
            else:
                # Standard GroupBy
                if val_col and pd.api.types.is_numeric_dtype(df[val_col]):
                    grouped = df.groupby(valid_rows)[val_col].agg(chosen_agg).reset_index()
                    grouped = grouped.sort_values(by=val_col, ascending=False)
                else:
                    grouped = df.groupby(valid_rows).size().reset_index(name='Count')
                    grouped = grouped.sort_values(by='Count', ascending=False)

                records = []
                for row in grouped.to_dict(orient='records'):
                    clean_row = {}
                    for k, v in row.items():
                        if isinstance(v, (float, np.floating)):
                            clean_row[k] = round(float(v), 2)
                        else:
                            clean_row[k] = v
                    records.append(clean_row)

                return {
                    "type": "groupby",
                    "columns": list(grouped.columns),
                    "data": records[:100]
                }
        except Exception as e:
            return {"error": str(e)}
