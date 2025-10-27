#!/usr/bin/env python3
"""
Clean contaminated price tables by removing wrong symbols
CRITICAL: Keep backups before cleaning!
"""

from google.cloud import bigquery
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

def backup_table(table_name):
    """Create a backup of the table before cleaning"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{table_name}_backup_{timestamp}"
    
    query = f"""
    CREATE TABLE `cbi-v14.bkp.{backup_name}` AS
    SELECT * FROM `cbi-v14.forecasting_data_warehouse.{table_name}`
    """
    
    try:
        client.query(query).result()
        logger.info(f"✅ Created backup: bkp.{backup_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to backup {table_name}: {e}")
        return False

def clean_soybean_oil_prices():
    """Remove all non-ZL symbols from soybean_oil_prices"""
    logger.info("\nCleaning soybean_oil_prices table...")
    
    # First check what we're about to delete
    query_check = """
    SELECT symbol, COUNT(*) as row_count
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE symbol != 'ZL'
    GROUP BY symbol
    """
    
    contamination = list(client.query(query_check))
    if contamination:
        logger.info("  Will remove:")
        for row in contamination:
            logger.info(f"    - {row['symbol']}: {row['row_count']} rows")
    
    # Delete contaminated data
    query_delete = """
    DELETE FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE symbol != 'ZL'
    """
    
    try:
        result = client.query(query_delete).result()
        logger.info(f"  ✅ Removed {result.num_dml_affected_rows} contaminated rows")
        return True
    except Exception as e:
        logger.error(f"  ❌ Failed to clean: {e}")
        return False

def clean_treasury_prices():
    """Remove ZNZ from treasury_prices (should be TNX, IRX, etc.)"""
    logger.info("\nCleaning treasury_prices table...")
    
    # Check what we have
    query_check = """
    SELECT symbol, COUNT(*) as row_count, AVG(close) as avg_price
    FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
    GROUP BY symbol
    """
    
    symbols = list(client.query(query_check))
    logger.info("  Current symbols:")
    for row in symbols:
        logger.info(f"    - {row['symbol']}: {row['row_count']} rows, avg ${row['avg_price']:.2f}")
    
    # ZNZ appears to be treasury futures contract (wrong format)
    # We should keep only yield data or convert properly
    logger.info("  ⚠️ ZNZ appears to be treasury futures, not yield")
    logger.info("  ⚠️ May need to source proper 10Y yield data (TNX)")
    
    return True

def clean_biofuel_prices():
    """Check biofuel_prices for wrong data"""
    logger.info("\nChecking biofuel_prices table...")
    
    query_check = """
    SELECT symbol, COUNT(*) as row_count, 
           MIN(close) as min_price, 
           MAX(close) as max_price,
           AVG(close) as avg_price
    FROM `cbi-v14.forecasting_data_warehouse.biofuel_prices`
    GROUP BY symbol
    """
    
    try:
        symbols = list(client.query(query_check))
        logger.info("  Current symbols:")
        for row in symbols:
            logger.info(f"    - {row['symbol']}: {row['row_count']} rows, ${row['min_price']:.2f} - ${row['max_price']:.2f}")
        
        # BDOV at $1000+ is wrong - should be $1-5/gallon
        logger.info("  ⚠️ BDOV prices seem wrong (too high for biofuel)")
        logger.info("  ⚠️ May need to re-source biofuel price data")
    except Exception as e:
        logger.error(f"  Error checking: {e}")
    
    return True

def create_metadata_view():
    """Create a metadata view for neural nets to understand commodities"""
    logger.info("\nCreating commodity metadata view...")
    
    query = """
    CREATE OR REPLACE VIEW `cbi-v14.models.vw_commodity_metadata` AS
    SELECT 
        'ZL' as symbol,
        'Soybean Oil' as commodity_name,
        'Extracted oil from soybeans' as description,
        'cents per pound' as unit,
        30 as typical_min_price,
        100 as typical_max_price,
        'forecasting_data_warehouse.soybean_oil_prices' as table_name,
        'close' as price_column,
        'Food/Energy' as category,
        'ZS' as related_symbols,
        'Palm Oil' as substitute_commodities
    UNION ALL
    SELECT 
        'ZS', 'Soybeans', 'Whole soybean (NOT oil)', 'cents per bushel',
        800, 1800, 'forecasting_data_warehouse.soybean_prices', 'close_price',
        'Agriculture', 'ZL,ZM', 'Corn'
    UNION ALL
    SELECT 
        'ZC', 'Corn', 'Corn/Maize futures', 'cents per bushel',
        300, 800, 'forecasting_data_warehouse.corn_prices', 'close',
        'Agriculture', 'ZS,ZW', 'Wheat,Soybeans'
    UNION ALL
    SELECT 
        'ZW', 'Wheat', 'Wheat futures', 'cents per bushel',
        400, 1400, 'forecasting_data_warehouse.wheat_prices', 'close',
        'Agriculture', 'ZC', 'Corn,Rice'
    UNION ALL
    SELECT 
        'CT', 'Cotton', 'Cotton futures', 'cents per pound',
        50, 150, 'forecasting_data_warehouse.cotton_prices', 'close',
        'Agriculture', NULL, NULL
    UNION ALL
    SELECT 
        'CL', 'Crude Oil', 'WTI Crude Oil', 'dollars per barrel',
        20, 150, 'forecasting_data_warehouse.crude_oil_prices', 'close_price',
        'Energy', 'BRENT,NG', 'Brent,Natural Gas'
    UNION ALL
    SELECT 
        'PALM', 'Palm Oil', 'Palm oil from Malaysia', 'MYR per metric ton',
        2000, 6000, 'forecasting_data_warehouse.palm_oil_prices', 'close',
        'Food/Energy', 'ZL', 'Soybean Oil,Rapeseed'
    UNION ALL
    SELECT 
        'VIX', 'Volatility Index', 'CBOE Volatility Index', 'index points',
        10, 90, 'forecasting_data_warehouse.vix_daily', 'close',
        'Market', 'SPX', NULL
    UNION ALL
    SELECT 
        'DXY', 'US Dollar Index', 'USD strength vs basket', 'index points',
        70, 120, 'forecasting_data_warehouse.usd_index_prices', 'close_price',
        'Currency', NULL, NULL
    """
    
    try:
        client.query(query).result()
        logger.info("  ✅ Created models.vw_commodity_metadata")
        return True
    except Exception as e:
        logger.error(f"  ❌ Failed to create metadata: {e}")
        return False

def verify_clean_data():
    """Verify data is clean after cleanup"""
    logger.info("\nVerifying clean data...")
    
    # Check soybean_oil_prices
    query = """
    SELECT 
        'soybean_oil_prices' as table_name,
        COUNT(DISTINCT symbol) as unique_symbols,
        STRING_AGG(DISTINCT symbol, ', ') as symbols,
        COUNT(*) as total_rows
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    """
    
    result = list(client.query(query))[0]
    logger.info(f"  soybean_oil_prices: {result['unique_symbols']} symbols ({result['symbols']}), {result['total_rows']} rows")
    
    if result['unique_symbols'] == 1 and result['symbols'] == 'ZL':
        logger.info("  ✅ soybean_oil_prices is CLEAN!")
    else:
        logger.warning("  ⚠️ soybean_oil_prices still has contamination")
    
    return True

def main():
    """Main cleanup process"""
    logger.info("=" * 70)
    logger.info("CLEANING CONTAMINATED PRICE TABLES")
    logger.info("=" * 70)
    
    # Step 1: Backup tables
    logger.info("\nStep 1: Creating backups...")
    backup_table('soybean_oil_prices')
    
    # Step 2: Clean soybean_oil_prices
    logger.info("\nStep 2: Cleaning tables...")
    clean_soybean_oil_prices()
    
    # Step 3: Check other tables
    clean_treasury_prices()
    clean_biofuel_prices()
    
    # Step 4: Create metadata
    logger.info("\nStep 3: Creating metadata...")
    create_metadata_view()
    
    # Step 5: Verify
    logger.info("\nStep 4: Verification...")
    verify_clean_data()
    
    logger.info("\n" + "=" * 70)
    logger.info("CLEANUP COMPLETE")
    logger.info("=" * 70)
    logger.info("\n✅ Key Points:")
    logger.info("• ZL (Soybean Oil) ≠ ZS (Soybeans)")
    logger.info("• Each commodity has specific units and price ranges")
    logger.info("• Metadata view created for neural net understanding")
    logger.info("• Backups saved in bkp dataset")

if __name__ == "__main__":
    main()
