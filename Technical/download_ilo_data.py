"""
ILO ILOSTAT Bulk Data Download - StarCruiser
=============================================
Track C1.2: Download ILO ILOSTAT bulk employment data for international comparisons.

Usage:
    python download_ilo_data.py

Output:
    Inputs/External/ILO/EMP_TEMP_SEX_AGE_NB.csv.gz  (Employment by sex and age)
    Inputs/External/ILO/UNE_TUNE_SEX_AGE_NB.csv.gz  (Unemployment by sex and age)
    Inputs/External/ILO/LAI_LFPR_SEX_AGE_RT.csv.gz   (Labor force participation rate)
"""

from pathlib import Path
from datetime import datetime
import requests
import gzip
import shutil
import logging
import json
import csv
import io

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = PROJECT_ROOT
ILO_DIR = BASE_DIR / "Inputs" / "External" / "ILO"
ILO_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = BASE_DIR / "Outputs" / "CATALOGS"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")

# ILO bulk data download base URL
ILO_BULK_URL = "https://www.ilo.org/ilostat-files/data/bulk/"

# Key employment datasets to download
DATASETS = {
    'EMP_TEMP_SEX_AGE_NB': {
        'description': 'Employment by sex and age (thousands)',
        'topic': 'Employment',
        'coverage': '189 countries, 1991-present',
    },
    'UNE_TUNE_SEX_AGE_NB': {
        'description': 'Unemployment by sex and age (thousands)',
        'topic': 'Unemployment',
        'coverage': '189 countries, 1991-present',
    },
    'LAI_LFPR_SEX_AGE_RT': {
        'description': 'Labour force participation rate by sex and age (%)',
        'topic': 'Labour Force',
        'coverage': '189 countries, 1990-present',
    },
    'EAR_4MTH_SEX_ECO_CUR_NB': {
        'description': 'Mean nominal monthly earnings by sex and economic activity',
        'topic': 'Earnings',
        'coverage': 'Selected countries',
    },
    'HOW_TEMP_SEX_ECO_NB': {
        'description': 'Mean weekly hours of work by sex and economic activity',
        'topic': 'Working Time',
        'coverage': 'Selected countries',
    },
}


def download_dataset(dataset_id, dataset_info):
    """Download a single ILO dataset."""
    url = f"{ILO_BULK_URL}{dataset_id}.csv.gz"
    output_gz = ILO_DIR / f"{dataset_id}.csv.gz"
    output_csv = ILO_DIR / f"[{TIMESTAMP}]_{dataset_id}.csv"

    logger.info(f"\nDownloading: {dataset_id}")
    logger.info(f"  Description: {dataset_info['description']}")
    logger.info(f"  URL: {url}")

    try:
        response = requests.get(url, timeout=180, stream=True)
        response.raise_for_status()

        # Save compressed file
        total_size = 0
        with open(output_gz, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                total_size += len(chunk)

        gz_size_mb = total_size / 1024 / 1024
        logger.info(f"  Downloaded: {gz_size_mb:.1f} MB (compressed)")

        # Decompress and save CSV
        logger.info("  Decompressing...")
        record_count = 0
        columns = None

        with gzip.open(output_gz, 'rt', encoding='utf-8', errors='replace') as gz_in:
            with open(output_csv, 'w', newline='', encoding='utf-8') as csv_out:
                for line in gz_in:
                    csv_out.write(line)
                    record_count += 1
                    if record_count == 1:
                        columns = line.strip().split(',')

        record_count -= 1  # Subtract header
        csv_size_mb = output_csv.stat().st_size / 1024 / 1024
        logger.info(f"  Decompressed: {csv_size_mb:.1f} MB | {record_count:,} records")

        if columns:
            logger.info(f"  Columns: {', '.join(columns[:8])}{'...' if len(columns) > 8 else ''}")

        # Clean up compressed file
        output_gz.unlink()

        return {
            'dataset_id': dataset_id,
            'description': dataset_info['description'],
            'topic': dataset_info['topic'],
            'file': output_csv.name,
            'size_mb': round(csv_size_mb, 1),
            'records': record_count,
            'columns': len(columns) if columns else 0,
            'status': 'OK',
        }

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"  NOT FOUND (404): Dataset may have been renamed or removed")
        else:
            logger.error(f"  HTTP Error: {e}")

        # Clean up partial downloads
        if output_gz.exists():
            output_gz.unlink()

        return {
            'dataset_id': dataset_id,
            'description': dataset_info['description'],
            'topic': dataset_info['topic'],
            'file': None,
            'size_mb': 0,
            'records': 0,
            'columns': 0,
            'status': f'FAILED: {e}',
        }

    except Exception as e:
        logger.error(f"  Error: {e}")
        if output_gz.exists():
            output_gz.unlink()

        return {
            'dataset_id': dataset_id,
            'description': dataset_info['description'],
            'topic': dataset_info['topic'],
            'file': None,
            'size_mb': 0,
            'records': 0,
            'columns': 0,
            'status': f'ERROR: {e}',
        }


def validate_us_data(csv_path, dataset_id):
    """Quick validation: check US data exists and looks reasonable."""
    try:
        import pandas as pd
        df = pd.read_csv(csv_path, nrows=100000)

        # Find country/reference area column
        ref_col = None
        for col in df.columns:
            if 'ref_area' in col.lower() or 'country' in col.lower():
                ref_col = col
                break

        if ref_col is None:
            return "No country column found"

        us_data = df[df[ref_col] == 'USA']
        if len(us_data) == 0:
            us_data = df[df[ref_col].str.contains('US', na=False)]

        if len(us_data) > 0:
            return f"US data found: {len(us_data)} records in sample"
        else:
            return "No US data in first 100K records"

    except Exception as e:
        return f"Validation error: {e}"


def main():
    logger.info("=" * 60)
    logger.info("StarCruiser ILO ILOSTAT Bulk Data Download")
    logger.info("=" * 60)
    logger.info(f"Output directory: {ILO_DIR}")
    logger.info(f"Datasets to download: {len(DATASETS)}\n")

    results = []

    for dataset_id, dataset_info in DATASETS.items():
        result = download_dataset(dataset_id, dataset_info)
        results.append(result)

        # Brief validation for successful downloads
        if result['status'] == 'OK' and result['file']:
            csv_path = ILO_DIR / result['file']
            validation = validate_us_data(csv_path, dataset_id)
            logger.info(f"  Validation: {validation}")
            result['validation'] = validation

    # Summary
    logger.info(f"\n{'=' * 60}")
    logger.info("Download Summary")
    logger.info(f"{'=' * 60}")

    total_records = sum(r['records'] for r in results)
    total_size = sum(r['size_mb'] for r in results)
    successful = sum(1 for r in results if r['status'] == 'OK')

    for r in results:
        status_icon = "OK" if r['status'] == 'OK' else "FAIL"
        logger.info(f"  [{status_icon}] {r['dataset_id']}: {r['records']:,} records ({r['size_mb']:.1f} MB)")

    logger.info(f"\nTotal: {successful}/{len(results)} successful")
    logger.info(f"Total records: {total_records:,}")
    logger.info(f"Total size: {total_size:.1f} MB")

    # Save download report
    report = {
        'timestamp': TIMESTAMP,
        'source': 'ILO ILOSTAT',
        'base_url': ILO_BULK_URL,
        'datasets': results,
        'total_records': total_records,
        'total_size_mb': round(total_size, 1),
        'successful': successful,
        'total': len(results),
    }

    report_file = ILO_DIR / f"[{TIMESTAMP}]_download_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"\nReport saved to: {report_file}")

    # Update catalog index
    catalog_file = OUTPUT_DIR / "ILO_DATA_INDEX.csv"
    with open(catalog_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'dataset_id', 'description', 'topic', 'file',
            'size_mb', 'records', 'columns', 'status'
        ])
        writer.writeheader()
        writer.writerows(results)
    logger.info(f"Catalog saved to: {catalog_file}")


if __name__ == "__main__":
    main()
