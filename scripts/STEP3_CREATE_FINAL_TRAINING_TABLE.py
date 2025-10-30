#!/usr/bin/env python3
"""
STEP 3: CREATE FINAL BQML-COMPATIBLE TRAINING TABLE
Joins all precomputed tables + existing views (NO window functions in final query)
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("STEP 3: CREATING FINAL TRAINING TABLE WITH ALL 159 FEATURES")
print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 80)

final_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.training_full_bqml_compatible`
CLUSTER BY date
AS
SELECT 
    p.date,
    
    -- TARGETS (4 columns)
    p.target_1w,
    p.target_1m,
    p.target_3m,
    p.target_6m,
    
    -- PRICE FEATURES (from precomputed - 11 columns)
    p.zl_price_current,
    p.zl_volume,
    p.zl_price_lag1,
    p.zl_price_lag7,
    p.zl_price_lag30,
    p.return_1d,
    p.return_7d,
    p.ma_7d,
    p.ma_30d,
    p.volatility_30d,
    
    -- WEATHER FEATURES (from precomputed - 6 columns)
    w.weather_brazil_temp,
    w.weather_brazil_precip,
    w.weather_argentina_temp,
    w.weather_argentina_precip,
    w.weather_us_temp,
    w.weather_us_precip,
    
    -- SENTIMENT FEATURES (from precomputed - 3 columns)
    s.avg_sentiment,
    s.sentiment_volatility,
    s.sentiment_volume,
    
    -- BIG 8 SIGNALS (from view - 8 columns)
    COALESCE(b8.feature_vix_stress, 0.5) as feature_vix_stress,
    COALESCE(b8.feature_harvest_pace, 0.5) as feature_harvest_pace,
    COALESCE(b8.feature_china_relations, 0.5) as feature_china_relations,
    COALESCE(b8.feature_tariff_threat, 0.5) as feature_tariff_threat,
    COALESCE(b8.feature_geopolitical_volatility, 0.5) as feature_geopolitical_volatility,
    COALESCE(b8.feature_biofuel_cascade, 0.5) as feature_biofuel_cascade,
    COALESCE(b8.feature_hidden_correlation, 0.5) as feature_hidden_correlation,
    COALESCE(b8.feature_biofuel_ethanol, 0.5) as feature_biofuel_ethanol,
    
    -- CORRELATION FEATURES (from view - 28 columns)
    COALESCE(corr.corr_zl_crude_7d, 0) as corr_zl_crude_7d,
    COALESCE(corr.corr_zl_palm_7d, 0) as corr_zl_palm_7d,
    COALESCE(corr.corr_zl_vix_7d, 0) as corr_zl_vix_7d,
    COALESCE(corr.corr_zl_dxy_7d, 0) as corr_zl_dxy_7d,
    COALESCE(corr.corr_zl_corn_7d, 0) as corr_zl_corn_7d,
    COALESCE(corr.corr_zl_wheat_7d, 0) as corr_zl_wheat_7d,
    COALESCE(corr.corr_zl_crude_30d, 0) as corr_zl_crude_30d,
    COALESCE(corr.corr_zl_palm_30d, 0) as corr_zl_palm_30d,
    COALESCE(corr.corr_zl_vix_30d, 0) as corr_zl_vix_30d,
    COALESCE(corr.corr_zl_dxy_30d, 0) as corr_zl_dxy_30d,
    COALESCE(corr.corr_zl_corn_30d, 0) as corr_zl_corn_30d,
    COALESCE(corr.corr_zl_wheat_30d, 0) as corr_zl_wheat_30d,
    COALESCE(corr.corr_zl_crude_90d, 0) as corr_zl_crude_90d,
    COALESCE(corr.corr_zl_palm_90d, 0) as corr_zl_palm_90d,
    COALESCE(corr.corr_zl_vix_90d, 0) as corr_zl_vix_90d,
    COALESCE(corr.corr_zl_dxy_90d, 0) as corr_zl_dxy_90d,
    COALESCE(corr.corr_zl_corn_90d, 0) as corr_zl_corn_90d,
    COALESCE(corr.corr_zl_crude_180d, 0) as corr_zl_crude_180d,
    COALESCE(corr.corr_zl_palm_180d, 0) as corr_zl_palm_180d,
    COALESCE(corr.corr_zl_vix_180d, 0) as corr_zl_vix_180d,
    COALESCE(corr.corr_zl_dxy_180d, 0) as corr_zl_dxy_180d,
    COALESCE(corr.corr_zl_crude_365d, 0) as corr_zl_crude_365d,
    COALESCE(corr.corr_zl_palm_365d, 0) as corr_zl_palm_365d,
    COALESCE(corr.corr_zl_vix_365d, 0) as corr_zl_vix_365d,
    COALESCE(corr.corr_zl_dxy_365d, 0) as corr_zl_dxy_365d,
    COALESCE(corr.corr_zl_corn_365d, 0) as corr_zl_corn_365d,
    COALESCE(corr.corr_palm_crude_30d, 0) as corr_palm_crude_30d,
    COALESCE(corr.corr_corn_wheat_30d, 0) as corr_corn_wheat_30d,
    
    -- SEASONALITY FEATURES (from view - ~10 columns)
    COALESCE(season.month, EXTRACT(MONTH FROM p.date)) as month,
    COALESCE(season.quarter, EXTRACT(QUARTER FROM p.date)) as quarter,
    COALESCE(season.is_harvest_season, 0) as is_harvest_season,
    COALESCE(season.is_planting_season, 0) as is_planting_season,
    COALESCE(season.days_to_harvest, 180) as days_to_harvest,
    
    -- CRUSH MARGINS (from view - ~4 columns)
    COALESCE(crush.crush_margin, 500) as crush_margin,
    COALESCE(crush.crush_margin_7d_ma, 500) as crush_margin_7d_ma,
    COALESCE(crush.crush_margin_30d_ma, 500) as crush_margin_30d_ma,
    COALESCE(crush.crush_margin_zscore, 0) as crush_margin_zscore,
    
    -- CHINA IMPORT FEATURES (from view - ~10 columns)
    COALESCE(china.soybean_imports_mt, 0) as china_soybean_imports_mt,
    COALESCE(china.oil_imports_mt, 0) as china_oil_imports_mt,
    COALESCE(china.import_growth_rate, 0) as china_import_growth_rate,
    COALESCE(china.china_sentiment, 0.5) as china_sentiment,
    COALESCE(china.china_sentiment_volatility, 0) as china_sentiment_volatility,
    COALESCE(china.china_sentiment_30d_ma, 0.5) as china_sentiment_30d_ma,
    COALESCE(china.import_seasonality, 1) as import_seasonality,
    
    -- BRAZIL EXPORT FEATURES (from view - ~9 columns)
    COALESCE(brazil.soybean_exports_mt, 0) as brazil_soybean_exports_mt,
    COALESCE(brazil.soy_oil_exports_mt, 0) as brazil_soy_oil_exports_mt,
    COALESCE(brazil.export_growth_rate, 0) as brazil_export_growth_rate,
    COALESCE(brazil.brazil_weather_index, 1) as brazil_weather_index,
    COALESCE(brazil.harvest_progress_pct, 50) as harvest_progress_pct,
    COALESCE(brazil.brazil_real_usd, 5.0) as brazil_real_usd,
    
    -- TRUMP/XI VOLATILITY (from view - ~13 columns)
    COALESCE(trump.trump_tweets_count, 0) as trump_tweets_count,
    COALESCE(trump.xi_mentions_count, 0) as xi_mentions_count,
    COALESCE(trump.trade_war_intensity, 0.5) as trade_war_intensity,
    COALESCE(trump.tariff_announcement_flag, 0) as tariff_announcement_flag,
    COALESCE(trump.co_mention_sentiment, 0.5) as co_mention_sentiment,
    COALESCE(trump.trumpxi_sentiment_volatility, 0) as trumpxi_sentiment_volatility,
    COALESCE(trump.geopolitical_risk_index, 0.5) as geopolitical_risk_index,
    
    -- TRADE WAR IMPACT (from view - ~5 columns)
    COALESCE(tw.trade_war_impact_score, 0.5) as trade_war_impact_score,
    COALESCE(tw.tariff_rate_soy, 0) as tariff_rate_soy,
    COALESCE(tw.trade_policy_uncertainty, 0.5) as trade_policy_uncertainty,
    
    -- EVENT DRIVEN FEATURES (from view - ~16 columns)
    COALESCE(events.vix_current, 20) as vix_current,
    COALESCE(events.vix_7d_change, 0) as vix_7d_change,
    COALESCE(events.vix_30d_ma, 20) as vix_30d_ma,
    COALESCE(events.drought_index, 0) as drought_index,
    COALESCE(events.flood_risk_index, 0) as flood_risk_index,
    COALESCE(events.usda_report_week, 0) as usda_report_week,
    COALESCE(events.fomc_meeting_week, 0) as fomc_meeting_week,
    COALESCE(events.earnings_season, 0) as earnings_season,
    
    -- CROSS ASSET LEAD/LAG (from view - ~28 columns)
    COALESCE(lag.crude_lead_1d, 0) as crude_lead_1d,
    COALESCE(lag.crude_lead_3d, 0) as crude_lead_3d,
    COALESCE(lag.crude_lead_5d, 0) as crude_lead_5d,
    COALESCE(lag.crude_lag_1d, 0) as crude_lag_1d,
    COALESCE(lag.crude_lag_3d, 0) as crude_lag_3d,
    COALESCE(lag.palm_lead_1d, 0) as palm_lead_1d,
    COALESCE(lag.palm_lead_3d, 0) as palm_lead_3d,
    COALESCE(lag.palm_lag_1d, 0) as palm_lag_1d,
    COALESCE(lag.palm_lag_3d, 0) as palm_lag_3d,
    COALESCE(lag.corn_lead_1d, 0) as corn_lead_1d,
    COALESCE(lag.corn_lag_1d, 0) as corn_lag_1d,
    COALESCE(lag.dxy_lead_1d, 0) as dxy_lead_1d,
    COALESCE(lag.dxy_lag_1d, 0) as dxy_lag_1d,
    COALESCE(lag.vix_lead_1d, 0) as vix_lead_1d,
    COALESCE(lag.vix_lag_1d, 0) as vix_lag_1d

FROM `cbi-v14.models.price_features_precomputed` p

-- Join precomputed tables (NO window functions)
LEFT JOIN `cbi-v14.models.weather_features_precomputed` w
    ON p.date = w.date
LEFT JOIN `cbi-v14.models.sentiment_features_precomputed` s
    ON p.date = s.date

-- Join existing views (these have NO window functions internally)
LEFT JOIN `cbi-v14.neural.vw_big_eight_signals` b8
    ON p.date = b8.date
LEFT JOIN `cbi-v14.models.vw_correlation_features` corr
    ON p.date = corr.date
LEFT JOIN `cbi-v14.models.vw_seasonality_features` season
    ON p.date = season.date
LEFT JOIN `cbi-v14.models.vw_crush_margins` crush
    ON p.date = crush.date
LEFT JOIN `cbi-v14.models.vw_china_import_tracker` china
    ON p.date = china.date
LEFT JOIN `cbi-v14.models.vw_brazil_export_lineup` brazil
    ON p.date = brazil.date
LEFT JOIN `cbi-v14.models.vw_trump_xi_volatility` trump
    ON p.date = trump.date
LEFT JOIN `cbi-v14.signals.vw_trade_war_impact` tw
    ON p.date = tw.date
LEFT JOIN `cbi-v14.models.vw_event_driven_features` events
    ON p.date = events.date
LEFT JOIN `cbi-v14.models.vw_cross_asset_lead_lag` lag
    ON p.date = lag.date

WHERE p.target_6m IS NOT NULL
AND p.date >= '2020-01-01'

ORDER BY p.date DESC
"""

print("\nCreating training_full_bqml_compatible...")
print("(Joining 13 feature sources with NO window functions in final query)")

try:
    job = client.query(final_query)
    result = job.result()
    
    # Verify
    stats = list(client.query("""
    SELECT 
        COUNT(*) as row_count,
        COUNT(DISTINCT date) as unique_dates,
        MIN(date) as min_date,
        MAX(date) as max_date
    FROM `cbi-v14.models.training_full_bqml_compatible`
    """).result())[0]
    
    cols = list(client.query("""
    SELECT COUNT(*) as col_count
    FROM `cbi-v14.models.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'training_full_bqml_compatible'
    """).result())[0]
    
    print(f"\n✅ SUCCESS!")
    print(f"   Rows: {stats.row_count:,}")
    print(f"   Unique dates: {stats.unique_dates:,}")
    print(f"   Date range: {stats.min_date} to {stats.max_date}")
    print(f"   Columns: {cols.col_count}")
    print(f"   Features: {cols.col_count - 5} (excluding date + 4 targets)")
    
    print("\n" + "=" * 80)
    print("✅ STEP 3 COMPLETE - READY FOR STEP 4 (BQML COMPATIBILITY TEST)")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ FAILED: {str(e)[:300]}")

print(f"\nCompleted: {datetime.now().strftime('%H:%M:%S')}")













