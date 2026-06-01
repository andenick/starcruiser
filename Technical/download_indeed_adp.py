"""
Download Indeed Job Postings and ADP Employment Report from FRED
=================================================================

Indeed Job Postings Index: Daily job postings data (leading indicator)
ADP National Employment Report: Monthly private sector employment

Both available through FRED API (no key required for these public series)
"""

import pandas as pd
from pathlib import Path
import requests
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Paths
LOCAL_EXTERNAL = (PROJECT_ROOT / "Inputs/External")
INDEED_PATH = LOCAL_EXTERNAL / "INDEED"
ADP_PATH = LOCAL_EXTERNAL / "ADP"

# Create directories
INDEED_PATH.mkdir(parents=True, exist_ok=True)
ADP_PATH.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("DOWNLOADING INDEED JOB POSTINGS INDEX")
print("=" * 80)

# Indeed Job Postings Index - U.S.
# FRED series: IHLIDXUS (Indeed Hiring Lab Index US)
indeed_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IHLIDXUS"

try:
    print(f"\nDownloading from FRED: {indeed_url}")
    response = requests.get(indeed_url, timeout=60)
    response.raise_for_status()

    # Save raw data
    indeed_file = INDEED_PATH / f"[{datetime.now().strftime('%Y.%m.%d')}] indeed_job_postings_us.csv"
    with open(indeed_file, 'wb') as f:
        f.write(response.content)

    print(f"[OK] Downloaded: {indeed_file.name}")
    print(f"  Size: {indeed_file.stat().st_size / 1024:.1f} KB")

    # Load and analyze
    df = pd.read_csv(indeed_file)
    print(f"  Records: {len(df):,}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Date range: {df.iloc[0, 0]} to {df.iloc[-1, 0]}")
    print(f"  Latest value: {df.iloc[-1, 1]}")

except Exception as e:
    print(f"[ERROR] Error downloading Indeed data: {e}")

print("\n" + "=" * 80)
print("DOWNLOADING ADP NATIONAL EMPLOYMENT REPORT")
print("=" * 80)

# ADP National Employment Report - Multiple series
adp_series = {
    'ADPMNUSNERSA': 'ADP National Employment - Total Nonfarm Private',
    'ADPMGOOD': 'ADP - Goods Producing',
    'ADPMSERV': 'ADP - Service Providing',
    'ADPMLARG': 'ADP - Large Establishments (500+)',
    'ADPMMED': 'ADP - Medium Establishments (50-499)',
    'ADPMSMALL': 'ADP - Small Establishments (1-49)',
}

adp_data_all = []

for series_id, series_name in adp_series.items():
    try:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        print(f"\nDownloading {series_id}: {series_name}")

        response = requests.get(url, timeout=60)
        response.raise_for_status()

        # Save individual series
        series_file = ADP_PATH / f"{series_id}.csv"
        with open(series_file, 'wb') as f:
            f.write(response.content)

        # Load and add to combined dataset
        df = pd.read_csv(series_file)
        df['series_id'] = series_id
        df['series_name'] = series_name
        adp_data_all.append(df)

        print(f"  [OK] {len(df):,} records ({df.iloc[0, 0]} to {df.iloc[-1, 0]})")

    except Exception as e:
        print(f"  [ERROR] Error: {e}")

# Combine all ADP series
if adp_data_all:
    combined_adp = pd.concat(adp_data_all, ignore_index=True)
    combined_file = ADP_PATH / f"[{datetime.now().strftime('%Y.%m.%d')}] adp_employment_all_series.csv"
    combined_adp.to_csv(combined_file, index=False)

    print(f"\n[OK] Combined ADP data saved: {combined_file.name}")
    print(f"  Total records: {len(combined_adp):,}")
    print(f"  Series count: {combined_adp['series_id'].nunique()}")
    print(f"  File size: {combined_file.stat().st_size / 1024:.1f} KB")

print("\n" + "=" * 80)
print("DOWNLOAD COMPLETE")
print("=" * 80)
print(f"Indeed data: {INDEED_PATH}")
print(f"ADP data: {ADP_PATH}")
print("=" * 80)
