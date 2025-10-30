#!/usr/bin/env python3
"""
SEGMENT NEWS INTO SPECIALIZED SIGNALS
Create dedicated feature channels for each weak area
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("SEGMENTING NEWS INTO SPECIALIZED SIGNALS")
print("="*80)

# Step 1: Extract and segment news by topic
print("\n1. EXTRACTING NEWS BY TOPIC AREA")
print("-"*60)

segment_query = """
WITH news_combined AS (
  SELECT
    DATE(published_date) AS date,
    source,
    title,
    full_content,
    relevance,
    total_score,
    soybean_oil_mentions,
    tariffs_mentions,
    china_mentions,
    brazil_mentions,
    legislation_mentions,
    lobbying_mentions,
    weather_mentions,
    biofuel_mentions
  FROM `cbi-v14.forecasting_data_warehouse.news_advanced`
  
  UNION ALL
  
  SELECT
    DATE(published_date) AS date,
    source,
    title,
    full_content,
    relevance,
    total_score,
    soybean_oil_mentions,
    tariffs_mentions,
    china_mentions,
    brazil_mentions,
    legislation_mentions,
    0 AS lobbying_mentions,
    0 AS weather_mentions,
    0 AS biofuel_mentions
  FROM `cbi-v14.forecasting_data_warehouse.news_ultra_aggressive`
),

-- TARIFF/TRADE WAR SIGNAL
tariff_signal AS (
  SELECT
    date,
    COUNT(*) AS tariff_article_count,
    SUM(tariffs_mentions) AS tariff_total_mentions,
    AVG(total_score) AS tariff_avg_relevance,
    MAX(total_score) AS tariff_max_relevance,
    -- Weighted signal: more mentions = stronger signal
    SUM(tariffs_mentions * total_score) / NULLIF(SUM(tariffs_mentions), 0) AS tariff_weighted_score,
    -- Momentum: increasing mentions = positive momentum
    SUM(tariffs_mentions) - LAG(SUM(tariffs_mentions), 1) OVER (ORDER BY date) AS tariff_momentum
  FROM news_combined
  WHERE tariffs_mentions > 0
  GROUP BY date
),

-- CHINA TRADE SIGNAL
china_signal AS (
  SELECT
    date,
    COUNT(*) AS china_article_count,
    SUM(china_mentions) AS china_total_mentions,
    AVG(total_score) AS china_avg_relevance,
    SUM(china_mentions * total_score) / NULLIF(SUM(china_mentions), 0) AS china_weighted_score,
    -- China purchase signals (look for keywords in content)
    SUM(CASE 
      WHEN LOWER(full_content) LIKE '%china%' AND LOWER(full_content) LIKE '%purchase%' THEN 1 
      ELSE 0 
    END) AS china_purchase_signals,
    SUM(CASE 
      WHEN LOWER(full_content) LIKE '%china%' AND LOWER(full_content) LIKE '%cancel%' THEN 1 
      ELSE 0 
    END) AS china_cancellation_signals
  FROM news_combined
  WHERE china_mentions > 0
  GROUP BY date
),

-- BRAZIL/ARGENTINA SIGNAL
brazil_arg_signal AS (
  SELECT
    date,
    COUNT(*) AS brazil_article_count,
    SUM(brazil_mentions) AS brazil_total_mentions,
    AVG(total_score) AS brazil_avg_relevance,
    -- Harvest signals
    SUM(CASE 
      WHEN LOWER(full_content) LIKE '%brazil%' AND LOWER(full_content) LIKE '%harvest%' THEN 1 
      ELSE 0 
    END) AS brazil_harvest_signals,
    SUM(CASE 
      WHEN LOWER(full_content) LIKE '%argentina%' AND LOWER(full_content) LIKE '%harvest%' THEN 1 
      ELSE 0 
    END) AS argentina_harvest_signals,
    -- Weather impact
    SUM(CASE 
      WHEN (LOWER(full_content) LIKE '%brazil%' OR LOWER(full_content) LIKE '%argentina%') 
        AND (LOWER(full_content) LIKE '%drought%' OR LOWER(full_content) LIKE '%flood%') THEN 1 
      ELSE 0 
    END) AS south_america_weather_impact
  FROM news_combined
  WHERE brazil_mentions > 0 OR LOWER(full_content) LIKE '%argentina%'
  GROUP BY date
),

-- LEGISLATION/POLICY SIGNAL
policy_signal AS (
  SELECT
    date,
    COUNT(*) AS policy_article_count,
    SUM(legislation_mentions + lobbying_mentions) AS policy_total_mentions,
    AVG(total_score) AS policy_avg_relevance,
    SUM((legislation_mentions + lobbying_mentions) * total_score) / 
      NULLIF(SUM(legislation_mentions + lobbying_mentions), 0) AS policy_weighted_score,
    -- Policy change momentum
    SUM(legislation_mentions + lobbying_mentions) - 
      LAG(SUM(legislation_mentions + lobbying_mentions), 1) OVER (ORDER BY date) AS policy_momentum
  FROM news_combined
  WHERE legislation_mentions > 0 OR lobbying_mentions > 0
  GROUP BY date
),

-- BIOFUEL DEMAND SIGNAL
biofuel_signal AS (
  SELECT
    date,
    COUNT(*) AS biofuel_article_count,
    SUM(biofuel_mentions) AS biofuel_total_mentions,
    AVG(total_score) AS biofuel_avg_relevance,
    -- RFS/mandate signals
    SUM(CASE 
      WHEN LOWER(full_content) LIKE '%rfs%' OR LOWER(full_content) LIKE '%renewable fuel%' THEN 1 
      ELSE 0 
    END) AS rfs_signals,
    SUM(CASE 
      WHEN LOWER(full_content) LIKE '%biodiesel%' AND LOWER(full_content) LIKE '%demand%' THEN 1 
      ELSE 0 
    END) AS biodiesel_demand_signals
  FROM news_combined
  WHERE biofuel_mentions > 0 OR LOWER(full_content) LIKE '%biodiesel%' OR LOWER(full_content) LIKE '%ethanol%'
  GROUP BY date
),

-- WEATHER IMPACT SIGNAL
weather_signal AS (
  SELECT
    date,
    COUNT(*) AS weather_article_count,
    SUM(weather_mentions) AS weather_total_mentions,
    AVG(total_score) AS weather_avg_relevance,
    -- Specific weather events
    SUM(CASE WHEN LOWER(full_content) LIKE '%drought%' THEN 1 ELSE 0 END) AS drought_signals,
    SUM(CASE WHEN LOWER(full_content) LIKE '%flood%' THEN 1 ELSE 0 END) AS flood_signals,
    SUM(CASE WHEN LOWER(full_content) LIKE '%frost%' THEN 1 ELSE 0 END) AS frost_signals,
    -- Regional weather
    SUM(CASE 
      WHEN LOWER(full_content) LIKE '%midwest%' AND weather_mentions > 0 THEN 1 
      ELSE 0 
    END) AS midwest_weather_signals
  FROM news_combined
  WHERE weather_mentions > 0
  GROUP BY date
)

-- COMBINE ALL SIGNALS
SELECT
  COALESCE(t.date, c.date, b.date, p.date, bf.date, w.date) AS date,
  
  -- Tariff signals
  COALESCE(t.tariff_article_count, 0) AS tariff_article_count,
  COALESCE(t.tariff_total_mentions, 0) AS tariff_total_mentions,
  COALESCE(t.tariff_weighted_score, 0) AS tariff_weighted_score,
  COALESCE(t.tariff_momentum, 0) AS tariff_momentum,
  
  -- China signals
  COALESCE(c.china_article_count, 0) AS china_article_count,
  COALESCE(c.china_total_mentions, 0) AS china_total_mentions,
  COALESCE(c.china_weighted_score, 0) AS china_weighted_score,
  COALESCE(c.china_purchase_signals, 0) AS china_purchase_signals,
  COALESCE(c.china_cancellation_signals, 0) AS china_cancellation_signals,
  
  -- Brazil/Argentina signals
  COALESCE(b.brazil_article_count, 0) AS brazil_article_count,
  COALESCE(b.brazil_harvest_signals, 0) AS brazil_harvest_signals,
  COALESCE(b.argentina_harvest_signals, 0) AS argentina_harvest_signals,
  COALESCE(b.south_america_weather_impact, 0) AS south_america_weather_impact,
  
  -- Policy signals
  COALESCE(p.policy_article_count, 0) AS policy_article_count,
  COALESCE(p.policy_total_mentions, 0) AS policy_total_mentions,
  COALESCE(p.policy_weighted_score, 0) AS policy_weighted_score,
  COALESCE(p.policy_momentum, 0) AS policy_momentum,
  
  -- Biofuel signals
  COALESCE(bf.biofuel_article_count, 0) AS biofuel_article_count,
  COALESCE(bf.rfs_signals, 0) AS rfs_signals,
  COALESCE(bf.biodiesel_demand_signals, 0) AS biodiesel_demand_signals,
  
  -- Weather signals
  COALESCE(w.weather_article_count, 0) AS weather_article_count,
  COALESCE(w.drought_signals, 0) AS drought_signals,
  COALESCE(w.flood_signals, 0) AS flood_signals,
  COALESCE(w.frost_signals, 0) AS frost_signals,
  COALESCE(w.midwest_weather_signals, 0) AS midwest_weather_signals

FROM tariff_signal t
FULL OUTER JOIN china_signal c ON t.date = c.date
FULL OUTER JOIN brazil_arg_signal b ON COALESCE(t.date, c.date) = b.date
FULL OUTER JOIN policy_signal p ON COALESCE(t.date, c.date, b.date) = p.date
FULL OUTER JOIN biofuel_signal bf ON COALESCE(t.date, c.date, b.date, p.date) = bf.date
FULL OUTER JOIN weather_signal w ON COALESCE(t.date, c.date, b.date, p.date, bf.date) = w.date
ORDER BY date DESC
"""

print("Extracting segmented news signals...")
news_signals_df = client.query(segment_query).to_dataframe()
print(f"✓ Extracted signals for {len(news_signals_df)} days")

# Show signal coverage
print("\nSignal Coverage:")
for col in ['tariff', 'china', 'brazil', 'policy', 'biofuel', 'weather']:
    count_col = f'{col}_article_count'
    if count_col in news_signals_df.columns:
        non_zero = (news_signals_df[count_col] > 0).sum()
        print(f"  {col.upper()}: {non_zero} days with articles")

# Step 2: Load existing training data
print("\n2. LOADING TRAINING DATA")
print("-"*60)

# Load from CSV we saved earlier
training_df = pd.read_csv('training_dataset_enhanced.csv')
training_df['date'] = pd.to_datetime(training_df['date'])
print(f"✓ Loaded training data: {len(training_df)} rows × {len(training_df.columns)} columns")

# Step 3: Merge segmented signals
print("\n3. MERGING SEGMENTED SIGNALS")
print("-"*60)

# Convert date columns to same type
news_signals_df['date'] = pd.to_datetime(news_signals_df['date'])

# Merge news signals
final_df = training_df.merge(news_signals_df, on='date', how='left')

# Fill NaN with 0 for news columns
news_cols = [col for col in news_signals_df.columns if col != 'date']
for col in news_cols:
    if col in final_df.columns:
        final_df[col] = final_df[col].fillna(0)

print(f"✓ Final dataset: {len(final_df)} rows × {len(final_df.columns)} columns")

# Step 4: Save enhanced training dataset
print("\n4. SAVING ENHANCED TRAINING DATASET")
print("-"*60)

# Save to CSV
output_file = 'training_dataset_final_enhanced.csv'
final_df.to_csv(output_file, index=False)
print(f"✓ Saved to {output_file}")

# Show feature summary
print("\nFeature Summary:")
print(f"  Original features: {len(training_df.columns)}")
print(f"  News signal features: {len(news_cols)}")
print(f"  Total features: {len(final_df.columns)}")

print("\nNew Signal Features Added:")
signal_groups = {
    'Tariff/Trade War': ['tariff_article_count', 'tariff_total_mentions', 'tariff_weighted_score', 'tariff_momentum'],
    'China Trade': ['china_article_count', 'china_total_mentions', 'china_weighted_score', 'china_purchase_signals', 'china_cancellation_signals'],
    'Brazil/Argentina': ['brazil_article_count', 'brazil_harvest_signals', 'argentina_harvest_signals', 'south_america_weather_impact'],
    'Policy/Legislation': ['policy_article_count', 'policy_total_mentions', 'policy_weighted_score', 'policy_momentum'],
    'Biofuel': ['biofuel_article_count', 'rfs_signals', 'biodiesel_demand_signals'],
    'Weather': ['weather_article_count', 'drought_signals', 'flood_signals', 'frost_signals', 'midwest_weather_signals']
}

for group, features in signal_groups.items():
    print(f"\n  {group}:")
    for feat in features:
        if feat in final_df.columns:
            non_zero = (final_df[feat] != 0).sum()
            print(f"    - {feat}: {non_zero} non-zero values")

print("\n" + "="*80)
print("SEGMENTATION COMPLETE")
print("="*80)
print(f"""
✓ News segmented into 6 specialized signal channels
✓ 25+ new targeted features added
✓ Ready for enhanced model training
✓ Saved as: {output_file}

NEXT: Train models with these segmented signals
""")
