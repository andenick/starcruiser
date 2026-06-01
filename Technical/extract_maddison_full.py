"""
Maddison Project Database - FULL EXTRACTION
============================================

Extracts ALL 169 countries from the Maddison Project Database 2023.

Current StarCruiser import: Only 10 countries (sample)
This script: ALL 169 countries (FULL dataset)

Coverage: 1 CE - 2022 (2,000+ years of economic data!)
Variables: Population, GDP, GDP per capita

Input: <DATA_ROOT>/DATA/Maddison/
Output: <repo>/Inputs/source/MADDISON/
"""

import pandas as pd
import os
from pathlib import Path
import json
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "data"))
OUTPUT_ROOT = Path(os.environ.get("OUTPUT_ROOT", "outputs"))


# Paths
SOURCE_MADDISON_PATH = DATA_ROOT / "DATA/Maddison"
LOCAL_INPUT = (PROJECT_ROOT / "Inputs/source/MADDISON")
LOCAL_OUTPUT = OUTPUT_ROOT

# Create output directories
LOCAL_INPUT.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("MADDISON PROJECT DATABASE - FULL EXTRACTION")
print("=" * 80)
print(f"Source: {SOURCE_MADDISON_PATH}")
print(f"Target: {LOCAL_INPUT}")
print()

# Step 1: Load Maddison dataset
print("Step 1: Loading Maddison Project Database...")
maddison_file = SOURCE_MADDISON_PATH / "[2025.10.09] maddison_project_2023.xlsx"
print(f"  File: {maddison_file.name}")
print(f"  Size: {maddison_file.stat().st_size / 1024 / 1024:.1f} MB")

xl = pd.ExcelFile(maddison_file)
print(f"  Sheets: {xl.sheet_names}")

# Step 2: Extract Full data sheet
print("\nStep 2: Extracting 'Full data' sheet (all countries, all years)...")
full_df = pd.read_excel(xl, sheet_name='Full data')
print(f"  Total records: {len(full_df):,}")
print(f"  Columns: {list(full_df.columns)}")

# Step 3: Extract GDPpc sheet
print("\nStep 3: Extracting 'GDPpc' sheet...")
gdppc_df = pd.read_excel(xl, sheet_name='GDPpc')
print(f"  Shape: {gdppc_df.shape}")
print(f"  Columns (first 10): {list(gdppc_df.columns[:10])}")

# Step 4: Extract Population sheet
print("\nStep 4: Extracting 'Population' sheet...")
pop_df = pd.read_excel(xl, sheet_name='Population')
print(f"  Shape: {pop_df.shape}")
print(f"  Columns (first 10): {list(pop_df.columns[:10])}")

# Step 5: Extract Regional data
print("\nStep 5: Extracting 'Regional data' sheet...")
regional_df = pd.read_excel(xl, sheet_name='Regional data')
print(f"  Total records: {len(regional_df):,}")
print(f"  Columns: {list(regional_df.columns)}")

# Step 6: Save all datasets
print("\nStep 6: Saving datasets...")

# Save Full data
full_output = LOCAL_INPUT / "maddison_full_data.csv"
full_df.to_csv(full_output, index=False, encoding='utf-8')
print(f"  1. Full data: {full_output.name} ({full_output.stat().st_size / 1024 / 1024:.1f} MB)")

# Save GDPpc
gdppc_output = LOCAL_INPUT / "maddison_gdp_per_capita.csv"
gdppc_df.to_csv(gdppc_output, index=False, encoding='utf-8')
print(f"  2. GDP per capita: {gdppc_output.name} ({gdppc_output.stat().st_size / 1024 / 1024:.1f} MB)")

# Save Population
pop_output = LOCAL_INPUT / "maddison_population.csv"
pop_df.to_csv(pop_output, index=False, encoding='utf-8')
print(f"  3. Population: {pop_output.name} ({pop_output.stat().st_size / 1024 / 1024:.1f} MB)")

# Save Regional data
regional_output = LOCAL_INPUT / "maddison_regional_data.csv"
regional_df.to_csv(regional_output, index=False, encoding='utf-8')
print(f"  4. Regional data: {regional_output.name} ({regional_output.stat().st_size / 1024 / 1024:.1f} MB)")

# Step 7: Analyze coverage
print("\nStep 7: Analyzing coverage...")

# Count countries in full data
if 'countrycode' in full_df.columns:
    countries = full_df['countrycode'].unique()
    print(f"  Countries in full data: {len(countries)}")
    print(f"  Sample countries: {list(countries[:10])}")
elif 'country' in full_df.columns:
    countries = full_df['country'].unique()
    print(f"  Countries in full data: {len(countries)}")
    print(f"  Sample countries: {list(countries[:10])}")

# Year range
if 'year' in full_df.columns:
    year_min = full_df['year'].min()
    year_max = full_df['year'].max()
    print(f"  Year range: {year_min} - {year_max} ({year_max - year_min + 1} years)")

# Variables available
print(f"  Variables: {', '.join(full_df.columns)}")

# Step 8: Create employment-relevant subset
print("\nStep 8: Creating employment-relevant subset...")
# Population is labor force proxy
# GDP per capita is labor productivity proxy
# Combine key indicators

employment_cols = []
if 'countrycode' in full_df.columns:
    employment_cols.append('countrycode')
if 'country' in full_df.columns:
    employment_cols.append('country')
if 'year' in full_df.columns:
    employment_cols.append('year')
if 'pop' in full_df.columns or 'population' in full_df.columns:
    employment_cols.append('pop' if 'pop' in full_df.columns else 'population')
if 'gdppc' in full_df.columns:
    employment_cols.append('gdppc')
if 'rgdpnapc' in full_df.columns:
    employment_cols.append('rgdpnapc')

if employment_cols:
    employment_df = full_df[employment_cols].copy()
    employment_output = LOCAL_INPUT / "maddison_employment_relevant.csv"
    employment_df.to_csv(employment_output, index=False, encoding='utf-8')
    print(f"  Saved: {employment_output.name}")
    print(f"  Variables: {employment_cols}")
    print(f"  Records: {len(employment_df):,}")

# Step 9: Generate summary statistics
print("\nStep 9: Generating summary statistics...")

summary_stats = {
    'extraction_date': datetime.now().isoformat(),
    'source_file': str(maddison_file),
    'total_records_full_data': len(full_df),
    'countries': int(len(countries)) if 'countries' in locals() else 0,
    'year_range': {
        'min': int(year_min) if 'year_min' in locals() else None,
        'max': int(year_max) if 'year_max' in locals() else None
    },
    'variables': list(full_df.columns),
    'sheets_extracted': ['Full data', 'GDPpc', 'Population', 'Regional data'],
    'gdppc_shape': list(gdppc_df.shape),
    'population_shape': list(pop_df.shape),
    'regional_records': len(regional_df)
}

summary_file = LOCAL_INPUT / "maddison_extraction_summary.json"
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary_stats, f, indent=2)
print(f"  Saved summary to: {summary_file.name}")

# Step 10: Create country inventory
print("\nStep 10: Creating country inventory...")
if 'countrycode' in full_df.columns or 'country' in full_df.columns:
    country_col = 'countrycode' if 'countrycode' in full_df.columns else 'country'

    country_stats = full_df.groupby(country_col).agg({
        'year': ['min', 'max', 'count']
    }).reset_index()
    country_stats.columns = ['Country', 'Year Min', 'Year Max', 'Total Years']
    country_stats = country_stats.sort_values('Total Years', ascending=False)

    inventory_file = LOCAL_OUTPUT / "MADDISON_COUNTRY_INVENTORY.csv"
    country_stats.to_csv(inventory_file, index=False, encoding='utf-8')
    print(f"  Saved to: {inventory_file.name}")

    # Display top 20 countries by data availability
    print("\n  Top 20 countries by data availability:")
    for _, row in country_stats.head(20).iterrows():
        print(f"    {row['Country']}: {row['Year Min']}-{row['Year Max']} ({row['Total Years']} years)")

# Step 11: Final summary
print("\n" + "=" * 80)
print("EXTRACTION COMPLETE")
print("=" * 80)
print(f"Total records (Full data): {len(full_df):,}")
print(f"Countries: {len(countries) if 'countries' in locals() else 'N/A'}")
print(f"Coverage: {year_min if 'year_min' in locals() else 'N/A'} - {year_max if 'year_max' in locals() else 'N/A'}")
print(f"GDPpc matrix: {gdppc_df.shape[0]} years × {gdppc_df.shape[1] - 1} countries")
print(f"Population matrix: {pop_df.shape[0]} years × {pop_df.shape[1] - 1} countries")
print(f"Regional aggregates: {len(regional_df):,} records")
print()
print(f"Output files:")
print(f"  1. {full_output.name} - Complete dataset")
print(f"  2. {gdppc_output.name} - GDP per capita matrix")
print(f"  3. {pop_output.name} - Population matrix")
print(f"  4. {regional_output.name} - Regional aggregates")
print(f"  5. {employment_output.name if 'employment_output' in locals() else 'N/A'} - Employment-relevant subset")
print(f"  6. {summary_file.name} - Metadata summary")
print(f"  7. {inventory_file.name if 'inventory_file' in locals() else 'N/A'} - Country inventory")
print("=" * 80)
