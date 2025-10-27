#!/usr/bin/env python3
"""
DEEP INSPECTION - Look INSIDE the data, check actual values
Don't assume based on names!
"""

from google.cloud import bigquery
import datetime
client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("DEEP DATA INSPECTION - WHAT'S REALLY IN OUR TABLES?")
print("=" * 80)

# 1. Search EVERYWHERE for S&P 500 data
print("\n1. SEARCHING FOR S&P 500 IN ALL TABLES")
print("-" * 40)

# Get all tables
all_tables_query = """
SELECT table_name 
FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.TABLES`
WHERE table_type = 'BASE TABLE'
"""

tables_to_check = []
for row in client.query(all_tables_query):
    tables_to_check.append(row.table_name)

# Search for S&P patterns in data
sp500_found = []
for table in tables_to_check:
    try:
        # Check if table has symbol column
        check_cols = f"""
        SELECT column_name 
        FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table}' 
        AND column_name IN ('symbol', 'indicator', 'ticker', 'name', 'asset')
        LIMIT 1
        """
        cols = list(client.query(check_cols))
        
        if cols:
            col_name = cols[0].column_name
            # Search for S&P patterns
            search_query = f"""
            SELECT DISTINCT {col_name} as symbol, COUNT(*) as cnt
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            WHERE UPPER({col_name}) LIKE '%SP%' 
               OR UPPER({col_name}) LIKE '%500%'
               OR UPPER({col_name}) LIKE '%SPX%'
               OR UPPER({col_name}) LIKE '%SPY%'
               OR UPPER({col_name}) = 'ES'
            GROUP BY {col_name}
            """
            results = list(client.query(search_query))
            if results:
                for r in results:
                    print(f"  ✓ FOUND in {table}: {r.symbol} ({r.cnt} rows)")
                    sp500_found.append((table, r.symbol, r.cnt))
    except:
        pass

if not sp500_found:
    print("  ❌ No S&P 500 data found with symbol search")

# 2. Check actual VALUES in key tables to identify what they really are
print("\n2. CHECKING ACTUAL VALUES TO IDENTIFY DATA")
print("-" * 40)

# Check crude oil - what are the actual price ranges?
print("\nCRUDE_OIL_PRICES - Actual values:")
query = """
SELECT 
    symbol,
    MIN(close_price) as min_price,
    MAX(close_price) as max_price,
    AVG(close_price) as avg_price,
    COUNT(*) as rows
FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
GROUP BY symbol
"""
for row in client.query(query):
    print(f"  Symbol: {row.symbol}")
    print(f"    Range: ${row.min_price:.2f} - ${row.max_price:.2f}")
    print(f"    Average: ${row.avg_price:.2f}")
    print(f"    Rows: {row.rows}")
    # Check if this is really crude based on price range
    if 20 < row.avg_price < 150:
        print(f"    ✓ Looks like crude oil prices")
    else:
        print(f"    ⚠️ Price range doesn't match crude oil!")

# Check VIX - should be 10-80 range typically
print("\nVIX_DAILY - Actual values:")
query = """
SELECT 
    symbol,
    MIN(close) as min_val,
    MAX(close) as max_val,
    AVG(close) as avg_val
FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
GROUP BY symbol
"""
for row in client.query(query):
    print(f"  Symbol: {row.symbol}")
    print(f"    Range: {row.min_val:.2f} - {row.max_val:.2f}")
    if 5 < row.avg_val < 100:
        print(f"    ✓ Looks like VIX volatility index")
    else:
        print(f"    ⚠️ Range doesn't match VIX!")

# Check treasury - should be yield percentages 0-6%
print("\nTREASURY_PRICES - Actual values:")
query = """
SELECT 
    symbol,
    MIN(close) as min_val,
    MAX(close) as max_val,
    AVG(close) as avg_val
FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
GROUP BY symbol
"""
for row in client.query(query):
    print(f"  Symbol: {row.symbol}")
    print(f"    Range: {row.min_val:.2f} - {row.max_val:.2f}")
    if 0 < row.avg_val < 10:
        print(f"    ✓ Looks like treasury yields (%)")
    elif 90 < row.avg_val < 140:
        print(f"    ⚠️ Might be treasury FUTURES prices, not yields!")

# Check market_prices - only 2 rows, what is it?
print("\nMARKET_PRICES - What's in here? (only 2 rows)")
query = """
SELECT * FROM `cbi-v14.forecasting_data_warehouse.market_prices`
"""
for row in client.query(query):
    print(f"  Row: {dict(row)}")

# Check gold - verify it's really gold prices
print("\nGOLD_PRICES - Actual values:")
query = """
SELECT 
    MIN(close_price) as min_val,
    MAX(close_price) as max_val,
    AVG(close_price) as avg_val
FROM `cbi-v14.forecasting_data_warehouse.gold_prices`
"""
for row in client.query(query):
    print(f"  Range: ${row.min_val:.2f} - ${row.max_val:.2f}")
    if 1000 < row.avg_val < 3000:
        print(f"  ✓ Looks like gold prices ($/oz)")
    else:
        print(f"  ⚠️ Range doesn't match gold!")

# 3. Check economic_indicators for hidden S&P data
print("\n3. CHECKING ECONOMIC_INDICATORS FOR HIDDEN DATA")
print("-" * 40)
query = """
SELECT DISTINCT indicator
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
WHERE UPPER(indicator) LIKE '%SP%' 
   OR UPPER(indicator) LIKE '%500%'
   OR UPPER(indicator) LIKE '%STOCK%'
   OR UPPER(indicator) LIKE '%EQUITY%'
"""
for row in client.query(query):
    print(f"  Found: {row.indicator}")

# 4. Check all datasets (not just forecasting_data_warehouse)
print("\n4. CHECKING OTHER DATASETS FOR S&P 500")
print("-" * 40)

datasets = ['staging', 'bkp', 'models', 'signals', 'api', 'curated']
for dataset in datasets:
    try:
        query = f"""
        SELECT table_name
        FROM `cbi-v14.{dataset}.INFORMATION_SCHEMA.TABLES`
        WHERE UPPER(table_name) LIKE '%SP%' 
           OR UPPER(table_name) LIKE '%500%'
           OR UPPER(table_name) LIKE '%STOCK%'
           OR UPPER(table_name) LIKE '%EQUITY%'
        """
        for row in client.query(query):
            print(f"  Found in {dataset}: {row.table_name}")
    except:
        pass

print("\n" + "=" * 80)
print("KEY FINDINGS:")
print("=" * 80)
print("1. Check if crude oil symbol 'CRUDE_OIL_PRICES' is just naming issue")
print("2. Verify treasury_prices - might be futures not yields")
print("3. market_prices table has only 2 rows - check what it is")
print("4. Look for S&P 500 in other datasets or under different names")
print("=" * 80)
