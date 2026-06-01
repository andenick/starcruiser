"""
Update Master Catalog with Quality Tier Classifications
========================================================

Adds quality tier system (Tier 1-4) based on Trump Data Policy Impact Report:
- Tier 1: Administrative data (QCEW, Economic Census, BEA Regional)
- Tier 2: High-quality surveys (CES/CPS national, pre-2025 BLS data)
- Tier 3: Moderate quality (substate surveys, 2025 survey data)
- Tier 4: Lower quality (shutdown periods, discontinued series)

Also adds:
- Data collection method (Administrative, Survey, Academic, Private)
- Time period flags (Pre-2025, 2025+, Shutdown-affected)
- Known quality issues
- Response rate estimates where applicable
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import json

import os

OUTPUT_ROOT = Path(os.environ.get("OUTPUT_ROOT", "outputs"))


CATALOGS_DIR = OUTPUT_ROOT / "CATALOGS"
MASTER_CATALOG = CATALOGS_DIR / "MASTER_CATALOG.csv"

print("=" * 80)
print("UPDATE MASTER CATALOG WITH QUALITY TIER CLASSIFICATIONS")
print("=" * 80)
print()

# Read existing master catalog
print("Reading existing master catalog...")
df = pd.read_csv(MASTER_CATALOG)
print(f"  Loaded {len(df)} datasets")
print()

# Define quality tier assignment logic
def assign_quality_tier(row):
    """Assign quality tier based on source characteristics"""

    source = row['source_name']
    source_type = row['source_type']
    file_name = row['file_name']

    # Parse date_max to check if data extends into 2025
    try:
        if pd.notna(row['date_max']):
            date_max_str = str(row['date_max'])
            if '2025' in date_max_str or '2026' in date_max_str:
                has_2025_data = True
            else:
                has_2025_data = False
        else:
            has_2025_data = False
    except:
        has_2025_data = False

    # TIER 1: Administrative data (highest quality)
    # QCEW, Economic Census, BEA Regional Accounts
    tier1_sources = []  # Currently no QCEW in database

    if source in tier1_sources:
        return 1

    # BEA uses QCEW benchmarking, so also Tier 1
    if source == 'BEA':
        return 1

    # TIER 2: High-quality surveys and pre-2025 official statistics
    tier2_sources = ['FRED', 'BLS_API', 'CENSUS', 'WORLD_BANK']

    if source in tier2_sources and not has_2025_data:
        return 2

    # NBER historical data (1860-1970) is Tier 2 - official but historical
    if source == 'NBER':
        return 2

    # TIER 3: Moderate quality (2025 survey data, academic sources, substate)
    tier3_sources = ['JST', 'MADDISON', 'OECD_SOCIAL']

    if source in tier3_sources:
        return 3

    # Survey-based 2025 data moves to Tier 3
    if source in tier2_sources and has_2025_data:
        return 3

    # TIER 4: Lower quality (private data, shutdown-affected, issues)
    tier4_sources = ['INDEED', 'ADP']

    if source in tier4_sources:
        return 4

    # Default to Tier 3 (moderate quality)
    return 3

def assign_collection_method(row):
    """Assign data collection method"""

    source = row['source_name']

    # Administrative data
    if source in ['BEA', 'CENSUS']:
        return 'Administrative'

    # Survey data
    if source in ['BLS_API', 'FRED', 'WORLD_BANK']:
        return 'Survey'

    # Academic research
    if source in ['JST', 'MADDISON', 'NBER', 'OECD_SOCIAL']:
        return 'Academic'

    # Private sector
    if source in ['INDEED', 'ADP']:
        return 'Private'

    return 'Unknown'

def assign_time_period_flag(row):
    """Assign time period quality flag"""

    try:
        if pd.notna(row['date_max']):
            date_max_str = str(row['date_max'])

            # Check for 2025 data
            if '2025' in date_max_str:
                # Check for shutdown-affected periods (Sept-Oct 2025)
                # For now, flag all 2025 data
                return '2025_DATA'

            # Pre-2025 data
            return 'PRE_2025'
        else:
            return 'UNKNOWN'
    except:
        return 'UNKNOWN'

def identify_quality_issues(row):
    """Identify known quality issues"""

    issues = []
    source = row['source_name']
    file_name = row['file_name']

    # Maddison matrix sparsity (by design, not a flaw)
    if source == 'MADDISON' and ('gdp_per_capita' in file_name or 'population' in file_name):
        issues.append('High missing values (matrix structure by design)')

    # Indeed data coverage concerns
    if source == 'INDEED':
        issues.append('Coverage limited to Indeed.com postings only')

    # ADP coverage bias
    if source == 'ADP':
        issues.append('Coverage limited to ADP payroll clients')

    # 2025 survey data
    if '2025' in str(row.get('date_max', '')):
        if source in ['BLS_API', 'FRED']:
            issues.append('2025 data affected by BLS staffing losses and shutdown')

    # World Bank metadata file
    if 'metadata' in file_name.lower():
        issues.append('Metadata file, not primary data')

    if not issues:
        return 'None identified'

    return '; '.join(issues)

def estimate_response_rate(row):
    """Estimate response rate for survey-based data"""

    source = row['source_name']
    collection_method = row.get('collection_method', '')

    # Only applicable to survey data
    if collection_method != 'Survey':
        return 'N/A (not survey-based)'

    # BLS surveys (2025 data)
    if source in ['BLS_API', 'FRED'] and '2025' in str(row.get('date_max', '')):
        return '~43% (CES) / ~62% (CPS) - declining'

    # BLS surveys (pre-2025)
    if source in ['BLS_API', 'FRED']:
        return '~64% (CES) / ~69% (CPS) - historical'

    # Census surveys
    if source == 'CENSUS':
        return 'Varies by survey (ACS ~62%, CBP administrative)'

    # World Bank (aggregates from national sources)
    if source == 'WORLD_BANK':
        return 'Varies by country and indicator'

    return 'Unknown'

# Apply classifications
print("Applying quality tier classifications...")
df['quality_tier'] = df.apply(assign_quality_tier, axis=1)
df['collection_method'] = df.apply(assign_collection_method, axis=1)
df['time_period_flag'] = df.apply(assign_time_period_flag, axis=1)
df['known_quality_issues'] = df.apply(identify_quality_issues, axis=1)
df['estimated_response_rate'] = df.apply(estimate_response_rate, axis=1)

# Add tier descriptions
tier_descriptions = {
    1: 'Highest Quality - Administrative data, 95%+ coverage',
    2: 'High Quality - Official surveys, pre-2025 data',
    3: 'Moderate Quality - Academic sources, 2025 survey data',
    4: 'Lower Quality - Private data, known limitations'
}

df['tier_description'] = df['quality_tier'].map(tier_descriptions)

# Add last updated timestamp
df['quality_assessment_date'] = datetime.now().isoformat()

# Reorder columns for readability
column_order = [
    'file_name',
    'source_name',
    'quality_tier',
    'tier_description',
    'collection_method',
    'time_period_flag',
    'records',
    'columns',
    'date_min',
    'date_max',
    'file_size_mb',
    'known_quality_issues',
    'estimated_response_rate',
    'source_type',
    'file_path',
    'column_names',
    'file_hash',
    'import_date',
    'quality_assessment_date',
    'status'
]

df = df[column_order]

# Save updated catalog
print("Saving updated master catalog...")
df.to_csv(MASTER_CATALOG, index=False, encoding='utf-8')
print(f"  Saved: {MASTER_CATALOG.name}")
print()

# Generate summary statistics
print("=" * 80)
print("QUALITY TIER SUMMARY")
print("=" * 80)
print()

tier_summary = df.groupby('quality_tier').agg({
    'file_name': 'count',
    'records': 'sum',
    'file_size_mb': 'sum'
}).round(1)

tier_summary.columns = ['Datasets', 'Total Records', 'Total Size (MB)']

print(tier_summary)
print()

print("By Quality Tier:")
for tier in sorted(df['quality_tier'].unique()):
    tier_data = df[df['quality_tier'] == tier]
    sources = tier_data['source_name'].unique()
    print(f"\nTier {tier}: {tier_descriptions[tier]}")
    print(f"  Datasets: {len(tier_data)}")
    print(f"  Records: {tier_data['records'].sum():,.0f}")
    print(f"  Sources: {', '.join(sorted(sources))}")

print("\nBy Collection Method:")
method_summary = df.groupby('collection_method').agg({
    'file_name': 'count',
    'records': 'sum'
})
print(method_summary)

print("\nBy Time Period Flag:")
period_summary = df.groupby('time_period_flag').agg({
    'file_name': 'count',
    'records': 'sum'
})
print(period_summary)

print("\nDatasets with Known Quality Issues:")
issues_data = df[df['known_quality_issues'] != 'None identified']
print(f"  Total: {len(issues_data)} datasets")
for _, row in issues_data.iterrows():
    print(f"  - {row['file_name']} ({row['source_name']}): {row['known_quality_issues']}")

# Save tier classification metadata
tier_metadata = {
    'classification_date': datetime.now().isoformat(),
    'total_datasets': len(df),
    'tier_definitions': {
        'Tier 1': {
            'description': tier_descriptions[1],
            'criteria': 'Administrative data with 95%+ coverage (QCEW, Economic Census, BEA Regional)',
            'datasets': len(df[df['quality_tier'] == 1]),
            'sources': df[df['quality_tier'] == 1]['source_name'].unique().tolist()
        },
        'Tier 2': {
            'description': tier_descriptions[2],
            'criteria': 'Official surveys with established methodology, pre-2025 data',
            'datasets': len(df[df['quality_tier'] == 2]),
            'sources': df[df['quality_tier'] == 2]['source_name'].unique().tolist()
        },
        'Tier 3': {
            'description': tier_descriptions[3],
            'criteria': 'Academic sources, 2025 survey data with declining response rates',
            'datasets': len(df[df['quality_tier'] == 3]),
            'sources': df[df['quality_tier'] == 3]['source_name'].unique().tolist()
        },
        'Tier 4': {
            'description': tier_descriptions[4],
            'criteria': 'Private sector data with coverage limitations',
            'datasets': len(df[df['quality_tier'] == 4]),
            'sources': df[df['quality_tier'] == 4]['source_name'].unique().tolist()
        }
    },
    'collection_methods': df['collection_method'].value_counts().to_dict(),
    'time_period_flags': df['time_period_flag'].value_counts().to_dict(),
    'datasets_with_quality_issues': len(issues_data),
    'trump_policy_impact': {
        'datasets_affected_2025': len(df[df['time_period_flag'] == '2025_DATA']),
        'affected_sources': df[df['time_period_flag'] == '2025_DATA']['source_name'].unique().tolist(),
        'reference_document': 'TRUMP_DATA_POLICY_IMPACT_REPORT.md'
    }
}

metadata_file = CATALOGS_DIR / "quality_tier_metadata.json"
with open(metadata_file, 'w', encoding='utf-8') as f:
    json.dump(tier_metadata, f, indent=2)

print(f"\n\nMetadata saved: {metadata_file.name}")

print("\n" + "=" * 80)
print("MASTER CATALOG UPDATE COMPLETE")
print("=" * 80)
print(f"\nUpdated catalog: {MASTER_CATALOG}")
print(f"Metadata file: {metadata_file}")
print(f"\nTotal datasets classified: {len(df)}")
print(f"Quality assessment date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\nFor tier definitions and methodology, see:")
print("  - TRUMP_DATA_POLICY_IMPACT_REPORT.md (Section 8.1)")
print("  - quality_tier_metadata.json")
print("=" * 80)
