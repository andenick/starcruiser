#!/usr/bin/env python3
"""
StarCruiser Dashboard — Plotly Dash Visualization App
=====================================================
Interactive macroeconomic data explorer with methodology panels,
data tables, CSV download, and startup validation.

Usage: python Dashboard/app.py
Serves on http://localhost:8050
"""

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html, dash_table, callback_context

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Prepared data-pipeline outputs (see data/MANIFEST.md). Override the base via
# the PIPELINE_ROOT env var if your pipeline outputs live elsewhere.
import os
PIPELINE_ROOT = Path(os.environ.get("PIPELINE_ROOT", str(PROJECT_ROOT / "Technical" / "pipeline")))
CHOPPED_DIR = PIPELINE_ROOT / "data" / "final-data" / "chopped"
REGISTRY_PATH = PIPELINE_ROOT / "series_registry.json"
RESEARCH_DIR = PIPELINE_ROOT / "research"

CATEGORIES = {
    "Inflation": {
        "file": "inflation_chopped.csv",
        "default_cols": ["cpi_yoy", "core_cpi_yoy", "pce_yoy", "core_pce_yoy"],
        "title": "Inflation Rates (YoY %)",
        "research": ["A01"],
    },
    "Employment": {
        "file": "employment_chopped.csv",
        "default_cols": ["unemployment_rate", "lfpr", "emp_pop_ratio", "u6_rate"],
        "title": "Labor Market Indicators",
        "research": ["A02"],
    },
    "Treasury & Monetary": {
        "file": "yield_curve_chopped.csv",
        "default_cols": ["fed_funds", "gs10", "gs2", "spread_10y2y"],
        "title": "Interest Rates & Yield Curve",
        "research": ["A03"],
    },
    "Recession Indicators": {
        "file": "recession_chopped.csv",
        "default_cols": [],
        "title": "Recession Probability & Leading Indicators",
        "research": ["A06"],
    },
    "Industry": {
        "file": "industry_chopped.csv",
        "default_cols": [],
        "title": "Industry Employment Decomposition",
        "research": ["A13"],
    },
    "Credit Conditions": {
        "file": "credit_chopped.csv",
        "default_cols": [],
        "title": "Credit & Lending Conditions",
        "research": ["A14"],
    },
    "Unemployment Intensity": {
        "file": "unemployment_intensity_chopped.csv",
        "default_cols": [],
        "title": "Unemployment Duration & Composition",
        "research": ["A09"],
    },
    "Shelter Pipeline": {
        "file": "shelter_chopped.csv",
        "default_cols": [],
        "title": "Housing & Shelter Inflation",
        "research": ["A34"],
    },
    "Energy Decomposition": {
        "file": "energy_chopped.csv",
        "default_cols": [],
        "title": "Energy Price Components",
        "research": ["A35"],
    },
    "Capital-Labor": {
        "file": "capital_labor_chopped.csv",
        "default_cols": [],
        "title": "Capital-Labor Ratios by Facility Type",
        "research": ["A56"],
    },
}


def load_chopped_csv(filepath: Path) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(filepath, header=None)
    meta_row = raw.iloc[0].tolist()
    id_row = raw.iloc[1].tolist()
    data = raw.iloc[2:].copy()

    result = pd.DataFrame()
    result["date"] = pd.to_datetime(data.iloc[:, 0], errors="coerce")

    col_meta = {}
    for i in range(1, len(meta_row)):
        col_desc = str(raw.iloc[0, i]) if pd.notna(raw.iloc[0, i]) else f"col_{i}"
        col_id = str(raw.iloc[1, i]) if pd.notna(raw.iloc[1, i]) else f"id_{i}"

        parts = col_id.split("-", 1)
        short_name = parts[1] if len(parts) > 1 else parts[0]

        result[short_name] = pd.to_numeric(data.iloc[:, i], errors="coerce")
        col_meta[short_name] = {"description": col_desc, "id": col_id}

    result = result.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return result, col_meta


def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_research(analysis_ids: list) -> dict:
    combined = {"methodology": [], "findings": []}
    for aid in analysis_ids:
        path = RESEARCH_DIR / f"{aid}_research.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            combined["methodology"].append(f"**{aid} — {data.get('name', '')}**: {data.get('methodology_description', '')}")
            for finding in data.get("key_findings", []):
                if finding:
                    combined["findings"].append(finding)
    return combined


def startup_validation() -> list[str]:
    issues = []
    if not CHOPPED_DIR.exists():
        issues.append(f"CRITICAL: Chopped directory not found: {CHOPPED_DIR}")
        return issues
    csv_count = len(list(CHOPPED_DIR.glob("*.csv")))
    if csv_count == 0:
        issues.append("CRITICAL: No chopped CSVs found")
    for cat_name, cat_info in CATEGORIES.items():
        fpath = CHOPPED_DIR / cat_info["file"]
        if not fpath.exists():
            issues.append(f"WARN: {cat_name} data file missing: {cat_info['file']}")
        elif fpath.stat().st_size < 100:
            issues.append(f"WARN: {cat_name} data file empty: {cat_info['file']}")
    if not REGISTRY_PATH.exists():
        issues.append("WARN: series_registry.json not found")
    return issues


registry = load_registry()

app = Dash(__name__)
app.title = "StarCruiser — Macro Intelligence"

app.layout = html.Div(
    style={"backgroundColor": "#1a1a2e", "minHeight": "100vh", "color": "#e0e0e0", "fontFamily": "Segoe UI, sans-serif"},
    children=[
        html.Div(
            style={"padding": "20px 30px", "borderBottom": "1px solid #333"},
            children=[
                html.H1("StarCruiser", style={"margin": "0", "color": "#00d4ff", "fontSize": "28px"}),
                html.P(
                    f"Macroeconomic Employment & Inflation Intelligence — "
                    f"{registry.get('total_series', 599)} series, "
                    f"{len(registry.get('categories', {}))} categories, "
                    f"56 analyses",
                    style={"margin": "5px 0 0 0", "color": "#888", "fontSize": "14px"},
                ),
            ],
        ),
        html.Div(
            style={"display": "flex", "padding": "20px 30px", "gap": "20px"},
            children=[
                # Sidebar
                html.Div(
                    style={"width": "220px", "flexShrink": "0"},
                    children=[
                        html.Label("Category", style={"fontWeight": "bold", "marginBottom": "8px", "display": "block"}),
                        dcc.Dropdown(
                            id="category-dropdown",
                            options=[{"label": k, "value": k} for k in CATEGORIES],
                            value="Inflation",
                            style={"backgroundColor": "#16213e", "color": "#000"},
                        ),
                        html.Div(id="series-selector", style={"marginTop": "20px"}),
                        html.Div(id="metadata-panel", style={"marginTop": "20px", "fontSize": "12px", "color": "#aaa"}),
                    ],
                ),
                # Main content
                html.Div(
                    style={"flex": "1"},
                    children=[
                        dcc.Graph(id="main-chart", style={"height": "500px"}),
                        html.Div(
                            id="summary-panel",
                            style={"marginTop": "10px", "padding": "15px", "backgroundColor": "#16213e", "borderRadius": "8px"},
                        ),
                        # Methodology panel
                        html.Details(
                            style={"marginTop": "15px", "backgroundColor": "#16213e", "borderRadius": "8px", "padding": "10px"},
                            children=[
                                html.Summary("Methodology & Key Findings", style={"cursor": "pointer", "color": "#00d4ff", "fontWeight": "bold"}),
                                html.Div(id="methodology-panel", style={"marginTop": "10px", "fontSize": "13px", "lineHeight": "1.6"}),
                            ],
                        ),
                        # Data table
                        html.Details(
                            style={"marginTop": "15px", "backgroundColor": "#16213e", "borderRadius": "8px", "padding": "10px"},
                            children=[
                                html.Summary("Data Table", style={"cursor": "pointer", "color": "#00d4ff", "fontWeight": "bold"}),
                                html.Div(
                                    id="data-table-container",
                                    style={"marginTop": "10px", "maxHeight": "400px", "overflowY": "auto"},
                                ),
                                html.Button(
                                    "Download CSV",
                                    id="download-btn",
                                    style={
                                        "marginTop": "10px", "padding": "8px 16px",
                                        "backgroundColor": "#00d4ff", "color": "#1a1a2e",
                                        "border": "none", "borderRadius": "4px", "cursor": "pointer",
                                    },
                                ),
                                dcc.Download(id="download-csv"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)

# Store current data for download
_current_data = {}


@app.callback(
    Output("series-selector", "children"),
    Input("category-dropdown", "value"),
)
def update_series_selector(category):
    if not category or category not in CATEGORIES:
        return html.P("Select a category")

    cat_info = CATEGORIES[category]
    filepath = CHOPPED_DIR / cat_info["file"]

    if not filepath.exists():
        return html.P(f"File not found: {cat_info['file']}", style={"color": "#ff6b6b"})

    df, col_meta = load_chopped_csv(filepath)
    numeric_cols = [c for c in df.columns if c != "date"]

    defaults = cat_info.get("default_cols", [])
    if not defaults:
        defaults = numeric_cols[:4]
    valid_defaults = [d for d in defaults if d in numeric_cols]

    options = []
    for c in numeric_cols:
        desc = col_meta.get(c, {}).get("description", c)
        label = desc if len(desc) <= 40 else c
        options.append({"label": f" {label}", "value": c})

    return dcc.Checklist(
        id="series-checklist",
        options=options,
        value=valid_defaults,
        style={"maxHeight": "400px", "overflowY": "auto", "fontSize": "12px"},
        labelStyle={"display": "block", "marginBottom": "4px"},
    )


@app.callback(
    Output("main-chart", "figure"),
    Output("summary-panel", "children"),
    Output("metadata-panel", "children"),
    Output("methodology-panel", "children"),
    Output("data-table-container", "children"),
    Input("category-dropdown", "value"),
    Input("series-checklist", "value"),
    prevent_initial_call=True,
)
def update_chart(category, selected_series):
    empty_fig = go.Figure()
    empty_fig.update_layout(
        template="plotly_dark", paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
        annotations=[{"text": "Select series to display", "showarrow": False, "font": {"size": 16, "color": "#888"}}],
    )

    if not category or not selected_series:
        return empty_fig, "", "", "", ""

    cat_info = CATEGORIES[category]
    filepath = CHOPPED_DIR / cat_info["file"]

    if not filepath.exists():
        return empty_fig, html.P("Data file not found"), "", "", ""

    df, col_meta = load_chopped_csv(filepath)

    # Chart
    fig = go.Figure()
    for col in selected_series:
        if col in df.columns:
            series = df[["date", col]].dropna()
            desc = col_meta.get(col, {}).get("description", col)
            label = desc if len(desc) <= 50 else col
            fig.add_trace(go.Scatter(x=series["date"], y=series[col], name=label, mode="lines"))

    fig.update_layout(
        title=cat_info["title"],
        template="plotly_dark", paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
        legend={"orientation": "h", "y": -0.15},
        margin={"l": 50, "r": 20, "t": 50, "b": 80},
        hovermode="x unified",
    )

    # Latest values
    summary_parts = []
    for col in selected_series:
        if col in df.columns:
            latest = df[["date", col]].dropna()
            if len(latest) > 0:
                last_row = latest.iloc[-1]
                desc = col_meta.get(col, {}).get("description", col)
                label = desc if len(desc) <= 30 else col
                summary_parts.append(html.Span(f"{label}: {last_row[col]:.2f}  ", style={"marginRight": "20px"}))

    summary = html.Div([html.Strong("Latest values: ", style={"color": "#00d4ff"}), *summary_parts])

    # Metadata
    meta_parts = []
    for col in selected_series[:5]:
        info = col_meta.get(col, {})
        reg_info = registry.get("series", {}).get(col, {}) or registry.get("series", {}).get(col.upper(), {})
        desc = info.get("description", col)
        source = reg_info.get("source", "")
        units = reg_info.get("units", "")
        tier = reg_info.get("quality_tier", "")
        detail = f"{col}: {desc}"
        if source:
            detail += f" [{source}]"
        if units:
            detail += f" ({units})"
        if tier:
            detail += f" Tier {tier}"
        meta_parts.append(html.P(detail))

    # Methodology
    research_ids = cat_info.get("research", [])
    research = load_research(research_ids)
    method_parts = []
    for m in research.get("methodology", []):
        method_parts.append(html.P(m, style={"marginBottom": "10px"}))
    if research.get("findings"):
        method_parts.append(html.H4("Key Findings", style={"color": "#00d4ff", "marginTop": "15px"}))
        for f in research["findings"]:
            method_parts.append(html.Li(f))

    # Data table
    table_df = df[["date"] + [c for c in selected_series if c in df.columns]].copy()
    table_df["date"] = table_df["date"].dt.strftime("%Y-%m")
    table_df = table_df.tail(60).round(4)

    _current_data["df"] = table_df
    _current_data["category"] = category

    table = dash_table.DataTable(
        data=table_df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in table_df.columns],
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": "#0f3460", "color": "#e0e0e0", "fontWeight": "bold"},
        style_cell={"backgroundColor": "#16213e", "color": "#e0e0e0", "border": "1px solid #333", "padding": "6px", "fontSize": "12px"},
        page_size=20,
        sort_action="native",
    )

    return fig, summary, html.Div(meta_parts), html.Div(method_parts), table


@app.callback(
    Output("download-csv", "data"),
    Input("download-btn", "n_clicks"),
    prevent_initial_call=True,
)
def download_data(n_clicks):
    if not n_clicks or "df" not in _current_data:
        return None
    cat = _current_data.get("category", "data").lower().replace(" ", "_")
    return dcc.send_data_frame(_current_data["df"].to_csv, f"starcruiser_{cat}.csv", index=False)


if __name__ == "__main__":
    print("StarCruiser Dashboard — Startup Validation")
    print("=" * 50)
    issues = startup_validation()
    csv_count = len(list(CHOPPED_DIR.glob("*.csv"))) if CHOPPED_DIR.exists() else 0
    series_count = registry.get("total_series", 0)
    print(f"  Chopped CSVs: {csv_count}")
    print(f"  Series in registry: {series_count}")
    print(f"  Categories: {len(CATEGORIES)}")
    if issues:
        for issue in issues:
            print(f"  {issue}")
    else:
        print("  All checks passed")
    print("=" * 50)
    print(f"Starting on http://localhost:8050")
    app.run(debug=False, port=8050)
