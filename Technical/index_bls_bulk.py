"""
BLS Bulk Data Index - StarCruiser
==================================
Track C1.1: Scan BLS FTP bulk data directories, count series and records,
create comprehensive inventory.

Usage:
    python index_bls_bulk.py

Output:
    Outputs/CATALOGS/BLS_BULK_INDEX.csv
"""

from pathlib import Path
from datetime import datetime
import csv
import logging
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = PROJECT_ROOT
BLS_FTP_DIR = BASE_DIR / "Inputs" / "External" / "BLS_FTP"
OUTPUT_DIR = BASE_DIR / "Outputs" / "CATALOGS"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")

# BLS category descriptions
BLS_CATEGORIES = {
    'CE': 'Current Employment Statistics (National)',
    'SM': 'State & Metro Area Employment',
    'LA': 'Local Area Unemployment Statistics',
    'LN': 'Labor Force Statistics (CPS)',
    'OE': 'Occupational Employment & Wages',
    'JT': 'Job Openings & Labor Turnover (JOLTS)',
    'BD': 'Business Employment Dynamics',
    'CW': 'County Employment & Wages (QCEW)',
    'AP': 'Average Price Data',
    'CU': 'Consumer Price Index (All Urban)',
    'WP': 'Producer Price Index',
    'EI': 'Employment Cost Index',
}


def analyze_data_file(file_path):
    """Analyze a BLS data file and return statistics."""
    stats = {
        'file': file_path.name,
        'size_mb': file_path.stat().st_size / 1024 / 1024,
        'records': 0,
        'series_count': 0,
        'date_range_start': None,
        'date_range_end': None,
    }

    try:
        series_ids = set()
        min_year = 9999
        max_year = 0
        line_count = 0

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            header = f.readline()  # Skip header

            for line in f:
                line_count += 1
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    series_ids.add(parts[0].strip())
                    try:
                        year = int(parts[1].strip())
                        if year < min_year:
                            min_year = year
                        if year > max_year:
                            max_year = year
                    except (ValueError, IndexError):
                        pass

        stats['records'] = line_count
        stats['series_count'] = len(series_ids)
        stats['date_range_start'] = min_year if min_year != 9999 else None
        stats['date_range_end'] = max_year if max_year != 0 else None

    except Exception as e:
        logger.warning(f"  Error analyzing {file_path.name}: {e}")

    return stats


def analyze_csv_file(file_path):
    """Analyze a CSV data file."""
    stats = {
        'file': file_path.name,
        'size_mb': file_path.stat().st_size / 1024 / 1024,
        'records': 0,
        'series_count': 0,
        'date_range_start': None,
        'date_range_end': None,
    }

    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                return stats

            line_count = sum(1 for _ in reader)
            stats['records'] = line_count

    except Exception as e:
        logger.warning(f"  Error analyzing {file_path.name}: {e}")

    return stats


def main():
    logger.info("=" * 60)
    logger.info("StarCruiser BLS Bulk Data Index")
    logger.info("=" * 60)

    if not BLS_FTP_DIR.exists():
        logger.warning(f"BLS FTP directory not found: {BLS_FTP_DIR}")
        logger.info("Creating empty index...")
        BLS_FTP_DIR.mkdir(parents=True, exist_ok=True)

    # Scan all subdirectories
    results = []
    total_records = 0
    total_series = 0
    total_size = 0

    # Check top-level categories
    categories_found = []
    for category_dir in sorted(BLS_FTP_DIR.iterdir()):
        if not category_dir.is_dir():
            continue

        category = category_dir.name
        category_desc = BLS_CATEGORIES.get(category, f"Unknown ({category})")
        categories_found.append(category)

        logger.info(f"\nScanning category: {category} - {category_desc}")

        # Find data files
        data_files = list(category_dir.glob("*.data.*")) + \
                     list(category_dir.glob("*.csv")) + \
                     list(category_dir.glob("*.txt"))

        if not data_files:
            logger.info(f"  No data files found in {category_dir}")
            results.append({
                'category': category,
                'category_description': category_desc,
                'file': '(empty)',
                'file_type': 'N/A',
                'size_mb': 0,
                'records': 0,
                'series_count': 0,
                'date_range_start': None,
                'date_range_end': None,
            })
            continue

        # Analyze each data file
        for data_file in sorted(data_files):
            logger.info(f"  Analyzing: {data_file.name} ({data_file.stat().st_size / 1024 / 1024:.1f} MB)")

            # Determine file type
            if data_file.suffix == '.csv':
                stats = analyze_csv_file(data_file)
                file_type = 'CSV'
            else:
                stats = analyze_data_file(data_file)
                file_type = 'BLS Tab-delimited'

            result = {
                'category': category,
                'category_description': category_desc,
                'file': stats['file'],
                'file_type': file_type,
                'size_mb': round(stats['size_mb'], 2),
                'records': stats['records'],
                'series_count': stats['series_count'],
                'date_range_start': stats['date_range_start'],
                'date_range_end': stats['date_range_end'],
            }
            results.append(result)

            total_records += stats['records']
            total_series += stats['series_count']
            total_size += stats['size_mb']

            if stats['records'] > 0:
                logger.info(f"    Records: {stats['records']:,} | Series: {stats['series_count']:,} | "
                          f"Years: {stats['date_range_start']}-{stats['date_range_end']}")

    # Also scan other external data directories
    for ext_dir in ['NBER', 'INDEED', 'ADP', 'OECD', 'ILO', 'IMF', 'QCEW']:
        ext_path = BASE_DIR / "Inputs" / "External" / ext_dir
        if ext_path.exists():
            files = list(ext_path.glob("*.csv"))
            if files:
                for f in files:
                    size_mb = f.stat().st_size / 1024 / 1024
                    results.append({
                        'category': ext_dir,
                        'category_description': f"External: {ext_dir}",
                        'file': f.name,
                        'file_type': 'CSV',
                        'size_mb': round(size_mb, 2),
                        'records': 0,  # Don't parse all external files
                        'series_count': 0,
                        'date_range_start': None,
                        'date_range_end': None,
                    })
                    total_size += size_mb

    # Write index CSV
    index_file = OUTPUT_DIR / f"BLS_BULK_INDEX.csv"
    with open(index_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'category', 'category_description', 'file', 'file_type',
            'size_mb', 'records', 'series_count',
            'date_range_start', 'date_range_end'
        ])
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"\n{'=' * 60}")
    logger.info("Summary")
    logger.info(f"{'=' * 60}")
    logger.info(f"Categories scanned: {len(categories_found)} ({', '.join(categories_found)})")
    logger.info(f"Total data files: {len(results)}")
    logger.info(f"Total records: {total_records:,}")
    logger.info(f"Total series: {total_series:,}")
    logger.info(f"Total size: {total_size:.1f} MB")
    logger.info(f"\nIndex saved to: {index_file}")

    # Save metadata
    metadata = {
        'timestamp': TIMESTAMP,
        'bls_ftp_dir': str(BLS_FTP_DIR),
        'categories_found': categories_found,
        'total_records': total_records,
        'total_series': total_series,
        'total_size_mb': round(total_size, 1),
        'total_files': len(results),
    }
    meta_file = OUTPUT_DIR / "bls_bulk_metadata.json"
    with open(meta_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved to: {meta_file}")


if __name__ == "__main__":
    main()
