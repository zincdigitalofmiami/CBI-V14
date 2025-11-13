# 🔍 CBI-V14 Training Status Report
**Generated**: November 6, 2025, 8:01 PM CST  
**Status**: ✅ **NO ACTIVE TRAINING JOBS**

---

## 📊 Executive Summary

**Current State**: All training jobs are **COMPLETE**. No active training pipelines running.

### Quick Status
- ✅ **BigQuery ML**: No active training jobs
- ✅ **Vertex AI AutoML**: No active training pipelines  
- ✅ **Most Recent Training**: `bqml_1m_v3` completed at 10:19 PM today (Nov 6)

---

## 🔨 BigQuery ML Models Status

### Production Models (Last Trained: Nov 4, 2025)

| Model | Created | Modified | Type | Status |
|-------|---------|----------|------|--------|
| `bqml_1w` | Nov 4, 5:25 PM | Nov 4, 5:25 PM | BOOSTED_TREE_REGRESSOR | ✅ Trained |
| `bqml_1m` | Nov 4, 5:29 PM | Nov 4, 5:29 PM | BOOSTED_TREE_REGRESSOR | ✅ Trained |
| `bqml_3m` | Nov 4, 5:36 PM | Nov 4, 5:36 PM | BOOSTED_TREE_REGRESSOR | ✅ Trained |
| `bqml_6m` | Nov 4, 5:41 PM | Nov 4, 5:41 PM | BOOSTED_TREE_REGRESSOR | ✅ Trained |

**Note**: Production models have **not been retrained** since Nov 4. According to audit reports, they were previously trained on Sep 10, 2025, then retrained on Nov 4.

### Experimental/Version Models

| Model | Created | Modified | Type | Status |
|-------|---------|----------|------|--------|
| `bqml_1m_v2` | Nov 6, 5:23 PM | Nov 6, 5:23 PM | BOOSTED_TREE_REGRESSOR | ✅ Complete |
| `bqml_1m_v3` | Nov 6, 10:19 PM | Nov 6, 10:19 PM | BOOSTED_TREE_REGRESSOR | ✅ Complete |

**Details**:
- **v2**: Trained with 334 features, achieved **80.83% MAE improvement** (MAE: $0.23, R²: 0.9941)
- **v3**: Trained with 422 features using DART booster + extreme L1 regularization (L1=15.0)
  - Started: Nov 6, 4:12 PM
  - Completed: Nov 6, 10:19 PM (~6 hours)
  - Expected to show which of the amplified features matter most

---

## 🤖 Vertex AI AutoML Models Status

### Existing Trained Models (No Active Training)

| Model Name | Model ID | Created | Horizon |
|------------|----------|---------|---------|
| `cbi_v14_automl_pilot_1w` | 575258986094264320 | Oct 28, 5:05 PM | 1W |
| `soybean_oil_1m_model_FINAL_20251029_1147` | 274643710967283712 | Oct 29, 4:47 PM | 1M |
| `soybean_oil_3m_final_v14_20251029_0808` | 3157158578716934144 | Oct 29, 1:08 PM | 3M |
| `soybean_oil_6m_model_v14_20251028_1737` | 3788577320223113216 | Oct 28, 10:37 PM | 6M |

**Status**: ✅ All models trained and available  
**Performance** (from audit):
- 1W: MAE 0.26 vs BQML 0.30 (-13% improvement)
- 3M: MAE 0.58 vs BQML 0.66 (-12% improvement)  
- 6M: MAE 0.81 vs BQML 0.90 (-10% improvement)

**Note**: No active training pipelines found in last 30 days. All Vertex AI models are in completed state.

---

## 📈 Training History Summary

### Recent Training Activity

1. **Nov 6, 10:19 PM**: `bqml_1m_v3` training completed
   - Configuration: DART booster, L1=15.0, 422 features
   - Duration: ~6 hours

2. **Nov 6, 5:23 PM**: `bqml_1m_v2` training completed
   - Performance: MAE $0.23, R² 0.9941 (80.83% improvement)

3. **Nov 4, 5:25-5:41 PM**: Production models (`bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m`) retrained
   - Previous training: Sep 10, 2025

4. **Oct 28-29**: Vertex AI AutoML models trained
   - All 4 horizons (1W, 1M, 3M, 6M) completed

---

## 🚨 Active Jobs Check

### BigQuery Jobs
- ✅ **No active/running BigQuery jobs** found
- ✅ **No pending training jobs** detected

### Vertex AI Pipelines  
- ✅ **No active training pipelines** in last 30 days
- ✅ **No pending pipelines** detected

---

## 📋 Next Steps & Recommendations

### Immediate Actions
1. **Evaluate `bqml_1m_v3` performance** - Compare against v2 to determine if DART + extreme L1 regularization improved results
2. **Extract feature importance** from v3 to identify which of the 422 features were selected by L1 regularization
3. **Decide on production deployment** - Choose between v2 (proven 80% improvement) or v3 (if it beats v2)

### Retraining Schedule
- **Production models** (`bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m`) last trained Nov 4
- **Recommendation**: Retrain weekly or when significant data updates occur
- **Note**: Cloud Build retrain triggers are currently **disabled** (per audit report)

### Data Freshness
- Production training tables updated through **Nov 5, 2025** (per audit)
- Some missing columns identified: `rin_price_avg`, `biofuel_mandate_tier2`, `argentina_port_delay_idx`
- **Action**: Fix failed Cloud Scheduler ingest jobs (Yahoo auth, RIN backfill) before next retrain

---

## 🔗 Related Documentation

- `V3_TRAINING_STATUS.md` - Details on v3 training configuration
- `AUDIT_BQML_VERTEX_20251106.md` - Comprehensive audit of models and data
- `PRE_TRAINING_STATUS_READY_FOR_APPROVAL.md` - Pre-training assessment
- `FINAL_PRODUCTION_STATUS_NOV5.md` - Production system status

---

## ✅ Summary

**Current Status**: ✅ **ALL TRAINING COMPLETE**

- **BigQuery ML**: 6 models exist (4 production + 2 experimental)
- **Vertex AI**: 4 models exist (all horizons covered)
- **Active Training**: **NONE**
- **Most Recent**: `bqml_1m_v3` completed Nov 6, 10:19 PM

**Ready for**: Model evaluation, feature importance extraction, and production deployment decisions.

---

_Report generated automatically by Cursor AI assistant_






