# ANSWER: Automated Pattern Discovery System

## Your Question
> "When the neural net finds obscure connections, how will this system record this information and observation and automatically go after more data like it in efforts to 'do deeper'?"

## The Answer: Self-Learning Loop ♻️

### 1. **Model Explains Itself** 🔍
After training, BigQuery ML extracts SHAP values showing which features matter most.
```sql
-- Example: "biofuel_cascade" ranks #3 with high SHAP value (unexpected!)
ML.EXPLAIN_PREDICT(MODEL zl_dnn_6m_v1, ...)
```

### 2. **System Records Discovery** 📝
High-importance obscure features get logged to `models.pattern_discoveries`:
```
Pattern: "biofuel_cascade"
Strength: 0.89
Hypothesis: "EPA mandates + crush margins + palm price = strong predictor"
Status: "pending_data_discovery"
```

### 3. **System Finds Similar Data** 🔎
Query `feature_metadata` registry for related sources:
```
Search: "biofuel" OR "renewable" OR "policy"
Found: 
  ✅ EPA RIN prices (already have)
  ❌ CA LCFS credits (missing)
  ❌ EU biodiesel mandates (missing)
```

### 4. **System Auto-Acquires Data** 🤖
For each missing source with `auto_acquire_enabled=TRUE`:
```python
# Fetch CA LCFS prices from API
data = fetch_from_api(feature_metadata.api_endpoint)
load_to_staging(data)
create_features(data)  # e.g., lcfs_price, lcfs_rin_spread
```

### 5. **System Expands Training** 📈
Add new features to training dataset:
```
Before: 159 features
After: 162 features (+3 LCFS features)
```

### 6. **System Tests & Validates** ⚖️
A/B test old vs new:
```
Model A (159 features): 4.5% MAPE
Model B (162 features): 4.2% MAPE  ← WINNER! 
```

### 7. **System Deploys or Rejects** ✅
If improvement > 2%: Deploy & log success  
If worse: Reject & try different sources

### 8. **Loop Repeats Forever** ∞
Next cycle discovers patterns in the NEW features...

---

## Current Status

**✅ We Have:**
- Working training dataset (1,251 rows × 159 features)
- Feature metadata registry (29 features)
- Pattern discovery scripts (need updating)

**❌ We Need:**
- Explainability extraction (NEW)
- Pattern discoveries table (NEW)
- Similar-data-finder (NEW)
- Auto-acquisition framework (NEW)
- A/B testing orchestrator (NEW)

**🔧 Need Fixing:**
- 4 broken pattern views (reference old dataset names)

---

## Next Steps

**Phase 1 (This Week):**
1. Fix 4 broken views
2. Extract SHAP values from trained models
3. Create pattern_discoveries table

**Phase 2 (Week 2):**
4. Build pattern analyzer
5. Enhance feature_metadata with API endpoints
6. Test similar-data-finder

**Phase 3 (Weeks 3-4):**
7. Build auto-acquisition
8. A/B testing framework
9. Deploy full self-learning loop

---

**📄 Full Technical Details:** See `docs/SELF_LEARNING_SYSTEM_ARCHITECTURE.md`









