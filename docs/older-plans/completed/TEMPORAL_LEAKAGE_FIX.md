# Temporal Leakage Fix - Action Plan

## 🔴 CRITICAL: 7 Forward-Looking Features Detected

### Leakage Features to Remove:

1. `crude_lead1_correlation` - Uses future crude price data
2. `dxy_lead1_correlation` - Uses future DXY index
3. `vix_lead1_correlation` - Uses future VIX
4. `palm_lead2_correlation` - Uses future palm price (2 periods ahead)
5. `leadlag_zl_price` - Forward-looking price correlation
6. `lead_signal_confidence` - Confidence based on future signals  
7. `days_to_next_event` - Knows future events

## 🎯 Fix Strategy

### Step 1: Update Training Views

**Files to modify:**
- Views: `train_1w`, `train_1m`, `train_3m`, `train_6m`
- Or source: `training_dataset_super_enriched`

**Action:** Exclude leakage features in `SELECT * EXCEPT(...)`

### Step 2: Retrain Models

Remove leakage features from all training SQL:
- `bigquery_sql/train_bqml_1w_mean.sql`
- `bigquery_sql/train_bqml_1m_mean.sql`
- `bigquery_sql/train_bqml_3m_mean.sql`
- `bigquery_sql/train_bqml_6m_mean.sql`

### Step 3: Re-evaluate

Run Phase 2 evaluation on test set without leakage features.

---

## 📊 Current Impact

- **Test MAPE:** 0.62% (good, but misleading)
- **Real-world MAPE:** Likely much higher (leakage features unavailable)
- **Root Cause:** Model depends on future data for predictions

---

## ✅ Expected Outcome After Fix

- Test MAPE may increase to 1-2% (more realistic)
- Production MAPE will match test MAPE (no leakage gap)
- Model will be truly production-ready



