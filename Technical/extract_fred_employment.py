"""
Extract employment-related series from FRED SQLite database
"""
import sqlite3
import pandas as pd
import os

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "data"))


# Source and destination paths
FRED_DB = str(DATA_ROOT / "DATA/FRED/fred_data/fred_data.db")
OUTPUT_DIR = str(PROJECT_ROOT / "Inputs/source/FRED")

# Employment-related keywords for filtering
EMPLOYMENT_KEYWORDS = [
    'employ', 'EMPLOY', 'Employ',
    'unemployment', 'UNEMPLOYMENT', 'Unemployment',
    'jobless', 'JOBLESS', 'Jobless',
    'payroll', 'PAYROLL', 'Payroll',
    'labor force', 'LABOR FORCE', 'Labor Force',
    'workforce', 'WORKFORCE', 'Workforce',
    'participation rate', 'PARTICIPATION RATE',
    'nonfarm', 'NONFARM', 'Nonfarm',
    'job openings', 'JOB OPENINGS',
    'JOLTS', 'jolts',
    'claims', 'CLAIMS', 'Claims',  # unemployment claims
]

def extract_employment_series():
    """Extract all employment-related series from FRED database"""

    print("Connecting to FRED database...")
    conn = sqlite3.connect(FRED_DB)

    # Get all series metadata
    print("Loading series metadata...")
    metadata_query = "SELECT * FROM fred_series"
    metadata = pd.read_sql_query(metadata_query, conn)

    print(f"Total FRED series: {len(metadata)}")

    # Filter for employment-related series
    employment_mask = metadata['title'].str.contains('|'.join(EMPLOYMENT_KEYWORDS), case=False, na=False)
    employment_series = metadata[employment_mask]

    print(f"Employment-related series found: {len(employment_series)}")

    # Save employment series metadata
    employment_series.to_csv(
        os.path.join(OUTPUT_DIR, "fred_employment_series_metadata.csv"),
        index=False
    )
    print(f"Saved metadata to fred_employment_series_metadata.csv")

    # Extract actual data for employment series
    series_ids = employment_series['series_id'].tolist()

    all_employment_data = []

    for series_id in series_ids:
        data_query = f"SELECT * FROM fred_observations WHERE series_id = '{series_id}'"
        series_data = pd.read_sql_query(data_query, conn)
        all_employment_data.append(series_data)

    # Combine all employment data
    if all_employment_data:
        combined_data = pd.concat(all_employment_data, ignore_index=True)
        combined_data.to_csv(
            os.path.join(OUTPUT_DIR, "fred_employment_observations.csv"),
            index=False
        )
        print(f"Saved {len(combined_data)} employment observations to fred_employment_observations.csv")

    conn.close()

    # Print summary statistics
    print("\n" + "="*60)
    print("FRED EMPLOYMENT DATA EXTRACTION SUMMARY")
    print("="*60)
    print(f"Total employment series: {len(employment_series)}")
    print(f"Total observations: {len(combined_data) if all_employment_data else 0}")
    print(f"\nTop 10 employment series by title:")
    for idx, row in employment_series.head(10).iterrows():
        print(f"  - {row['series_id']}: {row['title']}")
    print("="*60)

    return employment_series, combined_data if all_employment_data else None

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    employment_series, employment_data = extract_employment_series()
    print("\nExtraction complete!")
