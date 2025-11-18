#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBI-V14 - Alpha Vantage Comprehensive Data Collection
=====================================================

Master script for collecting a wide array of financial data from Alpha Vantage.
As per the FRESH_START_MASTER_PLAN, this script is responsible for:
- Fetching 50+ technical indicators for key futures contracts (ES=F, ZL=F).
- Collecting prices for major commodities, forex pairs, and US Treasuries.
- Handling API rate limits (75 calls/minute) with robust error handling.
- Saving all raw data into organized directories on the external drive.
"""
import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

import pandas as pd
import requests

# --- Setup Project Root ---
# Add parent directories to path to import keychain_manager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from src.utils.keychain_manager import get_api_key
except ImportError:
    print("Could not import keychain_manager. Ensure you are running from the project root.")
    sys.exit(1)

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('alpha_vantage_collection.log')
    ]
)
logger = logging.getLogger(__name__)

# --- API & Paths ---
try:
    API_KEY = get_api_key("ALPHA_VANTAGE_API_KEY")
    if not API_KEY:
        raise ValueError("API key is empty.")
    logger.info("✅ Successfully loaded Alpha Vantage API key from keychain.")
except Exception as e:
    logger.error(f"❌ Could not load Alpha Vantage API key from keychain: {e}")
    logger.error("Please store the key using: `security add-generic-password -a default -s cbi-v14.ALPHA_VANTAGE_API_KEY -w 'YOUR_KEY' -U`")
    sys.exit(1)

BASE_URL = "https://www.alphavantage.co/query"
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
OUTPUT_DIR = EXTERNAL_DRIVE / "TrainingData/raw/alpha_vantage"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API Rate Limit: 75 calls per minute (Premium Plan75)
# Conservative rate: 50 calls/minute to avoid overwhelming servers
# This gives us a 33% safety buffer
API_CALL_WAIT_SECONDS = 60 / 50  # 1.2 seconds between calls

# --- Data Definitions ---
SYMBOLS = {
    # ES Futures - collect directly (NO PROXY)
    'es_futures': ['ES=F'],  # S&P 500 E-mini futures
    # ALL commodities from Alpha Vantage
    'commodities': [
        'WTI', 'BRENT', 'NATURAL_GAS', 'COPPER', 'CORN', 'WHEAT', 
        'COTTON', 'SUGAR', 'COFFEE', 'ALUMINUM'
    ],
    # ALL symbols for technical indicators - collect indicators for EVERYTHING
    'all_symbols_for_technicals': [
        'ES=F',  # ES Futures (direct, no proxy)
        'USO',  # Oil ETF
        'UNG',  # Natural Gas ETF
        'CORN',  # Corn ETF
        'WEAT',  # Wheat ETF
        'SOYB',  # Soybeans ETF
        'DBA',  # Agriculture ETF
        'GLD',  # Gold ETF
        'SLV',  # Silver ETF
        'PALL',  # Palladium ETF
        'PPLT',  # Platinum ETF
    ],
    # ALL major forex pairs
    'forex': [
        'EURUSD', 'USDJPY', 'GBPUSD', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD',
        'EURJPY', 'EURGBP', 'EURAUD', 'EURCAD', 'GBPJPY', 'AUDJPY', 'CADJPY',
        'CHFJPY', 'AUDNZD', 'AUDCAD', 'NZDCAD', 'NZDJPY'
    ],
    # NO TREASURIES - we get those from FRED
    # ES futures intraday timeframes (all available)
    'es_intraday_timeframes': ['1min', '5min', '15min', '30min', '60min'],
    # Symbols for sentiment/analysis
    'sentiment_symbols': ['SPY', 'USO', 'UNG', 'CORN', 'WEAT', 'SOYB', 'DBA', 'GLD'],
    # Options chains (SOYB, CORN, WEAT, DBA, SPY)
    'options_symbols': ['SOYB', 'CORN', 'WEAT', 'DBA', 'SPY']
}

TECHNICAL_INDICATORS = [
    # Momentum Indicators
    "SMA", "EMA", "WMA", "DEMA", "TEMA", "TRIMA", "KAMA", "MAMA", "T3", "MACD",
    "MACDEXT", "STOCH", "STOCHF", "RSI", "STOCHRSI", "WILLR", "ADX", "ADXR",
    "APO", "PPO", "MOM", "BOP", "CCI", "CMO", "ROC", "ROCR", "AROON", "AROONOSC",
    "MFI", "TRIX", "ULTOSC", "DX", "MINUS_DI", "PLUS_DI", "MINUS_DM", "PLUS_DM",
    # Volatility Indicators
    "BBANDS", "TRANGE", "ATR", "NATR",
    # Volume Indicators
    "AD", "ADOSC", "OBV",
    # Cycle Indicators
    "HT_TRENDLINE", "HT_SINE", "HT_TRENDMODE", "HT_DCPERIOD", "HT_DCPHASE", "HT_PHASOR"
]

def make_api_call(params: Dict[str, Any], max_retries: int = 2) -> Optional[Dict[str, Any]]:
    """Makes a rate-limited API call to Alpha Vantage with error handling and retry logic."""
    params['apikey'] = API_KEY
    
    for attempt in range(max_retries + 1):
        time.sleep(API_CALL_WAIT_SECONDS)
        
        try:
            response = requests.get(BASE_URL, params=params, timeout=30)
            
            # Handle 500 errors with exponential backoff
            if response.status_code == 500:
                if attempt < max_retries:
                    wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                    logger.warning(f"Server error 500, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries + 1})...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"HTTP 500 after {max_retries + 1} attempts for {params.get('function')}/{params.get('symbol', '')}")
                    return None
            
            response.raise_for_status()
            data = response.json()
            
            if "Note" in data or "Information" in data:
                logger.warning(f"API call limit likely reached: {data}")
                time.sleep(60) # Wait a minute if we hit the limit
                response = requests.get(BASE_URL, params=params, timeout=30)
                data = response.json()
            if "Error Message" in data:
                logger.error(f"API Error for params {params.get('function')}/{params.get('symbol')}: {data['Error Message']}")
                return None
            return data
        except requests.exceptions.RequestException as e:
            if attempt < max_retries and "500" in str(e):
                wait_time = (2 ** attempt) * 5
                logger.warning(f"Request exception, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries + 1})...")
                time.sleep(wait_time)
                continue
            logger.error(f"HTTP Request failed for params {params.get('function')}: {e}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from response: {response.text[:200]}")
            return None
    
    return None

def fetch_technical_indicator(indicator: str, symbol: str) -> Optional[pd.DataFrame]:
    """Fetches a single technical indicator for a given symbol."""
    logger.info(f"Fetching {indicator} for {symbol}...")
    params = {
        'function': indicator,
        'symbol': symbol,
        'interval': 'daily',
        'time_period': '60', # Common default
        'series_type': 'close',
        'outputsize': 'full'
    }
    # Some indicators have different parameter names
    if indicator in ["STOCH", "STOCHF", "STOCHRSI"]:
        params.pop('time_period', None) # Uses fastkperiod etc.
    
    data = make_api_call(params)
    
    if not data:
        return None
    
    # Find the key containing the data (e.g., 'Technical Analysis: SMA')
    data_key = next((key for key in data if key.startswith('Technical Analysis:')), None)
    if not data_key:
        logger.warning(f"Could not find data key for {indicator} in response: {list(data.keys())}")
        return None

    df = pd.DataFrame.from_dict(data[data_key], orient='index', dtype=float)
    df.index.name = 'date'
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    
    # Add prefix to columns
    df = df.add_prefix(f'{indicator.lower()}_')
    return df

def collect_all_technicals_for_symbol(symbol: str):
    """Collects and merges all technical indicators for a single symbol."""
    output_path = OUTPUT_DIR / f"technicals_{symbol.replace('=F', '')}.parquet"
    
    # Skip if file already exists
    if output_path.exists():
        logger.info(f"⏭️  Skipping {symbol} - file already exists: {output_path.name}")
        return
    
    logger.info(f"--- Starting technical indicator collection for {symbol} ---")
    all_indicators_df = None
    
    for indicator in TECHNICAL_INDICATORS:
        indicator_df = fetch_technical_indicator(indicator, symbol)
        if indicator_df is not None and not indicator_df.empty:
            if all_indicators_df is None:
                all_indicators_df = indicator_df
            else:
                all_indicators_df = all_indicators_df.merge(indicator_df, on='date', how='outer')
    
    if all_indicators_df is not None and not all_indicators_df.empty:
        all_indicators_df.reset_index().to_parquet(output_path, index=False)
        logger.info(f"✅ Saved {len(all_indicators_df)} rows of technicals for {symbol} to {output_path}")
    else:
        logger.error(f"❌ No technical indicators were successfully collected for {symbol}")

def fetch_and_save_series(data_type: str, name: str, params: Dict[str, Any], data_key: str, value_col_name: str, output_prefix: str):
    """Generic function to fetch, process, and save a data series."""
    output_path = OUTPUT_DIR / f"{output_prefix}_{name.lower()}.parquet"
    
    # Skip if file already exists
    if output_path.exists():
        logger.info(f"⏭️  Skipping {data_type} {name} - file already exists: {output_path.name}")
        return
    
    logger.info(f"Fetching {data_type}: {name}...")
    
    # Ensure full history is requested where applicable
    if data_type in ['commodity', 'forex']:
        params['outputsize'] = 'full'

    data = make_api_call(params)
    if not data or 'data' not in data:
        logger.error(f"❌ No data returned for {name}.")
        return

    df = pd.DataFrame(data['data'])
    df['date'] = pd.to_datetime(df['date'])
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.dropna().sort_values('date').reset_index(drop=True)
    df = df.rename(columns={'value': value_col_name})

    if not df.empty:
        df.to_parquet(output_path, index=False)
        logger.info(f"✅ Saved {len(df)} rows for {name} to {output_path}")
    else:
        logger.warning(f"⚠️ No data processed for {name}.")

def fetch_forex_full_history(pair: str):
    """Fetch full forex history using multiple endpoints to bypass 5,000 row limit."""
    output_path = OUTPUT_DIR / f"forex_{pair.lower()}.parquet"
    
    # Skip if file already exists
    if output_path.exists():
        logger.info(f"⏭️  Skipping forex {pair} - file already exists: {output_path.name}")
        return
    
    logger.info(f"Fetching FULL history for {pair}...")
    from_symbol = pair[:3]
    to_symbol = pair[3:]
    
    all_data = []
    
    # Try FX_MONTHLY first for longest history
    params = {'function': 'FX_MONTHLY', 'from_symbol': from_symbol, 'to_symbol': to_symbol}
    data = make_api_call(params)
    if data and 'Time Series FX (Monthly)' in data:
        df_monthly = pd.DataFrame.from_dict(data['Time Series FX (Monthly)'], orient='index')
        df_monthly.index = pd.to_datetime(df_monthly.index)
        all_data.append(df_monthly)
        logger.info(f"  Got {len(df_monthly)} monthly rows")
    
    # Then FX_WEEKLY for more granularity
    params = {'function': 'FX_WEEKLY', 'from_symbol': from_symbol, 'to_symbol': to_symbol}
    data = make_api_call(params)
    if data and 'Time Series FX (Weekly)' in data:
        df_weekly = pd.DataFrame.from_dict(data['Time Series FX (Weekly)'], orient='index')
        df_weekly.index = pd.to_datetime(df_weekly.index)
        all_data.append(df_weekly)
        logger.info(f"  Got {len(df_weekly)} weekly rows")
    
    # Finally FX_DAILY for recent data
    params = {'function': 'FX_DAILY', 'from_symbol': from_symbol, 'to_symbol': to_symbol, 'outputsize': 'full'}
    data = make_api_call(params)
    if data and 'Time Series FX (Daily)' in data:
        df_daily = pd.DataFrame.from_dict(data['Time Series FX (Daily)'], orient='index')
        df_daily.index = pd.to_datetime(df_daily.index)
        all_data.append(df_daily)
        logger.info(f"  Got {len(df_daily)} daily rows")
    
    if all_data:
        # Combine and deduplicate
        combined = pd.concat(all_data)
        combined = combined[~combined.index.duplicated(keep='first')]
        combined = combined.sort_index()
        combined.index.name = 'date'
        combined = combined.apply(pd.to_numeric, errors='coerce')
        combined = combined.rename(columns=lambda x: x.split('. ')[1] if '. ' in x else x)
        combined['symbol'] = pair
        
        combined.reset_index().to_parquet(output_path, index=False)
        logger.info(f"✅ Saved {len(combined)} total rows for {pair} to {output_path}")
    else:
        logger.error(f"❌ No data collected for {pair}")

def fetch_es_daily():
    """Fetch ES futures daily data with full 25-year history from Alpha Vantage."""
    output_path = OUTPUT_DIR / "es_daily.parquet"
    
    # Skip if file already exists
    if output_path.exists():
        logger.info(f"⏭️  Skipping ES daily - file already exists: {output_path.name}")
        return None
    
    logger.info("Fetching ES futures daily data (full history) from Alpha Vantage...")
    
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': 'ES=F',
        'outputsize': 'full',  # Get full history (25+ years)
    }
    
    data = make_api_call(params)
    if data and 'Time Series (Daily)' in data:
        df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
        df.index.name = 'date'
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        df = df.apply(pd.to_numeric, errors='coerce')
        df = df.rename(columns=lambda x: x.split('. ')[1] if '. ' in x else x)
        df['symbol'] = 'ES=F'
        df = df.reset_index()
        
        df.to_parquet(output_path, index=False)
        logger.info(f"✅ Saved {len(df)} rows of ES daily data ({df['date'].min()} to {df['date'].max()}) to {output_path}")
        return df
    else:
        logger.warning("⚠️ ES=F not available from Alpha Vantage - will use Yahoo Finance fallback")
        return None

def fetch_es_intraday(timeframe: str):
    """Fetch ES futures intraday data directly (NO PROXY)."""
    output_path = OUTPUT_DIR / f"es_intraday_{timeframe}.parquet"
    
    # Skip if file already exists
    if output_path.exists():
        logger.info(f"⏭️  Skipping ES intraday {timeframe} - file already exists: {output_path.name}")
        return
    
    logger.info(f"Fetching ES intraday data ({timeframe}) directly from Alpha Vantage...")
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': 'ES=F',
        'interval': timeframe,
        'outputsize': 'full',
        'extended_hours': 'false'
    }
    data = make_api_call(params)
    if data and f'Time Series ({timeframe})' in data:
        df = pd.DataFrame.from_dict(data[f'Time Series ({timeframe})'], orient='index')
        df.index.name = 'datetime'
        df.index = pd.to_datetime(df.index)
        df = df.apply(pd.to_numeric, errors='coerce')
        df = df.rename(columns=lambda x: x.split('. ')[1] if '. ' in x else x)
        df['symbol'] = 'ES=F'
        df['timeframe'] = timeframe
        
        df.reset_index().to_parquet(output_path, index=False)
        logger.info(f"✅ Saved {len(df)} rows for ES {timeframe} to {output_path}")
    else:
        logger.warning(f"⚠️ ES intraday not available from Alpha Vantage for {timeframe} - will use Yahoo Finance fallback")

# ============================================================================
# INSTITUTIONAL-GRADE ZL (SOYBEAN OIL) KEYWORD MATRIX
# Master scraping topic → keyword intelligence for Hidden Relationship Module
# 40 Categories, 450+ keywords covering direct drivers, indirect drivers, drivers-of-drivers
# ============================================================================

ZL_KEYWORD_MATRIX = {
    # Category 1: Biofuel Mandates / SAF / LCFS (ZL ↑ strong)
    'biofuel_mandates': {
        'effect': 'ZL_UP',
        'primary': [
            'renewable fuel standard', 'rfs volumes', 'saf credit', 'saf tax credit',
            'lcfs', 'low carbon fuel standard', 'biofuel mandate', 'biodiesel blend',
            'b20', 'b40', 'b35', 'blend requirements', 'feedstock shortage',
            'biodiesel producers', 'renewable diesel capacity'
        ],
        'agencies': ['epa', 'doe', 'carb', 'anp brazil'],
        'triggers': ['proposed rule', 'final rule', 'pre-rule docket', 'expanded credit', 'retroactive volumes']
    },
    
    # Category 2: Indonesia/Malaysia Palm Policy (Palm ↑ → ZL ↑)
    'palm_policy': {
        'effect': 'ZL_UP',
        'primary': [
            'cpo export levy', 'palm oil export tax', 'indonesia export ban', 'mpob',
            'dmo', 'malaysia supply', 'el nino dry estates', 'india edible oil duty',
            'import duty cut', 'export quota'
        ],
        'triggers': ['port congestion', 'labor shortage', 'estate yield down', 'harvest disruption']
    },
    
    # Category 3: China Agricultural Demand / State Reserves / FX Strategy
    'china_demand': {
        'effect': 'ZL_MIXED',
        'primary': [
            'sinograin', 'cofco', 'ndrc soybean', 'state reserves', 'soybean auctions',
            'strategic stockpile', 'soybean crush margins china', 'dalian soy oil',
            'dce futures', 'cny devaluation', 'fx intervention', 'yuan liquidity'
        ],
        'triggers': ['food security directive', 'import suspension', 'port delays', 'customs inspections', 'african swine fever']
    },
    
    # Category 4: Trump / U.S. Policy / Tariffs / Argentina Backchannel
    'us_policy_tariffs': {
        'effect': 'ZL_STRUCTURAL',
        'primary': [
            'tariff threat', '301 investigation', 'trade retaliation', 'export license suspension',
            'sanction exemption', 'argentina cooperation', 'imf debt restructuring',
            'security cooperation argentina', 'food corridor agreement', 'trump tariff review',
            'farm belt support', 'agricultural exception'
        ],
        'triggers': ['national security review', 'executive order', 'trade enforcement action']
    },
    
    # Category 5: Brazil & Argentina Crop + Logistics (Major supply driver)
    'south_america_crop_logistics': {
        'effect': 'ZL_MAJOR',
        'primary': [
            'conab', 'mapa brazil', 'soybean harvest brazil', 'yield reduction',
            'mato grosso dryness', 'rio grande port strike', 'rosario strike',
            'up river port', 'barge delays', 'br-163 shutdown', 'export license delay',
            'truck blockade', 'sojadólar'
        ],
        'triggers': ['drought monitoring', 'la niña', 'el niño', 'pesticide limits', 'planting delays']
    },
    
    # Category 6: Weather (US/Brazil/Argentina) - Agronomically Relevant Only
    'weather_agronomic': {
        'effect': 'ZL_UP',
        'primary': [
            'soybean moisture stress', 'crop moisture index', 'soil deficit', 'heat dome',
            'frost risk', 'hail damage', 'gfs rainfall', 'inmet brazil alerts',
            'smn argentina weather', 'midwest heatwave', 'mississippi low water'
        ],
        'triggers': ['flash drought', 'crop stress', 'yield loss models']
    },
    
    # Category 7: Biofuel Lobbying Chain (predictive, 60-120 day lead)
    'biofuel_lobbying': {
        'effect': 'ZL_UP',
        'primary': [
            'biofuel lobby', 'renewable diesel lobbying', 'pac donation biofuel',
            'epa hearing biofuel', 'saf testimonies', 'refiner meeting epa',
            'industry working group'
        ],
        'triggers': ['proposed credit', 'industry petition', 'lobby disclosure filing']
    },
    
    # Category 8: Sovereign Wealth Funds (3-6 month lead)
    'sovereign_wealth': {
        'effect': 'ZL_UP',
        'primary': [
            'sovereign wealth investment', 'stake acquisition', 'agribusiness acquisition',
            'port infrastructure investment', 'logistics asset purchase', 'soy processing m&a'
        ],
        'triggers': ['5% stake', 'strategic equity', 'long-term supply agreement']
    },
    
    # Category 9: Carbon Market Arbitrage / EU Deforestation Law (EUDR)
    'carbon_eudr': {
        'effect': 'ZL_ORIGIN_SWITCH',
        'primary': [
            'carbon accounting', 'eu eudr enforcement', 'carbon credit arbitrage',
            'cbio', 'renovabio', 'lcfs credit price', 'deforestation compliance',
            'traceability regulation', 'import restriction'
        ],
        'triggers': ['carbon price spike', 'traceability requirement deadline']
    },
    
    # Category 10: Shipping, Chokepoints, War Risk Insurance
    'shipping_chokepoints': {
        'effect': 'ZL_UP',
        'primary': [
            'red sea attacks', 'suez disruption', 'panama canal drought', 'port insurance',
            'marine war risk premium', 'bab el-mandeb', 'strait of malacca congestion',
            'black sea grain corridor'
        ],
        'triggers': ['ships diverted', 'draft restrictions', 'slot reduction']
    },
    
    # Category 11: Defense-Agriculture Nexus
    'defense_agriculture': {
        'effect': 'ZL_HIDDEN',
        'primary': [
            'fms sale', 'security guarantee', 'naval escort announcement',
            'u.s. indo-pacific defense pact', 'military aid package agriculture linkage',
            'dual-use corridor'
        ],
        'triggers': ['joint training', 'security memorandum', 'defense procurement india', 'defense procurement indonesia']
    },
    
    # Category 12: Pharmaceutical Licensing → Agricultural Reciprocity
    'pharma_agriculture': {
        'effect': 'ZL_UP',
        'primary': [
            'patent extension', 'pharmaceutical licensing', 'accelerated approval',
            'bilateral medical cooperation', 'vaccine distribution agreement'
        ],
        'triggers': ['license granted', 'patent settlement', 'drug approval meeting']
    },
    
    # Category 13: CBDC + Trade Settlement Channels
    'cbdc_settlement': {
        'effect': 'ZL_CURRENCY',
        'primary': [
            'digital yuan', 'cbdc corridor', 'blockchain settlement bilateral',
            'brl-cny settlement', 'de-dollarization agriculture', 'currency swap agreement'
        ],
        'triggers': ['digital settlement pilot', 'pilot expansion', 'direct currency clearing']
    },
    
    # Category 14: Port Construction & Dredging Projects (6-12 month lead)
    'port_infrastructure': {
        'effect': 'ZL_UP',
        'primary': [
            'deep water port dredging', 'port expansion contract', 'loading equipment procurement',
            'grain terminal upgrade', 'secondary port modernization', 'dry bulk terminal construction'
        ],
        'triggers': ['dredging approval', 'equipment tender', 'capacity upgrade']
    },
    
    # Category 15: Academic / Ag University Cooperation
    'academic_cooperation': {
        'effect': 'ZL_SOFT_DIPLOMACY',
        'primary': [
            'agricultural mou', 'university exchange program', 'crop science partnership',
            'joint research grant', 'agricultural technical assistance'
        ],
        'triggers': ['memorandum signing', 'grant allocation', 'research partnership expansion']
    },
    
    # Category 16: U.S. Farm Bill / Commodity Programs
    'farm_bill': {
        'effect': 'ZL_MIXED',
        'primary': [
            'farm bill negotiations', 'commodity credit corporation', 'crop insurance subsidy',
            'soybean reference price', 'loan rate adjustment', 'bioenergy program funding'
        ],
        'triggers': ['mark-up session', 'budget resolution', 'conference committee']
    },
    
    # Category 17: Crush Margins & Processing Capacity
    'crush_margins': {
        'effect': 'ZL_UP',
        'primary': [
            'crush margin expansion', 'capacity utilization', 'soy processing expansion',
            'oil yield decline', 'crush plant outages', 'refinery conversion rd capacity'
        ],
        'triggers': ['maintenance shutdown', 'capacity expansion approval']
    },
    
    # Category 18: Global FX Shifts (BRL, ARS, CNY)
    'fx_shifts': {
        'effect': 'ZL_ORIGIN_SWITCH',
        'primary': [
            'brl weakness', 'real depreciation', 'peso collapse', 'fx intervention china',
            'soydollar policy'
        ],
        'triggers': ['fx swap activation', 'intervention round', 'fx corridor opened']
    },
    
    # Category 19: Food Security Policies
    'food_security': {
        'effect': 'ZL_UP',
        'primary': [
            'food emergency', 'reserve release', 'food security bill',
            'grain reserve program', 'import mandate'
        ],
        'triggers': ['government directs state buyers to replenish reserves']
    },
    
    # Category 20: Shipping Freight Rates
    'shipping_freight': {
        'effect': 'ZL_UP',
        'primary': [
            'dry bulk rate surge', 'asia-brazil freight', 'container crunch',
            'baltic dry index', 'mr tankers'
        ],
        'triggers': ['rate surge', 'charter premium', 'tonnage shortage']
    },
    
    # Category 21: Fertilizer & Energy Input Shocks
    'fertilizer_energy': {
        'effect': 'ZL_UP',
        'primary': [
            'nitrogen shortage', 'potash sanctions', 'ammonia plant outage',
            'urea tender disruption', 'energy price spike', 'natgas supply cut'
        ],
        'triggers': ['sanction risk', 'export restriction', 'plant accident']
    },
    
    # Category 22: U.S.-China Strategic Tensions
    'us_china_tensions': {
        'effect': 'ZL_MIXED',
        'primary': [
            'naval confrontation', 'spy balloon', 'sanctions list expansion',
            'export restrictions', 'taiwan strait drills'
        ],
        'triggers': ['joint military exercise', 'sanction announcement']
    },
    
    # Category 23: GMO / Agrochemical Policy
    'gmo_agrochemical': {
        'effect': 'ZL_MIXED',
        'primary': [
            'glyphosate ban', 'agrochemical approval delay', 'trait approval china',
            'ctnbio decision', 'pesticide restriction', 'herbicide program change'
        ],
        'triggers': ['ban proposal', 'trait approval', 'residue limit tightening']
    },
    
    # Category 24: Black Sea / War Spillovers
    'black_sea_war': {
        'effect': 'ZL_UP',
        'primary': [
            'odessa attack', 'danube corridor', 'sunflower oil export ban',
            'grain corridor', 'marine insurance suspension'
        ],
        'triggers': ['port hit', 'export ban', 'shipping suspension']
    },
    
    # Category 25: Labor Strikes (Ports, Trucks, Barge Lines)
    'labor_strikes': {
        'effect': 'ZL_UP',
        'primary': [
            'port strike', 'dockworker strike', 'rosario union', 'ilwu negotiations',
            'truck blockade'
        ],
        'triggers': ['strike notice', 'collective bargaining breakdown']
    },
    
    # Category 26: South American Trucking / Logistics
    'south_america_logistics': {
        'effect': 'ZL_CRITICAL',
        'primary': [
            'br-163 congestion', 'amazon corridor', 'soybean highway',
            'inland freight spike'
        ]
    },
    
    # Category 27: Refinery & RD Capacity Expansions (U.S. Gulf Coast)
    'refinery_rd_capacity': {
        'effect': 'ZL_UP',
        'primary': [
            'renewable diesel plant', 'hydrotreater conversion', 'refinery retrofit',
            'saf plant approval'
        ]
    },
    
    # Category 28: Tanker Availability / Clean Tanker Dynamics
    'tanker_dynamics': {
        'effect': 'ZL_COMPETITION',
        'primary': [
            'clean tanker index', 'mr tanker rates asia', 'charter rates vegoil'
        ]
    },
    
    # Category 29: Inflation, Rates, Macro Liquidity
    'macro_liquidity': {
        'effect': 'ZL_UP',
        'primary': [
            'fed rate cut', 'inflation spike', 'qe expectations', 'commodity hedge flows'
        ]
    },
    
    # Category 30: Spec Positioning (CFTC)
    'spec_positioning': {
        'effect': 'ZL_FLOWS',
        'primary': [
            'managed money net long', 'speculators reduce longs', 'cot report changes'
        ]
    },
    
    # Category 31: Risk-Off / VIX Surges
    'risk_off_vix': {
        'effect': 'ZL_DOWN',
        'primary': [
            'vix spike', 'market turmoil', 'equity selloff', 'risk aversion'
        ]
    },
    
    # Category 32: Shipping Insurance / Reinsurance
    'shipping_insurance': {
        'effect': 'ZL_UP',
        'primary': [
            'reinsurance withdrawal', 'portfolio exclusion', 'non-compliance carriers'
        ]
    },
    
    # Category 33: Port Throughput Indicators
    'port_throughput': {
        'effect': 'ZL_PREDICTIVE',
        'primary': [
            'container throughput', 'dry bulk loading', 'berth congestion', 'crane outage'
        ]
    },
    
    # Category 34: Chinese Local Government Financing Vehicles (LGFVs)
    'lgfv_debt': {
        'effect': 'ZL_DOWN',
        'primary': [
            'lgfv debt', 'provincial liquidity', 'bond rollover crisis'
        ]
    },
    
    # Category 35: Soybean Disease / Pests
    'soybean_disease': {
        'effect': 'ZL_UP',
        'primary': [
            'soybean rust', 'white mold', 'fungicide resistance', 'crop disease report'
        ]
    },
    
    # Category 36: Energy Markets (Crude, Diesel)
    'energy_markets': {
        'effect': 'ZL_CORRELATION',
        'primary': [
            'diesel shortage', 'crude rally', 'refinery outage', 'diesel crack spread'
        ]
    },
    
    # Category 37: Infrastructure Failures / Industrial Accidents
    'infrastructure_failures': {
        'effect': 'ZL_UP',
        'primary': [
            'grain silo collapse', 'port fire', 'pipeline rupture', 'processing plant explosion'
        ]
    },
    
    # Category 38: Bank Lending / Credit Crunch
    'credit_crunch': {
        'effect': 'ZL_DOWN',
        'primary': [
            'credit tightening', 'ag loan defaults', 'commercial credit freeze'
        ]
    },
    
    # Category 39: Elections / Political Instability
    'elections_politics': {
        'effect': 'ZL_POLICY_SHIFT',
        'primary': [
            'runoff election', 'new agriculture minister', 'policy overhaul', 'nationalization risk'
        ]
    },
    
    # Category 40: Digital Trade, Blockchain, Supply Chain Traceability
    'digital_traceability': {
        'effect': 'ZL_COMPLIANCE',
        'primary': [
            'blockchain traceability', 'digital supply chain', 'eudr compliance tech',
            'ag tracking platform'
        ]
    }
}

def filter_zl_relevant_articles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter news articles using institutional-grade ZL (soybean oil) keyword matrix.
    
    Uses 40 categories covering:
    - Direct drivers (biofuel, palm policy, crop logistics)
    - Indirect drivers (FX, shipping, weather)
    - Drivers-of-drivers (defense-agriculture nexus, pharma reciprocity, CBDC)
    
    Designed for Hidden Relationship Intelligence Module and Big 7/Big 14 signal expansion.
    """
    if df.empty:
        return df
    
    # Build comprehensive keyword list from all categories
    all_keywords = []
    all_triggers = []
    all_agencies = []
    
    for category, data in ZL_KEYWORD_MATRIX.items():
        all_keywords.extend(data.get('primary', []))
        all_triggers.extend(data.get('triggers', []))
        all_agencies.extend(data.get('agencies', []))
    
    # Keywords that indicate IRRELEVANCE (case-insensitive)
    irrelevant_keywords = [
        # Tech (unless about commodity trading platforms or blockchain traceability)
        'tech startup', 'venture capital', 'crypto', 'bitcoin', 'blockchain nft',
        'metaverse', 'gaming', 'streaming', 'ai software',
        
        # Entertainment/Sports
        'movie', 'film', 'tv', 'television', 'sports', 'football', 'basketball',
        'entertainment', 'celebrity', 'music',
        
        # Unrelated financial (unless commodity-related)
        'ipo', 'merger', 'acquisition', 'earnings', 'stock split',
        'dividend', 'corporate', 'company', 'business',
        
        # ES/MES specific (unless it's about correlations/VIX)
        's&p 500', 'sp500', 'spy', 'es futures', 'mes futures',
        'equity', 'stock market', 'nasdaq', 'dow jones'
    ]
    
    def is_relevant(row):
        """Check if article is relevant to ZL prediction using institutional matrix."""
        # Combine title, summary, and topics into searchable text
        search_text = ' '.join([
            str(row.get('title', '')),
            str(row.get('summary', '')),
            str(row.get('topics', ''))
        ]).lower()
        
        # Check for irrelevant keywords first (stronger filter)
        for keyword in irrelevant_keywords:
            if keyword in search_text:
                # Exception: Keep if it's explicitly about commodity-related topics
                commodity_context = any(rel in search_text for rel in [
                    'commodity', 'futures', 'agricultural', 'soybean', 'palm oil',
                    'edible oil', 'vegetable oil', 'crude oil', 'biofuel', 'renewable diesel',
                    'blockchain traceability', 'digital supply chain', 'vix', 'volatility'
                ])
                if not commodity_context:
                    return False
        
        # Check for matches in institutional keyword matrix
        # Primary keywords (strong match)
        for keyword in all_keywords:
            if keyword in search_text:
                return True
        
        # Trigger phrases (very strong match - predictive signals)
        for trigger in all_triggers:
            if trigger in search_text:
                return True
        
        # Agency names (regulatory/policy context)
        for agency in all_agencies:
            if agency in search_text:
                return True
        
        # If no matches found, filter out
        return False
    
    # Apply filter
    mask = df.apply(is_relevant, axis=1)
    filtered_df = df[mask].copy()
    
    if len(filtered_df) < len(df):
        logger.info(f"  Filtered {len(df) - len(filtered_df)} irrelevant articles, kept {len(filtered_df)} ZL-relevant articles (institutional matrix)")
    
    return filtered_df

def fetch_news_sentiment(symbol: str = None, topics: str = None, time_from: str = None, time_to: str = None, filter_zl_relevant: bool = True):
    """Fetch news sentiment and analysis, filtered for ZL (soybean oil) relevance.
    
    PRIMARY FOCUS: ZL (soybean oil) prediction
    SECONDARY: Cross-asset correlations (crude oil, VIX) for regime detection
    FILTERED OUT: General tech, entertainment, ES/MES-specific news
    
    Args:
        symbol: Optional ticker symbol (e.g., 'SPY' - only if needed for correlations)
        topics: Optional comma-separated topics (e.g., 'economy_macro')
        time_from: Optional start time in YYYYMMDDTHHMM format
        time_to: Optional end time in YYYYMMDDTHHMM format
        filter_zl_relevant: If True, filter articles to only ZL-relevant content
    
    Supported topics: economy_macro, economy_monetary (affect commodity prices)
    """
    from datetime import datetime, timedelta
    
    # Default to last 7 days if no time range specified
    if time_to is None:
        time_to = datetime.now()
    if time_from is None:
        time_from = time_to - timedelta(days=7)
    
    if isinstance(time_to, datetime):
        time_to = time_to.strftime("%Y%m%dT%H%M")
    if isinstance(time_from, datetime):
        time_from = time_from.strftime("%Y%m%dT%H%M")
    
    if symbol:
        logger.info(f"Fetching news sentiment for {symbol} (for ZL correlations)...")
    elif topics:
        logger.info(f"Fetching news sentiment for topics: {topics} (ZL-focused)...")
    else:
        logger.info("Fetching general news sentiment (ZL-focused)...")
    
    params = {
        'function': 'NEWS_SENTIMENT',
        'limit': 50  # Conservative limit for testing
    }
    
    # Add parameters based on what's provided
    if symbol:
        params['tickers'] = symbol
    if topics:
        params['topics'] = topics
    if time_from:
        params['time_from'] = time_from
    if time_to:
        params['time_to'] = time_to
    
    data = make_api_call(params)
    if data and 'feed' in data:
        articles = data['feed']
        
        if articles:
            df = pd.DataFrame(articles)
            # Convert time_published to datetime
            if 'time_published' in df.columns:
                df['time_published'] = pd.to_datetime(df['time_published'], format='%Y%m%dT%H%M%S', errors='coerce')
                df = df.sort_values('time_published')
            
            # Filter for ZL-relevance
            if filter_zl_relevant:
                df = filter_zl_relevant_articles(df)
            
            if df.empty:
                logger.warning(f"⚠️ No ZL-relevant articles found after filtering")
                return None
            
            # Determine output filename
            if symbol:
                output_path = OUTPUT_DIR / f"news_sentiment_{symbol.lower()}_zl_filtered.parquet"
            elif topics:
                # Use first topic for filename
                topic_name = topics.split(',')[0].replace('_', '_')
                output_path = OUTPUT_DIR / f"news_sentiment_{topic_name}_zl_filtered.parquet"
            else:
                output_path = OUTPUT_DIR / f"news_sentiment_general_zl_filtered.parquet"
            
            df.to_parquet(output_path, index=False)
            logger.info(f"✅ Saved {len(df)} ZL-relevant sentiment articles to {output_path}")
            return df
    else:
        if symbol:
            logger.warning(f"⚠️ No sentiment data for {symbol}")
        elif topics:
            logger.warning(f"⚠️ No sentiment data for topics: {topics}")
        else:
            logger.warning(f"⚠️ No sentiment data available")
    return None

def fetch_earnings(symbol: str):
    """Fetch earnings data and analysis."""
    logger.info(f"Fetching earnings data for {symbol}...")
    params = {
        'function': 'EARNINGS',
        'symbol': symbol
    }
    data = make_api_call(params)
    if data and 'quarterlyEarnings' in data:
        earnings = []
        for item in data['quarterlyEarnings']:
            earnings.append({
                'symbol': symbol,
                'fiscal_date': pd.to_datetime(item.get('fiscalDateEnding', '')),
                'reported_date': pd.to_datetime(item.get('reportedDate', '')),
                'reported_eps': item.get('reportedEPS', None),
                'estimated_eps': item.get('estimatedEPS', None),
                'surprise': item.get('surprise', None),
                'surprise_percentage': item.get('surprisePercentage', None)
            })
        
        if earnings:
            df = pd.DataFrame(earnings)
            df = df.sort_values('fiscal_date')
            output_path = OUTPUT_DIR / f"earnings_{symbol.lower()}.parquet"
            df.to_parquet(output_path, index=False)
            logger.info(f"✅ Saved {len(df)} earnings records for {symbol} to {output_path}")
    else:
        logger.warning(f"⚠️ No earnings data for {symbol}")

def fetch_options_chain(symbol: str):
    """Fetch options chain data for a symbol."""
    logger.info(f"Fetching options chain for {symbol}...")
    
    # Alpha Vantage doesn't have a standard options API, but we can try:
    # 1. Try OPTIONS_CHAIN function (if available in premium)
    # 2. Try REALTIME_OPTIONS function
    # 3. Fallback: Use options data from other sources if available
    
    params_list = [
        {
            'function': 'OPTIONS_CHAIN',
            'symbol': symbol
        },
        {
            'function': 'REALTIME_OPTIONS',
            'symbol': symbol
        }
    ]
    
    for params in params_list:
        data = make_api_call(params)
        if data and ('options' in data or 'chain' in data or 'calls' in data or 'puts' in data):
            # Parse options data
            options_data = []
            
            # Handle different response formats
            if 'options' in data:
                options = data['options']
            elif 'chain' in data:
                options = data['chain']
            elif 'calls' in data or 'puts' in data:
                # Combine calls and puts
                calls = data.get('calls', [])
                puts = data.get('puts', [])
                options = calls + puts
            else:
                continue
            
            for option in options:
                option_data = {
                    'symbol': symbol,
                    'contract_symbol': option.get('contractSymbol', ''),
                    'strike': option.get('strike', None),
                    'expiration': pd.to_datetime(option.get('expirationDate', '')) if option.get('expirationDate') else None,
                    'option_type': option.get('optionType', 'call'),
                    'last_price': option.get('lastPrice', None),
                    'bid': option.get('bid', None),
                    'ask': option.get('ask', None),
                    'volume': option.get('volume', 0),
                    'open_interest': option.get('openInterest', 0),
                    'implied_volatility': option.get('impliedVolatility', None),
                    'delta': option.get('delta', None),
                    'gamma': option.get('gamma', None),
                    'theta': option.get('theta', None),
                    'vega': option.get('vega', None),
                    'date': datetime.now().date()
                }
                options_data.append(option_data)
            
            if options_data:
                df = pd.DataFrame(options_data)
                output_path = OUTPUT_DIR / f"options_{symbol.lower()}.parquet"
                df.to_parquet(output_path, index=False)
                logger.info(f"✅ Saved {len(df)} options contracts for {symbol} to {output_path}")
                return df
            
        elif data and 'Error Message' in data:
            logger.debug(f"Options API not available for {symbol}: {data.get('Error Message')}")
        elif data and ('Note' in data or 'Information' in data):
            logger.debug(f"Options API limit or not available: {data}")
    
    logger.warning(f"⚠️ No options data available for {symbol} (may require premium tier or not supported)")
    return None

def fetch_company_overview(symbol: str):
    """Fetch company fundamental overview."""
    logger.info(f"Fetching company overview for {symbol}...")
    params = {
        'function': 'OVERVIEW',
        'symbol': symbol
    }
    data = make_api_call(params)
    if data and 'Symbol' in data:
        # Save as JSON since it's a single record with many fields
        import json
        output_path = OUTPUT_DIR / f"overview_{symbol.lower()}.json"
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"✅ Saved company overview for {symbol} to {output_path}")
    else:
        logger.warning(f"⚠️ No overview data for {symbol}")

def main():
    """Main execution function - COLLECT EVERYTHING."""
    logger.info("="*80)
    logger.info("Alpha Vantage COMPREHENSIVE Collection - ALL DATA")
    logger.info("="*80)
    
    successful_collections = []
    failed_collections = []

    # --- Collect ES Futures Daily Data (25 years) ---
    logger.info("\n--- Collecting ES Futures Daily Data (Full 25-Year History) ---")
    try:
        es_daily = fetch_es_daily()
        if es_daily is not None and not es_daily.empty:
            successful_collections.append("es_daily")
        else:
            logger.info("  ES daily not available from Alpha Vantage - run collect_es_yahoo_fallback.py for Yahoo Finance")
            failed_collections.append("es_daily")
    except Exception as e:
        logger.error(f"  Failed to collect ES daily data: {e}")
        failed_collections.append("es_daily")

    # --- Collect ALL Technical Indicators for ALL Symbols (including ES=F) ---
    logger.info("\n--- Collecting ALL Technical Indicators for ALL Symbols ---")
    logger.info("  (Pausing 5 seconds before starting large batch...)")
    time.sleep(5)  # Pause before large batch
    for symbol in SYMBOLS['all_symbols_for_technicals']:
        logger.info(f"\n=== Collecting technicals for {symbol} ===")
        try:
            collect_all_technicals_for_symbol(symbol)
            # This function saves its own file, we'll assume success if no exception
            successful_collections.append(f"technicals_{symbol}")
        except Exception as e:
            logger.error(f"  Failed to collect technicals for {symbol}: {e}")
            failed_collections.append(f"technicals_{symbol}")
            
    # --- Collect ALL Commodities ---
    logger.info("\n--- Collecting ALL Commodities ---")
    logger.info("  (Pausing 5 seconds before starting batch...)")
    time.sleep(5)  # Pause before batch
    for commodity in SYMBOLS['commodities']:
        try:
            fetch_and_save_series(
                data_type='commodity',
                name=commodity,
                params={'function': commodity, 'interval': 'daily'},
                data_key='data',
                value_col_name=f'price_{commodity.lower()}',
                output_prefix='commodity'
            )
            successful_collections.append(f"commodity_{commodity.lower()}")
        except Exception as e:
            logger.error(f"  Failed to collect commodity {commodity}: {e}")
            failed_collections.append(f"commodity_{commodity.lower()}")

    # --- Collect ALL Forex Pairs with FULL History ---
    logger.info("\n--- Collecting ALL Forex Pairs (Full History) ---")
    logger.info("  (Pausing 5 seconds before starting batch...)")
    time.sleep(5)  # Pause before batch
    for pair in SYMBOLS['forex']:
        try:
            fetch_forex_full_history(pair)
            successful_collections.append(f"forex_{pair.lower()}")
        except Exception as e:
            logger.error(f"  Failed to collect forex pair {pair}: {e}")
            failed_collections.append(f"forex_{pair.lower()}")

    # --- Collect ES Futures Intraday (All Timeframes) ---
    logger.info("\n--- Collecting ES Futures Intraday (All Timeframes) ---")
    for timeframe in SYMBOLS['es_intraday_timeframes']:
        try:
            fetch_es_intraday(timeframe)
            successful_collections.append(f"es_intraday_{timeframe}")
        except Exception as e:
            logger.error(f"  Failed to collect ES intraday {timeframe}: {e}")
            failed_collections.append(f"es_intraday_{timeframe}")
    logger.info("  If ES intraday not available from Alpha Vantage, run collect_es_yahoo_fallback.py for Yahoo Finance")

    # --- Collect News Sentiment & Analysis (ZL-FOCUSED) ---
    logger.info("\n--- Collecting News Sentiment & Analysis (ZL-Focused) ---")
    logger.info("  PRIMARY: ZL (soybean oil) prediction")
    logger.info("  SECONDARY: Cross-asset correlations (crude oil, VIX) for regime detection")
    logger.info("  FILTERED: General tech, entertainment, ES/MES-specific news excluded")
    logger.info("  (Pausing 5 seconds before starting batch...)")
    time.sleep(5)  # Pause before batch
    
    # Collect news by topics relevant to ZL (commodity prices, economic indicators)
    # Focus on topics that affect commodity prices, not general financial markets
    zl_relevant_topics = [
        'economy_macro',      # Macro economic indicators affect commodity demand
        'economy_monetary'    # Fed rates, monetary policy affect commodity prices
        # NOTE: Excluding 'financial_markets' (too broad, includes ES/MES)
        # NOTE: Excluding 'economy_fiscal' (less directly relevant to commodities)
        # NOTE: Excluding 'energy_transportation' (unless it mentions biofuels/commodities)
    ]
    
    for topic in zl_relevant_topics:
        try:
            result = fetch_news_sentiment(topics=topic, filter_zl_relevant=True)
            if result is not None and not result.empty:
                successful_collections.append(f"news_sentiment_{topic}")
            else:
                failed_collections.append(f"news_sentiment_{topic}")
        except Exception as e:
            logger.error(f"  Failed to collect news sentiment for topic {topic}: {e}")
            failed_collections.append(f"news_sentiment_{topic}")
    
    # Skip symbol-specific news collection (not relevant to ZL prediction)
    # ES/MES news is only used for correlations, not primary collection
    
    # --- Collect Options Chains ---
    logger.info("\n--- Collecting Options Chains ---")
    for symbol in SYMBOLS['options_symbols']:
        try:
            fetch_options_chain(symbol)
            successful_collections.append(f"options_{symbol.lower()}")
        except Exception as e:
            logger.error(f"  Failed to collect options for {symbol}: {e}")
            failed_collections.append(f"options_{symbol.lower()}")
    
    logger.info("="*80)
    logger.info("✅ Alpha Vantage COMPREHENSIVE Collection COMPLETE")
    logger.info(f"  Successfully collected: {len(successful_collections)} datasets")
    logger.info(f"  Failed to collect: {len(failed_collections)} datasets")
    if failed_collections:
        logger.warning(f"  Failed datasets: {', '.join(failed_collections)}")
    logger.info("   (Excluded Treasuries - sourced from FRED)")
    logger.info("   (Includes Options Chains for SOYB, CORN, WEAT, DBA, SPY)")
    logger.info("="*80)

if __name__ == "__main__":
    main()
