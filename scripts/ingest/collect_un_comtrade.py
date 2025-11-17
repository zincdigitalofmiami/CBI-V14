#!/usr/bin/env python3
"""
UN Comtrade API - China Soybean Imports
========================================
⚠️ NOT USABLE - Requires API Registration

This script is kept for reference but cannot be used without UN Comtrade API registration.
The API returns HTML instead of JSON without authentication.

Alternatives:
1. China Customs Statistics web scraping (https://stats.customs.gov.cn/indexEn)
2. Use USDA FAS ESR weekly export sales as proxy for China import pace
3. Use World Bank Pink Sheet for long-run trade data

HS Code 1201: Soybeans, whether or not broken
Reporter: China (156)
Partner: World (0)
Trade Flow: Imports (1)
"""

import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import time
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/china_trade"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# UN Comtrade API endpoint (Legacy v1 - stable & widely used)
COMTRADE_API = "https://comtrade.un.org/api/get"

# Parameters for China soybean imports
# Format: ps=YYYYMM:YYYYMM for date range
# r=156 (China), p=0 (World), rg=1 (Imports), cc=1201 (Soybeans)
PARAMS = {
    'max': 50000,           # Max records
    'type': 'C',           # Commodities
    'freq': 'M',           # Monthly
    'px': 'HS',            # HS classification
    'ps': '200001:202512', # Time period: Jan 2000 to Dec 2025
    'r': '156',            # Reporter: China
    'p': '0',              # Partner: World
    'rg': '1',             # Trade flow: Imports
    'cc': '1201',          # Commodity: Soybeans
    'fmt': 'json'          # Format
}

def fetch_comtrade_data(start_year: int, end_year: int) -> pd.DataFrame:
    """
    Fetch China soybean import data from UN Comtrade API.
    
    Args:
        start_year: Starting year
        end_year: Ending year
        
    Returns:
        DataFrame with import data
    """
    all_data = []
    
    # Process in yearly chunks to avoid API limits
    for year in range(start_year, end_year + 1):
        logger.info(f"Fetching {year} data...")
        
        # Update parameters for this year
        params = PARAMS.copy()
        params['ps'] = str(year)
        
        try:
            # Make API request
            response = requests.get(COMTRADE_API, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'dataset' in data and data['dataset']:
                    df = pd.DataFrame(data['dataset'])
                    logger.info(f"  ✅ Retrieved {len(df)} records for {year}")
                    all_data.append(df)
                else:
                    logger.warning(f"  No data for {year}")
            else:
                logger.error(f"  API error {response.status_code} for {year}")
                
            # Rate limiting - UN Comtrade has strict limits
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"  Error fetching {year}: {e}")
            time.sleep(5)  # Longer wait on error
    
    if not all_data:
        logger.error("No data collected")
        return pd.DataFrame()
    
    # Combine all years
    combined = pd.concat(all_data, ignore_index=True)
    
    return combined

def clean_and_standardize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize Comtrade data for our pipeline.
    """
    if df.empty:
        return df
    
    # Key columns to keep
    columns_map = {
        'period': 'date',
        'yr': 'year', 
        'rtTitle': 'reporter',
        'ptTitle': 'partner',
        'TradeValue': 'trade_value_usd',
        'NetWeight': 'net_weight_kg',
        'TradeQuantity': 'quantity',
        'qtDesc': 'quantity_unit',
        'cmdDescE': 'commodity_desc'
    }
    
    # Select and rename columns
    df_clean = df[list(columns_map.keys())].copy()
    df_clean.rename(columns=columns_map, inplace=True)
    
    # Convert date (format: YYYYMM)
    df_clean['date'] = pd.to_datetime(df_clean['date'], format='%Y%m')
    
    # Convert numeric columns
    numeric_cols = ['trade_value_usd', 'net_weight_kg', 'quantity']
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # Calculate metric tons from kg
    df_clean['quantity_mt'] = df_clean['net_weight_kg'] / 1000
    
    # Add metadata
    df_clean['hs_code'] = '1201'
    df_clean['trade_flow'] = 'imports'
    df_clean['source'] = 'UN_COMTRADE'
    df_clean['updated_at'] = datetime.now()
    
    # Sort by date
    df_clean = df_clean.sort_values('date')
    
    # Remove duplicates
    df_clean = df_clean.drop_duplicates(subset=['date', 'partner'], keep='last')
    
    return df_clean

def aggregate_monthly_totals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate to monthly totals (all partners combined).
    """
    if df.empty:
        return df
    
    monthly = df.groupby('date').agg({
        'trade_value_usd': 'sum',
        'quantity_mt': 'sum',
        'net_weight_kg': 'sum',
        'year': 'first',
        'reporter': 'first',
        'hs_code': 'first',
        'trade_flow': 'first',
        'source': 'first'
    }).reset_index()
    
    # Calculate average price per MT
    monthly['avg_price_per_mt'] = monthly['trade_value_usd'] / monthly['quantity_mt']
    
    return monthly

def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("UN COMTRADE - CHINA SOYBEAN IMPORTS")
    logger.info("="*80)
    
    # Fetch data from 2000 to current year
    start_year = 2000
    end_year = datetime.now().year
    
    logger.info(f"Date range: {start_year} to {end_year}")
    logger.info("="*80)
    
    # Fetch data
    raw_df = fetch_comtrade_data(start_year, end_year)
    
    if raw_df.empty:
        logger.error("No data fetched")
        return 1
    
    # Clean and standardize
    clean_df = clean_and_standardize(raw_df)
    
    # Save detailed data (by partner)
    detailed_file = RAW_DIR / f"china_soy_imports_detailed_{datetime.now().strftime('%Y%m%d')}.parquet"
    clean_df.to_parquet(detailed_file, index=False)
    logger.info(f"✅ Saved detailed data: {detailed_file.name}")
    
    # Aggregate monthly totals
    monthly_df = aggregate_monthly_totals(clean_df)
    
    # Save monthly aggregates
    monthly_file = RAW_DIR / f"china_soy_imports_monthly_{datetime.now().strftime('%Y%m%d')}.parquet"
    monthly_df.to_parquet(monthly_file, index=False)
    logger.info(f"✅ Saved monthly totals: {monthly_file.name}")
    
    # Summary statistics
    logger.info("\n" + "="*80)
    logger.info("COLLECTION SUMMARY")
    logger.info("="*80)
    logger.info(f"✅ Total records: {len(clean_df):,}")
    logger.info(f"📅 Date range: {clean_df['date'].min().date()} to {clean_df['date'].max().date()}")
    logger.info(f"📊 Monthly records: {len(monthly_df)}")
    
    if not monthly_df.empty:
        logger.info(f"\n📈 Recent imports (last 3 months):")
        recent = monthly_df.tail(3)
        for _, row in recent.iterrows():
            logger.info(f"   {row['date'].strftime('%Y-%m')}: {row['quantity_mt']:,.0f} MT " +
                       f"(${row['trade_value_usd']/1e6:.1f}M)")
    
    # Data quality check
    logger.info(f"\n📊 Data quality:")
    logger.info(f"   Value coverage: {clean_df['trade_value_usd'].notna().mean():.1%}")
    logger.info(f"   Quantity coverage: {clean_df['quantity_mt'].notna().mean():.1%}")
    
    logger.info("\n✅ UN COMTRADE COLLECTION COMPLETE!")
    logger.info("="*80)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
