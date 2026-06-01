"""
Import BLS API and OECD Social Data from the source store
================================================

BLS API Data:
- Source: <DATA_ROOT>/API_MODULES/BLS/data/
- Records: ~1,200 (2005-2025, 37 series)
- Size: 173 KB

OECD Social Data:
- Source: <DATA_ROOT>/API_MODULES/SOCIAL_SCIENCE/DATA/SOCIAL_SCIENCE_MASTER/OECD_SOCIAL/
- Records: ~100,000 (gender, education, demographics)
- Size: 577 MB (database + JSON files)
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil
import json

import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "data"))


print("=" * 80)
print("BLS API + OECD SOCIAL DATA IMPORT")
print("=" * 80)
print()

# ============================================================================
# PART 1: BLS API DATA
# ============================================================================

SOURCE_BLS = DATA_ROOT / "API_MODULES/BLS/data"
LOCAL_BLS_API = (PROJECT_ROOT / "Inputs/source/BLS_API")
LOCAL_BLS_API.mkdir(parents=True, exist_ok=True)

print("PART 1: BLS API DATA")
print("-" * 80)
print(f"Source: {SOURCE_BLS}")
print(f"Target: {LOCAL_BLS_API}")
print()

bls_stats = {'files': 0, 'records': 0, 'size_mb': 0}

if SOURCE_BLS.exists():
    bls_files = list(SOURCE_BLS.glob("*.csv"))
    print(f"Found {len(bls_files)} CSV files")

    for bls_file in sorted(bls_files):
        print(f"  Importing: {bls_file.name}")
        try:
            target = LOCAL_BLS_API / bls_file.name
            shutil.copy2(bls_file, target)

            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f) - 1

            size_mb = target.stat().st_size / 1024 / 1024

            bls_stats['files'] += 1
            bls_stats['records'] += line_count
            bls_stats['size_mb'] += size_mb

            print(f"    [OK] {line_count:,} records, {size_mb:.2f} MB")
        except Exception as e:
            print(f"    [ERROR] {str(e)[:80]}")

    # Copy JSON files too
    json_files = list(SOURCE_BLS.glob("*.json"))
    for json_file in json_files:
        shutil.copy2(json_file, LOCAL_BLS_API / json_file.name)
        print(f"  Copied metadata: {json_file.name}")

    # Create README
    readme_bls = f"""# BLS API Data

**Imported**: {datetime.now().strftime('%Y-%m-%d')}
**Source**: Bureau of Labor Statistics API via the source store
**Records**: {bls_stats['records']:,}
**Files**: {bls_stats['files']}
**Size**: {bls_stats['size_mb']:.1f} MB

## Coverage
- **Years**: 2005-2025 (20 years)
- **Series**: 37 employment and economic indicators
- **Frequency**: Monthly, quarterly, annual

## Key Series
- Employment levels (CES, payroll survey)
- Unemployment rates
- Labor force participation
- Consumer Price Index (CPI)
- Producer Price Index (PPI)
- Productivity measures
- JOLTS (Job Openings and Labor Turnover)

## Data Quality
- Official BLS statistics via API
- Regularly updated
- Seasonally adjusted and not seasonally adjusted versions

## Citation
Bureau of Labor Statistics. Retrieved via BLS API {datetime.now().year}.
From StarCruiser Employment Database.
"""

    with open(LOCAL_BLS_API / "README.md", 'w') as f:
        f.write(readme_bls)

    print(f"\nBLS API Import Complete:")
    print(f"  Files: {bls_stats['files']}")
    print(f"  Records: {bls_stats['records']:,}")
    print(f"  Size: {bls_stats['size_mb']:.1f} MB")

else:
    print("[WARNING] BLS API source directory not found")

print()

# ============================================================================
# PART 2: OECD SOCIAL DATA
# ============================================================================

SOURCE_OECD_SOCIAL = DATA_ROOT / "API_MODULES/SOCIAL_SCIENCE/DATA/SOCIAL_SCIENCE_MASTER/OECD_SOCIAL"
LOCAL_OECD_SOCIAL = (PROJECT_ROOT / "Inputs/source/OECD_SOCIAL")
LOCAL_OECD_SOCIAL.mkdir(parents=True, exist_ok=True)

print("PART 2: OECD SOCIAL DATA")
print("-" * 80)
print(f"Source: {SOURCE_OECD_SOCIAL}")
print(f"Target: {LOCAL_OECD_SOCIAL}")
print()

oecd_stats = {'files': 0, 'records': 0, 'size_mb': 0, 'databases': 0, 'json_files': 0}

if SOURCE_OECD_SOCIAL.exists():
    # Copy database files
    db_files = list(SOURCE_OECD_SOCIAL.glob("*.db"))
    for db_file in db_files:
        print(f"  Copying database: {db_file.name}")
        target = LOCAL_OECD_SOCIAL / db_file.name
        shutil.copy2(db_file, target)
        size_mb = target.stat().st_size / 1024 / 1024
        oecd_stats['databases'] += 1
        oecd_stats['size_mb'] += size_mb
        print(f"    [OK] {size_mb:.1f} MB")

    # Copy JSON files (raw data)
    json_files = list(SOURCE_OECD_SOCIAL.glob("*.json"))
    for json_file in json_files:
        target = LOCAL_OECD_SOCIAL / json_file.name
        shutil.copy2(json_file, target)
        size_mb = target.stat().st_size / 1024 / 1024
        oecd_stats['json_files'] += 1
        oecd_stats['size_mb'] += size_mb
        oecd_stats['files'] += 1

        # Try to estimate records from JSON
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    oecd_stats['records'] += len(data)
                elif isinstance(data, dict):
                    # Try common keys
                    for key in ['data', 'series', 'observations', 'values']:
                        if key in data and isinstance(data[key], list):
                            oecd_stats['records'] += len(data[key])
                            break
        except:
            pass

        if json_file.stat().st_size > 1024 * 1024:  # > 1 MB
            print(f"  Copied JSON: {json_file.name} ({size_mb:.1f} MB)")

    # Create README
    readme_oecd = f"""# OECD Social Data

**Imported**: {datetime.now().strftime('%Y-%m-%d')}
**Source**: OECD Social Indicators via the source store
**Files**: {oecd_stats['files']} (databases + JSON)
**Size**: {oecd_stats['size_mb']:.1f} MB

## Datasets Included

### Gender Employment
- Gender employment gaps
- Female labor force participation
- Gender wage gaps
- Work-family balance indicators

### Demographics
- HISTPOP: Historical population data
- Population projections
- Demographic transitions

### Education & Earnings
- Returns to education
- Educational attainment by cohort
- Earnings by education level

### Health
- Healthy life expectancy
- Disability and employment
- Health-related labor force exits

### Social Protection
- Family policies
- Work-family balance
- Disability support

## Data Format
- **Databases**: SQLite format (`.db` files)
- **Raw Data**: JSON format (original OECD API responses)
- **Coverage**: OECD member countries + partners
- **Years**: Varies by indicator (typically 1990-2023)

## Usage
Import SQLite databases with pandas or use JSON files for raw data access.

## Citation
OECD. Social and Welfare Statistics. Retrieved via OECD SDMX API {datetime.now().year}.
From StarCruiser Employment Database.
"""

    with open(LOCAL_OECD_SOCIAL / "README.md", 'w') as f:
        f.write(readme_oecd)

    print(f"\nOECD Social Import Complete:")
    print(f"  Databases: {oecd_stats['databases']}")
    print(f"  JSON files: {oecd_stats['json_files']}")
    print(f"  Estimated records: {oecd_stats['records']:,}")
    print(f"  Total size: {oecd_stats['size_mb']:.1f} MB")

else:
    print("[WARNING] OECD Social source directory not found")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("IMPORT SUMMARY")
print("=" * 80)
print(f"\nBLS API Data:")
print(f"  Files: {bls_stats['files']}")
print(f"  Records: {bls_stats['records']:,}")
print(f"  Size: {bls_stats['size_mb']:.1f} MB")
print(f"  Location: {LOCAL_BLS_API}")

print(f"\nOECD Social Data:")
print(f"  Files: {oecd_stats['files']}")
print(f"  Databases: {oecd_stats['databases']}")
print(f"  Estimated records: {oecd_stats['records']:,}")
print(f"  Size: {oecd_stats['size_mb']:.1f} MB")
print(f"  Location: {LOCAL_OECD_SOCIAL}")

total_records = bls_stats['records'] + oecd_stats['records']
total_size = bls_stats['size_mb'] + oecd_stats['size_mb']

print(f"\nTOTAL IMPORTED:")
print(f"  Combined records: {total_records:,}")
print(f"  Combined size: {total_size:.1f} MB")
print("=" * 80)
