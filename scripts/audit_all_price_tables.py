#!/usr/bin/env python3
"""
Comprehensive audit of ALL price tables to check for contamination
Each table has its own schema - we need to handle this properly
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

# Define expected schema and symbols for each table
TABLE_CONFIGS = {
    'soybean_oil_prices': {
        'price_column': 'close',
        'expected_symbols': ['ZL', 'ZL=F', 'SOYBEAN_OIL'],
        'expected_range': (30, 100),  # cents per pound
        'description': 'Soybean Oil Futures (ZL)'
    },
    'soybean_prices': {
        'price_column': 'close_price',
        'expected_symbols': ['ZS', 'ZS=F', 'SOYBEAN', 'S=F'],
        'expected_range': (800, 1800),  # cents per bushel
        'description': 'Soybean Futures (ZS) - NOT oil!'
    },
    'corn_prices': {
        'price_column': 'close',
        'expected_symbols': ['ZC', 'ZC=F', 'CORN', 'C=F'],
        'expected_range': (300, 800),  # cents per bushel
        'description': 'Corn Futures (ZC)'
    },
    'wheat_prices': {
        'price_column': 'close',
        'expected_symbols': ['ZW', 'ZW=F', 'WHEAT', 'W=F'],
        'expected_range': (400, 1400),  # cents per bushel
        'description': 'Wheat Futures (ZW)'
    },
    'cotton_prices': {
        'price_column': 'close',
        'expected_symbols': ['CT', 'CT=F', 'COTTON'],
        'expected_range': (50, 150),  # cents per pound
        'description': 'Cotton Futures (CT)'
    },
    'crude_oil_prices': {
        'price_column': 'close_price',
        'expected_symbols': ['CL', 'CL=F', 'WTI', 'BRENT', 'CRUDE_OIL', 'CRUDE'],
        'expected_range': (20, 150),  # dollars per barrel
        'description': 'Crude Oil (CL/Brent)'
    },
    'palm_oil_prices': {
        'price_column': 'close',
        'expected_symbols': ['FCPO', 'PALM', 'PALM_OIL'],
        'expected_range': (2000, 6000),  # MYR per metric ton (or USD equivalent)
        'description': 'Palm Oil (FCPO)'
    },
    'vix_daily': {
        'price_column': 'close',
        'expected_symbols': ['VIX', '^VIX', 'VOLATILITY'],
        'expected_range': (10, 90),  # volatility index
        'description': 'VIX Volatility Index'
    },
    'treasury_prices': {
        'price_column': 'close',
        'expected_symbols': ['TNX', 'TYX', 'IRX', 'FVX', 'TREASURY', '10Y', '10_YEAR'],
        'expected_range': (0, 10),  # yield percentage
        'description': '10-Year Treasury Yield'
    },
    'canola_oil_prices': {
        'price_column': 'close_price',
        'expected_symbols': ['RS', 'CANOLA', 'CANOLA_OIL'],
        'expected_range': (400, 1000),  # CAD per metric ton
        'description': 'Canola Oil (RS)'
    },
    'rapeseed_oil_prices': {
        'price_column': 'close_price',
        'expected_symbols': ['RAPESEED', 'RAPESEED_OIL'],
        'expected_range': (400, 1000),  # EUR per metric ton
        'description': 'Rapeseed Oil'
    },
    'usd_index_prices': {
        'price_column': 'close_price',
        'expected_symbols': ['DXY', 'DX', 'USD_INDEX', 'DOLLAR'],
        'expected_range': (70, 120),  # index value
        'description': 'US Dollar Index (DXY)'
    },
    'biofuel_prices': {
        'price_column': 'close',
        'expected_symbols': ['BIOFUEL', 'ETHANOL', 'BIODIESEL', 'RIN'],
        'expected_range': (1, 5),  # dollars per gallon
        'description': 'Biofuel/Ethanol Prices'
    }
}

def check_table_schema(table_name):
    """First check what columns exist in the table"""
    query = f"""
    SELECT column_name, data_type
    FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{table_name}'
    AND column_name IN ('close', 'close_price', 'price', 'symbol')
    """
    
    try:
        results = list(client.query(query))
        columns = {row['column_name']: row['data_type'] for row in results}
        return columns
    except:
        return {}

def audit_price_table(table_name, config):
    """Audit a single price table for contamination"""
    
    # First check the schema
    columns = check_table_schema(table_name)
    if not columns:
        return None, "Table not found or no relevant columns"
    
    # Determine the actual price column
    price_col = None
    if 'close' in columns:
        price_col = 'close'
    elif 'close_price' in columns:
        price_col = 'close_price'
    elif 'price' in columns:
        price_col = 'price'
    else:
        return None, f"No price column found. Columns: {columns}"
    
    # Check if symbol column exists
    has_symbol = 'symbol' in columns
    
    if not has_symbol:
        # No symbol column - just check price range
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            MIN({price_col}) as min_price,
            MAX({price_col}) as max_price,
            AVG({price_col}) as avg_price,
            STDDEV({price_col}) as std_price
        FROM `cbi-v14.forecasting_data_warehouse.{table_name}`
        WHERE {price_col} IS NOT NULL
        """
        
        try:
            result = list(client.query(query))[0]
            return [{
                'symbol': 'NO_SYMBOL_COLUMN',
                'row_count': result['row_count'],
                'min_price': result['min_price'],
                'max_price': result['max_price'],
                'avg_price': result['avg_price']
            }], None
        except Exception as e:
            return None, str(e)[:100]
    
    # Has symbol column - check each symbol
    query = f"""
    SELECT 
        symbol,
        COUNT(*) as row_count,
        MIN({price_col}) as min_price,
        MAX({price_col}) as max_price,
        AVG({price_col}) as avg_price
    FROM `cbi-v14.forecasting_data_warehouse.{table_name}`
    WHERE {price_col} IS NOT NULL
    GROUP BY symbol
    ORDER BY row_count DESC
    """
    
    try:
        results = list(client.query(query))
        return results, None
    except Exception as e:
        return None, str(e)[:100]

def main():
    """Run comprehensive audit of all price tables"""
    
    print("=" * 80)
    print("COMPREHENSIVE PRICE TABLE AUDIT - WITH SCHEMA AWARENESS")
    print("=" * 80)
    print()
    
    contamination_summary = []
    
    for table_name, config in TABLE_CONFIGS.items():
        print(f"\n{'='*70}")
        print(f"TABLE: {table_name}")
        print(f"Description: {config['description']}")
        print(f"Expected Range: ${config['expected_range'][0]:.0f} - ${config['expected_range'][1]:.0f}")
        print("-" * 70)
        
        results, error = audit_price_table(table_name, config)
        
        if error:
            print(f"  ⚠️ Error: {error}")
            continue
        
        if not results:
            print(f"  ⚠️ No data found")
            continue
        
        # Check each symbol
        for row in results:
            symbol = row['symbol']
            count = row['row_count']
            min_p = row['min_price'] or 0
            max_p = row['max_price'] or 0
            avg_p = row['avg_price'] or 0
            
            # Check if symbol belongs
            is_expected = False
            if symbol == 'NO_SYMBOL_COLUMN':
                # No symbol column - check price range
                is_expected = config['expected_range'][0] <= avg_p <= config['expected_range'][1] * 2
                status = '✅' if is_expected else '⚠️ CHECK RANGE'
            else:
                # Check if symbol is expected
                is_expected = any(
                    exp.upper() in symbol.upper() or symbol.upper() in exp.upper() 
                    for exp in config['expected_symbols']
                )
                
                # Check price range
                in_range = config['expected_range'][0] <= avg_p <= config['expected_range'][1] * 2
                
                if is_expected and in_range:
                    status = '✅'
                elif is_expected and not in_range:
                    status = '⚠️ WRONG RANGE'
                else:
                    status = '❌ CONTAMINATION'
                    contamination_summary.append({
                        'table': table_name,
                        'symbol': symbol,
                        'rows': count,
                        'issue': f'{symbol} should not be in {config["description"]} table'
                    })
            
            print(f"  {status} Symbol: {symbol:15} | Rows: {count:5} | Range: ${min_p:8.2f} - ${max_p:8.2f} (avg: ${avg_p:8.2f})")
            
            # Special warnings
            if symbol in ['SPX', 'SPY'] and table_name != 'equity_prices':
                print(f"      🚨 S&P 500 data contaminating commodity table!")
            elif symbol == 'ZS' and table_name == 'soybean_oil_prices':
                print(f"      🚨 ZS is Soybeans, NOT Soybean Oil! Different commodity!")
            elif symbol == 'GC':
                print(f"      🚨 Gold futures in wrong table!")
    
    # Print contamination summary
    print("\n" + "=" * 80)
    print("CONTAMINATION SUMMARY")
    print("=" * 80)
    
    if contamination_summary:
        print("\n❌ TABLES WITH CONTAMINATION:")
        for issue in contamination_summary:
            print(f"  • {issue['table']}: {issue['symbol']} ({issue['rows']} rows) - {issue['issue']}")
        
        print("\n🔧 REQUIRED FIXES:")
        print("1. Clean soybean_oil_prices - Remove SPX, SPY, GC, ZS, ZC, ZW, etc.")
        print("2. Keep ONLY the correct symbol for each table")
        print("3. Update training views to filter by symbol where needed")
        print("4. Add metadata/documentation for neural nets to understand each table")
    else:
        print("\n✅ No major contamination found!")
    
    print("\n" + "=" * 80)
    print("METADATA FOR NEURAL NETS")
    print("=" * 80)
    print("\nEach table should have clear metadata:")
    print("• Symbol mapping (ZL = Soybean Oil, ZS = Soybeans)")
    print("• Unit specification (cents/lb, cents/bushel, $/barrel)")
    print("• Expected price ranges for anomaly detection")
    print("• Relationship mappings (substitutes, correlations)")

if __name__ == "__main__":
    main()
