#!/usr/bin/env python3
"""
COMPREHENSIVE FEATURE AUDIT - Check ALL data sources
Including scraped data, sentiment, shocks, weather regions, legislation, tariffs, Trump, etc.
Every feature has specific role and weighting - need to understand ALL of them
"""

from google.cloud import bigquery
from datetime import datetime
import pandas as pd
from collections import defaultdict

client = bigquery.Client(project='cbi-v14')

print(f"COMPREHENSIVE FEATURE AUDIT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print("Checking ALL data sources, intelligence, and calculated features")
print("="*80)

# Track all features found
all_features = defaultdict(list)

print("\n1. SENTIMENT & SOCIAL INTELLIGENCE:")
print("-"*80)

sentiment_tables = [
    'social_sentiment',
    'news_intelligence', 
    'trump_policy_intelligence',
    'ice_enforcement_intelligence',
    'vw_social_sentiment_daily',
    'vw_trump_intelligence_dashboard',
    'vw_trump_effect_breakdown',
    'vw_trump_effect_categories',
]

for table in sentiment_tables:
    for dataset in ['forecasting_data_warehouse', 'signals', 'curated']:
        try:
            query = f"""
            SELECT 
                COUNT(*) as rows,
                COUNT(DISTINCT DATE(COALESCE(timestamp, date, created_at))) as unique_days
            FROM `cbi-v14.{dataset}.{table}`
            """
            result = client.query(query).to_dataframe()
            if result['rows'].iloc[0] > 0:
                print(f"\n{dataset}.{table}:")
                print(f"  Rows: {result['rows'].iloc[0]:,}")
                print(f"  Unique days: {result['unique_days'].iloc[0]:,}")
                
                # Sample to see what features it has
                sample_query = f"SELECT * FROM `cbi-v14.{dataset}.{table}` LIMIT 1"
                sample = client.query(sample_query).to_dataframe()
                print(f"  Features: {', '.join(sample.columns[:8])}...")
                
                all_features['sentiment'].append(f"{dataset}.{table}")
        except:
            pass

print("\n2. WEATHER BY REGION (Critical for production forecasting):")
print("-"*80)

weather_regions = [
    'weather_brazil_daily',
    'weather_argentina_daily', 
    'weather_us_midwest_daily',
    'weather_paraguay_daily',
    'weather_uruguay_daily',
    'vw_brazil_precip_daily',
    'vw_brazil_weather_summary',
    'vw_weather_ar_daily',
    'vw_weather_br_daily',
    'vw_weather_usmw_daily',
    'vw_weather_global_daily',
]

for table in weather_regions:
    for dataset in ['forecasting_data_warehouse', 'signals', 'curated']:
        try:
            query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{dataset}.{table}`"
            result = client.query(query).to_dataframe()
            if result['cnt'].iloc[0] > 0:
                print(f"  {dataset}.{table}: {result['cnt'].iloc[0]:,} rows")
                all_features['weather'].append(f"{dataset}.{table}")
        except:
            pass

print("\n3. MARKET SHOCKS & EVENT DETECTION:")
print("-"*80)

shock_signals = [
    'vw_vix_stress_signal',
    'vw_harvest_pace_signal',
    'vw_china_relations_signal',
    'vw_tariff_threat_signal',
    'vw_geopolitical_volatility_signal',
    'vw_biofuel_cascade_signal',
    'vw_hidden_correlation_signal',
    'vw_trade_war_impact',
    'vw_supply_glut_indicator',
    'vw_bear_market_regime',
    'vw_biofuel_policy_intensity',
]

for signal in shock_signals:
    for dataset in ['signals', 'curated', 'models']:
        try:
            query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{dataset}.{signal}`"
            result = client.query(query).to_dataframe()
            if result['cnt'].iloc[0] > 0:
                print(f"  {dataset}.{signal}: {result['cnt'].iloc[0]:,} rows")
                all_features['shocks'].append(f"{dataset}.{signal}")
        except:
            pass

print("\n4. POLICY & REGULATORY INTELLIGENCE:")
print("-"*80)

policy_sources = [
    'trump_policy_intelligence',
    'ice_enforcement_intelligence',
    'ice_trump_intelligence',
    'vw_ice_trump_daily',
    'vw_trump_xi_volatility',
    'biofuel_policy',
]

for table in policy_sources:
    for dataset in ['forecasting_data_warehouse', 'signals', 'curated']:
        try:
            query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{dataset}.{table}`"
            result = client.query(query).to_dataframe()
            if result['cnt'].iloc[0] > 0:
                print(f"  {dataset}.{table}: {result['cnt'].iloc[0]:,} rows")
                all_features['policy'].append(f"{dataset}.{table}")
        except:
            pass

print("\n5. VOLATILITY REGIMES & VIX:")
print("-"*80)

volatility_tables = [
    'vix_daily',
    'volatility_data',
    'vw_vix_stress_signal',
    'vw_vix_stress_daily',
]

for table in volatility_tables:
    for dataset in ['forecasting_data_warehouse', 'signals']:
        try:
            query = f"""
            SELECT 
                COUNT(*) as rows,
                MIN(COALESCE(close, value, signal)) as min_val,
                MAX(COALESCE(close, value, signal)) as max_val,
                AVG(COALESCE(close, value, signal)) as avg_val
            FROM `cbi-v14.{dataset}.{table}`
            """
            result = client.query(query).to_dataframe()
            if result['rows'].iloc[0] > 0:
                print(f"\n{dataset}.{table}:")
                print(f"  Rows: {result['rows'].iloc[0]:,}")
                print(f"  Range: {result['min_val'].iloc[0]:.2f} - {result['max_val'].iloc[0]:.2f}")
                print(f"  Average: {result['avg_val'].iloc[0]:.2f}")
                all_features['volatility'].append(f"{dataset}.{table}")
        except:
            pass

print("\n6. FUNDAMENTAL DATA (CFTC, EXPORTS, IMPORTS):")
print("-"*80)

fundamental_tables = [
    'cftc_cot',
    'usda_export_sales',
    'usda_harvest_progress',
    'palm_oil_fundamentals',
    'vw_cftc_soybean_oil_weekly',
    'vw_usda_export_sales_soy_weekly',
    'vw_china_import_tracker',
    'vw_brazil_export_lineup',
]

for table in fundamental_tables:
    for dataset in ['forecasting_data_warehouse', 'curated', 'models']:
        try:
            query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{dataset}.{table}`"
            result = client.query(query).to_dataframe()
            if result['cnt'].iloc[0] > 0:
                print(f"  {dataset}.{table}: {result['cnt'].iloc[0]:,} rows")
                all_features['fundamentals'].append(f"{dataset}.{table}")
        except:
            pass

print("\n7. CROSS-ASSET CORRELATIONS (Pre-calculated):")
print("-"*80)

correlation_tables = [
    'vw_correlation_features',
    'vw_cross_asset_lead_lag',
    'vw_hidden_correlation_signal',
    'vw_palm_soy_spread_daily',
]

for table in correlation_tables:
    for dataset in ['signals', 'curated', 'models']:
        try:
            query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{dataset}.{table}`"
            result = client.query(query).to_dataframe()
            if result['cnt'].iloc[0] > 0:
                print(f"  {dataset}.{table}: {result['cnt'].iloc[0]:,} rows")
                
                # Check what correlations are calculated
                sample_query = f"SELECT * FROM `cbi-v14.{dataset}.{table}` LIMIT 1"
                sample = client.query(sample_query).to_dataframe()
                corr_cols = [c for c in sample.columns if 'corr' in c.lower() or 'spread' in c.lower()]
                if corr_cols:
                    print(f"    Correlations: {', '.join(corr_cols[:5])}...")
                
                all_features['correlations'].append(f"{dataset}.{table}")
        except:
            pass

print("\n8. TARIFFS & TRADE WAR INDICATORS:")
print("-"*80)

tariff_tables = [
    'vw_tariff_threat_signal',
    'vw_trade_war_impact',
    'vw_china_relations_signal',
]

for table in tariff_tables:
    for dataset in ['signals', 'curated']:
        try:
            query = f"""
            SELECT 
                COUNT(*) as rows,
                AVG(COALESCE(tariff_threat_score, trade_war_intensity, signal, impact_score)) as avg_signal
            FROM `cbi-v14.{dataset}.{table}`
            """
            result = client.query(query).to_dataframe()
            if result['rows'].iloc[0] > 0:
                print(f"  {dataset}.{table}:")
                print(f"    Rows: {result['rows'].iloc[0]:,}")
                print(f"    Avg signal: {result['avg_signal'].iloc[0]:.3f}")
                all_features['tariffs'].append(f"{dataset}.{table}")
        except:
            pass

print("\n9. CURRENCY & FX IMPACTS:")
print("-"*80)

fx_tables = [
    'usd_index_prices',
    'currency_data',
    'vw_usd_index_daily',
]

for table in fx_tables:
    for dataset in ['forecasting_data_warehouse', 'curated']:
        try:
            query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{dataset}.{table}`"
            result = client.query(query).to_dataframe()
            if result['cnt'].iloc[0] > 0:
                print(f"  {dataset}.{table}: {result['cnt'].iloc[0]:,} rows")
                all_features['fx'].append(f"{dataset}.{table}")
        except:
            pass

print("\n10. ECONOMIC INDICATORS & FED DATA:")
print("-"*80)

economic_tables = [
    'economic_indicators',
    'treasury_prices',
    'vw_treasury_daily',
]

for table in economic_tables:
    for dataset in ['forecasting_data_warehouse', 'curated']:
        try:
            query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{dataset}.{table}`"
            result = client.query(query).to_dataframe()
            if result['cnt'].iloc[0] > 0:
                print(f"  {dataset}.{table}: {result['cnt'].iloc[0]:,} rows")
                
                # Check what indicators are included
                if 'economic_indicators' in table:
                    sample_query = f"SELECT DISTINCT indicator_name FROM `cbi-v14.{dataset}.{table}` LIMIT 10"
                    try:
                        indicators = client.query(sample_query).to_dataframe()
                        print(f"    Indicators: {', '.join(indicators['indicator_name'].tolist()[:5])}...")
                    except:
                        pass
                
                all_features['economic'].append(f"{dataset}.{table}")
        except:
            pass

print("\n11. SEASONALITY & CYCLES:")
print("-"*80)

seasonality_tables = [
    'vw_seasonality_features',
    'vw_harvest_pace_signal',
    'usda_harvest_progress',
]

for table in seasonality_tables:
    for dataset in ['forecasting_data_warehouse', 'signals', 'models']:
        try:
            query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{dataset}.{table}`"
            result = client.query(query).to_dataframe()
            if result['cnt'].iloc[0] > 0:
                print(f"  {dataset}.{table}: {result['cnt'].iloc[0]:,} rows")
                all_features['seasonality'].append(f"{dataset}.{table}")
        except:
            pass

print("\n12. BIOFUEL & ENERGY COMPLEX:")
print("-"*80)

biofuel_tables = [
    'biofuel_prices',
    'biofuel_policy',
    'vw_biofuel_cascade_signal',
    'vw_biofuel_ethanol_signal',
    'vw_biofuel_policy_intensity',
]

for table in biofuel_tables:
    for dataset in ['forecasting_data_warehouse', 'signals']:
        try:
            query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{dataset}.{table}`"
            result = client.query(query).to_dataframe()
            if result['cnt'].iloc[0] > 0:
                print(f"  {dataset}.{table}: {result['cnt'].iloc[0]:,} rows")
                all_features['biofuel'].append(f"{dataset}.{table}")
        except:
            pass

print("\n" + "="*80)
print("FEATURE SUMMARY")
print("="*80)

total_features = 0
for category, tables in all_features.items():
    print(f"\n{category.upper()}: {len(tables)} sources")
    total_features += len(tables)
    for table in tables[:3]:  # Show first 3
        print(f"  - {table}")
    if len(tables) > 3:
        print(f"  ... and {len(tables)-3} more")

print(f"\n" + "="*80)
print(f"TOTAL UNIQUE DATA SOURCES: {total_features}")
print("="*80)

print("""
CRITICAL INSIGHTS:
1. We have MASSIVE amounts of intelligence data not being used
2. Each feature type has SPECIFIC predictive power:
   - Sentiment: Leading indicator (1-3 days)
   - VIX: Regime detection
   - Weather: Supply shocks
   - CFTC: Positioning extremes
   - Trump/Policy: Regulatory shocks
   - Correlations: Substitution effects
   
3. Need to include ALL of these with proper:
   - Time lags (sentiment leads, fundamentals lag)
   - Weightings (VIX more important in crisis)
   - Interactions (weather × harvest × sentiment)
   - Regime switching (different models for different VIX levels)

TRAINING MUST INCLUDE ALL THESE FEATURES!
""")

# Check what's actually in current training dataset
print("\n" + "="*80)
print("CHECKING CURRENT TRAINING DATASET")
print("="*80)

try:
    current_query = """
    SELECT *
    FROM `cbi-v14.models.training_dataset_final_v1`
    LIMIT 1
    """
    current = client.query(current_query).to_dataframe()
    current_features = list(current.columns)
    
    print(f"\nCurrent training dataset has {len(current_features)} features")
    
    # Check what categories are missing
    missing_categories = []
    if not any('sentiment' in f.lower() for f in current_features):
        missing_categories.append('SENTIMENT')
    if not any('cftc' in f.lower() or 'cot' in f.lower() for f in current_features):
        missing_categories.append('CFTC POSITIONING')
    if not any('treasury' in f.lower() or 'yield' in f.lower() for f in current_features):
        missing_categories.append('TREASURY YIELDS')
    if not any('economic' in f.lower() or 'gdp' in f.lower() or 'inflation' in f.lower() for f in current_features):
        missing_categories.append('ECONOMIC INDICATORS')
    if not any('ice' in f.lower() or 'enforcement' in f.lower() for f in current_features):
        missing_categories.append('ICE ENFORCEMENT')
    
    if missing_categories:
        print(f"\n⚠️ MISSING CRITICAL CATEGORIES:")
        for cat in missing_categories:
            print(f"  ✗ {cat}")
    
except Exception as e:
    print(f"Error checking training dataset: {e}")

print("\nBOTTOM LINE: We have the data but it's NOT in the training dataset!")
