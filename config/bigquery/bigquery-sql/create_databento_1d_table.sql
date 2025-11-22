-- 📋 BEST PRACTICES: See `.cursorrules` and `docs/reference/BEST_PRACTICES_DRAFT.md` for mandatory best practices:
--    - No fake data, always check before creating, always audit after work
--    - us-central1 only, no costly resources without approval
--    - Research best practices, research quant finance modeling
--    - Always validate data quality, test queries, verify results

-- ============================================================================
-- RAW TABLE: databento_futures_ohlcv_1d
-- ============================================================================

CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_futures_ohlcv_1d` (
  data_date DATE NOT NULL,
  symbol STRING NOT NULL,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  volume INT64,
  settle FLOAT64,
  vwap FLOAT64,
  open_interest INT64,
  instrument_id STRING,
  exchange STRING,
  currency STRING,
  dataset STRING,
  load_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY data_date
CLUSTER BY symbol
OPTIONS (
  description='Daily OHLCV data from DataBento futures feed',
  location='us-central1'
);




