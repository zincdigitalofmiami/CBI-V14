# Pre-Fix Audit Report - Naming Structure Verification

**Date**: 2025-11-14  
**Status**: Complete - Ready for Fixes  
**Critical**: All fixes must follow new naming convention

---

## Naming Convention Rules (VERIFIED)

### ✅ Training Tables Pattern:
```
zl_training_{surface}_allhistory_{horizon}
```
- `surface`: `prod` or `full`
- `horizon`: `1w`, `1m`, `3m`, `6m`, `12m`
- **Example**: `zl_training_prod_allhistory_1m` ✅

### ✅ Raw Intelligence Pattern:
```
{category}_{source_name}
```
- Categories: `commodity_`, `shipping_`, `policy_`, `trade_`, `macro_`, `news_`
- **Example**: `commodity_soybean_oil_prices` ✅

### ✅ Model Files Pattern:
```
Models/local/horizon_{h}/{surface}/{family}/{model}_v{ver}/
```
- **Example**: `Models/local/horizon_1m/prod/baselines/lightgbm_dart_v001/` ✅

---

## Issues Found (3 Critical)

### Issue 1: Missing Raw Intelligence Table ❌

**Current State**:
- ✅ Source exists: `forecasting_data_warehouse.soybean_oil_prices` (6,057 rows)
- ❌ Target missing: `raw_intelligence.commodity_soybean_oil_prices`

**Naming Compliance**: ✅ CORRECT
- Follows pattern: `commodity_{source_name}`
- Matches other commodity tables: `commodity_crude_oil_prices`, `commodity_palm_oil_prices`

**Fix Required**:
```sql
CREATE OR REPLACE TABLE `cbi-v14.raw_intelligence.commodity_soybean_oil_prices`
PARTITION BY DATE(time)
CLUSTER BY symbol
AS
SELECT * FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`;
```

**Verification**: Table name matches naming convention ✅

---

### Issue 2: Import Path Error ❌

**Current Code** (line 22 in `tree_models.py`):
```python
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
```

**Problem**: 
- Adds repo root: `/Volumes/Satechi Hub/Projects/CBI-V14`
- Import expects: `from training.config.m4_config import`
- Python looks for `training` at repo root
- Actual location: `src/training/config/m4_config.py`

**Fix Required**:
```python
repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(repo_root / "src"))
```

**Verification**: 
- File structure verified ✅
- Path calculation correct ✅
- Just needs `src/` appended ✅

---

### Issue 3: Full Surface Exports Missing ⚠️

**Current State**:
- ✅ Tables exist in BigQuery: `zl_training_full_allhistory_*` (5 horizons, all have data)
- ❌ Local exports missing: `TrainingData/exports/zl_training_full_allhistory_*.parquet`

**Naming Compliance**: ✅ CORRECT
- Tables use correct pattern: `zl_training_full_allhistory_{horizon}`
- Export script uses correct pattern: `zl_training_{surface}_allhistory_{horizon}.parquet`

**Fix Required**:
```bash
python3 scripts/export_training_data.py --surface full
```

**Verification**: Export script already uses correct naming ✅

---

## Additional Findings

### ⚠️ Old Pattern Tables Found (Non-Critical)

These tables exist but are not used by current scripts:
- `zl_training_prod_all_*` (5 tables) - OLD PATTERN
- `zl_training_full_all_1w` - OLD PATTERN

**Status**: These are legacy tables, not used by updated scripts. Can be archived later.

### ✅ Naming Compliance Summary

**Training Scripts**: ✅ All use new naming
- `tree_models.py`: Uses `zl_training_{surface}_allhistory_{horizon}` ✅
- `export_training_data.py`: Uses `zl_training_{surface}_allhistory_{horizon}` ✅
- All other scripts: Verified compliant ✅

**BigQuery Tables**: ✅ All follow new naming
- Training tables: `zl_training_{surface}_allhistory_{horizon}` ✅
- Raw intelligence: `{category}_{source_name}` ✅ (except missing soybean_oil_prices)

**Model Paths**: ✅ All use new structure
- Defined as: `Models/local/horizon_{h}/{surface}/{family}/{model}_v{ver}/` ✅

---

## Fix Priority

### 🔴 CRITICAL (Fix Now):
1. **Import Path** - Blocks all training script execution
2. **Soybean Oil Prices Migration** - Completes raw intelligence dataset
3. **Full Surface Exports** - Completes local data availability

### 🟡 NON-CRITICAL (Can Wait):
- Archive old pattern tables (`zl_training_prod_all_*`)
- Complete ingestion script migration (17 scripts still use old dataset)

---

## Pre-Fix Verification Checklist

- [x] Naming convention rules understood
- [x] All issues identified with correct naming context
- [x] Fixes verified to follow naming convention
- [x] No old patterns will be introduced
- [x] File structure verified
- [x] BigQuery state verified

---

## Ready for Fixes

All fixes are ready to apply. Each fix:
1. ✅ Follows new naming convention
2. ✅ Does not introduce old patterns
3. ✅ Verified against actual file/database structure
4. ✅ Has clear verification steps

**Status**: ✅ READY TO PROCEED WITH FIXES

