-- ============================================================
-- DATABENTO TABLE SCHEMAS FOR BIGQUERY
-- ============================================================
-- Run this ONCE to create all target tables for Databento data
-- Dataset: market_data
-- ============================================================

-- 1. OHLCV Tables (1s, 1m, 1h, 1d)
-- ============================================================

-- Daily OHLCV (already exists, but ensure schema)
CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_futures_ohlcv_1d` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    instrument_id INT64,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64,
    ts_event TIMESTAMP
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS(description='Databento daily OHLCV bars for futures');

-- Hourly OHLCV
CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_futures_ohlcv_1h` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    instrument_id INT64,
    ts_event TIMESTAMP,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS(description='Databento hourly OHLCV bars for futures');

-- Minute OHLCV (HEAVY symbols only)
CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_futures_ohlcv_1m` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    instrument_id INT64,
    ts_event TIMESTAMP,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS(description='Databento minute OHLCV bars for futures (MES/ZL only)');

-- Second OHLCV (HEAVY symbols only)
CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_futures_ohlcv_1s` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    instrument_id INT64,
    ts_event TIMESTAMP,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS(description='Databento second OHLCV bars for futures (MES/ZL only)');

-- 2. BBO Tables (Best Bid/Offer)
-- ============================================================

-- BBO 1s (HEAVY only)
CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_bbo_1s` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    instrument_id INT64,
    ts_event TIMESTAMP,
    bid_px FLOAT64,
    ask_px FLOAT64,
    bid_sz INT64,
    ask_sz INT64,
    bid_ct INT64,
    ask_ct INT64
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS(description='Databento 1-second BBO snapshots (MES/ZL only)');

-- BBO 1m
CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_bbo_1m` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    instrument_id INT64,
    ts_event TIMESTAMP,
    bid_px FLOAT64,
    ask_px FLOAT64,
    bid_sz INT64,
    ask_sz INT64,
    bid_ct INT64,
    ask_ct INT64
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS(description='Databento 1-minute BBO snapshots');

-- TBBO (Top of Book with BBO, HEAVY only)
CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_tbbo` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    instrument_id INT64,
    ts_event TIMESTAMP,
    action STRING,
    side STRING,
    price FLOAT64,
    size INT64,
    bid_px FLOAT64,
    ask_px FLOAT64,
    bid_sz INT64,
    ask_sz INT64
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS(description='Databento TBBO (top-of-book with BBO, MES/ZL only)');

-- 3. Depth Tables (MBP/MBO, HEAVY only)
-- ============================================================

-- MBP-1 (Market by Price, 1 level)
CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_mbp_1` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    instrument_id INT64,
    ts_event TIMESTAMP,
    action STRING,
    side STRING,
    price FLOAT64,
    size INT64,
    depth INT64,
    flags INT64
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS(description='Databento MBP-1 depth (MES/ZL only)');

-- MBP-10 (Market by Price, 10 levels)
CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_mbp_10` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    instrument_id INT64,
    ts_event TIMESTAMP,
    -- Level 1
    bid_px_1 FLOAT64, ask_px_1 FLOAT64, bid_sz_1 INT64, ask_sz_1 INT64,
    -- Level 2
    bid_px_2 FLOAT64, ask_px_2 FLOAT64, bid_sz_2 INT64, ask_sz_2 INT64,
    -- Level 3
    bid_px_3 FLOAT64, ask_px_3 FLOAT64, bid_sz_3 INT64, ask_sz_3 INT64,
    -- Level 4
    bid_px_4 FLOAT64, ask_px_4 FLOAT64, bid_sz_4 INT64, ask_sz_4 INT64,
    -- Level 5
    bid_px_5 FLOAT64, ask_px_5 FLOAT64, bid_sz_5 INT64, ask_sz_5 INT64,
    -- Level 6
    bid_px_6 FLOAT64, ask_px_6 FLOAT64, bid_sz_6 INT64, ask_sz_6 INT64,
    -- Level 7
    bid_px_7 FLOAT64, ask_px_7 FLOAT64, bid_sz_7 INT64, ask_sz_7 INT64,
    -- Level 8
    bid_px_8 FLOAT64, ask_px_8 FLOAT64, bid_sz_8 INT64, ask_sz_8 INT64,
    -- Level 9
    bid_px_9 FLOAT64, ask_px_9 FLOAT64, bid_sz_9 INT64, ask_sz_9 INT64,
    -- Level 10
    bid_px_10 FLOAT64, ask_px_10 FLOAT64, bid_sz_10 INT64, ask_sz_10 INT64
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS(description='Databento MBP-10 depth (MES/ZL only)');

-- MBO (Market by Order, HEAVY only)
CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_mbo` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    instrument_id INT64,
    ts_event TIMESTAMP,
    order_id INT64,
    action STRING,
    side STRING,
    price FLOAT64,
    size INT64,
    channel_id INT64,
    flags INT64
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS(description='Databento MBO order-level data (MES/ZL only)');

-- 4. Statistics Table
-- ============================================================

CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_stats` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    instrument_id INT64,
    ts_event TIMESTAMP,
    stat_type STRING,
    stat_value FLOAT64,
    open_interest INT64,
    settlement_price FLOAT64,
    trading_session_date DATE
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS(description='Databento daily statistics (OI, settle, volume)');

-- 5. FX Daily (already created via bq mk, included for completeness)
-- ============================================================

CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.fx_daily` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64
)
PARTITION BY date
CLUSTER BY symbol
OPTIONS(description='FX futures daily OHLCV from Databento');

-- 6. Options Tables (for ZL.OPT, ES.OPT, MES.OPT)
-- ============================================================

CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_options_ohlcv_1d` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    instrument_id INT64,
    underlying STRING,
    expiration DATE,
    strike FLOAT64,
    option_type STRING,  -- 'C' or 'P'
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64,
    open_interest INT64
)
PARTITION BY date
CLUSTER BY symbol, underlying
OPTIONS(description='Databento options daily OHLCV');

CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_options_stats` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    instrument_id INT64,
    underlying STRING,
    expiration DATE,
    strike FLOAT64,
    option_type STRING,
    implied_vol FLOAT64,
    delta FLOAT64,
    gamma FLOAT64,
    theta FLOAT64,
    vega FLOAT64,
    open_interest INT64,
    settlement_price FLOAT64
)
PARTITION BY date
CLUSTER BY symbol, underlying
OPTIONS(description='Databento options statistics and greeks');


