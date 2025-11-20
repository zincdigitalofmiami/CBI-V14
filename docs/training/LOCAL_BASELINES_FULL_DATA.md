---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Local Baselines – Full Feature Set

**Updated:** November 13, 2025  
**Goal:** Use the wide `models_v4.full_220_comprehensive_2yr` table for local (Mac M4) baseline training.

---

## 1. Export the Wide Dataset (One Command)
```bash
cd /Users/kirkmusick/Documents/GitHub/CBI-V14
python3 scripts/export_full_feature_dataset.py
```
This writes `TrainingData/exports/full_220_comprehensive_2yr.parquet` (≈482 rows × 1,948 columns) using the BigQuery Python client.

Need a different table? Use:
```bash
python3 scripts/export_full_feature_dataset.py \
  --table models_v4.production_training_data_1m_backup_20251112_165404 \
  --output TrainingData/exports/production_training_data_1m_backup.parquet
```

---

## 2. Train Baselines with the Wide Dataset
All baseline scripts now accept `--data-path`.

### Statistical (ARIMA/Prophet)
```bash
python3 src/training/baselines/train_statistical.py \
  --horizon 1m \
  --data-path TrainingData/exports/full_220_comprehensive_2yr.parquet
```

### Tree-Based (LightGBM / XGBoost)
```bash
python3 src/training/baselines/train_tree.py \
  --horizon 1m \
  --data-path TrainingData/exports/full_220_comprehensive_2yr.parquet
```

### Neural (LSTM / GRU on TensorFlow Metal)
```bash
python3 src/training/baselines/train_simple_neural.py \
  --horizon 1m \
  --data-path TrainingData/exports/full_220_comprehensive_2yr.parquet
```

⚠️ Each script still expects `zl_price_current` as the target. The wide dataset also contains `target_1w`, `target_1m`, etc.—adapt the scripts if you want to train on those directly.

---

## 3. Output Locations
Models are saved under `Models/local/baselines/` (same as before). Results remain compatible with the Mac M4 workflow.

---

## 4. Next Steps
- Feature selection / grouping can now happen locally (Polars, DuckDB, etc.).
- When GPT-5 returns the cloud architecture, map the cleaned local features back to the new schema before publishing upstream.
