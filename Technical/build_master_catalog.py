"""
StarCruiser Master Catalog Builder
===================================

Builds comprehensive catalog system for ALL employment data sources:
1. MASTER_CATALOG.csv - All datasets with metadata
2. CROSS_REFERENCE_TABLE.csv - Duplicate detection and relationships
3. SERIES_INDEX.csv - Individual series inventory
4. LOCAL_CHECKOUT_LEDGER.csv - the source store integration tracking

Catalogs maintained in BOTH locations:
- <OUTPUT_ROOT>/CATALOGS/
- <DATA_ROOT>/DATA/ (checkout ledger)

Cross-references with the source store's existing master catalog.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import hashlib

import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "data"))


# Paths
LOCAL_BASE = PROJECT_ROOT
LOCAL_INPUTS = LOCAL_BASE / "Inputs"
LOCAL_CATALOGS = LOCAL_BASE / "Outputs" / "CATALOGS"
SOURCE_BASE = DATA_ROOT
SOURCE_DATA = SOURCE_BASE / "DATA"
SOURCE_CATALOG = SOURCE_BASE / "MASTER_CATALOG"

# Create catalog directory
LOCAL_CATALOGS.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("STARCRUISER MASTER CATALOG BUILDER")
print("=" * 80)
print(f"Catalog output: {LOCAL_CATALOGS}")
print(f"the source store integration: {SOURCE_DATA}")
print()

# Initialize catalog lists
master_catalog = []
cross_reference = []
series_index = []
robin_checkout = []

def compute_file_hash(file_path):
    """Compute MD5 hash for file integrity"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def analyze_csv(file_path, source_name, source_type):
    """Analyze a CSV file and extract metadata"""
    try:
        # Read first few rows to get structure
        df_head = pd.read_csv(file_path, nrows=100)

        # Get full row count efficiently
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            row_count = sum(1 for _ in f) - 1  # Subtract header

        # Get date range if date column exists
        date_cols = [col for col in df_head.columns if any(term in col.lower()
                     for term in ['date', 'year', 'time', 'period'])]

        date_min = None
        date_max = None
        if date_cols:
            try:
                df_dates = pd.read_csv(file_path, usecols=[date_cols[0]], parse_dates=[date_cols[0]])
                date_min = df_dates[date_cols[0]].min()
                date_max = df_dates[date_cols[0]].max()
            except:
                pass

        return {
            'file_name': file_path.name,
            'file_path': str(file_path),
            'source_name': source_name,
            'source_type': source_type,
            'records': row_count,
            'columns': len(df_head.columns),
            'column_names': ', '.join(df_head.columns.tolist()),
            'date_min': str(date_min) if date_min else None,
            'date_max': str(date_max) if date_max else None,
            'file_size_mb': file_path.stat().st_size / 1024 / 1024,
            'file_hash': compute_file_hash(file_path),
            'import_date': datetime.now().isoformat(),
            'status': 'active'
        }
    except Exception as e:
        return {
            'file_name': file_path.name,
            'file_path': str(file_path),
            'source_name': source_name,
            'source_type': source_type,
            'error': str(e),
            'status': 'error'
        }

# ============================================================================
# ROBIN IMPORTS - Track what came from the source store repository
# ============================================================================
print("Step 1: Cataloging the source store imports...")

robin_imports = {
    'WORLD_BANK': {
        'source_type': 'International Organization',
        'source_path': SOURCE_DATA / 'WORLD_BANK',
        'starcruiser_path': LOCAL_INPUTS / 'the source store' / 'WORLD_BANK'
    },
    'JST': {
        'source_type': 'Academic Research',
        'source_path': SOURCE_DATA / 'JST_MACROHISTORY',
        'starcruiser_path': LOCAL_INPUTS / 'the source store' / 'JST'
    },
    'BOE': {
        'source_type': 'Central Bank',
        'source_path': SOURCE_DATA / 'BoE',
        'starcruiser_path': LOCAL_INPUTS / 'the source store' / 'BOE'
    },
    'MADDISON': {
        'source_type': 'Academic Research',
        'source_path': SOURCE_DATA / 'Maddison',
        'starcruiser_path': LOCAL_INPUTS / 'the source store' / 'MADDISON'
    },
    'FRED': {
        'source_type': 'Federal Reserve',
        'source_path': SOURCE_DATA / 'FRED',
        'starcruiser_path': LOCAL_INPUTS / 'the source store' / 'FRED'
    },
    'CENSUS': {
        'source_type': 'Government Statistical Agency',
        'source_path': DATA_ROOT / "API_MODULES/CENSUS/data",
        'starcruiser_path': LOCAL_INPUTS / 'the source store' / 'CENSUS'
    },
    'BEA': {
        'source_type': 'Government Statistical Agency',
        'source_path': DATA_ROOT / "API_MODULES/BEA/data",
        'starcruiser_path': LOCAL_INPUTS / 'the source store' / 'BEA'
    },
    'BLS_API': {
        'source_type': 'Government Statistical Agency',
        'source_path': DATA_ROOT / "API_MODULES/BLS/data",
        'starcruiser_path': LOCAL_INPUTS / 'the source store' / 'BLS_API'
    },
    'OECD_SOCIAL': {
        'source_type': 'International Organization',
        'source_path': DATA_ROOT / "API_MODULES/SOCIAL_SCIENCE/DATA/SOCIAL_SCIENCE_MASTER/OECD_SOCIAL",
        'starcruiser_path': LOCAL_INPUTS / 'the source store' / 'OECD_SOCIAL'
    }
}

robin_import_count = 0
for source_name, paths in robin_imports.items():
    if paths['starcruiser_path'].exists():
        print(f"\n  Cataloging {source_name}...")
        csv_files = list(paths['starcruiser_path'].glob("*.csv"))

        for csv_file in csv_files:
            metadata = analyze_csv(csv_file, source_name, paths['source_type'])
            master_catalog.append(metadata)

            # Track the source store checkout
            robin_checkout.append({
                'source_name': source_name,
                'file_name': csv_file.name,
                'source_path': str(paths['source_path']),
                'starcruiser_path': str(csv_file),
                'checkout_date': datetime.now().isoformat(),
                'file_hash': metadata.get('file_hash', ''),
                'purpose': 'Employment database integration'
            })

            robin_import_count += 1
            print(f"    - {csv_file.name}: {metadata.get('records', 'N/A'):,} records")

print(f"\n  Total the source store imports cataloged: {robin_import_count} files")

# ============================================================================
# EXTERNAL DOWNLOADS - Indeed, ADP, NBER
# ============================================================================
print("\nStep 2: Cataloging external downloads...")

external_sources = {
    'INDEED': {'path': LOCAL_INPUTS / 'External' / 'INDEED', 'type': 'Private Employment Data'},
    'ADP': {'path': LOCAL_INPUTS / 'External' / 'ADP', 'type': 'Private Employment Data'},
    'NBER': {'path': LOCAL_INPUTS / 'External' / 'NBER', 'type': 'Historical Macroeconomic Data'}
}

external_count = 0
for source_name, info in external_sources.items():
    if info['path'].exists():
        print(f"\n  Cataloging {source_name}...")
        csv_files = list(info['path'].glob("*.csv"))

        for csv_file in csv_files:
            metadata = analyze_csv(csv_file, source_name, info['type'])
            master_catalog.append(metadata)
            external_count += 1
            print(f"    - {csv_file.name}: {metadata.get('records', 'N/A'):,} records")

print(f"\n  Total external downloads cataloged: {external_count} files")

# ============================================================================
# SAVE MASTER CATALOG
# ============================================================================
print("\nStep 3: Saving master catalog...")

master_df = pd.DataFrame(master_catalog)
master_file = LOCAL_CATALOGS / "MASTER_CATALOG.csv"
master_df.to_csv(master_file, index=False, encoding='utf-8')

print(f"  Saved: {master_file.name}")
print(f"  Total datasets: {len(master_df)}")
print(f"  Total records: {master_df['records'].sum():,.0f}")
print(f"  Total size: {master_df['file_size_mb'].sum():.1f} MB")

# ============================================================================
# SAVE ROBIN CHECKOUT LEDGER
# ============================================================================
print("\nStep 4: Saving source checkout ledger...")

checkout_df = pd.DataFrame(robin_checkout)
checkout_file = LOCAL_CATALOGS / "SOURCE_CHECKOUT_LEDGER.csv"
checkout_df.to_csv(checkout_file, index=False, encoding='utf-8')

# Also save to the source store directory for bidirectional tracking
robin_checkout_file = SOURCE_DATA / "LOCAL_CHECKOUT_LEDGER.csv"
robin_checkout_file.parent.mkdir(parents=True, exist_ok=True)
checkout_df.to_csv(robin_checkout_file, index=False, encoding='utf-8')

print(f"  Saved to StarCruiser: {checkout_file.name}")
print(f"  Saved to the source store: {robin_checkout_file}")
print(f"  Files checked out from the source store: {len(checkout_df)}")

# ============================================================================
# CREATE CROSS-REFERENCE TABLE TEMPLATE
# ============================================================================
print("\nStep 5: Creating cross-reference table template...")

# For now, create template structure - will populate during BLS/QCEW downloads
cross_ref_template = pd.DataFrame(columns=[
    'series_id_1',
    'source_1',
    'series_id_2',
    'source_2',
    'relationship_type',  # exact_duplicate, partial_overlap, subset, superset, vintage, complementary
    'overlap_start_date',
    'overlap_end_date',
    'recommended_primary',
    'notes'
])

cross_ref_file = LOCAL_CATALOGS / "CROSS_REFERENCE_TABLE.csv"
cross_ref_template.to_csv(cross_ref_file, index=False, encoding='utf-8')
print(f"  Created template: {cross_ref_file.name}")

# ============================================================================
# CREATE SERIES INDEX TEMPLATE
# ============================================================================
print("\nStep 6: Creating series index template...")

series_index_template = pd.DataFrame(columns=[
    'series_id',
    'source_name',
    'series_title',
    'frequency',
    'units',
    'seasonal_adjustment',
    'start_date',
    'end_date',
    'last_updated',
    'record_count',
    'file_location'
])

series_file = LOCAL_CATALOGS / "SERIES_INDEX.csv"
series_index_template.to_csv(series_file, index=False, encoding='utf-8')
print(f"  Created template: {series_file.name}")

# ============================================================================
# GENERATE SUMMARY STATISTICS
# ============================================================================
print("\nStep 7: Generating summary statistics...")

summary_stats = {
    'catalog_build_date': datetime.now().isoformat(),
    'total_datasets': len(master_df),
    'total_records': int(master_df['records'].sum()),
    'total_size_mb': float(master_df['file_size_mb'].sum()),
    'sources': {
        'robin_imports': robin_import_count,
        'external_downloads': external_count,
        'pending_bulk_downloads': 6  # BLS_FTP, QCEW, ILO, OECD, IMF, NBER
    },
    'source_breakdown': master_df.groupby('source_type')['records'].sum().to_dict(),
    'date_coverage': {
        'earliest': master_df['date_min'].dropna().min() if not master_df['date_min'].dropna().empty else 'N/A',
        'latest': master_df['date_max'].dropna().max() if not master_df['date_max'].dropna().empty else 'N/A'
    },
    'robin_integration': {
        'files_from_robin': len(checkout_df),
        'checkout_ledger_location': str(robin_checkout_file)
    }
}

summary_file = LOCAL_CATALOGS / "catalog_summary.json"
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary_stats, f, indent=2)

print(f"  Saved: {summary_file.name}")

# ============================================================================
# DISPLAY CATALOG SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("MASTER CATALOG SUMMARY")
print("=" * 80)

print(f"\nTotal Datasets: {len(master_df)}")
print(f"Total Records: {master_df['records'].sum():,.0f}")
print(f"Total Size: {master_df['file_size_mb'].sum():.1f} MB")

print("\nBy Source:")
for source in master_df['source_name'].unique():
    source_data = master_df[master_df['source_name'] == source]
    print(f"  {source}: {len(source_data)} files, {source_data['records'].sum():,.0f} records")

print(f"\nDate Coverage:")
date_min_val = master_df['date_min'].dropna().min() if not master_df['date_min'].dropna().empty else 'N/A'
date_max_val = master_df['date_max'].dropna().max() if not master_df['date_max'].dropna().empty else 'N/A'
print(f"  Earliest: {date_min_val}")
print(f"  Latest: {date_max_val}")

print(f"\nCatalog Files Created:")
print(f"  1. {master_file.name} - Master catalog of all datasets")
print(f"  2. {checkout_file.name} - the source store integration tracking")
print(f"  3. {cross_ref_file.name} - Cross-reference template (to populate)")
print(f"  4. {series_file.name} - Series index template (to populate)")
print(f"  5. {summary_file.name} - Summary statistics")

print(f"\nRobin Integration:")
print(f"  Files checked out from the source store: {len(checkout_df)}")
print(f"  Ledger saved to: {robin_checkout_file}")

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)
print("1. Download BLS FTP bulk data (CE, SM, LA series)")
print("2. Populate SERIES_INDEX.csv with individual series metadata")
print("3. Populate CROSS_REFERENCE_TABLE.csv to detect duplicates")
print("4. Download QCEW, NBER, OECD, IMF, ILO data")
print("5. Update catalogs as each new source is added")
print("=" * 80)
