#!/usr/bin/env python3
"""
Check yahoo_finance_comprehensive for data that can fill identified gaps
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("CHECKING YAHOO_FINANCE_COMPREHENSIVE FOR GAP FILLERS")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Check what symbols are available
print("\n1. AVAILABLE SYMBOLS IN YAHOO_FINANCE_COMPREHENSIVE")
print("-"*80)

query = """
SELECT 
    symbol,
    symbol_name,
    category,
    COUNT(*) as row_count,
    MIN(date) as min_date,
    MAX(date) as max_date,
    ROUND(100 * COUNT(DISTINCT date) / 
          NULLIF(DATE_DIFF(MAX(date), MIN(date), DAY), 0), 1) as completeness_pct
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
GROUP BY symbol, symbol_name, category
ORDER BY category, symbol
"""

print("\nQuerying available symbols...")
result = client.query(query).result()

commodities_found = {}
for row in result:
    status = "✅" if row.row_count > 1000 else "⚠️"
    print(f"{status} {row.symbol:10} | {row.symbol_name[:30]:30} | {row.category:15} | "
          f"{row.row_count:6,} rows | {row.min_date} to {row.max_date}")
    
    commodities_found[row.symbol] = {
        'name': row.symbol_name,
        'category': row.category,
        'rows': row.row_count,
        'date_range': f"{row.min_date} to {row.max_date}"
    }

print("\n2. MAPPING TO IDENTIFIED GAPS")
print("="*80)

# Map Yahoo symbols to our gaps
gap_mappings = {
    'CL=F': ('crude_oil_prices', 'Crude Oil WTI'),
    'NG=F': ('natural_gas_prices', 'Natural Gas'),
    'ZS=F': ('soybean_prices', 'Soybeans'),
    'ZC=F': ('corn_prices', 'Corn'),
    'ZW=F': ('wheat_prices', 'Wheat'),
    'ZM=F': ('soybean_meal_prices', 'Soybean Meal'),
    'GC=F': ('gold_prices', 'Gold'),
    'SI=F': ('silver_prices', 'Silver'),
    'DX-Y.NYB': ('usd_index_prices', 'USD Index'),
    'BZ=F': ('brent_oil_prices', 'Brent Oil'),
    'HG=F': ('copper_prices', 'Copper'),
    '^VIX': ('vix_daily', 'VIX Index'),
    '^GSPC': ('sp500_prices', 'S&P 500'),
    '^TNX': ('treasury_10y_yield', '10Y Treasury Yield'),
}

print("\nGAP FILLING OPPORTUNITIES:")
print("-"*80)

for yahoo_symbol, (our_table, description) in gap_mappings.items():
    if yahoo_symbol in commodities_found:
        data = commodities_found[yahoo_symbol]
        print(f"\n✅ CAN BACKFILL: {our_table}")
        print(f"   Yahoo Symbol: {yahoo_symbol}")
        print(f"   Description: {description}")
        print(f"   Available: {data['rows']:,} rows ({data['date_range']})")
        print(f"   Category: {data['category']}")
    else:
        print(f"\n❌ NOT AVAILABLE: {our_table} ({description})")
        print(f"   Would need symbol: {yahoo_symbol}")

print("\n3. ADDITIONAL USEFUL SYMBOLS FOUND")
print("="*80)

# Check for other useful symbols not in our mapping
print("\nOther potentially useful symbols:")
print("-"*80)

useful_patterns = ['oil', 'soy', 'corn', 'wheat', 'china', 'brazil', 'argent', 'palm', 'canola']

for symbol, data in commodities_found.items():
    if symbol not in gap_mappings:
        name_lower = data['name'].lower()
        if any(pattern in name_lower for pattern in useful_patterns):
            print(f"  {symbol:10} | {data['name'][:40]:40} | {data['rows']:,} rows")

print("\n4. BACKFILL SQL GENERATION")
print("="*80)

print("\nGenerated SQL for backfilling from Yahoo:")
print("-"*80)

for yahoo_symbol, (our_table, description) in gap_mappings.items():
    if yahoo_symbol in commodities_found:
        print(f"""
-- Backfill {description} to {our_table}
INSERT INTO `cbi-v14.forecasting_data_warehouse.{our_table}`
(time, open, high, low, close, volume, symbol, source_name)
SELECT 
    DATETIME(date) as time,
    open,
    high,
    low,
    close,
    volume,
    '{yahoo_symbol.replace("=F", "")}' as symbol,
    'yahoo_finance_comprehensive' as source_name
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = '{yahoo_symbol}'
  AND date < '2020-01-01'  -- Only backfill historical
ORDER BY date;
""")

print("\n5. CRITICAL GAPS STILL UNFILLED")
print("="*80)

unfilled_gaps = [
    'china_soybean_imports - Need USDA FAS or customs data',
    'cftc_cot - Need CFTC.gov historical files (2006-2024)',
    'baltic_dry_index - Need Bloomberg/Refinitiv data',
    'argentina_exports - Need INDEC/MAGyP data',
    'brazil_exports - Need SECEX/MDIC data',
    'port_congestion - Need port authority APIs',
    'trump_truth_social - Need Truth Social API',
    'fed_funds_rate - Can get from FRED API',
    'credit_spreads - Can get from FRED API',
]

print("\nGaps that still need external data sources:")
print("-"*80)
for gap in unfilled_gaps:
    print(f"  ❌ {gap}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
