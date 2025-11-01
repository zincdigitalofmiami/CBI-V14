# SCHEMA AUDIT - October 30, 2025

## CRITICAL FINDING: Training Dataset Mismatch

### `training_dataset_super_enriched` Actual Schema
- **Total Columns**: 11 (NOT 209 as expected!)
- **Rows**: 2,130 (2020-01-01 to 2025-10-30)
- **Target Columns**: 0 (NONE exist!)

**Actual Columns:**
1. `date`
2. `feature_vix_stress`
3. `feature_harvest_pace`
4. `feature_china_relations`
5. `feature_tariff_threat`
6. `feature_geopolitical_volatility`
7. `feature_biofuel_cascade`
8. `feature_hidden_correlation`
9. `feature_biofuel_ethanol`
10. `big8_composite_score`
11. (need to check 11th column)

### Models Were Trained On Different Dataset!

**Evidence:**
- Models expect 209 columns
- Current `training_dataset_super_enriched` has only 11 columns
- Models expect target columns but they don't exist
- Error: "Null values not allowed in transformations for target_1w"

**Hypothesis:**
- Models were trained on `enhanced_features_automl` VIEW (209 columns)
- OR models were trained on a different table that had all features + targets
- Current `training_dataset_super_enriched` is NOT the training source

### Next Steps:
1. Check `enhanced_features_automl` view schema
2. Check filtered views (`training_dataset_1m_filtered`, etc.)
3. Find which dataset/models were actually used for training
4. Use correct dataset for predictions

---

**AUDIT COMPLETE - Need to identify actual training source before proceeding**

