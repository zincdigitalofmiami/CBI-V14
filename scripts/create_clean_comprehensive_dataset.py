#!/usr/bin/env python3
"""
CREATE CLEAN COMPREHENSIVE NEURAL TRAINING DATASET
This version properly handles duplicates and aggregates everything to one row per date
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_clean_comprehensive_dataset():
    """Create a CLEAN comprehensive dataset with no duplicates"""
    
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_neural_training_dataset` AS
    WITH daily_prices AS (
        -- First aggregate to daily prices
        SELECT 
            DATE(time) as date,
            AVG(close) as close_price,
            SUM(volume) as volume
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
        WHERE symbol = 'ZL'
        AND DATE(time) >= '2020-01-01'
        GROUP BY DATE(time)
    ),
    targets AS (
        -- Then calculate targets on the aggregated data
        SELECT 
            date,
            close_price as zl_price_current,
            
            -- 5 forecast horizons
            LEAD(close_price, 7) OVER (ORDER BY date) as target_1w,
            LEAD(close_price, 30) OVER (ORDER BY date) as target_1m,
            LEAD(close_price, 90) OVER (ORDER BY date) as target_3m,
            LEAD(close_price, 180) OVER (ORDER BY date) as target_6m,
            LEAD(close_price, 365) OVER (ORDER BY date) as target_12m,
            
            -- Volume
            volume as zl_volume
            
        FROM daily_prices
    ),
    price_features AS (
        -- Calculate price features separately to avoid window function issues
        SELECT 
            date,
            zl_price_current,
            target_1w,
            target_1m,
            target_3m,
            target_6m,
            target_12m,
            zl_volume,
            
            -- Lags
            LAG(zl_price_current, 1) OVER (ORDER BY date) as zl_price_lag1,
            LAG(zl_price_current, 7) OVER (ORDER BY date) as zl_price_lag7,
            LAG(zl_price_current, 30) OVER (ORDER BY date) as zl_price_lag30,
            
            -- Returns
            (zl_price_current - LAG(zl_price_current, 1) OVER (ORDER BY date)) / 
                NULLIF(LAG(zl_price_current, 1) OVER (ORDER BY date), 0) as return_1d,
            (zl_price_current - LAG(zl_price_current, 7) OVER (ORDER BY date)) / 
                NULLIF(LAG(zl_price_current, 7) OVER (ORDER BY date), 0) as return_7d,
            (zl_price_current - LAG(zl_price_current, 30) OVER (ORDER BY date)) / 
                NULLIF(LAG(zl_price_current, 30) OVER (ORDER BY date), 0) as return_30d,
            
            -- Moving averages
            AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma_7d,
            AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as ma_30d,
            AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as ma_90d,
            
            -- Volatility
            STDDEV(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as volatility_30d,
            
            -- Volume MA
            AVG(zl_volume) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as avg_volume_30d
            
        FROM targets
    ),
    big8_clean AS (
        -- Clean Big 8 signals - aggregate to one row per date
        SELECT 
            date,
            AVG(feature_vix_stress) as feature_vix_stress,
            AVG(feature_harvest_pace) as feature_harvest_pace,
            AVG(feature_china_relations) as feature_china_relations,
            AVG(feature_tariff_threat) as feature_tariff_threat,
            AVG(feature_geopolitical_volatility) as feature_geopolitical_volatility,
            AVG(feature_biofuel_cascade) as feature_biofuel_cascade,
            AVG(feature_hidden_correlation) as feature_hidden_correlation,
            AVG(feature_biofuel_ethanol) as feature_biofuel_ethanol,
            AVG(big8_composite_score) as big8_composite_score
        FROM `cbi-v14.neural.vw_big_eight_signals`
        GROUP BY date
    ),
    correlations_clean AS (
        -- Clean correlations - aggregate to one row per date
        SELECT 
            date,
            AVG(corr_zl_crude_7d) as corr_zl_crude_7d,
            AVG(corr_zl_palm_7d) as corr_zl_palm_7d,
            AVG(corr_zl_vix_7d) as corr_zl_vix_7d,
            AVG(corr_zl_crude_30d) as corr_zl_crude_30d,
            AVG(corr_zl_palm_30d) as corr_zl_palm_30d,
            AVG(corr_zl_crude_90d) as corr_zl_crude_90d,
            AVG(corr_zl_palm_90d) as corr_zl_palm_90d,
            AVG(corr_zl_crude_180d) as corr_zl_crude_180d,
            AVG(corr_zl_crude_365d) as corr_zl_crude_365d
        FROM `cbi-v14.models.vw_correlation_features`
        GROUP BY date
    ),
    crush_clean AS (
        -- Clean crush margins - aggregate to one row per date
        SELECT 
            date,
            AVG(crush_margin) as crush_margin,
            AVG(crush_margin_7d_ma) as crush_margin_7d_ma,
            AVG(crush_margin_30d_ma) as crush_margin_30d_ma,
            STRING_AGG(profitability_status ORDER BY profitability_status LIMIT 1) as profitability_status
        FROM `cbi-v14.models.vw_crush_margins`
        GROUP BY date
    ),
    seasonality_clean AS (
        -- Clean seasonality - aggregate to one row per date
        SELECT 
            date,
            AVG(seasonal_index) as seasonal_index,
            AVG(monthly_zscore) as monthly_zscore,
            AVG(yoy_change) as yoy_change,
            STRING_AGG(agricultural_phase ORDER BY agricultural_phase LIMIT 1) as agricultural_phase
        FROM `cbi-v14.models.vw_seasonality_features`
        GROUP BY date
    ),
    lead_lag_clean AS (
        -- Clean lead/lag - aggregate to one row per date
        SELECT 
            date,
            AVG(palm_lag1) as palm_lag1,
            AVG(crude_lag1) as crude_lag1,
            AVG(palm_momentum_3d) as palm_momentum_3d,
            AVG(crude_momentum_2d) as crude_momentum_2d
        FROM `cbi-v14.models.vw_cross_asset_lead_lag`
        GROUP BY date
    ),
    weather_clean AS (
        -- Clean weather - properly aggregate to one row per date
        SELECT 
            date,
            AVG(CASE WHEN region LIKE '%Brazil%' OR region LIKE '%Mato Grosso%' THEN temp_max END) as brazil_temp,
            AVG(CASE WHEN region LIKE '%Brazil%' OR region LIKE '%Mato Grosso%' THEN precip_mm END) as brazil_precip,
            AVG(CASE WHEN region LIKE '%Argentina%' THEN temp_max END) as argentina_temp,
            AVG(CASE WHEN region LIKE '%Argentina%' THEN precip_mm END) as argentina_precip,
            AVG(CASE WHEN region LIKE '%US%' OR region LIKE '%Iowa%' OR region LIKE '%Illinois%' THEN temp_max END) as us_temp,
            AVG(CASE WHEN region LIKE '%US%' OR region LIKE '%Iowa%' OR region LIKE '%Illinois%' THEN precip_mm END) as us_precip
        FROM `cbi-v14.forecasting_data_warehouse.weather_data`
        GROUP BY date
    ),
    sentiment_clean AS (
        -- Clean sentiment - properly aggregate to one row per date
        SELECT 
            DATE(timestamp) as date,
            AVG(sentiment_score) as avg_sentiment,
            STDDEV(sentiment_score) as sentiment_volatility,
            COUNT(*) as sentiment_volume
        FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
        GROUP BY DATE(timestamp)
    ),
    market_regimes AS (
        -- Market regime signals - these should already be one per date
        SELECT 
            t.date,
            t.trade_war_impact_score,
            s.supply_glut_score,
            b.bear_market_score,
            p.biofuel_demand_score
        FROM `cbi-v14.signals.vw_trade_war_impact` t
        LEFT JOIN `cbi-v14.signals.vw_supply_glut_indicator` s ON t.date = s.date
        LEFT JOIN `cbi-v14.signals.vw_bear_market_regime` b ON t.date = b.date
        LEFT JOIN `cbi-v14.signals.vw_biofuel_policy_intensity` p ON t.date = p.date
    )
    
    -- MAIN SELECT - COMBINE EVERYTHING WITH PROPER JOINS
    SELECT 
        p.date,
        
        -- Targets
        p.target_1w,
        p.target_1m,
        p.target_3m,
        p.target_6m,
        p.target_12m,
        
        -- Price features
        p.zl_price_current,
        p.zl_price_lag1,
        p.zl_price_lag7,
        p.zl_price_lag30,
        p.return_1d,
        p.return_7d,
        p.return_30d,
        p.ma_7d,
        p.ma_30d,
        p.ma_90d,
        p.volatility_30d,
        p.zl_volume,
        p.avg_volume_30d,
        
        -- Big 8 signals
        COALESCE(b8.feature_vix_stress, 0.5) as feature_vix_stress,
        COALESCE(b8.feature_harvest_pace, 0.5) as feature_harvest_pace,
        COALESCE(b8.feature_china_relations, 0.5) as feature_china_relations,
        COALESCE(b8.feature_tariff_threat, 0.3) as feature_tariff_threat,
        COALESCE(b8.feature_geopolitical_volatility, 0.4) as feature_geopolitical_volatility,
        COALESCE(b8.feature_biofuel_cascade, 0.5) as feature_biofuel_cascade,
        COALESCE(b8.feature_hidden_correlation, 0.0) as feature_hidden_correlation,
        COALESCE(b8.feature_biofuel_ethanol, 0.5) as feature_biofuel_ethanol,
        COALESCE(b8.big8_composite_score, 0.5) as big8_composite_score,
        
        -- Correlations
        COALESCE(c.corr_zl_crude_7d, 0) as corr_zl_crude_7d,
        COALESCE(c.corr_zl_palm_7d, 0) as corr_zl_palm_7d,
        COALESCE(c.corr_zl_vix_7d, 0) as corr_zl_vix_7d,
        COALESCE(c.corr_zl_crude_30d, 0) as corr_zl_crude_30d,
        COALESCE(c.corr_zl_palm_30d, 0) as corr_zl_palm_30d,
        COALESCE(c.corr_zl_crude_90d, 0) as corr_zl_crude_90d,
        COALESCE(c.corr_zl_palm_90d, 0) as corr_zl_palm_90d,
        COALESCE(c.corr_zl_crude_180d, 0) as corr_zl_crude_180d,
        COALESCE(c.corr_zl_crude_365d, 0) as corr_zl_crude_365d,
        
        -- China import (already clean, one row per date)
        COALESCE(ci.china_mentions, 0) as china_mentions,
        COALESCE(ci.china_sentiment, 0.5) as china_sentiment,
        COALESCE(ci.import_demand_index, 0.5) as import_demand_index,
        
        -- Brazil export (already clean)
        COALESCE(be.export_capacity_index, 1.0) as brazil_export_capacity,
        COALESCE(be.harvest_pressure, 0.5) as brazil_harvest_pressure,
        
        -- Trump-Xi (already clean)
        COALESCE(tx.trump_mentions, 0) as trump_mentions,
        COALESCE(tx.tension_index, 0.0) as trump_xi_tension,
        
        -- Biofuel (aggregate if needed)
        COALESCE(bf.epa_mandate_strength, 1.0) as epa_mandate_strength,
        COALESCE(bf.biofuel_demand_index, 0.5) as biofuel_demand_index,
        
        -- Market regimes
        COALESCE(mr.trade_war_impact_score, 0.0) as trade_war_impact,
        COALESCE(mr.supply_glut_score, 0.0) as supply_glut_score,
        COALESCE(mr.bear_market_score, 0.0) as bear_market_score,
        
        -- Seasonality
        COALESCE(sz.seasonal_index, 1.0) as seasonal_index,
        COALESCE(sz.monthly_zscore, 0.0) as monthly_zscore,
        COALESCE(sz.yoy_change, 0.0) as yoy_change,
        
        -- Events (already clean)
        COALESCE(ev.is_wasde_day, 0) as is_wasde_day,
        COALESCE(ev.expected_volatility_multiplier, 1.0) as event_vol_mult,
        
        -- Lead/lag
        COALESCE(ll.palm_lag1, 0) as palm_lag1,
        COALESCE(ll.crude_lag1, 0) as crude_lag1,
        COALESCE(ll.palm_momentum_3d, 0) as palm_momentum_3d,
        
        -- Crush margins
        COALESCE(cm.crush_margin, 0) as crush_margin,
        CASE 
            WHEN cm.profitability_status = 'HIGHLY_PROFITABLE' THEN 1.0
            WHEN cm.profitability_status = 'PROFITABLE' THEN 0.75
            WHEN cm.profitability_status = 'BREAKEVEN' THEN 0.5
            WHEN cm.profitability_status = 'UNPROFITABLE' THEN 0.25
            ELSE 0.5
        END as profitability_index,
        
        -- Weather
        COALESCE(w.brazil_temp, 25) as weather_brazil_temp,
        COALESCE(w.brazil_precip, 100) as weather_brazil_precip,
        COALESCE(w.argentina_temp, 20) as weather_argentina_temp,
        COALESCE(w.us_temp, 20) as weather_us_temp,
        
        -- Sentiment
        COALESCE(s.avg_sentiment, 0.5) as avg_sentiment,
        COALESCE(s.sentiment_volatility, 0.1) as sentiment_volatility,
        COALESCE(s.sentiment_volume, 0) as sentiment_volume,
        
        -- Metadata
        EXTRACT(DAYOFWEEK FROM p.date) as day_of_week,
        EXTRACT(MONTH FROM p.date) as month,
        EXTRACT(QUARTER FROM p.date) as quarter
        
    FROM price_features p
    LEFT JOIN big8_clean b8 ON p.date = b8.date
    LEFT JOIN correlations_clean c ON p.date = c.date
    LEFT JOIN `cbi-v14.models.vw_china_import_tracker` ci ON p.date = ci.date
    LEFT JOIN `cbi-v14.models.vw_brazil_export_lineup` be ON p.date = be.date
    LEFT JOIN `cbi-v14.models.vw_trump_xi_volatility` tx ON p.date = tx.date
    LEFT JOIN (
        SELECT date, AVG(epa_mandate_strength) as epa_mandate_strength, 
               AVG(biofuel_demand_index) as biofuel_demand_index
        FROM `cbi-v14.models.vw_biofuel_bridge_features`
        GROUP BY date
    ) bf ON p.date = bf.date
    LEFT JOIN market_regimes mr ON p.date = mr.date
    LEFT JOIN seasonality_clean sz ON p.date = sz.date
    LEFT JOIN `cbi-v14.models.vw_event_driven_features` ev ON p.date = ev.date
    LEFT JOIN lead_lag_clean ll ON p.date = ll.date
    LEFT JOIN crush_clean cm ON p.date = cm.date
    LEFT JOIN weather_clean w ON p.date = w.date
    LEFT JOIN sentiment_clean s ON p.date = s.date
    
    WHERE p.target_12m IS NOT NULL  -- Must have all targets
    
    ORDER BY p.date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created CLEAN comprehensive neural training dataset!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create clean dataset: {e}")
        return False

def verify_clean_dataset():
    """Verify the clean dataset has proper structure"""
    
    # Check row count
    query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT date) as unique_dates,
        MIN(date) as min_date,
        MAX(date) as max_date
    FROM `cbi-v14.models.vw_neural_training_dataset`
    """
    
    result = client.query(query).result()
    for row in result:
        print(f"\n✅ CLEAN DATASET STATS:")
        print(f"  Total rows: {row.total_rows:,}")
        print(f"  Unique dates: {row.unique_dates:,}")
        print(f"  Date range: {row.min_date} to {row.max_date}")
        
        if row.total_rows == row.unique_dates:
            print(f"  ✅ PERFECT! One row per date as expected!")
            perfect = True
        else:
            print(f"  ⚠️ Still have {row.total_rows / row.unique_dates:.1f} rows per date")
            perfect = False
    
    # Check column count
    query2 = """
    SELECT COUNT(*) as column_count
    FROM `cbi-v14.models.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'vw_neural_training_dataset'
    """
    
    result2 = client.query(query2).result()
    for row in result2:
        print(f"\n  Dataset has {row.column_count} columns")
        
    return perfect

def main():
    print("=" * 80)
    print("CREATING CLEAN COMPREHENSIVE NEURAL TRAINING DATASET")
    print("=" * 80)
    print("\nThis version properly aggregates all duplicates to one row per date")
    
    # Create the clean dataset
    print("\n1. Creating clean comprehensive dataset...")
    success = create_clean_comprehensive_dataset()
    
    if success:
        # Verify it worked
        print("\n2. Verifying clean dataset...")
        is_clean = verify_clean_dataset()
        
        if is_clean:
            print("\n" + "=" * 80)
            print("✅ SUCCESS! CLEAN COMPREHENSIVE DATASET CREATED!")
            print("=" * 80)
            print("\n🎯 TRULY READY FOR TRAINING WITH:")
            print("  • ONE row per date (no duplicates)")
            print("  • 70+ features properly integrated")
            print("  • All aggregations handled correctly")
            print("  • Production-ready structure")
            print("\n📊 Dataset name: models.vw_neural_training_dataset")
        else:
            print("\n⚠️ Dataset created but may still have minor issues")
    else:
        print("\n❌ Failed to create clean dataset")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
