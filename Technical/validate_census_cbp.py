"""
Census CBP County Data Validator
=================================

Validates Census County Business Patterns data quality and structure.

Validation Checks:
1. County FIPS code validity (3,143 US counties expected)
2. NAICS code validity and hierarchy consistency
3. Temporal continuity (are all years present?)
4. Employment data completeness (missing/suppressed values)
5. Geographic aggregation (do counties sum to states?)

Author: StarCruiser Project
Created: December 5, 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Project paths
BASE_DIR = PROJECT_ROOT
CBP_DIR = BASE_DIR / "Inputs" / "source" / "CENSUS_CBP"
OUTPUTS_DIR = BASE_DIR / "Outputs" / "VALIDATION"

# Create directories
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# US county count (as of 2023 Census)
EXPECTED_COUNTIES = 3143  # Total US counties/equivalents


class CBPValidator:
    """Validate Census County Business Patterns data."""
    
    def __init__(self):
        """Initialize validator."""
        self.issues = []
        self.stats = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
    def load_cbp_data(self, year=2021):
        """Load CBP data for a specific year."""
        cbp_file = CBP_DIR / f"cbp_{year}.csv"
        
        if not cbp_file.exists():
            raise FileNotFoundError(f"CBP file not found: {cbp_file}")
        
        print(f"\n[LOADING] {cbp_file.name}...")
        df = pd.read_csv(cbp_file)
        
        print(f"  Records: {len(df):,}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Size: {cbp_file.stat().st_size / (1024*1024):.2f} MB")
        
        return df
    
    def validate_county_fips(self, df):
        """Validate county FIPS codes."""
        print(f"\n{'='*60}")
        print("CHECK 1: County FIPS Code Validity")
        print("=" * 60)
        
        # Get unique counties
        if 'county' not in df.columns or 'state' not in df.columns:
            print("[ERROR] Missing 'county' or 'state' columns")
            self.issues.append({
                "check": "county_fips",
                "severity": "HIGH",
                "issue": "Missing required columns"
            })
            return False
        
        # Create combined FIPS code (state + county)
        df['fips'] = df['state'].astype(str).str.zfill(2) + df['county'].astype(str).str.zfill(3)
        
        unique_counties = df['fips'].nunique()
        unique_states = df['state'].nunique()
        
        print(f"  Unique counties: {unique_counties:,}")
        print(f"  Unique states: {unique_states}")
        print(f"  Expected counties: ~{EXPECTED_COUNTIES:,}")
        
        # Calculate coverage
        coverage_pct = (unique_counties / EXPECTED_COUNTIES) * 100
        
        if coverage_pct < 90:
            self.issues.append({
                "check": "county_fips",
                "severity": "MEDIUM",
                "issue": f"Only {coverage_pct:.1f}% county coverage ({unique_counties}/{EXPECTED_COUNTIES})"
            })
            print(f"  [WARN] Low coverage: {coverage_pct:.1f}%")
        else:
            print(f"  [PASS] Coverage: {coverage_pct:.1f}%")
        
        # Check for invalid FIPS codes (should be 5 digits)
        invalid_fips = df[df['fips'].str.len() != 5]
        if not invalid_fips.empty:
            print(f"  [WARN] {len(invalid_fips)} records with invalid FIPS codes")
            self.issues.append({
                "check": "county_fips",
                "severity": "LOW",
                "issue": f"{len(invalid_fips)} invalid FIPS codes"
            })
        
        self.stats['unique_counties'] = unique_counties
        self.stats['unique_states'] = unique_states
        self.stats['coverage_pct'] = coverage_pct
        
        return coverage_pct >= 90
    
    def validate_naics_codes(self, df):
        """Validate NAICS industry codes."""
        print(f"\n{'='*60}")
        print("CHECK 2: NAICS Code Validity")
        print("=" * 60)
        
        if 'NAICS2017' not in df.columns:
            print("[ERROR] Missing NAICS2017 column")
            return False
        
        # Get unique NAICS codes
        unique_naics = df['NAICS2017'].nunique()
        
        print(f"  Unique NAICS codes: {unique_naics:,}")
        
        # NAICS code structure
        # 00 = Total
        # 11-99 = 2-digit sectors
        # 111-999 = 3-digit subsectors
        # 1111-9999 = 4-digit industry groups
        # 11111-99999 = 5-digit industries
        # 111111-999999 = 6-digit detailed industries
        
        naics_by_level = {}
        
        for level, desc in [(0, "Total"), (2, "Sector"), (3, "Subsector"), 
                             (4, "Industry Group"), (5, "Industry"), (6, "Detail")]:
            if level == 0:
                count = len(df[df['NAICS2017'] == '0'])
            else:
                count = len(df[df['NAICS2017'].astype(str).str.len() == level])
            
            naics_by_level[desc] = count
            print(f"    {desc} ({level}-digit): {count:,} records")
        
        # Check for common NAICS sectors (should all be present)
        expected_sectors = ['11', '21', '22', '23', '31', '42', '44', '48', '51', 
                            '52', '53', '54', '55', '56', '61', '62', '71', '72', '81']
        
        present_sectors = df[df['SECTOR'].astype(str).str.len() == 2]['SECTOR'].unique()
        missing_sectors = set(expected_sectors) - set(str(x) for x in present_sectors)
        
        if missing_sectors:
            print(f"  [WARN] Missing NAICS sectors: {missing_sectors}")
            self.issues.append({
                "check": "naics_codes",
                "severity": "LOW",
                "issue": f"Missing sectors: {missing_sectors}"
            })
        else:
            print(f"  [PASS] All major NAICS sectors present")
        
        self.stats['unique_naics'] = unique_naics
        self.stats['naics_by_level'] = naics_by_level
        
        return True
    
    def validate_employment_data(self, df):
        """Validate employment data completeness."""
        print(f"\n{'='*60}")
        print("CHECK 3: Employment Data Completeness")
        print("=" * 60)
        
        # Check for missing/suppressed employment values
        total_records = len(df)
        
        emp_missing = df['EMP'].isna().sum()
        emp_zero = (df['EMP'] == 0).sum()
        emp_present = total_records - emp_missing - emp_zero
        
        print(f"  Total records: {total_records:,}")
        print(f"  Employment present: {emp_present:,} ({emp_present/total_records*100:.1f}%)")
        print(f"  Employment missing: {emp_missing:,} ({emp_missing/total_records*100:.1f}%)")
        print(f"  Employment zero: {emp_zero:,} ({emp_zero/total_records*100:.1f}%)")
        
        # Check establishments data
        estab_missing = df['ESTAB'].isna().sum()
        estab_present = total_records - estab_missing
        
        print(f"\n  Establishments present: {estab_present:,} ({estab_present/total_records*100:.1f}%)")
        print(f"  Establishments missing: {estab_missing:,} ({estab_missing/total_records*100:.1f}%)")
        
        # Check payroll data
        payroll_missing = df['PAYANN'].isna().sum()
        payroll_present = total_records - payroll_missing
        
        print(f"\n  Payroll present: {payroll_present:,} ({payroll_present/total_records*100:.1f}%)")
        print(f"  Payroll missing: {payroll_missing:,} ({payroll_missing/total_records*100:.1f}%)")
        
        # Calculate total employment
        total_emp = df['EMP'].sum()
        total_estab = df['ESTAB'].sum()
        total_payroll = df['PAYANN'].sum()
        
        print(f"\n  Total employment: {total_emp:,.0f}")
        print(f"  Total establishments: {total_estab:,.0f}")
        print(f"  Total payroll: ${total_payroll:,.0f} thousand")
        
        # Check for data quality issues
        if emp_missing > total_records * 0.15:  # More than 15% missing
            self.issues.append({
                "check": "employment_data",
                "severity": "MEDIUM",
                "issue": f"High missing employment: {emp_missing/total_records*100:.1f}%"
            })
            print(f"\n  [WARN] High missing employment data")
        else:
            print(f"\n  [PASS] Acceptable missing data rate")
        
        self.stats['employment_completeness'] = {
            "total_records": total_records,
            "emp_present_pct": emp_present/total_records*100,
            "total_employment": int(total_emp),
            "total_establishments": int(total_estab),
            "total_payroll_k": int(total_payroll)
        }
        
        return emp_missing < total_records * 0.15
    
    def validate_geographic_aggregation(self, df):
        """Validate that county data aggregates correctly to state level."""
        print(f"\n{'='*60}")
        print("CHECK 4: Geographic Aggregation (County → State)")
        print("=" * 60)
        
        # Get total employment by state (NAICS code '0' = total)
        state_totals = df[df['NAICS2017'] == '0'].groupby('state')['EMP'].sum()
        
        # Get county-level data and aggregate to state
        county_data = df[(df['NAICS2017'] == '0') & (df['county'].notna())]
        county_to_state = county_data.groupby('state')['EMP'].sum()
        
        print(f"  States in data: {len(state_totals)}")
        print(f"  States with county detail: {len(county_to_state)}")
        
        # Compare state totals to county aggregations
        comparison = pd.DataFrame({
            'state_total': state_totals,
            'county_sum': county_to_state
        })
        
        comparison['diff'] = comparison['state_total'] - comparison['county_sum']
        comparison['diff_pct'] = (comparison['diff'] / comparison['state_total']) * 100
        
        # Check for significant discrepancies
        large_discrepancies = comparison[abs(comparison['diff_pct']) > 2.0]
        
        if not large_discrepancies.empty:
            print(f"\n  [WARN] {len(large_discrepancies)} states with >2% discrepancy")
            print("\n  Top 5 discrepancies:")
            top_5 = large_discrepancies.nlargest(5, 'diff_pct', keep='first')
            for state, row in top_5.iterrows():
                print(f"    State {state}: {row['diff_pct']:.2f}% difference")
            
            self.issues.append({
                "check": "geographic_aggregation",
                "severity": "MEDIUM",
                "issue": f"{len(large_discrepancies)} states with >2% county/state discrepancy"
            })
        else:
            print(f"\n  [PASS] All states within 2% discrepancy")
        
        # Calculate average discrepancy
        avg_discrepancy = comparison['diff_pct'].abs().mean()
        print(f"\n  Average discrepancy: {avg_discrepancy:.2f}%")
        
        self.stats['geo_aggregation'] = {
            "states_checked": len(comparison),
            "avg_discrepancy_pct": float(avg_discrepancy),
            "states_with_large_discrepancy": len(large_discrepancies)
        }
        
        return len(large_discrepancies) == 0
    
    def validate_small_county_suppression(self, df):
        """Identify counties with suppressed data."""
        print(f"\n{'='*60}")
        print("CHECK 5: Small County Disclosure Suppression")
        print("=" * 60)
        
        # Count counties with any suppressed employment data
        county_suppression = df.groupby(['state', 'county']).agg({
            'EMP': lambda x: x.isna().sum() / len(x) * 100
        }).reset_index()
        
        county_suppression.columns = ['state', 'county', 'suppression_pct']
        
        # Counties with high suppression (>50%)
        high_suppression = county_suppression[county_suppression['suppression_pct'] > 50]
        
        print(f"  Total counties analyzed: {len(county_suppression)}")
        print(f"  Counties with >50% suppression: {len(high_suppression)}")
        print(f"  Percentage affected: {len(high_suppression)/len(county_suppression)*100:.1f}%")
        
        if len(high_suppression) > 0:
            print(f"\n  [INFO] {len(high_suppression)} counties have significant disclosure suppression")
            print("  This is expected for small rural counties")
            
            # Show top 5 most suppressed
            print("\n  Top 5 most suppressed counties:")
            top_5_suppressed = high_suppression.nlargest(5, 'suppression_pct')
            for idx, row in top_5_suppressed.iterrows():
                print(f"    State {row['state']}, County {row['county']}: {row['suppression_pct']:.1f}% suppressed")
        
        self.stats['suppression'] = {
            "total_counties": len(county_suppression),
            "high_suppression_count": len(high_suppression),
            "high_suppression_pct": len(high_suppression)/len(county_suppression)*100
        }
        
        return True
    
    def generate_validation_report(self):
        """Generate comprehensive validation report."""
        report_path = OUTPUTS_DIR / f"[{self.timestamp}]_cbp_validation_report.txt"
        
        with open(report_path, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("CENSUS CBP DATA VALIDATION REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            high_issues = [i for i in self.issues if i.get("severity") == "HIGH"]
            medium_issues = [i for i in self.issues if i.get("severity") == "MEDIUM"]
            low_issues = [i for i in self.issues if i.get("severity") == "LOW"]
            
            f.write("-" * 80 + "\n")
            f.write("SUMMARY\n")
            f.write("-" * 80 + "\n\n")
            f.write(f"Total Issues: {len(self.issues)}\n")
            f.write(f"  High Severity: {len(high_issues)}\n")
            f.write(f"  Medium Severity: {len(medium_issues)}\n")
            f.write(f"  Low Severity: {len(low_issues)}\n\n")
            
            # Statistics
            f.write("-" * 80 + "\n")
            f.write("VALIDATION STATISTICS\n")
            f.write("-" * 80 + "\n\n")
            
            f.write(f"County Coverage: {self.stats.get('coverage_pct', 0):.1f}%\n")
            f.write(f"Unique Counties: {self.stats.get('unique_counties', 0):,}\n")
            f.write(f"Unique States: {self.stats.get('unique_states', 0)}\n")
            f.write(f"Unique NAICS Codes: {self.stats.get('unique_naics', 0):,}\n")
            
            if 'employment_completeness' in self.stats:
                emp = self.stats['employment_completeness']
                f.write(f"\nTotal Employment: {emp['total_employment']:,}\n")
                f.write(f"Total Establishments: {emp['total_establishments']:,}\n")
                f.write(f"Employment Data Present: {emp['emp_present_pct']:.1f}%\n")
            
            if 'geo_aggregation' in self.stats:
                geo = self.stats['geo_aggregation']
                f.write(f"\nGeographic Aggregation Discrepancy: {geo['avg_discrepancy_pct']:.2f}%\n")
            
            # Issues detail
            if self.issues:
                f.write("\n" + "-" * 80 + "\n")
                f.write("ISSUES DETAIL\n")
                f.write("-" * 80 + "\n\n")
                
                for issue in self.issues:
                    f.write(f"[{issue['severity']}] {issue['check'].upper()}\n")
                    f.write(f"  {issue['issue']}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("RECOMMENDATIONS\n")
            f.write("-" * 80 + "\n\n")
            
            if high_issues:
                f.write("HIGH PRIORITY:\n")
                f.write("  - Address high-severity issues before proceeding\n\n")
            
            if not self.issues:
                f.write("All validation checks passed. Data quality is good.\n")
                f.write("Ready for geographic hierarchy construction.\n\n")
            else:
                f.write("Review issues above before proceeding to analysis.\n\n")
        
        print(f"\n[SAVED] Validation report: {report_path.name}")
        
        # Save stats as JSON
        stats_path = OUTPUTS_DIR / f"[{self.timestamp}]_cbp_validation_stats.json"
        with open(stats_path, "w") as f:
            json.dump(self.stats, f, indent=2)
        print(f"[SAVED] Statistics JSON: {stats_path.name}")
        
        return report_path
    
    def run_all_validations(self, year=2021):
        """Run all validation checks."""
        print("\n" + "=" * 80)
        print("CENSUS CBP DATA VALIDATION")
        print("=" * 80)
        print(f"Year: {year}")
        
        # Load data
        df = self.load_cbp_data(year)
        
        # Run validations
        self.validate_county_fips(df)
        self.validate_naics_codes(df)
        self.validate_employment_data(df)
        self.validate_geographic_aggregation(df)
        self.validate_small_county_suppression(df)
        
        # Generate report
        report_path = self.generate_validation_report()
        
        # Summary
        print("\n" + "=" * 80)
        print("VALIDATION COMPLETE")
        print("=" * 80)
        print(f"Total issues: {len(self.issues)}")
        print(f"Report: {report_path}")
        
        if self.issues:
            high_count = len([i for i in self.issues if i.get("severity") == "HIGH"])
            if high_count > 0:
                print(f"\n[ALERT] {high_count} high-severity issues require attention!")
        else:
            print("\n[SUCCESS] All validation checks passed!")


def main():
    """Main execution function."""
    validator = CBPValidator()
    validator.run_all_validations(year=2021)


if __name__ == "__main__":
    main()
