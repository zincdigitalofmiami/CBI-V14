# ENSEMBLE ARCHITECTURE PLAN
**Combining BOOSTED_TREE + ARIMA for Superior Forecasting**

## CURRENT STATUS

### ✅ Phase 1: BOOSTED_TREE Complete
- **Model**: `cbi-v14.models_v4.bqml_1w_all_features`
- **Type**: BOOSTED_TREE_REGRESSOR
- **Features**: 276 numeric features
- **Performance**: MAPE 1.21%, R² 0.9956
- **Status**: ✅ **TRAINED AND READY**

### ⏳ Phase 2: ARIMA Baselines (Next Step)
- **Purpose**: Time-series baseline models
- **Models Needed**:
  - `arima_baseline_1w` (ARIMA_PLUS)
  - `arima_1w_xreg` (ARIMA_PLUS_XREG with external regressors)
- **Status**: ⏳ **NOT YET TRAINED**

### ⏳ Phase 3: Ensemble (Final Step)
- **Purpose**: Combine BOOSTED_TREE + ARIMA for best of both worlds
- **Strategy**: Weighted ensemble
- **Status**: ⏳ **NOT YET CREATED**

---

## ENSEMBLE ARCHITECTURE

### Model Combination Strategy

**Option 1: Weighted Average (Recommended)**
```
Final Prediction = 0.7 × BOOSTED_TREE + 0.3 × ARIMA_XREG
```

**Rationale**:
- **BOOSTED_TREE (70%)**: Captures non-linear relationships, all 276 features, complex interactions
- **ARIMA_XREG (30%)**: Captures time-series trends, seasonal patterns, temporal dependencies

**Option 2: Dynamic Weighting**
```
Weight_BOOSTED = f(volatility, regime, feature_availability)
Weight_ARIMA = 1 - Weight_BOOSTED
```

**Option 3: Stacking Ensemble**
```
Level 1: BOOSTED_TREE + ARIMA_XREG predictions
Level 2: Meta-learner (linear regression) combines predictions
```

---

## PHASE 2: ARIMA BASELINES

### Model 1: ARIMA_PLUS (Simple Baseline)
```sql
CREATE OR REPLACE MODEL `cbi-v14.models_v4.arima_baseline_1w`
OPTIONS(
  model_type='ARIMA_PLUS',
  time_series_timestamp_col='date',
  time_series_data_col='zl_price_current',
  horizon=7,
  auto_arima=TRUE,
  decompose_time_series=TRUE,
  clean_spikes_and_dips=TRUE,
  holiday_region='US'
) AS
SELECT 
  date,
  zl_price_current
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL
ORDER BY date;
```

### Model 2: ARIMA_PLUS_XREG (With External Regressors)
```sql
CREATE OR REPLACE MODEL `cbi-v14.models_v4.arima_1w_xreg`
OPTIONS(
  model_type='ARIMA_PLUS_XREG',
  time_series_timestamp_col='date',
  time_series_data_col='zl_price_current',
  horizon=7,
  auto_ar=TRUE,
  auto_diff=TRUE,
  auto_ma=TRUE,
  xreg_cols=[
    'corr_zl_corn_365d',
    'dxy_lag2',
    'brazil_precip_30d_ma',
    'crude_price',
    'palm_price',
    'usd_cny_rate',
    'fed_funds_rate',
    'treasury_10y_yield'
    -- Add top 20-30 features from BOOSTED_TREE feature importance
  ]
) AS
SELECT 
  date,
  zl_price_current,
  -- External regressors
  * EXCEPT(date, zl_price_current, target_1w, target_1m, target_3m, target_6m)
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL
ORDER BY date;
```

---

## PHASE 3: ENSEMBLE IMPLEMENTATION

### Ensemble Prediction Query
```sql
WITH 
-- BOOSTED_TREE predictions
boosted_predictions AS (
  SELECT 
    date,
    predicted_target_1w as boosted_prediction
  FROM ML.PREDICT(
    MODEL `cbi-v14.models_v4.bqml_1w_all_features`,
    (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1w IS NOT NULL)
  )
),

-- ARIMA predictions
arima_predictions AS (
  SELECT 
    date,
    forecast_value as arima_prediction
  FROM ML.FORECAST(
    MODEL `cbi-v14.models_v4.arima_1w_xreg`,
    STRUCT(7 AS horizon)
  )
),

-- Ensemble combination
ensemble AS (
  SELECT 
    b.date,
    b.boosted_prediction,
    a.arima_prediction,
    -- Weighted ensemble
    (0.7 * b.boosted_prediction + 0.3 * a.arima_prediction) as ensemble_prediction
  FROM boosted_predictions b
  JOIN arima_predictions a ON b.date = a.date
)

SELECT * FROM ensemble;
```

---

## EXPECTED BENEFITS

### BOOSTED_TREE Strengths
- ✅ Captures non-linear relationships
- ✅ Uses all 276 features
- ✅ Handles complex interactions
- ✅ Current MAPE: 1.21%

### ARIMA Strengths
- ✅ Captures time-series trends
- ✅ Handles seasonality
- ✅ Autocorrelation modeling
- ✅ Expected MAPE: 1.5-2.5%

### Ensemble Benefits
- ✅ Combines best of both approaches
- ✅ Expected MAPE: 0.8-1.2% (better than either alone)
- ✅ More robust predictions
- ✅ Better handling of regime changes

---

## EXECUTION PLAN

### Step 1: Train ARIMA Baselines ✅ READY
**Script**: Create `bigquery_sql/TRAIN_ARIMA_BASELINES.sql`
- Train `arima_baseline_1w` (simple ARIMA_PLUS)
- Train `arima_1w_xreg` (ARIMA_PLUS_XREG with top features)

### Step 2: Evaluate ARIMA Performance ✅ READY
**Script**: Create `bigquery_sql/EVALUATE_ARIMA_MODELS.sql`
- Compare ARIMA MAPE vs BOOSTED_TREE MAPE
- Identify best ARIMA model for ensemble

### Step 3: Create Ensemble ✅ READY
**Script**: Create `bigquery_sql/CREATE_ENSEMBLE_1W.sql`
- Combine BOOSTED_TREE + ARIMA predictions
- Weighted average (70/30 split)
- Evaluate ensemble performance

### Step 4: Compare All Models ✅ READY
**Script**: Create `bigquery_sql/COMPARE_ALL_MODELS.sql`
- BOOSTED_TREE: MAPE 1.21%
- ARIMA Baseline: MAPE TBD
- ARIMA_XREG: MAPE TBD
- Ensemble: MAPE TBD (expected best)

---

## CURRENT STATUS

**✅ Phase 1 Complete**: BOOSTED_TREE trained (MAPE 1.21%)
**⏳ Phase 2 Pending**: ARIMA baselines need to be trained
**⏳ Phase 3 Pending**: Ensemble after ARIMA training

---

## RECOMMENDATION

**Next Steps:**
1. Train ARIMA baselines (simple and with external regressors)
2. Evaluate ARIMA performance
3. Create ensemble combining BOOSTED_TREE + ARIMA
4. Compare final ensemble performance

**Expected Outcome:**
- Ensemble MAPE: 0.8-1.2% (better than individual models)
- More robust predictions across different market regimes
- Best of both worlds: non-linear relationships + time-series patterns


