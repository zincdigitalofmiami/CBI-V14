#!/usr/bin/env python3
"""
Volatility Data Ingestion (NO SIGNALS)
Extracts volatility metrics only, ignores buy/sell signals
"""

import pandas as pd
from google.cloud import bigquery
from pathlib import Path
from datetime import datetime

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"
TABLE_ID = "volatility_data"

def process_volatility_csv(file_path):
    """Process volatility CSV, extract metrics only (no signals)"""
    df = pd.read_csv(file_path)
    
    # Extract only volatility columns, skip all signals
    df_clean = df[['Symbol', 'Name', 'Last', 'IV/HV', 'Imp Vol']].copy()
    
    # Clean column names
    df_clean = df_clean.rename(columns={
        'Symbol': 'symbol',
        'Name': 'contract',
        'Last': 'last_price',
        'IV/HV': 'iv_hv_ratio',
        'Imp Vol': 'implied_vol'
    })
    
    # Convert implied vol from percentage string to float
    df_clean['implied_vol'] = df_clean['implied_vol'].str.replace('%', '').astype(float)
    
    # Add data date
    df_clean['data_date'] = datetime.now().date()
    
    return df_clean

def load_to_bigquery(df):
    """Load volatility data to BigQuery"""
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    schema = [
        bigquery.SchemaField("symbol", "STRING"),
        bigquery.SchemaField("contract", "STRING"),
        bigquery.SchemaField("last_price", "FLOAT64"),
        bigquery.SchemaField("iv_hv_ratio", "FLOAT64"),
        bigquery.SchemaField("implied_vol", "FLOAT64"),
        bigquery.SchemaField("data_date", "DATE"),
    ]
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema=schema,
    )
    
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()
    
    print(f"Loaded {len(df)} volatility records (no signals)")

def main():
    vol_file = Path("/Users/zincdigital/CBI-V14/data/csv/historical-prices-10-03-2025.csv")
    if vol_file.exists():
        df = process_volatility_csv(vol_file)
        load_to_bigquery(df)
        print(f"Volatility data: {len(df)} contracts loaded")
    else:
        print("No volatility file found")

if __name__ == "__main__":
    main()
