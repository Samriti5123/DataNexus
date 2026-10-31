import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

class ReportService:

    @classmethod
    def generate_html_report(
        cls,
        dataset_name: str,
        df: pd.DataFrame,
        eda_summary: Dict[str, Any],
        health_audit: Dict[str, Any],
        insights: Dict[str, Any]
    ) -> str:
        generation_time = datetime.now().strftime("%B %d, %Y - %H:%M UTC")
        
        # Build KPI cards HTML
        kpi_cards_html = ""
        for kpi in insights.get('kpi_highlights', []):
            kpi_cards_html += f"""
            <div class="kpi-card">
                <div class="kpi-title">{kpi['name']}</div>
                <div class="kpi-value">{kpi['total']}</div>
                <div class="kpi-sub">Average: <strong>{kpi['average']}</strong></div>
            </div>
            """

        # Build Drivers HTML
        drivers_html = ""
        for d in insights.get('key_drivers', []):
            badge_class = "badge-crit" if d['impact_level'] == 'Critical' else ("badge-high" if d['impact_level'] == 'High' else "badge-mod")
            drivers_html += f"""
            <div class="driver-row">
                <div class="driver-info">
                    <span class="driver-name">{d['feature']}</span>
                    <span class="driver-badge {badge_class}">{d['impact_level']} Impact</span>
                </div>
                <div class="driver-bar-bg">
                    <div class="driver-bar-fill" style="width: {min(100, max(5, d['importance_pct'] * 1.5))}%;"></div>
                </div>
                <div class="driver-summary">{d['summary']}</div>
            </div>
            """

        # Build Strategic Recommendations HTML
        recs_html = ""
        for r in insights.get('strategic_recommendations', []):
            recs_html += f"""
            <div class="rec-card">
                <div class="rec-header">
                    <span class="rec-badge">{r['badge']}</span>
                    <span class="rec-title">{r['title']}</span>
                </div>
                <p class="rec-desc">{r['description']}</p>
            </div>
            """

        # Build Data Health Audit HTML
        issues_html = ""
        if health_audit.get('issues'):
            for issue in health_audit['issues'][:5]:
                issues_html += f"<li class='issue-item'>{issue['message']}</li>"
        else:
            issues_html = "<li class='issue-item clean'>No data health issues found. 100% clean dataset.</li>"

        # Build Top Data Rows Table Preview
        table_headers = "".join([f"<th>{col}</th>" for col in df.columns[:8]])
        table_rows = ""
        for _, row in df.head(8).iterrows():
            cells = "".join([f"<td>{str(val)[:30]}</td>" for val in row.iloc[:8]])
            table_rows += f"<tr>{cells}</tr>"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataNexus Executive Report - {dataset_name}</title>
    <style>
        :root {{
            --primary: #0f172a;
            --accent: #10b981;
            --accent-blue: #3b82f6;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text-dark: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background-color: var(--bg); color: var(--text-dark); padding: 40px 20px; line-height: 1.6; }}
        .container {{ max-width: 1100px; margin: 0 auto; background: var(--card-bg); border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.06); padding: 48px; border: 1px solid var(--border); }}
        
        .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid var(--border); padding-bottom: 24px; margin-bottom: 32px; }}
        .logo-area {{ display: flex; align-items: center; gap: 12px; }}
        .logo-box {{ background: linear-gradient(135deg, #10b981, #3b82f6); width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 22px; }}
        .title {{ font-size: 26px; font-weight: 800; color: var(--primary); }}
        .subtitle {{ color: var(--text-muted); font-size: 14px; margin-top: 4px; }}
        .meta-box {{ text-align: right; font-size: 13px; color: var(--text-muted); }}

        .section-title {{ font-size: 18px; font-weight: 700; color: var(--primary); margin-bottom: 16px; display: flex; align-items: center; gap: 8px; border-left: 4px solid var(--accent); padding-left: 10px; }}
        
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 36px; }}
        .kpi-card {{ background: #f1f5f9; border-radius: 12px; padding: 20px; border: 1px solid var(--border); }}
        .kpi-title {{ font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); margin-bottom: 8px; }}
        .kpi-value {{ font-size: 26px; font-weight: 800; color: var(--primary); }}
        .kpi-sub {{ font-size: 12px; color: var(--text-muted); margin-top: 4px; }}

        .drivers-container {{ background: #f8fafc; border-radius: 12px; padding: 24px; border: 1px solid var(--border); margin-bottom: 36px; }}
        .driver-row {{ margin-bottom: 16px; }}
        .driver-info {{ display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 14px; font-weight: 600; }}
        .driver-badge {{ font-size: 11px; padding: 2px 8px; border-radius: 6px; text-transform: uppercase; font-weight: 700; }}
        .badge-crit {{ background: #fee2e2; color: #b91c1c; }}
        .badge-high {{ background: #ffedd5; color: #c2410c; }}
        .badge-mod {{ background: #dbeafe; color: #1d4ed8; }}
        .driver-bar-bg {{ background: #e2e8f0; border-radius: 99px; height: 8px; overflow: hidden; margin-bottom: 4px; }}
        .driver-bar-fill {{ background: linear-gradient(90deg, #10b981, #3b82f6); height: 100%; border-radius: 99px; }}
        .driver-summary {{ font-size: 12px; color: var(--text-muted); }}

        .recs-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 36px; }}
        .rec-card {{ background: #ffffff; border-radius: 12px; padding: 20px; border: 1px solid var(--border); box-shadow: 0 2px 6px rgba(0,0,0,0.02); }}
        .rec-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
        .rec-badge {{ background: #dcfce7; color: #15803d; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px; text-transform: uppercase; }}
        .rec-title {{ font-size: 14px; font-weight: 700; color: var(--primary); }}
        .rec-desc {{ font-size: 13px; color: #475569; line-height: 1.5; }}

        .stats-summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 36px; text-align: center; }}
        .stat-box {{ background: #f8fafc; border: 1px solid var(--border); border-radius: 10px; padding: 16px; }}
        .stat-num {{ font-size: 20px; font-weight: 800; color: var(--primary); }}
        .stat-lbl {{ font-size: 12px; color: var(--text-muted); margin-top: 4px; }}

        .table-wrap {{ overflow-x: auto; margin-bottom: 36px; border-radius: 10px; border: 1px solid var(--border); }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }}
        th {{ background: #f1f5f9; padding: 12px 14px; font-weight: 600; color: var(--primary); border-bottom: 1px solid var(--border); }}
        td {{ padding: 10px 14px; border-bottom: 1px solid var(--border); color: #334155; }}
        tr:last-child td {{ border-bottom: none; }}

        .print-btn {{ display: inline-block; background: var(--primary); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; text-decoration: none; font-size: 14px; }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ border: none; box-shadow: none; padding: 0; }}
            .print-btn {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo-area">
                <div class="logo-box">DN</div>
                <div>
                    <h1 class="title">DataNexus Executive Intelligence Report</h1>
                    <p class="subtitle">Dataset: <strong>{dataset_name}</strong> | Automated Synthesis</p>
                </div>
            </div>
            <div class="meta-box">
                <p>Generated on: <strong>{generation_time}</strong></p>
                <p style="margin-top: 8px;"><button class="print-btn" onclick="window.print()">Print / Save PDF</button></p>
            </div>
        </div>

        <div class="section-title">Key Executive Performance Indicators</div>
        <div class="kpi-grid">
            {kpi_cards_html}
        </div>

        <div class="stats-summary">
            <div class="stat-box">
                <div class="stat-num">{eda_summary.get('total_rows', len(df)):,}</div>
                <div class="stat-lbl">Total Records</div>
            </div>
            <div class="stat-box">
                <div class="stat-num">{eda_summary.get('total_columns', len(df.columns))}</div>
                <div class="stat-lbl">Dimensions / Attributes</div>
            </div>
            <div class="stat-box">
                <div class="stat-num">{health_audit.get('overall_score', 100)}%</div>
                <div class="stat-lbl">Data Quality Score</div>
            </div>
            <div class="stat-box">
                <div class="stat-num">{eda_summary.get('missing_cells', 0)}</div>
                <div class="stat-lbl">Missing Values</div>
            </div>
        </div>

        <div class="section-title">Statistical Driver & Impact Analysis</div>
        <div class="drivers-container">
            {drivers_html if drivers_html else '<p style="color: #64748b; font-size: 14px;">No multi-feature driver variance found.</p>'}
        </div>

        <div class="section-title">C-Suite Strategic Recommendations</div>
        <div class="recs-grid">
            {recs_html}
        </div>

        <div class="section-title">Data Snapshot Preview (Top 8 Records)</div>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>{table_headers}</tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        
        <div style="text-align: center; margin-top: 40px; border-top: 1px solid var(--border); padding-top: 20px; font-size: 12px; color: var(--text-muted);">
            Generated by DataNexus – Interactive Data Analysis & Business Intelligence Platform
        </div>
    </div>
</body>
</html>
        """
        return html
