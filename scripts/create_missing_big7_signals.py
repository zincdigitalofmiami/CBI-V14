#!/usr/bin/env python3
"""
Create the 3 missing Big 7 signals for multi-horizon forecasting
Phase 1 Step 1.2 of the Complete Multi-Horizon Neural Training Plan
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_tariff_threat_signal():
    """Create tariff threat signal from social intelligence"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.signals.vw_tariff_threat_signal` AS
    WITH daily_mentions AS (
        SELECT 
            PARSE_DATE('%Y-%m-%d', SUBSTR(created_at, 1, 10)) as date,
            SUM(CASE WHEN LOWER(content) LIKE '%tariff%' THEN 1 ELSE 0 END) as daily_tariff_mentions,
            AVG(CASE 
                WHEN LOWER(content) LIKE '%tariff%' AND LOWER(content) LIKE '%china%' THEN 0.9
                WHEN LOWER(content) LIKE '%tariff%' AND LOWER(content) LIKE '%trade%' THEN 0.8
                WHEN LOWER(content) LIKE '%tariff%' AND LOWER(content) LIKE '%agriculture%' THEN 0.85
                WHEN LOWER(content) LIKE '%tariff%' THEN 0.7
                ELSE 0.3
            END) as china_trade_tension
        FROM `cbi-v14.staging.comprehensive_social_intelligence`
        WHERE PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', created_at) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
        GROUP BY PARSE_DATE('%Y-%m-%d', SUBSTR(created_at, 1, 10))
    ),
    tariff_data AS (
        SELECT 
            date,
            -- 7-day rolling tariff mentions
            SUM(daily_tariff_mentions) OVER (
                ORDER BY date
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) as tariff_mentions_7d,
            china_trade_tension
        FROM daily_mentions
    )
    SELECT 
        date,
        tariff_mentions_7d,
        china_trade_tension,
        LEAST(
            (tariff_mentions_7d / 10.0) * 0.7 + china_trade_tension * 0.3,
            1.0
        ) as tariff_threat_score,
        CASE
            WHEN (tariff_mentions_7d / 10.0) * 0.7 + china_trade_tension * 0.3 > 0.8 THEN 'IMMINENT_TARIFF_ACTION'
            WHEN (tariff_mentions_7d / 10.0) * 0.7 + china_trade_tension * 0.3 > 0.6 THEN 'ELEVATED_TARIFF_RISK'
            WHEN (tariff_mentions_7d / 10.0) * 0.7 + china_trade_tension * 0.3 > 0.3 THEN 'BACKGROUND_RISK'
            ELSE 'LOW_TARIFF_PROBABILITY'
        END as tariff_regime,
        (tariff_mentions_7d / 10.0) * 0.7 + china_trade_tension * 0.3 > 0.8 as crisis_flag,
        CURRENT_TIMESTAMP() as updated_at
    FROM tariff_data
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created vw_tariff_threat_signal")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create vw_tariff_threat_signal: {e}")
        return False

def create_geopolitical_volatility_signal():
    """Create geopolitical volatility index (GVI) signal"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.signals.vw_geopolitical_volatility_signal` AS
    WITH vix_component AS (
        SELECT 
            date,
            LEAST(close / 20.0, 3.0) * 0.4 as vix_contribution
        FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    ),
    social_daily AS (
        SELECT 
            PARSE_DATE('%Y-%m-%d', SUBSTR(created_at, 1, 10)) as date,
            SUM(CASE WHEN LOWER(content) LIKE '%market%' OR LOWER(content) LIKE '%trade%' THEN 1 ELSE 0 END) as market_mentions,
            SUM(CASE WHEN LOWER(content) LIKE '%tariff%' OR LOWER(content) LIKE '%china%' THEN 1 ELSE 0 END) as tariff_china_mentions,
            SUM(CASE WHEN LOWER(content) LIKE '%panama%canal%' OR LOWER(content) LIKE '%suez%' THEN 1 ELSE 0 END) as panama_mentions,
            AVG(CASE 
                WHEN LOWER(content) LIKE '%emerging%market%' AND LOWER(content) LIKE '%crisis%' THEN 0.9
                WHEN LOWER(content) LIKE '%currency%' AND LOWER(content) LIKE '%devaluat%' THEN 0.8
                WHEN LOWER(content) LIKE '%debt%' AND LOWER(content) LIKE '%default%' THEN 0.85
                ELSE 0.3
            END) as em_stress
        FROM `cbi-v14.staging.comprehensive_social_intelligence`
        WHERE PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', created_at) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        GROUP BY PARSE_DATE('%Y-%m-%d', SUBSTR(created_at, 1, 10))
    ),
    social_components AS (
        SELECT 
            date,
            -- Trump tweet market correlation (simplified)
            ABS(CORR(market_mentions, tariff_china_mentions) OVER (
                ORDER BY date ROWS BETWEEN 30 PRECEDING AND CURRENT ROW
            )) * 0.3 as trump_contribution,
            
            -- Panama Canal delays (from mentions)
            LEAST(panama_mentions / 15.0, 1.0) * 0.2 as panama_contribution,
            
            -- Emerging market stress
            em_stress * 0.1 as em_contribution
        FROM social_daily
    )
    SELECT 
        COALESCE(v.date, s.date) as date,
        COALESCE(v.vix_contribution, 0.4) as vix_component,
        COALESCE(s.trump_contribution, 0.09) as trump_component,
        COALESCE(s.panama_contribution, 0) as panama_component,
        COALESCE(s.em_contribution, 0.03) as em_component,
        LEAST(
            COALESCE(v.vix_contribution, 0.4) + 
            COALESCE(s.trump_contribution, 0.09) + 
            COALESCE(s.panama_contribution, 0) + 
            COALESCE(s.em_contribution, 0.03),
            1.0
        ) as gvi_score,
        CASE
            WHEN COALESCE(v.vix_contribution, 0.4) + COALESCE(s.trump_contribution, 0.09) + 
                 COALESCE(s.panama_contribution, 0) + COALESCE(s.em_contribution, 0.03) > 0.8 
            THEN 'GEOPOLITICAL_CRISIS'
            WHEN COALESCE(v.vix_contribution, 0.4) + COALESCE(s.trump_contribution, 0.09) + 
                 COALESCE(s.panama_contribution, 0) + COALESCE(s.em_contribution, 0.03) > 0.6 
            THEN 'ELEVATED_RISK'
            WHEN COALESCE(v.vix_contribution, 0.4) + COALESCE(s.trump_contribution, 0.09) + 
                 COALESCE(s.panama_contribution, 0) + COALESCE(s.em_contribution, 0.03) > 0.3 
            THEN 'NORMAL_TENSION'
            ELSE 'STABLE_ENVIRONMENT'
        END as gvi_regime,
        COALESCE(v.vix_contribution, 0.4) + COALESCE(s.trump_contribution, 0.09) + 
        COALESCE(s.panama_contribution, 0) + COALESCE(s.em_contribution, 0.03) > 0.8 as crisis_flag,
        CURRENT_TIMESTAMP() as updated_at
    FROM vix_component v
    FULL OUTER JOIN social_components s ON v.date = s.date
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created vw_geopolitical_volatility_signal")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create vw_geopolitical_volatility_signal: {e}")
        return False

def create_hidden_correlation_signal():
    """Create hidden correlation index (HCI) signal"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.signals.vw_hidden_correlation_signal` AS
    WITH price_correlations AS (
        -- Calculate REAL rolling correlations matching forecast horizons
        SELECT 
            DATE(s.time) as date,
            
            -- 7-day correlations for 1 week forecast
            CORR(s.close, c.close_price) OVER (
                ORDER BY DATE(s.time) 
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) as zl_crude_corr_7d,
            
            -- 30-day correlations for 1 month forecast
            CORR(s.close, c.close_price) OVER (
                ORDER BY DATE(s.time) 
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as zl_crude_corr_30d,
            
            -- 90-day correlations for 3 month forecast
            CORR(s.close, c.close_price) OVER (
                ORDER BY DATE(s.time) 
                ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
            ) as zl_crude_corr_90d,
            
            -- Palm oil correlation
            CORR(s.close, p.close) OVER (
                ORDER BY DATE(s.time) 
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as soy_palm_correlation,
            
            -- DXY correlation (if available)
            CORR(s.close, d.close_price) OVER (
                ORDER BY DATE(s.time) 
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as zl_dxy_correlation
            
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices` s
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.crude_oil_prices` c
          ON DATE(s.time) = c.date
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.palm_oil_prices` p
          ON s.time = p.time
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.usd_index_prices` d
          ON DATE(s.time) = d.date
        WHERE DATE(s.time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
    ),
    trump_correlation AS (
        SELECT 
            -- VIX-Trump tweet correlation
            CORR(
                CASE WHEN LOWER(content) LIKE '%volatil%' THEN 1 ELSE 0 END,
                CASE WHEN LOWER(content) LIKE '%trump%' OR LOWER(content) LIKE '%tariff%' THEN 1 ELSE 0 END
            ) as vix_trump_correlation
        FROM `cbi-v14.staging.comprehensive_social_intelligence`
        WHERE PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', created_at) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    )
    SELECT 
        p.date,
        p.zl_crude_corr_7d,
        p.zl_crude_corr_30d,
        p.zl_crude_corr_90d,
        p.zl_dxy_correlation,
        p.soy_palm_correlation,
        COALESCE(t.vix_trump_correlation, 0) as vix_trump_correlation,
        
        -- Calculate HCI score using 30-day correlation as primary
        COALESCE(p.zl_crude_corr_30d, 0) * 0.25 + 
        COALESCE(p.zl_dxy_correlation, 0) * -0.25 +  -- Inverted
        COALESCE(p.soy_palm_correlation, 0.5) * 0.25 + 
        COALESCE(t.vix_trump_correlation, 0) * 0.25 as hci_score,
        
        CASE
            WHEN ABS(COALESCE(p.zl_crude_corr_30d, 0) * 0.25 + 
                     COALESCE(p.zl_dxy_correlation, 0) * -0.25 + 
                     COALESCE(p.soy_palm_correlation, 0.5) * 0.25 + 
                     COALESCE(t.vix_trump_correlation, 0) * 0.25) > 0.8 
            THEN 'EXTREME_CORRELATION_SHIFT'
            WHEN ABS(COALESCE(p.zl_crude_corr_30d, 0) * 0.25 + 
                     COALESCE(p.zl_dxy_correlation, 0) * -0.25 + 
                     COALESCE(p.soy_palm_correlation, 0.5) * 0.25 + 
                     COALESCE(t.vix_trump_correlation, 0) * 0.25) > 0.6 
            THEN 'STRONG_CORRELATIONS'
            WHEN ABS(COALESCE(p.zl_crude_corr_30d, 0) * 0.25 + 
                     COALESCE(p.zl_dxy_correlation, 0) * -0.25 + 
                     COALESCE(p.soy_palm_correlation, 0.5) * 0.25 + 
                     COALESCE(t.vix_trump_correlation, 0) * 0.25) > 0.2 
            THEN 'MODERATE_CORRELATIONS'
            ELSE 'NEUTRAL_PATTERNS'
        END as hci_regime,
        
        ABS(COALESCE(p.zl_crude_corr_30d, 0) * 0.25 + 
            COALESCE(p.zl_dxy_correlation, 0) * -0.25 + 
            COALESCE(p.soy_palm_correlation, 0.5) * 0.25 + 
            COALESCE(t.vix_trump_correlation, 0) * 0.25) > 0.8 as crisis_flag,
            
        CURRENT_TIMESTAMP() as updated_at
    FROM price_correlations p
    CROSS JOIN trump_correlation t
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created vw_hidden_correlation_signal")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create vw_hidden_correlation_signal: {e}")
        return False

def main():
    """Create all 3 missing Big 7 signals"""
    logger.info("=" * 50)
    logger.info("Creating Missing Big 7 Signals")
    logger.info("=" * 50)
    
    results = []
    
    # Create each signal
    logger.info("\n1. Creating Tariff Threat Signal...")
    results.append(create_tariff_threat_signal())
    
    logger.info("\n2. Creating Geopolitical Volatility Signal...")
    results.append(create_geopolitical_volatility_signal())
    
    logger.info("\n3. Creating Hidden Correlation Signal...")
    results.append(create_hidden_correlation_signal())
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("SUMMARY")
    logger.info("=" * 50)
    
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        logger.info(f"✅ SUCCESS: All {total_count} signals created successfully!")
    else:
        logger.warning(f"⚠️ PARTIAL: {success_count}/{total_count} signals created")
        
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
