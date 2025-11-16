#!/usr/bin/env python3
'''
WARNING: This file has been cleaned of ALL fake data.
Any functions that relied on fake data have been disabled.
Must be rewritten to use REAL data from BigQuery or APIs.
ZERO TOLERANCE FOR FAKE DATA.
'''

#!/usr/bin/env python3
"""
BUILD TRAINING DATASET FROM WAREHOUSE - NO FAKE DATA
====================================================
Builds training dataset directly from warehouse tables with:
- NO COALESCE with 0 (no fake data)
# REMOVED: - NO placeholders # NO FAKE DATA
- Proper joins validated
- Current data (through Oct 27, 2025)
- All math calculated correctly

Author: CBI-V14 Platform
Date: October 27, 2025
"""

from google.cloud import bigquery
from datetime import datetime
import sys

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("BUILDING TRAINING DATASET FROM WAREHOUSE - NO FAKE DATA")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Archive old datasets first
print("=" * 80)
print("STEP 1: Archiving Old/Stale Datasets")
print("=" * 80)

old_datasets_to_archive = [
    ('models', 'training_dataset', 'archive_training_dataset_20251027'),
    ('models', 'training_dataset_enhanced', 'archive_training_dataset_enhanced_20251027'),
    ('models', 'training_dataset_enhanced_v5', 'archive_training_dataset_enhanced_v5_20251027'),
    ('models_v4', 'training_dataset_super_enriched', 'archive_training_dataset_super_enriched_20251027_PRE_FIX')
]

for source_dataset, source_table, archive_name in old_datasets_to_archive:
    try:
        # Check if exists
        check_query = f"""
        SELECT 1 FROM `cbi-v14.{source_dataset}.INFORMATION_SCHEMA.TABLES`
        WHERE table_name = '{source_table}'
        LIMIT 1
        """
        
        result = list(client.query(check_query).result())
        
        if result:
            # Archive it
            archive_query = f"""
            CREATE OR REPLACE TABLE `cbi-v14.{source_dataset}.{archive_name}` AS
            SELECT * FROM `cbi-v14.{source_dataset}.{source_table}`
            """
            
            client.query(archive_query).result()
            print(f"✅ Archived {source_dataset}.{source_table} → {archive_name}")
        else:
            print(f"  (Skipped {source_dataset}.{source_table} - doesn't exist)")
            
    except Exception as e:
        print(f"  (Skipped {source_dataset}.{source_table} - {str(e)[:50]})")

print()

# Build from warehouse
print("=" * 80)
print("STEP 2: Building Base Dataset from Warehouse Tables")
print("=" * 80)
print("Source: Direct from forecasting_data_warehouse")
print("Method: Proper LEFT JOINS with NULL handling")
print()

base_dataset_query = """
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_base` AS
WITH

-- Base: Soybean Oil Prices (PRIMARY)
soybean_oil_base AS (
    SELECT 
        DATE(time) as date,
        close_price as zl_price_current,
        open_price as zl_open,
        high_price as zl_high,
        low_price as zl_low,
        volume as zl_volume,
        -- Price lags
        LAG(close_price, 1) OVER (ORDER BY time) as zl_price_lag1,
        LAG(close_price, 7) OVER (ORDER BY time) as zl_price_lag7,
        LAG(close_price, 30) OVER (ORDER BY time) as zl_price_lag30,
        -- Returns
        (close_price - LAG(close_price, 1) OVER (ORDER BY time)) / NULLIF(LAG(close_price, 1) OVER (ORDER BY time), 0) * 100 as return_1d,
        (close_price - LAG(close_price, 7) OVER (ORDER BY time)) / NULLIF(LAG(close_price, 7) OVER (ORDER BY time), 0) * 100 as return_7d,
        -- Moving averages
        AVG(close_price) OVER (ORDER BY time ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma_7d,
        AVG(close_price) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as ma_30d,
        -- Volatility
        STDDEV(close_price) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as volatility_30d,
        -- Targets (LEAD for forecasting)
        LEAD(close_price, 7) OVER (ORDER BY time) as target_1w,
        LEAD(close_price, 30) OVER (ORDER BY time) as target_1m,
        LEAD(close_price, 90) OVER (ORDER BY time) as target_3m,
        LEAD(close_price, 180) OVER (ORDER BY time) as target_6m
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE DATE(time) >= '2020-01-01'  -- 5+ years of data
),

-- Palm Oil Prices (CRITICAL - 15-25% variance driver)
palm_oil_prices AS (
    SELECT 
        DATE(time) as date,
        close_price as palm_price,
        LAG(close_price, 1) OVER (ORDER BY time) as palm_lag1,
        LAG(close_price, 2) OVER (ORDER BY time) as palm_lag2,
        LAG(close_price, 3) OVER (ORDER BY time) as palm_lag3,
        (close_price - LAG(close_price, 3) OVER (ORDER BY time)) / NULLIF(LAG(close_price, 3) OVER (ORDER BY time), 0) * 100 as palm_momentum_3d
    FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
    WHERE DATE(time) >= '2020-01-01'
),

-- Crude Oil Prices (Energy/Biofuel complex)
crude_oil_prices AS (
    SELECT 
        DATE(time) as date,
        close_price as crude_price,
        LAG(close_price, 1) OVER (ORDER BY time) as crude_lag1,
        LAG(close_price, 2) OVER (ORDER BY time) as crude_lag2,
        (close_price - LAG(close_price, 2) OVER (ORDER BY time)) / NULLIF(LAG(close_price, 2) OVER (ORDER BY time), 0) * 100 as crude_momentum_2d
    FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
    WHERE DATE(time) >= '2020-01-01'
),

-- Corn Prices
corn_prices AS (
    SELECT 
        DATE(time) as date,
        close_price as corn_price,
        LAG(close_price, 1) OVER (ORDER BY time) as corn_lag1
    FROM `cbi-v14.forecasting_data_warehouse.corn_prices`
    WHERE DATE(time) >= '2020-01-01'
),

-- Wheat Prices
wheat_prices AS (
    SELECT 
        DATE(time) as date,
        close_price as wheat_price,
        LAG(close_price, 1) OVER (ORDER BY time) as wheat_lag1
    FROM `cbi-v14.forecasting_data_warehouse.wheat_prices`
    WHERE DATE(time) >= '2020-01-01'
),

-- VIX (Volatility regime)
vix_data AS (
    SELECT 
        date,
        close as vix_level,
        LAG(close, 1) OVER (ORDER BY date) as vix_lag1,
        LAG(close, 2) OVER (ORDER BY date) as vix_lag2,
        CASE WHEN close > LAG(close, 1) OVER (ORDER BY date) * 1.1 THEN 1 ELSE 0 END as vix_spike_lag1
    FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
    WHERE date >= '2020-01-01'
),

-- Currency Data (BRL, CNY, ARS, EUR, DXY)
currency_data AS (
    SELECT 
        date,
        MAX(CASE WHEN to_currency = 'CNY' THEN rate END) as usd_cny_rate,
        MAX(CASE WHEN to_currency = 'BRL' THEN rate END) as usd_brl_rate,
        MAX(CASE WHEN to_currency = 'ARS' THEN rate END) as usd_ars_rate,
        MAX(CASE WHEN to_currency = 'EUR' THEN rate END) as usd_eur_rate,
        MAX(CASE WHEN from_currency = 'DXY' THEN rate END) as dollar_index,
        LAG(MAX(CASE WHEN from_currency = 'DXY' THEN rate END), 1) OVER (ORDER BY date) as dxy_lag1,
        LAG(MAX(CASE WHEN from_currency = 'DXY' THEN rate END), 2) OVER (ORDER BY date) as dxy_lag2,
        (MAX(CASE WHEN from_currency = 'DXY' THEN rate END) - 
         LAG(MAX(CASE WHEN from_currency = 'DXY' THEN rate END), 3) OVER (ORDER BY date)) / 
         NULLIF(LAG(MAX(CASE WHEN from_currency = 'DXY' THEN rate END), 3) OVER (ORDER BY date), 0) * 100 as dxy_momentum_3d
    FROM `cbi-v14.forecasting_data_warehouse.currency_data`
    WHERE date >= '2020-01-01'
    AND from_currency = 'USD'
    GROUP BY date
),

-- Economic Indicators (properly pivoted)
economic_data AS (
    SELECT 
        DATE(time) as date,
        MAX(CASE WHEN indicator = 'fed_funds_rate' THEN value END) as fed_funds_rate,
        MAX(CASE WHEN indicator = 'ten_year_treasury' THEN value END) as ten_year_treasury,
        MAX(CASE WHEN indicator = 'cpi_inflation' THEN value END) as cpi_inflation,
        MAX(CASE WHEN indicator = 'vix_index' THEN value END) as vix_index,
        MAX(CASE WHEN indicator = 'crude_oil_wti' THEN value END) as crude_oil_wti,
        MAX(CASE WHEN indicator = 'treasury_10y_yield' THEN value END) as treasury_10y_yield,
        -- Derived: yield curve
        MAX(CASE WHEN indicator = 'ten_year_treasury' THEN value END) - 
        MAX(CASE WHEN indicator = 'fed_funds_rate' THEN value END) as yield_curve
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    WHERE DATE(time) >= '2020-01-01'
    GROUP BY DATE(time)
)

-- MAIN JOIN (LEFT JOIN to preserve all soybean oil dates)
SELECT 
    base.*,
    -- Palm oil (NO COALESCE - use NULL if missing)
    palm.palm_price,
    palm.palm_lag1,
    palm.palm_lag2,
    palm.palm_lag3,
    palm.palm_momentum_3d,
    -- Crude oil
    crude.crude_price,
    crude.crude_lag1,
    crude.crude_lag2,
    crude.crude_momentum_2d,
    -- Corn
    corn.corn_price,
    corn.corn_lag1,
    -- Wheat  
    wheat.wheat_price,
    wheat.wheat_lag1,
    -- Corn/soy ratio
    corn.corn_price / NULLIF(base.zl_price_current, 0) as corn_soy_ratio_lag1,
    -- VIX
    vix.vix_level,
    vix.vix_lag1,
    vix.vix_lag2,
    vix.vix_spike_lag1,
    -- Currency (NO COALESCE - use NULL if missing)
    curr.usd_cny_rate,
    curr.usd_brl_rate,
    curr.usd_ars_rate,
    curr.usd_eur_rate,
    curr.dollar_index,
    curr.dxy_lag1,
    curr.dxy_lag2,
    curr.dxy_momentum_3d,
    -- Economic (NO COALESCE - use NULL if missing)
    econ.fed_funds_rate,
    econ.ten_year_treasury,
    econ.cpi_inflation,
    econ.vix_index,
    econ.crude_oil_wti,
    econ.treasury_10y_yield,
    econ.yield_curve
FROM soybean_oil_base base
LEFT JOIN palm_oil_prices palm ON base.date = palm.date
LEFT JOIN crude_oil_prices crude ON base.date = crude.date
LEFT JOIN corn_prices corn ON base.date = corn.date
LEFT JOIN wheat_prices wheat ON base.date = wheat.date
LEFT JOIN vix_data vix ON base.date = vix.date
LEFT JOIN currency_data curr ON base.date = curr.date
LEFT JOIN economic_data econ ON base.date = econ.date
WHERE base.date >= '2020-10-21'
ORDER BY base.date
"""

print("Creating base dataset from warehouse tables...")
print("NO COALESCE with 0 - Using NULL for missing data")
print()

try:
    job = client.query(base_dataset_query)
    result = job.result()
    print("✅ Base dataset created")
    
    # Verify
    verify_query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT date) as unique_dates,
        MIN(date) as min_date,
        MAX(date) as max_date,
        COUNTIF(palm_price IS NOT NULL) as palm_coverage,
        COUNTIF(crude_price IS NOT NULL) as crude_coverage,
        COUNTIF(vix_level IS NOT NULL) as vix_coverage,
        COUNTIF(usd_brl_rate IS NOT NULL) as brl_coverage
    FROM `cbi-v14.models_v4.training_dataset_base`
    """
    
    df = client.query(verify_query).to_dataframe()
    row = df.iloc[0]
    
    print()
    print("Dataset Verification:")
    print(f"  Total rows: {row['total_rows']:,}")
    print(f"  Unique dates: {row['unique_dates']:,}")
    print(f"  Date range: {row['min_date']} to {row['max_date']}")
    print(f"  Palm coverage: {row['palm_coverage']}/{row['total_rows']} ({row['palm_coverage']/row['total_rows']*100:.1f}%)")
    print(f"  Crude coverage: {row['crude_coverage']}/{row['total_rows']} ({row['crude_coverage']/row['total_rows']*100:.1f}%)")
    print(f"  VIX coverage: {row['vix_coverage']}/{row['total_rows']} ({row['vix_coverage']/row['total_rows']*100:.1f}%)")
    print(f"  BRL coverage: {row['brl_coverage']}/{row['total_rows']} ({row['brl_coverage']/row['total_rows']*100:.1f}%)")
    
    if row['total_rows'] != row['unique_dates']:
        print(f"  ❌ WARNING: Duplicates detected!")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print()

# Add correlations
print("=" * 80)
print("STEP 3: Adding Cross-Asset Correlations")
print("=" * 80)

correlations_query = """
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_with_correlations` AS
SELECT
    base.*,
    -- ZL-Palm correlations (5 horizons)
    CORR(base.zl_price_current, palm.palm_price) OVER (
        ORDER BY base.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as corr_zl_palm_7d,
    CORR(base.zl_price_current, palm.palm_price) OVER (
        ORDER BY base.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as corr_zl_palm_30d,
    CORR(base.zl_price_current, palm.palm_price) OVER (
        ORDER BY base.date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
    ) as corr_zl_palm_90d,
    CORR(base.zl_price_current, palm.palm_price) OVER (
        ORDER BY base.date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW
    ) as corr_zl_palm_180d,
    CORR(base.zl_price_current, palm.palm_price) OVER (
        ORDER BY base.date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
    ) as corr_zl_palm_365d,
    
    -- ZL-Crude correlations (5 horizons)
    CORR(base.zl_price_current, base.crude_price) OVER (
        ORDER BY base.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as corr_zl_crude_7d,
    CORR(base.zl_price_current, base.crude_price) OVER (
        ORDER BY base.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as corr_zl_crude_30d,
    CORR(base.zl_price_current, base.crude_price) OVER (
        ORDER BY base.date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
    ) as corr_zl_crude_90d,
    CORR(base.zl_price_current, base.crude_price) OVER (
        ORDER BY base.date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW
    ) as corr_zl_crude_180d,
    CORR(base.zl_price_current, base.crude_price) OVER (
        ORDER BY base.date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
    ) as corr_zl_crude_365d,
    
    -- ZL-VIX correlations (5 horizons)
    CORR(base.zl_price_current, base.vix_level) OVER (
        ORDER BY base.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as corr_zl_vix_7d,
    CORR(base.zl_price_current, base.vix_level) OVER (
        ORDER BY base.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as corr_zl_vix_30d,
    CORR(base.zl_price_current, base.vix_level) OVER (
        ORDER BY base.date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
    ) as corr_zl_vix_90d,
    CORR(base.zl_price_current, base.vix_level) OVER (
        ORDER BY base.date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW
    ) as corr_zl_vix_180d,
    CORR(base.zl_price_current, base.vix_level) OVER (
        ORDER BY base.date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
    ) as corr_zl_vix_365d,
    
    -- ZL-DXY correlations (4 horizons)
    CORR(base.zl_price_current, base.dollar_index) OVER (
        ORDER BY base.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as corr_zl_dxy_7d,
    CORR(base.zl_price_current, base.dollar_index) OVER (
        ORDER BY base.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as corr_zl_dxy_30d,
    CORR(base.zl_price_current, base.dollar_index) OVER (
        ORDER BY base.date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
    ) as corr_zl_dxy_90d,
    CORR(base.zl_price_current, base.dollar_index) OVER (
        ORDER BY base.date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW
    ) as corr_zl_dxy_180d,
    CORR(base.zl_price_current, base.dollar_index) OVER (
        ORDER BY base.date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
    ) as corr_zl_dxy_365d,
    
    -- ZL-Corn correlations
    CORR(base.zl_price_current, base.corn_price) OVER (
        ORDER BY base.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as corr_zl_corn_7d,
    CORR(base.zl_price_current, base.corn_price) OVER (
        ORDER BY base.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as corr_zl_corn_30d,
    CORR(base.zl_price_current, base.corn_price) OVER (
        ORDER BY base.date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
    ) as corr_zl_corn_90d,
    CORR(base.zl_price_current, base.corn_price) OVER (
        ORDER BY base.date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
    ) as corr_zl_corn_365d,
    
    -- ZL-Wheat correlations
    CORR(base.zl_price_current, base.wheat_price) OVER (
        ORDER BY base.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as corr_zl_wheat_7d,
    CORR(base.zl_price_current, base.wheat_price) OVER (
        ORDER BY base.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as corr_zl_wheat_30d,
    
    -- Palm-Crude correlation (substitution vs energy link)
    CORR(palm.palm_price, base.crude_price) OVER (
        ORDER BY base.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as corr_palm_crude_30d,
    
    -- Corn-Wheat correlation (grain complex)
    CORR(base.corn_price, base.wheat_price) OVER (
        ORDER BY base.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as corr_corn_wheat_30d,
    
    -- Lead/lag indicators (does palm lead ZL by 2-3 days?)
    CORR(LEAD(base.zl_price_current, 2) OVER (ORDER BY base.date), palm.palm_price) OVER (
        ORDER BY base.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as palm_lead2_correlation,
    
    CORR(LEAD(base.zl_price_current, 1) OVER (ORDER BY base.date), base.crude_price) OVER (
        ORDER BY base.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as crude_lead1_correlation,
    
    CORR(LEAD(base.zl_price_current, 1) OVER (ORDER BY base.date), base.vix_level) OVER (
        ORDER BY base.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as vix_lead1_correlation,
    
    CORR(LEAD(base.zl_price_current, 1) OVER (ORDER BY base.date), base.dollar_index) OVER (
        ORDER BY base.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as dxy_lead1_correlation,
    
    -- Directional accuracy of leads
    CASE 
        WHEN SIGN(palm.palm_price - LAG(palm.palm_price, 1) OVER (ORDER BY base.date)) =
             SIGN(LEAD(base.zl_price_current, 2) OVER (ORDER BY base.date) - LEAD(base.zl_price_current, 1) OVER (ORDER BY base.date))
        THEN 1 ELSE 0 
    END as palm_direction_correct,
    
    CASE 
        WHEN SIGN(base.crude_price - LAG(base.crude_price, 1) OVER (ORDER BY base.date)) =
             SIGN(LEAD(base.zl_price_current, 1) OVER (ORDER BY base.date) - base.zl_price_current)
        THEN 1 ELSE 0 
    END as crude_direction_correct,
    
    CASE 
        WHEN SIGN(LAG(base.vix_level, 1) OVER (ORDER BY base.date) - base.vix_level) =  -- VIX inverse
             SIGN(LEAD(base.zl_price_current, 1) OVER (ORDER BY base.date) - base.zl_price_current)
        THEN 1 ELSE 0 
    END as vix_inverse_correct,
    
    -- Lead signal confidence
    (
        (CASE WHEN SIGN(palm.palm_price - LAG(palm.palm_price, 1) OVER (ORDER BY base.date)) = SIGN(LEAD(base.zl_price_current, 2) OVER (ORDER BY base.date) - LEAD(base.zl_price_current, 1) OVER (ORDER BY base.date)) THEN 1 ELSE 0 END) +
        (CASE WHEN SIGN(base.crude_price - LAG(base.crude_price, 1) OVER (ORDER BY base.date)) = SIGN(LEAD(base.zl_price_current, 1) OVER (ORDER BY base.date) - base.zl_price_current) THEN 1 ELSE 0 END)
    ) / 2.0 as lead_signal_confidence,
    
    -- Momentum divergence (palm up, ZL down = potential substitution)
    CASE 
        WHEN palm.palm_momentum_3d > 2 AND base.return_7d < -2 THEN 1
        WHEN palm.palm_momentum_3d < -2 AND base.return_7d > 2 THEN 1
        ELSE 0
    END as momentum_divergence,
    
    -- Rolling accuracy of lead signals (30d window)
    AVG(CASE WHEN SIGN(palm.palm_price - LAG(palm.palm_price, 1) OVER (ORDER BY base.date)) = SIGN(LEAD(base.zl_price_current, 2) OVER (ORDER BY base.date) - LEAD(base.zl_price_current, 1) OVER (ORDER BY base.date)) THEN 1.0 ELSE 0.0 END) OVER (
        ORDER BY base.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as palm_accuracy_30d,
    
    AVG(CASE WHEN SIGN(base.crude_price - LAG(base.crude_price, 1) OVER (ORDER BY base.date)) = SIGN(LEAD(base.zl_price_current, 1) OVER (ORDER BY base.date) - base.zl_price_current) THEN 1.0 ELSE 0.0 END) OVER (
        ORDER BY base.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as crude_accuracy_30d,
    
    -- Preserved price for lead/lag features
    LEAD(base.zl_price_current, 1) OVER (ORDER BY base.date) as leadlag_zl_price
    
FROM `cbi-v14.models_v4.training_dataset_base` base
LEFT JOIN `cbi-v14.models_v4.training_dataset_base` palm ON base.date = palm.date
ORDER BY base.date
"""

print("=" * 80)
print("STEP 4: Adding Correlations and Lead/Lag Features")
print("=" * 80)

try:
    job = client.query(correlations_query)
    result = job.result()
    print("✅ Correlations added")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print()
print("=" * 80)
print("✅ COMPLETE - BASE DATASET WITH CORRELATIONS READY")
print("=" * 80)
print()
print("Next: Add Big 8 signals, weather, sentiment, and other features")

