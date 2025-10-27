#!/usr/bin/env python3
"""
CHECK WHAT FEATURES ARE ACTUALLY IN THE TRAINING DATASET
Compare to what's available in the warehouse
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print(f"TRAINING DATASET FEATURE AUDIT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

print("\n1. CHECKING TRAINING DATASET COLUMNS:")
print("-"*80)

# Get columns from training dataset
columns_query = """
SELECT column_name, data_type
FROM `cbi-v14.models.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_final_v1'
ORDER BY ordinal_position
"""

try:
    columns_df = client.query(columns_query).to_dataframe()
    print(f"Total columns in training dataset: {len(columns_df)}")
    
    # Group by category
    price_cols = [c for c in columns_df['column_name'] if 'price' in c.lower() or 'close' in c.lower()]
    sentiment_cols = [c for c in columns_df['column_name'] if 'sentiment' in c.lower() or 'social' in c.lower()]
    weather_cols = [c for c in columns_df['column_name'] if 'weather' in c.lower() or 'temp' in c.lower() or 'precip' in c.lower()]
    correlation_cols = [c for c in columns_df['column_name'] if 'corr' in c.lower()]
    vix_cols = [c for c in columns_df['column_name'] if 'vix' in c.lower() or 'volatility' in c.lower()]
    fx_cols = [c for c in columns_df['column_name'] if 'usd' in c.lower() or 'dxy' in c.lower() or 'currency' in c.lower()]
    policy_cols = [c for c in columns_df['column_name'] if 'trump' in c.lower() or 'tariff' in c.lower() or 'policy' in c.lower()]
    fundamental_cols = [c for c in columns_df['column_name'] if 'cftc' in c.lower() or 'export' in c.lower() or 'import' in c.lower()]
    
    print(f"\nFeatures by category:")
    print(f"  Price features: {len(price_cols)}")
    print(f"  Sentiment features: {len(sentiment_cols)}")
    print(f"  Weather features: {len(weather_cols)}")
    print(f"  Correlation features: {len(correlation_cols)}")
    print(f"  VIX/Volatility features: {len(vix_cols)}")
    print(f"  FX/Currency features: {len(fx_cols)}")
    print(f"  Policy/Tariff features: {len(policy_cols)}")
    print(f"  Fundamental features: {len(fundamental_cols)}")
    
except Exception as e:
    print(f"Error getting columns: {e}")
    print("Trying alternative method...")
    
    # Alternative: sample the table
    sample_query = """
    SELECT *
    FROM `cbi-v14.models.training_dataset_final_v1`
    LIMIT 1
    """
    sample = client.query(sample_query).to_dataframe()
    columns_df = sample.columns.tolist()
    print(f"Total columns: {len(columns_df)}")

print("\n2. CHECKING AVAILABLE DATA IN WAREHOUSE:")
print("-"*80)

# List tables in warehouse
from google.cloud import bigquery
tables = client.list_tables('cbi-v14.forecasting_data_warehouse')
table_list = []
for table in tables:
    table_list.append(table.table_id)
    
print(f"\nAvailable data tables ({len(table_list)} total):")
for table_name in sorted(table_list):
    try:
        count_query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.{table_name}`"
        result = client.query(count_query).to_dataframe()
        count = result['cnt'].iloc[0]
        print(f"  {table_name}: {count:,} rows")
    except:
        print(f"  {table_name}: (error counting)")

print("\n3. CHECKING WHAT'S MISSING FROM TRAINING:")
print("-"*80)

# Check specific important features
checks = [
    ("Sentiment data", "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`"),
    ("Trump policy data", "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`"),
    ("VIX data", "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.vix_daily`"),
    ("USD Index", "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.usd_index_prices`"),
    ("Treasury yields", "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`"),
    ("CFTC COT", "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`"),
    ("Palm oil", "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`"),
    ("Crude oil", "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`"),
    ("Corn", "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.corn_prices`"),
    ("Wheat", "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.wheat_prices`"),
    ("Soybeans", "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.soybean_prices`"),
    ("Gold", "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.gold_prices`"),
    ("Natural gas", "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.natural_gas_prices`"),
    ("S&P 500", "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.sp500_prices`"),
]

print("\nData availability check:")
available_data = {}
for name, query in checks:
    try:
        result = client.query(query).to_dataframe()
        count = result['cnt'].iloc[0]
        available_data[name] = count
        status = "✓" if count > 0 else "✗"
        print(f"  {status} {name}: {count:,} rows")
    except:
        print(f"  ✗ {name}: NOT FOUND")
        available_data[name] = 0

print("\n4. SAMPLE TRAINING DATASET TO SEE ACTUAL FEATURES:")
print("-"*80)

sample_query = """
SELECT *
FROM `cbi-v14.models.training_dataset_final_v1`
LIMIT 1
"""

sample = client.query(sample_query).to_dataframe()
all_columns = sample.columns.tolist()

print(f"\nALL {len(all_columns)} columns in training dataset:")
for i, col in enumerate(all_columns, 1):
    print(f"  {i:3}. {col}")

print("\n5. CRITICAL MISSING FEATURES:")
print("-"*80)

# Check what critical features are missing
critical_features = [
    'sentiment', 'vix', 'trump', 'tariff', 'usd', 'dxy', 'treasury', 'yield',
    'cftc', 'cot', 'export', 'import', 'china', 'brazil', 'argentina',
    'palm', 'crude', 'corn', 'wheat', 'soybean', 'gold', 'gas', 'sp500',
    'fed', 'rate', 'inflation', 'gdp', 'employment', 'dollar'
]

missing_features = []
for feature in critical_features:
    found = any(feature in col.lower() for col in all_columns)
    if not found:
        missing_features.append(feature)
        print(f"  ✗ MISSING: {feature.upper()}")

if not missing_features:
    print("  ✓ All critical features appear to be included")
else:
    print(f"\n  TOTAL MISSING: {len(missing_features)} critical feature categories")

print("\n" + "="*80)
print("TRAINING DATASET AUDIT COMPLETE")
print("="*80)
