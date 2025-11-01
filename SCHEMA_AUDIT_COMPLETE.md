# COMPLETE SCHEMA AUDIT - October 30, 2025

## CRITICAL DISCOVERY

### Actual Schema State:

| Table/View | Columns | Has Targets | Status |
|------------|---------|-------------|--------|
| `training_dataset_super_enriched` | **11** | ❌ NO | **REDUCED** - Only Big-8 features |
| `enhanced_features_automl` | **210** | ✅ YES | **COMPLETE** - All features + targets |
| `training_dataset_1m_filtered` | **209** | ✅ YES | **BROKEN VIEW** - References wrong table |
| `training_dataset_3m_filtered` | **209** | ✅ YES | **BROKEN VIEW** - References wrong table |
| `training_dataset_6m_filtered` | **209** | ✅ YES | **BROKEN VIEW** - References wrong table |

### Root Cause Identified:

1. **Models were trained on filtered views** (`training_dataset_1m_filtered`, etc.) which had 209 columns
2. **Filtered views reference** `training_dataset_super_enriched` 
3. **training_dataset_super_enriched was REDUCED** to only 11 columns (Big-8 features only)
4. **Views are broken** - they reference a table that doesn't have the features they expect
5. **enhanced_features_automl** has 210 columns (all features + targets) - THIS is the correct source!

### Solution Path:

**OPTION 1: Use enhanced_features_automl for predictions**
- Has all 209 feature columns + targets
- Can create predict_frame from this view
- Models likely trained from this or filtered views based on it

**OPTION 2: Fix filtered views to reference enhanced_features_automl**
- Update view definitions to use correct source
- Then create predict_frame from filtered views

**OPTION 3: Rebuild training_dataset_super_enriched**
- Restore all 209 columns from enhanced_features_automl
- This would fix all views automatically

### Recommendation:

**Use `enhanced_features_automl` as the prediction source** - it has everything we need:
- All 209 feature columns
- Target columns (for reference)
- Latest data
- Complete schema

Then create predict_frame that:
- SELECTs from `enhanced_features_automl`
- EXCEPTs all target columns
- Gets latest date row

---

**AUDIT COMPLETE - Now proceeding with fix using enhanced_features_automl**

