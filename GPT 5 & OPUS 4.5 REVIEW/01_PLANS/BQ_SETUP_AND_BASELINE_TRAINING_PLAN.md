# 🚀 BQ Setup & First Baseline Training Plan
**Date:** November 24, 2025  
**Status:** 🟢 READY FOR EXECUTION  
**Machine:** M4 Pro Mac (24GB RAM)

---

## 📊 CURRENT STATE

### BigQuery Data Available:
| Table | Rows | Symbols | Date Range |
|-------|------|---------|------------|
| `market_data.databento_futures_ohlcv_1d` | **6,034** | ZL (3,998), MES (2,036) | 2010-2025 |

### Scripts Available (in `Quant Check Plan/scripts/`):
| Folder | Scripts | Purpose |
|--------|---------|---------|
| `features/` | 10 scripts | Pivot, Fib, FX, MES, RIN calculations |
| `predictions/` | 3 scripts | Trump, ZL impact, ES predictions |
| `ingestion/` | 2 scripts | Feature consolidation, Databento loader |

---

## 🎯 EXECUTION PLAN

### Phase 1: Populate Reference Tables (30 min)
**Goal:** Set up regime calendar and weights

```sql
-- 1.1 Populate regime_calendar
INSERT INTO `cbi-v14.training.regime_calendar` (date, regime, weight, vol_percentile, k_vol)
WITH dates AS (
  SELECT date
  FROM UNNEST(GENERATE_DATE_ARRAY('2010-01-01', '2029-01-20')) AS date
)
SELECT 
  date,
  CASE
    -- Pre-Trump era
    WHEN date < '2017-01-20' THEN 'pre_trump_baseline'
    -- Trade war era
    WHEN date BETWEEN '2018-03-01' AND '2020-01-14' THEN 'tradewar_escalation'
    -- COVID
    WHEN date BETWEEN '2020-01-15' AND '2021-06-30' THEN 'covid_disruption'
    -- Inflation
    WHEN date BETWEEN '2021-07-01' AND '2023-10-31' THEN 'inflation_2021_2023'
    -- Trump anticipation
    WHEN date BETWEEN '2023-11-01' AND '2025-01-19' THEN 'trump_anticipation_2024'
    -- Trump second term
    WHEN date >= '2025-01-20' THEN 'trump_second_term'
    ELSE 'baseline'
  END AS regime,
  CASE
    WHEN date BETWEEN '2023-11-01' AND '2025-01-19' THEN 400
    WHEN date >= '2025-01-20' THEN 600
    WHEN date BETWEEN '2018-03-01' AND '2020-01-14' THEN 500
    WHEN date BETWEEN '2020-01-15' AND '2021-06-30' THEN 300
    ELSE 100
  END AS weight,
  0.5 AS vol_percentile,  -- Will be calculated later
  1.0 AS k_vol
FROM dates;

-- 1.2 Populate regime_weights
INSERT INTO `cbi-v14.training.regime_weights` (regime, weight, description)
VALUES
  ('pre_trump_baseline', 100, 'Pre-Trump baseline period'),
  ('tradewar_escalation', 500, 'US-China trade war escalation'),
  ('covid_disruption', 300, 'COVID market disruption'),
  ('inflation_2021_2023', 200, 'Post-COVID inflation period'),
  ('trump_anticipation_2024', 400, 'Trump 2.0 anticipation'),
  ('trump_second_term', 600, 'Trump second presidential term');
```

**Verification:**
```sql
SELECT regime, COUNT(*) as days, MIN(date) as start, MAX(date) as end
FROM `cbi-v14.training.regime_calendar`
GROUP BY regime
ORDER BY MIN(date);
```

---

### Phase 2: Run Pivot Calculator (15 min)
**Goal:** Calculate pivot points for all ZL and MES data

**Script:** `scripts/features/cloud_function_pivot_calculator.py`

**Run locally:**
```bash
cd "/Users/zincdigital/CBI-V14/Quant Check Plan"
python scripts/features/cloud_function_pivot_calculator.py
```

**Expected Output:**
- ~6,000 rows in `features.pivot_math_daily`
- Columns: P, R1-R4, S1-S4, M1-M8, distances, confluence, signals

**Verification:**
```sql
SELECT symbol, COUNT(*) as rows, MIN(date) as min_date, MAX(date) as max_date
FROM `cbi-v14.features.pivot_math_daily`
GROUP BY symbol;
```

---

### Phase 3: Run Feature Consolidation (30 min)
**Goal:** Build `features.daily_ml_matrix` with all features

**Script:** `scripts/ingestion/ingest_features_hybrid.py`

**Test run (100 rows):**
```bash
cd "/Users/zincdigital/CBI-V14/Quant Check Plan"
python scripts/ingestion/ingest_features_hybrid.py --test-batch 100
```

**Full run:**
```bash
python scripts/ingestion/ingest_features_hybrid.py --full
```

**Expected Output:**
- ~6,000 rows in `features.daily_ml_matrix`
- Nested STRUCTs: market_data, pivots, policy, golden_zone, regime

**Verification:**
```sql
SELECT 
  symbol,
  COUNT(*) as rows,
  MIN(data_date) as min_date,
  MAX(data_date) as max_date,
  COUNTIF(regime.name IS NOT NULL) as rows_with_regime
FROM `cbi-v14.features.daily_ml_matrix`
GROUP BY symbol;
```

---

### Phase 4: Populate Training Tables (20 min)
**Goal:** Move features to horizon-specific training tables

**SQL for ZL 1-week horizon:**
```sql
INSERT INTO `cbi-v14.training.zl_training_prod_allhistory_1w`
SELECT
  symbol,
  data_date,
  market_data.close AS close,
  market_data.volume AS volume,
  market_data.open AS open,
  market_data.high AS high,
  market_data.low AS low,
  
  -- Pivots
  pivots.P,
  pivots.R1,
  pivots.R2,
  pivots.S1,
  pivots.S2,
  pivots.distance_to_P,
  pivots.distance_to_nearest,
  pivots.weekly_P_distance,
  pivots.is_above_P,
  
  -- Regime
  regime.name AS regime_name,
  regime.weight AS regime_weight,
  
  -- Target: 5-day forward return
  SAFE_DIVIDE(
    LEAD(market_data.close, 5) OVER (ORDER BY data_date) - market_data.close,
    market_data.close
  ) * 100 AS target_1w,
  
  -- Split
  CASE
    WHEN data_date < '2023-01-01' THEN 'train'
    WHEN data_date < '2024-01-01' THEN 'val'
    ELSE 'test'
  END AS split,
  
  CURRENT_TIMESTAMP() AS created_at
FROM `cbi-v14.features.daily_ml_matrix`
WHERE symbol = 'ZL'
  AND LEAD(market_data.close, 5) OVER (ORDER BY data_date) IS NOT NULL;
```

**Repeat for other horizons:**
- `zl_training_prod_allhistory_1m` (21-day target)
- `zl_training_prod_allhistory_3m` (63-day target)
- `zl_training_prod_allhistory_6m` (126-day target)
- `zl_training_prod_allhistory_12m` (252-day target)

**Verification:**
```sql
SELECT 
  'zl_1w' as table_name, COUNT(*) as rows, 
  COUNTIF(split='train') as train, 
  COUNTIF(split='val') as val, 
  COUNTIF(split='test') as test
FROM `cbi-v14.training.zl_training_prod_allhistory_1w`
UNION ALL
SELECT 'zl_1m', COUNT(*), COUNTIF(split='train'), COUNTIF(split='val'), COUNTIF(split='test')
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;
```

---

### Phase 5: Export Training Data to Mac (10 min)
**Goal:** Export training data for local model training

**Export to CSV/Parquet:**
```bash
bq extract --destination_format=PARQUET \
  'cbi-v14:training.zl_training_prod_allhistory_1w' \
  'gs://cbi-v14-training-data/zl_1w_*.parquet'

# Download to Mac
gsutil cp 'gs://cbi-v14-training-data/zl_1w_*.parquet' \
  "/Users/zincdigital/CBI-V14/Quant Check Plan/training_data/"
```

**Or direct query to DataFrame:**
```python
from google.cloud import bigquery
import pandas as pd

client = bigquery.Client(project='cbi-v14')
query = """
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_1w`
WHERE split IN ('train', 'val')
"""
df = client.query(query).to_dataframe()
df.to_parquet('training_data/zl_1w_training.parquet')
```

---

### Phase 6: Train First Baseline Model (2-4 hours)
**Goal:** Train LightGBM baseline on ZL 1-week horizon

**Script:** `train_baseline_lightgbm.py`

```python
#!/usr/bin/env python3
"""
First Baseline Model: LightGBM on ZL 1-week horizon
Machine: M4 Pro Mac (24GB RAM, CPU training)
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, r2_score
import json
from pathlib import Path

# Load training data
df = pd.read_parquet('training_data/zl_1w_training.parquet')

# Define features (exclude target and metadata)
exclude_cols = ['target_1w', 'split', 'created_at', 'symbol', 'data_date', 'regime_name']
feature_cols = [c for c in df.columns if c not in exclude_cols]

# Split data
train_df = df[df['split'] == 'train']
val_df = df[df['split'] == 'val']
test_df = df[df['split'] == 'test']

X_train = train_df[feature_cols]
y_train = train_df['target_1w']
X_val = val_df[feature_cols]
y_val = val_df['target_1w']

# Sample weights from regime
sample_weights = train_df['regime_weight'].values

# LightGBM parameters (quality-focused, not speed-focused)
params = {
    'objective': 'regression',
    'metric': 'mae',
    'boosting_type': 'gbdt',
    'num_leaves': 127,
    'learning_rate': 0.01,
    'feature_fraction': 0.9,
    'bagging_fraction': 0.9,
    'bagging_freq': 5,
    'min_data_in_leaf': 20,
    'max_depth': 15,
    'lambda_l1': 0.1,
    'lambda_l2': 0.1,
    'verbose': -1,
    'seed': 42
}

# Create datasets
train_data = lgb.Dataset(X_train, label=y_train, weight=sample_weights)
val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

# Train with early stopping
model = lgb.train(
    params,
    train_data,
    num_boost_round=3000,
    valid_sets=[train_data, val_data],
    valid_names=['train', 'val'],
    callbacks=[
        lgb.early_stopping(stopping_rounds=100),
        lgb.log_evaluation(period=100)
    ]
)

# Evaluate
y_pred_val = model.predict(X_val)
y_pred_test = model.predict(test_df[feature_cols])

val_mae = mean_absolute_error(y_val, y_pred_val)
val_r2 = r2_score(y_val, y_pred_val)
test_mae = mean_absolute_error(test_df['target_1w'], y_pred_test)
test_r2 = r2_score(test_df['target_1w'], y_pred_test)

print(f"\n=== BASELINE RESULTS ===")
print(f"Validation MAE: {val_mae:.4f}%")
print(f"Validation R²:  {val_r2:.4f}")
print(f"Test MAE:       {test_mae:.4f}%")
print(f"Test R²:        {test_r2:.4f}")

# Feature importance
importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importance(importance_type='gain')
}).sort_values('importance', ascending=False)

print(f"\n=== TOP 20 FEATURES ===")
print(importance.head(20))

# Save model
model.save_model('models/zl_1w_baseline_lgb.txt')

# Save results
results = {
    'model': 'LightGBM',
    'horizon': '1w',
    'symbol': 'ZL',
    'val_mae': float(val_mae),
    'val_r2': float(val_r2),
    'test_mae': float(test_mae),
    'test_r2': float(test_r2),
    'num_features': len(feature_cols),
    'train_rows': len(train_df),
    'val_rows': len(val_df),
    'test_rows': len(test_df),
    'best_iteration': model.best_iteration,
    'top_features': importance.head(10).to_dict('records')
}

with open('models/zl_1w_baseline_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Model saved to models/zl_1w_baseline_lgb.txt")
print(f"✅ Results saved to models/zl_1w_baseline_results.json")
```

**Expected Results:**
- MAE: 2-4% (1-week forward return prediction)
- R²: 0.3-0.6 (baseline, will improve with more features)
- Training time: 30-60 minutes on M4 Pro

---

## 📋 EXECUTION CHECKLIST

### Day 1: BQ Setup (2-3 hours)
- [ ] **Phase 1:** Populate regime_calendar (30 min)
- [ ] **Phase 2:** Run pivot calculator (15 min)
- [ ] **Phase 3:** Run feature consolidation (30 min)
- [ ] **Phase 4:** Populate training tables (20 min)
- [ ] **Verify:** All tables have expected row counts

### Day 2: First Baseline (4-6 hours)
- [ ] **Phase 5:** Export training data (10 min)
- [ ] **Phase 6:** Train LightGBM baseline (2-4 hours)
- [ ] **Evaluate:** Review MAE, R², feature importance
- [ ] **Document:** Save results and model

### Day 3: Iterate (ongoing)
- [ ] Add more features (FX, weather, CFTC)
- [ ] Train other horizons (1m, 3m, 6m, 12m)
- [ ] Try TFT model (PyTorch MPS)
- [ ] Upload predictions to BQ

---

## 🎯 SUCCESS CRITERIA

### Phase 1-4 (BQ Setup):
- [ ] `training.regime_calendar` has 7,000+ rows (2010-2029)
- [ ] `features.pivot_math_daily` has ~6,000 rows
- [ ] `features.daily_ml_matrix` has ~6,000 rows
- [ ] `training.zl_training_prod_allhistory_1w` has ~3,900 rows

### Phase 5-6 (Baseline):
- [ ] LightGBM model trained successfully
- [ ] Validation MAE < 5% (1-week return)
- [ ] Test R² > 0.2 (meaningful signal)
- [ ] Top features include pivots and regime

---

## 🚨 TROUBLESHOOTING

### If pivot calculator fails:
1. Check BQ credentials: `gcloud auth application-default login`
2. Verify source table exists: `bq show market_data.databento_futures_ohlcv_1d`
3. Check for missing columns in source data

### If feature consolidation fails:
1. Verify regime_calendar is populated
2. Check pivot_math_daily has data
3. Run with `--debug` flag for detailed logs

### If training fails:
1. Check for NaN values in features
2. Reduce batch size if memory issues
3. Try fewer features initially

---

## 📁 FILE STRUCTURE

```
Quant Check Plan/
├── scripts/
│   ├── features/
│   │   ├── cloud_function_pivot_calculator.py
│   │   ├── cloud_function_fibonacci_calculator.py
│   │   ├── build_forex_features.py
│   │   ├── build_mes_all_features.py
│   │   ├── calculate_rin_proxies.py
│   │   └── ...
│   ├── predictions/
│   │   ├── trump_action_predictor.py
│   │   ├── zl_impact_predictor.py
│   │   └── es_futures_predictor.py
│   ├── ingestion/
│   │   ├── ingest_features_hybrid.py
│   │   └── load_databento_raw.py
│   ├── LOAD_ALL_REAL_HISTORICAL_DATA.sql
│   └── PULL_ALL_REAL_DATA.sql
├── training_data/
│   └── (exported parquet files)
├── models/
│   ├── zl_1w_baseline_lgb.txt
│   └── zl_1w_baseline_results.json
├── BQ_SETUP_AND_BASELINE_TRAINING_PLAN.md (this file)
├── DATA_FLOW_MAP_2025-11-21.md
├── CRITICAL_DATA_AUDIT_2025-11-21.md
├── BQ_AUDIT_2025-11-21.md
└── QUAD_CHECK_PLAN_2025-11-21.md
```

---

**Status:** 🟢 READY FOR EXECUTION
**Next Step:** Run Phase 1 (populate regime tables)


