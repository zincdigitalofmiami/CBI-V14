#!/usr/bin/env python3
"""
CBI-V14 Enhanced Data Pipeline - SAFE TEST RUN
Test the enhanced data pipeline before enabling automation
"""

import os
import sys
sys.path.append('/Users/zincdigital/CBI-V14/cbi-v14-ingestion')

from enhanced_data_pipeline import bidaily_data_collection, logger
from datetime import datetime

def main():
    """Run a safe test of the enhanced data pipeline"""
    
    print("=" * 80)
    print("CBI-V14 ENHANCED DATA PIPELINE - SAFE TEST RUN")
    print("=" * 80)
    print(f"Started at: {datetime.now()}")
    print()
    
    print("🔒 SAFETY FEATURES ENABLED:")
    print("  ✅ Strict duplicate detection")
    print("  ✅ Placeholder value rejection (0.5 detection)")
    print("  ✅ Range validation for all data types")
    print("  ✅ Recent data only (no historical corruption)")
    print("  ✅ Comprehensive validation before storage")
    print()
    
    print("📊 DATA SOURCES TO TEST:")
    print("  1. FX Rates (USD/BRL, USD/CNY, USD/ARS) - Last 15 days")
    print("  2. Fed Policy (Fed Funds, 10Y Treasury, Yield Curve) - Last 30 days")
    print("  3. Crush Margins - Verification only (calculated data)")
    print("  4. Export Sales - Skipped (awaiting USDA implementation)")
    print()
    
    try:
        # Run the bidaily collection
        logger.info("🚀 Starting enhanced data pipeline test...")
        success, results = bidaily_data_collection()
        
        print("=" * 80)
        print("TEST RESULTS")
        print("=" * 80)
        
        overall_status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"Overall Status: {overall_status}")
        print()
        
        # Detailed results
        for data_type, result in results.items():
            status_emoji = {
                'success': '✅',
                'failed': '❌', 
                'error': '🚨',
                'warning': '⚠️',
                'skipped': '⏭️',
                'not_started': '⏸️'
            }.get(result['status'], '❓')
            
            print(f"{status_emoji} {data_type.upper()}: {result['status'].upper()}")
            
            if result['issues']:
                for issue in result['issues']:
                    print(f"    - {issue}")
            else:
                print("    - No issues detected")
            print()
        
        # Summary recommendations
        print("=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        
        if success:
            print("🎉 TEST PASSED - Pipeline is ready for automation!")
            print()
            print("Next steps:")
            print("1. Run: cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion")
            print("2. Run: ./setup_enhanced_cron.sh")
            print("3. Monitor logs in /Users/zincdigital/CBI-V14/logs/")
            print()
            print("⚠️  Remember: This pipeline only fills recent data gaps.")
            print("   It does NOT pull historical years to avoid data corruption.")
        else:
            print("🛑 TEST FAILED - DO NOT enable automation yet!")
            print()
            print("Issues found:")
            failed_sources = [dt for dt, res in results.items() if res['status'] in ['failed', 'error']]
            for source in failed_sources:
                print(f"  - {source}: {results[source]['status']}")
            print()
            print("Fix these issues before proceeding with automation.")
        
        print()
        print("=" * 80)
        print(f"Test completed at: {datetime.now()}")
        print("=" * 80)
        
        return success
        
    except Exception as e:
        print(f"🚨 CRITICAL ERROR during test: {str(e)}")
        print()
        print("❌ Test failed due to exception - do not enable automation")
        return False

if __name__ == "__main__":
    success = main()
    
    # Set appropriate exit code
    exit(0 if success else 1)




