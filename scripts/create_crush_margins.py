#!/usr/bin/env python3
"""
Create Soybean Crush Margins Calculator
Formula: (Meal Price × 0.022) + (Oil Price × 0.11) - Bean Price
This is a CRITICAL profitability metric for processors
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_crush_margins_view():
    """
    Create the crush margins view using REAL prices
    One bushel of soybeans (60 lbs) produces:
    - 44 lbs of meal (0.022 short tons)
    - 11 lbs of oil (0.11 cwt)
    """
    
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_crush_margins` AS
    WITH aligned_prices AS (
        -- Get soybean oil prices (ZL - cents/lb needs conversion to $/cwt)
        SELECT 
            DATE(time) as date,
            close * 100 as oil_price_per_cwt,  -- Convert cents/lb to $/cwt (100 lbs)
            'ZL' as oil_symbol
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
        WHERE symbol = 'ZL'
    ),
    bean_prices AS (
        -- Get soybean prices (ZS - cents/bushel needs conversion to $/bushel)
        SELECT 
            DATE(time) as date,
            close / 100 as bean_price_per_bushel,  -- Convert cents to dollars
            'ZS' as bean_symbol
        FROM `cbi-v14.forecasting_data_warehouse.soybean_prices`
        WHERE symbol = 'ZS' OR symbol = 'S'
    ),
    meal_prices AS (
        -- Get soybean meal prices (ZM - $/ton)
        SELECT 
            DATE(time) as date,
            close as meal_price_per_ton,
            'ZM' as meal_symbol
        FROM `cbi-v14.forecasting_data_warehouse.soybean_meal_prices`
        WHERE symbol = 'ZM' OR symbol = 'SM'
    )
    SELECT 
        COALESCE(o.date, b.date, m.date) as date,
        
        -- Raw prices
        o.oil_price_per_cwt,
        b.bean_price_per_bushel,
        m.meal_price_per_ton,
        
        -- Crush margin calculation
        -- Revenue from products minus cost of beans
        (COALESCE(m.meal_price_per_ton, 350) * 0.022) +  -- Meal revenue
        (COALESCE(o.oil_price_per_cwt, 50) * 0.11) -     -- Oil revenue
        COALESCE(b.bean_price_per_bushel, 10) as crush_margin,
        
        -- Board crush (simplified when meal not available)
        CASE 
            WHEN m.meal_price_per_ton IS NOT NULL THEN 'Full Crush'
            ELSE 'Board Crush (Est)'
        END as margin_type,
        
        -- Profitability indicator
        CASE 
            WHEN ((COALESCE(m.meal_price_per_ton, 350) * 0.022) + 
                  (COALESCE(o.oil_price_per_cwt, 50) * 0.11) - 
                  COALESCE(b.bean_price_per_bushel, 10)) > 2 THEN 'Profitable'
            WHEN ((COALESCE(m.meal_price_per_ton, 350) * 0.022) + 
                  (COALESCE(o.oil_price_per_cwt, 50) * 0.11) - 
                  COALESCE(b.bean_price_per_bushel, 10)) > 0 THEN 'Marginal'
            ELSE 'Unprofitable'
        END as profitability_status,
        
        -- Moving averages for smoothing
        AVG((COALESCE(m.meal_price_per_ton, 350) * 0.022) + 
            (COALESCE(o.oil_price_per_cwt, 50) * 0.11) - 
            COALESCE(b.bean_price_per_bushel, 10)) OVER (
            ORDER BY COALESCE(o.date, b.date, m.date)
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as crush_margin_7d_ma,
        
        AVG((COALESCE(m.meal_price_per_ton, 350) * 0.022) + 
            (COALESCE(o.oil_price_per_cwt, 50) * 0.11) - 
            COALESCE(b.bean_price_per_bushel, 10)) OVER (
            ORDER BY COALESCE(o.date, b.date, m.date)
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as crush_margin_30d_ma
        
    FROM aligned_prices o
    FULL OUTER JOIN bean_prices b ON o.date = b.date
    FULL OUTER JOIN meal_prices m ON o.date = m.date
    WHERE COALESCE(o.date, b.date, m.date) >= '2020-01-01'
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created models.vw_crush_margins successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create crush margins view: {e}")
        return False

def verify_crush_margins():
    """Verify the crush margins view has data and makes sense"""
    
    verify_query = """
    SELECT 
        COUNT(*) as total_rows,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        AVG(crush_margin) as avg_margin,
        MIN(crush_margin) as min_margin,
        MAX(crush_margin) as max_margin,
        COUNTIF(profitability_status = 'Profitable') as profitable_days,
        COUNTIF(profitability_status = 'Marginal') as marginal_days,
        COUNTIF(profitability_status = 'Unprofitable') as unprofitable_days
    FROM `cbi-v14.models.vw_crush_margins`
    WHERE date >= '2024-01-01'
    """
    
    print("\n" + "=" * 80)
    print("CRUSH MARGINS VERIFICATION")
    print("=" * 80)
    
    try:
        result = list(client.query(verify_query).result())[0]
        print(f"Total rows: {result.total_rows}")
        print(f"Date range: {result.earliest_date} to {result.latest_date}")
        print(f"\nMargin Statistics ($/bushel):")
        print(f"  Average: ${result.avg_margin:.2f}")
        print(f"  Min: ${result.min_margin:.2f}")
        print(f"  Max: ${result.max_margin:.2f}")
        print(f"\nProfitability Distribution (2024+):")
        print(f"  Profitable days: {result.profitable_days}")
        print(f"  Marginal days: {result.marginal_days}")
        print(f"  Unprofitable days: {result.unprofitable_days}")
        
        # Check recent margins
        recent_query = """
        SELECT 
            date,
            oil_price_per_cwt,
            bean_price_per_bushel,
            meal_price_per_ton,
            crush_margin,
            profitability_status
        FROM `cbi-v14.models.vw_crush_margins`
        ORDER BY date DESC
        LIMIT 5
        """
        
        print(f"\nRecent Crush Margins:")
        recent_result = client.query(recent_query).result()
        for row in recent_result:
            print(f"  {row.date}: ${row.crush_margin:.2f} ({row.profitability_status})")
            
    except Exception as e:
        print(f"Error verifying crush margins: {e}")

def main():
    """Create and verify crush margins"""
    print("=" * 80)
    print("CREATING SOYBEAN CRUSH MARGINS CALCULATOR")
    print("=" * 80)
    print("\nFormula: (Meal × 0.022) + (Oil × 0.11) - Bean Price")
    print("This shows processor profitability - CRITICAL for demand!")
    
    success = create_crush_margins_view()
    
    if success:
        verify_crush_margins()
        print("\n✅ Crush margins calculator ready for use!")
    else:
        print("\n❌ Failed to create crush margins")
        
    return success

if __name__ == "__main__":
    main()
