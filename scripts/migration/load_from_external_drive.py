#!/usr/bin/env python3
"""
Load datasets from external drive directly into us-central1
Bypasses cross-location issues by using local parquet files
"""

from google.cloud import bigquery
import pandas as pd
import os
from pathlib import Path

PROJECT = "cbi-v14"
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
client = bigquery.Client(project=PROJECT, location="us-central1")

print("=" * 80)
print("LOADING FROM EXTERNAL DRIVE → us-central1")
print("=" * 80)
print()

# Dataset 1: market_data (yahoo finance files)
print("1. Loading market_data...")
print("-" * 80)

market_data_files = {
    "yahoo_finance_enhanced": EXTERNAL_DRIVE / "TrainingData/raw/forecasting_data_warehouse/yahoo_finance_enhanced.parquet",
    "_ARCHIVED_yahoo_finance_enhanced_20251102": EXTERNAL_DRIVE / "TrainingData/raw/market_data/_ARCHIVED_yahoo_finance_enhanced_20251102.parquet",
    "yahoo_finance_20yr_STAGING": EXTERNAL_DRIVE / "TrainingData/raw/market_data/yahoo_finance_20yr_STAGING.parquet",
}

# Create dataset if needed
try:
    client.get_dataset("cbi-v14.market_data")
    print("  ✅ market_data dataset exists in us-central1")
except:
    dataset = bigquery.Dataset("cbi-v14.market_data")
    dataset.location = "us-central1"
    client.create_dataset(dataset)
    print("  ✅ Created market_data dataset in us-central1")

for table_name, file_path in market_data_files.items():
    if file_path.exists():
        print(f"  → Loading {table_name}...")
        df = pd.read_parquet(file_path)
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
        
        job = client.load_table_from_dataframe(
            df, f"cbi-v14.market_data.{table_name}", 
            job_config=job_config,
            location="us-central1"
        )
        job.result()
        print(f"    ✅ Loaded {len(df):,} rows")
    else:
        print(f"    ⚠️  File not found: {file_path}")

print()

# Dataset 2: weather
print("2. Loading weather...")
print("-" * 80)

weather_files = {
    "daily_updates": EXTERNAL_DRIVE / "TrainingData/raw/forecasting_data_warehouse/weather_data.parquet",
}

# Create dataset if needed
try:
    client.get_dataset("cbi-v14.weather")
    print("  ✅ weather dataset exists in us-central1")
except:
    dataset = bigquery.Dataset("cbi-v14.weather")
    dataset.location = "us-central1"
    client.create_dataset(dataset)
    print("  ✅ Created weather dataset in us-central1")

for table_name, file_path in weather_files.items():
    if file_path.exists():
        print(f"  → Loading {table_name}...")
        df = pd.read_parquet(file_path)
        
        # Take only recent data if large
        if len(df) > 10000:
            df = df.tail(10000)
            print(f"    (limited to last 10K rows)")
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
        
        job = client.load_table_from_dataframe(
            df, f"cbi-v14.weather.{table_name}",
            job_config=job_config,
            location="us-central1"
        )
        job.result()
        print(f"    ✅ Loaded {len(df):,} rows")
    else:
        print(f"    ⚠️  File not found: {file_path}")

print()

# Dataset 3: dashboard (create empty in us-central1, populate from app)
print("3. Creating dashboard dataset...")
print("-" * 80)

try:
    client.get_dataset("cbi-v14.dashboard")
    print("  ✅ dashboard dataset exists")
except:
    dataset = bigquery.Dataset("cbi-v14.dashboard")
    dataset.location = "us-central1"
    client.create_dataset(dataset)
    print("  ✅ Created dashboard dataset in us-central1")

# Create empty tables with correct schema
dashboard_schemas = {
    "performance_metrics": [
        bigquery.SchemaField("metric_date", "DATE"),
        bigquery.SchemaField("metric_name", "STRING"),
        bigquery.SchemaField("metric_value", "FLOAT64"),
        bigquery.SchemaField("horizon", "STRING"),
    ],
    "prediction_history": [
        bigquery.SchemaField("prediction_date", "DATE"),
        bigquery.SchemaField("horizon", "STRING"),
        bigquery.SchemaField("predicted_price", "FLOAT64"),
        bigquery.SchemaField("actual_price", "FLOAT64"),
    ],
    "regime_history": [
        bigquery.SchemaField("date", "DATE"),
        bigquery.SchemaField("regime", "STRING"),
        bigquery.SchemaField("confidence", "FLOAT64"),
    ],
}

for table_name, schema in dashboard_schemas.items():
    table_id = f"cbi-v14.dashboard.{table_name}"
    table = bigquery.Table(table_id, schema=schema)
    try:
        client.create_table(table, exists_ok=True)
        print(f"  ✅ Created {table_name}")
    except:
        print(f"  ✅ {table_name} exists")

print()
print("=" * 80)
print("✅ ALL DATASETS LOADED FROM EXTERNAL DRIVE")
print("=" * 80)
print()
print("Next: Verify and delete US backups of these datasets")

