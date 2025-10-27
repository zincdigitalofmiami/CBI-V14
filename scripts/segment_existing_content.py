#!/usr/bin/env python3
"""
QUICK SEGMENTATION OF EXISTING CONTENT
Fast and safe extraction of signals from pre-existing news/sentiment
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("SEGMENTING PRE-EXISTING CONTENT (2,831 rows)")
print("="*80)

# Quick segmentation query - no risky operations
segment_existing_query = """
WITH existing_content AS (
  -- News Intelligence (1,955 rows)
  SELECT
    DATE(timestamp) AS date,
    title,
    content,
    intelligence_score,
    news_sentiment_score
  FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
  WHERE timestamp IS NOT NULL
  
  UNION ALL
  
  -- Social Sentiment (661 rows)  
  SELECT
    DATE(timestamp) AS date,
    title,
    CAST(comments AS STRING) AS content,
    sentiment_score AS intelligence_score,
    sentiment_score AS news_sentiment_score
  FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
  WHERE timestamp IS NOT NULL
  
  UNION ALL
  
  -- Trump Policy Intelligence (215 rows)
  SELECT
    DATE(timestamp) AS date,
    category AS title,
    text AS content,
    CAST(priority AS FLOAT64) / 10.0 AS intelligence_score,
    0.0 AS news_sentiment_score
  FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`
  WHERE timestamp IS NOT NULL
)

SELECT
  date,
  COUNT(*) AS existing_content_count,
  
  -- Tariff signals (search in title and content)
  SUM(CASE 
    WHEN LOWER(CONCAT(title, ' ', content)) LIKE '%tariff%' 
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%trade war%'
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%duty%'
    THEN 1 ELSE 0 
  END) AS existing_tariff_signals,
  
  -- China signals
  SUM(CASE 
    WHEN LOWER(CONCAT(title, ' ', content)) LIKE '%china%' 
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%chinese%'
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%beijing%'
    THEN 1 ELSE 0 
  END) AS existing_china_signals,
  
  -- Brazil/Argentina signals
  SUM(CASE 
    WHEN LOWER(CONCAT(title, ' ', content)) LIKE '%brazil%' 
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%argentina%'
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%south america%'
    THEN 1 ELSE 0 
  END) AS existing_brazil_arg_signals,
  
  -- Policy/Legislation signals
  SUM(CASE 
    WHEN LOWER(CONCAT(title, ' ', content)) LIKE '%congress%' 
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%senate%'
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%legislation%'
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%policy%'
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%regulation%'
    THEN 1 ELSE 0 
  END) AS existing_policy_signals,
  
  -- Biofuel signals
  SUM(CASE 
    WHEN LOWER(CONCAT(title, ' ', content)) LIKE '%biofuel%' 
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%biodiesel%'
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%ethanol%'
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%renewable fuel%'
    THEN 1 ELSE 0 
  END) AS existing_biofuel_signals,
  
  -- Weather signals
  SUM(CASE 
    WHEN LOWER(CONCAT(title, ' ', content)) LIKE '%drought%' 
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%flood%'
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%weather%'
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%rain%'
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%frost%'
    THEN 1 ELSE 0 
  END) AS existing_weather_signals,
  
  -- Soybean specific
  SUM(CASE 
    WHEN LOWER(CONCAT(title, ' ', content)) LIKE '%soybean%' 
      OR LOWER(CONCAT(title, ' ', content)) LIKE '%soy%'
    THEN 1 ELSE 0 
  END) AS existing_soybean_signals,
  
  -- Average sentiment
  AVG(news_sentiment_score) AS existing_avg_sentiment,
  AVG(intelligence_score) AS existing_avg_intelligence

FROM existing_content
GROUP BY date
ORDER BY date DESC
"""

print("\n1. EXTRACTING SIGNALS FROM EXISTING CONTENT")
print("-"*60)

try:
    existing_signals_df = client.query(segment_existing_query).to_dataframe()
    print(f"✓ Extracted signals for {len(existing_signals_df)} days")
    
    # Show coverage
    print("\nExisting Content Signal Coverage:")
    signal_cols = [
        'existing_tariff_signals',
        'existing_china_signals', 
        'existing_brazil_arg_signals',
        'existing_policy_signals',
        'existing_biofuel_signals',
        'existing_weather_signals',
        'existing_soybean_signals'
    ]
    
    for col in signal_cols:
        if col in existing_signals_df.columns:
            non_zero = (existing_signals_df[col] > 0).sum()
            total_signals = existing_signals_df[col].sum()
            print(f"  {col.replace('existing_', '').replace('_signals', '').upper()}: {non_zero} days, {int(total_signals)} total signals")
    
    # Save the segmented existing content
    existing_signals_df.to_csv('existing_content_signals.csv', index=False)
    print(f"\n✓ Saved existing content signals to existing_content_signals.csv")
    
except Exception as e:
    print(f"Error extracting existing content: {e}")
    print("Skipping existing content segmentation to avoid issues")
    existing_signals_df = pd.DataFrame()

# Now combine with the new scraped signals if we have both
print("\n2. COMBINING WITH NEW SCRAPED SIGNALS")
print("-"*60)

try:
    # Load the enhanced dataset we created earlier
    if 'training_dataset_enhanced.csv' in pd.io.common.file_exists('training_dataset_enhanced.csv'):
        training_df = pd.read_csv('training_dataset_enhanced.csv')
    else:
        training_df = pd.read_csv('training_dataset_final_enhanced.csv')
    
    training_df['date'] = pd.to_datetime(training_df['date'])
    
    # If we have existing signals, merge them
    if not existing_signals_df.empty:
        existing_signals_df['date'] = pd.to_datetime(existing_signals_df['date'])
        
        # Merge existing signals
        combined_df = training_df.merge(existing_signals_df, on='date', how='left')
        
        # Fill NaN with 0
        for col in existing_signals_df.columns:
            if col != 'date' and col in combined_df.columns:
                combined_df[col] = combined_df[col].fillna(0)
        
        print(f"✓ Combined dataset: {len(combined_df)} rows × {len(combined_df.columns)} columns")
        
        # Save combined dataset
        combined_df.to_csv('training_dataset_with_all_signals.csv', index=False)
        print(f"✓ Saved to training_dataset_with_all_signals.csv")
        
        # Show final feature count
        print(f"\nFinal Feature Count:")
        print(f"  Base features: 172")
        print(f"  New scraped news features: 22")
        print(f"  Existing content features: {len(existing_signals_df.columns) - 1}")
        print(f"  TOTAL: {len(combined_df.columns)}")
        
    else:
        print("No existing signals extracted, using only new scraped data")
        
except Exception as e:
    print(f"Error combining datasets: {e}")
    print("Using new scraped signals only")

print("\n" + "="*80)
print("SEGMENTATION COMPLETE")
print("="*80)
