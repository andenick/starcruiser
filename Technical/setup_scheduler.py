"""
Windows Task Scheduler Setup - StarCruiser
============================================
Track C3.1: Create Windows Task Scheduler entries for automated data refresh.

Usage:
    python setup_scheduler.py [--create | --delete | --status]

Tasks created:
    1. Weekly (Thursday 10 AM): update_ui_claims.py
    2. Monthly (1st Friday 10 AM): monthly_data_refresh.py
    3. Weekly (Sunday 6 AM): data_quality_monitor.py
"""

import subprocess
import sys
from pathlib import Path
import argparse
import logging

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PYTHON = sys.executable
SCRIPT_DIR = (PROJECT_ROOT / "Technical")

TASKS = [
    {
        "name": "StarCruiser_Weekly_Claims",
        "description": "Download weekly unemployment insurance claims data from FRED",
        "script": SCRIPT_DIR / "update_ui_claims.py",
        "args": "",
        "schedule_args": "/sc WEEKLY /d THU /st 10:00",
    },
    {
        "name": "StarCruiser_Monthly_Refresh",
        "description": "Monthly data refresh for StarCruiser dashboard (runs on BLS jobs day)",
        "script": SCRIPT_DIR / "monthly_data_refresh.py",
        "args": "--mode once",
        "schedule_args": "/sc MONTHLY /mo FIRST /d FRI /st 10:00",
    },
    {
        "name": "StarCruiser_Quality_Monitor",
        "description": "Weekly data quality monitoring and anomaly detection",
        "script": SCRIPT_DIR / "data_quality_monitor.py",
        "args": "",
        "schedule_args": "/sc WEEKLY /d SUN /st 06:00",
    },
]


def create_tasks():
    """Create all scheduled tasks."""
    logger.info("Creating Windows Task Scheduler entries...")
    logger.info(f"Python executable: {PYTHON}")
    logger.info(f"Script directory: {SCRIPT_DIR}\n")

    for task in TASKS:
        name = task["name"]
        script = task["script"]
        args = task["args"]
        schedule = task["schedule_args"]

        if not script.exists():
            logger.warning(f"  SKIP: Script not found: {script}")
            continue

        tr_cmd = f'"{PYTHON}" "{script}"'
        if args:
            tr_cmd += f" {args}"

        cmd = f'schtasks /create /tn "{name}" /tr {tr_cmd} {schedule} /f'

        logger.info(f"Creating: {name}")
        logger.info(f"  Schedule: {schedule}")
        logger.info(f"  Command: {tr_cmd}")

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"  OK: Task created successfully")
            else:
                logger.error(f"  FAILED: {result.stderr.strip()}")
                if "Access is denied" in result.stderr:
                    logger.error("  TIP: Run as Administrator to create scheduled tasks.")
        except Exception as e:
            logger.error(f"  ERROR: {e}")

        print()


def delete_tasks():
    """Delete all StarCruiser scheduled tasks."""
    logger.info("Deleting StarCruiser scheduled tasks...\n")

    for task in TASKS:
        name = task["name"]
        cmd = f'schtasks /delete /tn "{name}" /f'

        logger.info(f"Deleting: {name}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"  OK: Deleted")
            else:
                logger.warning(f"  Not found or error: {result.stderr.strip()}")
        except Exception as e:
            logger.error(f"  ERROR: {e}")


def check_status():
    """Check status of all StarCruiser scheduled tasks."""
    logger.info("Checking StarCruiser scheduled tasks...\n")

    for task in TASKS:
        name = task["name"]
        cmd = f'schtasks /query /tn "{name}" /fo LIST /v'

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"FOUND: {name}")
                # Parse key fields
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if any(key in line for key in ['Status:', 'Next Run Time:', 'Last Run Time:', 'Last Result:']):
                        logger.info(f"  {line}")
            else:
                logger.info(f"NOT FOUND: {name}")
        except Exception as e:
            logger.error(f"  ERROR checking {name}: {e}")

        print()


def main():
    parser = argparse.ArgumentParser(description="StarCruiser Task Scheduler Setup")
    parser.add_argument("--create", action="store_true", help="Create scheduled tasks")
    parser.add_argument("--delete", action="store_true", help="Delete scheduled tasks")
    parser.add_argument("--status", action="store_true", help="Check task status")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("StarCruiser Task Scheduler Setup")
    logger.info("=" * 60 + "\n")

    if args.delete:
        delete_tasks()
    elif args.status:
        check_status()
    elif args.create:
        create_tasks()
    else:
        # Default: show status, then offer to create
        check_status()
        logger.info("\nTo create tasks: python setup_scheduler.py --create")
        logger.info("To delete tasks: python setup_scheduler.py --delete")
        logger.info("\nNote: Creating tasks may require running as Administrator.")


if __name__ == "__main__":
    main()
