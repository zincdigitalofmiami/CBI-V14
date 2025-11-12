# 🚨 ZERO STALE DATA ACTION PLAN
**Date:** November 6, 2025  
**Mission:** Get ALL data current with ZERO staleness

---

## 🔴 CRITICAL ISSUES FOUND

### Current Data Staleness
| Dataset | Last Date | Days Stale | Status |
|---------|-----------|------------|--------|
| **production_training_data_1m** | Sep 10, 2025 | **57 DAYS!** | 🔴 CRITICAL |
| **cftc_cot** | Sep 23, 2025 | 44 days | 🟠 Bad |
| **soybean_oil_prices** | Nov 5, 2025 | 1 day | ✅ Good |
| **palm_oil_prices** | Nov 5, 2025 | 1 day | ✅ Good |
| **vw_big_eight_signals** | Nov 6, 2025 | 0 days | ✅ CURRENT |

---

## 🎯 IMMEDIATE ACTIONS

### Step 1: Pull Vertex AI Data Into Production
```sql
-- URGENT: Get all Vertex AI features into production
INSERT INTO `cbi-v14.models_v4.production_training_data_1m`
SELECT 
  CAST(date AS DATE) as date,
  -- All 200+ features from Vertex AI
  china_soybean_imports_mt,
  vix_level,
  palm_price,
  feature_vix_stress,
  feature_tariff_threat,
  feature_biofuel_cascade,
  -- ... (all other columns)
  target_1w,
  target_1m,
  target_3m,
  target_6m
FROM `cbi-v14.export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z.evaluated_data_items`
WHERE date >= '2025-09-11'  -- Fill the gap
  AND date NOT IN (SELECT date FROM `cbi-v14.models_v4.production_training_data_1m`)
```

### Step 2: Update with Big 8 Signals (Current Data)
```sql
-- Merge current Big 8 signals (Nov 6 data!)
MERGE `cbi-v14.models_v4.production_training_data_1m` t
USING `cbi-v14.neural.vw_big_eight_signals` s
ON t.date = s.date
WHEN MATCHED THEN UPDATE SET
  feature_vix_stress = s.feature_vix_stress,
  feature_harvest_pace = s.feature_harvest_pace,
  feature_china_relations = s.feature_china_relations,
  feature_tariff_threat = s.feature_tariff_threat,
  feature_geopolitical_volatility = s.feature_geopolitical_volatility,
  feature_biofuel_cascade = s.feature_biofuel_cascade,
  feature_hidden_correlation = s.feature_hidden_correlation,
  feature_biofuel_ethanol = s.feature_biofuel_ethanol,
  big8_composite_score = s.big8_composite_score
WHEN NOT MATCHED THEN INSERT 
  (date, feature_vix_stress, feature_harvest_pace, feature_china_relations,
   feature_tariff_threat, feature_geopolitical_volatility, feature_biofuel_cascade,
   feature_hidden_correlation, feature_biofuel_ethanol, big8_composite_score)
VALUES
  (date, feature_vix_stress, feature_harvest_pace, feature_china_relations,
   feature_tariff_threat, feature_geopolitical_volatility, feature_biofuel_cascade,
   feature_hidden_correlation, feature_biofuel_ethanol, big8_composite_score)
```

### Step 3: Fix CFTC Data Gap
```sql
-- Update CFTC data from staging (check if more recent)
INSERT INTO `cbi-v14.forecasting_data_warehouse.cftc_cot`
SELECT * FROM `cbi-v14.staging.cftc_cot`
WHERE report_date > '2025-09-23'
  AND report_date NOT IN (
    SELECT report_date FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
  )
```

### Step 4: Forward-Fill All Sparse Data
```sql
-- Use MEGA_CONSOLIDATION_ALL_DATA.sql but with CURRENT dates
CREATE OR REPLACE TABLE `cbi-v14.models_v4.production_training_data_1m` AS
WITH all_dates AS (
  -- Use Big 8 signals dates (CURRENT through Nov 6!)
  SELECT DISTINCT date 
  FROM `cbi-v14.neural.vw_big_eight_signals`
  WHERE date >= '2020-01-01'
),
-- Join ALL available data sources
-- Forward-fill sparse features
-- Result: 300 features, ZERO stale data
```

---

## 📊 DATA SOURCES TO CONSOLIDATE

### High Priority (Update Daily)
1. **Prices**: soybean_oil, palm_oil, corn, wheat, crude ✅ Current
2. **Big 8 Signals**: All 8 features ✅ Current  
3. **VIX/Volatility**: vix_daily ✅ Current
4. **CFTC**: Positioning data 🔴 44 days stale - NEEDS UPDATE

### Medium Priority (Update Weekly)
5. **China Imports**: Monthly data, forward-fill
6. **Trump Policy**: Since Oct 2024
7. **News/Sentiment**: Since Oct 2024
8. **Weather**: Daily updates

### Use Vertex AI Export For:
- **Missing dates**: Sep 11 - Oct 27 (fill the gap!)
- **Feature validation**: 200+ columns to verify
- **Importance ranking**: Focus on top features

---

## 🚀 OPTIMIZATION USING VERTEX AI DATA

### Create Feature Importance View
```sql
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_feature_importance` AS
WITH feature_stats AS (
  SELECT 
    -- Calculate coefficient of variation for each feature
    'china_soybean_imports_mt' as feature,
    STDDEV(china_soybean_imports_mt)/AVG(china_soybean_imports_mt) as cv,
    CORR(china_soybean_imports_mt, target_1w) as target_correlation
  FROM `cbi-v14.export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z.evaluated_data_items`
  
  UNION ALL
  
  SELECT 'vix_level',
    STDDEV(vix_level)/AVG(vix_level),
    CORR(vix_level, target_1w)
  FROM `cbi-v14.export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z.evaluated_data_items`
  
  -- Add all 200+ features
)
SELECT 
  feature,
  cv as variation_coefficient,
  ABS(target_correlation) as importance_score,
  RANK() OVER (ORDER BY ABS(target_correlation) DESC) as importance_rank
FROM feature_stats
ORDER BY importance_rank
```

### Create Focused Training Set (Top 50 Features)
```sql
-- Use only top 50 most important features for faster, focused model
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_training_focused_50` AS
SELECT 
  date,
  -- Top 50 features from importance ranking
  china_soybean_imports_mt,
  vix_level,
  palm_price,
  feature_vix_stress,
  feature_tariff_threat,
  -- ... (45 more)
  target_1w,
  target_1m,
  target_3m,
  target_6m
FROM `cbi-v14.models_v4.production_training_data_1m`
```

---

## ✅ SUCCESS CRITERIA

1. **production_training_data_1m** updated to Nov 6, 2025 ✓
2. All 300 features populated with <5% NULL rate ✓
3. CFTC data current (within 7 days) ✓
4. Feature importance view created ✓
5. Vertex AI data integrated ✓

---

## 🔧 IMPLEMENTATION

```bash
# 1. Run consolidation
bq query --use_legacy_sql=false < MEGA_CONSOLIDATION_ALL_DATA.sql

# 2. Verify freshness
bq query --use_legacy_sql=false "
  SELECT MAX(date) as latest, 
         COUNT(*) as rows,
         COUNT(DISTINCT date) as unique_dates
  FROM \`cbi-v14.models_v4.production_training_data_1m\`"

# 3. Create importance views
bq query --use_legacy_sql=false < create_feature_importance_views.sql

# 4. Archive old tables
./scripts/archive_old_tables.sh
```

---

**DEADLINE: Get to ZERO stale data TODAY!**






