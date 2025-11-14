#!/usr/bin/env python3
"""
Quick pull of Yahoo Finance data for technical indicators and related commodities
Pulls maximum data possible from Yahoo Finance API
"""
import yfinance as yf
from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import time

PROJECT_ID = "cbi-v14"
DATASET_ID = "market_data"

client = bigquery.Client(project=PROJECT_ID)

print("="*70)
print("🚀 FAST YAHOO FINANCE DATA PULL")
print("="*70)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Maximum symbols we can pull
SYMBOLS = {
    # Main targets
    'soybean_oil': 'ZL=F',
    'soybeans': 'ZS=F',
    'corn': 'ZC=F',
    'soybean_meal': 'ZM=F',
    'wheat': 'ZW=F',
    
    # Related commodities
    'crude_oil': 'CL=F',
    'crude_brent': 'BZ=F',
    'natural_gas': 'NG=F',
    'heating_oil': 'HO=F',
    'gasoline': 'RB=F',
    'palm_oil_futures': 'FCPO=F',  # If available
    
    # Grains
    'rice': 'ZR=F',
    'oats': 'ZO=F',
    
    # Soft commodities
    'sugar': 'SB=F',
    'coffee': 'KC=F',
    'cotton': 'CT=F',
    'cocoa': 'CC=F',
    
    # Metals (affect USD/inflation)
    'gold': 'GC=F',
    'silver': 'SI=F',
    'copper': 'HG=F',
    
    # Currencies (DXY components)
    'dxy': 'DX-Y.NYB',  # USD Index
    'eurusd': 'EURUSD=X',
    'gbpusd': 'GBPUSD=X',
    'usdjpy': 'JPY=X',
    'usdcad': 'CAD=X',
    
    # Stock indices (market sentiment)
    'sp500': '^GSPC',
    'dow': '^DJI',
    'nasdaq': '^IXIC',
    
    # Bonds (rates)
    '10y_treasury': '^TNX',
    '30y_treasury': '^TYX',
    '3m_treasury': '^IRX',
    
    # VIX (volatility)
    'vix': '^VIX',
    
    # Agriculture ETFs (proxy for sector sentiment)
    'dba': 'DBA',  # Agriculture ETF
    'corn_etf': 'CORN',  # Teucrium Corn Fund
}

def calculate_technical_indicators(df, price_col='Close'):
    """Calculate RSI, MACD, Bollinger Bands quickly"""
    if price_col not in df.columns or len(df) < 26:
        return df
    
    # RSI (14-day)
    delta = df[price_col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # MACD (12, 26, 9)
    ema_12 = df[price_col].ewm(span=12, adjust=False).mean()
    ema_26 = df[price_col].ewm(span=26, adjust=False).mean()
    df['macd_line'] = ema_12 - ema_26
    df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
    df['macd_histogram'] = df['macd_line'] - df['macd_signal']
    
    # Bollinger Bands (20-day, 2 std)
    df['bb_middle'] = df[price_col].rolling(window=20).mean()
    bb_std = df[price_col].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (2 * bb_std)
    df['bb_lower'] = df['bb_middle'] - (2 * bb_std)
    df['bb_percent'] = (df[price_col] - df['bb_middle']) / bb_std
    
    # Additional indicators
    # Moving Averages
    df['ma_7'] = df[price_col].rolling(window=7).mean()
    df['ma_30'] = df[price_col].rolling(window=30).mean()
    df['ma_90'] = df[price_col].rolling(window=90).mean()
    
    # Returns
    df['return_1d'] = df[price_col].pct_change(1)
    df['return_7d'] = df[price_col].pct_change(7)
    df['return_30d'] = df[price_col].pct_change(30)
    
    # Volatility
    df['volatility_7d'] = df['return_1d'].rolling(window=7).std()
    df['volatility_30d'] = df['return_1d'].rolling(window=30).std()
    
    return df

def pull_symbol(symbol, name, start_date='2020-01-01'):
    """Pull data for a single symbol"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, interval='1d')
        
        if hist.empty:
            print(f"  ⚠️  {name} ({symbol}): No data")
            return None
        
        # Calculate technical indicators
        hist = calculate_technical_indicators(hist, 'Close')
        
        # Add metadata
        hist['symbol'] = symbol
        hist['name'] = name
        hist['date'] = hist.index.date
        hist.reset_index(inplace=True)
        
        # Select columns
        cols = ['date', 'symbol', 'name', 'Open', 'High', 'Low', 'Close', 'Volume']
        tech_cols = ['rsi_14', 'macd_line', 'macd_signal', 'macd_histogram', 
                     'bb_middle', 'bb_upper', 'bb_lower', 'bb_percent',
                     'ma_7', 'ma_30', 'ma_90', 'return_1d', 'return_7d', 'return_30d',
                     'volatility_7d', 'volatility_30d']
        
        result = hist[[col for col in cols + tech_cols if col in hist.columns]]
        result['pulled_at'] = datetime.now()
        
        print(f"  ✅ {name}: {len(result)} rows, {datetime.now().strftime('%H:%M:%S')}")
        return result
        
    except Exception as e:
        print(f"  ❌ {name} ({symbol}): {str(e)[:50]}")
        return None

def save_to_bigquery(df_list, table_name='yahoo_finance_enhanced'):
    """Save all data to BigQuery"""
    if not df_list or all(d is None for d in df_list):
        print("\n❌ No data to save")
        return
    
    # Combine all dataframes
    df = pd.concat([d for d in df_list if d is not None], ignore_index=True)
    
    if df.empty:
        print("\n❌ Empty dataframe")
        return
    
    print(f"\n💾 Saving {len(df):,} rows to BigQuery...")
    
    # Prepare for BigQuery
    table_ref = client.dataset(DATASET_ID).table(table_name)
    
    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_TRUNCATE',  # Replace table
        schema=[
            bigquery.SchemaField('date', 'DATE'),
            bigquery.SchemaField('symbol', 'STRING'),
            bigquery.SchemaField('name', 'STRING'),
            bigquery.SchemaField('Open', 'FLOAT64'),
            bigquery.SchemaField('High', 'FLOAT64'),
            bigquery.SchemaField('Low', 'FLOAT64'),
            bigquery.SchemaField('Close', 'FLOAT64'),
            bigquery.SchemaField('Volume', 'INT64'),
            bigquery.SchemaField('rsi_14', 'FLOAT64'),
            bigquery.SchemaField('macd_line', 'FLOAT64'),
            bigquery.SchemaField('macd_signal', 'FLOAT64'),
            bigquery.SchemaField('macd_histogram', 'FLOAT64'),
            bigquery.SchemaField('bb_middle', 'FLOAT64'),
            bigquery.SchemaField('bb_upper', 'FLOAT64'),
            bigquery.SchemaField('bb_lower', 'FLOAT64'),
            bigquery.SchemaField('bb_percent', 'FLOAT64'),
            bigquery.SchemaField('ma_7', 'FLOAT64'),
            bigquery.SchemaField('ma_30', 'FLOAT64'),
            bigquery.SchemaField('ma_90', 'FLOAT64'),
            bigquery.SchemaField('return_1d', 'FLOAT64'),
            bigquery.SchemaField('return_7d', 'FLOAT64'),
            bigquery.SchemaField('return_30d', 'FLOAT64'),
            bigquery.SchemaField('volatility_7d', 'FLOAT64'),
            bigquery.SchemaField('volatility_30d', 'FLOAT64'),
            bigquery.SchemaField('pulled_at', 'TIMESTAMP'),
        ]
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()  # Wait for completion
        print(f"✅ Saved to {PROJECT_ID}.{DATASET_ID}.{table_name}")
        print(f"   Rows: {len(df):,}")
        print(f"   Symbols: {df['symbol'].nunique()}")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    except Exception as e:
        print(f"❌ Error saving: {e}")

def main():
    print(f"\n📊 Pulling {len(SYMBOLS)} symbols from Yahoo Finance...")
    print("   Calculating technical indicators (RSI, MACD, Bollinger Bands)...")
    
    start_time = time.time()
    
    # Pull all symbols in parallel for speed
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(pull_symbol, symbol, name)
            for name, symbol in SYMBOLS.items()
        ]
        results = [f.result() for f in futures]
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Pulled in {elapsed:.1f} seconds")
    
    # Save to BigQuery
    save_to_bigquery(results)
    
    print("\n" + "="*70)
    print("✅ COMPLETE")
    print("="*70)
    print(f"Next: Integrate into training_dataset_super_enriched")
    print(f"Table: {PROJECT_ID}.{DATASET_ID}.yahoo_finance_enhanced")

if __name__ == "__main__":
    main()









