"""
Quick Census Data Explorer
===========================

Examine Census CBP data structure to understand what we're working with.
"""

import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Paths
CENSUS_DIR = (PROJECT_ROOT / "Inputs/source/CENSUS")

# List all CSV files
csv_files = list(CENSUS_DIR.glob("*.csv"))

print(f"Found {len(csv_files)} CSV files:\n")

for f in csv_files:
    size_mb = f.stat().st_size / (1024 * 1024)
    print(f"  {f.name} ({size_mb:.2f} MB)")

print("\n" + "="*80)
print("Examining first file...")
print("="*80 + "\n")

# Load first file
df = pd.read_csv(csv_files[0], nrows=5)

print(f"File: {csv_files[0].name}")
print(f"Columns ({len(df.columns)}): {list(df.columns)}")
print(f"\nFirst 3 rows:\n")
print(df.head(3).to_string())

# Count total rows
row_count = pd.read_csv(csv_files[0], usecols=[0]).shape[0]
print(f"\nTotal rows: {row_count:,}")
