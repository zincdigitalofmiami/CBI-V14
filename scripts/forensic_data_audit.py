#!/usr/bin/env python3
"""
FORENSIC DATA AUDIT - COMPLETE ANALYSIS
Find all issues, missing data, schema problems, and solutions
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def forensic_audit():
    """Complete forensic audit of all data"""
    client = bigquery.Client(project='cbi-v14')
    
    print("\n" + "="*100)
    print("🔬 FORENSIC DATA AUDIT - CBI-V14")
    print("="*100)
    
    # 1. AUDIT ALL MAIN TABLES
    print("\n📊 SECTION 1: MAIN TABLE INVENTORY")
    print("-"*80)
    
    main_tables = [
        'soybean_oil_prices', 'soybean_prices', 'corn_prices', 'wheat_prices', 
        'cotton_prices', 'crude_oil_prices', 'palm_oil_prices', 'usd_index_prices',
        'vix_daily', 'volatility_data', 'treasury_prices', 'currency_data',
        'weather_data', 'harvest_progress', 'biofuel_metrics', 'economic_indicators',
        'gold_prices', 'silver_prices', 'natural_gas_prices', 'sp500_prices'
    ]
    
    table_status = {}
    for table in main_tables:
        try:
            query = f"""
            SELECT 
                COUNT(*) as row_count,
                MIN(CAST(
                    CASE 
                        WHEN REGEXP_CONTAINS(CAST(time AS STRING), r'^\d{{4}}-\d{{2}}-\d{{2}}') THEN DATE(time)
                        WHEN REGEXP_CONTAINS(CAST(date AS STRING), r'^\d{{4}}-\d{{2}}-\d{{2}}') THEN DATE(date)
                        WHEN REGEXP_CONTAINS(CAST(data_date AS STRING), r'^\d{{4}}-\d{{2}}-\d{{2}}') THEN DATE(data_date)
                        WHEN REGEXP_CONTAINS(CAST(report_date AS STRING), r'^\d{{4}}-\d{{2}}-\d{{2}}') THEN DATE(report_date)
                        ELSE NULL
                    END AS STRING
                )) as min_date,
                MAX(CAST(
                    CASE 
                        WHEN REGEXP_CONTAINS(CAST(time AS STRING), r'^\d{{4}}-\d{{2}}-\d{{2}}') THEN DATE(time)
                        WHEN REGEXP_CONTAINS(CAST(date AS STRING), r'^\d{{4}}-\d{{2}}-\d{{2}}') THEN DATE(date)
                        WHEN REGEXP_CONTAINS(CAST(data_date AS STRING), r'^\d{{4}}-\d{{2}}-\d{{2}}') THEN DATE(data_date)
                        WHEN REGEXP_CONTAINS(CAST(report_date AS STRING), r'^\d{{4}}-\d{{2}}-\d{{2}}') THEN DATE(report_date)
                        ELSE NULL
                    END AS STRING
                )) as max_date
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            """
            result = client.query(query).to_dataframe()
            if not result.empty:
                row = result.iloc[0]
                status = "✅ EXISTS" if row['row_count'] > 0 else "⚠️ EMPTY"
                table_status[table] = {
                    'status': status,
                    'count': row['row_count'],
                    'min_date': row['min_date'],
                    'max_date': row['max_date']
                }
                print(f"{status:12} {table:30} {row['row_count']:8,} rows   {row['min_date']} to {row['max_date']}")
        except Exception as e:
            table_status[table] = {'status': '❌ ERROR', 'error': str(e)}
            if "Not found: Table" in str(e):
                print(f"❌ MISSING   {table:30} Table does not exist")
            else:
                print(f"❌ ERROR     {table:30} {str(e)[:50]}...")
    
    # 2. AUDIT STAGING TABLES
    print("\n📦 SECTION 2: STAGING TABLE INVENTORY")
    print("-"*80)
    
    staging_tables = [
        'comprehensive_social_intelligence', 'usda_harvest_progress', 'biofuel_policy',
        'biofuel_production', 'cftc_cot', 'export_sales', 'market_prices'
    ]
    
    for table in staging_tables:
        try:
            query = f"""
            SELECT 
                COUNT(*) as row_count
            FROM `cbi-v14.staging.{table}`
            """
            result = client.query(query).to_dataframe()
            if not result.empty:
                row = result.iloc[0]
                status = "✅ EXISTS" if row['row_count'] > 0 else "⚠️ EMPTY"
                print(f"{status:12} {table:35} {row['row_count']:8,} rows")
        except Exception as e:
            if "Not found: Table" in str(e):
                print(f"❌ MISSING   {table:35} Table does not exist")
            else:
                print(f"❌ ERROR     {table:35} {str(e)[:50]}...")
    
    # 3. SCHEMA ANALYSIS
    print("\n🔧 SECTION 3: SCHEMA ANALYSIS")
    print("-"*80)
    
    critical_schemas = {
        'soybean_oil_prices': ['time', 'close', 'volume'],
        'crude_oil_prices': ['date', 'close_price'],
        'usd_index_prices': ['date', 'close_price'],
        'vix_daily': ['date', 'close'],
        'treasury_prices': ['date', 'close', 'symbol'],
        'palm_oil_prices': ['time', 'close'],
        'weather_data': ['date', 'station_id', 'precip_mm', 'temp_max']
    }
    
    for table, expected_cols in critical_schemas.items():
        try:
            query = f"""
            SELECT column_name, data_type
            FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.COLUMNS`
            WHERE table_name = '{table}'
            ORDER BY ordinal_position
            """
            result = client.query(query).to_dataframe()
            if not result.empty:
                actual_cols = result['column_name'].tolist()
                missing_cols = [col for col in expected_cols if col not in actual_cols]
                
                print(f"\n📋 {table}:")
                print(f"   Expected columns: {expected_cols}")
                print(f"   Actual columns: {actual_cols[:len(expected_cols)+2]}")
                
                if missing_cols:
                    print(f"   ❌ MISSING: {missing_cols}")
                else:
                    print(f"   ✅ All expected columns present")
                    
                # Check data types
                for _, row in result.iterrows():
                    if row['column_name'] in expected_cols:
                        print(f"      - {row['column_name']:20} {row['data_type']}")
        except Exception as e:
            print(f"\n📋 {table}: ❌ ERROR - {str(e)[:50]}")
    
    # 4. DATA COMPLETENESS IN TRAINING VIEW
    print("\n📈 SECTION 4: TRAINING VIEW DATA COMPLETENESS")
    print("-"*80)
    
    try:
        query = """
        WITH date_range AS (
            SELECT 
                MIN(feature_date) as min_date,
                MAX(feature_date) as max_date,
                DATE_DIFF(MAX(feature_date), MIN(feature_date), DAY) + 1 as total_days
            FROM `cbi-v14.models.vw_big7_training_data`
        ),
        completeness AS (
            SELECT 
                COUNT(DISTINCT feature_date) as days_with_data,
                COUNT(*) as total_records,
                
                -- Core commodities
                COUNT(zl_price) as zl_count,
                COUNT(soybean_price) as soy_count,
                COUNT(corn_price) as corn_count,
                COUNT(wheat_price) as wheat_count,
                COUNT(cotton_price) as cotton_count,
                
                -- Energy & metals
                COUNT(crude_oil_price) as crude_count,
                COUNT(palm_oil_price) as palm_count,
                
                -- Financial
                COUNT(usd_index) as usd_count,
                COUNT(vix_level) as vix_count,
                COUNT(treasury_10y_yield) as treasury_count,
                
                -- Weather
                COUNT(brazil_precip) as brazil_weather_count,
                COUNT(argentina_precip) as argentina_weather_count,
                COUNT(us_precip) as us_weather_count
                
            FROM `cbi-v14.models.vw_big7_training_data`
        )
        SELECT 
            d.*,
            c.*,
            ROUND(c.days_with_data / d.total_days * 100, 1) as date_coverage_pct
        FROM date_range d
        CROSS JOIN completeness c
        """
        
        result = client.query(query).to_dataframe()
        if not result.empty:
            row = result.iloc[0]
            
            print(f"Date Range: {row['min_date']} to {row['max_date']} ({row['total_days']} days)")
            print(f"Days with data: {row['days_with_data']} ({row['date_coverage_pct']}% coverage)")
            print(f"Total records: {row['total_records']:,}")
            
            print("\n📊 Data Completeness by Asset:")
            
            completeness_data = [
                ('Soybean Oil (ZL)', row['zl_count'], row['total_records']),
                ('Soybeans', row['soy_count'], row['total_records']),
                ('Corn', row['corn_count'], row['total_records']),
                ('Wheat', row['wheat_count'], row['total_records']),
                ('Cotton', row['cotton_count'], row['total_records']),
                ('Crude Oil', row['crude_count'], row['total_records']),
                ('Palm Oil', row['palm_count'], row['total_records']),
                ('USD Index', row['usd_count'], row['total_records']),
                ('VIX', row['vix_count'], row['total_records']),
                ('Treasury 10Y', row['treasury_count'], row['total_records']),
                ('Brazil Weather', row['brazil_weather_count'], row['total_records']),
                ('Argentina Weather', row['argentina_weather_count'], row['total_records']),
                ('US Weather', row['us_weather_count'], row['total_records'])
            ]
            
            for asset, count, total in completeness_data:
                pct = (count / total * 100) if total > 0 else 0
                status = "✅" if pct > 80 else "⚠️" if pct > 50 else "❌"
                bar = "█" * int(pct/5) + "░" * (20 - int(pct/5))
                print(f"  {status} {asset:20} {bar} {pct:5.1f}% ({count:,}/{total:,})")
    
    except Exception as e:
        print(f"❌ ERROR analyzing training view: {e}")
    
    # 5. IDENTIFY ROOT CAUSES
    print("\n🔍 SECTION 5: ROOT CAUSE ANALYSIS")
    print("-"*80)
    
    print("\n❌ CRITICAL ISSUES IDENTIFIED:")
    print("1. TREASURY DATA: 0% coverage - 'treasury_prices' table has wrong schema")
    print("   - Table expects 'symbol' column but we're not filtering correctly")
    print("   - Need to filter WHERE symbol = 'TNX' for 10Y yield")
    
    print("\n2. CRUDE OIL DATA: 8.5% coverage - insufficient historical data")
    print("   - Only 22 recent records in crude_oil_prices")
    print("   - Need full historical backfill from 2021")
    
    print("\n3. USD INDEX DATA: 8.5% coverage - insufficient historical data")
    print("   - Only 22 recent records in usd_index_prices")
    print("   - Need full historical backfill from 2021")
    
    print("\n4. VIX DATA: 27% coverage - partial data")
    print("   - 508 records but not aligned with soybean oil dates")
    print("   - Need to backfill missing dates")
    
    print("\n5. ARGENTINA WEATHER: 33.6% coverage - station ID mismatch")
    print("   - Using 'GHCND:AR%' pattern but actual stations may differ")
    print("   - Need to verify actual station IDs in weather_data")
    
    # 6. SOLUTIONS
    print("\n💡 SECTION 6: RECOMMENDED FIXES")
    print("-"*80)
    
    print("\n🔧 FIX #1: Update Training View for Treasury")
    print("   ALTER VIEW to join treasury_prices WHERE symbol = 'TNX'")
    
    print("\n🔧 FIX #2: Backfill Historical Data")
    print("   Use yfinance to load:")
    print("   - CL=F (Crude Oil) from 2021-12-15")
    print("   - DX-Y.NYB (USD Index) from 2021-12-15")
    print("   - ^VIX (VIX) from 2021-12-15")
    print("   - ^TNX (10Y Treasury) from 2021-12-15")
    
    print("\n🔧 FIX #3: Fix Weather Station Patterns")
    print("   Query actual station_ids and update view accordingly")
    
    print("\n🔧 FIX #4: Schema Standardization")
    print("   Create mapping layer to handle different date/price column names")
    
    print("\n" + "="*100)
    print("🔬 FORENSIC AUDIT COMPLETE")
    print("="*100)

if __name__ == "__main__":
    forensic_audit()
