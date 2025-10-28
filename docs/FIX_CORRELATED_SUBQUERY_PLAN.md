# FIX CORRELATED SUBQUERY ISSUE - EXECUTION PLAN
**Date:** October 22, 2025  
**Status:** ⚠️ AWAITING APPROVAL - DO NOT EXECUTE YET  
**Risk Level:** MEDIUM (creates new tables, does NOT modify existing views)

---

## 🎯 PROBLEM STATEMENT

`vw_neural_training_dataset` contains window functions (LAG, LEAD, AVG OVER, STDDEV OVER) in a CTE that is then used in LEFT JOINs. BigQuery ML interprets this as a correlated subquery and rejects it.

**Error:**
```
400 Correlated subqueries that reference other tables are not supported 
unless they can be de-correlated, such as by transforming them into an 
efficient JOIN.
```

---

## 🔍 ROOT CAUSE ANALYSIS

Looking at the view definition, the problematic section is the `price_features` CTE (lines 21-37):

```sql
price_features AS (
    SELECT 
        date,
        zl_price_current,
        target_1w, target_1m, target_3m, target_6m,
        zl_volume,
        LAG(zl_price_current, 1) OVER (ORDER BY date) as zl_price_lag1,     -- ← WINDOW
        LAG(zl_price_current, 7) OVER (ORDER BY date) as zl_price_lag7,     -- ← WINDOW
        LAG(zl_price_current, 30) OVER (ORDER BY date) as zl_price_lag30,   -- ← WINDOW
        (zl_price_current - LAG(...)) / NULLIF(...) as return_1d,            -- ← WINDOW
        (zl_price_current - LAG(...)) / NULLIF(...) as return_7d,            -- ← WINDOW
        AVG(zl_price_current) OVER (...) as ma_7d,                           -- ← WINDOW
        AVG(zl_price_current) OVER (...) as ma_30d,                          -- ← WINDOW
        STDDEV(zl_price_current) OVER (...) as volatility_30d                -- ← WINDOW
    FROM targets  -- ← targets ALSO has window functions (LEAD)
)
```

And `targets` CTE (lines 10-19) has more window functions:
```sql
targets AS (
    SELECT 
        date,
        close_price as zl_price_current,
        LEAD(close_price, 7) OVER (ORDER BY date) as target_1w,     -- ← WINDOW
        LEAD(close_price, 30) OVER (ORDER BY date) as target_1m,    -- ← WINDOW
        LEAD(close_price, 90) OVER (ORDER BY date) as target_3m,    -- ← WINDOW
        LEAD(close_price, 180) OVER (ORDER BY date) as target_6m,   -- ← WINDOW
        volume as zl_volume
    FROM daily_prices
)
```

---

## ✅ SOLUTION APPROACH

### Strategy:
**Materialize ALL price-related window functions into a table**, then JOIN it cleanly with the other feature views.

### What Gets Materialized:
1. All window functions from `targets` (LEAD for targets)
2. All window functions from `price_features` (LAG, AVG OVER, STDDEV OVER)
3. Simple aggregations from `daily_prices`, `weather_agg`, `sentiment_agg`

### What Stays as Views:
- All the other feature views (correlation, seasonality, crush margins, etc.)
- These already exist as separate views and can be JOINed cleanly

---

## 📋 EXECUTION STEPS

### Step 1: Create Materialized Price Features Table

**Table Name:** `models.price_features_materialized`  
**Purpose:** Pre-compute all price-related window functions  
**Size Estimate:** ~1,250 rows × 18 columns ≈ 0.02 MB

```sql
CREATE OR REPLACE TABLE `cbi-v14.models.price_features_materialized` AS
WITH daily_prices AS (
    SELECT 
        DATE(time) as date,
        AVG(close) as close_price,
        SUM(volume) as volume
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE symbol = 'ZL'
    GROUP BY DATE(time)
),
targets AS (
    SELECT 
        date,
        close_price as zl_price_current,
        LEAD(close_price, 7) OVER (ORDER BY date) as target_1w,
        LEAD(close_price, 30) OVER (ORDER BY date) as target_1m,
        LEAD(close_price, 90) OVER (ORDER BY date) as target_3m,
        LEAD(close_price, 180) OVER (ORDER BY date) as target_6m,
        volume as zl_volume
    FROM daily_prices
)
SELECT 
    date,
    zl_price_current,
    target_1w, target_1m, target_3m, target_6m,
    zl_volume,
    LAG(zl_price_current, 1) OVER (ORDER BY date) as zl_price_lag1,
    LAG(zl_price_current, 7) OVER (ORDER BY date) as zl_price_lag7,
    LAG(zl_price_current, 30) OVER (ORDER BY date) as zl_price_lag30,
    (zl_price_current - LAG(zl_price_current, 1) OVER (ORDER BY date)) / 
        NULLIF(LAG(zl_price_current, 1) OVER (ORDER BY date), 0) as return_1d,
    (zl_price_current - LAG(zl_price_current, 7) OVER (ORDER BY date)) / 
        NULLIF(LAG(zl_price_current, 7) OVER (ORDER BY date), 0) as return_7d,
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma_7d,
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as ma_30d,
    STDDEV(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as volatility_30d
FROM targets;
```

**Safety Check:**
- ✅ Creates NEW table (does not modify existing views)
- ✅ Uses existing source data (no data loss risk)
- ✅ Can be dropped if something goes wrong

### Step 2: Create Materialized Weather & Sentiment Tables

**Why:** These are simple aggregations but used in the main query

```sql
-- Weather aggregations
CREATE OR REPLACE TABLE `cbi-v14.models.weather_features_daily` AS
SELECT 
    date,
    AVG(CASE WHEN region LIKE '%Brazil%' THEN temp_max END) as brazil_temp,
    AVG(CASE WHEN region LIKE '%Brazil%' THEN precip_mm END) as brazil_precip,
    AVG(CASE WHEN region LIKE '%Argentina%' THEN temp_max END) as argentina_temp,
    AVG(CASE WHEN region LIKE '%US%' THEN temp_max END) as us_temp
FROM `cbi-v14.forecasting_data_warehouse.weather_data`
GROUP BY date;

-- Sentiment aggregations
CREATE OR REPLACE TABLE `cbi-v14.models.sentiment_features_daily` AS
SELECT 
    DATE(timestamp) as date,
    AVG(sentiment_score) as avg_sentiment,
    STDDEV(sentiment_score) as sentiment_volatility,
    COUNT(*) as sentiment_volume
FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
GROUP BY DATE(timestamp);
```

**Safety Check:**
- ✅ Creates NEW tables (separate from existing precomputed tables)
- ✅ Simple GROUP BY (no complex logic)
- ✅ Can verify row counts before proceeding

### Step 3: Create Final Training Table (Clean JOINs Only)

**Table Name:** `models.training_dataset_materialized`  
**Purpose:** Final BQML-compatible training dataset  
**Size Estimate:** ~1,250 rows × 159 columns ≈ 0.15 MB

```sql
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset_materialized`
PARTITION BY DATE_TRUNC(date, MONTH)
CLUSTER BY target_1w, target_1m
AS
SELECT 
    p.date,
    
    -- TARGETS (4)
    p.target_1w,
    p.target_1m,
    p.target_3m,
    p.target_6m,
    
    -- PRICE FEATURES (14) - ALL FROM MATERIALIZED TABLE (NO WINDOW FUNCTIONS)
    p.zl_price_current,
    p.zl_price_lag1,
    p.zl_price_lag7,
    p.zl_price_lag30,
    p.return_1d,
    p.return_7d,
    p.ma_7d,
    p.ma_30d,
    p.volatility_30d,
    p.zl_volume,
    
    -- BIG 8 SIGNALS (9) - FROM VIEW (SIMPLE SELECTS)
    COALESCE(b8.feature_vix_stress, 0.5) as feature_vix_stress,
    COALESCE(b8.feature_harvest_pace, 0.5) as feature_harvest_pace,
    COALESCE(b8.feature_china_relations, 0.5) as feature_china_relations,
    COALESCE(b8.feature_tariff_threat, 0.3) as feature_tariff_threat,
    COALESCE(b8.feature_geopolitical_volatility, 0.4) as feature_geopolitical_volatility,
    COALESCE(b8.feature_biofuel_cascade, 0.5) as feature_biofuel_cascade,
    COALESCE(b8.feature_hidden_correlation, 0.0) as feature_hidden_correlation,
    COALESCE(b8.feature_biofuel_ethanol, 0.5) as feature_biofuel_ethanol,
    COALESCE(b8.big8_composite_score, 0.5) as big8_composite_score,
    
    -- CORRELATIONS (35) - FROM VIEW
    COALESCE(c.corr_zl_crude_7d, 0) as corr_zl_crude_7d,
    COALESCE(c.corr_zl_palm_7d, 0) as corr_zl_palm_7d,
    COALESCE(c.corr_zl_vix_7d, 0) as corr_zl_vix_7d,
    COALESCE(c.corr_zl_dxy_7d, 0) as corr_zl_dxy_7d,
    COALESCE(c.corr_zl_corn_7d, 0) as corr_zl_corn_7d,
    COALESCE(c.corr_zl_wheat_7d, 0) as corr_zl_wheat_7d,
    COALESCE(c.corr_zl_crude_30d, 0) as corr_zl_crude_30d,
    COALESCE(c.corr_zl_palm_30d, 0) as corr_zl_palm_30d,
    COALESCE(c.corr_zl_vix_30d, 0) as corr_zl_vix_30d,
    COALESCE(c.corr_zl_dxy_30d, 0) as corr_zl_dxy_30d,
    COALESCE(c.corr_zl_corn_30d, 0) as corr_zl_corn_30d,
    COALESCE(c.corr_zl_wheat_30d, 0) as corr_zl_wheat_30d,
    COALESCE(c.corr_zl_crude_90d, 0) as corr_zl_crude_90d,
    COALESCE(c.corr_zl_palm_90d, 0) as corr_zl_palm_90d,
    COALESCE(c.corr_zl_vix_90d, 0) as corr_zl_vix_90d,
    COALESCE(c.corr_zl_dxy_90d, 0) as corr_zl_dxy_90d,
    COALESCE(c.corr_zl_corn_90d, 0) as corr_zl_corn_90d,
    COALESCE(c.corr_zl_crude_180d, 0) as corr_zl_crude_180d,
    COALESCE(c.corr_zl_palm_180d, 0) as corr_zl_palm_180d,
    COALESCE(c.corr_zl_vix_180d, 0) as corr_zl_vix_180d,
    COALESCE(c.corr_zl_dxy_180d, 0) as corr_zl_dxy_180d,
    COALESCE(c.corr_zl_crude_365d, 0) as corr_zl_crude_365d,
    COALESCE(c.corr_zl_palm_365d, 0) as corr_zl_palm_365d,
    COALESCE(c.corr_zl_vix_365d, 0) as corr_zl_vix_365d,
    COALESCE(c.corr_zl_dxy_365d, 0) as corr_zl_dxy_365d,
    COALESCE(c.corr_zl_corn_365d, 0) as corr_zl_corn_365d,
    COALESCE(c.corr_palm_crude_30d, 0) as corr_palm_crude_30d,
    COALESCE(c.corr_corn_wheat_30d, 0) as corr_corn_wheat_30d,
    COALESCE(c.crude_price, 0) as crude_price,
    COALESCE(c.palm_price, 0) as palm_price,
    COALESCE(c.corn_price, 0) as corn_price,
    COALESCE(c.wheat_price, 0) as wheat_price,
    COALESCE(c.vix_level, 0) as vix_level,
    COALESCE(c.dxy_level, 0) as dxy_level,
    
    -- SEASONALITY (3)
    COALESCE(sz.seasonal_index, 1.0) as seasonal_index,
    COALESCE(sz.monthly_zscore, 0.0) as monthly_zscore,
    COALESCE(sz.yoy_change, 0.0) as yoy_change,
    
    -- CRUSH MARGINS (6)
    COALESCE(cm.oil_price_per_cwt, 0) as oil_price_per_cwt,
    COALESCE(cm.bean_price_per_bushel, 0) as bean_price_per_bushel,
    COALESCE(cm.meal_price_per_ton, 0) as meal_price_per_ton,
    COALESCE(cm.crush_margin, 0) as crush_margin,
    COALESCE(cm.crush_margin_7d_ma, 0) as crush_margin_7d_ma,
    COALESCE(cm.crush_margin_30d_ma, 0) as crush_margin_30d_ma,
    
    -- CHINA IMPORT TRACKER (10)
    COALESCE(ci.china_mentions, 0) as china_mentions,
    COALESCE(ci.china_posts, 0) as china_posts,
    COALESCE(ci.import_posts, 0) as import_posts,
    COALESCE(ci.soy_posts, 0) as soy_posts,
    COALESCE(ci.china_sentiment, 0.5) as china_sentiment,
    COALESCE(ci.sentiment_volatility, 0.1) as china_sentiment_volatility,
    COALESCE(ci.policy_impact, 0) as china_policy_impact,
    COALESCE(ci.import_demand_index, 0.5) as import_demand_index,
    COALESCE(ci.china_posts_7d_ma, 0) as china_posts_7d_ma,
    COALESCE(ci.china_sentiment_30d_ma, 0.5) as china_sentiment_30d_ma,
    
    -- BRAZIL EXPORT (9)
    COALESCE(be.month, EXTRACT(MONTH FROM p.date)) as brazil_month,
    COALESCE(be.export_seasonality_factor, 1.0) as export_seasonality_factor,
    COALESCE(be.temperature_c, 25) as brazil_temperature_c,
    COALESCE(be.precipitation_mm, 100) as brazil_precipitation_mm,
    COALESCE(be.growing_degree_days, 0) as growing_degree_days,
    COALESCE(be.export_capacity_index, 1.0) as export_capacity_index,
    COALESCE(be.harvest_pressure, 0.5) as harvest_pressure,
    COALESCE(be.precip_30d_ma, 100) as brazil_precip_30d_ma,
    COALESCE(be.temp_7d_ma, 25) as brazil_temp_7d_ma,
    
    -- TRUMP-XI VOLATILITY (13)
    COALESCE(tx.trump_mentions, 0) as trump_mentions,
    COALESCE(tx.china_mentions, 0) as trumpxi_china_mentions,
    COALESCE(tx.co_mentions, 0) as trump_xi_co_mentions,
    COALESCE(tx.xi_mentions, 0) as xi_mentions,
    COALESCE(tx.tariff_mentions, 0) as tariff_mentions,
    COALESCE(tx.co_mention_sentiment, 0.5) as co_mention_sentiment,
    COALESCE(tx.sentiment_volatility, 0.1) as trumpxi_sentiment_volatility,
    COALESCE(tx.policy_impact, 0) as trumpxi_policy_impact,
    COALESCE(tx.max_policy_impact, 0) as max_policy_impact,
    COALESCE(tx.tension_index, 0.0) as tension_index,
    COALESCE(tx.volatility_multiplier, 1.0) as volatility_multiplier,
    COALESCE(tx.co_mentions_7d_ma, 0) as co_mentions_7d_ma,
    COALESCE(tx.volatility_30d_ma, 0.1) as trumpxi_volatility_30d_ma,
    
    -- TRADE WAR IMPACT (6)
    COALESCE(tw.china_tariff_rate, 0) as china_tariff_rate,
    COALESCE(tw.brazil_market_share, 0.5) as brazil_market_share,
    COALESCE(tw.us_export_impact, 0) as us_export_impact,
    COALESCE(tw.event_volatility_multiplier, 1.0) as tradewar_event_vol_mult,
    COALESCE(tw.trade_war_intensity, 0) as trade_war_intensity,
    COALESCE(tw.trade_war_impact_score, 0.0) as trade_war_impact_score,
    
    -- EVENT-DRIVEN FEATURES (16)
    COALESCE(ev.is_wasde_day, 0) as is_wasde_day,
    COALESCE(ev.is_fomc_day, 0) as is_fomc_day,
    COALESCE(ev.is_china_holiday, 0) as is_china_holiday,
    COALESCE(ev.is_crop_report_day, 0) as is_crop_report_day,
    COALESCE(ev.is_stocks_day, 0) as is_stocks_day,
    COALESCE(ev.is_planting_day, 0) as is_planting_day,
    COALESCE(ev.is_major_usda_day, 0) as is_major_usda_day,
    COALESCE(ev.event_impact_level, 0) as event_impact_level,
    COALESCE(ev.days_to_next_major_event, 30) as days_to_next_event,
    COALESCE(ev.days_since_last_major_event, 30) as days_since_last_event,
    COALESCE(ev.pre_event_window, 0) as pre_event_window,
    COALESCE(ev.post_event_window, 0) as post_event_window,
    COALESCE(ev.expected_volatility_multiplier, 1.0) as event_vol_mult,
    COALESCE(ev.is_options_expiry, 0) as is_options_expiry,
    COALESCE(ev.is_quarter_end, 0) as is_quarter_end,
    COALESCE(ev.is_month_end, 0) as is_month_end,
    
    -- LEAD/LAG SIGNALS (28)
    COALESCE(ll.palm_lag1, 0) as palm_lag1,
    COALESCE(ll.palm_lag2, 0) as palm_lag2,
    COALESCE(ll.palm_lag3, 0) as palm_lag3,
    COALESCE(ll.palm_momentum_3d, 0) as palm_momentum_3d,
    COALESCE(ll.crude_lag1, 0) as crude_lag1,
    COALESCE(ll.crude_lag2, 0) as crude_lag2,
    COALESCE(ll.crude_momentum_2d, 0) as crude_momentum_2d,
    COALESCE(ll.vix_lag1, 0) as vix_lag1,
    COALESCE(ll.vix_lag2, 0) as vix_lag2,
    COALESCE(ll.vix_spike_lag1, 0) as vix_spike_lag1,
    COALESCE(ll.dxy_lag1, 0) as dxy_lag1,
    COALESCE(ll.dxy_lag2, 0) as dxy_lag2,
    COALESCE(ll.dxy_momentum_3d, 0) as dxy_momentum_3d,
    COALESCE(ll.corn_lag1, 0) as corn_lag1,
    COALESCE(ll.wheat_lag1, 0) as wheat_lag1,
    COALESCE(ll.corn_soy_ratio_lag1, 0) as corn_soy_ratio_lag1,
    COALESCE(ll.palm_lead2_correlation, 0) as palm_lead2_correlation,
    COALESCE(ll.crude_lead1_correlation, 0) as crude_lead1_correlation,
    COALESCE(ll.vix_lead1_correlation, 0) as vix_lead1_correlation,
    COALESCE(ll.dxy_lead1_correlation, 0) as dxy_lead1_correlation,
    COALESCE(ll.palm_direction_correct, 0) as palm_direction_correct,
    COALESCE(ll.crude_direction_correct, 0) as crude_direction_correct,
    COALESCE(ll.vix_inverse_correct, 0) as vix_inverse_correct,
    COALESCE(ll.signal_confidence, 0.5) as lead_signal_confidence,
    COALESCE(ll.momentum_divergence, 0) as momentum_divergence,
    COALESCE(ll.palm_accuracy_30d, 0.5) as palm_accuracy_30d,
    COALESCE(ll.crude_accuracy_30d, 0.5) as crude_accuracy_30d,
    COALESCE(ll.zl_price, p.zl_price_current) as leadlag_zl_price,
    
    -- WEATHER (4) - FROM MATERIALIZED TABLE
    COALESCE(w.brazil_temp, 25) as weather_brazil_temp,
    COALESCE(w.brazil_precip, 100) as weather_brazil_precip,
    COALESCE(w.argentina_temp, 20) as weather_argentina_temp,
    COALESCE(w.us_temp, 20) as weather_us_temp,
    
    -- SENTIMENT (3) - FROM MATERIALIZED TABLE
    COALESCE(s.avg_sentiment, 0.5) as avg_sentiment,
    COALESCE(s.sentiment_volatility, 0.1) as sentiment_volatility,
    COALESCE(s.sentiment_volume, 0) as sentiment_volume,
    
    -- METADATA (3)
    EXTRACT(DAYOFWEEK FROM p.date) as day_of_week,
    EXTRACT(MONTH FROM p.date) as month,
    EXTRACT(QUARTER FROM p.date) as quarter
    
FROM `cbi-v14.models.price_features_materialized` p
LEFT JOIN `cbi-v14.neural.vw_big_eight_signals` b8 ON p.date = b8.date
LEFT JOIN `cbi-v14.models.vw_correlation_features` c ON p.date = c.date
LEFT JOIN `cbi-v14.models.vw_seasonality_features` sz ON p.date = sz.date
LEFT JOIN `cbi-v14.models.vw_crush_margins` cm ON p.date = cm.date
LEFT JOIN `cbi-v14.models.vw_china_import_tracker` ci ON p.date = ci.date
LEFT JOIN `cbi-v14.models.vw_brazil_export_lineup` be ON p.date = be.date
LEFT JOIN `cbi-v14.models.vw_trump_xi_volatility` tx ON p.date = tx.date
LEFT JOIN `cbi-v14.signals.vw_trade_war_impact` tw ON p.date = tw.date
LEFT JOIN `cbi-v14.models.vw_event_driven_features` ev ON p.date = ev.date
LEFT JOIN `cbi-v14.models.vw_cross_asset_lead_lag` ll ON p.date = ll.date
LEFT JOIN `cbi-v14.models.weather_features_daily` w ON p.date = w.date
LEFT JOIN `cbi-v14.models.sentiment_features_daily` s ON p.date = s.date

WHERE p.target_1w IS NOT NULL;
```

**Safety Features:**
- ✅ PARTITIONED by month for query performance
- ✅ CLUSTERED by target variables for training queries
- ✅ All window functions removed from JOINs
- ✅ Does NOT modify existing views

### Step 4: Test BQML Compatibility

**Test Query:**
```sql
-- Test that BQML can actually use this table
CREATE OR REPLACE MODEL `cbi-v14.models.test_compatibility_check`
OPTIONS(
    model_type='LINEAR_REG',
    input_label_cols=['target_1w'],
    max_iterations=1
) AS
SELECT * EXCEPT(date, target_1m, target_3m, target_6m)
FROM `cbi-v14.models.training_dataset_materialized`
LIMIT 100;
```

**Expected Result:** Should complete successfully (no correlated subquery error)

**Cleanup After Test:**
```sql
DROP MODEL IF EXISTS `cbi-v14.models.test_compatibility_check`;
```

### Step 5: Validate Data Quality

```sql
-- Check row counts and NULL values
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT date) as unique_dates,
    COUNTIF(target_1w IS NULL) as null_1w,
    COUNTIF(feature_vix_stress IS NULL) as null_vix,
    COUNTIF(corr_zl_crude_7d IS NULL) as null_corr
FROM `cbi-v14.models.training_dataset_materialized`;
```

**Expected:**
- total_rows: ~1,250
- unique_dates: ~1,250 (1:1 ratio)
- null_1w: 0
- null_vix: Should be low
- null_corr: Should be acceptable

---

## ⚠️ IMPORTANT SAFETY NOTES

### What This Plan DOES:
- ✅ Creates 3 NEW materialized tables
- ✅ Tests BQML compatibility
- ✅ Validates data quality

### What This Plan DOES NOT DO:
- ❌ Does NOT modify existing views
- ❌ Does NOT delete any existing objects
- ❌ Does NOT start training automatically
- ❌ Does NOT modify source data

### Rollback Plan (If Needed):
```sql
-- Delete all new tables created
DROP TABLE IF EXISTS `cbi-v14.models.price_features_materialized`;
DROP TABLE IF EXISTS `cbi-v14.models.weather_features_daily`;
DROP TABLE IF EXISTS `cbi-v14.models.sentiment_features_daily`;
DROP TABLE IF EXISTS `cbi-v14.models.training_dataset_materialized`;
```

---

## 💰 COST ESTIMATE

- Creating price_features_materialized: ~$0.001
- Creating weather_features_daily: ~$0.001
- Creating sentiment_features_daily: ~$0.001
- Creating training_dataset_materialized: ~$0.01
- Testing BQML compatibility: ~$0.001

**Total Estimated Cost:** < $0.02

**Storage Cost:** ~0.20 MB total (negligible)

---

## 🎯 SUCCESS CRITERIA

This plan is successful if:
1. ✅ All 3 materialized tables create without errors
2. ✅ Row counts match expected (~1,250 rows)
3. ✅ BQML compatibility test passes (no correlated subquery error)
4. ✅ NULL values are within acceptable ranges
5. ✅ Schema has all 159 expected columns

---

## 🚦 APPROVAL REQUIRED

**BEFORE EXECUTING, PLEASE CONFIRM:**

- [ ] Approach looks correct
- [ ] Safety measures are adequate
- [ ] Naming conventions are acceptable
- [ ] Ready to proceed with execution

**Once approved, execution order:**
1. Create price_features_materialized
2. Create weather_features_daily  
3. Create sentiment_features_daily
4. Create training_dataset_materialized
5. Test BQML compatibility
6. Validate data quality
7. **STOP - Do NOT train automatically**

---

**STATUS: ⏸️ AWAITING YOUR APPROVAL TO PROCEED**









