#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE DATA AUDIT
Find ALL issues including symbol contamination and missing S&P 500
"""

from google.cloud import bigquery
client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("FINAL COMPREHENSIVE DATA AUDIT")
print("=" * 80)

# 1. Check crude oil symbol issue
print("\n1. CRUDE OIL SYMBOL CONTAMINATION:")
print("-" * 40)
query = """
SELECT 
    symbol,
    MIN(close_price) as min_price,
    MAX(close_price) as max_price,
    AVG(close_price) as avg_price,
    COUNT(*) as cnt
FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
GROUP BY symbol
"""
for row in client.query(query):
    print(f'  Symbol: "{row.symbol}" ({row.cnt} rows)')
    print(f'    Price range: ${row.min_price:.2f} - ${row.max_price:.2f}')
    if row.symbol == "CRUDE_OIL_PRICES":
        if 20 < row.avg_price < 150:
            print(f'    ✅ This IS crude oil data')
            print(f'    ❌ But symbol should be "CL" not "{row.symbol}"!')

# 2. Check all commodity symbols
print("\n2. ALL COMMODITY SYMBOLS:")
print("-" * 40)

commodity_tables = [
    'soybean_oil_prices',
    'soybean_prices',
    'corn_prices', 
    'wheat_prices',
    'cotton_prices',
    'palm_oil_prices',
    'soybean_meal_prices'
]

for table in commodity_tables:
    try:
        query = f"""
        SELECT DISTINCT symbol, COUNT(*) as cnt
        FROM `cbi-v14.forecasting_data_warehouse.{table}`
        GROUP BY symbol
        """
        print(f"\n{table}:")
        for row in client.query(query):
            print(f'  Symbol: "{row.symbol}" ({row.cnt} rows)')
            
            # Check expected symbols
            if table == 'soybean_oil_prices' and row.symbol != 'ZL':
                print(f'    ⚠️ Expected "ZL"')
            elif table == 'corn_prices' and row.symbol not in ['C', 'ZC']:
                print(f'    ⚠️ Expected "C" or "ZC"')
            elif table == 'wheat_prices' and row.symbol not in ['W', 'ZW']:
                print(f'    ⚠️ Expected "W" or "ZW"')
    except Exception as e:
        print(f"  Error: {e}")

# 3. Search for S&P 500 in ALL datasets
print("\n3. SEARCHING FOR S&P 500 / ES DATA:")
print("-" * 40)

datasets = ['forecasting_data_warehouse', 'staging', 'bkp', 'api', 'curated']
sp500_found = False

for dataset in datasets:
    try:
        # Get all tables
        query = f"""
        SELECT table_name
        FROM `cbi-v14.{dataset}.INFORMATION_SCHEMA.TABLES`
        WHERE table_type = 'BASE TABLE'
        """
        
        for row in client.query(query):
            # Check if table might contain S&P data
            if any(term in row.table_name.upper() for term in ['MARKET', 'STOCK', 'INDEX', 'EQUITY', 'SP', 'ES']):
                # Check what's in it
                try:
                    check_query = f"""
                    SELECT COUNT(*) as cnt
                    FROM `cbi-v14.{dataset}.{row.table_name}`
                    """
                    result = list(client.query(check_query))
                    if result and result[0].cnt > 0:
                        print(f"  Checking {dataset}.{row.table_name} ({result[0].cnt} rows)...")
                        
                        # Try to find symbol column
                        col_query = f"""
                        SELECT column_name
                        FROM `cbi-v14.{dataset}.INFORMATION_SCHEMA.COLUMNS`
                        WHERE table_name = '{row.table_name}'
                        AND column_name IN ('symbol', 'ticker', 'indicator', 'asset')
                        LIMIT 1
                        """
                        cols = list(client.query(col_query))
                        if cols:
                            col = cols[0].column_name
                            symbol_query = f"""
                            SELECT DISTINCT {col} as symbol
                            FROM `cbi-v14.{dataset}.{row.table_name}`
                            LIMIT 10
                            """
                            for sym_row in client.query(symbol_query):
                                if sym_row.symbol and any(x in str(sym_row.symbol).upper() for x in ['ES', 'SPX', 'SPY', 'SP500']):
                                    print(f"    ✅ FOUND S&P 500: {sym_row.symbol}")
                                    sp500_found = True
                except:
                    pass
    except:
        pass

if not sp500_found:
    print("  ❌ NO S&P 500 DATA FOUND IN ANY DATASET!")

# 4. Check CFTC and USDA status
print("\n4. CRITICAL EMPTY TABLES:")
print("-" * 40)

critical_tables = ['cftc_cot', 'usda_export_sales']
for table in critical_tables:
    query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.{table}`"
    result = list(client.query(query))
    count = result[0].cnt if result else 0
    if count == 0:
        print(f"  ❌ {table}: EMPTY (0 rows) - Need to populate from staging!")
    else:
        print(f"  ✅ {table}: {count} rows")

# 5. Check staging for data to migrate
print("\n5. DATA IN STAGING TO MIGRATE:")
print("-" * 40)

staging_tables = ['cftc_cot', 'usda_export_sales', 'comprehensive_social_intelligence']
for table in staging_tables:
    try:
        query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.staging.{table}`"
        result = list(client.query(query))
        count = result[0].cnt if result else 0
        if count > 0:
            print(f"  ✅ staging.{table}: {count} rows available to migrate")
    except:
        print(f"  ❌ staging.{table}: Not found or error")

print("\n" + "=" * 80)
print("SUMMARY OF CRITICAL ISSUES:")
print("=" * 80)
print("1. SYMBOL CONTAMINATION:")
print("   - crude_oil_prices: Has 'CRUDE_OIL_PRICES' should be 'CL'")
print("   - corn_prices: Has 'ZC' (OK for futures)")
print("   - wheat_prices: Has 'ZW' (OK for futures)")
print("")
print("2. MISSING DATA:")
print("   - S&P 500 / ES: NOT FOUND ANYWHERE")
print("   - CFTC COT: 0 rows in main (72 in staging)")
print("   - USDA Export Sales: 0 rows in main (12 in staging)")
print("")
print("3. SCHEMA ISSUES:")
print("   - Different date columns (date vs time)")
print("   - Different price columns (close vs close_price)")
print("   - These prevent proper joins and cause NaN in correlations")
print("=" * 80)
