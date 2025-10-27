#!/usr/bin/env python3
"""
GET ALL THE FUCKING DATA - EVERY SYMBOL, EVERY DATASET!
Runs ALL data ingestion scripts to get EVERYTHING
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
        ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {description}")
            if result.stdout:
                print(f"📊 Output: {result.stdout.strip()}")
        else:
            print(f"❌ ERROR: {description}")
            print(f"🔍 Error: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: {description} (10 minutes)")
        return False
    except Exception as e:
        print(f"💥 EXCEPTION: {description} - {e}")
        return False
    
    return True

def main():
    """Run ALL data ingestion - EVERY FUCKING DATASET!"""
    print("=" * 100)
    print("🚀 GET ALL THE FUCKING DATA - EVERY SYMBOL, EVERY DATASET!")
    print("=" * 100)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to ingestion directory
    os.chdir('cbi-v14-ingestion')
    
    # ALL INGESTION SCRIPTS - EVERY FUCKING ONE!
    all_scripts = [
        # HARVEST DATA
        {
            'script': 'ingest_usda_harvest_real.py',
            'description': 'USDA HARVEST DATA - ALL CROPS, ALL COUNTRIES'
        },
        {
            'script': 'ingest_conab_harvest.py',
            'description': 'CONAB BRAZIL HARVEST DATA'
        },
        
        # BIOFUEL DATA
        {
            'script': 'ingest_eia_biofuel_real.py',
            'description': 'EIA BIOFUEL PRODUCTION DATA'
        },
        {
            'script': 'ingest_staging_biofuel_policy.py',
            'description': 'BIOFUEL POLICY DATA - RFS MANDATES'
        },
        {
            'script': 'ingest_staging_biofuel_production.py',
            'description': 'BIOFUEL PRODUCTION DATA'
        },
        
        # ALL PRICE DATA - EVERY SYMBOL!
        {
            'script': 'backfill_prices_yf.py',
            'description': 'ALL YFINANCE PRICES - ZL, ZS, ZM, ZC, ZW, CT, CL, GC, SI, NG, SPY, TNX, IRX'
        },
        
        # SOCIAL INTELLIGENCE - ALL PLATFORMS!
        {
            'script': 'social_intelligence.py',
            'description': 'SOCIAL MEDIA INTELLIGENCE - FACEBOOK, TWITTER, REDDIT'
        },
        {
            'script': 'ice_trump_intelligence.py',
            'description': 'ICE ENFORCEMENT + TRUMP POLICY INTELLIGENCE'
        },
        
        # ECONOMIC DATA - ALL OF IT!
        {
            'script': 'economic_intelligence.py',
            'description': 'ECONOMIC INDICATORS - FED RATES, YIELDS, EMPLOYMENT'
        },
        
        # WEATHER DATA - ALL REGIONS!
        {
            'script': 'ingest_weather_noaa.py',
            'description': 'NOAA WEATHER DATA - US, BRAZIL, ARGENTINA'
        },
        
        # NEWS INTELLIGENCE - ALL SOURCES!
        {
            'script': 'multi_source_news.py',
            'description': 'MULTI-SOURCE NEWS INTELLIGENCE - ALL CATEGORIES'
        },
        
        # VOLATILITY DATA
        {
            'script': 'ingest_volatility.py',
            'description': 'VOLATILITY DATA - VIX, IV, HV RATIOS'
        },
        
        # CFTC DATA
        {
            'script': 'ingest_cftc_positioning_REAL.py',
            'description': 'CFTC POSITIONING DATA - ALL COMMODITIES'
        },
        
        # COMPREHENSIVE SOCIAL INTELLIGENCE
        {
            'script': 'ingest_social_intelligence_comprehensive.py',
            'description': 'COMPREHENSIVE SOCIAL INTELLIGENCE - ALL PLATFORMS'
        }
    ]
    
    success_count = 0
    total_scripts = len(all_scripts)
    
    print(f"\n🎯 RUNNING {total_scripts} DATA INGESTION SCRIPTS...")
    print("=" * 100)
    
    for i, script_info in enumerate(all_scripts, 1):
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
        time.sleep(3)
    
    # Final summary
    print("\n" + "=" * 100)
    print("📊 ALL DATA INGESTION COMPLETE!")
    print("=" * 100)
    print(f"✅ Successful: {success_count}/{total_scripts}")
    print(f"❌ Failed: {total_scripts - success_count}/{total_scripts}")
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == total_scripts:
        print("🎉 ALL FUCKING DATA INGESTED SUCCESSFULLY!")
        print("🚀 EVERY SYMBOL, EVERY DATASET, ALL OF IT!")
    else:
        print("⚠️  SOME INGESTION FAILED - CHECK LOGS ABOVE")
        print("🔍 BUT WE GOT MOST OF THE FUCKING DATA!")

if __name__ == "__main__":
    main()
