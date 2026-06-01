"""
OECD Employment Data Downloader
=================================

Downloads OECD employment statistics via SDMX API (pandasdmx library).

Target Datasets:
1. LFS - Labour Force Statistics (Main indicators)
2. PDB - Productivity Database
3. MEI - Main Economic Indicators

Coverage: 38 OECD countries
Size: ~500-700 MB total
Format: SDMX (Statistical Data and Metadata eXchange)

Requires: pandasdmx library
Install: pip install pandasdmx
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import requests
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Paths
LOCAL_OECD = (PROJECT_ROOT / "Inputs/External/OECD")
LOCAL_OECD.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("OECD EMPLOYMENT DATA DOWNLOADER")
print("=" * 80)
print(f"Output: {LOCAL_OECD}")
print()

# Using direct CSV API downloads (no SDMX library needed)
print("[OK] Using OECD CSV API (no additional libraries required)")
print()

# OECD employment indicators via bulk CSV download
# OECD provides bulk downloads at: https://stats.oecd.org/

OECD_DATASETS = {
    'LFS_MAIN': {
        'name': 'Labour Force Statistics - Main Indicators',
        'url': 'https://stats.oecd.org/restsdmx/sdmx.ashx/GetData/ALFS_EMP/all/all',
        'description': 'Employment, unemployment, participation rates',
    },
    'LFS_DETAIL': {
        'name': 'Labour Force Statistics - Detailed',
        'url': 'https://stats.oecd.org/restsdmx/sdmx.ashx/GetData/LFS_SEXAGE_I_R/all/all',
        'description': 'Employment by age, sex, education',
    },
    'PDB': {
        'name': 'Productivity Database',
        'url': 'https://stats.oecd.org/restsdmx/sdmx.ashx/GetData/PDB_GR/all/all',
        'description': 'Labor productivity, hours worked',
    },
}

# Alternative: Direct CSV download URLs (more reliable)
OECD_CSV_URLS = {
    'unemployment_rate': {
        'name': 'Harmonised Unemployment Rate',
        'url': 'https://stats.oecd.org/sdmx-json/data/DP_LIVE/.UNEMP.TOT.PC_LF.M/OECD?contentType=csv&detail=code&separator=comma&csv-lang=en',
    },
    'employment_rate': {
        'name': 'Employment Rate',
        'url': 'https://stats.oecd.org/sdmx-json/data/DP_LIVE/.EMPRATE.TOT.PC_WKGPOP.A/OECD?contentType=csv&detail=code&separator=comma&csv-lang=en',
    },
    'labor_force_participation': {
        'name': 'Labour Force Participation Rate',
        'url': 'https://stats.oecd.org/sdmx-json/data/DP_LIVE/.LFPART.TOT.PC_WKGPOP.A/OECD?contentType=csv&detail=code&separator=comma&csv-lang=en',
    },
    'part_time_employment': {
        'name': 'Part-time Employment Rate',
        'url': 'https://stats.oecd.org/sdmx-json/data/DP_LIVE/.PARTTIME.TOT.PC_EMP.A/OECD?contentType=csv&detail=code&separator=comma&csv-lang=en',
    },
    'average_hours_worked': {
        'name': 'Average Annual Hours Worked',
        'url': 'https://stats.oecd.org/sdmx-json/data/DP_LIVE/.ANHRS.TOT.HR_WK.A/OECD?contentType=csv&detail=code&separator=comma&csv-lang=en',
    },
    'labor_productivity': {
        'name': 'GDP per Hour Worked',
        'url': 'https://stats.oecd.org/sdmx-json/data/DP_LIVE/.LABPRODUCTIVITY.TOT.PC_CHGPP.A/OECD?contentType=csv&detail=code&separator=comma&csv-lang=en',
    },
}

download_stats = {
    'successful': 0,
    'failed': 0,
    'total_records': 0,
    'errors': []
}

all_data = []
metadata = []

print("=" * 80)
print("DOWNLOADING OECD DATA VIA CSV API")
print("=" * 80)

for i, (dataset_id, info) in enumerate(OECD_CSV_URLS.items(), 1):
    print(f"\n[{i}/{len(OECD_CSV_URLS)}] {info['name']}...")
    print(f"  URL: {info['url'][:80]}...")

    try:
        # Download with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(info['url'], timeout=180)
                response.raise_for_status()
                break
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"  Timeout, retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(5)
                else:
                    raise
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"  Error, retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(5)
                else:
                    raise

        # Save raw CSV
        output_file = LOCAL_OECD / f"oecd_{dataset_id}.csv"
        with open(output_file, 'wb') as f:
            f.write(response.content)

        # Load and analyze
        df = pd.read_csv(output_file)

        # Add to collection
        df['dataset_id'] = dataset_id
        df['dataset_name'] = info['name']
        all_data.append(df)

        # Metadata
        metadata.append({
            'dataset_id': dataset_id,
            'dataset_name': info['name'],
            'records': len(df),
            'columns': len(df.columns),
            'file_size_mb': output_file.stat().st_size / 1024 / 1024,
            'file': output_file.name
        })

        download_stats['successful'] += 1
        download_stats['total_records'] += len(df)

        print(f"  [OK] {len(df):,} records")
        print(f"  Columns: {', '.join(df.columns[:5].tolist())}...")
        print(f"  Size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")

        # Rate limiting
        time.sleep(2)

    except Exception as e:
        print(f"  [ERROR] {str(e)[:100]}")
        download_stats['failed'] += 1
        download_stats['errors'].append(f"{dataset_id}: {str(e)[:80]}")

# Combine all datasets
print("\n" + "=" * 80)
print("COMBINING DATA")
print("=" * 80)

if all_data:
    combined = pd.concat(all_data, ignore_index=True)
    combined_file = LOCAL_OECD / f"[{datetime.now().strftime('%Y.%m.%d')}] oecd_employment_all.csv"
    combined.to_csv(combined_file, index=False)

    print(f"Combined data saved: {combined_file.name}")
    print(f"  Total records: {len(combined):,}")
    print(f"  Datasets: {combined['dataset_id'].nunique()}")
    print(f"  File size: {combined_file.stat().st_size / 1024 / 1024:.1f} MB")

# Save metadata
metadata_df = pd.DataFrame(metadata)
metadata_file = LOCAL_OECD / f"[{datetime.now().strftime('%Y.%m.%d')}] oecd_metadata.csv"
metadata_df.to_csv(metadata_file, index=False)

print(f"\nMetadata saved: {metadata_file.name}")
print(f"  Datasets cataloged: {len(metadata_df)}")

# Summary
print("\n" + "=" * 80)
print("DOWNLOAD COMPLETE")
print("=" * 80)
print(f"Successful downloads: {download_stats['successful']}/{len(OECD_CSV_URLS)}")
print(f"Failed downloads: {download_stats['failed']}")
print(f"Total records: {download_stats['total_records']:,}")

if download_stats['errors']:
    print(f"\nErrors ({len(download_stats['errors'])}):")
    for error in download_stats['errors']:
        print(f"  - {error}")

# Analyze coverage
if all_data:
    print("\n" + "=" * 80)
    print("COVERAGE ANALYSIS")
    print("=" * 80)

    # Get unique countries (LOCATION column)
    if 'LOCATION' in combined.columns:
        countries = combined['LOCATION'].unique()
        print(f"Countries: {len(countries)}")
        print(f"  {', '.join(sorted(countries)[:20])}...")

    # Date range (TIME column)
    if 'TIME' in combined.columns:
        years = combined['TIME'].unique()
        print(f"\nYears: {len(years)}")
        print(f"  Range: {min(years)} to {max(years)}")

print("\n" + "=" * 80)
print(f"Output directory: {LOCAL_OECD}")
print("Files created:")
print(f"  1. {combined_file.name if 'combined_file' in locals() else 'N/A'} - All employment data")
print(f"  2. {metadata_file.name if 'metadata_file' in locals() else 'N/A'} - Dataset metadata")
print(f"  3. {download_stats['successful']} individual dataset CSV files")
print("=" * 80)
