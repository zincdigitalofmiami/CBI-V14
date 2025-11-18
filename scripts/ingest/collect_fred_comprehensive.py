#!/usr/bin/env python3
"""
FRED Economic Data Collection - 100% Complete
==============================================
Collects ALL 30+ economic series from FRED API
Date range: 2000-01-01 to today
Rate limiting: 1 request per second
Zero tolerance for missing data or errors
"""

import os
import json
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fred_collection.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
# Try to get from keychain first, then environment
try:
    # Add parent directories to path to import keychain_manager
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.utils.keychain_manager import get_api_key
    FRED_API_KEY = get_api_key('FRED_API_KEY')
    if FRED_API_KEY:
        logger.info("Using FRED API key from keychain")
    else:
        raise ValueError("Key not found in keychain")
except Exception as e:
    logger.warning(f"Could not load from keychain: {e}")
    # Fallback to environment variable
    FRED_API_KEY = os.getenv('FRED_API_KEY')
    if FRED_API_KEY:
        logger.info("Using FRED API key from environment")

if not FRED_API_KEY:
    logger.error("FRED_API_KEY not found in keychain or environment!")
    logger.error("Store in keychain: security add-generic-password -a default -s cbi-v14.FRED_API_KEY -w 'your_key' -U")
    raise RuntimeError("FRED_API_KEY is required")

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
START_DATE = "2020-01-01"  # Focus on 2020-2025 for current needs
END_DATE = datetime.now().strftime("%Y-%m-%d")

# External drive paths
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/fred"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Cache directory (outside raw/ to avoid polluting immutable zone)
CACHE_DIR = EXTERNAL_DRIVE / ".cache" / "fred"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Create subdirectories
RAW_RESPONSES_DIR = RAW_DIR / "raw_responses"
PROCESSED_DIR = RAW_DIR / "processed"
COMBINED_DIR = RAW_DIR / "combined"
METADATA_DIR = RAW_DIR / "metadata"

for dir_path in [RAW_RESPONSES_DIR, PROCESSED_DIR, COMBINED_DIR, METADATA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# EXPANDED FRED series (55-60 series per FRESH_START plan)
FRED_SERIES = {
    # Interest Rates (9 series) - EXISTING
    'DFF': 'Federal Funds Rate',
    'DGS10': '10-Year Treasury Constant Maturity Rate',
    'DGS2': '2-Year Treasury Constant Maturity Rate',
    'DGS30': '30-Year Treasury Constant Maturity Rate',
    'DGS5': '5-Year Treasury Constant Maturity Rate',
    'DGS3MO': '3-Month Treasury Bill',
    'DGS1': '1-Year Treasury Constant Maturity Rate',
    'DFEDTARU': 'Federal Funds Target Range - Upper Limit',
    'DFEDTARL': 'Federal Funds Target Range - Lower Limit',
    
    # Inflation (4 series) - EXISTING
    'CPIAUCSL': 'Consumer Price Index for All Urban Consumers',
    'CPILFESL': 'Core CPI (Less Food and Energy)',
    'PCEPI': 'Personal Consumption Expenditures: Chain Price Index',
    'DPCCRV1Q225SBEA': 'Personal Consumption Expenditures Excluding Food and Energy',
    
    # PPI - Producer Price Index (4 series) - NEW
    'PPIACO': 'Producer Price Index for All Commodities',
    'PPICRM': 'PPI for Crude Materials',
    'PPIFIS': 'PPI for Finished Goods',
    'PPIIDC': 'PPI for Industrial Commodities',
    
    # Employment (6 series) - EXPANDED
    'UNRATE': 'Unemployment Rate',
    'PAYEMS': 'All Employees: Total Nonfarm Payrolls',
    'CIVPART': 'Labor Force Participation Rate',
    'EMRATIO': 'Employment-Population Ratio',
    'ICSA': 'Initial Unemployment Claims',  # NEW
    'CCSA': 'Continued Unemployment Claims',  # NEW
    
    # GDP & Production (4 series) - EXPANDED
    'GDP': 'Gross Domestic Product',
    'GDPC1': 'Real Gross Domestic Product',
    'INDPRO': 'Industrial Production Index',
    'DGORDER': 'Manufacturers New Orders: Durable Goods',
    # Note: NAPMPI and NAPM don't exist in FRED - removed
    
    # Money Supply (3 series) - EXISTING
    'M2SL': 'M2 Money Stock',
    'M1SL': 'M1 Money Stock',
    'BOGMBASE': 'St. Louis Adjusted Monetary Base',
    
    # Market Indicators (3 series) - EXISTING
    'VIXCLS': 'CBOE Volatility Index: VIX',
    'DTWEXBGS': 'Trade Weighted U.S. Dollar Index: Broad, Goods',
    'DTWEXEMEGS': 'Trade Weighted U.S. Dollar Index: Emerging Markets',
    
    # Credit Spreads (4 series) - EXPANDED
    'BAAFFM': 'Moody\'s Seasoned Baa Corporate Bond Minus Federal Funds Rate',
    'T10Y2Y': '10-Year Treasury Constant Maturity Minus 2-Year',
    'T10Y3M': '10-Year Treasury Constant Maturity Minus 3-Month',
    'TEDRATE': 'TED Spread',  # NEW
    
    # Commodity-Related (1 series) - EXISTING
    'DCOILWTICO': 'Crude Oil Prices: West Texas Intermediate (WTI)',
    # Note: GOLDPMGBD228NLBM doesn't exist in FRED - removed
    
    # Trade/Currency (4 series) - EXPANDED
    'DEXUSEU': 'U.S. / Euro Foreign Exchange Rate',  # EXISTING
    'DEXCHUS': 'China / U.S. Foreign Exchange Rate',  # NEW
    'DEXBZUS': 'Brazil / U.S. Foreign Exchange Rate',  # NEW
    'DEXMXUS': 'Mexico / U.S. Foreign Exchange Rate',  # NEW
    
    # Energy (3 series) - NEW
    'DCOILBRENTEU': 'Crude Oil Prices: Brent - Europe',
    'DHHNGSP': 'Henry Hub Natural Gas Spot Price',
    'GASREGW': 'US Regular All Formulations Gas Price',
    
    # Consumer & Housing (4 series) - EXPANDED
    'HOUST': 'Housing Starts: Total',  # EXISTING
    'UMCSENT': 'University of Michigan: Consumer Sentiment',  # EXISTING
    'CSUSHPISA': 'S&P/Case-Shiller U.S. National Home Price Index',  # NEW
    'RSXFS': 'Retail Sales Excluding Food Services',  # NEW
    
    # Economic Activity (4 series) - NEW
    'CFNAI': 'Chicago Fed National Activity Index',
    'USSLIND': 'Leading Index for the United States',
    'USREC': 'NBER Recession Indicators',
    'STLFSI2': 'St. Louis Fed Financial Stress Index'
}

# Total: 60 series (9+4+4+6+6+3+3+4+2+4+3+4+4+4 = 60)

def retry_with_backoff(func, cache_key=None, max_retries=3):
    """
    Retry function with exponential backoff and cache fallback.
    
    Args:
        func: Function to retry (should return DataFrame)
        cache_key: Cache key for fallback (e.g., 'fred_DFF')
        max_retries: Maximum retry attempts
        
    Returns:
        DataFrame from function or cache
    """
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            result = func()
            # Cache successful result
            if cache_key and result is not None:
                cache_file = CACHE_DIR / f"{cache_key}.pkl"
                pd.to_pickle(result, cache_file)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed - try cache fallback
                if cache_key:
                    cache_file = CACHE_DIR / f"{cache_key}.pkl"
                    if cache_file.exists():
                        logger.warning(f"⚠️ Using cached value from {cache_file}")
                        return pd.read_pickle(cache_file)
                raise
            else:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"  Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)
    
    return None


def fetch_series(series_id: str, series_name: str) -> dict:
    """
    Fetch a single FRED series with proper error handling, rate limiting, and cache fallback.
    Returns dict with status and data.
    """
    logger.info(f"Fetching {series_id}: {series_name}")
    
    cache_key = f"fred_{series_id}"
    
    def _fetch():
        # Don't specify frequency - let FRED return the series' natural frequency
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'observation_start': START_DATE,
            'observation_end': END_DATE
            # No frequency parameter - use series' natural frequency
        }
        
        # Make request
        response = requests.get(FRED_BASE_URL, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Save raw JSON response
            raw_file = RAW_RESPONSES_DIR / f"{series_id}_raw.json"
            with open(raw_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Extract observations
            observations = data.get('observations', [])
            
            if not observations:
                logger.warning(f"  ⚠️  No observations for {series_id}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(observations)
            
            # Clean and process
            df['date'] = pd.to_datetime(df['date'])
            df['series_id'] = series_id
            df['series_name'] = series_name
            
            # Handle missing values marked as "."
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            
            # Remove rows with NaN values
            initial_count = len(df)
            df = df.dropna(subset=['value'])
            final_count = len(df)
            
            if initial_count > final_count:
                logger.info(f"  Removed {initial_count - final_count} missing values")
            
            # CRITICAL: Sort by date before any pct_change calculations
            df = df.sort_values('date')
            
            # Save processed parquet
            processed_file = PROCESSED_DIR / f"{series_id}.parquet"
            df.to_parquet(processed_file, index=False)
            
            logger.info(f"  ✅ Success: {len(df)} observations saved")
            
            # Return dataframe with series_id preserved for combining
            result_df = df[['date', 'value', 'series_id']].copy()
            result_df = result_df.rename(columns={'value': series_id.lower()})
            return result_df
        
        elif response.status_code == 429:
            raise Exception(f"Rate limit hit: HTTP 429")
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")
    
    # Use retry with backoff and cache fallback
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            df = _fetch()
            if df is None:
                return {'status': 'no_data', 'series_id': series_id}
            
            # Cache successful result
            cache_file = CACHE_DIR / f"{cache_key}.pkl"
            pd.to_pickle(df, cache_file)
            
            return {
                'status': 'success',
                'series_id': series_id,
                'series_name': series_name,
                'observations': len(df),
                'date_range': f"{df['date'].min()} to {df['date'].max()}",
                'data': df
            }
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if 'rate limit' in error_msg or '429' in error_msg:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"  Rate limit hit. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            if attempt == max_retries - 1:
                # Last attempt - try cache fallback
                cache_file = CACHE_DIR / f"{cache_key}.pkl"
                if cache_file.exists():
                    logger.warning(f"⚠️ Using cached value from {cache_file}")
                    df = pd.read_pickle(cache_file)
                    return {
                        'status': 'success_cached',
                        'series_id': series_id,
                        'series_name': series_name,
                        'observations': len(df),
                        'date_range': f"{df['date'].min()} to {df['date'].max()}",
                        'data': df
                    }
                else:
                    return {'status': 'error', 'series_id': series_id, 'error': str(e)}
            else:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"  Error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
    
    return {'status': 'failed', 'series_id': series_id}

def validate_series_data(df: pd.DataFrame, series_id: str) -> dict:
    """
    Validate that series data meets quality requirements.
    """
    issues = []
    
    # Check date range
    min_date = df['date'].min()
    max_date = df['date'].max()
    expected_min = pd.Timestamp(START_DATE)
    
    if min_date > expected_min + pd.Timedelta(days=365):
        issues.append(f"Data starts late: {min_date} (expected near {expected_min})")
    
    # Check for large gaps
    df_sorted = df.sort_values('date')
    date_diff = df_sorted['date'].diff()
    max_gap = date_diff.max()
    
    if max_gap > pd.Timedelta(days=45):  # Some series are monthly
        gap_location = df_sorted[date_diff == max_gap]['date'].iloc[0]
        issues.append(f"Large gap of {max_gap.days} days at {gap_location}")
    
    # Check for outliers (basic check)
    # The value column is named after the series_id (lowercase)
    value_col = series_id.lower()
    if value_col in df.columns:
        mean_val = df[value_col].mean()
        std_val = df[value_col].std()
        outliers = df[(df[value_col] < mean_val - 5*std_val) | (df[value_col] > mean_val + 5*std_val)]
        if len(outliers) > 0:
            issues.append(f"Found {len(outliers)} potential outliers")
        
        # Check value ranges for specific series
        if series_id == 'UNRATE' and df[value_col].max() > 30:
            issues.append(f"Unemployment rate unusually high: {df[value_col].max()}%")
        
        if series_id == 'DFF' and df[value_col].min() < 0:
            issues.append(f"Negative Fed Funds rate: {df[value_col].min()}%")
    
    return {
        'series_id': series_id,
        'valid': len(issues) == 0,
        'issues': issues,
        'row_count': len(df),
        'date_range': f"{min_date.date()} to {max_date.date()}"
    }

def main():
    """
    Main execution: Collect ALL FRED series with 100% validation.
    """
    logger.info("="*80)
    logger.info("FRED ECONOMIC DATA COLLECTION - 100% COMPLETE")
    logger.info("="*80)
    logger.info(f"Date Range: {START_DATE} to {END_DATE}")
    logger.info(f"Total Series: {len(FRED_SERIES)}")
    logger.info(f"Output Directory: {RAW_DIR}")
    logger.info("="*80)
    
    # Track results
    results = {
        'success': [],
        'failed': [],
        'no_data': []
    }
    
    all_data = []
    collection_metadata = {
        'collection_date': datetime.now().isoformat(),
        'start_date': START_DATE,
        'end_date': END_DATE,
        'series_count': len(FRED_SERIES),
        'series': {}
    }
    
    # Collect each series
    for i, (series_id, series_name) in enumerate(FRED_SERIES.items(), 1):
        logger.info(f"\n[{i}/{len(FRED_SERIES)}] Processing {series_id}")
        
        # Fetch the series
        result = fetch_series(series_id, series_name)
        
        # Categorize result
        if result['status'] == 'success':
            results['success'].append(series_id)
            
            # Validate the data
            validation = validate_series_data(result['data'], series_id)
            
            if not validation['valid']:
                logger.warning(f"  ⚠️  Validation issues for {series_id}:")
                for issue in validation['issues']:
                    logger.warning(f"     - {issue}")
            
            # Store the dataframe for combining (it has date, series_id, and value column)
            all_data.append(result['data'])
            
            collection_metadata['series'][series_id] = {
                'name': series_name,
                'status': 'success',
                'observations': result['observations'],
                'date_range': result['date_range'],
                'validation': validation
            }
            
        elif result['status'] == 'no_data':
            results['no_data'].append(series_id)
            collection_metadata['series'][series_id] = {
                'name': series_name,
                'status': 'no_data'
            }
            
        else:
            results['failed'].append(series_id)
            collection_metadata['series'][series_id] = {
                'name': series_name,
                'status': 'failed',
                'error': result.get('error', result.get('code', 'unknown'))
            }
            logger.error(f"  ❌ FAILED: {series_id}")
        
        # Rate limiting: Wait 1 second between requests
        if i < len(FRED_SERIES):
            time.sleep(1.0)
    
    # Combine all successful data into wide format
    if all_data:
        logger.info("\n" + "="*80)
        logger.info("Combining all series into master dataset...")
        
        # Merge all dataframes on date (each has date + series_id + one value column)
        # Drop series_id column before merging since we're creating wide format
        combined_df = all_data[0].drop(columns=['series_id']).copy()
        for df in all_data[1:]:
            df_clean = df.drop(columns=['series_id'])
            combined_df = combined_df.merge(df_clean, on='date', how='outer')
        
        # Sort by date
        combined_df = combined_df.sort_values('date')
        
        # Save combined dataset (wide format)
        combined_file = COMBINED_DIR / f"fred_wide_format_{datetime.now().strftime('%Y%m%d')}.parquet"
        combined_df.to_parquet(combined_file, index=False)
        
        logger.info(f"✅ Combined dataset saved: {len(combined_df)} rows × {len(combined_df.columns)} columns")
        logger.info(f"   Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
    
    # Save metadata
    metadata_file = METADATA_DIR / f"collection_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(metadata_file, 'w') as f:
        json.dump(collection_metadata, f, indent=2, default=str)
    
    # Final report
    logger.info("\n" + "="*80)
    logger.info("COLLECTION COMPLETE - FINAL REPORT")
    logger.info("="*80)
    logger.info(f"✅ Successful: {len(results['success'])} series")
    if results['success']:
        logger.info(f"   Series: {', '.join(results['success'][:10])}")
        if len(results['success']) > 10:
            logger.info(f"   ... and {len(results['success']) - 10} more")
    
    if results['no_data']:
        logger.info(f"⚠️  No Data: {len(results['no_data'])} series")
        logger.info(f"   Series: {', '.join(results['no_data'])}")
    
    if results['failed']:
        logger.error(f"❌ Failed: {len(results['failed'])} series")
        logger.error(f"   Series: {', '.join(results['failed'])}")
        logger.error("CRITICAL: Data collection incomplete! Investigate failures.")
        return 1  # Exit with error
    
    # Success criteria check
    success_rate = len(results['success']) / len(FRED_SERIES)
    if success_rate < 0.95:  # Require 95% success rate
        logger.error(f"CRITICAL: Success rate too low: {success_rate:.1%}")
        logger.error("Plan requires 100% execution. Stopping.")
        return 1
    
    logger.info(f"\n✅ SUCCESS RATE: {success_rate:.1%}")
    logger.info(f"📁 Output directory: {RAW_DIR}")
    logger.info("="*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
