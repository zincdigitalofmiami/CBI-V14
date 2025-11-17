#!/usr/bin/env python3
"""
World Bank Pink Sheet - Monthly Commodity Prices
=================================================
Collects monthly FOB prices for all major vegetable oils.
Official, long-history source for computing FOB spreads.

Source: World Bank "Pink Sheet" - CMO Historical Data Monthly
URL: https://thedocs.worldbank.org/en/doc/7d1b0a7f8b2f4e22e6c64b6d8a3b6b73-0400082023/related/CMO-Historical-Data-Monthly.xlsx
Coverage: 1960s→present (monthly)
"""

import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import openpyxl

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

# World Bank Pink Sheet XLSX
# Try multiple possible URLs
PINK_SHEET_URLS = [
    "https://thedocs.worldbank.org/en/doc/7d1b0a7f8b2f4e22e6c64b6d8a3b6b73-0400082023/related/CMO-Historical-Data-Monthly.xlsx",
    "https://www.worldbank.org/en/research/commodity-markets",
    "https://www.worldbank.org/en/research/commodity-markets/data"
]

# Key vegetable oils we need
VEGOIL_SHEETS = {
    'soybean_oil_argentina': 'Soybean Oil (Argentina)',
    'palm_oil_malaysia': 'Palm Oil (Malaysia)',
    'sunflower_oil': 'Sunflower Oil',
    'rapeseed_oil': 'Rapeseed Oil'
}

def download_pinksheet() -> Path:
    """
    Download World Bank Pink Sheet XLSX file.
    Tries multiple URLs and methods.
    
    Returns:
        Path to downloaded file or None
    """
    logger.info("Downloading World Bank Pink Sheet...")
    
    local_file = RAW_DIR / "CMO-Historical-Data-Monthly.xlsx"
    
    # Try each URL
    for url in PINK_SHEET_URLS:
        try:
            logger.info(f"  Trying: {url[:80]}...")
            response = requests.get(url, timeout=120, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; CBI-V14-Data-Collector/1.0)',
                'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel, */*'
            }, allow_redirects=True)
            
            if response.status_code == 200:
                # Check if it's actually an Excel file
                content_type = response.headers.get('Content-Type', '')
                if 'excel' in content_type.lower() or 'spreadsheet' in content_type.lower() or url.endswith('.xlsx'):
                    with open(local_file, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"✅ Downloaded: {local_file.name} ({len(response.content)} bytes)")
                    return local_file
                else:
                    logger.warning(f"  Response is not Excel format: {content_type}")
            else:
                logger.warning(f"  HTTP {response.status_code}")
                
        except Exception as e:
            logger.debug(f"  Error with {url}: {e}")
            continue
    
    # If direct download failed, provide instructions
    logger.error("❌ Could not download Pink Sheet automatically")
    logger.error("")
    logger.error("ALTERNATIVE: Manual download required")
    logger.error("1. Visit: https://www.worldbank.org/en/research/commodity-markets")
    logger.error("2. Download 'CMO Historical Data Monthly' XLSX file")
    logger.error(f"3. Save to: {local_file}")
    logger.error("4. Re-run this script")
    
    return None

def parse_pinksheet_sheet(file_path: Path, sheet_name: str) -> pd.DataFrame:
    """
    Parse a specific sheet from the Pink Sheet XLSX.
    
    Args:
        file_path: Path to XLSX file
        sheet_name: Name of sheet to parse
        
    Returns:
        DataFrame with monthly price data
    """
    try:
        # Read Excel sheet
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        
        # Find date column (usually first column or named column)
        # World Bank format varies, but typically has date in first column
        date_col = None
        for col in df.columns:
            if 'date' in str(col).lower() or 'month' in str(col).lower() or 'year' in str(col).lower():
                date_col = col
                break
        
        if date_col is None and len(df.columns) > 0:
            # Try first column
            date_col = df.columns[0]
        
        if date_col:
            # Convert date column
            df['date'] = pd.to_datetime(df[date_col], errors='coerce')
            df = df[df['date'].notna()]  # Remove invalid dates
        
        # Find price column (usually FOB price)
        price_col = None
        for col in df.columns:
            col_lower = str(col).lower()
            if 'price' in col_lower or 'fob' in col_lower or 'usd' in col_lower:
                price_col = col
                break
        
        if price_col is None and len(df.columns) > 1:
            # Try second column
            price_col = df.columns[1]
        
        if price_col:
            df['price_usd_per_mt'] = pd.to_numeric(df[price_col], errors='coerce')
        
        # Add metadata
        df['commodity'] = sheet_name
        df['source'] = 'WORLD_BANK_PINK_SHEET'
        df['updated_at'] = datetime.now()
        
        # Select key columns
        result_cols = ['date', 'price_usd_per_mt', 'commodity', 'source', 'updated_at']
        result_df = df[[col for col in result_cols if col in df.columns]].copy()
        
        return result_df
        
    except Exception as e:
        logger.error(f"Error parsing sheet {sheet_name}: {e}")
        return pd.DataFrame()

def compute_fob_spreads(all_data: dict) -> pd.DataFrame:
    """
    Compute FOB spreads between vegetable oils.
    
    Args:
        all_data: Dict of commodity DataFrames
        
    Returns:
        DataFrame with computed spreads
    """
    if not all_data:
        return pd.DataFrame()
    
    # Combine all commodities
    combined = pd.concat(all_data.values(), ignore_index=True)
    
    # Pivot to wide format (one column per commodity)
    if 'date' in combined.columns and 'price_usd_per_mt' in combined.columns:
        wide = combined.pivot_table(
            index='date',
            columns='commodity',
            values='price_usd_per_mt',
            aggfunc='first'
        ).reset_index()
        
        # Compute spreads
        if 'Soybean Oil (Argentina)' in wide.columns and 'Palm Oil (Malaysia)' in wide.columns:
            wide['spread_sbo_palm'] = wide['Soybean Oil (Argentina)'] - wide['Palm Oil (Malaysia)']
        
        if 'Sunflower Oil' in wide.columns and 'Soybean Oil (Argentina)' in wide.columns:
            wide['spread_sun_sbo'] = wide['Sunflower Oil'] - wide['Soybean Oil (Argentina)']
        
        if 'Rapeseed Oil' in wide.columns and 'Soybean Oil (Argentina)' in wide.columns:
            wide['spread_rapeseed_sbo'] = wide['Rapeseed Oil'] - wide['Soybean Oil (Argentina)']
        
        wide['source'] = 'WORLD_BANK_PINK_SHEET'
        wide['updated_at'] = datetime.now()
        
        return wide
    
    return pd.DataFrame()

def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("WORLD BANK PINK SHEET COLLECTION")
    logger.info("="*80)
    logger.info("Monthly vegetable oil prices (1960s→present)")
    logger.info("="*80)
    
    # Download file
    xlsx_file = download_pinksheet()
    
    if xlsx_file is None:
        logger.error("Failed to download Pink Sheet")
        return 1
    
    # Parse each vegetable oil sheet
    all_commodity_data = {}
    
    for oil_key, sheet_name in VEGOIL_SHEETS.items():
        logger.info(f"\nParsing {sheet_name}...")
        df = parse_pinksheet_sheet(xlsx_file, sheet_name)
        
        if not df.empty:
            all_commodity_data[oil_key] = df
            logger.info(f"  ✅ {len(df)} monthly records")
            
            # Save individual commodity
            commodity_file = RAW_DIR / f"{oil_key}_{datetime.now().strftime('%Y%m%d')}.parquet"
            df.to_parquet(commodity_file, index=False)
        else:
            logger.warning(f"  ⚠️ No data for {sheet_name}")
    
    # Compute FOB spreads
    logger.info("\nComputing FOB spreads...")
    spreads_df = compute_fob_spreads(all_commodity_data)
    
    if not spreads_df.empty:
        spreads_file = RAW_DIR / f"vegoil_spreads_{datetime.now().strftime('%Y%m%d')}.parquet"
        spreads_df.to_parquet(spreads_file, index=False)
        logger.info(f"✅ Saved spreads: {spreads_file.name}")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("COLLECTION SUMMARY")
    logger.info("="*80)
    logger.info(f"✅ Commodities collected: {len(all_commodity_data)}")
    
    for oil_key, df in all_commodity_data.items():
        if 'date' in df.columns:
            logger.info(f"   {oil_key}: {df['date'].min().date()} to {df['date'].max().date()}")
    
    logger.info("\n✅ WORLD BANK PINK SHEET COLLECTION COMPLETE!")
    logger.info("="*80)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
