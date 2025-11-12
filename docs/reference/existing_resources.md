# Existing Vertex AI Resources

**Last Updated:** November 7, 2025  
**Status:** Reference Documentation

---

## Existing Models

### 1M Horizon Model
- **Model ID:** `274643710967283712`
- **Display Name:** `soybean_oil_1m_model_FINAL_20251029_1147`
- **Created:** October 29, 2025
- **Full Name:** `projects/1065708057795/locations/us-central1/models/274643710967283712`

### 3M Horizon Model
- **Model ID:** `3157158578716934144`
- **Display Name:** `soybean_oil_3m_final_v14_20251029_0808`
- **Created:** October 29, 2025
- **Full Name:** `projects/1065708057795/locations/us-central1/models/3157158578716934144`

### 6M Horizon Model
- **Model ID:** `3788577320223113216`
- **Display Name:** `soybean_oil_6m_model_v14_20251028_1737`
- **Created:** October 28, 2025
- **Full Name:** `projects/1065708057795/locations/us-central1/models/3788577320223113216`

### 1W Horizon Model
- **Model ID:** `575258986094264320`
- **Display Name:** `cbi_v14_automl_pilot_1w`
- **Created:** October 28, 2025
- **Full Name:** `projects/1065708057795/locations/us-central1/models/575258986094264320`

---

## Existing Datasets (from Console)

Based on Google Cloud Console screenshot, the following datasets exist:
- `_20251029_1148`
- `et_20251029_1146`
- `_20251029_0808`
- `e_20251028_1743`
- `_1m_20251028_1741`
- `_3m_20251028_1737`
- `_1m_20251028_1737`
- `_6m_20251028_1737`
- `_1m_20251028_1735`
- `_3m_20251028_1735`

**Note:** These appear to be training datasets from previous Vertex AI AutoML runs (October 28-29, 2025).

---

## Naming Convention Analysis

### Current Naming (Existing Resources)
- ❌ Uses date suffixes (`_20251029_1147`)
- ❌ Uses version suffixes (`_FINAL`, `_v14`)
- ❌ Inconsistent patterns
- ❌ Doesn't follow "CBI V14 Vertex" naming convention

### Target Naming (New Resources)
- ✅ `CBI V14 Vertex – AutoML 1M`
- ✅ `CBI V14 Vertex – AutoML 3M`
- ✅ `CBI V14 Vertex – AutoML 6M`
- ✅ `CBI V14 Vertex – AutoML 12M`

---

## Recommendations

### 1. Keep Existing Models for Reference
- These models can serve as baselines for comparison
- Document their performance metrics
- Use them to validate improvements in new models

### 2. Archive Old Datasets
- Old datasets from October can be archived or deleted if not needed
- New datasets will follow clean naming: `training_1m`, `training_3m`, etc.

### 3. Create New Resources with Clean Naming
- All new Vertex AI resources will follow `CLEAN_WORKSPACE_ORGANIZATION_PLAN.md`
- No date suffixes, no version suffixes
- Consistent "CBI V14 Vertex" prefix

### 4. Model ID Mapping
For backward compatibility, document the mapping:
```
Old Model IDs → New Model Names
274643710967283712 → CBI V14 Vertex – AutoML 1M (new)
3157158578716934144 → CBI V14 Vertex – AutoML 3M (new)
3788577320223113216 → CBI V14 Vertex – AutoML 6M (new)
575258986094264320 → CBI V14 Vertex – AutoML 1W (reference only)
```

---

## Next Steps

1. ✅ Document existing resources (this file)
2. ⏳ Create new training datasets with clean naming
3. ⏳ Train new models following clean workspace principles
4. ⏳ Compare new model performance to existing models
5. ⏳ Archive or delete old datasets if not needed

---

**Reference:** See `CLEAN_WORKSPACE_ORGANIZATION_PLAN.md` for complete naming conventions.

