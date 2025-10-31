#!/usr/bin/env python3
"""
Fix all signal views to use main tables instead of staging
CRITICAL: Production views should NEVER reference staging tables
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def fix_tariff_threat_signal():
    """Update tariff threat signal to use main social_sentiment table"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.signals.vw_tariff_threat_signal` AS
    WITH daily_mentions AS (
        SELECT 
            DATE(timestamp) as date,
            SUM(CASE WHEN LOWER(title) LIKE '%tariff%' THEN 1 ELSE 0 END) as daily_tariff_mentions,
            AVG(CASE 
                WHEN LOWER(title) LIKE '%tariff%' AND LOWER(title) LIKE '%china%' THEN 0.9
                WHEN LOWER(title) LIKE '%tariff%' AND LOWER(title) LIKE '%trade%' THEN 0.8
                WHEN LOWER(title) LIKE '%tariff%' AND LOWER(title) LIKE '%agriculture%' THEN 0.85
                WHEN LOWER(title) LIKE '%tariff%' THEN 0.7
                ELSE 0.3
            END) as china_trade_tension
        FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
        GROUP BY DATE(timestamp)
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
        logger.info("✅ Fixed vw_tariff_threat_signal - now uses main table")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to fix vw_tariff_threat_signal: {e}")
        return False

def fix_geopolitical_volatility_signal():
    """Update geopolitical volatility signal to use main social_sentiment table"""
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
            DATE(timestamp) as date,
            SUM(CASE WHEN LOWER(title) LIKE '%market%' OR LOWER(title) LIKE '%trade%' THEN 1 ELSE 0 END) as market_mentions,
            SUM(CASE WHEN LOWER(title) LIKE '%tariff%' OR LOWER(title) LIKE '%china%' THEN 1 ELSE 0 END) as tariff_china_mentions,
            SUM(CASE WHEN LOWER(title) LIKE '%panama%canal%' OR LOWER(title) LIKE '%suez%' THEN 1 ELSE 0 END) as panama_mentions,
            AVG(CASE 
                WHEN LOWER(title) LIKE '%emerging%market%' AND LOWER(title) LIKE '%crisis%' THEN 0.9
                WHEN LOWER(title) LIKE '%currency%' AND LOWER(title) LIKE '%devaluat%' THEN 0.8
                WHEN LOWER(title) LIKE '%debt%' AND LOWER(title) LIKE '%default%' THEN 0.85
                ELSE 0.3
            END) as em_stress
        FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        GROUP BY DATE(timestamp)
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
        logger.info("✅ Fixed vw_geopolitical_volatility_signal - now uses main table")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to fix vw_geopolitical_volatility_signal: {e}")
        return False

def fix_hidden_correlation_signal():
    """Update hidden correlation signal to use main social_sentiment table"""
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
            -- VIX-Trump tweet correlation using main table
            CORR(
                CASE WHEN LOWER(title) LIKE '%volatil%' THEN 1 ELSE 0 END,
                CASE WHEN LOWER(title) LIKE '%trump%' OR LOWER(title) LIKE '%tariff%' THEN 1 ELSE 0 END
            ) as vix_trump_correlation
        FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
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
        logger.info("✅ Fixed vw_hidden_correlation_signal - now uses main table")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to fix vw_hidden_correlation_signal: {e}")
        return False

def create_biofuel_signal_no_staging():
    """Create biofuel signal using ONLY main tables, no staging"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.signals.vw_biofuel_ethanol_signal` AS
    WITH biofuel_price_data AS (
        -- Use main biofuel_prices table
        SELECT 
            DATE(date) as date,
            AVG(close) as biofuel_price,
            AVG(volume) as biofuel_volume
        FROM `cbi-v14.forecasting_data_warehouse.biofuel_prices`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        GROUP BY DATE(date)
    ),
    palm_soy_spread AS (
        -- Palm/soy spread as substitution indicator
        SELECT 
            DATE(s.time) as date,
            s.close as soy_price,
            p.close as palm_price,
            SAFE_DIVIDE(p.close - s.close, s.close) as palm_soy_spread_pct
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices` s
        LEFT JOIN `cbi-v14.forecasting_data_warehouse.palm_oil_prices` p
            ON s.time = p.time
        WHERE DATE(s.time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
    ),
    social_signals AS (
        -- Social mentions of biofuel/ethanol from MAIN table
        SELECT 
            DATE(timestamp) as date,
            SUM(CASE 
                WHEN LOWER(title) LIKE '%biofuel%' THEN 1 
                WHEN LOWER(title) LIKE '%ethanol%' THEN 1
                WHEN LOWER(title) LIKE '%renewable%diesel%' THEN 1
                WHEN LOWER(title) LIKE '%biodiesel%' THEN 1
                WHEN LOWER(title) LIKE '%saf%' AND LOWER(title) LIKE '%fuel%' THEN 1
                WHEN LOWER(title) LIKE '%rfs%' THEN 1
                ELSE 0 
            END) as biofuel_mentions,
            AVG(CASE 
                WHEN LOWER(title) LIKE '%biofuel%' AND LOWER(title) LIKE '%mandate%' THEN 0.9
                WHEN LOWER(title) LIKE '%ethanol%' AND LOWER(title) LIKE '%subsid%' THEN 0.8
                WHEN LOWER(title) LIKE '%renewable%' AND LOWER(title) LIKE '%credit%' THEN 0.85
                ELSE sentiment_score  -- Use actual sentiment score
            END) as policy_intensity
        FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        GROUP BY DATE(timestamp)
    ),
    combined_signal AS (
        SELECT 
            COALESCE(b.date, p.date, s.date) as date,
            
            -- Biofuel price component (normalized)
            CASE 
                WHEN b.biofuel_price IS NOT NULL THEN 
                    LEAST(GREATEST((b.biofuel_price - 3.0) / (5.0 - 3.0), 0), 1)
                ELSE 0.5
            END as biofuel_price_strength,
            
            -- Palm/soy spread component (inverted - negative spread = soy advantage)
            CASE 
                WHEN p.palm_soy_spread_pct IS NOT NULL THEN
                    1.0 - LEAST(GREATEST((p.palm_soy_spread_pct + 0.2) / 0.4, 0), 1)
                ELSE 0.5
            END as soy_advantage,
            
            -- Social/policy component
            CASE 
                WHEN s.biofuel_mentions > 20 THEN 0.9
                WHEN s.biofuel_mentions > 10 THEN 0.7
                WHEN s.biofuel_mentions > 5 THEN 0.5
                ELSE 0.3
            END as policy_momentum,
            
            -- Raw values for transparency
            b.biofuel_price,
            b.biofuel_volume,
            p.palm_soy_spread_pct,
            s.biofuel_mentions,
            s.policy_intensity
            
        FROM biofuel_price_data b
        FULL OUTER JOIN palm_soy_spread p ON b.date = p.date
        FULL OUTER JOIN social_signals s ON COALESCE(b.date, p.date) = s.date
    )
    SELECT 
        date,
        
        -- Component scores
        biofuel_price_strength,
        soy_advantage,
        policy_momentum,
        
        -- Raw data
        biofuel_price,
        biofuel_volume,
        palm_soy_spread_pct,
        biofuel_mentions,
        policy_intensity,
        
        -- Composite biofuel/ethanol signal (weighted average)
        (
            biofuel_price_strength * 0.4 +    -- Price drives immediate impact
            soy_advantage * 0.3 +              -- Palm spread affects substitution
            policy_momentum * 0.3              -- Policy changes drive future demand
        ) as biofuel_ethanol_signal,
        
        -- Signal interpretation
        CASE
            WHEN (biofuel_price_strength * 0.4 + soy_advantage * 0.3 + policy_momentum * 0.3) > 0.8 
            THEN 'STRONG_BIOFUEL_DEMAND'
            WHEN (biofuel_price_strength * 0.4 + soy_advantage * 0.3 + policy_momentum * 0.3) > 0.6 
            THEN 'ELEVATED_BIOFUEL_IMPACT'
            WHEN (biofuel_price_strength * 0.4 + soy_advantage * 0.3 + policy_momentum * 0.3) > 0.4 
            THEN 'MODERATE_BIOFUEL_INFLUENCE'
            ELSE 'WEAK_BIOFUEL_FACTOR'
        END as biofuel_regime,
        
        -- Crisis flag
        (biofuel_price_strength * 0.4 + soy_advantage * 0.3 + policy_momentum * 0.3) > 0.8 as biofuel_crisis_flag,
        
        CURRENT_TIMESTAMP() as updated_at
        
    FROM combined_signal
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created vw_biofuel_ethanol_signal - uses ONLY main tables")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create vw_biofuel_ethanol_signal: {e}")
        return False

def verify_no_staging():
    """Verify that no signal views reference staging"""
    query = """
    SELECT 
        table_name,
        CASE 
            WHEN view_definition LIKE '%staging.%' THEN 'USES STAGING'
            ELSE 'CLEAN'
        END as status
    FROM `cbi-v14.signals.INFORMATION_SCHEMA.VIEWS`
    WHERE table_name IN (
        'vw_tariff_threat_signal',
        'vw_geopolitical_volatility_signal',
        'vw_hidden_correlation_signal',
        'vw_biofuel_ethanol_signal'
    )
    """
    
    try:
        results = client.query(query)
        logger.info("\nVerification Results:")
        all_clean = True
        for row in results:
            status_icon = "✅" if row['status'] == 'CLEAN' else "❌"
            logger.info(f"  {status_icon} {row['table_name']}: {row['status']}")
            if row['status'] != 'CLEAN':
                all_clean = False
        return all_clean
    except Exception as e:
        logger.error(f"Could not verify: {e}")
        return False

def main():
    """Fix all signal views to use main tables only"""
    logger.info("=" * 50)
    logger.info("FIXING ALL SIGNAL VIEWS TO USE MAIN TABLES ONLY")
    logger.info("=" * 50)
    
    results = []
    
    # Fix each signal
    logger.info("\n1. Fixing Tariff Threat Signal...")
    results.append(fix_tariff_threat_signal())
    
    logger.info("\n2. Fixing Geopolitical Volatility Signal...")
    results.append(fix_geopolitical_volatility_signal())
    
    logger.info("\n3. Fixing Hidden Correlation Signal...")
    results.append(fix_hidden_correlation_signal())
    
    logger.info("\n4. Creating Biofuel/Ethanol Signal (no staging)...")
    results.append(create_biofuel_signal_no_staging())
    
    # Verify
    logger.info("\n" + "=" * 50)
    logger.info("VERIFICATION")
    logger.info("=" * 50)
    
    all_clean = verify_no_staging()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("SUMMARY")
    logger.info("=" * 50)
    
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count and all_clean:
        logger.info(f"✅ SUCCESS: All {total_count} signals fixed - NO STAGING REFERENCES!")
        logger.info("All views now use ONLY main tables from forecasting_data_warehouse")
    else:
        logger.warning(f"⚠️ PARTIAL: {success_count}/{total_count} signals fixed")
        if not all_clean:
            logger.error("❌ Some views still reference staging!")
        
    return success_count == total_count and all_clean

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
