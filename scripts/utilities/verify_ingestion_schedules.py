#!/usr/bin/env python3
"""
COMPREHENSIVE INGESTION SCHEDULE VERIFICATION
Checks cron jobs, tests ingestion scripts, and verifies data freshness
"""

import subprocess
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
INGESTION_DIR = ROOT_DIR / "src" / "ingestion"
SCRIPTS_DIR = ROOT_DIR / "scripts"

def print_header(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def check_cron_jobs():
    """Check if cron jobs are set up"""
    print_header("CHECKING CRON JOBS")
    
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            cron_content = result.stdout
            cbi_jobs = [line for line in cron_content.split('\n') 
                       if 'CBI-V14' in line or 'ingestion' in line.lower() or 
                       any(script in line for script in ['ingest_', 'collector', 'intelligence'])]
            
            if cbi_jobs:
                print("✅ Found CBI-V14 cron jobs:")
                for job in cbi_jobs:
                    if job.strip() and not job.strip().startswith('#'):
                        print(f"   {job.strip()}")
                return True
            else:
                print("❌ No CBI-V14 cron jobs found")
                print("   Current crontab exists but no CBI-V14 jobs scheduled")
                return False
        else:
            print("❌ No crontab configured")
            print("   Run: src/ingestion/setup_daily_cron.sh")
            return False
            
    except Exception as e:
        print(f"❌ Error checking cron: {e}")
        return False

def test_ingestion_script(script_name):
    """Test a single ingestion script"""
    script_path = INGESTION_DIR / script_name
    
    if not script_path.exists():
        return {'status': 'NOT_FOUND', 'error': f'Script not found: {script_name}'}
    
    print(f"\n⏳ Testing {script_name}...")
    start_time = datetime.now()
    
    try:
        result = subprocess.run(
            ["python3", str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(ROOT_DIR)
        )
        
        runtime = (datetime.now() - start_time).total_seconds()
        
        if result.returncode == 0:
            output_preview = result.stdout[:200] if result.stdout else "No output"
            return {
                'status': 'SUCCESS',
                'runtime': runtime,
                'output': output_preview
            }
        else:
            error_preview = result.stderr[:300] if result.stderr else result.stdout[:300]
            return {
                'status': 'FAILED',
                'runtime': runtime,
                'error': error_preview,
                'returncode': result.returncode
            }
    except subprocess.TimeoutExpired:
        return {
            'status': 'TIMEOUT',
            'error': 'Script exceeded 5 minute timeout'
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'error': str(e)
        }

def check_stale_data_sources():
    """Run the stale data check script"""
    print_header("CHECKING DATA FRESHNESS")
    
    stale_check_script = SCRIPTS_DIR / "check_stale_data.py"
    
    if not stale_check_script.exists():
        print("⚠️  Stale data check script not found")
        return False
    
    try:
        result = subprocess.run(
            ["python3", str(stale_check_script)],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR)
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("\n✅ All data sources are fresh")
            return True
        else:
            print("\n❌ Stale data detected - see details above")
            return False
            
    except Exception as e:
        print(f"❌ Error running stale data check: {e}")
        return False

def main():
    print("="*80)
    print("  CBI-V14 INGESTION SCHEDULE VERIFICATION")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project Root: {ROOT_DIR}")
    print(f"Ingestion Dir: {INGESTION_DIR}")
    
    # Check cron jobs
    cron_ok = check_cron_jobs()
    
    # Test critical ingestion scripts from audit
    print_header("TESTING CRITICAL INGESTION SCRIPTS")
    
    critical_scripts = [
        "ingest_epa_rin_prices.py",      # Biofuel prices (29 days stale)
        "ingest_volatility.py",           # VIX (22 days stale)
        "ingest_cftc_positioning_REAL.py", # CFTC (low data)
        "ingest_baltic_dry_index.py",     # Baltic Dry Index
    ]
    
    results = {}
    for script in critical_scripts:
        results[script] = test_ingestion_script(script)
    
    # Print results
    print_header("TEST RESULTS SUMMARY")
    
    success_count = 0
    for script, result in results.items():
        status = result.get('status', 'UNKNOWN')
        if status == 'SUCCESS':
            print(f"✅ {script}: SUCCESS ({result.get('runtime', 0):.1f}s)")
            success_count += 1
        elif status == 'NOT_FOUND':
            print(f"⚠️  {script}: NOT FOUND")
        elif status == 'TIMEOUT':
            print(f"⏱️  {script}: TIMEOUT (>5 min)")
        else:
            error = result.get('error', 'Unknown error')[:100]
            print(f"❌ {script}: FAILED - {error}")
    
    print(f"\n📊 Results: {success_count}/{len(critical_scripts)} scripts succeeded")
    
    # Check data freshness
    data_fresh = check_stale_data_sources()
    
    # Final summary
    print_header("VERIFICATION SUMMARY")
    
    print(f"Cron Jobs: {'✅ Configured' if cron_ok else '❌ Not configured'}")
    print(f"Script Tests: {success_count}/{len(critical_scripts)} passed")
    print(f"Data Freshness: {'✅ Fresh' if data_fresh else '❌ Stale data detected'}")
    
    if not cron_ok:
        print("\n⚠️  ACTION REQUIRED: Set up cron jobs")
        print(f"   Run: {INGESTION_DIR}/setup_daily_cron.sh")
        print("   Note: Update paths in setup script first!")
    
    if success_count < len(critical_scripts):
        print("\n⚠️  ACTION REQUIRED: Fix failed ingestion scripts")
    
    if not data_fresh:
        print("\n⚠️  ACTION REQUIRED: Run ingestion scripts to update stale data")
        print("   Priority scripts from audit:")
        print("   - python3 src/ingestion/ingest_epa_rin_prices.py")
        print("   - python3 src/ingestion/ingest_volatility.py")
        print("   - python3 src/ingestion/ingest_cftc_positioning_REAL.py")
    
    if cron_ok and success_count == len(critical_scripts) and data_fresh:
        print("\n🎉 ALL CHECKS PASSED - System is healthy!")
        return 0
    else:
        print("\n❌ ISSUES DETECTED - Review above and take action")
        return 1

if __name__ == "__main__":
    sys.exit(main())

