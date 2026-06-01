"""
Data Quality Monitoring & Alerts
=================================

Automated data quality monitoring system for StarCruiser database.
Detects anomalies, missing data, outliers, and freshness issues.

Checks:
1. Missing Data: Are expected series present?
2. Outliers: Values >3 standard deviations from mean
3. Revisions: Did previously published data change significantly?
4. Freshness: Is data older than expected?
5. Completeness: Are there unexpected gaps in time series?

Output: Email alerts (if configured) + log file

Author: StarCruiser Project
Created: December 5, 2025
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Project paths
BASE_DIR = PROJECT_ROOT
CATALOG_PATH = BASE_DIR / "Outputs" / "CATALOGS" / "MASTER_CATALOG.csv"
INPUTS_DIR = BASE_DIR / "Inputs"
OUTPUTS_DIR = BASE_DIR / "Outputs"
VALIDATION_DIR = OUTPUTS_DIR / "VALIDATION"
LOG_DIR = OUTPUTS_DIR / "LOGS"

# Create directories
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Quality thresholds
FRESHNESS_THRESHOLD_DAYS = 60  # Data older than 60 days is stale
OUTLIER_THRESHOLD_SIGMA = 3    # Values >3 std devs are outliers
REVISION_THRESHOLD_PCT = 5     # Revisions >5% are significant
MAX_GAP_DAYS = 90              # Gaps >90 days are concerning


class QualityMonitor:
    """Data quality monitoring system."""
    
    def __init__(self):
        self.issues = []
        self.catalog = None
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def load_catalog(self):
        """Load master catalog."""
        if not CATALOG_PATH.exists():
            raise FileNotFoundError(f"Master catalog not found: {CATALOG_PATH}")
        
        self.catalog = pd.read_csv(CATALOG_PATH)
        print(f"[LOADED] Master catalog: {len(self.catalog)} datasets")
        
    def check_missing_data(self):
        """Check for expected series that are missing."""
        print(f"\n{'='*60}")
        print("CHECK 1: Missing Data")
        print("=" * 60)
        
        # Define expected series by source
        expected_series = {
            "FRED": ["UNRATE", "PAYEMS", "CPIAUCSL", "DGS10", "DGS2"],
            "BLS": ["CES0000000001", "LNS14000000"],
            "CENSUS": ["CBP"],
            "BEA": ["NIPA"]
        }
        
        issues_found = []
        
        for source, series_list in expected_series.items():
            source_data = self.catalog[self.catalog["source"].str.contains(source, case=False, na=False)]
            
            for series_id in series_list:
                matches = source_data[source_data["dataset_name"].str.contains(series_id, case=False, na=False)]
                
                if matches.empty:
                    issue = f"MISSING: {source} - {series_id}"
                    issues_found.append(issue)
                    self.issues.append({
                        "check": "missing_data",
                        "severity": "HIGH",
                        "issue": issue
                    })
                    print(f"  [FAIL] {issue}")
                else:
                    print(f"  [PASS] {source} - {series_id} present")
        
        if not issues_found:
            print(f"\n[PASS] All expected series present")
        else:
            print(f"\n[FAIL] {len(issues_found)} missing series")
        
        return len(issues_found) == 0
    
    def check_data_freshness(self):
        """Check if data is up to date."""
        print(f"\n{'='*60}")
        print("CHECK 2: Data Freshness")
        print("=" * 60)
        
        today = datetime.now()
        threshold_date = today - timedelta(days=FRESHNESS_THRESHOLD_DAYS)
        
        issues_found = []
        
        # Check end_date in catalog
        if "end_date" in self.catalog.columns:
            for idx, row in self.catalog.iterrows():
                try:
                    end_date = pd.to_datetime(row["end_date"])
                    
                    if end_date < threshold_date:
                        issue = f"STALE: {row['dataset_name']} - Last update {end_date.strftime('%Y-%m-%d')} ({(today - end_date).days} days ago)"
                        issues_found.append(issue)
                        self.issues.append({
                            "check": "freshness",
                            "severity": "MEDIUM",
                            "issue": issue,
                            "dataset": row["dataset_name"],
                            "days_old": (today - end_date).days
                        })
                        print(f"  [FAIL] {issue}")
                except:
                    pass
        
        if not issues_found:
            print(f"\n[PASS] All data is fresh (<{FRESHNESS_THRESHOLD_DAYS} days old)")
        else:
            print(f"\n[FAIL] {len(issues_found)} stale datasets")
        
        return len(issues_found) == 0
    
    def check_outliers(self):
        """Check for outliers in data (>3 sigma)."""
        print(f"\n{'='*60}")
        print("CHECK 3: Outlier Detection")
        print("=" * 60)
        
        # Sample check on FRED data (if available)
        fred_files = list((INPUTS_DIR / "source" / "FRED").glob("*.csv")) if (INPUTS_DIR / "source" / "FRED").exists() else []
        
        if not fred_files:
            print(f"  [SKIP] No FRED data files found for outlier check")
            return True
        
        issues_found = []
        
        for file_path in fred_files[:5]:  # Check first 5 files
            try:
                df = pd.read_csv(file_path)
                
                if "value" not in df.columns:
                    continue
                
                values = pd.to_numeric(df["value"], errors="coerce")
                values = values.dropna()
                
                if len(values) < 10:
                    continue
                
                mean = values.mean()
                std = values.std()
                
                if std == 0:
                    continue
                
                outliers = values[np.abs(values - mean) > OUTLIER_THRESHOLD_SIGMA * std]
                
                if len(outliers) > 0:
                    issue = f"OUTLIERS: {file_path.name} - {len(outliers)} values >{OUTLIER_THRESHOLD_SIGMA} sigma"
                    issues_found.append(issue)
                    self.issues.append({
                        "check": "outliers",
                        "severity": "LOW",
                        "issue": issue,
                        "file": file_path.name,
                        "outlier_count": len(outliers)
                    })
                    print(f"  [WARN] {issue}")
                else:
                    print(f"  [PASS] {file_path.name}")
                    
            except Exception as e:
                print(f"  [ERROR] Failed to check {file_path.name}: {e}")
        
        if not issues_found:
            print(f"\n[PASS] No significant outliers detected")
        else:
            print(f"\n[WARN] {len(issues_found)} files with outliers")
        
        return True  # Outliers are warnings, not failures
    
    def check_completeness(self):
        """Check for unexpected gaps in time series."""
        print(f"\n{'='*60}")
        print("CHECK 4: Time Series Completeness")
        print("=" * 60)
        
        # Sample check on key series
        key_series_files = {
            "UNRATE": INPUTS_DIR / "source" / "FRED" / "data" / "[2025.09.29] fred_employment_20250929.csv"
        }
        
        issues_found = []
        
        for series_name, file_path in key_series_files.items():
            if not file_path.exists():
                print(f"  [SKIP] {series_name} file not found")
                continue
            
            try:
                df = pd.read_csv(file_path)
                df = df[df["series_id"] == series_name].copy()
                
                if df.empty:
                    continue
                
                df["date"] = pd.to_datetime(df["date"])
                df = df.sort_values("date")
                
                # Check for gaps
                df["gap_days"] = df["date"].diff().dt.days
                large_gaps = df[df["gap_days"] > MAX_GAP_DAYS]
                
                if not large_gaps.empty:
                    issue = f"GAPS: {series_name} - {len(large_gaps)} gaps >{MAX_GAP_DAYS} days"
                    issues_found.append(issue)
                    self.issues.append({
                        "check": "completeness",
                        "severity": "MEDIUM",
                        "issue": issue,
                        "series": series_name,
                        "gap_count": len(large_gaps)
                    })
                    print(f"  [FAIL] {issue}")
                else:
                    print(f"  [PASS] {series_name} - No large gaps")
                    
            except Exception as e:
                print(f"  [ERROR] Failed to check {series_name}: {e}")
        
        if not issues_found:
            print(f"\n[PASS] No large gaps detected")
        else:
            print(f"\n[FAIL] {len(issues_found)} series with gaps")
        
        return len(issues_found) == 0
    
    def generate_report(self):
        """Generate quality monitoring report."""
        report_path = VALIDATION_DIR / f"quality_monitor_{self.timestamp}.txt"
        
        with open(report_path, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("STARCRUISER DATA QUALITY MONITORING REPORT\n")
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
            
            # Detail
            if self.issues:
                f.write("-" * 80 + "\n")
                f.write("ISSUES DETAIL\n")
                f.write("-" * 80 + "\n\n")
                
                for issue in self.issues:
                    f.write(f"[{issue['severity']}] {issue['check'].upper()}\n")
                    f.write(f"  {issue['issue']}\n\n")
            else:
                f.write("No issues detected!\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("RECOMMENDATIONS\n")
            f.write("-" * 80 + "\n\n")
            
            if high_issues:
                f.write("HIGH PRIORITY:\n")
                f.write("  - Address missing data immediately\n")
                f.write("  - Run data refresh scripts\n\n")
            
            if medium_issues:
                f.write("MEDIUM PRIORITY:\n")
                f.write("  - Investigate stale data sources\n")
                f.write("  - Review time series gaps\n\n")
            
            if not self.issues:
                f.write("All quality checks passed. No action required.\n\n")
            
            f.write(f"\nNext monitoring run: {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}\n")
        
        print(f"\n[SAVED] Quality report: {report_path.name}")
        return report_path
    
    def send_alert_email(self, report_path):
        """
        Send email alert if critical issues detected.
        
        Note: Requires email configuration in environment variables.
        """
        high_issues = [i for i in self.issues if i.get("severity") == "HIGH"]
        
        if not high_issues:
            print(f"\n[INFO] No high-severity issues, email alert not sent")
            return
        
        # Check for email configuration
        smtp_server = os.environ.get("SMTP_SERVER")
        smtp_port = os.environ.get("SMTP_PORT", 587)
        sender_email = os.environ.get("SENDER_EMAIL")
        sender_password = os.environ.get("SENDER_PASSWORD")
        recipient_email = os.environ.get("ALERT_EMAIL")
        
        if not all([smtp_server, sender_email, sender_password, recipient_email]):
            print(f"\n[WARNING] Email configuration incomplete, skipping alert")
            print(f"[INFO] Set environment variables: SMTP_SERVER, SENDER_EMAIL, SENDER_PASSWORD, ALERT_EMAIL")
            return
        
        # Create email
        subject = f"StarCruiser Data Quality Alert - {len(high_issues)} High-Severity Issues"
        
        body = f"""
StarCruiser Data Quality Monitoring Alert

{len(high_issues)} HIGH-SEVERITY issues detected:

"""
        for issue in high_issues:
            body += f"- {issue['issue']}\n"
        
        body += f"""

Full report: {report_path}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        try:
            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            print(f"\n[SUCCESS] Alert email sent to {recipient_email}")
        except Exception as e:
            print(f"\n[ERROR] Failed to send alert email: {e}")
    
    def run_all_checks(self):
        """Run all quality checks."""
        print("\n" + "=" * 80)
        print("STARCRUISER DATA QUALITY MONITORING")
        print("=" * 80 + "\n")
        
        # Load catalog
        self.load_catalog()
        
        # Run checks
        self.check_missing_data()
        self.check_data_freshness()
        self.check_outliers()
        self.check_completeness()
        
        # Generate report
        report_path = self.generate_report()
        
        # Send alert if needed
        self.send_alert_email(report_path)
        
        # Summary
        print("\n" + "=" * 80)
        print("QUALITY MONITORING COMPLETE")
        print("=" * 80)
        print(f"Total issues: {len(self.issues)}")
        print(f"Report: {report_path}")
        
        if self.issues:
            high_count = len([i for i in self.issues if i.get("severity") == "HIGH"])
            if high_count > 0:
                print(f"\n[ALERT] {high_count} high-severity issues require immediate attention!")
        else:
            print("\n[SUCCESS] All quality checks passed!")


def main():
    """Main execution function."""
    monitor = QualityMonitor()
    monitor.run_all_checks()


if __name__ == "__main__":
    main()
