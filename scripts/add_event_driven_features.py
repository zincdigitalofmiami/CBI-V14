#!/usr/bin/env python3
"""
Add Event-Driven Features
USDA reports, Fed meetings, Chinese holidays - massive volatility events
"""

from google.cloud import bigquery
import logging
from datetime import datetime, date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def create_event_calendar():
    """
    Create event calendar with major market-moving events
    USDA WASDE reports, FOMC meetings, Chinese holidays affect prices
    """
    
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_event_driven_features` AS
    WITH usda_wasde_dates AS (
        -- USDA WASDE reports (typically around 10th of each month, 12pm ET)
        -- These cause MASSIVE volatility
        SELECT date,
               'USDA_WASDE' as event_type,
               3 as impact_level,  -- Highest impact
               'Supply/demand estimates' as description
        FROM UNNEST([
            DATE('2024-01-12'), DATE('2024-02-08'), DATE('2024-03-08'),
            DATE('2024-04-11'), DATE('2024-05-10'), DATE('2024-06-12'),
            DATE('2024-07-12'), DATE('2024-08-12'), DATE('2024-09-12'),
            DATE('2024-10-11'), DATE('2024-11-08'), DATE('2024-12-10'),
            DATE('2025-01-10'), DATE('2025-02-11'), DATE('2025-03-11'),
            DATE('2025-04-09'), DATE('2025-05-09'), DATE('2025-06-11'),
            DATE('2025-07-11'), DATE('2025-08-12'), DATE('2025-09-12'),
            DATE('2025-10-10'), DATE('2025-11-10'), DATE('2025-12-10')
        ]) as date
    ),
    fomc_meetings AS (
        -- Federal Reserve FOMC meetings (affect dollar and commodities)
        SELECT date,
               'FOMC_MEETING' as event_type,
               2 as impact_level,  -- High impact
               'Fed policy decision' as description
        FROM UNNEST([
            DATE('2024-01-31'), DATE('2024-03-20'), DATE('2024-05-01'),
            DATE('2024-06-12'), DATE('2024-07-31'), DATE('2024-09-18'),
            DATE('2024-11-07'), DATE('2024-12-18'),
            DATE('2025-01-29'), DATE('2025-03-19'), DATE('2025-04-30'),
            DATE('2025-06-18'), DATE('2025-07-30'), DATE('2025-09-17'),
            DATE('2025-11-05'), DATE('2025-12-17')
        ]) as date
    ),
    chinese_holidays AS (
        -- Chinese holidays (affect demand patterns)
        SELECT date,
               event_type,
               2 as impact_level,
               description
        FROM UNNEST([
            STRUCT(DATE('2024-02-10') as date, 'CHINESE_NEW_YEAR' as event_type, 'Demand spike pre-holiday' as description),
            STRUCT(DATE('2024-09-17'), 'MID_AUTUMN_FESTIVAL', 'Increased consumption'),
            STRUCT(DATE('2024-10-01'), 'GOLDEN_WEEK', 'Markets closed, pent-up demand'),
            STRUCT(DATE('2025-01-29'), 'CHINESE_NEW_YEAR', 'Demand spike pre-holiday'),
            STRUCT(DATE('2025-09-06'), 'MID_AUTUMN_FESTIVAL', 'Increased consumption'),
            STRUCT(DATE('2025-10-01'), 'GOLDEN_WEEK', 'Markets closed, pent-up demand')
        ])
    ),
    usda_crop_reports AS (
        -- USDA Crop Progress reports (weekly during growing season)
        SELECT date,
               'CROP_PROGRESS' as event_type,
               1 as impact_level,  -- Medium impact
               'Weekly crop conditions' as description
        FROM UNNEST(GENERATE_DATE_ARRAY('2024-04-01', '2024-11-30', INTERVAL 7 DAY)) as date
        WHERE EXTRACT(DAYOFWEEK FROM date) = 2  -- Mondays
        
        UNION ALL
        
        SELECT date,
               'CROP_PROGRESS' as event_type,
               1 as impact_level,
               'Weekly crop conditions' as description
        FROM UNNEST(GENERATE_DATE_ARRAY('2025-04-01', '2025-11-30', INTERVAL 7 DAY)) as date
        WHERE EXTRACT(DAYOFWEEK FROM date) = 2  -- Mondays
    ),
    quarterly_stocks AS (
        -- Quarterly Grain Stocks reports (major market movers)
        SELECT date,
               'GRAIN_STOCKS' as event_type,
               3 as impact_level,
               'Quarterly inventory' as description
        FROM UNNEST([
            DATE('2024-03-28'), DATE('2024-06-28'), DATE('2024-09-30'), DATE('2024-12-10'),
            DATE('2025-03-31'), DATE('2025-06-30'), DATE('2025-09-30'), DATE('2025-12-10')
        ]) as date
    ),
    planting_intentions AS (
        -- Planting Intentions and Acreage reports
        SELECT date,
               'PLANTING_INTENTIONS' as event_type,
               3 as impact_level,
               'Acreage intentions' as description
        FROM UNNEST([
            DATE('2024-03-28'), DATE('2024-06-28'),
            DATE('2025-03-31'), DATE('2025-06-30')
        ]) as date
    ),
    all_events AS (
        SELECT * FROM usda_wasde_dates
        UNION ALL SELECT * FROM fomc_meetings
        UNION ALL SELECT * FROM chinese_holidays
        UNION ALL SELECT * FROM usda_crop_reports
        UNION ALL SELECT * FROM quarterly_stocks
        UNION ALL SELECT * FROM planting_intentions
    ),
    dates_with_events AS (
        -- Create a complete date series with event flags
        SELECT 
            d.date,
            
            -- Event flags
            COALESCE(MAX(CASE WHEN e.event_type = 'USDA_WASDE' THEN 1 ELSE 0 END), 0) as is_wasde_day,
            COALESCE(MAX(CASE WHEN e.event_type = 'FOMC_MEETING' THEN 1 ELSE 0 END), 0) as is_fomc_day,
            COALESCE(MAX(CASE WHEN e.event_type LIKE 'CHINESE%' OR e.event_type = 'GOLDEN_WEEK' THEN 1 ELSE 0 END), 0) as is_china_holiday,
            COALESCE(MAX(CASE WHEN e.event_type = 'CROP_PROGRESS' THEN 1 ELSE 0 END), 0) as is_crop_report_day,
            COALESCE(MAX(CASE WHEN e.event_type = 'GRAIN_STOCKS' THEN 1 ELSE 0 END), 0) as is_stocks_day,
            COALESCE(MAX(CASE WHEN e.event_type = 'PLANTING_INTENTIONS' THEN 1 ELSE 0 END), 0) as is_planting_day,
            
            -- Impact level
            COALESCE(MAX(e.impact_level), 0) as event_impact_level,
            
            -- Event description
            STRING_AGG(e.event_type, ', ') as events_today,
            
            -- Days to/from major events
            DATE_DIFF(
                (SELECT MIN(date) FROM all_events WHERE date > d.date AND impact_level = 3),
                d.date,
                DAY
            ) as days_to_next_major_event,
            
            DATE_DIFF(
                d.date,
                (SELECT MAX(date) FROM all_events WHERE date < d.date AND impact_level = 3),
                DAY
            ) as days_since_last_major_event
            
        FROM (
            SELECT DISTINCT DATE(time) as date
            FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
            WHERE DATE(time) >= '2020-01-01'
        ) d
        LEFT JOIN all_events e ON d.date = e.date
        GROUP BY d.date
    )
    SELECT 
        date,
        
        -- Event flags
        is_wasde_day,
        is_fomc_day,
        is_china_holiday,
        is_crop_report_day,
        is_stocks_day,
        is_planting_day,
        
        -- Combined event indicator
        CASE 
            WHEN is_wasde_day = 1 OR is_stocks_day = 1 OR is_planting_day = 1 THEN 1
            ELSE 0
        END as is_major_usda_day,
        
        -- Event impact
        event_impact_level,
        COALESCE(events_today, 'NONE') as events_today,
        
        -- Event proximity features
        COALESCE(days_to_next_major_event, 999) as days_to_next_major_event,
        COALESCE(days_since_last_major_event, 999) as days_since_last_major_event,
        
        -- Pre-event positioning (markets position ahead of reports)
        CASE 
            WHEN days_to_next_major_event BETWEEN 1 AND 3 THEN 1
            ELSE 0
        END as pre_event_window,
        
        -- Post-event adjustment (markets digest the news)
        CASE 
            WHEN days_since_last_major_event BETWEEN 1 AND 2 THEN 1
            ELSE 0
        END as post_event_window,
        
        -- Volatility multiplier based on events
        CASE 
            WHEN is_wasde_day = 1 THEN 2.5  -- WASDE days see 2.5x normal volatility
            WHEN is_stocks_day = 1 THEN 2.0
            WHEN is_planting_day = 1 THEN 2.0
            WHEN is_fomc_day = 1 THEN 1.5
            WHEN is_china_holiday = 1 THEN 1.3
            WHEN days_to_next_major_event BETWEEN 1 AND 3 THEN 1.2
            ELSE 1.0
        END as expected_volatility_multiplier,
        
        -- Trading behavior changes
        CASE 
            WHEN is_wasde_day = 1 OR is_stocks_day = 1 THEN 'HIGH_VOL_BREAKOUT'
            WHEN days_to_next_major_event BETWEEN 1 AND 3 THEN 'POSITIONING'
            WHEN days_since_last_major_event BETWEEN 1 AND 2 THEN 'ADJUSTMENT'
            WHEN is_china_holiday = 1 THEN 'REDUCED_LIQUIDITY'
            ELSE 'NORMAL'
        END as market_regime,
        
        -- Options expiry (monthly, third Friday)
        CASE 
            WHEN EXTRACT(DAYOFWEEK FROM date) = 6  -- Friday
             AND EXTRACT(DAY FROM date) BETWEEN 15 AND 21  -- Third week
            THEN 1 ELSE 0
        END as is_options_expiry,
        
        -- Quarter end effects
        CASE 
            WHEN EXTRACT(MONTH FROM date) IN (3, 6, 9, 12)
             AND EXTRACT(DAY FROM date) >= 25
            THEN 1 ELSE 0
        END as is_quarter_end,
        
        -- Month end effects
        CASE 
            WHEN EXTRACT(DAY FROM date) >= 25
            THEN 1 ELSE 0
        END as is_month_end
        
    FROM dates_with_events
    ORDER BY date DESC
    """
    
    try:
        client.query(query).result()
        logger.info("✅ Created event-driven features successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create event features: {e}")
        return False

def verify_events():
    """Verify event calendar is working"""
    
    verify_query = """
    SELECT 
        COUNTIF(is_wasde_day = 1) as wasde_days,
        COUNTIF(is_fomc_day = 1) as fomc_days,
        COUNTIF(is_china_holiday = 1) as china_holidays,
        COUNTIF(is_major_usda_day = 1) as major_usda_days,
        COUNTIF(pre_event_window = 1) as pre_event_days,
        COUNTIF(post_event_window = 1) as post_event_days,
        AVG(expected_volatility_multiplier) as avg_vol_multiplier,
        MAX(expected_volatility_multiplier) as max_vol_multiplier
    FROM `cbi-v14.models.vw_event_driven_features`
    WHERE date >= '2024-01-01'
    """
    
    print("\n" + "=" * 80)
    print("EVENT CALENDAR VERIFICATION")
    print("=" * 80)
    
    try:
        result = list(client.query(verify_query).result())[0]
        
        print("\nEvent Counts (2024+):")
        print(f"  WASDE reports: {result.wasde_days}")
        print(f"  FOMC meetings: {result.fomc_days}")
        print(f"  Chinese holidays: {result.china_holidays}")
        print(f"  Major USDA days: {result.major_usda_days}")
        print(f"  Pre-event positioning days: {result.pre_event_days}")
        print(f"  Post-event adjustment days: {result.post_event_days}")
        
        print(f"\nVolatility Impact:")
        print(f"  Average multiplier: {result.avg_vol_multiplier:.2f}x")
        print(f"  Maximum multiplier: {result.max_vol_multiplier:.1f}x (WASDE days)")
        
        # Check recent events
        recent_query = """
        SELECT 
            date,
            events_today,
            expected_volatility_multiplier,
            market_regime
        FROM `cbi-v14.models.vw_event_driven_features`
        WHERE event_impact_level > 0
        AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        ORDER BY date DESC
        LIMIT 5
        """
        
        print(f"\nRecent Major Events:")
        recent_result = client.query(recent_query).result()
        for row in recent_result:
            print(f"  {row.date}: {row.events_today} - {row.expected_volatility_multiplier:.1f}x vol ({row.market_regime})")
            
    except Exception as e:
        print(f"Error verifying events: {e}")

def main():
    """Create event-driven features"""
    print("=" * 80)
    print("ADDING EVENT-DRIVEN FEATURES")
    print("=" * 80)
    print("\nCapturing market-moving events:")
    print("  • USDA WASDE reports (2.5x volatility)")
    print("  • Grain Stocks reports (2.0x volatility)")
    print("  • FOMC meetings (1.5x volatility)")
    print("  • Chinese holidays (demand shifts)")
    print("  • Crop progress reports")
    print("  • Options expiry effects")
    
    print("\n1. Creating event calendar...")
    success = create_event_calendar()
    
    if success:
        print("\n2. Verifying event features...")
        verify_events()
        
        print("\n" + "=" * 80)
        print("✅ EVENT-DRIVEN FEATURES COMPLETE")
        print("=" * 80)
        print("\nFeatures created in: models.vw_event_driven_features")
        print("These capture:")
        print("  • Major report days with volatility multipliers")
        print("  • Pre/post event positioning windows")
        print("  • Market regime changes around events")
        print("  • Quarter-end and month-end effects")
    else:
        print("\n❌ Failed to create event features")
    
    return success

if __name__ == "__main__":
    main()
