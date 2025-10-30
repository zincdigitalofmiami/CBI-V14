#!/usr/bin/env python3
"""
EMERGENCY: Integrate ALL Missing Data into Training Dataset
Stop-the-presses integration of FX, monetary, fundamentals, volatility features
"""

from google.cloud import bigquery
from datetime import datetime
import sys

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚨 EMERGENCY DATA INTEGRATION - CREATING SUPER-ENRICHED DATASET")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Step 1: Create FX Derived Features
print("=" * 80)
print("STEP 1: Creating FX Derived Features")
print("=" * 80)

fx_query = """
CREATE OR REPLACE TABLE `cbi-v14.models_v4.fx_derived_features` AS
SELECT
  date,
  usd_cny_rate,
  usd_brl_rate,
  dollar_index,
  LAG(usd_cny_rate, 7) OVER(ORDER BY date) AS usd_cny_7d_ago,
  LAG(usd_brl_rate, 7) OVER(ORDER BY date) AS usd_brl_7d_ago,
  LAG(dollar_index, 7) OVER(ORDER BY date) AS dollar_index_7d_ago,
  (usd_cny_rate / NULLIF(LAG(usd_cny_rate, 7) OVER(ORDER BY date), 0) - 1) * 100 AS usd_cny_7d_change,
  (usd_brl_rate / NULLIF(LAG(usd_brl_rate, 7) OVER(ORDER BY date), 0) - 1) * 100 AS usd_brl_7d_change,
  (dollar_index / NULLIF(LAG(dollar_index, 7) OVER(ORDER BY date), 0) - 1) * 100 AS dollar_index_7d_change
FROM (
  SELECT 
    DATE(time) as date,
    MAX(IF(indicator = 'usd_cny_rate', value, NULL)) AS usd_cny_rate,
    MAX(IF(indicator = 'usd_brl_rate', value, NULL)) AS usd_brl_rate,
    MAX(IF(indicator = 'dollar_index', value, NULL)) AS dollar_index
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  GROUP BY date
)
WHERE date IS NOT NULL
ORDER BY date
"""

try:
    job = client.query(fx_query)
    result = job.result()
    print("✅ FX Derived Features Created")
except Exception as e:
    print(f"❌ Error creating FX features: {e}")
    sys.exit(1)

# Step 2: Create Monetary Derived Features
print("\n" + "=" * 80)
print("STEP 2: Creating Monetary Derived Features")
print("=" * 80)

monetary_query = """
CREATE OR REPLACE TABLE `cbi-v14.models_v4.monetary_derived_features` AS
SELECT
  date,
  fed_funds_rate,
  ten_year_treasury,
  cpi_inflation,
  ten_year_treasury - cpi_inflation AS real_yield,
  ten_year_treasury - fed_funds_rate AS yield_curve
FROM (
  SELECT 
    DATE(time) as date,
    MAX(IF(indicator = 'fed_funds_rate', value, NULL)) AS fed_funds_rate,
    MAX(IF(indicator = 'ten_year_treasury', value, NULL)) AS ten_year_treasury,
    MAX(IF(indicator = 'cpi_inflation', value, NULL)) AS cpi_inflation
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  GROUP BY date
)
WHERE date IS NOT NULL
ORDER BY date
"""

try:
    job = client.query(monetary_query)
    result = job.result()
    print("✅ Monetary Derived Features Created")
except Exception as e:
    print(f"❌ Error creating monetary features: {e}")
    sys.exit(1)

# Step 3: Create Fundamentals Derived Features
print("\n" + "=" * 80)
print("STEP 3: Creating Fundamentals Derived Features")
print("=" * 80)

fundamentals_query = """
CREATE OR REPLACE TABLE `cbi-v14.models_v4.fundamentals_derived_features` AS
SELECT
  date,
  br_soybean_production_kt,
  br_soybean_yield_t_per_ha,
  cn_soybean_imports_mmt_month,
  cn_soybean_imports_mmt_ytd,
  br_soybean_production_kt / NULLIF(cn_soybean_imports_mmt_ytd * 1000, 0) AS supply_demand_ratio
FROM (
  SELECT 
    DATE(time) as date,
    MAX(IF(indicator = 'br_soybean_production_kt', value, NULL)) AS br_soybean_production_kt,
    MAX(IF(indicator = 'br_soybean_yield_t_per_ha', value, NULL)) AS br_soybean_yield_t_per_ha,
    MAX(IF(indicator = 'cn_soybean_imports_mmt_month', value, NULL)) AS cn_soybean_imports_mmt_month,
    MAX(IF(indicator = 'cn_soybean_imports_mmt_ytd', value, NULL)) AS cn_soybean_imports_mmt_ytd
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  GROUP BY date
)
WHERE date IS NOT NULL
ORDER BY date
"""

try:
    job = client.query(fundamentals_query)
    result = job.result()
    print("✅ Fundamentals Derived Features Created")
except Exception as e:
    print(f"❌ Error creating fundamentals features: {e}")
    sys.exit(1)

# Step 4: Create Volatility Derived Features
print("\n" + "=" * 80)
print("STEP 4: Creating Volatility Derived Features")
print("=" * 80)

volatility_query = """
CREATE OR REPLACE TABLE `cbi-v14.models_v4.volatility_derived_features` AS
SELECT
  date,
  vix_index,
  crude_oil_wti,
  CASE
    WHEN vix_index < 15 THEN 'low_vol'
    WHEN vix_index BETWEEN 15 AND 25 THEN 'normal_vol'
    WHEN vix_index > 25 THEN 'high_vol'
    ELSE 'unknown'
  END AS vol_regime,
  (crude_oil_wti / NULLIF(LAG(crude_oil_wti, 7) OVER(ORDER BY date), 0) - 1) * 100 AS wti_7d_change
FROM (
  SELECT 
    DATE(time) as date,
    MAX(IF(indicator = 'vix_index', value, NULL)) AS vix_index,
    MAX(IF(indicator = 'crude_oil_wti', value, NULL)) AS crude_oil_wti
  FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
  GROUP BY date
)
WHERE date IS NOT NULL
ORDER BY date
"""

try:
    job = client.query(volatility_query)
    result = job.result()
    print("✅ Volatility Derived Features Created")
except Exception as e:
    print(f"❌ Error creating volatility features: {e}")
    sys.exit(1)

# Step 5: Create Super-Enriched Training Dataset
print("\n" + "=" * 80)
print("STEP 5: Creating Super-Enriched Training Dataset")
print("=" * 80)

super_enriched_query = """
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_super_enriched` AS
SELECT
  e.*,
  -- FX features
  COALESCE(fx.usd_cny_rate, 0) AS usd_cny_rate,
  COALESCE(fx.usd_brl_rate, 0) AS usd_brl_rate,
  COALESCE(fx.dollar_index, 0) AS dollar_index,
  COALESCE(fx.usd_cny_7d_change, 0) AS usd_cny_7d_change,
  COALESCE(fx.usd_brl_7d_change, 0) AS usd_brl_7d_change,
  COALESCE(fx.dollar_index_7d_change, 0) AS dollar_index_7d_change,
  -- Monetary features
  COALESCE(m.fed_funds_rate, 0) AS fed_funds_rate,
  COALESCE(m.real_yield, 0) AS real_yield,
  COALESCE(m.yield_curve, 0) AS yield_curve,
  -- Supply-Demand features
  COALESCE(f.supply_demand_ratio, 0) AS supply_demand_ratio,
  COALESCE(f.br_soybean_yield_t_per_ha, 0) AS br_yield,
  COALESCE(f.cn_soybean_imports_mmt_month, 0) AS cn_imports,
  -- Volatility features
  COALESCE(v.vix_index, 0) AS vix_index_new,
  COALESCE(v.crude_oil_wti, 0) AS crude_oil_wti_new,
  COALESCE(v.wti_7d_change, 0) AS wti_7d_change,
  CASE WHEN v.vol_regime = 'low_vol' THEN 1 ELSE 0 END AS is_low_vol,
  CASE WHEN v.vol_regime = 'normal_vol' THEN 1 ELSE 0 END AS is_normal_vol,
  CASE WHEN v.vol_regime = 'high_vol' THEN 1 ELSE 0 END AS is_high_vol
FROM `cbi-v14.models.training_dataset_enhanced` e
LEFT JOIN `cbi-v14.models_v4.fx_derived_features` fx 
  ON e.date = fx.date
LEFT JOIN `cbi-v14.models_v4.monetary_derived_features` m 
  ON e.date = m.date
LEFT JOIN `cbi-v14.models_v4.fundamentals_derived_features` f 
  ON e.date = f.date
LEFT JOIN `cbi-v14.models_v4.volatility_derived_features` v 
  ON e.date = v.date
"""

try:
    print("Creating super-enriched dataset (this may take a few minutes)...")
    job = client.query(super_enriched_query)
    result = job.result()
    
    # Check row count
    count_query = "SELECT COUNT(*) as row_count FROM `cbi-v14.models_v4.training_dataset_super_enriched`"
    count_df = client.query(count_query).to_dataframe()
    row_count = count_df['row_count'].iloc[0]
    
    print(f"✅ Super-Enriched Training Dataset Created!")
    print(f"   Rows: {row_count}")
except Exception as e:
    print(f"❌ Error creating super-enriched dataset: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 80)
print("✅ DATA INTEGRATION COMPLETE")
print("=" * 80)
print()
print("Created Tables:")
print("  1. ✅ fx_derived_features")
print("  2. ✅ monetary_derived_features")
print("  3. ✅ fundamentals_derived_features")
print("  4. ✅ volatility_derived_features")
print("  5. ✅ training_dataset_super_enriched")
print()
print("New Features Added:")
print("  - FX Rates (USD/CNY, USD/BRL, Dollar Index)")
print("  - FX Momentum (7-day changes)")
print("  - Fed Policy (Fed Funds Rate)")
print("  - Real Yield & Yield Curve")
print("  - Supply-Demand Fundamentals")
print("  - Volatility Regimes")
print("  - Crude Oil Momentum")
print()
print("Total Features: ~200+ (vs 179 previously)")
print()
print("=" * 80)
print("Next: Retrain all models with complete data")
print("=" * 80)












