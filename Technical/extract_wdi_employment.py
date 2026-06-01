"""
World Bank WDI Employment Data Extraction
==========================================

Extracts all employment-related series from the World Bank WDI dataset.

Target: 129 labor/employment series with "SL." prefix covering:
- Employment by sector (agriculture, industry, services)
- Employment to population ratios
- Labor force participation rates
- Unemployment rates
- Vulnerable employment
- Self-employment, wage workers
- Child employment
- GDP per person employed
- Labor force by education level

Input: <DATA_ROOT>/DATA/WorldBank/WDI_CSV/
Output: <repo>/Inputs/source/WORLD_BANK/
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
SOURCE_WDI_PATH = DATA_ROOT / "DATA/WorldBank/WDI_CSV"
LOCAL_INPUT = (PROJECT_ROOT / "Inputs/source/WORLD_BANK")
LOCAL_OUTPUT = OUTPUT_ROOT

# Create output directories
LOCAL_INPUT.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("WORLD BANK WDI EMPLOYMENT DATA EXTRACTION")
print("=" * 80)
print(f"Source: {SOURCE_WDI_PATH}")
print(f"Target: {LOCAL_INPUT}")
print()

# Step 1: Load WDI Series metadata to identify employment series
print("Step 1: Loading WDI Series metadata...")
series_file = SOURCE_WDI_PATH / "[2025.10.10] WDISeries.csv"
series_df = pd.read_csv(series_file, encoding='utf-8')
print(f"  Total WDI series: {len(series_df):,}")

# Step 2: Filter for employment/labor series
print("\nStep 2: Filtering for employment/labor series...")
# Employment series typically have "SL." prefix (Social Development - Labor)
employment_keywords = ['employment', 'labor', 'labour', 'unemployment', 'workforce',
                       'occupation', 'worker', 'job', 'wage', 'salary', 'payroll',
                       'labor force', 'labour force', 'employed', 'self-employed',
                       'vulnerable employment', 'informal employment']

# Filter series
employment_series = series_df[
    series_df['Series Code'].str.startswith('SL.', na=False) |
    series_df['Indicator Name'].str.contains('|'.join(employment_keywords), case=False, na=False)
].copy()

print(f"  Employment series found: {len(employment_series):,}")
print(f"  Primary prefix 'SL.': {len(employment_series[employment_series['Series Code'].str.startswith('SL.')])}")

# Save employment series metadata
employment_series_file = LOCAL_INPUT / "wdi_employment_series_metadata.csv"
employment_series.to_csv(employment_series_file, index=False, encoding='utf-8')
print(f"  Saved metadata to: {employment_series_file.name}")

# Step 3: Load main WDI data and filter for employment series
print("\nStep 3: Loading main WDI data (this may take a moment - 189 MB file)...")
data_file = SOURCE_WDI_PATH / "[2025.10.10] WDICSV.csv"

# Read in chunks to handle large file
chunk_size = 100000
employment_data_chunks = []

for chunk in pd.read_csv(data_file, encoding='utf-8', chunksize=chunk_size, low_memory=False):
    # Filter for employment series
    employment_chunk = chunk[chunk['Indicator Code'].isin(employment_series['Series Code'])]
    if len(employment_chunk) > 0:
        employment_data_chunks.append(employment_chunk)
    print(f"  Processed {len(chunk):,} rows... (found {len(employment_chunk):,} employment records)")

# Combine all chunks
employment_data = pd.concat(employment_data_chunks, ignore_index=True)
print(f"\n  Total employment records: {len(employment_data):,}")

# Step 4: Transform data from wide to long format
print("\nStep 4: Transforming data to long format...")
# Year columns are 1960-2024
year_columns = [str(year) for year in range(1960, 2025)]
year_columns_present = [col for col in year_columns if col in employment_data.columns]

# Melt the data
employment_long = employment_data.melt(
    id_vars=['Country Name', 'Country Code', 'Indicator Name', 'Indicator Code'],
    value_vars=year_columns_present,
    var_name='Year',
    value_name='Value'
)

# Drop null values
employment_long = employment_long.dropna(subset=['Value'])
employment_long['Year'] = employment_long['Year'].astype(int)

print(f"  Records after transformation: {len(employment_long):,}")
print(f"  Countries: {employment_long['Country Code'].nunique()}")
print(f"  Indicators: {employment_long['Indicator Code'].nunique()}")
print(f"  Year range: {employment_long['Year'].min()} - {employment_long['Year'].max()}")

# Step 5: Save employment data
print("\nStep 5: Saving employment data...")
output_file = LOCAL_INPUT / "wdi_employment_data.csv"
employment_long.to_csv(output_file, index=False, encoding='utf-8')
print(f"  Saved to: {output_file.name}")
print(f"  File size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")

# Step 6: Generate summary statistics
print("\nStep 6: Generating summary statistics...")
summary_stats = {
    'extraction_date': datetime.now().isoformat(),
    'source_file': str(data_file),
    'total_records': len(employment_long),
    'total_indicators': employment_long['Indicator Code'].nunique(),
    'total_countries': employment_long['Country Code'].nunique(),
    'year_range': {
        'min': int(employment_long['Year'].min()),
        'max': int(employment_long['Year'].max())
    },
    'indicators_list': employment_long['Indicator Code'].unique().tolist(),
    'countries_list': employment_long['Country Code'].unique().tolist(),
    'records_by_indicator': employment_long['Indicator Code'].value_counts().to_dict(),
    'records_by_country': employment_long.groupby('Country Code').size().nlargest(20).to_dict()
}

summary_file = LOCAL_INPUT / "wdi_employment_extraction_summary.json"
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary_stats, f, indent=2)
print(f"  Saved summary to: {summary_file.name}")

# Step 7: Create inventory report
print("\nStep 7: Creating inventory report...")
inventory_data = []

for indicator_code in employment_long['Indicator Code'].unique():
    indicator_data = employment_long[employment_long['Indicator Code'] == indicator_code]
    indicator_name = indicator_data['Indicator Name'].iloc[0]

    inventory_data.append({
        'Indicator Code': indicator_code,
        'Indicator Name': indicator_name,
        'Total Records': len(indicator_data),
        'Countries': indicator_data['Country Code'].nunique(),
        'Year Min': indicator_data['Year'].min(),
        'Year Max': indicator_data['Year'].max(),
        'Coverage (Years)': indicator_data['Year'].max() - indicator_data['Year'].min() + 1
    })

inventory_df = pd.DataFrame(inventory_data)
inventory_df = inventory_df.sort_values('Total Records', ascending=False)

inventory_file = LOCAL_OUTPUT / "WDI_EMPLOYMENT_INVENTORY.csv"
inventory_df.to_csv(inventory_file, index=False, encoding='utf-8')
print(f"  Saved inventory to: {inventory_file.name}")

# Step 8: Display top indicators
print("\n" + "=" * 80)
print("TOP 10 EMPLOYMENT INDICATORS (by record count)")
print("=" * 80)
for idx, row in inventory_df.head(10).iterrows():
    print(f"\n{row['Indicator Code']}")
    print(f"  {row['Indicator Name']}")
    print(f"  Records: {row['Total Records']:,} | Countries: {row['Countries']} | Years: {row['Year Min']}-{row['Year Max']}")

# Step 9: Final summary
print("\n" + "=" * 80)
print("EXTRACTION COMPLETE")
print("=" * 80)
print(f"Total employment records extracted: {len(employment_long):,}")
print(f"Total indicators: {employment_long['Indicator Code'].nunique()}")
print(f"Total countries/regions: {employment_long['Country Code'].nunique()}")
print(f"Coverage: {employment_long['Year'].min()}-{employment_long['Year'].max()}")
print()
print(f"Output files:")
print(f"  1. {output_file.name} ({output_file.stat().st_size / 1024 / 1024:.1f} MB)")
print(f"  2. {employment_series_file.name}")
print(f"  3. {summary_file.name}")
print(f"  4. {inventory_file.name}")
print("=" * 80)
