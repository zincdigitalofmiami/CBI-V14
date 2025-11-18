# CBI-V14 Architecture Wireframe
**Date:** November 17, 2025  
**Status:** Complete Architecture Integration (Alpha Vantage + Existing)

---

## COMPLETE SYSTEM ARCHITECTURE WIREFRAME

```
╔═══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                    CBI-V14 COMPLETE ARCHITECTURE                                         ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    LAYER 1: DATA COLLECTION (Mac M4)                                    │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │                          EXISTING SOURCES (Python Scripts)                                   │
    ├──────────────────────────────────────────────────────────────────────────────────────────────┤
    │                                                                                              │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
    │  │   FRED API   │  │ Yahoo Finance │  │  NOAA API    │  │  CFTC API    │  │ USDA API   │ │
    │  │  (Economic)  │  │   (ZL Only)  │  │  (Weather)   │  │ (Positioning)│  │ (Reports)  │ │
    │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
    │         │                 │                 │                 │                 │         │
    │         └─────────────────┴─────────────────┴─────────────────┴─────────────────┘         │
    │                                    │                                                         │
    │         ┌─────────────────────────▼─────────────────────────┐                              │
    │         │  scripts/ingest/collect_*_comprehensive.py        │                              │
    │         │  - collect_fred_comprehensive.py                  │                              │
    │         │  - collect_yahoo_finance_comprehensive.py        │                              │
    │         │  - collect_noaa_comprehensive.py                  │                              │
    │         │  - collect_cftc_comprehensive.py                 │                              │
    │         │  - collect_usda_comprehensive.py                 │                              │
    │         │  - collect_eia_comprehensive.py                  │                              │
    │         └─────────────────────────┬─────────────────────────┘                              │
    │                                   │                                                          │
    └───────────────────────────────────┼──────────────────────────────────────────────────────────┘
                                        │
    ┌───────────────────────────────────┼──────────────────────────────────────────────────────────┐
    │                          ALPHA VANTAGE (NEW - Python Scripts)                                │
    ├───────────────────────────────────┼──────────────────────────────────────────────────────────┤
    │                                   │                                                          │
    │         ┌─────────────────────────▼─────────────────────────┐                              │
    │         │  Alpha Vantage API (Plan75 Premium)               │                              │
    │         │  - Commodities (non-ZL)                           │                              │
    │         │  - FX Pairs                                        │                              │
    │         │  - Technical Indicators (50+)                   │                              │
    │         │  - ES Futures (11 timeframes)                    │                              │
    │         │  - Options                                         │                              │
    │         │  - News/Sentiment                                 │                              │
    │         └─────────────────────────┬─────────────────────────┘                              │
    │                                   │                                                          │
    │         ┌─────────────────────────▼─────────────────────────┐                              │
    │         │  scripts/ingest/collect_alpha_master.py          │                              │
    │         │  - Rate limiting (75 calls/min)                   │                              │
    │         │  - Manifest tracking                               │                              │
    │         │  - Error handling                                  │                              │
    │         └─────────────────────────┬─────────────────────────┘                              │
    │                                   │                                                          │
    └───────────────────────────────────┼──────────────────────────────────────────────────────────┘
                                        │
                                        │
┌───────────────────────────────────────▼───────────────────────────────────────────────────────────────┐
│                              LAYER 2: RAW STORAGE (External Drive)                                     │
└───────────────────────────────────────┬───────────────────────────────────────────────────────────────┘

    /Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/
    │
    ├── fred/                    (FRED economic data - Parquet)
    ├── yahoo_finance/           (ZL prices only - Parquet)
    ├── noaa/                    (Weather data - Parquet)
    ├── cftc/                    (COT positioning - Parquet)
    ├── usda/                    (Agricultural reports - Parquet)
    ├── eia/                     (Biofuel data - Parquet)
    └── alpha/                   (NEW - Alpha Vantage data)
        ├── prices/
        │   ├── commodities/     (CORN, WHEAT, etc.)
        │   ├── fx/              (USD_BRL, EUR_USD, etc.)
        │   └── indices/         (SPY, etc.)
        ├── indicators/
        │   ├── daily/           (50+ indicators per symbol)
        │   └── intraday/        (ES indicators)
        ├── es_intraday/         (11 timeframes: 5min-6mo)
        ├── options/             (Options chains)
        └── sentiment/           (News sentiment)

                                        │
                                        │
┌───────────────────────────────────────▼───────────────────────────────────────────────────────────────┐
│                          LAYER 3: STAGING TRANSFORMATION (Mac M4)                                      │
└───────────────────────────────────────┬───────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │                    EXISTING SOURCES STAGING                                                     │
    ├──────────────────────────────────────────────────────────────────────────────────────────────┤
    │                                                                                              │
    │  ┌────────────────────────────────────────────────────────────────────────────┐              │
    │  │  scripts/staging/create_staging_files.py (NEW - Task 2.0)                │              │
    │  │  - Reads raw/{source}/ files                                             │              │
    │  │  - Standardizes date columns                                             │              │
    │  │  - Filters date ranges (2000-2025)                                       │              │
    │  │  - Creates staging/{source}_{description}_{date_range}.parquet          │              │
    │  └────────────────────────────────────────────────────────────────────────────┘              │
    │                                    │                                                          │
    │                                    ▼                                                          │
    │  /Volumes/.../TrainingData/staging/                                                          │
    │  ├── yahoo_historical_all_symbols.parquet                                                   │
    │  ├── fred_macro_2000_2025.parquet                                                            │
    │  ├── noaa_weather_2000_2025.parquet                                                          │
    │  ├── cftc_cot_2006_2025.parquet                                                              │
    │  ├── usda_nass_2000_2025.parquet                                                             │
    │  └── eia_biofuels_2010_2025.parquet                                                          │
    │                                                                                              │
    └──────────────────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │                    ALPHA VANTAGE STAGING (NEW)                                                │
    ├──────────────────────────────────────────────────────────────────────────────────────────────┤
    │                                                                                              │
    │  ┌────────────────────────────────────────────────────────────────────────────┐              │
    │  │  scripts/staging/prepare_alpha_for_joins.py (Task 2.7)                    │              │
    │  │  - Reads raw/alpha/indicators/ → Combines into wide format                │              │
    │  │  - Reads raw/alpha/prices/ → Standardizes format                          │              │
    │  │  - Merges prices + indicators on date + symbol                             │              │
    │  │  - Validates with AlphaDataValidator                                       │              │
    │  │  - Output: staging/alpha/daily/alpha_complete_ready_for_join.parquet      │              │
    │  └────────────────────────────────────────────────────────────────────────────┘              │
    │                                    │                                                          │
    │                                    ▼                                                          │
    │  /Volumes/.../TrainingData/staging/alpha/daily/                                              │
    │  └── alpha_complete_ready_for_join.parquet                                                  │
    │      (Date, Symbol, OHLCV, RSI_14, MACD_line, SMA_*, EMA_*, ... 50+ columns)               │
    │                                                                                              │
    └──────────────────────────────────────────────────────────────────────────────────────────────┘

                                        │
                                        │
┌───────────────────────────────────────▼───────────────────────────────────────────────────────────────┐
│                          LAYER 4: JOIN PIPELINE (Mac M4)                                              │
└───────────────────────────────────────┬───────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │  scripts/assemble/execute_joins.py                                                           │
    │  Uses: registry/join_spec.yaml (Declarative join specification)                              │
    └──────────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │                              JOIN SEQUENCE (Order Matters!)                                   │
    ├──────────────────────────────────────────────────────────────────────────────────────────────┤
    │                                                                                              │
    │  1. base_prices                                                                             │
    │     └─► staging/yahoo_historical_all_symbols.parquet                                        │
    │         (55 symbols, 2000-2025, OHLCV)                                                       │
    │                                                                                              │
    │  2. add_macro                                                                                │
    │     └─► staging/fred_macro_2000_2025.parquet                                                 │
    │         (30+ economic series: Fed rates, VIX, Treasury, USD index)                          │
    │         JOIN ON: date                                                                        │
    │         NULL POLICY: ffill                                                                   │
    │                                                                                              │
    │  3. add_weather                                                                              │
    │     └─► staging/noaa_weather_2000_2025.parquet                                               │
    │         (US Midwest temperature, precipitation)                                              │
    │         JOIN ON: date                                                                        │
    │         NULL POLICY: static fill (0.0 for precip, 10.0 for temp)                            │
    │                                                                                              │
    │  4. add_cftc                                                                                 │
    │     └─► staging/cftc_cot_2006_2025.parquet                                                   │
    │         (Positioning data, starts 2006)                                                     │
    │         JOIN ON: date                                                                        │
    │         NULL POLICY: allow nulls (pre-2006)                                                  │
    │                                                                                              │
    │  5. add_usda                                                                                 │
    │     └─► staging/usda_nass_2000_2025.parquet                                                  │
    │         (Agricultural reports, monthly/weekly)                                                │
    │         JOIN ON: date                                                                        │
    │         NULL POLICY: ffill                                                                   │
    │                                                                                              │
    │  6. add_biofuels                                                                              │
    │     └─► staging/eia_biofuels_2010_2025.parquet                                                │
    │         (Biofuel production, starts 2010)                                                    │
    │         JOIN ON: date                                                                        │
    │         NULL POLICY: allow nulls (pre-2010)                                                  │
    │                                                                                              │
    │  7. add_regimes                                                                               │
    │     └─► registry/regime_calendar.parquet                                                      │
    │         (9 regimes: 1990-2025, training weights 50-1000)                                    │
    │         JOIN ON: date                                                                        │
    │         NULL POLICY: ffill + default fill (market_regime="allhistory", weight=1)             │
    │                                                                                              │
    │  8. add_alpha_enhanced ⭐ NEW                                                                │
    │     └─► staging/alpha/daily/alpha_complete_ready_for_join.parquet                            │
    │         (Prices + 50+ technical indicators per symbol)                                        │
    │         JOIN ON: date + symbol (MULTI-KEY JOIN!)                                             │
    │         NULL POLICY: ffill                                                                    │
    │                                                                                              │
    └──────────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │                    JOINED DATASET (Output)                                                     │
    ├──────────────────────────────────────────────────────────────────────────────────────────────┤
    │  - 6,000+ rows (2000-2025)                                                                   │
    │  - 400-500+ columns                                                                          │
    │  - Includes:                                                                                  │
    │    • Yahoo prices (ZL + 54 symbols)                                                          │
    │    • FRED macro (30+ series)                                                                 │
    │    • NOAA weather                                                                            │
    │    • CFTC positioning                                                                        │
    │    • USDA reports                                                                            │
    │    • EIA biofuels                                                                            │
    │    • Regime assignments (9 regimes, weights)                                                │
    │    • Alpha prices (commodities, FX)                                                          │
    │    • Alpha indicators (50+ per symbol: RSI, MACD, SMA, EMA, BBANDS, ATR, etc.)             │
    └──────────────────────────────────────────────────────────────────────────────────────────────┘

                                        │
                                        │
┌───────────────────────────────────────▼───────────────────────────────────────────────────────────────┐
│                      LAYER 5: FEATURE ENGINEERING (Mac M4)                                            │
└───────────────────────────────────────┬───────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │  scripts/features/build_all_features.py                                                      │
    │  Input: Joined dataset from execute_joins.py                                                │
    └──────────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │                    FEATURE CALCULATION STRATEGY                                               │
    ├──────────────────────────────────────────────────────────────────────────────────────────────┤
    │                                                                                              │
    │  ✅ VALIDATION CHECKPOINT                                                                    │
    │     └─► Check: TrainingData/validation_certificate.json exists                             │
    │         (Must run final_alpha_validation.py first)                                          │
    │                                                                                              │
    │  ✅ DETECT ALPHA INDICATORS                                                                  │
    │     └─► Check if RSI_14, MACD_line present in joined data                                  │
    │                                                                                              │
    │  IF Alpha indicators present:                                                               │
    │     └─► SKIP calculate_technical_indicators()                                                │
    │         (Use Alpha pre-calculated indicators)                                               │
    │                                                                                              │
    │  ELSE:                                                                                        │
    │     └─► RUN calculate_technical_indicators()                                                 │
    │         (Fallback if Alpha data missing)                                                     │
    │                                                                                              │
    │  ✅ ALWAYS RUN (Alpha doesn't provide):                                                       │
    │     ├─► calculate_cross_asset_features()                                                     │
    │     │   └─► ZL correlations with FRED, VIX, dollar index                                   │
    │     │   └─► Rolling correlations (30d, 90d)                                                │
    │     │                                                                                        │
    │     ├─► calculate_volatility_features()                                                      │
    │     │   └─► Realized volatility (custom windows)                                            │
    │     │   └─► Annualized volatility                                                           │
    │     │                                                                                        │
    │     ├─► calculate_seasonal_features()                                                        │
    │     │   └─► Day-of-week effects                                                             │
    │     │   └─► Month/quarter effects                                                           │
    │     │                                                                                        │
    │     ├─► calculate_macro_regime_features()                                                    │
    │     │   └─► Fed regime classification                                                        │
    │     │   └─► Yield curve features                                                             │
    │     │                                                                                        │
    │     └─► calculate_weather_aggregations()                                                      │
    │         └─► Precipitation rolling averages                                                   │
    │         └─► Temperature aggregations                                                        │
    │                                                                                              │
    │  ✅ REGIME PROCESSING                                                                        │
    │     ├─► add_regime_columns()                                                                 │
    │     └─► apply_regime_weights() (50-1000 scale)                                               │
    │                                                                                              │
    │  ✅ FINAL FLAGS                                                                              │
    │     └─► add_override_flags()                                                                 │
    │                                                                                              │
    └──────────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │                    MASTER FEATURES FILE                                                        │
    ├──────────────────────────────────────────────────────────────────────────────────────────────┤
    │  /Volumes/.../TrainingData/features/master_features_2000_2025.parquet                        │
    │                                                                                              │
    │  - 6,000+ rows (2000-2025)                                                                   │
    │  - 500-600+ columns                                                                           │
    │  - Includes:                                                                                  │
    │    • All joined data (Yahoo, FRED, NOAA, CFTC, USDA, EIA, Alpha)                            │
    │    • Alpha technical indicators (50+ per symbol)                                           │
    │    • Custom correlations (ZL vs FRED, VIX, etc.)                                            │
    │    • Custom volatility features                                                              │
    │    • Seasonal features                                                                       │
    │    • Macro regime features                                                                    │
    │    • Weather aggregations                                                                     │
    │    • Regime assignments + weights                                                             │
    └──────────────────────────────────────────────────────────────────────────────────────────────┘

                                        │
                                        │
┌───────────────────────────────────────▼───────────────────────────────────────────────────────────────┐
│                      LAYER 6: TRAINING EXPORTS (Mac M4)                                              │
└───────────────────────────────────────┬───────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │  scripts/features/create_horizon_exports.py (or build_all_features.py)                      │
    │  - Reads master_features_2000_2025.parquet                                                    │
    │  - Creates forward-looking labels (7d, 30d, 90d, 180d, 365d)                                │
    │  - Filters to ZL symbol only                                                                │
    │  - Exports per horizon                                                                       │
    └──────────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    /Volumes/.../TrainingData/exports/
    ├── zl_training_prod_allhistory_1w.parquet    (7-day horizon)
    ├── zl_training_prod_allhistory_1m.parquet    (30-day horizon)
    ├── zl_training_prod_allhistory_3m.parquet     (90-day horizon)
    ├── zl_training_prod_allhistory_6m.parquet     (180-day horizon)
    └── zl_training_prod_allhistory_12m.parquet   (365-day horizon)

                                        │
                                        │
┌───────────────────────────────────────▼───────────────────────────────────────────────────────────────┐
│                      LAYER 7: DUAL STORAGE SYNC (Mac M4 → BigQuery)                                  │
└───────────────────────────────────────┬───────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │                    ALPHA SYNC (NEW)                                                            │
    ├──────────────────────────────────────────────────────────────────────────────────────────────┤
    │                                                                                              │
    │  scripts/sync/sync_alpha_to_bigquery.py (Task 2.8)                                           │
    │  - Reads staging/alpha/daily/alpha_complete_ready_for_join.parquet                           │
    │  - Validates with AlphaDataValidator                                                         │
    │  - Syncs to BigQuery:                                                                        │
    │    • forecasting_data_warehouse.technical_indicators_alpha_daily                            │
    │    • forecasting_data_warehouse.commodity_alpha_daily                                        │
    │    • forecasting_data_warehouse.fx_alpha_daily                                                │
    │    • forecasting_data_warehouse.intraday_es_alpha                                            │
    │    • forecasting_data_warehouse.news_sentiment_alpha                                          │
    │    • forecasting_data_warehouse.options_snapshot_alpha                                        │
    │                                                                                              │
    └──────────────────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │                    TRAINING SYNC (Existing)                                                    │
    ├──────────────────────────────────────────────────────────────────────────────────────────────┤
    │                                                                                              │
    │  [Existing mechanism]                                                                       │
    │  - Reads exports/*.parquet                                                                  │
    │  - Syncs to BigQuery:                                                                        │
    │    • training.zl_training_prod_allhistory_*                                                  │
    │                                                                                              │
    └──────────────────────────────────────────────────────────────────────────────────────────────┘

                                        │
                                        │
┌───────────────────────────────────────▼───────────────────────────────────────────────────────────────┐
│                      LAYER 8: BIGQUERY STORAGE (Cloud)                                               │
└───────────────────────────────────────┬───────────────────────────────────────────────────────────────┘

    cbi-v14 (project)
    │
    ├── forecasting_data_warehouse (dataset)
    │   ├── [Existing tables: 99 tables]
    │   │   ├── commodity_crude_oil_prices
    │   │   ├── economic_indicators
    │   │   ├── weather_data
    │   │   └── ...
    │   │
    │   └── [NEW Alpha tables] ⭐
    │       ├── commodity_alpha_daily
    │       ├── fx_alpha_daily
    │       ├── technical_indicators_alpha_daily (50+ columns)
    │       ├── intraday_es_alpha
    │       ├── news_sentiment_alpha
    │       ├── options_snapshot_alpha
    │       └── collection_manifest_alpha
    │
    ├── training (dataset)
    │   ├── zl_training_prod_allhistory_1w
    │   ├── zl_training_prod_allhistory_1m
    │   ├── zl_training_prod_allhistory_3m
    │   ├── zl_training_prod_allhistory_6m
    │   ├── zl_training_prod_allhistory_12m
    │   ├── regime_calendar
    │   └── regime_weights
    │
    └── predictions (dataset)
        └── [Model predictions]

                                        │
                                        │
┌───────────────────────────────────────▼───────────────────────────────────────────────────────────────┐
│                      LAYER 9: TRAINING (Mac M4 - PyTorch MPS)                                        │
└───────────────────────────────────────┬───────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │  Local PyTorch Training (MPS - Metal Performance Shaders)                                    │
    │  - Reads: TrainingData/exports/zl_training_prod_allhistory_*.parquet                        │
    │  - Models: TCN, LSTM, XGBoost, Ensemble                                                       │
    │  - Output: Local model files                                                                  │
    └──────────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    /Volumes/.../Models/local/
    └── [Model checkpoints]

                                        │
                                        │
┌───────────────────────────────────────▼───────────────────────────────────────────────────────────────┐
│                      LAYER 10: PREDICTIONS (Mac M4 → BigQuery)                                       │
└───────────────────────────────────────┬───────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │  Prediction Generation                                                                       │
    │  - Uses trained models                                                                       │
    │  - Generates forecasts for all horizons                                                      │
    │  - Uploads to BigQuery: predictions.*                                                         │
    └──────────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    BigQuery: predictions.*
    └── [Forecast outputs]

                                        │
                                        │
┌───────────────────────────────────────▼───────────────────────────────────────────────────────────────┐
│                      LAYER 11: DASHBOARD (Vercel/Next.js)                                           │
└───────────────────────────────────────┬───────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
    │  Dashboard API                                                                               │
    │  - Queries BigQuery: predictions.*                                                            │
    │  - Displays forecasts, charts, metrics                                                       │
    └──────────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    [User-facing Dashboard]

╔═══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                    KEY ARCHITECTURAL DECISIONS                                        ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════════════╝

1. DATASET UNIFICATION
   ✅ All Alpha tables in forecasting_data_warehouse (same as existing)
   ✅ Consistent naming: {type}_alpha_{granularity}

2. PROCESSING LOCATION
   ✅ Mac M4: ALL collection, staging, joins, feature engineering, training
   ✅ BigQuery: Storage, scheduling (cron), dashboard queries only
   ❌ NOT used for: Feature engineering, training, calculations

3. DUAL STORAGE
   ✅ External Drive: Primary storage (Parquet files)
   ✅ BigQuery: Mirror storage (same dataset)
   ✅ Sync happens after staging/feature engineering

4. JOIN ORDER
   ✅ Alpha joins LAST (after regimes)
   ✅ Rationale: Multi-key join (date + symbol), adds most columns

5. CALCULATION INTEGRATION
   ✅ Alpha: Pre-calculated technical indicators (use as-is)
   ✅ Our calculations: Correlations, volatility, seasonal, macro, weather
   ✅ Both coexist: Alpha technicals + Our custom features

6. VALIDATION CHECKPOINTS
   ✅ Collection: AlphaDataValidator
   ✅ Staging: AlphaDataValidator
   ✅ BigQuery Sync: AlphaDataValidator
   ✅ Final: validation_certificate.json (blocks training)

╔═══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                    DATA FLOW SUMMARY                                                  ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════════════╝

Collection → Raw Storage → Staging → Joins → Features → Exports → BigQuery → Training → Predictions → Dashboard

Each layer has:
- ✅ Validation checkpoints
- ✅ Error handling
- ✅ Manifest tracking (Alpha)
- ✅ Dual storage sync (Alpha)

