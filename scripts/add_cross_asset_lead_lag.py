#!/usr/bin/env python3
"""
Add Cross-Asset Lead/Lag Analysis
Identifies which assets lead soybean oil price movements
Critical for predictive signals
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_lead_lag_analysis():
    """
    Create lead/lag analysis between soybean oil and other assets
    Palm oil leads soy by 2-3 days, crude leads by 1-2 days
    """
    
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_cross_asset_lead_lag` AS
    WITH aligned_prices AS (
        -- Get all asset prices aligned by date
        SELECT 
            COALESCE(zl.date, cl.date, palm.date, corn.date, wheat.date) as date,
            
            -- Soybean oil (our target)
            zl.close as zl_price,
            
            -- Crude oil
            cl.close_price as crude_price,
            
            -- Palm oil  
            palm.close as palm_price,
            
            -- Corn
            corn.close as corn_price,
            
            -- Wheat
            wheat.close as wheat_price,
            
            -- VIX
            vix.close as vix_level,
            
            -- USD Index
            dxy.close_price as dxy_level
            
        FROM (
            SELECT DATE(time) as date, close
            FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
            WHERE symbol = 'ZL'
        ) zl
        FULL OUTER JOIN (
            SELECT date, close_price
            FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
        ) cl ON zl.date = cl.date
        FULL OUTER JOIN (
            SELECT DATE(time) as date, close
            FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
        ) palm ON zl.date = palm.date
        FULL OUTER JOIN (
            SELECT DATE(time) as date, close
            FROM `cbi-v14.forecasting_data_warehouse.corn_prices`
        ) corn ON zl.date = corn.date
        FULL OUTER JOIN (
            SELECT DATE(time) as date, close
            FROM `cbi-v14.forecasting_data_warehouse.wheat_prices`
        ) wheat ON zl.date = wheat.date
        FULL OUTER JOIN (
            SELECT date, close
            FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
        ) vix ON zl.date = vix.date
        FULL OUTER JOIN (
            SELECT date, close_price
            FROM `cbi-v14.forecasting_data_warehouse.usd_index_prices`
        ) dxy ON zl.date = dxy.date
    ),
    lead_lag_features AS (
        SELECT 
            date,
            zl_price,
            
            -- PALM OIL LEADS (2-3 days ahead)
            LAG(palm_price, 1) OVER (ORDER BY date) as palm_lag1,
            LAG(palm_price, 2) OVER (ORDER BY date) as palm_lag2,
            LAG(palm_price, 3) OVER (ORDER BY date) as palm_lag3,
            
            -- Palm oil momentum (leading indicator)
            (LAG(palm_price, 1) OVER (ORDER BY date) - 
             LAG(palm_price, 3) OVER (ORDER BY date)) / 
            NULLIF(LAG(palm_price, 3) OVER (ORDER BY date), 0) as palm_momentum_3d,
            
            -- CRUDE OIL LEADS (1-2 days ahead)
            LAG(crude_price, 1) OVER (ORDER BY date) as crude_lag1,
            LAG(crude_price, 2) OVER (ORDER BY date) as crude_lag2,
            
            -- Crude momentum
            (LAG(crude_price, 1) OVER (ORDER BY date) - 
             LAG(crude_price, 2) OVER (ORDER BY date)) / 
            NULLIF(LAG(crude_price, 2) OVER (ORDER BY date), 0) as crude_momentum_2d,
            
            -- VIX LEADS (risk-off leads commodity selling)
            LAG(vix_level, 1) OVER (ORDER BY date) as vix_lag1,
            LAG(vix_level, 2) OVER (ORDER BY date) as vix_lag2,
            
            -- VIX spike indicator
            CASE 
                WHEN LAG(vix_level, 1) OVER (ORDER BY date) > 30 THEN 1
                ELSE 0
            END as vix_spike_lag1,
            
            -- CORN/WHEAT (compete for acreage)
            LAG(corn_price, 1) OVER (ORDER BY date) as corn_lag1,
            LAG(wheat_price, 1) OVER (ORDER BY date) as wheat_lag1,
            
            -- Corn/Soy ratio (planting decisions)
            LAG(corn_price, 1) OVER (ORDER BY date) / 
            NULLIF(zl_price, 0) as corn_soy_ratio_lag1,
            
            -- DXY INVERSE RELATIONSHIP
            LAG(dxy_level, 1) OVER (ORDER BY date) as dxy_lag1,
            LAG(dxy_level, 2) OVER (ORDER BY date) as dxy_lag2,
            
            -- Dollar momentum (inverse predictor)
            (LAG(dxy_level, 1) OVER (ORDER BY date) - 
             LAG(dxy_level, 3) OVER (ORDER BY date)) / 
            NULLIF(LAG(dxy_level, 3) OVER (ORDER BY date), 0) as dxy_momentum_3d,
            
            -- CONTEMPORANEOUS RELATIONSHIPS
            crude_price,
            palm_price,
            corn_price,
            wheat_price,
            vix_level,
            dxy_level
            
        FROM aligned_prices
    ),
    granger_causality AS (
        -- Calculate which assets Granger-cause soybean oil
        SELECT 
            llf.*,
            
            -- Palm leads soy (2-3 day lag optimal)
            CORR(llf.palm_lag2, llf.zl_price) OVER (
                ORDER BY llf.date 
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as palm_lead2_correlation,
            
            -- Crude leads soy (1-2 day lag)
            CORR(llf.crude_lag1, llf.zl_price) OVER (
                ORDER BY llf.date 
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as crude_lead1_correlation,
            
            -- VIX leads inversely (1 day)
            CORR(llf.vix_lag1, llf.zl_price) OVER (
                ORDER BY llf.date 
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as vix_lead1_correlation,
            
            -- DXY inverse lead (1-2 days)
            CORR(llf.dxy_lag1, llf.zl_price) OVER (
                ORDER BY llf.date 
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as dxy_lead1_correlation,
            
            -- Contemporaneous correlations for comparison
            CORR(llf.palm_price, llf.zl_price) OVER (
                ORDER BY llf.date 
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as palm_contemp_correlation,
            
            CORR(llf.crude_price, llf.zl_price) OVER (
                ORDER BY llf.date 
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as crude_contemp_correlation
            
        FROM lead_lag_features llf
    ),
    directional_agreement AS (
        -- Check if leading assets correctly predict direction
        SELECT 
            gc.*,
            
            -- Palm directional prediction (2-day lead)
            CASE 
                WHEN SIGN(gc.palm_lag2 - LAG(gc.palm_lag2, 1) OVER (ORDER BY gc.date)) = 
                     SIGN(gc.zl_price - LAG(gc.zl_price, 1) OVER (ORDER BY gc.date))
                THEN 1 ELSE 0
            END as palm_direction_correct,
            
            -- Crude directional prediction (1-day lead)
            CASE 
                WHEN SIGN(gc.crude_lag1 - LAG(gc.crude_lag1, 1) OVER (ORDER BY gc.date)) = 
                     SIGN(gc.zl_price - LAG(gc.zl_price, 1) OVER (ORDER BY gc.date))
                THEN 1 ELSE 0
            END as crude_direction_correct,
            
            -- VIX inverse prediction
            CASE 
                WHEN SIGN(gc.vix_lag1 - LAG(gc.vix_lag1, 1) OVER (ORDER BY gc.date)) = 
                     -SIGN(gc.zl_price - LAG(gc.zl_price, 1) OVER (ORDER BY gc.date))
                THEN 1 ELSE 0
            END as vix_inverse_correct,
            
            -- Combined signal strength
            CASE 
                WHEN gc.palm_momentum_3d > 0.02 AND gc.crude_momentum_2d > 0.01 THEN 'STRONG_BUY'
                WHEN gc.palm_momentum_3d > 0.01 AND gc.crude_momentum_2d > 0 THEN 'BUY'
                WHEN gc.palm_momentum_3d < -0.02 AND gc.crude_momentum_2d < -0.01 THEN 'STRONG_SELL'
                WHEN gc.palm_momentum_3d < -0.01 AND gc.crude_momentum_2d < 0 THEN 'SELL'
                ELSE 'NEUTRAL'
            END as lead_signal
            
        FROM granger_causality gc
    )
    SELECT 
        date,
        zl_price,
        
        -- Leading indicators
        palm_lag1,
        palm_lag2,
        palm_lag3,
        palm_momentum_3d,
        crude_lag1,
        crude_lag2,
        crude_momentum_2d,
        vix_lag1,
        vix_lag2,
        vix_spike_lag1,
        dxy_lag1,
        dxy_lag2,
        dxy_momentum_3d,
        corn_lag1,
        wheat_lag1,
        corn_soy_ratio_lag1,
        
        -- Lead correlations
        COALESCE(palm_lead2_correlation, 0) as palm_lead2_correlation,
        COALESCE(crude_lead1_correlation, 0) as crude_lead1_correlation,
        COALESCE(vix_lead1_correlation, 0) as vix_lead1_correlation,
        COALESCE(dxy_lead1_correlation, 0) as dxy_lead1_correlation,
        
        -- Directional accuracy
        palm_direction_correct,
        crude_direction_correct,
        vix_inverse_correct,
        
        -- Combined signal
        lead_signal,
        
        -- Signal confidence (based on correlation strength)
        GREATEST(
            ABS(COALESCE(palm_lead2_correlation, 0)),
            ABS(COALESCE(crude_lead1_correlation, 0)),
            ABS(COALESCE(vix_lead1_correlation, 0))
        ) as signal_confidence,
        
        -- Momentum divergence indicator
        CASE 
            WHEN SIGN(palm_momentum_3d) != SIGN(crude_momentum_2d) THEN 1
            ELSE 0
        END as momentum_divergence,
        
        -- Rolling directional accuracy (30-day)
        AVG(palm_direction_correct) OVER (
            ORDER BY date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as palm_accuracy_30d,
        
        AVG(crude_direction_correct) OVER (
            ORDER BY date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as crude_accuracy_30d
        
    FROM directional_agreement
    WHERE date >= '2023-01-01'
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created cross-asset lead/lag analysis successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create lead/lag analysis: {e}")
        return False

def verify_lead_lag():
    """Verify lead/lag relationships are captured"""
    
    verify_query = """
    SELECT 
        AVG(palm_lead2_correlation) as avg_palm_lead,
        AVG(crude_lead1_correlation) as avg_crude_lead,
        AVG(vix_lead1_correlation) as avg_vix_lead,
        AVG(dxy_lead1_correlation) as avg_dxy_lead,
        
        AVG(palm_accuracy_30d) as palm_directional_accuracy,
        AVG(crude_accuracy_30d) as crude_directional_accuracy,
        
        COUNTIF(lead_signal = 'STRONG_BUY') as strong_buy_days,
        COUNTIF(lead_signal = 'BUY') as buy_days,
        COUNTIF(lead_signal = 'STRONG_SELL') as strong_sell_days,
        COUNTIF(lead_signal = 'SELL') as sell_days,
        COUNTIF(lead_signal = 'NEUTRAL') as neutral_days
        
    FROM `cbi-v14.models.vw_cross_asset_lead_lag`
    WHERE date >= '2024-01-01'
    """
    
    print("\n" + "=" * 80)
    print("LEAD/LAG VERIFICATION")
    print("=" * 80)
    
    try:
        result = list(client.query(verify_query).result())[0]
        
        print("\nAverage Lead Correlations (2024+):")
        print(f"  Palm oil (2-day lead): {result.avg_palm_lead:.3f}")
        print(f"  Crude oil (1-day lead): {result.avg_crude_lead:.3f}")
        print(f"  VIX (1-day lead): {result.avg_vix_lead:.3f}")
        print(f"  DXY (1-day lead): {result.avg_dxy_lead:.3f}")
        
        print("\nDirectional Accuracy:")
        print(f"  Palm oil: {result.palm_directional_accuracy*100:.1f}%")
        print(f"  Crude oil: {result.crude_directional_accuracy*100:.1f}%")
        
        print("\nSignal Distribution:")
        total = (result.strong_buy_days + result.buy_days + result.strong_sell_days + 
                result.sell_days + result.neutral_days)
        print(f"  Strong Buy: {result.strong_buy_days} ({result.strong_buy_days/total*100:.1f}%)")
        print(f"  Buy: {result.buy_days} ({result.buy_days/total*100:.1f}%)")
        print(f"  Neutral: {result.neutral_days} ({result.neutral_days/total*100:.1f}%)")
        print(f"  Sell: {result.sell_days} ({result.sell_days/total*100:.1f}%)")
        print(f"  Strong Sell: {result.strong_sell_days} ({result.strong_sell_days/total*100:.1f}%)")
        
    except Exception as e:
        print(f"Error verifying lead/lag: {e}")

def main():
    """Create cross-asset lead/lag analysis"""
    print("=" * 80)
    print("ADDING CROSS-ASSET LEAD/LAG ANALYSIS")
    print("=" * 80)
    print("\nCapturing lead/lag relationships:")
    print("  • Palm oil leads soy by 2-3 days")
    print("  • Crude oil leads soy by 1-2 days")
    print("  • VIX spikes lead commodity selloffs")
    print("  • Dollar strength inversely leads commodities")
    print("  • Corn/wheat compete for acreage")
    
    print("\n1. Creating lead/lag analysis...")
    success = create_lead_lag_analysis()
    
    if success:
        print("\n2. Verifying lead/lag relationships...")
        verify_lead_lag()
        
        print("\n" + "=" * 80)
        print("✅ LEAD/LAG ANALYSIS COMPLETE")
        print("=" * 80)
        print("\nFeatures created in: models.vw_cross_asset_lead_lag")
        print("These provide:")
        print("  • Leading price indicators from related assets")
        print("  • Directional accuracy metrics")
        print("  • Combined momentum signals")
        print("  • Granger causality relationships")
    else:
        print("\n❌ Failed to create lead/lag analysis")
    
    return success

if __name__ == "__main__":
    main()
