# Gap Analysis & Completion Plan

## ❌ **MISSING FROM CURRENT EXECUTION PLAN**

### 1. **Forward Curve Integration**
**Status:** Route exists (`/api/v4/forward-curve`) but reads from wrong table
- **Current:** Reads from `predictions.monthly_vertex_predictions` (may be empty/old)
- **Needed:** Update to read from `agg_1m_latest` (our new materialized table)
- **Action:** Update `/api/v4/forward-curve/route.ts` to use `agg_1m_latest` with `future_day` as forward curve

### 2. **Rich Dashboard Addons (Promised Features)**
**Status:** Routes exist but not integrated into new architecture

#### Missing API Routes (need to update to use new data):
- ✅ `/api/v4/price-drivers` - EXISTS, needs SHAP integration
- ✅ `/api/v4/substitution-economics` - EXISTS, needs data source verification
- ✅ `/api/v4/risk-radar` - EXISTS, needs data source verification  
- ✅ `/api/v4/procurement-timing` - EXISTS, needs integration with new forecast
- ✅ `/api/v4/biofuel-mandates` - EXISTS, needs data source verification
- ❌ `/api/v4/currency-waterfall` - NEEDS CREATION
- ❌ `/api/forward-curve` - NEEDS UPDATE (to use `agg_1m_latest`)

#### Missing Components:
- SHAP driver calculation script (`scripts/calculate_shap_drivers.py`)
- SHAP integration with distilled model
- Breaking news AI summarizer (Gemini integration)
- React components for advanced visualizations (may exist, need verification)

### 3. **Training & Setup Gaps**

#### Model Lifecycle:
- ❌ **Retraining schedule**: Monthly retraining of distilled model
- ❌ **Model versioning**: Track model versions in BigQuery, rollback capability
- ❌ **A/B testing**: Compare new distilled model vs existing model
- ❌ **Model drift detection**: Automated drift checks, alert on degradation

#### Monitoring:
- ⚠️ **Basic monitoring exists** (Phase 7) but missing:
  - Model performance tracking (MAPE over time)
  - Feature drift detection
  - Prediction distribution monitoring
  - Gate blend effectiveness tracking

### 4. **Data Pipeline Completeness**
- ✅ 1W signal computation - COVERED
- ✅ 1M predictions - COVERED
- ⚠️ Forward curve - NEEDS UPDATE
- ❌ Breaking news pipeline - NOT COVERED (exists but may need refresh)
- ❌ Big-8 signals refresh - NOT COVERED (mentioned in IMPLEMENTATION_SCAFFOLD)

---

## ✅ **COMPLETION ADDITIONS NEEDED**

### **Phase 8: Forward Curve & Dashboard Integration (45min)**
1. **Update forward curve route:**
   - Modify `/app/api/v4/forward-curve/route.ts`
   - Read from `agg_1m_latest` instead of `monthly_vertex_predictions`
   - Map `future_day` to dates (D+1, D+2, ..., D+30)
   - Include q10/q90 bands in response

2. **Verify existing dashboard routes:**
   - Test `/api/v4/price-drivers` (may need SHAP integration)
   - Test `/api/v4/substitution-economics`
   - Test `/api/v4/risk-radar`
   - Test `/api/v4/procurement-timing` (update to use `agg_1m_latest`)
   - Create `/api/v4/currency-waterfall` if missing

### **Phase 9: SHAP Integration (1h)**
1. **SHAP calculation for distilled model:**
   - Script: `scripts/calculate_shap_drivers.py`
   - Use Vertex AI explanations (if available) or compute SHAP locally
   - Map technical features to business language
   - Store in BigQuery: `shap_drivers` table

2. **Update `/api/v4/price-drivers`:**
   - Read SHAP contributions from `shap_drivers`
   - Return top 10 drivers with dollar impacts
   - Format: "China demand up 12% → +$2.34/bu impact"

3. **Update `/api/explain`:**
   - Enhance with SHAP-derived explanations
   - Fallback to deterministic rules if SHAP unavailable

### **Phase 10: Model Lifecycle & Retraining (1h)**
1. **Monthly retraining workflow:**
   - Script: `scripts/retrain_distilled_quantile_1m.py`
   - Trigger: Cloud Scheduler (1st of month @ 2 AM)
   - Steps:
     - Train new distilled model with latest data
     - Validate performance (MAPE < 1.98%)
     - A/B test vs existing model (shadow mode)
     - If better, deploy; if worse, keep existing
     - Update model version in `predictions_1m` table

2. **Model versioning:**
   - Track versions in `predictions_1m.model_version`
   - Store model metadata: `model_versions` table
   - Columns: `version_id`, `model_id`, `trained_date`, `mape`, `r2`, `deployed_date`

3. **Drift detection:**
   - Script: `scripts/detect_model_drift.py`
   - Daily check: Feature distribution shifts, prediction distribution shifts
   - Alert if drift detected (trigger retraining early)

### **Phase 11: Breaking News & Big-8 Refresh (30min)**
1. **Breaking news pipeline:**
   - Verify `scripts/hourly_news.py` exists and works
   - Integrate Gemini AI summarizer (if not done)
   - Ensure `/api/v4/breaking-news` returns live data

2. **Big-8 signals refresh:**
   - Verify `scripts/refresh_features_pipeline.py` runs daily
   - Ensure Big-8 table stays fresh (within 24h)

---

## 📋 **UPDATED EXECUTION TIMELINE**

**Current Plan:** 3-3.5 hours (Phases 1-7)
**Complete Plan:** 5.5-6 hours (Phases 1-11)

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1 | Train Distilled Quantile Model | 1h | ✅ In Plan |
| 2 | Feature Assembly & Predict | 1.5h | ✅ In Plan |
| 3 | 1W Signal Computation | 45min | ✅ In Plan |
| 4 | Aggregation | 30min | ✅ In Plan |
| 5 | API Routes (Core) | 1h | ✅ In Plan |
| 6 | Dashboard Refactoring | 30min | ✅ In Plan |
| 7 | Monitoring & Alerts | 30min | ✅ In Plan |
| **8** | **Forward Curve & Dashboard Integration** | **45min** | **❌ MISSING** |
| **9** | **SHAP Integration** | **1h** | **❌ MISSING** |
| **10** | **Model Lifecycle & Retraining** | **1h** | **❌ MISSING** |
| **11** | **Breaking News & Big-8** | **30min** | **❌ MISSING** |

---

## 🎯 **DECISION: WHAT TO INCLUDE NOW?**

### **Option A: Minimal Go-Live (Current Plan)**
- ✅ Core functionality (1M predictions, 1W signals, basic API)
- ⚠️ Forward curve updated (quick fix)
- ❌ Advanced features deferred

**Time:** 3.5-4 hours (add Phase 8)
**Risk:** Low
**Go-Live:** Today

### **Option B: Complete Go-Live (Recommended)**
- ✅ Everything in Option A
- ✅ Forward curve integration
- ✅ SHAP integration (core explainability)
- ⚠️ Model lifecycle (can be done post-launch)
- ⚠️ Advanced dashboard addons (can be incremental)

**Time:** 5-6 hours (add Phases 8-9)
**Risk:** Medium
**Go-Live:** Today/Early tomorrow

### **Option C: Full Feature Complete**
- ✅ Everything in Option B
- ✅ Model lifecycle & retraining
- ✅ All advanced dashboard addons
- ✅ Breaking news & Big-8 verified

**Time:** 6.5-7 hours
**Risk:** High (scope creep)
**Go-Live:** Tomorrow

---

## ✅ **RECOMMENDATION**

**Proceed with Option B** (Add Phases 8-9):
1. Forward curve is critical (users expect it)
2. SHAP explainability is core to value prop
3. Model lifecycle can be automated post-launch
4. Advanced addons can be incremental

**Defer to Post-Launch:**
- Phase 10: Model lifecycle (can be automated in week 1)
- Phase 11: Breaking news (verify existing pipeline works)
- Advanced dashboard addons (incremental enhancement)

