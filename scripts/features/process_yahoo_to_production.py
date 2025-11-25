#!/usr/bin/env python3
"""
Process Yahoo Finance Data and Integrate to Production
Safely maps Yahoo data (245K rows) to production_training_data_* tables

KEY CONSTRAINTS:
- Production tables: cbi-v14.models_v4.production_training_data_1w/1m/3m/6m
- Location: us-central1
- Schema: 300 columns (must preserve all)
- Models: bqml_1w/1m/3m/6m (DO NOT RENAME!)
"""

import pandas as pd
import pickle
from pathlib import Path
from google.cloud import bigquery
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
CACHE_DIR = Path('/Users/zincdigital/CBI-V14/cache/yahoo_finance')

# CRITICAL: Column name mapping (Yahoo → Production)
COLUMN_MAPPING = {
    # Moving averages (Yahoo uses ma_7, Production uses ma_7d)
    'ma_7d': 'ma_7d',           # Already matches
    'ma_30d': 'ma_30d',         # Already matches
    'ma_50d': 'ma_50d',         # NEW - add to production
    'ma_90d': 'ma_90d',         # Already matches
    'ma_100d': 'ma_100d',       # NEW - add to production
    'ma_200d': 'ma_200d',       # NEW - add to production
    
    # Technical indicators (already match)
    'rsi_14': 'rsi_14',
    'macd_line': 'macd_line',
    'macd_signal': 'macd_signal',
    'macd_histogram': 'macd_histogram',
    
    # Bollinger Bands (NEW - add to production)
    'bb_upper': 'bb_upper',
    'bb_middle': 'bb_middle',
    'bb_lower': 'bb_lower',
    'bb_width': 'bb_width',
    'bb_percent': 'bb_percent',
    
    # ATR (NEW - add to production)
    'atr_14': 'atr_14',
    
    # Volatility (already exist in production)
    'volatility_7d': 'volatility_7d',
    'volatility_30d': 'volatility_30d',
    'volatility_90d': 'volatility_90d',  # NEW
    
    # Returns (already exist)
    'return_1d': 'return_1d',
    'return_7d': 'return_7d',
    'return_30d': 'return_30d',
    
    # Momentum (NEW)
    'price_momentum_7d': 'price_momentum_7d',
    'price_momentum_30d': 'price_momentum_30d',
    'price_vs_ma30': 'price_vs_ma30',
    'price_vs_ma200': 'price_vs_ma200',
    'ma50_vs_ma200': 'ma50_vs_ma200',
    'is_golden_cross': 'is_golden_cross',
}

# Symbol mapping for crush margin calculation
SYMBOL_MAPPING = {
    'ZL=F': {
        'clean': 'ZL',
        'production_col_price': 'zl_price_current',
        'production_col_volume': 'zl_volume',
        'crush_component': 'oil_price_per_cwt',  # ZL price → oil_price_per_cwt
        'conversion': lambda x: x  # Already in cents/lb, but need to verify units
    },
    'ZS=F': {
        'clean': 'ZS',
        'production_col_price': 'soybean_price',  # May need to add this column
        'crush_component': 'bean_price_per_bushel',
        'conversion': lambda x: x / 100  # cents/bushel → dollars/bushel
    },
    'ZM=F': {
        'clean': 'ZM',
        'production_col_price': 'soybean_meal_price',
        'crush_component': 'meal_price_per_ton',
        'conversion': lambda x: x / 100  # cents/ton → dollars/ton
    },
    'ZC=F': {
        'clean': 'ZC',
        'production_col_price': 'corn_price',
        'conversion': None
    },
    'ZW=F': {
        'clean': 'ZW',
        'production_col_price': 'wheat_price',
        'conversion': None
    },
}

def load_all_cached_data():
    """Load all cached Yahoo Finance data"""
    logger.info("="*70)
    logger.info("LOADING CACHED YAHOO FINANCE DATA")
    logger.info("="*70)
    
    all_data = []
    cache_files = list(CACHE_DIR.glob("*_2000-01-01.pkl"))
    
    logger.info(f"Found {len(cache_files)} cache files")
    
    for cache_file in sorted(cache_files):
        try:
            with open(cache_file, 'rb') as f:
                df = pickle.load(f)
                symbol = df['symbol'].iloc[0] if 'symbol' in df.columns else cache_file.stem.split('_')[0]
                logger.info(f"  ✅ {symbol}: {len(df):,} rows loaded from cache")
                all_data.append(df)
        except Exception as e:
            logger.error(f"  ❌ Error loading {cache_file.name}: {e}")
    
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        logger.info(f"\n📊 Total cached data: {len(combined):,} rows")
        logger.info(f"   Symbols: {combined['symbol'].nunique()}")
        logger.info(f"   Date range: {combined['date'].min()} to {combined['date'].max()}")
        return combined
    else:
        logger.error("❌ No cached data found")
        return None

def save_to_bigquery_us_central1(df, table_name='yahoo_finance_comprehensive'):
    """
    Save to BigQuery in us-central1 location (same as production tables)
    """
    client = bigquery.Client(project=PROJECT_ID)
    dataset_id = 'yahoo_finance_comprehensive'
    table_id = f"{PROJECT_ID}.{dataset_id}.{table_name}"
    
    logger.info(f"\n💾 Saving to BigQuery (us-central1): {table_id}")
    logger.info(f"   Rows to save: {len(df):,}")
    
    # Prepare schema with metadata
    schema = [
        bigquery.SchemaField('date', 'DATE', description='Trading date'),
        bigquery.SchemaField('symbol', 'STRING', description='Yahoo Finance symbol (e.g., ZL=F)'),
        bigquery.SchemaField('symbol_clean', 'STRING', description='Clean symbol (e.g., ZL)'),
        bigquery.SchemaField('name', 'STRING', description='Asset name'),
        
        # OHLCV
        bigquery.SchemaField('Open', 'FLOAT64', description='Opening price'),
        bigquery.SchemaField('High', 'FLOAT64', description='High price'),
        bigquery.SchemaField('Low', 'FLOAT64', description='Low price'),
        bigquery.SchemaField('Close', 'FLOAT64', description='Closing price'),
        bigquery.SchemaField('Volume', 'INT64', description='Trading volume'),
        
        # Moving Averages (6 timeframes)
        bigquery.SchemaField('ma_7d', 'FLOAT64', description='7-day simple moving average'),
        bigquery.SchemaField('ma_30d', 'FLOAT64', description='30-day simple moving average'),
        bigquery.SchemaField('ma_50d', 'FLOAT64', description='50-day simple moving average'),
        bigquery.SchemaField('ma_90d', 'FLOAT64', description='90-day simple moving average'),
        bigquery.SchemaField('ma_100d', 'FLOAT64', description='100-day simple moving average'),
        bigquery.SchemaField('ma_200d', 'FLOAT64', description='200-day simple moving average'),
        
        # RSI & MACD (proper calculations)
        bigquery.SchemaField('rsi_14', 'FLOAT64', description='14-period RSI (Wilders method via EWM)'),
        bigquery.SchemaField('macd_line', 'FLOAT64', description='MACD line (12-period EMA - 26-period EMA)'),
        bigquery.SchemaField('macd_signal', 'FLOAT64', description='MACD signal (9-period EMA of MACD line)'),
        bigquery.SchemaField('macd_histogram', 'FLOAT64', description='MACD histogram (MACD line - signal)'),
        
        # Bollinger Bands
        bigquery.SchemaField('bb_middle', 'FLOAT64', description='Bollinger middle band (20-day SMA)'),
        bigquery.SchemaField('bb_upper', 'FLOAT64', description='Bollinger upper band (middle + 2*std)'),
        bigquery.SchemaField('bb_lower', 'FLOAT64', description='Bollinger lower band (middle - 2*std)'),
        bigquery.SchemaField('bb_width', 'FLOAT64', description='Bollinger band width (upper-lower)/middle'),
        bigquery.SchemaField('bb_percent', 'FLOAT64', description='Price position within bands'),
        
        # ATR
        bigquery.SchemaField('atr_14', 'FLOAT64', description='14-period Average True Range'),
        
        # Returns
        bigquery.SchemaField('return_1d', 'FLOAT64', description='1-day return (pct change)'),
        bigquery.SchemaField('return_7d', 'FLOAT64', description='7-day return (pct change)'),
        bigquery.SchemaField('return_30d', 'FLOAT64', description='30-day return (pct change)'),
        
        # Volatility
        bigquery.SchemaField('volatility_7d', 'FLOAT64', description='7-day realized volatility (std of returns)'),
        bigquery.SchemaField('volatility_30d', 'FLOAT64', description='30-day realized volatility'),
        bigquery.SchemaField('volatility_90d', 'FLOAT64', description='90-day realized volatility'),
        
        # Momentum indicators
        bigquery.SchemaField('price_momentum_7d', 'FLOAT64', description='7-day price momentum'),
        bigquery.SchemaField('price_momentum_30d', 'FLOAT64', description='30-day price momentum'),
        bigquery.SchemaField('price_vs_ma30', 'FLOAT64', description='Price relative to 30-day MA'),
        bigquery.SchemaField('price_vs_ma200', 'FLOAT64', description='Price relative to 200-day MA'),
        bigquery.SchemaField('ma50_vs_ma200', 'FLOAT64', description='50-day MA vs 200-day MA (golden/death cross)'),
        bigquery.SchemaField('is_golden_cross', 'INT64', description='1 if golden cross (50>200), 0 otherwise'),
        
        # Metadata (CRITICAL for neural network training)
        bigquery.SchemaField('pulled_at', 'TIMESTAMP', description='Timestamp when data was pulled from Yahoo'),
        bigquery.SchemaField('data_source', 'STRING', description='Data source attribution'),
        bigquery.SchemaField('calculation_method', 'STRING', description='Technical indicator calculation method'),
    ]
    
    # Add metadata columns
    df['data_source'] = 'Yahoo Finance (yfinance library)'
    df['calculation_method'] = 'EMA-based MACD, Wilders RSI, SMA moving averages'
    
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition='WRITE_TRUNCATE',
    )
    
    try:
        # Select only columns that exist in df and match schema
        schema_cols = [field.name for field in schema]
        df_to_save = df[[col for col in schema_cols if col in df.columns]]
        
        job = client.load_table_from_dataframe(df_to_save, table_id, job_config=job_config)
        job.result()
        
        logger.info(f"✅ Saved to {table_id}")
        logger.info(f"   Rows: {len(df_to_save):,}")
        logger.info(f"   Columns: {len(df_to_save.columns)}")
        logger.info(f"   Date range: {df_to_save['date'].min()} to {df_to_save['date'].max()}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving to BigQuery: {e}")
        return False

def main():
    logger.info("\n" + "="*70)
    logger.info("YAHOO FINANCE → PRODUCTION INTEGRATION")
    logger.info("="*70)
    
    # Load all cached data
    df = load_all_cached_data()
    
    if df is not None:
        # Save to BigQuery in us-central1
        success = save_to_bigquery_us_central1(df, table_name='all_symbols_20yr')
        
        if success:
            logger.info("\n✅ Yahoo data ready in us-central1")
            logger.info("   Next: Map to production_training_data_* tables")
        else:
            logger.error("\n❌ Failed to save to BigQuery")
    
if __name__ == "__main__":
    main()








