import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

# Word-to-number mapping
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


def _clean_str(s: str) -> str:
    """Normalize string by removing spaces, underscores, dashes and lowercasing."""
    return re.sub(r'[\s_\-]+', '', s.lower())


def _build_column_map(df: pd.DataFrame) -> Dict[str, str]:
    """Build a lookup mapping normalized variants and aliases -> actual column name."""
    col_map: Dict[str, str] = {}
    for col in df.columns:
        c_low = col.lower()
        col_map[c_low] = col
        col_map[c_low.replace('_', '')] = col
        col_map[c_low.replace('_', ' ')] = col
        col_map[c_low.replace(' ', '')] = col
        col_map[_clean_str(col)] = col

    # Common semantic aliases across domains
    aliases = {
        'salary': ['MonthlyIncome', 'Monthly_Income_USD', 'MonthlyRate', 'HourlyRate', 'DailyRate', 'Salary', 'BaseSalary'],
        'income': ['MonthlyIncome', 'Monthly_Income_USD', 'MonthlyRate', 'HourlyRate', 'Salary'],
        'monthly income': ['MonthlyIncome', 'Monthly_Income_USD'],
        'monthlyincome': ['MonthlyIncome', 'Monthly_Income_USD'],
        'job role': ['JobRole', 'Job_Role'],
        'jobrole': ['JobRole', 'Job_Role'],
        'role': ['JobRole', 'Job_Role'],
        'department': ['Department', 'Dept'],
        'age': ['Age'],
        'attrition': ['Attrition', 'Churn', 'Turnover'],
        'left': ['Attrition', 'Churn'],
        'overtime': ['OverTime', 'Overtime'],
        'over time': ['OverTime', 'Overtime'],
        'satisfaction': ['JobSatisfaction', 'Job_Satisfaction_1to4', 'EnvironmentSatisfaction', 'RelationshipSatisfaction', 'Customer_Rating'],
        'job satisfaction': ['JobSatisfaction', 'Job_Satisfaction_1to4'],
        'travel': ['BusinessTravel', 'Travel'],
        'business travel': ['BusinessTravel'],
        'tenure': ['YearsAtCompany', 'Tenure_At_Company', 'Tenure_Months', 'TotalWorkingYears'],
        'years at company': ['YearsAtCompany', 'Tenure_At_Company'],
        'yearsatcompany': ['YearsAtCompany', 'Tenure_At_Company'],
        'sales': ['Sales', 'TotalSales', 'Revenue'],
        'profit': ['Profit', 'NetProfit'],
        'category': ['Category', 'ProductCategory', 'Customer_Segment'],
        'region': ['Region', 'Territory', 'Area'],
        'gender': ['Gender', 'Sex']
    }

    for alias, targets in aliases.items():
        for target in targets:
            for actual_col in df.columns:
                if _clean_str(actual_col) == _clean_str(target):
                    if alias not in col_map:
                        col_map[alias] = actual_col
                    if _clean_str(alias) not in col_map:
                        col_map[_clean_str(alias)] = actual_col
                    break
            if alias in col_map:
                break

    return col_map


def _resolve_column(text: str, df: pd.DataFrame, col_map: Dict[str, str],
                     prefer: str = 'any') -> Optional[str]:
    """Find the best matching column name in text."""
    if not text:
        return None
    text_lower = text.lower().strip()
    text_clean = _clean_str(text)
    numeric_cols = set(df.select_dtypes(include=[np.number]).columns)
    cat_cols = set(df.select_dtypes(include=['object', 'category', 'string', 'bool']).columns)

    # 1. Exact match on clean string
    if text_clean in col_map:
        return col_map[text_clean]

    # 2. Match candidate variants ordered by descending length
    candidates = sorted(col_map.keys(), key=len, reverse=True)
    matches: List[str] = []
    for variant in candidates:
        if ' ' not in variant and len(variant) > 2:
            if re.search(r'\b' + re.escape(variant) + r'\b', text_lower):
                matches.append(col_map[variant])
        else:
            if variant in text_lower:
                matches.append(col_map[variant])

    # Deduplicate while preserving order
    seen = set()
    unique_matches = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            unique_matches.append(m)

    if not unique_matches:
        # Fallback substring check against actual columns
        for col in sorted(df.columns, key=len, reverse=True):
            if _clean_str(col) in text_clean or text_clean in _clean_str(col):
                unique_matches.append(col)
                break

    if not unique_matches:
        return None

    if prefer == 'numeric':
        for m in unique_matches:
            if m in numeric_cols:
                return m
    elif prefer == 'categorical':
        for m in unique_matches:
            if m in cat_cols:
                return m

    return unique_matches[0]


def _find_all_columns(text: str, df: pd.DataFrame, col_map: Dict[str, str]) -> List[str]:
    """Find ALL column matches in text."""
    text_lower = text.lower().strip()
    candidates = sorted(col_map.keys(), key=len, reverse=True)
    found: List[str] = []
    seen = set()
    for variant in candidates:
        actual = col_map[variant]
        if actual in seen:
            continue
        if len(variant) <= 2:
            continue
        if ' ' not in variant:
            if re.search(r'\b' + re.escape(variant) + r'\b', text_lower):
                found.append(actual)
                seen.add(actual)
        else:
            if variant in text_lower:
                found.append(actual)
                seen.add(actual)
    return found


def _fmt(val, decimals=2):
    """Format numeric values cleanly."""
    if pd.isna(val) or val is None:
        return "-"
    if isinstance(val, (int, np.integer)):
        return int(val)
    if isinstance(val, (float, np.floating)):
        if val.is_integer():
            return int(val)
        return round(float(val), decimals)
    return val


def _clean_records(records: List[Dict]) -> List[Dict]:
    cleaned = []
    for row in records:
        clean_row = {}
        for k, v in row.items():
            clean_row[k] = _fmt(v)
        cleaned.append(clean_row)
    return cleaned


def _friendly_fallback(df: pd.DataFrame) -> Dict[str, Any]:
    """Return helpful message listing supported question types with examples from actual dataset."""
    col_map = _build_column_map(df)
    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                    if c.lower().replace('_', '') not in ('employeecount', 'standardhours', 'id', 'employeenumber')]
    cat_cols = [c for c in df.select_dtypes(include=['object', 'category', 'string', 'bool']).columns
                if c.lower().replace('_', '') not in ('over18', 'id')]

    num1 = numeric_cols[0] if numeric_cols else 'Value'
    num2 = numeric_cols[1] if len(numeric_cols) > 1 else num1
    cat1 = cat_cols[0] if cat_cols else 'Category'

    has_attrition = any('attrition' in c.lower() for c in df.columns)

    if has_attrition:
        supported_types = [
            "1. HR Attrition: \"What is the overall attrition rate?\", \"How many employees left the company?\"",
            f"2. Rate Analysis: \"Attrition rate by Department\", \"Does overtime affect attrition?\"",
            f"3. Group Comparison: \"Which department has the highest attrition?\", \"Which job role has the highest attrition?\"",
            f"4. Salary & Demographics: \"What is the average salary of employees who left?\", \"What is the average age of employees who left?\"",
            f"5. Count & Aggregation: \"Count by JobRole\", \"Average {num1} by {cat1}\"",
            f"6. Top / Bottom N: \"Top 5 by {num1}\", \"Bottom 5 by Age\"",
            f"7. Multi-Condition Filter: \"Filter Age > 40 and OverTime = Yes\", \"Show employees where Department = Sales and Age > 35\"",
            f"8. Distribution & Correlation: \"Distribution of {cat1}\", \"Correlation between {num1} and {num2}\""
        ]
        examples = [
            "What is the overall attrition rate?",
            "Attrition rate by Department",
            "Which job role has the highest attrition?",
            "Does overtime affect attrition?",
            "Compare employees who left and employees who stayed",
            f"Top 5 by {num1}"
        ]
    else:
        supported_types = [
            f"1. Count: \"How many records by {cat1}\", \"Count by {cat1}\"",
            f"2. Aggregation: \"Average {num1} by {cat1}\", \"Maximum {num1}\", \"Median {num1} by {cat1}\"",
            f"3. Top / Bottom N: \"Top 5 by {num1}\", \"Bottom 5 by {num2}\"",
            f"4. Rate / Percentage: \"Percentage of records by {cat1}\"",
            f"5. Multi-Condition Filter: \"Filter {num1} > 100 and {cat1} = Value\", \"Show records where {num1} > 50\"",
            f"6. Highest / Lowest Groups: \"Which {cat1} has the highest average {num1}?\"",
            f"7. Correlation: \"Correlation between {num1} and {num2}\"",
            f"8. Distribution: \"Distribution of {cat1}\", \"Distribution of {num1}\""
        ]
        examples = [
            f"Count by {cat1}",
            f"Average {num1} by {cat1}",
            f"Top 5 by {num1}",
            f"Distribution of {cat1}",
            f"Which {cat1} has the highest average {num1}?"
        ]

    return {
        "query": "",
        "interpretation": "I couldn't understand that question. Ask DataNexus AI supports natural language queries for counts, aggregations, rankings, filters, distributions, correlations, and HR attrition analysis.",
        "columns": [],
        "data": [],
        "total_results": 0,
        "suggested_chart": None,
        "explanation": "Please try asking using one of the supported query formats or click one of the suggestion chips.",
        "supported_types": supported_types,
        "examples": examples
    }


def _find_col_by_variants(df: pd.DataFrame, variants: List[str]) -> Optional[str]:
    """Find column in df matching any variant."""
    clean_cols = {_clean_str(c): c for c in df.columns}
    for v in variants:
        v_clean = _clean_str(v)
        if v_clean in clean_cols:
            return clean_cols[v_clean]
    for v in variants:
        v_clean = _clean_str(v)
        for c_clean, orig in clean_cols.items():
            if v_clean in c_clean:
                return orig
    return None


class QueryService:

    @classmethod
    def get_suggestion_chips(cls, df: pd.DataFrame) -> List[str]:
        """Generate ~6 dynamic suggestion chips tailored to dataset columns."""
        col_map = _build_column_map(df)
        numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns]
        cat_cols = [c for c in df.select_dtypes(include=['object', 'category', 'string', 'bool']).columns]

        # Filter out constant or ID columns
        def _is_useful(col: str) -> bool:
            if df[col].nunique(dropna=True) <= 1:
                return False
            clean = col.strip().lower().replace('_', '')
            if clean in ('employeecount', 'standardhours', 'over18', 'employeenumber', 'employeeid', 'id', 'orderid'):
                return False
            if df[col].nunique(dropna=True) >= len(df) * 0.98 and len(df) > 20:
                return False
            return True

        useful_numeric = [c for c in numeric_cols if _is_useful(c)]
        useful_cat = [c for c in cat_cols if _is_useful(c)]

        # Check for HR Attrition dataset
        attrition_col = _find_col_by_variants(df, ['Attrition', 'Churn', 'Turnover'])
        if attrition_col:
            dept_col = _find_col_by_variants(df, ['Department', 'Dept']) or (useful_cat[0] if useful_cat else 'Department')
            role_col = _find_col_by_variants(df, ['JobRole', 'Job_Role', 'Role']) or (useful_cat[1] if len(useful_cat) > 1 else 'JobRole')
            income_col = _find_col_by_variants(df, ['MonthlyIncome', 'Monthly_Income_USD', 'Salary', 'Income']) or (useful_numeric[0] if useful_numeric else 'MonthlyIncome')
            overtime_col = _find_col_by_variants(df, ['OverTime', 'Overtime'])

            chips = [
                "What is the overall attrition rate?",
                f"Attrition rate by {dept_col}",
                f"Which {role_col} has the highest attrition?" if role_col else f"Which {dept_col} has the highest attrition?",
                "Does overtime affect attrition?" if overtime_col else "How many employees left the company?",
                f"Average {income_col} by {dept_col}",
                f"Top 5 by {income_col}"
            ]
            return chips[:6]

        # Check for Sales / Retail dataset
        sales_col = _find_col_by_variants(df, ['Sales', 'Revenue', 'TotalSales'])
        profit_col = _find_col_by_variants(df, ['Profit', 'NetProfit'])
        cat_col = _find_col_by_variants(df, ['Category', 'Product_Category']) or (useful_cat[0] if useful_cat else 'Category')
        region_col = _find_col_by_variants(df, ['Region', 'Territory', 'Area']) or (useful_cat[1] if len(useful_cat) > 1 else 'Region')

        if sales_col and profit_col:
            chips = [
                f"Average {sales_col} by {cat_col}",
                f"Top 5 by {profit_col}",
                f"How many records by {region_col}",
                f"Correlation between {sales_col} and {profit_col}",
                f"Which {cat_col} has the highest average {sales_col}?",
                f"Distribution of {sales_col}"
            ]
            return chips[:6]

        # Generic dynamic dataset
        chips = []
        n1 = useful_numeric[0] if useful_numeric else 'Value'
        n2 = useful_numeric[1] if len(useful_numeric) > 1 else n1
        c1 = useful_cat[0] if useful_cat else 'Category'
        c2 = useful_cat[1] if len(useful_cat) > 1 else c1

        if useful_cat:
            chips.append(f"How many records by {c1}")
        if useful_numeric and useful_cat:
            chips.append(f"Average {n1} by {c1}")
        if useful_numeric:
            chips.append(f"Top 5 by {n1}")
        if len(useful_numeric) >= 2:
            chips.append(f"Correlation between {n1} and {n2}")
        if useful_cat and useful_numeric:
            chips.append(f"Which {c1} has the highest average {n1}?")
        if useful_cat:
            chips.append(f"Distribution of {c1}")

        # Ensure 6 chips
        while len(chips) < 6 and useful_numeric:
            chips.append(f"Distribution of {n2}")
            break

        return chips[:6]

    @classmethod
    def execute_query(cls, df: pd.DataFrame, query_str: str) -> Dict[str, Any]:
        """Hybrid question-answering system combining:
        1. New NLP-based Question Understanding System (Primary)
        2. Existing Deterministic Rule-Based System (Fallback)
        """
        raw_q = query_str.strip()
        if not raw_q:
            return {"error": "Query string cannot be empty."}

        # -------------------------------------------------------------
        # 1. PRIMARY: NLP-Based Query Understanding Engine
        # -------------------------------------------------------------
        try:
            from backend.services.nlp_query_service import NLPQueryEngine
            nlp_engine = NLPQueryEngine(df)
            nlp_res = nlp_engine.process_query(raw_q)
            if nlp_res is not None:
                # Successfully understood and calculated by NLP engine.
                # If zero matching rows are found, return it directly without falling back.
                nlp_res["engine"] = "nlp"
                return nlp_res
        except Exception:
            # Graceful failover: if any unexpected error occurs in NLP parsing,
            # fall back safely to the deterministic rule-based engine.
            pass

        # -------------------------------------------------------------
        # 2. FALLBACK: Existing Rule-Based System
        # -------------------------------------------------------------
        rule_res = cls._execute_rule_based(df, raw_q)
        if rule_res is not None:
            if rule_res.get("engine") is None and "couldn't understand" not in rule_res.get("interpretation", "").lower():
                rule_res["engine"] = "rule_based"
                if "answer" not in rule_res:
                    rule_res["answer"] = rule_res.get("explanation", "")
            return rule_res

        return _friendly_fallback(df)

    @classmethod
    def _execute_rule_based(cls, df: pd.DataFrame, query_str: str) -> Dict[str, Any]:
        """Parse natural language query and execute deterministic rule-based analysis."""
        raw_q = query_str.strip()
        if not raw_q:
            return {"error": "Query string cannot be empty."}

        # Clean query text
        q = raw_q.lower()
        q = q.rstrip('?!.')
        q = _normalize_number_words(q)

        col_map = _build_column_map(df)
        numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns]
        cat_cols = [c for c in df.select_dtypes(include=['object', 'category', 'string', 'bool']).columns]

        # =====================================================================
        # PART 3: HR EMPLOYEE ATTRITION QUESTIONS (15 SPECIFIC QUESTIONS)
        # =====================================================================
        hr_result = cls._handle_hr_attrition_queries(df, q, query_str)
        if hr_result is not None:
            return hr_result

        # =====================================================================
        # PART 2: GENERAL QUESTION PARSER (8 CATEGORIES)
        # =====================================================================

        # ---------------------------------------------------------------------
        # 7. Correlation: "Correlation between Age and MonthlyIncome", "Sales and Profit"
        # ---------------------------------------------------------------------
        corr_match = re.search(r'\b(?:correlation|corr|relationship)\b.*?\bbetween\b\s+(.+)', q)
        if not corr_match:
            corr_match = re.search(r'\b(?:correlation|corr)\s+(?:of|between)?\s*(.+)', q)
        if corr_match:
            remainder = corr_match.group(1).strip()
            # Split by "and" or ","
            parts = re.split(r'\s+and\s+|,\s*', remainder)
            if len(parts) >= 2:
                c1 = _resolve_column(parts[0], df, col_map, prefer='numeric')
                c2 = _resolve_column(parts[1], df, col_map, prefer='numeric')
            else:
                found_cols = _find_all_columns(remainder, df, col_map)
                num_found = [c for c in found_cols if c in numeric_cols]
                c1 = num_found[0] if len(num_found) > 0 else None
                c2 = num_found[1] if len(num_found) > 1 else None

            if c1 and c2 and c1 != c2:
                clean = df[[c1, c2]].dropna()
                if len(clean) > 2:
                    corr_val = float(clean[c1].corr(clean[c2]))
                    strength = "strong" if abs(corr_val) >= 0.7 else ("moderate" if abs(corr_val) >= 0.35 else "weak")
                    direction = "positive" if corr_val > 0 else "negative"

                    data = [{
                        "Variable 1": c1,
                        "Variable 2": c2,
                        "Correlation (r)": round(corr_val, 4),
                        "Strength": f"{strength.capitalize()} {direction.capitalize()}",
                        "Sample Size": len(clean)
                    }]
                    explanation = f"The Pearson correlation between {c1} and {c2} is {round(corr_val, 4)}, indicating a {strength} {direction} relationship across {len(clean):,} records."

                    return {
                        "query": query_str,
                        "interpretation": f"Correlation analysis between '{c1}' and '{c2}'.",
                        "columns": list(data[0].keys()),
                        "data": data,
                        "total_results": 1,
                        "suggested_chart": "scatter",
                        "explanation": explanation
                    }

        # ---------------------------------------------------------------------
        # 8. Distribution: "Distribution of JobSatisfaction", "Distribution of Department"
        # ---------------------------------------------------------------------
        dist_match = re.search(r'\b(?:distribution|breakdown|spread)\s+(?:of\s+)?(.+)', q)
        if dist_match:
            remainder = dist_match.group(1).strip()
            target_col = _resolve_column(remainder, df, col_map)
            if target_col:
                is_num = pd.api.types.is_numeric_dtype(df[target_col])
                n_unique = df[target_col].nunique(dropna=True)

                if is_num and n_unique > 12:
                    # Numeric histogram bins
                    series = pd.to_numeric(df[target_col], errors='coerce').dropna()
                    counts, bin_edges = np.histogram(series, bins=10)
                    data = []
                    for i in range(len(counts)):
                        data.append({
                            "Bin Range": f"{round(float(bin_edges[i]), 1)} - {round(float(bin_edges[i+1]), 1)}",
                            "Frequency": int(counts[i]),
                            "Percentage (%)": round(int(counts[i]) / len(series) * 100, 1)
                        })
                    top_bin = data[int(np.argmax(counts))]
                    explanation = f"The distribution of {target_col} spans from {_fmt(series.min())} to {_fmt(series.max())}, with the highest frequency in the range '{top_bin['Bin Range']}' ({top_bin['Frequency']} records, {top_bin['Percentage (%)']}%)."
                else:
                    # Categorical / discrete frequency table
                    val_counts = df[target_col].value_counts(dropna=False)
                    total_count = len(df)
                    data = []
                    for k, v in val_counts.head(20).items():
                        label = "Missing" if pd.isna(k) else str(k)
                        data.append({
                            str(target_col): label,
                            "Count": int(v),
                            "Percentage (%)": round(int(v) / total_count * 100, 1)
                        })
                    top_row = data[0]
                    explanation = f"The distribution of {target_col} has {n_unique} unique values, led by '{top_row[str(target_col)]}' with {top_row['Count']} records ({top_row['Percentage (%)']}% of total)."

                return {
                    "query": query_str,
                    "interpretation": f"Distribution analysis of '{target_col}'.",
                    "columns": list(data[0].keys()) if data else [],
                    "data": data,
                    "total_results": len(data),
                    "suggested_chart": "bar",
                    "explanation": explanation
                }

        # ---------------------------------------------------------------------
        # 6. Highest / Lowest Groups:
        # "Which Department has the highest average MonthlyIncome?"
        # "Which JobRole has the most Attrition?"
        # "Which Category has the highest average Sales?"
        # ---------------------------------------------------------------------
        which_match = re.search(
            r'\b(?:which|what)\b\s+(.+?)\s+(?:has|have|with|shows?)\s+(?:the\s+)?(highest|lowest|most|least|maximum|minimum|top|bottom|greatest|smallest)\s+(.+)',
            q
        )
        if which_match:
            group_text = which_match.group(1).strip()
            direction = which_match.group(2).strip()
            metric_text = which_match.group(3).strip()
            is_asc = direction in ('lowest', 'least', 'minimum', 'bottom', 'smallest')

            group_col = _resolve_column(group_text, df, col_map, prefer='categorical')
            
            # Check for aggregate in metric_text (e.g. "average MonthlyIncome", "total Sales")
            agg_sub = re.search(r'(average|avg|mean|total|sum|median|max|maximum|min|minimum|count)\s+(?:of\s+)?(.+)', metric_text)
            if agg_sub:
                agg_w = agg_sub.group(1)
                agg_type = 'mean' if agg_w in ('average', 'avg', 'mean') else ('sum' if agg_w in ('total', 'sum') else ('median' if agg_w == 'median' else ('min' if agg_w in ('min', 'minimum') else ('max' if agg_w in ('max', 'maximum') else 'count'))))
                metric_col = _resolve_column(agg_sub.group(2), df, col_map, prefer='numeric')
            else:
                metric_col = _resolve_column(metric_text, df, col_map)
                agg_type = None

            if group_col and metric_col:
                if metric_col in numeric_cols:
                    agg_type = agg_type or 'mean'
                    grouped = df.groupby(group_col)[metric_col].agg(agg_type).reset_index()
                    val_label = f"{agg_type.capitalize()} {metric_col}"
                    grouped.columns = [group_col, val_label]
                    grouped[val_label] = grouped[val_label].round(2)
                    grouped = grouped.sort_values(by=val_label, ascending=is_asc)
                    top_row = grouped.iloc[0]
                    data = _clean_records(grouped.to_dict(orient='records'))
                    explanation = f"The {group_col} with the {direction} {agg_type} {metric_col} is '{top_row[group_col]}' with a value of {_fmt(top_row[val_label])}."

                    return {
                        "query": query_str,
                        "interpretation": f"Finding the {group_col} with the {direction} {agg_type} {metric_col}.",
                        "columns": list(grouped.columns),
                        "data": data,
                        "total_results": len(data),
                        "suggested_chart": "bar",
                        "explanation": explanation
                    }
                else:
                    # Categorical metric (e.g. "most Attrition", "most churn")
                    vals_lower = set(df[metric_col].dropna().astype(str).str.lower().unique())
                    if vals_lower <= {'yes', 'no', '1', '0', 'true', 'false'}:
                        positive_vals = {'yes', '1', 'true'}
                        grp_data = []
                        for val, g in df.groupby(group_col):
                            total = len(g)
                            pos_count = g[metric_col].astype(str).str.lower().isin(positive_vals).sum()
                            rate = round(pos_count / total * 100, 2) if total > 0 else 0.0
                            grp_data.append({
                                group_col: str(val),
                                "Total Count": total,
                                f"{metric_col} Count": int(pos_count),
                                f"{metric_col} Rate (%)": rate
                            })
                        res_df = pd.DataFrame(grp_data)
                        sort_col = f"{metric_col} Rate (%)" if "rate" in metric_text else f"{metric_col} Count"
                        res_df = res_df.sort_values(by=sort_col, ascending=is_asc)
                        top_row = res_df.iloc[0]
                        data = _clean_records(res_df.to_dict(orient='records'))
                        explanation = f"The {group_col} with the {direction} {metric_col} is '{top_row[group_col]}' with {top_row[f'{metric_col} Count']} cases ({top_row[f'{metric_col} Rate (%)']}% rate, based on {sort_col})."

                        return {
                            "query": query_str,
                            "interpretation": f"Analysis of {group_col} with the {direction} {metric_col}.",
                            "columns": list(res_df.columns),
                            "data": data,
                            "total_results": len(data),
                            "suggested_chart": "bar",
                            "explanation": explanation
                        }
                    else:
                        counted = df.groupby(group_col)[metric_col].count().reset_index()
                        counted.columns = [group_col, f"Count of {metric_col}"]
                        counted = counted.sort_values(by=f"Count of {metric_col}", ascending=is_asc)
                        top_row = counted.iloc[0]
                        data = _clean_records(counted.to_dict(orient='records'))
                        explanation = f"The {group_col} with the {direction} count of {metric_col} is '{top_row[group_col]}' with {top_row[f'Count of {metric_col}']} occurrences."

                        return {
                            "query": query_str,
                            "interpretation": f"Comparison of {group_col} by {metric_col} count.",
                            "columns": list(counted.columns),
                            "data": data,
                            "total_results": len(data),
                            "suggested_chart": "bar",
                            "explanation": explanation
                        }

        # ---------------------------------------------------------------------
        # 4. Rate and Percentage:
        # "Attrition rate by Department", "Percentage of Attrition by OverTime"
        # "Percentage of employees by Department"
        # ---------------------------------------------------------------------
        rate_match = re.search(
            r'(?:rate|percentage|pct|proportion)\s+(?:of\s+)?(.+?)\s+(?:by|per|for|across|in)\s+(.+)',
            q
        )
        if not rate_match:
            rate_match = re.search(
                r'(.+?)\s+(?:rate|percentage|pct|proportion)\s+(?:by|per|for|across|in)\s+(.+)',
                q
            )
        if rate_match:
            target_text = rate_match.group(1).strip()
            group_text = rate_match.group(2).strip()

            target_col = _resolve_column(target_text, df, col_map)
            group_col = _resolve_column(group_text, df, col_map, prefer='categorical')

            # Special case: "Percentage of employees by Department" -> proportion of rows by department
            if target_text in ('employees', 'records', 'rows', 'people', 'all') and group_col:
                counted = df.groupby(group_col).size().reset_index(name='Count')
                total_rows = len(df)
                counted['Percentage (%)'] = (counted['Count'] / total_rows * 100).round(2)
                counted = counted.sort_values(by='Count', ascending=False)
                data = _clean_records(counted.to_dict(orient='records'))
                top_row = counted.iloc[0]
                explanation = f"The largest group is '{top_row[group_col]}' representing {top_row['Count']} records ({top_row['Percentage (%)']}% of all records)."

                return {
                    "query": query_str,
                    "interpretation": f"Percentage of records grouped by '{group_col}'.",
                    "columns": list(counted.columns),
                    "data": data,
                    "total_results": len(data),
                    "suggested_chart": "pie",
                    "explanation": explanation
                }

            if target_col and group_col and target_col != group_col:
                vals_lower = set(df[target_col].dropna().astype(str).str.lower().unique())
                if vals_lower <= {'yes', 'no', '1', '0', 'true', 'false'}:
                    positive_vals = {'yes', '1', 'true'}
                    grp_data = []
                    for val, g in df.groupby(group_col):
                        total = len(g)
                        pos_count = g[target_col].astype(str).str.lower().isin(positive_vals).sum()
                        rate = round(pos_count / total * 100, 2) if total > 0 else 0.0
                        grp_data.append({
                            group_col: str(val),
                            "Total Count": total,
                            f"{target_col} (Yes)": int(pos_count),
                            f"{target_col} Rate (%)": rate
                        })
                    res_df = pd.DataFrame(grp_data).sort_values(by=f"{target_col} Rate (%)", ascending=False)
                    data = _clean_records(res_df.to_dict(orient='records'))
                    top = res_df.iloc[0]
                    lowest = res_df.iloc[-1]
                    explanation = f"The highest {target_col} rate is in '{top[group_col]}' at {top[f'{target_col} Rate (%)']}%, while the lowest is in '{lowest[group_col]}' at {lowest[f'{target_col} Rate (%)']}%."

                    return {
                        "query": query_str,
                        "interpretation": f"Rate of '{target_col}' grouped by '{group_col}'.",
                        "columns": list(res_df.columns),
                        "data": data,
                        "total_results": len(data),
                        "suggested_chart": "bar",
                        "explanation": explanation
                    }
                else:
                    # Breakdown of categorical target within group
                    grp_data = []
                    for val, g in df.groupby(group_col):
                        counts = g[target_col].value_counts()
                        total = len(g)
                        for cat_val, cnt in counts.items():
                            grp_data.append({
                                group_col: str(val),
                                target_col: str(cat_val),
                                "Count": int(cnt),
                                "Percentage (%)": round(cnt / total * 100, 2) if total > 0 else 0.0
                            })
                    res_df = pd.DataFrame(grp_data).sort_values(by="Percentage (%)", ascending=False)
                    data = _clean_records(res_df.head(25).to_dict(orient='records'))
                    explanation = f"Calculated distribution of {target_col} across {group_col} segments."

                    return {
                        "query": query_str,
                        "interpretation": f"Percentage breakdown of '{target_col}' by '{group_col}'.",
                        "columns": list(res_df.columns),
                        "data": data,
                        "total_results": len(data),
                        "suggested_chart": "bar",
                        "explanation": explanation
                    }

        # ---------------------------------------------------------------------
        # 5. Multiple-condition Filters:
        # "Filter Age > 40 and OverTime = Yes"
        # "Show employees where Department = Sales and Age > 35"
        # "Show records where Profit > 100 and Region = East"
        # ---------------------------------------------------------------------
        filter_pattern = re.search(
            r'(?:filter|show|find|get|list|display)\s+(?:employees|records|rows|people|items|data)?\s*(?:where|with|for)?\s+(.+)',
            q
        )
        if filter_pattern and any(op in q for op in ('>', '<', '=', '>=', '<=', '!=', 'contains')):
            conditions_text = filter_pattern.group(1).strip()
            # Split conditions by "and" or "&"
            cond_parts = re.split(r'\s+and\s+|\s*&\s*', conditions_text)
            filtered_df = df.copy()
            applied = []

            for part in cond_parts:
                part = part.strip()
                match_op = re.search(r'(.+?)\s*(>=|<=|!=|>|<|==|=|is|contains)\s*(.+)', part)
                if match_op:
                    c_text = match_op.group(1).strip()
                    op = match_op.group(2).strip()
                    v_text = match_op.group(3).strip().strip("'\"")

                    col_name = _resolve_column(c_text, df, col_map)
                    if col_name:
                        op_norm = '==' if op in ('=', 'is') else op
                        if pd.api.types.is_numeric_dtype(filtered_df[col_name]):
                            try:
                                num_val = float(v_text)
                                if op_norm == '>':
                                    filtered_df = filtered_df[filtered_df[col_name] > num_val]
                                elif op_norm == '<':
                                    filtered_df = filtered_df[filtered_df[col_name] < num_val]
                                elif op_norm == '>=':
                                    filtered_df = filtered_df[filtered_df[col_name] >= num_val]
                                elif op_norm == '<=':
                                    filtered_df = filtered_df[filtered_df[col_name] <= num_val]
                                elif op_norm == '==':
                                    filtered_df = filtered_df[filtered_df[col_name] == num_val]
                                elif op_norm == '!=':
                                    filtered_df = filtered_df[filtered_df[col_name] != num_val]
                                applied.append(f"{col_name} {op_norm} {num_val}")
                            except ValueError:
                                pass
                        else:
                            if op_norm == '==':
                                filtered_df = filtered_df[filtered_df[col_name].astype(str).str.lower() == v_text.lower()]
                            elif op_norm == '!=':
                                filtered_df = filtered_df[filtered_df[col_name].astype(str).str.lower() != v_text.lower()]
                            elif op_norm == 'contains':
                                filtered_df = filtered_df[filtered_df[col_name].astype(str).str.lower().str.contains(v_text.lower(), regex=False)]
                            applied.append(f"{col_name} {op_norm} '{v_text}'")

            if applied:
                # Keep preview clean: priority columns
                preview_cols = [c for c in filtered_df.columns if _clean_str(c) not in ('employeecount', 'standardhours', 'over18')]
                if len(preview_cols) > 8:
                    priority = [a.split()[0] for a in applied if a.split()[0] in preview_cols]
                    for c in preview_cols:
                        if c not in priority:
                            priority.append(c)
                        if len(priority) >= 8:
                            break
                    preview_cols = priority

                preview_df = filtered_df[preview_cols].head(25)
                data = _clean_records(preview_df.to_dict(orient='records'))
                cond_summary = " and ".join(applied)
                explanation = f"Found {len(filtered_df):,} records matching condition: {cond_summary}."

                return {
                    "query": query_str,
                    "interpretation": f"Filtered records where {cond_summary}.",
                    "columns": preview_cols,
                    "data": data,
                    "total_results": len(filtered_df),
                    "suggested_chart": None,
                    "explanation": explanation
                }

        # ---------------------------------------------------------------------
        # 3. Top N and Bottom N:
        # "Top 5 by MonthlyIncome", "Bottom 5 by Age", "Top 5 by Profit", "Bottom 5 by Sales"
        # ---------------------------------------------------------------------
        top_match = re.search(r'\b(top|bottom|highest|lowest)\s+(\d+)\s*(?:by\s+)?(.+)?', q)
        if top_match:
            direction = top_match.group(1).lower()
            limit_n = int(top_match.group(2))
            remainder = top_match.group(3).strip() if top_match.group(3) else ""
            is_asc = direction in ('bottom', 'lowest')

            target_metric = _resolve_column(remainder, df, col_map, prefer='numeric')
            if not target_metric and numeric_cols:
                target_metric = numeric_cols[0]

            if target_metric and target_metric in df.columns:
                ranked = df.sort_values(by=target_metric, ascending=is_asc).head(limit_n)
                # Select readable columns
                show_cols = [target_metric]
                for c in cat_cols:
                    if c not in show_cols and _clean_str(c) not in ('over18', 'id'):
                        show_cols.append(c)
                    if len(show_cols) >= 4:
                        break
                for c in numeric_cols:
                    if c not in show_cols and _clean_str(c) not in ('employeecount', 'standardhours', 'employeenumber', 'id'):
                        show_cols.append(c)
                    if len(show_cols) >= 8:
                        break

                preview = ranked[show_cols]
                data = _clean_records(preview.to_dict(orient='records'))
                rank_label = "lowest" if is_asc else "highest"
                best_val = _fmt(ranked[target_metric].iloc[0])
                explanation = f"Showing the {len(data)} records with the {rank_label} {target_metric}, starting with {best_val}."

                return {
                    "query": query_str,
                    "interpretation": f"{direction.capitalize()} {limit_n} records ranked by '{target_metric}'.",
                    "columns": show_cols,
                    "data": data,
                    "total_results": len(data),
                    "suggested_chart": "bar",
                    "explanation": explanation
                }

        # ---------------------------------------------------------------------
        # 1. Count:
        # "How many employees by Department?", "Count by JobRole",
        # "Count by Category", "Count by Region"
        # ---------------------------------------------------------------------
        count_match = re.search(
            r'(?:how\s+many|count|number\s+of)\s*(?:employees|records|rows|people|items|customers|orders)?\s*(?:by|per|for|across|in)\s+(.+)',
            q
        )
        if not count_match and q.startswith("count by"):
            count_match = re.search(r'count\s+by\s+(.+)', q)

        if count_match:
            group_text = count_match.group(1).strip()
            group_col = _resolve_column(group_text, df, col_map, prefer='categorical')
            if group_col:
                counted = df.groupby(group_col).size().reset_index(name='Count')
                total_n = len(df)
                counted['Percentage (%)'] = (counted['Count'] / total_n * 100).round(2)
                counted = counted.sort_values(by='Count', ascending=False)
                data = _clean_records(counted.to_dict(orient='records'))
                top_row = counted.iloc[0]
                explanation = f"There are {len(counted)} distinct {group_col} groups. '{top_row[group_col]}' is the largest with {top_row['Count']} records ({top_row['Percentage (%)']}%)."

                return {
                    "query": query_str,
                    "interpretation": f"Count of records grouped by '{group_col}'.",
                    "columns": list(counted.columns),
                    "data": data,
                    "total_results": len(data),
                    "suggested_chart": "bar",
                    "explanation": explanation
                }

        # ---------------------------------------------------------------------
        # 2. Average, Sum, Minimum, Maximum, and Median:
        # "Average MonthlyIncome by Department", "Maximum Age",
        # "Median YearsAtCompany by JobRole", "Sum of MonthlyIncome by Department",
        # "Average Sales by Category"
        # ---------------------------------------------------------------------
        agg_match = re.search(
            r'(average|avg|mean|sum|total|median|max|maximum|min|minimum)\s+(?:of\s+)?(.+?)(?:\s+(?:by|per|for|across|in|grouped\s+by)\s+(.+))?$',
            q
        )
        if agg_match:
            agg_word = agg_match.group(1).strip()
            metric_text = agg_match.group(2).strip() if agg_match.group(2) else ""
            group_text = agg_match.group(3).strip() if agg_match.group(3) else None

            agg_map = {
                'average': 'mean', 'avg': 'mean', 'mean': 'mean',
                'sum': 'sum', 'total': 'sum',
                'median': 'median',
                'max': 'max', 'maximum': 'max',
                'min': 'min', 'minimum': 'min'
            }
            agg_type = agg_map.get(agg_word, 'mean')

            target_metric = _resolve_column(metric_text, df, col_map, prefer='numeric')
            group_col = _resolve_column(group_text, df, col_map, prefer='categorical') if group_text else None

            if target_metric and target_metric in numeric_cols:
                if group_col:
                    grouped = df.groupby(group_col)[target_metric].agg(agg_type).reset_index()
                    val_col = f"{agg_type.capitalize()} {target_metric}"
                    grouped.columns = [group_col, val_col]
                    grouped[val_col] = grouped[val_col].round(2)
                    grouped = grouped.sort_values(by=val_col, ascending=False)
                    data = _clean_records(grouped.to_dict(orient='records'))
                    top = grouped.iloc[0]
                    lowest = grouped.iloc[-1]
                    explanation = f"The {agg_type} of {target_metric} by {group_col}: highest is '{top[group_col]}' ({_fmt(top[val_col])}), lowest is '{lowest[group_col]}' ({_fmt(lowest[val_col])})."

                    return {
                        "query": query_str,
                        "interpretation": f"Calculated {agg_type.upper()} of '{target_metric}' grouped by '{group_col}'.",
                        "columns": list(grouped.columns),
                        "data": data,
                        "total_results": len(data),
                        "suggested_chart": "bar",
                        "explanation": explanation
                    }
                else:
                    # Single overall statistic
                    series = pd.to_numeric(df[target_metric], errors='coerce').dropna()
                    val = getattr(series, agg_type)()
                    data = [{
                        "Metric": f"{agg_type.capitalize()} {target_metric}",
                        "Value": _fmt(val),
                        "Total Valid Records": len(series)
                    }]
                    explanation = f"The overall {agg_type} of {target_metric} across all {len(series):,} records is {_fmt(val)}."

                    return {
                        "query": query_str,
                        "interpretation": f"Calculated overall {agg_type.upper()} of '{target_metric}'.",
                        "columns": ["Metric", "Value", "Total Valid Records"],
                        "data": data,
                        "total_results": 1,
                        "suggested_chart": None,
                        "explanation": explanation
                    }

        # Fallback friendly response
        return _friendly_fallback(df)

    @classmethod
    def _handle_hr_attrition_queries(cls, df: pd.DataFrame, q: str, query_str: str) -> Optional[Dict[str, Any]]:
        """Handles 15 specific HR attrition questions with deterministic calculation."""
        attrition_col = _find_col_by_variants(df, ['Attrition', 'Churn', 'Turnover'])
        
        # Check if query is asking about attrition or employee turnover
        is_attrition_query = any(k in q for k in (
            'attrition', 'left', 'stayed', 'stay', 'turnover', 'churn', 'leave', 'leaving'
        ))

        if not is_attrition_query:
            return None

        # If user asks an attrition question but dataset has no attrition column:
        if not attrition_col:
            return {
                "query": query_str,
                "interpretation": "HR Attrition Analysis requested, but no 'Attrition' column exists in this dataset.",
                "columns": ["Status", "Required Column"],
                "data": [{"Status": "Unavailable", "Required Column": "Attrition (Yes/No)"}],
                "total_results": 0,
                "suggested_chart": None,
                "explanation": "This question requires an 'Attrition' column, which is not present in the currently loaded dataset. Please upload or load an HR analytics dataset to run attrition analysis."
            }

        # Standardize Attrition to boolean Left series
        left_mask = df[attrition_col].astype(str).str.strip().str.lower().isin(['yes', '1', 'true'])
        total_employees = len(df)
        left_count = int(left_mask.sum())
        stayed_count = total_employees - left_count
        overall_rate = round(left_count / total_employees * 100, 2) if total_employees > 0 else 0.0

        # Helper column finders
        dept_col = _find_col_by_variants(df, ['Department', 'Dept'])
        role_col = _find_col_by_variants(df, ['JobRole', 'Job_Role', 'Role'])
        overtime_col = _find_col_by_variants(df, ['OverTime', 'Overtime'])
        income_col = _find_col_by_variants(df, ['MonthlyIncome', 'Monthly_Income_USD', 'Salary', 'Income'])
        age_col = _find_col_by_variants(df, ['Age'])
        gender_col = _find_col_by_variants(df, ['Gender', 'Sex'])
        satisfaction_col = _find_col_by_variants(df, ['JobSatisfaction', 'Job_Satisfaction_1to4', 'EnvironmentSatisfaction'])
        travel_col = _find_col_by_variants(df, ['BusinessTravel', 'Travel'])

        # -----------------------------------------------------------------
        # Q1: What is the overall attrition rate?
        # -----------------------------------------------------------------
        if re.search(r'\b(?:overall|total|company)\s+attrition\s+rate\b', q) or (
            'attrition rate' in q and not any(k in q for k in ('by', 'department', 'role', 'gender', 'overtime', 'travel', 'age'))
        ):
            data = [{
                "Metric": "Overall Attrition Rate",
                "Total Employees": total_employees,
                "Employees Left": left_count,
                "Employees Stayed": stayed_count,
                "Attrition Rate (%)": overall_rate
            }]
            explanation = f"The overall employee attrition rate is {overall_rate}%, with {left_count:,} out of {total_employees:,} employees having left the company."
            return {
                "query": query_str,
                "interpretation": "Overall company-wide employee attrition rate.",
                "columns": list(data[0].keys()),
                "data": data,
                "total_results": 1,
                "suggested_chart": "pie",
                "explanation": explanation
            }

        # -----------------------------------------------------------------
        # Q2: How many employees left the company?
        # -----------------------------------------------------------------
        if re.search(r'\bhow\s+many\b.*?\b(?:left|leave|resigned)\b', q) and not any(k in q for k in ('by', 'department', 'role', 'from each', 'satisfaction', 'salary', 'income', 'age', 'gender', 'travel')):
            data = [{
                "Status": "Employees Left (Attrition = Yes)",
                "Count": left_count,
                "Total Workforce": total_employees,
                "Share of Workforce (%)": overall_rate
            }]
            explanation = f"A total of {left_count:,} employees left the company, representing {overall_rate}% of the total workforce of {total_employees:,} employees."
            return {
                "query": query_str,
                "interpretation": "Total count of employees who left the company.",
                "columns": list(data[0].keys()),
                "data": data,
                "total_results": 1,
                "suggested_chart": None,
                "explanation": explanation
            }

        # -----------------------------------------------------------------
        # Q3: How many employees stayed?
        # -----------------------------------------------------------------
        if re.search(r'\bhow\s+many\b.*?\b(?:stayed|stay|retained|remained)\b', q):
            stay_pct = round(stayed_count / total_employees * 100, 2)
            data = [{
                "Status": "Employees Stayed (Attrition = No)",
                "Count": stayed_count,
                "Total Workforce": total_employees,
                "Retention Rate (%)": stay_pct
            }]
            explanation = f"A total of {stayed_count:,} employees remained with the company, representing a {stay_pct}% retention rate."
            return {
                "query": query_str,
                "interpretation": "Total count of employees who stayed with the company.",
                "columns": list(data[0].keys()),
                "data": data,
                "total_results": 1,
                "suggested_chart": None,
                "explanation": explanation
            }

        # -----------------------------------------------------------------
        # Q15: Compare employees who left and employees who stayed.
        # -----------------------------------------------------------------
        if re.search(r'\bcompare\b.*?\b(?:left|stayed|stay)\b', q) or 'left vs stayed' in q or 'attrition comparison' in q:
            left_df = df[left_mask]
            stayed_df = df[~left_mask]

            metrics_list = []
            # Count
            metrics_list.append({
                "Dimension": "Headcount",
                "Employees Left": f"{left_count:,} ({overall_rate}%)",
                "Employees Stayed": f"{stayed_count:,} ({round(100 - overall_rate, 2)}%)",
                "Variance / Difference": f"{left_count - stayed_count:,}"
            })

            # Age
            if age_col:
                avg_age_left = round(float(left_df[age_col].mean()), 1)
                avg_age_stay = round(float(stayed_df[age_col].mean()), 1)
                metrics_list.append({
                    "Dimension": f"Average {age_col} (Years)",
                    "Employees Left": str(avg_age_left),
                    "Employees Stayed": str(avg_age_stay),
                    "Variance / Difference": f"{round(avg_age_left - avg_age_stay, 1)} yrs"
                })

            # Income / Salary
            if income_col:
                avg_sal_left = round(float(left_df[income_col].mean()), 2)
                avg_sal_stay = round(float(stayed_df[income_col].mean()), 2)
                diff = round(avg_sal_left - avg_sal_stay, 2)
                metrics_list.append({
                    "Dimension": f"Average {income_col} ($)",
                    "Employees Left": f"${avg_sal_left:,.2f}",
                    "Employees Stayed": f"${avg_sal_stay:,.2f}",
                    "Variance / Difference": f"${diff:,.2f}"
                })

            # Job Satisfaction
            if satisfaction_col:
                avg_js_left = round(float(left_df[satisfaction_col].mean()), 2)
                avg_js_stay = round(float(stayed_df[satisfaction_col].mean()), 2)
                metrics_list.append({
                    "Dimension": f"Average {satisfaction_col} (1-4)",
                    "Employees Left": str(avg_js_left),
                    "Employees Stayed": str(avg_js_stay),
                    "Variance / Difference": f"{round(avg_js_left - avg_js_stay, 2)}"
                })

            # Overtime %
            if overtime_col:
                ot_left = round(left_df[overtime_col].astype(str).str.lower().eq('yes').mean() * 100, 1)
                ot_stay = round(stayed_df[overtime_col].astype(str).str.lower().eq('yes').mean() * 100, 1)
                metrics_list.append({
                    "Dimension": "Overtime Rate (%)",
                    "Employees Left": f"{ot_left}%",
                    "Employees Stayed": f"{ot_stay}%",
                    "Variance / Difference": f"+{round(ot_left - ot_stay, 1)}%"
                })

            explanation = (
                f"Comparison reveals employees who left were on average "
                f"{'younger (' + str(avg_age_left) + ' vs ' + str(avg_age_stay) + ' yrs), ' if age_col else ''}"
                f"{'earned lower salaries ($' + f'{avg_sal_left:,.0f}' + ' vs $' + f'{avg_sal_stay:,.0f}' + '), ' if income_col else ''}"
                f"and had significantly higher overtime participation."
            )

            return {
                "query": query_str,
                "interpretation": "Comparative profile of employees who left vs employees who stayed.",
                "columns": ["Dimension", "Employees Left", "Employees Stayed", "Variance / Difference"],
                "data": metrics_list,
                "total_results": len(metrics_list),
                "suggested_chart": None,
                "explanation": explanation
            }

        # -----------------------------------------------------------------
        # Q4: Which department has the highest attrition?
        # -----------------------------------------------------------------
        if dept_col and re.search(r'\bwhich\s+department\b.*?\b(?:highest|most)\s+attrition\b', q):
            grp_data = []
            for d, g in df.groupby(dept_col):
                tot = len(g)
                l_cnt = int(g[attrition_col].astype(str).str.lower().eq('yes').sum())
                s_cnt = tot - l_cnt
                rate = round(l_cnt / tot * 100, 2) if tot > 0 else 0.0
                grp_data.append({
                    "Department": str(d),
                    "Total Employees": tot,
                    "Employees Left": l_cnt,
                    "Employees Stayed": s_cnt,
                    "Attrition Rate (%)": rate
                })
            res_df = pd.DataFrame(grp_data)
            by_rate = res_df.sort_values(by="Attrition Rate (%)", ascending=False).iloc[0]
            by_count = res_df.sort_values(by="Employees Left", ascending=False).iloc[0]

            explanation = (
                f"By highest rate, '{by_rate['Department']}' leads with an attrition rate of {by_rate['Attrition Rate (%)']}% "
                f"({by_rate['Employees Left']} of {by_rate['Total Employees']}). "
                f"By highest absolute count, '{by_count['Department']}' had the most departures ({by_count['Employees Left']} employees, {by_count['Attrition Rate (%)']}% rate)."
            )

            return {
                "query": query_str,
                "interpretation": f"Department with highest attrition (ranked by rate and count).",
                "columns": list(res_df.columns),
                "data": _clean_records(res_df.sort_values(by="Attrition Rate (%)", ascending=False).to_dict(orient='records')),
                "total_results": len(res_df),
                "suggested_chart": "bar",
                "explanation": explanation
            }

        # -----------------------------------------------------------------
        # Q5: Which job role has the highest attrition?
        # -----------------------------------------------------------------
        if role_col and re.search(r'\bwhich\s+(?:job\s*role|role)\b.*?\b(?:highest|most)\s+attrition\b', q):
            grp_data = []
            for r, g in df.groupby(role_col):
                tot = len(g)
                l_cnt = int(g[attrition_col].astype(str).str.lower().eq('yes').sum())
                s_cnt = tot - l_cnt
                rate = round(l_cnt / tot * 100, 2) if tot > 0 else 0.0
                grp_data.append({
                    "Job Role": str(r),
                    "Total Employees": tot,
                    "Employees Left": l_cnt,
                    "Employees Stayed": s_cnt,
                    "Attrition Rate (%)": rate
                })
            res_df = pd.DataFrame(grp_data)
            by_rate = res_df.sort_values(by="Attrition Rate (%)", ascending=False).iloc[0]
            by_count = res_df.sort_values(by="Employees Left", ascending=False).iloc[0]

            explanation = (
                f"By highest rate, '{by_rate['Job Role']}' leads with an attrition rate of {by_rate['Attrition Rate (%)']}% "
                f"({by_rate['Employees Left']} of {by_rate['Total Employees']}). "
                f"By highest volume, '{by_count['Job Role']}' had the most departures ({by_count['Employees Left']} employees, {by_count['Attrition Rate (%)']}% rate)."
            )

            return {
                "query": query_str,
                "interpretation": "Job role with the highest attrition (evaluating rate and count).",
                "columns": list(res_df.columns),
                "data": _clean_records(res_df.sort_values(by="Attrition Rate (%)", ascending=False).to_dict(orient='records')),
                "total_results": len(res_df),
                "suggested_chart": "bar",
                "explanation": explanation
            }

        # -----------------------------------------------------------------
        # Q6: What is the attrition rate by department?
        # -----------------------------------------------------------------
        if dept_col and (
            re.search(r'\battrition\s+rate\s+by\s+department\b', q) or
            re.search(r'\bdepartment\b.*?\battrition\s+rate\b', q)
        ):
            grp_data = []
            for d, g in df.groupby(dept_col):
                tot = len(g)
                l_cnt = int(g[attrition_col].astype(str).str.lower().eq('yes').sum())
                s_cnt = tot - l_cnt
                rate = round(l_cnt / tot * 100, 2) if tot > 0 else 0.0
                grp_data.append({
                    "Department": str(d),
                    "Total Employees": tot,
                    "Employees Left": l_cnt,
                    "Employees Stayed": s_cnt,
                    "Attrition Rate (%)": rate
                })
            res_df = pd.DataFrame(grp_data).sort_values(by="Attrition Rate (%)", ascending=False)
            top = res_df.iloc[0]
            low = res_df.iloc[-1]
            explanation = f"Department attrition rates range from {top['Attrition Rate (%)']}% in '{top['Department']}' down to {low['Attrition Rate (%)']}% in '{low['Department']}'."

            return {
                "query": query_str,
                "interpretation": "Employee attrition rate by Department.",
                "columns": list(res_df.columns),
                "data": _clean_records(res_df.to_dict(orient='records')),
                "total_results": len(res_df),
                "suggested_chart": "bar",
                "explanation": explanation
            }

        # -----------------------------------------------------------------
        # Q7: How many employees left from each department?
        # -----------------------------------------------------------------
        if dept_col and (
            re.search(r'\bhow\s+many\b.*?\bleft\b.*?\b(?:from\s+each\s+department|by\s+department)\b', q) or
            re.search(r'\b(?:employees\s+left|departures)\s+(?:from\s+each\s+department|by\s+department)\b', q)
        ):
            grp_data = []
            for d, g in df.groupby(dept_col):
                tot = len(g)
                l_cnt = int(g[attrition_col].astype(str).str.lower().eq('yes').sum())
                share = round(l_cnt / left_count * 100, 2) if left_count > 0 else 0.0
                grp_data.append({
                    "Department": str(d),
                    "Employees Left": l_cnt,
                    "Total in Dept": tot,
                    "Share of All Departures (%)": share
                })
            res_df = pd.DataFrame(grp_data).sort_values(by="Employees Left", ascending=False)
            top = res_df.iloc[0]
            explanation = f"The department with the most departures is '{top['Department']}' with {top['Employees Left']} employees leaving ({top['Share of All Departures (%)']}% of all departures)."

            return {
                "query": query_str,
                "interpretation": "Count of employees who left broken down by Department.",
                "columns": list(res_df.columns),
                "data": _clean_records(res_df.to_dict(orient='records')),
                "total_results": len(res_df),
                "suggested_chart": "bar",
                "explanation": explanation
            }

        # -----------------------------------------------------------------
        # Q8: Does overtime affect attrition?
        # -----------------------------------------------------------------
        if overtime_col and ('overtime' in q or 'over time' in q) and ('affect' in q or 'impact' in q or 'relat' in q or 'effect' in q or 'attrition' in q):
            grp_data = []
            for ot_val, g in df.groupby(overtime_col):
                tot = len(g)
                l_cnt = int(g[attrition_col].astype(str).str.lower().eq('yes').sum())
                s_cnt = tot - l_cnt
                rate = round(l_cnt / tot * 100, 2) if tot > 0 else 0.0
                grp_data.append({
                    "OverTime Status": str(ot_val),
                    "Total Employees": tot,
                    "Employees Left": l_cnt,
                    "Employees Stayed": s_cnt,
                    "Attrition Rate (%)": rate
                })
            res_df = pd.DataFrame(grp_data).sort_values(by="Attrition Rate (%)", ascending=False)
            top_ot = res_df.iloc[0]
            low_ot = res_df.iloc[-1]
            explanation = (
                f"Employees with OverTime = '{top_ot['OverTime Status']}' exhibit an attrition rate of {top_ot['Attrition Rate (%)']}% "
                f"({top_ot['Employees Left']} of {top_ot['Total Employees']}), compared to {low_ot['Attrition Rate (%)']}% "
                f"for OverTime = '{low_ot['OverTime Status']}'. While strongly correlated, this relationship does not by itself prove direct causation."
            )

            return {
                "query": query_str,
                "interpretation": "Attrition rate comparison by OverTime status.",
                "columns": list(res_df.columns),
                "data": _clean_records(res_df.to_dict(orient='records')),
                "total_results": len(res_df),
                "suggested_chart": "bar",
                "explanation": explanation
            }

        # -----------------------------------------------------------------
        # Q9: What is the average salary of employees who left?
        # -----------------------------------------------------------------
        if income_col and (
            re.search(r'\baverage\s+(?:salary|income)\b.*?\b(?:left|leave)\b', q) or
            re.search(r'\b(?:salary|income)\b.*?\b(?:of\s+employees\s+who\s+left)\b', q)
        ):
            left_income = df[left_mask][income_col].dropna()
            stayed_income = df[~left_mask][income_col].dropna()
            avg_left = round(float(left_income.mean()), 2)
            med_left = round(float(left_income.median()), 2)
            avg_stay = round(float(stayed_income.mean()), 2)
            med_stay = round(float(stayed_income.median()), 2)

            data = [
                {"Cohort": "Employees Who Left", "Average Monthly Salary ($)": avg_left, "Median Monthly Salary ($)": med_left, "Count": len(left_income)},
                {"Cohort": "Employees Who Stayed", "Average Monthly Salary ($)": avg_stay, "Median Monthly Salary ($)": med_stay, "Count": len(stayed_income)}
            ]
            diff = round(avg_left - avg_stay, 2)
            explanation = f"Employees who left earned an average monthly salary of ${avg_left:,.2f} (median: ${med_left:,.2f}) compared to ${avg_stay:,.2f} for those who stayed (a difference of ${diff:,.2f})."

            return {
                "query": query_str,
                "interpretation": "Average salary of employees who left vs employees who stayed.",
                "columns": list(data[0].keys()),
                "data": data,
                "total_results": len(data),
                "suggested_chart": "bar",
                "explanation": explanation
            }

        # -----------------------------------------------------------------
        # Q10: What is the average age of employees who left?
        # -----------------------------------------------------------------
        if age_col and (
            re.search(r'\baverage\s+age\b.*?\b(?:left|leave)\b', q) or
            re.search(r'\bage\b.*?\b(?:of\s+employees\s+who\s+left)\b', q)
        ):
            left_age = df[left_mask][age_col].dropna()
            stayed_age = df[~left_mask][age_col].dropna()
            avg_l_age = round(float(left_age.mean()), 1)
            med_l_age = round(float(left_age.median()), 1)
            avg_s_age = round(float(stayed_age.mean()), 1)
            med_s_age = round(float(stayed_age.median()), 1)

            data = [
                {"Cohort": "Employees Who Left", "Average Age (Years)": avg_l_age, "Median Age (Years)": med_l_age, "Count": len(left_age)},
                {"Cohort": "Employees Who Stayed", "Average Age (Years)": avg_s_age, "Median Age (Years)": med_s_age, "Count": len(stayed_age)}
            ]
            explanation = f"Employees who left had an average age of {avg_l_age} years (median: {med_l_age}) compared to {avg_s_age} years for employees who stayed."

            return {
                "query": query_str,
                "interpretation": "Average age of employees who left vs employees who stayed.",
                "columns": list(data[0].keys()),
                "data": data,
                "total_results": len(data),
                "suggested_chart": "bar",
                "explanation": explanation
            }

        # -----------------------------------------------------------------
        # Q11: Which age group has the highest attrition?
        # -----------------------------------------------------------------
        if age_col and re.search(r'\bage\s*group\b.*?\b(?:highest|most)\s+attrition\b', q) or (
            'age' in q and 'group' in q and 'attrition' in q
        ):
            # Create standard age bins
            bins = [0, 29, 39, 49, 120]
            labels = ["Under 30", "30 - 39", "40 - 49", "50+"]
            df_temp = df.copy()
            df_temp['AgeGroup'] = pd.cut(df_temp[age_col], bins=bins, labels=labels, right=True)

            grp_data = []
            for ag, g in df_temp.groupby('AgeGroup', observed=False):
                tot = len(g)
                l_cnt = int(g[attrition_col].astype(str).str.lower().eq('yes').sum())
                s_cnt = tot - l_cnt
                rate = round(l_cnt / tot * 100, 2) if tot > 0 else 0.0
                grp_data.append({
                    "Age Group": str(ag),
                    "Total Employees": tot,
                    "Employees Left": l_cnt,
                    "Employees Stayed": s_cnt,
                    "Attrition Rate (%)": rate
                })
            res_df = pd.DataFrame(grp_data)
            by_rate = res_df.sort_values(by="Attrition Rate (%)", ascending=False).iloc[0]
            by_count = res_df.sort_values(by="Employees Left", ascending=False).iloc[0]

            explanation = (
                f"The age group with the highest attrition rate is '{by_rate['Age Group']}' at {by_rate['Attrition Rate (%)']}% "
                f"({by_rate['Employees Left']} of {by_rate['Total Employees']}), while '{by_count['Age Group']}' had the highest count of departures ({by_count['Employees Left']} employees)."
            )

            return {
                "query": query_str,
                "interpretation": "Attrition by Age Group (identifying both highest rate and volume).",
                "columns": list(res_df.columns),
                "data": _clean_records(res_df.sort_values(by="Attrition Rate (%)", ascending=False).to_dict(orient='records')),
                "total_results": len(res_df),
                "suggested_chart": "bar",
                "explanation": explanation
            }

        # -----------------------------------------------------------------
        # Q12: What is the attrition rate by gender?
        # -----------------------------------------------------------------
        if gender_col and ('gender' in q or 'sex' in q) and 'attrition' in q:
            grp_data = []
            for gen, g in df.groupby(gender_col):
                tot = len(g)
                l_cnt = int(g[attrition_col].astype(str).str.lower().eq('yes').sum())
                s_cnt = tot - l_cnt
                rate = round(l_cnt / tot * 100, 2) if tot > 0 else 0.0
                grp_data.append({
                    "Gender": str(gen),
                    "Total Employees": tot,
                    "Employees Left": l_cnt,
                    "Employees Stayed": s_cnt,
                    "Attrition Rate (%)": rate
                })
            res_df = pd.DataFrame(grp_data).sort_values(by="Attrition Rate (%)", ascending=False)
            top = res_df.iloc[0]
            low = res_df.iloc[-1]
            explanation = f"The attrition rate is {top['Attrition Rate (%)']}% for {top['Gender']} employees ({top['Employees Left']} of {top['Total Employees']}) compared to {low['Attrition Rate (%)']}% for {low['Gender']} employees ({low['Employees Left']} of {low['Total Employees']})."

            return {
                "query": query_str,
                "interpretation": "Attrition rate breakdown by Gender.",
                "columns": list(res_df.columns),
                "data": _clean_records(res_df.to_dict(orient='records')),
                "total_results": len(res_df),
                "suggested_chart": "bar",
                "explanation": explanation
            }

        # -----------------------------------------------------------------
        # Q13: How many employees with low job satisfaction left?
        # -----------------------------------------------------------------
        if satisfaction_col and ('low satisfaction' in q or 'job satisfaction' in q or 'satisfaction' in q) and ('left' in q or 'attrition' in q):
            # Low job satisfaction: levels 1 and 2 (or bottom 40% if continuous)
            df_temp = df.copy()
            if pd.api.types.is_numeric_dtype(df_temp[satisfaction_col]):
                low_sat_mask = df_temp[satisfaction_col] <= 2
            else:
                low_sat_mask = df_temp[satisfaction_col].astype(str).str.lower().isin(['low', '1', '2', 'dissatisfied'])

            low_sat_total = int(low_sat_mask.sum())
            low_sat_left = int((low_sat_mask & left_mask).sum())
            low_sat_stay = low_sat_total - low_sat_left
            low_sat_rate = round(low_sat_left / low_sat_total * 100, 2) if low_sat_total > 0 else 0.0

            high_sat_total = total_employees - low_sat_total
            high_sat_left = left_count - low_sat_left
            high_sat_rate = round(high_sat_left / high_sat_total * 100, 2) if high_sat_total > 0 else 0.0

            data = [
                {"Satisfaction Tier": "Low Satisfaction (Levels 1-2)", "Total Employees": low_sat_total, "Employees Left": low_sat_left, "Employees Stayed": low_sat_stay, "Attrition Rate (%)": low_sat_rate},
                {"Satisfaction Tier": "High Satisfaction (Levels 3-4)", "Total Employees": high_sat_total, "Employees Left": high_sat_left, "Employees Stayed": high_sat_total - high_sat_left, "Attrition Rate (%)": high_sat_rate}
            ]
            explanation = f"Among employees with low job satisfaction, {low_sat_left:,} employees left the company, representing an attrition rate of {low_sat_rate}% (compared to {high_sat_rate}% for satisfied employees)."

            return {
                "query": query_str,
                "interpretation": "Attrition among employees with low job satisfaction.",
                "columns": list(data[0].keys()),
                "data": data,
                "total_results": len(data),
                "suggested_chart": "bar",
                "explanation": explanation
            }

        # -----------------------------------------------------------------
        # Q14: What is the attrition rate among employees who travel frequently?
        # -----------------------------------------------------------------
        if travel_col and ('travel' in q or 'business travel' in q) and ('attrition' in q or 'left' in q or 'frequently' in q):
            grp_data = []
            for tr, g in df.groupby(travel_col):
                tot = len(g)
                l_cnt = int(g[attrition_col].astype(str).str.lower().eq('yes').sum())
                s_cnt = tot - l_cnt
                rate = round(l_cnt / tot * 100, 2) if tot > 0 else 0.0
                grp_data.append({
                    "Travel Frequency": str(tr),
                    "Total Employees": tot,
                    "Employees Left": l_cnt,
                    "Employees Stayed": s_cnt,
                    "Attrition Rate (%)": rate
                })
            res_df = pd.DataFrame(grp_data).sort_values(by="Attrition Rate (%)", ascending=False)
            freq_row = next((r for r in grp_data if 'frequent' in r['Travel Frequency'].lower()), res_df.iloc[0])
            explanation = f"Employees in category '{freq_row['Travel Frequency']}' have an attrition rate of {freq_row['Attrition Rate (%)']}% ({freq_row['Employees Left']} of {freq_row['Total Employees']} left)."

            return {
                "query": query_str,
                "interpretation": "Attrition rate grouped by business travel frequency.",
                "columns": list(res_df.columns),
                "data": _clean_records(res_df.to_dict(orient='records')),
                "total_results": len(res_df),
                "suggested_chart": "bar",
                "explanation": explanation
            }

        return None
