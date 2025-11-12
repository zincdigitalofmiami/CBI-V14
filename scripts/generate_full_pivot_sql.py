#!/usr/bin/env python3
"""
Generate SQL pivot for ALL 224 symbols with ALL indicators
"""

import sys
sys.path.append('/Users/zincdigital/CBI-V14/scripts')
from pull_224_driver_universe import SYMBOLS

# All technical indicators to pivot
INDICATORS = [
    'close', 'volume', 'rsi_14', 'macd_hist', 'bb_width', 'atr_14',
    'ma_7d', 'ma_30d', 'ma_50d', 'ma_200d', 'ema_12', 'ema_26',
    'stoch_k', 'stoch_d', 'williams_r', 'mfi_14', 'roc_10', 'momentum_10',
    'open_int', 'high_52w', 'low_52w', 'pct_from_high_52w', 'pct_from_low_52w',
    'vwap', 'obv', 'cmf', 'adx', 'plus_di', 'minus_di', 'cci_20'
]

print(f"Generating pivot SQL for {len(SYMBOLS)} symbols × {len(INDICATORS)} indicators = {len(SYMBOLS) * len(INDICATORS)} columns")

# Generate pivot statements
pivot_lines = []
for symbol, metadata in SYMBOLS.items():
    # Sanitize symbol for column names
    col_prefix = symbol.replace('=', '_').replace('-', '_').replace('^', '_').replace('.', '_').lower()
    
    for indicator in INDICATORS:
        col_name = f"{col_prefix}_{indicator}"
        pivot_lines.append(f"    MAX(IF(symbol = '{symbol}', {indicator}, NULL)) AS {col_name}")

# Write to file
with open('/tmp/full_224_pivot.sql', 'w') as f:
    f.write("-- AUTO-GENERATED PIVOT FOR 224 SYMBOLS\n")
    f.write(f"-- {len(SYMBOLS)} symbols × {len(INDICATORS)} indicators = {len(pivot_lines)} columns\n\n")
    f.write("SELECT\n")
    f.write("  date,\n")
    f.write(",\n".join(pivot_lines))
    f.write("\nFROM yahoo_raw")
    f.write("\nGROUP BY date")

print(f"✅ Generated pivot SQL with {len(pivot_lines)} columns")
print(f"📄 Saved to /tmp/full_224_pivot.sql")

# Also generate correlation pairs
print(f"\n🔄 Generating correlation pairs...")
correlation_windows = [7, 30, 90, 365]
corr_lines = []

# Top 20 most important pairs
key_pairs = [
    ('ZL=F', 'CL=F'), ('ZL=F', 'DXY'), ('ZL=F', 'VIX'),
    ('ZL=F', 'ZS=F'), ('ZL=F', 'ZC=F'), ('ZL=F', 'BZ=F'),
    ('CL=F', 'DXY'), ('CL=F', 'VIX'), ('DXY', 'VIX'),
    ('ZL=F', 'ADM'), ('ZL=F', 'BG'), ('ZL=F', 'SOYB')
]

for sym1, sym2 in key_pairs:
    col1 = sym1.replace('=', '_').replace('-', '_').lower() + '_close'
    col2 = sym2.replace('=', '_').replace('-', '_').lower() + '_close'
    
    for window in correlation_windows:
        corr_name = f"corr_{col1.split('_')[0]}_{col2.split('_')[0]}_{window}d"
        corr_lines.append(
            f"    CORR(y.{col1}, y.{col2}) OVER (ORDER BY y.date ROWS BETWEEN {window-1} PRECEDING AND CURRENT ROW) AS {corr_name}"
        )

print(f"✅ Generated {len(corr_lines)} correlation features")
print("📊 Ready for explosive training with ALL DATA!")

