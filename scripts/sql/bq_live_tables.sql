-- BigQuery table DDL for live futures OHLCV mirroring (1m) and rollups

-- 1) Base live 1m table (partitioned by date on ts_event; clustered by root,symbol)
CREATE SCHEMA IF NOT EXISTS `cbi-v14.market_data`;

CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.futures_ohlcv_1m_live` (
  ts_event TIMESTAMP,
  root STRING,
  symbol STRING,
  instrument_id INT64,
  publisher_id INT64,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  volume INT64
)
PARTITION BY DATE(ts_event)
CLUSTER BY root, symbol;

-- 2) 1h rollup (resample from 1m)
CREATE OR REPLACE TABLE `cbi-v14.market_data.futures_ohlcv_1h_live` AS
SELECT
  TIMESTAMP_TRUNC(ts_event, HOUR) AS ts_hour,
  root,
  symbol,
  ANY_VALUE(instrument_id) AS instrument_id,
  ANY_VALUE(publisher_id) AS publisher_id,
  ANY_VALUE(open IGNORE NULLS) KEEP FIRST OVER (PARTITION BY root,symbol,TIMESTAMP_TRUNC(ts_event,HOUR) ORDER BY ts_event) AS open,
  MAX(high) AS high,
  MIN(low) AS low,
  ANY_VALUE(close IGNORE NULLS) KEEP LAST OVER (PARTITION BY root,symbol,TIMESTAMP_TRUNC(ts_event,HOUR) ORDER BY ts_event) AS close,
  SUM(volume) AS volume
FROM `cbi-v14.market_data.futures_ohlcv_1m_live`
GROUP BY ts_hour, root, symbol;

-- 3) 1d rollup (resample from 1m)
CREATE OR REPLACE TABLE `cbi-v14.market_data.futures_ohlcv_1d_live` AS
SELECT
  TIMESTAMP_TRUNC(ts_event, DAY) AS ts_day,
  root,
  symbol,
  ANY_VALUE(instrument_id) AS instrument_id,
  ANY_VALUE(publisher_id) AS publisher_id,
  ANY_VALUE(open IGNORE NULLS) KEEP FIRST OVER (PARTITION BY root,symbol,TIMESTAMP_TRUNC(ts_event,DAY) ORDER BY ts_event) AS open,
  MAX(high) AS high,
  MIN(low) AS low,
  ANY_VALUE(close IGNORE NULLS) KEEP LAST OVER (PARTITION BY root,symbol,TIMESTAMP_TRUNC(ts_event,DAY) ORDER BY ts_event) AS close,
  SUM(volume) AS volume
FROM `cbi-v14.market_data.futures_ohlcv_1m_live`
GROUP BY ts_day, root, symbol;

