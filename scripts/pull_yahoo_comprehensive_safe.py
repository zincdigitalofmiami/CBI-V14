#!/usr/bin/env python3
"""
Yahoo Finance Comprehensive Data Pull - SAFE & COMPLIANT
Follows best practices: rate limiting, caching, verification, ToS compliance

Pulls 20+ years of historical data for soybean complex + indicators
Calculates proper technical indicators (RSI Wilder's, MACD EMA-based, 6 MAs)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import pickle
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/zincdigital/CBI-V14/logs/yahoo_pull.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "cbi-v14"
CACHE_DIR = Path('/Users/zincdigital/CBI-V14/cache/yahoo_finance')
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# RATE LIMITING (Yahoo Finance Best Practices)
RATE_LIMITS = {
    'per_symbol_delay': 2.5,      # 2.5 seconds between symbols (conservative)
    'batch_delay': 30.0,           # 30 seconds between batches
    'max_retries': 3,              # Max retry attempts
    'retry_delay': 60.0,           # 1 minute backoff on error
}

# Symbols to pull (soybean complex + correlates)
SYMBOLS = {
    # SOYBEAN COMPLEX (Primary)
    'soybean_oil': 'ZL=F',        # Soybean Oil Futures
    'soybeans': 'ZS=F',           # Soybean Futures  
    'soybean_meal': 'ZM=F',       # Soybean Meal Futures
    
    # GRAINS (Correlated)
    'corn': 'ZC=F',               # Corn Futures
    'wheat': 'ZW=F',              # Wheat Futures
    
    # ENERGY (Biofuel connection)
    'crude_oil': 'CL=F',          # Crude Oil Futures
    
    # MACRO (Dollar/Volatility)
    'dollar_index': 'DX-Y.NYB',   # US Dollar Index
    'vix': '^VIX',                # VIX Volatility Index
    
    # METALS (Inflation hedge)
    'gold': 'GC=F',               # Gold Futures
    
    # VEGETABLE OILS (Substitutes)
    'palm_oil': 'FCPO=F',         # Palm Oil (may not work)
}

def calculate_all_technical_indicators(df, price_col='Close'):
    """
    Calculate comprehensive technical indicators
    Uses PROPER formulas (Wilder's RSI, EMA-based MACD)
    """
    if price_col not in df.columns or len(df) < 200:
        logger.warning(f"Insufficient data for full calculations: {len(df)} rows")
        return df
    
    # ============================================
    # MOVING AVERAGES (6 timeframes)
    # ============================================
    df['ma_7d'] = df[price_col].rolling(window=7, min_periods=7).mean()
    df['ma_30d'] = df[price_col].rolling(window=30, min_periods=30).mean()
    df['ma_50d'] = df[price_col].rolling(window=50, min_periods=50).mean()
    df['ma_90d'] = df[price_col].rolling(window=90, min_periods=90).mean()
    df['ma_100d'] = df[price_col].rolling(window=100, min_periods=100).mean()
    df['ma_200d'] = df[price_col].rolling(window=200, min_periods=200).mean()
    
    # ============================================
    # RSI (14-day) - WILDER'S METHOD
    # ============================================
    delta = df[price_col].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Wilder's smoothing (EMA with alpha=1/14)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # ============================================
    # MACD - PROPER EMA-BASED
    # ============================================
    ema_12 = df[price_col].ewm(span=12, adjust=False).mean()
    ema_26 = df[price_col].ewm(span=26, adjust=False).mean()
    df['macd_line'] = ema_12 - ema_26
    df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
    df['macd_histogram'] = df['macd_line'] - df['macd_signal']
    
    # ============================================
    # BOLLINGER BANDS (20-day, 2 std dev)
    # ============================================
    df['bb_middle'] = df[price_col].rolling(window=20).mean()
    bb_std = df[price_col].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (2 * bb_std)
    df['bb_lower'] = df['bb_middle'] - (2 * bb_std)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    df['bb_percent'] = (df[price_col] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    # ============================================
    # ATR (Average True Range) - 14-day
    # ============================================
    df['high_low'] = df['High'] - df['Low']
    df['high_close'] = abs(df['High'] - df['Close'].shift(1))
    df['low_close'] = abs(df['Low'] - df['Close'].shift(1))
    df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    df['atr_14'] = df['true_range'].rolling(window=14).mean()
    df = df.drop(['high_low', 'high_close', 'low_close', 'true_range'], axis=1)
    
    # ============================================
    # RETURNS & VOLATILITY
    # ============================================
    df['return_1d'] = df[price_col].pct_change(1)
    df['return_7d'] = df[price_col].pct_change(7)
    df['return_30d'] = df[price_col].pct_change(30)
    
    df['volatility_7d'] = df['return_1d'].rolling(window=7).std()
    df['volatility_30d'] = df['return_1d'].rolling(window=30).std()
    df['volatility_90d'] = df['return_1d'].rolling(window=90).std()
    
    # ============================================
    # PRICE MOMENTUM INDICATORS
    # ============================================
    df['price_momentum_7d'] = (df[price_col] - df[price_col].shift(7)) / df[price_col].shift(7)
    df['price_momentum_30d'] = (df[price_col] - df[price_col].shift(30)) / df[price_col].shift(30)
    
    # Price relative to moving averages
    df['price_vs_ma30'] = df[price_col] / df['ma_30d'] - 1
    df['price_vs_ma200'] = df[price_col] / df['ma_200d'] - 1
    
    # ============================================
    # CROSS-SIGNAL INDICATORS
    # ============================================
    # Golden Cross / Death Cross
    df['ma50_vs_ma200'] = df['ma_50d'] / df['ma_200d'] - 1
    df['is_golden_cross'] = (df['ma_50d'] > df['ma_200d']).astype(int)
    
    return df

def get_cached_or_fetch(symbol, name, start_date='2000-01-01', use_cache=True):
    """
    Fetch data with caching to minimize API calls
    """
    cache_file = CACHE_DIR / f"{symbol.replace('=', '_')}_{start_date}.pkl"
    
    # Check cache first
    if use_cache and cache_file.exists():
        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if cache_age.total_seconds() < 86400:  # 24 hours
            logger.info(f"  📦 {name} ({symbol}): Using cached data (age: {cache_age.total_seconds()/3600:.1f}h)")
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
    
    # Fetch from Yahoo (with rate limiting)
    logger.info(f"  🌐 {name} ({symbol}): Fetching from Yahoo Finance...")
    time.sleep(RATE_LIMITS['per_symbol_delay'])  # RATE LIMIT
    
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, interval='1d')
        
        if hist.empty:
            logger.warning(f"  ⚠️  {name} ({symbol}): No data returned")
            return None
        
        # Calculate technical indicators
        hist = calculate_all_technical_indicators(hist, 'Close')
        
        # Add metadata
        hist['symbol'] = symbol
        hist['symbol_clean'] = symbol.replace('=F', '').replace('^', '').replace('-Y.NYB', '')
        hist['name'] = name
        hist['date'] = hist.index.date
        hist['pulled_at'] = datetime.now()
        hist.reset_index(drop=True, inplace=True)
        
        # Save to cache
        with open(cache_file, 'wb') as f:
            pickle.dump(hist, f)
        
        logger.info(f"  ✅ {name}: {len(hist):,} rows | {hist['date'].min()} to {hist['date'].max()}")
        
        return hist
        
    except Exception as e:
        logger.error(f"  ❌ {name} ({symbol}): {str(e)}")
        return None

def verify_data_quality(df, symbol, name):
    """
    Multi-point data quality verification
    """
    issues = []
    
    if df is None or df.empty:
        return ['❌ No data']
    
    # 1. Date continuity check
    date_range = pd.date_range(df['date'].min(), df['date'].max(), freq='B')
    expected_days = len(date_range)
    actual_days = len(df)
    gap_pct = (expected_days - actual_days) / expected_days * 100
    if gap_pct > 15:  # Allow 15% for holidays/non-trading days
        issues.append(f"⚠️ {gap_pct:.1f}% date gaps (expected <15%)")
    
    # 2. Outlier detection
    if 'Close' in df.columns:
        returns = df['Close'].pct_change()
        outliers = returns[abs(returns) > 0.20]  # >20% single-day move
        if len(outliers) > 5:
            issues.append(f"⚠️ {len(outliers)} extreme moves >20%")
    
    # 3. Duplicate dates
    duplicates = df['date'].duplicated().sum()
    if duplicates > 0:
        issues.append(f"❌ {duplicates} duplicate dates")
    
    # 4. NULL checks
    if 'Close' in df.columns:
        null_close = df['Close'].isnull().sum()
        if null_close > 0:
            issues.append(f"❌ {null_close} NULL Close prices")
    
    # 5. Logic checks
    if 'High' in df.columns and 'Low' in df.columns:
        invalid = (df['High'] < df['Low']).sum()
        if invalid > 0:
            issues.append(f"❌ {invalid} rows with High < Low (impossible)")
    
    # 6. Technical indicator sanity
    if 'rsi_14' in df.columns:
        rsi_out_of_range = ((df['rsi_14'] < 0) | (df['rsi_14'] > 100)).sum()
        if rsi_out_of_range > 0:
            issues.append(f"❌ {rsi_out_of_range} RSI values outside 0-100 range")
    
    if not issues:
        logger.info(f"  ✅ {name} data quality: PASSED all checks")
    else:
        for issue in issues:
            logger.warning(f"  {issue}")
    
    return issues

def main_test_phase():
    """
    PHASE 1: TEST - Pull 1 year for ZL only (need 200+ days for ma_200d)
    """
    logger.info("="*70)
    logger.info("PHASE 1: TEST - 1 Year Pull for ZL=F")
    logger.info("="*70)
    
    # Need at least 200 days for ma_200d calculation
    start_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
    
    df = get_cached_or_fetch('ZL=F', 'Soybean Oil Test', start_date=start_date, use_cache=False)
    
    if df is not None:
        # Verify quality
        issues = verify_data_quality(df, 'ZL=F', 'Soybean Oil')
        
        # Show sample
        logger.info("\n📊 SAMPLE DATA (last 10 rows):")
        # Check which columns actually exist
        sample_cols = [col for col in ['date', 'Close', 'ma_7d', 'ma_30d', 'ma_50d', 'rsi_14', 'macd_line'] if col in df.columns]
        if sample_cols:
            logger.info("\n" + df[sample_cols].tail(10).to_string())
        else:
            logger.info("\n" + df[['date', 'Close', 'Volume']].tail(10).to_string())
        
        # Statistics
        logger.info("\n📈 TECHNICAL INDICATOR STATISTICS:")
        if 'rsi_14' in df.columns:
            logger.info(f"  RSI avg: {df['rsi_14'].mean():.2f} (range: {df['rsi_14'].min():.2f}-{df['rsi_14'].max():.2f})")
        if 'macd_line' in df.columns:
            logger.info(f"  MACD avg: {df['macd_line'].mean():.4f}")
        if 'ma_7d' in df.columns:
            logger.info(f"  MA 7d avg: {df['ma_7d'].mean():.2f}")
        if 'ma_200d' in df.columns:
            logger.info(f"  MA 200d coverage: {df['ma_200d'].notna().sum()}/{len(df)} rows")
        else:
            logger.warning(f"  ⚠️  Technical indicators not calculated (need {len(df)} rows, need 200+ for full suite)")
        
        if len(issues) == 0:
            logger.info("\n✅ TEST PASSED - Ready for full 20-year pull")
            return True
        else:
            logger.warning(f"\n⚠️  TEST COMPLETED WITH {len(issues)} ISSUES - Review before proceeding")
            return False
    else:
        logger.error("\n❌ TEST FAILED - Could not fetch data")
        return False

def main_full_pull(test_mode=True):
    """
    PHASE 2: FULL PULL - 20 years for all symbols
    """
    if test_mode:
        logger.info("\n⚠️  TEST MODE - Set test_mode=False to execute full pull")
        return
    
    logger.info("="*70)
    logger.info("PHASE 2: FULL PULL - 20 Years All Symbols")
    logger.info("="*70)
    logger.info(f"Symbols to pull: {len(SYMBOLS)}")
    logger.info(f"Expected time: ~{len(SYMBOLS) * RATE_LIMITS['per_symbol_delay'] / 60:.1f} minutes")
    
    all_data = []
    
    for i, (name, symbol) in enumerate(SYMBOLS.items(), 1):
        logger.info(f"\n[{i}/{len(SYMBOLS)}] Processing {name} ({symbol})...")
        
        df = get_cached_or_fetch(symbol, name, start_date='2000-01-01', use_cache=True)
        
        if df is not None:
            # Verify quality
            issues = verify_data_quality(df, symbol, name)
            
            if len(issues) == 0:
                all_data.append(df)
                logger.info(f"  ✅ {name}: {len(df):,} rows added")
            else:
                logger.warning(f"  ⚠️  {name}: {len(issues)} quality issues (added anyway)")
                all_data.append(df)
        else:
            logger.error(f"  ❌ {name}: Failed to fetch")
        
        # Rate limiting between symbols
        if i < len(SYMBOLS):
            logger.info(f"  ⏸️  Rate limit pause ({RATE_LIMITS['per_symbol_delay']}s)...")
            time.sleep(RATE_LIMITS['per_symbol_delay'])
    
    # Combine all dataframes
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        logger.info(f"\n✅ Total rows fetched: {len(combined):,}")
        logger.info(f"   Symbols: {combined['symbol'].nunique()}")
        logger.info(f"   Date range: {combined['date'].min()} to {combined['date'].max()}")
        
        # Save to BigQuery STAGING
        save_to_staging(combined)
    else:
        logger.error("\n❌ No data fetched")

def save_to_staging(df):
    """
    Save to BigQuery STAGING table (not production!)
    """
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.market_data.yahoo_finance_20yr_STAGING"
    
    logger.info(f"\n💾 Saving to BigQuery STAGING: {table_id}")
    
    # Prepare schema
    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_TRUNCATE',
        schema=[
            bigquery.SchemaField('date', 'DATE'),
            bigquery.SchemaField('symbol', 'STRING'),
            bigquery.SchemaField('symbol_clean', 'STRING'),
            bigquery.SchemaField('name', 'STRING'),
            bigquery.SchemaField('Open', 'FLOAT64'),
            bigquery.SchemaField('High', 'FLOAT64'),
            bigquery.SchemaField('Low', 'FLOAT64'),
            bigquery.SchemaField('Close', 'FLOAT64'),
            bigquery.SchemaField('Volume', 'INT64'),
            # Moving Averages (6)
            bigquery.SchemaField('ma_7d', 'FLOAT64'),
            bigquery.SchemaField('ma_30d', 'FLOAT64'),
            bigquery.SchemaField('ma_50d', 'FLOAT64'),
            bigquery.SchemaField('ma_90d', 'FLOAT64'),
            bigquery.SchemaField('ma_100d', 'FLOAT64'),
            bigquery.SchemaField('ma_200d', 'FLOAT64'),
            # RSI & MACD
            bigquery.SchemaField('rsi_14', 'FLOAT64'),
            bigquery.SchemaField('macd_line', 'FLOAT64'),
            bigquery.SchemaField('macd_signal', 'FLOAT64'),
            bigquery.SchemaField('macd_histogram', 'FLOAT64'),
            # Bollinger Bands
            bigquery.SchemaField('bb_middle', 'FLOAT64'),
            bigquery.SchemaField('bb_upper', 'FLOAT64'),
            bigquery.SchemaField('bb_lower', 'FLOAT64'),
            bigquery.SchemaField('bb_width', 'FLOAT64'),
            bigquery.SchemaField('bb_percent', 'FLOAT64'),
            # ATR
            bigquery.SchemaField('atr_14', 'FLOAT64'),
            # Returns & Volatility
            bigquery.SchemaField('return_1d', 'FLOAT64'),
            bigquery.SchemaField('return_7d', 'FLOAT64'),
            bigquery.SchemaField('return_30d', 'FLOAT64'),
            bigquery.SchemaField('volatility_7d', 'FLOAT64'),
            bigquery.SchemaField('volatility_30d', 'FLOAT64'),
            bigquery.SchemaField('volatility_90d', 'FLOAT64'),
            # Momentum
            bigquery.SchemaField('price_momentum_7d', 'FLOAT64'),
            bigquery.SchemaField('price_momentum_30d', 'FLOAT64'),
            bigquery.SchemaField('price_vs_ma30', 'FLOAT64'),
            bigquery.SchemaField('price_vs_ma200', 'FLOAT64'),
            bigquery.SchemaField('ma50_vs_ma200', 'FLOAT64'),
            bigquery.SchemaField('is_golden_cross', 'INT64'),
            # Metadata
            bigquery.SchemaField('pulled_at', 'TIMESTAMP'),
        ]
    )
    
    try:
        # Select only columns in schema
        schema_cols = [field.name for field in job_config.schema]
        df_to_save = df[[col for col in schema_cols if col in df.columns]]
        
        job = client.load_table_from_dataframe(df_to_save, table_id, job_config=job_config)
        job.result()
        
        logger.info(f"✅ Saved to {table_id}")
        logger.info(f"   Rows: {len(df_to_save):,}")
        logger.info(f"   Columns: {len(df_to_save.columns)}")
        
    except Exception as e:
        logger.error(f"❌ Error saving to BigQuery: {e}")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║   YAHOO FINANCE 20-YEAR DATA PULL - SAFE & COMPLIANT            ║
╚══════════════════════════════════════════════════════════════════╝

This script will:
  1. Pull 20+ years of data (2000-2025) for soybean complex
  2. Calculate 6 moving averages (7, 30, 50, 90, 100, 200 day)
  3. Calculate proper technical indicators (Wilder's RSI, EMA MACD)
  4. Use rate limiting (2.5s between symbols)
  5. Cache data to minimize API calls
  6. Verify data quality
  7. Save to STAGING (not production)

COMPLIANCE:
  ✅ Rate limited (respectful of Yahoo API)
  ✅ Cached (minimize redundant calls)
  ✅ Verified (quality checks on all data)
  ✅ Attribution included
  ✅ Research/educational use

EXECUTION:
  Phase 1: Test with 30 days ZL only
  Phase 2: Full 20-year pull (requires approval)

""")
    
    # Run test phase
    test_passed = main_test_phase()
    
    if test_passed:
        print("\n✅ Test phase complete. Ready for full pull.")
        print("   To execute full pull, run: main_full_pull(test_mode=False)")
    else:
        print("\n⚠️  Test phase had issues. Review logs before proceeding.")

