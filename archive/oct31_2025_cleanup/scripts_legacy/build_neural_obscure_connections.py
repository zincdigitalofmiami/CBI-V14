#!/usr/bin/env python3
"""
Build Neural Network for Obscure Connections
This is where we find the ALPHA - non-obvious relationships that others miss!
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_interaction_features():
    """
    Create interaction features that capture obscure relationships
    These are the non-linear, non-obvious connections that generate alpha
    """
    
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_neural_interaction_features` AS
    WITH base_data AS (
        -- Get all base features
        SELECT 
            date,
            zl_price_current,
            feature_vix_stress,
            feature_harvest_pace,
            feature_china_relations,
            feature_tariff_threat,
            feature_geopolitical_volatility,
            feature_biofuel_cascade,
            feature_hidden_correlation,
            feature_biofuel_ethanol,
            corr_zl_crude_7d,
            corr_zl_palm_30d,
            corr_zl_vix_30d,
            brazil_temp,
            brazil_precip,
            argentina_temp,
            argentina_precip,
            avg_sentiment,
            sentiment_volume
        FROM `cbi-v14.models.vw_neural_training_dataset_v2_FIXED`
        WHERE NOT IS_NAN(corr_zl_crude_7d)  -- Filter NaN values
    ),
    market_regime AS (
        -- Add our new market regime signals
        SELECT 
            date,
            trade_war_impact_score,
            supply_glut_score,
            bear_market_score,
            biofuel_demand_score
        FROM `cbi-v14.signals.vw_trade_war_impact` t
        JOIN `cbi-v14.signals.vw_supply_glut_indicator` s USING(date)
        JOIN `cbi-v14.signals.vw_bear_market_regime` b USING(date)
        JOIN `cbi-v14.signals.vw_biofuel_policy_intensity` p USING(date)
    ),
    cftc_data AS (
        -- Add CFTC positioning
        SELECT 
            report_date as date,
            commercial_net / NULLIF(open_interest, 0) as commercial_net_pct,
            managed_money_net / NULLIF(open_interest, 0) as managed_money_net_pct,
            open_interest / 1000000 as open_interest_mm
        FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
        WHERE commodity = 'Soybean_Oil'
    ),
    crush_margins AS (
        -- Add crush margins
        SELECT 
            date,
            crush_margin,
            crush_margin_7d_ma,
            crush_margin_30d_ma,
            CASE 
                WHEN crush_margin > crush_margin_30d_ma THEN 1 
                ELSE 0 
            END as margin_expanding
        FROM `cbi-v14.models.vw_crush_margins`
    )
    SELECT 
        b.date,
        b.zl_price_current,
        
        -- OBSCURE INTERACTION 1: Weather × Sentiment × Harvest
        -- When weather is bad AND sentiment is negative AND harvest is critical = EXPLOSIVE
        (COALESCE(b.brazil_precip, 100) / 100) * 
        COALESCE(b.avg_sentiment, 0.5) * 
        COALESCE(b.feature_harvest_pace, 0.5) as weather_sentiment_harvest_interaction,
        
        -- OBSCURE INTERACTION 2: VIX × China Relations × Trade War
        -- Fear + China tensions + Trade war = Maximum volatility
        COALESCE(b.feature_vix_stress, 0.5) * 
        COALESCE(b.feature_china_relations, 0.5) * 
        COALESCE(m.trade_war_impact_score, 0.5) as fear_china_trade_interaction,
        
        -- OBSCURE INTERACTION 3: Palm Correlation × Biofuel × Crush Margins
        -- When palm correlation breaks AND biofuel demand high AND margins good = RALLY
        ABS(COALESCE(b.corr_zl_palm_30d, 0)) * 
        COALESCE(b.feature_biofuel_cascade, 0.5) * 
        (COALESCE(cm.crush_margin, 0) / 100) as palm_biofuel_margin_interaction,
        
        -- OBSCURE INTERACTION 4: Crude Correlation × Geopolitical × Dollar
        -- Energy complex + Geopolitics + Dollar weakness = Commodity super-cycle
        ABS(COALESCE(b.corr_zl_crude_7d, 0)) * 
        COALESCE(b.feature_geopolitical_volatility, 0.5) * 
        COALESCE(b.corr_zl_vix_30d, 0) as energy_geo_dollar_interaction,
        
        -- OBSCURE INTERACTION 5: CFTC × Supply Glut × Bear Market
        -- Commercial buying in oversupply bear market = Contrarian signal
        ABS(COALESCE(cftc.commercial_net_pct, 0)) * 
        COALESCE(m.supply_glut_score, 0.5) * 
        COALESCE(m.bear_market_score, 0.5) as positioning_supply_regime_interaction,
        
        -- POLYNOMIAL FEATURES (capture non-linear relationships)
        POWER(COALESCE(b.feature_vix_stress, 0.5), 2) as vix_squared,
        POWER(COALESCE(b.feature_vix_stress, 0.5), 3) as vix_cubed,
        POWER(COALESCE(b.feature_harvest_pace, 0.5), 2) as harvest_squared,
        POWER(ABS(COALESCE(b.corr_zl_crude_7d, 0)), 2) as correlation_squared,
        
        -- CROSS-MARKET REGIME INTERACTIONS
        CASE 
            WHEN COALESCE(b.feature_vix_stress, 0) > 0.7 
             AND COALESCE(b.feature_harvest_pace, 0) > 0.7 
            THEN 1 ELSE 0 
        END as double_crisis_flag,
        
        CASE 
            WHEN ABS(COALESCE(b.corr_zl_crude_7d, 0)) < 0.2 
             AND ABS(COALESCE(b.corr_zl_palm_30d, 0)) < 0.2 
            THEN 1 ELSE 0 
        END as correlation_breakdown_flag,
        
        -- SENTIMENT EXTREMES
        CASE 
            WHEN COALESCE(b.avg_sentiment, 0.5) > 0.8 THEN 2  -- Euphoria
            WHEN COALESCE(b.avg_sentiment, 0.5) > 0.6 THEN 1  -- Bullish
            WHEN COALESCE(b.avg_sentiment, 0.5) < 0.2 THEN -2 -- Panic
            WHEN COALESCE(b.avg_sentiment, 0.5) < 0.4 THEN -1 -- Bearish
            ELSE 0  -- Neutral
        END as sentiment_regime,
        
        -- VOLUME ANOMALIES
        CASE 
            WHEN COALESCE(b.sentiment_volume, 0) > 
                 AVG(COALESCE(b.sentiment_volume, 0)) OVER (
                     ORDER BY b.date 
                     ROWS BETWEEN 29 PRECEDING AND 1 PRECEDING
                 ) * 2 
            THEN 1 ELSE 0 
        END as volume_spike_flag,
        
        -- LAGGED INTERACTIONS (find lead/lag relationships)
        LAG(COALESCE(b.feature_china_relations, 0.5), 3) OVER (ORDER BY b.date) * 
        COALESCE(b.feature_tariff_threat, 0.5) as lagged_china_tariff_interaction,
        
        LAG(COALESCE(b.corr_zl_crude_7d, 0), 5) OVER (ORDER BY b.date) * 
        COALESCE(b.feature_biofuel_cascade, 0.5) as lagged_energy_biofuel_interaction,
        
        -- SEASONALITY INTERACTIONS
        EXTRACT(MONTH FROM b.date) as month,
        CASE 
            WHEN EXTRACT(MONTH FROM b.date) IN (9, 10, 11) THEN 1  -- Harvest
            WHEN EXTRACT(MONTH FROM b.date) IN (4, 5, 6) THEN 2    -- Planting
            ELSE 0 
        END as seasonal_phase,
        
        -- Include regime scores
        COALESCE(m.trade_war_impact_score, 0) as trade_war_impact_score,
        COALESCE(m.supply_glut_score, 0) as supply_glut_score,
        COALESCE(m.bear_market_score, 0) as bear_market_score,
        COALESCE(m.biofuel_demand_score, 0) as biofuel_demand_score,
        
        -- Include CFTC
        COALESCE(cftc.commercial_net_pct, 0) as commercial_net_pct,
        COALESCE(cftc.open_interest_mm, 0.7) as open_interest_mm,
        
        -- Include crush margins
        COALESCE(cm.crush_margin, 500) as crush_margin,
        COALESCE(cm.margin_expanding, 0) as margin_expanding
        
    FROM base_data b
    LEFT JOIN market_regime m ON b.date = m.date
    LEFT JOIN cftc_data cftc ON b.date = cftc.date
    LEFT JOIN crush_margins cm ON b.date = cm.date
    WHERE b.date >= '2023-01-01'  -- Focus on recent data with all features
    ORDER BY b.date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created neural interaction features successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create interaction features: {e}")
        return False

def train_deep_neural_network():
    """
    Train a deep neural network to find obscure patterns
    This is where the magic happens - finding alpha others miss
    """
    
    query = """
    CREATE OR REPLACE MODEL `cbi-v14.models.zl_deep_neural_obscure_v1`
    OPTIONS(
        model_type='DNN_REGRESSOR',
        hidden_units=[512, 256, 128, 64, 32, 16],  -- 6 layers for complex patterns
        activation_fn='RELU',
        dropout=0.3,
        batch_size=32,
        learn_rate=0.0001,  -- Small learning rate for stability
        optimizer='ADAM',
        input_label_cols=['zl_price_current'],
        data_split_method='SEQ',
        data_split_col='date',
        max_iterations=500,
        early_stop=TRUE,
        min_rel_progress=0.0001,
        warm_start=FALSE
    ) AS
    SELECT 
        * EXCEPT(date)
    FROM `cbi-v14.models.vw_neural_interaction_features`
    WHERE zl_price_current IS NOT NULL
    """
    
    try:
        logger.info("Training deep neural network for obscure connections...")
        logger.info("This may take 5-10 minutes...")
        client.query(query).result()
        logger.info("✅ Trained deep neural network successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to train neural network: {e}")
        return False

def verify_interactions():
    """Verify the interaction features are working"""
    
    verify_query = """
    SELECT 
        COUNT(*) as total_rows,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        
        -- Check interaction features
        AVG(weather_sentiment_harvest_interaction) as avg_weather_interaction,
        AVG(fear_china_trade_interaction) as avg_fear_interaction,
        AVG(palm_biofuel_margin_interaction) as avg_palm_interaction,
        AVG(energy_geo_dollar_interaction) as avg_energy_interaction,
        AVG(positioning_supply_regime_interaction) as avg_positioning_interaction,
        
        -- Check flags
        SUM(double_crisis_flag) as double_crisis_days,
        SUM(correlation_breakdown_flag) as correlation_breakdown_days,
        SUM(volume_spike_flag) as volume_spike_days,
        
        -- Check regimes
        COUNTIF(sentiment_regime = 2) as euphoria_days,
        COUNTIF(sentiment_regime = -2) as panic_days
        
    FROM `cbi-v14.models.vw_neural_interaction_features`
    WHERE date >= '2024-01-01'
    """
    
    print("\n" + "=" * 80)
    print("NEURAL INTERACTION FEATURES VERIFICATION")
    print("=" * 80)
    
    try:
        result = list(client.query(verify_query).result())[0]
        print(f"Total rows: {result.total_rows}")
        print(f"Date range: {result.earliest_date} to {result.latest_date}")
        print(f"\nInteraction Averages:")
        print(f"  Weather×Sentiment×Harvest: {result.avg_weather_interaction:.4f}")
        print(f"  Fear×China×Trade: {result.avg_fear_interaction:.4f}")
        print(f"  Palm×Biofuel×Margin: {result.avg_palm_interaction:.4f}")
        print(f"  Energy×Geo×Dollar: {result.avg_energy_interaction:.4f}")
        print(f"  Positioning×Supply×Regime: {result.avg_positioning_interaction:.4f}")
        print(f"\nExtreme Events (2024+):")
        print(f"  Double crisis days: {result.double_crisis_days}")
        print(f"  Correlation breakdown days: {result.correlation_breakdown_days}")
        print(f"  Volume spike days: {result.volume_spike_days}")
        print(f"  Euphoria days: {result.euphoria_days}")
        print(f"  Panic days: {result.panic_days}")
    except Exception as e:
        print(f"Error verifying interactions: {e}")

def main():
    """Create interaction features and train neural network"""
    print("=" * 80)
    print("BUILDING NEURAL NETWORK FOR OBSCURE CONNECTIONS")
    print("=" * 80)
    print("\nThis finds the ALPHA - non-obvious relationships others miss!")
    print("Creating interaction features that capture:")
    print("  • Weather × Sentiment × Harvest interactions")
    print("  • VIX × China × Trade war cascades")
    print("  • Palm × Biofuel × Crush margin dynamics")
    print("  • CFTC × Supply × Regime contrarian signals")
    print("  • Non-linear polynomial relationships")
    
    # Step 1: Create interaction features
    print("\n1. Creating interaction features...")
    success = create_interaction_features()
    
    if success:
        # Step 2: Verify features
        verify_interactions()
        
        # Step 3: Train neural network
        print("\n2. Training deep neural network...")
        print("   (This will take 5-10 minutes)")
        # Commenting out actual training for now to save time/cost
        # success = train_deep_neural_network()
        print("   ⚠️ Skipping actual training to save compute costs")
        print("   Run train_deep_neural_network() when ready")
        
        print("\n✅ Neural interaction features ready!")
        print("   These capture the obscure connections for alpha generation")
    else:
        print("\n❌ Failed to create interaction features")
    
    return success

if __name__ == "__main__":
    main()
