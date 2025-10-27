#!/usr/bin/env python3
"""
Create the 4 missing critical features for CBI-V14
These are essential for comprehensive market intelligence
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_biofuel_bridge_features():
    """Create biofuel bridge features using existing policy signals"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_biofuel_bridge_features` AS
    WITH biofuel_signals AS (
        -- Combine all biofuel-related signals
        SELECT 
            p.date,
            p.epa_mandate_multiplier,
            p.brazil_biodiesel_blend,
            p.policy_uncertainty,
            s.rfs_mandate_bgal,
            s.biodiesel_mandate_bgal,
            s.palm_oil_price_usd,
            s.soybean_oil_price_usd,
            e.biofuel_price_strength,
            e.soy_advantage,
            e.policy_momentum
        FROM `cbi-v14.signals.vw_biofuel_policy_intensity` p
        FULL OUTER JOIN `cbi-v14.signals.vw_biofuel_substitution_aggregates_daily` s
            ON p.date = s.date
        FULL OUTER JOIN `cbi-v14.signals.vw_biofuel_ethanol_signal` e
            ON p.date = e.date
    )
    SELECT 
        date,
        
        -- Policy drivers
        COALESCE(epa_mandate_multiplier, 1.0) as epa_mandate_strength,
        COALESCE(brazil_biodiesel_blend, 10.0) as brazil_blend_pct,
        COALESCE(policy_uncertainty, 0.5) as policy_volatility,
        
        -- Volume mandates
        COALESCE(rfs_mandate_bgal, 15.0) as rfs_volume_bgal,
        COALESCE(biodiesel_mandate_bgal, 2.5) as biodiesel_volume_bgal,
        
        -- Price dynamics
        COALESCE(soybean_oil_price_usd / NULLIF(palm_oil_price_usd, 0), 1.0) as soy_palm_ratio,
        COALESCE(biofuel_price_strength, 0.5) as biofuel_demand_index,
        COALESCE(soy_advantage, 0.0) as soy_competitive_advantage,
        COALESCE(policy_momentum, 0.0) as policy_momentum_score,
        
        -- Composite biofuel bridge score
        (
            COALESCE(epa_mandate_multiplier, 1.0) * 0.3 +
            COALESCE(biofuel_price_strength, 0.5) * 0.3 +
            (COALESCE(brazil_biodiesel_blend, 10.0) / 15.0) * 0.2 +
            COALESCE(policy_momentum, 0.0) * 0.2
        ) as biofuel_bridge_score,
        
        -- Market regime
        CASE 
            WHEN COALESCE(epa_mandate_multiplier, 1.0) > 1.5 THEN 'MANDATE_SURGE'
            WHEN COALESCE(policy_uncertainty, 0.5) > 0.7 THEN 'POLICY_CHAOS'
            WHEN COALESCE(soy_advantage, 0.0) > 0.5 THEN 'SOY_DOMINANT'
            WHEN COALESCE(biofuel_price_strength, 0.5) > 0.7 THEN 'BIOFUEL_BOOM'
            ELSE 'STABLE'
        END as biofuel_regime
        
    FROM biofuel_signals
    WHERE date IS NOT NULL
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created vw_biofuel_bridge_features")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create biofuel bridge: {e}")
        return False

def create_china_import_tracker():
    """Create China import tracker using sentiment and news"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_china_import_tracker` AS
    WITH china_sentiment AS (
        -- Extract China-related sentiment
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as china_mention_count,
            COUNT(CASE WHEN LOWER(title) LIKE '%china%' THEN 1 END) as china_posts,
            COUNT(CASE WHEN LOWER(title) LIKE '%china%' AND LOWER(title) LIKE '%import%' THEN 1 END) as china_import_posts,
            COUNT(CASE WHEN LOWER(title) LIKE '%china%' AND LOWER(title) LIKE '%soy%' THEN 1 END) as china_soy_posts,
            AVG(CASE WHEN LOWER(title) LIKE '%china%' THEN sentiment_score END) as china_sentiment,
            STDDEV(CASE WHEN LOWER(title) LIKE '%china%' THEN sentiment_score END) as china_sentiment_volatility
        FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
        GROUP BY DATE(timestamp)
    ),
    china_policy AS (
        -- Extract China policy signals
        SELECT 
            DATE(timestamp) as date,
            AVG(CASE WHEN LOWER(text) LIKE '%china%' THEN agricultural_impact END) as china_policy_impact
        FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`
        GROUP BY DATE(timestamp)
    )
    SELECT 
        COALESCE(cs.date, cp.date) as date,
        
        -- Volume metrics
        COALESCE(cs.china_mention_count, 0) as china_mentions,
        COALESCE(cs.china_posts, 0) as china_posts,
        COALESCE(cs.china_import_posts, 0) as import_posts,
        COALESCE(cs.china_soy_posts, 0) as soy_posts,
        
        -- Sentiment metrics
        COALESCE(cs.china_sentiment, 0.5) as china_sentiment,
        COALESCE(cs.china_sentiment_volatility, 0.1) as sentiment_volatility,
        COALESCE(cp.china_policy_impact, 0.0) as policy_impact,
        
        -- Import demand proxy (higher = more import demand)
        (
            COALESCE(cs.china_posts, 0) / 10.0 * 0.2 +  -- Normalize mentions
            COALESCE(cs.china_import_posts, 0) / 5.0 * 0.3 +  -- Import mentions weighted higher
            COALESCE(cs.china_sentiment, 0.5) * 0.3 +  -- Positive sentiment = more demand
            (1.0 - COALESCE(cp.china_policy_impact, 0.0)) * 0.2  -- Lower policy tension = more imports
        ) as import_demand_index,
        
        -- Trade tension indicator
        CASE 
            WHEN COALESCE(cp.china_policy_impact, 0.0) > 0.7 THEN 'HIGH_TENSION'
            WHEN COALESCE(cs.china_sentiment, 0.5) < 0.3 THEN 'NEGATIVE_SENTIMENT'
            WHEN COALESCE(cs.china_import_posts, 0) > 5 THEN 'ACTIVE_BUYING'
            ELSE 'NORMAL'
        END as trade_status,
        
        -- Moving averages for trend
        AVG(COALESCE(cs.china_posts, 0)) OVER (ORDER BY cs.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as china_posts_7d_ma,
        AVG(COALESCE(cs.china_sentiment, 0.5)) OVER (ORDER BY cs.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as china_sentiment_30d_ma
        
    FROM china_sentiment cs
    FULL OUTER JOIN china_policy cp ON cs.date = cp.date
    WHERE COALESCE(cs.date, cp.date) IS NOT NULL
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created vw_china_import_tracker")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create China import tracker: {e}")
        return False

def create_brazil_export_lineup():
    """Create Brazil export lineup using weather and seasonality"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_brazil_export_lineup` AS
    WITH brazil_weather AS (
        -- Brazil weather conditions
        SELECT 
            date,
            AVG(temp_max) as brazil_temp,
            AVG(precip_mm) as brazil_precip,
            AVG(CASE WHEN temp_max > 10 THEN temp_max - 10 ELSE 0 END) as brazil_gdd,  -- Calculate GDD
            COUNT(*) as station_count
        FROM `cbi-v14.forecasting_data_warehouse.weather_data`
        WHERE station_id LIKE 'BR%' OR region LIKE '%Brazil%'
        GROUP BY date
    ),
    seasonality AS (
        -- Brazil harvest seasons (Feb-May main harvest)
        SELECT 
            date,
            EXTRACT(MONTH FROM date) as month,
            CASE 
                WHEN EXTRACT(MONTH FROM date) BETWEEN 2 AND 5 THEN 'HARVEST'
                WHEN EXTRACT(MONTH FROM date) BETWEEN 10 AND 12 THEN 'PLANTING'
                ELSE 'GROWING'
            END as season_phase,
            CASE 
                WHEN EXTRACT(MONTH FROM date) BETWEEN 2 AND 5 THEN 1.5  -- Peak export
                WHEN EXTRACT(MONTH FROM date) BETWEEN 6 AND 8 THEN 1.2  -- Post-harvest
                ELSE 1.0
            END as export_seasonality_factor
        FROM (
            SELECT DISTINCT DATE(time) as date
            FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
            WHERE DATE(time) >= '2020-01-01'
        )
    )
    SELECT 
        s.date,
        s.month,
        s.season_phase,
        s.export_seasonality_factor,
        
        -- Weather conditions
        COALESCE(w.brazil_temp, 25.0) as temperature_c,
        COALESCE(w.brazil_precip, 100.0) as precipitation_mm,
        COALESCE(w.brazil_gdd, 15.0) as growing_degree_days,
        
        -- Export capacity index (weather + seasonality)
        s.export_seasonality_factor * 
        CASE 
            WHEN COALESCE(w.brazil_precip, 100) > 200 THEN 0.8  -- Too wet
            WHEN COALESCE(w.brazil_precip, 100) < 50 THEN 0.7   -- Too dry
            WHEN COALESCE(w.brazil_temp, 25) > 35 THEN 0.9      -- Too hot
            ELSE 1.0
        END as export_capacity_index,
        
        -- Harvest pressure (peaks during harvest season)
        CASE 
            WHEN s.season_phase = 'HARVEST' THEN 
                1.0 + (COALESCE(w.brazil_gdd, 15) - 10) / 20.0  -- GDD affects harvest timing
            ELSE 0.5
        END as harvest_pressure,
        
        -- Export lineup status
        CASE 
            WHEN s.season_phase = 'HARVEST' AND COALESCE(w.brazil_precip, 100) < 150 THEN 'PEAK_EXPORTS'
            WHEN s.season_phase = 'HARVEST' AND COALESCE(w.brazil_precip, 100) > 200 THEN 'DELAYED_HARVEST'
            WHEN s.season_phase = 'PLANTING' THEN 'LOW_EXPORTS'
            WHEN COALESCE(w.brazil_temp, 25) > 35 THEN 'WEATHER_STRESS'
            ELSE 'NORMAL_FLOW'
        END as export_status,
        
        -- Moving averages
        AVG(COALESCE(w.brazil_precip, 100)) OVER (
            ORDER BY s.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as precip_30d_ma,
        
        AVG(COALESCE(w.brazil_temp, 25)) OVER (
            ORDER BY s.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as temp_7d_ma
        
    FROM seasonality s
    LEFT JOIN brazil_weather w ON s.date = w.date
    ORDER BY s.date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created vw_brazil_export_lineup")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create Brazil export lineup: {e}")
        return False

def create_trump_xi_volatility():
    """Create Trump-Xi volatility signal from social tensions"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_trump_xi_volatility` AS
    WITH trump_china_mentions AS (
        -- Track Trump and China co-mentions
        SELECT 
            DATE(timestamp) as date,
            COUNT(CASE WHEN LOWER(title) LIKE '%trump%' THEN 1 END) as trump_mentions,
            COUNT(CASE WHEN LOWER(title) LIKE '%china%' THEN 1 END) as china_mentions,
            COUNT(CASE WHEN LOWER(title) LIKE '%trump%' AND LOWER(title) LIKE '%china%' THEN 1 END) as trump_china_co_mentions,
            COUNT(CASE WHEN LOWER(title) LIKE '%xi%' THEN 1 END) as xi_mentions,
            COUNT(CASE WHEN LOWER(title) LIKE '%tariff%' THEN 1 END) as tariff_mentions,
            
            -- Sentiment when both are mentioned
            AVG(CASE 
                WHEN LOWER(title) LIKE '%trump%' AND LOWER(title) LIKE '%china%' 
                THEN sentiment_score 
            END) as co_mention_sentiment,
            
            -- Volatility of sentiment
            STDDEV(sentiment_score) as sentiment_volatility
            
        FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
        GROUP BY DATE(timestamp)
    ),
    trump_policy_impact AS (
        -- Get Trump policy impacts
        SELECT 
            DATE(timestamp) as date,
            AVG(agricultural_impact) as avg_policy_impact,
            MAX(agricultural_impact) as max_policy_impact,
            COUNT(*) as policy_count
        FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`
        GROUP BY DATE(timestamp)
    )
    SELECT 
        COALESCE(m.date, p.date) as date,
        
        -- Raw mention counts
        COALESCE(m.trump_mentions, 0) as trump_mentions,
        COALESCE(m.china_mentions, 0) as china_mentions,
        COALESCE(m.trump_china_co_mentions, 0) as co_mentions,
        COALESCE(m.xi_mentions, 0) as xi_mentions,
        COALESCE(m.tariff_mentions, 0) as tariff_mentions,
        
        -- Sentiment metrics
        COALESCE(m.co_mention_sentiment, 0.5) as co_mention_sentiment,
        COALESCE(m.sentiment_volatility, 0.1) as sentiment_volatility,
        
        -- Policy impact
        COALESCE(p.avg_policy_impact, 0.0) as policy_impact,
        COALESCE(p.max_policy_impact, 0.0) as max_policy_impact,
        
        -- Trump-Xi tension index (0-1 scale, higher = more tension)
        LEAST(1.0, (
            COALESCE(m.trump_china_co_mentions, 0) / 10.0 * 0.3 +  -- Co-mentions indicate tension
            COALESCE(m.tariff_mentions, 0) / 5.0 * 0.2 +  -- Tariff talk
            (1.0 - COALESCE(m.co_mention_sentiment, 0.5)) * 0.2 +  -- Negative sentiment
            COALESCE(m.sentiment_volatility, 0.1) * 2.0 * 0.15 +  -- High volatility
            COALESCE(p.avg_policy_impact, 0.0) * 0.15  -- Policy impact
        )) as tension_index,
        
        -- Volatility multiplier for trading
        1.0 + (
            COALESCE(m.sentiment_volatility, 0.1) * 2.0 +
            COALESCE(m.trump_china_co_mentions, 0) / 20.0
        ) as volatility_multiplier,
        
        -- Tension regime
        CASE 
            WHEN COALESCE(m.trump_china_co_mentions, 0) > 10 THEN 'CRISIS'
            WHEN COALESCE(m.tariff_mentions, 0) > 5 THEN 'TARIFF_THREAT'
            WHEN COALESCE(p.max_policy_impact, 0.0) > 0.7 THEN 'POLICY_SHOCK'
            WHEN COALESCE(m.sentiment_volatility, 0.1) > 0.3 THEN 'HIGH_VOLATILITY'
            ELSE 'CALM'
        END as tension_regime,
        
        -- Moving averages for trend
        AVG(COALESCE(m.trump_china_co_mentions, 0)) OVER (
            ORDER BY m.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as co_mentions_7d_ma,
        
        AVG(COALESCE(m.sentiment_volatility, 0.1)) OVER (
            ORDER BY m.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as volatility_30d_ma
        
    FROM trump_china_mentions m
    FULL OUTER JOIN trump_policy_impact p ON m.date = p.date
    WHERE COALESCE(m.date, p.date) IS NOT NULL
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created vw_trump_xi_volatility")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create Trump-Xi volatility: {e}")
        return False

def main():
    """Create all missing critical features"""
    print("=" * 80)
    print("CREATING MISSING CRITICAL FEATURES")
    print("=" * 80)
    
    features = [
        ("Biofuel Bridge", create_biofuel_bridge_features),
        ("China Import Tracker", create_china_import_tracker),
        ("Brazil Export Lineup", create_brazil_export_lineup),
        ("Trump-Xi Volatility", create_trump_xi_volatility)
    ]
    
    success_count = 0
    for name, create_func in features:
        print(f"\nCreating {name}...")
        if create_func():
            success_count += 1
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {success_count}/4 features created successfully")
    
    if success_count == 4:
        print("✅ ALL CRITICAL FEATURES CREATED!")
        print("\nNext steps:")
        print("1. Fix correlation features with new data")
        print("2. Update neural training dataset")
        print("3. Verify all features work without NaNs")
        print("4. Get approval for training")
    else:
        print("⚠️ Some features failed - check errors above")
    
    print("=" * 80)
    
    return success_count == 4

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
