"""
⚠️ CRITICAL: NO FAKE DATA ⚠️
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
"""

# Fibonacci feature import — Mac run_once.py
# Imports Fibonacci features from BigQuery and merges into local features DataFrame

from google.cloud import bigquery
import pandas as pd

bq = bigquery.Client(project="cbi-v14")

# Fetch Fibonacci levels
fib = bq.query("""
  SELECT 
    date, symbol,
    swing_low_price, swing_high_price, trend_direction, days_since_swing,
    retrace_236, retrace_382, retrace_50, retrace_618, retrace_786,
    ext_100, ext_1236, ext_1382, ext_1618, ext_200, ext_2618,
    current_price, swing_position_pct,
    price_near_618_retrace, price_near_1618_ext, price_near_any_major
  FROM `cbi-v14.features.fib_levels_daily`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date, symbol ORDER BY last_updated DESC) = 1
""").to_dataframe()

# Rename columns to feature naming convention (feat_fib_*)
fib = fib.rename(columns={
    # Swing context
    "swing_low_price": "feat_fib_swing_low",
    "swing_high_price": "feat_fib_swing_high",
    "trend_direction": "feat_fib_trend_direction",
    "days_since_swing": "feat_fib_days_since_swing",
    
    # Retracements
    "retrace_236": "feat_fib_retrace_236",
    "retrace_382": "feat_fib_retrace_382",
    "retrace_50": "feat_fib_retrace_50",
    "retrace_618": "feat_fib_retrace_618",
    "retrace_786": "feat_fib_retrace_786",
    
    # Extensions
    "ext_100": "feat_fib_ext_100",
    "ext_1236": "feat_fib_ext_1236",
    "ext_1382": "feat_fib_ext_1382",
    "ext_1618": "feat_fib_ext_1618",
    "ext_200": "feat_fib_ext_200",
    "ext_2618": "feat_fib_ext_2618",
    
    # Context
    "swing_position_pct": "feat_fib_swing_position_pct",
    
    # Signals
    "price_near_618_retrace": "feat_fib_near_618_retrace",
    "price_near_1618_ext": "feat_fib_near_1618_ext",
    "price_near_any_major": "feat_fib_near_any_major",
})

# Example usage: merge into features DataFrame
# features_df = features_df.merge(fib, on=["date", "symbol"], how="left")

print(f"Loaded {len(fib)} Fibonacci feature records")
print(f"Columns: {list(fib.columns)}")

