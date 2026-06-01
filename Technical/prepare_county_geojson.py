"""
Prepare County GeoJSON for StarCruiser Dashboard Leaflet Map
=============================================================
Track B1.1: Merge county boundaries with cluster assignments into a single
GeoJSON file for the interactive leaflet map.

Usage:
    python prepare_county_geojson.py

Output:
    Dashboard/data/counties_with_clusters.geojson
"""

from pathlib import Path
from datetime import datetime
import json
import logging
import zipfile
import io

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = PROJECT_ROOT
CLUSTER_DIR = BASE_DIR / "Outputs" / "CLUSTERS"
# Find the most recent cluster assignments file (may have timestamp prefix)
_cluster_files = sorted(CLUSTER_DIR.glob("*cluster_assignments.csv")) if CLUSTER_DIR.exists() else []
CLUSTER_FILE = _cluster_files[-1] if _cluster_files else CLUSTER_DIR / "cluster_assignments.csv"
OUTPUT_DIR = BASE_DIR / "Dashboard" / "data"
OUTPUT_FILE = OUTPUT_DIR / "counties_with_clusters.geojson"

# Census TIGER/Line cartographic boundary file (20m resolution, ~5MB)
TIGER_URL = "https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_county_20m.zip"


def prepare_geojson_with_geopandas():
    """Primary method using geopandas for full GeoJSON with cluster data."""
    import geopandas as gpd
    import pandas as pd

    logger.info("Downloading county boundaries from Census TIGER/Line...")
    counties = gpd.read_file(TIGER_URL)
    logger.info(f"  Loaded {len(counties)} county boundaries")

    # Load cluster assignments
    logger.info("Loading cluster assignments...")
    clusters = pd.read_csv(CLUSTER_FILE)
    logger.info(f"  Loaded {len(clusters)} cluster assignments")

    # Determine FIPS column in clusters
    fips_col = None
    for col in ['fips', 'FIPS', 'GEO_ID', 'geo_id', 'GEOID']:
        if col in clusters.columns:
            fips_col = col
            break

    if fips_col is None:
        # Try constructing from state + county columns
        if 'state' in clusters.columns and 'county' in clusters.columns:
            clusters['fips'] = (
                clusters['state'].astype(str).str.zfill(2) +
                clusters['county'].astype(str).str.zfill(3)
            )
            fips_col = 'fips'
        else:
            raise ValueError("Cannot find FIPS column in cluster data")

    # Ensure FIPS is string and zero-padded
    clusters[fips_col] = clusters[fips_col].astype(str).str.zfill(5)

    # Add cluster_name if only numeric cluster column exists
    if 'cluster' in clusters.columns and 'cluster_name' not in clusters.columns:
        cluster_names = {
            0: "Growing Manufacturing", 1: "Service & Retail (Small)",
            2: "Service & Retail (Large)", 3: "Extreme Manufacturing",
            4: "Agricultural Services", 5: "Tourism & Hospitality",
            6: "Boom Counties (Mining)", 7: "Education & Healthcare"
        }
        clusters['cluster_name'] = clusters['cluster'].map(cluster_names)

    # Clean up GEOID in shapefile (remove prefix if present)
    counties['GEOID'] = counties['GEOID'].astype(str).str.zfill(5)

    # Merge clusters with county boundaries
    logger.info("Merging cluster data with county boundaries...")
    merged = counties.merge(clusters, left_on='GEOID', right_on=fips_col, how='left')
    matched = merged['cluster_name'].notna().sum() if 'cluster_name' in merged.columns else 0
    logger.info(f"  Merged: {matched} counties with cluster data")

    # Simplify geometry for performance (tolerance in degrees, ~0.01 = ~1km)
    logger.info("Simplifying geometry for web performance...")
    merged.geometry = merged.geometry.simplify(0.005, preserve_topology=True)

    # Select relevant columns
    keep_cols = ['GEOID', 'NAME', 'STUSPS', 'geometry']
    cluster_cols = [c for c in clusters.columns if c != fips_col and c in merged.columns]
    keep_cols.extend(cluster_cols)
    merged = merged[keep_cols]

    # Write GeoJSON
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing GeoJSON to {OUTPUT_FILE}...")
    merged.to_file(OUTPUT_FILE, driver="GeoJSON")

    file_size = OUTPUT_FILE.stat().st_size / 1024 / 1024
    logger.info(f"  Output size: {file_size:.1f} MB")
    logger.info("Done!")

    return True


def prepare_geojson_without_geopandas():
    """Fallback method: download GeoJSON directly and merge cluster data via JSON manipulation."""
    import pandas as pd
    import requests

    # Use Census Bureau's direct GeoJSON endpoint (cartographic boundaries)
    geojson_url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"

    logger.info("Downloading county GeoJSON (fallback method)...")
    response = requests.get(geojson_url, timeout=120)
    response.raise_for_status()
    geojson = response.json()
    logger.info(f"  Loaded {len(geojson['features'])} county features")

    # Load cluster assignments
    logger.info("Loading cluster assignments...")
    clusters = pd.read_csv(CLUSTER_FILE)

    # Determine FIPS column
    fips_col = None
    for col in ['fips', 'FIPS', 'GEO_ID', 'geo_id', 'GEOID']:
        if col in clusters.columns:
            fips_col = col
            break

    if fips_col is None and 'state' in clusters.columns and 'county' in clusters.columns:
        clusters['fips'] = (
            clusters['state'].astype(str).str.zfill(2) +
            clusters['county'].astype(str).str.zfill(3)
        )
        fips_col = 'fips'

    if fips_col is None:
        raise ValueError("Cannot find FIPS column in cluster data")

    clusters[fips_col] = clusters[fips_col].astype(str).str.zfill(5)

    # Build lookup dict from clusters
    cluster_lookup = {}
    cluster_cols = [c for c in clusters.columns if c != fips_col]
    for _, row in clusters.iterrows():
        fips = row[fips_col]
        cluster_lookup[fips] = {col: row[col] for col in cluster_cols
                                if pd.notna(row[col])}

    # Merge cluster data into GeoJSON properties
    matched = 0
    for feature in geojson['features']:
        fips = feature.get('id', feature.get('properties', {}).get('GEOID', ''))
        fips = str(fips).zfill(5)
        feature['properties']['GEOID'] = fips

        if fips in cluster_lookup:
            # Convert numpy types to Python native types
            for k, v in cluster_lookup[fips].items():
                try:
                    feature['properties'][k] = float(v) if isinstance(v, (int, float)) else str(v)
                except (ValueError, TypeError):
                    feature['properties'][k] = str(v)
            matched += 1

    logger.info(f"  Matched {matched} counties with cluster data")

    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(geojson, f)

    file_size = OUTPUT_FILE.stat().st_size / 1024 / 1024
    logger.info(f"  Output size: {file_size:.1f} MB")
    logger.info("Done!")

    return True


def main():
    logger.info("=" * 60)
    logger.info("StarCruiser County GeoJSON Preparation")
    logger.info("=" * 60)

    # Check cluster file exists
    if not CLUSTER_FILE.exists():
        logger.error(f"Cluster file not found: {CLUSTER_FILE}")
        logger.error("Run county_cluster_analysis.py first to generate cluster assignments.")
        return

    # Try geopandas first, fall back to JSON manipulation
    try:
        import geopandas
        logger.info("Using geopandas (full method)")
        prepare_geojson_with_geopandas()
    except ImportError:
        logger.warning("geopandas not installed, using fallback method")
        logger.warning("Install geopandas for better results: pip install geopandas")
        prepare_geojson_without_geopandas()


if __name__ == "__main__":
    main()
