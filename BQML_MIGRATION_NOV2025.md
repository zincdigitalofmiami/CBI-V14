# BQML MIGRATION - NOVEMBER 1, 2025

## 🎯 DECISION: MIGRATE FROM VERTEX AI TO BIGQUERY ML

**Date:** November 1, 2025  
**Status:** ✅ APPROVED - Ready for Execution  
**Impact:** $180/month → $0/month | Zero Complexity | Zero Label Leakage

---

## 📊 MIGRATION SUMMARY

### From: Vertex AI AutoML
- **Models:** 4 AutoML Tabular models (1W, 1M, 3M, 6M)
- **Cost:** $415 training + $180/month endpoints
- **Issue:** Label leakage (targets as features)
- **Deployment:** Complex (endpoints, traffic splits, schema contracts)
- **Performance:** 1.98-2.68% MAPE

### To: BigQuery ML BOOSTED_TREE
- **Models:** 12 BQML models (4 horizons × 3 quantiles)
- **Cost:** $0/month (within free tier for 1.25K rows)
- **Advantage:** Zero label leakage (SQL enforces schema)
- **Deployment:** None (SQL `ML.PREDICT` only)
- **Performance:** 2.38-3.16% MAPE (historical - comparable)

---

## 🔍 WHY MIGRATE?

### Problem 1: Label Leakage in Vertex AI
**Issue:**  
Vertex AI AutoML models were trained with target columns as input features, causing:
- 1M model (274643710967283712) fails with NULL rejection errors
- Predictions require target columns to be present (impossible at inference time)
- Model fundamentally broken - cannot be fixed without retraining

**BQML Solution:**  
Explicit SQL schema prevents this entirely:
```sql
SELECT * EXCEPT(date, target_1w, target_1m, target_3m, target_6m)
FROM training_dataset_super_enriched
```

### Problem 2: Vertex AI Costs
**Current Costs:**
- Training: $415 (one-time, already spent)
- 1M Endpoint: $90/month (n1-standard-2, min_replica=1)
- 1W Endpoint: $90/month (n1-standard-2, min_replica=1)
- **Total: $180/month = $2,160/year**

**BQML Costs:**
- Training: $0 (within 10GB free tier)
- Predictions: $0 (within free tier for daily batch)
- **Total: $0/month**

**3-Year Savings: $6,480**

### Problem 3: Operational Complexity
**Vertex AI:**
- Endpoint management (deploy, undeploy, traffic splits)
- Schema contracts (210 columns, targets as None)
- Deployment failures (misconfigured traffic splits)
- Monitoring (endpoint health, model versions)

**BQML:**
- SQL queries only
- BigQuery enforces schema automatically
- No deployments
- No endpoints to monitor

---

## 📈 PERFORMANCE COMPARISON

### Historical BQML Performance (Previously Deleted Models):
| Horizon | MAE | R² | MAPE (est) | Status |
|---------|-----|-----|------------|--------|
| 1W | 1.58 | 0.96 | ~3.16% | Deleted (Oct 27) |
| 1M | 1.42 | 0.97 | ~2.84% | Deleted (Oct 27) |
| 3M | 1.26 | 0.97 | ~2.52% | Deleted (Oct 27) |
| 6M | 1.19 | 0.98 | ~2.38% | Deleted (Oct 27) |

### Vertex AI AutoML Performance (Current):
| Horizon | Model ID | MAPE | Status |
|---------|----------|------|--------|
| 1W | 575258986094264320 | 2.02% | ⚠️ Label leakage |
| 1M | 274643710967283712 | 1.98% | ❌ Broken (NULL rejection) |
| 3M | 3157158578716934144 | 2.68% | ⚠️ Label leakage |
| 6M | 3788577320223113216 | 2.51% | ⚠️ Label leakage |

**Verdict:** BQML performance is comparable or better, especially for 6M horizon.

---

## 🚀 EXECUTION PLAN

### Phase 1: Train 12 BQML Models (2-3 hours)
1. Create `features_1m_clean` view (exclude targets)
2. Train 3 models per horizon (q10, mean, q90)
3. Validate with `ML.EVALUATE`
4. **Cost:** $0
5. **Status:** ⏳ Ready to Execute

### Phase 2: BQML Batch Predictions (1 hour)
1. Create `1m_predictor_job_bqml.py`
2. Use `ML.PREDICT` for all 3 quantiles
3. Combine results, apply 1W gate blend
4. Write to `predictions_1m` table
5. **Status:** ⏳ To Create

### Phase 3: BQML Explainability (30 min)
1. Create `calculate_shap_drivers_bqml.py`
2. Use `ML.EXPLAIN_PREDICT` (Shapley values)
3. Join with `shap_business_labels.json`
4. Write to `shap_drivers` table
5. **Optional:** Add daily LLM summary ($11/month)
6. **Status:** ⏳ To Create

### Phase 4-14: Dashboard Integration
- Same as current plan in `FINAL_REVIEW_AND_EXECUTION_PLAN.md`
- No changes needed (dashboard reads from same BigQuery tables)

---

## 📋 FILES TO CREATE

### BigQuery SQL (12 training scripts):
- `bigquery_sql/create_features_clean.sql`
- `bigquery_sql/train_bqml_1w_mean.sql`
- `bigquery_sql/train_bqml_1w_q10.sql`
- `bigquery_sql/train_bqml_1w_q90.sql`
- (Repeat for 1M, 3M, 6M)

### Python Scripts:
- `scripts/train_all_bqml_models.py` - Execute all training SQL
- `scripts/validate_bqml_models.py` - Test predictions
- `scripts/export_bqml_feature_schema.py` - Export schema
- `scripts/1m_predictor_job_bqml.py` - Batch predictions
- `scripts/calculate_shap_drivers_bqml.py` - Explainability

### Config:
- `config/bqml_models_config.json` - Model metadata

---

## ✅ APPROVAL & NEXT STEPS

**Decision:** ✅ APPROVED by Kirk (November 1, 2025)

**Next Steps:**
1. Execute Phase 1 (train 12 BQML models)
2. Validate model performance
3. Create prediction and explainability scripts
4. Deploy to production (no deployment needed - SQL only!)

**Reference Plans:**
- Complete 14-phase plan: `FINAL_REVIEW_AND_EXECUTION_PLAN.md`
- Master training history: `MASTER_TRAINING_PLAN.md`

---

**Total Migration Time:** ~5 hours  
**Total Migration Cost:** $0  
**Annual Savings:** $2,160  
**Operational Simplification:** Massive (SQL only vs endpoint management)

**Status:** 🎯 READY TO EXECUTE

