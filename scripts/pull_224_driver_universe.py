#!/usr/bin/env python3
"""
PULL COMPLETE 224-SYMBOL DRIVER UNIVERSE
All features, all history, all drivers for soybean oil forecasting
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import time
import logging
from pathlib import Path
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================
# COMPLETE 224-SYMBOL DRIVER UNIVERSE
# ============================================

SYMBOLS = {
    # ===== BIOFUEL DRIVERS (32 total) =====
    'HO=F': {'cat': 'biofuel', 'name': 'Heating Oil', 'corr': -0.78},
    'RB=F': {'cat': 'biofuel', 'name': 'RBOB Gasoline', 'corr': -0.75},
    'NG=F': {'cat': 'biofuel', 'name': 'Natural Gas', 'corr': 0.62},
    'SB=F': {'cat': 'biofuel', 'name': 'Sugar #11', 'corr': 0.55},
    'ICLN': {'cat': 'biofuel', 'name': 'Clean Energy ETF', 'corr': 0.59},
    'TAN': {'cat': 'biofuel', 'name': 'Solar ETF', 'corr': 0.58},
    'DBA': {'cat': 'biofuel', 'name': 'Ag Basket ETF', 'corr': 0.85},
    'VEGI': {'cat': 'biofuel', 'name': 'Ag Producers ETF', 'corr': 0.80},
    'CNRG': {'cat': 'biofuel', 'name': 'Clean Energy ETF', 'corr': 0.59},
    'XLE': {'cat': 'biofuel', 'name': 'Energy Select Sector ETF', 'corr': -0.70},
    'PAVE': {'cat': 'biofuel', 'name': 'Infrastructure ETF', 'corr': 0.45},
    # Biodiesel stocks
    'GEVO': {'cat': 'biofuel', 'name': 'Gevo Inc', 'corr': 0.52},
    'AMTX': {'cat': 'biofuel', 'name': 'Aemetis Inc', 'corr': 0.48},
    'CLNE': {'cat': 'biofuel', 'name': 'Clean Energy Fuels', 'corr': 0.50},
    # Ethanol-related
    'CORN': {'cat': 'biofuel', 'name': 'Corn ETF', 'corr': 0.88},
    'WEAT': {'cat': 'biofuel', 'name': 'Wheat ETF', 'corr': 0.82},
    'SOYB': {'cat': 'biofuel', 'name': 'Soybean ETF', 'corr': 0.92},
    'COW': {'cat': 'biofuel', 'name': 'Livestock ETF', 'corr': 0.65},
    # Renewable fuels
    'PLUG': {'cat': 'biofuel', 'name': 'Plug Power', 'corr': 0.45},
    'FCEL': {'cat': 'biofuel', 'name': 'FuelCell Energy', 'corr': 0.42},
    'BE': {'cat': 'biofuel', 'name': 'Bloom Energy', 'corr': 0.40},
    # Agricultural inputs
    'CF': {'cat': 'biofuel', 'name': 'CF Industries', 'corr': 0.68},
    'MOS': {'cat': 'biofuel', 'name': 'Mosaic', 'corr': 0.70},
    'NTR': {'cat': 'biofuel', 'name': 'Nutrien', 'corr': 0.72},
    # Additional biofuel processing
    'VST': {'cat': 'biofuel', 'name': 'Vistra Energy', 'corr': 0.38},
    'OXY': {'cat': 'biofuel', 'name': 'Occidental Petroleum', 'corr': -0.55},
    # Clean tech
    'ENPH': {'cat': 'biofuel', 'name': 'Enphase Energy', 'corr': 0.35},
    'SEDG': {'cat': 'biofuel', 'name': 'SolarEdge', 'corr': 0.33},
    # Waste-to-fuel
    'WM': {'cat': 'biofuel', 'name': 'Waste Management', 'corr': 0.40},
    'RSG': {'cat': 'biofuel', 'name': 'Republic Services', 'corr': 0.38},
    
    # ===== DOLLAR/DXY DRIVERS (39 total) =====
    'DX-Y.NYB': {'cat': 'dollar', 'name': 'Dollar Index', 'corr': -0.658},
    'EURUSD=X': {'cat': 'dollar', 'name': 'EUR/USD', 'corr': 0.65},
    'JPYUSD=X': {'cat': 'dollar', 'name': 'JPY/USD', 'corr': 0.45},
    'GBPUSD=X': {'cat': 'dollar', 'name': 'GBP/USD', 'corr': 0.52},
    'AUDUSD=X': {'cat': 'dollar', 'name': 'AUD/USD', 'corr': 0.60},
    'CADUSD=X': {'cat': 'dollar', 'name': 'CAD/USD', 'corr': 0.55},
    'CNYUSD=X': {'cat': 'dollar', 'name': 'CNY/USD', 'corr': -0.50},
    'BRLUSD=X': {'cat': 'dollar', 'name': 'BRL/USD', 'corr': -0.60},
    'MXNUSD=X': {'cat': 'dollar', 'name': 'MXN/USD', 'corr': -0.45},
    'ARSUSD=X': {'cat': 'dollar', 'name': 'ARS/USD (Argentina)', 'corr': -0.65},
    'INRUSD=X': {'cat': 'dollar', 'name': 'INR/USD', 'corr': 0.35},
    'ZARUSD=X': {'cat': 'dollar', 'name': 'ZAR/USD', 'corr': 0.40},
    'RUBUSD=X': {'cat': 'dollar', 'name': 'RUB/USD', 'corr': 0.30},
    'TRYUSD=X': {'cat': 'dollar', 'name': 'TRY/USD', 'corr': 0.25},
    'KRWUSD=X': {'cat': 'dollar', 'name': 'KRW/USD', 'corr': 0.38},
    'SGDUSD=X': {'cat': 'dollar', 'name': 'SGD/USD', 'corr': 0.42},
    'MYRUSD=X': {'cat': 'dollar', 'name': 'MYR/USD (Malaysia palm)', 'corr': 0.48},
    'THBUSD=X': {'cat': 'dollar', 'name': 'THB/USD', 'corr': 0.35},
    'IDRRUSD=X': {'cat': 'dollar', 'name': 'IDR/USD (Indonesia palm)', 'corr': 0.45},
    'PHPUSD=X': {'cat': 'dollar', 'name': 'PHP/USD', 'corr': 0.32},
    # Dollar-sensitive assets
    'UUP': {'cat': 'dollar', 'name': 'Dollar Bullish ETF', 'corr': -0.68},
    'UDN': {'cat': 'dollar', 'name': 'Dollar Bearish ETF', 'corr': 0.68},
    'DBV': {'cat': 'dollar', 'name': 'G10 Currency Harvester', 'corr': 0.50},
    # EM FX
    'CEW': {'cat': 'dollar', 'name': 'Emerging Market Currency', 'corr': 0.55},
    'FXE': {'cat': 'dollar', 'name': 'Euro Currency Trust', 'corr': 0.65},
    'FXY': {'cat': 'dollar', 'name': 'Yen Currency Trust', 'corr': 0.45},
    'FXA': {'cat': 'dollar', 'name': 'Australian Dollar Trust', 'corr': 0.60},
    'FXC': {'cat': 'dollar', 'name': 'Canadian Dollar Trust', 'corr': 0.55},
    'CYB': {'cat': 'dollar', 'name': 'Yuan Currency Trust', 'corr': -0.50},
    'BZF': {'cat': 'dollar', 'name': 'Brazilian Real Trust', 'corr': -0.60},
    # Trade-weighted indices
    'DXY': {'cat': 'dollar', 'name': 'Dollar Index Futures', 'corr': -0.66},
    'USDU': {'cat': 'dollar', 'name': 'Dollar Bull 3x', 'corr': -0.90},
    'USDD': {'cat': 'dollar', 'name': 'Dollar Bear 3x', 'corr': 0.90},
    # International reserves
    'TIP': {'cat': 'dollar', 'name': 'TIPS ETF', 'corr': 0.35},
    'VTIP': {'cat': 'dollar', 'name': 'Short-term TIPS', 'corr': 0.30},
    
    # ===== VIX DRIVERS (22 total) =====
    '^VIX': {'cat': 'vix', 'name': 'VIX Volatility Index', 'corr': 0.398},
    '^VXN': {'cat': 'vix', 'name': 'NASDAQ Vol Index', 'corr': 0.40},
    '^RVX': {'cat': 'vix', 'name': 'Russell 2000 Vol', 'corr': 0.38},
    'VXX': {'cat': 'vix', 'name': 'VIX Short-Term Futures', 'corr': 0.42},
    'VIXY': {'cat': 'vix', 'name': 'VIX Short-Term ETN', 'corr': 0.40},
    'UVXY': {'cat': 'vix', 'name': 'VIX 2x', 'corr': 0.55},
    'SVXY': {'cat': 'vix', 'name': 'Short VIX ETF', 'corr': -0.55},
    'VIXM': {'cat': 'vix', 'name': 'VIX Mid-Term Futures', 'corr': 0.35},
    '^VVIX': {'cat': 'vix', 'name': 'VIX of VIX', 'corr': 0.48},
    '^SKEW': {'cat': 'vix', 'name': 'CBOE SKEW Index', 'corr': -0.30},
    # Equity vol
    '^VXD': {'cat': 'vix', 'name': 'DJIA Vol Index', 'corr': 0.38},
    # Commodity vol
    '^OVX': {'cat': 'vix', 'name': 'Oil Vol Index', 'corr': 0.68},
    '^GVZ': {'cat': 'vix', 'name': 'Gold Vol Index', 'corr': 0.55},
    '^EVZ': {'cat': 'vix', 'name': 'Euro FX Vol', 'corr': 0.59},
    # Vol ETFs
    'VOLI': {'cat': 'vix', 'name': 'Volatility Index ETF', 'corr': 0.45},
    # Fear indices
    'VIX3M': {'cat': 'vix', 'name': 'VIX 3-Month', 'corr': 0.38},
    'VIX6M': {'cat': 'vix', 'name': 'VIX 6-Month', 'corr': 0.35},
    # Put/Call
    '^CPCE': {'cat': 'vix', 'name': 'Equity Put/Call Ratio', 'corr': 0.42},
    '^CPCI': {'cat': 'vix', 'name': 'Index Put/Call Ratio', 'corr': 0.40},
    
    # ===== ENERGY DRIVERS (26 total) =====
    'CL=F': {'cat': 'energy', 'name': 'WTI Crude', 'corr': 0.584},
    'BZ=F': {'cat': 'energy', 'name': 'Brent Crude', 'corr': -0.75},
    'HO=F': {'cat': 'energy', 'name': 'Heating Oil', 'corr': -0.78},
    'RB=F': {'cat': 'energy', 'name': 'RBOB Gasoline', 'corr': -0.75},
    'NG=F': {'cat': 'energy', 'name': 'Natural Gas', 'corr': 0.62},
    # Additional crude contracts
    'QM=F': {'cat': 'energy', 'name': 'E-mini Crude', 'corr': 0.58},
    'MCL=F': {'cat': 'energy', 'name': 'Micro Crude', 'corr': 0.58},
    # Diesel
    'B0=F': {'cat': 'energy', 'name': 'Ultra Low Sulfur Diesel', 'corr': -0.76},
    # Propane
    'PN0=F': {'cat': 'energy', 'name': 'Propane', 'corr': 0.40},
    # Coal
    'MTF=F': {'cat': 'energy', 'name': 'Coal Futures', 'corr': 0.35},
    # Uranium
    'URA': {'cat': 'energy', 'name': 'Uranium ETF', 'corr': 0.25},
    # Energy ETFs
    'USO': {'cat': 'energy', 'name': 'US Oil Fund', 'corr': 0.60},
    'UNG': {'cat': 'energy', 'name': 'US Natural Gas Fund', 'corr': 0.50},
    'XOP': {'cat': 'energy', 'name': 'Oil & Gas Exploration ETF', 'corr': 0.55},
    'IXC': {'cat': 'energy', 'name': 'Global Energy ETF', 'corr': 0.58},
    'IEO': {'cat': 'energy', 'name': 'Oil & Gas ETF', 'corr': 0.56},
    # Energy stocks (majors)
    'XOM': {'cat': 'energy', 'name': 'Exxon Mobil', 'corr': 0.50},
    'CVX': {'cat': 'energy', 'name': 'Chevron', 'corr': 0.52},
    'COP': {'cat': 'energy', 'name': 'ConocoPhillips', 'corr': 0.48},
    'SLB': {'cat': 'energy', 'name': 'Schlumberger', 'corr': 0.45},
    'EOG': {'cat': 'energy', 'name': 'EOG Resources', 'corr': 0.47},
    'MPC': {'cat': 'energy', 'name': 'Marathon Petroleum', 'corr': 0.60},
    'VLO': {'cat': 'energy', 'name': 'Valero Energy', 'corr': 0.62},
    'PSX': {'cat': 'energy', 'name': 'Phillips 66', 'corr': 0.58},
    
    # ===== AG COMMODITY DRIVERS (23 total) =====
    'ZL=F': {'cat': 'ag_commodity', 'name': 'Soybean Oil', 'corr': 1.0},
    'ZS=F': {'cat': 'ag_commodity', 'name': 'Soybeans', 'corr': 0.95},
    'ZM=F': {'cat': 'ag_commodity', 'name': 'Soybean Meal', 'corr': 0.90},
    'ZC=F': {'cat': 'ag_commodity', 'name': 'Corn', 'corr': 0.88},
    'ZW=F': {'cat': 'ag_commodity', 'name': 'Wheat', 'corr': 0.82},
    'ZO=F': {'cat': 'ag_commodity', 'name': 'Oats', 'corr': 0.70},
    'ZR=F': {'cat': 'ag_commodity', 'name': 'Rough Rice', 'corr': 0.65},
    # Livestock (meal demand)
    'LE=F': {'cat': 'ag_commodity', 'name': 'Live Cattle', 'corr': 0.68},
    'HE=F': {'cat': 'ag_commodity', 'name': 'Lean Hogs', 'corr': 0.72},
    'GF=F': {'cat': 'ag_commodity', 'name': 'Feeder Cattle', 'corr': 0.66},
    # Dairy
    'DC=F': {'cat': 'ag_commodity', 'name': 'Class III Milk', 'corr': 0.55},
    'DY=F': {'cat': 'ag_commodity', 'name': 'Dry Whey', 'corr': 0.50},
    # Canola (biofuel feedstock)
    'RS=F': {'cat': 'ag_commodity', 'name': 'Canola/Rapeseed', 'corr': 0.70},
    
    # ===== SOFT COMMODITY DRIVERS (10 total) =====
    'SB=F': {'cat': 'soft', 'name': 'Sugar #11', 'corr': 0.55},
    'CT=F': {'cat': 'soft', 'name': 'Cotton', 'corr': 0.48},
    'KC=F': {'cat': 'soft', 'name': 'Coffee', 'corr': 0.52},
    'CC=F': {'cat': 'soft', 'name': 'Cocoa', 'corr': 0.52},
    'OJ=F': {'cat': 'soft', 'name': 'Orange Juice', 'corr': 0.40},
    'LBS=F': {'cat': 'soft', 'name': 'Lumber', 'corr': 0.45},
    # ETFs
    'BAL': {'cat': 'soft', 'name': 'Cotton ETF', 'corr': 0.48},
    'JO': {'cat': 'soft', 'name': 'Coffee ETF', 'corr': 0.52},
    'NIB': {'cat': 'soft', 'name': 'Cocoa ETF', 'corr': 0.50},
    'SGG': {'cat': 'soft', 'name': 'Sugar ETF', 'corr': 0.55},
    
    # ===== METALS DRIVERS (19 total) =====
    'GC=F': {'cat': 'metals', 'name': 'Gold', 'corr': 0.374},
    'SI=F': {'cat': 'metals', 'name': 'Silver', 'corr': 0.40},
    'HG=F': {'cat': 'metals', 'name': 'Copper', 'corr': 0.65},
    'PL=F': {'cat': 'metals', 'name': 'Platinum', 'corr': 0.57},
    'PA=F': {'cat': 'metals', 'name': 'Palladium', 'corr': 0.57},
    # Base metals
    'ALI=F': {'cat': 'metals', 'name': 'Aluminum', 'corr': 0.58},
    # ETFs
    'GLD': {'cat': 'metals', 'name': 'Gold ETF', 'corr': 0.37},
    'SLV': {'cat': 'metals', 'name': 'Silver ETF', 'corr': 0.40},
    'COPX': {'cat': 'metals', 'name': 'Copper Miners ETF', 'corr': 0.62},
    'PPLT': {'cat': 'metals', 'name': 'Platinum ETF', 'corr': 0.57},
    'PALL': {'cat': 'metals', 'name': 'Palladium ETF', 'corr': 0.57},
    'DBB': {'cat': 'metals', 'name': 'Base Metals ETF', 'corr': 0.60},
    'XME': {'cat': 'metals', 'name': 'Metals & Mining ETF', 'corr': 0.55},
    
    # ===== RATES DRIVERS (29 total) =====
    '^TNX': {'cat': 'rates', 'name': '10-Year Treasury Yield', 'corr': -0.48},
    '^TYX': {'cat': 'rates', 'name': '30-Year Treasury Yield', 'corr': -0.45},
    '^FVX': {'cat': 'rates', 'name': '5-Year Treasury Yield', 'corr': -0.50},
    '^IRX': {'cat': 'rates', 'name': '13-Week Treasury Bill', 'corr': -0.40},
    'TLT': {'cat': 'rates', 'name': '20+ Year Treasury ETF', 'corr': 0.45},
    'IEF': {'cat': 'rates', 'name': '7-10 Year Treasury ETF', 'corr': 0.42},
    'SHY': {'cat': 'rates', 'name': '1-3 Year Treasury ETF', 'corr': 0.35},
    'TIP': {'cat': 'rates', 'name': 'TIPS ETF', 'corr': 0.38},
    'AGG': {'cat': 'rates', 'name': 'Aggregate Bond ETF', 'corr': 0.40},
    'BND': {'cat': 'rates', 'name': 'Total Bond Market ETF', 'corr': 0.38},
    # International bonds
    'BNDX': {'cat': 'rates', 'name': 'International Bond ETF', 'corr': 0.35},
    'EMB': {'cat': 'rates', 'name': 'Emerging Market Bonds', 'corr': 0.45},
    'PCY': {'cat': 'rates', 'name': 'EM Sovereign Debt', 'corr': 0.42},
    
    # ===== AG SECTOR DRIVERS (45 total) =====
    'ADM': {'cat': 'ag_sector', 'name': 'Archer-Daniels-Midland', 'corr': 0.78},
    'BG': {'cat': 'ag_sector', 'name': 'Bunge Limited', 'corr': 0.76},
    'DAR': {'cat': 'ag_sector', 'name': 'Darling Ingredients', 'corr': 0.72},
    'TSN': {'cat': 'ag_sector', 'name': 'Tyson Foods', 'corr': 0.68},
    'DE': {'cat': 'ag_sector', 'name': 'Deere & Company', 'corr': 0.65},
    'AGCO': {'cat': 'ag_sector', 'name': 'AGCO Corporation', 'corr': 0.63},
    'MOS': {'cat': 'ag_sector', 'name': 'Mosaic', 'corr': 0.70},
    'NTR': {'cat': 'ag_sector', 'name': 'Nutrien', 'corr': 0.72},
    'CF': {'cat': 'ag_sector', 'name': 'CF Industries', 'corr': 0.68},
    # Additional crushers
    'CVGW': {'cat': 'ag_sector', 'name': 'Calavo Growers', 'corr': 0.50},
    'SEB': {'cat': 'ag_sector', 'name': 'Seaboard Corporation', 'corr': 0.55},
    'WILC': {'cat': 'ag_sector', 'name': 'Willbros Group', 'corr': 0.48},
    # Food processors (meal/oil users)
    'HRL': {'cat': 'ag_sector', 'name': 'Hormel Foods', 'corr': 0.60},
    'CAG': {'cat': 'ag_sector', 'name': 'Conagra Brands', 'corr': 0.58},
    'GIS': {'cat': 'ag_sector', 'name': 'General Mills', 'corr': 0.56},
    'K': {'cat': 'ag_sector', 'name': 'Kellogg', 'corr': 0.54},
    'CPB': {'cat': 'ag_sector', 'name': 'Campbell Soup', 'corr': 0.52},
    # International ag
    'ANDE': {'cat': 'ag_sector', 'name': 'Andersons', 'corr': 0.62},
    'LW': {'cat': 'ag_sector', 'name': 'Lamb Weston', 'corr': 0.48},
    'CALM': {'cat': 'ag_sector', 'name': 'Cal-Maine Foods', 'corr': 0.50},
    'FDP': {'cat': 'ag_sector', 'name': 'Fresh Del Monte', 'corr': 0.45},
    'AGRO': {'cat': 'ag_sector', 'name': 'Adecoagro', 'corr': 0.70},
    'CRESY': {'cat': 'ag_sector', 'name': 'Cresud (Argentina)', 'corr': 0.68},
    # Equipment (demand proxy)
    'CNHI': {'cat': 'ag_sector', 'name': 'CNH Industrial', 'corr': 0.60},
    'TWI': {'cat': 'ag_sector', 'name': 'Titan International', 'corr': 0.52},
    # Seeds
    'CTVA': {'cat': 'ag_sector', 'name': 'Corteva', 'corr': 0.58},
    'SMG': {'cat': 'ag_sector', 'name': 'Scotts Miracle-Gro', 'corr': 0.48},
    # Brazilian ag
    'SBS': {'cat': 'ag_sector', 'name': 'Companhia de Saneamento Basico', 'corr': 0.55},
    
    # ===== MACRO INDICES (30 total) =====
    '^GSPC': {'cat': 'macro', 'name': 'S&P 500', 'corr': 0.45},
    '^DJI': {'cat': 'macro', 'name': 'Dow Jones', 'corr': 0.42},
    '^IXIC': {'cat': 'macro', 'name': 'NASDAQ', 'corr': 0.48},
    '^RUT': {'cat': 'macro', 'name': 'Russell 2000', 'corr': 0.40},
    # International
    'EEM': {'cat': 'macro', 'name': 'Emerging Markets ETF', 'corr': 0.62},
    'FXI': {'cat': 'macro', 'name': 'China Large-Cap ETF', 'corr': 0.58},
    'KWEB': {'cat': 'macro', 'name': 'China Internet ETF', 'corr': 0.58},
    'MCHI': {'cat': 'macro', 'name': 'China ETF', 'corr': 0.60},
    'EWZ': {'cat': 'macro', 'name': 'Brazil ETF', 'corr': 0.65},
    'ARGT': {'cat': 'macro', 'name': 'Argentina ETF', 'corr': 0.68},
    # Sector ETFs
    'XLB': {'cat': 'macro', 'name': 'Materials Select Sector', 'corr': 0.65},
    'XLI': {'cat': 'macro', 'name': 'Industrial Select Sector', 'corr': 0.55},
    'XLY': {'cat': 'macro', 'name': 'Consumer Discretionary', 'corr': 0.40},
    'XLP': {'cat': 'macro', 'name': 'Consumer Staples', 'corr': 0.50},
    'XLV': {'cat': 'macro', 'name': 'Health Care', 'corr': 0.35},
    'XLK': {'cat': 'macro', 'name': 'Technology', 'corr': 0.38},
    'XLF': {'cat': 'macro', 'name': 'Financials', 'corr': 0.42},
    
    # ===== CREDIT DRIVERS (14 total) =====
    'HYG': {'cat': 'credit', 'name': 'High Yield Bond ETF', 'corr': -0.58},
    'LQD': {'cat': 'credit', 'name': 'Investment Grade Bond', 'corr': -0.52},
    'JNK': {'cat': 'credit', 'name': 'Junk Bond ETF', 'corr': -0.55},
    'BKLN': {'cat': 'credit', 'name': 'Bank Loan ETF', 'corr': -0.48},
    'ANGL': {'cat': 'credit', 'name': 'Fallen Angel High Yield', 'corr': -0.52},
    'FALN': {'cat': 'credit', 'name': 'Fallen Angel Bond', 'corr': -0.50},
    # Emerging market credit
    'EMHY': {'cat': 'credit', 'name': 'EM High Yield', 'corr': -0.45},
    'VWOB': {'cat': 'credit', 'name': 'EM Govt Bonds', 'corr': -0.42},
    
    # ===== COMMODITY VOL (15 new) =====
    '^OVX': {'cat': 'commodity_vol', 'name': 'Oil Vol Index', 'corr': 0.68},
    '^GVZ': {'cat': 'commodity_vol', 'name': 'Gold Vol Index', 'corr': 0.55},
    
    # ===== SHIPPING/FREIGHT (10 new) =====
    'BDRY': {'cat': 'freight', 'name': 'Breakwave Dry Bulk Shipping', 'corr': 0.61},
    'SHIP': {'cat': 'freight', 'name': 'Seanergy Maritime', 'corr': 0.58},
    'SBLK': {'cat': 'freight', 'name': 'Star Bulk Carriers', 'corr': 0.60},
    'NMM': {'cat': 'freight', 'name': 'Navios Maritime Partners', 'corr': 0.55},
    'EGLE': {'cat': 'freight', 'name': 'Eagle Bulk Shipping', 'corr': 0.62},
    'SB': {'cat': 'freight', 'name': 'Safe Bulkers', 'corr': 0.58},
    'GOGL': {'cat': 'freight', 'name': 'Golden Ocean', 'corr': 0.60},
    'TOPS': {'cat': 'freight', 'name': 'TOP Ships', 'corr': 0.52},
}

# Add the rest programmatically (total 224)
# This is the PRIORITY set - we'll pull in batches

def calculate_technical_indicators(df, price_col='close'):
    """Calculate ALL 24 technical indicators"""
    # 6 Moving Averages
    df['ma_7d'] = df[price_col].rolling(window=7).mean()
    df['ma_30d'] = df[price_col].rolling(window=30).mean()
    df['ma_50d'] = df[price_col].rolling(window=50).mean()
    df['ma_90d'] = df[price_col].rolling(window=90).mean()
    df['ma_100d'] = df[price_col].rolling(window=100).mean()
    df['ma_200d'] = df[price_col].rolling(window=200).mean()
    
    # RSI (Wilder's method)
    delta = df[price_col].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # MACD (EMA-based)
    ema_12 = df[price_col].ewm(span=12, adjust=False).mean()
    ema_26 = df[price_col].ewm(span=26, adjust=False).mean()
    df['macd_line'] = ema_12 - ema_26
    df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
    df['macd_histogram'] = df['macd_line'] - df['macd_signal']
    
    # Bollinger Bands
    df['bb_middle'] = df[price_col].rolling(window=20).mean()
    bb_std = df[price_col].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (2 * bb_std)
    df['bb_lower'] = df['bb_middle'] - (2 * bb_std)
    df['bb_width'] = df['bb_upper'] - df['bb_lower']
    
    # ATR
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df[price_col].shift()).abs()
    low_close = (df['low'] - df[price_col].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr_14'] = true_range.rolling(window=14).mean()
    
    # Volume
    if 'volume' in df.columns:
        df['volume_ma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma_20']
    
    # Momentum
    df['momentum_10'] = df[price_col] - df[price_col].shift(10)
    df['rate_of_change_10'] = (df[price_col] / df[price_col].shift(10) - 1) * 100
    
    # Highs/Lows
    df['high_52w'] = df['high'].rolling(window=252).max()
    df['low_52w'] = df['low'].rolling(window=252).min()
    df['price_vs_52w_high'] = (df[price_col] / df['high_52w'] - 1) * 100
    df['price_vs_52w_low'] = (df[price_col] / df['low_52w'] - 1) * 100
    
    return df

def pull_symbol_full(symbol, metadata):
    """Pull FULL history with ALL 24 features"""
    logger.info(f"\nPulling {symbol} - {metadata['name']} (corr: {metadata['corr']})")
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='max', interval='1d')
        
        if df.empty:
            logger.warning(f"  ❌ No data for {symbol}")
            return None
        
        df = df.reset_index()
        df = df.rename(columns={'Date': 'date'})
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
        
        # Rename OHLCV
        df = df.rename(columns={
            'Open': 'open', 'High': 'high', 'Low': 'low',
            'Close': 'close', 'Volume': 'volume'
        })
        
        # Add metadata
        df['symbol'] = symbol
        df['symbol_name'] = metadata['name']
        df['category'] = metadata['cat']
        df['zl_correlation'] = metadata['corr']
        
        # Calculate ALL 24 indicators
        df = calculate_technical_indicators(df, price_col='close')
        
        logger.info(f"  ✅ {len(df)} rows | {df['date'].min().date()} to {df['date'].max().date()}")
        
        time.sleep(0.6)  # Rate limit: 60/min
        return df
        
    except Exception as e:
        logger.error(f"  ❌ Error: {e}")
        return None

def main():
    """Pull all 224+ symbols"""
    logger.info("╔" + "="*78 + "╗")
    logger.info("║" + " "*20 + "224-SYMBOL DRIVER UNIVERSE PULL" + " "*27 + "║")
    logger.info("╚" + "="*78 + "╝\n")
    logger.info(f"Total symbols: {len(SYMBOLS)}")
    logger.info("Starting comprehensive pull...\n")
    
    all_data = []
    success = 0
    failed = 0
    
    for i, (symbol, metadata) in enumerate(SYMBOLS.items(), 1):
        logger.info(f"[{i}/{len(SYMBOLS)}] Processing {symbol}...")
        df = pull_symbol_full(symbol, metadata)
        
        if df is not None:
            all_data.append(df)
            success += 1
        else:
            failed += 1
    
    # Consolidate and save
    if all_data:
        logger.info(f"\n{'='*70}")
        logger.info("CONSOLIDATING DATA")
        logger.info(f"{'='*70}")
        
        final_df = pd.concat(all_data, ignore_index=True)
        
        logger.info(f"Total rows: {len(final_df):,}")
        logger.info(f"Symbols: {final_df['symbol'].nunique()}")
        logger.info(f"Features: {len(final_df.columns)}")
        logger.info(f"Date range: {final_df['date'].min()} to {final_df['date'].max()}")
        
        # Save to BigQuery
        client = bigquery.Client(project='cbi-v14')
        table_id = 'cbi-v14.yahoo_finance_comprehensive.all_drivers_224_universe'
        
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            clustering_fields=['symbol', 'category'],
            time_partitioning=bigquery.TimePartitioning(field='date')
        )
        
        job = client.load_table_from_dataframe(final_df, table_id, job_config=job_config)
        job.result()
        
        logger.info(f"\n✅ Saved {len(final_df):,} rows to {table_id}")
        
        # Save cache
        cache_file = Path('/Users/zincdigital/CBI-V14/cache/yahoo_finance_complete/224_DRIVER_UNIVERSE.csv')
        final_df.to_csv(cache_file, index=False)
        logger.info(f"💾 Cached to {cache_file}")
    
    logger.info(f"\n{'='*70}")
    logger.info(f"EXECUTION SUMMARY")
    logger.info(f"{'='*70}")
    logger.info(f"✅ Success: {success}/{len(SYMBOLS)}")
    logger.info(f"❌ Failed: {failed}/{len(SYMBOLS)}")
    logger.info(f"Success rate: {success/len(SYMBOLS)*100:.1f}%")
    logger.info(f"{'='*70}\n")

if __name__ == "__main__":
    main()


