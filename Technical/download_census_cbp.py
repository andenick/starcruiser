"""
Census County Business Patterns (CBP) Downloader
=================================================

Downloads comprehensive county-level employment data from Census Bureau.
County Business Patterns (CBP) provides employment, establishments, and payroll
data by county and industry (NAICS codes).

Data Coverage:
- Geographic: All US counties (~3,220)
- Industry: NAICS codes (2-digit to 6-digit detail)
- Temporal: 1986-2022 (annual)
- Variables: Employment, establishments, payroll

Author: StarCruiser Project
Created: December 5, 2025
"""

import os
import sys
import json
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "data"))


# Add the source store API path
SOURCE_API_PATH = DATA_ROOT / "API_MODULES"
sys.path.insert(0, str(SOURCE_API_PATH))

# Project paths
BASE_DIR = PROJECT_ROOT
INPUTS_DIR = BASE_DIR / "Inputs" / "source" / "CENSUS_CBP"
OUTPUTS_DIR = BASE_DIR / "Outputs" / "CBP_DOWNLOAD"
SOURCE_ADMIN = DATA_ROOT / "ADMIN/api-keys"

# Create directories
INPUTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Census API configuration
CENSUS_API_BASE = "https://api.census.gov/data"


class CBPDownloader:
    """Download County Business Patterns data from Census API."""
    
    def __init__(self):
        """Initialize CBP downloader with API key."""
        self.api_key = self._load_census_api_key()
        
        if not self.api_key:
            raise ValueError("Census API key not found. Check the source store ADMIN/api-keys/[2025.09.28] api_keys.json")
        
        print(f"[INFO] Census API key loaded (length: {len(self.api_key)})")
        
        # Rate limiting
        self.rate_limit_delay = 0.5  # 500ms between requests
        self.last_request_time = 0
        
        # Downloaded data tracker
        self.downloaded_years = []
        self.total_records = 0
    
    def _load_census_api_key(self):
        """Load Census API key.

        Prefers the CENSUS_API_KEY environment variable (get a free key at
        https://api.census.gov/data/key_signup.html). Falls back to an optional
        local admin JSON for development.
        """
        env_key = os.environ.get("CENSUS_API_KEY")
        if env_key:
            return env_key
        try:
            api_keys_file = SOURCE_ADMIN / "[2025.09.28] api_keys.json"

            if not api_keys_file.exists():
                print(f"[ERROR] API keys file not found: {api_keys_file}")
                return None

            with open(api_keys_file, 'r') as f:
                keys = json.load(f)
                return keys.get("census_api_key")
        except Exception as e:
            print(f"[ERROR] Failed to load API key: {e}")
            return None
    
    def _rate_limit(self):
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def download_cbp_year(self, year):
        """
        Download CBP data for a specific year.
        
        Args:
            year (int): Year to download (1986-2022)
        
        Returns:
            pd.DataFrame: CBP data for the year
        """
        print(f"\n{'='*60}")
        print(f"Downloading CBP data for {year}")
        print("=" * 60)
        
        # CBP API endpoint varies by year
        if year >= 2017:
            endpoint = f"{CENSUS_API_BASE}/{year}/cbp"
        elif year >= 2012:
            endpoint = f"{CENSUS_API_BASE}/{year}/cbp"
        else:
            # Earlier years may have different endpoint structure
            endpoint = f"{CENSUS_API_BASE}/{year}/cbp"
        
        # Key variables to request (correct variable names from API)
        variables = [
            "EMP",            # Employment
            "ESTAB",          # Number of establishments
            "PAYANN",         # Annual payroll ($1,000)
            "NAICS2017",      # Industry code (NAICS 2017 classification)
            "SECTOR",         # Sector (2-digit NAICS)
            "SUBSECTOR",      # Subsector (3-digit NAICS)
            "YEAR",           # Year
            "GEO_ID"          # Geographic identifier
        ]
        
        # Request parameters
        # Note: 'state' and 'county' come from the 'for' parameter, not 'get'
        params = {
            "get": ",".join(variables),
            "for": "county:*",  # All counties
            "in": "state:*",    # All states
            "key": self.api_key
        }
        
        try:
            self._rate_limit()
            
            print(f"[REQUEST] {endpoint}")
            response = requests.get(endpoint, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or len(data) < 2:
                print(f"[WARNING] No data returned for {year}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Extract state and county from response (they come as separate columns)
            # and add year if not in response
            if "YEAR" not in df.columns:
                df["YEAR"] = year
            
            # Convert numeric columns
            numeric_cols = ["EMP", "ESTAB", "PAYANN", "YEAR"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            
            # Count unique values
            counties = df["county"].nunique() if "county" in df.columns else "N/A"
            industries = df['NAICS2017'].nunique() if 'NAICS2017' in df.columns else "N/A"
            
            print(f"[SUCCESS] Downloaded {len(df):,} records for {year}")
            print(f"  Counties: {counties}")
            print(f"  Industries: {industries}")
            
            return df
            
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] HTTP error for {year}: {e}")
            print(f"  Status code: {response.status_code}")
            print(f"  Response: {response.text[:500]}")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to download {year}: {e}")
            return None
    
    def download_cbp_range(self, start_year=2012, end_year=2022):
        """
        Download CBP data for a range of years.
        
        Args:
            start_year (int): First year to download
            end_year (int): Last year to download
        
        Returns:
            pd.DataFrame: Combined CBP data
        """
        print("\n" + "=" * 80)
        print("CENSUS COUNTY BUSINESS PATTERNS DOWNLOADER")
        print("=" * 80)
        print(f"Year range: {start_year}-{end_year}")
        print(f"Output: {INPUTS_DIR}")
        print("=" * 80 + "\n")
        
        all_data = []
        failed_years = []
        
        for year in range(start_year, end_year + 1):
            df = self.download_cbp_year(year)
            
            if df is not None:
                all_data.append(df)
                self.downloaded_years.append(year)
                self.total_records += len(df)
                
                # Save individual year file
                year_file = INPUTS_DIR / f"cbp_{year}.csv"
                df.to_csv(year_file, index=False)
                print(f"[SAVED] {year_file.name}")
            else:
                failed_years.append(year)
            
            # Small delay between years
            time.sleep(1)
        
        if not all_data:
            print("\n[ERROR] No data downloaded!")
            return None
        
        # Combine all years
        combined = pd.concat(all_data, ignore_index=True)
        
        # Save combined file
        timestamp = datetime.now().strftime("%Y%m%d")
        combined_file = INPUTS_DIR / f"[{timestamp}]_cbp_combined_{start_year}_{end_year}.csv"
        combined.to_csv(combined_file, index=False)
        
        print(f"\n{'='*60}")
        print("DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"Years downloaded: {len(self.downloaded_years)} / {end_year - start_year + 1}")
        print(f"  Successful: {self.downloaded_years}")
        if failed_years:
            print(f"  Failed: {failed_years}")
        print(f"Total records: {self.total_records:,}")
        print(f"Combined file: {combined_file.name}")
        print(f"Individual files: {len(all_data)} (one per year)")
        
        # Generate metadata
        metadata = {
            "download_date": datetime.now().isoformat(),
            "year_range": f"{start_year}-{end_year}",
            "years_downloaded": self.downloaded_years,
            "years_failed": failed_years,
            "total_records": self.total_records,
            "counties": int(combined["county"].nunique()),
            "states": int(combined["state"].nunique()),
            "combined_file": combined_file.name,
            "data_source": "US Census Bureau County Business Patterns",
            "api_endpoint": CENSUS_API_BASE
        }
        
        metadata_file = OUTPUTS_DIR / f"[{timestamp}]_cbp_download_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Metadata: {metadata_file.name}")
        
        return combined
    
    def generate_summary_report(self, df):
        """Generate summary report of downloaded CBP data."""
        if df is None or df.empty:
            print("[WARNING] No data to summarize")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        report_path = OUTPUTS_DIR / f"[{timestamp}]_cbp_summary_report.txt"
        
        with open(report_path, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("CENSUS COUNTY BUSINESS PATTERNS SUMMARY REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("DATA COVERAGE\n")
            f.write("-" * 80 + "\n\n")
            
            f.write(f"Total Records: {len(df):,}\n")
            f.write(f"Years: {df['year'].min()} to {df['year'].max()}\n")
            f.write(f"States: {df['state'].nunique()}\n")
            f.write(f"Counties: {df['county'].nunique()}\n")
            
            if "NAICS2017" in df.columns:
                f.write(f"Industries (NAICS codes): {df['NAICS2017'].nunique()}\n")
            
            f.write("\n")
            f.write("-" * 80 + "\n")
            f.write("EMPLOYMENT STATISTICS\n")
            f.write("-" * 80 + "\n\n")
            
            if "EMP" in df.columns:
                emp_df = df[df["EMP"].notna()]
                f.write(f"Records with employment data: {len(emp_df):,}\n")
                f.write(f"Total employment (sum): {emp_df['EMP'].sum():,.0f}\n")
                f.write(f"Mean employment per record: {emp_df['EMP'].mean():,.0f}\n")
                f.write(f"Median employment: {emp_df['EMP'].median():,.0f}\n")
            
            if "ESTAB" in df.columns:
                estab_df = df[df["ESTAB"].notna()]
                f.write(f"\nTotal establishments: {estab_df['ESTAB'].sum():,.0f}\n")
            
            if "PAYANN" in df.columns:
                payroll_df = df[df["PAYANN"].notna()]
                f.write(f"Total annual payroll: ${payroll_df['PAYANN'].sum():,.0f} thousand\n")
            
            f.write("\n")
            f.write("-" * 80 + "\n")
            f.write("TOP 10 COUNTIES BY EMPLOYMENT\n")
            f.write("-" * 80 + "\n\n")
            
            if "EMP" in df.columns:
                # Get latest year data
                year_col = "YEAR" if "YEAR" in df.columns else "year"
                latest_year = df[year_col].max()
                latest_df = df[df[year_col] == latest_year]
                
                # Aggregate by county (sum across industries)
                group_cols = ["state", "county"] if "county" in df.columns else ["state"]
                county_emp = latest_df.groupby(group_cols)["EMP"].sum().reset_index()
                top_counties = county_emp.nlargest(10, "EMP")
                
                for i, row in enumerate(top_counties.itertuples(), 1):
                    geo_id = f"State {row.state}, County {row.county}" if "county" in df.columns else f"State {row.state}"
                    f.write(f"{i:2d}. {geo_id}: {row.EMP:,.0f} employees\n")
            
            f.write("\n")
            f.write("-" * 80 + "\n")
            f.write("DATA QUALITY NOTES\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("- CBP data is based on administrative records (high quality)\n")
            f.write("- Small county values may be suppressed for disclosure protection\n")
            f.write("- Self-employed and some industries excluded (see Census documentation)\n")
            f.write("- NAICS codes changed over time (2002, 2007, 2012, 2017)\n")
            f.write("\n")
        
        print(f"\n[SAVED] Summary report: {report_path.name}")


def main():
    """Main execution function."""
    try:
        downloader = CBPDownloader()
        
        # Download CBP data for recent years (2012-2022)
        # Note: Earlier years (1986-2011) available but may have different data structure
        print("\n[INFO] Starting CBP download for 2012-2022...")
        print("[INFO] This will take approximately 5-10 minutes...")
        
        df = downloader.download_cbp_range(start_year=2012, end_year=2022)
        
        if df is not None:
            # Generate summary report
            downloader.generate_summary_report(df)
            
            print("\n" + "=" * 80)
            print("CBP DOWNLOAD COMPLETE")
            print("=" * 80)
            print(f"Data location: {INPUTS_DIR}")
            print(f"Report location: {OUTPUTS_DIR}")
            print("\nNext steps:")
            print("  1. Review summary report")
            print("  2. Run validate_census_cbp.py to check data quality")
            print("  3. Proceed with Track B geographic analysis")
            print("\n")
        else:
            print("\n[ERROR] Download failed. Check error messages above.")
            
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
