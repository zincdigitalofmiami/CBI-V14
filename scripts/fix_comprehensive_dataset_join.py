#!/usr/bin/env python3
"""
FIX THE COMPREHENSIVE NEURAL TRAINING DATASET JOIN ISSUE
The weather data is causing a 13,715x row explosion
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def fix_comprehensive_dataset():
    """Fix the JOIN explosion in comprehensive dataset"""
    
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_neural_training_dataset_comprehensive` AS
    WITH targets AS (
        -- Clean soybean oil prices with targets
        SELECT 
            DATE(time) as date,
            close as zl_price_current,
            
            -- 5 forecast horizons
            LEAD(close, 7) OVER (ORDER BY time) as target_1w,
            LEAD(close, 30) OVER (ORDER BY time) as target_1m,
            LEAD(close, 90) OVER (ORDER BY time) as target_3m,
            LEAD(close, 180) OVER (ORDER BY time) as target_6m,
            LEAD(close, 365) OVER (ORDER BY time) as target_12m,
            
            -- Price features
            LAG(close, 1) OVER (ORDER BY time) as zl_price_lag1,
            LAG(close, 7) OVER (ORDER BY time) as zl_price_lag7,
            LAG(close, 30) OVER (ORDER BY time) as zl_price_lag30,
            
            -- Returns
            (close - LAG(close, 1) OVER (ORDER BY time)) / NULLIF(LAG(close, 1) OVER (ORDER BY time), 0) as return_1d,
            (close - LAG(close, 7) OVER (ORDER BY time)) / NULLIF(LAG(close, 7) OVER (ORDER BY time), 0) as return_7d,
            (close - LAG(close, 30) OVER (ORDER BY time)) / NULLIF(LAG(close, 30) OVER (ORDER BY time), 0) as return_30d,
            
            -- Moving averages
            AVG(close) OVER (ORDER BY time ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma_7d,
            AVG(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as ma_30d,
            AVG(close) OVER (ORDER BY time ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as ma_90d,
            
            -- Volatility
            STDDEV(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as volatility_30d,
            
            -- Volume
            volume as zl_volume,
            AVG(volume) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as avg_volume_30d
            
        FROM `cbi-v14.forecasting_data_warehouse.vw_soybean_oil_daily_clean`
        WHERE DATE(time) >= '2020-01-01'
    ),
    big8_signals AS (
        -- Big 8 signals - already properly aggregated by date
        SELECT 
            date,
            feature_vix_stress,
            feature_harvest_pace,
            feature_china_relations,
            feature_tariff_threat,
            feature_geopolitical_volatility,
            feature_biofuel_cascade,
            feature_hidden_correlation,
            feature_biofuel_ethanol,
            big8_composite_score,
            market_regime as big8_regime,
            primary_driver
        FROM `cbi-v14.neural.vw_big_eight_signals`
    ),
    correlations AS (
        -- Correlation features - already one row per date
        SELECT 
            date,
            COALESCE(corr_zl_crude_7d, 0) as corr_zl_crude_7d,
            COALESCE(corr_zl_palm_7d, 0) as corr_zl_palm_7d,
            COALESCE(corr_zl_vix_7d, 0) as corr_zl_vix_7d,
            COALESCE(corr_zl_dxy_7d, 0) as corr_zl_dxy_7d,
            COALESCE(corr_zl_crude_30d, 0) as corr_zl_crude_30d,
            COALESCE(corr_zl_palm_30d, 0) as corr_zl_palm_30d,
            COALESCE(corr_zl_vix_30d, 0) as corr_zl_vix_30d,
            COALESCE(corr_zl_dxy_30d, 0) as corr_zl_dxy_30d,
            COALESCE(corr_zl_crude_90d, 0) as corr_zl_crude_90d,
            COALESCE(corr_zl_palm_90d, 0) as corr_zl_palm_90d,
            COALESCE(corr_zl_crude_180d, 0) as corr_zl_crude_180d,
            COALESCE(corr_zl_crude_365d, 0) as corr_zl_crude_365d
        FROM `cbi-v14.models.vw_correlation_features`
    ),
    weather_aggregated AS (
        -- FIX: Properly aggregate weather data FIRST to one row per date
        SELECT 
            date,
            AVG(CASE WHEN region LIKE '%Brazil%' OR region LIKE '%Mato Grosso%' THEN temp_max END) as brazil_weather_temp,
            AVG(CASE WHEN region LIKE '%Brazil%' OR region LIKE '%Mato Grosso%' THEN precip_mm END) as brazil_weather_precip,
            AVG(CASE WHEN region LIKE '%Argentina%' THEN temp_max END) as argentina_temp,
            AVG(CASE WHEN region LIKE '%Argentina%' THEN precip_mm END) as argentina_precip,
            AVG(CASE WHEN region LIKE '%US%' OR region LIKE '%Iowa%' OR region LIKE '%Illinois%' THEN temp_max END) as us_temp,
            AVG(CASE WHEN region LIKE '%US%' OR region LIKE '%Iowa%' OR region LIKE '%Illinois%' THEN precip_mm END) as us_precip
        FROM `cbi-v14.forecasting_data_warehouse.weather_data`
        GROUP BY date
    ),
    sentiment_aggregated AS (
        -- FIX: Properly aggregate sentiment FIRST to one row per date
        SELECT 
            DATE(timestamp) as date,
            AVG(sentiment_score) as avg_sentiment,
            STDDEV(sentiment_score) as sentiment_volatility,
            COUNT(*) as sentiment_volume
        FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
        GROUP BY DATE(timestamp)
    ),
    china_import AS (
        -- Already one row per date
        SELECT 
            date,
            china_mentions,
            import_posts,
            china_sentiment,
            import_demand_index,
            trade_status as china_trade_status
        FROM `cbi-v14.models.vw_china_import_tracker`
    ),
    brazil_export AS (
        -- Already one row per date
        SELECT 
            date,
            season_phase as brazil_season,
            export_capacity_index,
            harvest_pressure as brazil_harvest_pressure,
            export_status as brazil_export_status,
            temperature_c as brazil_temp,
            precipitation_mm as brazil_precip
        FROM `cbi-v14.models.vw_brazil_export_lineup`
    ),
    trump_xi AS (
        -- Already one row per date
        SELECT 
            date,
            trump_mentions,
            china_mentions as xi_china_mentions,
            co_mentions as trump_xi_co_mentions,
            tension_index as trump_xi_tension,
            volatility_multiplier as trump_xi_vol_mult,
            tension_regime as trump_xi_regime
        FROM `cbi-v14.models.vw_trump_xi_volatility`
    ),
    biofuel_bridge AS (
        -- Already one row per date
        SELECT 
            date,
            epa_mandate_strength,
            brazil_blend_pct,
            soy_palm_ratio,
            biofuel_demand_index,
            biofuel_bridge_score,
            biofuel_regime
        FROM `cbi-v14.models.vw_biofuel_bridge_features`
    ),
    market_regimes AS (
        -- Already one row per date
        SELECT 
            t.date,
            trade_war_impact_score,
            supply_glut_score,
            bear_market_score,
            biofuel_demand_score
        FROM `cbi-v14.signals.vw_trade_war_impact` t
        JOIN `cbi-v14.signals.vw_supply_glut_indicator` s ON t.date = s.date
        JOIN `cbi-v14.signals.vw_bear_market_regime` b ON t.date = b.date
        JOIN `cbi-v14.signals.vw_biofuel_policy_intensity` p ON t.date = p.date
    ),
    seasonality AS (
        -- Already one row per date
        SELECT 
            date,
            seasonal_index,
            monthly_zscore,
            agricultural_phase,
            harvest_pressure as seasonal_harvest_pressure,
            yoy_change
        FROM `cbi-v14.models.vw_seasonality_features`
    ),
    events AS (
        -- Already one row per date
        SELECT 
            date,
            is_wasde_day,
            is_fomc_day,
            is_major_usda_day,
            expected_volatility_multiplier as event_vol_mult,
            market_regime as event_regime
        FROM `cbi-v14.models.vw_event_driven_features`
    ),
    lead_lag AS (
        -- Already one row per date
        SELECT 
            date,
            palm_lag1,
            palm_lag2,
            crude_lag1,
            vix_lag1,
            palm_momentum_3d,
            crude_momentum_2d,
            lead_signal
        FROM `cbi-v14.models.vw_cross_asset_lead_lag`
    ),
    crush_margins AS (
        -- Already one row per date
        SELECT 
            date,
            crush_margin,
            crush_margin_7d_ma,
            crush_margin_30d_ma,
            profitability_status
        FROM `cbi-v14.models.vw_crush_margins`
    )
    
    -- MAIN SELECT - COMBINE EVERYTHING
    SELECT 
        t.date,
        
        -- ========== TARGETS ==========
        t.target_1w,
        t.target_1m,
        t.target_3m,
        t.target_6m,
        t.target_12m,
        
        -- ========== PRICE FEATURES ==========
        t.zl_price_current,
        t.zl_price_lag1,
        t.zl_price_lag7,
        t.zl_price_lag30,
        t.return_1d,
        t.return_7d,
        t.return_30d,
        t.ma_7d,
        t.ma_30d,
        t.ma_90d,
        t.volatility_30d,
        t.zl_volume,
        t.avg_volume_30d,
        
        -- ========== BIG 8 SIGNALS ==========
        COALESCE(b8.feature_vix_stress, 0.5) as feature_vix_stress,
        COALESCE(b8.feature_harvest_pace, 0.5) as feature_harvest_pace,
        COALESCE(b8.feature_china_relations, 0.5) as feature_china_relations,
        COALESCE(b8.feature_tariff_threat, 0.3) as feature_tariff_threat,
        COALESCE(b8.feature_geopolitical_volatility, 0.4) as feature_geopolitical_volatility,
        COALESCE(b8.feature_biofuel_cascade, 0.5) as feature_biofuel_cascade,
        COALESCE(b8.feature_hidden_correlation, 0.0) as feature_hidden_correlation,
        COALESCE(b8.feature_biofuel_ethanol, 0.5) as feature_biofuel_ethanol,
        COALESCE(b8.big8_composite_score, 0.5) as big8_composite_score,
        
        -- ========== CORRELATIONS ==========
        c.corr_zl_crude_7d,
        c.corr_zl_palm_7d,
        c.corr_zl_vix_7d,
        c.corr_zl_crude_30d,
        c.corr_zl_palm_30d,
        c.corr_zl_crude_90d,
        c.corr_zl_palm_90d,
        c.corr_zl_crude_180d,
        c.corr_zl_crude_365d,
        
        -- ========== CHINA IMPORT ==========
        COALESCE(ci.china_mentions, 0) as china_mentions,
        COALESCE(ci.import_posts, 0) as import_posts,
        COALESCE(ci.china_sentiment, 0.5) as china_sentiment,
        COALESCE(ci.import_demand_index, 0.5) as import_demand_index,
        
        -- ========== BRAZIL EXPORT ==========
        COALESCE(be.export_capacity_index, 1.0) as brazil_export_capacity,
        COALESCE(be.brazil_harvest_pressure, 0.5) as brazil_harvest_pressure,
        COALESCE(be.brazil_temp, 25) as brazil_temp,
        COALESCE(be.brazil_precip, 100) as brazil_precip,
        
        -- ========== TRUMP-XI VOLATILITY ==========
        COALESCE(tx.trump_mentions, 0) as trump_mentions,
        COALESCE(tx.trump_xi_co_mentions, 0) as trump_xi_co_mentions,
        COALESCE(tx.trump_xi_tension, 0.0) as trump_xi_tension,
        COALESCE(tx.trump_xi_vol_mult, 1.0) as trump_xi_vol_mult,
        
        -- ========== BIOFUEL BRIDGE ==========
        COALESCE(bf.epa_mandate_strength, 1.0) as epa_mandate_strength,
        COALESCE(bf.soy_palm_ratio, 1.0) as soy_palm_ratio,
        COALESCE(bf.biofuel_demand_index, 0.5) as biofuel_demand_index,
        COALESCE(bf.biofuel_bridge_score, 0.5) as biofuel_bridge_score,
        
        -- ========== MARKET REGIMES ==========
        COALESCE(mr.trade_war_impact_score, 0.0) as trade_war_impact,
        COALESCE(mr.supply_glut_score, 0.0) as supply_glut_score,
        COALESCE(mr.bear_market_score, 0.0) as bear_market_score,
        
        -- ========== SEASONALITY ==========
        COALESCE(sz.seasonal_index, 1.0) as seasonal_index,
        COALESCE(sz.monthly_zscore, 0.0) as monthly_zscore,
        COALESCE(sz.yoy_change, 0.0) as yoy_change,
        
        -- ========== EVENTS ==========
        COALESCE(ev.is_wasde_day, 0) as is_wasde_day,
        COALESCE(ev.is_major_usda_day, 0) as is_major_usda_day,
        COALESCE(ev.event_vol_mult, 1.0) as event_vol_mult,
        
        -- ========== LEAD/LAG ==========
        COALESCE(ll.palm_lag1, 0) as palm_lag1,
        COALESCE(ll.crude_lag1, 0) as crude_lag1,
        COALESCE(ll.palm_momentum_3d, 0) as palm_momentum_3d,
        
        -- ========== CRUSH MARGINS ==========
        COALESCE(cm.crush_margin, 0) as crush_margin,
        CASE 
            WHEN cm.profitability_status = 'HIGHLY_PROFITABLE' THEN 1.0
            WHEN cm.profitability_status = 'PROFITABLE' THEN 0.75
            WHEN cm.profitability_status = 'BREAKEVEN' THEN 0.5
            WHEN cm.profitability_status = 'UNPROFITABLE' THEN 0.25
            ELSE 0.5
        END as profitability_index,
        
        -- ========== WEATHER (FIXED AGGREGATION) ==========
        COALESCE(w.brazil_weather_temp, 25) as weather_brazil_temp,
        COALESCE(w.brazil_weather_precip, 100) as weather_brazil_precip,
        COALESCE(w.argentina_temp, 20) as weather_argentina_temp,
        COALESCE(w.us_temp, 20) as weather_us_temp,
        
        -- ========== SENTIMENT (FIXED AGGREGATION) ==========
        COALESCE(s.avg_sentiment, 0.5) as avg_sentiment,
        COALESCE(s.sentiment_volatility, 0.1) as sentiment_volatility,
        COALESCE(s.sentiment_volume, 0) as sentiment_volume,
        
        -- ========== METADATA ==========
        EXTRACT(DAYOFWEEK FROM t.date) as day_of_week,
        EXTRACT(MONTH FROM t.date) as month,
        EXTRACT(QUARTER FROM t.date) as quarter
        
    FROM targets t
    LEFT JOIN big8_signals b8 ON t.date = b8.date
    LEFT JOIN correlations c ON t.date = c.date
    LEFT JOIN china_import ci ON t.date = ci.date
    LEFT JOIN brazil_export be ON t.date = be.date
    LEFT JOIN trump_xi tx ON t.date = tx.date
    LEFT JOIN biofuel_bridge bf ON t.date = bf.date
    LEFT JOIN market_regimes mr ON t.date = mr.date
    LEFT JOIN seasonality sz ON t.date = sz.date
    LEFT JOIN events ev ON t.date = ev.date
    LEFT JOIN lead_lag ll ON t.date = ll.date
    LEFT JOIN crush_margins cm ON t.date = cm.date
    LEFT JOIN weather_aggregated w ON t.date = w.date  -- Use pre-aggregated weather
    LEFT JOIN sentiment_aggregated s ON t.date = s.date  -- Use pre-aggregated sentiment
    
    WHERE t.target_12m IS NOT NULL  -- Must have all targets
    AND t.date >= '2020-01-01'
    
    ORDER BY t.date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Fixed comprehensive neural training dataset!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to fix comprehensive dataset: {e}")
        return False

def verify_fixed_dataset():
    """Verify the fixed dataset has proper row count"""
    
    query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT date) as unique_dates,
        MIN(date) as min_date,
        MAX(date) as max_date
    FROM `cbi-v14.models.vw_neural_training_dataset_comprehensive`
    """
    
    result = client.query(query).result()
    for row in result:
        print(f"\n✅ FIXED DATASET STATS:")
        print(f"  Total rows: {row.total_rows:,}")
        print(f"  Unique dates: {row.unique_dates:,}")
        print(f"  Date range: {row.min_date} to {row.max_date}")
        
        if row.total_rows == row.unique_dates:
            print(f"  ✅ PERFECT! One row per date as expected!")
            return True
        else:
            print(f"  ⚠️ Still have {row.total_rows // row.unique_dates} rows per date")
            return False
    
    return False

def main():
    print("=" * 80)
    print("FIXING COMPREHENSIVE NEURAL TRAINING DATASET JOIN ISSUE")
    print("=" * 80)
    print("\nThe weather and sentiment data were not pre-aggregated, causing 13,715x row explosion")
    
    # Fix the dataset
    print("\n1. Fixing comprehensive dataset with proper aggregation...")
    success = fix_comprehensive_dataset()
    
    if success:
        # Verify it worked
        print("\n2. Verifying fixed dataset...")
        is_fixed = verify_fixed_dataset()
        
        if is_fixed:
            # Check column count
            query = """
            SELECT COUNT(*) as column_count
            FROM `cbi-v14.models.INFORMATION_SCHEMA.COLUMNS`
            WHERE table_name = 'vw_neural_training_dataset_comprehensive'
            """
            
            result = client.query(query).result()
            for row in result:
                print(f"\n  Dataset has {row.column_count} columns")
            
            print("\n" + "=" * 80)
            print("✅ SUCCESS! COMPREHENSIVE DATASET FIXED AND READY!")
            print("=" * 80)
            print("\n🎯 NOW TRULY READY FOR TRAINING WITH:")
            print("  • Proper one-row-per-date structure")
            print("  • All 77+ features integrated")
            print("  • No JOIN explosions")
            print("  • Clean, production-ready data")
        else:
            print("\n⚠️ Dataset updated but may still have issues")
    else:
        print("\n❌ Failed to fix dataset")
    
    return success and is_fixed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
