"""
Geographic Dispersion Metrics Calculator
=========================================

Calculates geographic concentration/dispersion metrics for county-level employment data.

Metrics:
1. Gini Coefficient - Employment concentration across counties (0 = equality, 1 = inequality)
2. Herfindahl-Hirschman Index (HHI) - Market concentration (0-10,000)
3. Coefficient of Variation (CV) - Dispersion measure (std dev / mean)
4. Top 10% Share - What % of employment is in top 10% counties?

Analysis:
- Time series (2017-2022) - Is employment concentrating over time?
- By industry (NAICS sectors) - Which industries are most concentrated?
- COVID-19 impact - Did 2020-2021 change geographic patterns?

Author: StarCruiser Project
Created: December 5, 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]



class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types."""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# Project paths
BASE_DIR = PROJECT_ROOT
CBP_DIR = BASE_DIR / "Inputs" / "source" / "CENSUS_CBP"
CATALOGS_DIR = BASE_DIR / "Outputs" / "CATALOGS"
OUTPUTS_DIR = BASE_DIR / "Outputs" / "DISPERSION"
VALIDATION_DIR = BASE_DIR / "Outputs" / "VALIDATION"

# Create directories
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


class GeographicDispersionCalculator:
    """Calculate geographic dispersion metrics for employment data."""
    
    def __init__(self):
        """Initialize calculator."""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        self.metrics = {}
        self.time_series = {}
        self.industry_metrics = {}
        
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
    
    def calculate_gini_coefficient(self, employment_shares):
        """
        Calculate Gini coefficient for employment concentration.
        
        Gini = 0: Perfect equality (all counties have same employment)
        Gini = 1: Perfect inequality (one county has all employment)
        """
        # Sort shares in ascending order
        sorted_shares = np.sort(employment_shares)
        n = len(sorted_shares)
        
        # Calculate cumulative shares
        cumsum = np.cumsum(sorted_shares)
        
        # Gini coefficient formula
        gini = (2 * np.sum((np.arange(1, n+1) * sorted_shares))) / (n * np.sum(sorted_shares)) - (n + 1) / n
        
        return gini
    
    def calculate_hhi(self, employment_shares):
        """
        Calculate Herfindahl-Hirschman Index (HHI).
        
        HHI = Sum of squared market shares (in percentage points)
        
        HHI < 1,000: Low concentration (competitive)
        1,000 < HHI < 2,500: Moderate concentration
        HHI > 2,500: High concentration
        """
        # Convert shares to percentages
        shares_pct = employment_shares * 100
        
        # HHI = sum of squared shares
        hhi = np.sum(shares_pct ** 2)
        
        return hhi
    
    def calculate_cv(self, employment_values):
        """
        Calculate Coefficient of Variation (CV).
        
        CV = standard deviation / mean
        Higher CV = more dispersed
        """
        mean_emp = np.mean(employment_values)
        std_emp = np.std(employment_values)
        
        cv = std_emp / mean_emp if mean_emp > 0 else 0
        
        return cv
    
    def calculate_top_share(self, employment_values, top_pct=0.10):
        """
        Calculate share of employment in top X% of counties.
        
        Example: top_pct=0.10 calculates share in top 10% of counties
        """
        sorted_emp = np.sort(employment_values)[::-1]  # Descending order
        
        n_top = int(len(sorted_emp) * top_pct)
        if n_top == 0:
            n_top = 1
        
        top_emp = np.sum(sorted_emp[:n_top])
        total_emp = np.sum(sorted_emp)
        
        share = top_emp / total_emp if total_emp > 0 else 0
        
        return share, n_top
    
    def calculate_national_metrics(self, df, year):
        """Calculate dispersion metrics for national employment (all industries)."""
        print(f"\n{'='*60}")
        print(f"NATIONAL DISPERSION METRICS - {year}")
        print("=" * 60)
        
        # Get county-level employment totals (sum across all industries)
        county_totals = df[df['YEAR'] == year].groupby(['state', 'county'])['EMP'].sum().reset_index()
        
        employment = county_totals['EMP'].values
        total_emp = employment.sum()
        
        # Remove zero/NaN values
        employment = employment[employment > 0]
        
        # Calculate shares
        shares = employment / total_emp
        
        # Calculate metrics
        gini = self.calculate_gini_coefficient(shares)
        hhi = self.calculate_hhi(shares)
        cv = self.calculate_cv(employment)
        top10_share, n_top = self.calculate_top_share(employment, top_pct=0.10)
        
        print(f"  Total employment: {total_emp:,.0f}")
        print(f"  Counties: {len(employment)}")
        print(f"\n  Gini Coefficient: {gini:.4f}")
        print(f"  HHI: {hhi:.2f}")
        print(f"  Coefficient of Variation: {cv:.4f}")
        print(f"  Top 10% share ({n_top} counties): {top10_share*100:.2f}%")
        
        return {
            'year': year,
            'total_employment': int(total_emp),
            'counties': len(employment),
            'gini': gini,
            'hhi': hhi,
            'cv': cv,
            'top10_share': top10_share,
            'top10_counties': n_top
        }
    
    def calculate_industry_metrics(self, df, year):
        """Calculate dispersion metrics by NAICS sector."""
        print(f"\n{'='*60}")
        print(f"INDUSTRY DISPERSION METRICS - {year}")
        print("=" * 60)
        
        # Get 2-digit sector data
        sector_data = df[(df['YEAR'] == year) & (df['NAICS2017'].astype(str).str.len() == 2)].copy()
        
        industry_results = []
        
        for sector in sorted(sector_data['NAICS2017'].unique()):
            sector_df = sector_data[sector_data['NAICS2017'] == sector]
            
            # Get county-level employment for this sector
            county_emp = sector_df.groupby(['state', 'county'])['EMP'].sum().values
            
            # Remove zero/NaN values
            county_emp = county_emp[county_emp > 0]
            
            if len(county_emp) < 2:
                continue  # Need at least 2 counties for meaningful metrics
            
            total_emp = county_emp.sum()
            shares = county_emp / total_emp
            
            gini = self.calculate_gini_coefficient(shares)
            hhi = self.calculate_hhi(shares)
            cv = self.calculate_cv(county_emp)
            
            industry_results.append({
                'sector': str(sector),
                'employment': int(total_emp),
                'counties': len(county_emp),
                'gini': gini,
                'hhi': hhi,
                'cv': cv
            })
        
        # Sort by Gini (most concentrated first)
        industry_results = sorted(industry_results, key=lambda x: x['gini'], reverse=True)
        
        print(f"\n  Top 5 Most Concentrated Industries (by Gini):")
        for i, ind in enumerate(industry_results[:5], 1):
            print(f"    {i}. Sector {ind['sector']}: Gini={ind['gini']:.4f}, HHI={ind['hhi']:.2f}")
        
        print(f"\n  Top 5 Least Concentrated Industries (by Gini):")
        for i, ind in enumerate(industry_results[-5:], 1):
            print(f"    {i}. Sector {ind['sector']}: Gini={ind['gini']:.4f}, HHI={ind['hhi']:.2f}")
        
        return industry_results
    
    def analyze_time_trends(self, df):
        """Analyze dispersion trends over time (2017-2022)."""
        print(f"\n{'='*60}")
        print("TIME SERIES ANALYSIS")
        print("=" * 60)
        
        years = sorted(df['YEAR'].unique())
        time_series = []
        
        for year in years:
            metrics = self.calculate_national_metrics(df, year)
            time_series.append(metrics)
        
        # Calculate changes
        if len(time_series) >= 2:
            first = time_series[0]
            last = time_series[-1]
            
            gini_change = last['gini'] - first['gini']
            hhi_change = last['hhi'] - first['hhi']
            
            print(f"\n{'='*60}")
            print(f"TRENDS ({first['year']} -> {last['year']})")
            print("=" * 60)
            print(f"  Gini change: {gini_change:+.4f} ({gini_change/first['gini']*100:+.2f}%)")
            print(f"  HHI change: {hhi_change:+.2f} ({hhi_change/first['hhi']*100:+.2f}%)")
            
            if gini_change > 0.01:
                print(f"  [TREND] Employment becoming MORE concentrated")
            elif gini_change < -0.01:
                print(f"  [TREND] Employment becoming LESS concentrated")
            else:
                print(f"  [TREND] Employment concentration relatively stable")
        
        return time_series
    
    def generate_dispersion_report(self, national_metrics, industry_metrics, time_series):
        """Generate comprehensive dispersion report."""
        report_path = OUTPUTS_DIR / f"[{self.timestamp}]_geographic_dispersion_report.txt"
        
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("GEOGRAPHIC DISPERSION METRICS REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("TIME SERIES SUMMARY\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("Year | Gini | HHI | CV | Top10% | Counties\n")
            f.write("-" * 80 + "\n")
            for ts in time_series:
                f.write(f"{ts['year']} | {ts['gini']:.4f} | {ts['hhi']:.2f} | "
                       f"{ts['cv']:.4f} | {ts['top10_share']*100:.2f}% | {ts['counties']}\n")
            
            f.write("\n")
            f.write("-" * 80 + "\n")
            f.write("INDUSTRY CONCENTRATION (Latest Year)\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("Sector | Gini | HHI | CV | Employment | Counties\n")
            f.write("-" * 80 + "\n")
            for ind in industry_metrics:
                f.write(f"{ind['sector']:6} | {ind['gini']:.4f} | {ind['hhi']:7.2f} | "
                       f"{ind['cv']:.4f} | {ind['employment']:12,} | {ind['counties']}\n")
            
            f.write("\n")
            f.write("-" * 80 + "\n")
            f.write("INTERPRETATION\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("Gini Coefficient:\n")
            f.write("  0.0 - 0.3: Low concentration (employment evenly distributed)\n")
            f.write("  0.3 - 0.5: Moderate concentration\n")
            f.write("  0.5 - 0.7: High concentration\n")
            f.write("  0.7 - 1.0: Very high concentration (employment in few counties)\n\n")
            
            f.write("HHI (Herfindahl-Hirschman Index):\n")
            f.write("  < 1,000: Low concentration (competitive market)\n")
            f.write("  1,000 - 2,500: Moderate concentration\n")
            f.write("  > 2,500: High concentration (potential monopoly/oligopoly)\n\n")
            
            f.write("Coefficient of Variation (CV):\n")
            f.write("  Lower CV: Employment more evenly distributed across counties\n")
            f.write("  Higher CV: Employment more variable (some large, some small)\n\n")
        
        print(f"\n[SAVED] Dispersion report: {report_path.name}")
        return report_path
    
    def save_metrics_json(self, national_metrics, industry_metrics, time_series):
        """Save metrics as JSON for downstream analysis."""
        json_path = OUTPUTS_DIR / f"[{self.timestamp}]_dispersion_metrics.json"
        
        output = {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'description': 'Geographic dispersion metrics for county-level employment',
                'years': [ts['year'] for ts in time_series],
                'source': 'Census County Business Patterns'
            },
            'time_series': time_series,
            'industry_metrics': industry_metrics,
            'national_metrics_latest': national_metrics
        }
        
        with open(json_path, 'w') as f:
            json.dump(output, f, indent=2, cls=NumpyEncoder)
        
        print(f"[SAVED] Metrics JSON: {json_path.name}")
        return json_path
    
    def run_all(self):
        """Run complete dispersion analysis."""
        print("\n" + "=" * 80)
        print("GEOGRAPHIC DISPERSION METRICS CALCULATOR")
        print("=" * 80)
        
        # Load data
        df = self.load_cbp_data(years=[2017, 2018, 2019, 2020, 2021, 2022])
        
        # Time series analysis
        time_series = self.analyze_time_trends(df)
        
        # Latest year national metrics
        latest_year = df['YEAR'].max()
        national_metrics = self.calculate_national_metrics(df, latest_year)
        
        # Industry metrics (latest year)
        industry_metrics = self.calculate_industry_metrics(df, latest_year)
        
        # Generate outputs
        report_path = self.generate_dispersion_report(national_metrics, industry_metrics, time_series)
        json_path = self.save_metrics_json(national_metrics, industry_metrics, time_series)
        
        # Summary
        print("\n" + "=" * 80)
        print("DISPERSION ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"Years analyzed: {len(time_series)}")
        print(f"Industries analyzed: {len(industry_metrics)}")
        print(f"\nOutput files:")
        print(f"  Report: {report_path.name}")
        print(f"  Metrics JSON: {json_path.name}")
        print("\n[SUCCESS] Geographic dispersion metrics calculated!")


def main():
    """Main execution function."""
    calculator = GeographicDispersionCalculator()
    calculator.run_all()


if __name__ == "__main__":
    main()
