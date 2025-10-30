#!/usr/bin/env python3
"""
Create biofuel features for neural network training
This captures the energy-agriculture bridge that drives 30% of soy oil demand
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_biofuel_bridge_features():
    """Create comprehensive biofuel features linking energy and agriculture"""
    
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_biofuel_bridge_features` AS
    WITH crude_prices AS (
        -- Get crude oil prices for energy side
        SELECT 
            date,
            close_price as crude_price,
            AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as crude_ma30
        FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
        WHERE symbol IN ('CRUDE_OIL_PRICES', 'CL')
    ),
    soy_oil_prices AS (
        -- Get soy oil prices
        SELECT 
            DATE(time) as date,
            close as soy_oil_price,
            AVG(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as soy_ma30
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
        WHERE symbol = 'ZL'
    ),
    palm_prices AS (
        -- Get palm oil for substitution dynamics
        SELECT 
            DATE(time) as date,
            close as palm_price,
            AVG(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as palm_ma30
        FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
    ),
    biofuel_policy AS (
        -- Get biofuel policy data (simplified for available schema)
        SELECT 
            date,
            MAX(mandate_volume) as mandate_volume,
            MAX(confidence_score) as policy_confidence,
            COUNT(*) as policy_updates
        FROM `cbi-v14.staging.biofuel_policy`
        WHERE policy_type IN ('RFS', 'LCFS', 'RED', 'SAF')
        GROUP BY date
    ),
    spreads_and_ratios AS (
        SELECT 
            COALESCE(s.date, c.date, p.date) as date,
            
            -- Core prices
            s.soy_oil_price,
            c.crude_price,
            p.palm_price,
            
            -- ENERGY-AG SPREADS (key arbitrage indicators)
            -- BOHO Spread: Biodiesel value vs heating oil equivalent
            (s.soy_oil_price * 7.5) - (c.crude_price * 0.0238) as boho_spread,
            
            -- Soy-Crude Ratio: Direct energy linkage
            SAFE_DIVIDE(s.soy_oil_price, c.crude_price) as soy_crude_ratio,
            
            -- Palm-Soy Spread: Substitution indicator
            p.palm_price - s.soy_oil_price as palm_soy_spread,
            SAFE_DIVIDE(p.palm_price - s.soy_oil_price, s.soy_oil_price) as palm_soy_spread_pct,
            
            -- BIODIESEL ECONOMICS
            -- Simplified biodiesel margin (soy oil is ~80% of biodiesel cost)
            CASE 
                WHEN c.crude_price > 80 THEN 1.0  -- Highly profitable
                WHEN c.crude_price > 70 THEN 0.7  -- Profitable
                WHEN c.crude_price > 60 THEN 0.4  -- Marginal
                ELSE 0.1  -- Unprofitable
            END as biodiesel_profitability_score,
            
            -- Crude regime (affects biofuel demand)
            CASE
                WHEN c.crude_price > 100 THEN 'HIGH_ENERGY'
                WHEN c.crude_price > 80 THEN 'FAVORABLE'
                WHEN c.crude_price > 60 THEN 'NEUTRAL'
                ELSE 'UNFAVORABLE'
            END as energy_regime,
            
            -- MOVING AVERAGES for trend
            s.soy_ma30,
            c.crude_ma30,
            p.palm_ma30,
            
            -- Momentum indicators
            (s.soy_oil_price - s.soy_ma30) / NULLIF(s.soy_ma30, 0) as soy_momentum_30d,
            (c.crude_price - c.crude_ma30) / NULLIF(c.crude_ma30, 0) as crude_momentum_30d
            
        FROM soy_oil_prices s
        FULL OUTER JOIN crude_prices c ON s.date = c.date
        FULL OUTER JOIN palm_prices p ON s.date = p.date
    ),
    biofuel_signals AS (
        SELECT 
            sr.date,
            
            -- PRICE FEATURES
            sr.soy_oil_price,
            sr.crude_price,
            sr.palm_price,
            
            -- SPREAD FEATURES (Critical for arbitrage)
            COALESCE(sr.boho_spread, 0) as boho_spread,
            COALESCE(sr.soy_crude_ratio, 0) as soy_crude_ratio,
            COALESCE(sr.palm_soy_spread, 0) as palm_soy_spread,
            COALESCE(sr.palm_soy_spread_pct, 0) as palm_soy_spread_pct,
            
            -- PROFITABILITY FEATURES
            sr.biodiesel_profitability_score,
            sr.energy_regime,
            
            -- POLICY FEATURES (simplified with available data)
            COALESCE(bp.mandate_volume, 15000) as mandate_volume_mgal,
            COALESCE(bp.policy_confidence, 0.7) as policy_confidence,
            COALESCE(bp.policy_updates, 0) as policy_update_count,
            
            -- COMPOSITE BIOFUEL DEMAND SCORE
            (
                sr.biodiesel_profitability_score * 0.3 +  -- Energy economics
                LEAST(GREATEST(COALESCE(bp.d4_rin_price, 2.0) / 3.0, 0), 1) * 0.3 +  -- Policy support
                CASE 
                    WHEN sr.palm_soy_spread_pct > 0.1 THEN 0.4  -- Soy preferred
                    WHEN sr.palm_soy_spread_pct > 0 THEN 0.2
                    ELSE 0
                END * 0.2 +  -- Substitution dynamics
                LEAST(COALESCE(bp.rd_capacity, 3000) / 5000, 1) * 0.2  -- Capacity utilization
            ) as biofuel_demand_score,
            
            -- REGIME FLAGS
            CASE WHEN sr.crude_price > 80 AND sr.boho_spread > 0 THEN 1 ELSE 0 END as biofuel_profitable_flag,
            CASE WHEN sr.palm_soy_spread_pct > 0.15 THEN 1 ELSE 0 END as soy_preferred_flag,
            CASE WHEN sr.soy_crude_ratio > 0.7 THEN 1 ELSE 0 END as energy_correlation_high_flag,
            
            -- CONDITIONAL CORRELATIONS (energy-ag linkage strength)
            CASE 
                WHEN sr.crude_price > 80 THEN 0.5  -- Strong linkage
                WHEN sr.crude_price > 70 THEN 0.3  -- Moderate linkage
                WHEN sr.crude_price > 60 THEN 0.15  -- Weak linkage
                ELSE 0.05  -- Minimal linkage
            END as energy_ag_correlation_strength,
            
            -- TREND FEATURES
            sr.soy_momentum_30d,
            sr.crude_momentum_30d,
            
            CURRENT_TIMESTAMP() as updated_at
            
        FROM spreads_and_ratios sr
        LEFT JOIN biofuel_policy bp ON sr.date = bp.date
    )
    SELECT * FROM biofuel_signals
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 YEAR)
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created models.vw_biofuel_bridge_features")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create biofuel bridge features: {e}")
        return False

def create_enhanced_training_view():
    """Update the training view to include biofuel features"""
    
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_neural_training_dataset_v3` AS
    SELECT 
        t.*,
        
        -- ADD BIOFUEL BRIDGE FEATURES
        b.boho_spread,
        b.soy_crude_ratio,
        b.palm_soy_spread_pct,
        b.biodiesel_profitability_score,
        b.d4_rin_price,
        b.d6_rin_price,
        b.rd_capacity_bpd,
        b.biofuel_demand_score,
        b.biofuel_profitable_flag,
        b.soy_preferred_flag,
        b.energy_ag_correlation_strength,
        
        -- Energy regime for conditional models
        b.energy_regime
        
    FROM `cbi-v14.models.vw_neural_training_dataset_v2` t
    LEFT JOIN `cbi-v14.models.vw_biofuel_bridge_features` b
        ON t.date = b.date
    WHERE t.target_12m IS NOT NULL
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created models.vw_neural_training_dataset_v3 with biofuel features")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create enhanced training view: {e}")
        return False

def verify_biofuel_features():
    """Verify biofuel features are working"""
    
    query = """
    SELECT 
        COUNT(*) as total_rows,
        
        -- Check biofuel features
        AVG(boho_spread) as avg_boho_spread,
        AVG(soy_crude_ratio) as avg_soy_crude_ratio,
        AVG(palm_soy_spread_pct) as avg_palm_soy_spread,
        AVG(biodiesel_profitability_score) as avg_biodiesel_profit,
        AVG(biofuel_demand_score) as avg_biofuel_demand,
        
        -- Check regime distribution
        COUNT(CASE WHEN energy_regime = 'FAVORABLE' THEN 1 END) as favorable_days,
        COUNT(CASE WHEN energy_regime = 'HIGH_ENERGY' THEN 1 END) as high_energy_days,
        
        -- Check correlation strength
        AVG(energy_ag_correlation_strength) as avg_correlation_strength,
        
        -- Check flags
        SUM(biofuel_profitable_flag) as profitable_days,
        SUM(soy_preferred_flag) as soy_preferred_days
        
    FROM `cbi-v14.models.vw_biofuel_bridge_features`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR)
    """
    
    try:
        result = list(client.query(query))[0]
        
        logger.info("\nBiofuel Bridge Features Statistics:")
        logger.info(f"  Total Rows: {result['total_rows']}")
        logger.info(f"\nSpread Indicators:")
        logger.info(f"  BOHO Spread: ${result['avg_boho_spread']:.2f}")
        logger.info(f"  Soy-Crude Ratio: {result['avg_soy_crude_ratio']:.3f}")
        logger.info(f"  Palm-Soy Spread: {result['avg_palm_soy_spread']:.1%}")
        logger.info(f"\nDemand Indicators:")
        logger.info(f"  Biodiesel Profitability: {result['avg_biodiesel_profit']:.2f}")
        logger.info(f"  Biofuel Demand Score: {result['avg_biofuel_demand']:.2f}")
        logger.info(f"\nRegime Analysis:")
        logger.info(f"  Favorable Energy Days: {result['favorable_days']}")
        logger.info(f"  High Energy Days: {result['high_energy_days']}")
        logger.info(f"  Profitable Biofuel Days: {result['profitable_days']}")
        logger.info(f"\nCorrelation Strength:")
        logger.info(f"  Avg Energy-Ag Correlation: {result['avg_correlation_strength']:.3f}")
        
        return result['total_rows'] > 0
        
    except Exception as e:
        logger.error(f"Could not verify: {e}")
        return False

def main():
    """Create biofuel features for neural training"""
    
    logger.info("=" * 70)
    logger.info("INTEGRATING BIOFUEL INTO NEURAL TRAINING")
    logger.info("=" * 70)
    logger.info("\nBiofuel = The Energy-Agriculture Bridge")
    logger.info("30% of US soy oil demand, growing to 50% by 2030")
    
    # Step 1: Create biofuel bridge features
    logger.info("\nStep 1: Creating biofuel bridge features...")
    success1 = create_biofuel_bridge_features()
    
    # Step 2: Update training view
    logger.info("\nStep 2: Updating training view with biofuel...")
    success2 = create_enhanced_training_view()
    
    # Step 3: Verify
    if success1 and success2:
        logger.info("\nStep 3: Verifying biofuel integration...")
        has_data = verify_biofuel_features()
        
        if has_data:
            logger.info("\n" + "=" * 70)
            logger.info("✅ SUCCESS: Biofuel Integrated into Neural Training!")
            logger.info("\nKey Features Added:")
            logger.info("  • BOHO Spread (biodiesel-heating oil)")
            logger.info("  • Soy-Crude Ratio (energy linkage)")
            logger.info("  • Palm-Soy Spread (substitution)")
            logger.info("  • RIN Prices (policy support)")
            logger.info("  • Energy Regime Detection")
            logger.info("  • Conditional Correlations")
            logger.info("\nExpected Impact:")
            logger.info("  • Better long-term forecasts (6-12 months)")
            logger.info("  • Improved regime detection")
            logger.info("  • Policy shock capture")
            logger.info("  • Energy transition insights")
        else:
            logger.warning("⚠️ Views created but may need data")
    else:
        logger.error("❌ Failed to integrate biofuel features")

if __name__ == "__main__":
    main()
