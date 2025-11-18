#!/usr/bin/env python3
"""
World Bank Pink Sheet Alternative - Open Data API
==================================================
Alternative to manual Pink Sheet download using World Bank Open Data API.

Sources:
- World Bank Open Data API (data.worldbank.org)
- Commodity Price Data (Pink Sheet equivalent)
- Monthly prices for vegetable oils and related commodities

Prefix: `worldbank_*` on all columns except `date`

Coverage: 1960s→present (monthly)
"""

import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/wb_pinksheet"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# World Bank Open Data API
WB_API_BASE = "https://api.worldbank.org/v2"

# Key commodity indicators (equivalent to Pink Sheet)
# Format: indicator_code: description
WB_INDICATORS = {
    # Vegetable Oils
    'PALMOIL': 'Palm oil price (Malaysian, FOB)',
    'SOYOIL': 'Soybean oil price (US, FOB)',
    'SUNOIL': 'Sunflower oil price (US, FOB)',
    'RAPOIL': 'Rapeseed oil price (Canadian, FOB)',
    
    # Related Commodities
    'SOYBEAN': 'Soybeans price (US, FOB)',
    'MAIZE': 'Maize (corn) price (US, FOB)',
    'WHEAT': 'Wheat price (US, FOB)',
    'SUGAR': 'Sugar price (world, FOB)',
    
    # Energy (for correlations)
    'CRUDE': 'Crude oil price (Brent)',
}

def fetch_wb_indicator(indicator_code: str, start_date: str = "1960", end_date: str = None) -> pd.DataFrame:
    """
    Fetch commodity price data from World Bank Open Data API.
    
    Args:
        indicator_code: World Bank indicator code (e.g., 'PALMOIL')
        start_date: Start year (default: 1960)
        end_date: End year (default: current year)
    
    Returns:
        DataFrame with date and price columns
    """
    if end_date is None:
        end_date = str(datetime.now().year)
    
    logger.info(f"Fetching {indicator_code} from World Bank API ({start_date}-{end_date})...")
    
    # World Bank API endpoint for commodity prices
    # Format: /v2/country/all/indicator/{indicator}?format=json&date={start}:{end}
    url = f"{WB_API_BASE}/country/all/indicator/{indicator_code}"
    params = {
        'format': 'json',
        'date': f"{start_date}:{end_date}",
        'per_page': 10000  # Get all data
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            # World Bank API returns nested structure: [metadata, [records]]
            # Debug: log structure
            logger.debug(f"  API response structure: {type(data)}, length: {len(data) if isinstance(data, list) else 'N/A'}")
            
            records = []
            if isinstance(data, list) and len(data) >= 2:
                records = data[1] if isinstance(data[1], list) else []
            elif isinstance(data, dict):
                # Try alternative structure
                records = data.get('data', []) or data.get('records', [])
            
            if not records:
                logger.warning(f"  No data returned for {indicator_code} (response structure: {type(data)})")
                # Try alternative: use commodity-specific endpoint
                return fetch_wb_commodity_alternative(indicator_code, start_date, end_date)
            
            # Convert to DataFrame
            df = pd.DataFrame(records)
            
            # World Bank API returns records with 'date' and 'value' fields
            if 'date' not in df.columns or 'value' not in df.columns:
                logger.warning(f"  Missing 'date' or 'value' columns. Available: {list(df.columns)}")
                return pd.DataFrame()
            
            # Extract date and value
            df['date'] = pd.to_datetime(df['date'].astype(str) + '-01', format='%Y-%m-%d', errors='coerce')
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            
            # Rename value column to indicator name
            df = df.rename(columns={'value': f'worldbank_{indicator_code.lower()}_price'})
            
            # Keep only date and price columns, drop NaN values
            df = df[['date', f'worldbank_{indicator_code.lower()}_price']].dropna()
            
            if not df.empty:
                logger.info(f"  ✅ Retrieved {len(df)} records ({df['date'].min()} to {df['date'].max()})")
            return df
        else:
            logger.warning(f"  API returned {response.status_code} for {indicator_code}")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"  Error fetching {indicator_code}: {e}")
        return pd.DataFrame()

def fetch_wb_commodity_alternative(indicator_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Alternative method: Try commodity-specific World Bank endpoints.
    """
    # World Bank commodity price indicators use different codes
    # Try common commodity price indicator codes
    commodity_codes = {
        'PALMOIL': 'PNRG_PALM_USD',  # Palm oil price
        'SOYOIL': 'PNRG_SOYA_USD',   # Soybean oil price
        'SOYBEAN': 'PNRG_SOYA_USD',  # Soybeans
        'MAIZE': 'PNRG_MAIZ_USD',     # Maize
        'WHEAT': 'PNRG_WHEA_USD',    # Wheat
        'CRUDE': 'PNRG_OIL_USD',      # Crude oil
    }
    
    if indicator_code not in commodity_codes:
        return pd.DataFrame()
    
    wb_code = commodity_codes[indicator_code]
    logger.info(f"  Trying alternative indicator code: {wb_code}")
    
    url = f"{WB_API_BASE}/country/all/indicator/{wb_code}"
    params = {
        'format': 'json',
        'date': f"{start_date}:{end_date}",
        'per_page': 10000
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
                records = data[1]
                if records:
                    df = pd.DataFrame(records)
                    if 'date' in df.columns and 'value' in df.columns:
                        df['date'] = pd.to_datetime(df['date'].astype(str) + '-01', format='%Y-%m-%d', errors='coerce')
                        df['value'] = pd.to_numeric(df['value'], errors='coerce')
                        df = df.rename(columns={'value': f'worldbank_{indicator_code.lower()}_price'})
                        df = df[['date', f'worldbank_{indicator_code.lower()}_price']].dropna()
                        logger.info(f"  ✅ Retrieved {len(df)} records via alternative method")
                        return df
    except Exception as e:
        logger.debug(f"  Alternative method failed: {e}")
    
    return pd.DataFrame()

def main():
    """
    Main collection function: Fetch all World Bank commodity prices.
    """
    logger.info("=" * 80)
    logger.info("WORLD BANK PINK SHEET ALTERNATIVE - OPEN DATA API")
    logger.info("=" * 80)
    logger.info("Collecting commodity prices via World Bank Open Data API")
    logger.info("(Alternative to manual Pink Sheet download)")
    logger.info("")
    
    all_dataframes = []
    
    # Fetch each indicator
    for indicator_code, description in WB_INDICATORS.items():
        df = fetch_wb_indicator(indicator_code, start_date="1960")
        if not df.empty:
            all_dataframes.append(df)
        time.sleep(1)  # Rate limiting
    
    if not all_dataframes:
        logger.error("❌ No World Bank data collected")
        return
    
    # Merge all indicators on date
    logger.info("\nMerging all indicators...")
    combined_df = all_dataframes[0].copy()
    for df in all_dataframes[1:]:
        combined_df = combined_df.merge(df, on='date', how='outer')
    
    # Sort by date
    combined_df = combined_df.sort_values('date').reset_index(drop=True)
    
    # Convert date to date type (not datetime)
    combined_df['date'] = pd.to_datetime(combined_df['date']).dt.date
    
    # Save raw data
    output_file = RAW_DIR / f"worldbank_commodity_prices_{datetime.now().strftime('%Y%m%d')}.parquet"
    combined_df.to_parquet(output_file, index=False)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✅ WORLD BANK COLLECTION COMPLETE")
    logger.info(f"   Indicators: {len(all_dataframes)}")
    logger.info(f"   Total rows: {len(combined_df):,}")
    logger.info(f"   Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
    logger.info(f"   Columns: {len(combined_df.columns)}")
    logger.info(f"   Saved to: {output_file}")
    logger.info("=" * 80)
    logger.info("")
    logger.info("NOTE: This is an alternative to the Pink Sheet.")
    logger.info("      If Pink Sheet becomes available, it may have more detailed data.")
    logger.info("      This API provides monthly commodity prices going back to 1960s.")

if __name__ == "__main__":
    main()

