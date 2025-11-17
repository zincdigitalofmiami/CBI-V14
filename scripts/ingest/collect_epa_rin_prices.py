#!/usr/bin/env python3
"""
EPA EMTS RIN Prices - Weekly Averages
======================================
Collects weekly RIN price averages from EPA EMTS Transparency dashboard.
Official source for D4, D5, D6 RIN prices.

Source: https://www.epa.gov/fuels-registration-reporting-and-compliance-help/rins-market-information
Coverage: 2010→present (weekly)
"""

import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import csv
import io

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/rins_epa"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# EPA EMTS RIN Prices page
RIN_PAGE = "https://www.epa.gov/fuels-registration-reporting-and-compliance-help/rins-market-information"

# CSV export endpoint (may need to be discovered from page)
RIN_CSV_EXPORT = "https://www.epa.gov/system/files/documents/2024-11/rins_weekly_price_averages.csv"

def fetch_rin_prices_csv() -> pd.DataFrame:
    """
    Fetch RIN weekly price averages CSV from EPA.
    
    Returns:
        DataFrame with RIN price data
    """
    logger.info("Fetching EPA RIN weekly price averages...")
    
    try:
        # Try direct CSV download
        response = requests.get(RIN_CSV_EXPORT, timeout=60, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; CBI-V14-Data-Collector/1.0)'
        })
        
        if response.status_code == 200:
            # Parse CSV
            df = pd.read_csv(io.StringIO(response.text))
            logger.info(f"✅ Retrieved {len(df)} records from CSV")
            return df
        else:
            logger.warning(f"CSV endpoint returned {response.status_code}, trying page scrape...")
            
    except Exception as e:
        logger.warning(f"CSV download failed: {e}, trying page scrape...")
    
    # Fallback: Scrape the page to find CSV export link
    try:
        response = requests.get(RIN_PAGE, timeout=60, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; CBI-V14-Data-Collector/1.0)'
        })
        
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for CSV download link
            csv_links = soup.find_all('a', href=True)
            for link in csv_links:
                href = link.get('href', '')
                if 'csv' in href.lower() or 'rins' in href.lower():
                    csv_url = href if href.startswith('http') else f"https://www.epa.gov{href}"
                    logger.info(f"Found CSV link: {csv_url}")
                    
                    csv_response = requests.get(csv_url, timeout=60)
                    if csv_response.status_code == 200:
                        df = pd.read_csv(io.StringIO(csv_response.text))
                        logger.info(f"✅ Retrieved {len(df)} records")
                        return df
    except Exception as e:
        logger.error(f"Page scrape failed: {e}")
    
    logger.error("Could not fetch RIN prices")
    return pd.DataFrame()

def clean_rin_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize RIN price data.
    """
    if df.empty:
        return df
    
    # Standardize column names (EPA CSV format may vary)
    rename_map = {
        'Date': 'date',
        'Week Ending': 'week_ending',
        'RIN Type': 'rin_type',
        'D4': 'd4_price',
        'D5': 'd5_price',
        'D6': 'd6_price',
        'D3': 'd3_price',
        'Average Price': 'avg_price',
        'Low Price': 'low_price',
        'High Price': 'high_price',
        'Volume': 'volume'
    }
    
    # Rename columns that exist
    for old_col, new_col in rename_map.items():
        if old_col in df.columns:
            df.rename(columns={old_col: new_col}, inplace=True)
    
    # Find date column
    date_col = None
    for col in ['date', 'week_ending', 'Date', 'Week Ending']:
        if col in df.columns:
            date_col = col
            break
    
    if date_col:
        df['date'] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Extract RIN type if in a column
    if 'rin_type' not in df.columns and 'RIN Type' in df.columns:
        df['rin_type'] = df['RIN Type']
    
    # Add metadata
    df['source'] = 'EPA_EMTS'
    df['updated_at'] = datetime.now()
    
    # Sort by date
    if 'date' in df.columns:
        df = df.sort_values('date')
        df = df.drop_duplicates(subset=['date', 'rin_type'], keep='last')
    
    return df

def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("EPA EMTS RIN PRICES COLLECTION")
    logger.info("="*80)
    logger.info("Weekly RIN price averages (D4, D5, D6)")
    logger.info("Coverage: 2010→present")
    logger.info("")
    logger.info("⚠️  LIMITATION: EPA EMTS dashboard URLs are not directly accessible.")
    logger.info("    This script attempts to find CSV exports but may require:")
    logger.info("    1. Manual download from EPA EMTS dashboard")
    logger.info("    2. Alternative source (OPIS, Argus - paywalled)")
    logger.info("    3. EPA API access (if available)")
    logger.info("="*80)
    
    # Fetch data
    raw_df = fetch_rin_prices_csv()
    
    if raw_df.empty:
        logger.error("No data collected")
        return 1
    
    # Clean data
    clean_df = clean_rin_data(raw_df)
    
    # Save
    output_file = RAW_DIR / f"rin_prices_{datetime.now().strftime('%Y%m%d')}.parquet"
    clean_df.to_parquet(output_file, index=False)
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("COLLECTION SUMMARY")
    logger.info("="*80)
    logger.info(f"✅ Total records: {len(clean_df):,}")
    
    if 'date' in clean_df.columns:
        logger.info(f"📅 Date range: {clean_df['date'].min().date()} to {clean_df['date'].max().date()}")
    
    if 'rin_type' in clean_df.columns:
        logger.info(f"📊 RIN types: {clean_df['rin_type'].unique().tolist()}")
    
    logger.info(f"\n✅ Saved: {output_file.name}")
    logger.info("="*80)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
