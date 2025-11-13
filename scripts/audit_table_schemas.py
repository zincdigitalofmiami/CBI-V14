#!/usr/bin/env python3
"""
Quick schema audit to find actual date column names
"""
from google.cloud import bigquery

PROJECT_ID = "cbi-v14"
WAREHOUSE_DATASET = "forecasting_data_warehouse"

client = bigquery.Client(project=PROJECT_ID)

# Tables that had errors
tables_to_check = [
    'canola_oil_prices',
    'corn_prices',
    'crude_oil_prices',
    'gold_prices',
    'natural_gas_prices',
    'cftc_cot',
    'news_intelligence',
    'news_advanced',
    'economic_indicators',
]

print("="*80)
print("SCHEMA AUDIT - Finding actual date column names")
print("="*80)

for table_name in tables_to_check:
    try:
        query = f"""
        SELECT column_name, data_type
        FROM `{PROJECT_ID}.{WAREHOUSE_DATASET}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
        """
        result = client.query(query).to_dataframe()
        
        if not result.empty:
            print(f"\n{table_name}:")
            # Find date-like columns
            date_cols = result[result['column_name'].str.contains('date|time|timestamp', case=False, na=False)]
            if not date_cols.empty:
                for _, row in date_cols.iterrows():
                    print(f"  ✅ {row['column_name']} ({row['data_type']})")
            else:
                print(f"  ⚠️  No obvious date columns found")
                print(f"  All columns: {', '.join(result['column_name'].tolist()[:10])}")
        else:
            print(f"\n{table_name}: Table not found")
    except Exception as e:
        print(f"\n{table_name}: Error - {e}")

