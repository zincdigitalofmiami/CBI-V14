#!/usr/bin/env python3
"""
Create the Big 8 Signals Aggregation View
This combines all 8 individual signals into one master view for training
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_big_eight_signals():
    """Create the master Big 8 signals aggregation view"""
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.neural.vw_big_eight_signals` AS
    WITH date_range AS (
        -- Create a date spine from earliest to latest
        SELECT date
        FROM UNNEST(GENERATE_DATE_ARRAY(
            DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR),
            CURRENT_DATE(),
            INTERVAL 1 DAY
        )) as date
    ),
    vix_signal AS (
        SELECT 
            date,
            vix_current,
            vix_stress_ratio,
            vix_signal as feature_vix_stress,
            vix_regime
        FROM `cbi-v14.signals.vw_vix_stress_signal`
    ),
    harvest_signal AS (
        SELECT 
            date,
            brazil_precip,
            argentina_precip,
            drought_stress,
            harvest_pace_signal as feature_harvest_pace
        FROM `cbi-v14.signals.vw_harvest_pace_signal`
    ),
    china_signal AS (
        SELECT 
            date,
            import_volume,
            import_change,
            china_relations_signal as feature_china_relations
        FROM `cbi-v14.signals.vw_china_relations_signal`
    ),
    tariff_signal AS (
        SELECT 
            date,
            tariff_mentions_7d,
            china_trade_tension,
            tariff_threat_score as feature_tariff_threat,
            tariff_regime
        FROM `cbi-v14.signals.vw_tariff_threat_signal`
    ),
    gvi_signal AS (
        SELECT 
            date,
            vix_component,
            trump_component,
            panama_component,
            em_component,
            gvi_score as feature_geopolitical_volatility,
            gvi_regime
        FROM `cbi-v14.signals.vw_geopolitical_volatility_signal`
    ),
    biofuel_cascade AS (
        SELECT 
            signal_date as date,
            ethanol_capacity_utilization,
            crush_margin_normalized,
            policy_score,
            biofuel_cascade_composite as feature_biofuel_cascade,
            CASE 
                WHEN biofuel_crisis_flag THEN 'BIOFUEL_CRISIS'
                ELSE 'NORMAL'
            END as bsc_regime
        FROM `cbi-v14.signals.vw_biofuel_cascade_signal`
    ),
    hidden_corr AS (
        SELECT 
            date,
            zl_crude_corr_7d,
            zl_crude_corr_30d,
            zl_crude_corr_90d,
            zl_dxy_correlation,
            soy_palm_correlation,
            vix_trump_correlation,
            hci_score as feature_hidden_correlation,
            hci_regime
        FROM `cbi-v14.signals.vw_hidden_correlation_signal`
    ),
    biofuel_ethanol AS (
        SELECT 
            date,
            biofuel_price_strength,
            soy_advantage,
            policy_momentum,
            biofuel_ethanol_signal as feature_biofuel_ethanol,
            biofuel_regime
        FROM `cbi-v14.signals.vw_biofuel_ethanol_signal`
    )
    SELECT 
        d.date,
        
        -- Big 8 Features (normalized 0-1)
        COALESCE(v.feature_vix_stress, 0.5) as feature_vix_stress,
        COALESCE(h.feature_harvest_pace, 0.5) as feature_harvest_pace,
        COALESCE(c.feature_china_relations, 0.5) as feature_china_relations,
        COALESCE(t.feature_tariff_threat, 0.3) as feature_tariff_threat,
        COALESCE(g.feature_geopolitical_volatility, 0.4) as feature_geopolitical_volatility,
        COALESCE(bc.feature_biofuel_cascade, 0.5) as feature_biofuel_cascade,
        COALESCE(hc.feature_hidden_correlation, 0.0) as feature_hidden_correlation,
        COALESCE(be.feature_biofuel_ethanol, 0.5) as feature_biofuel_ethanol,
        
        -- Composite Big 8 Score
        (
            COALESCE(v.feature_vix_stress, 0.5) * 0.15 +
            COALESCE(h.feature_harvest_pace, 0.5) * 0.15 +
            COALESCE(c.feature_china_relations, 0.5) * 0.15 +
            COALESCE(t.feature_tariff_threat, 0.3) * 0.125 +
            COALESCE(g.feature_geopolitical_volatility, 0.4) * 0.125 +
            COALESCE(bc.feature_biofuel_cascade, 0.5) * 0.1 +
            COALESCE(hc.feature_hidden_correlation, 0.0) * 0.1 +
            COALESCE(be.feature_biofuel_ethanol, 0.5) * 0.1
        ) as big8_composite_score,
        
        -- Crisis Detection
        CASE
            WHEN COALESCE(v.feature_vix_stress, 0.5) > 0.8 THEN 'VIX_CRISIS'
            WHEN COALESCE(h.feature_harvest_pace, 0.5) < 0.3 THEN 'HARVEST_CRISIS'
            WHEN COALESCE(c.feature_china_relations, 0.5) > 0.8 THEN 'CHINA_CRISIS'
            WHEN COALESCE(t.feature_tariff_threat, 0.3) > 0.8 THEN 'TARIFF_CRISIS'
            WHEN COALESCE(g.feature_geopolitical_volatility, 0.4) > 0.8 THEN 'GVI_CRISIS'
            WHEN COALESCE(bc.feature_biofuel_cascade, 0.5) > 0.8 THEN 'BIOFUEL_CRISIS'
            WHEN ABS(COALESCE(hc.feature_hidden_correlation, 0.0)) > 0.8 THEN 'CORRELATION_CRISIS'
            WHEN COALESCE(be.feature_biofuel_ethanol, 0.5) > 0.8 THEN 'ETHANOL_CRISIS'
            ELSE 'NORMAL'
        END as market_regime,
        
        -- Primary Driver
        CASE
            WHEN COALESCE(v.feature_vix_stress, 0.5) = GREATEST(
                COALESCE(v.feature_vix_stress, 0.5),
                COALESCE(h.feature_harvest_pace, 0.5),
                COALESCE(c.feature_china_relations, 0.5),
                COALESCE(t.feature_tariff_threat, 0.3),
                COALESCE(g.feature_geopolitical_volatility, 0.4),
                COALESCE(bc.feature_biofuel_cascade, 0.5),
                ABS(COALESCE(hc.feature_hidden_correlation, 0.0)),
                COALESCE(be.feature_biofuel_ethanol, 0.5)
            ) THEN 'VIX_STRESS'
            WHEN COALESCE(h.feature_harvest_pace, 0.5) = GREATEST(
                COALESCE(v.feature_vix_stress, 0.5),
                COALESCE(h.feature_harvest_pace, 0.5),
                COALESCE(c.feature_china_relations, 0.5),
                COALESCE(t.feature_tariff_threat, 0.3),
                COALESCE(g.feature_geopolitical_volatility, 0.4),
                COALESCE(bc.feature_biofuel_cascade, 0.5),
                ABS(COALESCE(hc.feature_hidden_correlation, 0.0)),
                COALESCE(be.feature_biofuel_ethanol, 0.5)
            ) THEN 'HARVEST_PACE'
            WHEN COALESCE(c.feature_china_relations, 0.5) = GREATEST(
                COALESCE(v.feature_vix_stress, 0.5),
                COALESCE(h.feature_harvest_pace, 0.5),
                COALESCE(c.feature_china_relations, 0.5),
                COALESCE(t.feature_tariff_threat, 0.3),
                COALESCE(g.feature_geopolitical_volatility, 0.4),
                COALESCE(bc.feature_biofuel_cascade, 0.5),
                ABS(COALESCE(hc.feature_hidden_correlation, 0.0)),
                COALESCE(be.feature_biofuel_ethanol, 0.5)
            ) THEN 'CHINA_RELATIONS'
            ELSE 'MIXED_DRIVERS'
        END as primary_driver,
        
        -- Additional correlation features from hidden_corr (if available)
        COALESCE(hc.zl_crude_corr_7d, 0) as corr_zl_crude_7d,
        COALESCE(hc.zl_crude_corr_30d, 0) as corr_zl_crude_30d,
        COALESCE(hc.zl_crude_corr_90d, 0) as corr_zl_crude_90d,
        COALESCE(hc.zl_dxy_correlation, 0) as corr_zl_dxy,
        COALESCE(hc.soy_palm_correlation, 0) as corr_soy_palm,
        
        CURRENT_TIMESTAMP() as updated_at
        
    FROM date_range d
    LEFT JOIN vix_signal v ON d.date = v.date
    LEFT JOIN harvest_signal h ON d.date = h.date
    LEFT JOIN china_signal c ON d.date = c.date
    LEFT JOIN tariff_signal t ON d.date = t.date
    LEFT JOIN gvi_signal g ON d.date = g.date
    LEFT JOIN biofuel_cascade bc ON d.date = bc.date
    LEFT JOIN hidden_corr hc ON d.date = hc.date
    LEFT JOIN biofuel_ethanol be ON d.date = be.date
    WHERE d.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)
    ORDER BY d.date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created neural.vw_big_eight_signals")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create neural.vw_big_eight_signals: {e}")
        return False

def verify_big8():
    """Verify the Big 8 aggregation view"""
    query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT date) as unique_dates,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        
        -- Check each signal
        AVG(feature_vix_stress) as avg_vix,
        AVG(feature_harvest_pace) as avg_harvest,
        AVG(feature_china_relations) as avg_china,
        AVG(feature_tariff_threat) as avg_tariff,
        AVG(feature_geopolitical_volatility) as avg_gvi,
        AVG(feature_biofuel_cascade) as avg_bsc,
        AVG(feature_hidden_correlation) as avg_hci,
        AVG(feature_biofuel_ethanol) as avg_biofuel,
        
        AVG(big8_composite_score) as avg_composite,
        
        -- Check regimes
        COUNT(CASE WHEN market_regime != 'NORMAL' THEN 1 END) as crisis_days,
        STRING_AGG(DISTINCT market_regime, ', ') as regimes_found
        
    FROM `cbi-v14.neural.vw_big_eight_signals`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR)
    """
    
    try:
        result = list(client.query(query))[0]
        logger.info("\nBig 8 Aggregation Statistics:")
        logger.info(f"  Total Rows: {result['total_rows']}")
        logger.info(f"  Date Range: {result['earliest_date']} to {result['latest_date']}")
        logger.info(f"\nSignal Averages (0-1 scale):")
        logger.info(f"  VIX Stress: {result['avg_vix']:.3f}")
        logger.info(f"  Harvest Pace: {result['avg_harvest']:.3f}")
        logger.info(f"  China Relations: {result['avg_china']:.3f}")
        logger.info(f"  Tariff Threat: {result['avg_tariff']:.3f}")
        logger.info(f"  GVI: {result['avg_gvi']:.3f}")
        logger.info(f"  BSC: {result['avg_bsc']:.3f}")
        logger.info(f"  HCI: {result['avg_hci']:.3f}")
        logger.info(f"  Biofuel/Ethanol: {result['avg_biofuel']:.3f}")
        logger.info(f"\nComposite Score: {result['avg_composite']:.3f}")
        logger.info(f"Crisis Days: {result['crisis_days']}")
        logger.info(f"Regimes: {result['regimes_found']}")
        
        return result['total_rows'] > 0
    except Exception as e:
        logger.error(f"Could not verify: {e}")
        return False

def main():
    """Create and verify the Big 8 signals aggregation"""
    logger.info("=" * 50)
    logger.info("Creating Big 8 Signals Aggregation View")
    logger.info("=" * 50)
    
    # Create the view
    logger.info("\nCreating neural.vw_big_eight_signals...")
    success = create_big_eight_signals()
    
    if success:
        logger.info("\nVerifying Big 8 aggregation...")
        has_data = verify_big8()
        
        if has_data:
            logger.info("\n" + "=" * 50)
            logger.info("✅ SUCCESS: Big 8 Signals Aggregation Created!")
            logger.info("This view combines all 8 signals:")
            logger.info("  1. VIX Stress")
            logger.info("  2. Harvest Pace")
            logger.info("  3. China Relations")
            logger.info("  4. Tariff Threat")
            logger.info("  5. Geopolitical Volatility (GVI)")
            logger.info("  6. Biofuel Cascade (BSC)")
            logger.info("  7. Hidden Correlations (HCI)")
            logger.info("  8. Biofuel/Ethanol")
            logger.info("\nReady for multi-horizon training!")
        else:
            logger.warning("⚠️ View created but may have limited data")
    else:
        logger.error("❌ Failed to create Big 8 aggregation view")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
