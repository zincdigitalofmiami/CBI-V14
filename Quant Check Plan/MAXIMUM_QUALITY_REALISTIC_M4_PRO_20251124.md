# Maximum Quality Training Strategy - M4 Pro Realistic
**Date**: November 24, 2025  
**Machine**: Mac mini M4 Pro, 24GB unified RAM  
**Principle**: Maximum quality within hardware constraints. No compromises on methodology, realistic on implementation.

---

## Core Principles (Revised)

### Quality First, But Bounded
- ✅ **Maximum quality methodology** (no shortcuts)
- ✅ **Respect hardware limits** (24GB RAM, MPS not CUDA)
- ✅ **No data leakage** (strict walk-forward splits)
- ✅ **Use all features** (but batch/stream for memory)
- ✅ **Smart hyperparameter search** (not brute-force)

### Hardware Reality
- **MPS (Metal Performance Shaders)**: Use for PyTorch (works even if TensorFlow Metal doesn't)
- **CPU**: Use for LightGBM/XGBoost
- **24GB unified RAM**: Shared between CPU/GPU - manage carefully
- **14-core CPU**: Fast, but not data-center GPU

---

## Targets & Data Strategy

### Targets: Forward Returns

```python
# Multi-horizon forward returns
TARGETS = {
    '1d': 1,   # 1 day ahead
    '5d': 5,   # 5 days ahead
    '20d': 20, # ~1 month
    '63d': 63  # ~3 months
}

# Back-adjusted front-month ZL continuous
# Plus near months (F/H/K/N/U/Z) if modeling curve jointly
```

**Calculation**:
```sql
-- In training table
SELECT
  date,
  price AS price_t0,
  LEAD(price, 1) OVER (ORDER BY date) AS price_1d_fwd,
  LEAD(price, 5) OVER (ORDER BY date) AS price_5d_fwd,
  LEAD(price, 20) OVER (ORDER BY date) AS price_20d_fwd,
  LEAD(price, 63) OVER (ORDER BY date) AS price_63d_fwd,
  
  -- Log returns (targets)
  LN(LEAD(price, 1) OVER (ORDER BY date) / NULLIF(price, 0)) AS return_1d_fwd,
  LN(LEAD(price, 5) OVER (ORDER BY date) / NULLIF(price, 0)) AS return_5d_fwd,
  LN(LEAD(price, 20) OVER (ORDER BY date) / NULLIF(price, 0)) AS return_20d_fwd,
  LN(LEAD(price, 63) OVER (ORDER BY date) / NULLIF(price, 0)) AS return_63d_fwd
FROM market_daily
WHERE symbol = 'ZL'
```

### Data: All History, Strict Holdout

```python
# Use ALL available history
TRAIN_START = '1900-01-01'  # All 125 years

# Strict holdout (never touched during tuning)
HOLDOUT_START = '2023-07-01'  # Last 18-24 months
TEST_START = '2024-01-01'     # Final test set

# Validation folds: 2020-01-01 to 2023-06-30
# Training: 1900-01-01 to 2019-12-31
```

**Principle**: More data = better models, but validate properly.

---

## Backtests & Splits: Strict Walk-Forward

### Time-Series Cross-Validation

```python
from sklearn.model_selection import TimeSeriesSplit

# Rolling walk-forward validation
tscv = TimeSeriesSplit(n_splits=10)

for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
    
    # Train on past, validate on future
    # No look-ahead bias
    
    model.fit(X_train, y_train)
    score = model.evaluate(X_val, y_val)
    
    print(f"Fold {fold}: Train {train_idx[0]}-{train_idx[-1]}, "
          f"Val {val_idx[0]}-{val_idx[-1]}, Score: {score:.4f}")
```

### Final Test Set

```python
# Last 18-24 months: NEVER touched during tuning
X_test = df[df['date'] >= '2023-07-01']
y_test = targets[targets['date'] >= '2023-07-01']

# Only evaluate here AFTER all hyperparameter tuning
final_score = best_model.evaluate(X_test, y_test)
```

### No Leakage Rules

```python
# ❌ WRONG: Feature known after label date
feature_value = get_feature(date)  # If this uses future data

# ✅ CORRECT: Report-day flags must be "known in advance"
is_wasde_day = date in WASDE_SCHEDULE  # Known calendar

# ✅ CORRECT: Post-release NLP goes to T+1
news_sentiment_today = process_news(date - 1)  # Yesterday's news affects today
```

---

## PyTorch TFT on MPS: Realistic Configuration

### MPS Setup (Metal Performance Shaders)

**Key Insight**: PyTorch MPS works even if TensorFlow Metal doesn't!

```python
import torch
from pytorch_lightning import Trainer

# Check MPS availability
if torch.backends.mps.is_available():
    device = "mps"
    print("✅ MPS (Metal) available!")
else:
    device = "cpu"
    print("⚠️  MPS not available, using CPU")

# MPS-specific considerations
# - Monitor for out-of-memory
# - Batch size: start small, scale up
# - Precision: float16 generally fine, fallback to float32 if unstable
```

### TFT Configuration: Large But Realistic

```python
from pytorch_forecasting import TemporalFusionTransformer

tft = TemporalFusionTransformer.from_dataset(
    training,
    
    # Model size: large but not absurd
    hidden_size=128,              # 64-128 range (not 256)
    attention_head_size=8,        # 4-8 range (not 16)
    lstm_layers=2,                # 1-2 layers (not 3+)
    hidden_continuous_size=64,    # 32-64 range (not 128)
    dropout=0.15,                 # 0.1-0.2 range
    
    # Sequence lengths: respect memory
    max_encoder_length=180,       # 120-180 days lookback (not 252+)
    max_prediction_length=63,     # 20-63 days ahead (align with horizons)
    
    # Training
    learning_rate=3e-4,           # Standard
    reduce_on_plateau_patience=5,
    output_size=len(quantiles),   # P10/P50/P90
)

trainer = Trainer(
    accelerator="mps",            # ✅ Use MPS!
    devices=1,
    
    # Training duration
    max_epochs=200,               # 100-200 with early stopping
    early_stopping_patience=15,    # 10-20 patience
    min_delta=1e-4,                # ~1e-4 minimum improvement
    
    # Memory management
    gradient_clip_val=0.3,         # 0.1-0.5 range
    precision=16,                  # Mixed precision (float16)
    # Fallback to precision=32 if stability issues
    
    # Checkpointing
    enable_checkpointing=True,
    callbacks=[
        ModelCheckpoint(monitor='val_loss', save_top_k=3),
        EarlyStopping(monitor='val_loss', patience=15, min_delta=1e-4),
        LearningRateMonitor(),
    ],
    
    # Logging
    logger=TensorBoardLogger("logs/"),
    log_every_n_steps=10,
)
```

### Batch Size Strategy

```python
# Start small, scale if memory allows
BATCH_SIZES = {
    'small': 32,   # If OOM errors
    'medium': 64,  # Default start
    'large': 128,  # If memory allows
    'xlarge': 256  # Unlikely on 24GB
}

# Monitor memory usage
import psutil
import torch

def check_memory():
    ram_used = psutil.virtual_memory().used / 1e9  # GB
    if torch.backends.mps.is_available():
        # MPS memory is shared with system RAM
        print(f"RAM used: {ram_used:.1f} GB / 24 GB")
    
    if ram_used > 20:  # Close to limit
        print("⚠️  Memory warning - reduce batch size")

# Start with 64, increase if stable
train_loader = training.to_dataloader(
    train=True,
    batch_size=64,  # Start here
    num_workers=2,   # 2-4 workers (not too many)
)
```

### Hyperparameter Search: Smart, Not Brute-Force

```python
import optuna
from optuna.integration import PyTorchLightningPruningCallback

def objective(trial):
    # Tuned ranges (not exhaustive)
    hidden_size = trial.suggest_int('hidden_size', 64, 128, step=16)
    attention_heads = trial.suggest_int('attention_heads', 4, 8, step=2)
    lstm_layers = trial.suggest_int('lstm_layers', 1, 2)
    dropout = trial.suggest_float('dropout', 0.1, 0.2, step=0.05)
    learning_rate = trial.suggest_loguniform('learning_rate', 1e-4, 1e-3)
    batch_size = trial.suggest_categorical('batch_size', [32, 64, 128])
    
    # Create model with trial params
    tft = TemporalFusionTransformer.from_dataset(
        training,
        hidden_size=hidden_size,
        attention_head_size=attention_heads,
        lstm_layers=lstm_layers,
        dropout=dropout,
        learning_rate=learning_rate
    )
    
    trainer = Trainer(
        accelerator="mps",
        max_epochs=100,  # Fewer epochs per trial
        callbacks=[PyTorchLightningPruningCallback(trial, monitor='val_loss')]
    )
    
    trainer.fit(tft, train_loader, val_loader)
    
    return trainer.callback_metrics['val_loss'].item()

# Smart search: 20-40 trials (not 100+)
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=30)  # 20-40 range

best_params = study.best_params
```

### Multiple Seeds: Practical

```python
# 3-5 runs averaged (not 10+)
SEEDS = [42, 123, 456, 789, 999][:5]  # 5 seeds max

predictions = []

for seed in SEEDS:
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    model = train_tft_with_params(best_params, seed=seed)
    pred = model.predict(test_loader)
    predictions.append(pred)

# Average predictions (reduce variance)
final_prediction = np.mean(predictions, axis=0)
prediction_std = np.std(predictions, axis=0)  # Uncertainty estimate
```

---

## LightGBM: Realistic CPU Configuration

### Quantile Models: Strong But Sane

```python
import lightgbm as lgb

# Realistic parameters (not maximum)
params = {
    'objective': 'quantile',
    'alpha': quantile,  # 0.1, 0.5, 0.9 for P10/P50/P90
    
    'boosting_type': 'gbdt',
    'num_leaves': 127,        # 63-127 range (not 255)
    'learning_rate': 0.02,    # 0.01-0.03 range (not 0.05+)
    
    # Feature/row sampling
    'feature_fraction': 0.9,  # 0.8-1.0 (use most features)
    'bagging_fraction': 0.9,  # 0.8-1.0 (use most rows)
    'bagging_freq': 3,        # 1-5 (don't kill generalization)
    
    # Tree structure
    'min_data_in_leaf': 30,   # 20-50 range
    'max_depth': 12,          # 10-15 range (not 20+)
    
    # Regularization (small > 0 to avoid overfit)
    'lambda_l1': 0.1,         # Small L1
    'lambda_l2': 0.1,         # Small L2
    
    # Performance
    'num_threads': 14,        # Use all CPU cores
    'verbose': -1
}

# Train with many rounds, early stopping
model = lgb.train(
    params,
    train_data,
    num_boost_round=2000,      # 1000-3000 range
    valid_sets=[train_data, val_data],
    callbacks=[
        lgb.early_stopping(stopping_rounds=75),  # 50-100 patience
        lgb.log_evaluation(period=100)
    ]
)
```

### Train Separate Models Per Quantile

```python
# Train separate models (better than single multi-output)
quantile_models = {}

for quantile, name in [(0.1, 'p10'), (0.5, 'p50'), (0.9, 'p90')]:
    params['alpha'] = quantile
    
    model = lgb.train(params, train_data, ...)
    quantile_models[name] = model

# Predict quantiles
predictions = {
    name: model.predict(X_test)
    for name, model in quantile_models.items()
}
```

### Hyperparameter Search: LightGBM

```python
def lightgbm_objective(trial):
    params = {
        'num_leaves': trial.suggest_int('num_leaves', 63, 127, step=16),
        'max_depth': trial.suggest_int('max_depth', 10, 15),
        'learning_rate': trial.suggest_loguniform('learning_rate', 0.01, 0.03),
        'feature_fraction': trial.suggest_float('feature_fraction', 0.8, 1.0),
        'bagging_fraction': trial.suggest_float('bagging_fraction', 0.8, 1.0),
        'lambda_l1': trial.suggest_loguniform('lambda_l1', 0.01, 1.0),
        'lambda_l2': trial.suggest_loguniform('lambda_l2', 0.01, 1.0),
    }
    
    model = lgb.train(params, train_data, num_boost_round=1000, ...)
    return evaluate_model(model, val_data)

# 15-30 trials (not 100+)
study = optuna.create_study(direction='minimize')
study.optimize(lightgbm_objective, n_trials=25)
```

---

## Deep NN Ensemble: Trimmed to Fit

### Realistic Architecture

```python
class DeepForecastingNet(nn.Module):
    def __init__(self, input_size, hidden_sizes=[512, 256, 128, 64], dropout=0.15):
        super().__init__()
        layers = []
        prev_size = input_size
        
        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.BatchNorm1d(hidden_size),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_size = hidden_size
        
        # Multiple output heads for quantiles
        self.base = nn.Sequential(*layers)
        self.heads = nn.ModuleList([
            nn.Linear(hidden_sizes[-1], 1) for _ in range(len(quantiles))
        ])
    
    def forward(self, x):
        features = self.base(x)
        return torch.stack([head(features) for head in self.heads], dim=-1)

# Realistic sizes (not absurd)
model = DeepForecastingNet(
    input_size=150,  # Top features (or all if memory allows)
    hidden_sizes=[512, 256, 128, 64],  # Not [1024, 1024, 512, ...]
    dropout=0.15
)

# Optimizer
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-3,           # 1e-3 to 1e-4 range
    weight_decay=1e-4,  # 1e-4 to 1e-3 range
    betas=(0.9, 0.999)
)

# Scheduler
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
    optimizer, T_max=150, eta_min=1e-6
)

# Training
trainer = Trainer(
    accelerator="mps",
    max_epochs=150,     # 50-150 range
    early_stopping_patience=10,
    precision=16,       # Mixed precision
)
```

### Feature Selection (If Needed)

```python
# If 9k features don't fit, use SHAP/LightGBM importance
if input_size > 1000:
    # Train LightGBM first to get feature importance
    lgb_model = lgb.train(...)
    importance = lgb_model.feature_importance(importance_type='gain')
    
    # Select top N features
    top_features = np.argsort(importance)[-500:]  # Top 500
    X_train_selected = X_train[:, top_features]
    X_val_selected = X_val[:, top_features]
    
    # Train Deep NN on selected features
    model = DeepForecastingNet(input_size=500, ...)
```

---

## Data Handling: Memory-Aware

### Streaming DataLoader

```python
from torch.utils.data import DataLoader, Dataset

class TimeSeriesDataset(Dataset):
    def __init__(self, data_path, chunk_size=10000):
        # Don't load all data at once
        self.data_path = data_path
        self.chunk_size = chunk_size
        self.total_rows = get_row_count(data_path)
    
    def __len__(self):
        return self.total_rows
    
    def __getitem__(self, idx):
        # Load chunk on-demand
        chunk_idx = idx // self.chunk_size
        chunk = load_chunk(self.data_path, chunk_idx)
        return chunk[idx % self.chunk_size]

# Stream data, don't load all at once
train_dataset = TimeSeriesDataset('data/train.parquet', chunk_size=10000)
train_loader = DataLoader(
    train_dataset,
    batch_size=64,
    num_workers=2,  # 2-4 workers (not too many)
    pin_memory=False,  # MPS doesn't need pin_memory
)
```

### Float Precision

```python
# Use float32 (not float64) to save memory
df = pd.read_parquet('data/training.parquet')

# Downcast floats
for col in df.select_dtypes(include=['float64']):
    df[col] = pd.to_numeric(df[col], downcast='float')

# Convert to float32 for PyTorch
X_tensor = torch.tensor(X.values, dtype=torch.float32)
```

### Feature Selection After Initial Fit

```python
# Strategy: Train with all features first, then select
# 1. Initial full fit
model_full = train_model(X_all_features, y)

# 2. Get feature importance
importance = get_feature_importance(model_full)  # SHAP or built-in

# 3. Select top features
top_features = importance.nlargest(500).index  # Top 500

# 4. Retrain on selected features
model_selected = train_model(X_all_features[top_features], y)
```

---

## Ensembling: Best Few Models

### Practical Ensemble

```python
# Train multiple model types
models = {
    'tft': train_tft(...),
    'lightgbm_p10': train_lightgbm(quantile=0.1),
    'lightgbm_p50': train_lightgbm(quantile=0.5),
    'lightgbm_p90': train_lightgbm(quantile=0.9),
    'deep_nn': train_deep_nn(...),
}

# Evaluate all
results = {}
for name, model in models.items():
    pred = model.predict(X_val)
    results[name] = {
        'predictions': pred,
        'mae': mean_absolute_error(y_val, pred),
        'rmse': root_mean_squared_error(y_val, pred),
    }

# Select best 3-4 models
top_models = sorted(results, key=lambda k: results[k]['mae'])[:4]

# Learn ensemble weights on validation set
from sklearn.linear_model import LinearRegression

X_ensemble = np.column_stack([
    results[name]['predictions'] for name in top_models
])

ensemble_weights = LinearRegression().fit(X_ensemble, y_val).coef_
ensemble_weights = ensemble_weights / ensemble_weights.sum()  # Normalize

# Final ensemble prediction
final_pred = sum(
    results[name]['predictions'] * weight
    for name, weight in zip(top_models, ensemble_weights)
)
```

**Principle**: Ensemble best few, not everything. Learn weights properly.

---

## Evaluation: Comprehensive Metrics

### Quantile Metrics

```python
from scipy.stats import norm

def quantile_loss(y_true, y_pred, quantile):
    """Pinball loss"""
    error = y_true - y_pred
    return np.maximum(quantile * error, (quantile - 1) * error).mean()

def crps(y_true, y_pred_p10, y_pred_p50, y_pred_p90):
    """Continuous Ranked Probability Score"""
    # Approximate CDF from quantiles
    # Calculate CRPS
    pass

def coverage(y_true, y_pred_p10, y_pred_p90):
    """Interval coverage"""
    return ((y_true >= y_pred_p10) & (y_true <= y_pred_p90)).mean()

def sharpness(y_pred_p10, y_pred_p90):
    """Prediction interval width"""
    return (y_pred_p90 - y_pred_p10).mean()

# Comprehensive evaluation
metrics = {
    'mae': mean_absolute_error(y_true, y_pred_p50),
    'rmse': root_mean_squared_error(y_true, y_pred_p50),
    'mape': mean_absolute_percentage_error(y_true, y_pred_p50),
    'pinball_p10': quantile_loss(y_true, y_pred_p10, 0.1),
    'pinball_p50': quantile_loss(y_true, y_pred_p50, 0.5),
    'pinball_p90': quantile_loss(y_true, y_pred_p90, 0.9),
    'crps': crps(y_true, y_pred_p10, y_pred_p50, y_pred_p90),
    'coverage_80': coverage(y_true, y_pred_p10, y_pred_p90),
    'sharpness': sharpness(y_pred_p10, y_pred_p90),
    'directional_accuracy': (np.sign(y_true) == np.sign(y_pred_p50)).mean(),
}
```

### Drift Monitoring

```python
def monitor_feature_drift(X_train, X_test, threshold=0.1):
    """Monitor feature distribution shifts"""
    drift_scores = {}
    
    for feature in X_train.columns:
        train_dist = X_train[feature].describe()
        test_dist = X_test[feature].describe()
        
        # Kolmogorov-Smirnov test
        from scipy.stats import ks_2samp
        statistic, p_value = ks_2samp(X_train[feature], X_test[feature])
        
        drift_scores[feature] = {
            'ks_statistic': statistic,
            'p_value': p_value,
            'drifted': statistic > threshold
        }
    
    drifted_features = [f for f, s in drift_scores.items() if s['drifted']]
    
    if len(drifted_features) > 10:  # Threshold
        print(f"⚠️  {len(drifted_features)} features drifted - consider retraining")
    
    return drift_scores
```

---

## Signal Translation: Risk Management

### Quantiles to Trading Signals

```python
def quantiles_to_signal(y_pred_p10, y_pred_p50, y_pred_p90, threshold=0.02):
    """
    Convert quantile forecasts to trading signals
    
    Long if: P50 > 0 AND P90 > threshold
    Short if: P50 < 0 AND P10 < -threshold
    Neutral otherwise
    """
    signals = []
    positions = []
    
    for p10, p50, p90 in zip(y_pred_p10, y_pred_p50, y_pred_p90):
        if p50 > 0 and p90 > threshold:
            signal = 'LONG'
            # Size by uncertainty (narrow bands = larger size)
            uncertainty = p90 - p10
            position_size = min(1.0, 0.5 / max(uncertainty, 0.01))
        elif p50 < 0 and p10 < -threshold:
            signal = 'SHORT'
            uncertainty = p90 - p10
            position_size = -min(1.0, 0.5 / max(uncertainty, 0.01))
        else:
            signal = 'NEUTRAL'
            position_size = 0.0
        
        signals.append(signal)
        positions.append(position_size)
    
    return np.array(signals), np.array(positions)

# Hard risk caps
MAX_POSITION = 1.0
MAX_LEVERAGE = 3.0
MAX_DRAWDOWN = 0.20  # 20% max drawdown stop
```

---

## Pipeline Alignment: BQ → Mac → BQ

### Export View (Flattened for Mac)

```sql
-- definitions/04_training/vw_tft_training_export.sqlx
config {
  type: "view",
  schema: "${dataform.projectConfig.vars.training_dataset}",
  tags: ["training", "mac_export"]
}

-- Flattened STRUCTs, all features, ready for CSV/Parquet
SELECT
  date,
  series_id,
  target,
  
  -- Time-varying known (flattened)
  dow, moy, dom, days_to_expiry, is_wasde_day,
  
  -- Time-varying unknown (flattened from STRUCTs)
  md_price, md_ma_5, md_rsi_14, md_vol_21d,
  s_crush_margin, s_china_imports, s_dollar_index,
  pol_trump_sentiment, zl_fcpo_corr_60d,
  biodiesel_margin, mm_net_length_zl,
  
  -- Regime
  regime_name, regime_weight,
  
  -- All other features...
  
FROM ${ref("vw_daily_ml_flat")}
WHERE date >= '1900-01-01'  -- All history
ORDER BY date, series_id
```

### Mac Export Script

```python
# scripts/export_training_data.py
from google.cloud import bigquery
import pandas as pd
import pyarrow.parquet as pq

def export_tft_training_data():
    client = bigquery.Client(project='cbi-v14')
    
    # Export flattened view
    query = "SELECT * FROM `cbi-v14.training.vw_tft_training_export`"
    
    print("Exporting from BigQuery...")
    df = client.query(query).to_dataframe()
    
    # Downcast to float32 (save memory)
    for col in df.select_dtypes(include=['float64']):
        df[col] = pd.to_numeric(df[col], downcast='float')
    
    # Save as Parquet
    output_path = 'data/tft_training_input.parquet'
    df.to_parquet(output_path, compression='snappy', index=False)
    
    print(f"Exported {len(df)} rows, {len(df.columns)} columns")
    print(f"Size: {output_path.stat().st_size / 1e6:.1f} MB")
    
    return df
```

### Mac Training Script

```python
# scripts/train_maximum_quality.py
import torch
from pytorch_lightning import Trainer
from pytorch_forecasting import TemporalFusionTransformer

# Load data
df = pd.read_parquet('data/tft_training_input.parquet')

# Split: strict walk-forward
train_end = '2020-01-01'
val_end = '2023-07-01'

X_train = df[df['date'] < train_end]
X_val = df[(df['date'] >= train_end) & (df['date'] < val_end)]
X_test = df[df['date'] >= val_end]  # Never touched

# Create datasets
training = TimeSeriesDataSet(X_train, ...)
validation = TimeSeriesDataSet.from_dataset(training, X_val, ...)

# Train TFT with MPS
trainer = Trainer(
    accelerator="mps",  # ✅ Use Metal!
    max_epochs=200,
    early_stopping_patience=15,
    precision=16,  # Mixed precision
)

tft = TemporalFusionTransformer.from_dataset(training, ...)
trainer.fit(tft, train_loader, val_loader)

# Evaluate on test (final, untouched)
test_predictions = tft.predict(test_loader)
final_metrics = evaluate_comprehensive(test_predictions, y_test)
```

### Mac → BigQuery Forecast Export

```python
# scripts/export_forecasts_to_bq.py
from google.cloud import bigquery

def export_forecasts(predictions_df):
    """Export model predictions back to BigQuery"""
    
    client = bigquery.Client(project='cbi-v14')
    
    # Write to forecasts table
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema_update_options=["ALLOW_FIELD_ADDITION"]
    )
    
    job = client.load_table_from_dataframe(
        predictions_df,
        'cbi-v14.forecasts.zl_forecasts_daily_schema',
        job_config=job_config
    )
    
    job.result()
    print(f"Exported {len(predictions_df)} forecasts to BigQuery")
```

---

## M4 Pro Specific Optimizations

### MPS Best Practices

```python
# 1. Check MPS availability
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("✅ Using MPS (Metal)")
else:
    device = torch.device("cpu")
    print("⚠️  MPS not available, using CPU")

# 2. Monitor memory
import psutil

def check_memory():
    ram = psutil.virtual_memory()
    print(f"RAM: {ram.used/1e9:.1f} GB / {ram.total/1e9:.1f} GB used")
    
    if ram.percent > 85:
        print("⚠️  High memory usage - reduce batch size")

# 3. DataLoader workers (moderate)
num_workers = 2  # 2-4 range (not 8+)

# 4. Mixed precision (prefer where stable)
precision = 16  # float16
# Fallback to precision=32 if unstable

# 5. Batch size scaling
batch_size = 64  # Start here
# Increase to 128 if memory allows
# Reduce to 32 if OOM errors
```

### Memory Management

```python
# Clear cache between models
torch.mps.empty_cache()

# Use gradient accumulation if batch size too small
trainer = Trainer(
    accumulate_grad_batches=2,  # Effective batch size = 64 * 2 = 128
    batch_size=64
)

# Stream large datasets
# Don't load 16k rows × 9k features all at once
# Use DataLoader with chunking
```

---

## Hyperparameter Search: Pragmatic Ranges

### TFT Search Space

```python
TFT_SEARCH_SPACE = {
    'hidden_size': [64, 80, 96, 112, 128],  # Not 256+
    'attention_head_size': [4, 6, 8],        # Not 16+
    'lstm_layers': [1, 2],                   # Not 3+
    'dropout': [0.1, 0.15, 0.2],
    'learning_rate': [1e-4, 3e-4, 1e-3],
    'batch_size': [32, 64, 128],            # Memory-dependent
    'max_encoder_length': [120, 150, 180],  # Not 252+
    'max_prediction_length': [20, 42, 63],  # Align with horizons
}

# 20-40 trials (not 100+)
n_trials = 30
```

### LightGBM Search Space

```python
LIGHTGBM_SEARCH_SPACE = {
    'num_leaves': [63, 95, 127],           # Not 255
    'max_depth': [10, 12, 15],             # Not 20+
    'learning_rate': [0.01, 0.02, 0.03],   # Not 0.05+
    'feature_fraction': [0.8, 0.9, 1.0],
    'bagging_fraction': [0.8, 0.9, 1.0],
    'lambda_l1': [0.01, 0.1, 1.0],
    'lambda_l2': [0.01, 0.1, 1.0],
}

# 15-30 trials
n_trials = 25
```

### Deep NN Search Space

```python
DEEP_NN_SEARCH_SPACE = {
    'hidden_sizes': [
        [256, 128, 64],
        [512, 256, 128, 64],
        [512, 256, 128],
    ],
    'dropout': [0.1, 0.15, 0.2],
    'learning_rate': [1e-4, 1e-3],
    'weight_decay': [1e-4, 1e-3],
}

# 10-20 trials max
n_trials = 15
```

---

## Complete Training Workflow

### Phase 1: Data Export (Day 1)

```bash
# Export from BigQuery
python scripts/export_training_data.py

# Verify data
python scripts/verify_exported_data.py
```

### Phase 2: Hyperparameter Search (Days 2-4)

```bash
# TFT search (30 trials, ~2 days)
python scripts/hyperparameter_search_tft.py --n_trials 30

# LightGBM search (25 trials, ~1 day)
python scripts/hyperparameter_search_lightgbm.py --n_trials 25

# Deep NN search (15 trials, ~0.5 day)
python scripts/hyperparameter_search_deepnn.py --n_trials 15
```

### Phase 3: Model Training (Days 5-10)

```bash
# Train TFT with best params (5 seeds, ~2 days)
python scripts/train_tft.py --seeds 42,123,456,789,999

# Train LightGBM quantiles (3 quantiles, ~1 day)
python scripts/train_lightgbm.py --quantiles 0.1,0.5,0.9

# Train Deep NN (~1 day)
python scripts/train_deepnn.py
```

### Phase 4: Ensemble & Evaluation (Days 11-12)

```bash
# Evaluate all models
python scripts/evaluate_all_models.py

# Learn ensemble weights
python scripts/learn_ensemble_weights.py

# Final test evaluation (untouched holdout)
python scripts/final_test_evaluation.py
```

### Phase 5: Deployment (Day 13)

```bash
# Export forecasts to BigQuery
python scripts/export_forecasts_to_bq.py

# Verify API views
python scripts/verify_api_views.py
```

---

## Summary: Maximum Quality, Realistic Implementation

### Principles Maintained

- ✅ **Maximum quality methodology** (no shortcuts)
- ✅ **All features, all data** (but memory-aware)
- ✅ **Strict validation** (walk-forward, no leakage)
- ✅ **Comprehensive evaluation** (many metrics)
- ✅ **Best models only** (no compromises)

### Realistic Constraints

- ✅ **MPS for PyTorch** (Metal Performance Shaders)
- ✅ **24GB RAM management** (streaming, float32, batching)
- ✅ **Smart hyperparameter search** (20-40 trials, not 100+)
- ✅ **Practical ensemble** (best 3-4 models, not everything)
- ✅ **Multiple seeds** (3-5 runs, not 10+)

### Configuration Ranges

**TFT**:
- hidden_size: 64-128 (not 256+)
- attention_heads: 4-8 (not 16+)
- max_encoder_length: 120-180 (not 252+)
- batch_size: 64-128 (start small)
- precision: 16 (float16, fallback to 32)

**LightGBM**:
- num_leaves: 63-127 (not 255)
- max_depth: 10-15 (not 20+)
- learning_rate: 0.01-0.03 (not 0.05+)
- num_boost_round: 1000-3000

**Deep NN**:
- hidden_sizes: [512, 256, 128, 64] (not [1024, 1024, ...])
- Feature selection if needed (SHAP importance)

---

**STATUS**: Maximum quality strategy, realistically tuned for M4 Pro. No compromises on methodology, practical on implementation.

