# Feature Enhancement & Model Architecture Plan

**Date:** 2025-11-02  
**Goal:** Integrate external data and enhance time-series features for maximum accuracy

## Current Feature Inventory

### ✅ Already Have:
- **Weather/Climate**: 13 features (Brazil weather, Argentina temp)
- **Related Commodities**: 41 features (corn, wheat, palm, crude correlations)
- **Economic Indicators**: 33 features (DXY, VIX, FX, correlations)
- **Global Demand**: 14 features (China imports, sentiment, livestock indicators)
- **Lag Features**: 4 features (zl_price_lag1/7/30)
- **Rolling Stats**: 20 features (MAs, volatility, momentum)
- **WASDE Indicators**: 6 features (is_wasde_day, is_crop_report_day)
- **Basic Technical**: 4 features (rsi_proxy, momentum_30d)

### ⚠️ Missing/Needs Enhancement:

1. **Weather/Climate** (High Priority):
   - Argentina weather: Precipitation, drought indices
   - US growing region weather (Midwest states)
   - La Niña/El Niño indicators (ONI index)
   - Growing season indicators (planting/harvest dates)

2. **Technical Indicators** (Medium Priority):
   - Full RSI (Relative Strength Index) - currently only proxy
   - MACD (Moving Average Convergence Divergence)
   - Bollinger Bands (upper/lower bands)
   - Stochastic Oscillator

3. **Lag Features** (Medium Priority):
   - More target variable lags (target_1w_lag1, target_1w_lag7, target_1w_lag30)
   - Additional feature lags for key predictors

4. **WASDE Integration** (Low Priority - already have indicators):
   - WASDE report actual values (supply/demand numbers)
   - Pre/post WASDE report price movements

## Recommended Model Architecture Enhancements

### Option 1: ARIMA_PLUS_XREG (For Time Series)
BQML's ARIMA_PLUS_XREG model incorporates external regressors (your features) with time-series modeling.

**Advantages:**
- Specifically designed for time-series forecasting
- Combines autoregressive time-series with external features
- Better captures temporal dependencies

**SQL Template:**
```sql
CREATE OR REPLACE MODEL `cbi-v14.models_v4.arima_1w_xreg`
OPTIONS(
  model_type='ARIMA_PLUS_XREG',
  time_series_timestamp_col='date',
  time_series_data_col='zl_price_current',
  auto_ar=TRUE,
  auto_diff=TRUE,
  auto_ma=TRUE,
  -- Include external regressors (all your features)
  xreg_cols=[  -- Add your key feature columns here
    'corr_zl_corn_365d',
    'dxy_lag2',
    'brazil_precip_30d_ma',
    -- ... etc
  ]
) AS
SELECT 
  date,
  zl_price_current,
  -- External regressors
  * EXCEPT(date, zl_price_current, target_1w)
FROM `cbi-v14.models_v4.train_1w`
WHERE target_1w IS NOT NULL;
```

### Option 2: Ensemble Approach (Best of Both)
Combine BOOSTED_TREE with ARIMA_PLUS_XREG in an ensemble.

**Strategy:**
- BOOSTED_TREE: 70% weight (non-linear relationships, all features)
- ARIMA_PLUS_XREG: 30% weight (time-series trend, seasonal patterns)

See: `scripts/train_v4_ensemble.py` (already has ARIMA ensemble framework)

## Feature Creation SQL

### Technical Indicators

```sql
-- Create RSI (14-day)
RSI_14 AS (
  SELECT 
    date,
    zl_price_current,
    100 - (100 / (1 + AVG(CASE WHEN zl_price_current > LAG(zl_price_current) OVER (ORDER BY date) 
                               THEN zl_price_current - LAG(zl_price_current) OVER (ORDER BY date)
                               ELSE 0 END) OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)
            / NULLIF(AVG(CASE WHEN zl_price_current < LAG(zl_price_current) OVER (ORDER BY date)
                             THEN ABS(zl_price_current - LAG(zl_price_current) OVER (ORDER BY date))
                             ELSE 0 END) OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW), 0)))
    AS rsi_14
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)

-- MACD (12, 26, 9)
MACD AS (
  SELECT 
    date,
    EMA_12 - EMA_26 AS macd_line,
    (EMA_12 - EMA_26) - EMA_9 AS macd_signal,
    (EMA_12 - EMA_26) - ((EMA_12 - EMA_26) - EMA_9) AS macd_histogram
  FROM (
    SELECT 
      date,
      AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS EMA_12,
      AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 25 PRECEDING AND CURRENT ROW) AS EMA_26,
      AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) AS EMA_9
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  )
)

-- Bollinger Bands (20-day, 2 std dev)
BOLLINGER AS (
  SELECT 
    date,
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS bb_middle,
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) + 
      (2 * STDDEV(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)) AS bb_upper,
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) - 
      (2 * STDDEV(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)) AS bb_lower,
    (zl_price_current - AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)) /
      NULLIF(STDDEV(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 0) AS bb_percent
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)
```

### Additional Lag Features

```sql
-- Target variable lags
target_1w_lag1,
target_1w_lag7,
target_1w_lag30,
-- Key feature lags
dxy_lag7,
dxy_lag30,
corn_price_lag7,
brazil_precip_30d_ma_lag7,
```

## Validation Strategy

### Current Approach:
- Custom split: `date < '2025-09-01'` for training
- Test: `date >= '2025-09-01'`

### Recommended: Rolling-Window Cross-Validation

```sql
-- Example rolling-window validation query
WITH rolling_windows AS (
  SELECT 
    date,
    CASE 
      WHEN date < '2022-01-01' THEN 'train_initial'
      WHEN date >= '2022-01-01' AND date < '2023-01-01' THEN 'val_window1'
      WHEN date >= '2023-01-01' AND date < '2024-01-01' THEN 'val_window2'
      WHEN date >= '2024-01-01' THEN 'test_final'
    END AS cv_fold
  FROM `cbi-v14.models_v4.train_1w`
)
SELECT * FROM rolling_windows
```

**Implementation:**
1. Train on 2020-2022, validate on 2023
2. Train on 2020-2023, validate on 2024
3. Final model: Train on 2020-2024, test on 2025

## Implementation Priority

### Phase 1: Quick Wins (Immediate)
1. ✅ **Current**: Optimized BOOSTED_TREE with hyperparameter tuning
2. **Add**: Target variable lags (target_1w_lag1/7/30)
3. **Add**: Technical indicators (RSI, MACD, Bollinger Bands)

### Phase 2: Model Enhancement (Next)
4. **Create**: ARIMA_PLUS_XREG model alongside BOOSTED_TREE
5. **Implement**: Ensemble combining both models
6. **Validate**: Rolling-window cross-validation

### Phase 3: External Data (Future)
7. **Integrate**: US growing region weather data
8. **Add**: La Niña/El Niño indicators (ONI index)
9. **Enhance**: WASDE actual report values

## Files to Create

1. `bigquery_sql/create_technical_indicators.sql` - RSI, MACD, Bollinger Bands
2. `bigquery_sql/create_additional_lags.sql` - Target and feature lags
3. `bigquery_sql/train_arima_1w_xreg.sql` - ARIMA with external regressors
4. `scripts/train_ensemble_1w.py` - Combined BOOSTED_TREE + ARIMA ensemble
5. `scripts/rolling_window_validation.py` - Rolling-window CV script

## Expected Impact

- **Current**: 57 features, 8% MAPE
- **After Phase 1**: ~80-100 features, estimated 5-6% MAPE
- **After Phase 2**: Ensemble model, estimated 3-4% MAPE
- **After Phase 3**: Full external data, estimated 2-3% MAPE (research-grade)

## Next Steps

1. Start with Phase 1: Add technical indicators and target lags
2. Test ARIMA_PLUS_XREG model
3. Compare ensemble vs single model
4. Implement rolling-window validation


