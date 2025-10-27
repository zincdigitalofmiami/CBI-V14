#!/usr/bin/env python3
"""
Investigate duplicate data entries in detail
SAFETY: Read-only investigation
"""

from google.cloud import bigquery
client = bigquery.Client(project='cbi-v14')

print('=' * 80)
print('CRITICAL: DUPLICATE DATA INVESTIGATION')
print('=' * 80)

# Check duplicates in detail
query = """
WITH duplicates AS (
    SELECT 
        DATE(time) as date,
        symbol,
        COUNT(*) as count,
        ARRAY_AGG(STRUCT(
            time,
            close,
            volume,
            source_name
        ) ORDER BY time) as entries
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE symbol = 'ZL'
    GROUP BY DATE(time), symbol
    HAVING COUNT(*) > 1
)
SELECT * FROM duplicates
ORDER BY date DESC
LIMIT 5
"""

print('\nDUPLICATE ENTRIES DETAIL (Top 5 dates):')
try:
    result = client.query(query).result()
    duplicate_dates = []
    for row in result:
        duplicate_dates.append(row.date)
        print(f'\n📅 {row.date}: {row.count} entries')
        for i, entry in enumerate(row.entries, 1):
            print(f'   {i}. Time: {entry.time}, Close: ${entry.close:.2f}, Vol: {entry.volume}, Source: {entry.source_name}')
except Exception as e:
    print(f'Error: {e}')

# Check if duplicates are from different sources or times
query2 = """
SELECT 
    source_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT DATE(time)) as unique_days
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
WHERE symbol = 'ZL'
GROUP BY source_name
"""

print('\n' + '=' * 80)
print('DATA SOURCES BREAKDOWN:')
try:
    result2 = client.query(query2).result()
    for row in result2:
        print(f'  Source: {row.source_name} - {row.total_rows} rows, {row.unique_days} unique days')
except Exception as e:
    print(f'Error: {e}')

# Check for intraday vs daily data mix
query3 = """
SELECT 
    DATE(time) as date,
    COUNT(DISTINCT EXTRACT(HOUR FROM time)) as unique_hours,
    MIN(time) as first_entry,
    MAX(time) as last_entry
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
WHERE symbol = 'ZL'
AND DATE(time) IN ('2025-10-21', '2025-10-20')
GROUP BY DATE(time)
"""

print('\n' + '=' * 80)
print('INTRADAY VS DAILY CHECK (Recent dates):')
try:
    result3 = client.query(query3).result()
    for row in result3:
        print(f'  {row.date}: {row.unique_hours} unique hours')
        print(f'    First: {row.first_entry}')
        print(f'    Last:  {row.last_entry}')
except Exception as e:
    print(f'Error: {e}')

print('\n' + '=' * 80)
print('RECOMMENDATION:')
print('=' * 80)
print('If duplicates are from:')
print('1. Different times of day → Keep latest or create daily aggregation')
print('2. Different sources → Keep most reliable source')
print('3. True duplicates → Deduplicate keeping first or last')
print('\nNEXT STEP: Create a clean view that handles duplicates properly')
