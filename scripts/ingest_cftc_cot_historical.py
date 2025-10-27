#!/usr/bin/env python3
"""
Ingest historical CFTC Commitment of Traders (COT) data
This is CRITICAL for understanding market positioning and reversals
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import logging
from google.cloud import bigquery
import io
import zipfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

# CFTC Historical data URL
CFTC_HISTORICAL_URL = "https://www.cftc.gov/files/dea/history/deacot1986_2016.zip"
CFTC_RECENT_URL = "https://www.cftc.gov/files/dea/history/deacot2017_2024.zip"
CFTC_CURRENT_URL = "https://www.cftc.gov/dea/newcot/deafut.txt"

# Commodity codes we care about
COMMODITY_CODES = {
    '001602': 'SOYBEAN_OIL',     # ZL
    '005602': 'SOYBEANS',        # ZS  
    '002602': 'CORN',            # ZC
    '001612': 'WHEAT_SRW',       # ZW
    '067651': 'WTI_CRUDE',       # CL
    '033661': 'COTTON',          # CT
    '088691': 'SOYBEAN_MEAL',    # ZM
}

def download_and_parse_cot_data():
    """Download and parse CFTC COT historical data"""
    
    all_data = []
    
    # Download recent data (2017-2024)
    logger.info("Downloading CFTC COT data 2017-2024...")
    try:
        response = requests.get(CFTC_RECENT_URL)
        response.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            # Find the annual file
            for filename in zip_file.namelist():
                if filename.endswith('.txt'):
                    logger.info(f"Processing {filename}")
                    
                    # Read the CSV data
                    with zip_file.open(filename) as file:
                        df = pd.read_csv(file)
                        
                        # Filter for our commodities
                        df_filtered = df[df['CFTC_Commodity_Code'].astype(str).str.zfill(6).isin(COMMODITY_CODES.keys())]
                        
                        if not df_filtered.empty:
                            all_data.append(df_filtered)
                            logger.info(f"  Found {len(df_filtered)} records for our commodities")
    
    except Exception as e:
        logger.error(f"Error downloading recent data: {e}")
    
    # Download current year data
    logger.info("Downloading current year CFTC COT data...")
    try:
        response = requests.get(CFTC_CURRENT_URL)
        response.raise_for_status()
        
        df_current = pd.read_csv(io.StringIO(response.text))
        df_filtered = df_current[df_current['CFTC_Commodity_Code'].astype(str).str.zfill(6).isin(COMMODITY_CODES.keys())]
        
        if not df_filtered.empty:
            all_data.append(df_filtered)
            logger.info(f"  Found {len(df_filtered)} current records")
    
    except Exception as e:
        logger.error(f"Error downloading current data: {e}")
    
    if all_data:
        # Combine all data
        df_combined = pd.concat(all_data, ignore_index=True)
        return process_cot_data(df_combined)
    else:
        logger.error("No data downloaded")
        return None

def process_cot_data(df):
    """Process COT data into our schema"""
    
    logger.info(f"Processing {len(df)} total COT records...")
    
    # Map commodity codes
    df['commodity'] = df['CFTC_Commodity_Code'].astype(str).str.zfill(6).map(COMMODITY_CODES)
    
    # Create processed dataframe
    processed = pd.DataFrame({
        'report_date': pd.to_datetime(df['Report_Date_as_YYYY-MM-DD']),
        'commodity': df['commodity'],
        'contract_market_name': df['Market_and_Exchange_Names'],
        
        # MANAGED MONEY (Hedge Funds) - KEY INDICATOR
        'managed_money_long': df['M_Money_Positions_Long_All'],
        'managed_money_short': df['M_Money_Positions_Short_All'],
        'managed_money_net': df['M_Money_Positions_Long_All'] - df['M_Money_Positions_Short_All'],
        'managed_money_spread': df['M_Money_Positions_Spread_All'],
        
        # PRODUCERS/MERCHANTS (Commercials)
        'commercial_long': df['Prod_Merc_Positions_Long_All'],
        'commercial_short': df['Prod_Merc_Positions_Short_All'],
        'commercial_net': df['Prod_Merc_Positions_Long_All'] - df['Prod_Merc_Positions_Short_All'],
        
        # SWAP DEALERS
        'swap_dealer_long': df['Swap_Positions_Long_All'],
        'swap_dealer_short': df['Swap_Positions_Short_All'],
        'swap_dealer_net': df['Swap_Positions_Long_All'] - df['Swap_Positions_Short_All'],
        
        # OTHER REPORTABLES
        'other_reportable_long': df['Other_Rept_Positions_Long_All'],
        'other_reportable_short': df['Other_Rept_Positions_Short_All'],
        
        # NON-REPORTABLES (Small Traders)
        'nonreportable_long': df['NonRept_Positions_Long_All'],
        'nonreportable_short': df['NonRept_Positions_Short_All'],
        
        # OPEN INTEREST
        'open_interest': df['Open_Interest_All'],
        
        # CHANGES FROM LAST WEEK
        'managed_money_change': df['Change_in_M_Money_Long_All'] - df['Change_in_M_Money_Short_All'],
        'commercial_change': df['Change_in_Prod_Merc_Long_All'] - df['Change_in_Prod_Merc_Short_All'],
        
        # METADATA
        'source_name': 'CFTC_COT',
        'confidence_score': 1.0,
        'ingest_timestamp_utc': datetime.utcnow()
    })
    
    # Calculate additional features
    processed['managed_money_net_pct'] = processed['managed_money_net'] / processed['open_interest']
    processed['commercial_net_pct'] = processed['commercial_net'] / processed['open_interest']
    
    # Calculate positioning extremes (for reversal signals)
    for commodity in processed['commodity'].unique():
        mask = processed['commodity'] == commodity
        commodity_data = processed[mask].copy()
        
        # Rolling percentiles (52-week)
        processed.loc[mask, 'managed_money_percentile'] = commodity_data['managed_money_net'].rolling(52, min_periods=1).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1]
        )
        
        processed.loc[mask, 'commercial_percentile'] = commodity_data['commercial_net'].rolling(52, min_periods=1).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1]
        )
    
    # Identify extreme positioning
    processed['extreme_bullish'] = (processed['managed_money_percentile'] > 0.9).astype(int)
    processed['extreme_bearish'] = (processed['managed_money_percentile'] < 0.1).astype(int)
    
    logger.info(f"Processed {len(processed)} records")
    logger.info(f"Date range: {processed['report_date'].min()} to {processed['report_date'].max()}")
    logger.info(f"Commodities: {processed['commodity'].unique()}")
    
    return processed

def load_to_bigquery(df):
    """Load processed COT data to BigQuery"""
    
    table_id = "cbi-v14.forecasting_data_warehouse.cftc_cot"
    
    # Configure load job
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Replace existing data
        schema=[
            bigquery.SchemaField("report_date", "DATE"),
            bigquery.SchemaField("commodity", "STRING"),
            bigquery.SchemaField("contract_market_name", "STRING"),
            bigquery.SchemaField("managed_money_long", "INTEGER"),
            bigquery.SchemaField("managed_money_short", "INTEGER"),
            bigquery.SchemaField("managed_money_net", "INTEGER"),
            bigquery.SchemaField("managed_money_spread", "INTEGER"),
            bigquery.SchemaField("commercial_long", "INTEGER"),
            bigquery.SchemaField("commercial_short", "INTEGER"),
            bigquery.SchemaField("commercial_net", "INTEGER"),
            bigquery.SchemaField("swap_dealer_long", "INTEGER"),
            bigquery.SchemaField("swap_dealer_short", "INTEGER"),
            bigquery.SchemaField("swap_dealer_net", "INTEGER"),
            bigquery.SchemaField("other_reportable_long", "INTEGER"),
            bigquery.SchemaField("other_reportable_short", "INTEGER"),
            bigquery.SchemaField("nonreportable_long", "INTEGER"),
            bigquery.SchemaField("nonreportable_short", "INTEGER"),
            bigquery.SchemaField("open_interest", "INTEGER"),
            bigquery.SchemaField("managed_money_change", "INTEGER"),
            bigquery.SchemaField("commercial_change", "INTEGER"),
            bigquery.SchemaField("managed_money_net_pct", "FLOAT64"),
            bigquery.SchemaField("commercial_net_pct", "FLOAT64"),
            bigquery.SchemaField("managed_money_percentile", "FLOAT64"),
            bigquery.SchemaField("commercial_percentile", "FLOAT64"),
            bigquery.SchemaField("extreme_bullish", "INTEGER"),
            bigquery.SchemaField("extreme_bearish", "INTEGER"),
            bigquery.SchemaField("source_name", "STRING"),
            bigquery.SchemaField("confidence_score", "FLOAT64"),
            bigquery.SchemaField("ingest_timestamp_utc", "TIMESTAMP"),
        ]
    )
    
    # Load data
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        logger.info(f"✅ Loaded {len(df)} rows to {table_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to load to BigQuery: {e}")
        return False

def main():
    """Main execution function"""
    
    logger.info("=" * 70)
    logger.info("CFTC COT DATA INGESTION")
    logger.info("=" * 70)
    logger.info("\nThis is CRITICAL data showing:")
    logger.info("• What hedge funds are doing (managed money)")
    logger.info("• What commercials are hedging")
    logger.info("• Extreme positioning for reversals")
    logger.info("• Smart money vs dumb money")
    
    # Download and process
    logger.info("\nStep 1: Downloading COT data...")
    df = download_and_parse_cot_data()
    
    if df is not None and not df.empty:
        # Load to BigQuery
        logger.info("\nStep 2: Loading to BigQuery...")
        success = load_to_bigquery(df)
        
        if success:
            # Show summary statistics
            logger.info("\n" + "=" * 70)
            logger.info("SUCCESS! COT Data Loaded")
            logger.info("=" * 70)
            
            # Check soybean oil specific data
            zl_data = df[df['commodity'] == 'SOYBEAN_OIL']
            if not zl_data.empty:
                logger.info(f"\nSoybean Oil (ZL) Statistics:")
                logger.info(f"  Records: {len(zl_data)}")
                logger.info(f"  Date Range: {zl_data['report_date'].min()} to {zl_data['report_date'].max()}")
                logger.info(f"  Current Net Position: {zl_data.iloc[-1]['managed_money_net']:,}")
                logger.info(f"  Current Percentile: {zl_data.iloc[-1]['managed_money_percentile']:.1%}")
                
                if zl_data.iloc[-1]['extreme_bullish']:
                    logger.warning("  ⚠️ EXTREME BULLISH positioning - potential reversal!")
                elif zl_data.iloc[-1]['extreme_bearish']:
                    logger.warning("  ⚠️ EXTREME BEARISH positioning - potential reversal!")
            
            logger.info("\n✅ Dashboard Features Now Enabled:")
            logger.info("  • Smart Money Positioning gauge")
            logger.info("  • Extreme positioning alerts")
            logger.info("  • Commercial vs Speculator divergence")
            logger.info("  • COT-based reversal signals")
    else:
        logger.error("Failed to download or process COT data")

if __name__ == "__main__":
    main()
