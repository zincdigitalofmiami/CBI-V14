---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# External Drive Organization - Research & Design
**Date:** November 18, 2025  
**Status:** RESEARCH PHASE - NO EXECUTION  
**Approval:** PENDING

---

## 🎯 OBJECTIVE

Design a comprehensive external drive folder structure that organizes data by:
1. **Regime** (11 regimes from 2000-2025)
2. **Horizon** (17 total: 5 ZL + 12 MES)
3. **Model Type** (baselines, advanced, ensemble, regime-specific)
4. **Topic/Domain** (market, fundamentals, intelligence, weather, policy)
5. **Data Source** (DataBento, FRED, USDA, EIA, CFTC, weather, news)
6. **Training Phase** (Phase 0, Phase 1, Phase 2)

---

## 📚 YOUR EXACT REQUIREMENTS (From Training Master Plan)

### 11 Regimes (Regime Calendar)
1. `historical_pre2000` (Before 2000) - Weight: 50
2. `pre_crisis_2000_2007` (2000-2007) - Weight: 100
3. `crisis_2008` (2008-2009) - Weight: 500
4. `recovery_2010_2016` (2010-2016) - Weight: 300
5. `trade_war_2017_2019` (2017-2019) - Weight: 1500
6. `covid_2020` (2020) - Weight: 800
7. `inflation_2021_2022` (2021-2022) - Weight: 1200
8. `trump_2023_2025` (2023-2025) - Weight: 5000
9. `normal` - Weight: 100
10. `bull` - Weight: 200
11. `bear` - Weight: 400

### 17 Horizons

**ZL (Soybean Oil) - 5 Daily Horizons:**
1. 1w (1 week)
2. 1m (1 month)
3. 3m (3 months)
4. 6m (6 months)
5. 12m (12 months)

**MES (Micro E-mini S&P 500) - 12 Intraday + Multi-period Horizons:**
- **Intraday (minutes):** 1min, 5min, 15min, 30min (4 horizons)
- **Intraday (hours):** 1hr, 4hr (2 horizons)
- **Multi-day:** 1d, 7d, 30d (3 horizons)
- **Multi-month:** 3m, 6m, 12m (3 horizons)

### Model Types (60-75 total models)
**ZL Models (30-35):**
- Baselines: ARIMA, Prophet, LightGBM, XGBoost, simple LSTM (5-10 models)
- Advanced: TCN, Multi-layer LSTM, Attention models (10-15 models)
- Regime-specific: Models per regime (8-11 models)
- Ensemble: Weighted combinations (3-5 models)

**MES Models (35-40):**
- Intraday neural: LSTM, TCN, CNN-LSTM for minute/hour horizons (15-20 models)
- Multi-day tree: LightGBM, XGBoost for day/month horizons (10-15 models)
- Regime-specific: MES regime models (5-10 models)

### Data Domains
1. **Market Data** - Price, volume, OI (DataBento, Yahoo)
2. **Fundamentals** - USDA, EIA, CFTC (supply, demand, positioning)
3. **Intelligence** - News, sentiment, policy (ScrapeCreators, Trump tracker)
4. **Weather** - NOAA, INMET (US, Brazil, Argentina)
5. **Macro** - FRED, volatility (rates, dollar, VIX)
6. **Hidden** - Cross-domain intelligence, lobbying, relationships

---

## 🏗️ PROPOSED FOLDER STRUCTURE

```
/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/
│
├── 📁 raw/                              ← Raw collected data (by source)
│   ├── databento/
│   │   ├── historical/
│   │   │   ├── ZL/
│   │   │   │   ├── 2010/
│   │   │   │   ├── 2011/
│   │   │   │   └── ... (by year)
│   │   │   ├── MES/
│   │   │   └── ES/
│   │   └── live/
│   │       ├── ZL/1m/
│   │       ├── MES/1m/
│   │       └── ES/1m/
│   │
│   ├── yahoo/
│   │   ├── ZL_F_2000_2010.parquet
│   │   ├── daily_all_symbols.parquet
│   │   └── historical/
│   │
│   ├── fred/
│   │   ├── daily/
│   │   ├── weekly/
│   │   └── monthly/
│   │
│   ├── usda/
│   │   ├── wasde/
│   │   ├── exports/
│   │   ├── crop_progress/
│   │   └── stocks/
│   │
│   ├── eia/
│   │   ├── biofuels/
│   │   ├── rins/
│   │   └── petroleum/
│   │
│   ├── cftc/
│   │   ├── cot_weekly/
│   │   └── by_commodity/
│   │
│   ├── weather/
│   │   ├── noaa_us/
│   │   ├── inmet_brazil/
│   │   └── smn_argentina/
│   │
│   ├── news/
│   │   ├── scrapecreators/
│   │   ├── policy_events/
│   │   └── trump_intelligence/
│   │
│   └── intelligence/
│       ├── hidden_relationships/
│       ├── lobbying/
│       └── cross_domain/
│
├── 📁 processed/                        ← Cleaned, normalized data (by domain)
│   ├── market/
│   │   ├── continuous_contracts/
│   │   │   ├── ZL_continuous_2000_2025.parquet
│   │   │   ├── MES_continuous_2010_2025.parquet
│   │   │   └── ES_continuous_2010_2025.parquet
│   │   ├── spreads/
│   │   └── curves/
│   │
│   ├── fundamentals/
│   │   ├── usda_unified.parquet
│   │   ├── eia_unified.parquet
│   │   └── cftc_unified.parquet
│   │
│   ├── macro/
│   │   ├── fred_unified.parquet
│   │   ├── volatility_unified.parquet
│   │   └── fx_unified.parquet
│   │
│   ├── intelligence/
│   │   ├── news_unified.parquet
│   │   ├── sentiment_unified.parquet
│   │   └── policy_unified.parquet
│   │
│   └── weather/
│       ├── us_midwest.parquet
│       ├── brazil_soy_belt.parquet
│       └── argentina.parquet
│
├── 📁 features/                         ← Feature-engineered data (by asset)
│   ├── ZL/
│   │   ├── master_features_2000_2025.parquet      ← THE canonical feature table
│   │   ├── technical_indicators.parquet
│   │   ├── crush_oilshare.parquet
│   │   ├── spreads_curves.parquet
│   │   ├── intelligence.parquet
│   │   └── big8_signals.parquet
│   │
│   └── MES/
│       ├── master_features_intraday_2010_2025.parquet
│       ├── microstructure.parquet
│       ├── orderflow.parquet
│       └── aggregated_daily.parquet
│
├── 📁 regimes/                          ← Regime classification & support
│   ├── regime_calendar.parquet          ← Maps every date → regime
│   ├── regime_weights.parquet           ← Maps regime → training weight
│   ├── regime_transitions.parquet
│   └── by_regime/
│       ├── trump_2023_2025/
│       ├── trade_war_2017_2019/
│       ├── crisis_2008/
│       └── ... (11 regime folders)
│
├── 📁 training/                         ← Training exports (by asset, horizon, regime)
│   ├── ZL/
│   │   ├── by_horizon/
│   │   │   ├── 1w/
│   │   │   │   ├── zl_training_prod_allhistory_1w.parquet
│   │   │   │   ├── zl_training_full_allhistory_1w.parquet
│   │   │   │   └── by_regime/
│   │   │   │       ├── trump_2023_2025_1w.parquet
│   │   │   │       ├── trade_war_2017_2019_1w.parquet
│   │   │   │       └── ... (11 regime files)
│   │   │   ├── 1m/
│   │   │   ├── 3m/
│   │   │   ├── 6m/
│   │   │   └── 12m/
│   │   │
│   │   └── by_regime/
│   │       ├── trump_2023_2025/
│   │       │   ├── 1w.parquet
│   │       │   ├── 1m.parquet
│   │       │   ├── 3m.parquet
│   │       │   ├── 6m.parquet
│   │       │   └── 12m.parquet
│   │       └── ... (11 regime folders)
│   │
│   └── MES/
│       ├── by_horizon/
│       │   ├── intraday_minutes/
│       │   │   ├── 1min/
│       │   │   ├── 5min/
│       │   │   ├── 15min/
│       │   │   └── 30min/
│       │   ├── intraday_hours/
│       │   │   ├── 1hr/
│       │   │   └── 4hr/
│       │   ├── multiday/
│       │   │   ├── 1d/
│       │   │   ├── 7d/
│       │   │   └── 30d/
│       │   └── multimonth/
│       │       ├── 3m/
│       │       ├── 6m/
│       │       └── 12m/
│       │
│       └── by_regime/
│           └── ... (regime folders if needed for MES)
│
├── 📁 models/                           ← Trained models (by asset, type, horizon)
│   ├── ZL/
│   │   ├── baselines/
│   │   │   ├── arima/
│   │   │   │   ├── 1w/
│   │   │   │   ├── 1m/
│   │   │   │   └── ... (5 horizon folders)
│   │   │   ├── prophet/
│   │   │   ├── lightgbm/
│   │   │   ├── xgboost/
│   │   │   └── simple_lstm/
│   │   │
│   │   ├── advanced/
│   │   │   ├── tcn/
│   │   │   ├── lstm_multilayer/
│   │   │   ├── attention/
│   │   │   └── cnn_lstm/
│   │   │
│   │   ├── regime_specific/
│   │   │   ├── trump_2023_2025/
│   │   │   │   ├── 1w/
│   │   │   │   └── ... (5 horizons)
│   │   │   ├── trade_war_2017_2019/
│   │   │   └── ... (11 regime folders)
│   │   │
│   │   └── ensemble/
│   │       ├── 1w_ensemble/
│   │       ├── 1m_ensemble/
│   │       └── ... (5 horizon ensembles)
│   │
│   └── MES/
│       ├── baselines/
│       ├── neural_intraday/
│       ├── tree_multiday/
│       └── ensemble/
│
├── 📁 predictions/                      ← Model outputs (by asset, horizon, date)
│   ├── ZL/
│   │   ├── by_horizon/
│   │   │   ├── 1w/
│   │   │   │   ├── 2025-11/
│   │   │   │   │   ├── predictions_2025-11-18.parquet
│   │   │   │   │   └── ...
│   │   │   │   └── 2025-10/
│   │   │   └── ... (5 horizon folders)
│   │   │
│   │   └── by_model/
│   │       ├── ensemble/
│   │       ├── lstm/
│   │       └── lightgbm/
│   │
│   └── MES/
│       └── by_horizon/
│           ├── 1min/
│           ├── 5min/
│           └── ... (12 horizon folders)
│
├── 📁 validation/                       ← Validation results (by model, horizon, regime)
│   ├── ZL/
│   │   ├── by_horizon/
│   │   │   ├── 1w/
│   │   │   │   ├── baseline_comparison.csv
│   │   │   │   ├── shap_values.parquet
│   │   │   │   ├── feature_importance.csv
│   │   │   │   └── regime_performance.csv
│   │   │   └── ... (5 horizons)
│   │   │
│   │   └── by_regime/
│   │       ├── trump_2023_2025/
│   │       └── ... (11 regimes)
│   │
│   └── MES/
│       └── by_horizon/
│           └── ... (12 horizons)
│
├── 📁 metadata/                         ← Catalogs, schemas, registries
│   ├── data_sources/
│   │   ├── databento_catalog.yaml
│   │   ├── fred_series_catalog.yaml
│   │   ├── usda_reports_catalog.yaml
│   │   └── ... (all sources)
│   │
│   ├── features/
│   │   ├── feature_catalog.csv         ← ALL 400+ features documented
│   │   ├── feature_groups.yaml
│   │   └── feature_importance_history.csv
│   │
│   ├── models/
│   │   ├── model_registry.yaml
│   │   ├── hyperparameters/
│   │   └── performance_history.csv
│   │
│   └── regimes/
│       ├── regime_definitions.yaml
│       ├── regime_transitions.csv
│       └── regime_performance.csv
│
└── 📁 exports/                          ← BigQuery sync exports
    ├── to_bigquery/
    │   ├── market_data/
    │   ├── raw_intelligence/
    │   ├── features/
    │   └── predictions/
    │
    └── from_bigquery/
        ├── training_data/
        └── validation_data/
```

---

## 🔍 RESEARCH FINDINGS

### Industry Best Practices (Quant Hedge Funds)

**1. Separation of Concerns:**
- Raw data separated from processed data
- Features separated from training data
- Models separated from predictions
- Metadata tracked separately

**2. Temporal Organization:**
- Raw data organized by collection date
- Processed data organized by data date
- Training data organized by regime AND horizon
- Predictions organized by prediction date

**3. Immutability:**
- Raw data NEVER modified (append-only)
- Processed data versioned (v1, v2, etc.)
- Training data snapshots preserved
- Models versioned and archived

**4. Regime-Awareness:**
- Training data explicitly segmented by market regime
- Models trained per regime with separate folders
- Cross-regime performance tracked

**5. Horizon-Specific:**
- Each prediction horizon gets own folder
- Features may differ by horizon
- Models specialized per horizon

---

## 📊 DETAILED DESIGN RATIONALE

### Level 1: raw/ (By Source)
**Purpose:** Preserve original data exactly as collected

**Organization:**
- One folder per data source (databento, yahoo, fred, usda, etc.)
- Sub-organized by time period (year/month for historical)
- Sub-organized by symbol/asset where applicable
- File naming: `{source}_{symbol}_{date}.parquet`

**Why:**
- Easy to re-process if feature engineering changes
- Clear audit trail of what was collected when
- Can rebuild entire pipeline from raw
- Source-specific issues easy to isolate

### Level 2: processed/ (By Domain)
**Purpose:** Cleaned, normalized, unified data

**Organization:**
- Organized by data domain (market, fundamentals, macro, intelligence, weather)
- Unified files per domain (e.g., usda_unified.parquet combines all USDA sources)
- Standardized schemas across domains
- File naming: `{domain}_{subdomain}_unified.parquet`

**Why:**
- Single file per domain = faster joins
- Normalized schemas = easier feature engineering
- Domain isolation = easier debugging
- Ready for feature creation

### Level 3: features/ (By Asset)
**Purpose:** Feature-engineered data ready for model training

**Organization:**
- Top level by asset (ZL/, MES/)
- Master features file per asset (canonical source of truth)
- Feature subsets by domain (technical, fundamental, intelligence)
- File naming: `{asset}_master_features_{start_date}_{end_date}.parquet`

**Why:**
- Asset-specific features isolated
- Master features = single source of truth
- Easy to version and track
- Clear lineage from raw → processed → features

### Level 4: regimes/ (Regime Support)
**Purpose:** Regime classification and weighting infrastructure

**Organization:**
- Regime calendar (date → regime mapping)
- Regime weights (regime → training weight)
- By-regime folders for regime-specific analysis
- Transition analysis

**Why:**
- Regime classification is first-class citizen
- Training weights drive model behavior
- Easy to update regime assignments
- Historical regime analysis preserved

### Level 5: training/ (By Asset → Horizon → Regime)
**Purpose:** Final training exports for model consumption

**Organization:**
- First level: Asset (ZL/, MES/)
- Second level: by_horizon/ or by_regime/
- Third level: Specific horizon (1w/, 1m/, etc.) or regime folder
- File naming: `{asset}_training_{scope}_{regime}_{horizon}.parquet`

**Why:**
- Models trained per asset-horizon combination
- Regime-specific training data easy to access
- Clear mapping: one file = one training job
- Prevents data leakage across horizons

### Level 6: models/ (By Asset → Type → Architecture → Horizon)
**Purpose:** Trained model artifacts

**Organization:**
- First level: Asset (ZL/, MES/)
- Second level: Model type (baselines/, advanced/, regime_specific/, ensemble/)
- Third level: Architecture (arima/, tcn/, lightgbm/, etc.)
- Fourth level: Horizon (1w/, 1m/, etc.)
- File naming: `{arch}_{horizon}_v{version}.keras` or `.pkl`

**Why:**
- Easy to find specific model
- Architecture comparisons straightforward
- Horizon-specific models isolated
- Versioning built into structure

### Level 7: predictions/ (By Asset → Horizon → Date)
**Purpose:** Model prediction outputs

**Organization:**
- First level: Asset (ZL/, MES/)
- Second level: by_horizon/ or by_model/
- Third level: Horizon folder (1w/, 1m/, etc.)
- Fourth level: By month (2025-11/, 2025-10/, etc.)
- File naming: `predictions_{date}.parquet`

**Why:**
- Time-series organization for predictions
- Easy to find predictions for specific date
- Monthly archiving keeps folders manageable
- Clear separation by horizon

### Level 8: validation/ (By Asset → Horizon → Metric)
**Purpose:** Model validation and performance tracking

**Organization:**
- First level: Asset (ZL/, MES/)
- Second level: by_horizon/ or by_regime/
- Third level: Specific horizon or regime
- Files: SHAP values, feature importance, MAPE metrics, regime performance

**Why:**
- Validation tied to specific horizon/regime
- Easy to compare model performance
- SHAP analysis preserved
- Historical performance tracking

### Level 9: metadata/ (Catalogs & Registries)
**Purpose:** Documentation, schemas, catalogs

**Organization:**
- data_sources/ - What's collected, from where, how often
- features/ - Complete feature catalog (400+ features documented)
- models/ - Model registry, hyperparameters, performance
- regimes/ - Regime definitions and transitions

**Why:**
- Single source of truth for all metadata
- Easy to audit data collection
- Feature catalog prevents duplication
- Model registry tracks experiments

### Level 10: exports/ (BigQuery Sync)
**Purpose:** Interface with BigQuery

**Organization:**
- to_bigquery/ - Data being uploaded to BQ
- from_bigquery/ - Data exported from BQ for training

**Why:**
- Clear boundary between local and cloud
- Easy to monitor sync status
- Prevent circular dependencies

---

## 🎯 FILE NAMING CONVENTIONS

### Raw Data Files
```
{source}_{symbol}_{date}.parquet
Examples:
- databento_ZL_2024-11-18.parquet
- yahoo_ZL_F_daily_2000_2010.parquet
- fred_DGS10_2000_2025.parquet
```

### Processed Data Files
```
{domain}_{subdomain}_unified_{start}_{end}.parquet
Examples:
- market_continuous_unified_2000_2025.parquet
- fundamentals_usda_unified_2000_2025.parquet
- macro_fred_unified_2000_2025.parquet
```

### Feature Files
```
{asset}_master_features_{start}_{end}.parquet
{asset}_{feature_group}_{start}_{end}.parquet
Examples:
- ZL_master_features_2000_2025.parquet
- ZL_technical_indicators_2000_2025.parquet
- MES_microstructure_2010_2025.parquet
```

### Training Files
```
{asset}_training_{scope}_{regime}_{horizon}.parquet
Examples:
- zl_training_prod_allhistory_1w.parquet
- zl_training_full_trump_2023_2025_1m.parquet
- mes_training_prod_allhistory_1min.parquet
```

### Model Files
```
{architecture}_{horizon}_v{version}.{extension}
Examples:
- tcn_1w_v001.keras
- lightgbm_1m_v003.pkl
- ensemble_3m_v002.pkl
```

### Prediction Files
```
predictions_{date}.parquet
Examples:
- predictions_2025-11-18.parquet
- predictions_2025-11-17.parquet
```

---

## 📋 MIGRATION PLAN (WHEN APPROVED)

### Phase 1: Create Structure (5 minutes)
```bash
# Create all folders (READ-ONLY SCRIPT - shows what would be created)
python3 scripts/migration/create_external_drive_structure.py --dry-run
```

### Phase 2: Organize Raw Data (1 hour)
```bash
# Move raw files to proper locations
python3 scripts/migration/organize_raw_data.py --dry-run
```

### Phase 3: Build Processed Data (2 hours)
```bash
# Create unified processed files
python3 scripts/features/build_processed_unified.py --dry-run
```

### Phase 4: Create Master Features (2 hours)
```bash
# Build ZL master_features with ALL 400+ columns
python3 scripts/features/build_master_features_complete.py --dry-run
```

### Phase 5: Export Training Data (1 hour)
```bash
# Create all training exports (by horizon, by regime)
python3 scripts/training/export_all_training_data.py --dry-run
```

---

## ⏸️ WAITING FOR APPROVAL

**I WILL DO NOTHING until you review and approve this structure.**

**Questions for you:**
1. Does this folder organization match your vision?
2. Any changes to the regime/horizon organization?
3. Should models be organized differently?
4. Any additional folders or reorganization needed?

**STATUS:** RESEARCH COMPLETE, AWAITING APPROVAL BEFORE ANY EXECUTION

