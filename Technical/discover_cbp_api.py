"""
Census CBP API Variable Discovery
==================================

Discover available variables for County Business Patterns API.
"""

import requests
import json
from pathlib import Path

import os

DATA_ROOT = Path(os.environ.get("DATA_ROOT", "data"))


# Load API key: prefer CENSUS_API_KEY env var (free key at
# https://api.census.gov/data/key_signup.html), else optional local admin JSON.
api_key = os.environ.get("CENSUS_API_KEY")
if not api_key:
    SOURCE_ADMIN = DATA_ROOT / "ADMIN/api-keys"
    api_keys_file = SOURCE_ADMIN / "[2025.09.28] api_keys.json"
    with open(api_keys_file, 'r') as f:
        keys = json.load(f)
        api_key = keys.get("census_api_key")

print(f"API key loaded: {api_key[:10]}...\n")

# Test different years to find working endpoint
test_years = [2021, 2020, 2019, 2017]

for year in test_years:
    print(f"{'='*60}")
    print(f"Testing CBP {year}")
    print("=" * 60)
    
    # Try to get variables list
    variables_url = f"https://api.census.gov/data/{year}/cbp/variables.json"
    
    try:
        response = requests.get(variables_url, timeout=10)
        
        if response.status_code == 200:
            variables = response.json()
            print(f"[SUCCESS] Found {len(variables.get('variables', {}))} variables\n")
            
            # Show interesting variables
            vars_dict = variables.get('variables', {})
            
            print("Key variables:")
            for var_name in ['NAME', 'EMP', 'ESTAB', 'PAYANN', 'NAICS2017', 'NAICS2012', 'county']:
                if var_name in vars_dict:
                    print(f"  ✓ {var_name}: {vars_dict[var_name].get('label', 'No description')}")
                else:
                    print(f"  ✗ {var_name}: NOT FOUND")
            
            print(f"\n[INFO] All variables saved to cbp_{year}_variables.json")
            with open(f"cbp_{year}_variables.json", "w") as f:
                json.dump(variables, f, indent=2)
            
            break  # Found working year, stop
        else:
            print(f"[FAIL] Status {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] {e}")
    
    print()

# Try a simple query with 2021 data
print(f"\n{'='*60}")
print("Testing simple query (2021, first 5 records)")
print("=" * 60)

test_url = f"https://api.census.gov/data/2021/cbp"
params = {
    "get": "NAME,EMP,ESTAB,NAICS2017",
    "for": "state:01",  # Alabama only
    "key": api_key
}

try:
    response = requests.get(test_url, params=params, timeout=10)
    print(f"URL: {response.url}\n")
    
    if response.status_code == 200:
        data = response.json()
        print(f"[SUCCESS] Got {len(data)-1} records")
        print(f"\nFirst 3 records:")
        for i, row in enumerate(data[:4]):
            print(f"  {i}: {row}")
    else:
        print(f"[FAIL] Status {response.status_code}")
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"[ERROR] {e}")
