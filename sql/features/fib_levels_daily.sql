---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

-- ============================================================================
-- FIBONACCI RETRACEMENTS + EXTENSIONS (Databento-based)
-- ============================================================================
-- Purpose: Calculate daily Fibonacci retracements and extensions for all symbols
-- Source: market_data.databento_futures_ohlcv_1d (Databento daily OHLCV)
-- Output: features.fib_levels_daily (one record per symbol per day)
-- ============================================================================

-- A1) Fibonacci levels table (daily row per symbol)
CREATE TABLE IF NOT EXISTS `cbi-v14.features.fib_levels_daily`
(
  date DATE NOT NULL,
  symbol STRING NOT NULL,

  -- Swing detection context
  swing_date_low  DATE,
  swing_date_high DATE,
  swing_low_price  FLOAT64,
  swing_high_price FLOAT64,
  trend_direction STRING,           -- 'up' or 'down'
  days_since_swing INT64,

  -- Retracements (inside swing)
  retrace_236 FLOAT64,
  retrace_382 FLOAT64,
  retrace_50  FLOAT64,
  retrace_618 FLOAT64,
  retrace_786 FLOAT64,

  -- Extensions (beyond swing, along trend)
  ext_100   FLOAT64,
  ext_1236  FLOAT64,
  ext_1382  FLOAT64,
  ext_1618  FLOAT64,
  ext_200   FLOAT64,
  ext_2618  FLOAT64,

  -- Context
  current_price  FLOAT64,
  swing_position_pct FLOAT64,       -- 0% = low, 100% = high, >100% = extension

  -- Near‑level boolean flags (ZL thresholds in ¢, generic elsewhere = 1% band)
  price_near_618_retrace BOOL,
  price_near_1618_ext   BOOL,
  price_near_any_major  BOOL,       -- (38.2, 50, 61.8, 100, 161.8)

  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS (
  description='Daily Fibonacci retracements and extensions for all symbols (Databento-based)'
);

-- Note: Uses curated.vw_ohlcv_daily view (already defined in pivot_math_daily.sql)
-- which sources from market_data.databento_futures_ohlcv_1d

