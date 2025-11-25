# Universal Calculator Standard (v1.0)

## Core Principles

1. **Source of Truth:** BigQuery `features` tables are the only valid input for training.

2. **Time Travel:** All calculations look backward only (lag/rolling windows). No forward-looking fields in features.

3. **Null Handling:**
   - `SAFE_DIVIDE` for all ratios.
   - `COALESCE(x, 0)` for volume/counts.
   - Drop rows with NULL targets in the training view, NOT in the feature table.

---

## Approved Formulas

| Metric | Formula (Python/Pandas) | Formula (BigQuery SQL) |
|:-------|:------------------------|:-----------------------|
| Returns | `pct_change(N)` | `SAFE_DIVIDE(close - LAG(close, N), LAG(close, N))` |
| Log return | `np.log(price / price.shift(N))` | `LN(close / NULLIF(LAG(close,N),0))` |
| Volatility | `rolling(21).std() * np.sqrt(252)` | `STDDEV_SAMP(return_1d) OVER (ROWS 20 PRECEDING) * SQRT(252)` |
| RSI (14) | Wilder's smoothing (Python UDF preferred) | (Use Python; SQL UDF/recursive CTE only if needed) |
| MA | `rolling(N).mean()` | `AVG(close) OVER (ROWS N-1 PRECEDING)` |
| Target | `price.shift(-N) / price - 1` | `SAFE_DIVIDE(LEAD(close, N) - close, NULLIF(close,0))` |
| Momentum | `(price - price.shift(N)) / price.shift(N)` | `SAFE_DIVIDE(close - LAG(close, N), LAG(close, N))` |
| ATR | `rolling(14).mean(tr)` | `AVG(true_range) OVER (ROWS 13 PRECEDING)` |

---

## Safe Division Pattern

### BigQuery SQL
```sql
-- Always use SAFE_DIVIDE for ratios
SAFE_DIVIDE(numerator, denominator)

-- Or with NULLIF for legacy compatibility
numerator / NULLIF(denominator, 0)
```

### Python/Pandas
```python
# Use numpy where for safe division
import numpy as np

def safe_divide(a, b, default=0):
    return np.where(b != 0, a / b, default)

# Or pandas built-in
df['ratio'] = df['numerator'].div(df['denominator'].replace(0, np.nan))
```

---

## Null Handling Standards

### Feature Tables (BigQuery)
```sql
-- Use COALESCE for counts and volumes
COALESCE(volume, 0) AS volume,
COALESCE(trade_count, 0) AS trade_count,

-- Keep NULLs for prices (don't invent data)
close,  -- NULL if missing
high,   -- NULL if missing

-- Forward-fill sparse data (e.g., FRED weekly → daily)
LAST_VALUE(value IGNORE NULLS) OVER (
    PARTITION BY series_id 
    ORDER BY date
) AS value_filled
```

### Training Views (BigQuery)
```sql
-- Drop rows with NULL targets in training view only
SELECT *
FROM features.zl_daily_v1
WHERE return_1m_fwd IS NOT NULL
  AND price IS NOT NULL
```

---

## Backward-Only Calculations

### ALLOWED in Feature Tables
```sql
-- LAG (look backward)
LAG(close, 1) OVER (ORDER BY date) AS close_prev

-- Rolling windows (backward)
AVG(close) OVER (ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) AS ma_21

-- Historical volatility
STDDEV_SAMP(return_1d) OVER (ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) AS vol_21d
```

### NOT ALLOWED in Feature Tables
```sql
-- LEAD (forward-looking) - ONLY in training views for targets
LEAD(close, 21) OVER (ORDER BY date)  -- ❌ NOT in features

-- Future knowledge
AVG(close) OVER (ORDER BY date ROWS BETWEEN CURRENT ROW AND 20 FOLLOWING)  -- ❌ NEVER
```

---

## Technical Indicator Calculations

### Moving Averages (Python)
```python
def calculate_moving_averages(df, windows=[5, 10, 21, 50, 200]):
    for w in windows:
        df[f'ma_{w}'] = df['close'].rolling(window=w).mean()
    return df
```

### Moving Averages (BigQuery)
```sql
AVG(close) OVER (ORDER BY date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS ma_5,
AVG(close) OVER (ORDER BY date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) AS ma_10,
AVG(close) OVER (ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) AS ma_21,
AVG(close) OVER (ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS ma_50,
AVG(close) OVER (ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS ma_200
```

### RSI (Python - Wilder's Smoothing)
```python
def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    
    # Wilder's smoothing (EMA with alpha = 1/period)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    return df
```

### Volatility (Annualized)
```python
# Python
df['vol_21d'] = df['return_1d'].rolling(21).std() * np.sqrt(252)
```

```sql
-- BigQuery
STDDEV_SAMP(return_1d) OVER (ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) * SQRT(252) AS vol_21d
```

---

## Cross-Asset Feature Calculations

### Crush Margin (BigQuery)
```sql
-- Board crush formula: (ZM * 11) + (ZL * 11) - ZS
-- ZM: Soybean Meal ($ per short ton → $ per bushel: /2000 * 48)
-- ZL: Soybean Oil (cents per pound → $ per bushel: /100 * 11)
-- ZS: Soybeans (cents per bushel → $ per bushel: /100)

SELECT
    date,
    SAFE_DIVIDE(soymeal_price * 48, 2000) * 11 +
    SAFE_DIVIDE(soyoil_price, 100) * 11 -
    SAFE_DIVIDE(soybean_price, 100) AS board_crush_margin
FROM prices
```

### Correlation Features (BigQuery)
```sql
-- Rolling 60-day correlation
WITH daily_returns AS (
    SELECT
        date,
        symbol,
        SAFE_DIVIDE(close - LAG(close, 1) OVER (PARTITION BY symbol ORDER BY date),
                    LAG(close, 1) OVER (PARTITION BY symbol ORDER BY date)) AS return_1d
    FROM market_data.databento_futures_ohlcv_1d
)
SELECT
    a.date,
    CORR(a.return_1d, b.return_1d) OVER (
        ORDER BY a.date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW
    ) AS corr_zl_cl_60d
FROM daily_returns a
JOIN daily_returns b ON a.date = b.date
WHERE a.symbol = 'ZL' AND b.symbol = 'CL'
```

---

## Target Variable Calculations (Training Views ONLY)

### Forward Returns
```sql
-- In training views ONLY (not features tables)
CREATE VIEW training.vw_zl_1m_v1 AS
SELECT
    f.*,
    -- Target: 21-day forward return
    SAFE_DIVIDE(
        LEAD(close, 21) OVER (ORDER BY trade_date) - close,
        NULLIF(close, 0)
    ) AS return_1m_fwd,
    -- Direction target
    CASE 
        WHEN LEAD(close, 21) OVER (ORDER BY trade_date) > close THEN 1 
        ELSE 0 
    END AS direction_1m_fwd
FROM features.zl_daily_v1 f
WHERE return_1m_fwd IS NOT NULL  -- Drop incomplete targets
```

---

## Date Handling Standards

### BigQuery
```sql
-- Always use DATE type for trade_date
CAST(timestamp AS DATE) AS trade_date

-- Partition by DATE
PARTITION BY trade_date

-- Date literals
WHERE trade_date >= DATE '2010-01-01'
```

### Python
```python
# Convert to date for BigQuery compatibility
df['trade_date'] = pd.to_datetime(df['date']).dt.date

# Ensure proper type for to_gbq
df['trade_date'] = pd.to_datetime(df['trade_date'])
```

---

## Validation Checklist

Before deploying any calculator:

- [ ] All ratios use `SAFE_DIVIDE` or `NULLIF`
- [ ] All counts/volumes use `COALESCE(x, 0)`
- [ ] No `LEAD()` in feature tables (only training views)
- [ ] All rolling windows are backward-only
- [ ] DATE types are consistent
- [ ] Targets are dropped in views, not features
- [ ] Source is `features.*` tables, not raw

---

## Files Following This Standard

| File | Type | Status |
|------|------|--------|
| `Quant Check Plan/scripts/ingest_zl_v1.py` | Python | Compliant |
| `bigquery-sql/CALCULATE_ADVANCED_BIOFUEL_FEATURES.sql` | SQL | Needs audit |
| `bigquery-sql/RECALCULATE_TECHNICAL_INDICATORS.sql` | SQL | Needs audit |
| `training.vw_zl_1m_v1` | BQ View | Compliant |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-24 | Initial standard |

