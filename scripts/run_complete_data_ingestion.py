#!/usr/bin/env python3
"""
COMPLETE DATA INGESTION SCRIPT FOR CBI-V14
Runs all missing data ingestion cheaply and efficiently
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def run_script(script_path, description):
    """Run a data ingestion script with error handling"""
    print(f"\n🚀 RUNNING: {description}")
    print(f"📁 Script: {script_path}")
    
    try:
        result = subprocess.run([
            'python3', script_path
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {description}")
            if result.stdout:
                print(f"📊 Output: {result.stdout.strip()}")
        else:
            print(f"❌ ERROR: {description}")
            print(f"🔍 Error: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: {description} (5 minutes)")
        return False
    except Exception as e:
        print(f"💥 EXCEPTION: {description} - {e}")
        return False
    
    return True

def main():
    """Run complete data ingestion pipeline"""
    print("=" * 80)
    print("🚀 CBI-V14 COMPLETE DATA INGESTION")
    print("=" * 80)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to ingestion directory
    os.chdir('cbi-v14-ingestion')
    
    # Define ingestion scripts in priority order
    ingestion_scripts = [
        # CRITICAL MISSING DATA
        {
            'script': 'ingest_usda_harvest_real.py',
            'description': 'USDA Harvest Progress Data (CRITICAL - 0 rows)'
        },
        {
            'script': 'ingest_eia_biofuel_real.py', 
            'description': 'EIA Biofuel Production Data (CRITICAL - 0 rows)'
        },
        {
            'script': 'ingest_staging_biofuel_policy.py',
            'description': 'Biofuel Policy Data (CRITICAL - 0 rows)'
        },
        
        # PRICE DATA BACKFILL
        {
            'script': 'backfill_prices_yf.py',
            'description': 'YFinance Price Data Backfill (Crude Oil, USD Index)'
        },
        
        # SOCIAL INTELLIGENCE
        {
            'script': 'social_intelligence.py',
            'description': 'Social Media Intelligence (22 rows → 1000+)'
        },
        
        # WEATHER DATA
        {
            'script': 'ingest_weather_noaa.py',
            'description': 'NOAA Weather Data Enhancement'
        },
        
        # ECONOMIC DATA
        {
            'script': 'economic_intelligence.py',
            'description': 'Economic Indicators Enhancement'
        },
        
        # NEWS INTELLIGENCE
        {
            'script': 'multi_source_news.py',
            'description': 'Multi-Source News Intelligence'
        }
    ]
    
    success_count = 0
    total_scripts = len(ingestion_scripts)
    
    for i, script_info in enumerate(ingestion_scripts, 1):
        print(f"\n📊 PROGRESS: {i}/{total_scripts}")
        
        script_path = script_info['script']
        description = script_info['description']
        
        # Check if script exists
        if not os.path.exists(script_path):
            print(f"⚠️  SKIP: {script_path} not found")
            continue
            
        # Run the script
        success = run_script(script_path, description)
        if success:
            success_count += 1
        
        # Small delay between scripts
        time.sleep(2)
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 INGESTION COMPLETE")
    print("=" * 80)
    print(f"✅ Successful: {success_count}/{total_scripts}")
    print(f"❌ Failed: {total_scripts - success_count}/{total_scripts}")
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == total_scripts:
        print("🎉 ALL DATA INGESTION SUCCESSFUL!")
    else:
        print("⚠️  SOME INGESTION FAILED - CHECK LOGS ABOVE")

if __name__ == "__main__":
    main()
