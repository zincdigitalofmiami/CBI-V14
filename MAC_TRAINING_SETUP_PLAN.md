# Mac Training Setup Plan - M2 Max TensorFlow Metal Pipeline
**Date**: November 7, 2025  
**Purpose**: Plan local Mac training infrastructure for neural forecasting pipeline

---

## Context

The VERTEX_AI_TRUMP_ERA_PLAN.md outlines a neural forecasting pipeline (Phase 4.5) that trains TensorFlow/Keras models locally on M2 Max MacBook Pro using GPU acceleration via tensorflow-metal, then deploys to Vertex AI.

**Current Status**: Planning phase - no Mac training infrastructure exists yet.

---

## Hardware & Software Requirements

### Confirmed Setup (from memory)
- **Hardware**: M2 Max MacBook Pro with 38-core GPU
- **Python**: 3.12.6
- **TensorFlow**: 2.20.0
- **TensorFlow Metal**: 1.2.0
- **Status**: ✅ Confirmed working

### Additional Requirements Needed
- **macOS**: 12.0+ (required for tensorflow-metal)
- **Xcode Command Line Tools**: Required for Metal support
- **Python Packages**: 
  - tensorflow
  - tensorflow-metal
  - keras
  - numpy
  - pandas
  - google-cloud-bigquery
  - shap (for explainability)
  - scikit-learn (for preprocessing)

---

## Architecture Decision: Mac Training vs BigQuery ML

### Option A: BigQuery ML (Current Trump-Era Plan)
- **Model**: DART boosted tree regressor
- **Training**: Cloud-based, no local setup needed
- **Cost**: ~$0.12 per training run
- **Time**: ~11 minutes
- **Status**: Ready to train (after bug fix)

### Option B: Mac Neural Pipeline (Vertex AI Plan Phase 4.5)
- **Model**: LSTM/GRU/Feedforward neural networks
- **Training**: Local M2 Max with GPU acceleration
- **Cost**: Free (local compute)
- **Time**: Varies by model complexity
- **Status**: Not yet implemented

### Decision Framework
- **Trump-Era DART Model**: Use BigQuery ML (simpler, faster, already planned)
- **Neural Pipeline**: Use Mac training (for advanced features: SHAP, Monte Carlo, what-if scenarios)
- **Both Can Coexist**: Different use cases, complementary approaches

---

## Mac Training Infrastructure Plan

### Phase 1: Environment Setup

#### 1.1 Verify Current Setup
```bash
# Check Python version
python3 --version  # Should be 3.12.6

# Check TensorFlow installation
python3 -c "import tensorflow as tf; print(tf.__version__)"
# Should show: 2.20.0

# Check Metal plugin
python3 -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
# Should show: [PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')]

# Verify Metal acceleration
python3 -c "import tensorflow as tf; print(tf.config.list_logical_devices('GPU'))"
# Should show Metal device
```

#### 1.2 Install Missing Dependencies
```bash
# Create virtual environment (if not exists)
python3 -m venv venv
source venv/bin/activate

# Install core packages
pip install tensorflow tensorflow-metal

# Install ML/AI packages
pip install keras numpy pandas scikit-learn shap

# Install Google Cloud packages
pip install google-cloud-bigquery google-cloud-storage

# Install utilities
pip install pyyaml click  # For config and CLI
```

#### 1.3 Test GPU Acceleration
```python
# test_gpu.py
import tensorflow as tf
import numpy as np

# Verify Metal GPU available
print("GPU Devices:", tf.config.list_physical_devices('GPU'))

# Simple test: matrix multiplication on GPU
with tf.device('/GPU:0'):
    a = tf.random.normal([1000, 1000])
    b = tf.random.normal([1000, 1000])
    c = tf.matmul(a, b)
    print("GPU test passed:", c.shape)
```

---

### Phase 2: Directory Structure

Create neural pipeline structure per VERTEX_AI_TRUMP_ERA_PLAN.md:

```
vertex-ai/neural-pipeline/
├── data/
│   ├── loaders.py              # BigQuery → TensorFlow data loaders
│   ├── preprocessors.py        # Normalization, windowing, feature validation
│   └── schemas.py              # Feature schema validation
│
├── models/
│   ├── model.py                # Model factory (LSTM/GRU/Feedforward)
│   ├── architectures.py       # Layer definitions
│   └── configs/
│       ├── lstm_1m.yaml        # 1M horizon config
│       ├── gru_3m.yaml         # 3M horizon config
│       └── feedforward_6m.yaml # 6M horizon config
│
├── train/
│   ├── train.py                # Main training script
│   ├── callbacks.py            # EarlyStopping, ModelCheckpoint
│   └── train_loop.py          # Reusable training loop
│
├── evaluate/
│   ├── evaluate.py             # Metrics calculation
│   ├── monte_carlo.py          # Monte Carlo dropout
│   └── forecast_generator.py   # Generate forecasts
│
├── interpret/
│   ├── compute_shap.py         # SHAP DeepExplainer
│   ├── global_importance.py   # Global feature importance
│   └── local_explanations.py  # Per-forecast explanations
│
├── scenario/
│   ├── run_scenario.py         # What-if scenario engine
│   └── api/
│       └── scenario_api.py     # FastAPI endpoint
│
├── utils/
│   ├── metrics.py              # MAPE, RMSE, etc.
│   ├── logging.py             # TensorBoard logging
│   └── versioning.py          # Model versioning
│
├── deployment/
│   ├── export_savedmodel.py   # Export to SavedModel
│   └── vertex_upload.py       # Upload to Vertex AI
│
└── main.py                     # CLI entry point
```

---

### Phase 3: Data Pipeline Integration

#### 3.1 BigQuery Data Loader
- **Source**: `cbi-v14.models_v4.trump_rich_2023_2025` (or `vertex_ai_training_*_base`)
- **Format**: TensorFlow `tf.data.Dataset` or NumPy arrays
- **Features**: All 58 columns (56 features + date + target)
- **Validation**: Match `feature_metadata_catalog` schema

#### 3.2 Preprocessing Pipeline
- **Normalization**: Min-max or z-score scaling
- **Time Windowing**: Sliding windows for LSTM/GRU (e.g., 30-day lookback)
- **Feature Selection**: Top 1,000 features (matches Vertex AI limit)
- **Missing Values**: Forward-fill or median imputation

---

### Phase 4: Model Training Workflow

#### 4.1 Training Configuration
- **Horizons**: 1M, 3M, 6M, 12M (parameterized)
- **Architectures**: LSTM (1M), GRU (3M), Feedforward (6M, 12M)
- **Dropout**: Enabled for Monte Carlo uncertainty
- **Callbacks**: EarlyStopping, ModelCheckpoint, ReduceLROnPlateau

#### 4.2 Training Execution
```bash
# Train 1M horizon model
python main.py train --horizon=1m --config=configs/lstm_1m.yaml

# Train 3M horizon model
python main.py train --horizon=3m --config=configs/gru_3m.yaml
```

#### 4.3 GPU Utilization
- **Batch Size**: Optimize for M2 Max GPU memory
- **Mixed Precision**: Use float16 for faster training
- **Multi-GPU**: Not applicable (single GPU on M2 Max)

---

### Phase 5: Integration with Existing Systems

#### 5.1 Data Source Coordination
- **Shared Data**: Both BQML and Mac training use same source tables
- **No Conflicts**: Different models, different purposes
- **Data Refresh**: Coordinate with BigQuery ingestion pipeline

#### 5.2 Model Deployment
- **BQML Models**: Deploy directly in BigQuery
- **Neural Models**: Export SavedModel → Upload to Vertex AI → Deploy endpoint
- **Hybrid Approach**: Use both model types (ensemble or A/B testing)

---

## Implementation Checklist

### Environment Setup
- [ ] Verify Python 3.12.6 installed
- [ ] Verify TensorFlow 2.20.0 + tensorflow-metal 1.2.0 installed
- [ ] Test GPU acceleration (Metal device visible)
- [ ] Install all required Python packages
- [ ] Create virtual environment (if not exists)

### Directory Structure
- [ ] Create `vertex-ai/neural-pipeline/` directory structure
- [ ] Create all subdirectories (data/, models/, train/, etc.)
- [ ] Create placeholder files for each module

### Data Pipeline
- [ ] Implement BigQuery data loader (`data/loaders.py`)
- [ ] Implement preprocessing pipeline (`data/preprocessors.py`)
- [ ] Implement schema validation (`data/schemas.py`)
- [ ] Test data loading from `trump_rich_2023_2025` table

### Model Architecture
- [ ] Implement model factory (`models/model.py`)
- [ ] Implement LSTM architecture
- [ ] Implement GRU architecture
- [ ] Implement Feedforward architecture
- [ ] Create YAML config files for each horizon

### Training Infrastructure
- [ ] Implement training script (`train/train.py`)
- [ ] Implement callbacks (`train/callbacks.py`)
- [ ] Test training loop with small dataset
- [ ] Verify GPU utilization during training

### Evaluation & Explainability
- [ ] Implement metrics calculation (`evaluate/evaluate.py`)
- [ ] Implement Monte Carlo dropout (`evaluate/monte_carlo.py`)
- [ ] Implement SHAP explainability (`interpret/compute_shap.py`)
- [ ] Test evaluation pipeline

### Deployment
- [ ] Implement SavedModel export (`deployment/export_savedmodel.py`)
- [ ] Implement Vertex AI upload (`deployment/vertex_upload.py`)
- [ ] Test deployment workflow

---

## Timeline Estimate

- **Phase 1 (Environment)**: 1-2 hours
- **Phase 2 (Structure)**: 1 hour
- **Phase 3 (Data Pipeline)**: 4-6 hours
- **Phase 4 (Training)**: 8-12 hours
- **Phase 5 (Integration)**: 2-4 hours

**Total**: ~16-25 hours of development time

---

## Success Criteria

- ✅ GPU acceleration working (Metal device visible)
- ✅ Data loads successfully from BigQuery
- ✅ Model trains on M2 Max GPU
- ✅ Training completes faster than CPU-only
- ✅ SavedModel exports correctly
- ✅ Model uploads to Vertex AI successfully

---

## Next Steps

1. **Verify Environment**: Run GPU test script
2. **Create Directory Structure**: Set up neural-pipeline folders
3. **Implement Data Loader**: Start with BigQuery → TensorFlow pipeline
4. **Build First Model**: Simple LSTM for 1M horizon
5. **Test Training**: Small dataset, verify GPU usage
6. **Iterate**: Expand to full pipeline

---

## Notes

- **Separate from BQML**: Mac training is for neural pipeline, not replacing BQML DART model
- **Complementary**: Both approaches can coexist and serve different purposes
- **Priority**: BQML DART model is ready to train now; Mac training is future enhancement
- **Resource**: M2 Max GPU is powerful but single device - optimize batch sizes accordingly

