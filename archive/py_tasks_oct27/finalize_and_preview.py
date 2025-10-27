#!/usr/bin/env python3
"""
FINALIZE DATASET AND SHOW TRAINING PREVIEW
Fix data types and show what models we can train
"""

import pandas as pd
import numpy as np
from datetime import datetime

print("="*80)
print("FINALIZING DATASET & TRAINING PREVIEW")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Load the CSV (more forgiving with mixed types)
print("\n1. LOADING AND FIXING DATASET")
print("-"*40)

df = pd.read_csv('training_dataset_enhanced_final.csv', low_memory=False)
print(f"Loaded dataset: {df.shape[0]} rows × {df.shape[1]} columns")

# Fix date column
df['date'] = pd.to_datetime(df['date'])

# Fix any object columns that should be numeric
print("\nFixing data types...")
for col in df.columns:
    if df[col].dtype == 'object' and col != 'date':
        try:
            # Try to convert to numeric
            df[col] = pd.to_numeric(df[col], errors='coerce')
        except:
            # If it's truly a string column, keep it as string
            df[col] = df[col].astype(str)

# Fill any NaN values appropriately
numeric_cols = df.select_dtypes(include=[np.number]).columns
for col in numeric_cols:
    df[col] = df[col].fillna(0)

print(f"✓ Fixed data types and filled missing values")

# Save clean version
df.to_csv('training_dataset_final.csv', index=False)
print(f"✓ Saved clean version: training_dataset_final.csv")

# 2. DATASET PREVIEW
print("\n" + "="*80)
print("📊 FINAL DATASET PREVIEW")
print("="*80)

print(f"\nDataset: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"Date Range: {df['date'].min().date()} to {df['date'].max().date()}")
print(f"Time Span: {(df['date'].max() - df['date'].min()).days / 365.25:.1f} years")

# Analyze feature categories
categories = {
    'Price & Returns': len([c for c in df.columns if any(x in c.lower() for x in ['price', 'return', 'target'])]),
    'Technical': len([c for c in df.columns if any(x in c.lower() for x in ['ma_', 'volatility', 'momentum'])]),
    'Commodities': len([c for c in df.columns if any(x in c.lower() for x in ['crude', 'palm', 'corn', 'wheat', 'bean', 'meal'])]),
    'Correlations': len([c for c in df.columns if 'corr_' in c.lower()]),
    'Market Indicators': len([c for c in df.columns if any(x in c.lower() for x in ['vix', 'dxy', 'sp500'])]),
    'Weather': len([c for c in df.columns if 'weather' in c.lower()]),
    'News & Sentiment': len([c for c in df.columns if any(x in c.lower() for x in ['news', 'sentiment', 'social'])]),
    'Policy & Events': len([c for c in df.columns if any(x in c.lower() for x in ['tariff', 'china', 'brazil', 'trump', 'policy'])]),
    'CFTC': len([c for c in df.columns if 'cftc' in c.lower()]),
    'Economic': len([c for c in df.columns if 'econ' in c.lower()]),
    'Signals': len([c for c in df.columns if 'signal' in c.lower()])
}

print("\n📈 FEATURE BREAKDOWN:")
print("-"*40)
for category, count in categories.items():
    bar = "█" * min(count // 5, 20)
    print(f"{category:20}: {count:3} features {bar}")

# Check sentiment coverage improvement
print("\n📰 SENTIMENT DATA COVERAGE:")
print("-"*40)

sentiment_features = [
    ('Social Sentiment', 'social_sentiment_avg'),
    ('Social Engagement', 'social_engagement_total'),
    ('News Volume', 'news_volume'),
    ('Sentiment Average', 'avg_sentiment'),
    ('Tariff Mentions', 'tariff_mentions'),
    ('Trade News', 'trade_news'),
    ('Oil News', 'oil_news'),
    ('Soybean News', 'soybean_news')
]

coverage_stats = []
for name, col in sentiment_features:
    if col in df.columns:
        non_zero = (df[col] != 0).sum()
        pct = (non_zero / len(df)) * 100
        coverage_stats.append((name, non_zero, pct))

coverage_stats.sort(key=lambda x: x[1], reverse=True)

for name, coverage, pct in coverage_stats:
    bar = "▓" * int(pct / 5)
    print(f"{name:20}: {coverage:4} days ({pct:5.1f}%) {bar}")

# 3. MODELS READY TO TRAIN
print("\n" + "="*80)
print("🚀 MODELS READY TO TRAIN")
print("="*80)

models = [
    {
        'category': '📈 PRICE FORECASTING',
        'models': [
            ('XGBoost Regressor', '1-week horizon', 'High accuracy for short-term'),
            ('LightGBM', '1-week horizon', 'Fast training, good performance'),
            ('Random Forest', 'Multi-horizon', 'Robust to outliers'),
            ('LSTM Neural Net', '1-month horizon', 'Captures complex patterns'),
            ('GRU Neural Net', '1-month horizon', 'Lighter than LSTM'),
            ('ARIMA/SARIMA', 'All horizons', 'Traditional time series')
        ]
    },
    {
        'category': '🌍 CROSS-COMMODITY',
        'models': [
            ('VAR Model', 'Multi-commodity', 'Vector autoregression'),
            ('Multivariate LSTM', 'All commodities', 'Deep learning across markets'),
            ('Correlation Network', 'Dynamic hedging', 'Risk management')
        ]
    },
    {
        'category': '📊 RISK-ADJUSTED',
        'models': [
            ('GARCH', 'Volatility forecast', 'Risk modeling'),
            ('Regime Switching', 'Market states', 'Bull/bear detection'),
            ('VIX-Weighted', 'Risk-adjusted', 'Volatility scaling')
        ]
    },
    {
        'category': '🌤️ WEATHER-DRIVEN',
        'models': [
            ('Weather RF', 'Seasonal', 'Climate impact'),
            ('Climate LSTM', 'Long-term', 'Weather patterns')
        ]
    },
    {
        'category': '📰 SENTIMENT-ENHANCED',
        'models': [
            ('News-Weighted XGBoost', 'Event-driven', 'News impact'),
            ('Social Sentiment LSTM', 'Market mood', 'Crowd psychology'),
            ('Policy Event Model', 'Shock prediction', 'Regulatory changes')
        ]
    }
]

for model_group in models:
    print(f"\n{model_group['category']}")
    print("-"*40)
    for model_name, horizon, description in model_group['models']:
        print(f"  • {model_name:25} [{horizon:15}] - {description}")

# 4. TRAINING CONFIGURATION
print("\n" + "="*80)
print("⚙️ RECOMMENDED TRAINING CONFIGURATION")
print("="*80)

print("\n1. TRAIN/TEST SPLIT:")
print("   • Training: 2020-2024 (80%)")
print("   • Validation: 2024 Q3-Q4 (10%)")
print("   • Test: 2025 (10%)")

print("\n2. FEATURE SETS:")
print("   • Core: Prices + Technical + Commodities")
print("   • Enhanced: Core + Weather + Market Indicators")
print("   • Full: All features including sentiment")

print("\n3. EVALUATION METRICS:")
print("   • MAE (Mean Absolute Error)")
print("   • RMSE (Root Mean Square Error)")
print("   • Direction Accuracy")
print("   • Sharpe Ratio (for trading)")

# 5. FINAL SUMMARY
print("\n" + "="*80)
print("✅ DATASET READY FOR TRAINING")
print("="*80)

print(f"\nFinal Dataset: training_dataset_final.csv")
print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"Features: {df.shape[1] - 5} (excluding date and targets)")  # Approximate

# Calculate data richness score
filled_cells = df.notna().sum().sum()
total_cells = df.shape[0] * df.shape[1]
richness = (filled_cells / total_cells) * 100

non_zero_cells = (df != 0).sum().sum()
data_density = (non_zero_cells / total_cells) * 100

print(f"\nData Quality Metrics:")
print(f"  • Fill Rate: {richness:.1f}%")
print(f"  • Data Density: {data_density:.1f}%")
print(f"  • Sentiment Coverage: {len(coverage_stats)} active features")

print("\n🎯 NEXT STEP: Run 'train_all_models.py' to train all models")
print("="*80)
