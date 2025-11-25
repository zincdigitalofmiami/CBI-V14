#!/usr/bin/env python3
"""
Feature Engineering Functions - Complex Python-Based Calculations
Part of hybrid feature engineering approach (Python + BigQuery SQL).

This module handles complex feature calculations that are better suited for Python:
- Sentiment analysis and NLP
- Policy extraction and classification
- Complex interactions and non-linear transformations
- Advanced time-series features requiring custom logic

Simple features (correlations, moving averages, regimes) are calculated in BigQuery SQL.
See: config/bigquery/bigquery-sql/advanced_feature_engineering.sql

Architecture: Hybrid Python + BigQuery SQL
- BigQuery SQL: Correlations (CORR() OVER window), moving averages, regimes
- Python (this file): Complex sentiment, NLP, policy extraction, interactions

Author: AI Assistant
Date: November 17, 2025
Last Updated: November 17, 2025
Status: Active - Part of production feature engineering pipeline
"""

import numpy as np
import pandas as pd
from datetime import datetime
import warnings

from src.utils.timeseries import (
    moving_average,
    bollinger_bands,
    relative_strength_index,
    macd,
    realized_volatility,
    range_volatility,
    seasonal_adjustment_rolling,
)

warnings.filterwarnings("ignore")

# Set random seeds for reproducibility (Fix #6)
import os

os.environ["PYTHONHASHSEED"] = "42"


def calculate_technical_indicators(df):
    """
    Calculate technical indicators for price series.
    
    Features:
    - RSI (14-day, 30-day)
    - MACD (12, 26, 9)
    - Bollinger Bands (20-day, 2 std dev)
    - Moving averages (7, 30, 90, 200 day)
    - Momentum indicators (ROC, Williams %R)
    - Volume indicators (OBV, volume MA)
    - Support/resistance levels
    
    Args:
        df: DataFrame with at least 'date' and price columns
        
    Returns:
        df: DataFrame with technical indicator columns added
    """
    print("\n📊 Calculating technical indicators...")
    
    # Identify price column (support multiple symbol prefixes)
    price_col = None
    for col in ['close', 'zl_price_current', 'mes_close', 'es_close', 'price']:
        if col in df.columns:
            price_col = col
            break
    
    if price_col is None:
        print("⚠️ Warning: No price column found for technical indicators")
        return df
    
    # Sort by date for time series calculations
    df = df.sort_values('date').copy()
    
    # Handle multi-symbol data
    if 'symbol' in df.columns:
        print(f"  Processing {df['symbol'].nunique()} symbols...")
        result_dfs = []
        for symbol in df['symbol'].unique():
            symbol_df = df[df['symbol'] == symbol].copy()
            symbol_df = _calculate_technical_for_series(symbol_df, price_col)
            result_dfs.append(symbol_df)
        df = pd.concat(result_dfs, ignore_index=True)
    else:
        df = _calculate_technical_for_series(df, price_col)
    
    print(f"  ✅ Added {len([c for c in df.columns if c.startswith('tech_')])} technical indicators")
    return df


def _calculate_technical_for_series(df, price_col):
    """Helper function to calculate technical indicators for a single series."""
    
    price = df[price_col]

    # Moving Averages
    for period in [7, 30, 90, 200]:
        df[f"tech_ma_{period}d"] = moving_average(price, period)
    
    # Price returns
    df["tech_return_1d"] = price.pct_change()
    df["tech_return_7d"] = price.pct_change(periods=7)
    df["tech_return_30d"] = price.pct_change(periods=30)
    
    # RSI (Relative Strength Index)
    for period in [14, 30]:
        df[f"tech_rsi_{period}d"] = relative_strength_index(price, period)
    
    # MACD (Moving Average Convergence Divergence)
    macd_df = macd(price, fast_span=12, slow_span=26, signal_span=9)
    df["tech_macd_line"] = macd_df["macd_line"]
    df["tech_macd_signal"] = macd_df["macd_signal"]
    df["tech_macd_histogram"] = macd_df["macd_histogram"]
    
    # Bollinger Bands
    bb_period = 20
    bb_std = 2
    bb = bollinger_bands(price, bb_period, num_std=bb_std)
    df["tech_bb_middle"] = bb["bb_middle"]
    df["tech_bb_upper"] = bb["bb_upper"]
    df["tech_bb_lower"] = bb["bb_lower"]
    df["tech_bb_width"] = bb["bb_width"]
    df["tech_bb_position"] = bb["bb_position"]
    
    # Rate of Change (ROC)
    for period in [10, 20]:
        df[f'tech_roc_{period}d'] = ((df[price_col] - df[price_col].shift(period)) / df[price_col].shift(period)) * 100
    
    # Williams %R
    period = 14
    if 'high' in df.columns and 'low' in df.columns:
        highest_high = df['high'].rolling(window=period, min_periods=1).max()
        lowest_low = df['low'].rolling(window=period, min_periods=1).min()
        df['tech_williams_r'] = -100 * ((highest_high - df[price_col]) / (highest_high - lowest_low + 1e-10))
    
    # Volume indicators (if volume data available)
    if 'volume' in df.columns or 'zl_volume' in df.columns:
        vol_col = 'volume' if 'volume' in df.columns else 'zl_volume'
        
        # On-Balance Volume (OBV)
        df['tech_obv'] = (df[vol_col] * np.sign(df[price_col].diff())).fillna(0).cumsum()
        
        # Volume Moving Average
        df['tech_volume_ma_20d'] = df[vol_col].rolling(window=20, min_periods=1).mean()
        df['tech_volume_ratio'] = df[vol_col] / (df['tech_volume_ma_20d'] + 1e-10)
    
    # Support and Resistance (simplified - using rolling min/max)
    for period in [20, 50]:
        df[f'tech_support_{period}d'] = df[price_col].rolling(window=period, min_periods=1).min()
        df[f'tech_resistance_{period}d'] = df[price_col].rolling(window=period, min_periods=1).max()
    
    # Price position indicators
    df['tech_price_vs_ma30'] = (df[price_col] - df['tech_ma_30d']) / (df['tech_ma_30d'] + 1e-10)
    df['tech_price_vs_ma200'] = (df[price_col] - df['tech_ma_200d']) / (df['tech_ma_200d'] + 1e-10)
    
    return df


def calculate_cross_asset_features(df):
    """
    Calculate cross-asset correlation and relationship features.
    
    Features:
    - Correlations (30-day, 90-day rolling) with key assets
    - Spread calculations (price differences)
    - Ratio calculations (price ratios)
    
    Args:
        df: DataFrame with price columns for multiple assets
        
    Returns:
        df: DataFrame with cross-asset feature columns added
    """
    print("\n🔗 Calculating cross-asset features...")
    
    # Define asset columns to look for
    asset_mapping = {
        'palm_oil': ['palm_oil_price', 'fcpo_price', 'palm_price'],
        'crude_oil': ['crude_oil_price', 'wti_price', 'crude_price'],
        'natural_gas': ['natural_gas_price', 'natgas_price', 'gas_price'],
        'corn': ['corn_price', 'corn_close'],
        'wheat': ['wheat_price', 'wheat_close'],
        'soybeans': ['soybeans_price', 'soybean_price', 'soy_price'],
        'gold': ['gold_price', 'gold_close'],
        'silver': ['silver_price', 'silver_close'],
        'copper': ['copper_price', 'copper_close'],
        'vix': ['vix', 'vix_close', 'vix_level'],
        'sp500': ['sp500_price', 'sp500_close', 'spx_price'],
        'usd': ['usd_index', 'dxy_price', 'dollar_index']
    }
    
    # Find available columns
    available_assets = {}
    for asset, possible_cols in asset_mapping.items():
        for col in possible_cols:
            if col in df.columns:
                available_assets[asset] = col
                break
    
    # Get base price column
    base_price = None
    for col in ['close', 'zl_price_current', 'price']:
        if col in df.columns:
            base_price = col
            break
    
    if base_price is None or len(available_assets) == 0:
        print("⚠️ Warning: Insufficient price columns for cross-asset features")
        return df
    
    print(f"  Found {len(available_assets)} cross-assets: {list(available_assets.keys())}")
    
    # Sort by date
    df = df.sort_values('date').copy()
    
    # Calculate features for each cross-asset
    for asset, col in available_assets.items():
        # Correlations (30-day and 90-day rolling)
        for period in [30, 90]:
            if 'symbol' in df.columns:
                # Multi-symbol: calculate per symbol
                corr_values = []
                for symbol in df['symbol'].unique():
                    mask = df['symbol'] == symbol
                    symbol_corr = df.loc[mask, base_price].rolling(window=period, min_periods=period//2).corr(df.loc[mask, col])
                    corr_values.extend(symbol_corr.values)
                df[f'cross_corr_{asset}_{period}d'] = corr_values
            else:
                df[f'cross_corr_{asset}_{period}d'] = df[base_price].rolling(window=period, min_periods=period//2).corr(df[col])
        
        # Spreads (price differences)
        df[f'cross_spread_{asset}'] = df[base_price] - df[col]
        df[f'cross_spread_{asset}_pct'] = (df[base_price] - df[col]) / (df[col] + 1e-10)
        
        # Ratios
        df[f'cross_ratio_{asset}'] = df[base_price] / (df[col] + 1e-10)
        
        # Relative strength (price performance difference)
        for period in [7, 30]:
            base_ret = df[base_price].pct_change(periods=period)
            asset_ret = df[col].pct_change(periods=period)
            df[f'cross_relstrength_{asset}_{period}d'] = base_ret - asset_ret
    
    # Special cross-asset combinations
    if 'palm_oil' in available_assets and 'crude_oil' in available_assets:
        # Palm/Crude spread (important for biofuel economics)
        df['cross_palm_crude_spread'] = df[available_assets['palm_oil']] - df[available_assets['crude_oil']]
        df['cross_palm_crude_ratio'] = df[available_assets['palm_oil']] / (df[available_assets['crude_oil']] + 1e-10)
    
    if 'corn' in available_assets and 'soybeans' in available_assets:
        # Corn/Soy ratio (planting decisions)
        df['cross_corn_soy_ratio'] = df[available_assets['corn']] / (df[available_assets['soybeans']] + 1e-10)
    
    print(f"  ✅ Added {len([c for c in df.columns if c.startswith('cross_')])} cross-asset features")
    return df


def calculate_volatility_features(df):
    """
    Calculate volatility-based features using futures-only inputs.
    
    Features (all derived from real prices we already have):
    - Realized volatility (5/10/20/60/120-day) – annualised
    - Vol-of-vol and percentile ranks
    - Parkinson / Garman-Klass / Yang-Zhang estimators (OHLC based)
    - Range-based signals
    - Volatility clustering + EWMA proxy
    - Regime overlays via VIX (if available)
    
    Args:
        df: DataFrame with price data
        
    Returns:
        df: DataFrame with volatility feature columns added
    """
    print("\n📈 Calculating volatility features...")
    
    # Get price column
    price_col = None
    for col in ['close', 'zl_price_current', 'price']:
        if col in df.columns:
            price_col = col
            break
    
    if price_col is None:
        print("⚠️ Warning: No price column found for volatility features")
        return df
    
    # Sort by date
    df = df.sort_values('date').copy()
    
    # Calculate returns if not already present
    if 'tech_return_1d' not in df.columns:
        df['returns'] = df[price_col].pct_change()
    else:
        df['returns'] = df['tech_return_1d']
    
    # Realized volatility (annualized) at multiple horizons
    realized_windows = [5, 10, 20, 60, 120]
    for period in realized_windows:
        if 'symbol' in df.columns:
            # Multi-symbol: calculate per symbol
            vol_values = []
            for symbol in df['symbol'].unique():
                mask = df['symbol'] == symbol
                symbol_vol = df.loc[mask, 'returns'].rolling(window=period, min_periods=period//2).std() * np.sqrt(252)
                vol_values.extend(symbol_vol.values)
            df[f'vol_realized_{period}d'] = vol_values
        else:
            df[f'vol_realized_{period}d'] = df['returns'].rolling(window=period, min_periods=period//2).std() * np.sqrt(252)
    
    # Volatility of volatility
    df['vol_of_vol_30d'] = df['vol_realized_30d'].rolling(window=30, min_periods=15).std()
    
    # Parkinson / Garman-Klass / Yang-Zhang (if OHLC available)
    has_ohlc = all(col in df.columns for col in ['open', 'high', 'low', 'close'])
    if has_ohlc:
        log_hl_sq = (np.log(df['high'] / df['low'])) ** 2
        log_co = np.log(df['close'] / df['open'])
        log_oc = np.log(df['open'] / df['close'].shift(1))
        log_cc = np.log(df['close'] / df['close'].shift(1))

        df['vol_parkinson_30d'] = np.sqrt(
            log_hl_sq.rolling(window=30, min_periods=15).mean() / (4 * np.log(2))
        ) * np.sqrt(252)

        gk_component = 0.5 * log_hl_sq - (2 * np.log(2) - 1) * (log_co ** 2)
        df['vol_garman_klass_30d'] = np.sqrt(
            gk_component.rolling(window=30, min_periods=15).mean()
        ) * np.sqrt(252)

        yz_component = (
            0.34 * (log_oc ** 2)
            + 0.66 * (log_cc ** 2)
            + (0.53 * log_hl_sq)
        )
        df['vol_yang_zhang_30d'] = np.sqrt(
            yz_component.rolling(window=30, min_periods=15).mean()
        ) * np.sqrt(252)
    
    # VIX-based features (backup/validation) - if VIX data available
    vix_col = None
    for col in ['vix', 'vix_close', 'vix_level']:
        if col in df.columns:
            vix_col = col
            break
    
    if vix_col:
        # VIX level and changes (for validation/cross-check)
        df['vol_vix_level'] = df[vix_col]
        df['vol_vix_change_1d'] = df[vix_col].diff()
        df['vol_vix_change_7d'] = df[vix_col].diff(7)
        
        # VIX regime
        df['vol_vix_regime'] = pd.cut(
            df[vix_col],
            bins=[0, 15, 20, 30, 100],
            labels=['low', 'normal', 'elevated', 'high']
        )
        df['vol_vix_regime_numeric'] = df['vol_vix_regime'].cat.codes
        
        # VIX term structure (if available)
        if 'vix9d' in df.columns and 'vix30d' in df.columns:
            df['vol_vix_term_structure'] = df['vix9d'] - df['vix30d']
    
    # Volatility clustering (autocorrelation of squared returns)
    squared_returns = df['returns'] ** 2
    df['vol_clustering_7d'] = squared_returns.rolling(window=7, min_periods=3).mean()
    df['vol_clustering_30d'] = squared_returns.rolling(window=30, min_periods=15).mean()
    
    # GARCH-style conditional volatility (simplified)
    # Using exponentially weighted moving average of squared returns
    df['vol_ewma'] = squared_returns.ewm(span=20, adjust=False).mean() ** 0.5 * np.sqrt(252)
    
    # Volatility percentile rank
    for period in [30, 90]:
        vol_col = f'vol_realized_{period}d'
        df[f'vol_percentile_{period}d'] = df[vol_col].rolling(window=252, min_periods=100).rank(pct=True)
    
    # High-low range volatility
    if 'high' in df.columns and 'low' in df.columns:
        df['vol_range_pct'] = (df['high'] - df['low']) / df[price_col]
        df['vol_range_ma_20d'] = df['vol_range_pct'].rolling(window=20, min_periods=10).mean()
    
    # Clean up temporary column
    if 'returns' in df.columns and 'tech_return_1d' in df.columns:
        df = df.drop('returns', axis=1)
    
    print(f"  ✅ Added {len([c for c in df.columns if c.startswith('vol_')])} volatility features")
    return df


def calculate_seasonal_features(df):
    """
    Calculate seasonal and calendar-based features.
    
    Features:
    - Month, quarter, day-of-week encoding
    - Harvest season indicators (US, Brazil, Argentina)
    - Cyclical patterns (sine/cosine transforms)
    - Holiday effects
    
    Args:
        df: DataFrame with date column
        
    Returns:
        df: DataFrame with seasonal feature columns added
    """
    print("\n📅 Calculating seasonal features...")
    
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Basic calendar features
    df['seas_month'] = df['date'].dt.month
    df['seas_quarter'] = df['date'].dt.quarter
    df['seas_day_of_week'] = df['date'].dt.dayofweek
    df['seas_day_of_month'] = df['date'].dt.day
    df['seas_week_of_year'] = df['date'].dt.isocalendar().week
    
    # Cyclical encoding (sine/cosine transforms for continuity)
    df['seas_month_sin'] = np.sin(2 * np.pi * df['seas_month'] / 12)
    df['seas_month_cos'] = np.cos(2 * np.pi * df['seas_month'] / 12)
    df['seas_day_of_week_sin'] = np.sin(2 * np.pi * df['seas_day_of_week'] / 7)
    df['seas_day_of_week_cos'] = np.cos(2 * np.pi * df['seas_day_of_week'] / 7)
    df['seas_week_sin'] = np.sin(2 * np.pi * df['seas_week_of_year'] / 52)
    df['seas_week_cos'] = np.cos(2 * np.pi * df['seas_week_of_year'] / 52)
    
    # Harvest season indicators
    # US harvest: September-November (months 9-11)
    df['seas_us_harvest'] = df['seas_month'].isin([9, 10, 11]).astype(int)
    df['seas_us_planting'] = df['seas_month'].isin([4, 5, 6]).astype(int)
    
    # Brazil harvest: February-April (months 2-4)
    df['seas_brazil_harvest'] = df['seas_month'].isin([2, 3, 4]).astype(int)
    df['seas_brazil_planting'] = df['seas_month'].isin([10, 11, 12]).astype(int)
    
    # Argentina harvest: March-May (months 3-5)
    df['seas_argentina_harvest'] = df['seas_month'].isin([3, 4, 5]).astype(int)
    df['seas_argentina_planting'] = df['seas_month'].isin([10, 11, 12]).astype(int)
    
    # Combined harvest indicator (any major harvest)
    df['seas_any_harvest'] = (
        df['seas_us_harvest'] | 
        df['seas_brazil_harvest'] | 
        df['seas_argentina_harvest']
    ).astype(int)
    
    # Quarter-end effects
    df['seas_quarter_end'] = df['date'].dt.is_quarter_end.astype(int)
    df['seas_month_end'] = df['date'].dt.is_month_end.astype(int)
    df['seas_month_start'] = df['date'].dt.is_month_start.astype(int)
    
    # Trading day features
    df['seas_monday'] = (df['seas_day_of_week'] == 0).astype(int)
    df['seas_friday'] = (df['seas_day_of_week'] == 4).astype(int)
    
    # Holiday proximity (simplified - US holidays)
    # Major holidays that might affect trading
    df['seas_january_effect'] = (df['seas_month'] == 1).astype(int)  # January effect
    df['seas_december'] = (df['seas_month'] == 12).astype(int)  # Year-end effects
    
    # Days since year start (for trend)
    df['seas_day_of_year'] = df['date'].dt.dayofyear
    df['seas_days_in_year'] = df['date'].dt.is_leap_year.map({True: 366, False: 365})
    df['seas_year_progress'] = df['seas_day_of_year'] / df['seas_days_in_year']
    
    # Seasonal strength indicators
    # Summer months (June-August) often have different volatility patterns
    df['seas_summer'] = df['seas_month'].isin([6, 7, 8]).astype(int)
    df['seas_winter'] = df['seas_month'].isin([12, 1, 2]).astype(int)
    
    # Options expiration week (third Friday of month)
    # Approximate by checking if it's the third week and Friday
    df['seas_options_week'] = (
        (df['seas_day_of_month'] >= 15) & 
        (df['seas_day_of_month'] <= 21) & 
        (df['seas_day_of_week'] == 4)
    ).astype(int)
    
    print(f"  ✅ Added {len([c for c in df.columns if c.startswith('seas_')])} seasonal features")
    return df


def calculate_macro_regime_features(df):
    """
    Calculate macroeconomic regime features.
    
    Features:
    - Fed funds rate regime (low/medium/high)
    - Yield curve features (10Y-2Y spread)
    - Economic cycle indicators
    - Inflation regime features
    
    Args:
        df: DataFrame with macro data columns
        
    Returns:
        df: DataFrame with macro regime feature columns added
    """
    print("\n🏛️ Calculating macro regime features...")
    
    # Fed funds rate regime
    if 'fed_funds_rate' in df.columns:
        # Define rate regimes based on historical context
        df['macro_fed_regime'] = pd.cut(
            df['fed_funds_rate'],
            bins=[-np.inf, 1.0, 3.0, 5.0, np.inf],
            labels=['ultra_low', 'low', 'normal', 'high']
        )
        df['macro_fed_regime_numeric'] = df['macro_fed_regime'].cat.codes
        
        # Rate changes
        df['macro_fed_change_30d'] = df['fed_funds_rate'].diff(30)
        df['macro_fed_change_90d'] = df['fed_funds_rate'].diff(90)
        
        # Rate cycle position (distance from 2-year min/max)
        df['macro_fed_2y_min'] = df['fed_funds_rate'].rolling(window=504, min_periods=252).min()
        df['macro_fed_2y_max'] = df['fed_funds_rate'].rolling(window=504, min_periods=252).max()
        df['macro_fed_cycle_position'] = (
            (df['fed_funds_rate'] - df['macro_fed_2y_min']) / 
            (df['macro_fed_2y_max'] - df['macro_fed_2y_min'] + 1e-10)
        )
    
    # Yield curve features
    if 'treasury_10y' in df.columns and 'treasury_2y' in df.columns:
        # 10Y-2Y spread (classic recession indicator)
        df['macro_yield_curve_10y2y'] = df['treasury_10y'] - df['treasury_2y']
        df['macro_yield_curve_inverted'] = (df['macro_yield_curve_10y2y'] < 0).astype(int)
        
        # Yield curve changes
        df['macro_yield_curve_change_30d'] = df['macro_yield_curve_10y2y'].diff(30)
        df['macro_yield_curve_change_90d'] = df['macro_yield_curve_10y2y'].diff(90)
        
        # Yield curve regime
        df['macro_yield_regime'] = pd.cut(
            df['macro_yield_curve_10y2y'],
            bins=[-np.inf, 0, 0.5, 1.5, np.inf],
            labels=['inverted', 'flat', 'normal', 'steep']
        )
        df['macro_yield_regime_numeric'] = df['macro_yield_regime'].cat.codes
    
    # Real rates (if inflation data available)
    if 'fed_funds_rate' in df.columns and 'cpi_yoy' in df.columns:
        df['macro_real_rate'] = df['fed_funds_rate'] - df['cpi_yoy']
        df['macro_real_rate_regime'] = pd.cut(
            df['macro_real_rate'],
            bins=[-np.inf, -1, 0, 2, np.inf],
            labels=['deeply_negative', 'negative', 'low_positive', 'high_positive']
        )
        df['macro_real_rate_regime_numeric'] = df['macro_real_rate_regime'].cat.codes
    
    # Dollar strength regime (if USD index available)
    for col in ['usd_index', 'dxy_price', 'dollar_index', 'usd_broad_index']:
        if col in df.columns:
            # Dollar trend
            df['macro_usd_ma_50d'] = df[col].rolling(window=50, min_periods=25).mean()
            df['macro_usd_ma_200d'] = df[col].rolling(window=200, min_periods=100).mean()
            df['macro_usd_trend'] = (df['macro_usd_ma_50d'] > df['macro_usd_ma_200d']).astype(int)
            
            # Dollar strength percentile
            df['macro_usd_percentile_1y'] = df[col].rolling(window=252, min_periods=126).rank(pct=True)
            
            # Dollar momentum
            df['macro_usd_momentum_30d'] = df[col].pct_change(periods=30)
            df['macro_usd_momentum_90d'] = df[col].pct_change(periods=90)
            break
    
    # Economic growth indicators (if GDP data available)
    if 'gdp_growth' in df.columns:
        df['macro_gdp_regime'] = pd.cut(
            df['gdp_growth'],
            bins=[-np.inf, 0, 2, 3, np.inf],
            labels=['recession', 'slow_growth', 'moderate_growth', 'strong_growth']
        )
        df['macro_gdp_regime_numeric'] = df['macro_gdp_regime'].cat.codes
    
    # Inflation regime (if CPI data available)
    if 'cpi_yoy' in df.columns or 'inflation_rate' in df.columns:
        inflation_col = 'cpi_yoy' if 'cpi_yoy' in df.columns else 'inflation_rate'
        df['macro_inflation_regime'] = pd.cut(
            df[inflation_col],
            bins=[-np.inf, 0, 2, 4, np.inf],
            labels=['deflation', 'low_inflation', 'moderate_inflation', 'high_inflation']
        )
        df['macro_inflation_regime_numeric'] = df['macro_inflation_regime'].cat.codes
        
        # Inflation momentum
        df['macro_inflation_change_90d'] = df[inflation_col].diff(90)
        df['macro_inflation_accelerating'] = (df['macro_inflation_change_90d'] > 0.5).astype(int)
    
    # Composite macro regime score
    regime_scores = []
    if 'macro_fed_regime_numeric' in df.columns:
        regime_scores.append(df['macro_fed_regime_numeric'])
    if 'macro_yield_regime_numeric' in df.columns:
        regime_scores.append(df['macro_yield_regime_numeric'])
    if 'macro_inflation_regime_numeric' in df.columns:
        regime_scores.append(df['macro_inflation_regime_numeric'])
    
    if regime_scores:
        df['macro_composite_regime'] = pd.concat(regime_scores, axis=1).mean(axis=1)
    
    print(f"  ✅ Added {len([c for c in df.columns if c.startswith('macro_')])} macro regime features")
    return df


def calculate_weather_aggregations(df):
    """
    Calculate weather-based aggregation features.
    
    Features:
    - Regional temperature aggregations (US Midwest, Brazil, Argentina)
    - Precipitation aggregations (30-day, 90-day rolling)
    - Drought indicators
    - Growing degree days
    
    Args:
        df: DataFrame with weather data columns
        
    Returns:
        df: DataFrame with weather feature columns added
    """
    print("\n🌦️ Calculating weather aggregations...")
    
    # Sort by date
    df = df.sort_values('date').copy()
    
    # US Midwest weather
    us_temp_cols = [col for col in df.columns if 
                    any(x in col.lower() for x in ['us_temp', 'midwest_temp', 'us_midwest_temp'])]
    us_precip_cols = [col for col in df.columns if 
                      any(x in col.lower() for x in ['us_precip', 'midwest_precip', 'us_midwest_precip'])]
    
    if us_temp_cols:
        temp_col = us_temp_cols[0]
        # Temperature aggregations
        df['weather_us_temp_ma_7d'] = df[temp_col].rolling(window=7, min_periods=3).mean()
        df['weather_us_temp_ma_30d'] = df[temp_col].rolling(window=30, min_periods=15).mean()
        
        # Temperature anomalies (vs 30-day average)
        df['weather_us_temp_anomaly'] = df[temp_col] - df['weather_us_temp_ma_30d']
        
        # Extreme temperature indicators
        df['weather_us_extreme_heat'] = (df[temp_col] > df[temp_col].quantile(0.9)).astype(int)
        df['weather_us_extreme_cold'] = (df[temp_col] < df[temp_col].quantile(0.1)).astype(int)
        
        # Growing degree days (base 50°F = 10°C)
        df['weather_us_gdd'] = np.maximum(df[temp_col] - 10, 0)
        df['weather_us_gdd_cumsum'] = df.groupby(df['date'].dt.year)['weather_us_gdd'].cumsum()
    
    if us_precip_cols:
        precip_col = us_precip_cols[0]
        # Precipitation aggregations
        df['weather_us_precip_7d'] = df[precip_col].rolling(window=7, min_periods=3).sum()
        df['weather_us_precip_30d'] = df[precip_col].rolling(window=30, min_periods=15).sum()
        df['weather_us_precip_90d'] = df[precip_col].rolling(window=90, min_periods=45).sum()
        
        # Drought indicators (low precipitation)
        df['weather_us_drought_30d'] = (df['weather_us_precip_30d'] < df['weather_us_precip_30d'].quantile(0.2)).astype(int)
        df['weather_us_drought_90d'] = (df['weather_us_precip_90d'] < df['weather_us_precip_90d'].quantile(0.2)).astype(int)
        
        # Excess moisture indicators
        df['weather_us_excess_moisture_30d'] = (df['weather_us_precip_30d'] > df['weather_us_precip_30d'].quantile(0.8)).astype(int)
    
    # Brazil weather
    brazil_temp_cols = [col for col in df.columns if 
                        any(x in col.lower() for x in ['brazil_temp', 'br_temp'])]
    brazil_precip_cols = [col for col in df.columns if 
                          any(x in col.lower() for x in ['brazil_precip', 'br_precip'])]
    
    if brazil_temp_cols:
        temp_col = brazil_temp_cols[0]
        df['weather_brazil_temp_ma_30d'] = df[temp_col].rolling(window=30, min_periods=15).mean()
        df['weather_brazil_temp_anomaly'] = df[temp_col] - df['weather_brazil_temp_ma_30d']
        df['weather_brazil_gdd'] = np.maximum(df[temp_col] - 10, 0)
    
    if brazil_precip_cols:
        precip_col = brazil_precip_cols[0]
        df['weather_brazil_precip_30d'] = df[precip_col].rolling(window=30, min_periods=15).sum()
        df['weather_brazil_drought_30d'] = (df['weather_brazil_precip_30d'] < df['weather_brazil_precip_30d'].quantile(0.2)).astype(int)
    
    # Argentina weather
    argentina_temp_cols = [col for col in df.columns if 
                           any(x in col.lower() for x in ['argentina_temp', 'ar_temp'])]
    argentina_precip_cols = [col for col in df.columns if 
                             any(x in col.lower() for x in ['argentina_precip', 'ar_precip'])]
    
    if argentina_temp_cols:
        temp_col = argentina_temp_cols[0]
        df['weather_argentina_temp_ma_30d'] = df[temp_col].rolling(window=30, min_periods=15).mean()
        df['weather_argentina_temp_anomaly'] = df[temp_col] - df['weather_argentina_temp_ma_30d']
        df['weather_argentina_gdd'] = np.maximum(df[temp_col] - 10, 0)
    
    if argentina_precip_cols:
        precip_col = argentina_precip_cols[0]
        df['weather_argentina_precip_30d'] = df[precip_col].rolling(window=30, min_periods=15).sum()
        df['weather_argentina_drought_30d'] = (df['weather_argentina_precip_30d'] < df['weather_argentina_precip_30d'].quantile(0.2)).astype(int)
    
    # Combined weather stress indicator
    drought_cols = [col for col in df.columns if 'drought' in col and col.startswith('weather_')]
    if drought_cols:
        df['weather_global_drought_stress'] = df[drought_cols].sum(axis=1)
        df['weather_any_drought'] = (df['weather_global_drought_stress'] > 0).astype(int)
    
    # La Niña/El Niño indicators (if SOI data available)
    if 'soi_index' in df.columns:
        df['weather_la_nina'] = (df['soi_index'] > 7).astype(int)
        df['weather_el_nino'] = (df['soi_index'] < -7).astype(int)
        df['weather_enso_neutral'] = ((df['soi_index'] >= -7) & (df['soi_index'] <= 7)).astype(int)
    
    print(f"  ✅ Added {len([c for c in df.columns if c.startswith('weather_')])} weather features")
    return df


def add_regime_columns(df):
    """
    Add market regime and training weight columns.
    
    Features:
    - Merge regime_calendar.parquet
    - Add market_regime column
    - Add training_weight column based on regime_weights.parquet
    - Validate regime assignments
    
    Args:
        df: DataFrame with date column
        
    Returns:
        df: DataFrame with regime columns added
    """
    print("\n🏷️ Adding regime columns...")
    
    from pathlib import Path
    DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
    
    # Load regime calendar
    regime_calendar_path = DRIVE / "registry/regime_calendar.parquet"
    regime_weights_path = DRIVE / "registry/regime_weights.parquet"
    
    if not regime_calendar_path.exists():
        print(f"⚠️ Warning: regime_calendar.parquet not found at {regime_calendar_path}")
        print("  Using default regime 'allhistory' with weight 1")
        df['market_regime'] = 'allhistory'
        df['training_weight'] = 1
        return df
    
    # Load regime data
    regime_calendar = pd.read_parquet(regime_calendar_path)
    regime_calendar['date'] = pd.to_datetime(regime_calendar['date'])
    
    # Merge regime assignments
    df['date'] = pd.to_datetime(df['date'])
    df = df.merge(regime_calendar[['date', 'regime']], on='date', how='left')
    
    # Rename to market_regime
    if 'regime' in df.columns:
        df['market_regime'] = df['regime']
        df = df.drop('regime', axis=1)
    
    # Fill any missing regimes with 'allhistory'
    df['market_regime'] = df['market_regime'].fillna('allhistory')
    
    # Load and apply regime weights
    if regime_weights_path.exists():
        regime_weights = pd.read_parquet(regime_weights_path)
        
        # Create weight mapping
        weight_map = dict(zip(regime_weights['regime'], regime_weights['weight']))
        
        # Apply weights
        df['training_weight'] = df['market_regime'].map(weight_map).fillna(1)
        
        print(f"  Regime weight mapping:")
        for regime, weight in sorted(weight_map.items(), key=lambda x: x[1], reverse=True):
            count = (df['market_regime'] == regime).sum()
            print(f"    {regime}: weight={weight}, rows={count:,}")
    else:
        print("⚠️ Warning: regime_weights.parquet not found, using weight=1 for all")
        df['training_weight'] = 1
    
    # Validate
    unique_regimes = df['market_regime'].nunique()
    weight_range = (df['training_weight'].min(), df['training_weight'].max())
    
    print(f"\n  ✅ Regime assignment complete:")
    print(f"     Unique regimes: {unique_regimes}")
    print(f"     Weight range: {weight_range[0]}-{weight_range[1]}")
    print(f"     Rows with regime: {df['market_regime'].notna().sum():,}/{len(df):,}")
    
    return df


def add_override_flags(df):
    """
    Add data quality and override flags.
    
    Features:
    - Data quality flags
    - Outlier flags
    - Missing data flags
    - Validation flags
    
    Args:
        df: DataFrame with feature columns
        
    Returns:
        df: DataFrame with override flag columns added
    """
    print("\n🚩 Adding override flags...")
    
    # Get price column
    price_col = None
    for col in ['close', 'zl_price_current', 'price']:
        if col in df.columns:
            price_col = col
            break
    
    # Missing data flags
    df['flag_missing_price'] = df[price_col].isna().astype(int) if price_col else 0
    
    # Count missing features
    feature_cols = [col for col in df.columns if any(col.startswith(prefix) for prefix in 
                    ['tech_', 'cross_', 'vol_', 'seas_', 'macro_', 'weather_'])]
    if feature_cols:
        df['flag_missing_features_count'] = df[feature_cols].isna().sum(axis=1)
        df['flag_missing_features_pct'] = df['flag_missing_features_count'] / len(feature_cols)
        df['flag_high_missing'] = (df['flag_missing_features_pct'] > 0.3).astype(int)
    
    # Outlier flags (using price data)
    if price_col:
        # Price outliers (beyond 3 standard deviations)
        price_mean = df[price_col].mean()
        price_std = df[price_col].std()
        df['flag_price_outlier'] = (
            (df[price_col] < price_mean - 3*price_std) | 
            (df[price_col] > price_mean + 3*price_std)
        ).astype(int)
        
        # Return outliers
        if 'tech_return_1d' in df.columns:
            df['flag_return_outlier'] = (df['tech_return_1d'].abs() > 0.1).astype(int)  # >10% daily move
        
        # Price jumps (for validation)
        price_pct_change = df[price_col].pct_change()
        df['flag_price_jump'] = (price_pct_change.abs() > 0.2).astype(int)  # >20% jump
    
    # Volume outliers (if available)
    if 'volume' in df.columns or 'zl_volume' in df.columns:
        vol_col = 'volume' if 'volume' in df.columns else 'zl_volume'
        vol_mean = df[vol_col].mean()
        vol_std = df[vol_col].std()
        df['flag_volume_outlier'] = (
            df[vol_col] > vol_mean + 3*vol_std
        ).astype(int)
        df['flag_low_volume'] = (df[vol_col] < df[vol_col].quantile(0.1)).astype(int)
    
    # Date-based flags
    df['flag_weekend'] = df['date'].dt.dayofweek.isin([5, 6]).astype(int)
    df['flag_month_end'] = df['date'].dt.is_month_end.astype(int)
    df['flag_quarter_end'] = df['date'].dt.is_quarter_end.astype(int)
    df['flag_year_end'] = ((df['date'].dt.month == 12) & (df['date'].dt.day >= 25)).astype(int)
    
    # Regime-based flags
    if 'market_regime' in df.columns:
        df['flag_rare_regime'] = df['market_regime'].isin(['structural_events']).astype(int)
        df['flag_high_weight'] = (df.get('training_weight', 1) > 1000).astype(int)
    
    # Data staleness flag (same price for multiple days)
    if price_col:
        df['flag_stale_price'] = (
            df[price_col] == df[price_col].shift(1)
        ).astype(int)
        
        # Extended staleness (3+ days)
        df['flag_extended_stale'] = (
            (df[price_col] == df[price_col].shift(1)) & 
            (df[price_col] == df[price_col].shift(2))
        ).astype(int)
    
    # Composite quality score
    flag_cols = [col for col in df.columns if col.startswith('flag_')]
    if flag_cols:
        # Exclude some benign flags from quality score
        quality_flags = [col for col in flag_cols if col not in 
                        ['flag_weekend', 'flag_month_end', 'flag_quarter_end']]
        df['flag_quality_score'] = df[quality_flags].sum(axis=1)
        df['flag_low_quality'] = (df['flag_quality_score'] >= 3).astype(int)
    
    print(f"  ✅ Added {len([c for c in df.columns if c.startswith('flag_')])} override flags")
    return df


# Main function to apply all features
def calculate_all_features(df):
    """
    Apply all feature engineering functions in sequence.
    
    Args:
        df: Input DataFrame
        
    Returns:
        df: DataFrame with all features added
    """
    print("\n" + "="*80)
    print("CALCULATING ALL FEATURES")
    print("="*80)
    
    initial_cols = len(df.columns)
    
    # Apply each feature function
    df = calculate_technical_indicators(df)
    df = calculate_cross_asset_features(df)
    df = calculate_volatility_features(df)
    df = calculate_seasonal_features(df)
    df = calculate_macro_regime_features(df)
    df = calculate_weather_aggregations(df)
    df = add_regime_columns(df)
    df = add_override_flags(df)
    
    final_cols = len(df.columns)
    
    print("\n" + "="*80)
    print(f"✅ FEATURE ENGINEERING COMPLETE")
    print(f"   Initial columns: {initial_cols}")
    print(f"   Final columns: {final_cols}")
    print(f"   Features added: {final_cols - initial_cols}")
    print("="*80)
    
    return df


if __name__ == "__main__":
    # Test with sample data
    print("Feature calculation functions ready for use")
    print("Import and use calculate_all_features() or individual functions")
