#!/usr/bin/env python3
"""
Palm Oil Daily Collection - Barchart/ICE Scraper
=================================================
Daily scraping of palm oil futures prices and volatility from Barchart/ICE.

Sources:
- Barchart: FCPO (Malaysian Palm Oil Futures) - primary source
- Yahoo Finance: CPO=F (fallback if Barchart unavailable)
- Historical: Loads existing historical data and appends new daily data

Prefix: `barchart_palm_*` on all columns except `date`

Coverage: Daily updates (historical already loaded in Week 0)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
import time
import requests
from bs4 import BeautifulSoup
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/barchart"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Historical file (already loaded in Week 0)
HISTORICAL_FILE = RAW_DIR / "palm_oil_historical.parquet"

# Barchart URLs for palm futures
BARCHART_URLS = {
    'fcpo': 'https://www.barchart.com/futures/quotes/FCPO*0/overview',  # Malaysian Palm Oil
    'palm': 'https://www.barchart.com/futures/quotes/PALM*0/overview',  # Alternative symbol
}

# Yahoo Finance fallback symbols
YAHOO_SYMBOLS = ['CPO=F', 'FCPO=F']  # Palm futures

def scrape_barchart_palm() -> pd.DataFrame:
    """
    Scrape palm oil futures from Barchart.com.
    
    Returns:
        DataFrame with daily palm prices
    """
    logger.info("Scraping palm oil futures from Barchart...")
    
    for symbol_type, url in BARCHART_URLS.items():
        try:
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; CBI-V14-Data-Collector/1.0)'
            })
            
            if response.status_code != 200:
                logger.warning(f"Barchart {symbol_type} returned {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find futures table (adjust selector based on actual page structure)
            table = soup.find('table', class_=re.compile(r'datatable|futures|quotes'))
            if not table:
                # Try alternative selectors
                table = soup.find('table', {'data-symbol': re.compile(r'FCPO|PALM', re.I)})
            
            if not table:
                logger.warning(f"Could not find futures table for {symbol_type}")
                continue
            
            rows = []
            for tr in table.find_all('tr')[1:]:  # Skip header
                cols = tr.find_all(['td', 'th'])
                if len(cols) < 5:
                    continue
                
                try:
                    # Extract symbol/contract
                    symbol_text = cols[0].get_text(strip=True)
                    
                    # Extract price (usually in 2nd or 3rd column)
                    price_text = None
                    for col in cols[1:4]:
                        text = col.get_text(strip=True)
                        # Look for numeric price
                        price_match = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
                        if price_match:
                            price_text = price_match.group()
                            break
                    
                    if not price_text:
                        continue
                    
                    price = float(price_text.replace(',', ''))
                    
                    # Extract volume (usually in 4th-6th column)
                    volume = 0
                    for col in cols[4:7]:
                        text = col.get_text(strip=True)
                        vol_match = re.search(r'[\d,]+', text.replace(',', ''))
                        if vol_match:
                            volume = int(vol_match.group().replace(',', ''))
                            break
                    
                    # Use front month contract (first row)
                    if not rows:  # Only take first (front month)
                        rows.append({
                            'date': datetime.now().date(),
                            'barchart_palm_close': price,
                            'barchart_palm_volume': volume,
                            'barchart_palm_symbol': symbol_text,
                            'barchart_palm_source': 'barchart',
                        })
                        break  # Only need front month
                
                except Exception as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue
            
            if rows:
                df = pd.DataFrame(rows)
                logger.info(f"✅ Barchart {symbol_type}: {len(df)} rows")
                return df
            
        except Exception as e:
            logger.warning(f"Error scraping Barchart {symbol_type}: {e}")
            continue
    
    return pd.DataFrame()

def fetch_yahoo_palm() -> pd.DataFrame:
    """
    Fetch palm oil from Yahoo Finance as fallback.
    
    Returns:
        DataFrame with daily palm prices
    """
    logger.info("Fetching palm oil from Yahoo Finance (fallback)...")
    
    for symbol in YAHOO_SYMBOLS:
        try:
            ticker = yf.Ticker(symbol)
            # Get recent data (last 5 days to catch any updates)
            history = ticker.history(period='5d')
            
            if history.empty:
                continue
            
            # Get most recent day
            latest = history.iloc[-1]
            
            df = pd.DataFrame([{
                'date': pd.to_datetime(history.index[-1]).date(),
                'barchart_palm_close': float(latest['Close']),
                'barchart_palm_open': float(latest['Open']),
                'barchart_palm_high': float(latest['High']),
                'barchart_palm_low': float(latest['Low']),
                'barchart_palm_volume': int(latest['Volume']) if pd.notna(latest['Volume']) else 0,
                'barchart_palm_symbol': symbol,
                'barchart_palm_source': 'yahoo',
            }])
            
            logger.info(f"✅ Yahoo {symbol}: {len(df)} rows")
            return df
            
        except Exception as e:
            logger.debug(f"Yahoo {symbol} failed: {e}")
            continue
    
    return pd.DataFrame()

def calculate_volatility(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate 20-day realized volatility for palm prices.
    
    Args:
        df: DataFrame with barchart_palm_close column
    
    Returns:
        DataFrame with added volatility column
    """
    if df.empty or 'barchart_palm_close' not in df.columns:
        return df
    
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # Calculate returns
    df['returns'] = df['barchart_palm_close'].pct_change()
    
    # Calculate 20-day realized volatility (annualized)
    df['barchart_palm_vol_20d'] = (
        df['returns'].rolling(window=20, min_periods=1).std() * np.sqrt(252) * 100
    )
    
    # Drop temporary returns column
    df = df.drop(columns=['returns'])
    
    return df

def load_historical() -> pd.DataFrame:
    """
    Load existing historical palm data.
    
    Returns:
        DataFrame with historical data
    """
    if not HISTORICAL_FILE.exists():
        logger.warning(f"Historical file not found: {HISTORICAL_FILE}")
        return pd.DataFrame()
    
    try:
        df = pd.read_parquet(HISTORICAL_FILE)
        logger.info(f"✅ Loaded historical data: {len(df)} rows ({df['date'].min()} to {df['date'].max()})")
        return df
    except Exception as e:
        logger.error(f"Error loading historical data: {e}")
        return pd.DataFrame()

def main():
    """
    Main collection function: Scrape daily palm data and append to historical.
    """
    logger.info("=" * 80)
    logger.info("PALM OIL DAILY COLLECTION - BARCHART/ICE SCRAPER")
    logger.info("=" * 80)
    logger.info("Daily scraping of palm futures prices + volatility")
    logger.info("")
    
    # 1. Load historical data
    historical_df = load_historical()
    
    # 2. Scrape Barchart (primary source)
    daily_df = scrape_barchart_palm()
    
    # 3. Fallback to Yahoo Finance if Barchart failed
    if daily_df.empty:
        logger.info("Barchart scrape failed, trying Yahoo Finance fallback...")
        daily_df = fetch_yahoo_palm()
    
    if daily_df.empty:
        logger.error("❌ No daily palm data collected from any source")
        if not historical_df.empty:
            logger.info(f"   Historical data available: {len(historical_df)} rows")
        return
    
    # 4. Calculate volatility
    daily_df = calculate_volatility(daily_df)
    
    # 5. Merge with historical data
    if not historical_df.empty:
        # Check if today's data already exists
        today = datetime.now().date()
        if 'date' in historical_df.columns:
            historical_df['date'] = pd.to_datetime(historical_df['date']).dt.date
            existing_today = historical_df[historical_df['date'] == today]
            
            if not existing_today.empty:
                logger.info(f"Today's data already exists ({len(existing_today)} rows), updating...")
                # Remove existing today's data
                historical_df = historical_df[historical_df['date'] != today]
        
        # Combine historical + daily
        combined_df = pd.concat([historical_df, daily_df], ignore_index=True)
    else:
        combined_df = daily_df.copy()
    
    # 6. Calculate volatility for entire dataset
    combined_df = calculate_volatility(combined_df)
    
    # 7. Sort by date
    combined_df = combined_df.sort_values('date').reset_index(drop=True)
    
    # 8. Save updated data
    combined_df.to_parquet(HISTORICAL_FILE, index=False)
    
    # 9. Also save daily snapshot
    daily_snapshot = RAW_DIR / f"palm_daily_{datetime.now().strftime('%Y%m%d')}.parquet"
    daily_df.to_parquet(daily_snapshot, index=False)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✅ PALM DAILY COLLECTION COMPLETE")
    logger.info(f"   Daily rows: {len(daily_df):,}")
    logger.info(f"   Total rows: {len(combined_df):,}")
    logger.info(f"   Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
    logger.info(f"   Saved to: {HISTORICAL_FILE}")
    logger.info(f"   Daily snapshot: {daily_snapshot}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()





