---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Naming Structure Audit Report

**Date**: 2025-11-14  
**Purpose**: Verify compliance with new naming convention before fixes

## Naming Convention Rules

### Training Tables:
- Pattern: `zl_training_{surface}_allhistory_{horizon}`
- `surface`: `prod` or `full`
- `horizon`: `1w`, `1m`, `3m`, `6m`, `12m`
- Example: `zl_training_prod_allhistory_1m`

### Raw Intelligence Tables:
- Pattern: `{category}_{source_name}`
- Categories: `commodity_`, `shipping_`, `policy_`, `trade_`, `macro_`, `news_`
- Example: `commodity_soybean_oil_prices`

### Model Files:
- Pattern: `Models/local/horizon_{h}/{surface}/{family}/{model}_v{ver}/`
- Example: `Models/local/horizon_1m/prod/baselines/lightgbm_dart_v001/`

## Audit Results

### ✅ CORRECT NAMING:
- Training tables: All use `zl_training_{surface}_allhistory_{horizon}`
- Regime tables: `regime_calendar`, `regime_weights`
- Raw intelligence: Most tables follow `{category}_{source}` pattern

### ⚠️ ISSUES FOUND:
1. Missing table: `raw_intelligence.commodity_soybean_oil_prices`
2. Import path: `tree_models.py` needs `src/` added to sys.path
3. Full surface exports: Tables exist but not exported locally

### ❌ OLD PATTERNS TO AVOID:
- `production_training_data_*` (old training table names)
- `forecasting_data_warehouse.*` (old dataset, migrating to `raw_intelligence`)
- `models_v4.production_*` (old location)

## Verification Checklist

- [x] Training tables use new naming
- [x] Raw intelligence tables use new naming (except missing soybean_oil_prices)
- [x] Training scripts reference new table names
- [x] Export script uses new naming
- [x] Model save paths use new structure
- [ ] Import paths correctly configured
- [ ] All raw intelligence tables migrated

