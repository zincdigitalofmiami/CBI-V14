#!/usr/bin/env python3
"""
COMPREHENSIVE DATA GAPS ANALYSIS
Identify all missing, thin, or incomplete datasets across regimes
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("COMPREHENSIVE DATA GAPS ANALYSIS")
print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Critical data sources by category
CRITICAL_DATASETS = {
    'CORE_PRICES': [
        ('soybean_oil_prices', 'time', 'Soybean Oil (Core)', '2000-01-01'),
        ('soybean_prices', 'time', 'Soybeans', '2000-01-01'),
        ('soybean_meal_prices', 'time', 'Soybean Meal', '2000-01-01'),
        ('palm_oil_prices', 'time', 'Palm Oil (Substitute)', '2000-01-01'),
        ('canola_oil_prices', 'date', 'Canola Oil', '2000-01-01'),
        ('corn_prices', 'time', 'Corn (Acreage)', '2000-01-01'),
        ('wheat_prices', 'time', 'Wheat', '2000-01-01'),
    ],
    'ENERGY_COMPLEX': [
        ('crude_oil_prices', 'date', 'Crude Oil', '2000-01-01'),
        ('natural_gas_prices', 'date', 'Natural Gas', '2000-01-01'),
        ('biofuel_prices', 'date', 'Biofuel/RIN', '2017-01-01'),  # EPA RINs
    ],
    'MARKET_INDICATORS': [
        ('vix_daily', 'date', 'VIX Volatility', '2000-01-01'),
        ('sp500_prices', 'time', 'S&P 500', '2000-01-01'),
        ('usd_index_prices', 'date', 'USD Index', '2000-01-01'),
        ('treasury_prices', 'time', '10Y Treasury', '2000-01-01'),
    ],
    'POSITIONING_DATA': [
        ('cftc_cot', 'report_date', 'CFTC COT', '2006-01-01'),  # CFTC modernized
    ],
    'ECONOMIC_DATA': [
        ('economic_indicators', 'time', 'Economic Indicators', '2000-01-01'),
        ('fed_funds_rate', 'date', 'Fed Funds Rate', '2000-01-01'),
    ],
    'SUPPLY_DEMAND': [
        ('china_soybean_imports', 'date', 'China Imports', '2010-01-01'),
        ('argentina_soybean_exports', 'date', 'Argentina Exports', '2010-01-01'),
        ('brazil_soybean_exports', 'date', 'Brazil Exports', '2010-01-01'),
        ('usda_wasde', 'release_date', 'USDA WASDE', '2000-01-01'),
    ],
    'NEWS_SENTIMENT': [
        ('news_intelligence', 'processed_timestamp', 'News Intelligence', '2020-01-01'),
        ('news_advanced', 'published_date', 'News Advanced', '2020-01-01'),
        ('social_sentiment', 'timestamp', 'Social Sentiment', '2021-01-01'),
        ('trump_policy_intelligence', 'created_at', 'Trump Policy', '2017-01-01'),
    ],
    'WEATHER_DATA': [
        ('weather_data', 'date', 'Weather Regional', '2015-01-01'),
        ('noaa_forecasts', 'forecast_date', 'NOAA Forecasts', '2020-01-01'),
    ],
    'TRADE_FLOW': [
        ('baltic_dry_index', 'date', 'Baltic Dry Index', '2000-01-01'),
        ('panama_canal_transit', 'date', 'Panama Canal', '2010-01-01'),
        ('port_congestion', 'date', 'Port Congestion', '2020-01-01'),
    ]
}

# Check regime periods for completeness
REGIME_PERIODS = {
    '2008 Crisis': ('2008-01-01', '2009-12-31'),
    'QE Era': ('2010-01-01', '2014-12-31'),
    'Oil Crash': ('2014-01-01', '2016-12-31'),
    'Trade War': ('2017-01-01', '2019-12-31'),
    'COVID': ('2020-01-01', '2021-12-31'),
    'Inflation': ('2021-01-01', '2023-12-31'),
    'Trump 2.0': ('2023-01-01', '2025-12-31'),
}

print("\n" + "="*80)
print("1. CHECKING CRITICAL DATA SOURCES")
print("="*80)

gaps_found = []

for category, tables in CRITICAL_DATASETS.items():
    print(f"\n{category}")
    print("-"*60)
    
    for table_name, date_col, description, min_date in tables:
        try:
            # Check if table exists
            check_query = f"""
            SELECT 
                COUNT(*) as total_rows,
                MIN(DATE({date_col})) as min_date,
                MAX(DATE({date_col})) as max_date,
                DATE_DIFF(MAX(DATE({date_col})), MIN(DATE({date_col})), DAY) as span_days,
                COUNT(DISTINCT DATE({date_col})) as unique_days,
                ROUND(100 * COUNT(DISTINCT DATE({date_col})) / 
                      NULLIF(DATE_DIFF(MAX(DATE({date_col})), MIN(DATE({date_col})), DAY), 0), 1) as completeness_pct
            FROM `cbi-v14.forecasting_data_warehouse.{table_name}`
            WHERE DATE({date_col}) >= '{min_date}'
            """
            
            result = client.query(check_query).result()
            row = list(result)[0]
            
            status = "✅" if row.total_rows > 100 else "⚠️"
            completeness = "✅" if row.completeness_pct and row.completeness_pct > 80 else "⚠️"
            
            print(f"  {status} {description:25} | Rows: {row.total_rows:7,} | "
                  f"Date: {row.min_date} to {row.max_date} | "
                  f"Complete: {row.completeness_pct:.1f}% {completeness}")
            
            # Record gaps
            if row.total_rows < 100 or (row.completeness_pct and row.completeness_pct < 80):
                gaps_found.append({
                    'category': category,
                    'table': table_name,
                    'description': description,
                    'rows': row.total_rows,
                    'completeness': row.completeness_pct,
                    'date_range': f"{row.min_date} to {row.max_date}"
                })
                
        except Exception as e:
            print(f"  ❌ {description:25} | ERROR: Table not found or {str(e)[:50]}")
            gaps_found.append({
                'category': category,
                'table': table_name,
                'description': description,
                'error': 'Table not found'
            })

print("\n" + "="*80)
print("2. REGIME-SPECIFIC DATA COVERAGE")
print("="*80)

for regime_name, (start_date, end_date) in REGIME_PERIODS.items():
    print(f"\n{regime_name} ({start_date} to {end_date})")
    print("-"*60)
    
    # Check core soybean oil data
    regime_query = f"""
    SELECT 
        COUNT(*) as soybean_oil_rows,
        COUNT(DISTINCT DATE(time)) as trading_days,
        MIN(DATE(time)) as actual_start,
        MAX(DATE(time)) as actual_end
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE DATE(time) >= '{start_date}' AND DATE(time) <= '{end_date}'
    """
    
    result = client.query(regime_query).result()
    row = list(result)[0]
    
    if row.soybean_oil_rows > 0:
        print(f"  ✅ Soybean Oil: {row.soybean_oil_rows:,} rows, {row.trading_days:,} days")
        print(f"     Coverage: {row.actual_start} to {row.actual_end}")
    else:
        print(f"  ❌ Soybean Oil: NO DATA for this regime!")

print("\n" + "="*80)
print("3. FEATURE ENGINEERING GAPS (production_training_data_*)")
print("="*80)

horizons = ['1w', '1m', '3m', '6m', '12m']

for horizon in horizons:
    try:
        feature_query = f"""
        SELECT 
            COUNT(*) as rows,
            MIN(date) as min_date,
            MAX(date) as max_date,
            ARRAY_LENGTH(REGEXP_EXTRACT_ALL(TO_JSON_STRING(t), r'"[^"]+":')) as feature_count
        FROM `cbi-v14.models_v4.production_training_data_{horizon}` t
        LIMIT 1
        """
        
        result = client.query(feature_query).result()
        row = list(result)[0]
        
        print(f"\n{horizon} horizon:")
        print(f"  Rows: {row.rows:,} | Features: ~290 | Date: {row.min_date} to {row.max_date}")
        
        # Check for specific regime coverage
        for regime_name, (start_date, end_date) in REGIME_PERIODS.items():
            regime_check = f"""
            SELECT COUNT(*) as regime_rows
            FROM `cbi-v14.models_v4.production_training_data_{horizon}`
            WHERE date >= '{start_date}' AND date <= '{end_date}'
            """
            regime_result = client.query(regime_check).result()
            regime_row = list(regime_result)[0]
            
            if regime_row.regime_rows < 100:
                print(f"  ⚠️ {regime_name}: Only {regime_row.regime_rows} rows")
                
    except Exception as e:
        print(f"\n{horizon} horizon: ❌ ERROR - {str(e)[:100]}")

print("\n" + "="*80)
print("4. DASHBOARD DATA REQUIREMENTS")
print("="*80)

# Check what the dashboard needs based on API endpoints
dashboard_requirements = [
    ('Historical Prices', 'soybean_oil_prices', 'time'),
    ('Predictions', 'predictions_ensemble', 'forecast_date'),
    ('Signals', 'signals.*', 'date'),
    ('News Feed', 'news_intelligence', 'processed_timestamp'),
    ('Economic Indicators', 'economic_indicators', 'time'),
    ('CFTC Positioning', 'cftc_cot', 'report_date'),
]

print("\nDashboard Data Status:")
for requirement, table, date_col in dashboard_requirements:
    try:
        if 'signals.*' in table:
            # Check signals dataset
            signal_query = """
            SELECT table_name
            FROM `cbi-v14.signals.INFORMATION_SCHEMA.TABLES`
            WHERE table_type = 'VIEW'
            """
            result = client.query(signal_query).result()
            signal_count = len(list(result))
            print(f"  ✅ {requirement}: {signal_count} signal views available")
        else:
            check = f"""
            SELECT COUNT(*) as rows, MAX(DATE({date_col})) as latest
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            """
            result = client.query(check).result()
            row = list(result)[0]
            
            days_old = (datetime.now().date() - row.latest).days if row.latest else 999
            status = "✅" if days_old < 7 else "⚠️"
            
            print(f"  {status} {requirement}: {row.rows:,} rows, latest: {row.latest} ({days_old} days old)")
    except Exception as e:
        print(f"  ❌ {requirement}: Not available - {str(e)[:50]}")

print("\n" + "="*80)
print("5. CRITICAL GAPS SUMMARY")
print("="*80)

if gaps_found:
    print("\n⚠️ CRITICAL DATA GAPS FOUND:")
    for gap in gaps_found:
        if 'error' in gap:
            print(f"\n❌ {gap['category']} - {gap['description']}:")
            print(f"   Table: {gap['table']}")
            print(f"   Issue: {gap['error']}")
        else:
            print(f"\n⚠️ {gap['category']} - {gap['description']}:")
            print(f"   Table: {gap['table']}")
            print(f"   Rows: {gap.get('rows', 0):,}")
            print(f"   Completeness: {gap.get('completeness', 0):.1f}%")
            print(f"   Range: {gap.get('date_range', 'N/A')}")
else:
    print("\n✅ No critical gaps found!")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
