#!/usr/bin/env python3
"""
LOAD ALL MISSING DATA - GET EVERYTHING!
Fill in all the gaps in our training data
"""

import yfinance as yf
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_all_missing_data():
    """Load ALL missing data using yfinance"""
    client = bigquery.Client(project='cbi-v14')
    
    # Define what we need with correct symbols
    symbols_to_load = {
        # RATES & YIELDS
        '^TNX': {
            'table': 'treasury_prices',
            'name': '10Y Treasury Yield',
            'period': 'max'
        },
        '^IRX': {
            'table': 'treasury_prices', 
            'name': '13W Treasury Bill',
            'period': 'max'
        },
        '^FVX': {
            'table': 'treasury_prices',
            'name': '5Y Treasury Yield', 
            'period': 'max'
        },
        
        # CRUDE OIL
        'CL=F': {
            'table': 'crude_oil_prices',
            'name': 'WTI Crude Oil',
            'period': 'max'
        },
        
        # USD INDEX
        'DX-Y.NYB': {
            'table': 'usd_index_prices',
            'name': 'US Dollar Index',
            'period': 'max'
        },
        
        # VIX
        '^VIX': {
            'table': 'vix_daily',
            'name': 'CBOE Volatility Index',
            'period': 'max'
        },
        
        # ADDITIONAL COMMODITIES
        'GC=F': {
            'table': 'gold_prices',
            'name': 'Gold Futures',
            'period': 'max'
        },
        'SI=F': {
            'table': 'silver_prices',
            'name': 'Silver Futures',
            'period': 'max'
        },
        'NG=F': {
            'table': 'natural_gas_prices',
            'name': 'Natural Gas',
            'period': 'max'
        },
        
        # STOCK INDICES (for correlation)
        '^GSPC': {
            'table': 'sp500_prices',
            'name': 'S&P 500',
            'period': 'max'
        },
        
        # CURRENCIES
        'EURUSD=X': {
            'table': 'currency_data',
            'name': 'EUR/USD',
            'period': 'max'
        },
        'BRL=X': {
            'table': 'currency_data',
            'name': 'USD/BRL',
            'period': 'max'
        },
        'CNY=X': {
            'table': 'currency_data',
            'name': 'USD/CNY',
            'period': 'max'
        }
    }
    
    for symbol, config in symbols_to_load.items():
        try:
            logger.info(f"📊 Loading {config['name']} ({symbol})...")
            
            # Download data
            data = yf.download(symbol, period=config['period'], progress=False)
            
            if data.empty:
                logger.warning(f"⚠️  No data returned for {symbol}")
                continue
            
            # Prepare for BigQuery
            data = data.reset_index()
            
            # Determine schema based on table
            if config['table'] in ['treasury_prices', 'vix_daily']:
                # These tables use date, open, high, low, close, volume
                records = []
                for idx, row in data.iterrows():
                    record = {
                        'date': row['Date'].strftime('%Y-%m-%d %H:%M:%S'),
                        'symbol': symbol.replace('^', '').replace('=F', '').replace('-Y.NYB', '').replace('=X', ''),
                        'open': float(row['Open']) if pd.notna(row['Open']) else None,
                        'high': float(row['High']) if pd.notna(row['High']) else None,
                        'low': float(row['Low']) if pd.notna(row['Low']) else None,
                        'close': float(row['Close']) if pd.notna(row['Close']) else None,
                        'volume': int(row['Volume']) if pd.notna(row['Volume']) else 0,
                        'source_name': 'yfinance',
                        'confidence_score': 0.95,
                        'ingest_timestamp_utc': datetime.utcnow().isoformat(),
                        'provenance_uuid': f"yf_{symbol}_{row['Date'].strftime('%Y%m%d')}"
                    }
                    records.append(record)
            
            elif config['table'] in ['crude_oil_prices', 'usd_index_prices', 'gold_prices', 
                                    'silver_prices', 'natural_gas_prices', 'sp500_prices']:
                # These tables use date, open_price, high_price, low_price, close_price, volume
                records = []
                for idx, row in data.iterrows():
                    record = {
                        'date': row['Date'].strftime('%Y-%m-%d'),
                        'symbol': symbol.replace('=F', '').replace('-Y.NYB', 'DXY').replace('^', ''),
                        'open_price': float(row['Open']) if pd.notna(row['Open']) else None,
                        'high_price': float(row['High']) if pd.notna(row['High']) else None,
                        'low_price': float(row['Low']) if pd.notna(row['Low']) else None,
                        'close_price': float(row['Close']) if pd.notna(row['Close']) else None,
                        'volume': int(row['Volume']) if pd.notna(row['Volume']) else 0,
                        'source_name': 'yfinance',
                        'confidence_score': 0.95,
                        'ingest_timestamp_utc': datetime.utcnow().isoformat(),
                        'provenance_uuid': f"yf_{symbol}_{row['Date'].strftime('%Y%m%d')}"
                    }
                    records.append(record)
            
            elif config['table'] == 'currency_data':
                # Currency data has different schema
                records = []
                for idx, row in data.iterrows():
                    record = {
                        'date': row['Date'].strftime('%Y-%m-%d'),
                        'currency_pair': config['name'],
                        'exchange_rate': float(row['Close']) if pd.notna(row['Close']) else None,
                        'open_rate': float(row['Open']) if pd.notna(row['Open']) else None,
                        'high_rate': float(row['High']) if pd.notna(row['High']) else None,
                        'low_rate': float(row['Low']) if pd.notna(row['Low']) else None,
                        'source': 'yfinance',
                        'confidence_score': 0.95,
                        'ingest_timestamp_utc': datetime.utcnow().isoformat()
                    }
                    records.append(record)
            
            # Load to BigQuery
            if records:
                table_id = f"cbi-v14.forecasting_data_warehouse.{config['table']}"
                
                # Check if table exists, if not create it
                try:
                    client.get_table(table_id)
                except:
                    logger.info(f"Creating table {table_id}...")
                    # Table doesn't exist, create it based on first record
                    from google.cloud.bigquery import SchemaField, Table
                    
                    schema = []
                    for key, value in records[0].items():
                        if isinstance(value, str):
                            schema.append(SchemaField(key, "STRING"))
                        elif isinstance(value, float):
                            schema.append(SchemaField(key, "FLOAT64"))
                        elif isinstance(value, int):
                            schema.append(SchemaField(key, "INT64"))
                        else:
                            schema.append(SchemaField(key, "STRING"))
                    
                    table = Table(table_id, schema=schema)
                    client.create_table(table)
                
                # Insert data
                errors = client.insert_rows_json(table_id, records)
                
                if errors:
                    logger.error(f"❌ Error loading {symbol}: {errors}")
                else:
                    logger.info(f"✅ Loaded {len(records)} records for {config['name']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load {symbol}: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("🎯 ALL DATA LOADING COMPLETE!")
    logger.info("="*80)

if __name__ == "__main__":
    load_all_missing_data()
