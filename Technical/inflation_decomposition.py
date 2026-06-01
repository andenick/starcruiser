#!/usr/bin/env python3
"""
INFLATION DECOMPOSITION ANALYSIS
================================
Comprehensive inflation analysis with multiple decomposition methods:
1. Component decomposition (Energy, Food, Shelter, etc.)
2. CPI vs PCE comparison (substitution bias analysis)
3. Core vs Headline (volatile component extraction)
4. Trimmed mean and sticky price analysis
5. Year-over-year vs Month-over-month dynamics
6. Real-time vintage analysis (ALFRED)
7. Breakeven inflation extraction

Data Sources:
- FRED: CPI, PCE, PPI series
- BLS: Detailed CPI components
- Cleveland Fed: Trimmed Mean PCE
- Atlanta Fed: Sticky Price CPI

Author: StarCruiser Project
Created: December 5, 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
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
OUTPUT_DIR = PROJECT_ROOT / "Outputs" / "INFLATION_ANALYSIS"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Inflation series definitions
INFLATION_SERIES = {
    # Headline CPI
    'CPIAUCSL': {'name': 'CPI All Items', 'type': 'headline', 'measure': 'CPI'},
    'CPIAUCNS': {'name': 'CPI All Items (NSA)', 'type': 'headline', 'measure': 'CPI'},

    # Core CPI
    'CPILFESL': {'name': 'CPI Less Food & Energy', 'type': 'core', 'measure': 'CPI'},
    'CPIULFSL': {'name': 'CPI Less Food', 'type': 'core', 'measure': 'CPI'},

    # CPI Components
    'CPIENGSL': {'name': 'CPI Energy', 'type': 'component', 'measure': 'CPI', 'weight': 0.07},
    'CPIFABSL': {'name': 'CPI Food & Beverages', 'type': 'component', 'measure': 'CPI', 'weight': 0.14},
    'CPIHOSSL': {'name': 'CPI Housing', 'type': 'component', 'measure': 'CPI', 'weight': 0.44},
    'CPIMEDSL': {'name': 'CPI Medical', 'type': 'component', 'measure': 'CPI', 'weight': 0.09},
    'CPITRNSL': {'name': 'CPI Transportation', 'type': 'component', 'measure': 'CPI', 'weight': 0.07},

    # Sub-components
    'CUSR0000SA0L2': {'name': 'CPI All Items Less Shelter', 'type': 'sub', 'measure': 'CPI'},
    'CUSR0000SA0L5': {'name': 'CPI All Items Less Medical', 'type': 'sub', 'measure': 'CPI'},

    # PCE
    'PCEPI': {'name': 'PCE Price Index', 'type': 'headline', 'measure': 'PCE'},
    'PCEPILFE': {'name': 'PCE Less Food & Energy', 'type': 'core', 'measure': 'PCE'},

    # Alternative Measures
    'CORESTICKM159SFRBATL': {'name': 'Sticky Price CPI (Atlanta Fed)', 'type': 'alternative', 'measure': 'CPI'},
    'PCETRIM12M159SFRBDAL': {'name': 'Trimmed Mean PCE (Dallas Fed)', 'type': 'alternative', 'measure': 'PCE'},
    'JCXFE': {'name': 'Core PCE (Chain-Type)', 'type': 'core', 'measure': 'PCE'},

    # PPI
    'PPIACO': {'name': 'PPI All Commodities', 'type': 'headline', 'measure': 'PPI'},
    'PPIFGS': {'name': 'PPI Final Demand Goods', 'type': 'component', 'measure': 'PPI'},
    'PPIFIS': {'name': 'PPI Final Demand Services', 'type': 'component', 'measure': 'PPI'},
    'WPSFD49207': {'name': 'PPI Finished Goods', 'type': 'component', 'measure': 'PPI'},
    'WPSFD49502': {'name': 'PPI Finished Consumer Goods', 'type': 'component', 'measure': 'PPI'},
}

# Approximate CPI component weights (2024 basis)
CPI_WEIGHTS = {
    'Food': 0.137,
    'Energy': 0.066,
    'Shelter': 0.347,
    'Medical': 0.086,
    'Transportation': 0.158,
    'Education': 0.058,
    'Recreation': 0.055,
    'Apparel': 0.024,
    'Other': 0.069,
}

# =============================================================================
# DATA LOADING
# =============================================================================

def load_inflation_data():
    """Load all inflation data from FRED files."""
    inflation_file = SOURCE_DATA / "[2025.10.07] fred_inflation_20250929.csv"

    if not inflation_file.exists():
        print(f"Error: Inflation data file not found at {inflation_file}")
        return None

    df = pd.read_csv(inflation_file)
    df['date'] = pd.to_datetime(df['date'])
    df['value'] = pd.to_numeric(df['value'], errors='coerce')

    print(f"Loaded {len(df):,} inflation observations")
    print(f"Series: {df['series_id'].nunique()}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")

    return df

def load_interest_rates():
    """Load interest rate data for breakeven calculations."""
    rates_file = SOURCE_DATA / "[2025.09.29] fred_interest_rates_20250929.csv"

    if not rates_file.exists():
        print(f"Warning: Interest rates file not found")
        return None

    df = pd.read_csv(rates_file)
    df['date'] = pd.to_datetime(df['date'])
    df['value'] = pd.to_numeric(df['value'], errors='coerce')

    return df

# =============================================================================
# DECOMPOSITION METHODS
# =============================================================================

def calculate_inflation_rates(df, periods=[1, 3, 12]):
    """
    Calculate inflation rates at various horizons.

    Args:
        df: DataFrame with date, value, series_id columns
        periods: List of periods for rate calculation (1=MoM, 12=YoY)

    Returns:
        DataFrame with inflation rates added
    """
    result = df.copy()

    for series_id in result['series_id'].unique():
        mask = result['series_id'] == series_id
        series_data = result.loc[mask].sort_values('date')

        for period in periods:
            if period == 1:
                col_name = 'mom_pct'
            elif period == 3:
                col_name = 'qoq_pct'  # Quarter-over-quarter annualized
            elif period == 12:
                col_name = 'yoy_pct'
            else:
                col_name = f'p{period}_pct'

            # Calculate percentage change
            pct_change = series_data['value'].pct_change(periods=period) * 100

            # Annualize if not already annual
            if period < 12:
                pct_change = ((1 + pct_change/100) ** (12/period) - 1) * 100

            result.loc[mask, col_name] = pct_change.values

    return result

def decompose_headline_to_core(df):
    """
    Decompose headline inflation into core + volatile components.

    Headline CPI = Core CPI + Food Contribution + Energy Contribution
    """
    # Pivot to wide format
    pivot = df.pivot_table(index='date', columns='series_id', values='value')

    if 'CPIAUCSL' not in pivot.columns or 'CPILFESL' not in pivot.columns:
        print("Warning: Missing required series for core decomposition")
        return None

    result = pd.DataFrame(index=pivot.index)
    result['headline_cpi'] = pivot['CPIAUCSL']
    result['core_cpi'] = pivot['CPILFESL']

    # Calculate YoY rates
    result['headline_yoy'] = result['headline_cpi'].pct_change(12) * 100
    result['core_yoy'] = result['core_cpi'].pct_change(12) * 100

    # Food and Energy contribution (residual)
    result['food_energy_contribution'] = result['headline_yoy'] - result['core_yoy']

    # Add energy and food if available
    if 'CPIENGSL' in pivot.columns:
        result['energy_index'] = pivot['CPIENGSL']
        result['energy_yoy'] = result['energy_index'].pct_change(12) * 100
        # Approximate contribution using weight
        result['energy_contribution'] = result['energy_yoy'] * CPI_WEIGHTS['Energy']

    if 'CPIFABSL' in pivot.columns:
        result['food_index'] = pivot['CPIFABSL']
        result['food_yoy'] = result['food_index'].pct_change(12) * 100
        result['food_contribution'] = result['food_yoy'] * CPI_WEIGHTS['Food']

    return result.reset_index()

def decompose_cpi_components(df):
    """
    Full component decomposition of CPI.

    Returns contribution of each major component to headline inflation.
    """
    pivot = df.pivot_table(index='date', columns='series_id', values='value')

    components = {
        'Energy': ('CPIENGSL', CPI_WEIGHTS['Energy']),
        'Food': ('CPIFABSL', CPI_WEIGHTS['Food']),
        'Shelter': ('CPIHOSSL', CPI_WEIGHTS['Shelter']),
        'Medical': ('CPIMEDSL', CPI_WEIGHTS['Medical']),
        'Transportation': ('CPITRNSL', CPI_WEIGHTS['Transportation']),
    }

    result = pd.DataFrame(index=pivot.index)

    if 'CPIAUCSL' in pivot.columns:
        result['headline_cpi'] = pivot['CPIAUCSL']
        result['headline_yoy'] = result['headline_cpi'].pct_change(12) * 100

    for name, (series_id, weight) in components.items():
        if series_id in pivot.columns:
            result[f'{name.lower()}_index'] = pivot[series_id]
            result[f'{name.lower()}_yoy'] = result[f'{name.lower()}_index'].pct_change(12) * 100
            result[f'{name.lower()}_contribution'] = result[f'{name.lower()}_yoy'] * weight

    # Calculate residual (other components)
    contribution_cols = [c for c in result.columns if c.endswith('_contribution')]
    if contribution_cols and 'headline_yoy' in result.columns:
        result['explained_inflation'] = result[contribution_cols].sum(axis=1)
        result['residual'] = result['headline_yoy'] - result['explained_inflation']

    return result.reset_index()

def compare_cpi_pce(df):
    """
    Compare CPI vs PCE inflation measures.

    Key differences:
    1. Formula: CPI uses Laspeyres (fixed basket), PCE uses Fisher (chain-weighted)
    2. Scope: CPI is urban consumers, PCE is all consumers
    3. Weights: CPI uses consumer expenditure surveys, PCE uses business surveys
    4. Substitution: PCE captures substitution bias better
    """
    pivot = df.pivot_table(index='date', columns='series_id', values='value')

    result = pd.DataFrame(index=pivot.index)

    # Headline measures
    if 'CPIAUCSL' in pivot.columns:
        result['cpi_headline'] = pivot['CPIAUCSL']
        result['cpi_headline_yoy'] = result['cpi_headline'].pct_change(12) * 100

    if 'PCEPI' in pivot.columns:
        result['pce_headline'] = pivot['PCEPI']
        result['pce_headline_yoy'] = result['pce_headline'].pct_change(12) * 100

    # Core measures
    if 'CPILFESL' in pivot.columns:
        result['cpi_core'] = pivot['CPILFESL']
        result['cpi_core_yoy'] = result['cpi_core'].pct_change(12) * 100

    if 'PCEPILFE' in pivot.columns:
        result['pce_core'] = pivot['PCEPILFE']
        result['pce_core_yoy'] = result['pce_core'].pct_change(12) * 100

    # Calculate CPI-PCE wedge (substitution bias proxy)
    if 'cpi_headline_yoy' in result.columns and 'pce_headline_yoy' in result.columns:
        result['headline_wedge'] = result['cpi_headline_yoy'] - result['pce_headline_yoy']

    if 'cpi_core_yoy' in result.columns and 'pce_core_yoy' in result.columns:
        result['core_wedge'] = result['cpi_core_yoy'] - result['pce_core_yoy']

    return result.reset_index()

def analyze_alternative_measures(df):
    """
    Analyze alternative inflation measures:
    - Sticky Price CPI (Atlanta Fed)
    - Trimmed Mean PCE (Dallas Fed)
    - Median CPI (Cleveland Fed)
    """
    pivot = df.pivot_table(index='date', columns='series_id', values='value')

    result = pd.DataFrame(index=pivot.index)

    # Standard measures for comparison
    if 'CPIAUCSL' in pivot.columns:
        result['cpi_yoy'] = pivot['CPIAUCSL'].pct_change(12) * 100

    if 'CPILFESL' in pivot.columns:
        result['core_cpi_yoy'] = pivot['CPILFESL'].pct_change(12) * 100

    # Alternative measures (already in YoY form typically)
    if 'CORESTICKM159SFRBATL' in pivot.columns:
        result['sticky_price_cpi'] = pivot['CORESTICKM159SFRBATL']

    if 'PCETRIM12M159SFRBDAL' in pivot.columns:
        result['trimmed_mean_pce'] = pivot['PCETRIM12M159SFRBDAL']

    return result.reset_index()

def calculate_breakeven_inflation(rates_df):
    """
    Calculate breakeven inflation rates from TIPS spreads.

    Breakeven = Nominal Treasury Yield - TIPS Yield

    This represents market expectations of future inflation plus
    an inflation risk premium.
    """
    if rates_df is None:
        return None

    pivot = rates_df.pivot_table(index='date', columns='series_id', values='value')

    result = pd.DataFrame(index=pivot.index)

    # 5-year breakeven
    if 'DGS5' in pivot.columns and 'DFII5' in pivot.columns:
        result['breakeven_5y'] = pivot['DGS5'] - pivot['DFII5']

    # 10-year breakeven
    if 'DGS10' in pivot.columns and 'DFII10' in pivot.columns:
        result['breakeven_10y'] = pivot['DGS10'] - pivot['DFII10']

    # Direct TIPS breakeven series from FRED
    if 'T5YIE' in pivot.columns:
        result['tips_breakeven_5y'] = pivot['T5YIE']

    if 'T10YIE' in pivot.columns:
        result['tips_breakeven_10y'] = pivot['T10YIE']

    # 5y5y forward inflation expectation
    if 'T5YIFR' in pivot.columns:
        result['forward_5y5y'] = pivot['T5YIFR']

    return result.reset_index()

def analyze_inflation_persistence(df, series_id='CPIAUCSL', lags=12):
    """
    Analyze inflation persistence using autocorrelation.

    High persistence suggests inflation is "sticky" and harder to reduce.
    """
    series_data = df[df['series_id'] == series_id].copy()
    series_data = series_data.sort_values('date')
    series_data['yoy'] = series_data['value'].pct_change(12) * 100

    yoy = series_data['yoy'].dropna()

    autocorr = {}
    for lag in range(1, lags + 1):
        autocorr[lag] = yoy.autocorr(lag=lag)

    return {
        'series_id': series_id,
        'autocorrelations': autocorr,
        'mean_inflation': yoy.mean(),
        'std_inflation': yoy.std(),
        'current_inflation': yoy.iloc[-1] if len(yoy) > 0 else None,
        'persistence_ratio': autocorr.get(1, 0) / autocorr.get(12, 1) if autocorr.get(12, 0) != 0 else None
    }

# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_inflation_report(df, rates_df=None):
    """Generate comprehensive inflation analysis report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    report = []
    report.append("=" * 80)
    report.append("COMPREHENSIVE INFLATION DECOMPOSITION ANALYSIS")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Data through: {df['date'].max().strftime('%Y-%m-%d')}")
    report.append("")

    # Current inflation snapshot
    report.append("-" * 80)
    report.append("CURRENT INFLATION SNAPSHOT")
    report.append("-" * 80)

    df_rates = calculate_inflation_rates(df)
    latest = df_rates.groupby('series_id').last().reset_index()

    key_series = ['CPIAUCSL', 'CPILFESL', 'PCEPI', 'PCEPILFE']
    for series_id in key_series:
        row = latest[latest['series_id'] == series_id]
        if len(row) > 0:
            name = INFLATION_SERIES.get(series_id, {}).get('name', series_id)
            yoy = row['yoy_pct'].values[0]
            mom = row['mom_pct'].values[0]
            report.append(f"  {name}: {yoy:.2f}% YoY, {mom:.2f}% MoM (annualized)")

    report.append("")

    # Core vs Headline decomposition
    report.append("-" * 80)
    report.append("CORE VS HEADLINE DECOMPOSITION")
    report.append("-" * 80)

    decomp = decompose_headline_to_core(df)
    if decomp is not None:
        latest_decomp = decomp.iloc[-1]
        report.append(f"  Headline CPI YoY: {latest_decomp.get('headline_yoy', 'N/A'):.2f}%")
        report.append(f"  Core CPI YoY: {latest_decomp.get('core_yoy', 'N/A'):.2f}%")
        report.append(f"  Food & Energy Contribution: {latest_decomp.get('food_energy_contribution', 'N/A'):.2f} pp")

        if 'energy_contribution' in latest_decomp:
            report.append(f"    - Energy: {latest_decomp['energy_contribution']:.2f} pp")
        if 'food_contribution' in latest_decomp:
            report.append(f"    - Food: {latest_decomp['food_contribution']:.2f} pp")

    report.append("")

    # Component decomposition
    report.append("-" * 80)
    report.append("CPI COMPONENT CONTRIBUTIONS")
    report.append("-" * 80)

    components = decompose_cpi_components(df)
    if components is not None:
        latest_comp = components.iloc[-1]
        for col in components.columns:
            if col.endswith('_contribution'):
                name = col.replace('_contribution', '').title()
                val = latest_comp[col]
                if pd.notna(val):
                    report.append(f"  {name}: {val:.2f} pp")

        if 'explained_inflation' in latest_comp and 'headline_yoy' in latest_comp:
            report.append(f"  Total Explained: {latest_comp['explained_inflation']:.2f}%")
            report.append(f"  Residual (Other): {latest_comp['residual']:.2f} pp")

    report.append("")

    # CPI vs PCE comparison
    report.append("-" * 80)
    report.append("CPI VS PCE COMPARISON (SUBSTITUTION BIAS)")
    report.append("-" * 80)

    cpi_pce = compare_cpi_pce(df)
    if cpi_pce is not None:
        latest_comparison = cpi_pce.iloc[-1]

        if 'cpi_headline_yoy' in latest_comparison and 'pce_headline_yoy' in latest_comparison:
            report.append(f"  CPI Headline: {latest_comparison['cpi_headline_yoy']:.2f}%")
            report.append(f"  PCE Headline: {latest_comparison['pce_headline_yoy']:.2f}%")
            report.append(f"  CPI-PCE Wedge: {latest_comparison['headline_wedge']:.2f} pp")
            report.append("")
            report.append("  Interpretation: CPI typically runs 0.2-0.4pp higher than PCE due to:")
            report.append("    - Formula effect (Laspeyres vs chain-weighted)")
            report.append("    - Scope effect (urban vs all consumers)")
            report.append("    - Weight source (consumer survey vs business survey)")

    report.append("")

    # Breakeven inflation
    if rates_df is not None:
        report.append("-" * 80)
        report.append("BREAKEVEN INFLATION (MARKET EXPECTATIONS)")
        report.append("-" * 80)

        breakeven = calculate_breakeven_inflation(rates_df)
        if breakeven is not None:
            latest_be = breakeven.iloc[-1]

            for col in ['breakeven_5y', 'breakeven_10y', 'tips_breakeven_5y',
                       'tips_breakeven_10y', 'forward_5y5y']:
                if col in latest_be and pd.notna(latest_be[col]):
                    name = col.replace('_', ' ').title()
                    report.append(f"  {name}: {latest_be[col]:.2f}%")

    report.append("")

    # Inflation persistence
    report.append("-" * 80)
    report.append("INFLATION PERSISTENCE ANALYSIS")
    report.append("-" * 80)

    persistence = analyze_inflation_persistence(df, 'CPIAUCSL')
    report.append(f"  Mean Inflation (historical): {persistence['mean_inflation']:.2f}%")
    report.append(f"  Std Dev: {persistence['std_inflation']:.2f}%")
    report.append(f"  Current: {persistence['current_inflation']:.2f}%")
    report.append(f"  1-month autocorrelation: {persistence['autocorrelations'].get(1, 0):.3f}")
    report.append(f"  12-month autocorrelation: {persistence['autocorrelations'].get(12, 0):.3f}")

    report.append("")
    report.append("=" * 80)
    report.append("END OF INFLATION DECOMPOSITION REPORT")
    report.append("=" * 80)

    # Save report
    report_text = "\n".join(report)
    report_file = OUTPUT_DIR / f"[{timestamp}]_inflation_decomposition_report.txt"
    with open(report_file, 'w') as f:
        f.write(report_text)

    print(f"\nReport saved to: {report_file}")
    print(report_text)

    return report_text

def save_decomposition_data(df, rates_df=None):
    """Save all decomposition data to CSV files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    # Calculate rates
    df_rates = calculate_inflation_rates(df)
    df_rates.to_csv(OUTPUT_DIR / f"[{timestamp}]_inflation_rates.csv", index=False)

    # Core/headline decomposition
    decomp = decompose_headline_to_core(df)
    if decomp is not None:
        decomp.to_csv(OUTPUT_DIR / f"[{timestamp}]_core_headline_decomposition.csv", index=False)

    # Component decomposition
    components = decompose_cpi_components(df)
    if components is not None:
        components.to_csv(OUTPUT_DIR / f"[{timestamp}]_component_decomposition.csv", index=False)

    # CPI vs PCE
    cpi_pce = compare_cpi_pce(df)
    if cpi_pce is not None:
        cpi_pce.to_csv(OUTPUT_DIR / f"[{timestamp}]_cpi_pce_comparison.csv", index=False)

    # Breakeven inflation
    if rates_df is not None:
        breakeven = calculate_breakeven_inflation(rates_df)
        if breakeven is not None:
            breakeven.to_csv(OUTPUT_DIR / f"[{timestamp}]_breakeven_inflation.csv", index=False)

    # Alternative measures
    alt = analyze_alternative_measures(df)
    if alt is not None:
        alt.to_csv(OUTPUT_DIR / f"[{timestamp}]_alternative_measures.csv", index=False)

    print(f"\nAll decomposition data saved to: {OUTPUT_DIR}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    print("=" * 60)
    print("INFLATION DECOMPOSITION ANALYSIS")
    print("=" * 60)

    # Load data
    df = load_inflation_data()
    if df is None:
        return

    rates_df = load_interest_rates()

    # Generate report
    generate_inflation_report(df, rates_df)

    # Save decomposition data
    save_decomposition_data(df, rates_df)

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
