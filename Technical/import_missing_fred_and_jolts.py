#!/usr/bin/env python3
"""
StarCruiser: Import Missing FRED Categories and JOLTS Data
============================================================

This script:
1. Copies missing FRED category files from the source store to StarCruiser
2. Downloads JOLTS data from FRED API for Beveridge curve analysis
3. Downloads comprehensive employment metrics (U-6, Emp-Pop ratio, wages)

Author: StarCruiser Project
Date: December 7, 2025
"""

import os
import shutil
import pandas as pd
from pathlib import Path
from datetime import datetime
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "data"))
OUTPUT_ROOT = Path(os.environ.get("OUTPUT_ROOT", "outputs"))


# Try to import fredapi for JOLTS download
try:
    from fredapi import Fred

    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False
    print("Warning: fredapi not installed. Run: pip install fredapi")

# Paths
SOURCE_FRED_PATH = DATA_ROOT / "API_MODULES/FRED/DATA"
LOCAL_FRED_PATH = (PROJECT_ROOT / "Inputs/source/FRED")
OUTPUT_PATH = OUTPUT_ROOT / "CATALOGS"

def get_fred_api_key():
    """Return the FRED API key from the FRED_API_KEY environment variable.

    Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html
    and set it via:  export FRED_API_KEY=your_key_here
    """
    key = os.environ.get("FRED_API_KEY")
    if not key:
        raise RuntimeError(
            "FRED_API_KEY is not set. Get a free key at "
            "https://fred.stlouisfed.org/docs/api/api_key.html and export it."
        )
    return key


# Categories to import from the source store (not yet in StarCruiser)
MISSING_CATEGORIES = [
    "fred_financial_stress_20250929.csv",
    "fred_fiscal_20250929.csv",
    "fred_gdp_growth_20250929.csv",
    "fred_housing_20250929.csv",
    "fred_income_spending_20250929.csv",
    "fred_interest_rates_20250929.csv",
    "fred_money_banking_20250929.csv",
    "fred_production_20250929.csv",
    "fred_regional_20250929.csv",
    "fred_trade_20250929.csv",
    "fred_business_20250929.csv",
    "fred_inflation_20250929.csv",
]

# JOLTS Series to download
JOLTS_SERIES = {
    # Job Openings
    "JTSJOL": "Job Openings: Total Nonfarm (Thousands)",
    "JTSJOR": "Job Openings Rate: Total Nonfarm (%)",
    # Hires
    "JTSHIL": "Hires: Total Nonfarm (Thousands)",
    "JTSHIR": "Hires Rate: Total Nonfarm (%)",
    # Total Separations
    "JTSTSL": "Total Separations: Total Nonfarm (Thousands)",
    "JTSTSR": "Total Separations Rate: Total Nonfarm (%)",
    # Quits
    "JTSQUL": "Quits: Total Nonfarm (Thousands)",
    "JTSQUR": "Quits Rate: Total Nonfarm (%)",
    # Layoffs and Discharges
    "JTSLDL": "Layoffs and Discharges: Total Nonfarm (Thousands)",
    "JTSLDR": "Layoffs and Discharges Rate: Total Nonfarm (%)",
}

# Comprehensive Employment Series
EMPLOYMENT_SERIES = {
    # Unemployment measures
    "UNRATE": "Unemployment Rate (U-3) (%)",
    "U6RATE": "Total Unemployed + Marginally Attached + Part-Time for Economic Reasons (U-6) (%)",
    "UNEMPLOY": "Unemployed (Thousands)",
    "UEMPLT5": "Number Unemployed for Less Than 5 Weeks (Thousands)",
    "UEMP5TO14": "Number Unemployed for 5-14 Weeks (Thousands)",
    "UEMP15T26": "Number Unemployed for 15-26 Weeks (Thousands)",
    "UEMP27OV": "Number Unemployed for 27 Weeks & Over (Thousands)",
    # Employment-Population
    "EMRATIO": "Employment-Population Ratio (%)",
    "CIVPART": "Labor Force Participation Rate (%)",
    "CLF16OV": "Civilian Labor Force (Thousands)",
    "CE16OV": "Civilian Employment (Thousands)",
    # Payrolls
    "PAYEMS": "All Employees: Total Nonfarm (Thousands)",
    "USPRIV": "All Employees: Total Private (Thousands)",
    "USGOVT": "All Employees: Government (Thousands)",
    # Wages and Hours
    "AHETPI": "Average Hourly Earnings: Total Private ($/hr)",
    "CES0500000003": "Average Hourly Earnings: Total Private ($/hr, alt)",
    "ECIWAG": "Employment Cost Index: Wages and Salaries (%)",
    "AWHAETP": "Average Weekly Hours: Total Private (Hours)",
    "AWHI": "Average Weekly Hours: Manufacturing (Hours)",
    # Weekly Claims
    "ICSA": "Initial Claims (Thousands)",
    "CCSA": "Continued Claims (Thousands)",
    "IC4WSA": "4-Week Moving Average of Initial Claims (Thousands)",
}


def copy_missing_categories():
    """Copy missing FRED category files from the source store to StarCruiser."""
    print("\n" + "=" * 60)
    print("STEP 1: Importing Missing FRED Categories from the source store")
    print("=" * 60)

    copied = []
    skipped = []
    missing = []

    for filename in MISSING_CATEGORIES:
        # Check for files with date prefix
        source_patterns = [
            SOURCE_FRED_PATH / f"[2025.09.29] {filename}",
            SOURCE_FRED_PATH / f"[2025.10.07] {filename}",
            SOURCE_FRED_PATH / filename,
        ]

        source_file = None
        for pattern in source_patterns:
            if pattern.exists():
                source_file = pattern
                break

        if source_file is None:
            missing.append(filename)
            continue

        # Target filename (preserve date prefix)
        target_file = LOCAL_FRED_PATH / source_file.name

        if target_file.exists():
            skipped.append(filename)
            print(f"  ⏭️  Already exists: {source_file.name}")
        else:
            shutil.copy2(source_file, target_file)
            copied.append(filename)
            print(f"  ✅ Copied: {source_file.name}")

    print(
        f"\nSummary: {len(copied)} copied, {len(skipped)} skipped, {len(missing)} not found"
    )
    return copied, skipped, missing


def download_jolts_data(fred: "Fred"):
    """Download JOLTS data from FRED API."""
    print("\n" + "=" * 60)
    print("STEP 2: Downloading JOLTS Data from FRED API")
    print("=" * 60)

    all_data = []

    for series_id, description in JOLTS_SERIES.items():
        try:
            print(f"  📥 Downloading {series_id}: {description[:50]}...")
            data = fred.get_series(series_id, observation_start="2000-12-01")

            df = pd.DataFrame(
                {
                    "date": data.index,
                    "value": data.values,
                    "series_id": series_id,
                    "description": description,
                    "category": "jolts",
                }
            )
            all_data.append(df)
            print(f"      Got {len(df)} observations")

        except Exception as e:
            print(f"  ❌ Failed to download {series_id}: {e}")

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        combined["realtime_start"] = datetime.now().strftime("%Y-%m-%d")
        combined["realtime_end"] = datetime.now().strftime("%Y-%m-%d")

        output_file = (
            LOCAL_FRED_PATH
            / f"fred_jolts_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        combined.to_csv(output_file, index=False)
        print(f"\n  ✅ Saved {len(combined)} JOLTS observations to {output_file.name}")
        return combined

    return None


def download_employment_data(fred: "Fred"):
    """Download comprehensive employment data from FRED API."""
    print("\n" + "=" * 60)
    print("STEP 3: Downloading Comprehensive Employment Data")
    print("=" * 60)

    all_data = []

    for series_id, description in EMPLOYMENT_SERIES.items():
        try:
            print(f"  📥 Downloading {series_id}: {description[:50]}...")
            data = fred.get_series(series_id, observation_start="1990-01-01")

            df = pd.DataFrame(
                {
                    "date": data.index,
                    "value": data.values,
                    "series_id": series_id,
                    "description": description,
                    "category": "comprehensive_employment",
                }
            )
            all_data.append(df)
            print(f"      Got {len(df)} observations")

        except Exception as e:
            print(f"  ❌ Failed to download {series_id}: {e}")

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        combined["realtime_start"] = datetime.now().strftime("%Y-%m-%d")
        combined["realtime_end"] = datetime.now().strftime("%Y-%m-%d")

        output_file = (
            LOCAL_FRED_PATH
            / f"fred_comprehensive_employment_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        combined.to_csv(output_file, index=False)
        print(
            f"\n  ✅ Saved {len(combined)} employment observations to {output_file.name}"
        )
        return combined

    return None


def generate_data_summary():
    """Generate summary of all FRED data now in StarCruiser."""
    print("\n" + "=" * 60)
    print("STEP 4: Generating Data Summary")
    print("=" * 60)

    all_files = list(LOCAL_FRED_PATH.glob("*.csv"))

    summary = []
    total_records = 0

    for f in all_files:
        try:
            df = pd.read_csv(f)
            records = len(df)
            total_records += records

            # Get unique series
            if "series_id" in df.columns:
                series_count = df["series_id"].nunique()
            else:
                series_count = 1

            # Get date range
            if "date" in df.columns:
                dates = pd.to_datetime(df["date"])
                date_range = f"{dates.min().strftime('%Y-%m')} to {dates.max().strftime('%Y-%m')}"
            else:
                date_range = "N/A"

            summary.append(
                {
                    "filename": f.name,
                    "records": records,
                    "series_count": series_count,
                    "date_range": date_range,
                    "size_kb": f.stat().st_size / 1024,
                }
            )

        except Exception as e:
            print(f"  ⚠️  Could not read {f.name}: {e}")

    summary_df = pd.DataFrame(summary)
    summary_df = summary_df.sort_values("records", ascending=False)

    # Save summary
    summary_file = OUTPUT_PATH / "FRED_DATA_INVENTORY.csv"
    summary_df.to_csv(summary_file, index=False)

    print(f"\n  📊 FRED Data Summary:")
    print(f"     Files: {len(summary_df)}")
    print(f"     Total Records: {total_records:,}")
    print(f"     Total Size: {summary_df['size_kb'].sum()/1024:.1f} MB")

    print(f"\n  Top files by record count:")
    for _, row in summary_df.head(10).iterrows():
        print(f"     {row['filename']}: {row['records']:,} records")

    return summary_df


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("  StarCruiser: FRED Data Import & JOLTS Download")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    # Ensure directories exist
    LOCAL_FRED_PATH.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    # Step 1: Copy missing categories
    copied, skipped, missing = copy_missing_categories()

    # Steps 2-3: Download from FRED API (if available)
    if FRED_AVAILABLE:
        api_key = get_fred_api_key()
        if api_key:
            fred = Fred(api_key=api_key)

            # Download JOLTS
            jolts_df = download_jolts_data(fred)

            # Download comprehensive employment
            emp_df = download_employment_data(fred)
        else:
            print(
                "\n⚠️  No FRED API key found. Skipping JOLTS and employment downloads."
            )
            print("   Set FRED_API_KEY environment variable or create:")
            print(f"   {FRED_API_KEY_PATH}")
    else:
        print("\n⚠️  fredapi not installed. Skipping JOLTS and employment downloads.")
        print("   Run: pip install fredapi")

    # Step 4: Generate summary
    summary_df = generate_data_summary()

    print("\n" + "=" * 60)
    print("  IMPORT COMPLETE")
    print("=" * 60)
    print(f"\n  Output location: {LOCAL_FRED_PATH}")
    print(f"  Summary saved to: {OUTPUT_PATH / 'FRED_DATA_INVENTORY.csv'}")

    return {
        "copied": copied,
        "skipped": skipped,
        "missing": missing,
        "summary": summary_df,
    }


if __name__ == "__main__":
    result = main()
