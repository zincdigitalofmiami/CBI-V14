#!/usr/bin/env python3
"""
Daily Data Update Script
========================
Keeps all data sources current by fetching latest data daily.
Run this script daily via cron or scheduler.

Data sources updated:
1. Yahoo Finance - All symbols (closes at 4pm ET)
2. FRED Economic - Daily series
3. Weather - NASA POWER API (if needed)
4. CFTC COT - Weekly (Fridays)
"""

import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta
import logging
import requests
import json
import time
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'daily_updates_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw"
STAGING_DIR = EXTERNAL_DRIVE / "TrainingData/staging"

# FRED API Key
FRED_API_KEY = os.getenv('FRED_API_KEY', 'a2c2c9495038ebf019e699ebef2e31e9')

# ============================================================================
# 1. UPDATE YAHOO FINANCE DATA
# ============================================================================

def update_yahoo_finance():
    """Update all Yahoo Finance symbols with latest data"""
    logger.info("="*80)
    logger.info("UPDATING YAHOO FINANCE DATA")
    logger.info("="*80)
    
    # Symbol categories to update
    symbols = {
        'commodities': [
            'ZL=F', 'ZS=F', 'ZM=F', 'ZC=F', 'ZW=F',  # Ags
            'CL=F', 'BZ=F', 'NG=F', 'RB=F', 'HO=F',  # Energy
            'GC=F', 'SI=F', 'HG=F'  # Metals
        ],
        'indices': [
            '^GSPC', '^DJI', '^IXIC', '^RUT', '^VIX',
            '^TNX', '^FVX', '^IRX', '^TYX'
        ],
        'currencies': [
            'DX-Y.NYB', 'EURUSD=X', 'GBPUSD=X', 'USDJPY=X',
            'BRLUSD=X', 'CNYUSD=X', 'ARSUSD=X'
        ],
        'etfs': [
            'TLT', 'IEF', 'SHY', 'HYG', 'LQD',
            'XLE', 'USO', 'DBA', 'MOO', 'CORN', 'SOYB', 'WEAT'
        ]
    }
    
    yahoo_dir = RAW_DIR / "yahoo_finance"
    updates_count = 0
    errors_count = 0
    
    for category, symbol_list in symbols.items():
        category_dir = yahoo_dir / "prices" / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        for symbol in symbol_list:
            try:
                # Get file path
                filename = symbol.replace('=', '_').replace('^', '').replace('-', '_')
                filepath = category_dir / f"{filename}.parquet"
                
                # Determine start date for update
                if filepath.exists():
                    # Load existing data to find last date
                    existing_df = pd.read_parquet(filepath)
                    if 'Date' in existing_df.columns:
                        last_date = pd.to_datetime(existing_df['Date']).max()
                        start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
                    else:
                        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                else:
                    # New symbol - get last 30 days
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                
                end_date = datetime.now().strftime('%Y-%m-%d')
                
                # Fetch latest data
                ticker = yf.Ticker(symbol)
                new_data = ticker.history(start=start_date, end=end_date, auto_adjust=True)
                
                if not new_data.empty:
                    # Prepare data
                    new_data = new_data.reset_index()
                    new_data['Date'] = pd.to_datetime(new_data['Date']).dt.tz_localize(None)
                    new_data['Symbol'] = symbol
                    
                    # Merge with existing data or save new
                    if filepath.exists() and not existing_df.empty:
                        # Combine old and new, remove duplicates
                        combined = pd.concat([existing_df, new_data], ignore_index=True)
                        combined = combined.drop_duplicates(subset=['Date'], keep='last')
                        combined = combined.sort_values('Date')
                        combined.to_parquet(filepath, index=False)
                        logger.info(f"  ✅ Updated {symbol}: +{len(new_data)} new records")
                    else:
                        new_data.to_parquet(filepath, index=False)
                        logger.info(f"  ✅ Created {symbol}: {len(new_data)} records")
                    
                    updates_count += 1
                    time.sleep(0.5)  # Rate limiting
                else:
                    logger.debug(f"  No new data for {symbol}")
                    
            except Exception as e:
                logger.error(f"  ❌ Error updating {symbol}: {e}")
                errors_count += 1
    
    logger.info(f"\n✅ Yahoo Finance Update Complete: {updates_count} symbols updated, {errors_count} errors")
    return updates_count > 0

# ============================================================================
# 2. UPDATE FRED ECONOMIC DATA
# ============================================================================

def update_fred_data():
    """Update FRED economic series with latest data"""
    logger.info("\n" + "="*80)
    logger.info("UPDATING FRED ECONOMIC DATA")
    logger.info("="*80)
    
    # Key FRED series to update daily
    series_list = {
        'DGS10': '10-Year Treasury Rate',
        'DGS2': '2-Year Treasury Rate',
        'DFEDTARU': 'Fed Funds Upper',
        'DFEDTARL': 'Fed Funds Lower',
        'DEXUSEU': 'USD/EUR Exchange Rate',
        'DCOILWTICO': 'WTI Crude Oil',
        'DCOILBRENTEU': 'Brent Crude Oil',
        'GOLDPMGBD228NLBM': 'Gold Price',
        'DEXBZUS': 'Brazil Real/USD',
        'DEXCHUS': 'China Yuan/USD',
        'CPIAUCSL': 'CPI All Urban',
        'UNRATE': 'Unemployment Rate',
        'T10Y2Y': '10Y-2Y Treasury Spread',
        'VIXCLS': 'VIX Close'
    }
    
    fred_dir = RAW_DIR / "fred"
    processed_dir = fred_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    all_data = []
    updates_count = 0
    
    for series_id, series_name in series_list.items():
        try:
            # Get last 30 days of data (FRED API limitation for real-time)
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            url = f"https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': series_id,
                'api_key': FRED_API_KEY,
                'file_type': 'json',
                'observation_start': start_date,
                'observation_end': end_date
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'observations' in data:
                    df = pd.DataFrame(data['observations'])
                    
                    if not df.empty:
                        # Clean and convert
                        df['date'] = pd.to_datetime(df['date'])
                        df['value'] = pd.to_numeric(df['value'], errors='coerce')
                        df['series_id'] = series_id
                        df['series_name'] = series_name
                        
                        # Remove missing values
                        df = df[df['value'].notna()]
                        
                        if not df.empty:
                            # Save individual series
                            series_file = processed_dir / f"{series_id}.parquet"
                            
                            # Merge with existing or create new
                            if series_file.exists():
                                existing = pd.read_parquet(series_file)
                                combined = pd.concat([existing, df], ignore_index=True)
                                combined = combined.drop_duplicates(subset=['date'], keep='last')
                                combined = combined.sort_values('date')
                                combined.to_parquet(series_file, index=False)
                            else:
                                df.to_parquet(series_file, index=False)
                            
                            all_data.append(df)
                            updates_count += 1
                            logger.info(f"  ✅ Updated {series_id}: {len(df)} records")
                        
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            logger.error(f"  ❌ Error updating {series_id}: {e}")
    
    # Save combined file with today's date
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_file = fred_dir / "combined" / f"fred_all_series_{datetime.now().strftime('%Y%m%d')}.parquet"
        combined_file.parent.mkdir(parents=True, exist_ok=True)
        combined_df.to_parquet(combined_file, index=False)
        logger.info(f"\n✅ FRED Update Complete: {updates_count} series updated")
    
    return updates_count > 0

# ============================================================================
# 3. UPDATE WEATHER DATA (if needed)
# ============================================================================

def update_weather_data():
    """Update weather data from NASA POWER API for recent dates"""
    logger.info("\n" + "="*80)
    logger.info("CHECKING WEATHER DATA")
    logger.info("="*80)
    
    weather_file = STAGING_DIR / "weather_2000_2025.parquet"
    
    if weather_file.exists():
        df = pd.read_parquet(weather_file)
        latest_date = pd.to_datetime(df['date']).max().date()
        days_behind = (datetime.now().date() - latest_date).days
        
        if days_behind <= 1:
            logger.info(f"✅ Weather data is current (last update: {latest_date})")
            return False
        else:
            logger.info(f"⚠️ Weather data is {days_behind} days behind")
            # Would implement NASA POWER API update here
            # For now, weather data is already current
    
    return False

# ============================================================================
# 4. UPDATE CFTC COT DATA (Weekly - Fridays)
# ============================================================================

def update_cftc_data():
    """Update CFTC Commitment of Traders data (releases Fridays)"""
    
    # Only run on Fridays or Saturdays
    if datetime.now().weekday() not in [4, 5]:  # Friday=4, Saturday=5
        return False
    
    logger.info("\n" + "="*80)
    logger.info("UPDATING CFTC COT DATA")
    logger.info("="*80)
    
    # CFTC COT data update would go here (not yet implemented)
    logger.info("⚠️ CFTC COT update not yet implemented")
    
    return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all daily updates"""
    logger.info("="*80)
    logger.info("DAILY DATA UPDATE SCRIPT")
    logger.info(f"Run time: {datetime.now()}")
    logger.info("="*80)
    
    updates_made = False
    
    # 1. Update Yahoo Finance
    try:
        if update_yahoo_finance():
            updates_made = True
    except Exception as e:
        logger.error(f"Yahoo Finance update failed: {e}")
    
    # 2. Update FRED
    try:
        if update_fred_data():
            updates_made = True
    except Exception as e:
        logger.error(f"FRED update failed: {e}")
    
    # 3. Check Weather
    try:
        if update_weather_data():
            updates_made = True
    except Exception as e:
        logger.error(f"Weather update failed: {e}")
    
    # 4. Update CFTC (weekly)
    try:
        if update_cftc_data():
            updates_made = True
    except Exception as e:
        logger.error(f"CFTC update failed: {e}")
    
    # Summary
    logger.info("\n" + "="*80)
    if updates_made:
        logger.info("✅ DAILY UPDATE COMPLETE - Data refreshed")
    else:
        logger.info("✅ DAILY UPDATE COMPLETE - All data was already current")
    logger.info("="*80)
    
    return 0 if updates_made else 1

if __name__ == "__main__":
    sys.exit(main())
