#!/usr/bin/env python3
"""
Create elasticity and regime features for multi-horizon training
These capture price sensitivities and market conditions
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_elasticity_features():
    """Create elasticity features showing price sensitivities"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_elasticity_features` AS
    WITH price_changes AS (
        SELECT 
            DATE(s.time) as date,
            
            -- ZL (soybean oil) price changes
            s.close as zl_price,
            LAG(s.close, 1) OVER (ORDER BY s.time) as zl_price_lag1,
            LAG(s.close, 7) OVER (ORDER BY s.time) as zl_price_lag7,
            LAG(s.close, 30) OVER (ORDER BY s.time) as zl_price_lag30,
            
            -- Crude oil price changes
            c.close_price as crude_price,
            LAG(c.close_price, 1) OVER (ORDER BY c.date) as crude_price_lag1,
            LAG(c.close_price, 7) OVER (ORDER BY c.date) as crude_price_lag7,
            LAG(c.close_price, 30) OVER (ORDER BY c.date) as crude_price_lag30,
            
            -- Palm oil price changes
            p.close as palm_price,
            LAG(p.close, 1) OVER (ORDER BY p.time) as palm_price_lag1,
            LAG(p.close, 7) OVER (ORDER BY p.time) as palm_price_lag7,
            LAG(p.close, 30) OVER (ORDER BY p.time) as palm_price_lag30,
            
            -- China sentiment (proxy for demand)
            cs.china_relations_signal as china_demand_proxy
            
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices` s
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.crude_oil_prices` c
            ON DATE(s.time) = c.date
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.palm_oil_prices` p
            ON s.time = p.time
        LEFT JOIN `cbi-v14.signals.vw_china_relations_signal` cs
            ON DATE(s.time) = cs.date
        WHERE DATE(s.time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)
    ),
    elasticities AS (
        SELECT 
            date,
            
            -- Soy-to-crude elasticity (% change ZL / % change crude)
            SAFE_DIVIDE(
                (zl_price - zl_price_lag7) / NULLIF(zl_price_lag7, 0),
                (crude_price - crude_price_lag7) / NULLIF(crude_price_lag7, 0)
            ) as soy_crude_elasticity_7d,
            
            SAFE_DIVIDE(
                (zl_price - zl_price_lag30) / NULLIF(zl_price_lag30, 0),
                (crude_price - crude_price_lag30) / NULLIF(crude_price_lag30, 0)
            ) as soy_crude_elasticity_30d,
            
            -- Palm substitution elasticity (% change ZL / % change palm)
            SAFE_DIVIDE(
                (zl_price - zl_price_lag7) / NULLIF(zl_price_lag7, 0),
                (palm_price - palm_price_lag7) / NULLIF(palm_price_lag7, 0)
            ) as palm_substitution_elasticity_7d,
            
            SAFE_DIVIDE(
                (zl_price - zl_price_lag30) / NULLIF(zl_price_lag30, 0),
                (palm_price - palm_price_lag30) / NULLIF(palm_price_lag30, 0)
            ) as palm_substitution_elasticity_30d,
            
            -- China demand elasticity (simplified - price response to sentiment)
            SAFE_DIVIDE(
                (zl_price - zl_price_lag7) / NULLIF(zl_price_lag7, 0),
                china_demand_proxy - 0.5  -- Centered around neutral
            ) as china_demand_elasticity_7d,
            
            -- Price momentum (for trend elasticity)
            (zl_price - zl_price_lag1) / NULLIF(zl_price_lag1, 0) as zl_momentum_1d,
            (zl_price - zl_price_lag7) / NULLIF(zl_price_lag7, 0) as zl_momentum_7d,
            (zl_price - zl_price_lag30) / NULLIF(zl_price_lag30, 0) as zl_momentum_30d,
            
            -- Relative value indicators
            zl_price / NULLIF(crude_price, 0) as zl_crude_ratio,
            zl_price / NULLIF(palm_price, 0) as zl_palm_ratio
            
        FROM price_changes
    )
    SELECT 
        date,
        
        -- Elasticity features (capped at reasonable ranges)
        LEAST(GREATEST(COALESCE(soy_crude_elasticity_7d, 0), -5), 5) as soy_crude_elasticity_7d,
        LEAST(GREATEST(COALESCE(soy_crude_elasticity_30d, 0), -5), 5) as soy_crude_elasticity_30d,
        
        LEAST(GREATEST(COALESCE(palm_substitution_elasticity_7d, 0), -5), 5) as palm_substitution_elasticity_7d,
        LEAST(GREATEST(COALESCE(palm_substitution_elasticity_30d, 0), -5), 5) as palm_substitution_elasticity_30d,
        
        LEAST(GREATEST(COALESCE(china_demand_elasticity_7d, 0), -10), 10) as china_demand_elasticity_7d,
        
        -- Momentum features
        COALESCE(zl_momentum_1d, 0) as zl_momentum_1d,
        COALESCE(zl_momentum_7d, 0) as zl_momentum_7d,
        COALESCE(zl_momentum_30d, 0) as zl_momentum_30d,
        
        -- Relative value
        COALESCE(zl_crude_ratio, 0) as zl_crude_ratio,
        COALESCE(zl_palm_ratio, 0) as zl_palm_ratio,
        
        CURRENT_TIMESTAMP() as updated_at
        
    FROM elasticities
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created models.vw_elasticity_features")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create models.vw_elasticity_features: {e}")
        return False

def create_regime_features():
    """Create regime detection features"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_regime_features` AS
    WITH market_data AS (
        SELECT 
            date,
            
            -- VIX regime
            vix_current,
            CASE 
                WHEN vix_current > 30 THEN 'CRISIS'
                WHEN vix_current > 25 THEN 'ELEVATED'
                WHEN vix_current > 20 THEN 'MODERATE'
                ELSE 'LOW'
            END as vix_regime,
            
            -- Harvest regime from signal
            harvest_pace_signal,
            CASE 
                WHEN harvest_pace_signal < 0.3 THEN 'DROUGHT'
                WHEN harvest_pace_signal < 0.5 THEN 'POOR'
                WHEN harvest_pace_signal < 0.8 THEN 'NORMAL'
                ELSE 'BUMPER'
            END as harvest_regime
            
        FROM `cbi-v14.signals.vw_vix_stress_signal` v
        FULL OUTER JOIN `cbi-v14.signals.vw_harvest_pace_signal` h
            USING(date)
    ),
    policy_data AS (
        SELECT 
            date,
            
            -- Policy regime from tariff threat
            tariff_threat_score,
            CASE 
                WHEN tariff_threat_score > 0.8 THEN 'CRISIS'
                WHEN tariff_threat_score > 0.6 THEN 'UNCERTAIN'
                WHEN tariff_threat_score > 0.3 THEN 'MODERATE'
                ELSE 'STABLE'
            END as policy_regime,
            
            -- Geopolitical regime
            gvi_score,
            CASE 
                WHEN gvi_score > 0.8 THEN 'EXTREME'
                WHEN gvi_score > 0.6 THEN 'ELEVATED'
                WHEN gvi_score > 0.4 THEN 'MODERATE'
                ELSE 'CALM'
            END as geopolitical_regime
            
        FROM `cbi-v14.signals.vw_tariff_threat_signal` t
        FULL OUTER JOIN `cbi-v14.signals.vw_geopolitical_volatility_signal` g
            USING(date)
    ),
    correlation_regimes AS (
        SELECT 
            date,
            
            -- Correlation regime (from Big 8 aggregation)
            CASE 
                WHEN ABS(corr_zl_crude_30d) > 0.7 THEN 'EXTREME_CORRELATION'
                WHEN ABS(corr_zl_crude_30d) > 0.5 THEN 'HIGH_CORRELATION'
                WHEN ABS(corr_zl_crude_30d) > 0.3 THEN 'MODERATE_CORRELATION'
                WHEN ABS(corr_zl_crude_30d) < 0.1 THEN 'BREAKDOWN'
                ELSE 'NORMAL_CORRELATION'
            END as correlation_regime,
            
            -- Volatility clustering (consecutive high vol days)
            COUNT(CASE WHEN ABS(corr_zl_crude_7d) > 0.5 THEN 1 END) OVER (
                ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) as high_corr_days_7d
            
        FROM `cbi-v14.neural.vw_big_eight_signals`
    )
    SELECT 
        COALESCE(m.date, p.date, c.date) as date,
        
        -- VIX regime features
        m.vix_regime,
        CASE WHEN m.vix_regime = 'CRISIS' THEN 1 ELSE 0 END as vix_crisis_flag,
        CASE WHEN m.vix_regime IN ('CRISIS', 'ELEVATED') THEN 1 ELSE 0 END as vix_stress_flag,
        
        -- Harvest regime features
        m.harvest_regime,
        CASE WHEN m.harvest_regime = 'DROUGHT' THEN 1 ELSE 0 END as harvest_crisis_flag,
        CASE WHEN m.harvest_regime IN ('DROUGHT', 'POOR') THEN 1 ELSE 0 END as harvest_stress_flag,
        
        -- Policy regime features
        p.policy_regime,
        CASE WHEN p.policy_regime = 'CRISIS' THEN 1 ELSE 0 END as policy_crisis_flag,
        CASE WHEN p.policy_regime IN ('CRISIS', 'UNCERTAIN') THEN 1 ELSE 0 END as policy_stress_flag,
        
        -- Geopolitical regime features
        p.geopolitical_regime,
        CASE WHEN p.geopolitical_regime = 'EXTREME' THEN 1 ELSE 0 END as geo_crisis_flag,
        CASE WHEN p.geopolitical_regime IN ('EXTREME', 'ELEVATED') THEN 1 ELSE 0 END as geo_stress_flag,
        
        -- Correlation regime features
        c.correlation_regime,
        CASE WHEN c.correlation_regime = 'BREAKDOWN' THEN 1 ELSE 0 END as correlation_breakdown_flag,
        CASE WHEN c.correlation_regime = 'EXTREME_CORRELATION' THEN 1 ELSE 0 END as extreme_correlation_flag,
        
        -- Volatility clustering
        COALESCE(c.high_corr_days_7d, 0) as volatility_cluster_strength,
        
        -- Overall market regime (composite)
        CASE 
            WHEN m.vix_regime = 'CRISIS' OR m.harvest_regime = 'DROUGHT' OR p.policy_regime = 'CRISIS' 
            THEN 'CRISIS_REGIME'
            WHEN m.vix_regime = 'ELEVATED' OR m.harvest_regime = 'POOR' OR p.policy_regime = 'UNCERTAIN'
            THEN 'STRESS_REGIME'
            WHEN c.correlation_regime = 'BREAKDOWN'
            THEN 'DECORRELATION_REGIME'
            WHEN c.correlation_regime = 'EXTREME_CORRELATION'
            THEN 'RISK_ON_REGIME'
            ELSE 'NORMAL_REGIME'
        END as overall_market_regime,
        
        CURRENT_TIMESTAMP() as updated_at
        
    FROM market_data m
    FULL OUTER JOIN policy_data p ON m.date = p.date
    FULL OUTER JOIN correlation_regimes c ON COALESCE(m.date, p.date) = c.date
    WHERE COALESCE(m.date, p.date, c.date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created models.vw_regime_features")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create models.vw_regime_features: {e}")
        return False

def verify_features():
    """Verify elasticity and regime features"""
    
    # Check elasticity features
    query1 = """
    SELECT 
        COUNT(*) as total_rows,
        AVG(ABS(soy_crude_elasticity_30d)) as avg_soy_crude_elasticity,
        AVG(ABS(palm_substitution_elasticity_30d)) as avg_palm_elasticity,
        AVG(zl_momentum_7d) as avg_momentum_7d
    FROM `cbi-v14.models.vw_elasticity_features`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR)
    """
    
    # Check regime features
    query2 = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT vix_regime) as vix_regimes,
        COUNT(DISTINCT harvest_regime) as harvest_regimes,
        COUNT(DISTINCT overall_market_regime) as market_regimes,
        SUM(vix_crisis_flag) as vix_crisis_days,
        SUM(harvest_crisis_flag) as harvest_crisis_days
    FROM `cbi-v14.models.vw_regime_features`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR)
    """
    
    try:
        # Check elasticity
        result1 = list(client.query(query1))[0]
        logger.info("\nElasticity Features Statistics:")
        logger.info(f"  Total Rows: {result1['total_rows']}")
        logger.info(f"  Avg Soy-Crude Elasticity: {result1['avg_soy_crude_elasticity']:.3f}")
        logger.info(f"  Avg Palm Substitution: {result1['avg_palm_elasticity']:.3f}")
        logger.info(f"  Avg 7-day Momentum: {result1['avg_momentum_7d']:.4f}")
        
        # Check regimes
        result2 = list(client.query(query2))[0]
        logger.info("\nRegime Features Statistics:")
        logger.info(f"  Total Rows: {result2['total_rows']}")
        logger.info(f"  Distinct VIX Regimes: {result2['vix_regimes']}")
        logger.info(f"  Distinct Harvest Regimes: {result2['harvest_regimes']}")
        logger.info(f"  Distinct Market Regimes: {result2['market_regimes']}")
        logger.info(f"  VIX Crisis Days: {result2['vix_crisis_days']}")
        logger.info(f"  Harvest Crisis Days: {result2['harvest_crisis_days']}")
        
        return result1['total_rows'] > 0 and result2['total_rows'] > 0
    except Exception as e:
        logger.error(f"Could not verify: {e}")
        return False

def main():
    """Create elasticity and regime features"""
    logger.info("=" * 50)
    logger.info("Creating Elasticity & Regime Features")
    logger.info("=" * 50)
    
    results = []
    
    # Create elasticity features
    logger.info("\n1. Creating Elasticity Features...")
    results.append(create_elasticity_features())
    
    # Create regime features
    logger.info("\n2. Creating Regime Features...")
    results.append(create_regime_features())
    
    # Verify
    if all(results):
        logger.info("\nVerifying features...")
        has_data = verify_features()
        
        if has_data:
            logger.info("\n" + "=" * 50)
            logger.info("✅ SUCCESS: Elasticity & Regime Features Created!")
            logger.info("Features capture:")
            logger.info("  • Price elasticities (soy-crude, palm substitution)")
            logger.info("  • Market regimes (VIX, harvest, policy, correlation)")
            logger.info("  • Volatility clustering")
            logger.info("  • Momentum indicators")
            logger.info("Ready for multi-horizon training!")
        else:
            logger.warning("⚠️ Views created but may have limited data")
    else:
        logger.error("❌ Failed to create some features")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
