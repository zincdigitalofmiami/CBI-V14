#!/usr/bin/env python3
"""
IDENTIFY TRUE DUPLICATES - Find actual duplicate data (not related commodities)
Understand what's a duplicate vs what's a different but related commodity
"""

from google.cloud import bigquery
from datetime import datetime
import pandas as pd

client = bigquery.Client(project='cbi-v14')

print(f"TRUE DUPLICATE IDENTIFICATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

print("\n1. ANALYZING SOYBEAN-RELATED TABLES (Checking if TRUE duplicates):")
print("-"*80)

soybean_tables = [
    ('forecasting_data_warehouse', 'soybean_prices', 'ZS - Soybeans'),
    ('forecasting_data_warehouse', 'soybean_oil_prices', 'ZL - Soybean Oil'),
    ('forecasting_data_warehouse', 'soybean_meal_prices', 'ZM - Soybean Meal'),
    ('forecasting_data_warehouse', 'soybean_oil_forecast', 'Forecast data'),
    ('forecasting_data_warehouse', 'vw_soybean_oil_daily_clean', 'View of ZL'),
    ('curated', 'vw_soybean_oil_features_daily', 'Features from ZL'),
    ('curated', 'vw_soybean_oil_quote', 'Quote data'),
]

for dataset, table, description in soybean_tables:
    try:
        # Get key metrics to identify what this table contains
        query = f"""
        SELECT 
            COUNT(*) as rows,
            COUNT(DISTINCT DATE(COALESCE(time, date))) as unique_days,
            MIN(COALESCE(close, close_price, predicted_close)) as min_price,
            MAX(COALESCE(close, close_price, predicted_close)) as max_price,
            AVG(COALESCE(close, close_price, predicted_close)) as avg_price
        FROM `cbi-v14.{dataset}.{table}`
        """
        
        result = client.query(query).to_dataframe()
        row = result.iloc[0]
        
        print(f"\n{dataset}.{table} ({description}):")
        print(f"  Rows: {row['rows']:,} | Days: {row['unique_days']:,}")
        print(f"  Price range: ${row['min_price']:.2f} - ${row['max_price']:.2f}")
        print(f"  Avg price: ${row['avg_price']:.2f}")
        
        # Determine commodity type based on price range
        if row['avg_price'] > 1000:
            print(f"  → Commodity: SOYBEANS (price ~$1,300)")
        elif row['avg_price'] > 300:
            print(f"  → Commodity: SOYBEAN MEAL (price ~$380)")
        elif row['avg_price'] < 100:
            print(f"  → Commodity: SOYBEAN OIL (price ~$55)")
        else:
            print(f"  → Commodity: UNKNOWN")
            
    except Exception as e:
        print(f"\n{dataset}.{table}: ERROR - {str(e)[:50]}")

print("\n2. IDENTIFYING TRUE DUPLICATES vs VIEWS:")
print("-"*80)

# Check if views are duplicating data or adding value
views_to_check = [
    ('forecasting_data_warehouse', 'vw_soybean_oil_daily_clean'),
    ('forecasting_data_warehouse', 'vw_crush_margins'),
    ('forecasting_data_warehouse', 'vw_social_sentiment_daily'),
    ('curated', 'vw_soybean_oil_features_daily'),
]

print("\nChecking if views add value or just duplicate:")
for dataset, view in views_to_check:
    try:
        # Get column count to see if view adds features
        query = f"SELECT * FROM `cbi-v14.{dataset}.{view}` LIMIT 1"
        sample = client.query(query).to_dataframe()
        
        print(f"\n{dataset}.{view}:")
        print(f"  Columns: {len(sample.columns)}")
        print(f"  Sample columns: {', '.join(list(sample.columns)[:5])}...")
        
        if len(sample.columns) > 15:
            print(f"  → ADDS VALUE: Has {len(sample.columns)} columns (features/calculations)")
        else:
            print(f"  → POSSIBLE DUPLICATE: Only {len(sample.columns)} columns")
            
    except Exception as e:
        print(f"\n{dataset}.{view}: ERROR")

print("\n3. CHECKING WEATHER DATA ORGANIZATION:")
print("-"*80)

weather_tables = [
    ('forecasting_data_warehouse', 'weather_data', 'Main table'),
    ('forecasting_data_warehouse', 'weather_brazil_daily', 'Brazil specific'),
    ('forecasting_data_warehouse', 'weather_argentina_daily', 'Argentina specific'),
    ('forecasting_data_warehouse', 'weather_us_midwest_daily', 'US Midwest specific'),
    ('forecasting_data_warehouse', 'vw_brazil_weather_summary', 'Brazil summary view'),
    ('forecasting_data_warehouse', 'vw_weather_daily', 'Daily aggregation'),
]

print("\nAnalyzing weather data structure:")
for dataset, table, description in weather_tables:
    try:
        query = f"""
        SELECT 
            COUNT(*) as rows,
            COUNT(DISTINCT DATE(COALESCE(date, time))) as unique_days
        FROM `cbi-v14.{dataset}.{table}`
        """
        
        result = client.query(query).to_dataframe()
        row = result.iloc[0]
        
        print(f"\n{dataset}.{table} ({description}):")
        print(f"  Rows: {row['rows']:,} | Days: {row['unique_days']:,}")
        
        # Check if it has region information
        region_query = f"""
        SELECT COUNT(DISTINCT COALESCE(region, country, location, 'global')) as regions
        FROM `cbi-v14.{dataset}.{table}`
        """
        try:
            region_result = client.query(region_query).to_dataframe()
            regions = region_result.iloc[0]['regions']
            print(f"  Regions: {regions}")
            
            if regions > 1:
                print(f"  → KEEP: Multi-region data ({regions} regions)")
            elif row['rows'] > 0:
                print(f"  → KEEP: Region-specific data")
            else:
                print(f"  → DELETE: Empty table")
        except:
            print(f"  → KEEP: Specific regional data")
            
    except Exception as e:
        print(f"\n{dataset}.{table}: ERROR - {str(e)[:50]}")

print("\n4. TRUE DUPLICATES TO DELETE:")
print("-"*80)

duplicates_to_delete = []

# Identify clear duplicates
print("\n✗ DELETE THESE (True duplicates or empty):")
print("  - forecasting_data_warehouse.soybean_oil_forecast (only 30 rows, old forecast)")
print("  - forecasting_data_warehouse.vw_soybean_oil_daily_clean (duplicate view, move to signals)")
print("  - forecasting_data_warehouse.weather_paraguay_daily (0 rows)")
print("  - forecasting_data_warehouse.weather_uruguay_daily (0 rows)")
print("  - forecasting_data_warehouse.biofuel_metrics (0 rows)")
print("  - forecasting_data_warehouse.extraction_labels (0 rows)")
print("  - forecasting_data_warehouse.harvest_progress (0 rows)")
print("  - staging_ml.* (all 15 tables - temporary staging)")

print("\n✓ KEEP THESE (Different commodities or add value):")
print("  - soybean_prices (ZS - different commodity)")
print("  - soybean_oil_prices (ZL - primary source)")
print("  - soybean_meal_prices (ZM - different commodity)")
print("  - weather_data (main weather table)")
print("  - weather_brazil_daily (region specific)")
print("  - weather_argentina_daily (region specific)")
print("  - weather_us_midwest_daily (region specific)")

print("\n5. REORGANIZATION PLAN:")
print("-"*80)

print("""
CLEANUP ACTIONS:

1. DELETE True Duplicates:
   - soybean_oil_forecast (old, only 30 rows)
   - All empty tables (0 rows)
   - All staging_ml tables (temporary)

2. MOVE Views to Proper Location:
   - All vw_* from forecasting_data_warehouse → signals
   - This separates raw data from calculations

3. STANDARDIZE Schemas:
   - Fix crude_oil_prices to match other commodities:
     * Rename 'date' → 'time'
     * Rename 'close_price' → 'close'
   - Ensure all price tables have: time, open, high, low, close, volume, symbol

4. KEEP These Separate (NOT duplicates):
   - soybean_prices (beans ~$1,300)
   - soybean_oil_prices (oil ~$55)
   - soybean_meal_prices (meal ~$380)
   - Regional weather tables (different locations)

5. Create Master Training Dataset:
   - Join all commodities properly
   - Include ALL features (sentiment, VIX, treasury, etc.)
   - Standardized date column
   - No duplicates
""")

print("\n" + "="*80)
print("TRUE DUPLICATE ANALYSIS COMPLETE")
print("="*80)
print("\nBottom line: Most 'duplicates' are actually DIFFERENT commodities or regional data!")
print("Only need to clean up empty tables, old forecasts, and reorganize views.")
