#!/usr/bin/env python3
"""
COMPREHENSIVE NULL AUDIT - Find ALL NULL columns in training dataset
Reports: NULL percentage, column type, data availability
"""
from google.cloud import bigquery
import pandas as pd

PROJECT_ID = "cbi-v14"
DATASET = "models_v4"
TABLE = "training_dataset_super_enriched"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔍 COMPREHENSIVE NULL AUDIT")
print("="*80)
print(f"Table: {DATASET}.{TABLE}")
print("="*80)

# Get all numeric/float columns
schema_query = f"""
SELECT column_name, data_type
FROM `{PROJECT_ID}.{DATASET}.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = '{TABLE}'
  AND data_type IN ('FLOAT64', 'INT64', 'NUMERIC', 'BIGNUMERIC', 'STRING', 'DATE', 'TIMESTAMP')
ORDER BY ordinal_position
"""

columns_df = client.query(schema_query).to_dataframe()
print(f"\nTotal columns to audit: {len(columns_df)}\n")

# Check NULL percentage for each column
null_results = []

for idx, row in columns_df.iterrows():
    col_name = row['column_name']
    col_type = row['data_type']
    
    # Query NULL count for this column
    null_query = f"""
    SELECT 
      COUNT(*) as total_rows,
      COUNTIF({col_name} IS NULL) as null_count,
      COUNTIF({col_name} IS NOT NULL) as non_null_count,
      ROUND(100.0 * COUNTIF({col_name} IS NULL) / COUNT(*), 2) as null_pct
    FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
    """
    
    try:
        result = client.query(null_query).to_dataframe()
        null_pct = result['null_pct'].iloc[0]
        null_count = int(result['null_count'].iloc[0])
        non_null_count = int(result['non_null_count'].iloc[0])
        total_rows = int(result['total_rows'].iloc[0])
        
        if null_pct > 0:
            null_results.append({
                'column_name': col_name,
                'data_type': col_type,
                'total_rows': total_rows,
                'null_count': null_count,
                'non_null_count': non_null_count,
                'null_pct': null_pct
            })
            
            status = "🔴 ALL NULL" if null_pct == 100 else "🟡 PARTIAL NULL" if null_pct > 50 else "🟢 MOSTLY FULL"
            print(f"{status} {col_name:50s} {null_pct:6.2f}% NULL ({null_count}/{total_rows})")
    
    except Exception as e:
        print(f"❌ Error checking {col_name}: {str(e)[:100]}")

# Summary
print("\n" + "="*80)
print("📊 NULL AUDIT SUMMARY")
print("="*80)

df_nulls = pd.DataFrame(null_results)

if len(df_nulls) > 0:
    all_null = df_nulls[df_nulls['null_pct'] == 100]
    high_null = df_nulls[(df_nulls['null_pct'] >= 50) & (df_nulls['null_pct'] < 100)]
    partial_null = df_nulls[df_nulls['null_pct'] < 50]
    
    print(f"\n🔴 ALL NULL (100%): {len(all_null)} columns")
    if len(all_null) > 0:
        for col in all_null['column_name'].values:
            print(f"   - {col}")
    
    print(f"\n🟡 HIGH NULL (50-99%): {len(high_null)} columns")
    if len(high_null) > 0:
        for col in high_null['column_name'].values:
            print(f"   - {col}")
    
    print(f"\n🟢 PARTIAL NULL (<50%): {len(partial_null)} columns")
    
    print("\n" + "="*80)
    print(f"TOTAL COLUMNS WITH NULLs: {len(df_nulls)}")
    print("="*80)
    
    # Save to CSV
    df_nulls.to_csv('null_audit_results.csv', index=False)
    print("\n✅ Results saved to: null_audit_results.csv")
else:
    print("✅ NO NULL COLUMNS FOUND!")









