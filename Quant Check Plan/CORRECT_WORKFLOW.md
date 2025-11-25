# ✅ CORRECT WORKFLOW: BQ Calculations → Mac Training

**Date:** November 24, 2025  
**Clarification:** Training is ALWAYS on Mac. BigQuery is for storage and calculations ONLY.

---

## 🔄 THE CORRECT FLOW

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BIGQUERY (Cloud)                              │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │  RAW DATA    │ →  │  STAGING     │ →  │  FEATURES            │   │
│  │              │    │              │    │  (calculations)      │   │
│  │ • Databento  │    │ • Normalized │    │ • TA indicators      │   │
│  │ • FRED       │    │ • Cleaned    │    │ • Regime stamps      │   │
│  │ • Weather    │    │ • Validated  │    │ • Cross-asset        │   │
│  └──────────────┘    └──────────────┘    └──────────────────────┘   │
│                                                  │                   │
│                                                  ▼                   │
│                                          ┌──────────────────────┐   │
│                                          │  TRAINING VIEWS      │   │
│                                          │  (export-ready)      │   │
│                                          │ • With targets       │   │
│                                          │ • With splits        │   │
│                                          │ • Flattened          │   │
│                                          └──────────────────────┘   │
│                                                  │                   │
└──────────────────────────────────────────────────│───────────────────┘
                                                   │
                                                   │ EXPORT (CSV/Parquet)
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          MAC (Local)                                 │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      TRAINING                                 │   │
│  │  • LightGBM baseline                                         │   │
│  │  • TFT (PyTorch)                                             │   │
│  │  • Hyperparameter tuning (Optuna)                            │   │
│  │  • Walk-forward validation                                    │   │
│  │  • SHAP analysis                                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    PREDICTIONS                                │   │
│  │  • Generate forecasts                                        │   │
│  │  • Confidence intervals                                      │   │
│  │  • Direction probabilities                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
└──────────────────────────────│───────────────────────────────────────┘
                               │
                               │ UPLOAD predictions
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        BIGQUERY (Cloud)                              │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    FORECASTS                                  │   │
│  │  • zl_forecasts_daily                                        │   │
│  │  • zl_explainers_daily (SHAP)                                │   │
│  │  • API views for Vercel                                      │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
└──────────────────────────────│───────────────────────────────────────┘
                               │
                               │ API
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         VERCEL (Frontend)                            │
│                                                                      │
│  • Dashboard                                                        │
│  • Charts                                                           │
│  • Alerts                                                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ✅ WHAT WE JUST DID (CORRECT)

| Step | Where | What |
|------|-------|------|
| 1. `regime_lookup` | BQ | Reference table for regime dates |
| 2. `zl_daily_v1` | BQ | Feature table (TA calculations) |
| 3. Ingestion script | Mac → BQ | Python calculates TA, loads to BQ |
| 4. `vw_zl_1m_v1` | BQ | View adds targets for export |
| 5. Assertions | BQ | Data quality checks |
| 6. **Training** | **MAC** | LightGBM trained locally |
| 7. Model saved | Mac | `models/zl_baseline_v1.txt` |

**The baseline training ran on Mac, not BQ. ✅**

---

## ❌ WHAT WE DID NOT DO

- ❌ No BQML models created
- ❌ No `ML.PREDICT()` calls
- ❌ No training in BigQuery

---

## 📋 BIGQUERY RESPONSIBILITIES

**DO in BigQuery:**
- Store raw data (Databento, FRED, weather)
- Calculate features (TA indicators, rolling stats)
- Stamp regimes
- Create training-ready views (with targets, splits)
- Store predictions (from Mac)
- Serve API views (for Vercel)

**DO NOT in BigQuery:**
- Train models (use Mac)
- Run inference (use Mac)
- Hyperparameter tuning (use Mac)

---

## 📋 MAC RESPONSIBILITIES

**DO on Mac:**
- Pull training data from BQ (CSV/Parquet)
- Train all models (LightGBM, TFT, etc.)
- Hyperparameter tuning (Optuna)
- SHAP analysis
- Generate predictions
- Push predictions back to BQ

---

## 🔗 DATA HANDOFF POINTS

### BQ → Mac (Training Data)
```python
# Pull from BQ view
query = "SELECT * FROM `cbi-v14.training.vw_zl_1m_v1`"
df = client.query(query).to_dataframe()
# OR
bq extract --destination_format=CSV cbi-v14:training.vw_zl_1m_v1 gs://bucket/training.csv
```

### Mac → BQ (Predictions)
```python
# Push predictions to BQ
job = client.load_table_from_dataframe(predictions_df, 'cbi-v14.forecasts.zl_forecasts_daily')
```

---

## ✅ CURRENT STATE

```
BigQuery:
├── market_data.databento_futures_ohlcv_1d  ✅ (6,034 rows - ZL + MES)
├── features.zl_daily_v1                    ✅ (3,936 rows - with TA)
├── training.regime_lookup                  ✅ (7 regimes)
├── training.vw_zl_1m_v1                    ✅ (view for export)
└── forecasts.* (empty - awaiting predictions)

Mac:
├── Quant Check Plan/scripts/ingest_zl_v1.py      ✅
├── Quant Check Plan/scripts/train_baseline_v1.py ✅
└── Quant Check Plan/models/zl_baseline_v1.txt    ✅ (trained model)
```

**The workflow is correct. Training happened on Mac, calculations in BQ.**

