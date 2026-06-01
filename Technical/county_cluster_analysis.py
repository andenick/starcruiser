"""
County Cluster Analysis
=======================

Identifies county typologies through clustering analysis:
- Tech Hubs
- Manufacturing Centers
- Rural Agricultural
- Service-Based Metros
- Declining Regions
- Boom Counties

Uses employment composition, growth rates, and shift-share components.

Author: StarCruiser Project
Date: 2025-12-05
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = Path(os.environ.get("OUTPUT_ROOT", "outputs"))


# Configuration
INPUT_DIR = (PROJECT_ROOT / "Inputs/source/CENSUS_CBP")
SHIFT_SHARE_DIR = OUTPUT_ROOT / "SHIFT_SHARE"
OUTPUT_DIR = OUTPUT_ROOT / "CLUSTERS"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

START_YEAR = 2017
END_YEAR = 2022

# NAICS 2-digit sectors with labels
SECTOR_LABELS = {
    11: 'Agriculture',
    21: 'Mining',
    22: 'Utilities',
    23: 'Construction',
    31: 'Manufacturing',
    42: 'Wholesale',
    44: 'Retail',
    48: 'Transportation',
    51: 'Information',
    52: 'Finance',
    53: 'Real Estate',
    54: 'Professional Services',
    55: 'Management',
    56: 'Admin Support',
    61: 'Education',
    62: 'Healthcare',
    71: 'Arts/Entertainment',
    72: 'Accommodation/Food'
}

SECTORS = list(SECTOR_LABELS.keys())

# Number of clusters to identify
N_CLUSTERS = 8


def load_cbp_data() -> pd.DataFrame:
    """Load and aggregate CBP data."""
    print("Loading CBP data...")
    
    df = pd.read_csv(
        INPUT_DIR / "[20251205]_cbp_combined_2012_2022.csv",
        dtype={'state': 'Int64', 'county': 'Int64', 'SECTOR': 'Int64'},
        usecols=['YEAR', 'EMP', 'SECTOR', 'state', 'county']
    )
    
    df = df.rename(columns={
        'YEAR': 'year',
        'EMP': 'emp',
        'SECTOR': 'naics'
    })
    
    # Filter to 2-digit NAICS, county level, and years
    df = df[df['naics'].isin(SECTORS)].copy()
    df = df[(df['state'].notna()) & (df['county'].notna())].copy()
    df = df[(df['year'] >= START_YEAR) & (df['year'] <= END_YEAR)].copy()
    
    # Aggregate to county-sector-year
    df = df.groupby(['year', 'state', 'county', 'naics'], as_index=False)['emp'].sum()
    
    print(f"  Loaded {len(df):,} records")
    print(f"  Years: {df['year'].min()}-{df['year'].max()}")
    print(f"  Counties: {df['county'].nunique():,}")
    
    return df


def load_shift_share_results() -> pd.DataFrame:
    """Load shift-share decomposition results."""
    print("\nLoading shift-share results...")
    
    # Find most recent shift-share JSON file
    json_files = sorted(SHIFT_SHARE_DIR.glob("*_shift_share_results.json"))
    if not json_files:
        raise FileNotFoundError("No shift-share results found. Run shift_share_decomposition.py first.")
    
    latest_file = json_files[-1]
    print(f"  Using: {latest_file.name}")
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    # Extract full period (2017-2022) results
    # full_results is a list of dictionaries
    df = pd.DataFrame(data['full_results'])
    
    # Filter to full period only
    df = df[(df['start_year'] == START_YEAR) & (df['end_year'] == END_YEAR)].copy()
    
    # Rename columns for consistency
    df = df.rename(columns={
        'initial_employment': 'base_employment'
    })
    
    print(f"  Loaded shift-share data for {len(df):,} counties")
    
    return df[['state', 'county', 'national_effect', 'industry_mix_effect', 
               'regional_share_effect', 'actual_change', 'base_employment']]


def calculate_industry_composition(cbp_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate industry composition shares for each county."""
    print("\nCalculating industry composition...")
    
    # Use END_YEAR for current composition
    df = cbp_df[cbp_df['year'] == END_YEAR].copy()
    
    # Calculate total employment per county
    county_totals = df.groupby(['state', 'county'])['emp'].sum().reset_index()
    county_totals = county_totals.rename(columns={'emp': 'total_emp'})
    
    # Merge totals
    df = df.merge(county_totals, on=['state', 'county'])
    
    # Calculate shares
    df['share'] = df['emp'] / df['total_emp']
    
    # Pivot to get one column per sector
    composition = df.pivot_table(
        index=['state', 'county'],
        columns='naics',
        values='share',
        fill_value=0.0
    ).reset_index()
    
    # Rename columns with sector labels
    composition.columns = ['state', 'county'] + [
        f'share_{SECTOR_LABELS[naics].lower().replace("/", "_").replace(" ", "_")}'
        for naics in composition.columns[2:]
    ]
    
    # Add total employment
    composition = composition.merge(
        county_totals[['state', 'county', 'total_emp']],
        on=['state', 'county']
    )
    
    print(f"  Calculated composition for {len(composition):,} counties")
    
    return composition


def calculate_growth_rates(cbp_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate employment growth rates."""
    print("\nCalculating growth rates...")
    
    # Get start and end year employment
    start_emp = cbp_df[cbp_df['year'] == START_YEAR].groupby(['state', 'county'])['emp'].sum().reset_index()
    start_emp = start_emp.rename(columns={'emp': 'emp_start'})
    
    end_emp = cbp_df[cbp_df['year'] == END_YEAR].groupby(['state', 'county'])['emp'].sum().reset_index()
    end_emp = end_emp.rename(columns={'emp': 'emp_end'})
    
    # Calculate growth
    growth = start_emp.merge(end_emp, on=['state', 'county'])
    growth['employment_change'] = growth['emp_end'] - growth['emp_start']
    growth['employment_growth_rate'] = (growth['emp_end'] / growth['emp_start'] - 1) * 100
    
    print(f"  Calculated growth rates for {len(growth):,} counties")
    
    return growth[['state', 'county', 'emp_start', 'emp_end', 'employment_change', 'employment_growth_rate']]


def prepare_clustering_data(composition: pd.DataFrame, 
                           growth: pd.DataFrame,
                           shift_share: pd.DataFrame) -> pd.DataFrame:
    """Combine all features for clustering."""
    print("\nPreparing clustering dataset...")
    
    # Merge all datasets
    data = composition.merge(growth, on=['state', 'county'])
    data = data.merge(shift_share, on=['state', 'county'])
    
    # Calculate normalized shift-share components (per 1000 workers)
    data['national_effect_per_1k'] = (data['national_effect'] / data['base_employment']) * 1000
    data['industry_mix_effect_per_1k'] = (data['industry_mix_effect'] / data['base_employment']) * 1000
    data['regional_share_effect_per_1k'] = (data['regional_share_effect'] / data['base_employment']) * 1000
    
    # Log of total employment (to capture size)
    data['log_total_emp'] = np.log1p(data['total_emp'])
    
    print(f"  Final dataset: {len(data):,} counties × {len(data.columns)} features")
    
    return data


def perform_clustering(data: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray, StandardScaler, PCA]:
    """Perform K-means clustering with PCA."""
    print(f"\nPerforming clustering (k={N_CLUSTERS})...")
    
    # Select features for clustering
    feature_cols = [col for col in data.columns if col.startswith('share_')] + [
        'log_total_emp',
        'employment_growth_rate',
        'industry_mix_effect_per_1k',
        'regional_share_effect_per_1k'
    ]
    
    X = data[feature_cols].values
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # PCA for dimensionality reduction and visualization
    print("  Running PCA...")
    pca = PCA(n_components=min(10, len(feature_cols)))
    X_pca = pca.fit_transform(X_scaled)
    
    explained_var = pca.explained_variance_ratio_[:3].sum() * 100
    print(f"  First 3 PCs explain {explained_var:.1f}% of variance")
    
    # K-means clustering
    print("  Running K-means...")
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=20)
    clusters = kmeans.fit_predict(X_scaled)
    
    # Add cluster labels
    data = data.copy()
    data['cluster'] = clusters
    
    # Add PCA coordinates
    data['pc1'] = X_pca[:, 0]
    data['pc2'] = X_pca[:, 1]
    if X_pca.shape[1] > 2:
        data['pc3'] = X_pca[:, 2]
    
    print(f"  Clustering complete")
    print(f"  Cluster sizes:")
    for i in range(N_CLUSTERS):
        count = (clusters == i).sum()
        pct = count / len(clusters) * 100
        print(f"    Cluster {i}: {count:,} counties ({pct:.1f}%)")
    
    return data, X_scaled, scaler, pca


def characterize_clusters(data: pd.DataFrame) -> Dict[int, Dict]:
    """Calculate cluster characteristics and assign meaningful labels."""
    print("\nCharacterizing clusters...")
    
    characteristics = {}
    
    for cluster_id in range(N_CLUSTERS):
        cluster_data = data[data['cluster'] == cluster_id]
        
        # Calculate means
        char = {
            'size': len(cluster_data),
            'avg_employment': cluster_data['total_emp'].mean(),
            'median_employment': cluster_data['total_emp'].median(),
            'avg_growth_rate': cluster_data['employment_growth_rate'].mean(),
            'avg_regional_share': cluster_data['regional_share_effect_per_1k'].mean(),
            'avg_industry_mix': cluster_data['industry_mix_effect_per_1k'].mean(),
            
            # Top 3 industries by average share
            'top_industries': {}
        }
        
        # Find dominant industries
        share_cols = [col for col in data.columns if col.startswith('share_')]
        for col in share_cols:
            industry = col.replace('share_', '').replace('_', ' ').title()
            char['top_industries'][industry] = cluster_data[col].mean()
        
        # Sort and keep top 3
        char['top_industries'] = dict(
            sorted(char['top_industries'].items(), key=lambda x: x[1], reverse=True)[:3]
        )
        
        characteristics[cluster_id] = char
    
    # Assign descriptive labels based on characteristics
    labels = assign_cluster_labels(characteristics)
    
    for cluster_id, label in labels.items():
        characteristics[cluster_id]['label'] = label
        print(f"\n  Cluster {cluster_id}: {label}")
        print(f"    Size: {characteristics[cluster_id]['size']:,} counties")
        print(f"    Avg employment: {characteristics[cluster_id]['avg_employment']:,.0f}")
        print(f"    Avg growth: {characteristics[cluster_id]['avg_growth_rate']:.1f}%")
        print(f"    Regional advantage: {characteristics[cluster_id]['avg_regional_share']:.1f} per 1k")
        print(f"    Top industries: {', '.join(characteristics[cluster_id]['top_industries'].keys())}")
    
    return characteristics


def assign_cluster_labels(characteristics: Dict[int, Dict]) -> Dict[int, str]:
    """Assign meaningful labels to clusters based on characteristics."""
    labels = {}
    
    for cluster_id, char in characteristics.items():
        top_industry = list(char['top_industries'].keys())[0]
        growth = char['avg_growth_rate']
        regional = char['avg_regional_share']
        size = char['median_employment']
        
        # Decision tree for labeling
        if 'Manufacturing' in top_industry and growth < 5:
            labels[cluster_id] = "Rust Belt Manufacturing"
        elif 'Manufacturing' in top_industry and growth >= 5:
            labels[cluster_id] = "Growing Manufacturing"
        elif 'Professional Services' in top_industry or 'Information' in top_industry:
            labels[cluster_id] = "Tech & Professional Hubs"
        elif 'Healthcare' in top_industry or 'Education' in top_industry:
            labels[cluster_id] = "Education & Healthcare Centers"
        elif 'Agriculture' in top_industry:
            labels[cluster_id] = "Rural Agricultural"
        elif 'Retail' in top_industry or 'Accommodation Food' in top_industry:
            labels[cluster_id] = "Service & Retail Centers"
        elif regional > 20:
            labels[cluster_id] = "Boom Counties"
        elif regional < -20:
            labels[cluster_id] = "Declining Regions"
        else:
            labels[cluster_id] = f"Mixed Economy {cluster_id}"
    
    return labels


def generate_report(data: pd.DataFrame, characteristics: Dict[int, Dict]) -> str:
    """Generate text report."""
    print("\nGenerating report...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    report_path = OUTPUT_DIR / f"[{timestamp}]_cluster_analysis_report.txt"
    
    lines = []
    lines.append("=" * 80)
    lines.append("COUNTY CLUSTER ANALYSIS REPORT")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Period: {START_YEAR}-{END_YEAR}")
    lines.append(f"Counties analyzed: {len(data):,}")
    lines.append(f"Number of clusters: {N_CLUSTERS}")
    lines.append("")
    
    lines.append("-" * 80)
    lines.append("CLUSTER SUMMARY")
    lines.append("-" * 80)
    lines.append("")
    
    for cluster_id in range(N_CLUSTERS):
        char = characteristics[cluster_id]
        lines.append(f"Cluster {cluster_id}: {char['label']}")
        lines.append(f"  Size: {char['size']:,} counties ({char['size']/len(data)*100:.1f}%)")
        lines.append(f"  Average employment: {char['avg_employment']:,.0f}")
        lines.append(f"  Median employment: {char['median_employment']:,.0f}")
        lines.append(f"  Average growth rate: {char['avg_growth_rate']:+.1f}%")
        lines.append(f"  Regional competitive effect: {char['avg_regional_share']:+.1f} per 1,000 workers")
        lines.append(f"  Industry mix effect: {char['avg_industry_mix']:+.1f} per 1,000 workers")
        lines.append(f"  Top 3 industries:")
        for industry, share in char['top_industries'].items():
            lines.append(f"    - {industry}: {share*100:.1f}%")
        lines.append("")
    
    lines.append("-" * 80)
    lines.append("DETAILED CLUSTER PROFILES")
    lines.append("-" * 80)
    lines.append("")
    
    for cluster_id in range(N_CLUSTERS):
        char = characteristics[cluster_id]
        cluster_data = data[data['cluster'] == cluster_id]
        
        lines.append(f"\n{'=' * 80}")
        lines.append(f"CLUSTER {cluster_id}: {char['label'].upper()}")
        lines.append(f"{'=' * 80}")
        lines.append("")
        
        lines.append(f"Size: {char['size']:,} counties")
        lines.append(f"Growth: {char['avg_growth_rate']:+.1f}% (2017-2022)")
        lines.append(f"Regional advantage: {char['avg_regional_share']:+.1f} per 1,000 workers")
        lines.append("")
        
        lines.append("Employment Statistics:")
        lines.append(f"  Average: {char['avg_employment']:,.0f}")
        lines.append(f"  Median: {char['median_employment']:,.0f}")
        lines.append(f"  Min: {cluster_data['total_emp'].min():,.0f}")
        lines.append(f"  Max: {cluster_data['total_emp'].max():,.0f}")
        lines.append("")
        
        lines.append("Industry Composition (average shares):")
        for industry, share in sorted(char['top_industries'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {industry:.<40} {share*100:>6.1f}%")
        lines.append("")
        
        # Top 10 counties by employment
        top_counties = cluster_data.nlargest(10, 'total_emp')
        lines.append("Top 10 Counties by Employment:")
        lines.append(f"  {'Rank':<6} {'State':<8} {'County':<8} {'Employment':>12} {'Growth':>10}")
        lines.append("  " + "-" * 70)
        for i, (_, row) in enumerate(top_counties.iterrows(), 1):
            lines.append(f"  {i:<6} {int(row['state']):<8} {int(row['county']):<8} "
                        f"{int(row['total_emp']):>12,} {row['employment_growth_rate']:>9.1f}%")
        lines.append("")
        
        # Top 10 by growth rate (min 1000 employment)
        large_counties = cluster_data[cluster_data['total_emp'] >= 1000]
        if len(large_counties) > 0:
            top_growth = large_counties.nlargest(10, 'employment_growth_rate')
            lines.append("Top 10 Counties by Growth Rate (min 1,000 employment):")
            lines.append(f"  {'Rank':<6} {'State':<8} {'County':<8} {'Growth':>10} {'Employment':>12}")
            lines.append("  " + "-" * 70)
            for i, (_, row) in enumerate(top_growth.iterrows(), 1):
                lines.append(f"  {i:<6} {int(row['state']):<8} {int(row['county']):<8} "
                            f"{row['employment_growth_rate']:>9.1f}% {int(row['total_emp']):>12,}")
        lines.append("")
    
    # Write report
    with open(report_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"  Report saved: {report_path}")
    return report_path


def save_results(data: pd.DataFrame, characteristics: Dict[int, Dict]):
    """Save clustering results to JSON."""
    print("\nSaving results...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    # Save full data CSV
    csv_path = OUTPUT_DIR / f"[{timestamp}]_cluster_assignments.csv"
    data.to_csv(csv_path, index=False)
    print(f"  CSV saved: {csv_path}")
    
    # Save JSON summary
    json_path = OUTPUT_DIR / f"[{timestamp}]_cluster_results.json"
    
    results = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'period': f"{START_YEAR}-{END_YEAR}",
            'n_counties': len(data),
            'n_clusters': N_CLUSTERS
        },
        'cluster_characteristics': characteristics,
        'county_assignments': {}
    }
    
    for _, row in data.iterrows():
        county_key = f"{int(row['state'])}_{int(row['county'])}"
        results['county_assignments'][county_key] = {
            'cluster': int(row['cluster']),
            'cluster_label': characteristics[int(row['cluster'])]['label'],
            'total_employment': int(row['total_emp']),
            'growth_rate': float(row['employment_growth_rate']),
            'regional_share_effect': float(row['regional_share_effect']),
            'pc1': float(row['pc1']),
            'pc2': float(row['pc2'])
        }
    
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"  JSON saved: {json_path}")


def main():
    """Main execution function."""
    print("=" * 80)
    print("COUNTY CLUSTER ANALYSIS")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Load data
    cbp_df = load_cbp_data()
    shift_share_df = load_shift_share_results()
    
    # Calculate features
    composition = calculate_industry_composition(cbp_df)
    growth = calculate_growth_rates(cbp_df)
    
    # Prepare clustering dataset
    data = prepare_clustering_data(composition, growth, shift_share_df)
    
    # Perform clustering
    clustered_data, X_scaled, scaler, pca = perform_clustering(data)
    
    # Characterize clusters
    characteristics = characterize_clusters(clustered_data)
    
    # Generate outputs
    report_path = generate_report(clustered_data, characteristics)
    save_results(clustered_data, characteristics)
    
    print("")
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    print("Outputs:")
    print(f"  Report: {report_path}")
    print(f"  CSV: {OUTPUT_DIR / '[timestamp]_cluster_assignments.csv'}")
    print(f"  JSON: {OUTPUT_DIR / '[timestamp]_cluster_results.json'}")


if __name__ == "__main__":
    main()
