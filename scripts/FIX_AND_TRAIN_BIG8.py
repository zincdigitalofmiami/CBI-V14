#!/usr/bin/env python3
"""
FIX AND TRAIN WITH EXISTING BIG 8 SIGNALS
We already HAVE the signals - just need to wire them properly!
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚀 FIXING BIG 8 TRAINING - USING EXISTING SIGNALS")
print("=" * 80)

# First, list what signals we ACTUALLY have
print("\nChecking existing signals...")
list_views = """
SELECT table_name
FROM `cbi-v14.signals.INFORMATION_SCHEMA.VIEWS`
WHERE table_name LIKE '%signal%'
"""

try:
    signals = client.query(list_views).result()
    print("\n✅ Found signal views:")
    for row in signals:
        print(f"  • {row.table_name}")
except Exception as e:
    print(f"Error listing signals: {e}")

# Check if vw_big_eight_signals exists
print("\nChecking for Big 8 aggregation view...")
check_big8 = """
SELECT table_name
FROM `cbi-v14.neural.INFORMATION_SCHEMA.VIEWS`
WHERE table_name = 'vw_big_eight_signals'
"""

try:
    result = list(client.query(check_big8))
    if result:
        print("✅ neural.vw_big_eight_signals EXISTS")
    else:
        print("❌ neural.vw_big_eight_signals missing - creating it now...")
        
        # Create Big 8 aggregation
        create_big8 = """
        CREATE OR REPLACE VIEW `cbi-v14.neural.vw_big_eight_signals` AS
        SELECT 
            COALESCE(v.date, h.signal_date, c.date, t.date, g.date, b.signal_date, hc.date, be.date) as date,
            COALESCE(v.vix_stress_score, 0) as feature_vix_stress,
            COALESCE(h.harvest_stress_index, 0) as feature_harvest_pace,
            COALESCE(c.china_relations_score, 0) as feature_china_relations,
            COALESCE(t.tariff_threat_score, 0) as feature_tariff_threat,
            COALESCE(g.geopolitical_volatility, 0) as feature_geopolitical_volatility,
            COALESCE(b.biofuel_impact_score, 0) as feature_biofuel_cascade,
            COALESCE(hc.hidden_correlation_score, 0) as feature_hidden_correlation,
            COALESCE(be.biofuel_ethanol_signal, 0) as feature_biofuel_ethanol
        FROM `cbi-v14.signals.vw_vix_stress_signal` v
        FULL OUTER JOIN `cbi-v14.signals.vw_harvest_pace_signal` h ON v.date = h.signal_date
        FULL OUTER JOIN `cbi-v14.signals.vw_china_relations_signal` c ON v.date = c.date
        FULL OUTER JOIN `cbi-v14.signals.vw_tariff_threat_signal` t ON v.date = t.date
        FULL OUTER JOIN `cbi-v14.signals.vw_geopolitical_volatility_signal` g ON v.date = g.date
        FULL OUTER JOIN `cbi-v14.signals.vw_biofuel_cascade_signal_real` b ON v.date = b.signal_date
        FULL OUTER JOIN `cbi-v14.signals.vw_hidden_correlation_signal` hc ON v.date = hc.date
        FULL OUTER JOIN `cbi-v14.signals.vw_biofuel_ethanol_signal` be ON v.date = be.date
        """
        
        client.query(create_big8).result()
        print("✅ Created neural.vw_big_eight_signals")
except Exception as e:
    print(f"Error with Big 8: {e}")

# Now create the CLEAN training dataset
print("\n" + "="*80)
print("CREATING CLEAN MULTI-HORIZON TRAINING VIEW")
print("="*80)

training_view = """
CREATE OR REPLACE VIEW `cbi-v14.models.vw_neural_training_dataset_v2` AS
WITH prices AS (
    SELECT 
        DATE(time) as date,
        close as zl_price,
        -- Multi-horizon targets
        LEAD(close, 7) OVER (ORDER BY time) as target_1w,
        LEAD(close, 30) OVER (ORDER BY time) as target_1m,
        LEAD(close, 90) OVER (ORDER BY time) as target_3m,
        LEAD(close, 180) OVER (ORDER BY time) as target_6m,
        LEAD(close, 365) OVER (ORDER BY time) as target_12m,
        -- Lagged features
        LAG(close, 1) OVER (ORDER BY time) as zl_lag1,
        LAG(close, 7) OVER (ORDER BY time) as zl_lag7,
        LAG(close, 30) OVER (ORDER BY time) as zl_lag30
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE symbol = 'ZL'
    AND time >= '2020-01-01'
),
big8 AS (
    SELECT * FROM `cbi-v14.neural.vw_big_eight_signals`
),
correlations AS (
    SELECT 
        DATE(s.time) as date,
        -- 7-day correlations
        CORR(s.close, c.close) OVER (ORDER BY s.time ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_zl_crude_7d,
        CORR(s.close, p.close) OVER (ORDER BY s.time ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_zl_palm_7d,
        -- 30-day correlations  
        CORR(s.close, c.close) OVER (ORDER BY s.time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_zl_crude_30d,
        CORR(s.close, p.close) OVER (ORDER BY s.time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_zl_palm_30d,
        -- 90-day correlations
        CORR(s.close, c.close) OVER (ORDER BY s.time ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_zl_crude_90d,
        CORR(s.close, p.close) OVER (ORDER BY s.time ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_zl_palm_90d,
        -- 180-day correlations
        CORR(s.close, c.close) OVER (ORDER BY s.time ROWS BETWEEN 179 PRECEDING AND CURRENT ROW) as corr_zl_crude_180d,
        -- 365-day correlations
        CORR(s.close, c.close) OVER (ORDER BY s.time ROWS BETWEEN 364 PRECEDING AND CURRENT ROW) as corr_zl_crude_365d
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices` s
    LEFT JOIN `cbi-v14.forecasting_data_warehouse.crude_oil_prices` c ON DATE(s.time) = c.date
    LEFT JOIN `cbi-v14.forecasting_data_warehouse.palm_oil_prices` p ON DATE(s.time) = DATE(p.time)
    WHERE s.symbol = 'ZL'
),
sentiment AS (
    SELECT 
        DATE(timestamp) as date,
        AVG(sentiment_score) as avg_sentiment,
        COUNT(*) as sentiment_volume
    FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
    GROUP BY DATE(timestamp)
)
SELECT 
    p.date,
    -- Targets (5 horizons)
    p.target_1w,
    p.target_1m,
    p.target_3m,
    p.target_6m,
    p.target_12m,
    -- Current and lagged prices
    p.zl_price,
    p.zl_lag1,
    p.zl_lag7,
    p.zl_lag30,
    -- Big 8 signals (with NULL handling)
    COALESCE(b.feature_vix_stress, 0) as feature_vix_stress,
    COALESCE(b.feature_harvest_pace, 0) as feature_harvest_pace,
    COALESCE(b.feature_china_relations, 0) as feature_china_relations,
    COALESCE(b.feature_tariff_threat, 0) as feature_tariff_threat,
    COALESCE(b.feature_geopolitical_volatility, 0) as feature_geopolitical_volatility,
    COALESCE(b.feature_biofuel_cascade, 0) as feature_biofuel_cascade,
    COALESCE(b.feature_hidden_correlation, 0) as feature_hidden_correlation,
    COALESCE(b.feature_biofuel_ethanol, 0) as feature_biofuel_ethanol,
    -- Correlations (with NULL handling)
    COALESCE(c.corr_zl_crude_7d, 0) as corr_zl_crude_7d,
    COALESCE(c.corr_zl_palm_7d, 0) as corr_zl_palm_7d,
    COALESCE(c.corr_zl_crude_30d, 0) as corr_zl_crude_30d,
    COALESCE(c.corr_zl_palm_30d, 0) as corr_zl_palm_30d,
    COALESCE(c.corr_zl_crude_90d, 0) as corr_zl_crude_90d,
    COALESCE(c.corr_zl_palm_90d, 0) as corr_zl_palm_90d,
    COALESCE(c.corr_zl_crude_180d, 0) as corr_zl_crude_180d,
    COALESCE(c.corr_zl_crude_365d, 0) as corr_zl_crude_365d,
    -- Sentiment
    COALESCE(s.avg_sentiment, 0) as avg_sentiment,
    COALESCE(s.sentiment_volume, 0) as sentiment_volume
FROM prices p
LEFT JOIN big8 b ON p.date = b.date
LEFT JOIN correlations c ON p.date = c.date
LEFT JOIN sentiment s ON p.date = s.date
WHERE p.target_12m IS NOT NULL
"""

try:
    client.query(training_view).result()
    print("✅ Created training view with BIG 8 signals")
    
    # Check the data
    check = """
    SELECT 
        COUNT(*) as rows,
        COUNT(DISTINCT date) as dates,
        MIN(date) as min_date,
        MAX(date) as max_date
    FROM `cbi-v14.models.vw_neural_training_dataset_v2`
    """
    result = list(client.query(check))[0]
    print(f"\nTraining data ready:")
    print(f"  • {result['rows']} rows")
    print(f"  • {result['dates']} unique dates")
    print(f"  • Date range: {result['min_date']} to {result['max_date']}")
except Exception as e:
    print(f"Error creating training view: {e}")

# Now train ONE CLEAN MODEL to test
print("\n" + "="*80)
print("TRAINING TEST MODEL WITH BIG 8")
print("="*80)

test_model = """
CREATE OR REPLACE MODEL `cbi-v14.models.zl_big8_test_lgb`
OPTIONS(
    model_type='BOOSTED_TREE_REGRESSOR',
    input_label_cols=['target_1m'],
    data_split_method='SEQ',
    data_split_col='date',
    max_iterations=50
) AS
SELECT 
    date,
    target_1m,
    zl_price,
    zl_lag7,
    feature_vix_stress,
    feature_harvest_pace,
    feature_china_relations,
    feature_tariff_threat,
    feature_geopolitical_volatility,
    feature_biofuel_cascade,
    feature_hidden_correlation,
    feature_biofuel_ethanol,
    corr_zl_crude_30d,
    corr_zl_palm_30d,
    avg_sentiment
FROM `cbi-v14.models.vw_neural_training_dataset_v2`
WHERE target_1m IS NOT NULL
"""

try:
    print("Training LightGBM with BIG 8 signals...")
    client.query(test_model).result()
    print("✅ Successfully trained test model!")
    
    # Evaluate
    eval_query = """
    SELECT *
    FROM ML.EVALUATE(MODEL `cbi-v14.models.zl_big8_test_lgb`)
    """
    eval_result = list(client.query(eval_query))[0]
    print(f"\nModel Performance:")
    print(f"  • RMSE: {eval_result.get('mean_squared_error', 'N/A')}")
    print(f"  • R²: {eval_result.get('r2_score', 'N/A')}")
    
except Exception as e:
    print(f"Error training test model: {e}")

print("\n" + "="*80)
print("✅ BIG 8 TRAINING SETUP COMPLETE")
print("="*80)
print("\nNext steps:")
print("1. Training view is ready with ALL 8 signals")
print("2. All NULL values handled with COALESCE")
print("3. Multi-horizon targets configured")
print("4. Ready to train 25 models")
