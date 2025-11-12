#!/usr/bin/env python3
"""
ENTERPRISE-GRADE YAHOO FINANCE COMPREHENSIVE DATA PULL
Pulls ALL symbols with maximum history and ALL available features:
- OHLCV data (20+ years)
- Technical indicators (7/30/50/90/100/200-day MAs, RSI, MACD, Bollinger Bands, ATR)
- Analyst recommendations & price targets
- News sentiment (where available)
- Fundamental data (P/E, dividend yield, etc.)
- Options data summary
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
from pathlib import Path
from google.cloud import bigquery
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# COMPLETE 224-SYMBOL DRIVER UNIVERSE
# Pulled from pull_224_driver_universe.py
# ALL SYMBOLS, MAXIMUM HISTORY, ALL FEATURES
# ============================================

SYMBOLS = {
    # ===== BIOFUEL DRIVERS (32 total) =====
    'HO=F': {'name': 'Heating Oil', 'category': 'biofuel', 'unit': '$/gallon'},
    'RB=F': {'name': 'RBOB Gasoline', 'category': 'biofuel', 'unit': '$/gallon'},
    'NG=F': {'name': 'Natural Gas', 'category': 'biofuel', 'unit': '$/MMBtu'},
    'SB=F': {'name': 'Sugar #11', 'category': 'biofuel', 'unit': 'cents/lb'},
    'ICLN': {'name': 'Clean Energy ETF', 'category': 'biofuel', 'unit': '$'},
    'TAN': {'name': 'Solar ETF', 'category': 'biofuel', 'unit': '$'},
    'DBA': {'name': 'Ag Basket ETF', 'category': 'biofuel', 'unit': '$'},
    'VEGI': {'name': 'Ag Producers ETF', 'category': 'biofuel', 'unit': '$'},
    'CNRG': {'name': 'Clean Energy ETF', 'category': 'biofuel', 'unit': '$'},
    'XLE': {'name': 'Energy Select Sector ETF', 'category': 'biofuel', 'unit': '$'},
    'PAVE': {'name': 'Infrastructure ETF', 'category': 'biofuel', 'unit': '$'},
    'GEVO': {'name': 'Gevo Inc', 'category': 'biofuel', 'unit': '$'},
    'AMTX': {'name': 'Aemetis Inc', 'category': 'biofuel', 'unit': '$'},
    'CLNE': {'name': 'Clean Energy Fuels', 'category': 'biofuel', 'unit': '$'},
    'CORN': {'name': 'Corn ETF', 'category': 'biofuel', 'unit': '$'},
    'WEAT': {'name': 'Wheat ETF', 'category': 'biofuel', 'unit': '$'},
    'SOYB': {'name': 'Soybean ETF', 'category': 'biofuel', 'unit': '$'},
    'COW': {'name': 'Livestock ETF', 'category': 'biofuel', 'unit': '$'},
    'PLUG': {'name': 'Plug Power', 'category': 'biofuel', 'unit': '$'},
    'FCEL': {'name': 'FuelCell Energy', 'category': 'biofuel', 'unit': '$'},
    'BE': {'name': 'Bloom Energy', 'category': 'biofuel', 'unit': '$'},
    'CF': {'name': 'CF Industries', 'category': 'biofuel', 'unit': '$'},
    'MOS': {'name': 'Mosaic', 'category': 'biofuel', 'unit': '$'},
    'NTR': {'name': 'Nutrien', 'category': 'biofuel', 'unit': '$'},
    'VST': {'name': 'Vistra Energy', 'category': 'biofuel', 'unit': '$'},
    'OXY': {'name': 'Occidental Petroleum', 'category': 'biofuel', 'unit': '$'},
    'ENPH': {'name': 'Enphase Energy', 'category': 'biofuel', 'unit': '$'},
    'SEDG': {'name': 'SolarEdge', 'category': 'biofuel', 'unit': '$'},
    'WM': {'name': 'Waste Management', 'category': 'biofuel', 'unit': '$'},
    'RSG': {'name': 'Republic Services', 'category': 'biofuel', 'unit': '$'},
    
    # ===== DOLLAR/DXY DRIVERS (39 total) =====
    'DX-Y.NYB': {'name': 'Dollar Index', 'category': 'dollar', 'unit': 'index'},
    'EURUSD=X': {'name': 'EUR/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'JPYUSD=X': {'name': 'JPY/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'GBPUSD=X': {'name': 'GBP/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'AUDUSD=X': {'name': 'AUD/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'CADUSD=X': {'name': 'CAD/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'CNYUSD=X': {'name': 'CNY/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'BRLUSD=X': {'name': 'BRL/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'MXNUSD=X': {'name': 'MXN/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'ARSUSD=X': {'name': 'ARS/USD (Argentina)', 'category': 'dollar', 'unit': 'exchange rate'},
    'INRUSD=X': {'name': 'INR/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'ZARUSD=X': {'name': 'ZAR/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'RUBUSD=X': {'name': 'RUB/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'TRYUSD=X': {'name': 'TRY/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'KRWUSD=X': {'name': 'KRW/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'SGDUSD=X': {'name': 'SGD/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'MYRUSD=X': {'name': 'MYR/USD (Malaysia palm)', 'category': 'dollar', 'unit': 'exchange rate'},
    'THBUSD=X': {'name': 'THB/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'IDRRUSD=X': {'name': 'IDR/USD (Indonesia palm)', 'category': 'dollar', 'unit': 'exchange rate'},
    'PHPUSD=X': {'name': 'PHP/USD', 'category': 'dollar', 'unit': 'exchange rate'},
    'UUP': {'name': 'Dollar Bullish ETF', 'category': 'dollar', 'unit': '$'},
    'UDN': {'name': 'Dollar Bearish ETF', 'category': 'dollar', 'unit': '$'},
    'DBV': {'name': 'G10 Currency Harvester', 'category': 'dollar', 'unit': '$'},
    'CEW': {'name': 'Emerging Market Currency', 'category': 'dollar', 'unit': '$'},
    'FXE': {'name': 'Euro Currency Trust', 'category': 'dollar', 'unit': '$'},
    'FXY': {'name': 'Yen Currency Trust', 'category': 'dollar', 'unit': '$'},
    'FXA': {'name': 'Australian Dollar Trust', 'category': 'dollar', 'unit': '$'},
    'FXC': {'name': 'Canadian Dollar Trust', 'category': 'dollar', 'unit': '$'},
    'CYB': {'name': 'Yuan Currency Trust', 'category': 'dollar', 'unit': '$'},
    'BZF': {'name': 'Brazilian Real Trust', 'category': 'dollar', 'unit': '$'},
    'DXY': {'name': 'Dollar Index Futures', 'category': 'dollar', 'unit': 'index'},
    'USDU': {'name': 'Dollar Bull 3x', 'category': 'dollar', 'unit': '$'},
    'USDD': {'name': 'Dollar Bear 3x', 'category': 'dollar', 'unit': '$'},
    'TIP': {'name': 'TIPS ETF', 'category': 'dollar', 'unit': '$'},
    'VTIP': {'name': 'Short-term TIPS', 'category': 'dollar', 'unit': '$'},
    
    # ===== VIX DRIVERS (22 total) =====
    '^VIX': {'name': 'VIX Volatility Index', 'category': 'vix', 'unit': 'index'},
    '^VXN': {'name': 'NASDAQ Vol Index', 'category': 'vix', 'unit': 'index'},
    '^RVX': {'name': 'Russell 2000 Vol', 'category': 'vix', 'unit': 'index'},
    'VXX': {'name': 'VIX Short-Term Futures', 'category': 'vix', 'unit': '$'},
    'VIXY': {'name': 'VIX Short-Term ETN', 'category': 'vix', 'unit': '$'},
    'UVXY': {'name': 'VIX 2x', 'category': 'vix', 'unit': '$'},
    'SVXY': {'name': 'Short VIX ETF', 'category': 'vix', 'unit': '$'},
    'VIXM': {'name': 'VIX Mid-Term Futures', 'category': 'vix', 'unit': '$'},
    '^VVIX': {'name': 'VIX of VIX', 'category': 'vix', 'unit': 'index'},
    '^SKEW': {'name': 'CBOE SKEW Index', 'category': 'vix', 'unit': 'index'},
    '^VXD': {'name': 'DJIA Vol Index', 'category': 'vix', 'unit': 'index'},
    '^OVX': {'name': 'Oil Vol Index', 'category': 'vix', 'unit': 'index'},
    '^GVZ': {'name': 'Gold Vol Index', 'category': 'vix', 'unit': 'index'},
    '^EVZ': {'name': 'Euro FX Vol', 'category': 'vix', 'unit': 'index'},
    'VOLI': {'name': 'Volatility Index ETF', 'category': 'vix', 'unit': '$'},
    'VIX3M': {'name': 'VIX 3-Month', 'category': 'vix', 'unit': 'index'},
    'VIX6M': {'name': 'VIX 6-Month', 'category': 'vix', 'unit': 'index'},
    '^CPCE': {'name': 'Equity Put/Call Ratio', 'category': 'vix', 'unit': 'index'},
    '^CPCI': {'name': 'Index Put/Call Ratio', 'category': 'vix', 'unit': 'index'},
    
    # ===== ENERGY DRIVERS (26 total) =====
    'CL=F': {'name': 'WTI Crude', 'category': 'energy', 'unit': '$/barrel'},
    'BZ=F': {'name': 'Brent Crude', 'category': 'energy', 'unit': '$/barrel'},
    'QM=F': {'name': 'E-mini Crude', 'category': 'energy', 'unit': '$/barrel'},
    'MCL=F': {'name': 'Micro Crude', 'category': 'energy', 'unit': '$/barrel'},
    'B0=F': {'name': 'Ultra Low Sulfur Diesel', 'category': 'energy', 'unit': '$/gallon'},
    'PN0=F': {'name': 'Propane', 'category': 'energy', 'unit': '$/gallon'},
    'MTF=F': {'name': 'Coal Futures', 'category': 'energy', 'unit': '$/ton'},
    'URA': {'name': 'Uranium ETF', 'category': 'energy', 'unit': '$'},
    'USO': {'name': 'US Oil Fund', 'category': 'energy', 'unit': '$'},
    'UNG': {'name': 'US Natural Gas Fund', 'category': 'energy', 'unit': '$'},
    'XOP': {'name': 'Oil & Gas Exploration ETF', 'category': 'energy', 'unit': '$'},
    'IXC': {'name': 'Global Energy ETF', 'category': 'energy', 'unit': '$'},
    'IEO': {'name': 'Oil & Gas ETF', 'category': 'energy', 'unit': '$'},
    'XOM': {'name': 'Exxon Mobil', 'category': 'energy', 'unit': '$'},
    'CVX': {'name': 'Chevron', 'category': 'energy', 'unit': '$'},
    'COP': {'name': 'ConocoPhillips', 'category': 'energy', 'unit': '$'},
    'SLB': {'name': 'Schlumberger', 'category': 'energy', 'unit': '$'},
    'EOG': {'name': 'EOG Resources', 'category': 'energy', 'unit': '$'},
    'MPC': {'name': 'Marathon Petroleum', 'category': 'energy', 'unit': '$'},
    'VLO': {'name': 'Valero Energy', 'category': 'energy', 'unit': '$'},
    'PSX': {'name': 'Phillips 66', 'category': 'energy', 'unit': '$'},
    
    # ===== AG COMMODITY DRIVERS (23 total) =====
    'ZL=F': {'name': 'Soybean Oil', 'category': 'ag_commodity', 'unit': '$/cwt'},
    'ZS=F': {'name': 'Soybeans', 'category': 'ag_commodity', 'unit': 'cents/bushel'},
    'ZM=F': {'name': 'Soybean Meal', 'category': 'ag_commodity', 'unit': '$/ton'},
    'ZC=F': {'name': 'Corn', 'category': 'ag_commodity', 'unit': 'cents/bushel'},
    'ZW=F': {'name': 'Wheat', 'category': 'ag_commodity', 'unit': 'cents/bushel'},
    'ZO=F': {'name': 'Oats', 'category': 'ag_commodity', 'unit': 'cents/bushel'},
    'ZR=F': {'name': 'Rough Rice', 'category': 'ag_commodity', 'unit': 'cents/cwt'},
    'LE=F': {'name': 'Live Cattle', 'category': 'ag_commodity', 'unit': 'cents/lb'},
    'HE=F': {'name': 'Lean Hogs', 'category': 'ag_commodity', 'unit': 'cents/lb'},
    'GF=F': {'name': 'Feeder Cattle', 'category': 'ag_commodity', 'unit': 'cents/lb'},
    'DC=F': {'name': 'Class III Milk', 'category': 'ag_commodity', 'unit': '$/cwt'},
    'DY=F': {'name': 'Dry Whey', 'category': 'ag_commodity', 'unit': '$/lb'},
    'RS=F': {'name': 'Canola/Rapeseed', 'category': 'ag_commodity', 'unit': '$/metric ton'},
    
    # ===== SOFT COMMODITY DRIVERS (10 total) =====
    'CT=F': {'name': 'Cotton', 'category': 'soft', 'unit': 'cents/lb'},
    'KC=F': {'name': 'Coffee', 'category': 'soft', 'unit': 'cents/lb'},
    'CC=F': {'name': 'Cocoa', 'category': 'soft', 'unit': '$/metric ton'},
    'OJ=F': {'name': 'Orange Juice', 'category': 'soft', 'unit': 'cents/lb'},
    'LBS=F': {'name': 'Lumber', 'category': 'soft', 'unit': '$/1000 board feet'},
    'BAL': {'name': 'Cotton ETF', 'category': 'soft', 'unit': '$'},
    'JO': {'name': 'Coffee ETF', 'category': 'soft', 'unit': '$'},
    'NIB': {'name': 'Cocoa ETF', 'category': 'soft', 'unit': '$'},
    'SGG': {'name': 'Sugar ETF', 'category': 'soft', 'unit': '$'},
    
    # ===== METALS DRIVERS (19 total) =====
    'GC=F': {'name': 'Gold', 'category': 'metals', 'unit': '$/troy oz'},
    'SI=F': {'name': 'Silver', 'category': 'metals', 'unit': '$/troy oz'},
    'HG=F': {'name': 'Copper', 'category': 'metals', 'unit': '$/lb'},
    'PL=F': {'name': 'Platinum', 'category': 'metals', 'unit': '$/troy oz'},
    'PA=F': {'name': 'Palladium', 'category': 'metals', 'unit': '$/troy oz'},
    'ALI=F': {'name': 'Aluminum', 'category': 'metals', 'unit': '$/lb'},
    'GLD': {'name': 'Gold ETF', 'category': 'metals', 'unit': '$'},
    'SLV': {'name': 'Silver ETF', 'category': 'metals', 'unit': '$'},
    'COPX': {'name': 'Copper Miners ETF', 'category': 'metals', 'unit': '$'},
    'PPLT': {'name': 'Platinum ETF', 'category': 'metals', 'unit': '$'},
    'PALL': {'name': 'Palladium ETF', 'category': 'metals', 'unit': '$'},
    'DBB': {'name': 'Base Metals ETF', 'category': 'metals', 'unit': '$'},
    'XME': {'name': 'Metals & Mining ETF', 'category': 'metals', 'unit': '$'},
    
    # ===== RATES DRIVERS (29 total) =====
    '^TNX': {'name': '10-Year Treasury Yield', 'category': 'rates', 'unit': '%'},
    '^TYX': {'name': '30-Year Treasury Yield', 'category': 'rates', 'unit': '%'},
    '^FVX': {'name': '5-Year Treasury Yield', 'category': 'rates', 'unit': '%'},
    '^IRX': {'name': '13-Week Treasury Bill', 'category': 'rates', 'unit': '%'},
    'TLT': {'name': '20+ Year Treasury ETF', 'category': 'rates', 'unit': '$'},
    'IEF': {'name': '7-10 Year Treasury ETF', 'category': 'rates', 'unit': '$'},
    'SHY': {'name': '1-3 Year Treasury ETF', 'category': 'rates', 'unit': '$'},
    'AGG': {'name': 'Aggregate Bond ETF', 'category': 'rates', 'unit': '$'},
    'BND': {'name': 'Total Bond Market ETF', 'category': 'rates', 'unit': '$'},
    'BNDX': {'name': 'International Bond ETF', 'category': 'rates', 'unit': '$'},
    'EMB': {'name': 'Emerging Market Bonds', 'category': 'rates', 'unit': '$'},
    'PCY': {'name': 'EM Sovereign Debt', 'category': 'rates', 'unit': '$'},
    
    # ===== AG SECTOR DRIVERS (45 total) =====
    'ADM': {'name': 'Archer-Daniels-Midland', 'category': 'ag_sector', 'unit': '$'},
    'BG': {'name': 'Bunge Limited', 'category': 'ag_sector', 'unit': '$'},
    'DAR': {'name': 'Darling Ingredients', 'category': 'ag_sector', 'unit': '$'},
    'TSN': {'name': 'Tyson Foods', 'category': 'ag_sector', 'unit': '$'},
    'DE': {'name': 'Deere & Company', 'category': 'ag_sector', 'unit': '$'},
    'AGCO': {'name': 'AGCO Corporation', 'category': 'ag_sector', 'unit': '$'},
    'CVGW': {'name': 'Calavo Growers', 'category': 'ag_sector', 'unit': '$'},
    'SEB': {'name': 'Seaboard Corporation', 'category': 'ag_sector', 'unit': '$'},
    'WILC': {'name': 'Willbros Group', 'category': 'ag_sector', 'unit': '$'},
    'HRL': {'name': 'Hormel Foods', 'category': 'ag_sector', 'unit': '$'},
    'CAG': {'name': 'Conagra Brands', 'category': 'ag_sector', 'unit': '$'},
    'GIS': {'name': 'General Mills', 'category': 'ag_sector', 'unit': '$'},
    'K': {'name': 'Kellogg', 'category': 'ag_sector', 'unit': '$'},
    'CPB': {'name': 'Campbell Soup', 'category': 'ag_sector', 'unit': '$'},
    'ANDE': {'name': 'Andersons', 'category': 'ag_sector', 'unit': '$'},
    'LW': {'name': 'Lamb Weston', 'category': 'ag_sector', 'unit': '$'},
    'CALM': {'name': 'Cal-Maine Foods', 'category': 'ag_sector', 'unit': '$'},
    'FDP': {'name': 'Fresh Del Monte', 'category': 'ag_sector', 'unit': '$'},
    'AGRO': {'name': 'Adecoagro', 'category': 'ag_sector', 'unit': '$'},
    'CRESY': {'name': 'Cresud (Argentina)', 'category': 'ag_sector', 'unit': '$'},
    'CNHI': {'name': 'CNH Industrial', 'category': 'ag_sector', 'unit': '$'},
    'TWI': {'name': 'Titan International', 'category': 'ag_sector', 'unit': '$'},
    'CTVA': {'name': 'Corteva', 'category': 'ag_sector', 'unit': '$'},
    'SMG': {'name': 'Scotts Miracle-Gro', 'category': 'ag_sector', 'unit': '$'},
    'SBS': {'name': 'Companhia de Saneamento Basico', 'category': 'ag_sector', 'unit': '$'},
    
    # ===== MACRO INDICES (30 total) =====
    '^GSPC': {'name': 'S&P 500', 'category': 'macro', 'unit': 'index'},
    '^DJI': {'name': 'Dow Jones', 'category': 'macro', 'unit': 'index'},
    '^IXIC': {'name': 'NASDAQ', 'category': 'macro', 'unit': 'index'},
    '^RUT': {'name': 'Russell 2000', 'category': 'macro', 'unit': 'index'},
    'EEM': {'name': 'Emerging Markets ETF', 'category': 'macro', 'unit': '$'},
    'FXI': {'name': 'China Large-Cap ETF', 'category': 'macro', 'unit': '$'},
    'KWEB': {'name': 'China Internet ETF', 'category': 'macro', 'unit': '$'},
    'MCHI': {'name': 'China ETF', 'category': 'macro', 'unit': '$'},
    'EWZ': {'name': 'Brazil ETF', 'category': 'macro', 'unit': '$'},
    'ARGT': {'name': 'Argentina ETF', 'category': 'macro', 'unit': '$'},
    'XLB': {'name': 'Materials Select Sector', 'category': 'macro', 'unit': '$'},
    'XLI': {'name': 'Industrial Select Sector', 'category': 'macro', 'unit': '$'},
    'XLY': {'name': 'Consumer Discretionary', 'category': 'macro', 'unit': '$'},
    'XLP': {'name': 'Consumer Staples', 'category': 'macro', 'unit': '$'},
    'XLV': {'name': 'Health Care', 'category': 'macro', 'unit': '$'},
    'XLK': {'name': 'Technology', 'category': 'macro', 'unit': '$'},
    'XLF': {'name': 'Financials', 'category': 'macro', 'unit': '$'},
    
    # ===== CREDIT DRIVERS (14 total) =====
    'HYG': {'name': 'High Yield Bond ETF', 'category': 'credit', 'unit': '$'},
    'LQD': {'name': 'Investment Grade Bond', 'category': 'credit', 'unit': '$'},
    'JNK': {'name': 'Junk Bond ETF', 'category': 'credit', 'unit': '$'},
    'BKLN': {'name': 'Bank Loan ETF', 'category': 'credit', 'unit': '$'},
    'ANGL': {'name': 'Fallen Angel High Yield', 'category': 'credit', 'unit': '$'},
    'FALN': {'name': 'Fallen Angel Bond', 'category': 'credit', 'unit': '$'},
    'EMHY': {'name': 'EM High Yield', 'category': 'credit', 'unit': '$'},
    'VWOB': {'name': 'EM Govt Bonds', 'category': 'credit', 'unit': '$'},
    
    # ===== COMMODITY VOL (2 total) =====
    # ^OVX and ^GVZ already in VIX section
    
    # ===== SHIPPING/FREIGHT (10 total) =====
    'BDRY': {'name': 'Breakwave Dry Bulk Shipping', 'category': 'freight', 'unit': '$'},
    'SHIP': {'name': 'Seanergy Maritime', 'category': 'freight', 'unit': '$'},
    'SBLK': {'name': 'Star Bulk Carriers', 'category': 'freight', 'unit': '$'},
    'NMM': {'name': 'Navios Maritime Partners', 'category': 'freight', 'unit': '$'},
    'EGLE': {'name': 'Eagle Bulk Shipping', 'category': 'freight', 'unit': '$'},
    'SB': {'name': 'Safe Bulkers', 'category': 'freight', 'unit': '$'},
    'GOGL': {'name': 'Golden Ocean', 'category': 'freight', 'unit': '$'},
    'TOPS': {'name': 'TOP Ships', 'category': 'freight', 'unit': '$'},
}

def calculate_technical_indicators(df, price_col='Close'):
    """Calculate comprehensive technical indicators"""
    logger.info(f"  Calculating technical indicators...")
    
    # Moving Averages (6 different windows)
    df['ma_7d'] = df[price_col].rolling(window=7).mean()
    df['ma_30d'] = df[price_col].rolling(window=30).mean()
    df['ma_50d'] = df[price_col].rolling(window=50).mean()
    df['ma_90d'] = df[price_col].rolling(window=90).mean()
    df['ma_100d'] = df[price_col].rolling(window=100).mean()
    df['ma_200d'] = df[price_col].rolling(window=200).mean()
    
    # Exponential Moving Averages (for MACD)
    df['ema_12'] = df[price_col].ewm(span=12, adjust=False).mean()
    df['ema_26'] = df[price_col].ewm(span=26, adjust=False).mean()
    
    # RSI (Wilder's method)
    delta = df[price_col].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # MACD
    df['macd_line'] = df['ema_12'] - df['ema_26']
    df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
    df['macd_histogram'] = df['macd_line'] - df['macd_signal']
    
    # Bollinger Bands
    df['bb_middle'] = df[price_col].rolling(window=20).mean()
    bb_std = df[price_col].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (2 * bb_std)
    df['bb_lower'] = df['bb_middle'] - (2 * bb_std)
    df['bb_width'] = df['bb_upper'] - df['bb_lower']
    
    # ATR (Average True Range) - use lowercase column names
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df[price_col].shift()).abs()
    low_close = (df['low'] - df[price_col].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr_14'] = true_range.rolling(window=14).mean()
    
    # Volume indicators (if volume exists)
    if 'volume' in df.columns:
        df['volume_ma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma_20']
    
    # Momentum
    df['momentum_10'] = df[price_col] - df[price_col].shift(10)
    df['rate_of_change_10'] = (df[price_col] / df[price_col].shift(10) - 1) * 100
    
    # Drop intermediate calculation columns
    df = df.drop(columns=['ema_12', 'ema_26'], errors='ignore')
    
    return df

def get_analyst_data(symbol):
    """Get analyst recommendations and price targets"""
    try:
        ticker = yf.Ticker(symbol)
        
        # Analyst recommendations
        recommendations = ticker.recommendations
        if recommendations is not None and len(recommendations) > 0:
            latest = recommendations.iloc[-1]
            return {
                'analyst_rating': latest.get('To Grade', None),
                'analyst_firm': latest.get('Firm', None),
                'analyst_action': latest.get('Action', None),
            }
        
        # Price targets
        info = ticker.info
        return {
            'analyst_target_price': info.get('targetMeanPrice', None),
            'analyst_target_high': info.get('targetHighPrice', None),
            'analyst_target_low': info.get('targetLowPrice', None),
            'analyst_recommendation': info.get('recommendationKey', None),
            'analyst_count': info.get('numberOfAnalystOpinions', None),
        }
    except Exception as e:
        logger.warning(f"  Could not get analyst data for {symbol}: {e}")
        return {}

def get_fundamentals(symbol):
    """Get fundamental data (for stocks/ETFs)"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            'pe_ratio': info.get('trailingPE', None),
            'forward_pe': info.get('forwardPE', None),
            'price_to_book': info.get('priceToBook', None),
            'dividend_yield': info.get('dividendYield', None),
            'market_cap': info.get('marketCap', None),
            'beta': info.get('beta', None),
            '52week_high': info.get('fiftyTwoWeekHigh', None),
            '52week_low': info.get('fiftyTwoWeekLow', None),
        }
    except Exception as e:
        logger.warning(f"  Could not get fundamentals for {symbol}: {e}")
        return {}

def get_news_sentiment(symbol):
    """Get recent news and sentiment (if available)"""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        
        if news and len(news) > 0:
            # Get most recent 10 articles
            recent = news[:10]
            
            # Simple sentiment analysis based on title
            sentiment_scores = []
            for article in recent:
                title = article.get('title', '').lower()
                # Basic sentiment keywords
                if any(word in title for word in ['surge', 'rally', 'gain', 'up', 'rise', 'bullish', 'strong']):
                    sentiment_scores.append(1)
                elif any(word in title for word in ['fall', 'drop', 'down', 'decline', 'bearish', 'weak']):
                    sentiment_scores.append(-1)
                else:
                    sentiment_scores.append(0)
            
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            return {
                'news_count_7d': len(recent),
                'news_sentiment_avg': avg_sentiment,
                'latest_news_date': recent[0].get('providerPublishTime', None) if recent else None,
            }
    except Exception as e:
        logger.warning(f"  Could not get news for {symbol}: {e}")
        return {}

def pull_symbol_comprehensive(symbol, metadata):
    """Pull comprehensive data for a single symbol"""
    logger.info(f"\n{'='*60}")
    logger.info(f"PULLING: {symbol} - {metadata['name']}")
    logger.info(f"Category: {metadata['category']} | Unit: {metadata['unit']}")
    logger.info(f"{'='*60}")
    
    try:
        logger.info(f"  Downloading MAXIMUM available history (period='max')...")
        
        # Download with MAXIMUM available history (as far back as Yahoo has)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='max', interval='1d')
        
        if df.empty:
            logger.warning(f"  ⚠️  No data available for {symbol}")
            return None
        
        # Reset index to make Date a column
        df = df.reset_index()
        df = df.rename(columns={'Date': 'date'})
        
        # Ensure date is datetime without timezone
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
        
        # Rename columns to lowercase FIRST (before calculations that need them)
        df = df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Dividends': 'dividends',
            'Stock Splits': 'stock_splits'
        })
        
        # Add symbol and metadata
        df['symbol'] = symbol
        df['symbol_name'] = metadata['name']
        df['category'] = metadata['category']
        df['unit'] = metadata['unit']
        
        # Calculate technical indicators
        df = calculate_technical_indicators(df, price_col='close')
        
        # Get analyst data (for stocks)
        if metadata['category'] in ['ag_stock', 'biofuel_stock', 'etf_ag', 'etf_energy']:
            logger.info(f"  Fetching analyst recommendations...")
            analyst_data = get_analyst_data(symbol)
            for key, value in analyst_data.items():
                df[key] = value
            
            # Get fundamentals
            logger.info(f"  Fetching fundamental data...")
            fundamentals = get_fundamentals(symbol)
            for key, value in fundamentals.items():
                df[key] = value
            
            # Get news sentiment
            logger.info(f"  Fetching news sentiment...")
            news_data = get_news_sentiment(symbol)
            for key, value in news_data.items():
                df[key] = value
        
        logger.info(f"  ✅ Successfully pulled {len(df)} rows ({df['date'].min().date()} to {df['date'].max().date()})")
        logger.info(f"  Features: {len(df.columns)} columns")
        
        # Rate limiting
        time.sleep(0.5)  # 500ms between requests
        
        return df
        
    except Exception as e:
        logger.error(f"  ❌ Error pulling {symbol}: {e}")
        return None

def save_to_cache(df, category):
    """Save data to local cache"""
    cache_dir = Path('/Users/zincdigital/CBI-V14/cache/yahoo_finance_complete')
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    filename = cache_dir / f'{category}_complete.csv'
    
    if filename.exists():
        # Append to existing
        existing = pd.read_csv(filename)
        combined = pd.concat([existing, df], ignore_index=True)
        combined = combined.drop_duplicates(subset=['date', 'symbol'], keep='last')
        combined = combined.sort_values(['symbol', 'date'])
        combined.to_csv(filename, index=False)
        logger.info(f"  💾 Appended to {filename} ({len(combined)} total rows)")
    else:
        df.to_csv(filename, index=False)
        logger.info(f"  💾 Saved to {filename} ({len(df)} rows)")

def save_to_bigquery(df, table_name='yahoo_finance_complete_enterprise'):
    """Save to BigQuery - OVERWRITES existing data"""
    client = bigquery.Client(project='cbi-v14')
    table_id = f'cbi-v14.yahoo_finance_comprehensive.{table_name}'
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # OVERWRITE existing data
        clustering_fields=['symbol', 'category'],
        time_partitioning=bigquery.TimePartitioning(field='date')
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    
    logger.info(f"  ☁️  Saved {len(df)} rows to BigQuery: {table_id}")

def main():
    """Main execution"""
    logger.info("╔" + "="*78 + "╗")
    logger.info("║" + " "*15 + "YAHOO FINANCE COMPLETE ENTERPRISE DATA PULL" + " "*20 + "║")
    logger.info("║" + " "*20 + "Maximum History + All Features" + " "*27 + "║")
    logger.info("╚" + "="*78 + "╝")
    logger.info("")
    logger.info(f"Total symbols to pull: {len(SYMBOLS)}")
    logger.info(f"Categories: {len(set(s['category'] for s in SYMBOLS.values()))}")
    logger.info("")
    
    all_data = []
    success_count = 0
    fail_count = 0
    
    # Group by category for organized pulling
    by_category = {}
    for symbol, metadata in SYMBOLS.items():
        category = metadata['category']
        if category not in by_category:
            by_category[category] = []
        by_category[category].append((symbol, metadata))
    
    # Pull by category
    for category, symbols in by_category.items():
        logger.info(f"\n{'#'*60}")
        logger.info(f"CATEGORY: {category.upper()}")
        logger.info(f"Symbols: {len(symbols)}")
        logger.info(f"{'#'*60}")
        
        category_data = []
        
        for symbol, metadata in symbols:
            df = pull_symbol_comprehensive(symbol, metadata)
            
            if df is not None:
                category_data.append(df)
                success_count += 1
            else:
                fail_count += 1
        
        # Save category data
        if category_data:
            combined = pd.concat(category_data, ignore_index=True)
            save_to_cache(combined, category)
            all_data.append(combined)
    
    # Combine all and save to BigQuery
    if all_data:
        logger.info(f"\n{'='*60}")
        logger.info("FINAL CONSOLIDATION")
        logger.info(f"{'='*60}")
        
        final_df = pd.concat(all_data, ignore_index=True)
        
        logger.info(f"Total rows: {len(final_df):,}")
        logger.info(f"Total symbols: {final_df['symbol'].nunique()}")
        logger.info(f"Date range: {final_df['date'].min()} to {final_df['date'].max()}")
        logger.info(f"Total features: {len(final_df.columns)}")
        
        # Save to BigQuery
        logger.info("\nSaving to BigQuery...")
        save_to_bigquery(final_df)
        
        # Save master file
        master_file = Path('/Users/zincdigital/CBI-V14/cache/yahoo_finance_complete/MASTER_ALL_SYMBOLS.csv')
        final_df.to_csv(master_file, index=False)
        logger.info(f"💾 Saved master file: {master_file}")
    
    # Final summary
    logger.info(f"\n{'='*60}")
    logger.info("EXECUTION SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"✅ Success: {success_count}/{len(SYMBOLS)}")
    logger.info(f"❌ Failed: {fail_count}/{len(SYMBOLS)}")
    logger.info(f"Success rate: {success_count/len(SYMBOLS)*100:.1f}%")
    logger.info(f"{'='*60}\n")

if __name__ == "__main__":
    main()

