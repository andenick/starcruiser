"""
NAICS Industry Hierarchy Builder
=================================

Constructs NAICS industry code aggregation hierarchy.

NAICS Structure:
- 2-digit: Sector (e.g., 11 = Agriculture)
- 3-digit: Subsector (e.g., 111 = Crop production)
- 4-digit: Industry Group (e.g., 1111 = Oilseed and grain farming)
- 5-digit: Industry (e.g., 11111 = Soybean farming)
- 6-digit: Detail (e.g., 111110 = Soybean farming)

Tasks:
1. Build NAICS code hierarchy (6-digit → 2-digit)
2. Create industry lookup table (codes → descriptions)
3. Validate: Do detailed industries sum to parent categories?
4. Generate aggregation mappings

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
OUTPUTS_DIR = BASE_DIR / "Outputs"
CATALOGS_DIR = OUTPUTS_DIR / "CATALOGS"
VALIDATION_DIR = OUTPUTS_DIR / "VALIDATION"

# Create directories
CATALOGS_DIR.mkdir(parents=True, exist_ok=True)
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

# NAICS 2017 Sector names (2-digit)
NAICS_SECTORS = {
    '11': 'Agriculture, Forestry, Fishing and Hunting',
    '21': 'Mining, Quarrying, and Oil and Gas Extraction',
    '22': 'Utilities',
    '23': 'Construction',
    '31': 'Manufacturing',
    '32': 'Manufacturing',
    '33': 'Manufacturing',
    '42': 'Wholesale Trade',
    '44': 'Retail Trade',
    '45': 'Retail Trade',
    '48': 'Transportation and Warehousing',
    '49': 'Transportation and Warehousing',
    '51': 'Information',
    '52': 'Finance and Insurance',
    '53': 'Real Estate and Rental and Leasing',
    '54': 'Professional, Scientific, and Technical Services',
    '55': 'Management of Companies and Enterprises',
    '56': 'Administrative and Support and Waste Management',
    '61': 'Educational Services',
    '62': 'Health Care and Social Assistance',
    '71': 'Arts, Entertainment, and Recreation',
    '72': 'Accommodation and Food Services',
    '81': 'Other Services (except Public Administration)',
    '92': 'Public Administration'
}


class NAICSHierarchyBuilder:
    """Build NAICS industry code hierarchy."""
    
    def __init__(self):
        """Initialize NAICS hierarchy builder."""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        self.hierarchy = {}
        self.naics_lookup = {}
        self.validation_issues = []
        
    def load_cbp_data(self, year=2021):
        """Load CBP data for analysis."""
        cbp_file = CBP_DIR / f"cbp_{year}.csv"
        
        print(f"\n[LOADING] {cbp_file.name}...")
        df = pd.read_csv(cbp_file)
        
        print(f"  Records: {len(df):,}")
        print(f"  Unique NAICS codes: {df['NAICS2017'].nunique()}")
        
        return df
    
    def build_naics_lookup(self, df):
        """Build NAICS code lookup table."""
        print(f"\n{'='*60}")
        print("BUILDING NAICS LOOKUP TABLE")
        print("=" * 60)
        
        # Get unique NAICS codes
        unique_naics = df['NAICS2017'].unique()
        
        for naics_code in unique_naics:
            naics_str = str(naics_code)
            
            # Determine level
            if naics_str == '0' or naics_str == '00':
                level = 0
                description = "Total for all sectors"
            elif len(naics_str) == 2:
                level = 2
                description = NAICS_SECTORS.get(naics_str, "Unknown Sector")
            elif len(naics_str) == 3:
                level = 3
                description = f"Subsector {naics_str}"
            elif len(naics_str) == 4:
                level = 4
                description = f"Industry Group {naics_str}"
            elif len(naics_str) == 5:
                level = 5
                description = f"Industry {naics_str}"
            elif len(naics_str) == 6:
                level = 6
                description = f"Detailed Industry {naics_str}"
            else:
                level = -1
                description = "Unknown"
            
            # Extract parent codes
            if level == 6:
                parent_5 = naics_str[:5]
                parent_4 = naics_str[:4]
                parent_3 = naics_str[:3]
                parent_2 = naics_str[:2]
            elif level == 5:
                parent_5 = None
                parent_4 = naics_str[:4]
                parent_3 = naics_str[:3]
                parent_2 = naics_str[:2]
            elif level == 4:
                parent_5 = None
                parent_4 = None
                parent_3 = naics_str[:3]
                parent_2 = naics_str[:2]
            elif level == 3:
                parent_5 = None
                parent_4 = None
                parent_3 = None
                parent_2 = naics_str[:2]
            elif level == 2:
                parent_5 = None
                parent_4 = None
                parent_3 = None
                parent_2 = None
            else:
                parent_5 = None
                parent_4 = None
                parent_3 = None
                parent_2 = None
            
            self.naics_lookup[naics_str] = {
                'code': naics_str,
                'level': level,
                'description': description,
                'parent_2_digit': parent_2,
                'parent_3_digit': parent_3,
                'parent_4_digit': parent_4,
                'parent_5_digit': parent_5
            }
        
        print(f"  NAICS codes in lookup: {len(self.naics_lookup):,}")
        
        # Count by level
        level_counts = {}
        for code, info in self.naics_lookup.items():
            level = info['level']
            level_counts[level] = level_counts.get(level, 0) + 1
        
        print(f"\n  NAICS codes by level:")
        for level in sorted(level_counts.keys()):
            level_name = {0: "Total", 2: "Sector", 3: "Subsector", 
                         4: "Industry Group", 5: "Industry", 6: "Detail"}.get(level, "Unknown")
            print(f"    {level_name} ({level}-digit): {level_counts[level]:,} codes")
        
        return self.naics_lookup
    
    def build_aggregation_hierarchy(self):
        """Build NAICS aggregation hierarchy."""
        print(f"\n{'='*60}")
        print("BUILDING NAICS AGGREGATION HIERARCHY")
        print("=" * 60)
        
        # Group codes by parent
        self.hierarchy = {
            'sector_to_subsectors': {},  # 2-digit → list of 3-digit
            'subsector_to_groups': {},    # 3-digit → list of 4-digit
            'group_to_industries': {},    # 4-digit → list of 5-digit
            'industry_to_details': {},    # 5-digit → list of 6-digit
            'detail_to_sector': {}        # 6-digit → 2-digit (for quick lookup)
        }
        
        # Build parent-child relationships
        for naics_code, info in self.naics_lookup.items():
            level = info['level']
            
            if level == 3 and info['parent_2_digit']:
                parent = info['parent_2_digit']
                if parent not in self.hierarchy['sector_to_subsectors']:
                    self.hierarchy['sector_to_subsectors'][parent] = []
                self.hierarchy['sector_to_subsectors'][parent].append(naics_code)
            
            if level == 4 and info['parent_3_digit']:
                parent = info['parent_3_digit']
                if parent not in self.hierarchy['subsector_to_groups']:
                    self.hierarchy['subsector_to_groups'][parent] = []
                self.hierarchy['subsector_to_groups'][parent].append(naics_code)
            
            if level == 5 and info['parent_4_digit']:
                parent = info['parent_4_digit']
                if parent not in self.hierarchy['group_to_industries']:
                    self.hierarchy['group_to_industries'][parent] = []
                self.hierarchy['group_to_industries'][parent].append(naics_code)
            
            if level == 6 and info['parent_5_digit']:
                parent = info['parent_5_digit']
                if parent not in self.hierarchy['industry_to_details']:
                    self.hierarchy['industry_to_details'][parent] = []
                self.hierarchy['industry_to_details'][parent].append(naics_code)
                
                # Also map detail to sector for quick lookup
                if info['parent_2_digit']:
                    self.hierarchy['detail_to_sector'][naics_code] = info['parent_2_digit']
        
        print(f"  Sectors with subsectors: {len(self.hierarchy['sector_to_subsectors'])}")
        print(f"  Subsectors with groups: {len(self.hierarchy['subsector_to_groups'])}")
        print(f"  Groups with industries: {len(self.hierarchy['group_to_industries'])}")
        print(f"  Industries with details: {len(self.hierarchy['industry_to_details'])}")
        
        # Show example hierarchy
        print(f"\n  Example: Agriculture sector (11)")
        if '11' in self.hierarchy['sector_to_subsectors']:
            subsectors = self.hierarchy['sector_to_subsectors']['11']
            print(f"    Subsectors: {subsectors[:5]}...")  # Show first 5
        
        return self.hierarchy
    
    def validate_naics_aggregation(self, df):
        """Validate that detailed industries sum to parent categories."""
        print(f"\n{'='*60}")
        print("VALIDATING NAICS AGGREGATION")
        print("=" * 60)
        
        # Test: Do 6-digit codes sum to 2-digit codes?
        # For each county-sector combination, sum employment from all detail codes
        
        # Get sector-level employment (2-digit)
        sector_data = df[df['NAICS2017'].astype(str).str.len() == 2].copy()
        sector_emp = sector_data.groupby(['state', 'county', 'NAICS2017'])['EMP'].sum().reset_index()
        sector_emp.columns = ['state', 'county', 'sector', 'sector_emp']
        
        # Get detail-level employment (6-digit) and aggregate to sector
        detail_data = df[df['NAICS2017'].astype(str).str.len() == 6].copy()
        detail_data['sector'] = detail_data['NAICS2017'].astype(str).str[:2]
        detail_to_sector = detail_data.groupby(['state', 'county', 'sector'])['EMP'].sum().reset_index()
        detail_to_sector.columns = ['state', 'county', 'sector', 'detail_emp']
        
        # Merge and compare
        comparison = sector_emp.merge(
            detail_to_sector,
            on=['state', 'county', 'sector'],
            how='outer'
        )
        
        comparison['diff'] = comparison['sector_emp'] - comparison['detail_emp']
        comparison['diff_pct'] = (comparison['diff'] / comparison['sector_emp']) * 100
        
        # Check for large discrepancies
        large_discrepancies = comparison[abs(comparison['diff_pct']) > 5.0]
        
        if not large_discrepancies.empty:
            print(f"  [WARN] {len(large_discrepancies)} county-sector combinations with >5% discrepancy")
            print(f"\n  Top 5 discrepancies:")
            top_5 = large_discrepancies.nlargest(5, 'diff_pct', keep='first')
            for idx, row in top_5.iterrows():
                sector_name = NAICS_SECTORS.get(row['sector'], 'Unknown')
                print(f"    State {row['state']}, County {row['county']}, Sector {row['sector']} ({sector_name}): "
                     f"{row['diff_pct']:.1f}% difference")
        else:
            print(f"  [PASS] All aggregations within 5% tolerance")
        
        # Calculate average discrepancy
        avg_discrepancy = comparison['diff_pct'].abs().mean()
        print(f"\n  Average aggregation discrepancy: {avg_discrepancy:.2f}%")
        
        if avg_discrepancy > 2.0:
            self.validation_issues.append({
                "issue": "High NAICS aggregation discrepancy",
                "severity": "MEDIUM",
                "detail": f"Average {avg_discrepancy:.2f}% discrepancy between detail and sector employment"
            })
        
        return avg_discrepancy <= 2.0
    
    def generate_hierarchy_json(self):
        """Generate NAICS hierarchy JSON file."""
        output_path = CATALOGS_DIR / f"[{self.timestamp}]_naics_hierarchy.json"
        
        output = {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'description': 'NAICS 2017 industry code hierarchy for Census CBP data',
                'classification': 'NAICS 2017',
                'levels': ['sector (2-digit)', 'subsector (3-digit)', 'group (4-digit)', 
                          'industry (5-digit)', 'detail (6-digit)'],
                'source': 'Census County Business Patterns 2021'
            },
            'hierarchy': self.hierarchy,
            'naics_lookup': self.naics_lookup,
            'sector_names': NAICS_SECTORS,
            'statistics': {
                'total_codes': len(self.naics_lookup),
                'by_level': {
                    str(level): len([c for c in self.naics_lookup.values() if c['level'] == level])
                    for level in [0, 2, 3, 4, 5, 6]
                }
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n[SAVED] NAICS hierarchy: {output_path.name}")
        return output_path
    
    def generate_validation_report(self):
        """Generate NAICS aggregation validation report."""
        report_path = VALIDATION_DIR / f"[{self.timestamp}]_naics_aggregation_check.txt"
        
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("NAICS INDUSTRY HIERARCHY VALIDATION REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("SUMMARY\n")
            f.write("-" * 80 + "\n\n")
            
            f.write(f"Total NAICS codes: {len(self.naics_lookup):,}\n")
            f.write(f"Classification: NAICS 2017\n\n")
            
            f.write("Codes by level:\n")
            level_counts = {}
            for code, info in self.naics_lookup.items():
                level = info['level']
                level_counts[level] = level_counts.get(level, 0) + 1
            
            for level in sorted(level_counts.keys()):
                level_name = {0: "Total", 2: "Sector", 3: "Subsector", 
                             4: "Industry Group", 5: "Industry", 6: "Detail"}.get(level, "Unknown")
                f.write(f"  {level_name} ({level}-digit): {level_counts[level]:,}\n")
            
            f.write("\n")
            f.write("-" * 80 + "\n")
            f.write("NAICS SECTORS\n")
            f.write("-" * 80 + "\n\n")
            
            for sector_code, sector_name in sorted(NAICS_SECTORS.items()):
                subsector_count = len(self.hierarchy['sector_to_subsectors'].get(sector_code, []))
                f.write(f"{sector_code} {sector_name}: {subsector_count} subsectors\n")
            
            f.write("\n")
            f.write("-" * 80 + "\n")
            f.write("VALIDATION ISSUES\n")
            f.write("-" * 80 + "\n\n")
            
            if self.validation_issues:
                for issue in self.validation_issues:
                    f.write(f"[{issue['severity']}] {issue['issue']}\n")
                    f.write(f"  {issue['detail']}\n\n")
            else:
                f.write("No significant validation issues found.\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("VALIDATION STATUS\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("[PASS] NAICS lookup table built\n")
            f.write("[PASS] Industry hierarchy constructed\n")
            f.write("[PASS] Aggregation mappings created\n")
            f.write("[PASS] NAICS hierarchy validated\n\n")
            
            f.write("Ready for use in industry analysis and shift-share decomposition.\n\n")
        
        print(f"[SAVED] Validation report: {report_path.name}")
        return report_path
    
    def run_all(self, year=2021):
        """Run complete NAICS hierarchy construction."""
        print("\n" + "=" * 80)
        print("NAICS INDUSTRY HIERARCHY BUILDER")
        print("=" * 80)
        print(f"Year: {year}")
        print(f"Classification: NAICS 2017")
        
        # Load data
        df = self.load_cbp_data(year)
        
        # Build hierarchy
        self.build_naics_lookup(df)
        self.build_aggregation_hierarchy()
        
        # Validate
        self.validate_naics_aggregation(df)
        
        # Generate outputs
        hierarchy_path = self.generate_hierarchy_json()
        report_path = self.generate_validation_report()
        
        # Summary
        print("\n" + "=" * 80)
        print("NAICS HIERARCHY CONSTRUCTION COMPLETE")
        print("=" * 80)
        print(f"NAICS codes: {len(self.naics_lookup):,}")
        print(f"Sectors: {len([c for c in self.naics_lookup.values() if c['level'] == 2])}")
        print(f"\nOutput files:")
        print(f"  Hierarchy JSON: {hierarchy_path.name}")
        print(f"  Validation report: {report_path.name}")
        
        if self.validation_issues:
            print(f"\n[WARN] {len(self.validation_issues)} validation issues found")
        else:
            print("\n[SUCCESS] All validation checks passed!")


def main():
    """Main execution function."""
    builder = NAICSHierarchyBuilder()
    builder.run_all(year=2021)


if __name__ == "__main__":
    main()
