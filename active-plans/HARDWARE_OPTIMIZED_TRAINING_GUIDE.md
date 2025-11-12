# M4 Mac Mini 16GB - Hardware-Optimized Training Guide
**Last Updated**: November 12, 2025  
**Hardware**: M4 Mac Mini, 16GB unified memory, 1TB external SSD  
**Status**: Production-ready specifications

---

## Critical Hardware Reality

**M4 Mac Mini 16GB Unified Memory**
- CPU + GPU share 16GB (not 32-64GB)
- Sequential training ONLY (one GPU job at a time)
- FP16 mixed precision MANDATORY
- External SSD for all artifacts
- Realistic target: **60-70 models in 7 days**

---

## Environment Specifications

### Python & Framework Versions

**Local (Apple Silicon M4):**
```bash
Python 3.12.6 (via pyenv)
tensorflow-macos==2.16.2
tensorflow-metal==1.2.0
torch==2.4.1 torchaudio==2.4.1 torchvision==0.19.1
polars==1.9.0
duckdb==1.1.1
pyarrow==17.0.0
lightgbm==4.5.0
xgboost==2.1.1
statsmodels==0.14.2
pmdarima==2.0.4
prophet==1.1.6
arch==6.3.0
mapie==0.9.1
shap==0.46.0
lime==0.2.0.1
mlflow==2.16.2
tensorboard==2.16.2
onnx==1.16.1
onnxruntime==1.19.2
scikit-learn==1.5.2
optuna==3.6.1
transformers==4.36.0  # For FinBERT inference
```

**Vertex AI (CPU containers):**
```
tensorflow==2.16.1  # Note: slightly different for CPU parity
```

### Environment Variables

**Use existing setup** (from `setup_new_machine.sh`):
```bash
export EXTERNAL_DRIVE="/Volumes/Satechi Hub"
export CBI_V14_REPO="$EXTERNAL_DRIVE/Projects/CBI-V14"
export CBI_V14_TRAINING_DATA="$CBI_V14_REPO/TrainingData"
export CBI_V14_MODELS="$CBI_V14_REPO/Models"
export CBI_V14_LOGS="$CBI_V14_REPO/Logs"
alias cbi='cd "$CBI_V14_REPO"'
alias cbdata='cd "$CBI_V14_TRAINING_DATA"'
```

**Optional convenience symlink:**
```bash
ln -s "$CBI_V14_REPO" ~/cbi_v14_cache
export CBI_CACHE=~/cbi_v14_cache
```

---

## External SSD Directory Layout

```
/Volumes/Satechi Hub/Projects/CBI-V14/
├── TrainingData/
│   ├── raw/              # BigQuery exports (Parquet)
│   ├── processed/        # Feature-engineered datasets
│   └── exports/          # Ready-to-train Parquet files
├── Models/
│   ├── local/
│   │   ├── baselines/    # Statistical, tree, simple neural
│   │   ├── 1w/           # 1-week horizon models
│   │   ├── 1m/           # 1-month horizon models
│   │   ├── 3m/           # 3-month horizon models
│   │   ├── 6m/           # 6-month horizon models
│   │   └── 12m/          # 12-month horizon models
│   ├── vertex-ai/        # SavedModels for deployment
│   ├── bqml/             # BQML metadata
│   └── mlflow/           # MLflow tracking database
└── Logs/
    ├── training/         # Training logs
    ├── ingestion/        # Data ingestion logs
    └── deployment/       # Deployment logs
```

---

## Mandatory Memory Optimization

### Mixed Precision (FP16) - Enable Globally

**Add to ALL training scripts:**
```python
# At process start (BEFORE importing Keras/models)
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "1"

import tensorflow as tf
from tensorflow.keras import mixed_precision

# Enable FP16 mixed precision (2x memory savings)
mixed_precision.set_global_policy("mixed_float16")
```

### Session Cleanup - After EVERY Model

**Critical for 16GB RAM:**
```python
# After each model fit/eval
from tensorflow.keras import backend as K
K.clear_session()
import gc
gc.collect()

# Optional: Force GPU memory release
if tf.config.list_physical_devices('GPU'):
    tf.config.experimental.reset_memory_stats('GPU:0')
```

### Batch Size Limits (MANDATORY)

```python
# Memory-constrained batch sizes for 16GB RAM
BATCH_SIZES = {
    'trees': None,              # Trees use all data, no batching
    'statistical': None,        # CPU-only, no GPU memory
    'feedforward': 64,          # Simple dense networks
    'lstm_1layer': 64,          # 1-layer LSTM/GRU
    'lstm_2layer': 32,          # 2-layer LSTM/GRU
    'tcn': 32,                  # Temporal Convolutional Networks
    'attention': 16,            # Attention mechanisms (if used)
    'finbert': 16               # FinBERT inference
}
```

### Sequence Length Limits

```python
SEQUENCE_LENGTHS = {
    'default': 256,      # Most models
    'hero_run': 512,     # ONLY for 1-2 special runs
    'attention': 256     # Attention models (never >256)
}
```

---

## Realistic Model Count (Total: 60-70 Models)

### Per-Horizon Breakdown (Shared Across All 5 Horizons)

| Type | Count (Total) | Note |
|------|---------------|------|
| **Trees (LGBM/XGB)** | 15-20 | 3-4 configs per horizon |
| **Stats (ARIMA/ETS/Prophet)** | 10-12 | 2-3 variants per horizon |
| **Simple NN (FFN/LSTM/GRU)** | 15-18 | 3 architectures × 5 horizons |
| **Advanced NN (2-layer/TCN)** | 8-10 | Selective (top 2-3 horizons) |
| **Volatility** | 3-4 | GARCH + neural (shared) |
| **Regime Classifier** | 1 | Shared across all horizons |
| **Regime-Specific** | 8-10 | Top 2-3 archs per regime |
| **Meta-Learners** | 5 | 1 per horizon (ensemble) |
| **TOTAL** | **60-70** | Achievable in 7 days |

**Note:** NOT 26-32 per horizon (that would be 130-160 total - too many for 16GB)

---

## Training Schedule (Prevent Thermal Throttling)

### Golden Rule: ONE HEAVY JOB AT A TIME

**Day 1:** Feature cache (Polars/DuckDB) + tree baselines for 1w/1m/3m (10-14 models)  
**Day 2:** Tree baselines for 6m/12m (8-10) + Stats for 1w/1m/3m (10-12)  
**Day 3:** Stats for 6m/12m (6-8) + Simple NN for 1w/1m/3m (9-12)  
**Day 4:** Simple NN for 6m/12m (6-8) + Advanced: 2-layer LSTM/GRU for 1-2 horizons (2-3)  
**Day 5:** Advanced: finish 2-3 models + Volatility (GARCH/quantile) (shared)  
**Day 6:** Regime classifier + Meta-stackers (1 per horizon) + FinBERT inference  
**Day 7:** Full walk-forward backtest + export winners  

### Thermal Management

- **Desk fan**: Point at Mac (yes, really)
- **Monitor**: Activity Monitor → GPU History
- **If throttling**: Drop batch size or pause for cooldown
- **Never**: Overlap two GPU jobs

---

## Data Pipeline Optimization

### Feature Caching (Build Once, Reuse Everywhere)

```python
import polars as pl
import duckdb

# Build features ONCE per horizon (Day 1)
def cache_features(horizon):
    """Generate all features, cache as Parquet on external SSD"""
    # Read from BigQuery export
    df = pl.read_parquet(f"{CBI_V14_TRAINING_DATA}/exports/production_training_data_{horizon}.parquet")
    
    # Feature engineering (lags, interactions, etc.)
    df = engineer_features(df, horizon)
    
    # Cache to external SSD
    output_path = f"{CBI_V14_TRAINING_DATA}/processed/{horizon}_features.parquet"
    df.write_parquet(output_path)
    
    print(f"✅ Cached features for {horizon}: {output_path}")
    return output_path

# Reuse across ALL models (trees, NN, regime, meta)
features = pl.read_parquet(f"{CBI_V14_TRAINING_DATA}/processed/{horizon}_features.parquet")
```

### Memory Limits

- **Working set:** < 1.5GB RAM per job
- **If larger:** Stream with `pl.scan_parquet()` instead of `read_parquet()`
- **External SSD:** All data, never load into internal drive

---

## Training Code Template (Mandatory Patterns)

### For ALL Neural Network Training

```python
#!/usr/bin/env python3
"""
Training template with mandatory M4 16GB optimizations
"""
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "1"

import tensorflow as tf
from tensorflow.keras import mixed_precision, backend as K
import polars as pl

# MANDATORY: Enable FP16 mixed precision
mixed_precision.set_global_policy("mixed_float16")

# Verify Metal GPU
gpus = tf.config.list_physical_devices('GPU')
print(f"GPU Devices: {gpus}")

# External SSD paths (from environment)
EXTERNAL_DRIVE = os.getenv("EXTERNAL_DRIVE", "/Volumes/Satechi Hub")
CBI_V14_REPO = os.getenv("CBI_V14_REPO", f"{EXTERNAL_DRIVE}/Projects/CBI-V14")
TRAINING_DATA = f"{CBI_V14_REPO}/TrainingData"
MODELS_DIR = f"{CBI_V14_REPO}/Models"

# Load cached features (from external SSD)
features = pl.read_parquet(f"{TRAINING_DATA}/processed/1m_features.parquet")

# Convert to numpy for TensorFlow
X_train, y_train = prepare_data(features)

# Build model with memory-safe batch size
model = build_lstm(units=64, layers=1)

# Train with SMALL batch size for 16GB RAM
history = model.fit(
    X_train, y_train,
    batch_size=32,              # NEVER exceed 64 for LSTM
    epochs=100,
    validation_split=0.2,
    callbacks=[
        tf.keras.callbacks.EarlyStopping(patience=12, restore_best_weights=True)
    ],
    verbose=1
)

# Save to external SSD
model.save(f"{MODELS_DIR}/local/1m/lstm_1layer.h5")

# MANDATORY: Clear session after EVERY model
K.clear_session()
gc.collect()

print("✅ Model trained, session cleared")
```

---

## Vertex AI Naming Convention (Dual)

### Resource Naming (CLI-friendly)

```bash
# Model resource IDs (lowercase, CLI-safe)
cbi-zl-1w-v01
cbi-zl-1m-v01
cbi-zl-3m-v01
cbi-zl-6m-v01
cbi-zl-12m-v01

# Endpoint resource IDs
cbi-zl-1w-endpoint
cbi-zl-1m-endpoint
cbi-zl-3m-endpoint
cbi-zl-6m-endpoint
cbi-zl-12m-endpoint
```

### Display Names (UI-friendly)

```bash
# Model display names (for Google Cloud Console)
"CBI V14 Vertex – Neural 1W v01"
"CBI V14 Vertex – Neural 1M v01"
"CBI V14 Vertex – Neural 3M v01"
"CBI V14 Vertex – Neural 6M v01"
"CBI V14 Vertex – Neural 12M v01"

# Endpoint display names
"CBI V14 Vertex – 1W Endpoint"
"CBI V14 Vertex – 1M Endpoint"
"CBI V14 Vertex – 3M Endpoint"
"CBI V14 Vertex – 6M Endpoint"
"CBI V14 Vertex – 12M Endpoint"
```

### Deployment Commands

```bash
# Upload model (using both resource ID and display name)
gcloud ai models upload \
  --region=us-central1 \
  --display-name="CBI V14 Vertex – Neural 1M v01" \
  --artifact-uri=gs://cbi-v14-models/1m/v01/model \
  --container-image-uri=us-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-16:latest

# Deploy endpoint
gcloud ai endpoints deploy-model $ENDPOINT_ID \
  --region=us-central1 \
  --model=$MODEL_ID \
  --traffic-split=0=100 \
  --min-replica-count=0 \
  --max-replica-count=1
```

**Min replicas = 0** keeps idle cost at zero (pay only for predictions)

---

## PSI Drift Monitoring Strategy

### Phase 1 (During Training): Baseline PSI

```python
from scipy.stats import entropy

def calculate_psi(expected, actual, bins=10):
    """Population Stability Index - detect feature drift"""
    expected_percents = np.histogram(expected, bins=bins)[0] / len(expected)
    actual_percents = np.histogram(actual, bins=bins)[0] / len(actual)
    
    # Avoid log(0)
    expected_percents = np.where(expected_percents == 0, 0.0001, expected_percents)
    actual_percents = np.where(actual_percents == 0, 0.0001, actual_percents)
    
    psi = np.sum((actual_percents - expected_percents) * np.log(actual_percents / expected_percents))
    return psi

# During training: Log baseline PSI
for feature in feature_cols:
    psi = calculate_psi(train_data[feature], val_data[feature])
    mlflow.log_metric(f"psi_{feature}", psi)
    print(f"Feature {feature}: PSI = {psi:.4f}")
```

### Phase 2 (Post-Launch): Operational Drift Monitoring

**Create:** `scripts/monitor_feature_drift.py` (runs daily via cron)

```python
# Check PSI daily on live data vs training data
if psi > 0.25:
    send_alert(f"Feature {feature} drifting (PSI={psi:.2f})")
    trigger_retrain_flag()
```

**Status:** Build baseline logging during training (Days 1-7), activate operational monitoring post-launch

---

## Model Count Budget (60-70 Total, Shared Across Horizons)

### Realistic Breakdown

| Type | Count | Distribution |
|------|-------|--------------|
| **Trees** | 15-20 | LightGBM DART (3-4 configs/horizon), XGBoost DART (2-3 configs/horizon) |
| **Statistical** | 10-12 | ARIMA, Auto-ARIMA, ETS, Prophet (2-3 variants/horizon) |
| **Simple Neural** | 15-18 | FFN, 1-layer LSTM, 1-layer GRU (3 archs × 5 horizons) |
| **Advanced Neural** | 8-10 | 2-layer LSTM/GRU, TCN (selective, top 2-3 horizons) |
| **Volatility** | 3-4 | GARCH, neural volatility (shared across horizons) |
| **Regime Classifier** | 1 | LightGBM (shared across horizons) |
| **Regime-Specific** | 8-10 | Crisis LSTM/GRU, Bull/Bear/Normal (1-2 archs each) |
| **Meta-Learners** | 5 | LightGBM stacker (1 per horizon) |
| **TOTAL** | **60-70** | **Achievable in 7 days on M4 16GB** |

**Each horizon gets:** 6-10 good candidate models (not 30)

---

## Training Knobs (Max Push Without Thermal Issues)

### Trees (LightGBM / XGBoost)

```python
# LightGBM DART
lgb_params = {
    'boosting_type': 'dart',
    'num_leaves': 31,  # to 63 for complex
    'max_depth': 6,    # to 10 for deep trees
    'learning_rate': 0.05,
    'n_estimators': 2000,
    'early_stopping_rounds': 100,
    'num_threads': 8  # M4 has 10 cores, leave 2 for OS
}

# XGBoost DART
xgb_params = {
    'booster': 'dart',
    'max_depth': 8,
    'learning_rate': 0.03,
    'n_estimators': 2000,
    'early_stopping_rounds': 100,
    'tree_method': 'hist',  # Fast histogram method
    'n_jobs': 8
}

# Hyperparameter optimization: Optuna with 20-30 trials per horizon
```

### 1-Layer LSTM/GRU (Simple Neural)

```python
model = tf.keras.Sequential([
    tf.keras.layers.LSTM(128, input_shape=(seq_len, n_features)),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(1)
])

# Training params for 16GB RAM
batch_size = 64          # Max for 1-layer
seq_len = 256            # Default sequence length
epochs = 100
early_stopping = 12
```

### 2-Layer LSTM/GRU (Advanced Neural)

```python
model = tf.keras.Sequential([
    tf.keras.layers.LSTM(128, return_sequences=True),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.LSTM(64),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(1)
])

# Training params for 16GB RAM
batch_size = 32          # Reduced for 2-layer
seq_len = 256
epochs = 120
gradient_accumulation_steps = 2  # If memory still tight
```

### TCN (Temporal Convolutional Network)

```python
# TCN params (efficient architecture)
batch_size = 32
kernel_size = 3  # to 5 for larger receptive field
nb_filters = 64
nb_stacks = 2
dilations = [1, 2, 4, 8]
```

### Tiny Attention (Optional - 1-2 total only)

```python
# ONLY if you must - keep it tiny!
d_model = 128            # Max 256
num_heads = 2            # Max 4
num_layers = 2           # Max 2
seq_len = 128            # Max 256
batch_size = 16          # Max 16
gradient_checkpointing = True  # MANDATORY
```

**Skip heavy Transformers entirely** - not worth thermal issues on 16GB

---

## FinBERT Inference (Pre-Trained, NOT Fine-Tuned)

### Inference-Only Mode (Local on M4)

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np

# Load pre-trained FinBERT (inference-only)
model_name = "ProsusAI/finbert"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Inference function
def score_headlines(texts, batch_size=16):
    """Score headlines for sentiment (inference-only)"""
    all_scores = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        inputs = tokenizer(batch, padding=True, truncation=True, max_length=128, return_tensors="pt")
        
        with torch.no_grad():  # NO training/backprop
            outputs = model(**inputs)
        
        # Get sentiment scores
        scores = torch.nn.functional.softmax(outputs.logits, dim=-1).numpy()
        sentiment_score = scores[:,2] - scores[:,0]  # positive - negative
        all_scores.extend(sentiment_score)
    
    return np.array(all_scores)

# Use case: Score 551 news articles from BigQuery
headlines = load_headlines_from_bigquery()
sentiment_scores = score_headlines(headlines, batch_size=16)

# Add as features to training data
df = df.with_columns(pl.Series("news_sentiment", sentiment_scores))
```

**What this does:** Generate sentiment features (NOT fine-tune model)  
**Why:** Fine-tuning requires 24-80GB GPU RAM (Colab/Kaggle territory)  
**Benefit:** Still get news impact predictions, just from pre-trained weights

### Optional: Fine-Tune on Colab (2 hours, $10)

**If you want custom-tuned FinBERT:**
1. Export 551 articles + price changes to CSV
2. Open Colab Pro notebook (T4 GPU, 16GB VRAM)
3. Fine-tune FinBERT (2 hours)
4. Download fine-tuned weights
5. Use fine-tuned model for inference locally

**Status:** Optional, not part of 7-day plan

---

## Artifact Export (Vertex-Ready)

### Per-Horizon Artifact Package

```
/Volumes/Satechi Hub/Projects/CBI-V14/Models/vertex-ai/<horizon>/
├── model/                      # SavedModel or .onnx
├── feature_schema.json         # Names, dtypes, order
├── metrics.json                # MAPE, Sharpe, dates, CV scheme
├── preproc.pkl                 # Scalers/encoders if used
└── training_hash.txt           # Git commit + data snapshot ID
```

### Deployment Script Integration

```python
# vertex-ai/deployment/upload_to_vertex.py
# Already created - use dual naming

model_resource_id = f"cbi-zl-{horizon}-v01"  # CLI-friendly
display_name = f"CBI V14 Vertex – Neural {horizon.upper()} v01"  # UI-friendly

aiplatform.Model.upload(
    display_name=display_name,
    artifact_uri=f"gs://cbi-v14-models/{horizon}/v01/model",
    serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-16:latest"
)
```

---

## Guardrails (Institutional Standards)

### 1. Leakage Prevention

```python
# Purged + Embargoed CV for overlapping labels
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5, gap=7)  # 7-day embargo between train/test
```

### 2. Overfitting Tripwire

```python
# Veto model if backtest significantly underperforms validation
if (backtest_sharpe - validation_sharpe) > 0.4:
    print(f"⚠️ Model overfitted - Sharpe gap: {backtest_sharpe - validation_sharpe:.2f}")
    veto_model()
```

### 3. MAPE Monitor (Operational)

```python
# Post-launch: Force retrain if rolling MAPE degrades by 50%
if rolling_mape_30d > target_mape * 1.5:
    trigger_retrain()
```

### 4. PSI Drift (Operational)

```python
# Quarantine features with PSI > 0.25
if psi > 0.25:
    quarantine_feature(feature_name)
    retrain_with_reduced_set()
```

---

## Daily Forecast Job (Local Cron)

```python
#!/usr/bin/env python3
"""
Daily forecast generation (runs locally via cron)
"""
import polars as pl
from datetime import datetime

# Load winner models per horizon
models = load_best_models_per_horizon()

# Score latest features
latest_features = get_latest_features_from_bigquery()

# Generate forecasts
forecasts = {}
for horizon, model in models.items():
    forecast = model.predict(latest_features)
    forecasts[horizon] = forecast

# Write to external SSD
output_path = f"{CBI_V14_LOGS}/forecasts/{datetime.now().strftime('%Y-%m-%d')}.parquet"
pl.DataFrame(forecasts).write_parquet(output_path)

# Optional: Export flat JSON for dashboard
pl.DataFrame(forecasts).write_json(f"{CBI_V14_LOGS}/forecasts/latest.json")

print(f"✅ Forecasts generated: {output_path}")
```

**No cloud costs** - runs entirely on M4, writes to external SSD, dashboard reads file

---

## Non-Negotiables (Mandatory for 16GB RAM)

1. ✅ **One heavy job at a time** - Never overlap GPU jobs
2. ✅ **Mixed precision ON** - FP16/bfloat16 for all neural models
3. ✅ **External SSD** - All data/checkpoints/logs
4. ✅ **Clear sessions** - Keras backend clear + GC after every model
5. ✅ **Batch ceilings** - LSTM/GRU/TCN ≤32, Attention ≤16, FFN ≤64
6. ✅ **Sequence length** - 128-256 max, 512 only for single "hero" run
7. ✅ **Early stopping** - Patience 10-15, restore best weights
8. ✅ **Monitor thermals** - Activity Monitor GPU, desk fan

---

## System Tuning (Maximize Performance)

### Kill Background Processes

```bash
# Disable on external drive
# - iCloud Drive sync
# - Time Machine backups
# - Photos indexing
# - Spotlight indexing

# Add to /Volumes/Satechi Hub/.metadata_never_index
touch "/Volumes/Satechi Hub/.metadata_never_index"
```

### Thermal Management

- Elevate Mac on stand
- Point desk fan at Mac
- Monitor: Activity Monitor → Window → GPU History
- If epoch time increases: You're throttling → drop batch size or pause

---

## Summary: Max Push Configuration

**Environment:** Python 3.12.6, TensorFlow 2.16.2 + Metal 1.2.0, existing `$CBI_V14_REPO` paths  
**Models:** 60-70 total (shared across horizons), not 130-160  
**Training:** Sequential only, FP16 mandatory, external SSD for all artifacts  
**Naming:** Dual (CLI: `cbi-zl-1m-v01`, UI: `CBI V14 Vertex – Neural 1M v01`)  
**PSI:** Baseline logging during training, operational monitoring post-launch  
**FinBERT:** Inference-only (pre-trained), optional Colab fine-tuning ($10)  
**Deployment:** Min replicas = 0 (zero idle cost)  

**Result:** Institutional-grade system, hardware-realistic, no thermal meltdown, guaranteed 7-day completion ✅

---

**Last Updated**: November 12, 2025  
**Status**: Production specifications for M4 Mac Mini 16GB

