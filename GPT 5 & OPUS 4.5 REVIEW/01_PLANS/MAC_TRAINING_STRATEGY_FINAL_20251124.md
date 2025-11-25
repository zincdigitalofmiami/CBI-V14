# Mac-Only Training Strategy - Final Plan
**Date**: November 24, 2025  
**Constraint**: ALL training on M4 Pro Mac, period  
**Machine**: Mac mini M4 Pro, 24GB RAM, 14-core CPU

---

## Training Architecture (Mac-Centric)

### Data Flow
```
BigQuery (Dataform) 
  → Export to CSV/Parquet
    → Mac Local Storage
      → Training (LightGBM/TFT/PyTorch)
        → Model Export (SavedModel/Pickle)
          → Deploy to BigQuery/Cloud Run
            → API/Dashboard
```

**No BQML training** (except maybe for comparison baseline)  
**No Vertex AI training** (Mac only)  
**All models trained locally**

---

## Baseline Model: LightGBM (Not XGBoost)

### Why LightGBM Wins on Mac

**Performance**:
- ✅ **2-10x faster** than XGBoost (critical for iteration)
- ✅ **Lower memory** (24GB is plenty, but efficiency matters)
- ✅ **Better categorical handling** (your Trump sentiment, regime flags)
- ✅ **Proven better** on forecasting tasks (research confirms)

**Mac-Specific Advantages**:
- ✅ **Native Python** (no BigQuery dependency)
- ✅ **Fast iteration** (train in minutes, not hours)
- ✅ **Full control** (hyperparameters, custom loss functions)
- ✅ **Quantile support** (native for P10/P50/P90)

### LightGBM Configuration for Your Data

```python
import lightgbm as lgb
import pandas as pd
import numpy as np

# Load from BigQuery export
df = pd.read_parquet('tft_training_input.parquet')

# Separate by horizon
for horizon in ['1d', '5d', '20d']:
    target_col = f'return_{horizon}_fwd'
    
    # Train quantile models
    for quantile, alpha in [(0.1, 'p10'), (0.5, 'p50'), (0.9, 'p90')]:
        params = {
            'objective': 'quantile',
            'alpha': quantile,
            'metric': 'quantile',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,  # Use 80% features per tree
            'bagging_fraction': 0.8,  # Use 80% rows per tree
            'bagging_freq': 5,
            'min_data_in_leaf': 20,
            'max_depth': 10,
            'verbose': -1
        }
        
        train_data = lgb.Dataset(
            df.drop(columns=[target_col]),
            label=df[target_col],
            categorical_feature=['regime_name', 'contract_month']  # Your categoricals
        )
        
        model = lgb.train(
            params,
            train_data,
            num_boost_round=200,
            valid_sets=[train_data],
            callbacks=[lgb.early_stopping(10), lgb.log_evaluation(10)]
        )
        
        # Save model
        model.save_model(f'lightgbm_{horizon}_{alpha}.txt')
```

**Expected Training Time** (M4 Pro CPU):
- Single model: 5-15 minutes
- Full ensemble (3 horizons × 3 quantiles): 45-90 minutes
- **Much faster than XGBoost!**

---

## TFT Training on Mac

### PyTorch Lightning Setup

```python
import torch
from pytorch_lightning import Trainer
from pytorch_forecasting import TimeSeriesDataSet, TemporalFusionTransformer

# Load from BigQuery export
df = pd.read_parquet('tft_training_input.parquet')

# Configure for Mac CPU (no GPU)
trainer = Trainer(
    max_epochs=50,
    accelerator='cpu',  # M4 Pro CPU (Metal not working)
    devices=1,
    enable_progress_bar=True,
    enable_model_summary=True,
    gradient_clip_val=0.5,
    callbacks=[
        EarlyStopping(monitor='val_loss', patience=5),
        ModelCheckpoint(monitor='val_loss')
    ]
)

# Training dataset
training = TimeSeriesDataSet(
    df,
    time_idx="time_idx",
    target="target",
    group_ids=["series_id"],
    max_encoder_length=60,
    max_prediction_length=20,
    time_varying_known_reals=["dow", "moy", "is_wasde"],
    time_varying_unknown_reals=[
        "zl_ret", "crush_margin", "china_imports", 
        "dollar_index", "trump_sentiment"
    ],
    static_categoricals=["contract_month"]
)

# Model
tft = TemporalFusionTransformer.from_dataset(
    training,
    learning_rate=3e-4,
    hidden_size=64,
    attention_head_size=4,
    dropout=0.15,
    reduce_on_plateau_patience=3
)

# Train
trainer.fit(tft, train_dataloader, val_dataloader)
```

**Expected Training Time** (M4 Pro CPU):
- Single horizon: 30-60 minutes
- Multi-horizon: 2-4 hours
- **Acceptable on CPU!**

---

## Data Export Strategy

### From BigQuery to Mac

**Option 1: Parquet Export (Recommended)**
```python
from google.cloud import bigquery
import pandas as pd

client = bigquery.Client(project='cbi-v14')

# Export TFT training input
query = """
SELECT * FROM `cbi-v14.training.tft_training_input`
WHERE date >= '2015-01-01'
"""

df = client.query(query).to_dataframe()

# Save as Parquet (compressed, fast)
df.to_parquet('data/tft_training_input.parquet', compression='snappy')

# Size estimate: ~150 features × 6,000 rows = ~50-100 MB
```

**Option 2: CSV Export (Simple)**
```bash
# Using bq command line
bq extract --destination_format=CSV \
  --compression=GZIP \
  'cbi-v14:training.tft_training_input' \
  'gs://cbi-v14-exports/tft_training_input_*.csv.gz'

# Download from GCS
gsutil cp gs://cbi-v14-exports/tft_training_input_*.csv.gz ./data/
gunzip data/tft_training_input_*.csv.gz
```

**Option 3: Incremental Updates**
```python
# Daily incremental export
last_date = pd.read_parquet('data/last_export_date.parquet')['date'].max()

query = f"""
SELECT * FROM `cbi-v14.training.tft_training_input`
WHERE date > '{last_date}'
"""

new_data = client.query(query).to_dataframe()
existing_data = pd.read_parquet('data/tft_training_input.parquet')

# Append and save
combined = pd.concat([existing_data, new_data]).drop_duplicates(subset=['date', 'series_id'])
combined.to_parquet('data/tft_training_input.parquet')
```

---

## Model Deployment Strategy

### After Training on Mac

**Step 1: Export Models**
```python
# LightGBM
model.save_model('models/lightgbm_1d_p50.txt')

# TFT (PyTorch)
torch.save(tft.state_dict(), 'models/tft_1d_20d.pt')
tft.save('models/tft_1d_20d.pkl')  # Full model

# Or use ONNX for cross-platform
import onnx
onnx_model = onnx.export(tft, ...)
```

**Step 2: Deploy to Cloud**

**Option A: Cloud Run (Python Service)**
```python
# cloud_run/predictor.py
import lightgbm as lgb
import pandas as pd

model = lgb.Booster(model_file='models/lightgbm_1d_p50.txt')

def predict(features):
    pred = model.predict(features)
    return pred

# Deploy
# gcloud run deploy predictor --source .
```

**Option B: BigQuery ML (Import Model)**
```sql
-- Import LightGBM model (if BQML supports it)
-- Or use ML.PREDICT with external model endpoint
```

**Option C: Vertex AI (Model Registry)**
```python
from google.cloud import aiplatform

aiplatform.init(project='cbi-v14', location='us-central1')

model = aiplatform.Model.upload(
    display_name='lightgbm_zl_1d',
    artifact_uri='gs://cbi-v14-models/lightgbm_1d_p50.txt',
    serving_container_image_uri='...'
)

endpoint = model.deploy()
```

---

## Training Workflow (Mac-Only)

### Daily Training Pipeline

```bash
#!/bin/bash
# scripts/train_daily.sh

# 1. Export latest data from BigQuery
python scripts/export_training_data.py

# 2. Train LightGBM baselines
python scripts/train_lightgbm.py \
  --horizon 1d --quantiles 0.1,0.5,0.9 \
  --output models/lightgbm_1d/

# 3. Train TFT (if needed)
python scripts/train_tft.py \
  --horizon 1d_20d \
  --output models/tft_1d_20d/

# 4. Evaluate models
python scripts/evaluate_models.py \
  --lightgbm models/lightgbm_1d/ \
  --tft models/tft_1d_20d/ \
  --output results/comparison.json

# 5. Deploy best model
python scripts/deploy_model.py \
  --model results/best_model.json \
  --target cloud_run
```

---

## Performance Expectations (M4 Pro CPU)

### LightGBM Training Times

| Model | Features | Rows | Time (CPU) |
|-------|----------|------|------------|
| Single quantile | 150 | 6,000 | 5-10 min |
| Full ensemble (3 quantiles) | 150 | 6,000 | 15-30 min |
| Multi-horizon (3 horizons) | 150 | 6,000 | 45-90 min |

**Total**: ~1-2 hours for complete baseline ensemble

### TFT Training Times

| Model | Features | Rows | Time (CPU) |
|-------|----------|------|------------|
| Single horizon | 150 | 6,000 | 30-60 min |
| Multi-horizon | 150 | 6,000 | 2-4 hours |

**Total**: ~2-4 hours for complete TFT model

### Comparison

**LightGBM**: Faster, simpler, good baselines  
**TFT**: Slower, more advanced, probabilistic forecasts

**Recommendation**: Start with LightGBM, add TFT later

---

## Updated Recommendations

### Baseline Models (Mac Training)

**Primary**: LightGBM
- ✅ Fastest iteration
- ✅ Best for high-dimensional features
- ✅ Native quantile support
- ✅ Proven better on forecasting

**Secondary**: XGBoost (for comparison only)
- Train on Mac for comparison
- Don't use BQML (Mac-only constraint)

### Advanced Models (Mac Training)

**Primary**: TFT (PyTorch Lightning)
- ✅ State-of-the-art
- ✅ Probabilistic forecasts
- ✅ Multi-contract support
- ⚠️ Slower (2-4 hours on CPU)

**Secondary**: Your LSTM/GRU plans
- Still valid for Mac training
- Use TensorFlow (CPU mode)

---

## Data Export Script

```python
# scripts/export_training_data.py
"""
Export BigQuery training data to Mac for local training
"""

from google.cloud import bigquery
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path

def export_tft_training_data():
    """Export TFT-ready training data from BigQuery"""
    
    client = bigquery.Client(project='cbi-v14')
    
    query = """
    SELECT 
      date,
      series_id,
      time_idx,
      target,
      -- Time-varying known
      dow, moy, dom, days_to_expiry, is_wasde_day,
      -- Time-varying unknown
      zl_ret, zl_vol20, m1_m2_spread, m1_m3_spread,
      crush_margin, china_imports, dollar_index, fed_policy,
      trump_sentiment, vix_regime,
      fcpo_ret, ho_ret, dxy_ret, usdbrl_ret,
      news_tone_finbert, weather_precip_anom,
      -- Static
      contract_month
    FROM `cbi-v14.training.tft_training_input`
    WHERE date >= '2015-01-01'
    ORDER BY date, series_id
    """
    
    print("Exporting data from BigQuery...")
    df = client.query(query).to_dataframe()
    
    print(f"Exported {len(df)} rows, {len(df.columns)} columns")
    
    # Save as Parquet
    output_path = Path('data/tft_training_input.parquet')
    output_path.parent.mkdir(exist_ok=True)
    
    df.to_parquet(output_path, compression='snappy', index=False)
    
    print(f"Saved to {output_path}")
    print(f"Size: {output_path.stat().st_size / 1e6:.1f} MB")
    
    return df

if __name__ == '__main__':
    export_tft_training_data()
```

---

## Training Script Template

```python
# scripts/train_lightgbm_baseline.py
"""
Train LightGBM baseline models on Mac
"""

import lightgbm as lgb
import pandas as pd
import numpy as np
from pathlib import Path
import json

def train_quantile_model(df, target_col, quantile, output_dir):
    """Train a single quantile model"""
    
    # Prepare data
    X = df.drop(columns=[target_col, 'date', 'series_id'])
    y = df[target_col]
    
    # Identify categorical features
    categoricals = ['contract_month', 'regime_name'] if 'regime_name' in X.columns else ['contract_month']
    
    # LightGBM parameters
    params = {
        'objective': 'quantile',
        'alpha': quantile,
        'metric': 'quantile',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'min_data_in_leaf': 20,
        'max_depth': 10,
        'verbose': -1
    }
    
    # Create dataset
    train_data = lgb.Dataset(
        X,
        label=y,
        categorical_feature=categoricals,
        free_raw_data=False
    )
    
    # Train
    print(f"Training quantile {quantile} model...")
    model = lgb.train(
        params,
        train_data,
        num_boost_round=200,
        valid_sets=[train_data],
        callbacks=[
            lgb.early_stopping(stopping_rounds=10),
            lgb.log_evaluation(period=10)
        ]
    )
    
    # Save
    output_path = Path(output_dir) / f'lightgbm_q{int(quantile*100)}.txt'
    model.save_model(str(output_path))
    
    print(f"Saved model to {output_path}")
    
    return model

def main():
    # Load data
    df = pd.read_parquet('data/tft_training_input.parquet')
    
    # Train for each horizon
    for horizon in ['1d', '5d', '20d']:
        target_col = f'return_{horizon}_fwd'
        
        if target_col not in df.columns:
            print(f"Skipping {horizon} - target column not found")
            continue
        
        output_dir = Path(f'models/lightgbm_{horizon}')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Train P10, P50, P90
        for quantile in [0.1, 0.5, 0.9]:
            model = train_quantile_model(
                df, target_col, quantile, output_dir
            )
        
        print(f"Completed {horizon} horizon training")

if __name__ == '__main__':
    main()
```

---

## Summary: Mac-Only Training Strategy

### Architecture

**Training**: 100% on Mac M4 Pro  
**Data Source**: BigQuery (exported to Mac)  
**Models**: LightGBM (primary), TFT (advanced), LSTM/GRU (your plan)  
**Deployment**: Cloud Run / Vertex AI / BigQuery ML (import)

### Key Decisions

1. ✅ **LightGBM for baselines** (not XGBoost)
2. ✅ **TFT on Mac CPU** (2-4 hours acceptable)
3. ✅ **Parquet export** (fast, compressed)
4. ✅ **Local model storage** (models/ directory)
5. ✅ **Cloud deployment** (after training)

### Workflow

1. **Daily**: Export latest data from BigQuery
2. **Train**: LightGBM baselines (1-2 hours)
3. **Train**: TFT if needed (2-4 hours)
4. **Evaluate**: Compare models
5. **Deploy**: Best model to Cloud Run/Vertex AI

### Performance

**M4 Pro CPU is sufficient**:
- LightGBM: 5-15 min per model
- TFT: 30-60 min per horizon
- Full ensemble: 1-4 hours total

**No GPU needed** (Metal not working anyway)

---

**STATUS**: Mac-only training strategy defined. All models train locally, deploy to cloud.

