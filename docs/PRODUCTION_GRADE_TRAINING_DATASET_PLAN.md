# PRODUCTION-GRADE TRAINING DATASET IMPLEMENTATION
**Date:** October 22, 2025  
**Status:** ⚠️ DESIGN PHASE - AWAITING APPROVAL  
**Approach:** Institutional-grade with full engineering best practices  
**Risk Level:** LOW (staged rollout with comprehensive validation)

---

## 🎯 EXECUTIVE SUMMARY

Build a **production-grade materialized training dataset** with:
- ✅ Intermediate validation at every step
- ✅ Proper partitioning and clustering for performance
- ✅ Incremental refresh mechanism for efficiency
- ✅ Schema documentation and metadata tracking
- ✅ Feature versioning for A/B testing
- ✅ Automated testing framework
- ✅ Monitoring and alerting
- ✅ Staging → Production promotion workflow

**Not a quick fix - this is institutional-grade data engineering.**

---

## 📐 ARCHITECTURE OVERVIEW

```
SOURCE DATA
    ↓
STAGING TABLES (with validation)
    ↓
VERSIONED FEATURE TABLES (partitioned/clustered)
    ↓
TESTING & VALIDATION (automated comparison)
    ↓
PRODUCTION TRAINING TABLE (with metadata)
    ↓
MONITORING & ALERTS (data quality tracking)
```

---

## 🏗️ PHASE 1: STAGING INFRASTRUCTURE

### 1.1 Create Staging Dataset

**Purpose:** Isolate work-in-progress from production

```sql
-- Create staging dataset if not exists
CREATE SCHEMA IF NOT EXISTS `cbi-v14.staging_ml`
OPTIONS(
    description="Staging environment for ML feature engineering",
    location="us-central1"
);
```

### 1.2 Create Metadata Tracking Table

**Purpose:** Track all feature table versions, lineage, and quality metrics

```sql
CREATE OR REPLACE TABLE `cbi-v14.staging_ml.feature_metadata` (
    feature_table_name STRING NOT NULL,
    version STRING NOT NULL,
    created_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    created_by STRING DEFAULT SESSION_USER(),
    source_query STRING,
    row_count INT64,
    column_count INT64,
    date_range_start DATE,
    date_range_end DATE,
    validation_status STRING,  -- 'pending', 'passed', 'failed'
    validation_results JSON,
    null_percentage_summary FLOAT64,
    promoted_to_production BOOL DEFAULT FALSE,
    promotion_timestamp TIMESTAMP,
    notes STRING
);
```

### 1.3 Create Data Quality Validation Framework

**Purpose:** Reusable validation functions

```sql
-- Validation results table
CREATE OR REPLACE TABLE `cbi-v14.staging_ml.validation_log` (
    validation_id STRING NOT NULL,
    table_name STRING NOT NULL,
    validation_type STRING NOT NULL,  -- 'row_count', 'null_check', 'distribution', etc.
    validation_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    status STRING NOT NULL,  -- 'PASS', 'FAIL', 'WARNING'
    expected_value STRING,
    actual_value STRING,
    difference_pct FLOAT64,
    details JSON
);
```

---

## 🏗️ PHASE 2: MATERIALIZED FEATURE TABLES (VERSIONED)

### 2.1 Price Features (v1) - STAGING

**Table:** `staging_ml.price_features_v1`  
**Partitioning:** By date (MONTH)  
**Clustering:** By zl_price_current, target_1w  

```sql
CREATE OR REPLACE TABLE `cbi-v14.staging_ml.price_features_v1`
PARTITION BY DATE_TRUNC(date, MONTH)
CLUSTER BY zl_price_current, target_1w
OPTIONS(
    description="Materialized price features with all window functions - Version 1",
    labels=[("feature_type", "price"), ("version", "v1"), ("environment", "staging")]
)
AS
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

**Validation Step 2.1.1: Row Count & Completeness**

```sql
-- Insert validation record
INSERT INTO `cbi-v14.staging_ml.validation_log` (
    validation_id,
    table_name,
    validation_type,
    status,
    expected_value,
    actual_value,
    details
)
WITH validation_checks AS (
    SELECT 
        GENERATE_UUID() as validation_id,
        'price_features_v1' as table_name,
        'row_count' as validation_type,
        CASE 
            WHEN COUNT(*) >= 1200 THEN 'PASS'
            WHEN COUNT(*) >= 1000 THEN 'WARNING'
            ELSE 'FAIL'
        END as status,
        '>=1250' as expected_value,
        CAST(COUNT(*) AS STRING) as actual_value,
        TO_JSON(STRUCT(
            COUNT(*) as total_rows,
            COUNT(DISTINCT date) as unique_dates,
            MIN(date) as min_date,
            MAX(date) as max_date,
            COUNTIF(target_1w IS NULL) as null_targets,
            COUNTIF(zl_price_lag1 IS NULL) as null_lag1
        )) as details
    FROM `cbi-v14.staging_ml.price_features_v1`
)
SELECT * FROM validation_checks;
```

**Validation Step 2.1.2: Window Function Accuracy Test**

```sql
-- Test that LAG calculations match expectations
WITH test_sample AS (
    -- Get 100 random dates
    SELECT date
    FROM `cbi-v14.staging_ml.price_features_v1`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
    ORDER BY RAND()
    LIMIT 100
),
recalculated AS (
    SELECT 
        p.date,
        p.zl_price_lag1 as materialized_lag1,
        LAG(p.zl_price_current) OVER (ORDER BY p.date) as recalc_lag1,
        ABS(p.zl_price_lag1 - LAG(p.zl_price_current) OVER (ORDER BY p.date)) as diff
    FROM `cbi-v14.staging_ml.price_features_v1` p
    WHERE p.date IN (SELECT date FROM test_sample)
)
INSERT INTO `cbi-v14.staging_ml.validation_log` (
    validation_id,
    table_name,
    validation_type,
    status,
    expected_value,
    actual_value,
    details
)
SELECT 
    GENERATE_UUID(),
    'price_features_v1',
    'window_function_accuracy',
    CASE 
        WHEN AVG(diff) < 0.0001 THEN 'PASS'
        WHEN AVG(diff) < 0.01 THEN 'WARNING'
        ELSE 'FAIL'
    END,
    '<0.0001',
    CAST(AVG(diff) AS STRING),
    TO_JSON(STRUCT(
        COUNT(*) as samples_tested,
        AVG(diff) as avg_difference,
        MAX(diff) as max_difference,
        COUNTIF(diff > 0.01) as significant_diffs
    ))
FROM recalculated;
```

**Validation Step 2.1.3: Update Metadata**

```sql
INSERT INTO `cbi-v14.staging_ml.feature_metadata` (
    feature_table_name,
    version,
    source_query,
    row_count,
    column_count,
    date_range_start,
    date_range_end,
    validation_status,
    validation_results
)
SELECT 
    'price_features' as feature_table_name,
    'v1' as version,
    'See staging_ml.price_features_v1 DDL' as source_query,
    (SELECT COUNT(*) FROM `cbi-v14.staging_ml.price_features_v1`) as row_count,
    (SELECT COUNT(*) FROM `cbi-v14.staging_ml.INFORMATION_SCHEMA.COLUMNS` 
     WHERE table_name = 'price_features_v1') as column_count,
    (SELECT MIN(date) FROM `cbi-v14.staging_ml.price_features_v1`) as date_range_start,
    (SELECT MAX(date) FROM `cbi-v14.staging_ml.price_features_v1`) as date_range_end,
    (SELECT 
        CASE 
            WHEN COUNTIF(status = 'FAIL') > 0 THEN 'failed'
            WHEN COUNTIF(status = 'WARNING') > 0 THEN 'warning'
            ELSE 'passed'
        END
     FROM `cbi-v14.staging_ml.validation_log` 
     WHERE table_name = 'price_features_v1') as validation_status,
    (SELECT TO_JSON(ARRAY_AGG(STRUCT(validation_type, status, actual_value)))
     FROM `cbi-v14.staging_ml.validation_log`
     WHERE table_name = 'price_features_v1') as validation_results;
```

### 2.2 Weather Features (v1) - STAGING

**Table:** `staging_ml.weather_features_v1`  
**Partitioning:** By date (MONTH)  
**Clustering:** By brazil_temp, argentina_temp

```sql
CREATE OR REPLACE TABLE `cbi-v14.staging_ml.weather_features_v1`
PARTITION BY DATE_TRUNC(date, MONTH)
CLUSTER BY brazil_temp, argentina_temp
OPTIONS(
    description="Daily weather features aggregated by region - Version 1",
    labels=[("feature_type", "weather"), ("version", "v1"), ("environment", "staging")]
)
AS
SELECT 
    date,
    AVG(CASE WHEN region LIKE '%Brazil%' THEN temp_max END) as brazil_temp,
    AVG(CASE WHEN region LIKE '%Brazil%' THEN precip_mm END) as brazil_precip,
    AVG(CASE WHEN region LIKE '%Argentina%' THEN temp_max END) as argentina_temp,
    AVG(CASE WHEN region LIKE '%US%' THEN temp_max END) as us_temp
FROM `cbi-v14.forecasting_data_warehouse.weather_data`
GROUP BY date;
```

**Validation:** (Similar pattern as price_features)

### 2.3 Sentiment Features (v1) - STAGING

**Table:** `staging_ml.sentiment_features_v1`  
**Partitioning:** By date (MONTH)  
**Clustering:** By avg_sentiment

```sql
CREATE OR REPLACE TABLE `cbi-v14.staging_ml.sentiment_features_v1`
PARTITION BY DATE_TRUNC(date, MONTH)
CLUSTER BY avg_sentiment
OPTIONS(
    description="Daily sentiment features from social media - Version 1",
    labels=[("feature_type", "sentiment"), ("version", "v1"), ("environment", "staging")]
)
AS
SELECT 
    DATE(timestamp) as date,
    AVG(sentiment_score) as avg_sentiment,
    STDDEV(sentiment_score) as sentiment_volatility,
    COUNT(*) as sentiment_volume
FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
GROUP BY DATE(timestamp);
```

**Validation:** (Similar pattern)

---

## 🏗️ PHASE 3: STAGING TRAINING TABLE

### 3.1 Create Full Training Table - STAGING

**Table:** `staging_ml.training_dataset_v1`  
**Partitioning:** By date (MONTH)  
**Clustering:** By target_1w, target_1m, feature_vix_stress

```sql
CREATE OR REPLACE TABLE `cbi-v14.staging_ml.training_dataset_v1`
PARTITION BY DATE_TRUNC(date, MONTH)
CLUSTER BY target_1w, target_1m, feature_vix_stress
OPTIONS(
    description="Complete BQML-compatible training dataset with all 159 features - Version 1",
    labels=[("purpose", "ml_training"), ("version", "v1"), ("environment", "staging")]
)
AS
SELECT 
    p.date,
    
    -- TARGETS (4)
    p.target_1w,
    p.target_1m,
    p.target_3m,
    p.target_6m,
    
    -- PRICE FEATURES (14) - FROM MATERIALIZED TABLE
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
    
    -- [ALL OTHER FEATURES FROM YOUR ORIGINAL VIEW]
    -- (Full query from previous plan - 159 total columns)
    
    -- BIG 8 SIGNALS (9)
    COALESCE(b8.feature_vix_stress, 0.5) as feature_vix_stress,
    COALESCE(b8.feature_harvest_pace, 0.5) as feature_harvest_pace,
    COALESCE(b8.feature_china_relations, 0.5) as feature_china_relations,
    COALESCE(b8.feature_tariff_threat, 0.3) as feature_tariff_threat,
    COALESCE(b8.feature_geopolitical_volatility, 0.4) as feature_geopolitical_volatility,
    COALESCE(b8.feature_biofuel_cascade, 0.5) as feature_biofuel_cascade,
    COALESCE(b8.feature_hidden_correlation, 0.0) as feature_hidden_correlation,
    COALESCE(b8.feature_biofuel_ethanol, 0.5) as feature_biofuel_ethanol,
    COALESCE(b8.big8_composite_score, 0.5) as big8_composite_score,
    
    -- ... (rest of features)
    
    -- METADATA (3)
    EXTRACT(DAYOFWEEK FROM p.date) as day_of_week,
    EXTRACT(MONTH FROM p.date) as month,
    EXTRACT(QUARTER FROM p.date) as quarter
    
FROM `cbi-v14.staging_ml.price_features_v1` p
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
LEFT JOIN `cbi-v14.staging_ml.weather_features_v1` w ON p.date = w.date
LEFT JOIN `cbi-v14.staging_ml.sentiment_features_v1` s ON p.date = s.date

WHERE p.target_1w IS NOT NULL;
```

### 3.2 Comprehensive Validation of Training Table

**Schema Validation:**
```sql
-- Verify all 159 columns present
INSERT INTO `cbi-v14.staging_ml.validation_log` (
    validation_id,
    table_name,
    validation_type,
    status,
    expected_value,
    actual_value,
    details
)
SELECT 
    GENERATE_UUID(),
    'training_dataset_v1',
    'schema_column_count',
    CASE WHEN COUNT(*) = 159 THEN 'PASS' ELSE 'FAIL' END,
    '159',
    CAST(COUNT(*) AS STRING),
    TO_JSON(ARRAY_AGG(column_name ORDER BY ordinal_position))
FROM `cbi-v14.staging_ml.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_v1';
```

**Data Quality Validation:**
```sql
-- NULL percentage by column
INSERT INTO `cbi-v14.staging_ml.validation_log` (
    validation_id,
    table_name,
    validation_type,
    status,
    expected_value,
    actual_value,
    details
)
WITH null_stats AS (
    SELECT 
        column_name,
        COUNTIF(column_value IS NULL) as null_count,
        COUNT(*) as total_count,
        ROUND(COUNTIF(column_value IS NULL) / COUNT(*) * 100, 2) as null_pct
    FROM `cbi-v14.staging_ml.training_dataset_v1`,
    UNNEST([
        -- Dynamic column unpivot would go here
        -- For production, generate this programmatically
    ]) as column_value
    GROUP BY column_name
)
SELECT 
    GENERATE_UUID(),
    'training_dataset_v1',
    'null_percentage_summary',
    CASE 
        WHEN AVG(null_pct) < 5 THEN 'PASS'
        WHEN AVG(null_pct) < 15 THEN 'WARNING'
        ELSE 'FAIL'
    END,
    '<5%',
    CAST(AVG(null_pct) AS STRING),
    TO_JSON(ARRAY_AGG(STRUCT(column_name, null_pct) ORDER BY null_pct DESC LIMIT 10))
FROM null_stats;
```

### 3.3 BQML Compatibility Test - STAGING

```sql
-- Test actual BQML training
CREATE OR REPLACE MODEL `cbi-v14.staging_ml.compatibility_test_v1`
OPTIONS(
    model_type='LINEAR_REG',
    input_label_cols=['target_1w'],
    max_iterations=1,
    labels=[("purpose", "validation_test"), ("version", "v1")]
) AS
SELECT * EXCEPT(date, target_1m, target_3m, target_6m)
FROM `cbi-v14.staging_ml.training_dataset_v1`
WHERE target_1w IS NOT NULL
LIMIT 100;

-- Log result
INSERT INTO `cbi-v14.staging_ml.validation_log` (
    validation_id,
    table_name,
    validation_type,
    status,
    expected_value,
    actual_value,
    details
)
SELECT 
    GENERATE_UUID(),
    'training_dataset_v1',
    'bqml_compatibility',
    'PASS',  -- If we got here, it passed
    'Model created successfully',
    'Linear regression model trained on 100 rows',
    TO_JSON(STRUCT(
        'compatibility_test_v1' as model_name,
        CURRENT_TIMESTAMP() as test_timestamp,
        100 as rows_used,
        'No correlated subquery errors' as result
    ));

-- Clean up test model
DROP MODEL `cbi-v14.staging_ml.compatibility_test_v1`;
```

---

## 🏗️ PHASE 4: INCREMENTAL REFRESH MECHANISM

### 4.1 Create Refresh Procedure

**Purpose:** Update materialized tables with only new data

```sql
CREATE OR REPLACE PROCEDURE `cbi-v14.staging_ml.refresh_price_features`()
BEGIN
    -- Get last date in materialized table
    DECLARE last_materialized_date DATE;
    
    SET last_materialized_date = (
        SELECT MAX(date) 
        FROM `cbi-v14.staging_ml.price_features_v1`
    );
    
    -- Insert only new rows
    INSERT INTO `cbi-v14.staging_ml.price_features_v1`
    WITH daily_prices AS (
        SELECT 
            DATE(time) as date,
            AVG(close) as close_price,
            SUM(volume) as volume
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
        WHERE symbol = 'ZL'
        AND DATE(time) > last_materialized_date
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
    
    -- Log refresh
    INSERT INTO `cbi-v14.staging_ml.feature_metadata` (
        feature_table_name,
        version,
        notes
    )
    VALUES (
        'price_features',
        'v1',
        FORMAT('Incremental refresh completed at %t. Added %d new rows.', 
               CURRENT_TIMESTAMP(), 
               @@row_count)
    );
END;
```

### 4.2 Schedule Daily Refresh

**Cloud Scheduler Job (to be configured via console or gcloud):**
```bash
# Schedule daily at 6 AM UTC
gcloud scheduler jobs create http refresh-ml-features \
    --location=us-central1 \
    --schedule="0 6 * * *" \
    --uri="https://bigquery.googleapis.com/bigquery/v2/projects/cbi-v14/jobs" \
    --http-method=POST \
    --message-body='{
        "configuration": {
            "query": {
                "query": "CALL `cbi-v14.staging_ml.refresh_price_features`()",
                "useLegacySql": false
            }
        }
    }'
```

---

## 🏗️ PHASE 5: SCHEMA DOCUMENTATION

### 5.1 Create Data Dictionary

```sql
CREATE OR REPLACE TABLE `cbi-v14.staging_ml.data_dictionary` (
    table_name STRING NOT NULL,
    column_name STRING NOT NULL,
    data_type STRING NOT NULL,
    description STRING,
    calculation_logic STRING,
    source_table STRING,
    business_definition STRING,
    expected_range STRING,
    null_policy STRING,  -- 'NOT_ALLOWED', 'EXPECTED', 'COALESCED'
    created_date DATE DEFAULT CURRENT_DATE(),
    last_updated DATE DEFAULT CURRENT_DATE()
);

-- Populate for price_features
INSERT INTO `cbi-v14.staging_ml.data_dictionary` VALUES
('price_features_v1', 'date', 'DATE', 'Trading date', 'DATE(time)', 'soybean_oil_prices', 'Business day for soybean oil futures trading', '2020-10-21 to present', 'NOT_ALLOWED', CURRENT_DATE(), CURRENT_DATE()),
('price_features_v1', 'zl_price_current', 'FLOAT64', 'Current day closing price', 'AVG(close)', 'soybean_oil_prices', 'Soybean oil futures (ZL) closing price in $/cwt', '20.0 to 80.0', 'NOT_ALLOWED', CURRENT_DATE(), CURRENT_DATE()),
('price_features_v1', 'target_1w', 'FLOAT64', '1-week forward price target', 'LEAD(close_price, 7) OVER (ORDER BY date)', 'price_features', 'Price 7 trading days in the future', '20.0 to 80.0', 'EXPECTED (last 7 rows)', CURRENT_DATE(), CURRENT_DATE()),
('price_features_v1', 'zl_price_lag1', 'FLOAT64', 'Previous day price', 'LAG(zl_price_current, 1) OVER (ORDER BY date)', 'price_features', 'T-1 closing price for momentum calculations', '20.0 to 80.0', 'EXPECTED (first row)', CURRENT_DATE(), CURRENT_DATE()),
-- ... (Continue for all 159 columns)
;
```

### 5.2 Create Lineage Tracking

```sql
CREATE OR REPLACE TABLE `cbi-v14.staging_ml.feature_lineage` (
    feature_table STRING NOT NULL,
    feature_column STRING NOT NULL,
    source_table STRING NOT NULL,
    source_column STRING,
    transformation_type STRING,  -- 'DIRECT', 'WINDOW', 'AGGREGATE', 'JOIN'
    transformation_logic STRING,
    dependency_level INT64  -- How many hops from raw data
);

-- Example lineage entries
INSERT INTO `cbi-v14.staging_ml.feature_lineage` VALUES
('training_dataset_v1', 'zl_price_lag1', 'price_features_v1', 'zl_price_lag1', 'DIRECT', 'SELECT from materialized table', 1),
('price_features_v1', 'zl_price_lag1', 'soybean_oil_prices', 'close', 'WINDOW', 'LAG(close, 1) OVER (ORDER BY date)', 0),
('training_dataset_v1', 'feature_vix_stress', 'vw_big_eight_signals', 'feature_vix_stress', 'JOIN', 'LEFT JOIN on date with COALESCE default', 1);
```

---

## 🏗️ PHASE 6: MONITORING & ALERTING

### 6.1 Create Monitoring Dashboard Table

```sql
CREATE OR REPLACE TABLE `cbi-v14.staging_ml.data_quality_metrics` (
    metric_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    table_name STRING NOT NULL,
    metric_name STRING NOT NULL,
    metric_value FLOAT64,
    threshold_warning FLOAT64,
    threshold_critical FLOAT64,
    status STRING,  -- 'OK', 'WARNING', 'CRITICAL'
    alert_sent BOOL DEFAULT FALSE
);
```

### 6.2 Data Quality Monitoring Procedure

```sql
CREATE OR REPLACE PROCEDURE `cbi-v14.staging_ml.monitor_data_quality`()
BEGIN
    -- Check for row count drops
    INSERT INTO `cbi-v14.staging_ml.data_quality_metrics` (
        table_name,
        metric_name,
        metric_value,
        threshold_warning,
        threshold_critical,
        status
    )
    WITH current_count AS (
        SELECT COUNT(*) as cnt
        FROM `cbi-v14.staging_ml.training_dataset_v1`
    ),
    expected_count AS (
        SELECT 1250 as expected
    )
    SELECT 
        'training_dataset_v1',
        'row_count',
        current_count.cnt,
        expected_count.expected * 0.95,  -- 5% drop = warning
        expected_count.expected * 0.90,  -- 10% drop = critical
        CASE 
            WHEN current_count.cnt < expected_count.expected * 0.90 THEN 'CRITICAL'
            WHEN current_count.cnt < expected_count.expected * 0.95 THEN 'WARNING'
            ELSE 'OK'
        END
    FROM current_count, expected_count;
    
    -- Check for NULL percentage spikes
    -- Check for distribution shifts
    -- Check for data freshness
    -- ... (Additional monitoring checks)
END;
```

---

## 🏗️ PHASE 7: PRODUCTION PROMOTION

### 7.1 Promotion Checklist Procedure

```sql
CREATE OR REPLACE PROCEDURE `cbi-v14.staging_ml.promote_to_production`(
    staging_table_name STRING,
    production_table_name STRING
)
BEGIN
    DECLARE all_validations_passed BOOL;
    
    -- Check all validations passed
    SET all_validations_passed = (
        SELECT COUNTIF(status = 'FAIL') = 0
        FROM `cbi-v14.staging_ml.validation_log`
        WHERE table_name = staging_table_name
        AND validation_timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    );
    
    IF NOT all_validations_passed THEN
        RAISE USING MESSAGE = 'Cannot promote - validation failures exist';
    END IF;
    
    -- Create production table (or replace if exists)
    EXECUTE IMMEDIATE FORMAT('''
        CREATE OR REPLACE TABLE `cbi-v14.models.%s`
        CLONE `cbi-v14.staging_ml.%s`
        OPTIONS(
            labels=[("environment", "production"), ("promoted_from", "staging")]
        )
    ''', production_table_name, staging_table_name);
    
    -- Update metadata
    UPDATE `cbi-v14.staging_ml.feature_metadata`
    SET promoted_to_production = TRUE,
        promotion_timestamp = CURRENT_TIMESTAMP()
    WHERE feature_table_name = staging_table_name
    AND version = REGEXP_EXTRACT(staging_table_name, r'_v(\d+)$');
    
    -- Log promotion
    INSERT INTO `cbi-v14.staging_ml.validation_log` (
        validation_id,
        table_name,
        validation_type,
        status,
        details
    )
    VALUES (
        GENERATE_UUID(),
        production_table_name,
        'production_promotion',
        'SUCCESS',
        TO_JSON(STRUCT(
            staging_table_name as source,
            CURRENT_TIMESTAMP() as promoted_at,
            SESSION_USER() as promoted_by
        ))
    );
END;
```

---

## 📋 EXECUTION WORKFLOW

### ✅ Complete Step-by-Step Process:

```
1. CREATE INFRASTRUCTURE
   ├─ Create staging_ml dataset
   ├─ Create metadata tables
   └─ Create validation framework
   
2. BUILD STAGING FEATURES (v1)
   ├─ price_features_v1
   │  ├─ Create table
   │  ├─ Validate row counts
   │  ├─ Validate window functions
   │  └─ Update metadata
   ├─ weather_features_v1
   │  └─ (Same validation pattern)
   └─ sentiment_features_v1
      └─ (Same validation pattern)
   
3. BUILD STAGING TRAINING TABLE (v1)
   ├─ training_dataset_v1
   ├─ Schema validation (159 columns)
   ├─ Data quality validation
   ├─ BQML compatibility test
   └─ Update metadata
   
4. SETUP AUTOMATION
   ├─ Create refresh procedures
   ├─ Schedule daily refreshes
   ├─ Setup monitoring
   └─ Configure alerts
   
5. DOCUMENTATION
   ├─ Populate data dictionary
   ├─ Create lineage tracking
   └─ Generate schema docs
   
6. STAGING VALIDATION
   ├─ Review all validation logs
   ├─ Verify data quality metrics
   └─ Confirm BQML compatibility
   
7. PRODUCTION PROMOTION (Only if all pass)
   ├─ Run promotion checklist
   ├─ Clone to production
   └─ Update production metadata
   
8. PRODUCTION VALIDATION
   ├─ Re-run BQML compatibility test
   ├─ Compare staging vs production
   └─ Final sign-off
```

---

## 💰 COST ESTIMATE

- **Initial Build**: ~$0.15 (all tables + validation)
- **Daily Refresh**: ~$0.02/day
- **Monthly Monitoring**: ~$0.10/month
- **Storage**: ~0.5 MB (~$0.01/month)

**Total First Month:** ~$0.75  
**Ongoing Monthly:** ~$0.72

---

## 🎯 SUCCESS CRITERIA

Production promotion approved only if:

- [ ] All validation checks show 'PASS' status
- [ ] Schema contains exactly 159 columns
- [ ] Row count ≥ 1,200
- [ ] NULL percentage < 5% average
- [ ] BQML compatibility test succeeds
- [ ] Window function accuracy test passes
- [ ] Data dictionary complete
- [ ] Lineage tracking documented
- [ ] Monitoring active
- [ ] Incremental refresh tested

---

## ⚠️ ROLLBACK PLAN

At any point, revert by:
```sql
-- Drop all staging tables
DROP SCHEMA IF EXISTS `cbi-v14.staging_ml` CASCADE;

-- Production tables remain untouched unless explicitly promoted
```

---

**STATUS: ⏸️ AWAITING YOUR APPROVAL**

**This is institutional-grade. Ready to proceed when you are.**












