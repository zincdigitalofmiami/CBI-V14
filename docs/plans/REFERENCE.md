---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

**📋 BEST PRACTICES:** See `.cursorrules` and `docs/reference/BEST_PRACTICES_DRAFT.md` for mandatory best practices including: no fake data, always check before creating, always audit after work, us-central1 only, no costly resources without approval, research best practices, research quant finance modeling.

# CBI-V14 Quick Reference
**Purpose:** Fast lookup for tables, data sources, and key information  
**Updated:** November 19, 2025

---

## BigQuery Datasets (8 Active)

| Dataset | Purpose | Key Tables |
|---------|---------|------------|
| `api` | Public views for dashboard | `vw_dashboard_current_state`, `vw_mes_private` |
| `features` | Feature engineering | `master_features`, `mes_*`, `technical_features` |
| `market_data` | Market prices & signals | `futures_prices`, `calendar_spreads`, `crush_margins` |
| `monitoring` | Model performance | `model_performance`, `prediction_accuracy`, `data_quality` |
| `predictions` | Forecasts & predictions | `daily_forecasts`, `historical_predictions` |
| `raw_intelligence` | Raw data ingestion | `databento_*`, `fred_*`, `news_*`, `policy_*` |
| `training` | Training datasets | `zl_training_*`, `regime_calendar`, `regime_weights` |
| `z_archive_20251119` | Archive (327 tables) | All old/backup data |

---

## Data Sources

### Primary Sources (Active)
| Source | Data | API/Method | Status |
|--------|------|------------|--------|
| **DataBento** | Futures OHLCV (ZL, ES/MES, ZS/ZM, ZC/ZW, CL/HO/RB/NG, key FX futures) | API + historical files | ✅ Active |
| **FRED** | Macro indicators (VIXCLS, rates, credit) | API | ✅ Active |
| **CFTC** | Commitments of Traders (positioning) | CSV/API | ✅ Active |
| **EIA** | Energy & biofuels (RINs, production) | API | ✅ Active |
| **USDA** | WASDE, export sales, crop progress | API/files | ✅ Active |
| **NOAA/Regional** | Weather (US/Brazil/Argentina belts) | API | ✅ Active |
| **ScrapeCreators** | Aggregated news/policy/social (incl. Truth Social) + Google search sweeps | API | ✅ Active |

### Secondary/Bridge
| Source | Data | Notes |
|--------|------|-------|
| **Yahoo Finance** | Historical ZL (2000–2010) | Bridge only; no indicators |
| **Alpha Vantage** | News only (optional) | Not used for indicators |
| **CME CVOL** | SOVL/SVL implied vol indices | Discontinued (not used) |

### Cost Guardrail
- No new historical backfills outside the approved plan. Only the existing Yahoo ZL=F (2000–2010) bridge is permitted; all other acquisition must be live DataBento (forward‑only) or approved agency feeds. Any exceptions require explicit approval due to cost.

### Secondary Sources (Planned/Reference)
| Source | Data | Notes |
|--------|------|-------|
| **USDA NASS** | Crop data, exports | API available |
| **CBOE** | VIX, VVIX | CSV downloads |
| **CME Group** | Futures metadata | Web scraping |
| **Trump X/Twitter** | Policy sentiment | API + VADER |
| **NOAA** | Weather data | API |

---

## Key Staging Files → BigQuery Mapping

### Futures Data
- `zl_futures_daily.parquet` → `raw_intelligence.databento_futures_ohlcv_1d`
- `mes_futures_daily.parquet` → `market_data.mes_futures_daily`
- `es_futures_daily.parquet` → `market_data.es_futures_daily`

### Features
- `technical_features.parquet` → `features.technical_features` (computed in‑house from DataBento OHLCV)
- `mes_confirmation_features.parquet` → `features.mes_confirmation`
- `zl_confirmation_features.parquet` → `features.zl_confirmation`

### Macro Data
- `fred_macro_expanded.parquet` → `raw_intelligence.fred_macro`
- `eia_biofuels_2010_2025.parquet` → `raw_intelligence.eia_biofuels`
- `cftc_commitments.parquet` → `raw_intelligence.cftc_cot`
- `worldbank_macro_alternative.parquet` (if present, from `scripts/ingest/collect_worldbank_alternative.py`) → `raw_intelligence.worldbank_macro_alt` (complementary series only; FRED remains canonical for overlapping indicators)

### News & Intelligence
- `trump_policy_*.parquet` → `raw_intelligence.trump_policy`
- `news_*.parquet` → `raw_intelligence.news_sentiments`
- `usda_*.parquet` → `raw_intelligence.usda_*`

---

## Training Data Horizons

| Horizon | Target | Use Case | File Pattern |
|---------|--------|----------|--------------|
| 1-min | Next minute | Intraday scalping | `*_1min_training.parquet` |
| 15-min | Next 15 min | Microstructure | `*_15min_training.parquet` |
| 1-hour | Next hour | Intraday positions | `*_1h_training.parquet` |
| 1-day | Next day | Daily procurement | `*_1d_training.parquet` |
| 1-week | Next week | Weekly planning | `*_1w_training.parquet` |
| 1-month | Next month | Strategic planning | `*_1m_training.parquet` |
| 3-month | Quarter ahead | Long-term contracts | `*_3m_training.parquet` |
| 6-month | Half-year ahead | Annual planning | `*_6m_training.parquet` |

---

## Symbols & Contracts

### Primary Symbols
- **ZL** - Soybean Oil futures (60,000 lbs, CME)
- **MES** - Micro E-mini S&P 500 (1/10th ES, CME)
- **ES** - E-mini S&P 500 (CME)

### Related Commodities
- **ZS** - Soybeans
- **ZM** - Soybean Meal
- **ZC** - Corn
- **ZW** - Wheat
- **CL** - Crude Oil
- **HO** - Heating Oil
- **RB** - RBOB Gasoline

### Contract Months
- **Quarterly:** H (Mar), M (Jun), U (Sep), Z (Dec)
- **ZL Trading:** Year-round on CME Globex
- **MES Trading:** 23/6 (Sun 6PM - Fri 5PM ET)

---

## Model Regimes

| Regime | Characteristics | Weighting Strategy |
|--------|----------------|-------------------|
| **Pre-Crisis (2000-2007)** | Stable, low volatility | Standard weight |
| **Crisis (2008-2009)** | High volatility, crashes | 2-3x weight |
| **Recovery (2010-2016)** | Gradual recovery | Standard weight |
| **Trade War (2017-2019)** | Tariff impacts | 1.5x weight |
| **COVID (2020-2021)** | Extreme volatility | 2x weight |
| **Post-COVID (2022-2023)** | Normalization | Standard weight |
| **Trump 2.0 (2024-2025)** | Policy uncertainty | 2x weight (current) |

---

## External Drive Structure

```
/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/
├── 01_raw/              # Raw historical data from APIs
├── 02_staging/          # Cleaned parquet files
├── 03_features/         # Feature engineering outputs
├── 04_exports/          # Training data by horizon
├── 05_training/         # Model artifacts & checkpoints
└── 00_bigquery_backup_YYYYMMDD/  # BQ backups
```

---

## API Keys & Credentials

**Location:** `.env` file (never commit!)

```bash
DATABENTO_API_KEY=db-xxx
# If used for news only (optional)
# ALPHA_VANTAGE_API_KEY=xxx
FRED_API_KEY=xxx
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
BIGQUERY_PROJECT_ID=cbi-v14
```

---

## Important Scripts

### Data Collection
- `scripts/ingest/databento_historical_download.py` - Download futures data
- `scripts/ingest/fred_macro_collector.py` - Collect macro data
- `scripts/ingest/collect_comprehensive_sentiment.py` - News/Sentiment (provider‑agnostic)

### Staging
- `scripts/staging/aggregate_*_daily.py` - Daily aggregation
- `scripts/staging/aggregate_*_intraday.py` - Intraday aggregation
- `scripts/staging/build_*_15min_series.py` - 15-min features

### Feature Engineering
- `scripts/features/build_confirmation_features.py` - Confirmation signals
- `scripts/features/build_master_features.py` - Master feature table
- `scripts/features/feature_calculations.py` - Technical indicators (from DataBento OHLCV)

### Training
- `scripts/training/export_training_horizons.py` - Create horizon exports
- `scripts/training/train_*.py` - Training scripts per model

### Deployment
- `scripts/deployment/deploy_essential_bq_tables.sh` - Deploy BQ structure
- `scripts/deployment/archive_datasets_now.sh` - Archive old datasets
- `scripts/migration/load_all_external_drive_data.py` - Load to BQ

---

## Quick Commands

### BigQuery
```bash
# List datasets
bq ls --project_id=cbi-v14

# View table schema
bq show cbi-v14:dataset.table

# Query table
bq query --use_legacy_sql=false "SELECT * FROM \`cbi-v14.dataset.table\` LIMIT 10"

# Export table to external drive
bq extract --destination_format=PARQUET \
  cbi-v14:dataset.table \
  gs://bucket/file.parquet
```

### DataBento
```bash
# Download historical data
python scripts/ingest/databento_historical_download.py \
  --symbol ZL --start 2000-01-01 --end 2025-11-19

# Live ingestion
python scripts/ingest/databento_live_ingestion.py --symbol ZL
```

### Training Export
```bash
# Export all horizons
python scripts/training/export_training_horizons.py \
  --symbol ZL --output /Volumes/Satechi\ Hub/Projects/CBI-V14/TrainingData/04_exports/
```

---

## Critical Paths

### Data Flow
```
DataBento → 01_raw/ → 02_staging/ → BigQuery raw_intelligence
→ 03_features/ → BigQuery features → master_features
→ 04_exports/ → Training → 05_training/ → BigQuery predictions
```

### Training Flow
```
master_features → export_training_horizons.py → horizon parquets
→ train_*.py → model artifacts → BigQuery monitoring
→ predict.py → BigQuery predictions → Dashboard API
```

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| BigQuery Datasets | 8 | ✅ 8 |
| Staging Files | 20+ | ✅ 19 |
| Features | 400-500 | 🔄 290 |
| Training Date Range | 25+ years | ✅ 25 years |
| Model Regimes | 7 | ✅ 7 |
| Forecast Horizons | 8 | ✅ 8 |
| MAPE Target | <3% | 🎯 TBD |

---

## Contact & Support

**Project Owner:** Kirk Musick (kirkmusick@gmail.com)  
**Repository:** `/Users/kirkmusick/Documents/GitHub/CBI-V14`  
**Documentation:** `docs/plans/`  
**Master Plans:** See `MASTER_PLAN.md`, `TRAINING_PLAN.md`, `BIGQUERY_MIGRATION_PLAN.md`

---

**For detailed information, refer to:**
- `TABLE_MAPPING_MATRIX.md` - Complete staging → BQ mapping
- `DATA_SOURCES_REFERENCE.md` - Full data source catalog
- `MASTER_PLAN.md` - Overall project strategy
- `TRAINING_PLAN.md` - Training methodology
- `ARCHITECTURE.md` - System design
