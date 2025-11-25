---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

-- ============================================================================
-- PURE PIVOT POINT MATHEMATICS (Databento-based)
-- ============================================================================
-- Purpose: Calculate daily/weekly/monthly/quarterly pivot points for all symbols
-- Source: market_data.databento_futures_ohlcv_1d (Databento daily OHLCV)
-- Output: features.pivot_math_daily (one record per symbol per day)
-- ============================================================================

-- B1) Helper view: Curated OHLCV from Databento
-- Uses Databento daily table directly (cleanest source)
CREATE OR REPLACE VIEW `cbi-v14.curated.vw_ohlcv_daily` AS
SELECT
  date,
  symbol,
  open,
  high,
  low,
  close,
  volume
FROM `cbi-v14.market_data.databento_futures_ohlcv_1d`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 5 YEAR)  -- Last 5 years
QUALIFY ROW_NUMBER() OVER (PARTITION BY date, symbol ORDER BY collection_timestamp DESC) = 1;

-- B2) Pivot math store (one daily record per symbol, includes weekly/monthly context)
CREATE TABLE IF NOT EXISTS `cbi-v14.features.pivot_math_daily`
(
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  
  -- Daily pivots (using prior session's H, L, C)
  P  FLOAT64, R1 FLOAT64, S1 FLOAT64, R2 FLOAT64, S2 FLOAT64, 
  R3 FLOAT64, S3 FLOAT64, R4 FLOAT64, S4 FLOAT64,
  M1 FLOAT64, M2 FLOAT64, M3 FLOAT64, M4 FLOAT64, 
  M5 FLOAT64, M6 FLOAT64, M7 FLOAT64, M8 FLOAT64,
  
  -- Weekly pivots (completed prior week, Mon–Sun)
  WP FLOAT64, WR1 FLOAT64, WS1 FLOAT64, WR2 FLOAT64, WS2 FLOAT64, 
  WR3 FLOAT64, WS3 FLOAT64,
  
  -- Monthly pivots (completed prior month)
  MP FLOAT64, MR1 FLOAT64, MS1 FLOAT64, MR2 FLOAT64, MS2 FLOAT64, 
  MR3 FLOAT64, MS3 FLOAT64,
  
  -- Pure math features (units = instrument price units; *_cents populated for ZL only)
  current_price FLOAT64,
  distance_to_P  FLOAT64, distance_to_R1 FLOAT64, distance_to_S1 FLOAT64,
  distance_to_R2 FLOAT64, distance_to_S2 FLOAT64, distance_to_R3 FLOAT64, distance_to_S3 FLOAT64,
  distance_to_nearest_pivot FLOAT64, 
  nearest_pivot_type STRING,
  
  price_above_P BOOL, 
  price_between_R1_R2 BOOL, 
  price_between_S1_P BOOL,
  
  weekly_pivot_distance FLOAT64, 
  monthly_pivot_distance FLOAT64,
  
  pivot_confluence_count INT64,            -- within ±1.0¢ of current price (ZL only; NULL otherwise)
  pivot_zone_strength INT64,               -- 1..5
  
  -- High-probability signals
  price_rejected_R1_twice BOOL,
  price_bouncing_off_S1 BOOL,
  price_stuck_between_R1_S1_for_3_days BOOL,
  weekly_pivot_flip BOOL,
  pivot_confluence_3_or_higher BOOL,
  
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS (
  description='Daily pivot point mathematics for all symbols (Databento-based)'
);

