"""
JST Macrohistory Database - FULL EXTRACTION
============================================

Extracts ALL 48 variables for ALL 18 countries from the JST Macrohistory Database.

Current StarCruiser import: Only 5 variables from 3 countries (sample)
This script: ALL 48 variables × 18 countries (FULL dataset)

Countries (18): Australia, Belgium, Canada, Switzerland, Germany, Denmark, Spain,
                Finland, France, UK, Italy, Japan, Netherlands, Norway, Portugal,
                Sweden, USA

Variables (48): Population, GDP, consumption, investment, government spending,
                exports, imports, CPI, wages, hours worked, employment, unemployment,
                interest rates, stock prices, house prices, credit, money supply,
                and many more macroeconomic indicators (1870-2020, 150 years!)

Input: <DATA_ROOT>/DATA/JST/
Output: <repo>/Inputs/source/JST/
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
SOURCE_JST_PATH = DATA_ROOT / "DATA/JST"
LOCAL_INPUT = (PROJECT_ROOT / "Inputs/source/JST")
LOCAL_OUTPUT = OUTPUT_ROOT

# Create output directories
LOCAL_INPUT.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("JST MACROHISTORY DATABASE - FULL EXTRACTION")
print("=" * 80)
print(f"Source: {SOURCE_JST_PATH}")
print(f"Target: {LOCAL_INPUT}")
print()

# Step 1: Load JST dataset
print("Step 1: Loading JST Macrohistory Dataset...")
jst_file = SOURCE_JST_PATH / "[2025.10.09] JST_dataset_R6.xlsx"
print(f"  File: {jst_file.name}")
print(f"  Size: {jst_file.stat().st_size / 1024 / 1024:.1f} MB")

# Load the full dataset
jst_df = pd.read_excel(jst_file, sheet_name='Sheet1')
print(f"  Total records: {len(jst_df):,}")
print(f"  Columns: {len(jst_df.columns)}")

# Step 2: Examine data structure
print("\nStep 2: Examining data structure...")
print(f"  Columns: {list(jst_df.columns)[:10]}... (showing first 10)")
print(f"  Countries (unique iso codes): {jst_df['iso'].nunique() if 'iso' in jst_df.columns else 'N/A'}")
print(f"  Year range: {jst_df['year'].min() if 'year' in jst_df.columns else 'N/A'} - {jst_df['year'].max() if 'year' in jst_df.columns else 'N/A'}")

# List all columns
print("\n  All columns in dataset:")
for i, col in enumerate(jst_df.columns, 1):
    print(f"    {i:2d}. {col}")

# Step 3: Identify employment/labor-related variables
print("\nStep 3: Identifying employment/labor-related variables...")
employment_keywords = ['employ', 'labor', 'labour', 'wage', 'hour', 'work',
                       'unemployment', 'job', 'occupation', 'pop']

employment_vars = []
for col in jst_df.columns:
    if any(keyword in col.lower() for keyword in employment_keywords):
        employment_vars.append(col)

print(f"  Employment-related variables found: {len(employment_vars)}")
for var in employment_vars:
    print(f"    - {var}")

# Step 4: Extract and save full dataset
print("\nStep 4: Saving FULL JST dataset...")
full_output_file = LOCAL_INPUT / "jst_macrohistory_full.csv"
jst_df.to_csv(full_output_file, index=False, encoding='utf-8')
print(f"  Saved to: {full_output_file.name}")
print(f"  File size: {full_output_file.stat().st_size / 1024 / 1024:.1f} MB")

# Step 5: Create employment subset
print("\nStep 5: Creating employment subset...")
# Key columns to keep: year, iso, country, and all employment-related variables
key_cols = ['year', 'iso', 'country'] if 'country' in jst_df.columns else ['year', 'iso']
employment_subset_cols = key_cols + employment_vars

employment_df = jst_df[employment_subset_cols].copy()
employment_output_file = LOCAL_INPUT / "jst_employment_data.csv"
employment_df.to_csv(employment_output_file, index=False, encoding='utf-8')
print(f"  Saved to: {employment_output_file.name}")
print(f"  File size: {employment_output_file.stat().st_size / 1024 / 1024:.1f} MB")
print(f"  Variables included: {len(employment_vars)}")

# Step 6: Generate summary statistics
print("\nStep 6: Generating summary statistics...")

# Get country information
if 'iso' in jst_df.columns:
    countries = jst_df.groupby('iso')['year'].agg(['min', 'max', 'count']).reset_index()
    countries.columns = ['Country Code', 'Year Min', 'Year Max', 'Total Years']
    print(f"\n  Countries in dataset ({len(countries)}):")
    for _, row in countries.iterrows():
        print(f"    {row['Country Code']}: {row['Year Min']}-{row['Year Max']} ({row['Total Years']} years)")

# Calculate completeness for each variable
variable_stats = []
for col in jst_df.columns:
    if col not in ['year', 'iso', 'country']:
        non_null = jst_df[col].notna().sum()
        total = len(jst_df)
        completeness = (non_null / total) * 100 if total > 0 else 0

        variable_stats.append({
            'Variable': col,
            'Non-Null Count': non_null,
            'Total Records': total,
            'Completeness (%)': completeness,
            'Is Employment Related': col in employment_vars
        })

variable_stats_df = pd.DataFrame(variable_stats)
variable_stats_df = variable_stats_df.sort_values('Completeness (%)', ascending=False)

stats_output_file = LOCAL_OUTPUT / "JST_VARIABLE_COMPLETENESS.csv"
variable_stats_df.to_csv(stats_output_file, index=False, encoding='utf-8')
print(f"\n  Variable completeness saved to: {stats_output_file.name}")

# Step 7: Create metadata summary
print("\nStep 7: Creating metadata summary...")
summary_stats = {
    'extraction_date': datetime.now().isoformat(),
    'source_file': str(jst_file),
    'total_records': len(jst_df),
    'total_variables': len(jst_df.columns) - 3,  # Excluding year, iso, country
    'countries': int(jst_df['iso'].nunique()) if 'iso' in jst_df.columns else 0,
    'year_range': {
        'min': int(jst_df['year'].min()) if 'year' in jst_df.columns else None,
        'max': int(jst_df['year'].max()) if 'year' in jst_df.columns else None
    },
    'employment_variables': employment_vars,
    'all_variables': [col for col in jst_df.columns if col not in ['year', 'iso', 'country']],
    'countries_list': jst_df['iso'].unique().tolist() if 'iso' in jst_df.columns else []
}

summary_file = LOCAL_INPUT / "jst_extraction_summary.json"
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary_stats, f, indent=2)
print(f"  Saved summary to: {summary_file.name}")

# Step 8: Display employment variable completeness
print("\n" + "=" * 80)
print("EMPLOYMENT-RELATED VARIABLES COMPLETENESS")
print("=" * 80)
employment_stats = variable_stats_df[variable_stats_df['Is Employment Related'] == True]
for _, row in employment_stats.iterrows():
    print(f"\n{row['Variable']}")
    print(f"  Completeness: {row['Completeness (%)']:.1f}%")
    print(f"  Non-null records: {row['Non-Null Count']:,} / {row['Total Records']:,}")

# Step 9: Final summary
print("\n" + "=" * 80)
print("EXTRACTION COMPLETE")
print("=" * 80)
print(f"Total records extracted: {len(jst_df):,}")
print(f"Total variables: {len(jst_df.columns) - 3} (excluding year, iso, country)")
print(f"Employment variables: {len(employment_vars)}")
print(f"Countries: {jst_df['iso'].nunique() if 'iso' in jst_df.columns else 'N/A'}")
print(f"Coverage: {jst_df['year'].min() if 'year' in jst_df.columns else 'N/A'}-{jst_df['year'].max() if 'year' in jst_df.columns else 'N/A'} ({jst_df['year'].max() - jst_df['year'].min() + 1 if 'year' in jst_df.columns else 0} years)")
print()
print(f"Output files:")
print(f"  1. {full_output_file.name} ({full_output_file.stat().st_size / 1024 / 1024:.1f} MB) - FULL dataset")
print(f"  2. {employment_output_file.name} ({employment_output_file.stat().st_size / 1024 / 1024:.1f} MB) - Employment subset")
print(f"  3. {summary_file.name}")
print(f"  4. {stats_output_file.name}")
print("=" * 80)
