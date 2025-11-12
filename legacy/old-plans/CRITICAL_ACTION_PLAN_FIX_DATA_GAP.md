# 🚨 CRITICAL ACTION PLAN: FIX 56-DAY DATA GAP
**Date:** November 5, 2025  
**Status:** EMERGENCY PRIORITY

---

## 🔴 CRITICAL ISSUE
**Production data is 56 days stale!**
- Last date in production: **September 10, 2025**
- Current date: **November 5, 2025**
- Gap: **56 days of missing data**

## ✅ OFFICIAL PRODUCTION SYSTEM (CONFIRMED)
- **Models:** `bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m`
- **Training Data:** `production_training_data_1w/1m/3m/6m` (300 features)
- **ALL ingestion MUST update these tables**

---

## 📋 IMMEDIATE ACTION PLAN

### STEP 1: Update Core Price Data (CRITICAL)
```bash
# Update ZL soybean oil prices to current
cd /Users/zincdigital/CBI-V14
python3 scripts/emergency_zl_update.py

# Update palm oil prices
python3 cbi-v14-ingestion/ingest_palm_oil_proxies.py

# Update other commodity prices
python3 ingestion/ingest_market_prices.py
```

### STEP 2: Run Feature Generation
```bash
# Generate Big 8 signals (if working)
python3 scripts/refresh_features_pipeline.py

# Update predict frame
python3 scripts/refresh_predict_frame.py
```

### STEP 3: Run Daily Aggregations
```sql
-- Rebuild all daily aggregation tables
-- This forward-fills weekly data to daily
bq query --nouse_legacy_sql < bigquery-sql/create_new_features_daily_aggregations.sql
```

### STEP 4: Update Production Tables
```sql
-- Run comprehensive integration to update production_training_data_*
bq query --nouse_legacy_sql < bigquery-sql/COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql

-- Or run the new features update
bq query --nouse_legacy_sql < bigquery-sql/UPDATE_PRODUCTION_WITH_NEW_FEATURES.sql
```

### STEP 5: Verify Update
```sql
-- Check that data is current
SELECT 
  MIN(date) as first_date,
  MAX(date) as last_date,
  COUNT(*) as row_count
FROM `cbi-v14.models_v4.production_training_data_1m`
WHERE date >= '2025-11-01';
-- Should show dates through Nov 5, 2025
```

---

## 🔧 FIX INGESTION SCRIPTS

### Priority 1: Price Data (MUST WORK)
- [ ] `emergency_zl_update.py` - Soybean oil prices
- [ ] `ingest_palm_oil_proxies.py` - Palm oil prices
- [ ] `ingest_market_prices.py` - Other commodities

### Priority 2: Critical Features
- [ ] `ingest_cftc_positioning_REAL.py` - CFTC data
- [ ] `ingest_china_imports_uncomtrade.py` - China imports
- [ ] `backfill_trump_intelligence.py` - Policy data

### Priority 3: New Features (After Core Fixed)
- [ ] Fix pandas.read_html issues in RIN/RFS scrapers
- [ ] Run GDELT backfill for news
- [ ] Add freight/logistics data

---

## ⚠️ ABOUT THE OPTIMIZATION PLAN

### AFTER fixing the data gap, useful elements:
✅ **USE THESE:**
- GDELT 2.0 for news backfill (Oct 2024 → present)
- CFTC forward-fill logic (but we have it)
- Coverage monitoring queries (adapt column names)
- EPA RIN/RFS sources (we have scrapers)

❌ **DON'T USE THESE:**
- Different feature names (rin_d4 vs rin_d4_price)
- New table creation (we have tables)
- Schema changes (would break models)

⚠️ **ADAPT THESE:**
- SQL queries → update column names to match ours
- Coverage thresholds → apply after data is current
- Feature engineering → add after core data works

---

## 🎯 SUCCESS CRITERIA

1. **Data Currency:** 
   - All production tables have data through Nov 5, 2025
   - No gaps in date sequence

2. **Feature Coverage:**
   - Core features (prices, Big 8) > 90% coverage
   - CFTC/News > 50% coverage
   - New features (RIN/RFS) > 0% coverage

3. **Model Ready:**
   - Can run predictions on current data
   - No NULL values in critical features for last 7 days

---

## ⏰ TIMELINE

**TODAY (Emergency):**
1. Update price data to current
2. Run integration SQL
3. Verify dates are current

**TOMORROW:**
1. Fix remaining ingestion scripts
2. Backfill October-November data
3. Run coverage checks

**THIS WEEK:**
1. Implement useful parts of optimization plan
2. Add GDELT news backfill
3. Fix RIN/RFS scrapers

---

## 🚨 DO NOT PROCEED WITH OPTIMIZATION PLAN UNTIL:
- [ ] Production data is current (Nov 5, 2025)
- [ ] Core features have >50% coverage
- [ ] Models can make predictions on current data

**Remember:** A sophisticated optimization plan is useless if the data is 56 days old!






