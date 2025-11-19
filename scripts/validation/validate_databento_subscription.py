#!/usr/bin/env python3
"""
DataBento Subscription Validation
Tests all required symbols and schemas for CBI-V14
"""
import os
import sys
import databento as db
from datetime import datetime, timedelta

def validate_subscription():
    """Comprehensive DataBento validation"""
    
    # Get API key from environment
    api_key = os.environ.get('DATABENTO_API_KEY')
    if not api_key:
        print('❌ ERROR: DATABENTO_API_KEY not set in environment')
        print('Set it: export DATABENTO_API_KEY="your_key_here"')
        return False
    
    print('='*80)
    print('DATABENTO SUBSCRIPTION VALIDATION')
    print('='*80)
    print(f'Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'API Key: {api_key[:10]}...{api_key[-5:]}')
    print('='*80)
    
    try:
        client = db.Historical(api_key)
    except Exception as e:
        print(f'❌ Failed to create client: {e}')
        return False
    
    # Step 1: List all datasets
    print('\n' + '='*80)
    print('STEP 1: AVAILABLE DATASETS')
    print('='*80)
    try:
        datasets = client.metadata.list_datasets()
        for ds in datasets:
            print(f'  ✅ {ds}')
        
        if 'GLBX.MDP3' not in datasets:
            print('❌ ERROR: GLBX.MDP3 not in available datasets!')
            return False
        print('\n✅ GLBX.MDP3 confirmed available')
    except Exception as e:
        print(f'❌ Error listing datasets: {e}')
        return False
    
    # Step 2: Check GLBX.MDP3 schemas
    print('\n' + '='*80)
    print('STEP 2: GLBX.MDP3 SCHEMAS')
    print('='*80)
    try:
        schemas = client.metadata.list_schemas('GLBX.MDP3')
        print(f'Available schemas: {", ".join(schemas)}')
        
        required_schemas = ['ohlcv-1m', 'ohlcv-1d']
        for schema in required_schemas:
            if schema in schemas:
                print(f'  ✅ {schema} available')
            else:
                print(f'  ❌ {schema} NOT available (CRITICAL)')
                return False
    except Exception as e:
        print(f'❌ Error listing schemas: {e}')
        return False
    
    # Step 3: Check date range
    print('\n' + '='*80)
    print('STEP 3: DATASET DATE RANGE')
    print('='*80)
    try:
        range_info = client.metadata.get_dataset_range('GLBX.MDP3')
        print(f'Start: {range_info.get("start")}')
        print(f'End: {range_info.get("end")}')
        
        # Check ohlcv-1m range
        if 'schema' in range_info and 'ohlcv-1m' in range_info['schema']:
            schema_range = range_info['schema']['ohlcv-1m']
            print(f'\nohlcv-1m range:')
            print(f'  Start: {schema_range.get("start")}')
            print(f'  End: {schema_range.get("end")}')
    except Exception as e:
        print(f'⚠️  Could not get date range: {e}')
    
    # Step 4: Validate ALL 13 required symbols
    print('\n' + '='*80)
    print('STEP 4: SYMBOL VALIDATION (All 13 Required Symbols)')
    print('='*80)
    
    # Define symbols by priority
    primary_symbols = {
        'ZL.FUT': 'Soybean Oil (PRIMARY ASSET)',
        'MES.FUT': 'Micro E-mini S&P 500',
        'ES.FUT': 'S&P 500 E-mini',
    }
    
    secondary_symbols = {
        'ZS.FUT': 'Soybeans',
        'ZM.FUT': 'Soybean Meal',
        'CL.FUT': 'WTI Crude Oil',
        'NG.FUT': 'Natural Gas',
        'ZC.FUT': 'Corn',
        'ZW.FUT': 'Wheat',
        'RB.FUT': 'RBOB Gasoline',
        'HO.FUT': 'Heating Oil',
        'GC.FUT': 'Gold',
        'SI.FUT': 'Silver',
        'HG.FUT': 'Copper',
    }
    
    all_symbols = {**primary_symbols, **secondary_symbols}
    
    # Test date range (last 2 weeks for daily data)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=14)
    
    success_count = 0
    failed_symbols = []
    
    print('\nPRIMARY SYMBOLS (5-minute collection):')
    for symbol, description in primary_symbols.items():
        try:
            data = client.timeseries.get_range(
                dataset='GLBX.MDP3',
                symbols=[symbol],
                stype_in='parent',
                schema='ohlcv-1d',
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                limit=10
            )
            df = data.to_df() if hasattr(data, 'to_df') else data
            print(f'  ✅ {symbol:12} ({description}): {len(df)} records')
            success_count += 1
        except Exception as e:
            print(f'  ❌ {symbol:12} ({description}): {str(e)[:80]}')
            failed_symbols.append(symbol)
    
    print('\nSECONDARY SYMBOLS (1-hour collection):')
    for symbol, description in secondary_symbols.items():
        try:
            data = client.timeseries.get_range(
                dataset='GLBX.MDP3',
                symbols=[symbol],
                stype_in='parent',
                schema='ohlcv-1d',
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                limit=10
            )
            df = data.to_df() if hasattr(data, 'to_df') else data
            print(f'  ✅ {symbol:12} ({description}): {len(df)} records')
            success_count += 1
        except Exception as e:
            print(f'  ❌ {symbol:12} ({description}): {str(e)[:80]}')
            failed_symbols.append(symbol)
    
    # Step 5: Test 1-minute schema on primary symbols
    print('\n' + '='*80)
    print('STEP 5: 1-MINUTE DATA VALIDATION (Primary Symbols)')
    print('='*80)
    
    # Test last hour of 1-minute data
    end_1m = datetime.now()
    start_1m = end_1m - timedelta(hours=2)
    
    for symbol in ['ZL.FUT', 'ES.FUT', 'MES.FUT']:
        try:
            data = client.timeseries.get_range(
                dataset='GLBX.MDP3',
                symbols=[symbol],
                stype_in='parent',
                schema='ohlcv-1m',
                start=start_1m.strftime('%Y-%m-%dT%H:%M:%S'),
                end=end_1m.strftime('%Y-%m-%dT%H:%M:%S'),
                limit=120
            )
            df = data.to_df() if hasattr(data, 'to_df') else data
            print(f'  ✅ {symbol:12}: {len(df)} 1-minute bars')
        except Exception as e:
            print(f'  ⚠️  {symbol:12}: {str(e)[:80]}')
            print(f'      (May be outside market hours - not critical)')
    
    # Step 6: Test FX futures availability
    print('\n' + '='*80)
    print('STEP 6: FX FUTURES AVAILABILITY (Optional)')
    print('='*80)
    
    fx_futures = {
        '6E.FUT': 'EUR/USD futures',
        '6B.FUT': 'GBP/USD futures',
        '6J.FUT': 'JPY/USD futures',
    }
    
    fx_available = []
    for symbol, description in fx_futures.items():
        try:
            data = client.timeseries.get_range(
                dataset='GLBX.MDP3',
                symbols=[symbol],
                stype_in='parent',
                schema='ohlcv-1d',
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                limit=10
            )
            df = data.to_df() if hasattr(data, 'to_df') else data
            print(f'  ✅ {symbol:12} ({description}): Available')
            fx_available.append(symbol)
        except Exception as e:
            print(f'  ❌ {symbol:12} ({description}): Not available')
    
    # Final Results
    print('\n' + '='*80)
    print('VALIDATION RESULTS')
    print('='*80)
    
    print(f'\n✅ Symbols validated: {success_count}/14')
    if failed_symbols:
        print(f'❌ Failed symbols: {", ".join(failed_symbols)}')
    
    if fx_available:
        print(f'✅ FX futures available: {", ".join(fx_available)}')
        print('   → Use DataBento for FX futures')
    else:
        print('⚠️  No FX futures available')
        print('   → Use Yahoo Finance for spot FX (EUR/USD, GBP/USD, etc.)')
    
    # Final verdict
    print('\n' + '='*80)
    if success_count == 14 and not failed_symbols:
        print('✅✅✅ VALIDATION PASSED - ALL SYSTEMS GO ✅✅✅')
        print('='*80)
        print('\nYou can proceed with:')
        print('  1. Create BigQuery tables')
        print('  2. Deploy DataBento collectors')
        print('  3. Set up processing layers')
        print('\nSee: PRODUCTION_DATA_ARCHITECTURE.md for implementation plan')
        return True
    else:
        print('❌❌❌ VALIDATION FAILED - DO NOT PROCEED ❌❌❌')
        print('='*80)
        print(f'\nFailed: {len(failed_symbols)} symbols')
        print('Contact DataBento support to resolve access issues')
        print('\nFailed symbols:', ', '.join(failed_symbols) if failed_symbols else 'None')
        return False

if __name__ == '__main__':
    success = validate_subscription()
    sys.exit(0 if success else 1)

