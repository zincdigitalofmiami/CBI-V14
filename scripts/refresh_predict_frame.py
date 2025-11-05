#!/usr/bin/env python3
"""
refresh_predict_frame.py
Refresh predict_frame_209 with latest data from feature tables and Big 8 signals
"""
import subprocess
import sys
from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"

def get_latest_date():
    """Get the latest date available in price data"""
    client = bigquery.Client(project=PROJECT_ID)
    query = """
    SELECT MAX(DATE(time)) as latest_date
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE symbol = 'ZL'
    """
    result = client.query(query).to_dataframe()
    return result.iloc[0]['latest_date']

def update_latest_date_table(latest_date):
    """Update or create _latest_date table"""
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}._latest_date` AS
    SELECT DATE('{latest_date}') as latest_date
    """
    client.query(query).result()
    print(f"✅ Updated _latest_date to: {latest_date}")

def refresh_predict_frame():
    """Refresh predict_frame_209 with latest data"""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Get latest date
    latest_date = get_latest_date()
    print(f"📅 Latest available date: {latest_date}")
    
    # Update _latest_date table
    update_latest_date_table(latest_date)
    
    # Check if training_dataset_super_enriched has data for latest date
    check_query = f"""
    SELECT COUNT(*) as row_count
    FROM `{PROJECT_ID}.neural.vw_big_eight_signals`
    WHERE date = DATE('{latest_date}')
    """
    result = client.query(check_query).to_dataframe()
    
    if result.iloc[0]['row_count'] == 0:
        print(f"⚠️  Warning: No training data found for {latest_date}")
        print("   Using most recent available date from training data...")
        
        # Get most recent date from training data
        fallback_query = f"""
        SELECT MAX(date) as latest_date
        FROM `{PROJECT_ID}.neural.vw_big_eight_signals`
        """
        fallback_result = client.query(fallback_query).to_dataframe()
        latest_date = fallback_result.iloc[0]['latest_date']
        update_latest_date_table(latest_date)
        print(f"   Using: {latest_date}")
    
    # Create predict_frame_209
    print(f"🔨 Refreshing predict_frame_209 for date: {latest_date}")
    
    query = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.predict_frame_209` AS
    WITH d AS (
      SELECT DATE('{latest_date}') as latest_date
    ),
    price_data AS (
      SELECT 
        DATE(time) AS date,
        close,
        volume,
        LAG(close, 1)  OVER (ORDER BY time) AS lag1,
        LAG(close, 7)  OVER (ORDER BY time) AS lag7,
        LAG(close, 30) OVER (ORDER BY time) AS lag30
      FROM `{PROJECT_ID}.forecasting_data_warehouse.soybean_oil_prices`
      WHERE symbol = 'ZL'
        AND DATE(time) <= DATE('{latest_date}')
      QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY time DESC) = 1
    ),
    big8_signals AS (
      SELECT * FROM `{PROJECT_ID}.neural.vw_big_eight_signals`
      WHERE date = DATE('{latest_date}')
      LIMIT 1
    )
    SELECT
      -- REQUIRED KEYS
      d.latest_date AS date,
      
      -- PRICE CORE (recomputed from fresh price data)
      p.close AS zl_price_current,
      p.lag1 AS zl_price_lag1,
      p.lag7 AS zl_price_lag7,
      p.lag30 AS zl_price_lag30,
      (p.close - p.lag1) / NULLIF(p.lag1, 0) AS return_1d,
      (p.close - p.lag7) / NULLIF(p.lag7, 0) AS return_7d,
      AVG(p.close) OVER (ORDER BY p.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_7d,
      AVG(p.close) OVER (ORDER BY p.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS ma_30d,
      STDDEV_POP(p.close) OVER (ORDER BY p.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS volatility_30d,
      p.volume AS zl_volume,
      
      -- BIG 8 SIGNALS (from neural.vw_big_eight_signals)
      b.feature_vix_stress,
      b.feature_harvest_pace,
      b.feature_china_relations,
      b.feature_tariff_threat,
      b.feature_geopolitical_volatility,
      b.feature_biofuel_cascade,
      b.feature_hidden_correlation,
      b.feature_biofuel_ethanol,
      b.big8_composite_score,
      b.market_regime,
      
      
      -- TARGET COLUMNS (REQUIRED BY MODEL SCHEMA; NO NULLS!)
      -- Set to current price to satisfy "no NULL in transformations"
      CAST(p.close AS FLOAT64) AS target_1w,
      CAST(p.close AS FLOAT64) AS target_1m,
      CAST(p.close AS FLOAT64) AS target_3m,
      CAST(p.close AS FLOAT64) AS target_6m
    
    FROM d
    JOIN price_data p ON p.date = d.latest_date
    CROSS JOIN big8_signals b
    """
    
    try:
        client.query(query).result()
        print(f"✅ Successfully refreshed predict_frame_209")
        
        # Verify
        verify_query = f"""
        SELECT date, zl_price_current, feature_vix_stress, feature_harvest_pace, 
               big8_composite_score
        FROM `{PROJECT_ID}.{DATASET_ID}.predict_frame_209`
        LIMIT 1
        """
        verify_result = client.query(verify_query).to_dataframe()
        print(f"✅ Verified: predict_frame_209 date = {verify_result.iloc[0]['date']}")
        print(f"   Price: ${verify_result.iloc[0]['zl_price_current']:.2f}")
        print(f"   Big 8 Composite: {verify_result.iloc[0]['big8_composite_score']:.3f}")
        
    except Exception as e:
        print(f"❌ Error refreshing predict_frame_209: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 70)
    print("REFRESHING PREDICT_FRAME_209")
    print("=" * 70)
    refresh_predict_frame()
    print("=" * 70)
    print("✅ COMPLETE")
    print("=" * 70)

