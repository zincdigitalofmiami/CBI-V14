#!/usr/bin/env python3
import pandas as pd
from google.cloud import bigquery
from pathlib import Path

csv_files = list(Path("/Users/zincdigital/CBI-V14/data/csv").glob("*price-history*.csv"))
if not csv_files:
    print("No CSV files found")
    exit(1)

SYMBOL_MAP = {
    'ZLZ25': 'ZL', 'ZSX25': 'ZS', 'ZMZ25': 'ZM', 'ZCZ25': 'ZC',
    'ZNZ25': 'ZN', 'CCZ25': 'CC', 'CTZ25': 'CT', 'FLX25': 'FL'
}

client = bigquery.Client(project="cbi-v14")
schema = [
    bigquery.SchemaField("time", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("open", "FLOAT64"),
    bigquery.SchemaField("high", "FLOAT64"),
    bigquery.SchemaField("low", "FLOAT64"),
    bigquery.SchemaField("close", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("volume", "INT64"),
]

total_rows = 0
for csv_file in csv_files:
    df = pd.read_csv(csv_file)
    df = df[~df['Time'].astype(str).str.contains('Downloaded', na=False)]
    df = df.rename(columns={'Time': 'time', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Last': 'close', 'Volume': 'volume'})
    df['time'] = pd.to_datetime(df['time'], errors='coerce')
    df = df.dropna(subset=['time', 'close'])
    
    contract = csv_file.stem.split('_')[0].upper().split(' ')[0]
    df['symbol'] = SYMBOL_MAP.get(contract, contract[:2])
    
    df = df[['time', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
    df['volume'] = df['volume'].fillna(0).astype('int64')
    
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND", schema=schema)
    job = client.load_table_from_dataframe(df, "cbi-v14.forecasting_data_warehouse.commodity_prices", job_config=job_config)
    job.result()
    
    print(f"{df['symbol'].iloc[0]}: {len(df)} rows loaded")
    total_rows += len(df)

print(f"\nTotal: {total_rows} rows")
