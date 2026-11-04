import re
import difflib
from typing import Dict, Any, List, Optional, Tuple, Set, Union
import pandas as pd
import numpy as np

try:
    import rapidfuzz
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

# Word-to-number dictionary for natural numbers
WORD_TO_NUM = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
    'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
    'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
    'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
    'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
    'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90, 'hundred': 100
}

# Common column semantic aliases across standard business and HR domains
DOMAIN_ALIASES = {
    'salary': ['MonthlyIncome', 'Monthly_Income_USD', 'MonthlyRate', 'HourlyRate', 'DailyRate', 'Salary', 'BaseSalary'],
    'income': ['MonthlyIncome', 'Monthly_Income_USD', 'MonthlyRate', 'HourlyRate', 'Salary', 'Revenue'],
    'monthly income': ['MonthlyIncome', 'Monthly_Income_USD'],
    'monthly rate': ['MonthlyRate'],
    'hourly rate': ['HourlyRate'],
    'daily rate': ['DailyRate'],
    'pay': ['MonthlyIncome', 'Monthly_Income_USD', 'Salary'],
    'wage': ['HourlyRate', 'MonthlyIncome', 'Salary'],
    'compensation': ['MonthlyIncome', 'Monthly_Income_USD', 'Salary'],
    'earnings': ['MonthlyIncome', 'Profit', 'Salary'],
    'job role': ['JobRole', 'Job_Role'],
    'jobrole': ['JobRole', 'Job_Role'],
    'role': ['JobRole', 'Job_Role'],
    'position': ['JobRole', 'Job_Role'],
    'title': ['JobRole', 'Job_Role'],
    'department': ['Department', 'Dept'],
    'dept': ['Department', 'Dept'],
    'division': ['Department', 'Dept'],
    'age': ['Age'],
    'years of age': ['Age'],
    'attrition': ['Attrition', 'Churn', 'Turnover'],
    'churn': ['Attrition', 'Churn'],
    'turnover': ['Attrition', 'Churn'],
    'left': ['Attrition', 'Churn'],
    'leave': ['Attrition', 'Churn'],
    'leaving': ['Attrition', 'Churn'],
    'stayed': ['Attrition', 'Churn'],
    'overtime': ['OverTime', 'Overtime'],
    'over time': ['OverTime', 'Overtime'],
    'extra hours': ['OverTime', 'Overtime'],
    'satisfaction': ['JobSatisfaction', 'Job_Satisfaction_1to4', 'EnvironmentSatisfaction', 'RelationshipSatisfaction', 'Customer_Rating'],
    'job satisfaction': ['JobSatisfaction', 'Job_Satisfaction_1to4'],
    'environment satisfaction': ['EnvironmentSatisfaction'],
    'relationship satisfaction': ['RelationshipSatisfaction'],
    'travel': ['BusinessTravel', 'Travel'],
    'business travel': ['BusinessTravel', 'Travel'],
    'travel frequency': ['BusinessTravel', 'Travel'],
    'tenure': ['YearsAtCompany', 'Tenure_At_Company', 'Tenure_Months', 'TotalWorkingYears'],
    'years at company': ['YearsAtCompany', 'Tenure_At_Company'],
    'years in current role': ['YearsInCurrentRole'],
    'years with curr manager': ['YearsWithCurrManager', 'YearsWithCurrentManager'],
    'years since last promotion': ['YearsSinceLastPromotion'],
    'total working years': ['TotalWorkingYears'],
    'distance from home': ['DistanceFromHome'],
    'distance': ['DistanceFromHome'],
    'education': ['Education', 'EducationField'],
    'education field': ['EducationField'],
    'marital status': ['MaritalStatus'],
    'gender': ['Gender', 'Sex'],
    'sex': ['Gender', 'Sex'],
    'performance rating': ['PerformanceRating'],
    'stock option level': ['StockOptionLevel'],
    'num companies worked': ['NumCompaniesWorked'],
    'work life balance': ['WorkLifeBalance'],
    'job involvement': ['JobInvolvement'],
    'job level': ['JobLevel'],
    'sales': ['Sales', 'TotalSales', 'Revenue'],
    'profit': ['Profit', 'NetProfit'],
    'category': ['Category', 'ProductCategory', 'Customer_Segment'],
    'sub category': ['SubCategory', 'Sub_Category'],
    'region': ['Region', 'Territory', 'Area']
}


def _clean_text(s: str) -> str:
    """Normalize text by lowercasing and stripping non-alphanumeric characters."""
    return re.sub(r'[^a-z0-9]', '', str(s).lower())


def _fuzzy_similarity(s1: str, s2: str) -> float:
    """Calculate string similarity ratio between 0.0 and 1.0."""
    if HAS_RAPIDFUZZ:
        return fuzz.token_sort_ratio(s1, s2) / 100.0
    return difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def _fmt(val: Any, decimals: int = 2) -> Any:
    """Format numeric values cleanly."""
    if pd.isna(val) or val is None:
        return "-"
    if isinstance(val, (int, np.integer)):
        return int(val)
    if isinstance(val, (float, np.floating)):
        if float(val).is_integer():
            return int(val)
        return round(float(val), decimals)
    return val


def _clean_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format dictionary records with rounded floats."""
    cleaned = []
    for row in records:
        clean_row = {}
        for k, v in row.items():
            clean_row[k] = _fmt(v)
        cleaned.append(clean_row)
    return cleaned


class NLPColumnResolver:
    """Robust column resolution using exact, alias, and fuzzy matching."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.columns = list(df.columns)
        self.clean_col_map: Dict[str, str] = {}
        self.exact_lower_map: Dict[str, str] = {}

        for col in self.columns:
            self.clean_col_map[_clean_text(col)] = col
            self.exact_lower_map[col.lower().strip()] = col

        # Build alias lookup mapped to existing columns
        self.alias_map: Dict[str, str] = {}
        for alias, targets in DOMAIN_ALIASES.items():
            for target in targets:
                for actual_col in self.columns:
                    if _clean_text(actual_col) == _clean_text(target):
                        self.alias_map[alias] = actual_col
                        self.alias_map[_clean_text(alias)] = actual_col
                        break
                if alias in self.alias_map:
                    break

    def resolve(self, text: str, prefer_numeric: Optional[bool] = None) -> Optional[str]:
        """Find the best column match for a given phrase."""
        if not text:
            return None

        text_stripped = text.strip()
        text_lower = text_stripped.lower()
        text_clean = _clean_text(text)

        # 1. Exact match on lower or clean
        if text_lower in self.exact_lower_map:
            return self.exact_lower_map[text_lower]
        if text_clean in self.clean_col_map:
            return self.clean_col_map[text_clean]

        # 2. Domain alias match
        if text_lower in self.alias_map:
            return self.alias_map[text_lower]
        if text_clean in self.alias_map:
            return self.alias_map[text_clean]

        # 3. Word token matching in alias map
        for alias, actual in self.alias_map.items():
            if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
                return actual

        # 4. Substring match against column names
        candidates: List[Tuple[str, float]] = []
        for col in self.columns:
            col_lower = col.lower()
            col_clean = _clean_text(col)

            if col_clean in text_clean and len(col_clean) >= 3:
                score = 0.95 + (len(col_clean) / (len(text_clean) + 10))
                candidates.append((col, score))
            elif text_clean in col_clean and len(text_clean) >= 3:
                score = 0.90 + (len(text_clean) / (len(col_clean) + 10))
                candidates.append((col, score))
            elif re.search(r'\b' + re.escape(col_lower) + r'\b', text_lower):
                candidates.append((col, 0.99))

        # 5. Fuzzy match
        for col in self.columns:
            sim = _fuzzy_similarity(text_lower, col.lower())
            if sim >= 0.75:
                candidates.append((col, sim))

        if not candidates:
            return None

        # Sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)

        if prefer_numeric is not None:
            for col, score in candidates:
                is_num = pd.api.types.is_numeric_dtype(self.df[col])
                if is_num == prefer_numeric:
                    return col

        return candidates[0][0]

    def extract_all_columns(self, text: str) -> List[str]:
        """Extract all column names mentioned in text in order of appearance."""
        found: List[Tuple[int, str]] = []
        text_lower = text.lower()

        # Check full column names
        for col in self.columns:
            col_lower = col.lower()
            pattern = r'\b' + re.escape(col_lower) + r'\b'
            for match in re.finditer(pattern, text_lower):
                found.append((match.start(), col))
            
            # Also check spaced out pascal case (e.g. "Monthly Income" for "MonthlyIncome")
            col_spaced = re.sub(r'([A-Z])', r' \1', col).strip().lower()
            if col_spaced != col_lower:
                pattern_sp = r'\b' + re.escape(col_spaced) + r'\b'
                for match in re.finditer(pattern_sp, text_lower):
                    found.append((match.start(), col))

        # Check aliases
        for alias, actual in self.alias_map.items():
            pattern = r'\b' + re.escape(alias) + r'\b'
            for match in re.finditer(pattern, text_lower):
                found.append((match.start(), actual))

        # Deduplicate while preserving earliest appearance
        found.sort(key=lambda x: x[0])
        res: List[str] = []
        seen: Set[str] = set()
        for _, col in found:
            if col not in seen:
                seen.add(col)
                res.append(col)
        return res


class NLPQueryEngine:
    """Primary Natural Language Processing Query Engine for DataNexus."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.resolver = NLPColumnResolver(df)
        self.numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns]
        self.cat_cols = [c for c in df.select_dtypes(include=['object', 'category', 'string', 'bool']).columns]

    def process_query(self, raw_query: str) -> Optional[Dict[str, Any]]:
        """Parse user natural language query and safely execute using Pandas.
        
        Returns:
            Dict[str, Any] on successful understanding and execution,
            or None if the query should be handled by the fallback system.
        """
        q = raw_query.strip()
        if not q:
            return None

        q_lower = q.lower().rstrip('?!.')
        q_norm = self._normalize_number_words(q_lower)

        # 0. Specialized queries delegated to rule-based fallback system
        # (Correlation, Distributions, Causal impact, Left vs Stayed comparison, and "Which <group> has the highest/lowest <metric>")
        if re.search(r'\b(correlation|corr|relationship)\b', q_lower):
            return None
        if re.search(r'\bwhich\s+(.+?)\s+has\s+the\s+(highest|most|lowest|least|maximum|max|minimum|min)\b', q_lower):
            return None
        if re.search(r'\bdistribution\b', q_lower):
            return None
        if re.search(r'\b(affect|impact|cause)\b', q_lower):
            return None
        if 'left' in q_lower and 'stayed' in q_lower:
            return None

        # 1. Try Column Projection: "Show Age and Department", "Select Age, Department"
        col_proj = self._handle_column_projection(q_norm, raw_query)
        if col_proj is not None:
            return col_proj

        # 2. Try Top N / Bottom N / Highest N: "Top 5 departments by attrition", "Top 5 by MonthlyIncome"
        top_res = self._handle_top_n(q_norm, raw_query)
        if top_res is not None:
            return top_res

        # 3. Try Group Comparison / Department-wise: "Compare attrition by department", "Attrition by department"
        grp_comp = self._handle_group_comparison(q_norm, raw_query)
        if grp_comp is not None:
            return grp_comp

        # 4. Try Aggregation: "Find average income of employees who left", "Average MonthlyIncome by Department", "Sum of MonthlyIncome"
        agg_res = self._handle_aggregation(q_norm, raw_query)
        if agg_res is not None:
            return agg_res

        # 5. Try Filter List: "Show employees above 35", "Show employees above 35 working overtime", "Age between 30 and 40"
        filter_res = self._handle_filtering(q_norm, raw_query)
        if filter_res is not None:
            return filter_res

        # 6. Try Sorting: "Sort employees by age", "Order by income descending"
        sort_res = self._handle_sorting(q_norm, raw_query)
        if sort_res is not None:
            return sort_res

        # Not recognized with high confidence by NLP -> return None to invoke existing fallback
        return None

    def _normalize_number_words(self, text: str) -> str:
        """Convert written numbers ('five', 'ten', 'thirty five') into numeric digits."""
        words = text.split()
        out = []
        i = 0
        while i < len(words):
            w = words[i]
            # Check two-word numbers like 'thirty five'
            if i + 1 < len(words):
                w2 = words[i + 1]
                if w in ('twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety') and w2 in WORD_TO_NUM:
                    val = WORD_TO_NUM[w] + WORD_TO_NUM[w2]
                    out.append(str(val))
                    i += 2
                    continue
            if w in WORD_TO_NUM:
                out.append(str(WORD_TO_NUM[w]))
            else:
                out.append(w)
            i += 1
        return " ".join(out)

    # -------------------------------------------------------------------------
    # 1. COLUMN PROJECTION (e.g. "Show Age and Department", "Select Age, Department")
    # -------------------------------------------------------------------------
    def _handle_column_projection(self, q: str, raw_query: str) -> Optional[Dict[str, Any]]:
        proj_pattern = re.match(
            r'^(?:show|display|list|view|select|get|columns?)\s+(?:only\s+)?(?:the\s+)?(?:columns?|fields?|variables?)?\s*(.+)$',
            q
        )
        if not proj_pattern:
            return None

        # Disqualify if it contains filter, aggregation, ranking or comparison words
        stop_words = [
            'above', 'below', 'greater', 'less', 'more', 'under', 'over', 'older', 'younger',
            'between', '>', '<', '=', '>=', '<=', '!=', 'average', 'avg', 'mean', 'sum',
            'min', 'max', 'count', 'median', 'top', 'bottom', 'highest', 'lowest', 'compare',
            'where', 'who', 'whose', 'left', 'stayed', 'working overtime'
        ]
        if any(re.search(r'\b' + re.escape(sw) + r'\b', q) for sw in stop_words):
            return None

        remainder = proj_pattern.group(1).strip()
        parts = [p.strip() for p in re.split(r',|\band\b', remainder) if p.strip()]
        if not parts:
            return None

        matched_cols: List[str] = []
        for p in parts:
            col = self.resolver.resolve(p)
            if col and col not in matched_cols:
                matched_cols.append(col)

        # Must have matched at least one column and the majority of requested tokens
        if not matched_cols or len(matched_cols) < len(parts) * 0.6:
            return None

        preview_df = self.df[matched_cols].head(50)
        data = _clean_records(preview_df.to_dict(orient='records'))
        cols_str = ", ".join(matched_cols)
        explanation = f"Displaying {len(matched_cols)} requested column(s): {cols_str} across {len(self.df):,} total records."

        return {
            "query": raw_query,
            "interpretation": f"Selected column projection: [{cols_str}].",
            "columns": matched_cols,
            "data": data,
            "total_results": len(self.df),
            "suggested_chart": None,
            "explanation": explanation,
            "engine": "nlp",
            "applied_filters": [],
            "answer": f"Here is the data for {cols_str} ({len(self.df):,} rows)."
        }

    # -------------------------------------------------------------------------
    # 2. TOP N / BOTTOM N (e.g. "Top 5 departments by attrition", "Top 5 by income")
    # -------------------------------------------------------------------------
    def _handle_top_n(self, q: str, raw_query: str) -> Optional[Dict[str, Any]]:
        top_match = re.search(
            r'\b(top|bottom|highest|lowest|first|last)\s+(\d+)\s*(?:departments?|roles?|categories?|groups?|records?|employees?|items?)?\s*(?:by|in|for|with)?\s*(.+)?',
            q
        )
        if not top_match:
            return None

        direction = top_match.group(1)
        is_asc = direction in ('bottom', 'lowest', 'last')
        n = int(top_match.group(2))
        remainder = top_match.group(3).strip() if top_match.group(3) else ""

        # Case A: Group-level ranking ("top 5 departments by attrition")
        group_keywords = ['department', 'dept', 'job role', 'role', 'education field', 'category', 'region', 'gender']
        detected_group: Optional[str] = None
        for gk in group_keywords:
            if gk in q:
                resolved_g = self.resolver.resolve(gk, prefer_numeric=False)
                if resolved_g:
                    detected_group = resolved_g
                    break

        if detected_group:
            metric_target = self.resolver.resolve(remainder)
            if not metric_target and remainder:
                metric_target = self.resolver.resolve(remainder)

            if metric_target:
                # If metric is binary (like Attrition)
                vals_lower = set(self.df[metric_target].dropna().astype(str).str.lower().unique())
                if vals_lower <= {'yes', 'no', '1', '0', 'true', 'false'}:
                    grp_data = []
                    pos_vals = {'yes', '1', 'true'}
                    for g_val, g_df in self.df.groupby(detected_group):
                        tot = len(g_df)
                        pos_cnt = int(g_df[metric_target].astype(str).str.lower().isin(pos_vals).sum())
                        rate = round(pos_cnt / tot * 100, 2) if tot > 0 else 0.0
                        grp_data.append({
                            detected_group: str(g_val),
                            "Total Employees": tot,
                            f"{metric_target} (Yes)": pos_cnt,
                            f"{metric_target} Rate (%)": rate
                        })
                    res_df = pd.DataFrame(grp_data).sort_values(by=f"{metric_target} (Yes)", ascending=is_asc).head(n)
                    data = _clean_records(res_df.to_dict(orient='records'))
                    top_names = ", ".join([f"{r[detected_group]} ({r[f'{metric_target} (Yes)']})" for r in data[:3]])
                    explanation = f"Top {len(data)} {detected_group} groups ranked by {metric_target}: {top_names}."

                    return {
                        "query": raw_query,
                        "interpretation": f"Top {n} {detected_group} groups ranked by {metric_target}.",
                        "columns": list(res_df.columns),
                        "data": data,
                        "total_results": len(data),
                        "suggested_chart": "bar",
                        "explanation": explanation,
                        "engine": "nlp",
                        "applied_filters": [],
                        "answer": explanation
                    }
                elif metric_target in self.numeric_cols:
                    grouped = self.df.groupby(detected_group)[metric_target].mean().reset_index()
                    val_col = f"Average {metric_target}"
                    grouped.columns = [detected_group, val_col]
                    grouped[val_col] = grouped[val_col].round(2)
                    grouped = grouped.sort_values(by=val_col, ascending=is_asc).head(n)
                    data = _clean_records(grouped.to_dict(orient='records'))
                    top_row = data[0] if data else {}
                    explanation = f"Top {len(data)} {detected_group} groups by average {metric_target}, led by '{top_row.get(detected_group)}' ({top_row.get(val_col)})."

                    return {
                        "query": raw_query,
                        "interpretation": f"Top {n} {detected_group} groups by average {metric_target}.",
                        "columns": list(grouped.columns),
                        "data": data,
                        "total_results": len(data),
                        "suggested_chart": "bar",
                        "explanation": explanation,
                        "engine": "nlp",
                        "applied_filters": [],
                        "answer": explanation
                    }

        # Case B: Row-level ranking ("Top 5 by MonthlyIncome", "Bottom 5 by Age")
        sort_col = self.resolver.resolve(remainder, prefer_numeric=True) if remainder else (self.numeric_cols[0] if self.numeric_cols else None)
        if not sort_col or sort_col not in self.df.columns:
            return None

        ranked_df = self.df.sort_values(by=sort_col, ascending=is_asc).head(n)
        display_cols = [sort_col]
        for c in self.cat_cols:
            if c not in display_cols and _clean_text(c) not in ('over18', 'id'):
                display_cols.append(c)
            if len(display_cols) >= 4:
                break
        for c in self.numeric_cols:
            if c not in display_cols and _clean_text(c) not in ('employeecount', 'standardhours', 'employeenumber', 'id'):
                display_cols.append(c)
            if len(display_cols) >= 8:
                break

        preview_df = ranked_df[display_cols]
        data = _clean_records(preview_df.to_dict(orient='records'))
        dir_label = "lowest" if is_asc else "highest"
        best_val = _fmt(ranked_df[sort_col].iloc[0]) if len(ranked_df) > 0 else "-"
        explanation = f"Showing the {len(data)} records with the {dir_label} {sort_col}, starting with {best_val}."

        return {
            "query": raw_query,
            "interpretation": f"{direction.capitalize()} {n} records ranked by '{sort_col}'.",
            "columns": display_cols,
            "data": data,
            "total_results": len(data),
            "suggested_chart": "bar",
            "explanation": explanation,
            "engine": "nlp",
            "applied_filters": [],
            "answer": f"Here are the {direction} {len(data)} records by {sort_col}."
        }

    # -------------------------------------------------------------------------
    # 3. GROUP COMPARISONS (e.g. "Compare attrition by department", "Attrition by department")
    # -------------------------------------------------------------------------
    def _handle_group_comparison(self, q: str, raw_query: str) -> Optional[Dict[str, Any]]:
        comp_match = re.search(
            r'(?:compare|breakdown|difference\s+in|distribution\s+of)?\s*(.+?)\s+(?:by|across|between|per|in)\s+(.+)',
            q
        )
        if not comp_match:
            dept_wise = re.search(r'([a-z\s]+?)(?:-wise|\s+wise)\s+(.+)', q)
            if dept_wise:
                group_phrase = dept_wise.group(1).strip()
                metric_phrase = dept_wise.group(2).strip()
            else:
                return None
        else:
            metric_phrase = comp_match.group(1).strip()
            group_phrase = comp_match.group(2).strip()

        clean_metric = re.sub(r'\b(compare|rate|percentage|count|number\s+of|the|overall)\b', '', metric_phrase).strip()
        if not clean_metric:
            clean_metric = metric_phrase

        group_col = self.resolver.resolve(group_phrase, prefer_numeric=False)
        metric_col = self.resolver.resolve(clean_metric)

        if not group_col:
            return None

        # Record count breakdown if no specific metric or asking for employees/records
        if not metric_col or metric_col == group_col or clean_metric in ('employees', 'records', 'people', 'all', 'staff'):
            counted = self.df.groupby(group_col).size().reset_index(name='Count')
            tot = len(self.df)
            counted['Percentage (%)'] = (counted['Count'] / tot * 100).round(2)
            counted = counted.sort_values(by='Count', ascending=False)
            data = _clean_records(counted.to_dict(orient='records'))
            top_g = counted.iloc[0]
            explanation = f"Breakdown by {group_col}: '{top_g[group_col]}' represents {top_g['Count']:,} records ({top_g['Percentage (%)']}% of all {tot:,} records)."

            return {
                "query": raw_query,
                "interpretation": f"Record count breakdown by '{group_col}'.",
                "columns": list(counted.columns),
                "data": data,
                "total_results": len(data),
                "suggested_chart": "bar",
                "explanation": explanation,
                "engine": "nlp",
                "applied_filters": [],
                "answer": explanation
            }

        # Binary metric comparison (e.g. Attrition, OverTime)
        vals_lower = set(self.df[metric_col].dropna().astype(str).str.lower().unique())
        if vals_lower <= {'yes', 'no', '1', '0', 'true', 'false'}:
            pos_vals = {'yes', '1', 'true'}
            grp_data = []
            for g_val, g_df in self.df.groupby(group_col):
                total = len(g_df)
                pos_cnt = int(g_df[metric_col].astype(str).str.lower().isin(pos_vals).sum())
                neg_cnt = total - pos_cnt
                rate = round(pos_cnt / total * 100, 2) if total > 0 else 0.0
                grp_data.append({
                    group_col: str(g_val),
                    "Total Employees": total,
                    f"{metric_col} (Left/Yes)": pos_cnt,
                    f"{metric_col} (Stayed/No)": neg_cnt,
                    f"{metric_col} Rate (%)": rate
                })
            res_df = pd.DataFrame(grp_data).sort_values(by=f"{metric_col} Rate (%)", ascending=False)
            data = _clean_records(res_df.to_dict(orient='records'))
            top_row = res_df.iloc[0]
            low_row = res_df.iloc[-1]
            explanation = (
                f"{group_col} {metric_col} comparison: highest rate is in '{top_row[group_col]}' at {top_row[f'{metric_col} Rate (%)']}% "
                f"({top_row[f'{metric_col} (Left/Yes)']} of {top_row['Total Employees']}), "
                f"lowest is in '{low_row[group_col]}' at {low_row[f'{metric_col} Rate (%)']}%."
            )

            return {
                "query": raw_query,
                "interpretation": f"Comparison of '{metric_col}' across '{group_col}'.",
                "columns": list(res_df.columns),
                "data": data,
                "total_results": len(data),
                "suggested_chart": "bar",
                "explanation": explanation,
                "engine": "nlp",
                "applied_filters": [],
                "answer": explanation
            }

        # Numeric metric comparison
        if metric_col in self.numeric_cols:
            agg_type = 'mean'
            if any(w in q for w in ('sum', 'total')):
                agg_type = 'sum'
            elif any(w in q for w in ('median',)):
                agg_type = 'median'
            elif any(w in q for w in ('min', 'minimum')):
                agg_type = 'min'
            elif any(w in q for w in ('max', 'maximum', 'highest')):
                agg_type = 'max'

            grouped = self.df.groupby(group_col)[metric_col].agg(agg_type).reset_index()
            val_col = f"{agg_type.capitalize()} {metric_col}"
            grouped.columns = [group_col, val_col]
            grouped[val_col] = grouped[val_col].round(2)
            grouped = grouped.sort_values(by=val_col, ascending=False)
            data = _clean_records(grouped.to_dict(orient='records'))
            top_row = grouped.iloc[0]
            low_row = grouped.iloc[-1]
            explanation = (
                f"{agg_type.capitalize()} {metric_col} across {group_col}: highest is '{top_row[group_col]}' ({_fmt(top_row[val_col])}), "
                f"lowest is '{low_row[group_col]}' ({_fmt(low_row[val_col])})."
            )

            return {
                "query": raw_query,
                "interpretation": f"{agg_type.capitalize()} of '{metric_col}' compared by '{group_col}'.",
                "columns": list(grouped.columns),
                "data": data,
                "total_results": len(data),
                "suggested_chart": "bar",
                "explanation": explanation,
                "engine": "nlp",
                "applied_filters": [],
                "answer": explanation
            }

        return None

    # -------------------------------------------------------------------------
    # 4. AGGREGATION (e.g. "Find average income of employees who left", "Average salary by department")
    # -------------------------------------------------------------------------
    def _handle_aggregation(self, q: str, raw_query: str) -> Optional[Dict[str, Any]]:
        agg_pattern = re.search(
            r'\b(average|avg|mean|sum|total|median|minimum|min|maximum|max|highest|lowest|count)\b\s+(?:of\s+)?(.+)',
            q
        )
        if not agg_pattern:
            return None

        agg_word = agg_pattern.group(1).lower()
        remainder = agg_pattern.group(2).strip()

        agg_map = {
            'average': 'mean', 'avg': 'mean', 'mean': 'mean',
            'sum': 'sum', 'total': 'sum',
            'median': 'median',
            'min': 'min', 'minimum': 'min', 'lowest': 'min',
            'max': 'max', 'maximum': 'max', 'highest': 'max',
            'count': 'count'
        }
        agg_func = agg_map.get(agg_word, 'mean')

        # Cohort filter clause: "of employees who left", "for employees with overtime"
        cohort_mask = pd.Series(True, index=self.df.index)
        cohort_desc: List[str] = []

        if any(w in remainder for w in ('who left', 'who have left', 'employees that left', 'attrition yes', 'attrition is yes')):
            attr_col = self.resolver.resolve('attrition')
            if attr_col:
                cohort_mask = self.df[attr_col].astype(str).str.lower().isin(['yes', '1', 'true'])
                cohort_desc.append(f"{attr_col} == 'Yes'")
                remainder = re.sub(r'\b(who\s+left|who\s+have\s+left|employees\s+that\s+left|attrition\s+is\s+yes|attrition\s+yes)\b', '', remainder).strip()
        elif any(w in remainder for w in ('who stayed', 'employees who stay', 'attrition no')):
            attr_col = self.resolver.resolve('attrition')
            if attr_col:
                cohort_mask = self.df[attr_col].astype(str).str.lower().isin(['no', '0', 'false'])
                cohort_desc.append(f"{attr_col} == 'No'")
                remainder = re.sub(r'\b(who\s+stayed|employees\s+who\s+stay|attrition\s+no)\b', '', remainder).strip()

        # Group by clause: "by Department"
        by_match = re.search(r'\s+(?:by|across|per|in)\s+(.+)$', remainder)
        group_col: Optional[str] = None
        if by_match:
            grp_text = by_match.group(1).strip()
            group_col = self.resolver.resolve(grp_text, prefer_numeric=False)
            remainder = remainder[:by_match.start()].strip()

        # Target metric
        target_metric = self.resolver.resolve(remainder, prefer_numeric=True)
        if not target_metric:
            return None

        filtered_df = self.df[cohort_mask]

        if group_col:
            if target_metric not in self.numeric_cols and agg_func != 'count':
                return None
            grouped = filtered_df.groupby(group_col)[target_metric].agg(agg_func).reset_index()
            val_col = f"{agg_func.capitalize()} {target_metric}"
            grouped.columns = [group_col, val_col]
            if agg_func != 'count':
                grouped[val_col] = grouped[val_col].round(2)
            grouped = grouped.sort_values(by=val_col, ascending=False)
            data = _clean_records(grouped.to_dict(orient='records'))
            top = grouped.iloc[0] if len(grouped) > 0 else {}
            explanation = (
                f"Calculated {agg_func} of {target_metric} grouped by {group_col}: "
                f"highest is '{top.get(group_col)}' ({_fmt(top.get(val_col))})."
            )

            return {
                "query": raw_query,
                "interpretation": f"{agg_func.capitalize()} of '{target_metric}' grouped by '{group_col}'.",
                "columns": list(grouped.columns),
                "data": data,
                "total_results": len(data),
                "suggested_chart": "bar",
                "explanation": explanation,
                "engine": "nlp",
                "applied_filters": cohort_desc,
                "answer": explanation
            }
        else:
            series = pd.to_numeric(filtered_df[target_metric], errors='coerce').dropna()
            calc_val = getattr(series, agg_func)() if len(series) > 0 else 0
            formatted_val = _fmt(calc_val)
            
            if any(term in target_metric.lower() for term in ('income', 'salary', 'sales', 'profit', 'rate')):
                val_display = f"${formatted_val:,.2f}" if isinstance(formatted_val, (int, float)) else str(formatted_val)
            else:
                val_display = str(formatted_val)

            filter_str = f" for employees where {' and '.join(cohort_desc)}" if cohort_desc else ""
            explanation = f"The {agg_func} of {target_metric}{filter_str} is {val_display} (computed across {len(series):,} valid records)."

            data = [{
                "Metric": f"{agg_func.capitalize()} of {target_metric}",
                "Value": val_display,
                "Sample Count": len(series)
            }]

            return {
                "query": raw_query,
                "interpretation": f"Calculated overall {agg_func.upper()} of '{target_metric}'{filter_str}.",
                "columns": ["Metric", "Value", "Sample Count"],
                "data": data,
                "total_results": 1,
                "suggested_chart": None,
                "explanation": explanation,
                "engine": "nlp",
                "applied_filters": cohort_desc,
                "answer": f"{agg_func.capitalize()} {target_metric}: {val_display}"
            }

    # -------------------------------------------------------------------------
    # 5. FILTERING (e.g. "Show employees above 35", "above 35 working overtime", "Age between 30 and 40")
    # -------------------------------------------------------------------------
    def _handle_filtering(self, q: str, raw_query: str) -> Optional[Dict[str, Any]]:
        has_filter_trigger = bool(re.search(
            r'\b(show|find|list|get|filter|display|who|where|whose|above|below|older|younger|over|under|between|greater|less|working|overtime|staff|employees?)\b',
            q
        ))
        if not has_filter_trigger and not any(op in q for op in ('>', '<', '=', '>=', '<=')):
            return None

        conditions = self._parse_conditions(q)
        if not conditions:
            return None

        # Check for top-level OR connector
        has_top_or = bool(re.search(r'\b\s+or\s+\b', q))

        current_mask = pd.Series(True, index=self.df.index)
        applied_descs: List[str] = []
        filter_cols: List[str] = []

        if has_top_or and len(conditions) > 1:
            or_mask = pd.Series(False, index=self.df.index)
            for cond in conditions:
                m, desc, col = self._evaluate_single_condition(cond)
                if m is not None:
                    or_mask = or_mask | m
                    applied_descs.append(desc)
                    if col and col not in filter_cols:
                        filter_cols.append(col)
            current_mask = or_mask
            combined_desc = " OR ".join(applied_descs)
        else:
            for cond in conditions:
                m, desc, col = self._evaluate_single_condition(cond)
                if m is not None:
                    current_mask = current_mask & m
                    applied_descs.append(desc)
                    if col and col not in filter_cols:
                        filter_cols.append(col)
            combined_desc = " AND ".join(applied_descs)

        if not applied_descs:
            return None

        filtered_df = self.df[current_mask]
        total_matching = len(filtered_df)

        preview_cols = list(filter_cols)
        key_cols = ['Department', 'JobRole', 'MonthlyIncome', 'Age', 'Attrition', 'OverTime', 'Gender', 'Sales', 'Profit', 'Category']
        for kc in key_cols:
            if kc in self.df.columns and kc not in preview_cols:
                preview_cols.append(kc)
            if len(preview_cols) >= 8:
                break

        for col in self.df.columns:
            if col not in preview_cols and _clean_text(col) not in ('employeecount', 'standardhours', 'over18'):
                preview_cols.append(col)
            if len(preview_cols) >= 8:
                break

        preview_data = _clean_records(filtered_df[preview_cols].head(50).to_dict(orient='records'))

        if total_matching == 0:
            explanation = f"Found 0 records matching condition: {combined_desc}."
            answer = f"No matching records found where {combined_desc}."
        else:
            pct = round(total_matching / len(self.df) * 100, 1)
            explanation = f"Found {total_matching:,} records matching condition: {combined_desc} ({pct}% of {len(self.df):,} total records)."
            answer = f"There are {total_matching:,} records matching {combined_desc}."

        return {
            "query": raw_query,
            "interpretation": f"Filtered records where {combined_desc}.",
            "columns": preview_cols,
            "data": preview_data,
            "total_results": total_matching,
            "suggested_chart": None,
            "explanation": explanation,
            "engine": "nlp",
            "applied_filters": applied_descs,
            "answer": answer
        }

    def _parse_conditions(self, full_query: str) -> List[Dict[str, Any]]:
        """Parse conditions from query string with support for multi-clause AND/OR."""
        conditions: List[Dict[str, Any]] = []
        text = full_query

        # 1. Extract boolean / categorical flags first and remove them from text to simplify remaining numeric parsing
        # OverTime
        if re.search(r'\b(?:working\s+overtime|work\s+overtime|has\s+overtime|with\s+overtime|overtime\s+(?:is\s+)?yes|overtime)\b', text) and not re.search(r'\b(?:no\s+overtime|not\s+working\s+overtime|without\s+overtime)\b', text):
            ot_col = self.resolver.resolve('overtime')
            if ot_col:
                conditions.append({'col': ot_col, 'op': '==', 'val': 'Yes', 'type': 'exact'})
                text = re.sub(r'\b(?:working\s+overtime|work\s+overtime|has\s+overtime|with\s+overtime|overtime\s+(?:is\s+)?yes|overtime)\b', '', text)
        elif re.search(r'\b(?:no\s+overtime|not\s+working\s+overtime|without\s+overtime)\b', text):
            ot_col = self.resolver.resolve('overtime')
            if ot_col:
                conditions.append({'col': ot_col, 'op': '==', 'val': 'No', 'type': 'exact'})
                text = re.sub(r'\b(?:no\s+overtime|not\s+working\s+overtime|without\s+overtime)\b', '', text)

        # Attrition
        if re.search(r'\b(?:who\s+left|employees\s+who\s+left|resigned|departed|attrition\s+(?:is\s+)?yes)\b', text):
            attr_col = self.resolver.resolve('attrition')
            if attr_col:
                conditions.append({'col': attr_col, 'op': '==', 'val': 'Yes', 'type': 'exact'})
                text = re.sub(r'\b(?:who\s+left|employees\s+who\s+left|resigned|departed|attrition\s+(?:is\s+)?yes)\b', '', text)
        elif re.search(r'\b(?:who\s+stayed|employees\s+who\s+stay|attrition\s+(?:is\s+)?no)\b', text):
            attr_col = self.resolver.resolve('attrition')
            if attr_col:
                conditions.append({'col': attr_col, 'op': '==', 'val': 'No', 'type': 'exact'})
                text = re.sub(r'\b(?:who\s+stayed|employees\s+who\s+stay|attrition\s+(?:is\s+)?no)\b', '', text)

        # Clean introductory words
        clean_text = re.sub(r'^(?:please\s+)?(?:show|find|list|get|filter|display)\s+(?:all\s+)?(?:the\s+)?(?:employees?|records?|rows?|people|staff|workers?|items?|data)?\s*(?:where|who|whose|with)?\s*', '', text).strip()

        # Split remaining clauses by 'and', 'or', commas
        between_map: Dict[str, str] = {}
        def _protect(m):
            k = f"__B_{len(between_map)}__"
            between_map[k] = m.group(0)
            return k

        protected = re.sub(r'\bbetween\s+\d+(?:\.\d+)?\s+and\s+\d+(?:\.\d+)?\b', _protect, clean_text)
        protected = re.sub(r'\bfrom\s+\d+(?:\.\d+)?\s+to\s+\d+(?:\.\d+)?\b', _protect, protected)

        clauses = [c.strip() for c in re.split(r'\s+and\s+|\s+or\s+|\s*,\s*', protected) if c.strip()]
        for idx in range(len(clauses)):
            for k, orig in between_map.items():
                clauses[idx] = clauses[idx].replace(k, orig)

        for clause in clauses:
            if not clause:
                continue

            # Between check
            btw_match = re.search(r'(.+?)?\s*(?:between|from|in\s+range)\s+(\d+(?:\.\d+)?)\s+(?:and|to)\s+(\d+(?:\.\d+)?)', clause)
            if btw_match:
                c_phrase = btw_match.group(1).strip() if btw_match.group(1) else ""
                v1, v2 = float(btw_match.group(2)), float(btw_match.group(3))
                col = self.resolver.resolve(c_phrase, prefer_numeric=True) if c_phrase else None
                if not col:
                    if 'age' in full_query or any(w in full_query for w in ('employees', 'people', 'staff', 'older', 'younger')):
                        col = self.resolver.resolve('age', prefer_numeric=True)
                    elif self.numeric_cols:
                        col = self.numeric_cols[0]
                if col:
                    conditions.append({'col': col, 'op': 'between', 'val': (min(v1, v2), max(v1, v2)), 'type': 'between'})
                    continue

            # Greater than check: "above 35", "older than 35", "age > 35", "over 40"
            gt_match = re.search(r'(.+?)?\s*(?:>=|>|above|over|older\s+than|greater\s+than|more\s+than|higher\s+than|at\s+least|exceeding)\s+(\d+(?:\.\d+)?)', clause)
            if gt_match:
                c_phrase = gt_match.group(1).strip() if gt_match.group(1) else ""
                val = float(gt_match.group(2))
                col = self.resolver.resolve(c_phrase, prefer_numeric=True) if c_phrase else None
                if not col:
                    # Check if entire query or clause refers to age
                    if any(w in full_query for w in ('age', 'older', 'younger', 'employees', 'staff', 'people', 'workers', 'years')) and (15 <= val <= 99 or 'age' in full_query):
                        col = self.resolver.resolve('age', prefer_numeric=True)
                    elif val > 500:
                        col = self.resolver.resolve('salary', prefer_numeric=True) or (self.numeric_cols[0] if self.numeric_cols else None)
                    elif self.numeric_cols:
                        col = self.numeric_cols[0]
                if col:
                    op = '>=' if 'at least' in clause or '>=' in clause else '>'
                    conditions.append({'col': col, 'op': op, 'val': val, 'type': 'numeric'})
                    continue

            # Less than check: "below 35", "under 35", "younger than 35", "age < 35"
            lt_match = re.search(r'(.+?)?\s*(?:<=|<|below|under|younger\s+than|less\s+than|fewer\s+than|lower\s+than|at\s+most)\s+(\d+(?:\.\d+)?)', clause)
            if lt_match:
                c_phrase = lt_match.group(1).strip() if lt_match.group(1) else ""
                val = float(lt_match.group(2))
                col = self.resolver.resolve(c_phrase, prefer_numeric=True) if c_phrase else None
                if not col:
                    if any(w in full_query for w in ('age', 'older', 'younger', 'employees', 'staff', 'people', 'workers', 'years')) and (15 <= val <= 99 or 'age' in full_query):
                        col = self.resolver.resolve('age', prefer_numeric=True)
                    elif val > 500:
                        col = self.resolver.resolve('salary', prefer_numeric=True) or (self.numeric_cols[0] if self.numeric_cols else None)
                    elif self.numeric_cols:
                        col = self.numeric_cols[0]
                if col:
                    op = '<=' if 'at most' in clause or '<=' in clause else '<'
                    conditions.append({'col': col, 'op': op, 'val': val, 'type': 'numeric'})
                    continue

            # Equals check: "Department is Sales", "Department = Sales", "Gender is Female"
            eq_match = re.search(r'(.+?)\s*(?:==|=|is|equals?|in|matching)\s+(.+)', clause)
            if eq_match:
                c_phrase = eq_match.group(1).strip()
                v_phrase = eq_match.group(2).strip().strip("'\"")
                col = self.resolver.resolve(c_phrase)
                if col:
                    conditions.append({'col': col, 'op': '==', 'val': v_phrase, 'type': 'categorical'})
                    continue

        return conditions

    def _evaluate_single_condition(self, cond: Dict[str, Any]) -> Tuple[Optional[pd.Series], str, Optional[str]]:
        """Safely evaluate a parsed condition dictionary into a Boolean pandas Series."""
        col = cond.get('col')
        if not col or col not in self.df.columns:
            return None, "", None

        op = cond.get('op')
        val = cond.get('val')
        c_series = self.df[col]

        # Numeric comparison
        if pd.api.types.is_numeric_dtype(c_series) and isinstance(val, (int, float)):
            num_series = pd.to_numeric(c_series, errors='coerce')
            if op == '>':
                mask = num_series > val
                desc = f"{col} > {int(val) if float(val).is_integer() else val}"
            elif op == '>=':
                mask = num_series >= val
                desc = f"{col} >= {int(val) if float(val).is_integer() else val}"
            elif op == '<':
                mask = num_series < val
                desc = f"{col} < {int(val) if float(val).is_integer() else val}"
            elif op == '<=':
                mask = num_series <= val
                desc = f"{col} <= {int(val) if float(val).is_integer() else val}"
            elif op == '==':
                mask = num_series == val
                desc = f"{col} == {int(val) if float(val).is_integer() else val}"
            elif op == '!=':
                mask = num_series != val
                desc = f"{col} != {int(val) if float(val).is_integer() else val}"
            else:
                return None, "", None
            return mask.fillna(False), desc, col

        # Between comparison
        if op == 'between' and isinstance(val, tuple):
            v1, v2 = val
            num_series = pd.to_numeric(c_series, errors='coerce')
            mask = (num_series >= v1) & (num_series <= v2)
            desc = f"{col} between {int(v1) if float(v1).is_integer() else v1} and {int(v2) if float(v2).is_integer() else v2}"
            return mask.fillna(False), desc, col

        # Categorical comparison
        if isinstance(val, str):
            val_clean = val.strip().lower()
            str_series = c_series.astype(str).str.strip().str.lower()

            actual_cats = c_series.dropna().astype(str).unique()
            best_cat = None
            for cat in actual_cats:
                if cat.lower() == val_clean or _clean_text(cat) == _clean_text(val_clean):
                    best_cat = cat
                    break

            if best_cat is None and HAS_RAPIDFUZZ:
                matches = process.extract(val_clean, [c.lower() for c in actual_cats], limit=1)
                if matches and matches[0][1] >= 80:
                    matched_idx = [c.lower() for c in actual_cats].index(matches[0][0])
                    best_cat = actual_cats[matched_idx]

            target_val = best_cat if best_cat else val
            target_lower = target_val.lower()

            if op == '!=':
                mask = str_series != target_lower
                desc = f"{col} != '{target_val}'"
            else:
                mask = str_series == target_lower
                desc = f"{col} == '{target_val}'"

            return mask.fillna(False), desc, col

        return None, "", None

    # -------------------------------------------------------------------------
    # 6. SORTING (e.g. "Sort employees by age", "Order by income descending")
    # -------------------------------------------------------------------------
    def _handle_sorting(self, q: str, raw_query: str) -> Optional[Dict[str, Any]]:
        sort_match = re.search(
            r'\b(?:sort|order|rank)\s+(?:employees|records|rows|data)?\s*(?:by)?\s+(.+)',
            q
        )
        if not sort_match:
            return None

        remainder = sort_match.group(1).strip()
        is_desc = any(w in remainder for w in ('desc', 'descending', 'highest to lowest', 'down'))
        clean_col_phrase = re.sub(r'\b(desc|descending|asc|ascending)\b', '', remainder).strip()

        col = self.resolver.resolve(clean_col_phrase)
        if not col or col not in self.df.columns:
            return None

        sorted_df = self.df.sort_values(by=col, ascending=not is_desc).head(50)
        show_cols = [col]
        for c in self.df.columns:
            if c not in show_cols and _clean_text(c) not in ('employeecount', 'standardhours', 'over18'):
                show_cols.append(c)
            if len(show_cols) >= 8:
                break

        data = _clean_records(sorted_df[show_cols].to_dict(orient='records'))
        order_str = "descending" if is_desc else "ascending"
        explanation = f"Sorted records by {col} in {order_str} order."

        return {
            "query": raw_query,
            "interpretation": f"Sorted records by '{col}' ({order_str}).",
            "columns": show_cols,
            "data": data,
            "total_results": len(self.df),
            "suggested_chart": None,
            "explanation": explanation,
            "engine": "nlp",
            "applied_filters": [],
            "answer": f"Displaying records sorted by {col} ({order_str})."
        }
