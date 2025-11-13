#!/usr/bin/env python3
"""
CFTC COT Historical Backfill (2006-2025)
==========================================
Backfills 19 years of CFTC Commitment of Traders data for Soybean Oil (ZL)
"""

import sys
import os

# Add both ingestion directory and repo root to path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INGESTION_DIR = os.path.join(REPO_ROOT, 'src', 'ingestion')
sys.path.insert(0, INGESTION_DIR)
sys.path.insert(0, REPO_ROOT)

from ingest_cftc_positioning_REAL import CFTCScraper
from datetime import datetime, timedelta
import logging
import time
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backfill_cftc_by_year(start_year: int = 2006, end_year: int = 2025):
    """
    Backfill CFTC COT data year by year to avoid API limits.
    
    Args:
        start_year: Starting year (default: 2006)
        end_year: Ending year (default: 2025)
    """
    scraper = CFTCScraper()
    total_rows = 0
    results = []
    
    logger.info(f"🚀 Starting CFTC COT backfill from {start_year} to {end_year}")
    
    # Process year by year
    for year in range(start_year, end_year + 1):
        logger.info(f"\n📅 Processing year {year}...")
        
        # Define year boundaries
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        # For current year, use today's date
        if year == datetime.now().year:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Fetch data for this year
            raw_data = scraper.fetch_cot_data(
                start_date=start_date,
                end_date=end_date,
                limit=10000  # CFTC typically has ~52 reports per year
            )
            
            if not raw_data:
                logger.warning(f"⚠️  No data found for {year}")
                results.append({
                    'year': year,
                    'status': 'NO_DATA',
                    'rows_loaded': 0
                })
                continue
            
            # Transform to schema
            transformed = scraper.transform_to_schema(raw_data)
            
            if not transformed:
                logger.warning(f"⚠️  No transformed data for {year}")
                results.append({
                    'year': year,
                    'status': 'TRANSFORM_FAILED',
                    'rows_loaded': 0
                })
                continue
            
            # Load to BigQuery
            rows_loaded = scraper.load_to_bigquery(transformed)
            total_rows += rows_loaded
            
            logger.info(f"✅ Year {year}: Loaded {rows_loaded} rows")
            
            results.append({
                'year': year,
                'status': 'SUCCESS',
                'rows_loaded': rows_loaded,
                'date_range': f"{start_date} to {end_date}"
            })
            
            # Rate limiting between years
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"❌ Error processing year {year}: {e}")
            results.append({
                'year': year,
                'status': 'ERROR',
                'rows_loaded': 0,
                'error': str(e)
            })
            continue
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("CFTC COT BACKFILL SUMMARY")
    logger.info("="*60)
    logger.info(f"Total rows loaded: {total_rows}")
    logger.info(f"Years processed: {len(results)}")
    logger.info(f"Successful years: {sum(1 for r in results if r['status'] == 'SUCCESS')}")
    logger.info(f"Failed years: {sum(1 for r in results if r['status'] != 'SUCCESS')}")
    
    return {
        'total_rows_loaded': total_rows,
        'years_processed': len(results),
        'results': results
    }


if __name__ == '__main__':
    # Check for command line arguments
    start_year = 2006
    end_year = 2025
    
    if len(sys.argv) > 1:
        start_year = int(sys.argv[1])
    if len(sys.argv) > 2:
        end_year = int(sys.argv[2])
    
    result = backfill_cftc_by_year(start_year, end_year)
    print(json.dumps(result, indent=2))

