# Deployment Phase 1 Results
**Date:** 2025-11-18 20:23:44  
**Project:** CBI-V14  

---

## Phase 1: Schema Deployment Validation

============================================================
CBI-V14 BigQuery Deployment Validation
Phase: 1
============================================================
Project: cbi-v14
Location: us-central1
Date: 2025-11-18 20:23:45
============================================================

📁 Validating Datasets...
------------------------------------------------------------
✅ market_data
✅ raw_intelligence
✅ signals
✅ features
✅ training
✅ regimes
✅ drivers
✅ neural
✅ predictions
✅ monitoring
✅ dim
✅ ops

📊 Validating Critical Tables...
------------------------------------------------------------

market_data:
  ✅ databento_futures_ohlcv_1m (0 rows, 16 cols) 📅🔗
  ✅ databento_futures_ohlcv_1d (0 rows, 14 cols) 📅🔗
  ✅ databento_futures_continuous_1d (0 rows, 14 cols) 📅🔗
  ✅ yahoo_zl_historical_2000_2010 (0 rows, 8 cols) 📅

signals:
  ✅ big_eight_live (0 rows, 17 cols) 📅
  ✅ crush_oilshare_daily (0 rows, 12 cols) 📅
  ✅ hidden_relationship_signals (0 rows, 16 cols) 📅

features:
  ✅ master_features (0 rows, 57 cols) 📅🔗

training:
  ✅ regime_calendar (0 rows, 4 cols) 📅
  ✅ regime_weights (0 rows, 5 cols) 
  ✅ zl_training_prod_allhistory_1w (0 rows, 5 cols) 📅🔗
  ✅ mes_training_prod_allhistory_1min (0 rows, 5 cols) 📅🔗

regimes:
  ✅ market_regimes (0 rows, 9 cols) 📅🔗

ops:
  ✅ ingestion_runs (0 rows, 8 cols) 📅🔗
  ✅ data_quality_events (0 rows, 10 cols) 📅🔗

============================================================
VALIDATION SUMMARY
============================================================
✅ PASS - datasets
✅ PASS - tables

============================================================
✅ ALL VALIDATIONS PASSED - Deployment Ready!
============================================================

**Status:** ✅ PASS - Datasets and tables created successfully
