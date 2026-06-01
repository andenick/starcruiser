"""
Import CENSUS Data from the source store to StarCruiser
=============================================

Imports comprehensive US Census Bureau employment data:
- American Community Survey (ACS) 2010-2022
- County Business Patterns (CBP) 2012-2022
- Decennial Census 2010, 2020

Source: <DATA_ROOT>/API_MODULES/CENSUS/data/
Target: <repo>/Inputs/source/CENSUS/

Total Records: ~173,280
Size: ~36 MB
Coverage: 3,220+ US counties, 13 years
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil

import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "data"))


# Paths
SOURCE_CENSUS = DATA_ROOT / "API_MODULES/CENSUS/data"
LOCAL_CENSUS = (PROJECT_ROOT / "Inputs/source/CENSUS")
LOCAL_CENSUS.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("CENSUS DATA IMPORT FROM ROBIN")
print("=" * 80)
print(f"Source: {SOURCE_CENSUS}")
print(f"Target: {LOCAL_CENSUS}")
print()

# Check source exists
if not SOURCE_CENSUS.exists():
    print(f"[ERROR] Source directory not found: {SOURCE_CENSUS}")
    exit(1)

# Find all CENSUS CSV files
census_files = list(SOURCE_CENSUS.glob("*.csv"))
print(f"Found {len(census_files)} CSV files in the source store CENSUS directory")
print()

import_stats = {
    'files_copied': 0,
    'total_records': 0,
    'total_size_mb': 0,
    'import_date': datetime.now().isoformat()
}

# Import each file
for census_file in sorted(census_files):
    print(f"Importing: {census_file.name}")

    try:
        # Copy file to StarCruiser
        target_file = LOCAL_CENSUS / census_file.name
        shutil.copy2(census_file, target_file)

        # Get stats
        file_size = target_file.stat().st_size / 1024 / 1024

        # Read to get record count
        df = pd.read_csv(target_file, nrows=10000)  # Sample for speed

        # Try to estimate full record count
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            line_count = sum(1 for _ in f) - 1  # Subtract header

        import_stats['files_copied'] += 1
        import_stats['total_records'] += line_count
        import_stats['total_size_mb'] += file_size

        print(f"  [OK] Copied: {file_size:.1f} MB, {line_count:,} records")
        print(f"  Columns: {len(df.columns)}")
        print(f"  Sample columns: {', '.join(df.columns[:5].tolist())}")

    except Exception as e:
        print(f"  [ERROR] Failed to import: {str(e)[:100]}")

    print()

# Create README
readme_content = f"""# CENSUS Data - US Census Bureau Employment Statistics

## Overview
Imported from the source store: {datetime.now().strftime('%Y-%m-%d')}

**Source**: US Census Bureau via the source store API_MODULES
**Coverage**: United States (county-level detail)
**Records**: {import_stats['total_records']:,}
**Size**: {import_stats['total_size_mb']:.1f} MB

## Datasets Included

### American Community Survey (ACS)
- **Years**: 2010-2022 (13 years)
- **Type**: 5-year estimates + selected 1-year estimates
- **Variables**: Demographics, economics, employment, housing, education
- **Key Employment Fields**:
  - Employment status (employed, unemployed, not in labor force)
  - Occupation codes (SOC classification)
  - Industry codes (NAICS classification)
  - Income and wages
  - Work hours and commute patterns

### County Business Patterns (CBP)
- **Years**: 2012-2022 (11 years)
- **Coverage**: 3,220+ US counties
- **Variables**: Establishments, employment, payroll by industry
- **Detail**: Industry breakdowns (2-6 digit NAICS)

### Decennial Census
- **Years**: 2010, 2020
- **Type**: Full population count
- **Employment Data**: Labor force participation, occupation, industry

## Data Quality
- **Completeness**: High (Census Bureau official statistics)
- **Frequency**: Annual (ACS), Annual (CBP), Decadal (Census)
- **Geographic Detail**: County, State, National
- **Industry Detail**: NAICS 2-6 digit codes

## Usage Notes
- ACS data uses margin of error estimates (MOE) - check for confidence intervals
- CBP suppresses data for disclosure avoidance (small cell sizes)
- Decennial Census is complete enumeration, ACS is survey-based
- All data uses Census Bureau's geographic codes (FIPS)

## Integration with StarCruiser
- **Complements**: BLS data (national vs county-level)
- **Overlaps**: FRED local area employment (different methodologies)
- **Extends**: Geographic coverage to all 3,220+ US counties

## Source Documentation
- Source location: `<DATA_ROOT>/API_MODULES/CENSUS/`
- Collection date: {import_stats['import_date']}
- Census Bureau: https://www.census.gov/
- API Documentation: https://www.census.gov/data/developers.html

## Citation
US Census Bureau. American Community Survey, County Business Patterns, and Decennial Census.
Accessed via Census API, {datetime.now().year}.
Retrieved from StarCruiser Employment Database.
"""

readme_file = LOCAL_CENSUS / "README.md"
with open(readme_file, 'w', encoding='utf-8') as f:
    f.write(readme_content)

print("=" * 80)
print("IMPORT COMPLETE")
print("=" * 80)
print(f"Files imported: {import_stats['files_copied']}")
print(f"Total records: {import_stats['total_records']:,}")
print(f"Total size: {import_stats['total_size_mb']:.1f} MB")
print(f"README created: {readme_file.name}")
print()
print(f"Target directory: {LOCAL_CENSUS}")
print("=" * 80)
