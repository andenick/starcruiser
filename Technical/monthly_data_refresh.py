"""
Monthly Data Refresh Pipeline
==============================

Automated pipeline to refresh StarCruiser dashboard data monthly.
Runs on first Friday of each month (BLS employment report day).

Tasks:
1. Download latest FRED data
2. Download latest BLS data
3. Update master catalog
4. Convert to FST format (for dashboard performance)
5. Generate refresh report

Schedule:
- Windows: Task Scheduler (first Friday 10:00 AM)
- Linux: Cron job (0 10 * * 5)

Author: StarCruiser Project  
Created: December 5, 2025
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd
import json
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Project paths
BASE_DIR = PROJECT_ROOT
TECHNICAL_DIR = BASE_DIR / "Technical"
OUTPUTS_DIR = BASE_DIR / "Outputs"
DASHBOARD_DIR = BASE_DIR / "Dashboard"
LOG_DIR = OUTPUTS_DIR / "LOGS"
REFRESH_DIR = OUTPUTS_DIR / "REFRESH_REPORTS"

# Create directories
LOG_DIR.mkdir(parents=True, exist_ok=True)
REFRESH_DIR.mkdir(parents=True, exist_ok=True)

# Log file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"monthly_refresh_{timestamp}.log"


def log(message, level="INFO"):
    """Write message to log file and console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{level}] {message}"
    
    print(log_message)
    
    with open(LOG_FILE, "a") as f:
        f.write(log_message + "\n")


def run_script(script_name, script_dir=TECHNICAL_DIR, timeout=600):
    """
    Run a Python script and capture output.
    
    Args:
        script_name (str): Script filename
        script_dir (Path): Directory containing script
        timeout (int): Timeout in seconds
    
    Returns:
        tuple: (success: bool, output: str)
    """
    script_path = script_dir / script_name
    
    if not script_path.exists():
        log(f"Script not found: {script_path}", "ERROR")
        return False, f"Script not found: {script_path}"
    
    log(f"Running {script_name}...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(script_dir)
        )
        
        if result.returncode == 0:
            log(f"{script_name} completed successfully", "SUCCESS")
            return True, result.stdout
        else:
            log(f"{script_name} failed with return code {result.returncode}", "ERROR")
            log(f"Error output: {result.stderr}", "ERROR")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        log(f"{script_name} timed out after {timeout} seconds", "ERROR")
        return False, f"Timeout after {timeout} seconds"
    except Exception as e:
        log(f"{script_name} failed with exception: {e}", "ERROR")
        return False, str(e)


def run_r_script(script_name, script_dir=TECHNICAL_DIR, timeout=300):
    """
    Run an R script.
    
    Args:
        script_name (str): Script filename
        script_dir (Path): Directory containing script
        timeout (int): Timeout in seconds
    
    Returns:
        tuple: (success: bool, output: str)
    """
    script_path = script_dir / script_name
    
    if not script_path.exists():
        log(f"R script not found: {script_path}", "ERROR")
        return False, f"Script not found: {script_path}"
    
    log(f"Running {script_name}...")
    
    try:
        result = subprocess.run(
            ["Rscript", str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(script_dir)
        )
        
        if result.returncode == 0:
            log(f"{script_name} completed successfully", "SUCCESS")
            return True, result.stdout
        else:
            log(f"{script_name} failed with return code {result.returncode}", "ERROR")
            log(f"Error output: {result.stderr}", "ERROR")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        log(f"{script_name} timed out after {timeout} seconds", "ERROR")
        return False, f"Timeout after {timeout} seconds"
    except Exception as e:
        log(f"{script_name} failed with exception: {e}", "ERROR")
        return False, str(e)


def backup_current_data():
    """Backup current data files before refresh."""
    log("Backing up current data...")
    
    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = OUTPUTS_DIR / "BACKUPS" / backup_timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup master catalog
    catalog_path = OUTPUTS_DIR / "CATALOGS" / "MASTER_CATALOG.csv"
    if catalog_path.exists():
        shutil.copy2(catalog_path, backup_dir / "MASTER_CATALOG.csv")
        log(f"Backed up master catalog to {backup_dir}")
    
    return backup_dir


def generate_refresh_report(results):
    """
    Generate refresh report summarizing what was updated.
    
    Args:
        results (dict): Dictionary of task results
    """
    report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REFRESH_DIR / f"refresh_report_{report_timestamp}.txt"
    
    with open(report_path, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("STARCRUISER MONTHLY DATA REFRESH REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Log File: {LOG_FILE.name}\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("TASK EXECUTION SUMMARY\n")
        f.write("-" * 80 + "\n\n")
        
        total_tasks = len(results)
        successful_tasks = sum(1 for success, _ in results.values() if success)
        
        f.write(f"Total Tasks: {total_tasks}\n")
        f.write(f"Successful: {successful_tasks}\n")
        f.write(f"Failed: {total_tasks - successful_tasks}\n\n")
        
        for task_name, (success, output) in results.items():
            status = "SUCCESS" if success else "FAILED"
            f.write(f"{task_name}: {status}\n")
            if not success and output:
                f.write(f"  Error: {output[:200]}...\n")
        
        f.write("\n")
        f.write("-" * 80 + "\n")
        f.write("NEXT STEPS\n")
        f.write("-" * 80 + "\n\n")
        
        if successful_tasks == total_tasks:
            f.write("All tasks completed successfully.\n")
            f.write("Dashboard data is up to date.\n")
        else:
            f.write("Some tasks failed. Review log file for details.\n")
            f.write("Dashboard may be using stale data.\n")
        
        f.write("\n")
        f.write(f"Next refresh scheduled: First Friday of next month\n")
        f.write("\n")
    
    log(f"Refresh report saved: {report_path.name}")
    return report_path


def monthly_update():
    """Execute monthly data refresh pipeline."""
    log("=" * 60)
    log("STARCRUISER MONTHLY DATA REFRESH STARTED")
    log("=" * 60)
    
    results = {}
    
    # Task 1: Backup current data
    log("\n[TASK 1/6] Backing up current data...")
    try:
        backup_dir = backup_current_data()
        results["backup"] = (True, str(backup_dir))
    except Exception as e:
        log(f"Backup failed: {e}", "ERROR")
        results["backup"] = (False, str(e))
    
    # Task 2: Download latest FRED employment data
    log("\n[TASK 2/6] Downloading FRED employment data...")
    success, output = run_script("extract_fred_employment.py")
    results["fred_download"] = (success, output)
    
    # Task 3: Download latest BLS data (if script exists)
    log("\n[TASK 3/6] Downloading BLS data...")
    if (TECHNICAL_DIR / "download_bls_api.py").exists():
        success, output = run_script("download_bls_api.py")
        results["bls_download"] = (success, output)
    else:
        log("BLS download script not found, skipping", "WARNING")
        results["bls_download"] = (False, "Script not found")
    
    # Task 4: Download UI claims (real-time indicator)
    log("\n[TASK 4/6] Downloading UI claims...")
    success, output = run_script("update_ui_claims.py")
    results["ui_claims_download"] = (success, output)
    
    # Task 5: Update master catalog
    log("\n[TASK 5/6] Updating master catalog...")
    success, output = run_script("build_master_catalog.py")
    results["catalog_update"] = (success, output)
    
    # Task 6: Convert to FST format (if R script exists)
    log("\n[TASK 6/6] Converting to FST format for dashboard...")
    if (TECHNICAL_DIR / "convert_csv_to_fst.R").exists():
        success, output = run_r_script("convert_csv_to_fst.R")
        results["fst_conversion"] = (success, output)
    else:
        log("FST conversion script not found, skipping", "WARNING")
        results["fst_conversion"] = (False, "Script not found")
    
    # Generate refresh report
    log("\nGenerating refresh report...")
    report_path = generate_refresh_report(results)
    
    # Summary
    log("\n" + "=" * 60)
    log("MONTHLY DATA REFRESH COMPLETE")
    log("=" * 60)
    log(f"Log file: {LOG_FILE}")
    log(f"Refresh report: {report_path}")
    
    successful_tasks = sum(1 for success, _ in results.values() if success)
    total_tasks = len(results)
    
    if successful_tasks == total_tasks:
        log("All tasks completed successfully!", "SUCCESS")
    else:
        log(f"{successful_tasks}/{total_tasks} tasks successful, review logs", "WARNING")


def schedule_monthly_update():
    """
    Schedule monthly updates.
    
    Note: This uses the 'schedule' library for demonstration.
    For production, use OS-level scheduling (Task Scheduler, cron).
    """
    try:
        import schedule
        import time
    except ImportError:
        log("'schedule' package not installed", "ERROR")
        log("Run: pip install schedule", "INFO")
        log("Alternatively, use Task Scheduler (Windows) or cron (Linux)", "INFO")
        return
    
    # Schedule for first Friday of each month at 10:00 AM
    # Note: schedule library doesn't have built-in "first Friday" support
    # This is a simplified version; use Task Scheduler for production
    
    schedule.every().friday.at("10:00").do(monthly_update)
    
    log("Monthly update scheduled for every Friday at 10:00 AM")
    log("(In production, configure Task Scheduler to run ONLY on first Friday)")
    log("\nPress Ctrl+C to stop scheduler...\n")
    
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="StarCruiser Monthly Data Refresh Pipeline")
    parser.add_argument(
        "--mode",
        choices=["once", "schedule"],
        default="once",
        help="Run once immediately or schedule for recurring execution"
    )
    
    args = parser.parse_args()
    
    if args.mode == "once":
        monthly_update()
    elif args.mode == "schedule":
        schedule_monthly_update()


if __name__ == "__main__":
    main()
