# 🚀 Phase 2: Next Steps - Complete Execution Plan
**Date:** November 24, 2025  
**Status:** Ready to execute  
**Goal:** Complete data pull, feature expansion, and baseline retraining

---

## ✅ WHAT WE JUST COMPLETED

1. **Databento Options Integration**
   - ✅ Added ZL options: OZL.OPT, OZS.OPT, OZM.OPT
   - ✅ Added MES options: ES.OPT, MES.OPT
   - ✅ Updated `submit_granular_microstructure.py` with all options symbols
   - ✅ Confirmed symbol formats from DATABENTO_PLAN_VALIDATION.md
   - ✅ CME Options Add-On confirmed ENABLED

2. **Documentation Updates**
   - ✅ Updated PHASE2_DATA_PULL_PLAN.md with options
   - ✅ Feature expansion plan consolidated into ZL_EXECUTION_PLAN.md
   - ✅ Created DATABENTO_SYMBOL_FORMAT_REFERENCE.md

---

## 📋 IMMEDIATE NEXT STEPS (In Order)

### Step 1: Submit Databento Options Jobs ⏰ **DO THIS FIRST**

**Script:** `scripts/ingest/submit_granular_microstructure.py`

**What it submits:**
- **Futures:** ZL.FUT, MES.FUT (HEAVY - full microstructure)
- **Futures:** ES.FUT, ZS.FUT, ZM.FUT, ZC.FUT, CL.FUT, HO.FUT (LIGHT - reduced)
- **Options:** OZL.OPT, OZS.OPT, OZM.OPT, ES.OPT, MES.OPT (NEW!)

**Run:**
```bash
cd /Users/zincdigital/CBI-V14
export DATABENTO_API_KEY="your_key"
python scripts/ingest/submit_granular_microstructure.py
```

**Output:**
- Job IDs printed to console
- Download from https://databento.com/portal/batch/jobs when complete

---

### Step 2: Pull Fresh FRED Data (2010-2025) ⏰ **DO THIS SECOND**

**Script:** `Quant Check Plan/scripts/collect_fred_data.py`

**What it does:**
- Pulls 40+ FRED series (VIXCLS, DFF, DGS10, CPIAUCSL, etc.)
- Full history from 2010-01-01 to present
- Rate-limited (1 req/sec)
- Loads to `raw_intelligence.fred_economic`

**Run:**
```bash
cd /Users/zincdigital/CBI-V14
export FRED_API_KEY="your_key"
python "Quant Check Plan/scripts/collect_fred_data.py"
```

**Verify:**
```sql
SELECT 
  series_id, 
  COUNT(*) as rows, 
  MIN(date) as min_date, 
  MAX(date) as max_date
FROM `cbi-v14.raw_intelligence.fred_economic`
GROUP BY series_id
ORDER BY series_id
```

---

### Step 3: Load Databento Data to BigQuery ⏰ **DO THIS THIRD**

**Script:** `Quant Check Plan/scripts/load_databento_csv.py`

**What it does:**
- Loads Databento CSV files to BigQuery
- Auto-detects schema from filename
- Idempotent MERGE on (date, symbol, instrument_id)
- Handles all schemas: ohlcv, bbo, tbbo, mbp, mbo, statistics

**Run:**
```bash
# After downloading Databento jobs
python "Quant Check Plan/scripts/load_databento_csv.py" /path/to/databento/csvs/
```

**Tables created:**
- `market_data.databento_futures_ohlcv_1d`
- `market_data.databento_futures_ohlcv_1h`
- `market_data.databento_futures_ohlcv_1m`
- `market_data.databento_bbo_1s`
- `market_data.databento_tbbo`
- `market_data.databento_mbp_1`
- `market_data.databento_mbp_10`
- `market_data.databento_mbo`
- `market_data.databento_stats`

---

### Step 4: Expand Feature Calculation ⏰ **DO THIS FOURTH**

**Script:** Update `Quant Check Plan/scripts/ingest_zl_v1.py` → `ingest_zl_v2.py`

**New features to add:**
1. **Crush Margin** (from ZS, ZM, ZL)
   - `crush_margin_gross`
   - `crush_margin_21d_ma`
   - `crush_margin_percentile_90d`
   - `crush_margin_zscore_63d`

2. **Cross-Asset Features** (from ZS, ZM, CL, HO)
   - Returns, volatility, correlations, betas

3. **FRED Macro Features** (from `raw_intelligence.fred_economic`)
   - VIX level, MA, z-score
   - Fed funds rate
   - Yield curve spread
   - USD index

4. **Options-Based Features** (from OZL.OPT, OZS.OPT, OZM.OPT)
   - `zl_implied_vol_30d`
   - `zl_vol_surface_slope`
   - `zl_put_call_ratio`
   - `zl_gamma_exposure`
   - `zl_skew`
   - `crush_implied_vol`

5. **Enhanced TA**
   - Bollinger Bands
   - MACD
   - ATR
   - Stochastic
   - Volume z-score

**Target:** 50-64 features total (up from 9)

---

### Step 5: Retrain Baseline v2 ⏰ **DO THIS FIFTH**

**Script:** Update `Quant Check Plan/scripts/train_baseline_v1.py` → `train_baseline_v2.py`

**Improvements:**
- Use TimeSeriesSplit (5 folds) instead of simple train/val split
- More trees (3000) with patience (100)
- Lower learning rate (0.01)
- Expanded feature set (50-64 features)

**Target metrics:**
- MAE: <5.0% (down from 6.16%)
- Direction Accuracy: >54% (up from 49.3%)
- Best Iteration: 500+ (up from 9)

---

## 📊 DATA STATUS CHECKLIST

### Databento Futures
- [ ] ZL.FUT - Check if already in BQ
- [ ] ZS.FUT - Need to pull
- [ ] ZM.FUT - Need to pull
- [ ] CL.FUT - Need to pull
- [ ] HO.FUT - Need to pull
- [ ] ES.FUT - Need to pull

### Databento Options (NEW)
- [ ] OZL.OPT - Submit job
- [ ] OZS.OPT - Submit job
- [ ] OZM.OPT - Submit job
- [ ] ES.OPT - Submit job
- [ ] MES.OPT - Submit job

### FRED Data
- [ ] VIXCLS - Pull 2010-2025
- [ ] DFF - Pull 2010-2025
- [ ] DGS10 - Pull 2010-2025
- [ ] CPIAUCSL - Pull 2010-2025
- [ ] All other series - Pull 2010-2025

### BigQuery Tables
- [ ] `raw_intelligence.fred_economic` - Load FRED data
- [ ] `market_data.databento_futures_ohlcv_1d` - Load Databento futures
- [ ] `market_data.databento_futures_ohlcv_1h` - Load Databento futures
- [ ] `market_data.databento_futures_ohlcv_1m` - Load Databento futures
- [ ] `market_data.databento_options_ohlcv_1d` - Load Databento options (NEW)
- [ ] `features.zl_daily_v2` - Create with expanded features

---

## 🎯 SUCCESS CRITERIA

| Metric | Current (v1) | Target (v2) |
|--------|--------------|------------|
| Features | 9 | 50-64 |
| MAE | 6.16% | <5.0% |
| Direction Acc | 49.3% | >54% |
| Best Iteration | 9 | 500+ |
| Data Sources | 1 (ZL only) | 5+ (ZL, ZS, ZM, CL, HO, FRED, Options) |

---

## 📁 FILES TO CREATE/MODIFY

```
scripts/ingest/
├── submit_granular_microstructure.py  ✅ UPDATED (added ZL options)
└── validate_databento_options.py    ✅ UPDATED (added all options)

Quant Check Plan/scripts/
├── collect_fred_data.py              ✅ EXISTS (needs to run)
├── load_databento_csv.py             ✅ EXISTS (needs to run)
├── ingest_zl_v1.py                   ✅ EXISTS (needs expansion)
├── ingest_zl_v2.py                   ❌ CREATE (expanded features)
├── train_baseline_v1.py              ✅ EXISTS (needs improvement)
└── train_baseline_v2.py              ❌ CREATE (TimeSeriesSplit, more features)
```

---

## ⏱️ ESTIMATED TIMELINE

| Task | Time | Status |
|------|------|--------|
| Submit Databento options jobs | 5 min | ⏳ Pending |
| Pull FRED data (2010-2025) | 30 min | ⏳ Pending |
| Wait for Databento jobs | 1-24 hrs | ⏳ Pending |
| Load Databento to BQ | 1 hr | ⏳ Pending |
| Expand feature calculation | 2 hrs | ⏳ Pending |
| Retrain v2 | 30 min | ⏳ Pending |
| **Total** | **~5-26 hrs** | |

---

## 🚀 READY TO START

**First command:**
```bash
cd /Users/zincdigital/CBI-V14
python scripts/ingest/submit_granular_microstructure.py
```

**Then proceed through steps 2-5 in order.**

---

**Status:** ✅ All options added, plan updated, ready to execute!

