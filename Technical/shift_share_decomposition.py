"""
Shift-Share Decomposition Analysis for County Business Patterns Data

Decomposes county employment growth into three components:
1. National Growth Effect: What if county grew at national rate?
2. Industry Mix Effect: Does county have fast-growing industries?
3. Regional Share Effect: Does county outperform within its industries?

Formula (Classical Shift-Share):
ΔE_j = Σ_i [E_ij(0) × r] + Σ_i [E_ij(0) × (r_i - r)] + Σ_i [E_ij(0) × (r_ij - r_i)]

Where:
- E_ij(0) = Employment in county j, industry i at time 0
- r = National growth rate (all industries)
- r_i = National growth rate for industry i
- r_ij = Growth rate for industry i in county j
- ΔE_j = Total employment change in county j

Output:
1. Decomposition results for each county (2017-2022)
2. Rankings by component (which counties have strongest effects?)
3. Summary statistics and interpretation
4. JSON output for further analysis

Author: StarCruiser Project
Date: December 5, 2025
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = Path(os.environ.get("OUTPUT_ROOT", "outputs"))


# Configuration
INPUT_DIR = (PROJECT_ROOT / "Inputs/source/CENSUS_CBP")
OUTPUT_DIR = OUTPUT_ROOT / "SHIFT_SHARE"
OUTPUT_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")

# NAICS sectors to analyze (2-digit level)
SECTORS = [11, 21, 22, 23, 31, 42, 44, 48, 51, 52, 53, 54, 55, 56, 61, 62, 71, 72]

# Time periods
START_YEAR = 2017
END_YEAR = 2022
GROWTH_PERIODS = [
    (2017, 2018),
    (2018, 2019),
    (2019, 2020),
    (2020, 2021),
    (2021, 2022),
    (2017, 2022)  # Full period
]


def load_cbp_data() -> pd.DataFrame:
    """Load CBP data from CSV files."""
    print("Loading CBP data...")
    
    # Load combined CSV file
    df = pd.read_csv(
        INPUT_DIR / "[20251205]_cbp_combined_2012_2022.csv",
        dtype={'state': 'Int64', 'county': 'Int64', 'SECTOR': 'Int64'},
        usecols=['YEAR', 'EMP', 'SECTOR', 'state', 'county']
    )
    
    # Rename columns to lowercase for consistency
    df = df.rename(columns={
        'YEAR': 'year',
        'EMP': 'emp',
        'SECTOR': 'naics'
    })
    
    # Filter to 2-digit NAICS sectors
    df = df[df['naics'].isin(SECTORS)].copy()
    
    # Filter to county level (state + county)
    df = df[(df['state'].notna()) & (df['county'].notna())].copy()
    
    # Filter years
    df = df[(df['year'] >= START_YEAR) & (df['year'] <= END_YEAR)].copy()
    
    # Aggregate by county-sector-year (sum employment across all sub-sectors)
    print("  Aggregating to 2-digit NAICS level...")
    df = df.groupby(['year', 'state', 'county', 'naics'], as_index=False)['emp'].sum()
    
    print(f"Loaded and aggregated {len(df):,} records")
    print(f"Years: {df['year'].min()}-{df['year'].max()}")
    print(f"Counties: {df['county'].nunique():,}")
    print(f"Sectors: {df['naics'].nunique()}")
    
    return df


def calculate_national_growth_rates(df: pd.DataFrame) -> Dict[Tuple[int, int], float]:
    """Calculate national employment growth rates by period."""
    print("\nCalculating national growth rates...")
    
    national_rates = {}
    
    for start_year, end_year in GROWTH_PERIODS:
        # Filter data
        start_data = df[df['year'] == start_year].copy()
        end_data = df[df['year'] == end_year].copy()
        
        # Total national employment
        start_emp = start_data['emp'].sum()
        end_emp = end_data['emp'].sum()
        
        # Growth rate
        if start_emp > 0:
            growth_rate = (end_emp - start_emp) / start_emp
        else:
            growth_rate = 0.0
        
        national_rates[(start_year, end_year)] = growth_rate
        
        print(f"  {start_year}-{end_year}: {growth_rate:+.2%} "
              f"({start_emp:,.0f} → {end_emp:,.0f})")
    
    return national_rates


def calculate_industry_growth_rates(df: pd.DataFrame) -> Dict[Tuple[int, int, int], float]:
    """Calculate national industry growth rates by sector and period."""
    print("\nCalculating industry growth rates...")
    
    industry_rates = {}
    
    for start_year, end_year in GROWTH_PERIODS:
        # Filter data
        start_data = df[df['year'] == start_year].copy()
        end_data = df[df['year'] == end_year].copy()
        
        for sector in SECTORS:
            # Industry employment
            start_emp = start_data[start_data['naics'] == sector]['emp'].sum()
            end_emp = end_data[end_data['naics'] == sector]['emp'].sum()
            
            # Growth rate
            if start_emp > 0:
                growth_rate = (end_emp - start_emp) / start_emp
            else:
                growth_rate = 0.0
            
            industry_rates[(start_year, end_year, sector)] = growth_rate
    
    # Print summary for full period
    print(f"\n  Full period ({START_YEAR}-{END_YEAR}) industry growth rates:")
    for sector in SECTORS:
        rate = industry_rates.get((START_YEAR, END_YEAR, sector), 0.0)
        print(f"    NAICS {sector:2d}: {rate:+7.2%}")
    
    return industry_rates


def calculate_county_growth_rates(df: pd.DataFrame) -> Dict[Tuple[int, int, int, int], float]:
    """Calculate county-industry growth rates using vectorized operations."""
    print("\nCalculating county-industry growth rates...")
    
    county_rates = {}
    
    for start_year, end_year in GROWTH_PERIODS:
        print(f"  Period {start_year}-{end_year}...")
        
        # Filter data for this period
        start_data = df[df['year'] == start_year].copy()
        end_data = df[df['year'] == end_year].copy()
        
        # Merge on state, county, naics
        merged = start_data.merge(
            end_data,
            on=['state', 'county', 'naics'],
            suffixes=('_start', '_end'),
            how='outer'
        )
        
        # Fill missing values with 0
        merged['emp_start'] = merged['emp_start'].fillna(0)
        merged['emp_end'] = merged['emp_end'].fillna(0)
        
        # Calculate growth rates
        merged['growth_rate'] = np.where(
            merged['emp_start'] > 0,
            (merged['emp_end'] - merged['emp_start']) / merged['emp_start'],
            0.0
        )
        
        # Store in dictionary
        for _, row in merged.iterrows():
            key = (start_year, end_year, int(row['state']), int(row['county']), int(row['naics']))
            county_rates[key] = row['growth_rate']
    
    print(f"  Calculated {len(county_rates):,} county-industry growth rates")
    
    return county_rates


def perform_shift_share_decomposition(
    df: pd.DataFrame,
    national_rates: Dict[Tuple[int, int], float],
    industry_rates: Dict[Tuple[int, int, int], float],
    county_rates: Dict[Tuple[int, int, int, int], float]
) -> pd.DataFrame:
    """
    Perform shift-share decomposition for all counties.
    
    Returns DataFrame with columns:
    - state, county, start_year, end_year
    - initial_employment, final_employment, actual_change
    - national_effect, industry_mix_effect, regional_share_effect
    - total_predicted_change
    """
    print("\nPerforming shift-share decomposition...")
    
    results = []
    
    # Get unique counties
    counties = df[['state', 'county']].drop_duplicates()
    total_counties = len(counties)
    
    for idx, (_, row) in enumerate(counties.iterrows(), 1):
        state = int(row['state'])
        county = int(row['county'])
        
        if idx % 500 == 0:
            print(f"  Processing county {idx:,} / {total_counties:,}")
        
        for start_year, end_year in GROWTH_PERIODS:
            # Get initial employment by sector
            start_data = df[
                (df['year'] == start_year) &
                (df['state'] == state) &
                (df['county'] == county)
            ].copy()
            
            end_data = df[
                (df['year'] == end_year) &
                (df['state'] == state) &
                (df['county'] == county)
            ].copy()
            
            # Total employment
            initial_emp = start_data['emp'].sum()
            final_emp = end_data['emp'].sum()
            actual_change = final_emp - initial_emp
            
            if initial_emp == 0:
                continue
            
            # Shift-share components
            national_effect = 0.0
            industry_mix_effect = 0.0
            regional_share_effect = 0.0
            
            # National growth rate
            r = national_rates.get((start_year, end_year), 0.0)
            
            for sector in SECTORS:
                # Initial employment in sector
                E_ij0 = start_data[start_data['naics'] == sector]['emp'].sum()
                
                if E_ij0 == 0:
                    continue
                
                # Industry growth rate (national)
                r_i = industry_rates.get((start_year, end_year, sector), 0.0)
                
                # County-industry growth rate
                r_ij = county_rates.get((start_year, end_year, state, county, sector), 0.0)
                
                # Components
                national_effect += E_ij0 * r
                industry_mix_effect += E_ij0 * (r_i - r)
                regional_share_effect += E_ij0 * (r_ij - r_i)
            
            total_predicted = national_effect + industry_mix_effect + regional_share_effect
            
            results.append({
                'state': state,
                'county': county,
                'start_year': start_year,
                'end_year': end_year,
                'initial_employment': initial_emp,
                'final_employment': final_emp,
                'actual_change': actual_change,
                'national_effect': national_effect,
                'industry_mix_effect': industry_mix_effect,
                'regional_share_effect': regional_share_effect,
                'total_predicted_change': total_predicted,
                'residual': actual_change - total_predicted
            })
    
    results_df = pd.DataFrame(results)
    
    print(f"\n  Completed decomposition for {len(results_df):,} county-period combinations")
    print(f"  Counties analyzed: {results_df[['state', 'county']].drop_duplicates().shape[0]:,}")
    
    return results_df


def generate_rankings(results_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Generate top/bottom rankings by each component."""
    print("\nGenerating rankings...")
    
    # Filter to full period only
    full_period = results_df[
        (results_df['start_year'] == START_YEAR) &
        (results_df['end_year'] == END_YEAR)
    ].copy()
    
    rankings = {}
    
    # Top/bottom by each component
    components = [
        ('national_effect', 'National Effect'),
        ('industry_mix_effect', 'Industry Mix Effect'),
        ('regional_share_effect', 'Regional Share Effect'),
        ('actual_change', 'Actual Change')
    ]
    
    for col, name in components:
        # Top 50
        top_50 = full_period.nlargest(50, col).copy()
        top_50['rank'] = range(1, len(top_50) + 1)
        rankings[f'top_{col}'] = top_50
        
        # Bottom 50
        bottom_50 = full_period.nsmallest(50, col).copy()
        bottom_50['rank'] = range(1, len(bottom_50) + 1)
        rankings[f'bottom_{col}'] = bottom_50
        
        print(f"  {name}:")
        print(f"    Top: {top_50.iloc[0][col]:+,.0f} jobs")
        print(f"    Bottom: {bottom_50.iloc[0][col]:+,.0f} jobs")
    
    return rankings


def calculate_summary_statistics(results_df: pd.DataFrame) -> Dict:
    """Calculate summary statistics for the decomposition."""
    print("\nCalculating summary statistics...")
    
    # Filter to full period
    full_period = results_df[
        (results_df['start_year'] == START_YEAR) &
        (results_df['end_year'] == END_YEAR)
    ].copy()
    
    stats = {
        'period': f"{START_YEAR}-{END_YEAR}",
        'counties_analyzed': int(len(full_period)),
        'total_initial_employment': float(full_period['initial_employment'].sum()),
        'total_final_employment': float(full_period['final_employment'].sum()),
        'total_actual_change': float(full_period['actual_change'].sum()),
        'total_national_effect': float(full_period['national_effect'].sum()),
        'total_industry_mix_effect': float(full_period['industry_mix_effect'].sum()),
        'total_regional_share_effect': float(full_period['regional_share_effect'].sum()),
        'total_predicted_change': float(full_period['total_predicted_change'].sum()),
        'total_residual': float(full_period['residual'].sum()),
        'mean_national_effect': float(full_period['national_effect'].mean()),
        'mean_industry_mix_effect': float(full_period['industry_mix_effect'].mean()),
        'mean_regional_share_effect': float(full_period['regional_share_effect'].mean()),
        'counties_positive_growth': int((full_period['actual_change'] > 0).sum()),
        'counties_negative_growth': int((full_period['actual_change'] < 0).sum()),
        'counties_positive_industry_mix': int((full_period['industry_mix_effect'] > 0).sum()),
        'counties_negative_industry_mix': int((full_period['industry_mix_effect'] < 0).sum()),
        'counties_positive_regional_share': int((full_period['regional_share_effect'] > 0).sum()),
        'counties_negative_regional_share': int((full_period['regional_share_effect'] < 0).sum())
    }
    
    print(f"\n  Period: {stats['period']}")
    print(f"  Counties: {stats['counties_analyzed']:,}")
    print(f"  Total employment change: {stats['total_actual_change']:+,.0f}")
    print(f"    National effect: {stats['total_national_effect']:+,.0f} "
          f"({stats['total_national_effect'] / stats['total_actual_change'] * 100:.1f}%)")
    print(f"    Industry mix effect: {stats['total_industry_mix_effect']:+,.0f} "
          f"({stats['total_industry_mix_effect'] / stats['total_actual_change'] * 100:.1f}%)")
    print(f"    Regional share effect: {stats['total_regional_share_effect']:+,.0f} "
          f"({stats['total_regional_share_effect'] / stats['total_actual_change'] * 100:.1f}%)")
    
    return stats


def write_report(
    results_df: pd.DataFrame,
    rankings: Dict[str, pd.DataFrame],
    stats: Dict,
    output_file: Path
):
    """Write human-readable report."""
    print(f"\nWriting report to {output_file}...")
    
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("SHIFT-SHARE DECOMPOSITION ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary statistics
        f.write("-" * 80 + "\n")
        f.write("SUMMARY STATISTICS\n")
        f.write("-" * 80 + "\n\n")
        f.write(f"Period: {stats['period']}\n")
        f.write(f"Counties analyzed: {stats['counties_analyzed']:,}\n\n")
        f.write(f"Total employment change: {stats['total_actual_change']:+,.0f}\n")
        f.write(f"  National effect:       {stats['total_national_effect']:+,.0f} "
                f"({stats['total_national_effect'] / stats['total_actual_change'] * 100:+.1f}%)\n")
        f.write(f"  Industry mix effect:   {stats['total_industry_mix_effect']:+,.0f} "
                f"({stats['total_industry_mix_effect'] / stats['total_actual_change'] * 100:+.1f}%)\n")
        f.write(f"  Regional share effect: {stats['total_regional_share_effect']:+,.0f} "
                f"({stats['total_regional_share_effect'] / stats['total_actual_change'] * 100:+.1f}%)\n\n")
        
        f.write(f"Average effects per county:\n")
        f.write(f"  National effect:       {stats['mean_national_effect']:+,.0f}\n")
        f.write(f"  Industry mix effect:   {stats['mean_industry_mix_effect']:+,.0f}\n")
        f.write(f"  Regional share effect: {stats['mean_regional_share_effect']:+,.0f}\n\n")
        
        f.write(f"Growth distribution:\n")
        f.write(f"  Positive growth: {stats['counties_positive_growth']:,} counties "
                f"({stats['counties_positive_growth'] / stats['counties_analyzed'] * 100:.1f}%)\n")
        f.write(f"  Negative growth: {stats['counties_negative_growth']:,} counties "
                f"({stats['counties_negative_growth'] / stats['counties_analyzed'] * 100:.1f}%)\n\n")
        
        # Top 25 by regional share effect (competitive advantage)
        f.write("-" * 80 + "\n")
        f.write("TOP 25 COUNTIES BY REGIONAL SHARE EFFECT (Competitive Advantage)\n")
        f.write("-" * 80 + "\n\n")
        f.write("Counties that outperformed their industry mix expectations\n\n")
        f.write(f"{'Rank':<5} | {'State':<6} | {'County':<7} | {'Regional Share':<15} | "
                f"{'Industry Mix':<14} | {'Actual Change':<14}\n")
        f.write("-" * 80 + "\n")
        
        top_regional = rankings['top_regional_share_effect'].head(25)
        for _, row in top_regional.iterrows():
            f.write(f"{row['rank']:<5} | {int(row['state']):<6} | {int(row['county']):<7} | "
                    f"{row['regional_share_effect']:+14,.0f} | "
                    f"{row['industry_mix_effect']:+13,.0f} | "
                    f"{row['actual_change']:+13,.0f}\n")
        
        # Bottom 25 by regional share effect
        f.write("\n" + "-" * 80 + "\n")
        f.write("BOTTOM 25 COUNTIES BY REGIONAL SHARE EFFECT (Competitive Disadvantage)\n")
        f.write("-" * 80 + "\n\n")
        f.write("Counties that underperformed their industry mix expectations\n\n")
        f.write(f"{'Rank':<5} | {'State':<6} | {'County':<7} | {'Regional Share':<15} | "
                f"{'Industry Mix':<14} | {'Actual Change':<14}\n")
        f.write("-" * 80 + "\n")
        
        bottom_regional = rankings['bottom_regional_share_effect'].head(25)
        for _, row in bottom_regional.iterrows():
            f.write(f"{row['rank']:<5} | {int(row['state']):<6} | {int(row['county']):<7} | "
                    f"{row['regional_share_effect']:+14,.0f} | "
                    f"{row['industry_mix_effect']:+13,.0f} | "
                    f"{row['actual_change']:+13,.0f}\n")
        
        # Top 25 by industry mix effect
        f.write("\n" + "-" * 80 + "\n")
        f.write("TOP 25 COUNTIES BY INDUSTRY MIX EFFECT (Favorable Industry Composition)\n")
        f.write("-" * 80 + "\n\n")
        f.write("Counties with strong concentration in fast-growing industries\n\n")
        f.write(f"{'Rank':<5} | {'State':<6} | {'County':<7} | {'Industry Mix':<14} | "
                f"{'Regional Share':<15} | {'Actual Change':<14}\n")
        f.write("-" * 80 + "\n")
        
        top_industry = rankings['top_industry_mix_effect'].head(25)
        for _, row in top_industry.iterrows():
            f.write(f"{row['rank']:<5} | {int(row['state']):<6} | {int(row['county']):<7} | "
                    f"{row['industry_mix_effect']:+13,.0f} | "
                    f"{row['regional_share_effect']:+14,.0f} | "
                    f"{row['actual_change']:+13,.0f}\n")
        
        # Bottom 25 by industry mix effect
        f.write("\n" + "-" * 80 + "\n")
        f.write("BOTTOM 25 COUNTIES BY INDUSTRY MIX EFFECT (Unfavorable Industry Composition)\n")
        f.write("-" * 80 + "\n\n")
        f.write("Counties with strong concentration in declining industries\n\n")
        f.write(f"{'Rank':<5} | {'State':<6} | {'County':<7} | {'Industry Mix':<14} | "
                f"{'Regional Share':<15} | {'Actual Change':<14}\n")
        f.write("-" * 80 + "\n")
        
        bottom_industry = rankings['bottom_industry_mix_effect'].head(25)
        for _, row in bottom_industry.iterrows():
            f.write(f"{row['rank']:<5} | {int(row['state']):<6} | {int(row['county']):<7} | "
                    f"{row['industry_mix_effect']:+13,.0f} | "
                    f"{row['regional_share_effect']:+14,.0f} | "
                    f"{row['actual_change']:+13,.0f}\n")
        
        # Interpretation
        f.write("\n" + "=" * 80 + "\n")
        f.write("INTERPRETATION GUIDE\n")
        f.write("=" * 80 + "\n\n")
        f.write("NATIONAL EFFECT:\n")
        f.write("  What employment change would have occurred if the county grew at\n")
        f.write("  the national average rate. Always proportional to county size.\n\n")
        f.write("INDUSTRY MIX EFFECT:\n")
        f.write("  Employment change due to county's industry composition.\n")
        f.write("  Positive = County has fast-growing industries (e.g., tech, professional)\n")
        f.write("  Negative = County has declining industries (e.g., manufacturing)\n\n")
        f.write("REGIONAL SHARE EFFECT:\n")
        f.write("  Employment change due to county's competitive advantages/disadvantages.\n")
        f.write("  Positive = County outperforms within its industries (quality jobs, amenities)\n")
        f.write("  Negative = County underperforms (declining region, poor policy)\n\n")
        f.write("ACTUAL CHANGE = National Effect + Industry Mix Effect + Regional Share Effect\n\n")
        
        f.write("=" * 80 + "\n")
    
    print(f"  Report saved: {output_file}")


def main():
    """Main execution function."""
    print("=" * 80)
    print("SHIFT-SHARE DECOMPOSITION ANALYSIS")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load data
    df = load_cbp_data()
    
    # Calculate growth rates
    national_rates = calculate_national_growth_rates(df)
    industry_rates = calculate_industry_growth_rates(df)
    county_rates = calculate_county_growth_rates(df)
    
    # Perform decomposition
    results_df = perform_shift_share_decomposition(
        df, national_rates, industry_rates, county_rates
    )
    
    # Generate rankings
    rankings = generate_rankings(results_df)
    
    # Calculate summary statistics
    stats = calculate_summary_statistics(results_df)
    
    # Write outputs
    output_file = OUTPUT_DIR / f"[{TIMESTAMP}]_shift_share_report.txt"
    write_report(results_df, rankings, stats, output_file)
    
    # Save JSON
    json_file = OUTPUT_DIR / f"[{TIMESTAMP}]_shift_share_results.json"
    print(f"\nSaving JSON results to {json_file}...")
    
    # Convert results to JSON-serializable format
    output_data = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'period': f"{START_YEAR}-{END_YEAR}",
            'counties_analyzed': stats['counties_analyzed']
        },
        'summary_statistics': stats,
        'full_results': results_df.to_dict(orient='records')
    }
    
    with open(json_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"  JSON saved: {json_file}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nOutputs:")
    print(f"  Report: {output_file}")
    print(f"  JSON:   {json_file}")


if __name__ == "__main__":
    main()
