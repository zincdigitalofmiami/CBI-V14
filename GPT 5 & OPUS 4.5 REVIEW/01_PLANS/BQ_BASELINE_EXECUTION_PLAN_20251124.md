# 🚀 BQ BASELINE EXECUTION PLAN
**Date:** November 24, 2025  
**Status:** 🟢 VALIDATED - READY FOR EXECUTION  
**Purpose:** Get from current state → first baseline model trained

---

## 📊 CURRENT BIGQUERY STATE (VERIFIED)

### **Datasets Present:**
| Dataset | Purpose | Status |
|---------|---------|--------|
| `market_data` | Databento price data | ✅ EXISTS |
| `raw_intelligence` | FRED, weather, news | ✅ EXISTS (empty) |
| `features` | Calculated features | ✅ EXISTS (empty) |
| `training` | Training tables | ✅ EXISTS (empty) |
| `predictions` | Model outputs | ✅ EXISTS |
| `monitoring` | Ops tracking | ✅ EXISTS |
| `ops` | Operations | ✅ EXISTS |
| `api` | API serving | ✅ EXISTS |
| `utils` | Utilities | ✅ EXISTS |
| `views` | Views | ✅ EXISTS |

### **Data Present:**
| Table | Rows | Date Range | Status |
|-------|------|------------|--------|
| `market_data.databento_futures_ohlcv_1d` | **6,034** | 2010-2025 | ✅ POPULATED |
| - ZL (Soybean Oil) | 3,998 | 2010-06-06 → 2025-11-14 | ✅ |
| - MES (Micro E-mini S&P) | 2,036 | 2019-05-05 → 2025-11-16 | ✅ |
| All other tables | **0** | N/A | ⏸️ Empty shells |

### **Tables Empty (Need Population):**
- `raw_intelligence.fred_economic` - 0 rows
- `raw_intelligence.weather_segmented` - 0 rows
- `raw_intelligence.cftc_positioning` - 0 rows
- `raw_intelligence.volatility_daily` - 0 rows
- `features.daily_ml_matrix` - 0 rows
- `features.regime_calendar` - 0 rows
- All `training.*` tables - 0 rows

---

## 🎯 EXECUTION PHASES

### **PHASE 0: Regime Calendar (30 min)** ⏳

**Goal:** Populate regime calendar so all data can be tagged with regime

```sql
-- Insert regime calendar
INSERT INTO `cbi-v14.features.regime_calendar` (date, regime, weight, description)
WITH date_series AS (
    SELECT date
    FROM UNNEST(GENERATE_DATE_ARRAY('2010-01-01', CURRENT_DATE())) AS date
)
SELECT 
    date,
    CASE
        -- Pre-crisis normal
        WHEN date < '2018-03-01' THEN 'normal_pre_2018'
        -- Trade war escalation
        WHEN date >= '2018-03-01' AND date < '2020-01-01' THEN 'trade_war_2018_2019'
        -- COVID crash
        WHEN date >= '2020-01-01' AND date < '2020-06-01' THEN 'covid_crash_2020'
        -- COVID recovery
        WHEN date >= '2020-06-01' AND date < '2021-01-01' THEN 'covid_recovery_2020'
        -- Inflation surge
        WHEN date >= '2021-01-01' AND date < '2023-01-01' THEN 'inflation_2021_2022'
        -- Trump anticipation
        WHEN date >= '2023-01-01' AND date < '2025-01-20' THEN 'trump_anticipation_2024'
        -- Trump second term
        WHEN date >= '2025-01-20' THEN 'trump_second_term'
        ELSE 'unknown'
    END AS regime,
    CASE
        -- Weights reflect importance for training
        WHEN date < '2018-03-01' THEN 100
        WHEN date >= '2018-03-01' AND date < '2020-01-01' THEN 300
        WHEN date >= '2020-01-01' AND date < '2020-06-01' THEN 200
        WHEN date >= '2020-06-01' AND date < '2021-01-01' THEN 200
        WHEN date >= '2021-01-01' AND date < '2023-01-01' THEN 300
        WHEN date >= '2023-01-01' AND date < '2025-01-20' THEN 400
        WHEN date >= '2025-01-20' THEN 600
        ELSE 100
    END AS weight,
    CASE
        WHEN date < '2018-03-01' THEN 'Pre-trade war normal market conditions'
        WHEN date >= '2018-03-01' AND date < '2020-01-01' THEN 'US-China trade war escalation'
        WHEN date >= '2020-01-01' AND date < '2020-06-01' THEN 'COVID-19 market crash'
        WHEN date >= '2020-06-01' AND date < '2021-01-01' THEN 'Post-COVID recovery'
        WHEN date >= '2021-01-01' AND date < '2023-01-01' THEN 'High inflation regime'
        WHEN date >= '2023-01-01' AND date < '2025-01-20' THEN 'Trump 2.0 anticipation'
        WHEN date >= '2025-01-20' THEN 'Trump second presidential term'
        ELSE 'Unknown regime'
    END AS description
FROM date_series;
```

---

### **PHASE 1: Pull FRED Macro Data (1 hour)** ⏳

**Goal:** Populate `raw_intelligence.fred_economic` with key macro indicators

**Script:** `scripts/fetch_fred_economic_data.py`

**Series to Pull:**
| Series | Name | Frequency |
|--------|------|-----------|
| `VIXCLS` | VIX Close | Daily |
| `DFF` | Fed Funds Rate | Daily |
| `DTWEXBGS` | Dollar Index (DXY) | Daily |
| `DGS10` | 10-Year Treasury | Daily |
| `DGS2` | 2-Year Treasury | Daily |
| `T10Y2Y` | 10Y-2Y Spread | Daily |
| `CPIAUCSL` | CPI | Monthly |
| `UNRATE` | Unemployment | Monthly |

**Execution:**
```bash
cd /Users/zincdigital/CBI-V14
python scripts/fetch_fred_economic_data.py --start-date 2010-01-01 --end-date 2025-11-24
```

**Expected Output:** ~5,000+ rows in `raw_intelligence.fred_economic`

---

### **PHASE 2: Pull Weather Data (1 hour)** ⏳

**Goal:** Populate `raw_intelligence.weather_segmented` with US Midwest weather

**Options:**
1. **NOAA API** - `ingestion/ingest_weather_noaa.py`
2. **Google BigQuery Public Data** - Query directly
3. **OpenMeteo** - `ingestion/ingest_midwest_weather_openmeteo.py`

**Google Public Data Option (Fastest):**
```sql
-- Pull from Google's NOAA GSOD public dataset
INSERT INTO `cbi-v14.raw_intelligence.weather_segmented` (date, region, temp_avg, temp_anomaly, precip, precip_anomaly)
SELECT 
    PARSE_DATE('%Y%m%d', CAST(gsod.year*10000 + gsod.mo*100 + gsod.da AS STRING)) AS date,
    'US_MIDWEST' AS region,
    (gsod.temp - 32) * 5/9 AS temp_avg_celsius,
    -- Calculate anomaly vs 30-year average (simplified)
    (gsod.temp - 50) / 10 AS temp_anomaly_zscore,
    gsod.prcp AS precip_inches,
    (gsod.prcp - 0.1) / 0.5 AS precip_anomaly_zscore
FROM `bigquery-public-data.noaa_gsod.gsod*` gsod
WHERE 
    -- US Midwest stations (IA, IL, IN, MN, NE, OH, WI)
    gsod.stn IN (SELECT usaf FROM `bigquery-public-data.noaa_gsod.stations` 
                 WHERE state IN ('IA', 'IL', 'IN', 'MN', 'NE', 'OH', 'WI'))
    AND gsod.year >= 2010
GROUP BY date, region, temp_avg_celsius, temp_anomaly_zscore, precip_inches, precip_anomaly_zscore
ORDER BY date;
```

**Expected Output:** ~5,000+ rows in `raw_intelligence.weather_segmented`

---

### **PHASE 3: Calculate Basic Features (2 hours)** ⏳

**Goal:** Populate `features.daily_ml_matrix` with baseline features

**Step 3.1: Calculate Technical Indicators**

```sql
-- Create baseline features from Databento data
INSERT INTO `cbi-v14.features.daily_ml_matrix` 
(symbol, data_date, timestamp, market_data, pivots, policy, golden_zone, regime, ingestion_ts)

WITH price_data AS (
    SELECT 
        symbol,
        date AS data_date,
        TIMESTAMP(date) AS timestamp,
        open, high, low, close, volume,
        -- Returns
        SAFE_DIVIDE(close - LAG(close, 1) OVER w, LAG(close, 1) OVER w) AS return_1d,
        SAFE_DIVIDE(close - LAG(close, 5) OVER w, LAG(close, 5) OVER w) AS return_5d,
        SAFE_DIVIDE(close - LAG(close, 21) OVER w, LAG(close, 21) OVER w) AS return_21d,
        -- Moving averages
        AVG(close) OVER (ORDER BY date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS ma_5,
        AVG(close) OVER (ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) AS ma_21,
        AVG(close) OVER (ORDER BY date ROWS BETWEEN 62 PRECEDING AND CURRENT ROW) AS ma_63,
        -- Volatility
        STDDEV_SAMP(SAFE_DIVIDE(close - LAG(close, 1) OVER w, LAG(close, 1) OVER w)) 
            OVER (ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) AS volatility_21d,
        -- RSI components
        AVG(IF(close > LAG(close, 1) OVER w, close - LAG(close, 1) OVER w, 0)) 
            OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_gain_14,
        AVG(IF(close < LAG(close, 1) OVER w, LAG(close, 1) OVER w - close, 0)) 
            OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_loss_14
    FROM `cbi-v14.market_data.databento_futures_ohlcv_1d`
    WHERE symbol = 'ZL'
    WINDOW w AS (PARTITION BY symbol ORDER BY date)
),
with_rsi AS (
    SELECT 
        *,
        100 - (100 / (1 + SAFE_DIVIDE(avg_gain_14, NULLIF(avg_loss_14, 0)))) AS rsi_14
    FROM price_data
),
with_regime AS (
    SELECT 
        p.*,
        r.regime AS regime_name,
        r.weight AS regime_weight
    FROM with_rsi p
    LEFT JOIN `cbi-v14.features.regime_calendar` r ON p.data_date = r.date
)
SELECT 
    symbol,
    data_date,
    timestamp,
    -- Market data STRUCT
    STRUCT(
        close AS price,
        open, high, low, close, volume,
        ma_5, ma_21, ma_63,
        rsi_14,
        volatility_21d,
        return_1d AS momentum_21d
    ) AS market_data,
    -- Pivots STRUCT (placeholder - will be calculated by pivot script)
    STRUCT(
        CAST(NULL AS FLOAT64) AS P,
        CAST(NULL AS FLOAT64) AS R1,
        CAST(NULL AS FLOAT64) AS R2,
        CAST(NULL AS FLOAT64) AS S1,
        CAST(NULL AS FLOAT64) AS S2,
        CAST(NULL AS FLOAT64) AS distance_to_P,
        CAST(NULL AS FLOAT64) AS distance_to_nearest,
        CAST(NULL AS FLOAT64) AS weekly_P_distance,
        CAST(NULL AS BOOL) AS is_above_P
    ) AS pivots,
    -- Policy STRUCT (placeholder)
    STRUCT(
        CAST(NULL AS FLOAT64) AS trump_action_prob,
        CAST(NULL AS FLOAT64) AS trump_score,
        CAST(NULL AS FLOAT64) AS trump_sentiment_7d,
        CAST(NULL AS FLOAT64) AS trump_tariff_intensity,
        FALSE AS is_shock_regime
    ) AS policy,
    -- Golden zone STRUCT (placeholder)
    STRUCT(
        0 AS state,
        CAST(NULL AS FLOAT64) AS swing_high,
        CAST(NULL AS FLOAT64) AS swing_low,
        CAST(NULL AS FLOAT64) AS fib_50,
        CAST(NULL AS FLOAT64) AS fib_618,
        CAST(NULL AS FLOAT64) AS vol_decay_slope,
        FALSE AS qualified_trigger
    ) AS golden_zone,
    -- Regime STRUCT
    STRUCT(
        regime_name AS name,
        regime_weight AS weight,
        CAST(NULL AS FLOAT64) AS vol_percentile,
        CAST(NULL AS FLOAT64) AS k_vol
    ) AS regime,
    CURRENT_TIMESTAMP() AS ingestion_ts
FROM with_regime
WHERE data_date >= '2010-01-01';
```

**Expected Output:** ~3,998 rows in `features.daily_ml_matrix`

---

### **PHASE 4: Join Macro Data (30 min)** ⏳

**Goal:** Add FRED macro indicators to features

```sql
-- Update daily_ml_matrix with FRED data
-- This would be done via Python script or additional SQL
-- joining raw_intelligence.fred_economic to features.daily_ml_matrix
```

---

### **PHASE 5: Populate Training Table (30 min)** ⏳

**Goal:** Create training-ready dataset with targets

```sql
-- Populate ZL 1-month training table
INSERT INTO `cbi-v14.training.zl_training_prod_allhistory_1m`
SELECT 
    f.symbol,
    f.data_date,
    f.market_data.close AS price_t0,
    -- Target: 1-month forward return
    SAFE_DIVIDE(
        LEAD(f.market_data.close, 21) OVER (ORDER BY f.data_date) - f.market_data.close,
        f.market_data.close
    ) * 100 AS target_return_1m,
    -- Direction target
    IF(LEAD(f.market_data.close, 21) OVER (ORDER BY f.data_date) > f.market_data.close, 1, 0) AS target_direction_1m,
    -- Features
    f.market_data.ma_5,
    f.market_data.ma_21,
    f.market_data.ma_63,
    f.market_data.rsi_14,
    f.market_data.volatility_21d,
    -- Regime
    f.regime.name AS regime_name,
    f.regime.weight AS sample_weight,
    -- Split
    CASE
        WHEN f.data_date < '2023-01-01' THEN 'train'
        WHEN f.data_date < '2024-01-01' THEN 'val'
        ELSE 'test'
    END AS split,
    CURRENT_TIMESTAMP() AS processed_at
FROM `cbi-v14.features.daily_ml_matrix` f
WHERE f.symbol = 'ZL'
    AND f.data_date >= '2010-01-01'
    -- Ensure we have forward data for target
    AND f.data_date <= DATE_SUB(CURRENT_DATE(), INTERVAL 21 DAY);
```

---

### **PHASE 6: Export to Mac & Train Baseline (2 hours)** ⏳

**Step 6.1: Export Training Data**
```bash
# Export training data to CSV
bq extract --destination_format=CSV \
    'cbi-v14:training.zl_training_prod_allhistory_1m' \
    gs://cbi-v14-training-data/zl_training_1m.csv

# Or use Python to export directly
python scripts/export_training_data.py --horizon 1m --output ./training_data/
```

**Step 6.2: Train LightGBM Baseline**
```python
# scripts/training/train_lightgbm_baseline.py
import lightgbm as lgb
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

# Load data
df = pd.read_csv('training_data/zl_training_1m.csv')

# Features
feature_cols = ['ma_5', 'ma_21', 'ma_63', 'rsi_14', 'volatility_21d']
X = df[feature_cols]
y = df['target_return_1m']
weights = df['sample_weight']

# Time series split
tscv = TimeSeriesSplit(n_splits=5)

# Train
params = {
    'objective': 'regression',
    'metric': 'mae',
    'num_leaves': 63,
    'learning_rate': 0.02,
    'feature_fraction': 0.9,
    'bagging_fraction': 0.9,
    'bagging_freq': 5,
    'verbose': -1
}

for train_idx, val_idx in tscv.split(X):
    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
    
    train_data = lgb.Dataset(X_train, label=y_train, weight=weights.iloc[train_idx])
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[train_data, val_data],
        callbacks=[lgb.early_stopping(50)]
    )
    
    print(f"Fold MAE: {model.best_score['valid_1']['l1']:.4f}")
```

---

## 📋 TIMELINE SUMMARY

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| 0 | Populate regime_calendar | 30 min | ⏳ Pending |
| 1 | Pull FRED macro data | 1 hour | ⏳ Pending |
| 2 | Pull weather data | 1 hour | ⏳ Pending |
| 3 | Calculate basic features | 2 hours | ⏳ Pending |
| 4 | Join macro data | 30 min | ⏳ Pending |
| 5 | Populate training table | 30 min | ⏳ Pending |
| 6 | Export & train baseline | 2 hours | ⏳ Pending |
| **TOTAL** | | **7.5 hours** | |

---

## ✅ SUCCESS CRITERIA

### Baseline Model Requirements:
- [ ] `features.regime_calendar` has 5,000+ rows (2010-2025)
- [ ] `features.daily_ml_matrix` has 3,998 rows (ZL daily)
- [ ] `training.zl_training_prod_allhistory_1m` has 3,900+ rows
- [ ] LightGBM baseline trained with MAE < 5%
- [ ] Time series CV shows stable performance across folds

### Data Quality Checks:
- [ ] No NULL values in required features
- [ ] Date alignment correct (no gaps)
- [ ] Regime tags present for all rows
- [ ] Target variable calculated correctly

---

## 🔴 BLOCKERS & RISKS

| Risk | Mitigation |
|------|------------|
| FRED API rate limits | Use batch requests, cache responses |
| Weather data gaps | Use forward-fill for missing dates |
| Feature calculation errors | Test on 100 rows first |
| Model overfitting | Use time series CV, not random split |

---

## 📝 NOTES

### NO YAHOO DATA
- All price data comes from Databento ONLY
- Date range: 2010-06-06 to present (15 years)
- All other data must align to Databento dates

### Databento Live API
- Use for real-time data streaming in production
- Warehouse data (6,034 rows) is historical batch
- API key stored securely (not in code)

### Feature Calculation Scripts
All scripts are in `Quant Check Plan/scripts/`:
- `features/cloud_function_pivot_calculator.py`
- `features/cloud_function_fibonacci_calculator.py`
- `features/build_forex_features.py`
- `ingestion/ingest_features_hybrid.py`

---

**Status:** 🟢 READY FOR EXECUTION
**Next Step:** Execute Phase 0 (regime calendar)


