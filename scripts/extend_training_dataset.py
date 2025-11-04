#!/usr/bin/env python3
"""
Extend training dataset backward and forward using available Yahoo Finance data
Adds missing dates from 2020-01-02 to 2025-11-02
"""
from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "cbi-v14"
client = bigquery.Client(project=PROJECT_ID)

print("="*70)
print("🔄 EXTENDING TRAINING DATASET BACKWARD AND FORWARD")
print("="*70)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Step 1: Find dates to add
print("1️⃣  Finding missing dates...")
query_missing = """
WITH current_dates AS (
  SELECT DISTINCT date
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE zl_price_current IS NOT NULL
),
available_dates AS (
  SELECT DISTINCT date
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'ZL=F'
    AND date BETWEEN '2020-01-02' AND '2025-11-02'
),
missing_dates AS (
  SELECT ad.date
  FROM available_dates ad
  LEFT JOIN current_dates cd ON ad.date = cd.date
  WHERE cd.date IS NULL
)
SELECT 
  COUNT(*) as missing_count,
  MIN(date) as earliest,
  MAX(date) as latest
FROM missing_dates
"""
missing_info = client.query(query_missing).to_dataframe().iloc[0]
print(f"   Missing dates: {missing_info['missing_count']:,}")
print(f"   Range: {missing_info['earliest']} to {missing_info['latest']}\n")

if missing_info['missing_count'] == 0:
    print("✅ No missing dates found!")
    exit(0)

# Step 2: Use the existing backfill script pattern but extend the date range
print("2️⃣  Extending via backfill pattern...")
print("   Using INSERT with minimal columns, letting feature engineering fill the rest\n")

# Use JOINs instead of correlated subqueries for targets
extend_sql = """
-- Extend training dataset using Yahoo Finance data with JOINs for targets
INSERT INTO `cbi-v14.models_v4.training_dataset_super_enriched`
(
  date,
  zl_price_current,
  zl_volume,
  target_1w,
  target_1m,
  target_3m,
  target_6m
)
SELECT 
  yf.date,
  yf.Close AS zl_price_current,
  CAST(yf.Volume AS INT64) AS zl_volume,
  -- Calculate targets from future prices using JOINs
  target_1w.Close AS target_1w,
  target_1m.Close AS target_1m,
  target_3m.Close AS target_3m,
  target_6m.Close AS target_6m
FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced` yf
LEFT JOIN `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced` target_1w
  ON target_1w.symbol = 'ZL=F' 
  AND target_1w.date = DATE_ADD(yf.date, INTERVAL 7 DAY)
LEFT JOIN `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced` target_1m
  ON target_1m.symbol = 'ZL=F' 
  AND target_1m.date = DATE_ADD(yf.date, INTERVAL 30 DAY)
LEFT JOIN `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced` target_3m
  ON target_3m.symbol = 'ZL=F' 
  AND target_3m.date = DATE_ADD(yf.date, INTERVAL 90 DAY)
LEFT JOIN `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced` target_6m
  ON target_6m.symbol = 'ZL=F' 
  AND target_6m.date = DATE_ADD(yf.date, INTERVAL 180 DAY)
WHERE yf.symbol = 'ZL=F'
  AND yf.date BETWEEN '2020-01-02' AND '2025-11-02'
  AND yf.date NOT IN (
    SELECT DISTINCT date 
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE zl_price_current IS NOT NULL
  )
  AND yf.Close IS NOT NULL
ORDER BY yf.date
"""

try:
    print("3️⃣  Executing extension...")
    job = client.query(extend_sql)
    job.result()
    
    print("✅ Extension complete!\n")
    
    # Verify
    query_verify = """
    SELECT 
      MIN(date) as min_date,
      MAX(date) as max_date,
      COUNT(*) as total_rows,
      COUNTIF(target_1w IS NOT NULL) as rows_with_target_1w,
      COUNTIF(target_1m IS NOT NULL) as rows_with_target_1m
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE zl_price_current IS NOT NULL
    """
    result = client.query(query_verify).to_dataframe().iloc[0]
    
    print("📊 Updated Dataset:")
    print(f"   Range: {result['min_date']} to {result['max_date']}")
    print(f"   Total rows: {result['total_rows']:,}")
    print(f"   Rows with target_1w: {result['rows_with_target_1w']:,}")
    print(f"   Rows with target_1m: {result['rows_with_target_1m']:,}")
    
    # Check train_1w view
    print("\n4️⃣  Checking train_1w view...")
    query_train = """
    SELECT 
      COUNT(*) as total,
      COUNTIF(target_1w IS NOT NULL) as with_target
    FROM `cbi-v14.models_v4.train_1w`
    """
    train_result = client.query(query_train).to_dataframe().iloc[0]
    print(f"   train_1w: {train_result['total']:,} rows, {train_result['with_target']:,} with target")
    
    print("\n" + "="*70)
    print("✅ DATASET EXTENSION COMPLETE!")
    print("="*70)
    print("\nNote: Other features will be populated by feature engineering views")
    print("      Run feature engineering scripts to fill in all derived features")
    
except Exception as e:
    error_str = str(e)
    print(f"\n❌ Error: {error_str[:400]}")
    if 'duplicate' in error_str.lower():
        print("\n💡 Some dates may already exist - that's okay")
    import traceback
    traceback.print_exc()
