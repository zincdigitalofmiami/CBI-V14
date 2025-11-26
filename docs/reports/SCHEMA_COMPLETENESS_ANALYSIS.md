---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Schema Completeness Analysis
**Date:** November 18, 2025  
**Status:** Mixed State - Legacy + New Architecture

---

## 🎯 Executive Summary

**Current Situation:** You have a **mixed state** - legacy tables from previous work exist alongside the new architecture that hasn't been deployed yet.

**Why some tables have data:**
- Legacy tables from previous iterations (before MASTER_PLAN redesign)
- 654 tables exist across 43 datasets (mostly old/backup datasets)
- Only 8 of your 11 NEW datasets exist, with partial table coverage

**Do we have everything defined?**
- ✅ YES - All schemas, views, and features are defined in files
- ❌ NO - They haven't been deployed to BigQuery yet
- 📋 Deployment will create the complete new architecture

---

## 📊 What Exists vs. What's Defined

### Schema Definitions (Files)

| Component | Defined | Location |
|-----------|---------|----------|
| **Tables** | 55 tables | `PRODUCTION_READY_BQ_SCHEMA.sql` |
| **Overlay Views** | 31 views | `scripts/deployment/create_overlay_views.sql` |
| **Datasets** | 12 datasets | `deploy_bq_schema.sh` |
| **Total Objects** | **98 objects** | Ready to deploy |

### Current BigQuery State

| Component | Current | Status |
|-----------|---------|--------|
| **Datasets** | 43 total | 35 legacy, 8 new/partial |
| **Tables** | 654 total | Mostly legacy/backup |
| **Expected Tables** | 55 NEW | Only 0-18 per dataset exist |
| **Missing Tables** | 37+ tables | Need deployment |

---

## 🔍 Detailed Breakdown

### Dataset Status

#### ✅ Exist (Partial Coverage)
1. **market_data** - Has 4 legacy tables, missing 9 NEW tables
2. **raw_intelligence** - Has 7 legacy tables, missing 10+ NEW tables
3. **signals** - Has 1 legacy table, missing 5 NEW tables
4. **features** - Has 4 legacy tables, missing master_features (NEW)
5. **training** - Has 18 legacy tables, missing 0 NEW tables (good!)
6. **predictions** - Has 4 legacy tables, missing NEW prediction tables
7. **monitoring** - Has 1 legacy table, missing model_performance (NEW)
8. **neural** - Has 1 legacy table, missing feature_vectors (NEW)
9. **regimes** - EXISTS but 0 tables (new dataset, empty)

#### ❌ Missing (Need Creation)
10. **drivers** - Dataset doesn't exist (2 tables needed)
11. **dim** - Dataset doesn't exist (3 tables needed)
12. **ops** - Dataset doesn't exist (2 tables needed)

#### ⚠️ Legacy (35 datasets to clean up later)
- archive, archive_backup_20251115, bkp, curated, dashboard, etc.
- Contains 600+ legacy tables
- Should be archived/deleted after new deployment validated

---

## 📋 What's Missing (Need Deployment)

### Missing Datasets (3)
1. `dim` - Reference data and metadata
2. `drivers` - Primary drivers and meta-drivers
3. `ops` - Operations and data quality

### Missing Tables (37+)

#### market_data (9 missing)
- ❌ databento_futures_ohlcv_1m
- ❌ databento_futures_ohlcv_1d
- ❌ databento_futures_continuous_1d
- ❌ roll_calendar
- ❌ futures_curve_1d
- ❌ cme_indices_eod
- ❌ fx_daily
- ❌ orderflow_1m
- ❌ yahoo_zl_historical_2000_2010

#### raw_intelligence (10 missing)
- ❌ fred_economic
- ❌ eia_biofuels
- ❌ usda_granular
- ❌ weather_segmented
- ❌ weather_weighted
- ❌ cftc_positioning
- ❌ policy_events
- ❌ volatility_daily
- ❌ news_intelligence
- ❌ news_bucketed

#### signals (5 missing)
- ❌ calendar_spreads_1d
- ❌ crush_oilshare_daily
- ❌ energy_proxies_daily
- ❌ calculated_signals
- ❌ hidden_relationship_signals
- ❌ big_eight_live (CRITICAL)

#### features (1 missing)
- ❌ master_features (CRITICAL - 400+ columns)

#### neural (1 missing)
- ❌ feature_vectors

#### monitoring (1 missing)
- ❌ model_performance

#### drivers (2 missing - entire dataset)
- ❌ primary_drivers
- ❌ meta_drivers

#### dim (3 missing - entire dataset)
- ❌ instrument_metadata
- ❌ production_weights
- ❌ crush_conversion_factors

#### ops (2 missing - entire dataset)
- ❌ data_quality_events
- ❌ ingestion_runs

### Missing Views (31 overlay views)
- ❌ 17 API overlay views (api.vw_futures_overlay_*)
- ❌ 5 Prediction overlay views (predictions.vw_zl_*_latest)
- ❌ 1 Regime overlay view (regimes.vw_live_regime_overlay)
- ❌ 5 Compatibility views (training.vw_zl_training_*)
- ❌ 1 Signals composite view (signals.vw_big_seven_signals)
- ❌ 2 MES overlay views (features.vw_mes_*)

---

## ✅ What IS Complete (Defined in Files)

### 1. Complete Schema Definition
**File:** `PRODUCTION_READY_BQ_SCHEMA.sql` (55 tables)

**Covers:**
- All 12 datasets
- 55 production tables
- Full 400+ column master_features
- All training tables (5 ZL + 12 MES horizons)
- Hidden intelligence tables
- News intelligence tables
- Regime support tables

### 2. Complete Overlay Views
**File:** `scripts/deployment/create_overlay_views.sql` (31 views)

**Covers:**
- API-facing views for dashboard
- Prediction overlay views
- Regime overlay views
- Compatibility views for training
- MES intraday/daily aggregations

### 3. Complete Migration Scripts
- `migrate_master_features.py` - Column mapping logic
- Dry-run and force modes
- Idempotent execution

### 4. Complete Validation Scripts
- Pre-flight validation (6 checks)
- Post-deployment monitoring (5 phases)
- Environment scanning

---

## 🤔 Why the Mixed State?

### Historical Context

1. **Previous Architecture (Pre-MASTER_PLAN)**
   - You had tables from earlier iterations
   - Different naming conventions (no prefixes)
   - Multiple backup datasets created during migrations
   - 654 legacy tables across 43 datasets

2. **MASTER_PLAN Redesign (Current)**
   - Complete re-architecture with venue-pure approach
   - New naming: prefixed columns, organized datasets
   - 55 NEW tables across 12 datasets
   - Not deployed yet (waiting for this deployment)

3. **Result: Overlap**
   - Some datasets exist with old tables
   - New tables not created yet
   - 35 legacy/backup datasets cluttering the project

---

## 🚀 Deployment Will Create

### Phase 1: Schema
- Create 3 missing datasets (dim, drivers, ops)
- Create 37+ missing tables
- Update existing datasets with new tables
- Apply labels to all 12 datasets

### Phase 2: Folders
- Create live data folders on external drive

### Phase 3: Overlay Views
- Create all 31 overlay views
- API, prediction, regime, compatibility views

### Phase 4: Data Migration
- Migrate master_features_canonical → master_features
- Apply column prefixing
- Populate regime tables

### Phase 5: Validation
- Verify all 55 tables exist
- Verify all 31 views exist
- Verify data integrity

---

## 📊 Post-Deployment State

### After deployment completes:

**NEW Architecture (Production)**
- 12 datasets (labeled and organized)
- 55 tables (with proper prefixes)
- 31 overlay views
- Clean, documented structure

**Legacy Architecture (Archive)**
- 35 legacy datasets (can be deleted after validation)
- 654 legacy tables (backup for rollback if needed)

**Recommendation:** After 30 days of successful operation, archive/delete legacy datasets.

---

## ✅ Completeness Checklist

### Defined in Files (100%)
- [x] All 55 tables defined in PRODUCTION_READY_BQ_SCHEMA.sql
- [x] All 31 views defined in create_overlay_views.sql
- [x] All 12 datasets defined in deploy_bq_schema.sh
- [x] Migration scripts ready
- [x] Validation scripts ready
- [x] Monitoring hooks ready

### Deployed to BigQuery (0%)
- [ ] 3 missing datasets not created
- [ ] 37+ missing tables not created
- [ ] 31 overlay views not created
- [ ] Data migration not executed
- [ ] Labels not applied

### After Running Deployment (100%)
- [ ] All datasets created
- [ ] All tables created
- [ ] All views created
- [ ] Data migrated
- [ ] Labels applied
- [ ] Validation passed

---

## 🎯 Summary

**Question 1: Why did some tables have data and some did not?**

**Answer:** 
- Tables with data = Legacy tables from previous iterations
- Tables without data = New architecture not deployed yet
- Mixed state is normal pre-deployment

**Question 2: Do we have every single schema, view, feature available?**

**Answer:**
- ✅ **YES in files** - Everything is defined and ready
- ❌ **NO in BigQuery** - Not deployed yet
- 🚀 **After deployment** - Everything will exist
- 📍 **Region mandate:** All new objects must live in `us-central1`; migration in progress to align entirely with that region.

**Current Completeness:**
- **Defined:** 100% (55 tables + 31 views = 86 objects)
- **Deployed:** ~40% (legacy tables, not the new architecture)
- **After deployment:** 100%

---

**Next Action:** Run `./scripts/deployment/deploy_bq_schema.sh` to deploy the complete new architecture.

**Estimated Time:** 15 minutes for Phase 1 (schema + labels)
