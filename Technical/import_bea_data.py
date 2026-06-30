"""
Import BEA Data from the source store to StarCruiser
==========================================

Imports Bureau of Economic Analysis National Income and Product Accounts:
- NIPA Tables (25+ tables, 1929-2025)
- Regional Data (state-level GDP, income, employment)

Source: <DATA_ROOT>/API_MODULES/BEA/data/
Target: <repo>/Inputs/source/BEA/

Total Records: ~50,000
Size: ~800 KB
Coverage: US National Accounts
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil

import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "data"))


# Paths
SOURCE_BEA = DATA_ROOT / "API_MODULES/BEA/data"
LOCAL_BEA = (PROJECT_ROOT / "Inputs/source/BEA")
LOCAL_BEA.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("BEA DATA IMPORT FROM SOURCE STORE")
print("=" * 80)
print(f"Source: {SOURCE_BEA}")
print(f"Target: {LOCAL_BEA}")
print()

# Check source exists
if not SOURCE_BEA.exists():
    print(f"[ERROR] Source directory not found: {SOURCE_BEA}")
    exit(1)

# Find all BEA CSV files
bea_files = list(SOURCE_BEA.glob("*.csv"))
print(f"Found {len(bea_files)} CSV files in source BEA directory")
print()

import_stats = {
    'files_copied': 0,
    'total_records': 0,
    'total_size_mb': 0,
    'import_date': datetime.now().isoformat(),
    'nipa_tables': 0,
    'regional_files': 0
}

# Import each file
for bea_file in sorted(bea_files):
    print(f"Importing: {bea_file.name}")

    try:
        # Copy file to StarCruiser
        target_file = LOCAL_BEA / bea_file.name
        shutil.copy2(bea_file, target_file)

        # Get stats
        file_size = target_file.stat().st_size / 1024 / 1024

        # Read to get record count
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            line_count = sum(1 for _ in f) - 1  # Subtract header

        # Read sample
        df = pd.read_csv(target_file, nrows=100)

        import_stats['files_copied'] += 1
        import_stats['total_records'] += line_count
        import_stats['total_size_mb'] += file_size

        # Categorize file type
        if 'nipa' in bea_file.name.lower() or 'expanded' in bea_file.name.lower():
            import_stats['nipa_tables'] += 1
            file_type = "NIPA"
        elif 'regional' in bea_file.name.lower():
            import_stats['regional_files'] += 1
            file_type = "Regional"
        else:
            file_type = "Other"

        print(f"  [OK] Type: {file_type}, {file_size:.2f} MB, {line_count:,} records")
        print(f"  Columns ({len(df.columns)}): {', '.join(df.columns[:5].tolist())}")

    except Exception as e:
        print(f"  [ERROR] Failed to import: {str(e)[:100]}")

    print()

# Create README
readme_content = f"""# BEA Data - Bureau of Economic Analysis

## Overview
Imported from the source store: {datetime.now().strftime('%Y-%m-%d')}

**Source**: Bureau of Economic Analysis via the source store API_MODULES
**Coverage**: United States (National and State-level)
**Records**: {import_stats['total_records']:,}
**Size**: {import_stats['total_size_mb']:.1f} MB

## Datasets Included

### NIPA Tables (National Income and Product Accounts)
- **Tables**: {import_stats['nipa_tables']} files
- **Years**: 1929-2025 (97 years, annual and quarterly)
- **Content**: GDP, personal income, government receipts/expenditures, corporate profits

**Key Employment-Relevant Tables**:
- **T10101-T10105**: Domestic income and product accounts
  - Compensation of employees
  - Wages and salaries
  - Employer contributions for social insurance

- **T20100**: Income distribution
  - Personal income by state
  - Wage and salary disbursements

- **T30100**: Personal income and outlays
  - Disposable personal income
  - Personal consumption expenditures

- **T40100**: Government accounts
  - Government wages and salaries
  - Social benefit payments (unemployment insurance, etc.)

- **T50100**: Supplemental tables
  - National income by industry
  - Corporate profits

### Regional Data
- **Files**: {import_stats['regional_files']}
- **Coverage**: State-level economic indicators
- **Variables**:
  - Gross Domestic Product by state
  - Personal income by state
  - Regional employment indicators
  - State-level compensation

## Data Quality
- **Frequency**: Annual (1929+), Quarterly (2010+)
- **Source**: Official BEA statistics
- **Revisions**: Data includes latest BEA revisions
- **Seasonal Adjustment**: Both seasonally adjusted and not seasonally adjusted series

## Usage Notes
- NIPA tables use BEA's standardized table numbers (T10101, etc.)
- Data is in millions of current dollars unless otherwise noted
- Some series have been discontinued or revised over time
- Regional data uses BEA's state codes

## Integration with StarCruiser
- **Complements**: BLS employment data (BEA provides income context)
- **Overlaps**: FRED national accounts (FRED sources from BEA)
- **Unique**: Historical national accounts going back to 1929
- **Value**: Links employment to GDP, income, productivity

## Source Documentation
- Source location: `<DATA_ROOT>/API_MODULES/BEA/`
- Collection date: {import_stats['import_date']}
- BEA Website: https://www.bea.gov/
- NIPA Handbook: https://www.bea.gov/resources/methodologies/nipa-handbook

## Citation
Bureau of Economic Analysis. National Income and Product Accounts.
Retrieved via BEA API, {datetime.now().year}.
From StarCruiser Employment Database.
"""

readme_file = LOCAL_BEA / "README.md"
with open(readme_file, 'w', encoding='utf-8') as f:
    f.write(readme_content)

print("=" * 80)
print("IMPORT COMPLETE")
print("=" * 80)
print(f"Files imported: {import_stats['files_copied']}")
print(f"  NIPA tables: {import_stats['nipa_tables']}")
print(f"  Regional files: {import_stats['regional_files']}")
print(f"Total records: {import_stats['total_records']:,}")
print(f"Total size: {import_stats['total_size_mb']:.1f} MB")
print(f"README created: {readme_file.name}")
print()
print(f"Target directory: {LOCAL_BEA}")
print("=" * 80)
