# COMPLETE FIX REVIEW - PRE-PHASE 2
## All Fixes That Must Be Applied Before Expanding to 220 Symbols

**Date:** November 7, 2025  
**Status:** Phase 1 Complete - Backup Done  
**Next:** Phase 2 - Apply All Fixes Before Expansion

---

## ✅ FIXES ALREADY IN PLACE (Keep As-Is)

### 1. Timestamp Conversion ✅
**Location:** Line 90
```sql
DATE(TIMESTAMP_MICROS(CAST(date/1000 AS INT64))) as date
```
**Status:** ✅ CORRECT - Converts nanoseconds to microseconds  
**Action:** Keep as-is

**Filter:** Lines 101-102
```sql
AND date > 1704067200000000000  -- 2024-01-01 in NANOSECONDS
AND date < 1767225600000000000  -- 2026-01-01 in NANOSECONDS
```
**Status:** ✅ CORRECT - Uses nanosecond values  
**Action:** Keep as-is

---

### 2. Table Structure ✅
**Location:** Line 75
```sql
CREATE OR REPLACE TABLE `cbi-v14.models_v4.baseline_1m_comprehensive_2yr` AS
```
**Status:** ✅ CORRECT - No PARTITION BY or CLUSTER BY  
**Action:** Keep as-is

**Final SELECT:** Lines 578-586
```sql
SELECT
  p.*,
  y.* EXCEPT(date),
  c.* EXCEPT(date),
  i.* EXCEPT(date)
FROM base_production p
LEFT JOIN yahoo_pivoted y ON p.date = y.date
LEFT JOIN correlations c ON p.date = c.date
LEFT JOIN interactions i ON p.date = i.date;
```
**Status:** ✅ CORRECT - No ORDER BY (would conflict with partitioning)  
**Action:** Keep as-is

---

### 3. NULLIF for Division ✅
**Location:** Lines 553-555, 562-563
```sql
p.soyb_close / NULLIF(p.corn_etf_close, 0) as soyb_corn_ratio,
y.cl_f_close / NULLIF(y.dx_y_nyb_close, 0) as crude_dxy_ratio,
y.vix_close / NULLIF(y.gspc_close, 0) as vix_spx_ratio,
p.soyb_atr_14 / NULLIF(y.vix_close, 0) as soyb_vol_to_vix,
y.cl_f_atr / NULLIF(y.vix_close, 0) as crude_vol_to_vix,
```
**Status:** ✅ CORRECT - Prevents division by zero  
**Action:** Keep pattern for all divisions

---

### 4. Window Function Date Ordering ✅
**Location:** Lines 504-531, 567-568
```sql
CORR(...) OVER (ORDER BY p.date ROWS BETWEEN ...)
AVG(...) OVER (ORDER BY p.date ROWS BETWEEN ...)
```
**Status:** ✅ CORRECT - Consistent ordering using p.date  
**Action:** Keep pattern for all window functions

---

### 5. LEFT JOINs ✅
**Location:** Lines 537, 571, 584-586
```sql
LEFT JOIN yahoo_pivoted y ON p.date = y.date
LEFT JOIN correlations c ON p.date = c.date
LEFT JOIN interactions i ON p.date = i.date
```
**Status:** ✅ CORRECT - Preserves all production data  
**Action:** Keep as-is

---

## ⚠️ FIXES THAT MUST BE APPLIED (Before Phase 2)

### 6. Data Split Method ⚠️ CRITICAL FIX
**Current (WRONG):** Line 608
```sql
data_split_method='RANDOM',
data_split_eval_fraction=0.2
```

**Must Change To:**
```sql
data_split_method='SEQ',
data_split_col='date',
data_split_eval_fraction=0.2
```

**Why:** Random split for time series causes data leakage (predicting past from future)  
**Impact:** Validation metrics are invalid  
**Action:** ⚠️ MUST FIX before training

---

### 7. Special Character Sanitization ⚠️ NEW FIX NEEDED
**Current Examples:**
- `DX-Y.NYB` → `dx_y_nyb_close` (lines 214-220)
- `^VIX` → `vix_close` (lines 487-493)
- `CL=F` → `cl_f_close` (lines 172-178)
- `BZ=F` → `bz_f_close` (lines 144-150)

**For 220 Symbols, Need Function:**
- Remove `^` prefix: `^SYMBOL` → `symbol`
- Replace `=` with `_`: `SYMBOL=F` → `symbol_f`, `SYMBOL=X` → `symbol_x`
- Replace `-` with `_`: `SYM-BOL` → `sym_bol`
- Replace `.` with `_`: `SYM.BOL` → `sym_bol`
- Convert to lowercase

**Why:** BigQuery column names cannot contain special characters  
**Impact:** Will cause "Invalid column name" errors  
**Action:** ⚠️ MUST CREATE sanitization function before generating pivot

---

### 8. Column Conflict Detection ⚠️ MUST EXPAND
**Current:** 10 symbols with `_yh` suffix
- ADM, BG, CF, DAR, HYG, MOS, NTR, SOYB, TSN, WEAT

**For 220 Symbols:**
- Need to detect ALL symbols that conflict with production columns
- Query `production_training_data_1m` schema
- Compare sanitized symbol names against production columns
- Mark conflicts for `_yh` suffix

**Why:** Prevents "duplicate column name" errors  
**Impact:** Training will fail if conflicts exist  
**Action:** ⚠️ MUST DETECT all conflicts before generating pivot

---

### 9. Model Name ⚠️ MUST UPDATE
**Current:** Line 592
```sql
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m_baseline_exploratory`
```

**Must Change To:**
```sql
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m_baseline_exploratory_220_symbols`
```

**Why:** Option B - keep existing model, create new with "220" in name  
**Action:** ⚠️ MUST UPDATE before training

---

### 10. Training Configuration ⚠️ MUST UPDATE
**Current:** Lines 596-609
```sql
max_iterations=50,
learn_rate=0.05,
early_stop=TRUE,
min_rel_progress=0.0001,
l1_reg=1.5,
l2_reg=0.5,
data_split_method='RANDOM',
data_split_eval_fraction=0.2
```

**Must Change To:**
```sql
max_iterations=300,
learn_rate=0.12,
early_stop=TRUE,
min_rel_progress=0.00001,
l1_reg=0.7,
l2_reg=0.3,
data_split_method='SEQ',
data_split_col='date',
data_split_eval_fraction=0.2
```

**Why:** 
- 300 iterations: Allow full convergence (was stopping at 50 while still improving)
- 0.12 LR: 2.4× faster convergence
- 0.00001 min_rel_progress: 10× tighter threshold (0.001%)
- 0.7 L1: Looser to keep more Yahoo features
- 0.3 L2: Looser regularization
- SEQ split: Time-aware split (CRITICAL FIX)

**Action:** ⚠️ MUST UPDATE all parameters

---

### 11. 100% NULL Column Exclusion ⚠️ MUST EXPAND DYNAMICALLY
**Current:** Lines 624-659
- 28 columns explicitly excluded in EXCEPT clause

**For 220 Symbols:**
- 165 symbols × 7 indicators = 1,155 columns will be 100% NULL
- Cannot manually list all - must detect dynamically

**Process:**
1. Create table with all 220 symbols
2. Scan table to detect all 100% NULL columns
3. Generate EXCEPT clause with all NULL columns
4. Update CREATE MODEL statement

**Why:** BQML fails with "Failed to calculate mean since all entries are NULLs"  
**Impact:** Training will fail if NULL columns not excluded  
**Action:** ⚠️ MUST DETECT after table creation, before training

---

### 12. Column Reference Verification ⚠️ MUST VERIFY
**Current References in Correlations CTE:**
- `y.dx_y_nyb_close` ✅ (line 522)
- `y.cl_f_close` ✅ (line 516)
- `y.vix_close` ✅ (line 528)
- `p.soyb_close` ✅ (line 504)
- `p.corn_etf_close` ✅ (line 510)

**Current References in Interactions CTE:**
- `y.cl_f_close` ✅ (line 549, 554)
- `y.bz_f_close` ✅ (line 549)
- `y.dx_y_nyb_close` ✅ (line 554, 567)
- `y.vix_close` ✅ (line 555, 562, 563, 566)
- `y.gspc_close` ✅ (line 555)
- `y.cl_f_atr` ✅ (line 563)

**For 220 Symbols:**
- Must verify ALL column references match actual pivot column names
- After generating pivot, check all references
- Update any that don't match

**Why:** "Name X not found" errors if references don't match  
**Impact:** Training will fail  
**Action:** ⚠️ MUST VERIFY after pivot generation

---

### 13. Pivot Generation ⚠️ MUST EXPAND
**Current:** Lines 106-493
- 55 symbols × 7 indicators = 385 pivot lines

**For 220 Symbols:**
- 220 symbols × 7 indicators = 1,540 pivot lines
- Must apply sanitization to all symbols
- Must add `_yh` suffix to conflicting symbols
- Must generate all 7 indicators per symbol

**Action:** ⚠️ MUST GENERATE complete pivot before table creation

---

## COMPLETE FIX CHECKLIST

### Pre-Pivot Generation:
- [x] ✅ Timestamp conversion (keep as-is)
- [x] ✅ Table structure (keep as-is)
- [x] ✅ NULLIF pattern (keep as-is)
- [x] ✅ Window function ordering (keep as-is)
- [x] ✅ LEFT JOINs (keep as-is)
- [ ] ⚠️ Create special character sanitization function
- [ ] ⚠️ Detect column conflicts (which symbols need `_yh` suffix)
- [ ] ⚠️ Generate pivot for all 220 symbols with sanitized names

### Pre-Table Creation:
- [ ] ⚠️ Update model name to `_220_symbols`
- [ ] ⚠️ Update training config (300 iter, 0.12 LR, SEQ split, L1=0.7, etc.)
- [ ] ⚠️ Verify all column references in correlations/interactions CTEs

### Post-Table Creation:
- [ ] ⚠️ Detect all 100% NULL columns
- [ ] ⚠️ Generate complete EXCEPT clause with all NULL columns
- [ ] ⚠️ Update CREATE MODEL statement with complete EXCEPT clause

### Final:
- [ ] ⚠️ Execute training

---

## SUMMARY

**Total Fixes:** 13 items
- ✅ **Already Done:** 5 (timestamp, table structure, NULLIF, window functions, LEFT JOINs)
- ⚠️ **Must Do:** 8 (data split, sanitization, conflicts, model name, config, NULL detection, references, pivot)

**Critical Path:**
1. Create sanitization function
2. Detect conflicts
3. Generate 220-symbol pivot
4. Update model name and config
5. Verify column references
6. Create table
7. Detect NULL columns
8. Update EXCEPT clause
9. Train model

**All fixes must be in place before Phase 2 execution.**


