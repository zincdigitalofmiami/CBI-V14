#!/usr/bin/env python3
"""
Bulk CSV Loader for CBI-V14 Historical Data
Handles 20-year datasets for all symbols (rates, dollar, soy, wheat, oil, corn, notes)
Uses CBI-V14 standard BigQuery utilities with db_dtypes for type conversion
"""
import pandas as pd
import zipfile
import tempfile
import shutil
from pathlib import Path
from google.cloud import bigquery
from datetime import datetime, timezone
import uuid
import argparse
import logging
import db_dtypes  # For automatic pandas -> BigQuery type conversion
from bigquery_utils import safe_load_to_bigquery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BulkCSVLoader:
    def __init__(self, project_id='cbi-v14'):
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        
        # Research-based FX weights (soybean oil correlation impact)
        self.fx_weights = {
            'USDMYR': 0.15,  # Malaysia palm oil correlation
            'USDCNY': 0.25,  # China trade impact (highest)
            'USDARS': 0.10,  # Argentina soy production
            'USDBRL': 0.20,  # Brazil soy/weather correlation
            'EURUSD': 0.15,  # European demand
            'USDJPY': 0.15   # Asian market sentiment
        }
        
        # Research-based Treasury weights (monetary policy impact)
        self.treasury_weights = {
            'TNX': 0.40,    # 10Y Treasury - primary rate benchmark
            'FFR': 0.35,    # Fed Funds Rate - monetary policy
            'ZNZ': 0.15,    # Treasury futures
            'FIX': 0.10     # Fixed income derivatives
        }
        
        # Commodity symbols that need strict deduplication
        self.commodity_symbols = ['ZL', 'ZS', 'ZM', 'ZC', 'ZW', 'CL', 'CT']
        
        # Biofuel symbols (ethanol impact on soy oil)
        self.biofuel_symbols = ['BDOV', 'ETH', 'RIN']

    def extract_zip(self, zip_path: Path, extract_to: Path) -> list:
        """Extract zip file and return list of CSV files"""
        csv_files = []
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            for file in extract_to.rglob('*.csv'):
                csv_files.append(file)
        return csv_files

    def detect_symbol_type(self, filename: str) -> tuple:
        """Detect symbol and target table from filename with enhanced categorization"""
        filename = filename.lower()

        # FOREX PAIRS (Research-weighted)
        if any(x in filename for x in ['usdmyr', 'myr', 'ringgit']):
            return 'USDMYR', 'currency_data'
        elif any(x in filename for x in ['usdcny', 'cny', 'yuan']):
            return 'USDCNY', 'currency_data'
        elif any(x in filename for x in ['usdars', 'ars', 'peso']):
            return 'USDARS', 'currency_data'
        elif any(x in filename for x in ['usdbrl', 'brl', 'real']):
            return 'USDBRL', 'currency_data'
        elif any(x in filename for x in ['eurusd', 'eur']):
            return 'EURUSD', 'currency_data'
        elif any(x in filename for x in ['usdjpy', 'jpy', 'yen']):
            return 'USDJPY', 'currency_data'

        # COMMODITY FUTURES (Deduplication critical)
        elif any(x in filename for x in ['zl25', 'zl_', 'zl', 'soybean_oil', 'soyoil']):
            return 'ZL', 'soybean_oil_prices'
        elif any(x in filename for x in ['zs25', 'zs_', 'zs', 'soybean']):
            return 'ZS', 'soybean_prices'
        elif any(x in filename for x in ['zm25', 'zm_', 'zm', 'soymeal', 'soybean_meal']):
            return 'ZM', 'soybean_meal_prices'
        elif any(x in filename for x in ['zc25', 'zc_', 'zc', 'corn']):
            return 'ZC', 'corn_prices'
        elif any(x in filename for x in ['zw25', 'zw_', 'zw', 'wheat']):
            return 'ZW', 'wheat_prices'
        elif any(x in filename for x in ['ct25', 'ct_', 'cotton']):
            return 'CT', 'cotton_prices'
        elif any(x in filename for x in ['cl25', 'cl_', 'cl', 'crude', 'oil']):
            return 'CL', 'crude_oil_prices'

        # RATES & TREASURY (Research-weighted)
        elif any(x in filename for x in ['tnx', '10y', 'treasury', 'note']):
            return 'TNX', 'treasury_prices'
        elif any(x in filename for x in ['znz25', 'znz_', 'treasury_futures']):
            return 'ZNZ', 'treasury_prices'
        elif any(x in filename for x in ['fix25', 'fix_', 'fed', 'rates', 'ffr']):
            return 'FFR', 'treasury_prices'

        # PALM OIL / FCPO (route to generic market_prices for now)
        elif any(x in filename for x in ['fcpo', 'palm', 'mpob', 'cpo', 'bmd']):
            return 'FCPO', 'market_prices'
        elif any(x in filename for x in ['mpcv', 'mpc', 'usd_malaysian_crude_palm', 'usd cpo']):
            return 'MPC', 'market_prices'

        # ETHANOL/BIOFUELS
        elif any(x in filename for x in ['bdov25', 'bdov_', 'biodiesel']):
            return 'BDOV', 'biofuel_prices'
        elif any(x in filename for x in ['eth25', 'eth_', 'ethanol']):
            return 'ETH', 'biofuel_prices'
        elif any(x in filename for x in ['rin25', 'rin_', 'renewable']):
            return 'RIN', 'biofuel_prices'

        # INDICES & VOLATILITY
        elif any(x in filename for x in ['dxy', 'dollar', 'usd_index']):
            return 'DXY', 'usd_index_prices'
        elif any(x in filename for x in ['vix25', 'vix_', 'vix', 'volatility']):
            return 'VIX', 'vix_daily'

        # OTHER COMMODITIES (Generic routing)
        elif any(x in filename for x in ['qa225', 'qa2_']):
            return 'QA2', 'market_prices'
        elif any(x in filename for x in ['cs225', 'cs2_']):
            return 'CS2', 'market_prices'
        elif any(x in filename for x in ['rsx25', 'rsx_']):
            return 'RSX', 'market_prices'
        elif any(x in filename for x in ['zwz25', 'zwz_']):
            return 'ZWZ', 'wheat_prices'

        # Default to market_prices for unknown
        return 'UNKNOWN', 'market_prices'

    def standardize_csv(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Standardize CSV format to match BigQuery schema"""
        # Clean up common CSV issues (footer text, empty rows)
        df = df.dropna(how='all')  # Remove completely empty rows
        
        # Remove rows where the first column can't be parsed as a date (flexible formats)
        if len(df) > 0:
            first_col = df.columns[0]
            parsed = pd.to_datetime(df[first_col], errors='coerce', infer_datetime_format=True)
            df = df[parsed.notna()]
        
        # Common column mappings
        col_map = {
            'Time': 'date', 'Date': 'date', 'DATE': 'date', 'date': 'date',
            'Open': 'open', 'OPEN': 'open', 'open': 'open',
            'High': 'high', 'HIGH': 'high', 'high': 'high', 
            'Low': 'low', 'LOW': 'low', 'low': 'low',
            'Close': 'close', 'CLOSE': 'close', 'close': 'close',
            'Last': 'close', 'LAST': 'close', 'last': 'close',
            'Adj Close': 'close', 'Adj_Close': 'close', 'adj_close': 'close',
            'Volume': 'volume', 'VOLUME': 'volume', 'volume': 'volume',
            'Price': 'close', 'PRICE': 'close', 'price': 'close',
            'Value': 'close', 'VALUE': 'close', 'value': 'close'
        }

        # Rename columns
        df = df.rename(columns=col_map)

        # Ensure required columns exist
        required_cols = ['date', 'close']
        for col in required_cols:
            if col not in df.columns:
                if col == 'close' and 'price' in df.columns:
                    df['close'] = df['price']
                elif col == 'date' and df.index.name in ['Date', 'date', 'Time']:
                    df = df.reset_index()
                    df['date'] = df['Date'] if 'Date' in df.columns else df['date']

        # Standardize date format using pandas datetime (db_dtypes will convert to BigQuery TIMESTAMP)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # For tables that expect 'time' instead of 'date' (like soybean_oil_prices)
        if symbol in ['ZL', 'ZS', 'ZM', 'ZC', 'ZW', 'CL']:
            df['time'] = df['date']
            df = df.drop('date', axis=1)

        # Handle currency pairs differently
        if symbol in ['USDMYR', 'USDBRL', 'USDARS', 'USDCNY']:
            # Currency data schema: from_currency, to_currency, rate
            df['from_currency'] = 'USD'
            df['to_currency'] = symbol[3:]  # Extract MYR, BRL, etc.
            df['rate'] = df['close']
            df['source_name'] = 'Bulk_Historical_CSV'
            df['confidence_score'] = 0.95
            df['ingest_timestamp_utc'] = pd.to_datetime(datetime.now(timezone.utc))
            df['provenance_uuid'] = str(uuid.uuid4())

            # Select currency-specific columns
            final_cols = ['date', 'from_currency', 'to_currency', 'rate', 'source_name', 'confidence_score', 'ingest_timestamp_utc', 'provenance_uuid']
        else:
            # Regular market data schema: symbol, close, etc.
            df['symbol'] = symbol
            df['source_name'] = 'Bulk_Historical_CSV'
            df['confidence_score'] = 0.95
            df['ingest_timestamp_utc'] = pd.to_datetime(datetime.now(timezone.utc))
            df['provenance_uuid'] = str(uuid.uuid4())

            # Select and order columns (use 'time' for futures, 'date' for others)
            date_col = 'time' if symbol in ['ZL', 'ZS', 'ZM', 'ZC', 'ZW', 'CL'] else 'date'
            base_cols = [date_col, 'symbol', 'close']
            optional_cols = ['open', 'high', 'low', 'volume']
            meta_cols = ['source_name', 'confidence_score', 'ingest_timestamp_utc', 'provenance_uuid']
            final_cols = base_cols + [col for col in optional_cols if col in df.columns] + meta_cols

        df = df[final_cols]

        # Remove duplicates and sort
        if symbol in ['USDMYR', 'USDBRL', 'USDARS', 'USDCNY']:
            df = df.drop_duplicates(subset=['date', 'from_currency', 'to_currency']).sort_values('date')
        else:
            # Use appropriate date column for deduplication
            date_col = 'time' if symbol in ['ZL', 'ZS', 'ZM', 'ZC', 'ZW', 'CL'] else 'date'
            df = df.drop_duplicates(subset=[date_col, 'symbol']).sort_values(date_col)

        return df

    def load_to_bigquery(self, df: pd.DataFrame, table_name: str, dataset: str = 'forecasting_data_warehouse'):
        """Load DataFrame to BigQuery table using CBI-V14 standard approach"""
        table_id = f"{self.project_id}.{dataset}.{table_name}"

        # Use CBI-V14 standard job config with autodetect and db_dtypes
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            autodetect=True,  # Let BigQuery detect schema automatically
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
        )

        try:
            # Use the CBI-V14 standard safe_load_to_bigquery function
            job = safe_load_to_bigquery(self.client, df, table_id, job_config)
            
            if job:
                logger.info(f"✅ Loaded {len(df)} rows to {table_id}")
                return True
            else:
                logger.warning(f"⚠️ No job returned for {table_id}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to load to {table_id}: {e}")
            return False

    def process_single_csv(self, csv_path: Path):
        """Process a single CSV file"""
        logger.info(f"Processing single CSV: {csv_path}")

        try:
            # Detect symbol and table
            symbol, table_name = self.detect_symbol_type(csv_path.name)
            logger.info(f"Processing {csv_path.name} → {symbol} → {table_name}")

            # Load and standardize CSV
            df = pd.read_csv(csv_path)
            df = self.standardize_csv(df, symbol)

            if len(df) == 0:
                logger.warning(f"⚠️ Empty DataFrame for {csv_path.name}")
                return []

            # Load to BigQuery
            success = self.load_to_bigquery(df, table_name)

            result = {
                'file': csv_path.name,
                'symbol': symbol,
                'table': table_name,
                'rows': len(df),
                'success': success
            }

            logger.info(f"📊 SINGLE CSV SUMMARY:")
            logger.info(f"File: {csv_path.name}")
            logger.info(f"Symbol: {symbol} → Table: {table_name}")
            logger.info(f"Rows loaded: {len(df):,}")
            logger.info(f"Status: {'✅ SUCCESS' if success else '❌ FAILED'}")

            return [result]

        except Exception as e:
            logger.error(f"❌ Failed to process {csv_path.name}: {e}")
            return [{
                'file': csv_path.name,
                'symbol': 'ERROR',
                'table': 'ERROR',
                'rows': 0,
                'success': False,
                'error': str(e)
            }]

    def process_zip_file(self, zip_path: Path):
        """Process entire zip file of CSV data"""
        logger.info(f"Processing zip file: {zip_path}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract zip
            csv_files = self.extract_zip(zip_path, temp_path)
            logger.info(f"Found {len(csv_files)} CSV files")

            results = []

            for csv_file in csv_files:
                try:
                    # Detect symbol and table
                    symbol, table_name = self.detect_symbol_type(csv_file.name)
                    logger.info(f"Processing {csv_file.name} → {symbol} → {table_name}")

                    # Load and standardize CSV
                    df = pd.read_csv(csv_file)
                    df = self.standardize_csv(df, symbol)

                    if len(df) == 0:
                        logger.warning(f"⚠️ Empty DataFrame for {csv_file.name}")
                        continue

                    # Load to BigQuery
                    success = self.load_to_bigquery(df, table_name)

                    results.append({
                        'file': csv_file.name,
                        'symbol': symbol,
                        'table': table_name,
                        'rows': len(df),
                        'success': success
                    })

                except Exception as e:
                    logger.error(f"❌ Failed to process {csv_file.name}: {e}")
                    results.append({
                        'file': csv_file.name,
                        'symbol': 'ERROR',
                        'table': 'ERROR',
                        'rows': 0,
                        'success': False,
                        'error': str(e)
                    })

            # Summary
            successful = sum(1 for r in results if r['success'])
            total_rows = sum(r['rows'] for r in results if r['success'])

            logger.info(f"\n📊 BULK LOAD SUMMARY:")
            logger.info(f"Files processed: {len(results)}")
            logger.info(f"Successful loads: {successful}")
            logger.info(f"Total rows loaded: {total_rows:,}")

            return results

def main():
    parser = argparse.ArgumentParser(description='Bulk CSV Loader for CBI-V14')
    parser.add_argument('file_path', help='Path to CSV file or zip archive')
    parser.add_argument('--project', default='cbi-v14', help='BigQuery project ID')

    args = parser.parse_args()

    file_path = Path(args.file_path)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return

    loader = BulkCSVLoader(project_id=args.project)

    # Determine file type and process accordingly
    if file_path.suffix.lower() == '.zip':
        results = loader.process_zip_file(file_path)
    elif file_path.suffix.lower() == '.csv':
        results = loader.process_single_csv(file_path)
    else:
        logger.error(f"Unsupported file type: {file_path.suffix}")
        return

    # Print results table
    print("\n" + "="*80)
    print(f"{'File':<30} {'Symbol':<8} {'Table':<25} {'Rows':<8} {'Status'}")
    print("="*80)
    for r in results:
        status = "✅ OK" if r['success'] else "❌ FAIL"
        print(f"{r['file']:<30} {r['symbol']:<8} {r['table']:<25} {r['rows']:<8} {status}")

if __name__ == '__main__':
    main()
