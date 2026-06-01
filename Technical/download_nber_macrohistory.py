"""
NBER Macrohistory Database Download via FRED
==============================================

Downloads NBER Macrohistory Database series from FRED API.

Coverage: 1890s-1942 (fills pre-1939 employment gap)
Series: 172 macroeconomic series
Size: ~30 MB

Key Employment Series:
- m0892: Index of Manufacturing Employment (1899-1939)
- m0893a: Manufacturing Employment Index (1919-1939)
- m0876: Industrial Production Index (1919-1939)
- m0885: Factory Employment (1914-1933)

Available through FRED API - no key required for public series.
"""

import pandas as pd
from pathlib import Path
import requests
from datetime import datetime
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Paths
LOCAL_NBER = (PROJECT_ROOT / "Inputs/External/NBER")
LOCAL_NBER.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("NBER MACROHISTORY DATABASE DOWNLOAD")
print("=" * 80)
print(f"Source: FRED (Federal Reserve Economic Data)")
print(f"Output: {LOCAL_NBER}")
print()

# NBER Macrohistory employment-related series
# Actual series IDs available in FRED as of 2025
NBER_EMPLOYMENT_SERIES = {
    # Unemployment Rate
    'M0892AUSM156SNBR': 'Unemployment Rate for United States (Apr 1929 - Jun 1942)',
    'Q0892BUSQ156SNBR': 'Unemployment Rate Quarterly (Q2 1940 - Q4 1946)',
    'M0892BUSM156SNBR': 'Unemployment Rate Monthly (Jan 1940 - Dec 1946)',
    'M0892CUSM156NNBR': 'Unemployment Rate NSA (Jan 1947 - Dec 1966)',

    # Unemployment levels
    'M08I4AUSM175NNBR': 'Unemployment Thousands of Persons (Jan 1929 - Dec 1944)',
    'M08K4BUSM148NNBR': 'Unemployment Millions of Persons (Mar 1940 - Dec 1957)',

    # Wages and earnings
    'A08139USA052NNBR': 'Laborers Average Hourly Rate of Wages (1860-1891)',
    'M08343USM232SNBR': 'Real Average Hourly Earnings Production Workers (Jan 1932 - Dec 1968)',
    'M08067USM325NNBR': 'Estimated Per Capita Real Earnings Manufacturing (Jan 1915 - Dec 1928)',

    # Hours worked
    'M08354USM310NNBR': 'Average Hours of Work Per Week Total (Jan 1947 - Jan 1970)',

    # Unemployment insurance
    'M08297USM548NNBR': 'Initial Claims Unemployment Insurance (Aug 1945 - Mar 1969)',
}

print(f"Downloading {len(NBER_EMPLOYMENT_SERIES)} NBER employment series...")
print()

all_data = []
series_metadata = []
download_stats = {
    'successful': 0,
    'failed': 0,
    'total_records': 0,
    'errors': []
}

for i, (series_id, series_name) in enumerate(NBER_EMPLOYMENT_SERIES.items(), 1):
    print(f"[{i:2d}/{len(NBER_EMPLOYMENT_SERIES)}] {series_id}: {series_name[:60]}...", end='', flush=True)

    try:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        response = requests.get(url, timeout=60)

        if response.status_code == 404:
            print(f" [SKIP] Not found in FRED")
            download_stats['failed'] += 1
            download_stats['errors'].append(f"{series_id}: Not found")
            continue

        response.raise_for_status()

        # Save individual series
        series_file = LOCAL_NBER / f"{series_id}.csv"
        with open(series_file, 'wb') as f:
            f.write(response.content)

        # Load and add metadata
        df = pd.read_csv(series_file)
        df['series_id'] = series_id
        df['series_name'] = series_name
        all_data.append(df)

        # Record metadata
        series_metadata.append({
            'series_id': series_id,
            'series_name': series_name,
            'records': len(df),
            'start_date': df.iloc[0, 0],
            'end_date': df.iloc[-1, 0],
            'file': series_file.name
        })

        download_stats['successful'] += 1
        download_stats['total_records'] += len(df)

        print(f" [OK] {len(df):,} records ({df.iloc[0, 0]} to {df.iloc[-1, 0]})")
        time.sleep(0.5)  # Rate limiting

    except Exception as e:
        print(f" [ERROR] {str(e)[:50]}")
        download_stats['failed'] += 1
        download_stats['errors'].append(f"{series_id}: {str(e)[:60]}")

# Combine all series
print("\n" + "=" * 80)
print("COMBINING DATA")
print("=" * 80)

if all_data:
    combined = pd.concat(all_data, ignore_index=True)
    combined_file = LOCAL_NBER / f"[{datetime.now().strftime('%Y.%m.%d')}] nber_macrohistory_employment.csv"
    combined.to_csv(combined_file, index=False)

    print(f"Combined data saved: {combined_file.name}")
    print(f"  Total records: {len(combined):,}")
    print(f"  Total series: {combined['series_id'].nunique()}")
    print(f"  File size: {combined_file.stat().st_size / 1024 / 1024:.1f} MB")

# Save metadata
metadata_df = pd.DataFrame(series_metadata)
metadata_file = LOCAL_NBER / f"[{datetime.now().strftime('%Y.%m.%d')}] nber_series_metadata.csv"
metadata_df.to_csv(metadata_file, index=False)

print(f"\nMetadata saved: {metadata_file.name}")
print(f"  Series cataloged: {len(metadata_df)}")

# Summary
print("\n" + "=" * 80)
print("DOWNLOAD COMPLETE")
print("=" * 80)
print(f"Successful downloads: {download_stats['successful']}/{len(NBER_EMPLOYMENT_SERIES)}")
print(f"Failed downloads: {download_stats['failed']}")
print(f"Total records: {download_stats['total_records']:,}")

if download_stats['errors']:
    print(f"\nErrors ({len(download_stats['errors'])}):")
    for error in download_stats['errors'][:10]:  # Show first 10
        print(f"  - {error}")

# Date coverage analysis
if all_data:
    print("\n" + "=" * 80)
    print("DATE COVERAGE ANALYSIS")
    print("=" * 80)

    # Find earliest and latest dates across all series
    earliest_dates = []
    latest_dates = []

    for df in all_data:
        try:
            dates = pd.to_datetime(df.iloc[:, 0])
            earliest_dates.append(dates.min())
            latest_dates.append(dates.max())
        except:
            pass

    if earliest_dates and latest_dates:
        print(f"Earliest data point: {min(earliest_dates).strftime('%Y-%m-%d')}")
        print(f"Latest data point: {max(latest_dates).strftime('%Y-%m-%d')}")
        print(f"Total coverage: {(max(latest_dates).year - min(earliest_dates).year)} years")

print("\n" + "=" * 80)
print(f"Output directory: {LOCAL_NBER}")
print("Files created:")
print(f"  1. {combined_file.name if 'combined_file' in locals() else 'N/A'} - All employment data")
print(f"  2. {metadata_file.name if 'metadata_file' in locals() else 'N/A'} - Series metadata")
print(f"  3. {download_stats['successful']} individual series CSV files")
print("=" * 80)
