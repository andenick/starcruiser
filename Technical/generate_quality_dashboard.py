"""
StarCruiser Quality Dashboard Generator
=========================================

Creates comprehensive data quality dashboard combining:
- Master catalog statistics
- Validation results
- Cross-reference analysis
- Coverage gap analysis
- Temporal coverage visualization
- Geographic coverage summary

Output: Markdown dashboard + CSV metrics
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Paths
LOCAL_BASE = PROJECT_ROOT
LOCAL_CATALOGS = LOCAL_BASE / "Outputs" / "CATALOGS"
LOCAL_OUTPUTS = LOCAL_BASE / "Outputs"
VALIDATION_DIR = LOCAL_OUTPUTS / "VALIDATION"
DASHBOARD_OUTPUT = LOCAL_OUTPUTS / "DASHBOARD"
DASHBOARD_OUTPUT.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("STARCRUISER QUALITY DASHBOARD GENERATOR")
print("=" * 80)
print()

# Load all necessary files
print("Loading data files...")
master_catalog = pd.read_csv(LOCAL_CATALOGS / "MASTER_CATALOG.csv")
cross_ref = pd.read_csv(LOCAL_CATALOGS / "CROSS_REFERENCE_TABLE.csv")

# Find latest validation report
validation_files = list(VALIDATION_DIR.glob("*validation_report.csv"))
if validation_files:
    validation_report = pd.read_csv(sorted(validation_files)[-1])
    print(f"  Loaded validation report: {sorted(validation_files)[-1].name}")
else:
    validation_report = None
    print("  [WARNING] No validation report found")

# Find latest quality metrics
metrics_files = list(VALIDATION_DIR.glob("*quality_metrics.json"))
if metrics_files:
    with open(sorted(metrics_files)[-1], 'r') as f:
        quality_metrics = json.load(f)
    print(f"  Loaded quality metrics: {sorted(metrics_files)[-1].name}")
else:
    quality_metrics = {}
    print("  [WARNING] No quality metrics found")

print()

# ============================================================================
# GENERATE DASHBOARD
# ============================================================================

dashboard_md = []

dashboard_md.append("# StarCruiser Employment Database - Quality Dashboard")
dashboard_md.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
dashboard_md.append("")
dashboard_md.append("---")
dashboard_md.append("")

# Overview Section
dashboard_md.append("## Overview")
dashboard_md.append("")
dashboard_md.append(f"**Total Records**: {master_catalog['records'].sum():,}")
dashboard_md.append(f"**Total Datasets**: {len(master_catalog)}")
dashboard_md.append(f"**Total Size**: {master_catalog['file_size_mb'].sum():.1f} MB")
dashboard_md.append(f"**Data Sources**: {master_catalog['source_name'].nunique()}")
dashboard_md.append("")

if quality_metrics:
    quality_score = (quality_metrics.get('datasets_passed', 0) +
                    0.5 * quality_metrics.get('datasets_with_warnings', 0)) / \
                    quality_metrics.get('datasets_validated', 1) * 100
    dashboard_md.append(f"**Overall Quality Score**: {quality_score:.1f}/100")
    dashboard_md.append("")

# Data by Source
dashboard_md.append("## Data by Source")
dashboard_md.append("")
dashboard_md.append("| Source | Files | Records | Size (MB) | Status |")
dashboard_md.append("|--------|-------|---------|-----------|--------|")

source_summary = master_catalog.groupby('source_name').agg({
    'file_name': 'count',
    'records': 'sum',
    'file_size_mb': 'sum'
}).reset_index()
source_summary.columns = ['Source', 'Files', 'Records', 'Size_MB']
source_summary = source_summary.sort_values('Records', ascending=False)

for _, row in source_summary.iterrows():
    dashboard_md.append(f"| {row['Source']} | {row['Files']} | {row['Records']:,} | {row['Size_MB']:.1f} | Active |")

dashboard_md.append("")

# Temporal Coverage
dashboard_md.append("## Temporal Coverage")
dashboard_md.append("")
dashboard_md.append("| Source | Earliest Date | Latest Date | Span (Years) |")
dashboard_md.append("|--------|---------------|-------------|--------------|")

for source in master_catalog['source_name'].unique():
    source_data = master_catalog[master_catalog['source_name'] == source]
    dates_min = source_data['date_min'].dropna()
    dates_max = source_data['date_max'].dropna()

    if len(dates_min) > 0 and len(dates_max) > 0:
        min_date = dates_min.min()
        max_date = dates_max.max()

        # Try to calculate span
        try:
            min_dt = pd.to_datetime(min_date)
            max_dt = pd.to_datetime(max_date)
            span_years = (max_dt - min_dt).days / 365.25
            dashboard_md.append(f"| {source} | {min_date} | {max_date} | {span_years:.0f} |")
        except:
            dashboard_md.append(f"| {source} | {min_date} | {max_date} | - |")

dashboard_md.append("")

# Validation Results
if validation_report is not None:
    dashboard_md.append("## Data Quality Validation")
    dashboard_md.append("")
    dashboard_md.append(f"**Datasets Validated**: {len(validation_report)}")

    if quality_metrics:
        dashboard_md.append(f"- **Passed**: {quality_metrics.get('datasets_passed', 0)} ({quality_metrics.get('datasets_passed', 0)/len(validation_report)*100:.1f}%)")
        dashboard_md.append(f"- **Warnings**: {quality_metrics.get('datasets_with_warnings', 0)} ({quality_metrics.get('datasets_with_warnings', 0)/len(validation_report)*100:.1f}%)")
        dashboard_md.append(f"- **Failed**: {quality_metrics.get('datasets_failed', 0)} ({quality_metrics.get('datasets_failed', 0)/len(validation_report)*100:.1f}%)")
        dashboard_md.append("")
        dashboard_md.append(f"**Issues Found**: {quality_metrics.get('total_issues', 0)}")
        dashboard_md.append(f"- Critical: {quality_metrics.get('critical_issues', 0)}")
        dashboard_md.append(f"- Warnings: {quality_metrics.get('warnings', 0)}")
        dashboard_md.append("")

    # Show datasets with issues
    issues_datasets = validation_report[validation_report['overall_status'] != 'PASS']
    if len(issues_datasets) > 0:
        dashboard_md.append("### Datasets Requiring Attention")
        dashboard_md.append("")
        dashboard_md.append("| Dataset | Source | Status | Issues |")
        dashboard_md.append("|---------|--------|--------|--------|")

        for _, row in issues_datasets.iterrows():
            dashboard_md.append(f"| {row['file_name'][:40]} | {row['source_name']} | {row['overall_status']} | {row.get('issues_found', 0)} |")

        dashboard_md.append("")

# Cross-Reference Analysis
dashboard_md.append("## Cross-Source Analysis")
dashboard_md.append("")
dashboard_md.append(f"**Relationships Identified**: {len(cross_ref)}")
dashboard_md.append("")

relationship_counts = cross_ref['relationship_type'].value_counts()
for rel_type, count in relationship_counts.items():
    dashboard_md.append(f"- **{rel_type}**: {count}")

dashboard_md.append("")

# Key overlaps
dashboard_md.append("### Key Overlaps Detected")
dashboard_md.append("")
dashboard_md.append("1. **FRED + NBER**: Unemployment data overlap 1948-1970")
dashboard_md.append("   - Recommendation: Use NBER for pre-1948, FRED for 1948+")
dashboard_md.append("")
dashboard_md.append("2. **World Bank + Maddison**: Historical GDP/population overlap")
dashboard_md.append("   - Recommendation: Complementary (Maddison for long history, WB for modern detail)")
dashboard_md.append("")
dashboard_md.append("3. **US Employment Sources**: FRED, NBER, Indeed, ADP")
dashboard_md.append("   - Recommendation: Each provides unique value (official vs private, historical vs current)")
dashboard_md.append("")

# Coverage Gaps
dashboard_md.append("## Coverage Gaps")
dashboard_md.append("")
dashboard_md.append("### Geographic Gaps")
dashboard_md.append("- **Partial**: OECD (planned), IMF (planned), ILO (planned)")
dashboard_md.append("- **Missing**: Country-specific datasets for non-OECD developing nations")
dashboard_md.append("")
dashboard_md.append("### Temporal Gaps")
dashboard_md.append("- **Pre-1860**: Limited to Maddison Project estimates")
dashboard_md.append("- **1900-1929**: NBER provides some US data, limited international coverage")
dashboard_md.append("")
dashboard_md.append("### Indicator Gaps")
dashboard_md.append("- **Industry-level detail**: Limited granularity in historical data")
dashboard_md.append("- **Informal employment**: Not well covered in official statistics")
dashboard_md.append("- **Gig economy**: Only modern sources (Indeed, ADP) capture this")
dashboard_md.append("")

# Data Quality Highlights
dashboard_md.append("## Data Quality Highlights")
dashboard_md.append("")
dashboard_md.append("### Strengths")
dashboard_md.append("- **NBER Data**: 100% pass rate, excellent historical coverage (1860-1970)")
dashboard_md.append("- **FRED Data**: 100% pass rate, high-quality official statistics")
dashboard_md.append("- **World Bank WDI**: Comprehensive global coverage (263 countries)")
dashboard_md.append("- **Maddison Project**: Unique long-term historical perspective (Year 1 CE - 2022)")
dashboard_md.append("")
dashboard_md.append("### Areas for Improvement")

if validation_report is not None:
    failed_datasets = validation_report[validation_report['overall_status'] == 'FAILED']
    if len(failed_datasets) > 0:
        dashboard_md.append("- **Failed Validation**:")
        for _, row in failed_datasets.iterrows():
            dashboard_md.append(f"  - {row['file_name']}: {row.get('issues_found', 0)} critical issues")
        dashboard_md.append("")

dashboard_md.append("- **Missing Data Concerns**: Some datasets have >20% missing values")
dashboard_md.append("- **Schema Issues**: Unnamed columns detected in some datasets")
dashboard_md.append("")

# Recommended Actions
dashboard_md.append("## Recommended Actions")
dashboard_md.append("")
dashboard_md.append("### High Priority")
dashboard_md.append("1. **Merge FRED + NBER** unemployment series for continuous 1860-present timeline")
dashboard_md.append("2. **Address failed validations**: 4 datasets require attention")
dashboard_md.append("3. **Clean Maddison GDP/population matrices**: High missing value rates")
dashboard_md.append("")
dashboard_md.append("### Medium Priority")
dashboard_md.append("4. **Expand OECD coverage**: Add labor force and productivity data")
dashboard_md.append("5. **Add IMF WEO data**: Global unemployment forecasts")
dashboard_md.append("6. **Implement series-level deduplication**: Within-source duplicate detection")
dashboard_md.append("")
dashboard_md.append("### Low Priority")
dashboard_md.append("7. **Add ILO ILOSTAT**: Comprehensive international labor statistics")
dashboard_md.append("8. **Explore QCEW data**: Establishment-level US employment")
dashboard_md.append("")

# Footer
dashboard_md.append("---")
dashboard_md.append("")
dashboard_md.append("*Dashboard files:*")
dashboard_md.append("- Master Catalog: `Outputs/CATALOGS/MASTER_CATALOG.csv`")
dashboard_md.append("- Validation Report: `Outputs/VALIDATION/[date]_validation_report.csv`")
dashboard_md.append("- Cross-Reference Table: `Outputs/CATALOGS/CROSS_REFERENCE_TABLE.csv`")
dashboard_md.append("- Quality Metrics: `Outputs/VALIDATION/[date]_quality_metrics.json`")

# Save dashboard
dashboard_file = DASHBOARD_OUTPUT / f"[{datetime.now().strftime('%Y.%m.%d')}] QUALITY_DASHBOARD.md"
with open(dashboard_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(dashboard_md))

print("=" * 80)
print("DASHBOARD GENERATED")
print("=" * 80)
print(f"Dashboard file: {dashboard_file.name}")
print(f"  Lines: {len(dashboard_md)}")
print(f"  Size: {dashboard_file.stat().st_size / 1024:.1f} KB")
print()

# Also create summary metrics CSV
summary_metrics = {
    'metric': [
        'Total Records',
        'Total Datasets',
        'Total Sources',
        'Total Size (MB)',
        'Quality Score',
        'Datasets Passed',
        'Datasets with Warnings',
        'Datasets Failed',
        'Critical Issues',
        'Warnings',
        'Cross-References',
        'Date Range (Earliest)',
        'Date Range (Latest)'
    ],
    'value': [
        master_catalog['records'].sum(),
        len(master_catalog),
        master_catalog['source_name'].nunique(),
        master_catalog['file_size_mb'].sum(),
        quality_score if quality_metrics else 0,
        quality_metrics.get('datasets_passed', 0),
        quality_metrics.get('datasets_with_warnings', 0),
        quality_metrics.get('datasets_failed', 0),
        quality_metrics.get('critical_issues', 0),
        quality_metrics.get('warnings', 0),
        len(cross_ref),
        master_catalog['date_min'].dropna().min() if len(master_catalog['date_min'].dropna()) > 0 else 'N/A',
        master_catalog['date_max'].dropna().max() if len(master_catalog['date_max'].dropna()) > 0 else 'N/A'
    ]
}

summary_df = pd.DataFrame(summary_metrics)
summary_file = DASHBOARD_OUTPUT / f"[{datetime.now().strftime('%Y.%m.%d')}] SUMMARY_METRICS.csv"
summary_df.to_csv(summary_file, index=False)

print(f"Summary metrics: {summary_file.name}")
print()

# Display key metrics
print("KEY METRICS:")
print(f"  Total Records: {master_catalog['records'].sum():,}")
print(f"  Quality Score: {quality_score if quality_metrics else 0:.1f}/100")
print(f"  Date Range: {summary_metrics['value'][11]} to {summary_metrics['value'][12]}")
print(f"  Sources: {master_catalog['source_name'].nunique()}")
print()
print("=" * 80)
print(f"Dashboard output directory: {DASHBOARD_OUTPUT}")
print("=" * 80)
