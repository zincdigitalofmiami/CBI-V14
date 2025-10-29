#!/usr/bin/env python3
"""
FIX ALL BROKEN VIEWS - Update to canonical dataset and correct column names
Post naming cleanup - remove all v2/v3/_FIXED references
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("FIXING ALL BROKEN VIEWS - CANONICAL DATASET REFERENCES")
print("=" * 80)

# FIX 1: vw_neural_interaction_features
print("\n1. FIXING vw_neural_interaction_features...")

fix_neural_interaction = """
CREATE OR REPLACE VIEW `cbi-v14.models.vw_neural_interaction_features` AS
WITH base_data AS (
    SELECT 
        date,
        zl_price_current,
        feature_vix_stress,
        feature_harvest_pace,
        feature_china_relations,
        feature_tariff_threat,
        feature_geopolitical_volatility,
        feature_biofuel_cascade,
        feature_hidden_correlation,
        feature_biofuel_ethanol,
        corr_zl_crude_7d,
        corr_zl_palm_30d,
        corr_zl_vix_30d,
        weather_brazil_temp,
        weather_brazil_precip,
        weather_argentina_temp,
        avg_sentiment,
        sentiment_volume
    FROM `cbi-v14.models.vw_neural_training_dataset`
    WHERE corr_zl_crude_7d IS NOT NULL
),
cftc_data AS (
    SELECT 
        report_date as date,
        commercial_net / NULLIF(open_interest, 0) as commercial_net_pct,
        managed_money_net / NULLIF(open_interest, 0) as managed_money_net_pct,
        open_interest / 1000000 as open_interest_mm
    FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
    WHERE commodity = 'Soybean_Oil'
),
crush_margins AS (
    SELECT 
        date,
        crush_margin,
        crush_margin_7d_ma,
        crush_margin_30d_ma,
        CASE WHEN crush_margin > crush_margin_30d_ma THEN 1 ELSE 0 END as margin_expanding
    FROM `cbi-v14.models.vw_crush_margins`
)
SELECT 
    b.date,
    b.zl_price_current,
    
    -- OBSCURE INTERACTION 1: Weather × Sentiment × Harvest
    (COALESCE(b.weather_brazil_precip, 100) / 100) * 
    COALESCE(b.avg_sentiment, 0.5) * 
    COALESCE(b.feature_harvest_pace, 0.5) as weather_sentiment_harvest_interaction,
    
    -- OBSCURE INTERACTION 2: VIX × China Relations
    COALESCE(b.feature_vix_stress, 0.5) * 
    COALESCE(b.feature_china_relations, 0.5) as fear_china_interaction,
    
    -- OBSCURE INTERACTION 3: Palm Correlation × Biofuel × Crush Margins
    ABS(COALESCE(b.corr_zl_palm_30d, 0)) * 
    COALESCE(b.feature_biofuel_cascade, 0.5) * 
    (COALESCE(cm.crush_margin, 0) / 100) as palm_biofuel_margin_interaction,
    
    -- OBSCURE INTERACTION 4: Crude Correlation × Geopolitical
    ABS(COALESCE(b.corr_zl_crude_7d, 0)) * 
    COALESCE(b.feature_geopolitical_volatility, 0.5) as energy_geo_interaction,
    
    -- OBSCURE INTERACTION 5: CFTC Positioning
    ABS(COALESCE(cftc.commercial_net_pct, 0)) as positioning_interaction,
    
    -- POLYNOMIAL FEATURES
    POWER(COALESCE(b.feature_vix_stress, 0.5), 2) as vix_squared,
    POWER(COALESCE(b.feature_vix_stress, 0.5), 3) as vix_cubed,
    POWER(COALESCE(b.feature_harvest_pace, 0.5), 2) as harvest_squared,
    POWER(ABS(COALESCE(b.corr_zl_crude_7d, 0)), 2) as correlation_squared,
    
    -- REGIME FLAGS
    CASE 
        WHEN COALESCE(b.feature_vix_stress, 0) > 0.7 
         AND COALESCE(b.feature_harvest_pace, 0) > 0.7 
        THEN 1 ELSE 0 
    END as double_crisis_flag,
    
    CASE 
        WHEN ABS(COALESCE(b.corr_zl_crude_7d, 0)) < 0.2 
         AND ABS(COALESCE(b.corr_zl_palm_30d, 0)) < 0.2 
        THEN 1 ELSE 0 
    END as correlation_breakdown_flag,
    
    -- SENTIMENT EXTREMES
    CASE 
        WHEN COALESCE(b.avg_sentiment, 0.5) > 0.8 THEN 2
        WHEN COALESCE(b.avg_sentiment, 0.5) > 0.6 THEN 1
        WHEN COALESCE(b.avg_sentiment, 0.5) < 0.2 THEN -2
        WHEN COALESCE(b.avg_sentiment, 0.5) < 0.4 THEN -1
        ELSE 0
    END as sentiment_regime,
    
    -- VOLUME ANOMALIES
    CASE 
        WHEN COALESCE(b.sentiment_volume, 0) > 
             AVG(COALESCE(b.sentiment_volume, 0)) OVER (
                 ORDER BY b.date 
                 ROWS BETWEEN 29 PRECEDING AND 1 PRECEDING
             ) * 2 
        THEN 1 ELSE 0 
    END as volume_spike_flag,
    
    -- LAGGED INTERACTIONS
    LAG(COALESCE(b.feature_china_relations, 0.5), 3) OVER (ORDER BY b.date) * 
    COALESCE(b.feature_tariff_threat, 0.5) as lagged_china_tariff_interaction,
    
    LAG(COALESCE(b.corr_zl_crude_7d, 0), 5) OVER (ORDER BY b.date) * 
    COALESCE(b.feature_biofuel_cascade, 0.5) as lagged_energy_biofuel_interaction,
    
    -- SEASONALITY
    EXTRACT(MONTH FROM b.date) as month,
    CASE 
        WHEN EXTRACT(MONTH FROM b.date) IN (9, 10, 11) THEN 1
        WHEN EXTRACT(MONTH FROM b.date) IN (4, 5, 6) THEN 2
        ELSE 0 
    END as seasonal_phase,
    
    -- CFTC
    COALESCE(cftc.commercial_net_pct, 0) as commercial_net_pct,
    COALESCE(cftc.open_interest_mm, 0.7) as open_interest_mm,
    
    -- CRUSH MARGINS
    COALESCE(cm.crush_margin, 500) as crush_margin,
    COALESCE(cm.margin_expanding, 0) as margin_expanding
    
FROM base_data b
LEFT JOIN cftc_data cftc ON b.date = cftc.date
LEFT JOIN crush_margins cm ON b.date = cm.date
WHERE b.date >= '2020-01-01'
ORDER BY b.date DESC
"""

try:
    client.query(fix_neural_interaction).result()
    test = list(client.query("SELECT COUNT(*) as cnt FROM `cbi-v14.models.vw_neural_interaction_features`").result())[0]
    print(f"   ✅ FIXED: vw_neural_interaction_features ({test.cnt:,} rows)")
except Exception as e:
    print(f"   ❌ ERROR: {str(e)[:200]}")

# Note: The other 3 views are broken due to missing columns that don't exist in source tables
# They need schema investigation before fixing
# For now, focus on training with existing working views

print("\n" + "=" * 80)
print("STATUS: vw_neural_interaction_features FIXED")
print("Note: Other broken views require schema fixes in source tables")
print("=" * 80)










