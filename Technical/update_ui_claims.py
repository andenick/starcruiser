"""
Weekly Unemployment Insurance Claims Updater
============================================

Downloads latest weekly unemployment insurance claims data from FRED.
Serves as real-time leading indicator (claims lead unemployment by 1-2 months).

Data Series:
- ICSA: Initial Claims (seasonally adjusted)
- CCSA: Continued Claims (seasonally adjusted)
- State-level claims (if available)

Author: StarCruiser Project
Created: December 5, 2025
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import requests
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "data"))


# Add the source store API modules to path
SOURCE_API_PATH = DATA_ROOT / "API_MODULES"
sys.path.insert(0, str(SOURCE_API_PATH))

# Project paths
BASE_DIR = PROJECT_ROOT
INPUTS_DIR = BASE_DIR / "Inputs" / "External" / "UI_Claims"
OUTPUTS_DIR = BASE_DIR / "Outputs" / "REALTIME"
CATALOG_PATH = BASE_DIR / "Outputs" / "CATALOGS" / "MASTER_CATALOG.csv"

# Create directories
INPUTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# FRED API configuration
FRED_API_KEY = os.environ.get("FRED_API_KEY", None)
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def get_fred_series(series_id, start_date=None, api_key=None):
    """
    Download FRED series via API.
    
    Args:
        series_id (str): FRED series ID (e.g., 'ICSA')
        start_date (str): Start date in YYYY-MM-DD format (default: 1 year ago)
        api_key (str): FRED API key (optional, uses env var if not provided)
    
    Returns:
        pd.DataFrame: Series data with columns [date, value, series_id]
    """
    if api_key is None:
        api_key = FRED_API_KEY
    
    if api_key is None:
        print(f"[WARNING] No FRED API key found. Set FRED_API_KEY environment variable.")
        print(f"[WARNING] Register at: https://fred.stlouisfed.org/docs/api/api_key.html")
        return None
    
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date
    }
    
    print(f"[DOWNLOAD] {series_id} from {start_date}...")
    
    try:
        response = requests.get(FRED_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if "observations" not in data:
            print(f"[ERROR] No observations found for {series_id}")
            return None
        
        observations = data["observations"]
        df = pd.DataFrame(observations)
        
        if df.empty:
            print(f"[WARNING] {series_id} returned no data")
            return None
        
        df = df[["date", "value"]].copy()
        df["series_id"] = series_id
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["date"] = pd.to_datetime(df["date"])
        
        # Filter out missing values
        df = df[df["value"].notna()].copy()
        
        print(f"[SUCCESS] {series_id}: {len(df)} observations")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to download {series_id}: {e}")
        return None


def download_ui_claims_data(lookback_years=5):
    """
    Download all unemployment insurance claims series.
    
    Args:
        lookback_years (int): How many years of historical data to fetch
    
    Returns:
        dict: Dictionary of dataframes by series_id
    """
    start_date = (datetime.now() - timedelta(days=365 * lookback_years)).strftime("%Y-%m-%d")
    
    series_to_download = {
        "ICSA": "Initial Claims (SA)",
        "CCSA": "Continued Claims (SA)",
        "ICNSA": "Initial Claims (NSA)",
        "CCNSA": "Continued Claims (NSA)",
        "IURNSA": "Insured Unemployment Rate (NSA)",
        "IURSA": "Insured Unemployment Rate (SA)"
    }
    
    all_data = {}
    
    print(f"\n{'='*60}")
    print(f"Downloading Unemployment Insurance Claims Data")
    print(f"Lookback Period: {lookback_years} years (from {start_date})")
    print(f"{'='*60}\n")
    
    for series_id, description in series_to_download.items():
        df = get_fred_series(series_id, start_date=start_date)
        if df is not None:
            all_data[series_id] = df
            print(f"  {series_id} ({description}): {len(df)} obs, Latest: {df['date'].max().strftime('%Y-%m-%d')}")
    
    return all_data


def save_ui_claims_data(data_dict, output_dir):
    """
    Save UI claims data to CSV files.
    
    Args:
        data_dict (dict): Dictionary of dataframes by series_id
        output_dir (Path): Output directory
    """
    timestamp = datetime.now().strftime("%Y%m%d")
    
    print(f"\n{'='*60}")
    print(f"Saving UI Claims Data")
    print(f"{'='*60}\n")
    
    # Save individual series
    for series_id, df in data_dict.items():
        filename = f"[{timestamp}]_{series_id}.csv"
        filepath = output_dir / filename
        df.to_csv(filepath, index=False)
        print(f"[SAVED] {filepath.name} ({len(df)} rows)")
    
    # Save combined file
    if data_dict:
        combined = pd.concat(data_dict.values(), ignore_index=True)
        combined_path = output_dir / f"[{timestamp}]_ui_claims_combined.csv"
        combined.to_csv(combined_path, index=False)
        print(f"[SAVED] {combined_path.name} ({len(combined)} rows, {len(data_dict)} series)")


def generate_summary_report(data_dict, output_dir):
    """
    Generate summary report of UI claims data.
    
    Args:
        data_dict (dict): Dictionary of dataframes by series_id
        output_dir (Path): Output directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    report_path = output_dir / f"[{timestamp}]_ui_claims_summary.txt"
    
    with open(report_path, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("UI CLAIMS DATA UPDATE SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Series: {len(data_dict)}\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("SERIES DETAILS\n")
        f.write("-" * 80 + "\n\n")
        
        for series_id, df in data_dict.items():
            f.write(f"Series: {series_id}\n")
            f.write(f"  Observations: {len(df)}\n")
            f.write(f"  Date Range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}\n")
            f.write(f"  Latest Value: {df['value'].iloc[-1]:,.0f}\n")
            f.write(f"  Mean: {df['value'].mean():,.0f}\n")
            f.write(f"  Std Dev: {df['value'].std():,.0f}\n")
            f.write(f"  Min: {df['value'].min():,.0f}\n")
            f.write(f"  Max: {df['value'].max():,.0f}\n")
            f.write("\n")
        
        f.write("-" * 80 + "\n")
        f.write("LEADING INDICATOR ANALYSIS\n")
        f.write("-" * 80 + "\n\n")
        
        if "ICSA" in data_dict:
            icsa = data_dict["ICSA"]
            recent_4wk = icsa.tail(4)["value"].mean()
            recent_13wk = icsa.tail(13)["value"].mean()
            
            f.write(f"Initial Claims (ICSA):\n")
            f.write(f"  Latest (week ending {icsa['date'].iloc[-1].strftime('%Y-%m-%d')}): {icsa['value'].iloc[-1]:,.0f}\n")
            f.write(f"  4-Week Average: {recent_4wk:,.0f}\n")
            f.write(f"  13-Week Average: {recent_13wk:,.0f}\n")
            
            if recent_4wk > recent_13wk:
                f.write(f"  Trend: RISING (potential labor market weakening)\n")
            else:
                f.write(f"  Trend: FALLING (potential labor market strengthening)\n")
        
        f.write("\n")
        f.write("-" * 80 + "\n")
        f.write("NOTES\n")
        f.write("-" * 80 + "\n\n")
        f.write("- Initial claims typically LEAD unemployment rate by 1-2 months\n")
        f.write("- Sustained increases in claims suggest rising unemployment ahead\n")
        f.write("- Compare to pre-pandemic baseline (~220K) for context\n")
        f.write("- COVID-19 peak: 6.15M (April 2020)\n")
        f.write("- Great Recession peak: 665K (March 2009)\n")
        f.write("\n")
    
    print(f"[SAVED] {report_path.name}")


def update_master_catalog(data_dict, catalog_path):
    """
    Update master catalog with UI claims data.
    
    Args:
        data_dict (dict): Dictionary of dataframes by series_id
        catalog_path (Path): Path to master catalog CSV
    """
    if not catalog_path.exists():
        print(f"[WARNING] Master catalog not found: {catalog_path}")
        return
    
    print(f"\n[UPDATE] Updating master catalog...")
    
    catalog = pd.read_csv(catalog_path)
    
    for series_id, df in data_dict.items():
        new_row = {
            "source": "FRED_REALTIME",
            "category": "UI_CLAIMS",
            "dataset_name": f"{series_id}_weekly",
            "file_name": f"{series_id}.csv",
            "records": len(df),
            "start_date": df["date"].min().strftime("%Y-%m-%d"),
            "end_date": df["date"].max().strftime("%Y-%m-%d"),
            "collection_date": datetime.now().strftime("%Y-%m-%d"),
            "quality_tier": 2,
            "tier_description": "Official survey data (weekly real-time)",
            "collection_method": "Administrative",
            "time_period_flag": "REALTIME",
            "frequency": "weekly"
        }
        
        # Check if series already exists (handle different catalog column names)
        name_col = "dataset_name" if "dataset_name" in catalog.columns else "file_name"
        key_value = new_row.get("dataset_name", new_row.get("file_name", series_id))

        if name_col in catalog.columns:
            existing = catalog[catalog[name_col] == key_value]
        else:
            existing = pd.DataFrame()

        if not existing.empty:
            for col, val in new_row.items():
                if col in catalog.columns:
                    catalog.loc[catalog[name_col] == key_value, col] = val
            print(f"  [UPDATED] {series_id} in catalog")
        else:
            catalog = pd.concat([catalog, pd.DataFrame([new_row])], ignore_index=True)
            print(f"  [ADDED] {series_id} to catalog")
    
    catalog.to_csv(catalog_path, index=False)
    print(f"[SUCCESS] Master catalog updated")


def main():
    """Main execution function."""
    print("\n" + "=" * 80)
    print("WEEKLY UNEMPLOYMENT INSURANCE CLAIMS UPDATER")
    print("=" * 80 + "\n")
    
    # Check for API key
    if FRED_API_KEY is None:
        print("[ERROR] FRED_API_KEY not found in environment variables")
        print("[INFO] To use this script:")
        print("  1. Register for API key: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("  2. Set environment variable: $env:FRED_API_KEY='your_key_here'")
        print("\n[FALLBACK] Using existing source FRED store data if available...\n")
        
        # Try to use existing the source store data
        source_fred_path = DATA_ROOT / "API_MODULES/FRED/data"
        if source_fred_path.exists():
            print(f"[INFO] Found existing FRED data in the source store: {source_fred_path}")
            print(f"[INFO] Consider using that data instead, or register for API key.")
        
        return
    
    # Download data
    ui_claims_data = download_ui_claims_data(lookback_years=5)
    
    if not ui_claims_data:
        print("\n[ERROR] No data downloaded. Check API key and network connection.")
        return
    
    # Save data
    save_ui_claims_data(ui_claims_data, INPUTS_DIR)
    
    # Generate summary report
    generate_summary_report(ui_claims_data, OUTPUTS_DIR)
    
    # Update master catalog
    update_master_catalog(ui_claims_data, CATALOG_PATH)
    
    print("\n" + "=" * 80)
    print("UPDATE COMPLETE")
    print("=" * 80)
    print(f"\nData Location: {INPUTS_DIR}")
    print(f"Report Location: {OUTPUTS_DIR}")
    print(f"\nNext Steps:")
    print("  1. Review summary report")
    print("  2. Integrate into dashboard (add 'Real-Time Indicators' tab)")
    print("  3. Schedule weekly updates (Task Scheduler or cron)")
    print("\n")


if __name__ == "__main__":
    main()
