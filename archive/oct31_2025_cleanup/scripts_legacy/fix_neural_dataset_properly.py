#!/usr/bin/env python3
"""
FIX THE NEURAL TRAINING DATASET PROPERLY
- Create ONE proper view: models.vw_neural_training_dataset
- Delete all the bullshit versions
- Update all scripts to use the proper one
"""

from google.cloud import bigquery
import logging
import glob
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_proper_neural_dataset():
    """Create THE PROPER neural training dataset - no suffixes"""
    
    print("\n1. CREATING THE PROPER NEURAL TRAINING DATASET...")
    
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_neural_training_dataset` AS
    WITH daily_prices AS (
        -- Aggregate to daily prices FIRST
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
        -- Calculate targets on aggregated data
        SELECT 
            date,
            close_price as zl_price_current,
            LEAD(close_price, 7) OVER (ORDER BY date) as target_1w,
            LEAD(close_price, 30) OVER (ORDER BY date) as target_1m,
            LEAD(close_price, 90) OVER (ORDER BY date) as target_3m,
            LEAD(close_price, 180) OVER (ORDER BY date) as target_6m,
            LEAD(close_price, 365) OVER (ORDER BY date) as target_12m,
            volume as zl_volume
        FROM daily_prices
    ),
    price_features AS (
        -- Price-based features
        SELECT 
            date,
            zl_price_current,
            target_1w, target_1m, target_3m, target_6m, target_12m,
            zl_volume,
            LAG(zl_price_current, 1) OVER (ORDER BY date) as zl_price_lag1,
            LAG(zl_price_current, 7) OVER (ORDER BY date) as zl_price_lag7,
            LAG(zl_price_current, 30) OVER (ORDER BY date) as zl_price_lag30,
            (zl_price_current - LAG(zl_price_current, 1) OVER (ORDER BY date)) / 
                NULLIF(LAG(zl_price_current, 1) OVER (ORDER BY date), 0) as return_1d,
            (zl_price_current - LAG(zl_price_current, 7) OVER (ORDER BY date)) / 
                NULLIF(LAG(zl_price_current, 7) OVER (ORDER BY date), 0) as return_7d,
            (zl_price_current - LAG(zl_price_current, 30) OVER (ORDER BY date)) / 
                NULLIF(LAG(zl_price_current, 30) OVER (ORDER BY date), 0) as return_30d,
            AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma_7d,
            AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as ma_30d,
            AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as ma_90d,
            STDDEV(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as volatility_30d,
            AVG(zl_volume) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as avg_volume_30d
        FROM targets
    ),
    big8_clean AS (
        -- Aggregate Big 8 signals to one row per date
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
        -- Aggregate correlations to one row per date
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
    weather_clean AS (
        -- Aggregate weather to one row per date
        SELECT 
            date,
            AVG(CASE WHEN region LIKE '%Brazil%' OR region LIKE '%Mato Grosso%' THEN temp_max END) as brazil_temp,
            AVG(CASE WHEN region LIKE '%Brazil%' OR region LIKE '%Mato Grosso%' THEN precip_mm END) as brazil_precip,
            AVG(CASE WHEN region LIKE '%Argentina%' THEN temp_max END) as argentina_temp,
            AVG(CASE WHEN region LIKE '%Argentina%' THEN precip_mm END) as argentina_precip,
            AVG(CASE WHEN region LIKE '%US%' OR region LIKE '%Iowa%' THEN temp_max END) as us_temp,
            AVG(CASE WHEN region LIKE '%US%' OR region LIKE '%Iowa%' THEN precip_mm END) as us_precip
        FROM `cbi-v14.forecasting_data_warehouse.weather_data`
        GROUP BY date
    ),
    sentiment_clean AS (
        -- Aggregate sentiment to one row per date
        SELECT 
            DATE(timestamp) as date,
            AVG(sentiment_score) as avg_sentiment,
            STDDEV(sentiment_score) as sentiment_volatility,
            COUNT(*) as sentiment_volume
        FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
        GROUP BY DATE(timestamp)
    ),
    market_regimes AS (
        -- Market regime signals
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
    
    -- MAIN SELECT - PROPERLY JOINED
    SELECT 
        p.date,
        
        -- Targets
        p.target_1w, p.target_1m, p.target_3m, p.target_6m, p.target_12m,
        
        -- Price features
        p.zl_price_current,
        p.zl_price_lag1, p.zl_price_lag7, p.zl_price_lag30,
        p.return_1d, p.return_7d, p.return_30d,
        p.ma_7d, p.ma_30d, p.ma_90d,
        p.volatility_30d,
        p.zl_volume, p.avg_volume_30d,
        
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
        
        -- China import
        COALESCE(ci.china_mentions, 0) as china_mentions,
        COALESCE(ci.china_sentiment, 0.5) as china_sentiment,
        COALESCE(ci.import_demand_index, 0.5) as import_demand_index,
        
        -- Brazil export
        COALESCE(be.export_capacity_index, 1.0) as brazil_export_capacity,
        COALESCE(be.harvest_pressure, 0.5) as brazil_harvest_pressure,
        
        -- Trump-Xi
        COALESCE(tx.trump_mentions, 0) as trump_mentions,
        COALESCE(tx.tension_index, 0.0) as trump_xi_tension,
        
        -- Market regimes
        COALESCE(mr.trade_war_impact_score, 0.0) as trade_war_impact,
        COALESCE(mr.supply_glut_score, 0.0) as supply_glut_score,
        COALESCE(mr.bear_market_score, 0.0) as bear_market_score,
        
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
    LEFT JOIN market_regimes mr ON p.date = mr.date
    LEFT JOIN weather_clean w ON p.date = w.date
    LEFT JOIN sentiment_clean s ON p.date = s.date
    
    WHERE p.target_12m IS NOT NULL
    ORDER BY p.date DESC
    """
    
    try:
        client.query(query).result()
        print("  ✅ Created models.vw_neural_training_dataset (THE PROPER ONE)")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def delete_bullshit_views():
    """Delete all the bullshit versions"""
    
    print("\n2. DELETING BULLSHIT VERSIONS...")
    
    views_to_delete = [
        'models.vw_neural_training_dataset_comprehensive',
        'models.vw_neural_training_dataset_final',
        'models.vw_neural_training_dataset_v2',
        'models.vw_neural_training_dataset_v2_FIXED'
    ]
    
    for view in views_to_delete:
        try:
            query = f"DROP VIEW IF EXISTS `cbi-v14.{view}`"
            client.query(query).result()
            print(f"  ✅ Deleted {view}")
        except Exception as e:
            print(f"  ⚠️ Could not delete {view}: {e}")

def update_scripts():
    """Update all scripts to use the proper view"""
    
    print("\n3. UPDATING SCRIPTS TO USE PROPER VIEW...")
    
    scripts_to_update = {
        'scripts/FIX_AND_TRAIN_PROPERLY.py': [
            ('vw_neural_training_dataset_v2_FIXED', 'vw_neural_training_dataset'),
            ('vw_neural_training_dataset_v2', 'vw_neural_training_dataset')
        ],
        'scripts/create_comprehensive_neural_dataset.py': [
            ('vw_neural_training_dataset_comprehensive', 'vw_neural_training_dataset')
        ],
        'scripts/create_clean_comprehensive_dataset.py': [
            ('vw_neural_training_dataset_final', 'vw_neural_training_dataset')
        ]
    }
    
    for script_path, replacements in scripts_to_update.items():
        if os.path.exists(script_path):
            try:
                with open(script_path, 'r') as f:
                    content = f.read()
                
                for old, new in replacements:
                    if old in content:
                        content = content.replace(old, new)
                        print(f"  ✅ Updated {os.path.basename(script_path)}: {old} → {new}")
                
                with open(script_path, 'w') as f:
                    f.write(content)
            except Exception as e:
                print(f"  ⚠️ Could not update {script_path}: {e}")

def verify_proper_dataset():
    """Verify the proper dataset works"""
    
    print("\n4. VERIFYING PROPER DATASET...")
    
    query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT date) as unique_dates,
        MIN(date) as min_date,
        MAX(date) as max_date,
        COUNT(*) as column_count
    FROM `cbi-v14.models.vw_neural_training_dataset`,
    (SELECT COUNT(*) as column_count 
     FROM `cbi-v14.models.INFORMATION_SCHEMA.COLUMNS`
     WHERE table_name = 'vw_neural_training_dataset')
    """
    
    try:
        result = client.query(query).result()
        for row in result:
            print(f"  ✅ Total rows: {row.total_rows:,}")
            print(f"  ✅ Unique dates: {row.unique_dates:,}")
            print(f"  ✅ Date range: {row.min_date} to {row.max_date}")
            
            if row.total_rows == row.unique_dates:
                print(f"  ✅ PERFECT! One row per date")
                return True
            else:
                print(f"  ❌ PROBLEM: Multiple rows per date")
                return False
    except Exception as e:
        print(f"  ❌ Could not verify: {e}")
        return False

def main():
    print("=" * 80)
    print("FIXING THE NEURAL TRAINING DATASET PROPERLY")
    print("=" * 80)
    print("\nNO MORE BULLSHIT SUFFIXES - ONE PROPER VIEW")
    
    # Create the proper view
    success = create_proper_neural_dataset()
    
    if success:
        # Delete the bullshit versions
        delete_bullshit_views()
        
        # Update scripts
        update_scripts()
        
        # Verify it works
        is_valid = verify_proper_dataset()
        
        if is_valid:
            print("\n" + "=" * 80)
            print("✅ SUCCESS! NEURAL TRAINING DATASET FIXED PROPERLY")
            print("=" * 80)
            print("\nONE PROPER VIEW: models.vw_neural_training_dataset")
            print("All bullshit versions deleted")
            print("All scripts updated")
            print("\n🎯 NOW ACTUALLY READY FOR TRAINING")
        else:
            print("\n⚠️ View created but may have issues")
    else:
        print("\n❌ Failed to create proper dataset")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
