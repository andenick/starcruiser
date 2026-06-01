"""
BLS FTP Bulk Data Downloader
==============================

Downloads Bureau of Labor Statistics bulk data files from FTP server.

Target Series (prioritized for employment):
- CE: Current Employment Statistics (National) - 500 MB
- SM: State & Metro Area Employment - 2-3 GB
- LA: Local Area Unemployment Statistics - 3-5 GB
- LN: Labor Force Statistics (CPS) - 500 MB
- OE: Occupational Employment Statistics - 1.5 GB

Total estimated: 8-12 GB

FTP Server: ftp.bls.gov
Path: /pub/time.series/

Files per series:
- *.data.*.Current - Latest data
- *.series - Series definitions
- *.industry - Industry codes
- *.area - Area codes
- *.data_type - Data type codes

Strategy:
1. Download series metadata files first (small, essential for decoding)
2. Download current data files (large)
3. Extract and validate
4. Cross-reference with the source store's BLS API data
5. Update master catalog

Note: BLS FTP is public, no credentials required
"""

import ftplib
import os
from pathlib import Path
from datetime import datetime
import zipfile
import gzip
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "data"))


# Paths
LOCAL_BLS = (PROJECT_ROOT / "Inputs/External/BLS_FTP")
SOURCE_BLS = DATA_ROOT / "API_MODULES/BLS/data"

# Create directories
LOCAL_BLS.mkdir(parents=True, exist_ok=True)
for series in ['CE', 'SM', 'LA', 'LN', 'OE']:
    (LOCAL_BLS / series).mkdir(exist_ok=True)

# FTP connection
FTP_HOST = 'ftp.bls.gov'
FTP_BASE_PATH = '/pub/time.series'

print("=" * 80)
print("BLS FTP BULK DATA DOWNLOADER")
print("=" * 80)
print(f"FTP Server: {FTP_HOST}")
print(f"Output: {LOCAL_BLS}")
print()

# Series to download with priority order
SERIES_CONFIG = {
    'ce': {
        'name': 'Current Employment Statistics',
        'priority': 1,
        'estimated_size': '500 MB',
        'files': ['ce.data.0.Current', 'ce.series', 'ce.industry', 'ce.data_type',
                  'ce.seasonal', 'ce.supersector', 'ce.state']
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
                  'la.measure', 'la.state']
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

def download_file(ftp, remote_path, local_path):
    """Download a file from FTP server"""
    try:
        file_size = ftp.size(remote_path)
        print(f"    Downloading {remote_path} ({file_size / 1024 / 1024:.1f} MB)...", end='', flush=True)

        start_time = time.time()
        with open(local_path, 'wb') as f:
            ftp.retrbinary(f'RETR {remote_path}', f.write)

        elapsed = time.time() - start_time
        speed = file_size / 1024 / 1024 / elapsed if elapsed > 0 else 0

        print(f" [OK] {elapsed:.1f}s ({speed:.1f} MB/s)")
        return True

    except ftplib.error_perm as e:
        if '550' in str(e):  # File not found
            print(f" [SKIP] Not found")
        else:
            print(f" [ERROR] {e}")
        return False
    except Exception as e:
        print(f" [ERROR] {e}")
        return False

def connect_ftp():
    """Connect to BLS FTP server"""
    print("Connecting to BLS FTP server...")
    try:
        ftp = ftplib.FTP(FTP_HOST, timeout=60)
        ftp.login()  # Anonymous login
        print(f"  [OK] Connected to {FTP_HOST}")
        return ftp
    except Exception as e:
        print(f"  [ERROR] Connection failed: {e}")
        return None

# Main download loop
print("\n" + "=" * 80)
print("DOWNLOADING BLS BULK DATA")
print("=" * 80)

ftp = connect_ftp()
if not ftp:
    print("Failed to connect to FTP server. Exiting.")
    exit(1)

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

    series_path = f"{FTP_BASE_PATH}/{series_code}"
    output_dir = LOCAL_BLS / series_code.upper()

    # Change to series directory
    try:
        ftp.cwd(series_path)
        print(f"  Changed to: {series_path}")
    except Exception as e:
        print(f"  [ERROR] Cannot access {series_path}: {e}")
        download_summary['errors'].append(f"{series_code}: {e}")
        continue

    # Download each file in the series
    files_downloaded = 0
    series_bytes = 0

    for filename in config['files']:
        local_file = output_dir / filename

        # Skip if already exists and is recent (downloaded in last 7 days)
        if local_file.exists():
            age_days = (datetime.now() - datetime.fromtimestamp(local_file.stat().st_mtime)).days
            if age_days < 7:
                print(f"    {filename}: [SKIP] Already downloaded ({age_days} days old)")
                continue

        if download_file(ftp, filename, local_file):
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

# Close FTP connection
ftp.quit()
print(f"\n  Disconnected from {FTP_HOST}")

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
print("=" * 80)

# Next steps message
print("\nNEXT STEPS:")
print("1. Run bls_series_decoder.py to parse series IDs")
print("2. Run cross_reference_with_robin.py to detect duplicates with the source store BLS data")
print("3. Update MASTER_CATALOG.csv with new BLS datasets")
print("=" * 80)
