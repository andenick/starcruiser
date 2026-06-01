#!/usr/bin/env python3
"""
TREASURY MARKET ANALYSIS
=========================
Comprehensive treasury market analysis tools including:
1. Yield curve analysis and visualization
2. Term structure decomposition
3. Yield spread analysis (2s10s, 3mo10y)
4. Real yields and breakeven inflation
5. Term premium estimation
6. Fed policy rate analysis
7. Mortgage rate dynamics

Data Sources:
- FRED: Treasury yields, TIPS yields, breakeven inflation
- TIC: Foreign holdings (requires separate download)

Author: StarCruiser Project
Created: December 5, 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from scipy import interpolate
import json
import warnings

import os

DATA_ROOT = Path(os.environ.get("DATA_ROOT", "data"))

warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
SOURCE_DATA = DATA_ROOT / "API_MODULES/FRED/data"
OUTPUT_DIR = PROJECT_ROOT / "Outputs" / "TREASURY_ANALYSIS"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Treasury series definitions
TREASURY_SERIES = {
    # Nominal Treasury Yields
    'DGS1': {'name': '1-Year Treasury', 'maturity_months': 12, 'type': 'nominal'},
    'DGS2': {'name': '2-Year Treasury', 'maturity_months': 24, 'type': 'nominal'},
    'DGS5': {'name': '5-Year Treasury', 'maturity_months': 60, 'type': 'nominal'},
    'DGS7': {'name': '7-Year Treasury', 'maturity_months': 84, 'type': 'nominal'},
    'DGS10': {'name': '10-Year Treasury', 'maturity_months': 120, 'type': 'nominal'},
    'DGS20': {'name': '20-Year Treasury', 'maturity_months': 240, 'type': 'nominal'},
    'DGS30': {'name': '30-Year Treasury', 'maturity_months': 360, 'type': 'nominal'},

    # Short-term rates
    'DTB3': {'name': '3-Month T-Bill', 'maturity_months': 3, 'type': 'nominal'},
    'DTB6': {'name': '6-Month T-Bill', 'maturity_months': 6, 'type': 'nominal'},
    'DGS3MO': {'name': '3-Month Treasury', 'maturity_months': 3, 'type': 'nominal'},

    # TIPS Yields (Real)
    'DFII5': {'name': '5-Year TIPS', 'maturity_months': 60, 'type': 'real'},
    'DFII7': {'name': '7-Year TIPS', 'maturity_months': 84, 'type': 'real'},
    'DFII10': {'name': '10-Year TIPS', 'maturity_months': 120, 'type': 'real'},
    'DFII20': {'name': '20-Year TIPS', 'maturity_months': 240, 'type': 'real'},
    'DFII30': {'name': '30-Year TIPS', 'maturity_months': 360, 'type': 'real'},

    # Weekly TIPS
    'WFII5': {'name': '5-Year TIPS (Weekly)', 'maturity_months': 60, 'type': 'real'},
    'WFII10': {'name': '10-Year TIPS (Weekly)', 'maturity_months': 120, 'type': 'real'},

    # Breakeven Inflation
    'T5YIE': {'name': '5-Year Breakeven', 'maturity_months': 60, 'type': 'breakeven'},
    'T10YIE': {'name': '10-Year Breakeven', 'maturity_months': 120, 'type': 'breakeven'},
    'T5YIFR': {'name': '5Y5Y Forward Inflation', 'maturity_months': 120, 'type': 'forward'},

    # Policy rates
    'DFF': {'name': 'Fed Funds Effective', 'maturity_months': 0, 'type': 'policy'},
    'FEDFUNDS': {'name': 'Fed Funds Rate', 'maturity_months': 0, 'type': 'policy'},
    'DPRIME': {'name': 'Prime Rate', 'maturity_months': 0, 'type': 'policy'},

    # Mortgage rates
    'MORTGAGE30US': {'name': '30-Year Mortgage', 'maturity_months': 360, 'type': 'mortgage'},
    'MORTGAGE15US': {'name': '15-Year Mortgage', 'maturity_months': 180, 'type': 'mortgage'},

    # Term Premium
    'THREEFYTP3': {'name': '3-Month Term Premium', 'maturity_months': 3, 'type': 'term_premium'},
    'THREEFYTP6': {'name': '6-Month Term Premium', 'maturity_months': 6, 'type': 'term_premium'},
}

# Maturities for yield curve (in years)
YIELD_CURVE_MATURITIES = [0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]

# =============================================================================
# DATA LOADING
# =============================================================================

def load_treasury_data():
    """Load all treasury data from FRED files."""
    rates_file = SOURCE_DATA / "[2025.09.29] fred_interest_rates_20250929.csv"

    if not rates_file.exists():
        print(f"Error: Treasury data file not found at {rates_file}")
        return None

    df = pd.read_csv(rates_file)
    df['date'] = pd.to_datetime(df['date'])
    df['value'] = pd.to_numeric(df['value'], errors='coerce')

    print(f"Loaded {len(df):,} treasury observations")
    print(f"Series: {sorted(df['series_id'].unique())}")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    return df

# =============================================================================
# YIELD CURVE ANALYSIS
# =============================================================================

def build_yield_curve(df, date):
    """
    Build yield curve for a specific date.

    Returns yields for standard maturities, interpolating where necessary.
    """
    if isinstance(date, str):
        date = pd.to_datetime(date)

    # Get data for this date
    day_data = df[df['date'] == date].copy()

    if len(day_data) == 0:
        # Try nearest date
        closest = df['date'].unique()
        closest = closest[closest <= date]
        if len(closest) == 0:
            return None
        date = closest[-1]
        day_data = df[df['date'] == date].copy()

    # Map series to maturities
    maturity_yield = {}

    series_maturity = {
        'DTB3': 0.25, 'DGS3MO': 0.25,
        'DTB6': 0.5,
        'DGS1': 1,
        'DGS2': 2,
        'DGS5': 5,
        'DGS7': 7,
        'DGS10': 10,
        'DGS20': 20,
        'DGS30': 30,
    }

    for _, row in day_data.iterrows():
        series_id = row['series_id']
        if series_id in series_maturity and pd.notna(row['value']):
            maturity = series_maturity[series_id]
            maturity_yield[maturity] = row['value']

    if len(maturity_yield) < 3:
        return None

    # Sort by maturity
    maturities = sorted(maturity_yield.keys())
    yields = [maturity_yield[m] for m in maturities]

    return {
        'date': date,
        'maturities': maturities,
        'yields': yields,
        'data': maturity_yield
    }

def interpolate_yield_curve(curve_data, target_maturities=None):
    """
    Interpolate yield curve to standard maturities using cubic spline.
    """
    if curve_data is None:
        return None

    if target_maturities is None:
        target_maturities = YIELD_CURVE_MATURITIES

    maturities = np.array(curve_data['maturities'])
    yields = np.array(curve_data['yields'])

    # Filter target maturities to be within range
    min_mat = maturities.min()
    max_mat = maturities.max()
    target = [m for m in target_maturities if min_mat <= m <= max_mat]

    if len(target) < 2:
        return None

    # Cubic spline interpolation
    spline = interpolate.CubicSpline(maturities, yields)
    interp_yields = spline(target)

    return {
        'date': curve_data['date'],
        'maturities': target,
        'yields': interp_yields.tolist(),
        'original_data': curve_data['data']
    }

def calculate_yield_spreads(df):
    """
    Calculate key yield spreads:
    - 2s10s: 10-year minus 2-year (classic recession indicator)
    - 3mo10y: 10-year minus 3-month (Fed's preferred indicator)
    - 2s30s: 30-year minus 2-year
    - Mortgage spread: 30-year mortgage minus 10-year treasury
    """
    pivot = df.pivot_table(index='date', columns='series_id', values='value')

    result = pd.DataFrame(index=pivot.index)

    # 2s10s spread
    if 'DGS2' in pivot.columns and 'DGS10' in pivot.columns:
        result['spread_2s10s'] = pivot['DGS10'] - pivot['DGS2']

    # 3mo10y spread
    if 'DGS10' in pivot.columns:
        if 'DTB3' in pivot.columns:
            result['spread_3mo10y'] = pivot['DGS10'] - pivot['DTB3']
        elif 'DGS3MO' in pivot.columns:
            result['spread_3mo10y'] = pivot['DGS10'] - pivot['DGS3MO']

    # 2s30s spread
    if 'DGS2' in pivot.columns and 'DGS30' in pivot.columns:
        result['spread_2s30s'] = pivot['DGS30'] - pivot['DGS2']

    # 5s30s spread
    if 'DGS5' in pivot.columns and 'DGS30' in pivot.columns:
        result['spread_5s30s'] = pivot['DGS30'] - pivot['DGS5']

    # Mortgage spread over 10-year
    if 'MORTGAGE30US' in pivot.columns and 'DGS10' in pivot.columns:
        result['mortgage_spread'] = pivot['MORTGAGE30US'] - pivot['DGS10']

    # Real yield spread (10-year TIPS vs nominal)
    if 'DFII10' in pivot.columns and 'DGS10' in pivot.columns:
        result['breakeven_10y'] = pivot['DGS10'] - pivot['DFII10']

    # Fed funds vs 2-year (policy expectation)
    if 'DFF' in pivot.columns and 'DGS2' in pivot.columns:
        result['fed_vs_2y'] = pivot['DGS2'] - pivot['DFF']

    return result.reset_index()

def analyze_yield_curve_shape(curve_data):
    """
    Analyze yield curve shape:
    - Normal: upward sloping (short < long)
    - Flat: minimal slope
    - Inverted: downward sloping (short > long)
    - Humped: rises then falls
    """
    if curve_data is None or len(curve_data['maturities']) < 3:
        return {'shape': 'insufficient_data'}

    maturities = np.array(curve_data['maturities'])
    yields = np.array(curve_data['yields'])

    # Calculate slopes at different points
    short_idx = np.argmin(np.abs(maturities - 2))  # 2-year
    mid_idx = np.argmin(np.abs(maturities - 5))    # 5-year
    long_idx = np.argmin(np.abs(maturities - 10))  # 10-year

    short_yield = yields[short_idx] if short_idx < len(yields) else yields[0]
    mid_yield = yields[mid_idx] if mid_idx < len(yields) else yields[len(yields)//2]
    long_yield = yields[long_idx] if long_idx < len(yields) else yields[-1]

    front_slope = mid_yield - short_yield
    back_slope = long_yield - mid_yield
    total_slope = long_yield - short_yield

    # Determine shape
    if total_slope < -0.25:
        if front_slope < 0 and back_slope < 0:
            shape = 'inverted'
        else:
            shape = 'partially_inverted'
    elif total_slope > 0.5:
        if front_slope > back_slope:
            shape = 'steep_front'
        elif back_slope > front_slope:
            shape = 'steep_back'
        else:
            shape = 'normal'
    elif abs(total_slope) <= 0.25:
        shape = 'flat'
    else:
        if mid_yield > max(short_yield, long_yield):
            shape = 'humped'
        elif mid_yield < min(short_yield, long_yield):
            shape = 'u_shaped'
        else:
            shape = 'normal'

    return {
        'shape': shape,
        'total_slope': total_slope,
        'front_slope': front_slope,
        'back_slope': back_slope,
        'short_yield': short_yield,
        'mid_yield': mid_yield,
        'long_yield': long_yield,
    }

# =============================================================================
# REAL YIELDS AND INFLATION EXPECTATIONS
# =============================================================================

def calculate_real_yields(df):
    """
    Calculate real yields and decompose nominal yields:
    Nominal Yield = Real Yield + Breakeven Inflation + Term Premium
    """
    pivot = df.pivot_table(index='date', columns='series_id', values='value')

    result = pd.DataFrame(index=pivot.index)

    # 5-year decomposition
    if 'DGS5' in pivot.columns:
        result['nominal_5y'] = pivot['DGS5']
    if 'DFII5' in pivot.columns:
        result['real_5y'] = pivot['DFII5']
    if 'T5YIE' in pivot.columns:
        result['breakeven_5y'] = pivot['T5YIE']

    # 10-year decomposition
    if 'DGS10' in pivot.columns:
        result['nominal_10y'] = pivot['DGS10']
    if 'DFII10' in pivot.columns:
        result['real_10y'] = pivot['DFII10']
    if 'T10YIE' in pivot.columns:
        result['breakeven_10y'] = pivot['T10YIE']

    # 5y5y forward inflation
    if 'T5YIFR' in pivot.columns:
        result['forward_5y5y'] = pivot['T5YIFR']

    # Calculate implied term premium (rough estimate)
    # Term premium = Nominal - Real - Breakeven - Expected short rates
    # We approximate with: Nominal - Real - Breakeven
    if 'nominal_10y' in result.columns and 'real_10y' in result.columns and 'breakeven_10y' in result.columns:
        result['implied_residual_10y'] = result['nominal_10y'] - result['real_10y'] - result['breakeven_10y']

    return result.reset_index()

def analyze_inflation_expectations(df):
    """
    Analyze market-based inflation expectations.
    """
    pivot = df.pivot_table(index='date', columns='series_id', values='value')

    result = pd.DataFrame(index=pivot.index)

    # Direct breakeven measures
    for series_id in ['T5YIE', 'T10YIE', 'T5YIFR']:
        if series_id in pivot.columns:
            result[series_id] = pivot[series_id]

    # Calculate breakevens from spreads
    if 'DGS5' in pivot.columns and 'DFII5' in pivot.columns:
        result['calc_breakeven_5y'] = pivot['DGS5'] - pivot['DFII5']

    if 'DGS10' in pivot.columns and 'DFII10' in pivot.columns:
        result['calc_breakeven_10y'] = pivot['DGS10'] - pivot['DFII10']

    return result.reset_index()

# =============================================================================
# POLICY ANALYSIS
# =============================================================================

def analyze_fed_policy(df):
    """
    Analyze Fed policy stance and expectations.
    """
    pivot = df.pivot_table(index='date', columns='series_id', values='value')

    result = pd.DataFrame(index=pivot.index)

    # Fed funds rate
    if 'DFF' in pivot.columns:
        result['fed_funds'] = pivot['DFF']
    elif 'FEDFUNDS' in pivot.columns:
        result['fed_funds'] = pivot['FEDFUNDS']

    # Prime rate
    if 'DPRIME' in pivot.columns:
        result['prime_rate'] = pivot['DPRIME']

    # Short-term treasury
    if 'DTB3' in pivot.columns:
        result['tbill_3m'] = pivot['DTB3']

    # Policy stance indicators
    if 'fed_funds' in result.columns:
        # Rate of change
        result['fed_funds_change_1m'] = result['fed_funds'].diff(periods=20)  # ~1 month
        result['fed_funds_change_3m'] = result['fed_funds'].diff(periods=63)  # ~3 months

        # Is Fed hiking, cutting, or on hold?
        result['policy_direction'] = np.where(
            result['fed_funds_change_3m'] > 0.25, 'hiking',
            np.where(result['fed_funds_change_3m'] < -0.25, 'cutting', 'hold')
        )

    # Market expectations (2-year vs fed funds)
    if 'fed_funds' in result.columns and 'DGS2' in pivot.columns:
        result['market_vs_fed'] = pivot['DGS2'] - result['fed_funds']
        # Positive = market expects higher rates, Negative = market expects cuts

    return result.reset_index()

# =============================================================================
# MORTGAGE MARKET
# =============================================================================

def analyze_mortgage_rates(df):
    """
    Analyze mortgage rate dynamics.
    """
    pivot = df.pivot_table(index='date', columns='series_id', values='value')

    result = pd.DataFrame(index=pivot.index)

    # Mortgage rates
    if 'MORTGAGE30US' in pivot.columns:
        result['mortgage_30y'] = pivot['MORTGAGE30US']

    if 'MORTGAGE15US' in pivot.columns:
        result['mortgage_15y'] = pivot['MORTGAGE15US']

    # 10-year treasury (key driver)
    if 'DGS10' in pivot.columns:
        result['treasury_10y'] = pivot['DGS10']

    # Mortgage spread
    if 'mortgage_30y' in result.columns and 'treasury_10y' in result.columns:
        result['mortgage_spread'] = result['mortgage_30y'] - result['treasury_10y']

        # Historical average spread is ~1.7%
        result['spread_vs_avg'] = result['mortgage_spread'] - 1.7

    # 30-15 year spread (term premium in mortgages)
    if 'mortgage_30y' in result.columns and 'mortgage_15y' in result.columns:
        result['mortgage_term_spread'] = result['mortgage_30y'] - result['mortgage_15y']

    return result.reset_index()

# =============================================================================
# HISTORICAL ANALYSIS
# =============================================================================

def get_recession_periods():
    """NBER recession periods."""
    return [
        {'start': '2001-03-01', 'end': '2001-11-01', 'name': 'Dot-com'},
        {'start': '2007-12-01', 'end': '2009-06-01', 'name': 'Great Recession'},
        {'start': '2020-02-01', 'end': '2020-04-01', 'name': 'COVID-19'},
    ]

def analyze_yield_curve_inversions(spreads_df):
    """
    Identify yield curve inversions (recession predictors).
    """
    inversions = []

    for spread_col in ['spread_2s10s', 'spread_3mo10y']:
        if spread_col not in spreads_df.columns:
            continue

        # Find periods where spread is negative
        spreads_df['inverted'] = spreads_df[spread_col] < 0

        # Find inversion start and end dates
        spreads_df['inversion_start'] = (spreads_df['inverted'] & ~spreads_df['inverted'].shift(1).fillna(False))
        spreads_df['inversion_end'] = (~spreads_df['inverted'] & spreads_df['inverted'].shift(1).fillna(False))

        starts = spreads_df[spreads_df['inversion_start']]['date'].tolist()
        ends = spreads_df[spreads_df['inversion_end']]['date'].tolist()

        for i, start in enumerate(starts):
            end = ends[i] if i < len(ends) else spreads_df['date'].max()
            duration = (end - start).days
            min_spread = spreads_df[(spreads_df['date'] >= start) & (spreads_df['date'] <= end)][spread_col].min()

            inversions.append({
                'spread': spread_col,
                'start': start,
                'end': end,
                'duration_days': duration,
                'min_spread': min_spread
            })

    return inversions

# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_treasury_report(df):
    """Generate comprehensive treasury market report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    report = []
    report.append("=" * 80)
    report.append("TREASURY MARKET ANALYSIS REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Data through: {df['date'].max().strftime('%Y-%m-%d')}")
    report.append("")

    # Latest yield curve
    report.append("-" * 80)
    report.append("CURRENT YIELD CURVE")
    report.append("-" * 80)

    latest_date = df['date'].max()
    curve = build_yield_curve(df, latest_date)

    if curve:
        for mat, yld in zip(curve['maturities'], curve['yields']):
            if mat < 1:
                mat_str = f"{int(mat*12)}-month"
            else:
                mat_str = f"{int(mat)}-year"
            report.append(f"  {mat_str:12s}: {yld:.3f}%")

        # Analyze shape
        shape = analyze_yield_curve_shape(curve)
        report.append("")
        report.append(f"  Curve Shape: {shape['shape'].upper()}")
        report.append(f"  Total Slope (2y-10y): {shape['total_slope']:.2f}%")

    report.append("")

    # Key spreads
    report.append("-" * 80)
    report.append("KEY YIELD SPREADS")
    report.append("-" * 80)

    spreads = calculate_yield_spreads(df)
    latest_spreads = spreads.iloc[-1]

    spread_labels = {
        'spread_2s10s': '2s10s Spread (recession indicator)',
        'spread_3mo10y': '3mo10y Spread (Fed preferred)',
        'spread_2s30s': '2s30s Spread',
        'spread_5s30s': '5s30s Spread',
        'mortgage_spread': 'Mortgage Spread (30y vs 10y)',
        'breakeven_10y': '10y Breakeven Inflation',
        'fed_vs_2y': '2y vs Fed Funds (policy expectation)',
    }

    for col, label in spread_labels.items():
        if col in latest_spreads and pd.notna(latest_spreads[col]):
            report.append(f"  {label}: {latest_spreads[col]:.2f}%")

    report.append("")

    # Real yields
    report.append("-" * 80)
    report.append("REAL YIELDS AND INFLATION EXPECTATIONS")
    report.append("-" * 80)

    real_yields = calculate_real_yields(df)
    latest_real = real_yields.iloc[-1]

    real_labels = {
        'nominal_10y': '10y Nominal',
        'real_10y': '10y Real (TIPS)',
        'breakeven_10y': '10y Breakeven',
        'forward_5y5y': '5y5y Forward Inflation',
    }

    for col, label in real_labels.items():
        if col in latest_real and pd.notna(latest_real[col]):
            report.append(f"  {label}: {latest_real[col]:.2f}%")

    report.append("")

    # Fed policy
    report.append("-" * 80)
    report.append("FED POLICY ANALYSIS")
    report.append("-" * 80)

    policy = analyze_fed_policy(df)
    latest_policy = policy.iloc[-1]

    if 'fed_funds' in latest_policy and pd.notna(latest_policy['fed_funds']):
        report.append(f"  Fed Funds Effective: {latest_policy['fed_funds']:.2f}%")
    if 'prime_rate' in latest_policy and pd.notna(latest_policy['prime_rate']):
        report.append(f"  Prime Rate: {latest_policy['prime_rate']:.2f}%")
    if 'policy_direction' in latest_policy:
        report.append(f"  Policy Direction: {latest_policy['policy_direction'].upper()}")
    if 'market_vs_fed' in latest_policy and pd.notna(latest_policy['market_vs_fed']):
        direction = "higher" if latest_policy['market_vs_fed'] > 0 else "lower"
        report.append(f"  Market expects rates {direction}: {latest_policy['market_vs_fed']:+.2f}%")

    report.append("")

    # Mortgage analysis
    report.append("-" * 80)
    report.append("MORTGAGE MARKET")
    report.append("-" * 80)

    mortgages = analyze_mortgage_rates(df)
    latest_mort = mortgages.iloc[-1]

    if 'mortgage_30y' in latest_mort and pd.notna(latest_mort['mortgage_30y']):
        report.append(f"  30-Year Mortgage: {latest_mort['mortgage_30y']:.2f}%")
    if 'mortgage_15y' in latest_mort and pd.notna(latest_mort['mortgage_15y']):
        report.append(f"  15-Year Mortgage: {latest_mort['mortgage_15y']:.2f}%")
    if 'mortgage_spread' in latest_mort and pd.notna(latest_mort['mortgage_spread']):
        report.append(f"  Mortgage Spread: {latest_mort['mortgage_spread']:.2f}%")
    if 'spread_vs_avg' in latest_mort and pd.notna(latest_mort['spread_vs_avg']):
        status = "ELEVATED" if latest_mort['spread_vs_avg'] > 0.5 else "NORMAL"
        report.append(f"  Spread vs Average: {latest_mort['spread_vs_avg']:+.2f}% ({status})")

    report.append("")

    # Historical inversions
    report.append("-" * 80)
    report.append("YIELD CURVE INVERSION HISTORY")
    report.append("-" * 80)

    inversions = analyze_yield_curve_inversions(spreads)
    recent_inversions = [inv for inv in inversions if inv['start'] >= pd.Timestamp('2019-01-01')]

    if recent_inversions:
        for inv in recent_inversions:
            report.append(f"  {inv['spread']}: {inv['start'].strftime('%Y-%m-%d')} to {inv['end'].strftime('%Y-%m-%d')}")
            report.append(f"    Duration: {inv['duration_days']} days, Min spread: {inv['min_spread']:.2f}%")
    else:
        report.append("  No inversions since 2019")

    report.append("")
    report.append("=" * 80)
    report.append("END OF TREASURY MARKET REPORT")
    report.append("=" * 80)

    # Save report
    report_text = "\n".join(report)
    report_file = OUTPUT_DIR / f"[{timestamp}]_treasury_market_report.txt"
    with open(report_file, 'w') as f:
        f.write(report_text)

    print(f"\nReport saved to: {report_file}")
    print(report_text)

    return report_text

def save_treasury_data(df):
    """Save all treasury analysis data to CSV files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    # Yield spreads
    spreads = calculate_yield_spreads(df)
    spreads.to_csv(OUTPUT_DIR / f"[{timestamp}]_yield_spreads.csv", index=False)

    # Real yields
    real_yields = calculate_real_yields(df)
    real_yields.to_csv(OUTPUT_DIR / f"[{timestamp}]_real_yields.csv", index=False)

    # Policy analysis
    policy = analyze_fed_policy(df)
    policy.to_csv(OUTPUT_DIR / f"[{timestamp}]_fed_policy.csv", index=False)

    # Mortgage analysis
    mortgages = analyze_mortgage_rates(df)
    mortgages.to_csv(OUTPUT_DIR / f"[{timestamp}]_mortgage_analysis.csv", index=False)

    # Inflation expectations
    inflation_exp = analyze_inflation_expectations(df)
    inflation_exp.to_csv(OUTPUT_DIR / f"[{timestamp}]_inflation_expectations.csv", index=False)

    # Yield curve snapshots for key dates
    curves = []
    key_dates = df['date'].unique()[-30::5]  # Last 30 days, every 5 days

    for date in key_dates:
        curve = build_yield_curve(df, date)
        if curve:
            for mat, yld in zip(curve['maturities'], curve['yields']):
                curves.append({
                    'date': date,
                    'maturity_years': mat,
                    'yield': yld
                })

    if curves:
        pd.DataFrame(curves).to_csv(OUTPUT_DIR / f"[{timestamp}]_yield_curves.csv", index=False)

    print(f"\nAll treasury data saved to: {OUTPUT_DIR}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    print("=" * 60)
    print("TREASURY MARKET ANALYSIS")
    print("=" * 60)

    # Load data
    df = load_treasury_data()
    if df is None:
        return

    # Generate report
    generate_treasury_report(df)

    # Save analysis data
    save_treasury_data(df)

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
