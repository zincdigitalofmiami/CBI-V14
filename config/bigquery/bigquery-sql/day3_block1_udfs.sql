-- 📋 BEST PRACTICES: See `.cursorrules` and `docs/reference/BEST_PRACTICES_DRAFT.md` for mandatory best practices:
--    - No fake data, always check before creating, always audit after work
--    - us-central1 only, no costly resources without approval
--    - Research best practices, research quant finance modeling
--    - Always validate data quality, test queries, verify results

-- 🛠️ BLOCK 1: Utility Functions (UDFs)
-- Purpose: Enables MACD and EMA calculations inside BigQuery views.

CREATE SCHEMA IF NOT EXISTS utils
OPTIONS (location='us-central1', description='Utility functions and UDFs');

-- 1. EMA Helper
CREATE OR REPLACE FUNCTION utils.ema(values ARRAY<FLOAT64>, period INT64) AS ((
  SELECT IFNULL((
     SELECT
       SUM(val * POW(2.0 / (period + 1), idx)) / SUM(POW(2.0 / (period + 1), idx))
       FROM UNNEST(values) AS val WITH OFFSET AS idx
     ), NULL)
));

-- 2. MACD Calculator (Full Struct Return)
CREATE OR REPLACE FUNCTION utils.macd_full(vals ARRAY<FLOAT64>) AS ((
  WITH mac AS (
     SELECT
       utils.ema(vals, 12) AS ema12,
       utils.ema(vals, 26) AS ema26
  )
  SELECT STRUCT(
     ema12 - ema26 AS macd_line,
     utils.ema([ema12 - ema26], 9) AS macd_signal,
     (ema12 - ema26) - utils.ema([ema12 - ema26], 9) AS macd_hist
  )
  FROM mac
));

