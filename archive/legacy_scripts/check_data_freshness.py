#!/usr/bin/env python3
"""
Phase 0.1: Check Data Freshness
Verifies all source tables are fresh before proceeding with training.
"""

from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

def check_freshness():
    """Check freshness of all source tables"""
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT 
      'soybean_oil_prices' AS table_name,
      COUNT(*) AS total_rows,
      MAX(timestamp) AS latest_date,
      TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(timestamp), HOUR) AS hours_stale,
      CASE 
        WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(timestamp), HOUR) > 48 
        THEN '❌ STALE - Refresh needed'
        WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(timestamp), HOUR) > 24 
        THEN '⚠️ WARNING - Approaching staleness'
        ELSE '✅ FRESH'
      END AS status
    FROM `{PROJECT_ID}.{DATASET_ID}.soybean_oil_prices`
    
    UNION ALL
    
    SELECT 
      'weather_data' AS table_name,
      COUNT(*) AS total_rows,
      MAX(observation_time) AS latest_date,
      TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(observation_time), HOUR) AS hours_stale,
      CASE 
        WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(observation_time), HOUR) > 24 
        THEN '❌ STALE - Refresh needed'
        WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(observation_time), HOUR) > 12 
        THEN '⚠️ WARNING'
        ELSE '✅ FRESH'
      END AS status
    FROM `{PROJECT_ID}.{DATASET_ID}.weather_data`
    
    UNION ALL
    
    SELECT 
      'usda_reports' AS table_name,
      COUNT(*) AS total_rows,
      CAST(MAX(report_date) AS TIMESTAMP) AS latest_date,
      TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), CAST(MAX(report_date) AS TIMESTAMP), HOUR) AS hours_stale,
      CASE 
        WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), CAST(MAX(report_date) AS TIMESTAMP), HOUR) > 168 
        THEN '⚠️ Check for new reports'
        ELSE '✅ FRESH'
      END AS status
    FROM `{PROJECT_ID}.{DATASET_ID}.usda_reports`;
    """
    
    try:
        results = client.query(query).to_dataframe()
        print("\n" + "="*60)
        print("📊 DATA FRESHNESS CHECK")
        print("="*60)
        print(results.to_string(index=False))
        print("="*60)
        
        # Check if any are stale
        stale = results[results['status'].str.contains('STALE|WARNING', na=False)]
        if len(stale) > 0:
            print(f"\n⚠️  Found {len(stale)} stale table(s). Run data refresh before proceeding.")
            return False
        else:
            print("\n✅ All tables are fresh. Ready to proceed.")
            return True
            
    except Exception as e:
        print(f"\n❌ Error checking freshness: {str(e)}")
        print("Note: Some tables may not exist yet. This is OK if running for first time.")
        return False

if __name__ == "__main__":
    check_freshness()

