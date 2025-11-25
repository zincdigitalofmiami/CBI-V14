#!/usr/bin/env python3
"""
Load raw biofuel component prices to BigQuery as independent features
These can be used both independently AND for RIN proxy calculations
"""

import pandas as pd
from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Load biofuel raw prices from cache"""
    logger.info("Loading biofuel component raw prices from cache...")
    
    # Load the combined file
    df = pd.read_csv('/Users/zincdigital/CBI-V14/cache/yahoo_finance_biofuel/all_biofuel_components.csv')
    df['Date'] = pd.to_datetime(df['Date'], utc=True)
    
    # Remove timezone for BigQuery compatibility
    df['Date'] = df['Date'].dt.tz_localize(None)
    df = df.rename(columns={'Date': 'date'})
    
    # Calculate technical indicators for each symbol
    logger.info("Calculating technical indicators for biofuel components...")
    
    results = []
    for symbol in df['symbol'].unique():
        symbol_df = df[df['symbol'] == symbol].copy().sort_values('date')
        
        # Technical indicators
        symbol_df['ma_7d'] = symbol_df['Close'].rolling(window=7).mean()
        symbol_df['ma_30d'] = symbol_df['Close'].rolling(window=30).mean()
        symbol_df['rsi_14'] = calculate_rsi(symbol_df['Close'], 14)
        
        results.append(symbol_df)
    
    combined = pd.concat(results, ignore_index=True)
    
    # Save to BigQuery
    client = bigquery.Client(project='cbi-v14')
    table_id = 'cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw'
    
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(combined, table_id, job_config=job_config)
    job.result()
    
    logger.info(f"✅ Saved {len(combined)} rows to {table_id}")
    logger.info(f"Symbols: {combined['symbol'].unique().tolist()}")
    logger.info(f"Date range: {combined['date'].min()} to {combined['date'].max()}")
    
def calculate_rsi(prices, period=14):
    """Calculate RSI using Wilder's method"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

if __name__ == "__main__":
    main()








