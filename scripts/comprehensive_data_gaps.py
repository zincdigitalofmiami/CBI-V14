#!/usr/bin/env python3
"""
Comprehensive data gaps analysis with regime coverage
"""

from google.cloud import bigquery
from datetime import datetime
import pandas as pd

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("COMPREHENSIVE DATA GAPS & THIN DATA ANALYSIS")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Define regimes for analysis
REGIMES = {
    'Pre-2008': ('2000-01-01', '2007-12-31'),
    '2008 Crisis': ('2008-01-01', '2009-12-31'),
    'QE Era': ('2010-01-01', '2014-12-31'),
    'Oil Crash': ('2014-01-01', '2016-12-31'),
    'Trade War': ('2017-01-01', '2019-12-31'),
    'COVID': ('2020-01-01', '2021-12-31'),
    'Inflation': ('2021-01-01', '2023-01-01'),
    'Trump 2.0': ('2023-01-01', '2025-12-31'),
}

print("\n1. CRITICAL DATA GAPS")
print("="*80)

# Tables with correct date columns
critical_tables = {
    # Core commodities
    'soybean_oil_prices': ('time', '✅ COMPLETE (6,057 rows, 2000-2025)'),
    'palm_oil_prices': ('time', '⚠️ THIN - Only 2020+ (1,340 rows)'),
    'canola_oil_prices': ('date', '❌ VERY THIN - Only 2023+ (770 rows)'),
    'corn_prices': ('time', '⚠️ THIN - Only 2020+ (1,271 rows)'),
    'soybean_prices': ('time', '⚠️ THIN - Only 2020+ (1,272 rows)'),
    
    # Energy (need schema fix)
    'crude_oil_prices': ('time', '❓ CHECK SCHEMA'),
    'natural_gas_prices': ('time', '❓ CHECK SCHEMA'),
    'biofuel_prices': ('date', '❌ VERY THIN - Only 2025 (354 rows)'),
    
    # Market indicators
    'vix_daily': ('date', '✅ GOOD (2,717 rows, 2015-2025)'),
    'sp500_prices': ('time', '✅ GOOD (1,961 rows, 2018-2025)'),
    
    # Critical gaps
    'cftc_cot': ('report_date', '❌ CRITICAL GAP - Only 86 rows!'),
    'china_soybean_imports': ('date', '❌ CRITICAL GAP - Only 22 rows!'),
    'baltic_dry_index': ('date', '❌ MISSING - Table does not exist'),
    
    # Trump/Policy
    'trump_policy_intelligence': ('timestamp', '❓ CHECK SCHEMA'),
}

print("\nCRITICAL DATA STATUS:")
print("-"*80)
for table, (_, status) in critical_tables.items():
    print(f"  {table:30} | {status}")

print("\n2. REGIME DATA COVERAGE")
print("="*80)

# Check soybean oil coverage for each regime
print("\nSoybean Oil Price Coverage by Regime:")
print("-"*80)

for regime_name, (start_date, end_date) in REGIMES.items():
    try:
        query = f"""
        SELECT 
            COUNT(*) as rows,
            MIN(DATE(time)) as min_date,
            MAX(DATE(time)) as max_date
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
        WHERE DATE(time) >= '{start_date}' AND DATE(time) <= '{end_date}'
        """
        result = client.query(query).result()
        for row in result:
            if row.rows > 0:
                coverage = "✅ COVERED" if row.rows > 200 else "⚠️ PARTIAL"
                print(f"  {regime_name:15} | {coverage} | {row.rows:,} rows | {row.min_date} to {row.max_date}")
            else:
                print(f"  {regime_name:15} | ❌ NO DATA")
    except:
        pass

print("\n3. MISSING CRITICAL FEATURES FOR REGIMES")
print("="*80)

missing_features = {
    'Trade War (2017-2019)': [
        'china_soybean_imports - Only 22 rows total, none for 2017-2019',
        'trump_policy_intelligence - Schema issues, needs investigation',
        'tariff_announcements - No dedicated table',
        'argentina_soybean_exports - Table missing',
        'brazil_soybean_exports - Table missing',
    ],
    '2008 Crisis': [
        'cftc_cot - Only starts 2024 (missing crisis positioning data)',
        'credit_spreads - No table exists',
        'interbank_rates - No table exists', 
        'baltic_dry_index - Table missing (shipping collapse indicator)',
    ],
    'COVID (2020-2021)': [
        'port_congestion - No historical data',
        'supply_chain_stress - No dedicated metrics',
        'lockdown_indices - Not tracked',
    ],
    'Inflation (2021-2023)': [
        'fed_funds_rate - Not in separate table',
        'inflation_expectations - No market-based measures',
        'wage_growth - No labor market data',
    ],
    'Trump 2.0 (2023+)': [
        'social_sentiment - Only 677 rows (sparse)',
        'truth_social_data - Not being collected',
        'prediction_markets - No polymarket/predictit data',
    ]
}

print("\nMissing Features by Regime:")
print("-"*80)
for regime, features in missing_features.items():
    print(f"\n{regime}:")
    for feature in features:
        print(f"  ❌ {feature}")

print("\n4. BACKFILL REQUIREMENTS")
print("="*80)

backfill_needs = {
    'URGENT - Training Critical': [
        ('china_soybean_imports', '2017-2025', 'USDA FAS, customs data'),
        ('cftc_cot', '2006-2024', 'CFTC.gov historical files'),
        ('baltic_dry_index', '2000-2025', 'Bloomberg/Refinitiv'),
        ('argentina_exports', '2010-2025', 'INDEC/MAGyP'),
        ('brazil_exports', '2010-2025', 'SECEX/MDIC'),
    ],
    'HIGH - Regime Analysis': [
        ('palm_oil_prices', '2000-2020', 'Yahoo Finance historical'),
        ('canola_oil_prices', '2000-2023', 'ICE Futures historical'),
        ('corn_prices', '2000-2020', 'CME historical data'),
        ('soybean_prices', '2000-2020', 'CME historical data'),
    ],
    'MEDIUM - Enhanced Features': [
        ('fed_funds_rate', '2000-2025', 'FRED API'),
        ('inflation_breakevens', '2003-2025', 'FRED TIPS spreads'),
        ('credit_spreads', '2000-2025', 'FRED corporate spreads'),
        ('port_congestion', '2020-2025', 'Port authorities'),
    ],
    'LOW - Nice to Have': [
        ('weather_historical', '2000-2015', 'NOAA archives'),
        ('usda_wasde_historical', '2000-2025', 'USDA archives'),
        ('news_historical', 'Pre-2025', 'News API historical'),
    ]
}

print("\nBackfill Priority List:")
print("-"*80)
for priority, items in backfill_needs.items():
    print(f"\n{priority}:")
    for table, period, source in items:
        print(f"  • {table:25} | {period:12} | Source: {source}")

print("\n5. DASHBOARD DATA REQUIREMENTS")
print("="*80)

dashboard_gaps = {
    'Historical View': [
        '✅ soybean_oil_prices - GOOD (25 years)',
        '⚠️ Related commodities - LIMITED (only 2020+)',
        '❌ CFTC positioning - CRITICAL GAP (only 86 rows)',
    ],
    'Predictions View': [
        '✅ BQML predictions - Working',
        '⚠️ Ensemble predictions - Need regime models',
        '❌ Confidence intervals - Not calculated',
    ],
    'Signals View': [
        '✅ Signal views exist',
        '⚠️ Many signals limited by thin source data',
        '❌ Historical signal backtesting impossible',
    ],
    'News/Sentiment': [
        '✅ Recent news working',
        '❌ Historical news missing',
        '❌ Trump Truth Social not integrated',
    ],
}

print("\nDashboard Data Gaps:")
print("-"*80)
for section, items in dashboard_gaps.items():
    print(f"\n{section}:")
    for item in items:
        print(f"  {item}")

print("\n6. TRAINING DATA IMPACT")
print("="*80)

print("\nTraining Impact Assessment:")
print("-"*80)

training_impacts = {
    'BQML Models': 'Limited to 2020+ for most features (missing 20 years)',
    'Regime Models': 'Cannot train on 2008 crisis or trade war properly',
    'Ensemble': 'Missing critical features for regime detection',
    'Neural Networks': 'Insufficient data for deep architectures',
    'Feature Importance': 'SHAP values biased by missing historical context',
}

for model, impact in training_impacts.items():
    print(f"  {model:20} | ❌ {impact}")

print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)

print("""
IMMEDIATE ACTIONS REQUIRED:

1. URGENT BACKFILL (This Week):
   • China soybean imports (2017-2025) - Critical for trade war analysis
   • CFTC COT data (2006-2024) - Essential for positioning signals  
   • Baltic Dry Index (2000-2025) - Key shipping/demand indicator

2. SCHEMA FIXES:
   • crude_oil_prices - Fix date column
   • natural_gas_prices - Fix date column  
   • usd_index_prices - Fix date column
   • trump_policy_intelligence - Fix timestamp column

3. DATA COLLECTION SETUP:
   • Argentina/Brazil export monitors
   • Port congestion tracking
   • Fed funds rate ingestion
   • Truth Social monitor

4. HISTORICAL BACKFILL (Next Week):
   • Palm oil, canola, corn, soybeans (2000-2020)
   • Use yahoo_finance_comprehensive as template
   • Align all commodity date ranges

5. REGIME MODEL REQUIREMENTS:
   • Complete 2008 crisis data
   • Complete trade war data (2017-2019)
   • Add credit spread indicators
   • Add shipping/logistics metrics

Without these fixes:
- Cannot properly train regime-aware models
- Cannot backtest strategies over crises
- Dashboard shows incomplete picture
- Risk models miss critical indicators
""")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
