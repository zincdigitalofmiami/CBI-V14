#!/usr/bin/env python3
"""
Create and load BigQuery regime_calendar table from parquet files.
Part of regime infrastructure setup (pre-backfill).
"""

import pandas as pd
from google.cloud import bigquery
from pathlib import Path
from datetime import datetime

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")

def create_regime_table(client: bigquery.Client):
    """Create the regime_calendar table in BigQuery."""
    
    ddl = """
    CREATE TABLE IF NOT EXISTS features.regime_calendar (
        date DATE,
        regime STRING,
        training_weight INT64,
        regime_start_date DATE,
        regime_end_date DATE,
        regime_description STRING,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    ) CLUSTER BY date, regime
    """
    
    client.query(ddl, location=LOCATION).result()
    print("✓ Created features.regime_calendar table")

def load_regime_data(client: bigquery.Client):
    """Load regime data from parquet files."""
    
    # Load regime calendar (date-level assignments with weights already included)
    calendar_df = pd.read_parquet(DRIVE / "registry/regime_calendar.parquet")
    
    # Load regime weights (regime-level metadata)
    weights_df = pd.read_parquet(DRIVE / "registry/regime_weights.parquet")
    
    # Join to get metadata (start_date, end_date, description)
    merged_df = calendar_df.merge(
        weights_df[['regime', 'start_date', 'end_date', 'description']],
        on='regime',
        how='left'
    )
    
    # Rename columns to match BigQuery schema
    merged_df = merged_df.rename(columns={
        'start_date': 'regime_start_date',
        'end_date': 'regime_end_date',
        'description': 'regime_description'
    })
    
    # Ensure correct data types
    merged_df['date'] = pd.to_datetime(merged_df['date']).dt.date
    merged_df['regime_start_date'] = pd.to_datetime(merged_df['regime_start_date']).dt.date
    merged_df['regime_end_date'] = pd.to_datetime(merged_df['regime_end_date']).dt.date
    merged_df['training_weight'] = merged_df['training_weight'].astype('int64')
    
    # Select final columns
    final_df = merged_df[[
        'date', 'regime', 'training_weight', 
        'regime_start_date', 'regime_end_date', 'regime_description'
    ]].copy()
    
    print(f"\nPrepared {len(final_df)} rows for upload")
    print(f"Date range: {final_df['date'].min()} to {final_df['date'].max()}")
    print(f"Unique regimes: {final_df['regime'].nunique()}")
    
    # Upload to BigQuery
    table_id = f"{PROJECT_ID}.features.regime_calendar"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Replace existing data
        schema=[
            bigquery.SchemaField("date", "DATE"),
            bigquery.SchemaField("regime", "STRING"),
            bigquery.SchemaField("training_weight", "INTEGER"),
            bigquery.SchemaField("regime_start_date", "DATE"),
            bigquery.SchemaField("regime_end_date", "DATE"),
            bigquery.SchemaField("regime_description", "STRING"),
        ]
    )
    
    load_job = client.load_table_from_dataframe(
        final_df, table_id, job_config=job_config, location=LOCATION
    )
    load_job.result()  # Wait for completion
    
    print(f"✓ Loaded {len(final_df)} rows to features.regime_calendar")
    
    return final_df

def verify_regime_table(client: bigquery.Client):
    """Verify the regime table was created and loaded correctly."""
    
    query = """
    SELECT 
        COUNT(*) as total_rows,
        MIN(date) as min_date,
        MAX(date) as max_date,
        COUNT(DISTINCT regime) as unique_regimes,
        MIN(training_weight) as min_weight,
        MAX(training_weight) as max_weight
    FROM features.regime_calendar
    """
    
    result = client.query(query, location=LOCATION).result()
    row = list(result)[0]
    
    print("\n" + "="*60)
    print("REGIME TABLE VERIFICATION")
    print("="*60)
    print(f"Total rows: {row.total_rows}")
    print(f"Date range: {row.min_date} to {row.max_date}")
    print(f"Unique regimes: {row.unique_regimes}")
    print(f"Weight range: {row.min_weight} to {row.max_weight}")
    
    # Show regime distribution
    query2 = """
    SELECT 
        regime,
        training_weight,
        COUNT(*) as days,
        MIN(date) as start_date,
        MAX(date) as end_date
    FROM features.regime_calendar
    GROUP BY regime, training_weight
    ORDER BY training_weight DESC, start_date
    """
    
    print("\nRegime Distribution:")
    result2 = client.query(query2, location=LOCATION).result()
    for row in result2:
        print(f"  {row.regime:40s} weight={row.training_weight:4d} days={row.days:5d} ({row.start_date} to {row.end_date})")
    
    # Verify expected row count
    expected_rows = 9497
    if row.total_rows == expected_rows:
        print(f"\n✓ Row count matches expected: {expected_rows}")
    else:
        print(f"\n⚠ Row count mismatch: {row.total_rows} (expected {expected_rows})")
    
    # Verify weight range
    if row.min_weight >= 50 and row.max_weight <= 1000:
        print(f"✓ Weight range valid: {row.min_weight}-{row.max_weight} (50-1000 scale)")
    else:
        print(f"⚠ Weight range invalid: {row.min_weight}-{row.max_weight} (expected 50-1000)")

def main():
    """Create and load regime_calendar table."""
    
    print("\n" + "="*60)
    print("CREATE BIGQUERY REGIME TABLE")
    print("="*60)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Step 1: Create table
    print("\n1. Creating table...")
    create_regime_table(client)
    
    # Step 2: Load data
    print("\n2. Loading data...")
    load_regime_data(client)
    
    # Step 3: Verify
    print("\n3. Verifying...")
    verify_regime_table(client)
    
    print("\n" + "="*60)
    print("✓ REGIME TABLE READY")
    print("="*60)
    print("\nNext steps:")
    print("1. Generate missing staging files (USDA, CFTC)")
    print("2. Add palm/crude to yahoo staging")
    print("3. QA all staging files")
    print("4. Proceed to Week 0 Day 4 backfill")
    
    return 0

if __name__ == "__main__":
    exit(main())

