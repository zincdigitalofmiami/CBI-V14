# Check BQ freshness

Run these checks in BigQuery before serious training:

```sql
-- ZL engine roots: daily Databento coverage
SELECT symbol, MIN(date) AS min_date, MAX(date) AS max_date, COUNT(*) AS rows
FROM `cbi-v14.market_data.databento_futures_ohlcv_1d`
WHERE symbol IN ('ZL','ZS','ZM','CL','HO')
GROUP BY symbol
ORDER BY symbol;

-- FRED macro key series (example)
SELECT series_id, MIN(date) AS min_date, MAX(date) AS max_date
FROM `cbi-v14.macro.fred_series`
WHERE series_id IN ('DFF','DGS10','DTWEXBGS','VIXCLS')
GROUP BY series_id
ORDER BY series_id;

-- Palm (once wired)
SELECT MIN(date) AS min_date, MAX(date) AS max_date
FROM `cbi-v14.macro.palm_price_daily`;
```

If `MAX(date)` is stale for any of these, fix ingestion first.

