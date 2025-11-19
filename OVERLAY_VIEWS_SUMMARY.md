# Super-Optimized Overlay Views Summary
**Date:** November 18, 2025  
**Status:** Documented in Fresh Start Master Plan

## 📊 Overview

The overlay layer provides curated, dashboard-ready views that eliminate complex joins at query time. These views combine raw tables into single-query endpoints for the Vercel dashboard and training exports.

## ✅ Components Documented

### 1. API-Facing Overlay Views
- **`api.vw_futures_overlay_{horizon}`** - 17 views (5 ZL + 12 MES horizons)
  - Combines continuous futures + drivers + macro + regime context
  - Single query per horizon instead of 5+ table joins

- **`predictions.vw_zl_{horizon}_latest`** - 5 views (ZL horizons)
  - Adds prediction metadata (model version, regime tags) to raw predictions
  - Latest 90 days with full context

### 2. Regime Overlay Views
- **`regimes.vw_live_regime_overlay`** - 1 view
  - Big 8 + hidden drivers regime spine
  - Collapses VIX stress, biofuel policy, trade risk into single daily row
  - Includes override_flag logic for hidden relationships

### 3. Compatibility Views
- **`training.vw_zl_training_prod_allhistory_{horizon}`** - 5 views
  - Passthrough views for backward compatibility during migration
  - Legacy applications continue working

### 4. Signals-Driver Composite Views
- **`signals.vw_big_seven_signals`** - 1 view
  - Combines crush, spreads, energy, hidden composite
  - Predecessor to Big 8 (maintained for compatibility)
  - Weighted composite score

- **`signals.hidden_relationship_signals`** - ✅ Table already in schema
  - Hidden cross-domain intelligence signals
  - Feeds into Big 8 and regime overlays

### 5. MES Overlay Views
- **`features.vw_mes_intraday_overlay`** - 1 view
  - Rolls up 1/5/15/30 minute tables into single wide dataset
  - Training exports read from this instead of joining 4+ tables

- **`features.vw_mes_daily_aggregated`** - 1 view
  - Intraday→daily aggregator (1h/4h, 1d/7d/30d)
  - Feeds features layer with daily aggregates

### 6. Big 8 Refresh Job
- **`scripts/sync/sync_signals_big8.py`** - Scheduled job
  - Runs every 15 minutes
  - Recalculates `signals.big_eight_live` with policy/trump/regime overrides
  - MERGE operation on `signal_timestamp`

## 📋 Total View Count

- **API Overlays:** 17 views (`api.vw_futures_overlay_*`)
- **Prediction Overlays:** 5 views (`predictions.vw_zl_*_latest`)
- **Regime Overlays:** 1 view (`regimes.vw_live_regime_overlay`)
- **Compatibility:** 5 views (`training.vw_zl_training_*`)
- **Signals Composite:** 1 view (`signals.vw_big_seven_signals`)
- **MES Overlays:** 2 views (`features.vw_mes_*`)

**Total: 31 overlay views** (plus 1 table: `signals.hidden_relationship_signals`)

## 🔄 Creation Order

1. **Base Tables** (via `PRODUCTION_READY_BQ_SCHEMA.sql`)
2. **Compatibility Views** (training.vw_*)
3. **Signals Composite Views** (vw_big_seven_signals)
4. **MES Overlay Views** (vw_mes_intraday_overlay, vw_mes_daily_aggregated)
5. **Regime Overlay View** (regimes.vw_live_regime_overlay)
6. **API Overlay Views** (api.vw_futures_overlay_*)
7. **Prediction Overlay Views** (predictions.vw_zl_*_latest)

## 📝 Next Steps

1. Create `scripts/deployment/create_overlay_views.sql` with all view definitions
2. Add `api` dataset creation to schema (or note it already exists)
3. Document Big 8 refresh job dependencies and schedule
4. Test view queries before dashboard deployment

---
**Status:** ✅ Documented in Fresh Start Master Plan  
**Location:** `docs/plans/FRESH_START_MASTER_PLAN.md` - Section: "SUPER-OPTIMIZED API-FACING OVERLAY LAYER"

