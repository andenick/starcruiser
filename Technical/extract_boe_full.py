"""
Bank of England Millennium Database - FULL EXTRACTION
======================================================

Extracts ALL 109 sheets from the Bank of England Millennium Database.

Current StarCruiser import: Only 3 sheets (sample)
This script: ALL 109 sheets (FULL dataset)

Coverage: 1086-2016 (930 years of UK economic history!)

Key Employment Sheets:
- A47. Wages and prices
- A48. Real Earnings
- A49. GB Employment in C18th
- A50. Employment & unemployment
- A51. Public Sector Employment
- A52a. Wages, Salaries and Comp
- A52b. Other labour statistics
- A53. Employment by industry
- A54. Hours worked
- A56. Productivity
- M4. Monthly IP 1920+
- M5. Administrative unemp 1881+
- M6. Monthly prices and wages
- Q6. Quarterly labour market Qs

Input: <DATA_ROOT>/DATA/BoE/
Output: <repo>/Inputs/source/BOE/
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
SOURCE_BOE_PATH = DATA_ROOT / "DATA/BoE"
LOCAL_INPUT = (PROJECT_ROOT / "Inputs/source/BOE")
LOCAL_OUTPUT = OUTPUT_ROOT

# Create output directories
LOCAL_INPUT.mkdir(parents=True, exist_ok=True)
(LOCAL_INPUT / "sheets").mkdir(exist_ok=True)

print("=" * 80)
print("BANK OF ENGLAND MILLENNIUM DATABASE - FULL EXTRACTION")
print("=" * 80)
print(f"Source: {SOURCE_BOE_PATH}")
print(f"Target: {LOCAL_INPUT}")
print()

# Step 1: Load Excel file and get all sheets
print("Step 1: Loading Bank of England Millennium Database...")
boe_file = SOURCE_BOE_PATH / "[2025.10.09] boe_millennium_data.xlsx"
print(f"  File: {boe_file.name}")
print(f"  Size: {boe_file.stat().st_size / 1024 / 1024:.1f} MB")

xl = pd.ExcelFile(boe_file)
print(f"  Total sheets: {len(xl.sheet_names)}")

# Step 2: Identify employment-related sheets
print("\nStep 2: Identifying employment-related sheets...")
employment_keywords = ['employ', 'labor', 'labour', 'wage', 'salary', 'hour',
                       'earning', 'compensation', 'productivity', 'unemp',
                       'workforce', 'job', 'worker', 'population', 'pop']

employment_sheets = []
for sheet in xl.sheet_names:
    if any(keyword in sheet.lower() for keyword in employment_keywords):
        employment_sheets.append(sheet)

print(f"  Employment-related sheets found: {len(employment_sheets)}")
for sheet in employment_sheets:
    print(f"    - {sheet}")

# Step 3: Extract all sheets
print("\nStep 3: Extracting ALL sheets...")
sheet_info = []
total_records = 0

# Skip metadata/info sheets
skip_sheets = ['Disclaimer', 'Corrections to V3.1', 'Front page',
               'BEG Table of contents', 'Notes on GDP estimates']

for i, sheet_name in enumerate(xl.sheet_names, 1):
    print(f"  [{i:3d}/{len(xl.sheet_names)}] Processing: {sheet_name[:50]}...", end='')

    if sheet_name in skip_sheets:
        print(" [SKIPPED - metadata]")
        continue

    try:
        # Read the sheet
        df = pd.read_excel(xl, sheet_name=sheet_name)

        # Save as CSV
        clean_name = sheet_name.replace('/', '_').replace(':', '_').replace('?', '_')
        output_file = LOCAL_INPUT / "sheets" / f"{clean_name}.csv"
        df.to_csv(output_file, index=False, encoding='utf-8')

        # Record info
        is_employment = sheet_name in employment_sheets
        records = len(df)
        total_records += records

        sheet_info.append({
            'sheet_number': i,
            'sheet_name': sheet_name,
            'records': records,
            'columns': len(df.columns),
            'is_employment_related': is_employment,
            'file_size_kb': output_file.stat().st_size / 1024
        })

        print(f" [OK] {records:,} records, {len(df.columns)} cols")

    except Exception as e:
        print(f" [ERROR] {str(e)[:50]}")
        sheet_info.append({
            'sheet_number': i,
            'sheet_name': sheet_name,
            'error': str(e),
            'is_employment_related': sheet_name in employment_sheets
        })

print(f"\n  Total records extracted: {total_records:,}")

# Step 4: Create combined employment dataset
print("\nStep 4: Creating combined employment dataset...")
employment_data = {}

for sheet in employment_sheets:
    try:
        clean_name = sheet.replace('/', '_').replace(':', '_').replace('?', '_')
        file_path = LOCAL_INPUT / "sheets" / f"{clean_name}.csv"
        if file_path.exists():
            df = pd.read_csv(file_path)
            employment_data[sheet] = df
            print(f"  Loaded: {sheet} ({len(df):,} records)")
    except Exception as e:
        print(f"  ERROR loading {sheet}: {e}")

print(f"\n  Total employment sheets loaded: {len(employment_data)}")

# Step 5: Save sheet inventory
print("\nStep 5: Saving sheet inventory...")
sheet_df = pd.DataFrame(sheet_info)
inventory_file = LOCAL_OUTPUT / "BOE_SHEET_INVENTORY.csv"
sheet_df.to_csv(inventory_file, index=False, encoding='utf-8')
print(f"  Saved to: {inventory_file.name}")

# Step 6: Create metadata summary
print("\nStep 6: Creating metadata summary...")
summary_stats = {
    'extraction_date': datetime.now().isoformat(),
    'source_file': str(boe_file),
    'total_sheets': len(xl.sheet_names),
    'sheets_extracted': len([s for s in sheet_info if 'error' not in s]),
    'sheets_skipped': len([s for s in sheet_info if s.get('sheet_name') in skip_sheets]),
    'sheets_with_errors': len([s for s in sheet_info if 'error' in s]),
    'total_records': total_records,
    'employment_sheets': len(employment_sheets),
    'employment_sheet_names': employment_sheets,
    'all_sheet_names': xl.sheet_names
}

summary_file = LOCAL_INPUT / "boe_extraction_summary.json"
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary_stats, f, indent=2)
print(f"  Saved summary to: {summary_file.name}")

# Step 7: Display employment sheets summary
print("\n" + "=" * 80)
print("EMPLOYMENT-RELATED SHEETS")
print("=" * 80)
employment_sheet_df = sheet_df[sheet_df['is_employment_related'] == True]
for _, row in employment_sheet_df.iterrows():
    if 'error' not in row:
        print(f"\n{row['sheet_name']}")
        print(f"  Records: {row['records']:,}")
        print(f"  Columns: {row['columns']}")
        print(f"  Size: {row['file_size_kb']:.1f} KB")

# Step 8: Display top 20 sheets by record count
print("\n" + "=" * 80)
print("TOP 20 SHEETS BY RECORD COUNT")
print("=" * 80)
valid_sheets = sheet_df[~sheet_df['records'].isna()].sort_values('records', ascending=False)
for _, row in valid_sheets.head(20).iterrows():
    emp_marker = " [EMPLOYMENT]" if row['is_employment_related'] else ""
    print(f"{row['sheet_name'][:60]:<60} {row['records']:>8,} records{emp_marker}")

# Step 9: Final summary
print("\n" + "=" * 80)
print("EXTRACTION COMPLETE")
print("=" * 80)
print(f"Total sheets in file: {len(xl.sheet_names)}")
print(f"Sheets extracted: {len([s for s in sheet_info if 'error' not in s])}")
print(f"Sheets skipped (metadata): {len([s for s in sheet_info if s.get('sheet_name') in skip_sheets])}")
print(f"Employment-related sheets: {len(employment_sheets)}")
print(f"Total records: {total_records:,}")
print(f"Coverage: 1086-2016 (930 years of UK economic history)")
print()
print(f"Output directory: {LOCAL_INPUT / 'sheets'}")
print(f"Files created: {len([s for s in sheet_info if 'error' not in s])} CSV files")
print(f"Inventory: {inventory_file.name}")
print(f"Summary: {summary_file.name}")
print("=" * 80)
