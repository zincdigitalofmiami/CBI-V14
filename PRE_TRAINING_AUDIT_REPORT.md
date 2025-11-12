# PRE-TRAINING AUDIT REPORT
**Date:** November 7, 2025  
**Table:** `cbi-v14.models_v4.full_220_comprehensive_2yr`  
**Model:** `bqml_1m_v5_5_dart_p10/p50/p90`  

## AUDIT SUMMARY: 18/24 PASS ✅ | 4 FAIL ❌ | 2 WARNING ⚠️

## ✅ PASSING AUDITS (18)

| Audit | Name | Result |
|-------|------|--------|
| 1 | Table Exists | ✅ Table exists |
| 2 | Column Count | ✅ 1,948 columns |
| 3 | Row Count | ✅ 482 rows |
| 4 | Target Column | ✅ target_1m exists |
| 5 | Date Column | ✅ date column exists |
| 9 | Timestamp Issues | ✅ No timestamp issues |
| 10 | Date Range | ✅ 2024-01-02 to 2025-11-06 |
| 11 | Duplicates | ✅ No duplicate dates |
| 12 | Target Distribution | ✅ Range: 31.32 to 57.54 |
| 13 | Critical NULLs | ✅ No NULLs in date/target_1m |
| 15 | DART Parameters | ✅ Valid DART params |
| 16 | Regularization | ✅ L1=0.5, L2=0.2 good for 1948 features |
| 17 | Sequential Split | ✅ 80/20 split is sequential |
| 18 | Quantiles | ✅ 0.1, 0.5, 0.9 are valid |
| 19 | Correlations | ✅ 60 correlation features found |
| 20 | Interactions | ✅ 426 interaction features found |
| 23 | Early Stopping | ✅ min_rel_progress=0.00005 is good |
| 24 | Memory Usage | ✅ 7.16 MB well within limits |

## ❌ FAILING AUDITS (4) - CRITICAL FIXES NEEDED

### 1. **AUDIT 8: String Columns** ❌
- **Issue:** 2 string columns found: `volatility_regime`, `yahoo_data_source`
- **Impact:** BQML will fail on string features
- **FIX:** Add to EXCEPT clause: `volatility_regime, yahoo_data_source`

### 2. **AUDIT 14: 100% NULL Columns** ❌
- **Issue:** Multiple columns are 100% NULL (e.g., trump_soybean_sentiment_7d, agg_close, agg_rsi_14)
- **Impact:** BQML will fail with "Failed to calculate mean" error
- **FIX:** Must identify and exclude ALL 100% NULL columns in EXCEPT clause

### 3. **AUDIT 22: Production Features** ❌
- **Issue:** Only 4 of 10 expected production features found
- **Impact:** Missing critical features like china_soybean_imports_mt, argentina_export_tax
- **FIX:** Verify production data join or accept reduced feature set

### 4. **AUDIT 6: Data Drift** (Skipped - column doesn't exist)
- **Issue:** palm_oil_spot_price column not found
- **Impact:** Cannot validate data drift
- **FIX:** Use alternative column or skip this check

## ⚠️ WARNING AUDITS (2)

### 1. **AUDIT 7: Monotonic Sanity** ⚠️
- **Issue:** RIN correlation with target is 0.197 (expected < -0.6)
- **Impact:** Monotonic constraint may be incorrect
- **FIX:** Review or remove monotonic constraint for RIN

### 2. **AUDIT 21: Yahoo Pivot** ⚠️
- **Issue:** Only 126 Yahoo columns found (expected 1,470)
- **Impact:** Most Yahoo symbols have no data
- **FIX:** Accept reduced symbol set or populate missing data

## CRITICAL ACTIONS BEFORE TRAINING

1. **IMMEDIATE (Blocking):**
   ```sql
   -- Add to EXCEPT clause in CREATE MODEL:
   EXCEPT(date, target_1m, volatility_regime, yahoo_data_source, 
          trump_soybean_sentiment_7d, agg_close, agg_rsi_14, 
          -- [ADD ALL OTHER 100% NULL COLUMNS HERE])
   ```

2. **RUN NULL DETECTION SCRIPT:**
   - Must identify ALL 100% NULL columns (likely 1,000+ columns)
   - Add all to EXCEPT clause

3. **REVIEW MONOTONIC CONSTRAINTS:**
   - Remove or adjust RIN constraint (currently positive correlation)

## TRAINING READINESS: ❌ NOT READY
**Reason:** Must fix string columns and 100% NULL columns before training can proceed.

## NEXT STEPS
1. ✅ Run comprehensive NULL column detection
2. ✅ Generate complete EXCEPT clause
3. ✅ Update CREATE MODEL statements with full EXCEPT clause
4. ✅ Remove/adjust monotonic constraints
5. ✅ Re-run audits to confirm all pass
6. ✅ Proceed with DART model training

