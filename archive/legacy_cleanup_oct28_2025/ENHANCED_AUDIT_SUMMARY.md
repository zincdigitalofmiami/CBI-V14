# Enhanced Pre-Training Audit Summary
**Date:** October 27, 2025  
**Script:** `enhanced_pretraining_audit.py`  
**Status:** ❌ CRITICAL ISSUES FOUND - DO NOT TRAIN UNTIL FIXED

---

## 🚨 CRITICAL ISSUES (12 Total)

### 1. MASSIVE DUPLICATE RECORDS (3,475+ extra records)

#### Most Critical:
- **treasury_prices**: 1,960 duplicate records (ALL data appears duplicated on 2025-10-21)
- **economic_indicators**: 1,380 duplicate records (536 duplicates on 2025-10-23 alone)
- **news_intelligence**: 1,159 duplicate records (255 on 2025-10-14)

#### Other Duplicates:
- **weather_data**: 100 duplicate records
- **weather_brazil_daily**: 10 duplicate records
- **weather_argentina_daily**: 10 duplicate records  
- **weather_us_midwest_daily**: 35 duplicate records
- **social_sentiment**: 8 duplicate records

#### Training Datasets:
- **training_dataset_enhanced**: 12 duplicate date rows (should use `training_dataset_enhanced_v5` instead)
- **training_dataset**: 12 duplicate date rows
- **FINAL_TRAINING_DATASET_COMPLETE**: 12 duplicate date rows

### 2. PLACEHOLDER VALUE CONTAMINATION

#### social_sentiment Table:
- ❌ **38 instances** of value `0.5` (5.7% of rows) - Classic placeholder
- ⚠️ **63.7% of rows** dominated by value `0.16666666666666666` - Suspicious repeated pattern

**Impact:** Sentiment features likely contain mock data that will degrade model performance

---

## ⚠️ WARNINGS (7 Total)

### Data Coverage Issues:
- **weather_brazil_daily**: Only 33 rows (minimal data)
- **weather_argentina_daily**: Only 33 rows (minimal data)
- **weather_us_midwest_daily**: Only 64 rows (minimal data)
- **cftc_cot**: Only 72 rows (minimal data)
- **usda_export_sales**: Only 12 rows (minimal data)

### Date Range Issues:
- **social_sentiment**: Only 653 unique dates across 6,157 day span (10.6% coverage)

---

## ✅ WHAT'S WORKING

### Clean Datasets:
- **training_dataset_enhanced_v5**: 1,251 rows, NO duplicates ✓
- All price tables (soybean_oil, corn, wheat, palm, crude, gold, natural_gas, sp500) ✓
- Economic indicators (71,827 rows) ✓
- VIX daily (2,717 rows) ✓
- Currency data (59,102 rows) ✓

### Production Models:
- 37 production models found
- Note: Model evaluation failed (training dataset reference issue)

---

## 🎯 RECOMMENDED ACTIONS BEFORE TRAINING

### Priority 1: Fix Duplicate Records (CRITICAL)

**1. Fix treasury_prices:**
```sql
-- Remove duplicates from treasury_prices
DELETE FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
WHERE rowid NOT IN (
    SELECT MIN(rowid)
    FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
    GROUP BY DATE(time)
);
```

**2. Fix economic_indicators:**
```sql
-- Remove duplicates from economic_indicators
DELETE FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
WHERE rowid NOT IN (
    SELECT MIN(rowid)
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    GROUP BY DATE(time), indicator
);
```

**3. Fix news_intelligence:**
```sql
-- Remove duplicates from news_intelligence
DELETE FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
WHERE rowid NOT IN (
    SELECT MIN(rowid)
    FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
    GROUP BY DATE(published), title
);
```

**4. Fix weather tables:**
```sql
-- Run for each weather table
DELETE FROM `cbi-v14.forecasting_data_warehouse.{table_name}`
WHERE rowid NOT IN (
    SELECT MIN(rowid)
    FROM `cbi-v14.forecasting_data_warehouse.{table_name}`
    GROUP BY date
);
```

**5. Fix social_sentiment:**
```sql
-- Remove duplicates from social_sentiment
DELETE FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
WHERE rowid NOT IN (
    SELECT MIN(rowid)
    FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
    GROUP BY DATE(timestamp)
);
```

### Priority 2: Clean Placeholder Values

**Fix sentiment_score placeholder contamination:**
```sql
-- Identify placeholder rows
SELECT 
    sentiment_score,
    COUNT(*) as count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as pct
FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
GROUP BY sentiment_score
ORDER BY count DESC;

-- Remove or replace placeholder values
UPDATE `cbi-v14.forecasting_data_warehouse.social_sentiment`
SET sentiment_score = NULL
WHERE sentiment_score = 0.5 OR sentiment_score = 0.16666666666666666;
```

### Priority 3: Use Clean Training Dataset

**Use the clean dataset:**
- ✅ **RECOMMENDED:** `training_dataset_enhanced_v5` (1,251 rows, NO duplicates)
- ❌ **AVOID:** `training_dataset_enhanced`, `training_dataset`, `FINAL_TRAINING_DATASET_COMPLETE` (all have 12 duplicate rows)

---

## 📊 AUDIT RESULTS BREAKDOWN

### Dataset Status:
- ✅ **31 datasets** verified and operational
- ⚠️ **5 datasets** have minimal data (<100 rows)
- ❌ **8 datasets** have duplicate records

### Total Duplicate Records: **3,475+**
- This represents significant data contamination
- Duplicates will cause model overfitting and invalid predictions
- **Training MUST be delayed until duplicates are removed**

### Placeholder Contamination:
- Sentiment features: **5.7% placeholder values** (value 0.5)
- Sentiment features: **63.7% dominated by single pattern**
- **Sentiment features are NOT usable in current state**

---

## 🎯 NEXT STEPS

1. **IMMEDIATE:** Create duplicate removal script for all affected tables
2. **CLEANSE:** Remove placeholder values from sentiment data
3. **VERIFY:** Re-run enhanced audit to confirm all issues resolved
4. **TRAIN:** Only proceed when audit shows 0 critical issues

---

## 📝 AUDIT SCRIPT USAGE

```bash
# Run enhanced audit
python3 enhanced_pretraining_audit.py

# Exit codes:
# 0 = Pass (can proceed with training)
# 1 = Fail (must fix issues before training)
```

---

**CONCLUSION:** Data quality issues MUST be resolved before any new model training. Current state has 3,475+ duplicate records that will corrupt training results.





