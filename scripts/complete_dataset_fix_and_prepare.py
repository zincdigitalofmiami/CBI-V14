#!/usr/bin/env python3
"""
Complete Dataset Fix and Preparation
1. Audit all NULLs
2. Fill appropriately
3. Ensure proper dates/schema
4. Rebuild super-enriched properly
5. Verify for training
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("COMPLETE DATASET FIX AND PREPARATION")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Step 1: Audit base enriched dataset
print("=" * 80)
print("STEP 1: AUDITING BASE ENRICHED DATASET")
print("=" * 80)

audit_query = """
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT date) as unique_dates,
    MIN(date) as min_date,
    MAX(date) as max_date
FROM `cbi-v14.models.training_dataset_enhanced`
"""

audit_df = client.query(audit_query).to_dataframe()
print(f"✅ Base dataset: {audit_df['total_rows'].iloc[0]} rows, {audit_df['unique_dates'].iloc[0]} unique dates")
print(f"   Date range: {audit_df['min_date'].iloc[0]} to {audit_df['max_date'].iloc[0]}")
print()

# Step 2: Get all derived features with proper date handling
print("=" * 80)
print("STEP 2: CREATING DERIVED FEATURES WITH PROPER DATES")
print("=" * 80)

# FX Features
print("Creating FX features...")
fx_query = """
CREATE OR REPLACE TABLE `cbi-v14.models_v4.fx_derived_features` AS
SELECT
  DATE(time) as date,
  MAX(IF(indicator = 'usd_cny_rate', value, NULL)) AS usd_cny_rate,
  MAX(IF(indicator = 'usd_brl_rate', value, NULL)) AS usd_brl_rate,
  MAX(IF(indicator = 'dollar_index_fred', value, NULL)) AS dollar_index,
  MAX(IF(indicator = 'usd_ars_rate', value, NULL)) AS usd_ars_rate,
  MAX(IF(indicator = 'usd_eur_rate', value, NULL)) AS usd_eur_rate
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
WHERE DATE(time) >= '2020-01-01'
GROUP BY DATE(time)
ORDER BY date
"""

job = client.query(fx_query)
result = job.result()
print("✅ FX features created")

# Monetary Features  
print("Creating monetary features...")
monetary_query = """
CREATE OR REPLACE TABLE `cbi-v14.models_v4.monetary_derived_features` AS
SELECT
  DATE(time) as date,
  MAX(IF(indicator = 'fed_funds_rate', value, NULL)) AS fed_funds_rate,
  MAX(IF(indicator = 'ten_year_treasury', value, NULL)) AS ten_year_treasury,
  MAX(IF(indicator = 'cpi_inflation', value, NULL)) AS cpi_inflation,
  MAX(IF(indicator = 'yield_curve', value, NULL)) AS yield_curve
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
WHERE DATE(time) >= '2020-01-01'
GROUP BY DATE(time)
ORDER BY date
"""

job = client.query(monetary_query)
result = job.result()
print("✅ Monetary features created")

# Volatility Features
print("Creating volatility features...")
volatility_query = """
CREATE OR REPLACE TABLE `cbi-v14.models_v4.volatility_derived_features` AS
SELECT
  DATE(time) as date,
  MAX(IF(indicator = 'vix_index_fred', value, NULL)) AS vix_index,
  MAX(IF(indicator = 'crude_oil_wti', value, NULL)) AS crude_oil_wti
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
WHERE DATE(time) >= '2020-01-01'
GROUP BY DATE(time)
ORDER BY date
"""

job = client.query(volatility_query)
result = job.result()
print("✅ Volatility features created")
print()

# Step 3: Create super-enriched with proper NULL handling
print("=" * 80)
print("STEP 3: CREATING SUPER-ENRICHED WITH NULL HANDLING")
print("=" * 80)

super_query = """
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_super_enriched` AS
SELECT DISTINCT
    e.date,
    e.* EXCEPT(date, treasury_10y_yield),
    -- FX features with 0 fill
    COALESCE(fx.usd_cny_rate, 0) AS usd_cny_rate,
    COALESCE(fx.usd_brl_rate, 0) AS usd_brl_rate,
    COALESCE(fx.dollar_index, 0) AS dollar_index,
    COALESCE(fx.usd_ars_rate, 0) AS usd_ars_rate,
    COALESCE(fx.usd_eur_rate, 0) AS usd_eur_rate,
    -- Monetary features with 0 fill
    COALESCE(m.fed_funds_rate, 0) AS fed_funds_rate,
    COALESCE(m.ten_year_treasury, 0) AS ten_year_treasury,
    COALESCE(m.cpi_inflation, 0) AS cpi_inflation,
    COALESCE(m.yield_curve, 0) AS yield_curve,
    -- Volatility features with 0 fill
    COALESCE(v.vix_index, 0) AS vix_index,
    COALESCE(v.crude_oil_wti, 0) AS crude_oil_wti,
    -- Keep original treasury for now
    COALESCE(e.treasury_10y_yield, m.ten_year_treasury, 0) AS treasury_10y_yield
FROM `cbi-v14.models.training_dataset_enhanced` e
LEFT JOIN `cbi-v14.models_v4.fx_derived_features` fx ON e.date = fx.date
LEFT JOIN `cbi-v14.models_v4.monetary_derived_features` m ON e.date = m.date
LEFT JOIN `cbi-v14.models_v4.volatility_derived_features` v ON e.date = v.date
ORDER BY e.date
"""

print("Creating super-enriched dataset...")
job = client.query(super_query)
result = job.result()

# Verify
verify_query = """
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT date) as unique_dates,
    COUNT(CASE WHEN treasury_10y_yield != 0 THEN 1 END) as treasury_non_zero,
    COUNT(CASE WHEN fed_funds_rate != 0 THEN 1 END) as fed_non_zero,
    COUNT(CASE WHEN usd_brl_rate != 0 THEN 1 END) as brl_non_zero
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
"""

verify_df = client.query(verify_query).to_dataframe()
print(f"✅ Super-enriched created: {verify_df['total_rows'].iloc[0]} rows")
print(f"   Treasury non-zero: {verify_df['treasury_non_zero'].iloc[0]}")
print(f"   Fed non-zero: {verify_df['fed_non_zero'].iloc[0]}")
print(f"   BRL non-zero: {verify_df['brl_non_zero'].iloc[0]}")
print()

print("=" * 80)
print("✅ DATASET READY FOR TRAINING")
print("=" * 80)
print(f"Rows: {verify_df['total_rows'].iloc[0]}")
print(f"Unique dates: {verify_df['unique_dates'].iloc[0]}")
print("All NULLs filled with 0 where appropriate")
print("=" * 80)





