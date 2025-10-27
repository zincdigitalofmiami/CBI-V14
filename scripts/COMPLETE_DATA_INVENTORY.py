#!/usr/bin/env python3
"""
COMPLETE INVENTORY OF ALL DATA TYPES
Including Fed rates, 10Y yields, S&P 500, tariffs, biofuel, cotton, and MORE
"""

from google.cloud import bigquery
client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("COMPLETE DATA INVENTORY - EVERYTHING WE HAVE")
print("=" * 80)

# Get ALL tables from ALL datasets
datasets = ['forecasting_data_warehouse', 'staging', 'signals', 'models', 'neural', 'api', 'curated']

all_tables = {}
for dataset in datasets:
    query = f"""
    SELECT table_name, row_count, table_type
    FROM `cbi-v14.{dataset}.__TABLES__`
    ORDER BY table_name
    """
    try:
        tables = []
        for row in client.query(query):
            tables.append((row.table_name, row.row_count, row.table_type))
        all_tables[dataset] = tables
    except:
        pass

# Categorize all data types
print("\n1. COMMODITY FUTURES (Agricultural)")
print("-" * 40)
commodity_futures = [
    'soybean_oil_prices', 'soybean_prices', 'soybean_meal_prices',
    'corn_prices', 'wheat_prices', 'cotton_prices', 
    'cocoa_prices', 'coffee_prices', 'sugar_prices'
]
for dataset, tables in all_tables.items():
    for table_name, row_count, table_type in tables:
        if table_name in commodity_futures:
            print(f"  {dataset}.{table_name}: {row_count:,} rows")

print("\n2. ENERGY MARKETS")
print("-" * 40)
energy_tables = [
    'crude_oil_prices', 'natural_gas_prices', 'biofuel_prices',
    'biofuel_policy', 'biofuel_metrics', 'biofuel_production'
]
for dataset, tables in all_tables.items():
    for table_name, row_count, table_type in tables:
        if table_name in energy_tables or 'biofuel' in table_name:
            print(f"  {dataset}.{table_name}: {row_count:,} rows")

print("\n3. VEGETABLE OILS (Substitutes)")
print("-" * 40)
veg_oil_tables = [
    'palm_oil_prices', 'palm_oil_fundamentals',
    'canola_oil_prices', 'rapeseed_oil_prices', 
    'sunflower_oil_prices'
]
for dataset, tables in all_tables.items():
    for table_name, row_count, table_type in tables:
        if table_name in veg_oil_tables:
            print(f"  {dataset}.{table_name}: {row_count:,} rows")

print("\n4. FINANCIAL MARKETS")
print("-" * 40)
financial_tables = [
    'treasury_prices', 'vix_daily', 'usd_index_prices',
    'currency_data', 'gold_prices'
]
for dataset, tables in all_tables.items():
    for table_name, row_count, table_type in tables:
        if table_name in financial_tables:
            print(f"  {dataset}.{table_name}: {row_count:,} rows")

# Check for S&P 500
query = """
SELECT DISTINCT symbol, COUNT(*) as cnt
FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
GROUP BY symbol
"""
print("\n  Checking for S&P 500 and Fed data:")
try:
    for row in client.query(query):
        print(f"    • {row.symbol}: {row.cnt} rows")
except:
    pass

print("\n5. FUNDAMENTAL DATA (Supply/Demand)")
print("-" * 40)
fundamental_tables = [
    'cftc_cot', 'usda_export_sales', 'harvest_progress',
    'usda_wasde', 'usda_harvest_progress'
]
for dataset, tables in all_tables.items():
    for table_name, row_count, table_type in tables:
        if any(fund in table_name for fund in ['cftc', 'usda', 'harvest', 'wasde']):
            print(f"  {dataset}.{table_name}: {row_count:,} rows")

print("\n6. WEATHER & CLIMATE")
print("-" * 40)
weather_tables = [
    'weather_data', 'weather_us_midwest_daily',
    'weather_brazil_daily', 'weather_argentina_daily',
    'weather_paraguay_daily', 'weather_uruguay_daily'
]
for dataset, tables in all_tables.items():
    for table_name, row_count, table_type in tables:
        if 'weather' in table_name:
            print(f"  {dataset}.{table_name}: {row_count:,} rows")

print("\n7. POLICY & TARIFFS")
print("-" * 40)
policy_tables = [
    'trump_policy_intelligence', 'trade_policy_events',
    'ice_enforcement_intelligence', 'biofuel_policy'
]
for dataset, tables in all_tables.items():
    for table_name, row_count, table_type in tables:
        if any(pol in table_name for pol in ['policy', 'trump', 'ice', 'trade', 'tariff']):
            print(f"  {dataset}.{table_name}: {row_count:,} rows")

print("\n8. SENTIMENT & INTELLIGENCE")
print("-" * 40)
sentiment_tables = [
    'social_sentiment', 'news_intelligence', 
    'comprehensive_social_intelligence'
]
for dataset, tables in all_tables.items():
    for table_name, row_count, table_type in tables:
        if any(sent in table_name for sent in ['sentiment', 'intelligence', 'social', 'news']):
            print(f"  {dataset}.{table_name}: {row_count:,} rows")

print("\n9. ECONOMIC INDICATORS")
print("-" * 40)
for dataset, tables in all_tables.items():
    for table_name, row_count, table_type in tables:
        if 'economic' in table_name or 'indicator' in table_name:
            print(f"  {dataset}.{table_name}: {row_count:,} rows")

# Check what's in economic_indicators
query = """
SELECT DISTINCT indicator_name
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
LIMIT 20
"""
print("\n  Economic indicators include:")
try:
    for row in client.query(query):
        print(f"    • {row.indicator_name}")
except:
    pass

print("\n10. SIGNALS & FEATURES (Derived)")
print("-" * 40)
signal_count = 0
for dataset, tables in all_tables.items():
    for table_name, row_count, table_type in tables:
        if 'signal' in table_name or 'feature' in table_name:
            signal_count += 1
print(f"  Total signal/feature views: {signal_count}")

print("\n" + "=" * 80)
print("CRITICAL DATA GAPS TO CHECK:")
print("=" * 80)

# Check for specific missing data
missing_checks = [
    ('S&P 500', 'SPX or SPY symbol'),
    ('Fed Funds Rate', 'FRED data or economic_indicators'),
    ('10-Year Yield', 'treasury_prices or TNX'),
    ('Tariff data', 'trade_policy_events or trump tables'),
    ('China imports', 'china_import tables'),
    ('Crush margins', 'calculated from soy/meal/oil'),
    ('Freight rates', 'Baltic Dry Index or shipping'),
    ('Options/volatility', 'implied volatility data')
]

for data_type, where_to_look in missing_checks:
    print(f"  ? {data_type}: Check {where_to_look}")

print("\n" + "=" * 80)
print("DATA QUALITY ISSUES FOUND:")
print("=" * 80)
print("1. Different date column names (date, time, timestamp, report_date)")
print("2. Different price column names (close, close_price)")
print("3. Wrong symbols (CRUDE_OIL_PRICES instead of CL)")
print("4. Missing currency conversions (palm in MYR, canola in CAD)")
print("5. Mixing futures with spot prices")
print("6. Mixing prices with indices/percentages")
print("=" * 80)
