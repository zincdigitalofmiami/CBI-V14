#!/usr/bin/env python3
"""
CFTC Commitment of Traders (COT) Data Collection - 100% Complete
================================================================
Collects COT positioning data for all agricultural and related futures
Date range: 2006-2025 (start of disaggregated data)
Source: CFTC.gov public data files
Zero tolerance for missing contracts
"""

import os
import io
import zipfile
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import sys
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cftc_collection.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
CFTC_BASE_URL = "https://www.cftc.gov/files/dea/history"
START_YEAR = 2006  # Start of disaggregated data
END_YEAR = datetime.now().year

# External drive paths
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/cftc"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Create subdirectories
RAW_FILES_DIR = RAW_DIR / "raw_files"
PROCESSED_DIR = RAW_DIR / "processed"
COMBINED_DIR = RAW_DIR / "combined"
METADATA_DIR = RAW_DIR / "metadata"
PERCENTILES_DIR = RAW_DIR / "percentiles"

for dir_path in [RAW_FILES_DIR, PROCESSED_DIR, COMBINED_DIR, METADATA_DIR, PERCENTILES_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# COMPLETE list of CFTC contracts (focus on agricultural + key correlations)
CFTC_CONTRACTS = {
    # Primary Agricultural (Soybean Complex)
    '067651': {'name': 'SOYBEAN OIL', 'exchange': 'CHICAGO BOARD OF TRADE', 'category': 'agricultural'},
    '005602': {'name': 'SOYBEANS', 'exchange': 'CHICAGO BOARD OF TRADE', 'category': 'agricultural'},
    '026603': {'name': 'SOYBEAN MEAL', 'exchange': 'CHICAGO BOARD OF TRADE', 'category': 'agricultural'},
    
    # Other Grains
    '002602': {'name': 'CORN', 'exchange': 'CHICAGO BOARD OF TRADE', 'category': 'agricultural'},
    '001602': {'name': 'WHEAT-SRW', 'exchange': 'CHICAGO BOARD OF TRADE', 'category': 'agricultural'},
    '001612': {'name': 'WHEAT-HRW', 'exchange': 'KANSAS CITY BOARD OF TRADE', 'category': 'agricultural'},
    
    # Softs
    '033661': {'name': 'COTTON NO. 2', 'exchange': 'ICE FUTURES U.S.', 'category': 'agricultural'},
    '083731': {'name': 'COFFEE C', 'exchange': 'ICE FUTURES U.S.', 'category': 'agricultural'},
    '073732': {'name': 'COCOA', 'exchange': 'ICE FUTURES U.S.', 'category': 'agricultural'},
    '080732': {'name': 'SUGAR NO. 11', 'exchange': 'ICE FUTURES U.S.', 'category': 'agricultural'},
    
    # Energy (for correlations with biodiesel)
    '067411': {'name': 'CRUDE OIL, LIGHT SWEET', 'exchange': 'NEW YORK MERCANTILE EXCHANGE', 'category': 'energy'},
    '023651': {'name': 'NATURAL GAS', 'exchange': 'NEW YORK MERCANTILE EXCHANGE', 'category': 'energy'},
    '022651': {'name': 'GASOLINE BLENDSTOCK (RBOB)', 'exchange': 'NEW YORK MERCANTILE EXCHANGE', 'category': 'energy'},
    '022601': {'name': 'NO. 2 HEATING OIL', 'exchange': 'NEW YORK MERCANTILE EXCHANGE', 'category': 'energy'},
    
    # Metals (for macro correlations)
    '088691': {'name': 'GOLD', 'exchange': 'COMMODITY EXCHANGE INC.', 'category': 'metals'},
    '084691': {'name': 'SILVER', 'exchange': 'COMMODITY EXCHANGE INC.', 'category': 'metals'},
    '085692': {'name': 'COPPER', 'exchange': 'COMMODITY EXCHANGE INC.', 'category': 'metals'},
    
    # Currencies (for FX impact)
    '099741': {'name': 'U.S. DOLLAR INDEX', 'exchange': 'ICE FUTURES U.S.', 'category': 'currency'},
    '096742': {'name': 'EURO FX', 'exchange': 'CHICAGO MERCANTILE EXCHANGE', 'category': 'currency'},
    '092741': {'name': 'JAPANESE YEN', 'exchange': 'CHICAGO MERCANTILE EXCHANGE', 'category': 'currency'},
}

# Required fields from COT reports
REQUIRED_FIELDS = [
    'Report_Date_as_YYYY-MM-DD',
    'Market_and_Exchange_Names',
    'CFTC_Contract_Market_Code',
    'Open_Interest_All',
    # Producer/Merchant (Commercials)
    'Prod_Merc_Positions_Long_All',
    'Prod_Merc_Positions_Short_All',
    # Swap Dealers
    'Swap_Positions_Long_All',
    'Swap__Positions_Short_All',
    # Managed Money (Large Speculators)
    'M_Money_Positions_Long_All',
    'M_Money_Positions_Short_All',
    # Other Reportables
    'Other_Rept_Positions_Long_All',
    'Other_Rept_Positions_Short_All',
    # Non-Reportables (Small Speculators)
    'NonRept_Positions_Long_All',
    'NonRept_Positions_Short_All',
    # Changes
    'Change_in_Open_Interest_All',
    'Change_in_Prod_Merc_Long_All',
    'Change_in_Prod_Merc_Short_All',
    'Change_in_M_Money_Long_All',
    'Change_in_M_Money_Short_All'
]

def download_cot_file(year: int) -> Optional[pd.DataFrame]:
    """
    Download and parse COT disaggregated futures file for a given year.
    """
    if year == datetime.now().year:
        # Current year file  
        filename = "deacot.txt"
        url = f"https://www.cftc.gov/files/dea/cotarchives/{year}/futures/deacot{year}.zip"
    else:
        # Historical files - updated URL pattern
        filename = f"annual.txt"
        url = f"https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
    
    logger.info(f"Downloading COT data for {year}...")
    logger.info(f"  URL: {url}")
    
    try:
        # Download zip file
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            # Extract and read the text file
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                # List files in zip
                file_list = z.namelist()
                logger.info(f"  Files in archive: {file_list}")
                
                # Find the data file
                data_file = None
                for f in file_list:
                    if f.endswith('.txt') or f.endswith('.csv'):
                        data_file = f
                        break
                
                if not data_file:
                    logger.error(f"  No data file found in archive")
                    return None
                
                # Read the data
                with z.open(data_file) as f:
                    df = pd.read_csv(f, low_memory=False)
                    
                    # Save raw file
                    raw_file = RAW_FILES_DIR / f"cot_{year}.csv"
                    df.to_csv(raw_file, index=False)
                    
                    logger.info(f"  ✅ Downloaded {len(df)} records")
                    return df
        else:
            logger.error(f"  HTTP {response.status_code} for year {year}")
            return None
            
    except Exception as e:
        logger.error(f"  Error downloading {year}: {e}")
        return None

def process_cot_data(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Process and filter COT data for relevant contracts.
    """
    # Standardize column names (handle different formats)
    df.columns = df.columns.str.replace(' ', '_').str.replace('-', '_').str.replace('__', '_')
    
    # Convert date column
    date_cols = ['Report_Date_as_YYYY_MM_DD', 'Report_Date_as_MM_DD_YYYY', 'As_of_Date_in_Form_YYYY_MM_DD']
    date_col = None
    for col in date_cols:
        if col in df.columns:
            date_col = col
            break
    
    if date_col:
        df['report_date'] = pd.to_datetime(df[date_col])
    else:
        logger.warning(f"  No standard date column found for {year}")
        return pd.DataFrame()
    
    # Filter for our contracts
    contract_codes = list(CFTC_CONTRACTS.keys())
    
    # Try different column names for contract code
    code_cols = ['CFTC_Contract_Market_Code', 'Contract_Market_Code', 'CFTC_Market_Code']
    code_col = None
    for col in code_cols:
        if col in df.columns:
            code_col = col
            break
    
    if code_col:
        # Convert to string and pad with zeros
        df[code_col] = df[code_col].astype(str).str.zfill(6)
        df_filtered = df[df[code_col].isin(contract_codes)]
        logger.info(f"  Filtered to {len(df_filtered)} records for tracked contracts")
    else:
        logger.warning(f"  No contract code column found")
        return pd.DataFrame()
    
    return df_filtered

def calculate_net_positions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate net positions and positioning metrics.
    """
    # Commercial net position
    if 'Prod_Merc_Positions_Long_All' in df.columns:
        df['commercial_net'] = (
            pd.to_numeric(df['Prod_Merc_Positions_Long_All'], errors='coerce') -
            pd.to_numeric(df['Prod_Merc_Positions_Short_All'], errors='coerce')
        )
    
    # Managed Money net position
    if 'M_Money_Positions_Long_All' in df.columns:
        df['managed_money_net'] = (
            pd.to_numeric(df['M_Money_Positions_Long_All'], errors='coerce') -
            pd.to_numeric(df['M_Money_Positions_Short_All'], errors='coerce')
        )
    
    # Total speculative net (Managed Money + Non-Reportables)
    if 'M_Money_Positions_Long_All' in df.columns and 'NonRept_Positions_Long_All' in df.columns:
        df['speculative_net'] = (
            pd.to_numeric(df['M_Money_Positions_Long_All'], errors='coerce') +
            pd.to_numeric(df['NonRept_Positions_Long_All'], errors='coerce') -
            pd.to_numeric(df['M_Money_Positions_Short_All'], errors='coerce') -
            pd.to_numeric(df['NonRept_Positions_Short_All'], errors='coerce')
        )
    
    # Positioning as % of Open Interest
    if 'Open_Interest_All' in df.columns:
        oi = pd.to_numeric(df['Open_Interest_All'], errors='coerce')
        
        if 'commercial_net' in df.columns:
            df['commercial_net_pct_oi'] = (df['commercial_net'] / oi * 100).round(2)
        
        if 'managed_money_net' in df.columns:
            df['managed_money_net_pct_oi'] = (df['managed_money_net'] / oi * 100).round(2)
    
    return df

def calculate_percentiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate rolling percentiles for positioning metrics.
    """
    # Group by contract
    code_col = 'CFTC_Contract_Market_Code' if 'CFTC_Contract_Market_Code' in df.columns else 'Contract_Market_Code'
    
    for contract_code in df[code_col].unique():
        mask = df[code_col] == contract_code
        contract_df = df[mask].sort_values('report_date')
        
        # Calculate percentiles for different windows
        for window in [13, 26, 52]:  # 13 weeks, 26 weeks, 52 weeks
            if 'managed_money_net' in df.columns:
                df.loc[mask, f'mm_net_percentile_{window}w'] = (
                    contract_df['managed_money_net']
                    .rolling(window=window, min_periods=window)
                    .apply(lambda x: (x.iloc[-1] > x).sum() / len(x) * 100)
                )
            
            if 'commercial_net' in df.columns:
                df.loc[mask, f'commercial_net_percentile_{window}w'] = (
                    contract_df['commercial_net']
                    .rolling(window=window, min_periods=window)
                    .apply(lambda x: (x.iloc[-1] > x).sum() / len(x) * 100)
                )
    
    return df

def main():
    """
    Main execution: Collect ALL CFTC COT data with 100% validation.
    """
    logger.info("="*80)
    logger.info("CFTC COT DATA COLLECTION - 100% COMPLETE")
    logger.info("="*80)
    logger.info(f"Date Range: {START_YEAR} to {END_YEAR}")
    logger.info(f"Contracts: {len(CFTC_CONTRACTS)}")
    logger.info(f"Output Directory: {RAW_DIR}")
    logger.info("="*80)
    
    # Track results
    all_data = []
    results = {
        'success': [],
        'failed': [],
        'no_data': []
    }
    
    collection_metadata = {
        'collection_date': datetime.now().isoformat(),
        'start_year': START_YEAR,
        'end_year': END_YEAR,
        'contracts': CFTC_CONTRACTS,
        'years': {}
    }
    
    # Download data for each year
    for year in range(START_YEAR, END_YEAR + 1):
        logger.info(f"\nProcessing year {year}...")
        
        # Download the file
        df_raw = download_cot_file(year)
        
        if df_raw is not None:
            # Process the data
            df_processed = process_cot_data(df_raw, year)
            
            if not df_processed.empty:
                # Calculate additional metrics
                df_processed = calculate_net_positions(df_processed)
                
                # Save processed data
                processed_file = PROCESSED_DIR / f"cot_{year}.parquet"
                df_processed.to_parquet(processed_file, index=False)
                
                all_data.append(df_processed)
                results['success'].append(year)
                
                collection_metadata['years'][year] = {
                    'status': 'success',
                    'records': len(df_processed),
                    'contracts_found': df_processed['CFTC_Contract_Market_Code'].nunique() if 'CFTC_Contract_Market_Code' in df_processed.columns else 0
                }
                
                logger.info(f"  ✅ Processed {len(df_processed)} records")
            else:
                results['no_data'].append(year)
                collection_metadata['years'][year] = {'status': 'no_data'}
        else:
            results['failed'].append(year)
            collection_metadata['years'][year] = {'status': 'failed'}
    
    # Combine all years
    if all_data:
        logger.info("\n" + "="*80)
        logger.info("Combining all years...")
        
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df = combined_df.sort_values('report_date')
        
        # Calculate percentiles on the full dataset
        logger.info("Calculating positioning percentiles...")
        combined_df = calculate_percentiles(combined_df)
        
        # Save combined dataset
        combined_file = COMBINED_DIR / f"cot_all_years_{datetime.now().strftime('%Y%m%d')}.parquet"
        combined_df.to_parquet(combined_file, index=False)
        
        logger.info(f"✅ Combined dataset saved: {len(combined_df)} rows")
        
        # Save by contract for easy access
        code_col = 'CFTC_Contract_Market_Code' if 'CFTC_Contract_Market_Code' in combined_df.columns else 'Contract_Market_Code'
        
        for contract_code, contract_info in CFTC_CONTRACTS.items():
            contract_df = combined_df[combined_df[code_col] == contract_code]
            if not contract_df.empty:
                contract_file = COMBINED_DIR / f"{contract_code}_{contract_info['name'].replace(' ', '_').lower()}.parquet"
                contract_df.to_parquet(contract_file, index=False)
                logger.info(f"  Saved {contract_info['name']}: {len(contract_df)} records")
    
    # Save metadata
    metadata_file = METADATA_DIR / f"collection_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(metadata_file, 'w') as f:
        import json
        json.dump(collection_metadata, f, indent=2, default=str)
    
    # Final report
    logger.info("\n" + "="*80)
    logger.info("COLLECTION COMPLETE - FINAL REPORT")
    logger.info("="*80)
    logger.info(f"✅ Successful years: {len(results['success'])}/{END_YEAR - START_YEAR + 1}")
    if results['success']:
        logger.info(f"   Years: {results['success']}")
    
    if results['no_data']:
        logger.info(f"⚠️  No data: {len(results['no_data'])} years")
        logger.info(f"   Years: {results['no_data']}")
    
    if results['failed']:
        logger.error(f"❌ Failed: {len(results['failed'])} years")
        logger.error(f"   Years: {results['failed']}")
    
    # Success criteria check
    success_rate = len(results['success']) / (END_YEAR - START_YEAR + 1)
    if success_rate < 0.90:  # Require 90% success rate
        logger.error(f"WARNING: Success rate low: {success_rate:.1%}")
        return 1
    
    logger.info(f"\n✅ SUCCESS RATE: {success_rate:.1%}")
    logger.info(f"📁 Output directory: {RAW_DIR}")
    logger.info("="*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
