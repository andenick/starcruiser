#!/usr/bin/env python3
"""
StarCruiser: Beveridge Curve and Labor Market Dynamics Analysis
================================================================

Implements:
1. Beveridge Curve - Job Openings vs Unemployment relationship
2. Labor Market Tightness (V/U ratio)
3. Labor Market Flows analysis (hires, quits, separations)
4. Hodrick-Prescott filter for trend/cycle decomposition
5. Rolling correlation analysis

Author: StarCruiser Project
Date: December 7, 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import warnings

import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = Path(os.environ.get("OUTPUT_ROOT", "outputs"))


warnings.filterwarnings("ignore")

# Paths
FRED_PATH = (PROJECT_ROOT / "Inputs/source/FRED")
OUTPUT_PATH = OUTPUT_ROOT / "LABOR_DYNAMICS"

# Create output directory
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)


def load_fred_data():
    """Load all relevant FRED data for labor market analysis."""
    print("\n" + "=" * 60)
    print("Loading FRED Data")
    print("=" * 60)

    # Load JOLTS data
    jolts_file = list(FRED_PATH.glob("fred_jolts_*.csv"))
    if jolts_file:
        jolts_df = pd.read_csv(jolts_file[0])
        jolts_df["date"] = pd.to_datetime(jolts_df["date"])
        print(f"  ✅ JOLTS: {len(jolts_df)} observations")
    else:
        print("  ❌ No JOLTS data found")
        return None

    # Load comprehensive employment data
    emp_file = list(FRED_PATH.glob("fred_comprehensive_employment_*.csv"))
    if emp_file:
        emp_df = pd.read_csv(emp_file[0])
        emp_df["date"] = pd.to_datetime(emp_df["date"])
        print(f"  ✅ Employment: {len(emp_df)} observations")
    else:
        print("  ❌ No comprehensive employment data found")
        return None

    return jolts_df, emp_df


def hp_filter(series, lamb=129600):
    """
    Hodrick-Prescott filter for trend/cycle decomposition.

    Lambda values:
    - Monthly data: 129600 (default)
    - Quarterly data: 1600
    - Annual data: 6.25
    """
    T = len(series)

    # Build the HP filter matrix
    a = np.zeros((T, T))

    # First observation
    a[0, 0] = 1 + lamb
    a[0, 1] = -2 * lamb
    a[0, 2] = lamb

    # Second observation
    a[1, 0] = -2 * lamb
    a[1, 1] = 1 + 5 * lamb
    a[1, 2] = -4 * lamb
    a[1, 3] = lamb

    # Interior observations
    for i in range(2, T - 2):
        a[i, i - 2] = lamb
        a[i, i - 1] = -4 * lamb
        a[i, i] = 1 + 6 * lamb
        a[i, i + 1] = -4 * lamb
        a[i, i + 2] = lamb

    # Second to last observation
    a[T - 2, T - 4] = lamb
    a[T - 2, T - 3] = -4 * lamb
    a[T - 2, T - 2] = 1 + 5 * lamb
    a[T - 2, T - 1] = -2 * lamb

    # Last observation
    a[T - 1, T - 3] = lamb
    a[T - 1, T - 2] = -2 * lamb
    a[T - 1, T - 1] = 1 + lamb

    # Solve for trend
    trend = np.linalg.solve(a, series)
    cycle = series - trend

    return trend, cycle


def build_beveridge_data(jolts_df, emp_df):
    """Build Beveridge curve dataset by merging JOLTS and unemployment data."""
    print("\n" + "=" * 60)
    print("Building Beveridge Curve Data")
    print("=" * 60)

    # Extract job openings rate
    job_openings = jolts_df[jolts_df["series_id"] == "JTSJOR"][["date", "value"]].copy()
    job_openings.columns = ["date", "vacancy_rate"]
    job_openings = job_openings.dropna()

    # Extract unemployment rate
    unemployment = emp_df[emp_df["series_id"] == "UNRATE"][["date", "value"]].copy()
    unemployment.columns = ["date", "unemployment_rate"]
    unemployment = unemployment.dropna()

    # Merge on date
    beveridge = pd.merge(job_openings, unemployment, on="date", how="inner")
    beveridge = beveridge.sort_values("date").reset_index(drop=True)

    # Calculate labor market tightness (V/U ratio)
    beveridge["vu_ratio"] = beveridge["vacancy_rate"] / beveridge["unemployment_rate"]

    # Add year and quarter for coloring
    beveridge["year"] = beveridge["date"].dt.year
    beveridge["quarter"] = beveridge["date"].dt.quarter
    beveridge["year_quarter"] = (
        beveridge["year"].astype(str) + "Q" + beveridge["quarter"].astype(str)
    )

    # Add recession indicator (simplified - key recessions)
    beveridge["recession"] = False
    # COVID recession
    beveridge.loc[
        (beveridge["date"] >= "2020-02-01") & (beveridge["date"] <= "2020-04-30"),
        "recession",
    ] = True
    # 2008-2009 recession
    beveridge.loc[
        (beveridge["date"] >= "2007-12-01") & (beveridge["date"] <= "2009-06-30"),
        "recession",
    ] = True

    print(f"  ✅ Beveridge data: {len(beveridge)} monthly observations")
    print(
        f"     Date range: {beveridge['date'].min().strftime('%Y-%m')} to {beveridge['date'].max().strftime('%Y-%m')}"
    )
    print(f"     Current V/U ratio: {beveridge['vu_ratio'].iloc[-1]:.2f}")
    print(f"     Current vacancy rate: {beveridge['vacancy_rate'].iloc[-1]:.1f}%")
    print(
        f"     Current unemployment rate: {beveridge['unemployment_rate'].iloc[-1]:.1f}%"
    )

    return beveridge


def calculate_labor_flows(jolts_df):
    """Calculate labor market flow rates and dynamics."""
    print("\n" + "=" * 60)
    print("Calculating Labor Market Flows")
    print("=" * 60)

    # Pivot JOLTS data to wide format
    flows = jolts_df.pivot_table(
        index="date", columns="series_id", values="value", aggfunc="first"
    )
    flows = flows.reset_index()

    # Rename columns for clarity
    rename_map = {
        "JTSJOL": "job_openings_level",
        "JTSJOR": "job_openings_rate",
        "JTSHIL": "hires_level",
        "JTSHIR": "hires_rate",
        "JTSTSL": "separations_level",
        "JTSTSR": "separations_rate",
        "JTSQUL": "quits_level",
        "JTSQUR": "quits_rate",
        "JTSLDL": "layoffs_level",
        "JTSLDR": "layoffs_rate",
    }
    flows = flows.rename(columns=rename_map)

    # Calculate net employment change
    if "hires_level" in flows.columns and "separations_level" in flows.columns:
        flows["net_employment_change"] = (
            flows["hires_level"] - flows["separations_level"]
        )

    # Calculate job-to-job transition proxy (quits as indicator)
    if "quits_rate" in flows.columns and "hires_rate" in flows.columns:
        flows["quits_to_hires_ratio"] = flows["quits_rate"] / flows["hires_rate"]

    # Calculate voluntary vs involuntary separation ratio
    if "quits_level" in flows.columns and "layoffs_level" in flows.columns:
        flows["voluntary_separation_ratio"] = flows["quits_level"] / (
            flows["quits_level"] + flows["layoffs_level"]
        )

    flows = flows.dropna(subset=["job_openings_rate", "hires_rate"])

    print(f"  ✅ Labor flows: {len(flows)} monthly observations")
    print(f"     Latest hires rate: {flows['hires_rate'].iloc[-1]:.1f}%")
    print(f"     Latest quits rate: {flows['quits_rate'].iloc[-1]:.1f}%")
    print(f"     Latest layoffs rate: {flows['layoffs_rate'].iloc[-1]:.1f}%")

    return flows


def decompose_employment_trends(emp_df):
    """Apply HP filter to decompose employment trends."""
    print("\n" + "=" * 60)
    print("Decomposing Employment Trends (HP Filter)")
    print("=" * 60)

    results = []

    series_to_decompose = ["UNRATE", "EMRATIO", "CIVPART", "PAYEMS"]

    for series_id in series_to_decompose:
        series_data = emp_df[emp_df["series_id"] == series_id].copy()
        series_data = series_data.sort_values("date").dropna(subset=["value"])

        if len(series_data) < 24:  # Need at least 24 months
            print(f"  ⚠️  {series_id}: Not enough data ({len(series_data)} obs)")
            continue

        # Apply HP filter
        values = series_data["value"].values
        trend, cycle = hp_filter(values)

        series_data["trend"] = trend
        series_data["cycle"] = cycle
        series_data["cycle_pct"] = (cycle / trend) * 100  # As percentage of trend

        results.append(series_data)

        print(f"  ✅ {series_id}: Decomposed {len(series_data)} observations")
        print(
            f"      Current cycle component: {cycle[-1]:.3f} ({series_data['cycle_pct'].iloc[-1]:.2f}% of trend)"
        )

    if results:
        combined = pd.concat(results, ignore_index=True)
        return combined

    return None


def calculate_correlations(emp_df, jolts_df, window=24):
    """Calculate rolling correlations between labor market indicators."""
    print("\n" + "=" * 60)
    print(f"Calculating Rolling Correlations ({window}-month window)")
    print("=" * 60)

    # Build wide dataset
    # Get unemployment
    unrate = emp_df[emp_df["series_id"] == "UNRATE"][["date", "value"]].copy()
    unrate.columns = ["date", "UNRATE"]

    # Get employment-population ratio
    emratio = emp_df[emp_df["series_id"] == "EMRATIO"][["date", "value"]].copy()
    emratio.columns = ["date", "EMRATIO"]

    # Get initial claims
    claims = emp_df[emp_df["series_id"] == "ICSA"][["date", "value"]].copy()
    claims.columns = ["date", "ICSA"]
    # Aggregate weekly claims to monthly
    claims["month"] = claims["date"].dt.to_period("M")
    claims = claims.groupby("month")["ICSA"].mean().reset_index()
    claims["date"] = claims["month"].dt.to_timestamp()
    claims = claims[["date", "ICSA"]]

    # Get job openings
    openings = jolts_df[jolts_df["series_id"] == "JTSJOR"][["date", "value"]].copy()
    openings.columns = ["date", "JTSJOR"]

    # Get quits rate
    quits = jolts_df[jolts_df["series_id"] == "JTSQUR"][["date", "value"]].copy()
    quits.columns = ["date", "JTSQUR"]

    # Merge all
    merged = unrate
    for df in [emratio, claims, openings, quits]:
        merged = pd.merge(merged, df, on="date", how="outer")

    merged = merged.sort_values("date").dropna()

    if len(merged) < window:
        print(f"  ⚠️  Not enough overlapping data ({len(merged)} obs)")
        return None

    # Calculate rolling correlations
    corr_results = []

    for i in range(window, len(merged)):
        window_data = merged.iloc[i - window : i]
        date = merged.iloc[i]["date"]

        # Correlations with unemployment
        corr_row = {"date": date}
        for col in ["EMRATIO", "ICSA", "JTSJOR", "JTSQUR"]:
            if col in window_data.columns:
                corr = window_data["UNRATE"].corr(window_data[col])
                corr_row[f"UNRATE_vs_{col}"] = corr

        corr_results.append(corr_row)

    corr_df = pd.DataFrame(corr_results)

    print(f"  ✅ Rolling correlations: {len(corr_df)} observations")
    print(f"     Latest UNRATE vs JTSJOR: {corr_df['UNRATE_vs_JTSJOR'].iloc[-1]:.3f}")
    print(f"     Latest UNRATE vs JTSQUR: {corr_df['UNRATE_vs_JTSQUR'].iloc[-1]:.3f}")

    return corr_df


def generate_labor_dynamics_report(beveridge, flows, decomposed, correlations):
    """Generate comprehensive labor dynamics report."""
    print("\n" + "=" * 60)
    print("Generating Labor Dynamics Report")
    print("=" * 60)

    report = []
    report.append("# StarCruiser Labor Market Dynamics Report")
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Beveridge Curve Analysis
    report.append("## 1. Beveridge Curve Analysis\n")

    latest = beveridge.iloc[-1]
    report.append(f"**Latest Data**: {latest['date'].strftime('%Y-%m')}\n")
    report.append(f"- Vacancy Rate: {latest['vacancy_rate']:.1f}%")
    report.append(f"- Unemployment Rate: {latest['unemployment_rate']:.1f}%")
    report.append(f"- V/U Ratio: {latest['vu_ratio']:.2f}")

    # Historical context
    avg_vu = beveridge["vu_ratio"].mean()
    report.append(f"\n**Historical Context**:")
    report.append(f"- Average V/U Ratio (2001-present): {avg_vu:.2f}")
    report.append(
        f"- Current vs Average: {((latest['vu_ratio'] / avg_vu) - 1) * 100:+.1f}%"
    )

    # Labor market conditions
    if latest["vu_ratio"] > 1.0:
        report.append(
            f"\n**Labor Market Condition**: TIGHT (more openings than unemployed)"
        )
    elif latest["vu_ratio"] > 0.5:
        report.append(f"\n**Labor Market Condition**: BALANCED")
    else:
        report.append(
            f"\n**Labor Market Condition**: SLACK (more unemployed than openings)"
        )

    # Flows Analysis
    report.append("\n## 2. Labor Market Flows\n")

    flows_latest = flows.iloc[-1]
    report.append(f"**Latest Flows** ({flows_latest['date'].strftime('%Y-%m')}):\n")
    report.append(f"- Hires Rate: {flows_latest['hires_rate']:.1f}%")
    report.append(f"- Separations Rate: {flows_latest['separations_rate']:.1f}%")
    report.append(f"- Quits Rate: {flows_latest['quits_rate']:.1f}%")
    report.append(f"- Layoffs Rate: {flows_latest['layoffs_rate']:.1f}%")

    if "voluntary_separation_ratio" in flows_latest:
        report.append(
            f"- Voluntary Separation Ratio: {flows_latest['voluntary_separation_ratio']:.1%}"
        )

    # Trend/Cycle Decomposition
    if decomposed is not None:
        report.append("\n## 3. Employment Trend/Cycle Decomposition\n")
        report.append("Using Hodrick-Prescott filter (λ=129600 for monthly data)\n")

        for series in decomposed["series_id"].unique():
            series_data = decomposed[decomposed["series_id"] == series].iloc[-1]
            report.append(f"**{series}**:")
            report.append(f"  - Current value: {series_data['value']:.2f}")
            report.append(f"  - Trend: {series_data['trend']:.2f}")
            report.append(
                f"  - Cycle: {series_data['cycle']:.3f} ({series_data['cycle_pct']:.2f}% of trend)"
            )

    # Correlations
    if correlations is not None:
        report.append("\n## 4. Rolling Correlation Analysis (24-month window)\n")

        latest_corr = correlations.iloc[-1]
        report.append(
            f"**Latest Correlations** ({latest_corr['date'].strftime('%Y-%m')}):\n"
        )
        report.append(
            f"- Unemployment vs Job Openings: {latest_corr['UNRATE_vs_JTSJOR']:.3f}"
        )
        report.append(
            f"- Unemployment vs Quits Rate: {latest_corr['UNRATE_vs_JTSQUR']:.3f}"
        )
        report.append(
            f"- Unemployment vs Initial Claims: {latest_corr['UNRATE_vs_ICSA']:.3f}"
        )

    # Save report
    report_text = "\n".join(report)
    report_file = OUTPUT_PATH / "LABOR_DYNAMICS_REPORT.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"  ✅ Report saved to: {report_file}")

    return report_text


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("  StarCruiser: Labor Market Dynamics Analysis")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    # Load data
    result = load_fred_data()
    if result is None:
        print("  ❌ Failed to load data")
        return None

    jolts_df, emp_df = result

    # Build Beveridge curve data
    beveridge = build_beveridge_data(jolts_df, emp_df)
    beveridge.to_csv(OUTPUT_PATH / "beveridge_curve_data.csv", index=False)
    print(f"  Saved: beveridge_curve_data.csv")

    # Calculate labor flows
    flows = calculate_labor_flows(jolts_df)
    flows.to_csv(OUTPUT_PATH / "labor_market_flows.csv", index=False)
    print(f"  Saved: labor_market_flows.csv")

    # Decompose employment trends
    decomposed = decompose_employment_trends(emp_df)
    if decomposed is not None:
        decomposed.to_csv(OUTPUT_PATH / "employment_hp_decomposition.csv", index=False)
        print(f"  Saved: employment_hp_decomposition.csv")

    # Calculate correlations
    correlations = calculate_correlations(emp_df, jolts_df)
    if correlations is not None:
        correlations.to_csv(OUTPUT_PATH / "rolling_correlations.csv", index=False)
        print(f"  Saved: rolling_correlations.csv")

    # Generate report
    report = generate_labor_dynamics_report(beveridge, flows, decomposed, correlations)

    print("\n" + "=" * 60)
    print("  ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\n  Output location: {OUTPUT_PATH}")

    return {
        "beveridge": beveridge,
        "flows": flows,
        "decomposed": decomposed,
        "correlations": correlations,
    }


if __name__ == "__main__":
    result = main()
