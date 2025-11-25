---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# FIBONACCI RETRACEMENTS + EXTENSIONS — Databento-Based

**Status:** Production-ready, Databento-integrated  
**Purpose:** Calculate daily Fibonacci retracements and extensions for all symbols  
**Source:** `market_data.databento_futures_ohlcv_1d` (Databento daily OHLCV)

---

## ARCHITECTURE

### A1) BigQuery Schema

**Table:** `features.fib_levels_daily`
- One record per symbol per day
- Includes swing detection, retracements, extensions
- Near-level boolean flags for trading signals

**View:** Uses `curated.vw_ohlcv_daily` (defined in `pivot_math_daily.sql`)
- Source: `market_data.databento_futures_ohlcv_1d`
- **Updated:** Uses Databento directly (no Yahoo/Alpha fallback)

### A2) Cloud Function (Gen-2)

**File:** `scripts/features/cloud_function_fibonacci_calculator.py`
- **Updated:** Uses Databento view instead of Yahoo/Alpha
- Runs daily via Cloud Scheduler
- Zigzag algorithm for swing detection
- Calculates all Fibonacci levels

**Deploy:**
```bash
gcloud functions deploy compute_fibonacci \
  --gen2 --region=us-central1 --runtime=python311 --entry-point=handler \
  --memory=512Mi --timeout=120 --trigger-http --no-allow-unauthenticated \
  --set-env-vars="BQ_PROJECT=cbi-v14,SRC_VIEW=cbi-v14.curated.vw_ohlcv_daily,DST_TABLE=cbi-v14.features.fib_levels_daily"
```

**Schedule:** Daily at 05:45 UTC (after market close, after pivot calculation)

### A3) Mac Feature Import

**File:** `scripts/features/fibonacci_feature_import.py`
- Imports Fibonacci features from BigQuery
- Renames to `feat_fib_*` convention
- Merges into local features DataFrame

---

## FIBONACCI FORMULAS

### Retracements (Inside Swing)

For **uptrend** (swing low → swing high):
```
retrace_236 = swing_high - 0.236 × range
retrace_382 = swing_high - 0.382 × range
retrace_50  = swing_high - 0.500 × range
retrace_618 = swing_high - 0.618 × range
retrace_786 = swing_high - 0.786 × range
```

For **downtrend** (swing high → swing low):
```
retrace_236 = swing_low + 0.236 × range
retrace_382 = swing_low + 0.382 × range
retrace_50  = swing_low + 0.500 × range
retrace_618 = swing_low + 0.618 × range
retrace_786 = swing_low + 0.786 × range
```

Where `range = swing_high - swing_low`

### Extensions (Beyond Swing)

For **uptrend**:
```
ext_100  = swing_high (100% extension = no extension)
ext_1236 = swing_high + 0.236 × range
ext_1382 = swing_high + 0.382 × range
ext_1618 = swing_high + 0.618 × range
ext_200  = swing_high + 1.000 × range
ext_2618 = swing_high + 1.618 × range
```

For **downtrend**:
```
ext_100  = swing_low (100% extension = no extension)
ext_1236 = swing_low - 0.236 × range
ext_1382 = swing_low - 0.382 × range
ext_1618 = swing_low - 0.618 × range
ext_200  = swing_low - 1.000 × range
ext_2618 = swing_low - 1.618 × range
```

---

## ZIGZAG ALGORITHM

**Purpose:** Detect swing highs and lows using percentage-based pivots

**Parameters:**
- `ZIGZAG_PCT`: Minimum percentage move to register a pivot (default 6%)
- `SWING_WINDOW`: Number of trading days to look back (default 126)

**Algorithm:**
1. Start from first price point
2. Track direction (up/down/unknown)
3. When price moves ≥ `ZIGZAG_PCT` in current direction, register pivot
4. Switch direction and continue
5. Return last two pivots (swing low and swing high)

**Fallback:** If < 2 pivots found, use absolute min/max in lookback window

---

## FEATURE NAMING

All features use `feat_fib_*` prefix:

| Original Column | Feature Name | Description |
|----------------|--------------|-------------|
| `swing_low_price` | `feat_fib_swing_low` | Swing low price |
| `swing_high_price` | `feat_fib_swing_high` | Swing high price |
| `trend_direction` | `feat_fib_trend_direction` | 'up' or 'down' |
| `days_since_swing` | `feat_fib_days_since_swing` | Days since swing |
| `retrace_236` | `feat_fib_retrace_236` | 23.6% retracement level |
| `retrace_382` | `feat_fib_retrace_382` | 38.2% retracement level |
| `retrace_50` | `feat_fib_retrace_50` | 50% retracement level |
| `retrace_618` | `feat_fib_retrace_618` | 61.8% retracement level |
| `retrace_786` | `feat_fib_retrace_786` | 78.6% retracement level |
| `ext_100` | `feat_fib_ext_100` | 100% extension (swing high/low) |
| `ext_1236` | `feat_fib_ext_1236` | 123.6% extension |
| `ext_1382` | `feat_fib_ext_1382` | 138.2% extension |
| `ext_1618` | `feat_fib_ext_1618` | 161.8% extension (golden ratio) |
| `ext_200` | `feat_fib_ext_200` | 200% extension |
| `ext_2618` | `feat_fib_ext_2618` | 261.8% extension |
| `swing_position_pct` | `feat_fib_swing_position_pct` | Current price position in swing (0-100%) |
| `price_near_618_retrace` | `feat_fib_near_618_retrace` | Boolean: price near 61.8% retracement |
| `price_near_1618_ext` | `feat_fib_near_1618_ext` | Boolean: price near 161.8% extension |
| `price_near_any_major` | `feat_fib_near_any_major` | Boolean: price near any major level (38.2, 50, 61.8, 100, 161.8) |

---

## NEAR-LEVEL TOLERANCES

**ZL=F (Soybean Oil):**
- 61.8% retracement: ±0.8¢ absolute
- 161.8% extension: ±1.2¢ absolute
- Other levels: ±1.0% of price

**All Other Symbols:**
- All levels: ±1.0% of price

---

## CHANGES FROM YAHOO/ALPHA VERSION

1. **View Source:** Changed from `features.master_features` (Yahoo/Alpha COALESCE) to `market_data.databento_futures_ohlcv_1d` directly via `curated.vw_ohlcv_daily`
2. **Column Names:** No prefix needed (Databento columns are `open`, `high`, `low`, `close`, `volume`)
3. **Symbol Support:** Added `MES=F`, `ZS=F`, `ZM=F` to default symbols list
4. **Data Quality:** Uses `QUALIFY ROW_NUMBER()` to handle duplicate timestamps

---

## USAGE

### In Training Pipeline

```python
from scripts.features.fibonacci_feature_import import fib

# Merge Fibonacci features into features DataFrame
features_df = features_df.merge(fib, on=["date", "symbol"], how="left")
```

### In BigQuery Queries

```sql
SELECT 
  f.*,
  m.*
FROM `cbi-v14.features.fib_levels_daily` f
LEFT JOIN `cbi-v14.features.master_features` m
  ON f.date = m.date AND f.symbol = m.symbol
WHERE f.symbol = 'ZL=F'
  AND f.price_near_618_retrace = TRUE
ORDER BY f.date DESC
```

### In MES Trading Cockpit

Fibonacci levels are used for:
- **Main Chart:** Auto-detected fib pullbacks (0.236-0.786) + extensions (1.272-2.618) with live tap probabilities
- **Context Charts:** Full fib grid from major swing high/low
- **Right Rail:** Live Fibonacci target table with probabilities

---

## INITIAL FEATURE IMPORTANCE (Seed Order)

Based on ZL/FCPO/USDBRL commodity experiments (2020–2025), practical starting order:

1. `feat_fib_near_618_retrace` - Price near 61.8% retracement (most predictive)
2. `feat_fib_near_1618_ext` - Price near 161.8% extension
3. `feat_fib_swing_position_pct` - Position within swing range
4. `feat_fib_near_any_major` - Near any major level
5. `feat_fib_retrace_618` - 61.8% retracement level (distance)
6. `feat_fib_ext_1618` - 161.8% extension level (distance)
7. `feat_fib_days_since_swing` - Age of current swing
8. `feat_fib_trend_direction` - Uptrend/downtrend
9. `feat_fib_retrace_382` - 38.2% retracement level
10. `feat_fib_retrace_50` - 50% retracement level
11. `feat_fib_ext_200` - 200% extension level
12. `feat_fib_retrace_786` - 78.6% retracement level
13. `feat_fib_ext_2618` - 261.8% extension level
14. `feat_fib_retrace_236` - 23.6% retracement level
15. `feat_fib_ext_1236` - 123.6% extension level
16. `feat_fib_ext_1382` - 138.2% extension level

**Note:** Training pipeline should recompute and persist true SHAP ranks on first run.

---

**Last Updated:** November 19, 2025  
**Status:** Production-ready, Databento-integrated  
**Reference:** Pure Fibonacci mathematics with no visual components

