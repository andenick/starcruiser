"""
Leading County Identification (Annual Growth Patterns)
======================================================

Identifies counties that consistently lead or lag national employment trends.

Since CBP data is annual (not monthly/quarterly), we analyze:
1. Growth Rate Leadership: Which counties grow faster than national average?
2. Volatility Leadership: Which counties have early/exaggerated cycles?
3. Industry Mix Leadership: Which counties have high-growth industry portfolios?

Alternative to Granger Causality (requires high-frequency data):
- Annual growth correlation at different lags
- Employment growth momentum (2-year rolling)
- Industry composition effects

Author: StarCruiser Project
Created: December 5, 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Project paths
BASE_DIR = PROJECT_ROOT
CBP_DIR = BASE_DIR / "Inputs" / "source" / "CENSUS_CBP"
CATALOGS_DIR = BASE_DIR / "Outputs" / "CATALOGS"
OUTPUTS_DIR = BASE_DIR / "Outputs" / "LEADING_COUNTIES"
VALIDATION_DIR = BASE_DIR / "Outputs" / "VALIDATION"

# Create directories
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


class LeadingCountyAnalyzer:
    """Identify leading/lagging counties from annual employment data."""
    
    def __init__(self):
        """Initialize analyzer."""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        self.county_data = None
        self.national_data = None
        self.growth_rates = None
        self.leading_counties = []
        
    def load_cbp_data(self, years=None):
        """Load CBP data for multiple years."""
        if years is None:
            years = [2017, 2018, 2019, 2020, 2021, 2022]
        
        print(f"\n[LOADING] CBP data for {len(years)} years...")
        
        dfs = []
        for year in years:
            cbp_file = CBP_DIR / f"cbp_{year}.csv"
            if cbp_file.exists():
                df = pd.read_csv(cbp_file)
                df['YEAR'] = year
                dfs.append(df)
                print(f"  {year}: {len(df):,} records")
            else:
                print(f"  [WARN] {year}: File not found")
        
        combined = pd.concat(dfs, ignore_index=True)
        print(f"\n  Total records: {len(combined):,}")
        
        return combined
    
    def calculate_county_totals(self, df):
        """Calculate total employment by county-year."""
        print(f"\n{'='*60}")
        print("CALCULATING COUNTY EMPLOYMENT TOTALS")
        print("=" * 60)
        
        # Sum employment across all industries for each county-year
        county_totals = df.groupby(['state', 'county', 'YEAR'])['EMP'].sum().reset_index()
        county_totals['county_code'] = county_totals['state'].astype(str).str.zfill(2) + \
                                        county_totals['county'].astype(str).str.zfill(3)
        
        print(f"  County-year combinations: {len(county_totals):,}")
        print(f"  Unique counties: {county_totals['county_code'].nunique()}")
        print(f"  Years: {sorted(county_totals['YEAR'].unique())}")
        
        return county_totals
    
    def calculate_national_totals(self, df):
        """Calculate national employment by year."""
        print(f"\n{'='*60}")
        print("CALCULATING NATIONAL EMPLOYMENT TOTALS")
        print("=" * 60)
        
        # Sum employment across all counties for each year
        national_totals = df.groupby('YEAR')['EMP'].sum().reset_index()
        national_totals.columns = ['YEAR', 'NATIONAL_EMP']
        
        print(f"  National employment by year:")
        for idx, row in national_totals.iterrows():
            print(f"    {row['YEAR']}: {row['NATIONAL_EMP']:,.0f}")
        
        return national_totals
    
    def calculate_growth_rates(self, county_totals, national_totals):
        """Calculate year-over-year growth rates for counties and nation."""
        print(f"\n{'='*60}")
        print("CALCULATING GROWTH RATES")
        print("=" * 60)
        
        # National growth rates
        national_totals = national_totals.sort_values('YEAR')
        national_totals['NATIONAL_GROWTH'] = national_totals['NATIONAL_EMP'].pct_change() * 100
        
        print(f"\n  National growth rates:")
        for idx, row in national_totals.iterrows():
            if pd.notna(row['NATIONAL_GROWTH']):
                print(f"    {int(row['YEAR'])}: {row['NATIONAL_GROWTH']:+.2f}%")
        
        # County growth rates
        county_totals = county_totals.sort_values(['county_code', 'YEAR'])
        county_totals['COUNTY_GROWTH'] = county_totals.groupby('county_code')['EMP'].pct_change() * 100
        
        # Merge national growth for comparison
        county_totals = county_totals.merge(
            national_totals[['YEAR', 'NATIONAL_GROWTH']], 
            on='YEAR', 
            how='left'
        )
        
        # Calculate relative growth (county vs national)
        county_totals['RELATIVE_GROWTH'] = county_totals['COUNTY_GROWTH'] - county_totals['NATIONAL_GROWTH']
        
        print(f"\n  County growth rates calculated: {county_totals['COUNTY_GROWTH'].notna().sum():,} observations")
        
        return county_totals, national_totals
    
    def identify_growth_leaders(self, county_totals, top_n=50):
        """Identify counties with consistently above-average growth."""
        print(f"\n{'='*60}")
        print("IDENTIFYING GROWTH LEADERS")
        print("=" * 60)
        
        # Calculate average relative growth for each county (2018-2022)
        growth_summary = county_totals[county_totals['YEAR'] >= 2018].groupby('county_code').agg({
            'RELATIVE_GROWTH': ['mean', 'std', 'count'],
            'EMP': 'mean',
            'state': 'first',
            'county': 'first'
        }).reset_index()
        
        growth_summary.columns = ['county_code', 'avg_relative_growth', 'std_growth', 
                                  'n_years', 'avg_employment', 'state', 'county']
        
        # Filter: Need at least 4 years of data
        growth_summary = growth_summary[growth_summary['n_years'] >= 4]
        
        # Calculate consistency score (high growth, low volatility)
        growth_summary['consistency_score'] = growth_summary['avg_relative_growth'] / (growth_summary['std_growth'] + 0.1)
        
        # Rank by average relative growth
        growth_summary = growth_summary.sort_values('avg_relative_growth', ascending=False)
        
        print(f"\n  Top {top_n} Growth Leaders (2018-2022):")
        print(f"  {'Rank':<5} {'State':<6} {'County':<8} {'Avg Growth':<12} {'Consistency':<12} {'Avg Emp':<15}")
        print("  " + "-" * 70)
        
        for idx, row in growth_summary.head(top_n).iterrows():
            print(f"  {idx+1:<5} {int(row['state']):<6} {int(row['county']):<8} "
                  f"{row['avg_relative_growth']:+.2f}%{'':<6} "
                  f"{row['consistency_score']:+.2f}{'':<6} "
                  f"{row['avg_employment']:,.0f}")
        
        return growth_summary
    
    def identify_volatility_leaders(self, county_totals, top_n=50):
        """Identify counties with high volatility (early cycle indicators)."""
        print(f"\n{'='*60}")
        print("IDENTIFYING VOLATILITY LEADERS")
        print("=" * 60)
        
        # Calculate growth volatility (std dev of growth rates)
        volatility_summary = county_totals[county_totals['YEAR'] >= 2018].groupby('county_code').agg({
            'COUNTY_GROWTH': 'std',
            'EMP': 'mean',
            'state': 'first',
            'county': 'first'
        }).reset_index()
        
        volatility_summary.columns = ['county_code', 'growth_volatility', 
                                      'avg_employment', 'state', 'county']
        
        # Higher volatility = more cyclical = potentially leading
        volatility_summary = volatility_summary.sort_values('growth_volatility', ascending=False)
        
        print(f"\n  Top {top_n} Most Volatile Counties (2018-2022):")
        print(f"  {'Rank':<5} {'State':<6} {'County':<8} {'Volatility':<12} {'Avg Emp':<15}")
        print("  " + "-" * 60)
        
        for idx, row in volatility_summary.head(top_n).iterrows():
            print(f"  {idx+1:<5} {int(row['state']):<6} {int(row['county']):<8} "
                  f"{row['growth_volatility']:.2f}%{'':<6} "
                  f"{row['avg_employment']:,.0f}")
        
        return volatility_summary
    
    def analyze_industry_composition(self, df):
        """Identify counties with high-growth industry mix."""
        print(f"\n{'='*60}")
        print("ANALYZING INDUSTRY COMPOSITION")
        print("=" * 60)
        
        # Focus on 2022 data, 2-digit sectors
        sector_data = df[(df['YEAR'] == 2022) & (df['NAICS2017'].astype(str).str.len() == 2)].copy()
        
        # Calculate each county's industry mix (employment shares by sector)
        county_industry = sector_data.groupby(['state', 'county', 'NAICS2017'])['EMP'].sum().reset_index()
        county_industry['county_code'] = county_industry['state'].astype(str).str.zfill(2) + \
                                         county_industry['county'].astype(str).str.zfill(3)
        
        # Calculate total employment per county
        county_totals = county_industry.groupby('county_code')['EMP'].sum().reset_index()
        county_totals.columns = ['county_code', 'total_emp']
        
        # Merge and calculate shares
        county_industry = county_industry.merge(county_totals, on='county_code', how='left')
        county_industry['emp_share'] = county_industry['EMP'] / county_industry['total_emp']
        
        # High-growth sectors (Information 51, Professional Services 54, Finance 52)
        high_growth_sectors = ['51', '54', '52']
        
        # Calculate high-growth industry share for each county
        county_hg_share = county_industry[
            county_industry['NAICS2017'].astype(str).isin(high_growth_sectors)
        ].groupby('county_code')['emp_share'].sum().reset_index()
        county_hg_share.columns = ['county_code', 'high_growth_share']
        
        # Add county info
        county_info = county_industry[['county_code', 'state', 'county', 'total_emp']].drop_duplicates()
        county_hg_share = county_hg_share.merge(county_info, on='county_code', how='left')
        
        # Rank by high-growth industry concentration
        county_hg_share = county_hg_share.sort_values('high_growth_share', ascending=False)
        
        print(f"\n  Top 50 Counties by High-Growth Industry Concentration (2022):")
        print(f"  {'Rank':<5} {'State':<6} {'County':<8} {'Tech/Prof/Fin %':<16} {'Total Emp':<15}")
        print("  " + "-" * 65)
        
        for idx, row in county_hg_share.head(50).iterrows():
            print(f"  {idx+1:<5} {int(row['state']):<6} {int(row['county']):<8} "
                  f"{row['high_growth_share']*100:.2f}%{'':<11} "
                  f"{row['total_emp']:,.0f}")
        
        return county_hg_share
    
    def load_geographic_hierarchy(self):
        """Load geographic hierarchy for county name lookups."""
        # Find most recent geographic hierarchy JSON
        geo_files = list(CATALOGS_DIR.glob("*geographic_hierarchy.json"))
        if not geo_files:
            print(f"  [WARN] No geographic hierarchy found")
            return None
        
        latest_geo = sorted(geo_files)[-1]
        with open(latest_geo, 'r') as f:
            geo_data = json.load(f)
        
        return geo_data.get('county_lookup', {})
    
    def generate_leading_counties_report(self, growth_leaders, volatility_leaders, industry_leaders):
        """Generate comprehensive leading counties report."""
        report_path = OUTPUTS_DIR / f"[{self.timestamp}]_leading_counties_report.txt"
        
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("LEADING COUNTIES ANALYSIS REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("NOTE: This analysis uses annual CBP data (2017-2022).\n")
            f.write("True 'leading indicator' analysis requires monthly/quarterly data.\n")
            f.write("This report identifies counties with strong growth momentum instead.\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("GROWTH LEADERS (Top 50)\n")
            f.write("-" * 80 + "\n\n")
            f.write("Counties with consistently above-average employment growth (2018-2022)\n\n")
            f.write("Rank | State | County | Avg Relative Growth | Consistency | Avg Employment\n")
            f.write("-" * 80 + "\n")
            
            for idx, row in growth_leaders.head(50).iterrows():
                f.write(f"{idx+1:4} | {int(row['state']):5} | {int(row['county']):6} | "
                       f"{row['avg_relative_growth']:+7.2f}% | {row['consistency_score']:+7.2f} | "
                       f"{row['avg_employment']:12,.0f}\n")
            
            f.write("\n")
            f.write("-" * 80 + "\n")
            f.write("VOLATILITY LEADERS (Top 50)\n")
            f.write("-" * 80 + "\n\n")
            f.write("Counties with highest employment growth volatility (early cycle indicators)\n\n")
            f.write("Rank | State | County | Growth Volatility | Avg Employment\n")
            f.write("-" * 80 + "\n")
            
            for idx, row in volatility_leaders.head(50).iterrows():
                f.write(f"{idx+1:4} | {int(row['state']):5} | {int(row['county']):6} | "
                       f"{row['growth_volatility']:7.2f}% | {row['avg_employment']:12,.0f}\n")
            
            f.write("\n")
            f.write("-" * 80 + "\n")
            f.write("HIGH-GROWTH INDUSTRY CONCENTRATION (Top 50)\n")
            f.write("-" * 80 + "\n\n")
            f.write("Counties with highest concentration in Information (51),\n")
            f.write("Professional Services (54), and Finance (52) sectors (2022)\n\n")
            f.write("Rank | State | County | Tech/Prof/Fin Share | Total Employment\n")
            f.write("-" * 80 + "\n")
            
            for idx, row in industry_leaders.head(50).iterrows():
                f.write(f"{idx+1:4} | {int(row['state']):5} | {int(row['county']):6} | "
                       f"{row['high_growth_share']*100:7.2f}% | {row['total_emp']:12,.0f}\n")
            
            f.write("\n")
            f.write("-" * 80 + "\n")
            f.write("INTERPRETATION\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("Growth Leaders:\n")
            f.write("  Counties that consistently outperform national growth rates.\n")
            f.write("  Positive values = faster than national average.\n")
            f.write("  Higher consistency score = stable outperformance.\n\n")
            
            f.write("Volatility Leaders:\n")
            f.write("  Counties with high employment growth volatility.\n")
            f.write("  Often early-cycle indicators (amplify national trends).\n")
            f.write("  High volatility can signal leading OR lagging behavior.\n\n")
            
            f.write("Industry Concentration:\n")
            f.write("  Counties with high concentration in fast-growing sectors.\n")
            f.write("  Information, Professional Services, Finance drive growth.\n")
            f.write("  High concentration suggests potential for continued leadership.\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("LIMITATIONS\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("1. Annual data cannot identify true leading/lagging relationships\n")
            f.write("   (need monthly/quarterly for Granger causality tests).\n\n")
            
            f.write("2. 'Leading' here means 'faster growing', not 'predicts future'.\n\n")
            
            f.write("3. For true leading indicator analysis, use QCEW quarterly data\n")
            f.write("   or BLS State and Metro Area Employment (monthly).\n\n")
        
        print(f"\n[SAVED] Leading counties report: {report_path.name}")
        return report_path
    
    def save_results_json(self, growth_leaders, volatility_leaders, industry_leaders):
        """Save results as JSON."""
        json_path = OUTPUTS_DIR / f"[{self.timestamp}]_leading_counties.json"
        
        output = {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'description': 'Leading counties analysis (annual growth patterns)',
                'years': [2017, 2018, 2019, 2020, 2021, 2022],
                'source': 'Census County Business Patterns',
                'limitation': 'Annual data - cannot perform true leading indicator analysis'
            },
            'growth_leaders_top50': growth_leaders.head(50).to_dict('records'),
            'volatility_leaders_top50': volatility_leaders.head(50).to_dict('records'),
            'industry_leaders_top50': industry_leaders.head(50).to_dict('records')
        }
        
        # Custom encoder for numpy types
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (np.integer, np.int64, np.int32)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super().default(obj)
        
        with open(json_path, 'w') as f:
            json.dump(output, f, indent=2, cls=NumpyEncoder)
        
        print(f"[SAVED] Results JSON: {json_path.name}")
        return json_path
    
    def run_all(self):
        """Run complete leading counties analysis."""
        print("\n" + "=" * 80)
        print("LEADING COUNTIES ANALYZER (ANNUAL GROWTH PATTERNS)")
        print("=" * 80)
        print("\nNOTE: CBP data is annual. True 'leading indicator' analysis")
        print("requires monthly/quarterly data (use QCEW or BLS SAMES).")
        print("This analysis identifies counties with strong growth momentum.\n")
        
        # Load data
        df = self.load_cbp_data(years=[2017, 2018, 2019, 2020, 2021, 2022])
        
        # Calculate totals
        county_totals = self.calculate_county_totals(df)
        national_totals = self.calculate_national_totals(county_totals)
        
        # Calculate growth rates
        county_totals, national_totals = self.calculate_growth_rates(county_totals, national_totals)
        
        # Identify leaders
        growth_leaders = self.identify_growth_leaders(county_totals, top_n=50)
        volatility_leaders = self.identify_volatility_leaders(county_totals, top_n=50)
        industry_leaders = self.analyze_industry_composition(df)
        
        # Generate outputs
        report_path = self.generate_leading_counties_report(
            growth_leaders, volatility_leaders, industry_leaders
        )
        json_path = self.save_results_json(growth_leaders, volatility_leaders, industry_leaders)
        
        # Summary
        print("\n" + "=" * 80)
        print("LEADING COUNTIES ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"Counties analyzed: {county_totals['county_code'].nunique()}")
        print(f"Years: 2017-2022 (6 years)")
        print(f"\nOutput files:")
        print(f"  Report: {report_path.name}")
        print(f"  JSON: {json_path.name}")
        print("\n[SUCCESS] Leading counties identified (growth momentum analysis)!")


def main():
    """Main execution function."""
    analyzer = LeadingCountyAnalyzer()
    analyzer.run_all()


if __name__ == "__main__":
    main()
