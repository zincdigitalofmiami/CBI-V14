"""
FRED Data Collection Script
Pulls economic data from Federal Reserve Economic Data (FRED)
Compliant with Universal Calculator Standard v1.0

Usage:
    export FRED_API_KEY="your_api_key"
    python collect_fred_data.py
"""

import os
import time
import pandas as pd
from datetime import datetime

try:
    from fredapi import Fred
except ImportError:
    print("ERROR: fredapi not installed. Run: pip install fredapi")
    exit(1)

try:
    from google.cloud import bigquery
except ImportError:
    print("ERROR: google-cloud-bigquery not installed. Run: pip install google-cloud-bigquery")
    exit(1)

# =============================================================================
# CONFIGURATION
# =============================================================================

API_KEY = os.environ.get("FRED_API_KEY")
if not API_KEY:
    raise ValueError("FRED_API_KEY environment variable not set. Get key from https://fred.stlouisfed.org/docs/api/api_key.html")

START_DATE = "2010-01-01"  # Full 15-year history
PROJECT_ID = "cbi-v14"
DATASET_ID = "raw_intelligence"
TABLE_ID = "fred_economic"

# =============================================================================
# SERIES MAP - All key economic indicators for ZL forecasting
# =============================================================================

SERIES_MAP = {
    # --- Interest Rates ---
    "DFF": "fed_funds_rate",              # Federal Funds Rate
    "DGS10": "10y_treasury",              # 10-Year Treasury Constant Maturity
    "DGS2": "2y_treasury",                # 2-Year Treasury Constant Maturity
    "DGS30": "30y_treasury",              # 30-Year Treasury Constant Maturity (MES)
    "DGS3MO": "3m_treasury",              # 3-Month Treasury
    "T10Y2Y": "10y_2y_spread",            # 10Y-2Y Spread (yield curve)
    "T10Y3M": "10y_3m_spread",            # 10Y-3M Spread (yield curve)
    "T10YIE": "breakeven_inflation_10y",  # 10-Year Breakeven Inflation (MES real yields)
    
    # --- Volatility & Credit ---
    "VIXCLS": "vix_close",                # VIX Close (CBOE Volatility Index)
    "VXOCLS": "vxo_close",                # VXO Close (Old VIX, S&P 100)
    "VXVCLS": "vxv_close",                # VXV Close (3-Month VIX) - for term structure
    "BAMLC0A0CM": "us_corp_spread",       # US Corporate Bond Spread
    "BAMLH0A0HYM2": "high_yield_spread",  # High Yield Bond Spread
    "TEDRATE": "ted_spread",              # TED Spread (3-Month LIBOR - 3-Month Treasury)
    
    # --- Inflation & Economic Activity ---
    "CPIAUCSL": "cpi_all_urban",          # CPI All Urban Consumers
    "CPILFESL": "core_cpi",               # Core CPI (Less Food and Energy)
    "PCE": "pce",                         # Personal Consumption Expenditures
    "PCEPI": "pce_price_index",           # PCE Price Index
    "GDP": "gdp",                         # Gross Domestic Product
    "GDPC1": "real_gdp",                  # Real GDP
    "UNRATE": "unemployment_rate",        # Unemployment Rate
    "ICSA": "initial_claims",             # Initial Jobless Claims
    
    # --- Currency / Dollar Index ---
    "DTWEXBGS": "dollar_index_broad",     # Trade Weighted Dollar Index: Broad
    "DTWEXAFEGS": "dollar_index_afe",     # Trade Weighted Dollar Index: AFE
    "DTWEXEMEGS": "dollar_index_eme",     # Trade Weighted Dollar Index: EME
    "DEXBZUS": "usd_brl",                 # USD/BRL Exchange Rate
    "DEXCHUS": "usd_cny",                 # USD/CNY Exchange Rate
    "DEXJPUS": "usd_jpy",                 # USD/JPY Exchange Rate
    "DEXUSEU": "eur_usd",                 # EUR/USD Exchange Rate
    
    # --- Commodities (for cross-asset) ---
    "DCOILWTICO": "wti_crude",            # WTI Crude Oil Spot Price
    "DCOILBRENTEU": "brent_crude",        # Brent Crude Oil Spot Price
    "GASREGW": "gas_retail_weekly",       # Regular Gas Price
    "DHHNGSP": "natural_gas_henry_hub",   # Henry Hub Natural Gas Spot Price
    
    # --- Logistics & Shipping ---
    "BDILCY": "baltic_dry_index",         # Baltic Dry Index (shipping cost proxy)
    
    # --- Money Supply & Rates ---
    "M2SL": "m2_money_supply",            # M2 Money Supply
    "WALCL": "fed_balance_sheet",         # Fed Total Assets
    "FEDFUNDS": "fed_funds_effective",    # Federal Funds Effective Rate
    "NFCI": "financial_conditions_index", # Chicago Fed National Financial Conditions Index (MES)
    
    # --- Consumer & Business ---
    "UMCSENT": "consumer_sentiment",      # U Michigan Consumer Sentiment
    "RSAFS": "retail_sales",              # Retail Sales
    "INDPRO": "industrial_production",    # Industrial Production Index
    "PAYEMS": "nonfarm_payrolls",         # Total Nonfarm Payrolls
}

# =============================================================================
# MAIN COLLECTION FUNCTION
# =============================================================================

def collect_fred_data():
    """
    Collect all FRED series and load to BigQuery.
    Rate limited to 1 request per second per FRED API guidelines.
    """
    fred = Fred(api_key=API_KEY)
    frames = []
    errors = []
    
    print("=" * 70)
    print("FRED DATA COLLECTION")
    print("=" * 70)
    print(f"Start Date: {START_DATE}")
    print(f"Series Count: {len(SERIES_MAP)}")
    print(f"Target: {PROJECT_ID}.{DATASET_ID}.{TABLE_ID}")
    print("=" * 70)
    
    for i, (series_id, name) in enumerate(SERIES_MAP.items(), 1):
        try:
            print(f"[{i:02d}/{len(SERIES_MAP)}] Fetching {series_id} ({name})...", end=" ", flush=True)
            
            # Fetch series from FRED
            series = fred.get_series(series_id, observation_start=START_DATE)
            
            if series is None or len(series) == 0:
                print("⚠️  No data")
                continue
            
            # Convert to DataFrame
            df_s = series.to_frame(name="value")
            df_s.index.name = "date"
            df_s.reset_index(inplace=True)
            
            # Add metadata
            df_s["series_id"] = series_id
            df_s["series_name"] = name
            
            frames.append(df_s)
            print(f"✅ {len(df_s)} rows")
            
            # Rate limiting: 1 request per second
            time.sleep(1.1)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            errors.append((series_id, str(e)))
    
    # Combine all series
    if not frames:
        print("\n❌ No data collected!")
        return
    
    final_df = pd.concat(frames, ignore_index=True)
    
    # Clean up data
    final_df["date"] = pd.to_datetime(final_df["date"]).dt.date
    final_df["ingestion_ts"] = pd.Timestamp.now()
    
    # Remove any rows with null values
    before = len(final_df)
    final_df = final_df.dropna(subset=["value"])
    after = len(final_df)
    
    print("\n" + "=" * 70)
    print("DATA SUMMARY")
    print("=" * 70)
    print(f"Total rows: {after} (dropped {before - after} nulls)")
    print(f"Series collected: {final_df['series_id'].nunique()}")
    print(f"Date range: {final_df['date'].min()} to {final_df['date'].max()}")
    
    if errors:
        print(f"\n⚠️  Errors ({len(errors)}):")
        for series_id, error in errors:
            print(f"   - {series_id}: {error}")
    
    # Load to BigQuery
    dest = f"{DATASET_ID}.{TABLE_ID}"
    print(f"\n📤 Uploading to BigQuery ({dest})...")
    
    try:
        final_df.to_gbq(
            destination_table=dest,
            project_id=PROJECT_ID,
            if_exists="replace"  # Full reload for consistency
        )
        print("✅ Upload complete!")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        # Save locally as backup
        backup_path = f"fred_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        final_df.to_csv(backup_path, index=False)
        print(f"💾 Saved backup to {backup_path}")
    
    # Verification query
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        result = client.query(f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT series_id) as unique_series,
                MIN(date) as min_date,
                MAX(date) as max_date,
                COUNT(DISTINCT date) as unique_dates
            FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        """).to_dataframe()
        
        print(f"   Total rows: {result['total_rows'].iloc[0]}")
        print(f"   Unique series: {result['unique_series'].iloc[0]}")
        print(f"   Date range: {result['min_date'].iloc[0]} to {result['max_date'].iloc[0]}")
        print(f"   Unique dates: {result['unique_dates'].iloc[0]}")
    except Exception as e:
        print(f"   Verification query failed: {e}")
    
    print("\n✅ FRED DATA COLLECTION COMPLETE")


if __name__ == "__main__":
    collect_fred_data()

