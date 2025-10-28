#!/usr/bin/env python3
"""
EMERGENCY DATA REFRESH - Pull from working sources only
Skip government sites (FRED) during shutdown
"""

import yfinance as yf
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timezone, timedelta
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def pull_yahoo_finance_data():
    """Pull all commodity data from Yahoo Finance (working source)"""
    
    commodities = [
        ('ZL=F', 'soybean_oil'),
        ('ZS=F', 'soybeans'),
        ('ZM=F', 'soybean_meal'),
        ('ZC=F', 'corn'),
        ('ZW=F', 'wheat'),
        ('CL=F', 'crude_oil'),
        ('NG=F', 'natural_gas'),
        ('GC=F', 'gold'),
        ('SI=F', 'silver'),
        ('^VIX', 'vix'),
        ('DX-Y.NYB', 'dollar_index'),
        ('BRL=X', 'usd_brl'),
        ('CNY=X', 'usd_cny')
    ]
    
    all_data = []
    
    for symbol, name in commodities:
        try:
            logger.info(f"Pulling {name} ({symbol})...")
            ticker = yf.Ticker(symbol)
            
            # Get 2 years of data
            data = ticker.history(period='2y')
            
            if not data.empty:
                # Process each row
                for idx, row in data.iterrows():
                    record = {
                        'time': idx.to_pydatetime().replace(tzinfo=timezone.utc),
                        'symbol': symbol,
                        'open': float(row['Open']) if pd.notna(row['Open']) else None,
                        'high': float(row['High']) if pd.notna(row['High']) else None,
                        'low': float(row['Low']) if pd.notna(row['Low']) else None,
                        'close': float(row['Close']) if pd.notna(row['Close']) else None,
                        'volume': int(row['Volume']) if pd.notna(row['Volume']) else 0,
                        'source_name': 'Yahoo_Finance',
                        'confidence_score': 0.95,
                        'ingest_timestamp_utc': datetime.now(timezone.utc),
                        'provenance_uuid': str(uuid.uuid4())
                    }
                    all_data.append(record)
                
                logger.info(f"✅ {name}: {len(data)} days of data collected")
            else:
                logger.warning(f"⚠️ {name}: No data returned")
                
        except Exception as e:
            logger.error(f"❌ {name}: {str(e)}")
    
    return all_data

def store_commodity_data(data_records):
    """Store commodity data in appropriate BigQuery tables"""
    
    # Group by commodity type
    commodity_mapping = {
        'soybean_oil': 'soybean_oil_prices',
        'corn': 'corn_prices',
        'wheat': 'wheat_prices',
        'crude_oil': 'crude_oil_prices',
        'soybeans': 'soybean_prices',
        'soybean_meal': 'soybean_meal_prices',
        'natural_gas': 'natural_gas_prices',
        'gold': 'gold_prices',
        'silver': 'silver_prices'
    }
    
    # Convert symbol to commodity name
    symbol_to_commodity = {
        'ZL=F': 'soybean_oil',
        'ZC=F': 'corn',
        'ZW=F': 'wheat',
        'CL=F': 'crude_oil',
        'ZS=F': 'soybeans',
        'ZM=F': 'soybean_meal',
        'NG=F': 'natural_gas',
        'GC=F': 'gold',
        'SI=F': 'silver'
    }
    
    for commodity, table_name in commodity_mapping.items():
        # Filter records for this commodity
        commodity_data = [r for r in data_records 
                          if symbol_to_commodity.get(r['symbol']) == commodity]
        
        if commodity_data:
            df = pd.DataFrame(commodity_data)
            
            # Remove duplicates based on time
            df = df.drop_duplicates(subset=['time'], keep='last')
            
            table_id = f'cbi-v14.forecasting_data_warehouse.{table_name}'
            
            job_config = bigquery.LoadJobConfig(
                write_disposition='WRITE_APPEND'  # Append to existing data, no schema conflicts
            )
            
            try:
                job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
                job.result()
                logger.info(f"✅ Stored {len(df)} records to {table_name}")
            except Exception as e:
                logger.error(f"❌ Error storing {commodity}: {e}")

def backfill_weather_data():
    """Backfill weather data from available sources"""
    
    # For now, just ensure recent data is there
    logger.info("Weather data backfill would go here...")
    # This would call weather APIs that are still working
    
def main():
    print("="*80)
    print("EMERGENCY DATA REFRESH - GOVERNMENT SHUTDOWN MODE")
    print("="*80)
    print("Skipping FRED API (government shutdown)")
    print("Using alternative sources...")
    print()
    
    # Pull Yahoo Finance data (2 years)
    logger.info("Pulling 2 years of commodity data from Yahoo Finance...")
    yahoo_data = pull_yahoo_finance_data()
    
    if yahoo_data:
        logger.info(f"Collected {len(yahoo_data)} total records")
        
        # Store in BigQuery
        logger.info("Storing data in BigQuery...")
        store_commodity_data(yahoo_data)
    
    # Check final status
    print("\n" + "="*80)
    print("DATA REFRESH COMPLETE")
    print("="*80)
    
    # Verify what we have
    tables = ['soybean_oil_prices', 'corn_prices', 'crude_oil_prices', 'palm_oil_prices']
    for table in tables:
        try:
            query = f"""
            SELECT 
                COUNT(*) as rows,
                MIN(CAST(time AS DATE)) as earliest,
                MAX(CAST(time AS DATE)) as latest
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            """
            result = client.query(query).to_dataframe()
            print(f"✅ {table}: {result['rows'].iloc[0]:,} rows ({result['earliest'].iloc[0]} to {result['latest'].iloc[0]})")
        except:
            print(f"❌ {table}: Error checking")

if __name__ == "__main__":
    main()
