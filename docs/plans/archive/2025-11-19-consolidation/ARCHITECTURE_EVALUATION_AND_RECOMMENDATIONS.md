---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Architecture Evaluation & Recommendations
**Date**: November 17, 2025  
**Status**: Strategic Review  
**Purpose**: Evaluate current "Local-First" architecture and propose improvements

---

## Current Architecture Analysis

### Current State: "Local-First" Architecture

```
BigQuery (Storage)
    ↓ Export to Parquet
Mac M4 (Training)
    ↓ Train Models Locally
Local Filesystem (Model Artifacts)
    ↓ Generate Predictions Locally
    ↓ Upload Predictions
BigQuery (Predictions)
    ↓ Read
Dashboard (Display)
```

**Strengths**:
- ✅ $0 cloud compute costs
- ✅ Full control over training process
- ✅ No vendor lock-in
- ✅ Privacy/security (data stays local during training)
- ✅ Fast iteration for experimentation

**Weaknesses**:
- ❌ Sequential training (60-70 models) = very slow
- ❌ Memory constraints (16GB) limit batch sizes and model complexity
- ❌ No model versioning/backup in cloud
- ❌ Manual export/upload workflow (error-prone)
- ❌ Can't leverage BigQuery's compute for preprocessing
- ❌ No distributed training capability
- ❌ Model artifacts only on one machine (single point of failure)

---

## Architecture Alternatives

### Option 1: Hybrid Cloud-Local (RECOMMENDED)

**Structure**:
```
BigQuery (Storage + Preprocessing)
    ↓ Export preprocessed Parquet
Mac M4 (Training - Experimentation)
    ↓ Train & Validate Locally
    ↓ Upload validated models to Cloud Storage
Google Cloud Storage (Model Artifacts - Versioned)
    ↓ Download for inference
Mac M4 (Inference - Daily)
    ↓ Generate Predictions
    ↓ Upload to BigQuery
BigQuery (Predictions)
    ↓ Read
Dashboard (Display)
```

**Benefits**:
- ✅ Keep $0 training costs (still local)
- ✅ Model versioning in cloud (backup, rollback capability)
- ✅ Use BigQuery for heavy preprocessing (joins, feature engineering)
- ✅ Faster iteration (preprocessing happens in BigQuery)
- ✅ Better separation: storage (BQ) → compute (local) → artifacts (GCS)
- ✅ Can share models across team members
- ✅ Disaster recovery (models backed up)

**Trade-offs**:
- ⚠️ Small GCS storage cost (~$0.02/GB/month for model artifacts)
- ⚠️ Need to set up GCS bucket and upload scripts

**Implementation**:
1. Create GCS bucket: `cbi-v14-models`
2. Add model upload to `src/training/utils/model_saver.py`
3. Use BigQuery for feature engineering (SQL views → export)
4. Keep training local, store artifacts in GCS

---

### Option 2: BigQuery ML for Baselines (Hybrid Training)

**Structure**:
```
BigQuery (Storage + BQML Training for Simple Models)
    ↓ Train LightGBM/XGBoost in BigQuery
BigQuery (BQML Models)
    ↓ Export model artifacts
Mac M4 (Neural Network Training - Complex Models)
    ↓ Train LSTM/Attention locally
Google Cloud Storage (All Model Artifacts)
    ↓ Ensemble locally or in BigQuery
BigQuery (Predictions)
```

**Benefits**:
- ✅ Parallel training (BQML can train multiple models simultaneously)
- ✅ No memory constraints for tree models
- ✅ Faster baseline training
- ✅ Still use local for complex neural models

**Trade-offs**:
- ⚠️ BQML costs (~$5-20 per model training)
- ⚠️ Two training pipelines to maintain
- ⚠️ Model format differences (BQML vs local)

**When to Use**: If you need to train many tree models quickly and cost is acceptable.

---

### Option 3: Fully Cloud (Vertex AI)

**Structure**:
```
BigQuery (Storage)
    ↓
Vertex AI (Training)
    ↓
Vertex AI Model Registry (Artifacts)
    ↓
Vertex AI Endpoints (Inference)
    ↓
BigQuery (Predictions)
```

**Benefits**:
- ✅ Parallel training (train all 60-70 models simultaneously)
- ✅ No memory constraints
- ✅ Auto-scaling
- ✅ Built-in MLOps (versioning, monitoring, A/B testing)

**Trade-offs**:
- ❌ High cost ($100-500+ per training run)
- ❌ Vendor lock-in
- ❌ Less control
- ❌ Overkill for current scale

**When to Use**: If you need to scale to 100+ models or have budget for cloud compute.

---

## Recommended Architecture: Enhanced Hybrid

### Core Principle: "Smart Hybrid"

**Use the right tool for each job**:
- **BigQuery**: Data storage, preprocessing, feature engineering (SQL is fast)
- **Mac M4**: Model training, experimentation, daily inference
- **Cloud Storage**: Model artifacts, versioning, backup
- **BigQuery**: Predictions storage, dashboard data

### Improved Workflow

```
1. DATA PREPROCESSING (BigQuery)
   - Feature engineering in SQL views
   - Regime assignments
   - Data quality checks
   - Export to Parquet (preprocessed, ready to train)

2. TRAINING (Mac M4)
   - Import preprocessed Parquet
   - Train models locally
   - Validate performance
   - Save to local + upload to GCS

3. MODEL REGISTRY (Google Cloud Storage)
   - Versioned model artifacts
   - Metadata (performance, features, hyperparameters)
   - Easy rollback if new model performs worse

4. INFERENCE (Mac M4 - Daily)
   - Download latest model from GCS (or use local cache)
   - Generate predictions
   - Upload to BigQuery

5. DASHBOARD (Vercel)
   - Read from BigQuery
   - Display predictions, metrics, signals
```

---

## Specific Improvements

### 1. Move Feature Engineering to BigQuery

**Current**: Export raw data → engineer features in Python  
**Better**: Engineer features in BigQuery SQL → export ready-to-train data

**Benefits**:
- ✅ Faster (BigQuery is optimized for joins/aggregations)
- ✅ Consistent (SQL is version-controlled)
- ✅ No memory issues (BigQuery handles large datasets)
- ✅ Can preview features before export

**Implementation**:
```sql
-- Create feature engineering view
CREATE OR REPLACE VIEW `training.vw_training_features_ready` AS
SELECT 
  date,
  -- Price features
  zl_price_current,
  zl_return_7d,
  zl_return_30d,
  -- Regime features (JOIN to regime_calendar)
  market_regime,
  training_weight,
  -- All other features...
FROM `training.zl_training_prod_allhistory_1m` t
JOIN `training.regime_calendar` r ON t.date = r.date
-- Export this view to Parquet
```

---

### 2. Add Model Versioning in Cloud Storage

**Current**: Models only on local filesystem  
**Better**: Upload validated models to GCS with versioning

**Structure**:
```
gs://cbi-v14-models/
  ├── lightgbm/
  │   ├── v001/ (MAPE: 0.8%, date: 2025-11-15)
  │   ├── v002/ (MAPE: 0.7%, date: 2025-11-17) ← current
  │   └── metadata.json
  ├── lstm/
  │   ├── v001/
  │   └── v002/
  └── ensemble/
      └── v001/
```

**Benefits**:
- ✅ Backup (models safe if Mac fails)
- ✅ Version control (can rollback bad models)
- ✅ Team sharing (others can use your models)
- ✅ Reproducibility (metadata tracks what was used)

**Implementation**:
```python
# In model_saver.py
def save_model_with_versioning(model, metrics, gcs_bucket='cbi-v14-models'):
    # Save locally
    local_path = save_model_local(model, metrics)
    
    # Upload to GCS
    gcs_path = f"gs://{gcs_bucket}/{model_name}/v{version}/"
    upload_to_gcs(local_path, gcs_path)
    
    # Save metadata
    save_metadata(gcs_path, metrics, hyperparameters)
```

---

### 3. Optimize Training Pipeline

**Current**: Sequential training (one model at a time)  
**Better**: Parallel training where possible + better scheduling

**Options**:
1. **Parallel Tree Models**: Train LightGBM and XGBoost simultaneously (different processes)
2. **Batch Training**: Group similar models, train in batches
3. **Priority Queue**: Train high-impact models first (1w, 1m horizons)

**Implementation**:
```python
# Train tree models in parallel
from multiprocessing import Process

def train_lightgbm():
    # Train LightGBM

def train_xgboost():
    # Train XGBoost

# Run in parallel
p1 = Process(target=train_lightgbm)
p2 = Process(target=train_xgboost)
p1.start()
p2.start()
p1.join()
p2.join()
```

---

### 4. Better Data Pipeline

**Current**: Export → Train → Upload (manual steps)  
**Better**: Automated pipeline with validation

**Pipeline**:
```python
# scripts/training_pipeline.py
def run_training_pipeline():
    # 1. Export from BigQuery (with validation)
    data = export_training_data(validate=True)
    
    # 2. Train models
    models = train_all_models(data)
    
    # 3. Validate performance
    validated = validate_models(models)
    
    # 4. Upload to GCS
    upload_models(validated)
    
    # 5. Generate predictions
    predictions = generate_predictions(validated)
    
    # 6. Upload to BigQuery
    upload_predictions(predictions)
```

---

## Cost Analysis

### Current Architecture
- **BigQuery Storage**: ~$20/month (data storage)
- **Cloud Compute**: $0 (local only)
- **Total**: ~$20/month

### Recommended Hybrid Architecture
- **BigQuery Storage**: ~$20/month (same)
- **BigQuery Compute**: ~$5/month (feature engineering queries)
- **GCS Model Storage**: ~$1/month (model artifacts, ~50GB)
- **Cloud Compute**: $0 (still local training)
- **Total**: ~$26/month (+$6/month)

**ROI**: $6/month for model versioning, backup, and faster preprocessing = excellent value

---

## Migration Path

### Phase 1: Add GCS Model Storage (1 day)
1. Create GCS bucket
2. Update `model_saver.py` to upload to GCS
3. Test upload/download workflow

### Phase 2: Move Feature Engineering to BigQuery (2-3 days)
1. Create SQL views for feature engineering
2. Update export script to use views
3. Validate feature consistency

### Phase 3: Optimize Training Pipeline (1-2 days)
1. Add parallel training for tree models
2. Implement priority queue
3. Add automated pipeline script

### Phase 4: Add Model Registry (1 day)
1. Create metadata tracking
2. Add version comparison tools
3. Implement rollback capability

---

## Recommendation

**Adopt Enhanced Hybrid Architecture**:
- ✅ Keep local training (maintains $0 compute cost)
- ✅ Add GCS for model artifacts (backup, versioning)
- ✅ Move feature engineering to BigQuery (faster, more reliable)
- ✅ Optimize training pipeline (parallel where possible)

**Why This Is Better**:
1. **Resilience**: Models backed up in cloud
2. **Speed**: BigQuery preprocessing is faster than Python
3. **Reliability**: Versioned models enable rollback
4. **Cost**: Only +$6/month for significant improvements
5. **Scalability**: Can add cloud training later if needed

**When to Revisit**:
- If you need to train 100+ models regularly → Consider BQML or Vertex AI
- If training time becomes bottleneck → Consider cloud training for some models
- If team grows → Cloud model registry becomes essential

---

## Conclusion

**Current architecture is good for cost control, but has limitations.**

**Recommended improvements** (minimal cost, high value):
1. Add GCS model storage (backup, versioning)
2. Move feature engineering to BigQuery (speed, reliability)
3. Optimize training pipeline (parallel where possible)

**This maintains your $0 training cost while adding resilience and speed.**



