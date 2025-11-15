# M4 Mac Training Optimization Guide

**Last Updated**: November 2025  
**Status**: ✅ Complete Implementation

This guide documents the M4 Mac optimizations implemented to match or exceed cloud (BQML/Vertex AI) accuracy while training locally.

---

## Overview

The M4 Mac is fully capable of training production-quality forecasting models. The key is not more power, but:

1. **Consistent preprocessing** (frozen scaling, imputation)
2. **Disciplined splits** (walk-forward validation, not random)
3. **Sane hyperparameters** (tuned for local compute)
4. **Strict evaluation gates** (MAPE/Sharpe thresholds)

---

## Architecture Components

### 1. Pre-Training Calculations

**Location**: `src/training/features/compute_correlations.py`

**Features**:
- Block-wise correlation computation (avoids full N×N matrix)
- Polars lazy queries for memory efficiency
- Rolling correlations (90d, 180d, 365d windows)
- Caching with date-based invalidation
- Cross-block correlations only for top-k candidates

**Usage**:
```bash
python src/training/features/compute_correlations.py \
    --data-path TrainingData/exports/zl_training_prod_allhistory_1m.parquet \
    --cache-max-age 7
```

**Key Optimizations**:
- Feature blocks: Big7+Macro, Spreads, News/Sentiment, Weather, Policy/Political
- Key pairs tracked: ZL vs VIX, DXY, FCPO, Crush Margin
- Regime-specific correlations computed separately

### 2. Evaluation Pipeline

**Location**: `src/training/evaluation/metrics.py`

**Metrics Provided**:
- **MAPE** (Mean Absolute Percentage Error) by horizon, regime, season
- **Sharpe Ratio** (annualized) for trading strategy evaluation
- **Regime-specific breakdown** (crisis vs normal performance)
- **Leakage detection** (future data contamination checks)

**Usage**:
```bash
python src/training/evaluation/metrics.py \
    --predictions predictions.parquet \
    --y-true-col target_1m \
    --y-pred-col predicted_1m \
    --horizon 1m \
    --regime-col market_regime
```

**Evaluation Thresholds** (gates for model promotion):
- 1w: MAPE ≤ 3.0%, Sharpe ≥ 1.2
- 1m: MAPE ≤ 4.0%, Sharpe ≥ 1.0
- 3m: MAPE ≤ 6.0%, Sharpe ≥ 0.8
- 6m: MAPE ≤ 8.0%, Sharpe ≥ 0.6
- 12m: MAPE ≤ 12.0%, Sharpe ≥ 0.5

### 3. M4 Training Configuration

**Location**: `src/training/config/m4_config.py`

**Configurations**:
- **LightGBM**: num_leaves=31, max_depth=6, lr=0.05, n_estimators=1500
- **XGBoost**: max_depth=8, lr=0.03, tree_method='hist', n_jobs=4-6
- **Neural Nets**: Batch size scales with RAM (128-512), FP16 mixed precision, MPS device

**System Detection**:
- Auto-detects CPU count (4-6 performance cores)
- Auto-detects RAM (16-48GB)
- Adjusts batch sizes and sequence lengths accordingly

**Usage**:
```python
from training.config.m4_config import get_config_for_model

config = get_config_for_model('lightgbm', horizon='1m')
# Returns M4-optimized hyperparameters
```

### 4. Pre-Training Diagnostics

**Location**: `scripts/training/pre_training_diagnostics.py`

**Checks**:
1. Regime statistics (mean/std returns, MAPE, Sharpe by regime)
2. Target alignment (properly shifted, no leakage)
3. Missing data patterns (>50% threshold)
4. Regime weight distribution

**Usage**:
```bash
python scripts/training/pre_training_diagnostics.py \
    --data-path TrainingData/exports/zl_training_prod_allhistory_1m.parquet \
    --horizon 1m
```

**Output**: JSON file with all diagnostic results

---

## Environment Setup

### 1. Create Conda Environment

**Location**: `scripts/setup/m4_environment.sh`

**What it installs**:
- Python 3.12 (arm64 optimized)
- NumPy/SciPy (built against Accelerate framework)
- Polars (fast columnar processing)
- LightGBM/XGBoost (with multithreading)
- TensorFlow-Mac + TensorFlow-Metal (GPU acceleration)
- PyTorch (with MPS support)
- MLflow (model tracking)

**Usage**:
```bash
bash scripts/setup/m4_environment.sh cbi-m4-training
conda activate cbi-m4-training
```

### 2. Verify Installation

```bash
# Check TensorFlow Metal GPU
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"

# Check Polars
python -c "import polars as pl; print(pl.__version__)"

# Check system config
python src/training/config/m4_config.py
```

---

## Training Workflow

### Step 1: Export Training Data

```bash
python scripts/export_training_data.py --horizon 1m --surface prod
```

### Step 2: Run Pre-Training Diagnostics

```bash
python scripts/training/pre_training_diagnostics.py \
    --data-path TrainingData/exports/zl_training_prod_allhistory_1m.parquet \
    --horizon 1m
```

**Review**:
- Regime statistics (should match expected distributions)
- Alignment checks (all should pass)
- Missing data (should be minimal)
- Regime weights (should match training plan)

### Step 3: Compute Correlations (Optional)

```bash
python src/training/features/compute_correlations.py \
    --data-path TrainingData/exports/zl_training_prod_allhistory_1m.parquet
```

**Output**: Cached correlation features in `TrainingData/exports/cache/`

### Step 4: Train Models

**Tree Models**:
```bash
python src/training/baselines/tree_models.py --horizon 1m --surface prod
```

**Neural Models**:
```bash
python src/training/baselines/neural_baseline.py --horizon 1m --surface prod
```

**Enhanced Features**:
- Uses M4-optimized configs automatically
- Walk-forward validation (not random split)
- Comprehensive evaluation with regime breakdown
- Threshold checking (warns if MAPE/Sharpe below targets)

### Step 5: Evaluate Results

Models are automatically evaluated during training. Check MLflow UI:

```bash
mlflow ui --backend-store-uri file:///path/to/Models/mlflow
```

**Key Metrics to Review**:
- `val_mape`: Should be ≤ threshold for horizon
- `mape_{regime}`: Regime-specific performance
- `sharpe_{regime}`: Trading strategy performance
- `meets_mape_threshold`: Boolean gate for promotion

---

## Key Differences vs Cloud Training

### What Changed

1. **Preprocessing**: Now explicit and serialized (was hidden in BQML)
2. **Splits**: Walk-forward validation (was random in BQML)
3. **Hyperparameters**: Fewer but smarter trials (no massive AutoML sweeps)
4. **Evaluation**: Stricter gates (MAPE drift >20% = no promotion)

### What Stayed the Same

1. **Regime weights**: Same 50-5000 scale from training plan
2. **Feature engineering**: Same correlation windows, lags, spreads
3. **Model families**: LightGBM, XGBoost, LSTM, GRU (same as before)
4. **Target metrics**: MAPE 2-3% short horizon, Sharpe 1.2-2.0+

---

## Performance Benchmarks

### Expected Training Times (M4 16GB)

- **LightGBM**: ~5-10 minutes per horizon
- **XGBoost**: ~8-15 minutes per horizon
- **LSTM (1-layer)**: ~15-30 minutes per horizon
- **Multi-layer LSTM**: ~30-60 minutes per horizon

### Memory Usage

- **16GB RAM**: Batch size 128, sequence length 30
- **32GB RAM**: Batch size 256, sequence length 60
- **48GB+ RAM**: Batch size 512, sequence length 90

### Storage Recommendations

**Fast NVMe External SSD (USB-C/Thunderbolt)**:
- `TrainingData/exports/*.parquet` (training data)
- `Models/local/...` (trained models)
- `TrainingData/exports/cache/` (correlation matrices)

**Why**: I/O bottlenecks are the #1 performance killer. Fast disk = faster training.

---

## Troubleshooting

### Issue: Out of Memory

**Solution**:
1. Reduce batch size in `m4_config.py`
2. Use Polars lazy queries (already implemented)
3. Process data in chunks
4. Close browsers/video during training

### Issue: Slow Training

**Solution**:
1. Ensure data is on fast external SSD
2. Check CPU throttling (Activity Monitor)
3. Disable Spotlight indexing on training data directory
4. Use fewer threads (4-6 instead of 8-10)

### Issue: MAPE Above Threshold

**Solution**:
1. Check pre-training diagnostics (data quality)
2. Verify regime weights are applied correctly
3. Review feature engineering (correlations, lags)
4. Try different hyperparameters (learning rate, depth)

### Issue: GPU Not Detected

**Solution**:
```bash
# Reinstall TensorFlow Metal
pip uninstall tensorflow-macos tensorflow-metal
pip install tensorflow-macos tensorflow-metal

# Verify
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

---

## Next Steps

1. **Benchmark full training cycle**: Export → Diagnose → Train → Evaluate
2. **Tune batch size & n_jobs**: Increase until memory/CPU saturates
3. **Compare against BQML/Vertex**: Use same evaluation metrics
4. **Adjust regime weights**: Only if validation says so (regime-level MAPE/Sharpe)

---

## References

- **Training Plan**: `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md`
- **M4 Config**: `src/training/config/m4_config.py`
- **Evaluation**: `src/training/evaluation/metrics.py`
- **Correlations**: `src/training/features/compute_correlations.py`

---

**Status**: ✅ All components implemented and ready for use.

