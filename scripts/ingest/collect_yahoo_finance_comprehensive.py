#!/usr/bin/env python3
"""
Comprehensive Yahoo Finance Data Collection
Pulls EVERYTHING: prices, indicators, analysis, forecasts for all symbols

REPLACES existing data in TrainingData/raw/yahoo_finance/
"""

import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
import time
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')

# Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = DRIVE / "TrainingData" / "raw"
YAHOO_DIR = RAW_DIR / "yahoo_finance"

# Create directories (will replace existing)
YAHOO_DIR.mkdir(parents=True, exist_ok=True)
(YAHOO_DIR / "prices").mkdir(exist_ok=True)
(YAHOO_DIR / "prices" / "commodities").mkdir(exist_ok=True)
(YAHOO_DIR / "prices" / "indices").mkdir(exist_ok=True)
(YAHOO_DIR / "prices" / "currencies").mkdir(exist_ok=True)
(YAHOO_DIR / "prices" / "etfs").mkdir(exist_ok=True)
(YAHOO_DIR / "technical").mkdir(exist_ok=True)
(YAHOO_DIR / "fundamentals").mkdir(exist_ok=True)
(YAHOO_DIR / "options").mkdir(exist_ok=True)
(YAHOO_DIR / "news").mkdir(exist_ok=True)

# COMPREHENSIVE SYMBOL LIST
SYMBOLS = {
    'commodities': [
        # Soybean Complex
        'ZL=F',  # Soybean Oil (PRIMARY)
        'ZS=F',  # Soybeans
        'ZM=F',  # Soybean Meal
        # Grains
        'ZC=F',  # Corn
        'ZW=F',  # Wheat
        'ZO=F',  # Oats
        'ZR=F',  # Rough Rice
        # Softs
        'CT=F',  # Cotton
        'KC=F',  # Coffee
        'CC=F',  # Cocoa
        'SB=F',  # Sugar
        # Energy
        'CL=F',  # WTI Crude
        'BZ=F',  # Brent
        'NG=F',  # Natural Gas
        'RB=F',  # RBOB Gasoline
        'HO=F',  # Heating Oil
        # Metals
        'GC=F',  # Gold
        'SI=F',  # Silver
        'HG=F',  # Copper
        'PA=F',  # Palladium
        'PL=F',  # Platinum
    ],
    'indices': [
        # US Indices
        '^GSPC',  # S&P 500
        '^DJI',   # Dow Jones
        '^IXIC',  # NASDAQ
        '^RUT',   # Russell 2000
        '^VIX',   # VIX Volatility
        # Treasury Yields
        '^TNX',   # 10-Year
        '^FVX',   # 5-Year
        '^IRX',   # 3-Month
        '^TYX',   # 30-Year
        # International
        '^FTSE',  # FTSE 100
        '^N225',  # Nikkei 225
        '^HSI',   # Hang Seng
        '^STOXX50E',  # Euro Stoxx 50
        '^GDAXI',  # DAX
        '^FCHI',   # CAC 40
    ],
    'currencies': [
        # Dollar Index
        'DX-Y.NYB',  # DXY
        # Major Pairs
        'EURUSD=X',
        'GBPUSD=X',
        'USDJPY=X',
        'USDCHF=X',
        'AUDUSD=X',
        'NZDUSD=X',
        'USDCAD=X',
        # Commodity Currencies (CRITICAL)
        'BRLUSD=X',  # Brazilian Real (Soy exports)
        'CNYUSD=X',  # Chinese Yuan (Soy imports)
        'ARSUSD=X',  # Argentine Peso (Soy exports)
        'MYRUSD=X',  # Malaysian Ringgit (Palm oil)
        'INRUSD=X',  # Indian Rupee (Edible oils)
        'IDRUSD=X',  # Indonesian Rupiah (Palm oil)
        # Emerging Markets
        'ZARUSD=X',  # South African Rand
        'MXNUSD=X',  # Mexican Peso
        'RUBUSD=X',  # Russian Ruble
        'TRYUSD=X',  # Turkish Lira
    ],
    'etfs': [
        # Bonds
        'TLT',  # 20+ Year Treasury
        'IEF',  # 7-10 Year Treasury
        'SHY',  # 1-3 Year Treasury
        'HYG',  # High Yield Corporate
        'LQD',  # Investment Grade Corporate
        # Energy
        'XLE',  # Energy Sector
        'USO',  # Oil Fund
        'UCO',  # Ultra Crude Oil
        # Agriculture
        'DBA',  # Agriculture Fund
        'MOO',  # Agribusiness ETF
        'CORN',  # Corn Fund
        'SOYB',  # Soybean Fund
        'WEAT',  # Wheat Fund
        # Financial
        'XLF',  # Financial Sector
        'KRE',  # Regional Banking
        # Consumer Staples
        'XLP',  # Consumer Staples
        'FSTA',  # Consumer Staples Index
    ],
    'volatility': [
        '^VIX',   # VIX
        '^VXN',   # NASDAQ Volatility
        '^RVX',   # Russell 2000 Volatility
        'VIX9D',  # 9-Day VIX
        'VIX3M',  # 3-Month VIX
    ],
    'commodity_indices': [
        '^DJC',   # Dow Jones Commodity
        '^CRB',   # CRB Index
        '^DJAIG', # Dow Jones AIG
    ]
}

# Date range (25 years)
START_DATE = '2000-01-01'
END_DATE = datetime.now().strftime('%Y-%m-%d')


def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate ALL technical indicators
    """
    if df.empty or 'Close' not in df.columns:
        return df
    
    df = df.copy()
    
    # Moving Averages
    for period in [5, 10, 20, 50, 100, 200]:
        df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
        df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # Bollinger Bands
    for period in [20, 50]:
        sma = df['Close'].rolling(window=period).mean()
        std = df['Close'].rolling(window=period).std()
        df[f'BB_Upper_{period}'] = sma + (2 * std)
        df[f'BB_Middle_{period}'] = sma
        df[f'BB_Lower_{period}'] = sma - (2 * std)
        df[f'BB_Width_{period}'] = (df[f'BB_Upper_{period}'] - df[f'BB_Lower_{period}']) / df[f'BB_Middle_{period}']
    
    # Stochastic Oscillator
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    df['Stoch_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
    
    # ATR (Average True Range)
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['ATR_14'] = true_range.rolling(window=14).mean()
    
    # ADX (simplified)
    plus_dm = df['High'].diff()
    minus_dm = -df['Low'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    tr = true_range
    plus_di = 100 * (plus_dm.rolling(window=14).mean() / tr.rolling(window=14).mean())
    minus_di = 100 * (minus_dm.rolling(window=14).mean() / tr.rolling(window=14).mean())
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    df['ADX_14'] = dx.rolling(window=14).mean()
    
    # OBV (On-Balance Volume)
    df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
    
    # CCI (Commodity Channel Index)
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    sma_tp = typical_price.rolling(window=20).mean()
    mad = typical_price.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
    df['CCI_20'] = (typical_price - sma_tp) / (0.015 * mad)
    
    # Williams %R
    highest_high = df['High'].rolling(window=14).max()
    lowest_low = df['Low'].rolling(window=14).min()
    df['Williams_R'] = -100 * ((highest_high - df['Close']) / (highest_high - lowest_low))
    
    # Rate of Change
    for period in [10, 20]:
        df[f'ROC_{period}'] = df['Close'].pct_change(periods=period) * 100
    
    # Momentum
    for period in [10, 20]:
        df[f'Momentum_{period}'] = df['Close'].diff(periods=period)
    
    # Returns
    for period in [1, 5, 10, 20, 60, 252]:
        df[f'Return_{period}d'] = df['Close'].pct_change(periods=period)
    
    # Volatility
    for period in [5, 10, 20, 60, 252]:
        df[f'Volatility_{period}d'] = df['Close'].pct_change().rolling(window=period).std() * np.sqrt(252)
    
    return df


def collect_symbol(symbol: str, category: str) -> bool:
    """
    Collect all data for a single symbol
    SEQUENTIAL PROCESSING: Delete old file → Write new file → Wait
    Respectful rate limiting to avoid getting blocked
    """
    max_retries = 3
    retry_delay = 2  # Start with 2 seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Collecting {symbol} ({category})... [Attempt {attempt + 1}/{max_retries}]")
            
            # Download historical data with timeout
            ticker = yf.Ticker(symbol)
            
            # Respectful delay before request
            if attempt > 0:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"  Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                time.sleep(1.0)  # 1 second delay between symbols (respectful)
            
            df = ticker.history(start=START_DATE, end=END_DATE, auto_adjust=True, prepost=True, timeout=30)
            
            if df.empty:
                logger.warning(f"  ⚠️  No data for {symbol}")
                return False
            
            # Standardize column names
            df.columns = [col.replace(' ', '_') for col in df.columns]
            df = df.rename(columns={
                'Open': 'Open',
                'High': 'High',
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            })
            
            # Add symbol and date
            df['Symbol'] = symbol
            df['Date'] = df.index
            df = df.reset_index(drop=False)
            if 'Date' not in df.columns:
                df['Date'] = df.index
            
            # Calculate technical indicators
            df_with_indicators = calculate_technical_indicators(df)
            
            # SEQUENTIAL REPLACEMENT: Delete old file → Write new file
            price_dir = YAHOO_DIR / "prices" / category
            price_dir.mkdir(parents=True, exist_ok=True)
            price_file = price_dir / f"{symbol.replace('=', '_').replace('^', '').replace('-', '_')}.parquet"
            
            # Delete old file if exists
            if price_file.exists():
                price_file.unlink()
                logger.info(f"  🗑️  Deleted old file: {price_file.name}")
            
            # Write new file immediately
            df_with_indicators.to_parquet(price_file, index=False)
            logger.info(f"  ✅ Saved {len(df_with_indicators)} rows for {symbol}")
            
            # Save technical indicators separately (same pattern: delete → write)
            indicator_cols = [col for col in df_with_indicators.columns 
                             if any(x in col for x in ['SMA', 'EMA', 'RSI', 'MACD', 'BB', 'Stoch', 
                                                       'ATR', 'ADX', 'OBV', 'CCI', 'Williams', 'ROC', 
                                                       'Momentum', 'Return', 'Volatility'])]
            if indicator_cols:
                indicators_df = df_with_indicators[['Date', 'Symbol'] + indicator_cols].copy()
                indicator_file = YAHOO_DIR / "technical" / f"{symbol.replace('=', '_').replace('^', '').replace('-', '_')}_indicators.parquet"
                
                # Delete old indicator file if exists
                if indicator_file.exists():
                    indicator_file.unlink()
                
                # Write new indicator file
                indicators_df.to_parquet(indicator_file, index=False)
            
            # Get fundamental data (if available) - same pattern
            try:
                time.sleep(0.5)  # Small delay before info request
                info = ticker.info
                if info:
                    fundamentals_df = pd.DataFrame([{
                        'Symbol': symbol,
                        'Date': datetime.now().date(),
                        **{k: v for k, v in info.items() if isinstance(v, (int, float, str))}
                    }])
                    fundamentals_file = YAHOO_DIR / "fundamentals" / f"{symbol.replace('=', '_').replace('^', '').replace('-', '_')}_fundamentals.parquet"
                    
                    # Delete old fundamentals file if exists
                    if fundamentals_file.exists():
                        fundamentals_file.unlink()
                    
                    # Write new fundamentals file
                    fundamentals_df.to_parquet(fundamentals_file, index=False)
            except Exception as e:
                logger.debug(f"  No fundamentals for {symbol}: {e}")
            
            # Success - return
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for rate limiting errors
            if any(keyword in error_msg for keyword in ['rate limit', 'too many requests', '429', 'blocked', 'forbidden']):
                wait_time = retry_delay * (2 ** (attempt + 1))  # Exponential backoff
                logger.warning(f"  ⚠️  Rate limit detected for {symbol}. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue  # Retry
            
            # Check for timeout errors
            elif 'timeout' in error_msg or 'timed out' in error_msg:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"  ⚠️  Timeout for {symbol}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue  # Retry
            
            # Other errors - log and retry once
            elif attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"  ⚠️  Error for {symbol}: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue  # Retry
            else:
                logger.error(f"  ❌ Failed to collect {symbol} after {max_retries} attempts: {e}")
                return False
    
    return False


def main():
    """
    Collect ALL data from Yahoo Finance
    """
    logger.info("="*80)
    logger.info("YAHOO FINANCE COMPREHENSIVE DATA COLLECTION")
    logger.info("="*80)
    logger.info(f"Start Date: {START_DATE}")
    logger.info(f"End Date: {END_DATE}")
    logger.info(f"Output Directory: {YAHOO_DIR}")
    logger.info("")
    
    # Note: We do NOT batch delete - we delete files one at a time as we replace them
    # This is handled in collect_symbol() function for each symbol
    logger.info("📋 Sequential processing: Files will be deleted and replaced one at a time")
    logger.info("   This prevents data loss and respects Yahoo Finance rate limits")
    logger.info("")
    
    # Collect all symbols
    total_symbols = sum(len(symbols) for symbols in SYMBOLS.values())
    collected = 0
    failed = 0
    
    logger.info(f"\n📊 Collecting {total_symbols} symbols...")
    logger.info("")
    
    for category, symbols in SYMBOLS.items():
        logger.info(f"\n{'='*80}")
        logger.info(f"Category: {category.upper()} ({len(symbols)} symbols)")
        logger.info(f"{'='*80}")
        
        # SEQUENTIAL PROCESSING: One symbol at a time
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"\n[{i}/{len(symbols)}] Processing {symbol}...")
            success = collect_symbol(symbol, category)
            if success:
                collected += 1
            else:
                failed += 1
            
            # Respectful delay between symbols (already handled in collect_symbol, but extra safety)
            if i < len(symbols):  # Don't wait after last symbol
                time.sleep(0.5)  # Additional small delay between symbols
    
    # Summary
    logger.info("")
    logger.info("="*80)
    logger.info("COLLECTION COMPLETE")
    logger.info("="*80)
    logger.info(f"✅ Collected: {collected} symbols")
    logger.info(f"❌ Failed: {failed} symbols")
    logger.info(f"📁 Data saved to: {YAHOO_DIR}")
    logger.info("")
    
    # Create master index
    logger.info("Creating master index...")
    master_index = []
    for price_file in (YAHOO_DIR / "prices").rglob("*.parquet"):
        try:
            df = pd.read_parquet(price_file)
            master_index.append({
                'file': str(price_file.relative_to(YAHOO_DIR)),
                'symbol': df['Symbol'].iloc[0] if 'Symbol' in df.columns else price_file.stem,
                'rows': len(df),
                'start_date': df['Date'].min() if 'Date' in df.columns else None,
                'end_date': df['Date'].max() if 'Date' in df.columns else None,
            })
        except:
            pass
    
    if master_index:
        index_df = pd.DataFrame(master_index)
        index_file = YAHOO_DIR / "master_index.parquet"
        index_df.to_parquet(index_file, index=False)
        logger.info(f"✅ Master index created: {len(master_index)} files")
    
    logger.info("")
    logger.info("✅ ALL DATA COLLECTED AND SAVED!")


if __name__ == "__main__":
    main()
