import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from typing import Dict, Any, List, Optional

class InsightsService:

    @classmethod
    def generate_business_insights(cls, df: pd.DataFrame, target_col: Optional[str] = None) -> Dict[str, Any]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category', 'string', 'bool']).columns.tolist()
        total_rows = len(df)

        if total_rows == 0:
            return {"error": "Dataset is empty."}

        # 1. Detect or validate target column
        if not target_col or target_col not in df.columns:
            # Smart detection of target candidate
            candidates = ['profit', 'sales', 'churn', 'revenue', 'income', 'attrition', 'amount', 'risk_score', 'rating']
            found_target = None
            for cand in candidates:
                for col in df.columns:
                    if cand in col.lower():
                        found_target = col
                        break
                if found_target:
                    break
            target_col = found_target or (numeric_cols[0] if numeric_cols else df.columns[0])

        # 2. Executive KPI Highlights
        kpis = []
        for col in numeric_cols[:4]:
            series = df[col].dropna()
            if len(series) > 0:
                total_val = float(series.sum())
                avg_val = float(series.mean())
                max_val = float(series.max())
                min_val = float(series.min())
                
                # Check for standard business naming
                is_currency = any(k in col.lower() for k in ['sale', 'profit', 'charge', 'revenue', 'income', 'cost', 'amount', 'price'])
                prefix = "$" if is_currency else ""
                
                kpis.append({
                    "name": col,
                    "total": f"{prefix}{total_val:,.2f}" if abs(total_val) >= 1000 else f"{prefix}{total_val:.2f}",
                    "average": f"{prefix}{avg_val:,.2f}",
                    "min": f"{prefix}{min_val:,.2f}",
                    "max": f"{prefix}{max_val:,.2f}",
                    "raw_total": round(total_val, 2),
                    "raw_avg": round(avg_val, 2),
                    "trend": "positive" if avg_val > 0 else "neutral"
                })

        # 3. Automated Key Driver Analysis (Machine Learning & Statistics)
        drivers = []
        is_target_numeric = target_col in numeric_cols

        try:
            # Prepare feature matrix
            feature_cols = [c for c in df.columns if c != target_col and df[c].nunique() > 1 and df[c].nunique() < total_rows * 0.95]
            if len(feature_cols) >= 1 and total_rows >= 10:
                X = pd.DataFrame()
                for c in feature_cols:
                    if pd.api.types.is_numeric_dtype(df[c]):
                        X[c] = df[c].fillna(df[c].median())
                    else:
                        # Label encode categorical
                        le = LabelEncoder()
                        X[c] = le.fit_transform(df[c].astype(str))

                y_raw = df[target_col].dropna()
                common_idx = y_raw.index.intersection(X.index)
                X_clean = X.loc[common_idx]
                y_clean = y_raw.loc[common_idx]

                if is_target_numeric:
                    model = RandomForestRegressor(n_estimators=50, max_depth=6, random_state=42)
                    model.fit(X_clean, y_clean)
                else:
                    le_y = LabelEncoder()
                    y_encoded = le_y.fit_transform(y_clean.astype(str))
                    model = RandomForestClassifier(n_estimators=50, max_depth=6, random_state=42)
                    model.fit(X_clean, y_encoded)

                importances = model.feature_importances_
                
                for feat, imp in zip(feature_cols, importances):
                    # Also calculate correlation if both numeric
                    corr_val = None
                    if feat in numeric_cols and is_target_numeric:
                        corr_val = round(float(df[[feat, target_col]].corr().iloc[0, 1]), 3)

                    impact_level = "Critical" if imp >= 0.25 else ("High" if imp >= 0.12 else ("Moderate" if imp >= 0.05 else "Low"))
                    drivers.append({
                        "feature": feat,
                        "importance_pct": round(float(imp) * 100, 1),
                        "impact_level": impact_level,
                        "correlation": corr_val,
                        "summary": f"Accounts for {round(float(imp)*100, 1)}% of variance in {target_col}."
                    })

                drivers.sort(key=lambda x: x["importance_pct"], reverse=True)
                drivers = drivers[:6]
        except Exception as e:
            # Fallback correlation
            if is_target_numeric:
                for c in numeric_cols:
                    if c != target_col:
                        corr_val = df[[c, target_col]].corr().iloc[0, 1]
                        if not np.isnan(corr_val):
                            drivers.append({
                                "feature": c,
                                "importance_pct": round(abs(float(corr_val)) * 50, 1),
                                "impact_level": "High" if abs(corr_val) > 0.5 else "Moderate",
                                "correlation": round(float(corr_val), 3),
                                "summary": f"Correlation with {target_col} is {round(float(corr_val), 3)}"
                            })
                drivers.sort(key=lambda x: abs(x.get("correlation", 0)), reverse=True)

        # 4. Anomaly & Risk Alerts
        anomalies = []
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) > 10:
                q25 = series.quantile(0.25)
                q75 = series.quantile(0.75)
                iqr = q75 - q25
                if iqr > 0:
                    extreme_high = series[series > (q75 + 3.0 * iqr)]
                    extreme_low = series[series < (q25 - 3.0 * iqr)]
                    if len(extreme_high) > 0:
                        anomalies.append({
                            "type": "outlier_high",
                            "column": col,
                            "count": len(extreme_high),
                            "max_value": round(float(extreme_high.max()), 2),
                            "message": f"Detected {len(extreme_high)} extreme high outliers in '{col}' reaching up to {extreme_high.max():,.2f}."
                        })
                    if len(extreme_low) > 0:
                        anomalies.append({
                            "type": "outlier_low",
                            "column": col,
                            "count": len(extreme_low),
                            "min_value": round(float(extreme_low.min()), 2),
                            "message": f"Detected {len(extreme_low)} extreme negative/low outliers in '{col}' down to {extreme_low.min():,.2f}."
                        })

        # Segment breakdown for top categorical columns.
        # Pick columns that are actually usable for cohorting (a handful of
        # distinct groups) instead of blindly taking the first 2 text columns,
        # which are often high-cardinality fields like names/IDs that produce
        # no useful cohorts and leave this section empty.
        cohort_insights = []
        cohort_candidates = [c for c in cat_cols if 2 <= df[c].nunique() <= 12]
        for cat in cohort_candidates[:2]:
            if is_target_numeric:
                grp = df.groupby(cat)[target_col].agg(['mean', 'sum', 'count']).reset_index()
                grp = grp.sort_values(by='mean', ascending=False)
                top_segment = grp.iloc[0]
                bottom_segment = grp.iloc[-1]
                
                cohort_insights.append({
                    "category_dimension": cat,
                    "top_performer": {
                        "name": str(top_segment[cat]),
                        "mean_value": round(float(top_segment['mean']), 2),
                        "total_volume": round(float(top_segment['sum']), 2),
                        "count": int(top_segment['count'])
                    },
                    "bottom_performer": {
                        "name": str(bottom_segment[cat]),
                        "mean_value": round(float(bottom_segment['mean']), 2),
                        "total_volume": round(float(bottom_segment['sum']), 2),
                        "count": int(bottom_segment['count'])
                    }
                })

        # 5. Executive Strategic Recommendations
        recommendations = []
        if drivers:
            top_driver = drivers[0]
            recommendations.append({
                "title": f"Optimize Primary Driver ({top_driver['feature']})",
                "badge": "High Priority",
                "description": f"Our analysis indicates '{top_driver['feature']}' exerts {top_driver['importance_pct']}% relative influence on {target_col}. Focus operational initiatives on monitoring and calibrating this parameter."
            })

        if cohort_insights:
            c = cohort_insights[0]
            recommendations.append({
                "title": f"Scale Winning Cohort in '{c['category_dimension']}'",
                "badge": "Growth Opportunity",
                "description": f"'{c['top_performer']['name']}' outperforms peers with an average {target_col} of {c['top_performer']['mean_value']:,}. Replicate best practices from this cohort across '{c['bottom_performer']['name']}'."
            })

        if anomalies:
            a = anomalies[0]
            recommendations.append({
                "title": f"Mitigate Data & Financial Variances in '{a['column']}'",
                "badge": "Risk Alert",
                "description": a['message'] + " Consider setting automated boundary alerts to prevent margin leakages."
            })

        # Add general data-driven recommendation
        recommendations.append({
            "title": "Continuous Automated Monitoring",
            "badge": "Best Practice",
            "description": f"Dataset contains {total_rows:,} records across {len(df.columns)} dimensions. Establish recurring ETL syncs to track real-time KPI velocity."
        })

        return {
            "target_column": target_col,
            "target_is_numeric": is_target_numeric,
            "kpi_highlights": kpis,
            "key_drivers": drivers,
            "anomalies": anomalies,
            "cohort_insights": cohort_insights,
            "strategic_recommendations": recommendations
        }
