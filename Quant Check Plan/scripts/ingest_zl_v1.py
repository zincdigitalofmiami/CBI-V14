"""
ZL v1 Ingestion - Minimal Baseline
Reads Databento OHLCV, calculates basic TA, stamps regime, loads to BQ.

DATE HANDLING:
- BigQuery source: DATE type
- Pandas: datetime64[ns] or date object
- BigQuery target: DATE type (for partitioning)
- Ensure: pd.to_datetime() then .dt.date for DATE columns
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, date

# Config
PROJECT = 'cbi-v14'
SOURCE_TABLE = f'{PROJECT}.market_data.databento_futures_ohlcv_1d'
TARGET_TABLE = f'{PROJECT}.features.zl_daily_v1'
REGIME_TABLE = f'{PROJECT}.training.regime_lookup'

# Regime definitions with proper date objects
REGIMES = [
    ('pre_trade_war', date(2010, 1, 1), date(2018, 2, 28), 100),
    ('trade_war', date(2018, 3, 1), date(2019, 12, 31), 300),
    ('covid_crash', date(2020, 1, 1), date(2020, 5, 31), 200),
    ('covid_recovery', date(2020, 6, 1), date(2020, 12, 31), 200),
    ('inflation', date(2021, 1, 1), date(2022, 12, 31), 300),
    ('trump_anticipation', date(2023, 1, 1), date(2025, 1, 19), 400),
    ('trump_term', date(2025, 1, 20), date(2029, 12, 31), 600),
]

def get_regime(d):
    """
    Lookup regime for a given date.
    
    Args:
        d: Can be datetime64, Timestamp, date, or string
    Returns:
        (regime_name, weight) tuple
    """
    # Normalize to date object for comparison
    if isinstance(d, pd.Timestamp):
        d = d.date()
    elif isinstance(d, str):
        d = datetime.strptime(d, '%Y-%m-%d').date()
    elif hasattr(d, 'date') and callable(d.date):
        d = d.date()
    
    for name, start, end, weight in REGIMES:
        if start <= d <= end:
            return name, weight
    return 'unknown', 100

def calculate_ta(df):
    """Calculate basic technical indicators."""
    df = df.sort_values('date').copy()
    
    # Returns
    df['return_1d'] = df['close'].pct_change(1)
    df['return_5d'] = df['close'].pct_change(5)
    df['return_21d'] = df['close'].pct_change(21)
    
    # Moving averages
    df['ma_5'] = df['close'].rolling(5).mean()
    df['ma_21'] = df['close'].rolling(21).mean()
    df['ma_63'] = df['close'].rolling(63).mean()
    
    # Volatility (21-day realized)
    df['volatility_21d'] = df['return_1d'].rolling(21).std() * np.sqrt(252)
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    return df

def main():
    client = bigquery.Client(project=PROJECT)
    
    # 1. Read Databento ZL data
    print("=" * 60)
    print("ZL v1 INGESTION")
    print("=" * 60)
    print("\n1. Reading Databento ZL data...")
    query = f"""
        SELECT date, open, high, low, close, volume
        FROM `{SOURCE_TABLE}`
        WHERE symbol = 'ZL'
        ORDER BY date
    """
    df = client.query(query).to_dataframe()
    print(f"   Loaded {len(df)} rows")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Date dtype: {df['date'].dtype}")
    
    # 2. Ensure date column is proper datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # 3. Calculate TA
    print("\n2. Calculating technical indicators...")
    df = calculate_ta(df)
    
    # 4. Stamp regime (vectorized for speed)
    print("\n3. Stamping regimes...")
    regime_data = df['date'].apply(get_regime)
    df['regime_name'] = regime_data.apply(lambda x: x[0])
    df['regime_weight'] = regime_data.apply(lambda x: x[1])
    
    # 5. Rename and prepare for BQ
    df = df.rename(columns={'date': 'trade_date'})
    df['symbol'] = 'ZL'
    df['ingestion_ts'] = datetime.utcnow()
    
    # 6. Convert trade_date to DATE type for BQ partitioning
    # BigQuery expects date objects, not datetime64
    df['trade_date'] = df['trade_date'].dt.date
    
    # 7. Select only columns we need (in correct order)
    cols = [
        'trade_date', 'symbol', 'open', 'high', 'low', 'close', 'volume',
        'return_1d', 'return_5d', 'return_21d',
        'ma_5', 'ma_21', 'ma_63',
        'volatility_21d', 'rsi_14',
        'regime_name', 'regime_weight', 'ingestion_ts'
    ]
    df = df[cols]
    
    # 8. Drop rows with NaN in critical columns (first ~63 rows)
    before = len(df)
    df = df.dropna(subset=['ma_63', 'volatility_21d', 'rsi_14'])
    print(f"   Dropped {before - len(df)} rows with NaN (warmup period)")
    print(f"   Final row count: {len(df)}")
    
    # 9. Validate before load
    print("\n4. Validation:")
    print(f"   NULL regime_name: {df['regime_name'].isna().sum()}")
    print(f"   NULL close: {df['close'].isna().sum()}")
    print(f"   Unknown regimes: {(df['regime_name'] == 'unknown').sum()}")
    print(f"\n   Regime distribution:")
    print(df['regime_name'].value_counts().to_string())
    
    # 10. Load to BigQuery
    print(f"\n5. Loading {len(df)} rows to {TARGET_TABLE}...")
    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_TRUNCATE',  # Replace for v0
    )
    job = client.load_table_from_dataframe(df, TARGET_TABLE, job_config=job_config)
    job.result()
    print("   Done!")
    
    # 11. Verify
    result = client.query(f"""
        SELECT 
            COUNT(*) as total_rows,
            COUNTIF(regime_name IS NULL) as null_regimes,
            COUNTIF(close IS NULL) as null_prices,
            MIN(trade_date) as min_date,
            MAX(trade_date) as max_date
        FROM `{TARGET_TABLE}`
    """).to_dataframe()
    
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    print(f"   Total rows: {result['total_rows'].iloc[0]}")
    print(f"   NULL regimes: {result['null_regimes'].iloc[0]}")
    print(f"   NULL prices: {result['null_prices'].iloc[0]}")
    print(f"   Date range: {result['min_date'].iloc[0]} to {result['max_date'].iloc[0]}")
    print("\n✅ INGESTION COMPLETE")

if __name__ == '__main__':
    main()





