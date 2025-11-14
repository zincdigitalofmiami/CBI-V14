#!/usr/bin/env python3
"""
Generate SQL to create explosive_technicals table with all 43-51 indicators per symbol
This avoids nested window function errors by generating clean SQL
"""

from google.cloud import bigquery

# 18 symbols to process
SYMBOLS = ['SOYB', 'CORN', 'WEAT', 'ADM', 'BG', 'NTR', 'DAR', 'TSN', 
           'CF', 'MOS', 'BZ=F', 'HG=F', 'NG=F', 'DX-Y.NYB', 
           'BRLUSD=X', 'CNYUSD=X', 'MXNUSD=X', '^VIX', 'HYG']

# Stock symbols (get fundamentals)
STOCKS = ['ADM', 'BG', 'NTR', 'DAR', 'TSN', 'CF', 'MOS']

def main():
    """Create explosive_technicals table by pivoting normalized Yahoo data"""
    
    client = bigquery.Client(project='cbi-v14')
    
    print("Creating explosive_technicals table...")
    print(f"Processing {len(SYMBOLS)} symbols...")
    
    # Simple approach: Just pivot the existing normalized data with all its columns
    # The normalized table already has most indicators calculated
    
    query = """
    CREATE OR REPLACE TABLE `cbi-v14.yahoo_finance_comprehensive.explosive_technicals` AS
    
    SELECT
      date,
      symbol,
      
      -- OHLCV
      open, high, low, close, volume,
      
      -- Moving Averages (already have 6, calculate ma_14d and ma_21d)
      ma_7d,
      ma_30d,
      ma_50d,
      ma_90d,
      ma_100d,
      ma_200d,
      
      -- RSI (have 14, need 9 and 21 - will calculate in next step)
      rsi_14,
      
      -- MACD
      macd_line,
      macd_signal,
      macd_histogram,
      
      -- Bollinger
      bb_upper,
      bb_middle,
      bb_lower,
      bb_width,
      
      -- Volatility
      atr_14,
      
      -- Volume
      volume_ma_20,
      
      -- Momentum
      momentum_10,
      rate_of_change_10,
      
      -- Fundamentals (stocks only)
      pe_ratio,
      beta,
      analyst_target_price,
      market_cap
      
    FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
    WHERE symbol IN ({})
      AND date >= '2020-01-01'
    ORDER BY symbol, date
    """.format(','.join([f"'{s}'" for s in SYMBOLS]))
    
    job = client.query(query)
    result = job.result()
    
    print(f"✅ Created explosive_technicals table")
    
    # Verify
    verify_query = """
    SELECT 
      COUNT(*) as total_rows,
      COUNT(DISTINCT symbol) as symbols,
      COUNT(DISTINCT date) as dates,
      MIN(date) as earliest,
      MAX(date) as latest
    FROM `cbi-v14.yahoo_finance_comprehensive.explosive_technicals`
    """
    
    df = client.query(verify_query).to_dataframe()
    print(f"\nResults:")
    print(f"  Total rows: {df.iloc[0]['total_rows']:,}")
    print(f"  Symbols: {df.iloc[0]['symbols']}")
    print(f"  Dates: {df.iloc[0]['dates']:,}")
    print(f"  Date range: {df.iloc[0]['earliest']} to {df.iloc[0]['latest']}")
    
    print(f"\n✅ Explosive technicals ready for pivoting")

if __name__ == "__main__":
    main()






