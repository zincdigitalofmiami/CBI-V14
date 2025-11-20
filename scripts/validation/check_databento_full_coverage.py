#!/usr/bin/env python3
"""
Comprehensive DataBento Coverage Check
Validates EVERYTHING we might need from DataBento:
- All 14 confirmed futures
- Palm oil (if available)
- Other vegetable oils
- Additional commodities
- FX futures vs spot
- Options data
- Any other relevant instruments
"""
import os
import sys
import databento as db
from datetime import datetime, timedelta

def check_comprehensive_coverage():
    api_key = os.environ.get('DATABENTO_API_KEY')
    if not api_key:
        print('❌ Set DATABENTO_API_KEY first')
        return False
    
    client = db.Historical(api_key)
    
    print('='*80)
    print('DATABENTO COMPREHENSIVE COVERAGE CHECK')
    print('='*80)
    
    # Test date range
    end = datetime.now()
    start = end - timedelta(days=14)
    
    # Categories to test
    tests = {
        'CONFIRMED FUTURES': [
            ('ES.FUT', 'S&P 500 E-mini'),
            ('MES.FUT', 'Micro E-mini S&P 500'),
            ('ZL.FUT', 'Soybean Oil'),
            ('ZS.FUT', 'Soybeans'),
            ('ZM.FUT', 'Soybean Meal'),
            ('CL.FUT', 'WTI Crude'),
            ('NG.FUT', 'Natural Gas'),
            ('ZC.FUT', 'Corn'),
            ('ZW.FUT', 'Wheat'),
            ('RB.FUT', 'RBOB Gasoline'),
            ('HO.FUT', 'Heating Oil'),
            ('GC.FUT', 'Gold'),
            ('SI.FUT', 'Silver'),
            ('HG.FUT', 'Copper'),
        ],
        'FX FUTURES (CONFIRMED)': [
            ('6E.FUT', 'EUR/USD futures'),
            ('6B.FUT', 'GBP/USD futures'),
            ('6J.FUT', 'JPY/USD futures'),
            ('6C.FUT', 'CAD/USD futures'),
            ('6A.FUT', 'AUD/USD futures'),
            ('6S.FUT', 'CHF/USD futures'),
        ],
        'PALM OIL (CHECK IF AVAILABLE)': [
            ('PO.FUT', 'Palm Oil futures - generic'),
            ('FCPO.FUT', 'BMD Malaysia Palm Oil'),
            ('PKO.FUT', 'Palm Kernel Oil'),
            ('PALM.FUT', 'Palm Oil - alt ticker'),
        ],
        'OTHER VEGETABLE OILS': [
            ('BO.FUT', 'Soybean Oil - alt ticker'),
            ('RS.FUT', 'Rapeseed/Canola'),
            ('RSEED.FUT', 'Rapeseed - alt'),
            ('SUN.FUT', 'Sunflower Oil'),
        ],
        'ADDITIONAL AG COMMODITIES': [
            ('ZR.FUT', 'Rice'),
            ('ZO.FUT', 'Oats'),
            ('CT.FUT', 'Cotton'),
            ('KC.FUT', 'Coffee'),
            ('CC.FUT', 'Cocoa'),
            ('SB.FUT', 'Sugar'),
        ],
        'LIVESTOCK (POTENTIAL SUBSTITUTION)': [
            ('LE.FUT', 'Live Cattle'),
            ('GF.FUT', 'Feeder Cattle'),
            ('HE.FUT', 'Lean Hogs'),
        ],
        'ENERGY (ADDITIONAL)': [
            ('BZ.FUT', 'Brent Crude'),
            ('QM.FUT', 'E-mini Crude'),
        ],
        'METALS (ADDITIONAL)': [
            ('PA.FUT', 'Palladium'),
            ('PL.FUT', 'Platinum'),
        ],
    }
    
    results = {}
    
    for category, symbols in tests.items():
        print(f'\n{"="*80}')
        print(f'{category}')
        print('='*80)
        
        available = []
        not_available = []
        
        for symbol, description in symbols:
            try:
                data = client.timeseries.get_range(
                    dataset='GLBX.MDP3',
                    symbols=[symbol],
                    stype_in='parent',
                    schema='ohlcv-1d',
                    start=start.strftime('%Y-%m-%d'),
                    end=end.strftime('%Y-%m-%d'),
                    limit=5
                )
                df = data.to_df() if hasattr(data, 'to_df') else data
                if not df.empty:
                    available.append((symbol, description))
                    print(f'  ✅ {symbol:15} {description}')
                else:
                    not_available.append((symbol, description))
                    print(f'  ❌ {symbol:15} {description} (empty)')
            except Exception as e:
                not_available.append((symbol, description))
                error_msg = str(e)[:60]
                print(f'  ❌ {symbol:15} {description} ({error_msg})')
        
        results[category] = {
            'available': available,
            'not_available': not_available
        }
    
    # Summary
    print('\n' + '='*80)
    print('SUMMARY - WHAT DATABENTO HAS')
    print('='*80)
    
    total_available = 0
    total_tested = 0
    
    for category, result in results.items():
        avail_count = len(result['available'])
        total_count = avail_count + len(result['not_available'])
        total_available += avail_count
        total_tested += total_count
        
        if avail_count > 0:
            print(f'\n✅ {category}: {avail_count}/{total_count}')
            for sym, desc in result['available']:
                print(f'   • {sym} ({desc})')
    
    print(f'\n{"="*80}')
    print(f'TOTAL: {total_available}/{total_tested} symbols available')
    print('='*80)
    
    # Recommendations
    print('\n' + '='*80)
    print('RECOMMENDATIONS')
    print('='*80)
    
    # Palm oil
    palm_available = [s for s, d in results.get('PALM OIL (CHECK IF AVAILABLE)', {}).get('available', [])]
    if palm_available:
        print(f'\n✅ PALM OIL: Use DataBento {palm_available[0]}')
    else:
        print('\n❌ PALM OIL: NOT on DataBento → Use Barchart/ICE/Yahoo as per Fresh Start')
    
    # Other vegoils
    vegoil_available = [s for s, d in results.get('OTHER VEGETABLE OILS', {}).get('available', [])]
    if vegoil_available:
        print(f'✅ OTHER VEGOILS: Use DataBento {", ".join(vegoil_available)}')
    else:
        print('❌ OTHER VEGOILS: NOT on DataBento → Use World Bank Pink Sheet / Alpha Vantage')
    
    # Additional ag
    ag_available = [s for s, d in results.get('ADDITIONAL AG COMMODITIES', {}).get('available', [])]
    if ag_available:
        print(f'✅ ADDITIONAL AG: {len(ag_available)} symbols available on DataBento')
    
    print('\n' + '='*80)
    print('NEXT STEPS')
    print('='*80)
    print('''
1. For available symbols: Use DataBento (primary source)
2. For missing symbols: Use alternative sources per Fresh Start plan
3. Create BigQuery tables based on ACTUAL data sources
4. Lock down schema before any collection starts
    ''')
    
    return True

if __name__ == '__main__':
    check_comprehensive_coverage()





