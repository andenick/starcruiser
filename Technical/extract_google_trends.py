"""
Google Trends Labor Market Proxy Extractor
==========================================

Downloads Google search interest data for labor market-related terms.
Tests hypothesis: Spikes in unemployment-related searches predict rising unemployment.

Search Terms:
- "unemployment benefits"
- "file for unemployment"  
- "jobs near me"
- "resume"

Output: Weekly search index (2004-present) for correlation analysis

Author: StarCruiser Project
Created: December 5, 2025
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import time

import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "data"))


# Project paths
BASE_DIR = PROJECT_ROOT
INPUTS_DIR = BASE_DIR / "Inputs" / "External" / "Google_Trends"
OUTPUTS_DIR = BASE_DIR / "Outputs" / "REALTIME"

# Create directories
INPUTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def check_pytrends():
    """Check if pytrends is installed."""
    try:
        from pytrends.request import TrendReq
        return True
    except ImportError:
        return False


def download_google_trends(keywords, geo="US", timeframe="today 5-y"):
    """
    Download Google Trends data for specified keywords.
    
    Args:
        keywords (list): List of search terms
        geo (str): Geographic region (US, GB, etc.)
        timeframe (str): Time period (e.g., 'today 5-y', 'all', '2019-01-01 2024-12-31')
    
    Returns:
        pd.DataFrame: Trends data with columns for each keyword
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("[ERROR] pytrends not installed")
        print("[FIX] Run: pip install pytrends")
        return None
    
    print(f"\n{'='*60}")
    print(f"Downloading Google Trends Data")
    print(f"Keywords: {', '.join(keywords)}")
    print(f"Region: {geo}")
    print(f"Timeframe: {timeframe}")
    print(f"{'='*60}\n")
    
    # Initialize pytrends
    pytrends = TrendReq(hl='en-US', tz=360)
    
    try:
        # Build payload
        print(f"[REQUEST] Building payload...")
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo, gprop='')
        
        # Get interest over time
        print(f"[DOWNLOAD] Fetching interest over time...")
        trends_df = pytrends.interest_over_time()
        
        if trends_df.empty:
            print(f"[WARNING] No data returned for keywords: {keywords}")
            return None
        
        # Drop 'isPartial' column if exists
        if 'isPartial' in trends_df.columns:
            trends_df = trends_df.drop(columns=['isPartial'])
        
        print(f"[SUCCESS] Downloaded {len(trends_df)} observations")
        print(f"  Date range: {trends_df.index.min()} to {trends_df.index.max()}")
        print(f"  Columns: {list(trends_df.columns)}")
        
        return trends_df
        
    except Exception as e:
        print(f"[ERROR] Failed to download trends data: {e}")
        return None


def download_all_labor_market_terms():
    """
    Download trends for all labor market-related search terms.
    
    Note: Google Trends API limits to 5 keywords per request.
    We'll make multiple requests if needed.
    
    Returns:
        dict: Dictionary of dataframes by keyword group
    """
    # Define keyword groups (max 5 per group due to API limits)
    keyword_groups = {
        "unemployment_group": [
            "unemployment benefits",
            "file for unemployment",
            "unemployment office",
            "unemployment claim"
        ],
        "job_search_group": [
            "jobs near me",
            "job search",
            "indeed",
            "linkedin jobs"
        ],
        "resume_group": [
            "resume",
            "resume template",
            "how to write a resume",
            "resume builder"
        ],
        "layoff_group": [
            "layoffs",
            "fired from job",
            "unemployment insurance",
            "apply for unemployment"
        ]
    }
    
    all_trends = {}
    
    for group_name, keywords in keyword_groups.items():
        print(f"\n[GROUP] Processing {group_name}...")
        
        # Download this group
        df = download_google_trends(keywords, geo="US", timeframe="all")
        
        if df is not None:
            all_trends[group_name] = df
            
        # Rate limit: wait between requests
        print(f"[WAIT] Pausing 10 seconds (rate limit)...")
        time.sleep(10)
    
    return all_trends


def save_trends_data(trends_dict, output_dir):
    """
    Save Google Trends data to CSV files.
    
    Args:
        trends_dict (dict): Dictionary of dataframes by group
        output_dir (Path): Output directory
    """
    timestamp = datetime.now().strftime("%Y%m%d")
    
    print(f"\n{'='*60}")
    print(f"Saving Google Trends Data")
    print(f"{'='*60}\n")
    
    # Save individual groups
    for group_name, df in trends_dict.items():
        filename = f"[{timestamp}]_google_trends_{group_name}.csv"
        filepath = output_dir / filename
        df.to_csv(filepath)
        print(f"[SAVED] {filepath.name} ({len(df)} rows, {len(df.columns)} terms)")
    
    # Save combined file
    if trends_dict:
        # Concatenate all groups (horizontally)
        combined = pd.concat(trends_dict.values(), axis=1)
        combined_path = output_dir / f"[{timestamp}]_google_trends_combined.csv"
        combined.to_csv(combined_path)
        print(f"[SAVED] {combined_path.name} ({len(combined)} rows, {len(combined.columns)} terms)")


def generate_correlation_analysis(trends_dict, output_dir):
    """
    Generate correlation analysis with unemployment rate (if available).
    
    Args:
        trends_dict (dict): Dictionary of trend dataframes
        output_dir (Path): Output directory
    """
    # Try to load unemployment rate from StarCruiser data
    employment_file = DATA_ROOT / "API_MODULES/FRED/data/[2025.09.29] fred_employment_20250929.csv"
    
    if not employment_file.exists():
        print(f"[WARNING] Employment data not found, skipping correlation analysis")
        return
    
    print(f"\n{'='*60}")
    print(f"Correlation Analysis")
    print(f"{'='*60}\n")
    
    # Load UNRATE (unemployment rate)
    employment_df = pd.read_csv(employment_file)
    unrate = employment_df[employment_df["series_id"] == "UNRATE"].copy()
    unrate["date"] = pd.to_datetime(unrate["date"])
    unrate = unrate.set_index("date")["value"]
    unrate = unrate.resample("W").mean()  # Weekly average
    
    # Combine all trends
    all_trends = pd.concat(trends_dict.values(), axis=1)
    
    # Align dates
    merged = pd.merge(
        all_trends,
        unrate.to_frame("unemployment_rate"),
        left_index=True,
        right_index=True,
        how="inner"
    )
    
    if merged.empty:
        print(f"[WARNING] No overlapping dates between trends and unemployment data")
        return
    
    # Calculate correlations
    correlations = {}
    for col in all_trends.columns:
        if col in merged.columns:
            corr = merged[col].corr(merged["unemployment_rate"])
            correlations[col] = corr
    
    # Sort by absolute correlation
    corr_df = pd.DataFrame.from_dict(correlations, orient="index", columns=["correlation"])
    corr_df = corr_df.sort_values("correlation", ascending=False, key=abs)
    
    # Save correlation report
    timestamp = datetime.now().strftime("%Y%m%d")
    corr_path = output_dir / f"[{timestamp}]_trends_unemployment_correlation.csv"
    corr_df.to_csv(corr_path)
    print(f"[SAVED] {corr_path.name}")
    
    # Generate summary report
    report_path = output_dir / f"[{timestamp}]_trends_analysis_summary.txt"
    
    with open(report_path, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("GOOGLE TRENDS LABOR MARKET ANALYSIS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("CORRELATION WITH UNEMPLOYMENT RATE\n")
        f.write("-" * 80 + "\n\n")
        
        f.write(f"{'Search Term':<40} {'Correlation':>12}\n")
        f.write("-" * 80 + "\n")
        
        for term, corr in corr_df.iterrows():
            f.write(f"{term:<40} {corr['correlation']:>12.3f}\n")
        
        f.write("\n")
        f.write("-" * 80 + "\n")
        f.write("INTERPRETATION\n")
        f.write("-" * 80 + "\n\n")
        
        f.write("Positive correlation: Search interest rises when unemployment rises\n")
        f.write("Negative correlation: Search interest falls when unemployment rises\n")
        f.write("\n")
        f.write("Expected patterns:\n")
        f.write("  - 'unemployment benefits' should have POSITIVE correlation\n")
        f.write("  - 'jobs near me' may have POSITIVE correlation (people looking for work)\n")
        f.write("  - Strong correlations (|r| > 0.6) suggest predictive value\n")
        f.write("\n")
        
        # Top correlated terms
        top_3 = corr_df.head(3)
        f.write("Top 3 Most Correlated Terms:\n")
        for i, (term, row) in enumerate(top_3.iterrows(), 1):
            f.write(f"  {i}. {term} (r = {row['correlation']:.3f})\n")
        
        f.write("\n")
        f.write("-" * 80 + "\n")
        f.write("NOTES\n")
        f.write("-" * 80 + "\n\n")
        f.write("- Google Trends index ranges 0-100 (relative search interest)\n")
        f.write("- Data is normalized within each keyword (not comparable across terms)\n")
        f.write("- Correlation does not imply causation\n")
        f.write("- Consider lag analysis (do searches LEAD unemployment?)\n")
        f.write("\n")
    
    print(f"[SAVED] {report_path.name}")
    
    print(f"\n[SUMMARY] Top 3 Most Correlated Terms:")
    for i, (term, row) in enumerate(top_3.iterrows(), 1):
        print(f"  {i}. {term} (r = {row['correlation']:.3f})")


def main():
    """Main execution function."""
    print("\n" + "=" * 80)
    print("GOOGLE TRENDS LABOR MARKET PROXY EXTRACTOR")
    print("=" * 80 + "\n")
    
    # Check if pytrends is installed
    if not check_pytrends():
        print("[ERROR] pytrends package not installed")
        print("[FIX] Run: pip install pytrends")
        print("\nExiting...")
        return
    
    # Download all labor market terms
    trends_data = download_all_labor_market_terms()
    
    if not trends_data:
        print("\n[ERROR] No data downloaded. Check network connection.")
        return
    
    # Save data
    save_trends_data(trends_data, INPUTS_DIR)
    
    # Generate correlation analysis
    generate_correlation_analysis(trends_data, OUTPUTS_DIR)
    
    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"\nData Location: {INPUTS_DIR}")
    print(f"Analysis Location: {OUTPUTS_DIR}")
    print(f"\nNext Steps:")
    print("  1. Review correlation analysis")
    print("  2. Test lag analysis (do searches lead unemployment by 1-2 weeks?)")
    print("  3. Integrate into dashboard as experimental indicator")
    print("\n")


if __name__ == "__main__":
    main()
