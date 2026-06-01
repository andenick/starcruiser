"""
BLS HTTP Bulk Data Downloader
===============================

Downloads Bureau of Labor Statistics bulk data via HTTP.
Fallback when FTP is unavailable.

BLS provides data via HTTPS at: https://download.bls.gov/pub/time.series/

Target Series (prioritized for employment):
- CE: Current Employment Statistics (National) - 500 MB
- SM: State & Metro Area Employment - 2-3 GB
- LA: Local Area Unemployment Statistics - 3-5 GB
- LN: Labor Force Statistics (CPS) - 500 MB
- OE: Occupational Employment Statistics - 1.5 GB

Total estimated: 8-12 GB
"""

import requests
from pathlib import Path
from datetime import datetime
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Paths
LOCAL_BLS = (PROJECT_ROOT / "Inputs/External/BLS_FTP")

# Create directories
LOCAL_BLS.mkdir(parents=True, exist_ok=True)
for series in ['CE', 'SM', 'LA', 'LN', 'OE']:
    (LOCAL_BLS / series).mkdir(exist_ok=True)

# Base URL
BASE_URL = 'https://download.bls.gov/pub/time.series'

print("=" * 80)
print("BLS HTTP BULK DATA DOWNLOADER")
print("=" * 80)
print(f"Base URL: {BASE_URL}")
print(f"Output: {LOCAL_BLS}")
print()

# Series configuration
SERIES_CONFIG = {
    'ce': {
        'name': 'Current Employment Statistics',
        'priority': 1,
        'estimated_size': '500 MB',
        'files': ['ce.data.0.Current', 'ce.series', 'ce.industry', 'ce.data_type',
                  'ce.seasonal', 'ce.supersector']
    },
    'sm': {
        'name': 'State & Metro Area Employment',
        'priority': 2,
        'estimated_size': '2-3 GB',
        'files': ['sm.data.0.Current', 'sm.series', 'sm.industry', 'sm.area',
                  'sm.data_type', 'sm.state']
    },
    'la': {
        'name': 'Local Area Unemployment Statistics',
        'priority': 3,
        'estimated_size': '3-5 GB',
        'files': ['la.data.0.Current', 'la.series', 'la.area', 'la.area_type',
                  'la.measure']
    },
    'ln': {
        'name': 'Labor Force Statistics (CPS)',
        'priority': 4,
        'estimated_size': '500 MB',
        'files': ['ln.data.0.Current', 'ln.series', 'ln.data_type', 'ln.seasonal']
    },
    'oe': {
        'name': 'Occupational Employment Statistics',
        'priority': 5,
        'estimated_size': '1.5 GB',
        'files': ['oe.data.0.Current', 'oe.series', 'oe.area', 'oe.industry',
                  'oe.occupation', 'oe.data_type']
    }
}

def download_file(url, local_path, timeout=600):
    """Download file with progress tracking"""
    try:
        print(f"    Downloading {url.split('/')[-1]}...", end='', flush=True)
        start_time = time.time()

        response = requests.get(url, timeout=timeout, stream=True)

        if response.status_code == 404:
            print(f" [SKIP] Not found")
            return False

        response.raise_for_status()

        # Get file size from headers
        file_size = int(response.headers.get('content-length', 0))

        # Download with progress
        downloaded = 0
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

        elapsed = time.time() - start_time
        speed = downloaded / 1024 / 1024 / elapsed if elapsed > 0 else 0

        print(f" [OK] {downloaded / 1024 / 1024:.1f} MB in {elapsed:.1f}s ({speed:.1f} MB/s)")
        return True

    except requests.exceptions.Timeout:
        print(f" [ERROR] Timeout after {timeout}s")
        return False
    except requests.exceptions.RequestException as e:
        print(f" [ERROR] {str(e)[:60]}")
        return False
    except Exception as e:
        print(f" [ERROR] {str(e)[:60]}")
        return False

# Main download loop
print("\n" + "=" * 80)
print("DOWNLOADING BLS BULK DATA")
print("=" * 80)

download_summary = {
    'start_time': datetime.now().isoformat(),
    'series_downloaded': [],
    'files_downloaded': 0,
    'total_bytes': 0,
    'errors': []
}

for series_code, config in sorted(SERIES_CONFIG.items(), key=lambda x: x[1]['priority']):
    print(f"\n{'=' * 80}")
    print(f"[{config['priority']}/5] {config['name']} ({series_code.upper()})")
    print(f"Estimated size: {config['estimated_size']}")
    print(f"{'=' * 80}")

    output_dir = LOCAL_BLS / series_code.upper()
    files_downloaded = 0
    series_bytes = 0

    for filename in config['files']:
        local_file = output_dir / filename
        url = f"{BASE_URL}/{series_code}/{filename}"

        # Skip if already exists and is recent
        if local_file.exists():
            age_days = (datetime.now() - datetime.fromtimestamp(local_file.stat().st_mtime)).days
            if age_days < 7:
                print(f"    {filename}: [SKIP] Already downloaded ({age_days} days old)")
                files_downloaded += 1
                series_bytes += local_file.stat().st_size
                continue

        # Increase timeout for large data files
        timeout = 1800 if '.data.' in filename else 300

        if download_file(url, local_file, timeout):
            files_downloaded += 1
            download_summary['files_downloaded'] += 1
            file_size = local_file.stat().st_size
            series_bytes += file_size
            download_summary['total_bytes'] += file_size

    print(f"\n  Series {series_code.upper()} summary:")
    print(f"    Files downloaded: {files_downloaded}/{len(config['files'])}")
    print(f"    Total size: {series_bytes / 1024 / 1024:.1f} MB")

    if files_downloaded > 0:
        download_summary['series_downloaded'].append(series_code)

# Final summary
print("\n" + "=" * 80)
print("DOWNLOAD COMPLETE")
print("=" * 80)
print(f"Start time: {download_summary['start_time']}")
print(f"End time: {datetime.now().isoformat()}")
print(f"Series downloaded: {', '.join(download_summary['series_downloaded'])}")
print(f"Files downloaded: {download_summary['files_downloaded']}")
print(f"Total size: {download_summary['total_bytes'] / 1024 / 1024 / 1024:.2f} GB")

if download_summary['errors']:
    print(f"\nErrors encountered: {len(download_summary['errors'])}")
    for error in download_summary['errors']:
        print(f"  - {error}")

print(f"\nOutput directory: {LOCAL_BLS}")

# Verify what was downloaded
print("\n" + "=" * 80)
print("DOWNLOAD VERIFICATION")
print("=" * 80)

for series in ['CE', 'SM', 'LA', 'LN', 'OE']:
    series_dir = LOCAL_BLS / series
    if series_dir.exists():
        files = list(series_dir.glob('*'))
        total_size = sum(f.stat().st_size for f in files)
        print(f"{series}: {len(files)} files, {total_size / 1024 / 1024:.1f} MB")

print("\n" + "=" * 80)
print("NEXT STEPS:")
print("1. Run bls_series_decoder.py to parse series IDs")
print("2. Run cross_reference_with_robin.py to detect duplicates with the source store BLS data")
print("3. Update MASTER_CATALOG.csv with new BLS datasets")
print("=" * 80)
