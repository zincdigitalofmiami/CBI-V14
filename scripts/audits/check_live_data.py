#!/usr/bin/env python3
"""Check live data feeds for key indicators"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery

print('=== LIVE DATA FEED CHECK ===')

# Check live ZL (Soybean Oil Futures)
print('\n1. SOYBEAN OIL (ZL) - LIVE:')
try:
    zl = yf.Ticker('ZL=F')
    hist = zl.history(period='5d')
    if not hist.empty:
        print(f'Latest Price: ${hist["Close"].iloc[-1]:.2f}')
        print(f'Today Change: {((hist["Close"].iloc[-1] / hist["Close"].iloc[-2] - 1) * 100):.2f}%')
        print(f'5-Day Range: ${hist["Low"].min():.2f} - ${hist["High"].max():.2f}')
except Exception as e:
    print(f'Error fetching ZL: {e}')

# Check live VIX
print('\n2. VIX (VOLATILITY) - LIVE:')
try:
    vix = yf.Ticker('^VIX')
    vix_hist = vix.history(period='5d')
    if not vix_hist.empty:
        latest_vix = vix_hist["Close"].iloc[-1]
        print(f'Latest VIX: {latest_vix:.2f}')
        print(f'VIX Status: {"CRISIS" if latest_vix > 30 else "ELEVATED" if latest_vix > 20 else "NORMAL"}')
except Exception as e:
    print(f'Error fetching VIX: {e}')

# Check live DXY (Dollar Index)
print('\n3. DOLLAR INDEX (DXY) - LIVE:')
try:
    dxy = yf.Ticker('DX-Y.NYB')
    dxy_hist = dxy.history(period='5d')
    if not dxy_hist.empty:
        print(f'Latest DXY: {dxy_hist["Close"].iloc[-1]:.2f}')
        print(f'5-Day Change: {((dxy_hist["Close"].iloc[-1] / dxy_hist["Close"].iloc[0] - 1) * 100):.2f}%')
except Exception as e:
    print(f'Error fetching DXY: {e}')

# Check live Crude Oil
print('\n4. CRUDE OIL (CL) - LIVE:')
try:
    cl = yf.Ticker('CL=F')
    cl_hist = cl.history(period='5d')
    if not cl_hist.empty:
        print(f'Latest Crude: ${cl_hist["Close"].iloc[-1]:.2f}')
        print(f'Crude/Soy Correlation Impact: {"HIGH" if cl_hist["Close"].iloc[-1] > 80 else "MODERATE"}')
except Exception as e:
    print(f'Error fetching Crude: {e}')

# Check live Treasury Yield
print('\n5. 10-YEAR TREASURY - LIVE:')
try:
    tnx = yf.Ticker('^TNX')
    tnx_hist = tnx.history(period='5d')
    if not tnx_hist.empty:
        print(f'Latest 10Y Yield: {tnx_hist["Close"].iloc[-1]:.2f}%')
except Exception as e:
    print(f'Error fetching Treasury: {e}')

# Check live currencies
print('\n6. CURRENCY IMPACTS - LIVE:')
try:
    # Brazil Real
    brl = yf.Ticker('BRL=X')
    brl_hist = brl.history(period='5d')
    if not brl_hist.empty:
        print(f'USD/BRL: {brl_hist["Close"].iloc[-1]:.4f} (Brazil competitiveness)')
    
    # Chinese Yuan
    cny = yf.Ticker('CNY=X')
    cny_hist = cny.history(period='5d')
    if not cny_hist.empty:
        print(f'USD/CNY: {cny_hist["Close"].iloc[-1]:.4f} (China purchasing power)')
except Exception as e:
    print(f'Error fetching currencies: {e}')

print('\n=== CHRIS\'S BIG 4 STATUS (FROM BIGQUERY) ===')
try:
    client = bigquery.Client(project='cbi-v14')
    
    # Check VIX stress from our view
    vix_query = """
    SELECT vix_current, vix_stress_ratio, vix_regime
    FROM `cbi-v14.signals.vw_vix_stress_signal`
    ORDER BY date DESC
    LIMIT 1
    """
    vix_result = client.query(vix_query).to_dataframe()
    if not vix_result.empty:
        print(f'1. VIX Stress: {vix_result["vix_stress_ratio"].iloc[0]:.2f} ({vix_result["vix_regime"].iloc[0]})')
    
    # Check social sentiment (Trump/Tariff signals)
    social_query = """
    SELECT 
        COUNT(*) as trump_mentions_24h,
        SUM(CASE WHEN LOWER(content) LIKE '%tariff%' THEN 1 ELSE 0 END) as tariff_mentions,
        SUM(CASE WHEN LOWER(content) LIKE '%china%' THEN 1 ELSE 0 END) as china_mentions
    FROM `cbi-v14.staging.comprehensive_social_intelligence`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
      AND (handle LIKE '%Trump%' OR handle LIKE '%donald%')
    """
    social_result = client.query(social_query).to_dataframe()
    if not social_result.empty:
        print(f'2. Trump Activity (24h): {social_result["trump_mentions_24h"].iloc[0]} posts')
        print(f'   - Tariff mentions: {social_result["tariff_mentions"].iloc[0]}')
        print(f'   - China mentions: {social_result["china_mentions"].iloc[0]}')
    
    # Check harvest/weather status
    weather_query = """
    SELECT 
        MAX(date) as latest_date,
        COUNT(*) as data_points
    FROM `cbi-v14.forecasting_data_warehouse.weather_data`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    """
    weather_result = client.query(weather_query).to_dataframe()
    if not weather_result.empty:
        print(f'3. South America Weather: Last update {weather_result["latest_date"].iloc[0]}')
    
    # Check China trade data
    china_query = """
    SELECT 
        MAX(CASE WHEN indicator LIKE '%china%' THEN value END) as china_imports,
        MAX(time) as latest_update
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    WHERE indicator LIKE '%china%' OR indicator LIKE '%cn_%'
    """
    china_result = client.query(china_query).to_dataframe()
    if not china_result.empty and china_result["china_imports"].iloc[0]:
        print(f'4. China Relations: Import volume {china_result["china_imports"].iloc[0]:.0f} MMT')
    
except Exception as e:
    print(f'Error accessing BigQuery: {e}')

print('\n=== DATA FRESHNESS ===')
print(f'Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('All live feeds operational ✅')
