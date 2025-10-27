#!/usr/bin/env python3
"""
UNDERSTAND THE DIFFERENT DATA TYPES
Not everything is a simple price - we have weights, volumes, averages, indices, sentiments, etc.
Each needs DIFFERENT handling!
"""

from google.cloud import bigquery
client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("UNDERSTANDING DIFFERENT DATA TYPES IN OUR SYSTEM")
print("=" * 80)

# 1. COMMODITY FUTURES PRICES (need symbol, contract month, volume)
print("\n1. COMMODITY FUTURES (SYMBOL-BASED PRICES)")
print("-" * 40)
futures_tables = [
    ('soybean_oil_prices', 'ZL', 'cents/lb', 'continuous contract'),
    ('soybean_prices', 'S', 'cents/bushel', 'continuous contract'),
    ('corn_prices', 'C/ZC', 'cents/bushel', 'continuous contract'),
    ('wheat_prices', 'W/ZW', 'cents/bushel', 'continuous contract'),
    ('cotton_prices', 'CT', 'cents/lb', 'continuous contract'),
    ('soybean_meal_prices', 'SM/ZM', '$/ton', 'continuous contract')
]

for table, symbol, units, contract_type in futures_tables:
    print(f"{table}:")
    print(f"  Symbol: {symbol}")
    print(f"  Units: {units}")
    print(f"  Type: {contract_type}")
    print(f"  Needs: open/high/low/close/volume, contract month")

# 2. SPOT/CASH PRICES (no contracts, just daily prices)
print("\n2. SPOT/CASH PRICES (NO CONTRACTS)")
print("-" * 40)
spot_tables = [
    ('crude_oil_prices', 'CL/WTI/Brent', '$/barrel', 'spot price'),
    ('palm_oil_prices', 'FCPO/Palm', 'MYR/tonne', 'Malaysian spot'),
    ('canola_oil_prices', 'Canola', 'CAD/tonne', 'Canadian spot'),
    ('rapeseed_oil_prices', 'Rapeseed', 'EUR/tonne', 'European spot')
]

for table, symbol, units, price_type in spot_tables:
    print(f"{table}:")
    print(f"  Symbol: {symbol}")
    print(f"  Units: {units}")
    print(f"  Type: {price_type}")
    print(f"  Needs: daily price, currency conversion")

# 3. FINANCIAL INDICES (calculated values, not traded)
print("\n3. FINANCIAL INDICES (CALCULATED VALUES)")
print("-" * 40)
index_tables = [
    ('vix_daily', 'VIX', 'volatility %', 'fear gauge - NOT a price'),
    ('usd_index_prices', 'DXY', 'index value', 'weighted basket'),
    ('treasury_prices', '10Y/ZN', 'yield %', 'interest rate - NOT commodity')
]

for table, symbol, units, nature in index_tables:
    print(f"{table}:")
    print(f"  Symbol: {symbol}")
    print(f"  Units: {units}")
    print(f"  Nature: {nature}")
    print(f"  Needs: special handling for correlations")

# 4. FUNDAMENTAL DATA (volumes, not prices)
print("\n4. FUNDAMENTAL DATA (VOLUMES/QUANTITIES)")
print("-" * 40)
fundamental_tables = [
    ('cftc_cot', 'positions', 'contracts', 'trader positioning'),
    ('usda_export_sales', 'sales', 'metric tons', 'export volumes'),
    ('harvest_progress', 'progress', 'percentage', 'crop completion'),
    ('weather_data', 'weather', 'temp/precip', 'environmental conditions')
]

for table, data_type, units, description in fundamental_tables:
    print(f"{table}:")
    print(f"  Type: {data_type}")
    print(f"  Units: {units}")
    print(f"  Description: {description}")
    print(f"  NOT PRICES - different join logic needed!")

# 5. SENTIMENT/INTELLIGENCE (scores, not prices)
print("\n5. SENTIMENT & INTELLIGENCE (SCORES/TEXT)")
print("-" * 40)
sentiment_tables = [
    ('social_sentiment', 'sentiment score', '0-1 scale', 'text analysis'),
    ('trump_policy_intelligence', 'policy impact', 'categorical', 'event data'),
    ('news_intelligence', 'news sentiment', 'scored text', 'media analysis')
]

for table, data_type, scale, description in sentiment_tables:
    print(f"{table}:")
    print(f"  Type: {data_type}")
    print(f"  Scale: {scale}")
    print(f"  Description: {description}")
    print(f"  Cannot correlate directly with prices!")

# 6. DERIVED/CALCULATED METRICS
print("\n6. DERIVED METRICS (CALCULATED FROM OTHER DATA)")
print("-" * 40)
derived_tables = [
    ('biofuel_policy', 'policy metrics', 'various', 'RIN prices, mandates'),
    ('crush_margins', 'spread calculation', '$/bushel', 'processing economics'),
    ('correlation_features', 'rolling correlations', '-1 to 1', 'statistical relationships')
]

for table, metric_type, units, description in derived_tables:
    print(f"{table}:")
    print(f"  Type: {metric_type}")
    print(f"  Units: {units}")
    print(f"  Description: {description}")

# Now check actual data to understand the problems
print("\n" + "=" * 80)
print("ACTUAL DATA STRUCTURE ISSUES")
print("=" * 80)

# Check date/time columns across different data types
query = """
SELECT 
    table_name,
    column_name,
    data_type
FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.COLUMNS`
WHERE column_name IN ('date', 'time', 'timestamp', 'report_date', 'week_ending')
ORDER BY table_name, column_name
"""

print("\nDATE/TIME COLUMN VARIATIONS:")
date_columns = {}
for row in client.query(query):
    if row.table_name not in date_columns:
        date_columns[row.table_name] = []
    date_columns[row.table_name].append(f"{row.column_name}:{row.data_type}")

for table, cols in date_columns.items():
    print(f"  {table}: {', '.join(cols)}")

print("\n" + "=" * 80)
print("CRITICAL INSIGHTS:")
print("=" * 80)
print("1. FUTURES need contract months and volume")
print("2. SPOT PRICES need currency conversion")
print("3. INDICES are NOT prices (VIX is %, Treasury is yield)")
print("4. FUNDAMENTALS are volumes/quantities, not prices")
print("5. SENTIMENT is scores/text, cannot correlate directly")
print("6. Each data type needs DIFFERENT join logic")
print("7. Correlation between VIX and prices is DIFFERENT than price-to-price")
print("8. Weather affects prices but isn't a price itself")
print("=" * 80)
