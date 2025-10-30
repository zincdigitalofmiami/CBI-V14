#!/usr/bin/env python3
"""
Add Seasonality Decomposition for Soybean Oil
Critical for capturing harvest/planting cycles
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_seasonality_features():
    """
    Create seasonality features capturing agricultural cycles
    Soybean oil has STRONG seasonal patterns we must capture
    """
    
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_seasonality_features` AS
    WITH price_data AS (
        SELECT 
            DATE(time) as date,
            close as price,
            EXTRACT(YEAR FROM time) as year,
            EXTRACT(MONTH FROM time) as month,
            EXTRACT(QUARTER FROM time) as quarter,
            EXTRACT(WEEK FROM time) as week_of_year,
            EXTRACT(DAYOFWEEK FROM time) as day_of_week
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
        WHERE symbol = 'ZL'
    ),
    seasonal_averages AS (
        -- Calculate historical seasonal patterns
        SELECT 
            month,
            AVG(price) as avg_monthly_price,
            STDDEV(price) as stddev_monthly_price,
            COUNT(*) as observations
        FROM price_data
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 YEAR)
        GROUP BY month
    ),
    quarterly_patterns AS (
        SELECT 
            quarter,
            AVG(price) as avg_quarterly_price,
            STDDEV(price) as stddev_quarterly_price
        FROM price_data
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 YEAR)
        GROUP BY quarter
    ),
    harvest_calendar AS (
        -- Define critical agricultural periods
        SELECT 
            date,
            CASE 
                -- U.S. Harvest (September-November)
                WHEN EXTRACT(MONTH FROM date) IN (9, 10, 11) THEN 'US_HARVEST'
                -- Brazil Harvest (January-March)
                WHEN EXTRACT(MONTH FROM date) IN (1, 2, 3) THEN 'BRAZIL_HARVEST'
                -- Argentina Harvest (March-May)
                WHEN EXTRACT(MONTH FROM date) IN (3, 4, 5) THEN 'ARGENTINA_HARVEST'
                -- U.S. Planting (April-June)
                WHEN EXTRACT(MONTH FROM date) IN (4, 5, 6) THEN 'US_PLANTING'
                -- Brazil Planting (September-November)
                WHEN EXTRACT(MONTH FROM date) IN (9, 10, 11) THEN 'BRAZIL_PLANTING'
                -- Growing Season (June-August)
                WHEN EXTRACT(MONTH FROM date) IN (6, 7, 8) THEN 'GROWING_SEASON'
                ELSE 'NEUTRAL'
            END as agricultural_phase,
            
            -- Harvest pressure indicator
            CASE 
                WHEN EXTRACT(MONTH FROM date) IN (9, 10, 11, 1, 2, 3, 4, 5) THEN 1
                ELSE 0
            END as harvest_pressure,
            
            -- Chinese demand cycles
            CASE 
                -- Chinese New Year (Jan/Feb) - demand spike
                WHEN EXTRACT(MONTH FROM date) IN (1, 2) THEN 1.2
                -- Mid-Autumn Festival (Sep/Oct) - demand spike
                WHEN EXTRACT(MONTH FROM date) IN (9, 10) THEN 1.1
                -- Normal demand
                ELSE 1.0
            END as china_demand_multiplier,
            
            -- Northern vs Southern hemisphere
            CASE 
                WHEN EXTRACT(MONTH FROM date) IN (9, 10, 11, 12, 1, 2, 3) THEN 'SOUTHERN_DOMINANT'
                ELSE 'NORTHERN_DOMINANT'
            END as hemisphere_dominance
            
        FROM (
            SELECT DISTINCT DATE(time) as date
            FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
        )
    ),
    year_over_year AS (
        -- Year-over-year comparisons
        SELECT 
            p1.date,
            p1.price as current_price,
            p2.price as price_1y_ago,
            (p1.price - p2.price) / NULLIF(p2.price, 0) as yoy_change,
            p3.price as price_2y_ago,
            (p1.price - p3.price) / NULLIF(p3.price, 0) as two_year_change
        FROM price_data p1
        LEFT JOIN price_data p2 
            ON p1.month = p2.month 
            AND p1.year = p2.year + 1
        LEFT JOIN price_data p3 
            ON p1.month = p3.month 
            AND p1.year = p3.year + 2
    ),
    seasonal_decomposition AS (
        SELECT 
            p.date,
            p.price,
            p.month,
            p.quarter,
            p.week_of_year,
            p.day_of_week,
            
            -- Seasonal index (price relative to monthly average)
            p.price / NULLIF(s.avg_monthly_price, 0) as seasonal_index,
            
            -- Z-score within month
            (p.price - s.avg_monthly_price) / NULLIF(s.stddev_monthly_price, 0) as monthly_zscore,
            
            -- Quarterly patterns
            p.price / NULLIF(q.avg_quarterly_price, 0) as quarterly_index,
            
            -- Deseasonalized price
            p.price - (s.avg_monthly_price - AVG(s.avg_monthly_price) OVER ()) as deseasonalized_price,
            
            -- Seasonal strength indicator
            s.stddev_monthly_price / NULLIF(s.avg_monthly_price, 0) as seasonal_volatility,
            
            -- Month-to-month seasonal change
            LAG(s.avg_monthly_price, 1) OVER (ORDER BY p.date) as prev_month_seasonal,
            (s.avg_monthly_price - LAG(s.avg_monthly_price, 1) OVER (ORDER BY p.date)) / 
                NULLIF(LAG(s.avg_monthly_price, 1) OVER (ORDER BY p.date), 0) as seasonal_momentum
            
        FROM price_data p
        LEFT JOIN seasonal_averages s ON p.month = s.month
        LEFT JOIN quarterly_patterns q ON p.quarter = q.quarter
    )
    SELECT 
        sd.date,
        sd.month,
        sd.quarter,
        sd.week_of_year,
        sd.day_of_week,
        
        -- Core seasonal features
        COALESCE(sd.seasonal_index, 1.0) as seasonal_index,
        COALESCE(sd.monthly_zscore, 0.0) as monthly_zscore,
        COALESCE(sd.quarterly_index, 1.0) as quarterly_index,
        COALESCE(sd.deseasonalized_price, sd.price) as deseasonalized_price,
        COALESCE(sd.seasonal_volatility, 0.1) as seasonal_volatility,
        COALESCE(sd.seasonal_momentum, 0.0) as seasonal_momentum,
        
        -- Agricultural calendar
        hc.agricultural_phase,
        hc.harvest_pressure,
        hc.china_demand_multiplier,
        hc.hemisphere_dominance,
        
        -- Year-over-year
        COALESCE(yoy.yoy_change, 0.0) as yoy_change,
        COALESCE(yoy.two_year_change, 0.0) as two_year_change,
        
        -- Seasonal flags
        CASE WHEN sd.month IN (9, 10, 11) THEN 1 ELSE 0 END as us_harvest_season,
        CASE WHEN sd.month IN (1, 2, 3) THEN 1 ELSE 0 END as brazil_harvest_season,
        CASE WHEN sd.month IN (4, 5, 6) THEN 1 ELSE 0 END as planting_season,
        CASE WHEN sd.month IN (6, 7, 8) THEN 1 ELSE 0 END as growing_season,
        CASE WHEN sd.month IN (12, 1, 2) THEN 1 ELSE 0 END as winter_season,
        
        -- Trading patterns
        CASE WHEN sd.day_of_week IN (2, 3, 4) THEN 1 ELSE 0 END as mid_week,
        CASE WHEN sd.day_of_week = 6 THEN 1 ELSE 0 END as friday_effect,
        CASE WHEN sd.day_of_week = 2 THEN 1 ELSE 0 END as monday_effect,
        
        -- Quarterly transitions
        CASE 
            WHEN sd.month IN (3, 6, 9, 12) THEN 1 
            ELSE 0 
        END as quarter_end,
        
        CASE 
            WHEN sd.month IN (1, 4, 7, 10) THEN 1 
            ELSE 0 
        END as quarter_start
        
    FROM seasonal_decomposition sd
    LEFT JOIN harvest_calendar hc ON sd.date = hc.date
    LEFT JOIN year_over_year yoy ON sd.date = yoy.date
    WHERE sd.date >= '2020-01-01'
    ORDER BY sd.date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created seasonality features successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create seasonality features: {e}")
        return False

def verify_seasonality():
    """Verify seasonality patterns are captured correctly"""
    
    verify_query = """
    WITH monthly_patterns AS (
        SELECT 
            month,
            AVG(seasonal_index) as avg_seasonal_index,
            COUNT(*) as observations
        FROM `cbi-v14.models.vw_seasonality_features`
        GROUP BY month
        ORDER BY month
    ),
    phase_analysis AS (
        SELECT 
            agricultural_phase,
            COUNT(*) as days,
            AVG(seasonal_index) as avg_index
        FROM `cbi-v14.models.vw_seasonality_features`
        WHERE date >= '2024-01-01'
        GROUP BY agricultural_phase
    )
    SELECT * FROM monthly_patterns
    """
    
    print("\n" + "=" * 80)
    print("SEASONALITY VERIFICATION")
    print("=" * 80)
    
    try:
        print("\nMonthly Seasonal Patterns:")
        result = client.query(verify_query).result()
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for row in result:
            month_name = months[row.month - 1] if row.month <= 12 else f"Month {row.month}"
            bar = '█' * int(row.avg_seasonal_index * 20)
            print(f"  {month_name:3}: {bar} {row.avg_seasonal_index:.3f}")
        
        # Check agricultural phases
        phase_query = """
        SELECT 
            agricultural_phase,
            COUNT(*) as days,
            AVG(seasonal_index) as avg_index,
            AVG(harvest_pressure) as avg_pressure
        FROM `cbi-v14.models.vw_seasonality_features`
        WHERE date >= '2024-01-01'
        GROUP BY agricultural_phase
        ORDER BY avg_index DESC
        """
        
        print("\nAgricultural Phases (2024+):")
        result2 = client.query(phase_query).result()
        for row in result2:
            print(f"  {row.agricultural_phase:20}: {row.days:3} days, Index: {row.avg_index:.3f}, Pressure: {row.avg_pressure:.2f}")
        
        # Check YoY patterns
        yoy_query = """
        SELECT 
            EXTRACT(YEAR FROM date) as year,
            AVG(yoy_change) as avg_yoy_change,
            MIN(yoy_change) as min_yoy,
            MAX(yoy_change) as max_yoy
        FROM `cbi-v14.models.vw_seasonality_features`
        WHERE yoy_change IS NOT NULL
        GROUP BY year
        ORDER BY year DESC
        LIMIT 3
        """
        
        print("\nYear-over-Year Changes:")
        result3 = client.query(yoy_query).result()
        for row in result3:
            print(f"  {row.year}: Avg: {row.avg_yoy_change*100:.1f}%, Range: {row.min_yoy*100:.1f}% to {row.max_yoy*100:.1f}%")
            
    except Exception as e:
        print(f"Error verifying seasonality: {e}")

def main():
    """Create seasonality decomposition features"""
    print("=" * 80)
    print("ADDING SEASONALITY DECOMPOSITION")
    print("=" * 80)
    print("\nCapturing critical seasonal patterns:")
    print("  • U.S. Harvest (Sep-Nov) - Price pressure")
    print("  • Brazil Harvest (Jan-Mar) - Southern supply")
    print("  • Argentina Harvest (Mar-May) - Extended pressure")
    print("  • Planting Season (Apr-Jun) - Weather premium")
    print("  • Chinese New Year (Jan-Feb) - Demand spike")
    print("  • Growing Season (Jun-Aug) - Weather markets")
    
    print("\n1. Creating seasonality features...")
    success = create_seasonality_features()
    
    if success:
        print("\n2. Verifying seasonal patterns...")
        verify_seasonality()
        
        print("\n" + "=" * 80)
        print("✅ SEASONALITY DECOMPOSITION COMPLETE")
        print("=" * 80)
        print("\nFeatures created in: models.vw_seasonality_features")
        print("These capture:")
        print("  • Monthly seasonal indices")
        print("  • Agricultural phase indicators")
        print("  • Harvest pressure signals")
        print("  • Year-over-year comparisons")
        print("  • China demand cycles")
        print("  • Hemisphere dominance patterns")
    else:
        print("\n❌ Failed to create seasonality features")
    
    return success

if __name__ == "__main__":
    main()
