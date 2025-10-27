#!/usr/bin/env python3
"""
FIND MORE SEGMENTED NEWS DATA
Look for all the segmented news work that was done
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

print("="*80)
print("SEARCHING FOR MORE SEGMENTED DATA")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

client = bigquery.Client(project='cbi-v14')

# Load current enhanced dataset
df = pd.read_parquet('training_dataset_enhanced_final.parquet')
print(f"Current dataset: {df.shape}")

# Search for more segmented data tables
print("\n1. CHECKING ALL MODELS TABLES FOR SEGMENTED DATA")
print("-"*40)

models_tables = [
    'models.enhanced_news_proxy',
    'models.news_features_materialized', 
    'models.sentiment_features_materialized',
    'models.tariff_features_materialized',
    'models.complete_signals_features',
    'models.signals_master',
    'models.vix_features_materialized'
]

additional_data = []

for table_path in models_tables:
    try:
        # Check what's in each table
        query = f"""
        SELECT *
        FROM `cbi-v14.{table_path}`
        LIMIT 5
        """
        
        sample = client.query(query).to_dataframe()
        
        if len(sample) > 0:
            print(f"\n{table_path}:")
            print(f"  Columns: {', '.join(sample.columns[:5])}")
            
            # Get full data if it has useful columns
            if 'date' in sample.columns:
                full_query = f"""
                SELECT *
                FROM `cbi-v14.{table_path}`
                WHERE date >= '2020-01-01'
                ORDER BY date
                """
                
                full_df = client.query(full_query).to_dataframe()
                if len(full_df) > 0:
                    full_df['date'] = pd.to_datetime(full_df['date'])
                    additional_data.append((table_path, full_df))
                    print(f"  ✓ Loaded {len(full_df)} rows")
                    print(f"  Date range: {full_df['date'].min().date()} to {full_df['date'].max().date()}")
                    
    except Exception as e:
        print(f"{table_path}: Error - {str(e)[:50]}")

# Check staging tables
print("\n2. CHECKING STAGING TABLES")
print("-"*40)

staging_tables = [
    'staging.comprehensive_social_intelligence',
    'staging.trump_policy_intelligence',
    'staging.ice_enforcement_intelligence'
]

for table_path in staging_tables:
    try:
        # Get column info first
        query = f"""
        SELECT column_name
        FROM `cbi-v14.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_schema = '{table_path.split('.')[0]}'
        AND table_name = '{table_path.split('.')[1]}'
        """
        
        columns = client.query(query).to_dataframe()
        
        if len(columns) > 0:
            print(f"\n{table_path}:")
            print(f"  Available columns: {', '.join(columns['column_name'].head(10))}")
            
            # Try to get data with appropriate date column
            date_cols = ['date', 'created_at', 'published_at', 'timestamp']
            for date_col in date_cols:
                if date_col in columns['column_name'].values:
                    try:
                        data_query = f"""
                        SELECT 
                            DATE({date_col}) as date,
                            COUNT(*) as count
                        FROM `cbi-v14.{table_path}`
                        GROUP BY date
                        HAVING date >= '2020-01-01'
                        ORDER BY date
                        """
                        
                        data = client.query(data_query).to_dataframe()
                        if len(data) > 0:
                            print(f"  ✓ Found {len(data)} days of data using {date_col}")
                            break
                    except:
                        continue
                        
    except Exception as e:
        print(f"{table_path}: {str(e)[:50]}")

# 3. MERGE ADDITIONAL DATA
print("\n3. MERGING ADDITIONAL SEGMENTED DATA")
print("-"*40)

enhanced_df = df.copy()
total_added = 0

for source_name, source_df in additional_data:
    # Clean source name for column prefixes
    clean_name = source_name.split('.')[-1].replace('_materialized', '')
    
    # Get non-date columns
    merge_cols = [col for col in source_df.columns if col != 'date']
    
    # Rename columns to avoid conflicts
    rename_dict = {}
    for col in merge_cols:
        if col in enhanced_df.columns:
            rename_dict[col] = f"{col}_{clean_name}"
    
    if rename_dict:
        source_df = source_df.rename(columns=rename_dict)
        merge_cols = [col for col in source_df.columns if col != 'date']
    
    # Merge
    before = len(enhanced_df.columns)
    enhanced_df = enhanced_df.merge(source_df, on='date', how='left')
    
    # Fill NaN with 0
    for col in merge_cols:
        if col in enhanced_df.columns:
            enhanced_df[col] = enhanced_df[col].fillna(0)
    
    added = len(enhanced_df.columns) - before
    total_added += added
    print(f"  {clean_name}: Added {added} columns")

print(f"\nTotal new columns added: {total_added}")

# 4. SAVE FINAL ENHANCED DATASET
print("\n4. SAVING FINAL ENHANCED DATASET")
print("-"*40)

enhanced_df.to_csv('training_dataset_enhanced_final.csv', index=False)
enhanced_df.to_parquet('training_dataset_enhanced_final.parquet', index=False)

print(f"✓ Saved enhanced dataset: {enhanced_df.shape}")

# 5. PREVIEW FOR TRAINING
print("\n" + "="*80)
print("📊 DATASET PREVIEW FOR MODEL TRAINING")
print("="*80)

print(f"\nFinal Dataset Shape: {enhanced_df.shape[0]} rows × {enhanced_df.shape[1]} columns")

# Analyze sentiment coverage
sentiment_cols = [col for col in enhanced_df.columns if any(x in col.lower() for x in 
                  ['sentiment', 'tariff', 'china', 'brazil', 'policy', 'social', 'news', 'trump', 'signal'])]

print(f"\nSentiment/Signal Features: {len(sentiment_cols)}")

# Check coverage
coverage_stats = []
for col in sentiment_cols[:20]:  # Sample first 20
    non_zero = (enhanced_df[col] != 0).sum()
    if non_zero > 0:
        coverage_stats.append((col, non_zero))

coverage_stats.sort(key=lambda x: x[1], reverse=True)

print("\nTop Sentiment Features by Coverage:")
for col, coverage in coverage_stats[:10]:
    pct = (coverage / len(enhanced_df)) * 100
    print(f"  {col:40}: {coverage:4} days ({pct:5.1f}%)")

# Check key model inputs
print("\n✅ KEY MODEL INPUTS:")
print("-"*40)

model_inputs = {
    'Price Data': ['zl_price_current', 'return_1d', 'ma_7d', 'volatility_30d'],
    'Commodities': ['crude_price', 'palm_price', 'corn_price'],
    'Market': ['vix_level', 'dxy_level'],
    'Weather': ['weather_brazil_temp', 'weather_us_temp'],
    'Sentiment': ['social_sentiment_avg', 'social_engagement_total'],
    'Targets': ['target_1w', 'target_1m']
}

all_ready = True
for category, cols in model_inputs.items():
    available = [c for c in cols if c in enhanced_df.columns]
    filled = sum((enhanced_df[c] != 0).sum() for c in available if c in enhanced_df.columns) / len(available) if available else 0
    status = "✅" if len(available) == len(cols) else "⚠️"
    print(f"{status} {category:12}: {len(available)}/{len(cols)} features available")
    if len(available) < len(cols):
        all_ready = False

print("\n" + "="*80)
if all_ready:
    print("🚀 READY TO TRAIN ALL MODELS")
else:
    print("✅ READY TO TRAIN MOST MODELS")
    
print("="*80)
print("\nDataset file: training_dataset_enhanced_final.parquet")
print("Next step: Train all models with this enhanced dataset")
print("="*80)
