import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from backend.services.visualize_service import VisualizeService

# Lets "top five orders" work the same as "top 5 orders"
_WORD_TO_NUM = {
    'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
    'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
    'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14',
    'fifteen': '15', 'sixteen': '16', 'seventeen': '17', 'eighteen': '18',
    'nineteen': '19', 'twenty': '20'
}


def _normalize_number_words(text: str) -> str:
    def replace(match):
        return _WORD_TO_NUM[match.group(0)]
    pattern = r'\b(' + '|'.join(_WORD_TO_NUM.keys()) + r')\b'
    return re.sub(pattern, replace, text)


class QueryService:

    @classmethod
    def execute_query(cls, df: pd.DataFrame, query_str: str) -> Dict[str, Any]:
        q = query_str.strip().lower()
        if not q:
            return {"error": "Query string cannot be empty."}
        q = _normalize_number_words(q)

        cols = list(df.columns)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category', 'string', 'bool']).columns.tolist()

        # Helper to find closest matching column in query
        def find_column_in_text(text: str, candidates: List[str]) -> Optional[str]:

            for c in candidates:
                c_clean = c.lower().replace('_', ' ')
                if c_clean in text or c.lower() in text:
                    return c
            # Token match
            tokens = re.findall(r'\w+', text)
            for t in tokens:
                for c in candidates:
                    if t == c.lower() or t == c.lower().replace('_', ''):
                        return c
            return None

        # Helper to detect an explicit category VALUE mentioned in the query text
        # (e.g. "north" for a Region column with values North/South/East/West),
        # so phrases like "in north region" or "for north" act as a filter
        # instead of being silently ignored.
        def find_value_filter(text: str, exclude_col: Optional[str] = None):
            tokens = set(re.findall(r'\w+', text))
            if not tokens:
                return None
            for c in cat_cols:
                if c == exclude_col:
                    continue
                try:
                    uniques = df[c].dropna().unique().tolist()
                except Exception:
                    continue
                # Skip high-cardinality free-text columns (names, IDs, etc.) -
                # matching against those is unreliable and can false-positive.
                if len(uniques) == 0 or len(uniques) > 50:
                    continue
                for val in uniques:
                    val_str = str(val).strip()
                    if not val_str:
                        continue
                    val_lower = val_str.lower()
                    if ' ' in val_lower:
                        if val_lower in text:
                            return c, val_str
                    elif val_lower in tokens:
                        return c, val_str
            return None

        # 1. Check for "Top N" / "Bottom N" pattern
        top_match = re.search(r'(top|bottom)\s+(\d+)\s+(.*)', q)
        if top_match:
            direction = top_match.group(1)
            limit_n = int(top_match.group(2))
            remainder = top_match.group(3) or ""
            is_ascending = direction == 'bottom'

            # Does the query name a specific value to filter to first,
            # e.g. "top 5 orders in north region" -> filter Region == North
            value_filter = find_value_filter(remainder)
            working_df = df
            remaining_cat_cols = cat_cols
            filter_note = ""
            if value_filter:
                f_col, f_val = value_filter
                working_df = df[df[f_col].astype(str).str.lower() == str(f_val).lower()]
                remaining_cat_cols = [c for c in cat_cols if c != f_col]
                filter_note = f" where '{f_col}' is '{f_val}'"

            target_metric = find_column_in_text(remainder, numeric_cols) or find_column_in_text(q, numeric_cols) or (numeric_cols[0] if numeric_cols else None)

            # Only group by a dimension when the query explicitly says "by <dimension>";
            # otherwise this is a request for the top individual rows, not a rollup.
            by_match = re.search(r'\bby\s+([a-zA-Z0-9_\s]+)', remainder)
            dim_col = find_column_in_text(by_match.group(1), remaining_cat_cols) if by_match else None

            if target_metric and dim_col:
                grouped = working_df.groupby(dim_col)[target_metric].sum().reset_index()
                grouped = grouped.sort_values(by=target_metric, ascending=is_ascending).head(limit_n)

                chart_data = VisualizeService.build_chart_data(
                    df=working_df[working_df[dim_col].isin(grouped[dim_col])],
                    chart_type='bar',
                    x_axis=dim_col,
                    y_axis=target_metric,
                    aggregation='sum',
                    sort_by='value_asc' if is_ascending else 'value_desc',
                    limit=limit_n
                )

                records = grouped.to_dict(orient='records')
                return {
                    "query": query_str,
                    "interpretation": f"Calculated {direction.upper()} {limit_n} '{dim_col}' ranked by total '{target_metric}'{filter_note}.",
                    "columns": list(grouped.columns),
                    "data": records,
                    "total_results": len(records),
                    "suggested_chart": chart_data
                }

            if target_metric and len(working_df) > 0:
                ranked = working_df.sort_values(by=target_metric, ascending=is_ascending).head(limit_n)
                records = ranked.to_dict(orient='records')
                return {
                    "query": query_str,
                    "interpretation": f"Showing {direction.upper()} {limit_n} records ranked by '{target_metric}'{filter_note}.",
                    "columns": list(ranked.columns),
                    "data": records,
                    "total_results": len(records),
                    "suggested_chart": None
                }

        # 2. Check for "Average / Sum / Count [Metric] by [Dimension]"
        agg_match = re.search(r'(average|avg|mean|sum|total|count|median|max|min)\s+(?:of\s+)?([a-zA-Z0-9_\s]+)?\s+(?:by|per|for)\s+([a-zA-Z0-9_\s]+)', q)
        if agg_match:
            agg_word = agg_match.group(1)
            agg_type = 'mean' if agg_word in ['average', 'avg', 'mean'] else ('sum' if agg_word in ['sum', 'total'] else ('count' if agg_word == 'count' else agg_word))
            
            target_metric = find_column_in_text(agg_match.group(2) or q, numeric_cols) or (numeric_cols[0] if numeric_cols else None)
            group_clause = agg_match.group(3) or q

            # "...by west region" or "...for the North region" names a specific
            # VALUE, not a general breakdown -> filter to it and return one number,
            # rather than silently grouping across every value of that column.
            value_filter = find_value_filter(group_clause)
            if value_filter:
                f_col, f_val = value_filter
                filtered_df = df[df[f_col].astype(str).str.lower() == str(f_val).lower()]

                if agg_type == 'count' or not target_metric:
                    result_val = len(filtered_df)
                    val_col = 'Count'
                else:
                    result_val = filtered_df[target_metric].agg(agg_type)
                    val_col = target_metric

                record = {f_col: f_val, val_col: (None if pd.isna(result_val) else result_val)}
                return {
                    "query": query_str,
                    "interpretation": f"Calculated {agg_type.upper()} of '{val_col}' where '{f_col}' is '{f_val}'.",
                    "columns": [f_col, val_col],
                    "data": [record],
                    "total_results": 1,
                    "suggested_chart": None
                }

            dim_col = find_column_in_text(group_clause, cat_cols) or (cat_cols[0] if cat_cols else None)

            if dim_col and (target_metric or agg_type == 'count'):
                if agg_type == 'count' or not target_metric:
                    grouped = df.groupby(dim_col).size().reset_index(name='Count')
                    val_col = 'Count'
                else:
                    grouped = df.groupby(dim_col)[target_metric].agg(agg_type).reset_index()
                    val_col = target_metric

                grouped = grouped.sort_values(by=val_col, ascending=False).head(15)

                chart_data = VisualizeService.build_chart_data(
                    df=df,
                    chart_type='bar',
                    x_axis=dim_col,
                    y_axis=val_col if val_col != 'Count' else None,
                    aggregation=agg_type,
                    limit=15
                )

                return {
                    "query": query_str,
                    "interpretation": f"Calculated {agg_type.upper()} of '{val_col}' grouped by '{dim_col}'.",
                    "columns": list(grouped.columns),
                    "data": grouped.to_dict(orient='records'),
                    "total_results": len(grouped),
                    "suggested_chart": chart_data
                }

        # 3. Check for Direct Filter Query (e.g. "profit > 1000", "region is West", "churn == Yes")
        filter_match = re.search(r'([a-zA-Z0-9_]+)\s*(==|!=|>=|<=|>|<|=|contains|is)\s*([a-zA-Z0-9_\.\-]+)', q)
        if filter_match:
            col_raw = filter_match.group(1)
            op = filter_match.group(2)
            val_raw = filter_match.group(3)

            matched_col = find_column_in_text(col_raw, cols)
            if matched_col:
                op_clean = '==' if op in ['=', 'is'] else op
                filtered_df = df.copy()

                if pd.api.types.is_numeric_dtype(filtered_df[matched_col]):
                    try:
                        num_val = float(val_raw)
                        if op_clean == '>':
                            filtered_df = filtered_df[filtered_df[matched_col] > num_val]
                        elif op_clean == '<':
                            filtered_df = filtered_df[filtered_df[matched_col] < num_val]
                        elif op_clean == '>=':
                            filtered_df = filtered_df[filtered_df[matched_col] >= num_val]
                        elif op_clean == '<=':
                            filtered_df = filtered_df[filtered_df[matched_col] <= num_val]
                        elif op_clean == '==':
                            filtered_df = filtered_df[filtered_df[matched_col] == num_val]
                        elif op_clean == '!=':
                            filtered_df = filtered_df[filtered_df[matched_col] != num_val]
                    except ValueError:
                        pass
                else:
                    if op_clean == '==':
                        filtered_df = filtered_df[filtered_df[matched_col].astype(str).str.lower() == val_raw.lower()]
                    elif op_clean == '!=':
                        filtered_df = filtered_df[filtered_df[matched_col].astype(str).str.lower() != val_raw.lower()]
                    elif op_clean == 'contains':
                        filtered_df = filtered_df[filtered_df[matched_col].astype(str).str.lower().str.contains(val_raw.lower(), regex=False)]

                preview = filtered_df.head(25).to_dict(orient='records')
                return {
                    "query": query_str,
                    "interpretation": f"Filtered records where '{matched_col}' {op_clean} '{val_raw}'. Found {len(filtered_df):,} matching rows.",
                    "columns": list(filtered_df.columns),
                    "data": preview,
                    "total_results": len(filtered_df),
                    "suggested_chart": None
                }

        # 4. Default Search Fallback
        # Search query term across string columns
        mask = df.astype(str).apply(lambda col: col.str.lower().str.contains(q, regex=False)).any(axis=1)
        matches = df[mask]
        preview = matches.head(25).to_dict(orient='records')

        return {
            "query": query_str,
            "interpretation": f"Searched entire dataset for text '{query_str}'. Found {len(matches):,} matching records.",
            "columns": list(df.columns),
            "data": preview,
            "total_results": len(matches),
            "suggested_chart": None
        }
