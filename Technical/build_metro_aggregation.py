"""
Metro-Level Employment Aggregation - StarCruiser
=================================================
Track B1.5: Aggregate county CBP data to Metropolitan Statistical Area (MSA) level
using Census CBSA delineation files.

Usage:
    python build_metro_aggregation.py

Input:
    Inputs/source/CENSUS_CBP/[20251205]_cbp_combined_2012_2022.csv (646 MB)

Output:
    Outputs/METRO/metro_employment_YYYYMMDD.csv
    Outputs/METRO/metro_summary_YYYYMMDD.csv
"""

from pathlib import Path
from datetime import datetime
import pandas as pd
import requests
import logging
import io

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = PROJECT_ROOT
CBP_DIR = BASE_DIR / "Inputs" / "source" / "CENSUS_CBP"
OUTPUT_DIR = BASE_DIR / "Outputs" / "METRO"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")

# Census CBSA delineation file URL (March 2023 revision)
CBSA_URL = "https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list2_2023.xlsx"
CBSA_CACHE = BASE_DIR / "Inputs" / "External" / "CENSUS" / "cbsa_delineation_2023.csv"


def download_cbsa_crosswalk():
    """Download or load cached CBSA county-to-MSA crosswalk."""
    cache_dir = CBSA_CACHE.parent
    cache_dir.mkdir(parents=True, exist_ok=True)

    if CBSA_CACHE.exists():
        logger.info(f"Loading cached CBSA crosswalk from {CBSA_CACHE}")
        return pd.read_csv(CBSA_CACHE, dtype=str)

    logger.info("Downloading CBSA delineation file from Census Bureau...")
    try:
        response = requests.get(CBSA_URL, timeout=60)
        response.raise_for_status()

        # Read Excel file
        df = pd.read_excel(io.BytesIO(response.content), dtype=str, skiprows=2)

        # Standardize column names
        col_map = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'fips state' in col_lower:
                col_map[col] = 'state_fips'
            elif 'fips county' in col_lower:
                col_map[col] = 'county_fips'
            elif 'cbsa code' in col_lower:
                col_map[col] = 'cbsa_code'
            elif 'cbsa title' in col_lower:
                col_map[col] = 'cbsa_title'
            elif 'metropolitan/micropolitan' in col_lower:
                col_map[col] = 'metro_micro'
            elif 'central/outlying' in col_lower:
                col_map[col] = 'central_outlying'

        df = df.rename(columns=col_map)

        # Construct 5-digit FIPS
        df['fips'] = df['state_fips'].str.zfill(2) + df['county_fips'].str.zfill(3)

        # Keep relevant columns
        keep_cols = [c for c in ['fips', 'cbsa_code', 'cbsa_title', 'metro_micro', 'central_outlying']
                     if c in df.columns]
        df = df[keep_cols].dropna(subset=['fips', 'cbsa_code'])

        # Cache
        df.to_csv(CBSA_CACHE, index=False)
        logger.info(f"  Cached {len(df)} county-CBSA mappings to {CBSA_CACHE}")

        return df

    except Exception as e:
        logger.error(f"Failed to download CBSA crosswalk: {e}")
        logger.info("Creating simple crosswalk from CBP data instead...")
        return None


def load_cbp_data():
    """Load combined CBP data."""
    combined_file = CBP_DIR / "[20251205]_cbp_combined_2012_2022.csv"

    if combined_file.exists():
        logger.info(f"Loading combined CBP data from {combined_file}...")
        df = pd.read_csv(combined_file, dtype={'state': str, 'county': str})
        logger.info(f"  Loaded {len(df):,} records")
        return df

    # Fall back to individual year files
    logger.info("Loading individual CBP year files...")
    frames = []
    for year_file in sorted(CBP_DIR.glob("cbp_20*.csv")):
        logger.info(f"  Loading {year_file.name}...")
        df = pd.read_csv(year_file, dtype={'state': str, 'county': str})
        frames.append(df)

    if not frames:
        raise FileNotFoundError(f"No CBP data files found in {CBP_DIR}")

    combined = pd.concat(frames, ignore_index=True)
    logger.info(f"  Total: {len(combined):,} records from {len(frames)} files")
    return combined


def main():
    logger.info("=" * 60)
    logger.info("StarCruiser Metro-Level Employment Aggregation")
    logger.info("=" * 60)

    # Load CBP data
    cbp = load_cbp_data()

    # Construct FIPS code
    cbp['state'] = cbp['state'].astype(str).str.zfill(2)
    cbp['county'] = cbp['county'].astype(str).str.zfill(3)
    cbp['fips'] = cbp['state'] + cbp['county']

    # Filter out state and national totals (county = 000)
    cbp = cbp[cbp['county'] != '000'].copy()
    logger.info(f"  County-level records (excluding totals): {len(cbp):,}")

    # Download CBSA crosswalk
    cbsa = download_cbsa_crosswalk()

    if cbsa is not None:
        # Merge CBP with CBSA
        logger.info("Merging CBP with CBSA crosswalk...")
        merged = cbp.merge(cbsa[['fips', 'cbsa_code', 'cbsa_title']], on='fips', how='left')

        in_metro = merged['cbsa_code'].notna().sum()
        total = len(merged)
        logger.info(f"  {in_metro:,} / {total:,} records ({in_metro/total*100:.1f}%) are in MSAs")

        # Filter to metro counties only
        metro_data = merged[merged['cbsa_code'].notna()].copy()
    else:
        logger.warning("No CBSA crosswalk available. Aggregating by state instead.")
        metro_data = cbp.copy()
        metro_data['cbsa_code'] = metro_data['state']
        metro_data['cbsa_title'] = 'State ' + metro_data['state']

    # Determine year column
    year_col = 'YEAR' if 'YEAR' in metro_data.columns else 'year'
    if year_col not in metro_data.columns:
        logger.error("No YEAR column found in CBP data")
        return

    # Determine employment columns
    emp_col = 'EMP' if 'EMP' in metro_data.columns else 'emp'
    estab_col = 'ESTAB' if 'ESTAB' in metro_data.columns else 'estab'
    payroll_col = 'PAYANN' if 'PAYANN' in metro_data.columns else 'payann'

    # Determine NAICS column
    naics_col = None
    for candidate in ['NAICS2017', 'naics2017', 'NAICS', 'naics']:
        if candidate in metro_data.columns:
            naics_col = candidate
            break

    if naics_col is None:
        naics_col = 'SECTOR' if 'SECTOR' in metro_data.columns else 'sector'

    # Convert numeric columns
    for col in [emp_col, estab_col, payroll_col]:
        if col in metro_data.columns:
            metro_data[col] = pd.to_numeric(metro_data[col], errors='coerce').fillna(0).astype(int)

    # Aggregate to MSA level
    logger.info("Aggregating to MSA level...")
    agg_cols = {}
    if emp_col in metro_data.columns:
        agg_cols[emp_col] = 'sum'
    if estab_col in metro_data.columns:
        agg_cols[estab_col] = 'sum'
    if payroll_col in metro_data.columns:
        agg_cols[payroll_col] = 'sum'

    group_cols = ['cbsa_code', 'cbsa_title', year_col]
    if naics_col in metro_data.columns:
        group_cols.append(naics_col)

    metro_agg = metro_data.groupby(group_cols, dropna=False).agg(agg_cols).reset_index()
    metro_agg.columns = [c.lower() for c in metro_agg.columns]

    logger.info(f"  Aggregated to {len(metro_agg):,} MSA-year-industry records")
    logger.info(f"  Unique MSAs: {metro_agg['cbsa_code'].nunique()}")
    logger.info(f"  Year range: {metro_agg[year_col.lower()].min()} - {metro_agg[year_col.lower()].max()}")

    # Save detailed output
    detail_file = OUTPUT_DIR / f"metro_employment_{TIMESTAMP}.csv"
    metro_agg.to_csv(detail_file, index=False)
    logger.info(f"  Saved detailed data to {detail_file}")

    # Create summary (total employment by MSA and year)
    summary_cols = ['cbsa_code', 'cbsa_title', year_col.lower()]
    emp_lower = emp_col.lower()

    # Filter to total (all industries) - NAICS sector "00" or "--"
    naics_lower = naics_col.lower() if naics_col else None
    if naics_lower and naics_lower in metro_agg.columns:
        totals = metro_agg[metro_agg[naics_lower].isin(['00', '--', '0', ''])]
        if len(totals) == 0:
            # Aggregate all sectors
            totals = metro_agg.groupby(['cbsa_code', 'cbsa_title', year_col.lower()]).agg(
                {emp_lower: 'sum'}
            ).reset_index()
    else:
        totals = metro_agg.groupby(['cbsa_code', 'cbsa_title', year_col.lower()]).agg(
            {emp_lower: 'sum'}
        ).reset_index()

    # Sort by employment (largest MSAs first)
    totals = totals.sort_values([year_col.lower(), emp_lower], ascending=[False, False])

    summary_file = OUTPUT_DIR / f"metro_summary_{TIMESTAMP}.csv"
    totals.to_csv(summary_file, index=False)
    logger.info(f"  Saved summary to {summary_file}")

    # Print top 10 MSAs by employment for latest year
    latest_year = totals[year_col.lower()].max()
    top10 = totals[totals[year_col.lower()] == latest_year].head(10)
    logger.info(f"\n  Top 10 MSAs by employment ({latest_year}):")
    for _, row in top10.iterrows():
        logger.info(f"    {row['cbsa_title']}: {row[emp_lower]:,.0f}")

    logger.info("\nDone!")


if __name__ == "__main__":
    main()
