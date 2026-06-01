"""
Census API Key Setup Script for StarCruiser
============================================

Purpose: Retrieve and configure Census API key from the source store repository
Author: Claude Sonnet 4
Created: December 5, 2025

This script checks for existing Census API configuration in the source store's API modules
and helps set up the API key for geographic data analysis.

Usage:
    python setup_census_api.py
"""

from pathlib import Path
import os
import shutil
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "data"))


# Directories
BASE_DIR = PROJECT_ROOT
SOURCE_API = DATA_ROOT / "api"
SOURCE_ENV = SOURCE_API / ".env"
SOURCE_ENV_EXAMPLE = SOURCE_API / ".env.example"
PROJECT_ENV = BASE_DIR / ".env"

def check_robin_census_key():
    """Check if the source store has Census API key configured"""
    print("=" * 70)
    print("CENSUS API KEY SETUP - StarCruiser Geographic Analysis")
    print("=" * 70)
    print()
    
    # Check for the source store .env file
    if SOURCE_ENV.exists():
        print("[FOUND] the source store .env file exists at:")
        print(f"        {SOURCE_ENV}")
        print()
        
        # Read and check for Census key
        with open(SOURCE_ENV, 'r') as f:
            env_content = f.read()
        
        if "CENSUS_API_KEY" in env_content:
            # Extract key (safely, without exposing it fully)
            for line in env_content.split('\n'):
                if line.startswith("CENSUS_API_KEY="):
                    key_value = line.split("=", 1)[1].strip()
                    if key_value and key_value != "your_census_api_key":
                        key_preview = key_value[:8] + "..." if len(key_value) > 8 else "[PRESENT]"
                        print(f"[SUCCESS] Census API key found: {key_preview}")
                        print()
                        return key_value, True
                    else:
                        print("[WARNING] Census API key placeholder found, not configured")
                        print()
                        return None, False
        else:
            print("[WARNING] No CENSUS_API_KEY in the source store .env file")
            print()
            return None, False
    else:
        print("[NOT FOUND] the source store .env file does not exist")
        print(f"             Expected at: {SOURCE_ENV}")
        print()
        return None, False

def check_example_template():
    """Check .env.example template"""
    if SOURCE_ENV_EXAMPLE.exists():
        print("[FOUND] the source store .env.example template:")
        print()
        with open(SOURCE_ENV_EXAMPLE, 'r') as f:
            for line in f:
                if "CENSUS" in line:
                    print(f"        {line.strip()}")
        print()
        return True
    else:
        print("[NOT FOUND] the source store .env.example template")
        print()
        return False

def create_project_env(census_key):
    """Create project-specific .env file with Census key"""
    print("Creating StarCruiser .env file...")
    
    env_content = f"""# StarCruiser Geographic Analysis - Environment Variables
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Census API Configuration
CENSUS_API_KEY={census_key}
CENSUS_BASE_URL=https://api.census.gov/data

# Data Sources
FRED_API_KEY=
BLS_API_KEY=

# Project Settings
PROJECT_NAME=StarCruiser
DATA_REFRESH_INTERVAL=monthly
"""
    
    with open(PROJECT_ENV, 'w') as f:
        f.write(env_content)
    
    print(f"[CREATED] {PROJECT_ENV}")
    print()

def provide_instructions():
    """Provide instructions for obtaining Census API key"""
    print("=" * 70)
    print("HOW TO OBTAIN CENSUS API KEY")
    print("=" * 70)
    print()
    print("The Census Bureau provides free API keys for accessing their data.")
    print()
    print("Steps to obtain your key:")
    print()
    print("1. Visit: https://api.census.gov/data/key_signup.html")
    print()
    print("2. Fill out the registration form:")
    print("   - Organization: Personal / Academic / Research")
    print("   - Email: Your email address")
    print()
    print("3. Check your email for the API key (arrives within minutes)")
    print()
    print("4. Once received, add the key to the source store's .env file:")
    print(f"   Location: {SOURCE_ENV}")
    print("   Format: CENSUS_API_KEY=your_actual_key_here")
    print()
    print("5. Run this script again to configure StarCruiser")
    print()
    print("=" * 70)
    print()

def main():
    """Main execution"""
    # Check for existing key in the source store
    census_key, key_found = check_robin_census_key()
    
    # Check for example template
    example_exists = check_example_template()
    
    if key_found and census_key:
        # Key found, configure project
        print("=" * 70)
        print("CONFIGURING STARCRUISER")
        print("=" * 70)
        print()
        
        # Copy key to project
        create_project_env(census_key)
        
        print("[SUCCESS] Census API key configured for StarCruiser!")
        print()
        print("Next Steps:")
        print("  1. Test API connection with: python test_census_api.py")
        print("  2. Download geographic data")
        print("  3. Begin county-level analysis")
        print()
        print("=" * 70)
        
    elif example_exists and not key_found:
        # Template exists but no key configured
        print("=" * 70)
        print("ACTION REQUIRED")
        print("=" * 70)
        print()
        print("Census API key not found in the source store configuration.")
        print()
        
        # Check if user wants instructions
        print("OPTIONS:")
        print()
        print("  A. I already have a Census API key (enter it now)")
        print("  B. I need to obtain a Census API key (show instructions)")
        print("  C. Use existing Census data only (no API access)")
        print()
        
        choice = input("Select option (A/B/C): ").strip().upper()
        print()
        
        if choice == 'A':
            print("Enter your Census API key:")
            user_key = input("Key: ").strip()
            
            if user_key and len(user_key) > 20:
                # Create the source store .env if needed
                if not SOURCE_ENV.exists():
                    print(f"Creating the source store .env file: {SOURCE_ENV}")
                    with open(SOURCE_ENV_EXAMPLE, 'r') as f:
                        template = f.read()
                    with open(SOURCE_ENV, 'w') as f:
                        f.write(template.replace("your_census_api_key", user_key))
                    print("[CREATED]")
                    print()
                
                # Create project .env
                create_project_env(user_key)
                
                print("[SUCCESS] Census API key configured!")
                print()
                print("Test with: python test_census_api.py")
                print()
            else:
                print("[ERROR] Invalid API key format (too short)")
                print()
        
        elif choice == 'B':
            provide_instructions()
        
        elif choice == 'C':
            print("=" * 70)
            print("USING EXISTING CENSUS DATA")
            print("=" * 70)
            print()
            print("You can continue with existing Census County Business Patterns data:")
            print()
            print(f"  Location: {BASE_DIR}/Inputs/source/CENSUS/")
            print("  Files: 5 CSV files (34.91 MB)")
            print("  Coverage: 1986-2024, 346K records")
            print()
            print("Note: Without API access, you cannot:")
            print("  - Download updated data")
            print("  - Access additional geographic levels")
            print("  - Use real-time data refresh")
            print()
            print("You CAN still:")
            print("  - Analyze existing county data")
            print("  - Build geographic hierarchies")
            print("  - Calculate dispersion metrics")
            print("  - Create interactive dashboards")
            print()
        
        else:
            print("[CANCELLED] Setup cancelled")
            print()
    
    else:
        # No template, no key
        print("=" * 70)
        print("ROBIN API CONFIGURATION MISSING")
        print("=" * 70)
        print()
        print("the source store's API configuration files are not properly set up.")
        print()
        print("Recommendations:")
        print("  1. Check the source store documentation for API setup")
        print("  2. Use existing Census data in Inputs/source/CENSUS/")
        print("  3. Manually configure Census API if needed")
        print()

if __name__ == "__main__":
    main()
