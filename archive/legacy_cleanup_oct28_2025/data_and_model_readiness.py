#!/usr/bin/env python3
"""
DATA AND MODEL READINESS ASSESSMENT
What data do we have and what models can we train?
"""

import pandas as pd
import numpy as np
from datetime import datetime

print("="*80)
print("DATA AND MODEL READINESS ASSESSMENT")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Load the clean dataset
df = pd.read_csv('training_dataset_clean.csv')
df['date'] = pd.to_datetime(df['date'])

print("\n📊 DATASET OVERVIEW")
print("-"*60)
print(f"Total Rows: {len(df):,}")
print(f"Total Features: {df.shape[1]}")
print(f"Date Range: {df['date'].min().date()} to {df['date'].max().date()}")
print(f"Time Span: {(df['date'].max() - df['date'].min()).days / 365.25:.1f} years")

# Analyze what data is actually populated
print("\n📈 DATA AVAILABILITY BY CATEGORY")
print("-"*60)

categories = {
    'PRICE DATA': {
        'columns': ['zl_price_current', 'zl_price_lag1', 'zl_price_lag7', 'zl_price_lag30'],
        'description': 'Soybean oil spot and historical prices'
    },
    'TECHNICAL INDICATORS': {
        'columns': ['return_1d', 'return_7d', 'ma_7d', 'ma_30d', 'volatility_30d'],
        'description': 'Returns, moving averages, volatility'
    },
    'TARGET VARIABLES': {
        'columns': ['target_1w', 'target_1m', 'target_3m', 'target_6m'],
        'description': 'Future prices for prediction'
    },
    'COMMODITY PRICES': {
        'columns': ['crude_price', 'palm_price', 'corn_price', 'wheat_price'],
        'description': 'Related commodity prices'
    },
    'CORRELATIONS': {
        'columns': [c for c in df.columns if 'corr_' in c][:5],  # Sample
        'description': 'Cross-market correlations (28 total)'
    },
    'MARKET INDICATORS': {
        'columns': ['vix_level', 'dxy_level'],
        'description': 'VIX volatility index, Dollar index'
    },
    'WEATHER DATA': {
        'columns': ['weather_brazil_temp', 'weather_brazil_precip', 'weather_us_temp'],
        'description': 'Temperature and precipitation data'
    },
    'EVENTS': {
        'columns': ['is_wasde_day', 'is_fomc_day', 'is_crop_report_day'],
        'description': 'Economic and agricultural events'
    },
    'NEWS & SENTIMENT': {
        'columns': ['news_article_count', 'tariff_weighted_score', 'china_weighted_score'],
        'description': 'News counts and sentiment scores'
    },
    'CFTC POSITIONING': {
        'columns': ['cftc_commercial_net', 'cftc_managed_net', 'cftc_open_interest'],
        'description': 'Futures positioning data'
    },
    'ECONOMIC DATA': {
        'columns': ['econ_gdp_growth', 'econ_inflation_rate', 'econ_unemployment_rate'],
        'description': 'Macroeconomic indicators'
    }
}

data_quality = {}

for category, info in categories.items():
    cols = [c for c in info['columns'] if c in df.columns]
    if cols:
        # Calculate fill rate
        total_values = len(df) * len(cols)
        non_zero = sum((df[col] != 0).sum() for col in cols)
        non_null = sum(df[col].notna().sum() for col in cols)
        
        fill_rate = (non_null / total_values) * 100 if total_values > 0 else 0
        populated_rate = (non_zero / total_values) * 100 if total_values > 0 else 0
        
        data_quality[category] = {
            'fill_rate': fill_rate,
            'populated_rate': populated_rate,
            'quality': 'EXCELLENT' if populated_rate > 80 else 'GOOD' if populated_rate > 50 else 'PARTIAL' if populated_rate > 10 else 'SPARSE'
        }
        
        status = "✅" if populated_rate > 50 else "🟨" if populated_rate > 10 else "⚠️"
        
        print(f"\n{status} {category}")
        print(f"   Description: {info['description']}")
        print(f"   Features: {len(cols)}")
        print(f"   Fill Rate: {fill_rate:.1f}%")
        print(f"   Data Quality: {data_quality[category]['quality']}")

# Model recommendations based on data availability
print("\n" + "="*80)
print("🎯 MODELS YOU CAN TRAIN NOW")
print("="*80)

print("\n✅ READY TO TRAIN (Excellent Data):")
print("-"*60)

models_ready = []

# Check for price prediction models
if data_quality.get('PRICE DATA', {}).get('quality') == 'EXCELLENT' and \
   data_quality.get('TARGET VARIABLES', {}).get('quality') == 'EXCELLENT':
    models_ready.append({
        'name': 'Price Forecasting Models',
        'types': ['ARIMA', 'LSTM', 'GRU', 'Random Forest', 'XGBoost'],
        'horizons': ['1-week', '1-month', '3-month', '6-month'],
        'features': 'Price, technical indicators, correlations'
    })

if data_quality.get('COMMODITY PRICES', {}).get('quality') in ['EXCELLENT', 'GOOD']:
    models_ready.append({
        'name': 'Cross-Commodity Models',
        'types': ['VAR', 'Multivariate LSTM', 'Ensemble'],
        'horizons': ['1-week', '1-month'],
        'features': 'Soybean oil + Crude + Palm + Corn + Wheat'
    })

if data_quality.get('MARKET INDICATORS', {}).get('quality') in ['EXCELLENT', 'GOOD']:
    models_ready.append({
        'name': 'Risk-Adjusted Models',
        'types': ['GARCH', 'Regime-Switching', 'Volatility-Weighted'],
        'horizons': ['1-week', '1-month'],
        'features': 'Prices + VIX + DXY + Volatility'
    })

if data_quality.get('WEATHER DATA', {}).get('quality') in ['EXCELLENT', 'GOOD']:
    models_ready.append({
        'name': 'Weather-Driven Models',
        'types': ['Weather-Adjusted RF', 'Climate LSTM'],
        'horizons': ['1-month', '3-month'],
        'features': 'Prices + Brazil/US weather'
    })

for model in models_ready:
    print(f"\n{model['name']}:")
    print(f"  Model Types: {', '.join(model['types'])}")
    print(f"  Horizons: {', '.join(model['horizons'])}")
    print(f"  Features: {model['features']}")

print("\n🟨 LIMITED TRAINING (Partial Data):")
print("-"*60)

if data_quality.get('NEWS & SENTIMENT', {}).get('quality') in ['PARTIAL', 'SPARSE']:
    print("\nNews Sentiment Models:")
    print("  Status: Only 4 days of news data")
    print("  Action: Need more news scraping for effective training")

if data_quality.get('CFTC POSITIONING', {}).get('quality') in ['PARTIAL', 'SPARSE']:
    print("\nPositioning-Based Models:")
    print("  Status: Only 72 days of CFTC data")
    print("  Action: Need historical CFTC data for COT analysis")

if data_quality.get('ECONOMIC DATA', {}).get('quality') in ['PARTIAL', 'SPARSE']:
    print("\nMacro-Driven Models:")
    print("  Status: Very sparse economic data")
    print("  Action: Need to load Fed/economic data properly")

# Specific model recommendations
print("\n" + "="*80)
print("💡 RECOMMENDED IMMEDIATE ACTIONS")
print("="*80)

print("\n1. START WITH THESE MODELS (Best Data):")
print("-"*40)
print("   • XGBoost Regressor for 1-week forecast")
print("   • LSTM for 1-month forecast")
print("   • Random Forest ensemble for multiple horizons")
print("   • Cross-commodity correlation model")

print("\n2. FEATURE ENGINEERING OPPORTUNITIES:")
print("-"*40)
print("   • Create rolling correlation windows")
print("   • Add seasonal decomposition")
print("   • Calculate relative strength indicators")
print("   • Build momentum features")

print("\n3. DATA TO PRIORITIZE LOADING:")
print("-"*40)
print("   • CFTC managed money positions (currently 0%)")
print("   • Treasury yields (currently 0%)")
print("   • More economic indicators")
print("   • Expand news coverage beyond 4 days")

# Summary statistics
print("\n" + "="*80)
print("📊 FINAL ASSESSMENT")
print("="*80)

excellent_count = sum(1 for v in data_quality.values() if v['quality'] == 'EXCELLENT')
good_count = sum(1 for v in data_quality.values() if v['quality'] == 'GOOD')
partial_count = sum(1 for v in data_quality.values() if v['quality'] == 'PARTIAL')
sparse_count = sum(1 for v in data_quality.values() if v['quality'] == 'SPARSE')

print(f"\nData Quality Summary:")
print(f"  Excellent: {excellent_count} categories")
print(f"  Good: {good_count} categories")
print(f"  Partial: {partial_count} categories")
print(f"  Sparse: {sparse_count} categories")

print(f"\nOverall Readiness: {'READY FOR PRODUCTION' if excellent_count >= 4 else 'READY FOR TESTING'}")
print(f"You can train {len(models_ready)} different model types immediately")

print("\n" + "="*80)
