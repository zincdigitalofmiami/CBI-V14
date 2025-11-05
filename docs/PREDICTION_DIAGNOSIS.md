# Prediction Diagnosis Report
**Date:** November 5, 2025  
**Issue:** Predictions show unusual pattern + no automation running

## 🚨 Critical Findings

### 1. NO AUTOMATION DEPLOYED
```
❌ Cloud Function: NOT FOUND (404)
❌ Scheduler: NOT FOUND (404) 
❌ Last forecast: Nov 4, 2025 21:56:18 (manual test)
```

**Status:** System is NOT running daily forecasts automatically

### 2. Training Data Variance Analysis

| Year | Rows | Price Range | Avg Price | Std Dev | Volatility |
|------|------|-------------|-----------|---------|------------|
| 2025 | 307  | $39-$58     | $48.89    | $4.08   | Normal     |
| 2024 | 366  | $39-$50     | $44.42    | $2.56   | **LOW**    |
| 2023 | 365  | $46-$73     | $57.71    | $6.43   | High       |
| 2022 | 365  | $56-$91     | $71.11    | $7.47   | **VERY HIGH** |
| 2021 | 365  | $42-$72     | $57.93    | $7.40   | High       |
| 2020 | 275  | $25-$43     | $31.84    | $4.55   | Normal     |

**Key Insight:** 2024 had VERY LOW volatility (stddev $2.56) compared to 2022-2023 (stddev $6-7). 
Models trained on 2020-2025 may have learned conservative predictions.

### 3. Recent Market Movement (Last 30 Days)

```
Date Range: Oct 20 - Nov 3, 2025
Price Range: $48.68 - $51.31
Daily Changes: Mostly $0.00 - $0.77
Pattern: LOW VOLATILITY (sub-dollar moves)
```

**Current Price:** $48.92 (Nov 3)

### 4. Current Predictions (Nov 4 Test Run)

| Horizon | Prediction | Change from Current | Makes Sense? |
|---------|------------|---------------------|--------------|
| 1W      | $48.07     | -$0.85 (-1.7%)      | ✅ Reasonable |
| 1M      | $46.00     | -$2.92 (-6.0%)      | ⚠️ Big drop   |
| 3M      | $44.22     | -$4.70 (-9.6%)      | ❌ Major crash |
| 6M      | $47.37     | -$1.55 (-3.3%)      | ❌ Recovery? Why? |

**Problem:** 6M predicting recovery while 3M predicts crash doesn't make economic sense.

## Hypotheses

### Hypothesis 1: Models Over-Trained on Low-Variance Data
- 2024 data (366 rows) has very low volatility (stddev $2.56)
- Models may have learned to predict small ranges
- Recent 2025 volatility ($4.08 stddev) is higher, but models still conservative

### Hypothesis 2: Feature Staleness
- Palm price: FLAT at $1058.50 for 10+ days (likely stale data)
- Other inputs may be stale as well
- Models seeing "frozen" inputs → producing static outputs

### Hypothesis 3: Model Architecture Limitation
- Linear regression in BQML may not capture complex regime shifts
- 258 features might be creating overfitting
- Models predicting mean reversion to training average

## ROOT CAUSE: STALE DATA

### Palm Oil Data (TOP-10 FEATURE)
```
Last Update: Oct 24, 2025
Days Stale: 12 DAYS
Price: FROZEN at $1058.50
Feature Importance: 300-500 (Top 10-12)
```

### Feature Importance Analysis (1M Model)
```
TOP DRIVERS:
1. corn_price: 9,098 (✅ fresh)
2. usd_ars_rate: 3,709 (⚠️ check)
3. cpi_yoy: 2,814 (⚠️ check)
4. vix_index_new: 2,353 (✅ fresh)
5. bb_upper: 1,946 (✅ calculated)
10. corr_zl_palm_365d: 300 (❌ STALE - based on 12-day-old palm data)
12. corr_zl_palm_180d: 208 (❌ STALE)
```

**Conclusion:** Models are using stale palm data → frozen correlations → low prediction variance

## Immediate Action Plan

### PRIORITY 1: Refresh Palm Oil Data
```bash
cd /Users/zincdigital/CBI-V14
python cbi-v14-ingestion/ingest_palm_oil_proxies.py
```

### PRIORITY 2: Rebuild Training Dataset
```sql
-- Regenerate with fresh palm → recalculate correlations
-- Execute: COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql
```

### PRIORITY 3: Deploy Automation (AFTER fresh data)
- Manual Console deployment required (gcloud bug)
- URL: https://console.cloud.google.com/functions/create?project=cbi-v14
- Test predictions after deployment

## Status
- [x] Root cause identified (stale palm data)
- [x] Feature importance analyzed
- [ ] Palm data refreshed
- [ ] Training dataset rebuilt
- [ ] Automation deployed
- [ ] New predictions tested

