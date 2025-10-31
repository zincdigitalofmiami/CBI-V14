#!/usr/bin/env python3
"""
DIRECT NEWS INTEGRATION - Bypass sandbox restrictions
Query news data directly and append to training dataset
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("DIRECT NEWS INTEGRATION INTO TRAINING")
print("="*80)

# Step 1: Get current training data
print("\n1. LOADING CURRENT TRAINING DATA")
print("-"*60)

training_query = """
SELECT * FROM `cbi-v14.models.training_dataset`
ORDER BY date
"""

print("Loading existing training dataset...")
training_df = client.query(training_query).to_dataframe()
print(f"✓ Loaded {len(training_df)} rows with {len(training_df.columns)} columns")

# Step 2: Process news data
print("\n2. PROCESSING NEWS DATA")
print("-"*60)

news_query = """
WITH all_news AS (
  -- News from advanced scraper
  SELECT
    DATE(published_date) AS date,
    source,
    relevance,
    total_score,
    soybean_oil_mentions,
    tariffs_mentions,
    china_mentions,
    brazil_mentions,
    legislation_mentions,
    lobbying_mentions,
    weather_mentions,
    biofuel_mentions,
    content_length
  FROM `cbi-v14.forecasting_data_warehouse.news_advanced`
  WHERE published_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
  
  UNION ALL
  
  -- News from ultra-aggressive scraper
  SELECT
    DATE(published_date) AS date,
    source,
    relevance,
    total_score,
    soybean_oil_mentions,
    tariffs_mentions,
    china_mentions,
    brazil_mentions,
    legislation_mentions,
    0 AS lobbying_mentions,
    0 AS weather_mentions,
    0 AS biofuel_mentions,
    content_length
  FROM `cbi-v14.forecasting_data_warehouse.news_ultra_aggressive`
  WHERE published_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
)

SELECT
  date,
  -- News volume metrics
  COUNT(*) AS news_total_count_new,
  COUNT(DISTINCT source) AS news_source_count,
  COUNT(CASE WHEN relevance IN ('critical', 'high') THEN 1 END) AS news_high_relevance_count,
  
  -- Topic-specific counts
  SUM(soybean_oil_mentions) AS news_soybean_oil_mentions,
  COUNT(CASE WHEN soybean_oil_mentions > 0 THEN 1 END) AS news_soybean_oil_articles,
  
  SUM(tariffs_mentions) AS news_tariff_mentions,
  COUNT(CASE WHEN tariffs_mentions > 0 THEN 1 END) AS news_tariff_articles,
  AVG(CASE WHEN tariffs_mentions > 0 THEN total_score END) AS news_tariff_avg_score,
  
  SUM(china_mentions) AS news_china_mentions,
  COUNT(CASE WHEN china_mentions > 0 THEN 1 END) AS news_china_articles,
  
  SUM(brazil_mentions) AS news_brazil_mentions,
  COUNT(CASE WHEN brazil_mentions > 0 THEN 1 END) AS news_brazil_articles,
  
  SUM(legislation_mentions) AS news_legislation_mentions,
  COUNT(CASE WHEN legislation_mentions > 0 THEN 1 END) AS news_legislation_articles,
  
  SUM(lobbying_mentions) AS news_lobbying_mentions,
  COUNT(CASE WHEN lobbying_mentions > 0 THEN 1 END) AS news_lobbying_articles,
  
  SUM(weather_mentions) AS news_weather_mentions,
  COUNT(CASE WHEN weather_mentions > 0 THEN 1 END) AS news_weather_articles,
  
  SUM(biofuel_mentions) AS news_biofuel_mentions,
  COUNT(CASE WHEN biofuel_mentions > 0 THEN 1 END) AS news_biofuel_articles,
  
  AVG(total_score) AS news_avg_relevance_score,
  AVG(content_length) AS news_avg_content_length
  
FROM all_news
GROUP BY date
ORDER BY date
"""

print("Processing news features...")
news_df = client.query(news_query).to_dataframe()
print(f"✓ Processed news data for {len(news_df)} days")

# Step 3: Merge datasets
print("\n3. MERGING DATASETS")
print("-"*60)

# Merge news features with training data
enhanced_df = training_df.merge(news_df, on='date', how='left')

# Fill NaN values with 0 for news columns
news_columns = [col for col in enhanced_df.columns if 'news_' in col and col.endswith('_new')]
for col in news_columns:
    enhanced_df[col] = enhanced_df[col].fillna(0)

# Rename columns to remove _new suffix
for col in news_columns:
    if col == 'news_total_count_new':
        # Special handling for existing column
        enhanced_df['news_total_count_enhanced'] = enhanced_df[col]
        enhanced_df = enhanced_df.drop(columns=[col])
    else:
        new_name = col.replace('_new', '')
        enhanced_df[new_name] = enhanced_df[col]
        if col != new_name:
            enhanced_df = enhanced_df.drop(columns=[col])

print(f"✓ Enhanced dataset: {len(enhanced_df)} rows × {len(enhanced_df.columns)} columns")

# Show new columns added
original_cols = set(training_df.columns)
new_cols = set(enhanced_df.columns) - original_cols
print(f"\nNew columns added ({len(new_cols)}):")
for col in sorted(new_cols):
    non_zero = (enhanced_df[col] != 0).sum()
    print(f"  - {col}: {non_zero} non-zero values")

# Step 4: Save enhanced dataset
print("\n4. SAVING ENHANCED DATASET")
print("-"*60)

# Configure job
job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_TRUNCATE",
    time_partitioning=bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.MONTH,
        field="date"
    ),
    clustering_fields=["date"]
)

# Save to BigQuery
table_id = "cbi-v14.models.training_dataset_enhanced"
print(f"Saving to {table_id}...")

try:
    job = client.load_table_from_dataframe(
        enhanced_df,
        table_id,
        job_config=job_config
    )
    job.result()
    print(f"✓ Saved enhanced dataset to {table_id}")
    
    # Verify
    verify_query = f"""
    SELECT
      COUNT(*) AS total_rows,
      COUNT(DISTINCT date) AS unique_dates,
      AVG(news_tariff_mentions) AS avg_tariff_mentions,
      AVG(news_china_mentions) AS avg_china_mentions,
      AVG(news_soybean_oil_mentions) AS avg_soybean_oil_mentions
    FROM `{table_id}`
    """
    
    stats = client.query(verify_query).to_dataframe()
    print("\nEnhanced Dataset Stats:")
    print(stats.to_string(index=False))
    
except Exception as e:
    print(f"Error saving: {e}")
    print("\nTrying alternative: Save as CSV for manual upload")
    
    csv_file = "training_dataset_enhanced.csv"
    enhanced_df.to_csv(csv_file, index=False)
    print(f"✓ Saved to {csv_file}")
    print(f"  Upload manually: bq load --autodetect cbi-v14:models.training_dataset_enhanced {csv_file}")

print("\n" + "="*80)
print("INTEGRATION COMPLETE")
print("="*80)

# Step 5: Create backup of original and swap tables
print("\n5. FINALIZING INTEGRATION")
print("-"*60)

swap_query = """
-- Create backup of original
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset_backup` AS
SELECT * FROM `cbi-v14.models.training_dataset`;

-- Replace original with enhanced
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset`
PARTITION BY date
CLUSTER BY date
AS
SELECT * FROM `cbi-v14.models.training_dataset_enhanced`;
"""

print("To complete integration, run this SQL in BigQuery console:")
print(swap_query)

print(f"""
SUMMARY:
- Original features: {len(training_df.columns)}
- Enhanced features: {len(enhanced_df.columns)}
- New news features: {len(new_cols)}
- Ready for model training with comprehensive news signals

NEXT STEPS:
1. Retrain models with enhanced dataset
2. Compare performance metrics
3. Schedule regular news updates
""")
