#!/usr/bin/env python3
"""
Create the Biofuel/Ethanol signal as the 8th Big signal
Phase 1 Step 1.3 of the Complete Multi-Horizon Neural Training Plan
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_biofuel_ethanol_signal():
    """Create comprehensive biofuel/ethanol signal combining multiple factors"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.signals.vw_biofuel_ethanol_signal` AS
    WITH rin_prices AS (
        -- RIN prices from staging biofuel policy (if available)
        SELECT 
            DATE(timestamp) as date,
            AVG(d4_rin_price) as d4_rin,
            AVG(d6_rin_price) as d6_rin
        FROM `cbi-v14.staging.biofuel_policy`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
        GROUP BY DATE(timestamp)
    ),
    biofuel_price_data AS (
        -- Biofuel prices if available
        SELECT 
            date,
            AVG(close_price) as biofuel_price
        FROM `cbi-v14.forecasting_data_warehouse.biofuel_prices`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        GROUP BY date
    ),
    capacity_data AS (
        -- Use biofuel metrics or staging data
        SELECT 
            DATE(timestamp) as date,
            AVG(rd_capacity_bpd) as rd_capacity,
            AVG(saf_capacity_bpd) as saf_capacity
        FROM `cbi-v14.staging.biofuel_policy`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
        GROUP BY DATE(timestamp)
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
        -- Social mentions of biofuel/ethanol policy
        SELECT 
            PARSE_DATE('%Y-%m-%d', SUBSTR(created_at, 1, 10)) as date,
            SUM(CASE 
                WHEN LOWER(content) LIKE '%biofuel%' THEN 1 
                WHEN LOWER(content) LIKE '%ethanol%' THEN 1
                WHEN LOWER(content) LIKE '%renewable%diesel%' THEN 1
                WHEN LOWER(content) LIKE '%biodiesel%' THEN 1
                WHEN LOWER(content) LIKE '%saf%' AND LOWER(content) LIKE '%fuel%' THEN 1
                WHEN LOWER(content) LIKE '%rfs%' THEN 1
                ELSE 0 
            END) as biofuel_mentions,
            AVG(CASE 
                WHEN LOWER(content) LIKE '%biofuel%' AND LOWER(content) LIKE '%mandate%' THEN 0.9
                WHEN LOWER(content) LIKE '%ethanol%' AND LOWER(content) LIKE '%subsid%' THEN 0.8
                WHEN LOWER(content) LIKE '%renewable%' AND LOWER(content) LIKE '%credit%' THEN 0.85
                ELSE 0.5
            END) as policy_intensity
        FROM `cbi-v14.staging.comprehensive_social_intelligence`
        WHERE PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', created_at) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        GROUP BY PARSE_DATE('%Y-%m-%d', SUBSTR(created_at, 1, 10))
    ),
    combined_signal AS (
        SELECT 
            COALESCE(r.date, c.date, p.date, s.date) as date,
            
            -- RIN price component (normalized 0-1)
            CASE 
                WHEN r.d4_rin IS NOT NULL THEN 
                    LEAST(GREATEST((r.d4_rin - 0.5) / (2.0 - 0.5), 0), 1)
                ELSE 0.5
            END as rin_strength,
            
            -- Capacity component (normalized 0-1)
            CASE 
                WHEN c.rd_capacity IS NOT NULL THEN
                    LEAST(c.rd_capacity / 1000000, 1.0)  -- Normalize to 1M bpd
                ELSE 0.3
            END as capacity_factor,
            
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
            r.d4_rin,
            r.d6_rin,
            c.rd_capacity,
            c.saf_capacity,
            p.palm_soy_spread_pct,
            s.biofuel_mentions,
            s.policy_intensity
            
        FROM rin_prices r
        FULL OUTER JOIN capacity_data c ON r.date = c.date
        FULL OUTER JOIN palm_soy_spread p ON COALESCE(r.date, c.date) = p.date
        FULL OUTER JOIN social_signals s ON COALESCE(r.date, c.date, p.date) = s.date
    )
    SELECT 
        date,
        
        -- Component scores
        rin_strength,
        capacity_factor,
        soy_advantage,
        policy_momentum,
        
        -- Raw data
        d4_rin,
        d6_rin,
        rd_capacity,
        saf_capacity,
        palm_soy_spread_pct,
        biofuel_mentions,
        policy_intensity,
        
        -- Composite biofuel/ethanol signal (weighted average)
        (
            rin_strength * 0.3 +           -- RIN prices drive immediate demand
            capacity_factor * 0.3 +         -- Capacity sets structural demand
            soy_advantage * 0.2 +           -- Palm spread affects substitution
            policy_momentum * 0.2           -- Policy changes drive future demand
        ) as biofuel_ethanol_signal,
        
        -- Signal interpretation
        CASE
            WHEN (rin_strength * 0.3 + capacity_factor * 0.3 + soy_advantage * 0.2 + policy_momentum * 0.2) > 0.8 
            THEN 'STRONG_BIOFUEL_DEMAND'
            WHEN (rin_strength * 0.3 + capacity_factor * 0.3 + soy_advantage * 0.2 + policy_momentum * 0.2) > 0.6 
            THEN 'ELEVATED_BIOFUEL_IMPACT'
            WHEN (rin_strength * 0.3 + capacity_factor * 0.3 + soy_advantage * 0.2 + policy_momentum * 0.2) > 0.4 
            THEN 'MODERATE_BIOFUEL_INFLUENCE'
            ELSE 'WEAK_BIOFUEL_FACTOR'
        END as biofuel_regime,
        
        -- Crisis flag
        (rin_strength * 0.3 + capacity_factor * 0.3 + soy_advantage * 0.2 + policy_momentum * 0.2) > 0.8 as biofuel_crisis_flag,
        
        CURRENT_TIMESTAMP() as updated_at
        
    FROM combined_signal
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created vw_biofuel_ethanol_signal")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create vw_biofuel_ethanol_signal: {e}")
        return False

def verify_signal():
    """Verify the signal was created and has data"""
    query = """
    SELECT 
        COUNT(*) as row_count,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        AVG(biofuel_ethanol_signal) as avg_signal,
        MAX(biofuel_ethanol_signal) as max_signal,
        MIN(biofuel_ethanol_signal) as min_signal
    FROM `cbi-v14.signals.vw_biofuel_ethanol_signal`
    """
    
    try:
        result = list(client.query(query))[0]
        logger.info(f"Signal Statistics:")
        logger.info(f"  Rows: {result['row_count']}")
        logger.info(f"  Date Range: {result['earliest_date']} to {result['latest_date']}")
        logger.info(f"  Signal Range: {result['min_signal']:.3f} to {result['max_signal']:.3f}")
        logger.info(f"  Average Signal: {result['avg_signal']:.3f}")
        return result['row_count'] > 0
    except Exception as e:
        logger.warning(f"Could not verify signal: {e}")
        return False

def main():
    """Create and verify the Biofuel/Ethanol signal"""
    logger.info("=" * 50)
    logger.info("Creating Biofuel/Ethanol Signal (8th Big Signal)")
    logger.info("=" * 50)
    
    # Create the signal
    logger.info("\nCreating signal view...")
    success = create_biofuel_ethanol_signal()
    
    if success:
        logger.info("\nVerifying signal data...")
        has_data = verify_signal()
        
        if not has_data:
            logger.warning("⚠️ Signal created but may have limited data (check biofuel_policy table)")
    
    # Summary
    logger.info("\n" + "=" * 50)
    if success:
        logger.info("✅ SUCCESS: Biofuel/Ethanol signal created as 8th Big signal!")
        logger.info("The Big 8 signals are now:")
        logger.info("  1. VIX Stress")
        logger.info("  2. Harvest Pace")
        logger.info("  3. China Relations")
        logger.info("  4. Tariff Threat")
        logger.info("  5. Geopolitical Volatility (GVI)")
        logger.info("  6. Biofuel Cascade (BSC)")
        logger.info("  7. Hidden Correlations (HCI)")
        logger.info("  8. Biofuel/Ethanol Signal ✨ NEW")
    else:
        logger.error("❌ FAILED: Could not create Biofuel/Ethanol signal")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
