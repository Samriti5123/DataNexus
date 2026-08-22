import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


def _is_number(value) -> bool:
    """True for real numeric scalars (int/float/numpy numeric), excluding bool."""
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, float, np.integer, np.floating))

# Distinct modern color palette for charts
CHART_PALETTES = {
    'modern_emerald': [
        'rgba(16, 185, 129, 0.85)', 'rgba(59, 130, 246, 0.85)', 'rgba(245, 158, 11, 0.85)',
        'rgba(239, 68, 68, 0.85)', 'rgba(168, 85, 247, 0.85)', 'rgba(236, 72, 153, 0.85)',
        'rgba(20, 184, 166, 0.85)', 'rgba(249, 115, 22, 0.85)', 'rgba(99, 102, 241, 0.85)'
    ],
    'cyber_indigo': [
        'rgba(99, 102, 241, 0.85)', 'rgba(14, 165, 233, 0.85)', 'rgba(244, 63, 94, 0.85)',
        'rgba(139, 92, 246, 0.85)', 'rgba(16, 185, 129, 0.85)', 'rgba(234, 179, 8, 0.85)',
        'rgba(249, 115, 22, 0.85)', 'rgba(217, 70, 239, 0.85)', 'rgba(6, 182, 212, 0.85)'
    ],
    'sunset_warmth': [
        'rgba(249, 115, 22, 0.85)', 'rgba(245, 158, 11, 0.85)', 'rgba(239, 68, 68, 0.85)',
        'rgba(217, 70, 239, 0.85)', 'rgba(139, 92, 246, 0.85)', 'rgba(59, 130, 246, 0.85)',
        'rgba(16, 185, 129, 0.85)', 'rgba(20, 184, 166, 0.85)', 'rgba(168, 85, 247, 0.85)'
    ]
}

class VisualizeService:

    @classmethod
    def get_chart_options(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Provides available columns classified by numeric, categorical, datetime for the visualizer UI."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category', 'string', 'bool']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime', 'datetime64']).columns.tolist()

        # Check if any string column is convertible to date
        for col in cat_cols[:]:
            if 'date' in col.lower() or 'time' in col.lower() or 'timestamp' in col.lower():
                if col not in date_cols:
                    date_cols.append(col)

        return {
            "all_columns": list(df.columns),
            "numeric_columns": numeric_cols,
            "categorical_columns": cat_cols,
            "datetime_columns": date_cols,
            "chart_types": [
                {"id": "bar", "label": "Bar Chart", "category": "comparison"},
                {"id": "stacked_bar", "label": "Stacked Bar Chart", "category": "comparison"},
                {"id": "horizontal_bar", "label": "Horizontal Bar", "category": "comparison"},
                {"id": "line", "label": "Line Chart", "category": "trend"},
                {"id": "area", "label": "Area Chart", "category": "trend"},
                {"id": "scatter", "label": "Scatter Plot", "category": "correlation"},
                {"id": "bubble", "label": "Bubble Chart", "category": "correlation"},
                {"id": "pie", "label": "Pie Chart", "category": "composition"},
                {"id": "donut", "label": "Donut Chart", "category": "composition"},
                {"id": "histogram", "label": "Histogram", "category": "distribution"},
                {"id": "boxplot", "label": "Box Plot", "category": "distribution"}
            ],
            "aggregations": ["sum", "mean", "count", "median", "min", "max"]
        }

    @classmethod
    def build_chart_data(
        cls,
        df: pd.DataFrame,
        chart_type: str,
        x_axis: str,
        y_axis: Optional[str] = None,
        y_axes: Optional[List[str]] = None,
        group_by: Optional[str] = None,
        size_axis: Optional[str] = None,  # for bubble chart
        aggregation: str = 'sum',
        sort_by: str = 'none',  # 'none', 'value_desc', 'value_asc', 'label_asc'
        limit: int = 15,
        palette_name: str = 'modern_emerald'
    ) -> Dict[str, Any]:
        palette = CHART_PALETTES.get(palette_name, CHART_PALETTES['modern_emerald'])
        
        if x_axis not in df.columns:
            x_axis = df.columns[0]

        # Consolidate target y columns
        active_y_cols = []
        if y_axes and len(y_axes) > 0:
            active_y_cols = [c for c in y_axes if c in df.columns]
        elif y_axis and y_axis in df.columns:
            active_y_cols = [y_axis]

        # ----------------------------------------------------
        # 1. HISTOGRAM
        # ----------------------------------------------------
        if chart_type == 'histogram':
            target_col = active_y_cols[0] if active_y_cols else x_axis
            if target_col not in df.columns or not pd.api.types.is_numeric_dtype(df[target_col]):
                num_cols = df.select_dtypes(include=[np.number]).columns
                target_col = num_cols[0] if len(num_cols) > 0 else x_axis
            
            clean_series = pd.to_numeric(df[target_col], errors='coerce').dropna()
            num_bins = min(20, max(5, int(limit)))
            counts, bin_edges = np.histogram(clean_series, bins=num_bins)
            
            labels = [f"{round(bin_edges[i], 1)} - {round(bin_edges[i+1], 1)}" for i in range(len(counts))]
            dataset = {
                "label": f"Distribution of {target_col}",
                "data": [int(c) for c in counts],
                "backgroundColor": palette[0],
                "borderColor": palette[0].replace('0.85', '1'),
                "borderWidth": 1
            }
            return {
                "chart_type": "bar",
                "title": f"Histogram Distribution: {target_col}",
                "labels": labels,
                "datasets": [dataset],
                "stats": {
                    "count": int(len(clean_series)),
                    "mean": round(float(clean_series.mean()), 2),
                    "median": round(float(clean_series.median()), 2),
                    "std": round(float(clean_series.std()), 2)
                }
            }

        # ----------------------------------------------------
        # 2. SCATTER & BUBBLE PLOTS
        # ----------------------------------------------------
        if chart_type in ['scatter', 'bubble']:
            if not active_y_cols:
                num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                y_col = num_cols[1] if len(num_cols) > 1 else (num_cols[0] if num_cols else x_axis)
            else:
                y_col = active_y_cols[0]

            temp_df = df.dropna(subset=[x_axis, y_col]).head(250)
            
            datasets = []
            if group_by and group_by in temp_df.columns:
                unique_groups = temp_df[group_by].unique()[:8]
                for idx, g in enumerate(unique_groups):
                    gdf = temp_df[temp_df[group_by] == g]
                    data_points = []
                    for _, row in gdf.iterrows():
                        pt = {
                            "x": round(float(row[x_axis]), 2) if _is_number(row[x_axis]) else row[x_axis],
                            "y": round(float(row[y_col]), 2) if _is_number(row[y_col]) else row[y_col]
                        }
                        if chart_type == 'bubble' and size_axis and size_axis in gdf.columns:
                            raw_r = float(row[size_axis]) if not pd.isna(row[size_axis]) else 5
                            pt["r"] = max(4, min(25, int(raw_r / (temp_df[size_axis].max() or 1) * 20 + 4)))
                        elif chart_type == 'bubble':
                            pt["r"] = 6
                        data_points.append(pt)

                    color = palette[idx % len(palette)]
                    datasets.append({
                        "label": str(g),
                        "data": data_points,
                        "backgroundColor": color,
                        "borderColor": color.replace('0.85', '1'),
                        "pointRadius": 5 if chart_type == 'scatter' else None
                    })
            else:
                data_points = []
                for _, row in temp_df.iterrows():
                    pt = {
                        "x": round(float(row[x_axis]), 2) if _is_number(row[x_axis]) else row[x_axis],
                        "y": round(float(row[y_col]), 2) if _is_number(row[y_col]) else row[y_col]
                    }
                    if chart_type == 'bubble' and size_axis and size_axis in temp_df.columns:
                        raw_r = float(row[size_axis]) if not pd.isna(row[size_axis]) else 5
                        pt["r"] = max(4, min(25, int(raw_r / (temp_df[size_axis].max() or 1) * 20 + 4)))
                    elif chart_type == 'bubble':
                        pt["r"] = 6
                    data_points.append(pt)

                datasets.append({
                    "label": f"{x_axis} vs {y_col}",
                    "data": data_points,
                    "backgroundColor": palette[0],
                    "borderColor": palette[0].replace('0.85', '1'),
                    "pointRadius": 5 if chart_type == 'scatter' else None
                })

            return {
                "chart_type": chart_type,
                "title": f"{chart_type.capitalize()}: {x_axis} vs {y_col}",
                "labels": [],
                "datasets": datasets
            }

        # ----------------------------------------------------
        # 3. BOXPLOT
        # ----------------------------------------------------
        if chart_type == 'boxplot':
            val_col = active_y_cols[0] if active_y_cols else (x_axis if pd.api.types.is_numeric_dtype(df[x_axis]) else df.select_dtypes(include=[np.number]).columns[0])
            cat_col = x_axis if x_axis != val_col else (group_by or 'All Data')

            box_datasets = []
            labels = []

            if cat_col in df.columns and cat_col != 'All Data':
                top_cats = df[cat_col].value_counts().head(8).index.tolist()
                for c in top_cats:
                    sub = pd.to_numeric(df[df[cat_col] == c][val_col], errors='coerce').dropna()
                    if len(sub) > 2:
                        labels.append(str(c))
                        box_datasets.append({
                            "min": round(float(sub.min()), 2),
                            "q1": round(float(sub.quantile(0.25)), 2),
                            "median": round(float(sub.median()), 2),
                            "q3": round(float(sub.quantile(0.75)), 2),
                            "max": round(float(sub.max()), 2),
                            "mean": round(float(sub.mean()), 2)
                        })
            else:
                sub = pd.to_numeric(df[val_col], errors='coerce').dropna()
                labels.append(val_col)
                box_datasets.append({
                    "min": round(float(sub.min()), 2),
                    "q1": round(float(sub.quantile(0.25)), 2),
                    "median": round(float(sub.median()), 2),
                    "q3": round(float(sub.quantile(0.75)), 2),
                    "max": round(float(sub.max()), 2),
                    "mean": round(float(sub.mean()), 2)
                })

            return {
                "chart_type": "boxplot",
                "title": f"Box Plot Distribution: {val_col}",
                "labels": labels,
                "box_stats": box_datasets
            }

        # ----------------------------------------------------
        # 4. AGGREGATED CHARTS: BAR, STACKED BAR, LINE, AREA, PIE, DONUT
        # ----------------------------------------------------
        if not active_y_cols:
            # Count aggregation by default
            counts = df[x_axis].value_counts().head(limit)
            if sort_by == 'value_asc':
                counts = counts.sort_values(ascending=True)
            elif sort_by == 'label_asc':
                counts = counts.sort_index(ascending=True)

            labels = [str(k) for k in counts.index]
            data = [int(v) for v in counts.values]

            if chart_type in ['pie', 'donut']:
                bg_colors = palette[:len(labels)] if len(palette) >= len(labels) else (palette * 3)[:len(labels)]
            else:
                bg_colors = [palette[0]] * len(labels)

            return {
                "chart_type": chart_type,
                "title": f"Record Count by {x_axis}",
                "labels": labels,
                "datasets": [{
                    "label": "Count",
                    "data": data,
                    "backgroundColor": bg_colors,
                    "borderColor": palette[0].replace('0.85', '1'),
                    "borderWidth": 1,
                    "fill": chart_type == 'area'
                }]
            }

        # Group-by multi-dimension aggregation
        if group_by and group_by in df.columns and group_by != x_axis:
            y_col = active_y_cols[0]
            top_x = df[x_axis].value_counts().head(limit).index.tolist()
            top_g = df[group_by].value_counts().head(6).index.tolist()

            sub_df = df[df[x_axis].isin(top_x) & df[group_by].isin(top_g)]
            pivot = pd.pivot_table(
                sub_df,
                index=x_axis,
                columns=group_by,
                values=y_col,
                aggfunc=aggregation,
                fill_value=0
            )

            labels = [str(k) for k in pivot.index]
            datasets = []
            for idx, g in enumerate(pivot.columns):
                color = palette[idx % len(palette)]
                datasets.append({
                    "label": str(g),
                    "data": [round(float(v), 2) for v in pivot[g].values],
                    "backgroundColor": color,
                    "borderColor": color.replace('0.85', '1'),
                    "borderWidth": 1.5,
                    "fill": chart_type == 'area',
                    "stack": "stack1" if chart_type == 'stacked_bar' else None
                })

            return {
                "chart_type": 'bar' if chart_type == 'stacked_bar' else chart_type,
                "title": f"{aggregation.capitalize()} of {y_col} by {x_axis} and {group_by}",
                "labels": labels,
                "datasets": datasets
            }

        # Single / Multi Y-series aggregation
        datasets = []
        labels = []

        agg_dict = {col: aggregation for col in active_y_cols}
        grouped = df.groupby(x_axis)[active_y_cols].agg(agg_dict).reset_index()

        if sort_by == 'value_desc':
            grouped = grouped.sort_values(by=active_y_cols[0], ascending=False)
        elif sort_by == 'value_asc':
            grouped = grouped.sort_values(by=active_y_cols[0], ascending=True)
        elif sort_by == 'label_asc':
            grouped = grouped.sort_values(by=x_axis, ascending=True)
        else:
            grouped = grouped.head(limit)

        grouped = grouped.head(limit)
        labels = [str(k) for k in grouped[x_axis]]

        for idx, y_col in enumerate(active_y_cols):
            color = palette[idx % len(palette)]
            if chart_type in ['pie', 'donut']:
                bg_colors = palette[:len(labels)] if len(palette) >= len(labels) else (palette * 3)[:len(labels)]
            else:
                bg_colors = color

            datasets.append({
                "label": f"{aggregation.capitalize()} of {y_col}",
                "data": [round(float(v), 2) for v in grouped[y_col]],
                "backgroundColor": bg_colors,
                "borderColor": color.replace('0.85', '1'),
                "borderWidth": 2 if chart_type in ['line', 'area'] else 1,
                "fill": chart_type == 'area',
                "tension": 0.35 if chart_type in ['line', 'area'] else 0
            })

        return {
            "chart_type": chart_type,
            "title": f"{aggregation.capitalize()} of {', '.join(active_y_cols)} by {x_axis}",
            "labels": labels,
            "datasets": datasets
        }
