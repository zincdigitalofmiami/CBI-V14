#!/usr/bin/env python3
"""
Migrate soybean_oil_prices from forecasting_data_warehouse (us-central1) 
to raw_intelligence.commodity_soybean_oil_prices (US)
Handles cross-location migration properly using pandas.
"""

from google.cloud import bigquery
import pandas as pd
import os

PROJECT = os.getenv("PROJECT", "cbi-v14")

# Source is in us-central1
source_client = bigquery.Client(project=PROJECT, location="us-central1")
# Destination is in US  
dest_client = bigquery.Client(project=PROJECT, location="US")

print("=" * 80)
print("CROSS-LOCATION MIGRATION: soybean_oil_prices")
print("=" * 80)
print(f"Source: forecasting_data_warehouse.soybean_oil_prices (us-central1)")
print(f"Destination: raw_intelligence.commodity_soybean_oil_prices (US)")
print()

# Step 1: Read from source into pandas
print("Step 1: Reading from source...")
source_query = """
SELECT 
  CAST(time AS DATE) AS time,
  symbol,
  CAST(open AS FLOAT64) AS open,
  CAST(high AS FLOAT64) AS high,
  CAST(low AS FLOAT64) AS low,
  close,
  CAST(volume AS INT64) AS volume,
  source_name,
  confidence_score,
  ingest_timestamp_utc,
  provenance_uuid
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
WHERE symbol = 'ZL'
ORDER BY time
"""

df = source_client.query(source_query, location="us-central1").to_dataframe()
print(f"✅ Read {len(df):,} rows from source")
print()

# Step 2: Create destination table schema
print("Step 2: Creating destination table...")
dest_table_id = "cbi-v14.raw_intelligence.commodity_soybean_oil_prices"

schema = [
    bigquery.SchemaField("time", "DATE"),
    bigquery.SchemaField("symbol", "STRING"),
    bigquery.SchemaField("open", "FLOAT64"),
    bigquery.SchemaField("high", "FLOAT64"),
    bigquery.SchemaField("low", "FLOAT64"),
    bigquery.SchemaField("close", "FLOAT64"),
    bigquery.SchemaField("volume", "INT64"),
    bigquery.SchemaField("source_name", "STRING"),
    bigquery.SchemaField("confidence_score", "FLOAT64"),
    bigquery.SchemaField("ingest_timestamp_utc", "TIMESTAMP"),
    bigquery.SchemaField("provenance_uuid", "STRING"),
]

table = bigquery.Table(dest_table_id, schema=schema)
# Note: Not partitioning by DATE to avoid too many partitions
# Can add monthly partitioning later if needed
table.clustering_fields = ["symbol"]

try:
    table = dest_client.create_table(table, exists_ok=True)
    print(f"✅ Created table: {dest_table_id}")
except Exception as e:
    print(f"⚠️  Table may already exist: {e}")
    table = dest_client.get_table(dest_table_id)
    print(f"✅ Using existing table: {dest_table_id}")

print()

# Step 3: Write data using load job
print("Step 3: Writing data to destination...")
load_job_config = bigquery.LoadJobConfig(
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    schema=schema,
    # Note: Not partitioning to avoid too many partitions (4000 limit)
    # Can add monthly partitioning later: time_partitioning=bigquery.TimePartitioning(field="time", type_=bigquery.TimePartitioningType.MONTH),
    clustering_fields=["symbol"],
)

load_job = dest_client.load_table_from_dataframe(
    df, dest_table_id, job_config=load_job_config, location="US"
)
load_job.result()

print(f"✅ Wrote {load_job.output_rows:,} rows to destination")
print()

# Step 4: Verify
print("Step 4: Verifying migration...")
verify_query = f"""
SELECT 
  COUNT(*) as row_count,
  MIN(time) as min_date,
  MAX(time) as max_date,
  COUNT(DISTINCT symbol) as symbol_count
FROM `{dest_table_id}`
"""

verify_job = dest_client.query(verify_query, location="US")
verify_results = verify_job.result()
for row in verify_results:
    print(f"✅ Verification:")
    print(f"   Rows: {row.row_count:,}")
    print(f"   Date range: {row.min_date} to {row.max_date}")
    print(f"   Symbols: {row.symbol_count}")

print()
print("=" * 80)
print("✅ MIGRATION COMPLETE")
print("=" * 80)

