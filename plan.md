CBI-V14 Plan (Single Source of Truth)

Ground rules
- BigQuery ML only for training/forecasting. API is a thin wrapper.
- Protect working ZL forecast and endpoints at all times.
- Prefer local/offline collection to reduce BQ costs; batch loads via safe_load_to_bigquery.
- One canonical table per commodity; no mixed tables.

Today’s progress (EOD snapshot)
- Views added/verified:
  - vw_economic_daily, vw_news_intel_daily, vw_social_daily, vw_ice_trump_daily, vw_shipping_daily
  - vw_brazil_precip_daily (from local NOAA-ingested `weather_data`)
  - Drafted vw_zl_features_daily_all with explicit JOINs to avoid USING(date) ambiguity
- Ingestion inventory confirmed present and wired to `safe_load_to_bigquery`:
  - multi_source_news.py, economic_intelligence.py, social_intelligence.py
  - shipping_intelligence.py, ice_trump_intelligence.py
  - ingest_weather_noaa.py (US/AR/BR stations, backfill capable)
- BigQuery access: public GHCN-D blocked; replaced with NOAA API + BR stations
- Costs: deferred model training; focused on views and local collectors

Open issues/notes
- vw_zl_features_daily_all: need to re-run CREATE OR REPLACE VIEW with explicit ON clauses (provided in chat)
- Coverage check pending before any training
- Brazil policy/news sources are flowing through multi_source_news; can add CONAB/ABIOVE-specific scoring if needed

Immediate next actions (low-cost first)
1) Run local collectors (no BigQuery queries until load):
   - python3 cbi-v14-ingestion/multi_source_news.py
   - python3 cbi-v14-ingestion/social_intelligence.py
   - python3 cbi-v14-ingestion/shipping_intelligence.py
   - python3 cbi-v14-ingestion/ice_trump_intelligence.py
   - python3 cbi-v14-ingestion/economic_intelligence.py
2) Weather backfill via NOAA (batch writes):
   - python3 cbi-v14-ingestion/ingest_weather_noaa.py --backfill --years 2
3) Create/refresh vw_zl_features_daily_all (SQL in chat; explicit ON join clauses)
4) Coverage check (single COUNTIF query) and only then proceed to model training/evaluation

Upcoming (after coverage >= minimal)
- Train/evaluate ARIMA_PLUS baseline and XREG using vw_zl_features_daily_all
- Backtesting: 2-year MAPE; compare baseline vs. multivariate
- Dashboard wiring (Firebase Hosting) to display latest forecast and drivers

Definitions
- Canonical tables: soybean_oil_prices, weather_data, news_intelligence, social_sentiment,
  economic_indicators, shipping_alerts, ice_trump_intelligence, volatility_data

Risks & mitigations
- All-null regressors → guarded by COALESCE and pre-train coverage check
- Brazil public data access → NOAA API with BR stations as substitute
- Cost creep → local collection first; batch loads; avoid console-heavy queries


