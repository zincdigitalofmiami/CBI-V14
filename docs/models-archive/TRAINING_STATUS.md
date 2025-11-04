# Training Status Summary

## Current Status: READY FOR RETRAIN

**Last Updated:** November 2, 2025

### Leakage Fix Complete ✅

**Total Leakage Features Excluded: 11**
1. `crude_lead1_correlation`
2. `dxy_lead1_correlation`
3. `vix_lead1_correlation`
4. `palm_lead2_correlation`
5. `leadlag_zl_price`
6. `lead_signal_confidence`
7. `days_to_next_event`
8. `post_event_window` ⚠️ **NEWLY ADDED**
9. `event_impact_level` ⚠️ **NEWLY ADDED**
10. `event_vol_mult` ⚠️ **NEWLY ADDED**
11. `tradewar_event_vol_mult` ⚠️ **NEWLY ADDED**

### Model Training Configuration

- **Training Features:** 194 (205 total - 11 leakage)
- **Dashboard Features:** 205 (all features available in `predict_frame`)
- **Training Data:** Pre-2024 (train), 2024+ (test)
- **Models:** 4 BQML BOOSTED_TREE_REGRESSOR models

### Files Updated

- ✅ `bigquery_sql/train_bqml_1w_mean.sql`
- ✅ `bigquery_sql/train_bqml_1m_mean.sql`
- ✅ `bigquery_sql/train_bqml_3m_mean.sql`
- ✅ `bigquery_sql/train_bqml_6m_mean.sql`

### Previous Performance

- **MAPE with leakage:** 8.50% (artificially good due to future data)
- **Expected after fix:** Initial MAPE may be higher, but production will be reliable

### Next Steps

1. **Drop existing models:**
   ```sql
   DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_1w_mean`;
   DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_1m_mean`;
   DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_3m_mean`;
   DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_6m_mean`;
   ```

2. **Retrain all models:**
   ```bash
   python3 scripts/execute_phase_1.py
   ```

3. **Verify no leakage features in model:**
   ```sql
   SELECT feature
   FROM ML.GLOBAL_EXPLAIN(MODEL `cbi-v14.models_v4.bqml_1w_mean`)
   WHERE feature IN (
     'post_event_window',
     'event_impact_level',
     'event_vol_mult',
     'tradewar_event_vol_mult'
   );
   -- Should return 0 rows
   ```

4. **Run Phase 2 evaluation:**
   ```bash
   python3 scripts/audit_phase_1_training.py
   ```

### Notes

- All leakage features are excluded from training but remain in `predict_frame` for dashboard/SHAP
- Vertex AI dependencies removed from training pipeline
- Distribution drift detected (23.9% mean shift, 62% stddev shift) - this is expected given regime change



