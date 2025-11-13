#!/usr/bin/env python3
"""
Critical Data Gaps Backfill Runner
===================================
Runs all three critical backfill scripts:
1. CFTC COT (2006-2025)
2. China Soybean Imports (2017-2025)
3. Baltic Dry Index (Historical)
"""

import subprocess
import sys
import os
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

def run_backfill_script(script_name: str, description: str, args: list = None) -> dict:
    """Run a backfill script and return results"""
    script_path = os.path.join(SCRIPT_DIR, script_name)
    
    if not os.path.exists(script_path):
        logger.error(f"❌ Script not found: {script_path}")
        return {
            'status': 'SCRIPT_NOT_FOUND',
            'script': script_name
        }
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Running: {description}")
    logger.info(f"Script: {script_name}")
    logger.info(f"{'='*60}")
    
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per script
        )
        
        if result.returncode == 0:
            try:
                output_data = json.loads(result.stdout)
                logger.info(f"✅ {description} completed successfully")
                return {
                    'status': 'SUCCESS',
                    'script': script_name,
                    'output': output_data
                }
            except json.JSONDecodeError:
                logger.warning(f"⚠️  {description} completed but output not JSON")
                return {
                    'status': 'SUCCESS_NO_JSON',
                    'script': script_name,
                    'stdout': result.stdout[:500]  # First 500 chars
                }
        else:
            logger.error(f"❌ {description} failed with return code {result.returncode}")
            logger.error(f"Error output: {result.stderr[:500]}")
            return {
                'status': 'FAILED',
                'script': script_name,
                'returncode': result.returncode,
                'stderr': result.stderr[:500]
            }
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {description} timed out after 1 hour")
        return {
            'status': 'TIMEOUT',
            'script': script_name
        }
    except Exception as e:
        logger.error(f"❌ Error running {description}: {e}")
        return {
            'status': 'ERROR',
            'script': script_name,
            'error': str(e)
        }


def main():
    """Run all critical backfill scripts"""
    logger.info("🚀 Starting Critical Data Gaps Backfill")
    logger.info(f"Repository: {REPO_ROOT}")
    logger.info(f"Started: {datetime.now().isoformat()}")
    
    results = {}
    
    # 1. CFTC COT Backfill (2006-2025)
    logger.info("\n" + "="*60)
    logger.info("CRITICAL GAP #1: CFTC COT (2006-2025)")
    logger.info("="*60)
    results['cftc_cot'] = run_backfill_script(
        'backfill_cftc_cot_historical.py',
        'CFTC COT Historical Backfill',
        ['2006', '2025']
    )
    
    # 2. China Soybean Imports Backfill (2017-2025)
    logger.info("\n" + "="*60)
    logger.info("CRITICAL GAP #2: China Soybean Imports (2017-2025)")
    logger.info("="*60)
    results['china_imports'] = run_backfill_script(
        'backfill_china_imports_historical.py',
        'China Soybean Imports Historical Backfill',
        ['2017', '2025']
    )
    
    # 3. Baltic Dry Index Backfill
    logger.info("\n" + "="*60)
    logger.info("CRITICAL GAP #3: Baltic Dry Index (Historical)")
    logger.info("="*60)
    results['baltic_dry_index'] = run_backfill_script(
        'backfill_baltic_dry_index_historical.py',
        'Baltic Dry Index Historical Backfill',
        ['2006', '2025', 'true']  # Use estimates if real data unavailable
    )
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("BACKFILL SUMMARY")
    logger.info("="*60)
    
    total_success = sum(1 for r in results.values() if r.get('status') == 'SUCCESS')
    total_failed = sum(1 for r in results.values() if r.get('status') in ['FAILED', 'ERROR', 'TIMEOUT'])
    
    for name, result in results.items():
        status = result.get('status', 'UNKNOWN')
        status_icon = '✅' if status == 'SUCCESS' else '❌' if status in ['FAILED', 'ERROR', 'TIMEOUT'] else '⚠️'
        logger.info(f"{status_icon} {name}: {status}")
        
        if 'output' in result and isinstance(result['output'], dict):
            rows = result['output'].get('total_rows_loaded', result['output'].get('rows_loaded', 0))
            if rows > 0:
                logger.info(f"   Rows loaded: {rows}")
    
    logger.info(f"\nTotal successful: {total_success}/3")
    logger.info(f"Total failed: {total_failed}/3")
    
    # Save results to file
    results_file = os.path.join(REPO_ROOT, 'Logs', 'backfill_results.json')
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'summary': {
                'total_success': total_success,
                'total_failed': total_failed
            }
        }, f, indent=2)
    
    logger.info(f"\n📄 Results saved to: {results_file}")
    logger.info(f"✅ Backfill process completed: {datetime.now().isoformat()}")
    
    # Exit with error code if any failed
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == '__main__':
    main()

