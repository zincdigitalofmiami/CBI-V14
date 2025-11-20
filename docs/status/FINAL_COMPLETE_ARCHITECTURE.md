---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# FINAL Complete Architecture - Validated & Ready
**Date**: November 18, 2025  
**Status**: ✅ DataBento validated, Trump scripts found, Schema locked  
**Next**: Deploy to BigQuery

---

## Validation Results Summary

Reference: For model horizons, data granularity, and how intraday special models integrate with daily main models, see `HORIZON_TRAINING_STRATEGY.md` (horizon registry + training workflows). For data‑plane details (ingestion/orchestration/serving) see `docs/plans/BIGQUERY_CENTRIC_MIGRATION_PLAN.md`.

### ✅ DataBento Coverage (29 Symbols Confirmed)

**Primary (5-min)**:
- ZL, MES

**Secondary (1-hour)**:
- ES, ZS, ZM, CL, NG, ZC, ZW, RB, HO, GC, SI, HG (core 12)
- 6E, 6B, 6J, 6C, 6A, 6S (FX futures 6)
- BZ, QM (additional energy 2)
- PA, PL (additional metals 2)
- ZR, ZO (rice, oats 2)
- LE, GF, HE (livestock 3)

**Total from DataBento**: **29 symbols**

### ❌ What's NOT on DataBento (Need Alternatives)

1. **Palm Oil** → Use Barchart/ICE/Yahoo (as Fresh Start says)
2. **RINs & Biofuels** → Use EIA/EPA (government data)
3. **Spot FX** (USD/CNY, USD/ARS, USD/MYR) → Use FRED/Yahoo
4. **Other Vegoils** (rapeseed, sunflower) → Use World Bank Pink Sheet

### ✅ Existing Scripts Found

1. **`trump_action_predictor.py`** ✅
2. **`zl_impact_predictor.py`** ✅
3. **`collect_policy_trump.py`** ✅

**Action**: Integrate these into architecture (already built!)

---

## Complete Data Source Matrix

| Data Type | Source | Symbols/Series | Frequency | Table |
|-----------|--------|----------------|-----------|-------|
| **Futures OHLCV** | DataBento | 14 core (+ grains/FX/equity/energy additions) | 1m/daily | `market_data.databento_futures_ohlcv_1m`, `_1d` |
| **FX Futures** | DataBento | 6 pairs | 1hr | Same table |
| **Additional Futures** | DataBento | 9 (livestock/metals/energy) | 1hr | Same table |
| **Palm Oil** | Barchart/ICE | 1 | Daily | `market_data.palm_oil_daily` |
| **Other Vegoils** | World Bank | 3 (rapeseed/sunflower/canola) | Daily | `market_data.oils_competing_daily` |
| **Spot FX** | FRED/Yahoo | 3 (CNY/ARS/MYR) | Daily | `market_data.fx_spot_daily` |
| **Macro Economic** | FRED | 60 series | 4hr | `raw_intelligence.fred_economic` |
| **CME CVOL Indices** | CME CVOL (licensed) | SOVL (ZL), SVL (ZS) | Daily | `raw_intelligence.cme_cvol_indices` |
| **RINs & Biofuels** | EIA/EPA | 15+ series | Daily | `raw_intelligence.eia_biofuels_granular` |
| **USDA Granular** | USDA | 20+ series | Weekly | `raw_intelligence.usda_granular` |
| **Weather Raw** | NOAA/INMET/SMN | By area code | Daily | `raw_intelligence.weather_segmented` |
| **Weather Aggregated** | Calculated | Production-weighted | Daily | `raw_intelligence.weather_aggregated` |
| **CFTC** | CFTC API | 10+ commodities | 8hr | `raw_intelligence.cftc_positioning` |
| **News Bucketed** | NewsAPI/Alpha | All topics | 1hr/15min | `raw_intelligence.news_bucketed` |
| **Trump/Policy** | ScrapeCreators | Truth Social/White House | 15min | `raw_intelligence.policy_trump_signals` |
| **Alpha Insider** | Alpha Vantage | 8+ stocks | Daily | `raw_intelligence.alpha_insider_transactions` (Deprecated for futures price proxies) |
| **Alpha Analytics** | Alpha Vantage | Fixed + sliding | Daily | `raw_intelligence.alpha_analytics` (Deprecated where DataBento futures exist) |
| **Volatility** | Calculated | VIX + realized | Daily | `raw_intelligence.volatility_daily` |
| **Regimes** | Calculated | All types | Hourly | `regimes.market_regimes` |
| **Drivers** | Calculated | Correlations | Daily | `drivers.primary_drivers` |
| **Meta-Drivers** | Calculated | Impact chains | Daily | `drivers_of_drivers.meta_drivers` |
| **Signals** | Calculated | Technical indicators | Hourly | `signals.calculated_signals` |
| **Big 8 Live** | Calculated | 8 pillars | 15min | `signals.big_eight_live` |
| **Master Features** | Merged | Canonical table | Daily | `features.master_features_2000_2025` |
| **Neural Vectors** | Assembled | Training features | Daily | `neural.feature_vectors` |

### Additions for ZL Procurement & MES Microstructure

- Grains complex breadth (ZC, ZW, KE) → daily OHLCV in `market_data.databento_futures_ohlcv_1d`.
- FX risk channels (6L/BRL, CNH) → daily OHLCV in `market_data.databento_futures_ohlcv_1d`.
- Equity risk proxies (NQ/MNQ, RTY/M2K) → 1m + daily OHLCV for router features.
- Energy spreads (CL, HO, RB) → daily OHLCV for biofuel parity.
- CME CVOL: SOVL, SVL → `raw_intelligence.cme_cvol_indices` (index feed, not futures).
- MES microstructure: MBP‑10 depth, trades, quotes/TBBO via GLBX.MDP3 → extend `market_data.orderflow_1m` and align with OHLCV.

**Total**: **23 tables**, **~100+ data series**

---

## Collection Schedule (Final)

### Every 5 Minutes
```
✅ DataBento: ZL, MES (primary symbols)
```

### Every 15 Minutes  
```
✅ News Breaking: ZL critical
✅ Trump/Policy: Truth Social, White House (EXISTING SCRIPTS!)
```

### Every Hour
```
✅ DataBento: ES (modeling)
✅ DataBento: ZS, ZM, CL, NG, ZC, ZW, RB, HO, GC, SI, HG (secondary)
✅ DataBento: 6E, 6B, 6J, 6C, 6A, 6S (FX futures)
✅ DataBento: BZ, QM, PA, PL (additional energy/metals)
✅ News General: All topics
✅ Alpha Sentiment: Hourly
```

### Every 4 Hours
```
✅ FRED: 60 macro series (existing, don't touch)
```

### Every 8 Hours
```
✅ CFTC: Positioning data
```

### Daily
```
✅ Palm Oil: Barchart/ICE
✅ Spot FX: USD/CNY, USD/ARS, USD/MYR (FRED/Yahoo)
✅ Weather: US/BR/AR segmented by area code
✅ EIA Biofuels: Check for updates (weekly actuals)
✅ Alpha Insider: Biofuel/ag companies (ADM, BG, REX, GEVO, etc.)
✅ Alpha Analytics: Fixed + sliding windows
✅ Volatility: Calculate from OHLCV
✅ Regimes: Classify all types
✅ Drivers: Correlation analysis
✅ Signals: Calculate technicals
✅ Master Features: Assemble canonical table
```

### Weekly
```
✅ USDA: Granular exports (by destination), yields (by state)
```

---

## BigQuery Tables (23 Total)

### Dataset: market_data (5 tables)
1. `databento_futures_ohlcv_1m` - 29 symbols, 1-minute
2. `databento_futures_ohlcv_1d` - 29 symbols, daily
3. `palm_oil_daily` - Barchart/ICE palm
4. `oils_competing_daily` - World Bank vegoils
5. `fx_spot_daily` - FRED/Yahoo spot FX

### Dataset: raw_intelligence (11 tables)
6. `fred_economic` - EXISTING, don't modify
7. `eia_biofuels_granular` - RINs, biodiesel by PADD, ethanol, SAF
8. `usda_granular` - WASDE, exports by destination, yields by state
9. `weather_segmented` - US/BR/AR by area code
10. `weather_aggregated` - Production-weighted indices
11. `cftc_positioning` - COT data
12. `news_bucketed` - Topic/regime/correlation
13. `policy_trump_signals` - Trump predictor outputs (EXISTING SCRIPTS!)
14. `alpha_insider_transactions` - Insider buying/selling
15. `alpha_analytics` - Fixed + sliding window metrics
16. `volatility_daily` - VIX + realized vols

### Dataset: regimes (1 table)
17. `market_regimes` - All regime types

### Dataset: drivers (1 table)
18. `primary_drivers` - Direct factors

### Dataset: drivers_of_drivers (1 table)
19. `meta_drivers` - Impact chains

### Dataset: signals (2 tables)
20. `calculated_signals` - Technical indicators
21. `big_eight_live` - Big 8 pillars (15-min refresh)

### Dataset: features (1 table)
22. `master_features_2000_2025` - CANONICAL table (mirrors Parquet)

### Dataset: neural (1 table)
23. `feature_vectors` - Training features

---

## Critical Features Confirmed

### ✅ Palm Oil Coverage
**Source**: Barchart/ICE (NOT DataBento)
**Table**: `market_data.palm_oil_daily`
**Prefix**: `barchart_palm_`
**Critical**: PRIMARY substitution driver for ZL

### ✅ RINs & Biofuels Coverage
**Source**: EIA/EPA (NOT DataBento)
**Table**: `raw_intelligence.eia_biofuels_granular`
**Granularity**: PADD-level biodiesel, D4/D6 RINs, SAF
**Critical**: SAF policy shock pillar

### ✅ Trump/Policy Coverage
**Source**: Existing scripts! (`trump_action_predictor.py`, `zl_impact_predictor.py`)
**Table**: `raw_intelligence.policy_trump_signals`
**Collection**: Every 15 minutes (Truth Social, White House, USTR)
**Critical**: Policy shock pillar

### ✅ FX Coverage
**DataBento**: 6 FX futures (EUR, GBP, JPY, CAD, AUD, CHF)
**FRED/Yahoo**: Spot pairs for CNY, ARS, MYR
**Critical**: Trade transmission mechanism

---

## Data Authority Policy (Deprecations)

- Futures OHLCV (intraday + daily)
  - Authority: DataBento for all covered roots (2010→present)
  - Deprecate: Vendor/Alpha daily bars where an equivalent DataBento future exists.
  - Bridge: Yahoo ZL is retained for 2000–2010 only to complete history; prefer DataBento thereafter.

- Macro & risk series
  - Authority: FRED (rates, VIXCLS, credit) and CME CVOL for implied vol indices (SOVL, SVL).
  - Keep: FRED sources as canonical for macro overlays.

- Notes
  - Dashboards and training exports must source futures prices from DataBento tables, falling back to Yahoo ZL only for pre‑2010 slices.
  - Remove any joins to Alpha/Vendor price bars in features/training once DataBento coverage is confirmed.

### ✅ Weather Segmentation
**Collection**: By area code (not aggregated only)
**Aggregation**: Production-weighted in processing layer
**Critical**: Regional weather shock detection

### ✅ USDA Granularity
**Exports**: By destination (China vs EU)
**Yields**: By state (Illinois, Iowa, etc.)
**WASDE**: World vs US soyoil production/consumption
**Critical**: Isolate China demand

### ✅ Big 8 + Master Features
**big_eight_live**: 15-minute refresh, feeds dashboard
**master_features_2000_2025**: Canonical table, mirrors Parquet
**Critical**: Dashboard and training single source of truth

---

## Cost Projection (Month 12)

| Component | Size | Cost |
|-----------|------|------|
| DataBento futures 1m (29 symbols, 1yr retention) | 350 MB | $0.007 |
| DataBento futures 1d (29 symbols, 5yr retention) | 50 MB | $0.001 |
| Palm oil daily | 10 MB | $0.0002 |
| Competing oils daily | 5 MB | $0.0001 |
| FX spot daily | 5 MB | $0.0001 |
| EIA biofuels granular | 20 MB | $0.0004 |
| USDA granular | 50 MB | $0.001 |
| Weather segmented | 180 MB | $0.004 |
| Weather aggregated | 20 MB | $0.0004 |
| CFTC positioning | 24 MB | $0.0005 |
| News bucketed | 1.8 GB | $0.036 |
| Policy Trump signals | 100 MB | $0.002 |
| Alpha insider | 10 MB | $0.0002 |
| Alpha analytics | 20 MB | $0.0004 |
| Volatility daily | 10 MB | $0.0002 |
| Regimes | 50 MB | $0.001 |
| Drivers | 100 MB | $0.002 |
| Meta-drivers | 50 MB | $0.001 |
| Signals | 500 MB | $0.010 |
| Big 8 live | 50 MB | $0.001 |
| Master features | 2.0 GB | $0.040 |
| Neural vectors | 500 MB | $0.010 |
| **TOTAL** | **~5.9 GB** | **$0.12/month** |

**Still under 10 GB free tier** ✅

---

## What We Have Now

### ✅ Validated
- DataBento: 29 symbols working
- Trump scripts: Already exist
- FRED: Already working (don't touch)

### ✅ Missing Sources Identified
- Palm: Barchart/ICE (not DataBento)
- RINs: EIA/EPA (not DataBento)
- Other vegoils: World Bank (not DataBento)

### ✅ Schema Created
- `COMPLETE_BIGQUERY_SCHEMA.sql` (23 tables)
- Includes all Fresh Start layers
- Source prefixing preserved
- 2000-2010 historical bridge in master_features

---

## Ready to Deploy

**Files Created**:
1. ✅ `COMPLETE_BIGQUERY_SCHEMA.sql` - All 23 table DDLs
2. ✅ `DATABENTO_COVERAGE_RESULTS.md` - What DataBento has/doesn't have
3. ✅ `FINAL_COMPLETE_ARCHITECTURE.md` - This file
4. ✅ `AUDIT_REVIEW_REPORT.md` - Gap analysis (audit was correct)
5. ✅ Validation scripts in `scripts/validation/`

**Existing Scripts to Integrate**:
1. ✅ `scripts/predictions/trump_action_predictor.py`
2. ✅ `scripts/predictions/zl_impact_predictor.py`
3. ✅ `scripts/ingest/collect_policy_trump.py`

**Next Steps**:
1. Review `COMPLETE_BIGQUERY_SCHEMA.sql` (23 tables)
2. Deploy to BigQuery (run the SQL)
3. Create collection scripts for each source
4. Set up cron schedule
5. Deploy processing layers

**Ready when you are!** 🚀
