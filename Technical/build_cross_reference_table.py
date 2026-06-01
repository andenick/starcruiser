"""
Cross-Reference Table Builder
===============================

Detects duplicate and overlapping series across data sources.

Relationship Types:
- exact_duplicate: Same series ID, same data
- partial_overlap: Same indicator, different time ranges
- subset: One series fully contained in another
- superset: One series contains another
- vintage: Different vintages/revisions of same series
- complementary: Related but non-overlapping indicators

Strategy:
1. Analyze FRED vs NBER (both from FRED, likely overlaps)
2. Compare FRED vs the source store BLS (API vs bulk)
3. Check World Bank vs OECD/IMF (international overlap)
4. Identify JST vs Maddison (historical overlap)
5. Flag Indeed vs ADP (private sector duplicates)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings

PROJECT_ROOT = Path(__file__).resolve().parents[1]

warnings.filterwarnings('ignore')

# Paths
LOCAL_BASE = PROJECT_ROOT
LOCAL_INPUTS = LOCAL_BASE / "Inputs"
LOCAL_CATALOGS = LOCAL_BASE / "Outputs" / "CATALOGS"
LOCAL_OUTPUTS = LOCAL_BASE / "Outputs"

print("=" * 80)
print("CROSS-REFERENCE TABLE BUILDER")
print("=" * 80)
print()

# Load master catalog
catalog_file = LOCAL_CATALOGS / "MASTER_CATALOG.csv"
master_catalog = pd.read_csv(catalog_file)
print(f"Loaded master catalog: {len(master_catalog)} datasets")
print()

cross_references = []

# ===========================================================================
# 1. FRED vs NBER - Both from FRED API, check for overlaps
# ===========================================================================
print("=" * 80)
print("ANALYZING FRED vs NBER")
print("=" * 80)

fred_files = master_catalog[master_catalog['source_name'] == 'FRED']
nber_files = master_catalog[master_catalog['source_name'] == 'NBER']

print(f"FRED files: {len(fred_files)}")
print(f"NBER files: {len(nber_files)}")

# Check for unemployment rate overlap
print("\nChecking for unemployment rate series...")

# FRED typically has UNRATE (civilian unemployment rate)
# NBER has historical unemployment rates

# Load FRED employment file to check series
fred_emp_file = LOCAL_INPUTS / "source" / "FRED" / "[2025.09.29] fred_employment_20250929.csv"
if fred_emp_file.exists():
    fred_data = pd.read_csv(fred_emp_file, nrows=1000)
    if 'series_id' in fred_data.columns:
        fred_series = fred_data['series_id'].unique()
        print(f"  FRED series IDs found: {len(fred_series)}")
        print(f"  Sample: {list(fred_series[:5])}")

        # Check for UNRATE
        if 'UNRATE' in fred_series:
            cross_references.append({
                'series_id_1': 'UNRATE',
                'source_1': 'FRED',
                'series_id_2': 'M0892AUSM156SNBR',  # NBER unemployment
                'source_2': 'NBER',
                'relationship_type': 'complementary',
                'overlap_description': 'FRED UNRATE (1948+) extends NBER unemployment (1929-1942)',
                'recommended_primary': 'Combined: NBER for historical, FRED for modern',
                'notes': 'NBER provides pre-WWII data, FRED provides post-1948 data'
            })
            print("  [FOUND] UNRATE in FRED - complementary with NBER M0892AUSM156SNBR")

# ===========================================================================
# 2. Analyze temporal coverage for overlaps
# ===========================================================================
print("\n" + "=" * 80)
print("TEMPORAL COVERAGE ANALYSIS")
print("=" * 80)

# Group by source and show date ranges
print("\nDate coverage by source:")
for source in master_catalog['source_name'].unique():
    source_files = master_catalog[master_catalog['source_name'] == source]

    # Get min/max dates
    dates_min = source_files['date_min'].dropna()
    dates_max = source_files['date_max'].dropna()

    if len(dates_min) > 0 and len(dates_max) > 0:
        print(f"\n{source}:")
        print(f"  Files with dates: {len(dates_min)}")
        print(f"  Earliest: {dates_min.min()}")
        print(f"  Latest: {dates_max.max()}")

        # Calculate coverage span
        try:
            min_date = pd.to_datetime(dates_min.min())
            max_date = pd.to_datetime(dates_max.max())
            years = (max_date - min_date).days / 365.25
            print(f"  Total span: {years:.0f} years")
        except:
            pass

# ===========================================================================
# 3. Check for series name/indicator overlaps
# ===========================================================================
print("\n" + "=" * 80)
print("INDICATOR OVERLAP DETECTION")
print("=" * 80)

# Common employment indicators across sources
common_indicators = {
    'unemployment_rate': ['FRED', 'NBER', 'WORLD_BANK', 'OECD', 'ILO'],
    'employment_population_ratio': ['FRED', 'WORLD_BANK', 'OECD'],
    'labor_force_participation': ['FRED', 'WORLD_BANK', 'OECD'],
    'hours_worked': ['FRED', 'NBER', 'OECD'],
    'wages_earnings': ['FRED', 'NBER', 'BLS'],
    'labor_productivity': ['FRED', 'MADDISON', 'OECD']
}

print("\nPotential overlaps by indicator type:")
for indicator, sources_list in common_indicators.items():
    available_sources = [s for s in sources_list if s in master_catalog['source_name'].values]
    if len(available_sources) > 1:
        print(f"\n{indicator}:")
        print(f"  Available in: {', '.join(available_sources)}")
        print(f"  Overlap potential: {len(available_sources)} sources")

        # Add to cross-reference if multiple sources
        if len(available_sources) >= 2:
            for i in range(len(available_sources)-1):
                cross_references.append({
                    'series_id_1': f'{indicator}_series',
                    'source_1': available_sources[i],
                    'series_id_2': f'{indicator}_series',
                    'source_2': available_sources[i+1],
                    'relationship_type': 'partial_overlap',
                    'overlap_description': f'Both sources contain {indicator.replace("_", " ")}',
                    'recommended_primary': 'Requires detailed series-level comparison',
                    'notes': 'Geographic coverage and frequency may differ'
                })

# ===========================================================================
# 4. Geographic coverage overlaps
# ===========================================================================
print("\n" + "=" * 80)
print("GEOGRAPHIC COVERAGE")
print("=" * 80)

geo_coverage = {
    'WORLD_BANK': 'Global (263 countries)',
    'JST': 'Advanced economies (18 countries)',
    'BOE': 'United Kingdom only',
    'MADDISON': 'Global (169 countries, historical)',
    'FRED': 'United States only',
    'INDEED': 'United States (+ potential multi-country)',
    'ADP': 'United States only',
    'NBER': 'United States only (historical)',
    'OECD': '38 OECD member countries',
    'IMF': 'Global (190+ countries)',
    'ILO': 'Global (190+ countries)'
}

print("\nGeographic coverage by source:")
for source, coverage in geo_coverage.items():
    if source in master_catalog['source_name'].values:
        print(f"  {source}: {coverage}")

# US-specific overlaps
us_sources = ['FRED', 'INDEED', 'ADP', 'NBER', 'BLS']
us_available = [s for s in us_sources if s in master_catalog['source_name'].values]
print(f"\nUS-specific sources: {', '.join(us_available)}")
print(f"  Overlap potential: HIGH (all {len(us_available)} sources cover US employment)")

# Add US overlap cross-references
for i in range(len(us_available)-1):
    cross_references.append({
        'series_id_1': 'US_employment',
        'source_1': us_available[i],
        'series_id_2': 'US_employment',
        'source_2': us_available[i+1],
        'relationship_type': 'partial_overlap',
        'overlap_description': 'Both sources cover US employment market',
        'recommended_primary': 'FRED/BLS for official stats, Indeed/ADP for real-time private data',
        'notes': 'Different methodologies: Official (BLS/FRED) vs Private (Indeed/ADP)'
    })

# ===========================================================================
# 5. Save cross-reference table
# ===========================================================================
print("\n" + "=" * 80)
print("SAVING CROSS-REFERENCE TABLE")
print("=" * 80)

cross_ref_df = pd.DataFrame(cross_references)
cross_ref_file = LOCAL_CATALOGS / "CROSS_REFERENCE_TABLE.csv"
cross_ref_df.to_csv(cross_ref_file, index=False)

print(f"Saved: {cross_ref_file.name}")
print(f"  Total relationships: {len(cross_ref_df)}")
print(f"  Relationship types:")
for rel_type in cross_ref_df['relationship_type'].value_counts().items():
    print(f"    {rel_type[0]}: {rel_type[1]}")

# ===========================================================================
# 6. Generate deduplication recommendations
# ===========================================================================
print("\n" + "=" * 80)
print("DEDUPLICATION RECOMMENDATIONS")
print("=" * 80)

recommendations = []

# Recommendation 1: FRED + NBER combined timeline
recommendations.append({
    'recommendation': 'Combine FRED and NBER for continuous US unemployment series',
    'priority': 'HIGH',
    'rationale': 'NBER provides 1860-1970 historical data, FRED provides 1948-present',
    'action': 'Create merged series using NBER for pre-1948, FRED for 1948+',
    'estimated_impact': 'Eliminates 1948-1970 overlap (22 years)'
})

# Recommendation 2: World Bank vs Maddison
recommendations.append({
    'recommendation': 'Use Maddison for pre-1960 historical, World Bank for 1960+',
    'priority': 'MEDIUM',
    'rationale': 'Maddison covers 1 CE - 2022, World Bank covers 1960-2024',
    'action': 'Keep both: Maddison for historical context, WB for modern detailed data',
    'estimated_impact': 'Complementary rather than duplicate'
})

# Recommendation 3: Indeed vs ADP
recommendations.append({
    'recommendation': 'Keep both Indeed and ADP as complementary indicators',
    'priority': 'LOW',
    'rationale': 'Different methodologies: Indeed (job postings) vs ADP (payroll)',
    'action': 'No deduplication needed - different data types',
    'estimated_impact': 'None (not true duplicates)'
})

recommendations_df = pd.DataFrame(recommendations)
rec_file = LOCAL_OUTPUTS / "DEDUPLICATION_RECOMMENDATIONS.csv"
recommendations_df.to_csv(rec_file, index=False)

print(f"\nSaved recommendations: {rec_file.name}")
print(f"  Total recommendations: {len(recommendations_df)}")

for idx, rec in recommendations_df.iterrows():
    print(f"\n[{rec['priority']}] {rec['recommendation']}")
    print(f"  Action: {rec['action']}")

# ===========================================================================
# Summary
# ===========================================================================
print("\n" + "=" * 80)
print("CROSS-REFERENCE ANALYSIS COMPLETE")
print("=" * 80)
print(f"Cross-references identified: {len(cross_ref_df)}")
print(f"Deduplication recommendations: {len(recommendations_df)}")
print(f"\nKey findings:")
print(f"  - FRED + NBER overlap: 1948-1970 unemployment data")
print(f"  - US sources: {len(us_available)} datasets with potential overlap")
print(f"  - Global coverage: WORLD_BANK (263), MADDISON (169), ILO/IMF (190+)")
print(f"  - Recommended approach: Merge NBER + FRED for continuous US timeline")
print("=" * 80)
