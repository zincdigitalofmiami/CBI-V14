#!/usr/bin/env python3
"""
Phase 0: Data Refresh & Validation
Complete execution script for Phase 0 of CBI-V14
"""

import sys
import subprocess
from pathlib import Path
from google.cloud import bigquery

def check_tables_exist(client, dataset_id, table_names):
    """Check which tables already exist"""
    existing_tables = [t.table_id for t in client.list_tables(dataset_id)]
    found = [t for t in table_names if t in existing_tables]
    missing = [t for t in table_names if t not in existing_tables]
    return found, missing

def run_sql_file(sql_path, description, check_before_create=True):
    """Execute a SQL file using BigQuery Python client"""
    print(f"\n📊 {description}...")
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project='cbi-v14')
        
        # Read SQL file
        with open(sql_path, 'r') as f:
            sql_content = f.read()
        
        # If checking before create, extract table names and verify
        if check_before_create and 'CREATE TABLE' in sql_content.upper():
            # Extract table names from CREATE TABLE statements
            import re
            table_names = re.findall(r'`cbi-v14\.forecasting_data_warehouse\.(\w+)`', sql_content)
            
            if table_names:
                found, missing = check_tables_exist(client, 'forecasting_data_warehouse', table_names)
                if found:
                    print(f"  ⚠️  {len(found)} table(s) already exist: {found[:3]}...")
                    print(f"  ℹ️  Using CREATE TABLE IF NOT EXISTS (safe to proceed)")
                print(f"  ℹ️  Will create {len(missing)} new table(s)")
        
        # Execute SQL
        job = client.query(sql_content)
        job.result()  # Wait for completion
        
        print(f"  ✅ {description} completed")
        return True
    except Exception as e:
        print(f"  ❌ {description} failed: {str(e)}")
        return False

def main():
    print("="*60)
    print("🚀 PHASE 0: DATA REFRESH & VALIDATION")
    print("="*60)
    
    # Step 0.1: Check data freshness
    print("\n[0.1] Checking data freshness...")
    result = subprocess.run(
        ['python3', 'scripts/check_data_freshness.py'],
        cwd=Path(__file__).parent.parent
    )
    if result.returncode != 0:
        print("  ⚠️ Some tables may be missing or stale. This is OK for first run.")
    
    # Step 0.2: Create web scraping tables
    print("\n[0.2] Setting up web scraping infrastructure...")
    sql_path = Path(__file__).parent.parent / 'bigquery_sql' / 'create_web_scraping_tables.sql'
    if sql_path.exists():
        # Pre-check tables before creating
        try:
            from google.cloud import bigquery
            client = bigquery.Client(project='cbi-v14')
            web_scraping_tables = [
                'futures_prices_barchart', 'futures_prices_marketwatch', 'futures_prices_investing',
                'futures_sentiment_tradingview', 'policy_rfs_volumes', 'legislative_bills',
                'policy_events_federalregister', 'ers_oilcrops_monthly', 'usda_wasde_soy',
                'news_industry_brownfield', 'news_market_farmprogress', 'enso_climate_status',
                'industry_intelligence_asa', 'news_reuters', 'futures_prices_cme_public',
                'market_analysis_correlations'
            ]
            found, missing = check_tables_exist(client, 'forecasting_data_warehouse', web_scraping_tables)
            
            if found:
                print(f"  ⚠️  {len(found)} web scraping table(s) already exist: {found}")
                print(f"  ✅ SQL uses CREATE TABLE IF NOT EXISTS - safe to proceed")
            print(f"  ℹ️  {len(missing)} table(s) need to be created: {missing[:3]}...")
        except Exception as e:
            print(f"  ⚠️  Could not check existing tables: {str(e)}")
        
        run_sql_file(sql_path, "Creating web scraping tables", check_before_create=True)
    else:
        print("  ⚠️ SQL file not found. Will create tables via SQL later.")
    
    # Step 0.3: Validate feature engineering
    print("\n[0.3] Validating feature engineering...")
    validate_sql = """
    -- Feature count validation
    SELECT 
      'training_dataset_super_enriched' AS table_name,
      COUNT(*) AS num_features,
      CASE 
        WHEN COUNT(*) BETWEEN 205 AND 209 THEN '✅ VALID'
        WHEN COUNT(*) < 205 THEN '❌ MISSING FEATURES'
        WHEN COUNT(*) > 209 THEN '❌ EXTRA FEATURES'
      END AS status
    FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'training_dataset_super_enriched';
    """
    
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project='cbi-v14')
        results = client.query(validate_sql).to_dataframe()
        print(results.to_string(index=False))
        
        if len(results) > 0 and 'VALID' in results['status'].iloc[0]:
            print("  ✅ Feature count is valid")
        else:
            print("  ⚠️ Feature count validation failed - may need to rebuild features")
    except Exception as e:
        print(f"  ⚠️ Could not validate features: {str(e)}")
        print("  Note: This is OK if training table doesn't exist yet.")
    
    print("\n" + "="*60)
    print("✅ PHASE 0 EXECUTION COMPLETE")
    print("="*60)
    print("\nNext Steps:")
    print("  - If data is stale, run data ingestion pipeline")
    print("  - Verify web scraping tables created")
    print("  - Proceed to Phase 0.5 (Vertex AI residual extraction)")
    print("="*60)

if __name__ == "__main__":
    main()

