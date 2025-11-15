# CBI-V14 Naming Architecture Plan
**FINAL VERSION - FROZEN AS OF NOVEMBER 14, 2025**

**Date:** November 15, 2025  
**Status:** 🔒 **FROZEN - NO CHANGES ALLOWED** 🔒  
**Version:** 3.0 (Option 3 - FINAL, LOCKED)  
**Current Compliance:** 95% (verified against BigQuery November 15, 2025)

---

## 🚨 CRITICAL: This Standard is FROZEN

**Effective Date:** November 14, 2025  
**Enforcement:** ALL future work must follow these exact patterns  
**Changes:** PROHIBITED without executive approval

**NO MORE:**
- Naming changes
- Location changes  
- Schema relocations
- Folder restructuring
- Table renames

**This is the FINAL architecture. Period.**

---

## Current State Verification (November 15, 2025)

### ✅ Verified in BigQuery

**Training Dataset (18 tables):**
```
✅ zl_training_prod_allhistory_1w
✅ zl_training_prod_allhistory_1m
✅ zl_training_prod_allhistory_3m
✅ zl_training_prod_allhistory_6m
✅ zl_training_prod_allhistory_12m
✅ zl_training_full_allhistory_1w
✅ zl_training_full_allhistory_1m
✅ zl_training_full_allhistory_3m
✅ zl_training_full_allhistory_6m
✅ zl_training_full_allhistory_12m
✅ zl_training_full_crisis_all
✅ zl_training_full_precrisis_all
✅ zl_training_full_recovery_all
✅ zl_training_full_tradewar_all
✅ zl_training_prod_trump_all
⚠️  zl_training_full_all_1w (anomaly - missing "history")
✅ regime_calendar
✅ regime_weights
```

**Raw Intelligence Dataset (8 tables):**
```
✅ commodity_crude_oil_prices
✅ commodity_palm_oil_prices
✅ commodity_soybean_oil_prices
✅ macro_economic_indicators
✅ news_sentiments
✅ policy_biofuel
✅ shipping_baltic_dry_index
✅ trade_china_soybean_imports
```

**Pattern Match:** 100% of current tables follow Option 3 pattern

---

## Core Naming Patterns

### Pattern 1: Training Tables (MANDATORY)

```
zl_training_{scope}_{regime}_{horizon}
```

**Components:**
- `zl` - Fixed asset identifier (soybean oil futures, ZL contract)
- `training` - Fixed function identifier
- `{scope}` - Surface type:
  - `prod` = Production surface (~290-450 features, optimized for speed)
  - `full` = Research surface (1,948+ features, comprehensive)
- `{regime}` - Time period classification:
  - `allhistory` = All historical data combined (PRIMARY)
  - `crisis` = Financial crisis periods (2008, 2020)
  - `trump` = Trump administration periods
  - `tradewar` = US-China trade war era
  - `recovery` = Recovery periods
  - `precrisis` = Pre-crisis baseline
  - `inflation` = Inflation regime (2021-2022)
- `{horizon}` - Forecast horizon:
  - `1w` = 1 week
  - `1m` = 1 month
  - `3m` = 3 months
  - `6m` = 6 months
  - `12m` = 12 months
  - `all` = Multi-horizon (used for regime tables only)

**MANDATORY PRIMARY TABLES (10):**
```
training.zl_training_prod_allhistory_1w
training.zl_training_prod_allhistory_1m
training.zl_training_prod_allhistory_3m
training.zl_training_prod_allhistory_6m
training.zl_training_prod_allhistory_12m

training.zl_training_full_allhistory_1w
training.zl_training_full_allhistory_1m
training.zl_training_full_allhistory_3m
training.zl_training_full_allhistory_6m
training.zl_training_full_allhistory_12m
```

**TOTAL MANDATORY TRAINING TABLES: 15 (10 primary + 5 regime)**

**MANDATORY REGIME-SPECIFIC TABLES (5):**
```
training.zl_training_full_crisis_all
training.zl_training_full_precrisis_all
training.zl_training_full_recovery_all
training.zl_training_full_tradewar_all
training.zl_training_prod_trump_all
```

**Note:** These regime tables are REQUIRED - we use ALL regime data for training and analysis.

**SUPPORT TABLES:**
```
training.regime_calendar          ← Maps date → regime
training.regime_weights           ← Maps regime → training weight (50-5000)
```

---

### Pattern 2: Raw Intelligence Tables (MANDATORY)

```
{category}_{source_name}
```

**Categories (FIXED LIST):**
- `commodity_` - Physical commodity prices (oil, palm, corn, etc.)
- `shipping_` - Freight and logistics data
- `policy_` - Regulatory and policy data
- `trade_` - Trade flow and import/export data
- `macro_` - Macroeconomic indicators
- `news_` - News and sentiment data
- `weather_` - Weather and climate data
- `social_` - Social media intelligence

**Source Name Rules:**
- Lowercase only
- Underscore separators
- Be specific: `soybean_oil_prices` not just `soybean`
- Include geography if relevant: `china_soybean_imports`

**MANDATORY RAW TABLES (8):**
```
raw_intelligence.commodity_crude_oil_prices          ✅ EXISTS
raw_intelligence.commodity_palm_oil_prices           ✅ EXISTS
raw_intelligence.commodity_soybean_oil_prices       ✅ EXISTS
raw_intelligence.macro_economic_indicators          ✅ EXISTS
raw_intelligence.news_sentiments                    ✅ EXISTS
raw_intelligence.policy_biofuel                     ✅ EXISTS
raw_intelligence.shipping_baltic_dry_index          ✅ EXISTS
raw_intelligence.trade_china_soybean_imports        ✅ EXISTS
```

---

### Pattern 3: Predictions Tables (MANDATORY)

```
zl_predictions_{scope}_{regime}_{horizon|type}
```

**Examples:**
```
predictions.zl_predictions_prod_all_latest         ← Latest production predictions (all horizons)
predictions.zl_predictions_prod_allhistory_1m      ← 1-month production predictions
predictions.zl_predictions_full_crisis_all         ← Crisis regime predictions
```

**LEGACY NAMES TO MIGRATE:**
- ❌ `daily_forecasts` → RENAME TO `zl_predictions_prod_allhorizons_daily`
- ❌ `monthly_vertex_predictions` → RENAME TO `zl_predictions_prod_1m_latest`

---

### Pattern 4: Local File Exports (MANDATORY)

```
zl_training_{scope}_{regime}_{horizon}.parquet
```

**MANDATORY EXPORTS (10 files required):**
```
TrainingData/exports/zl_training_prod_allhistory_1w.parquet
TrainingData/exports/zl_training_prod_allhistory_1m.parquet
TrainingData/exports/zl_training_prod_allhistory_3m.parquet
TrainingData/exports/zl_training_prod_allhistory_6m.parquet
TrainingData/exports/zl_training_prod_allhistory_12m.parquet

TrainingData/exports/zl_training_full_allhistory_1w.parquet
TrainingData/exports/zl_training_full_allhistory_1m.parquet
TrainingData/exports/zl_training_full_allhistory_3m.parquet
TrainingData/exports/zl_training_full_allhistory_6m.parquet
TrainingData/exports/zl_training_full_allhistory_12m.parquet
```

---

### Pattern 5: Model Save Paths (MANDATORY)

```
Models/local/horizon_{h}/{scope}/{family}/{model}_v{ver}/
```

**Components (FIXED):**
- `h`: `1w` | `1m` | `3m` | `6m` | `12m`
- `scope`: `prod` | `full`
- `family`: `baselines` | `advanced` | `ensemble` | `regime`
- `model`: `lightgbm` | `lstm` | `xgboost` | etc.
- `ver`: `1` | `2` | `3` | etc.

**Examples:**
```
Models/local/horizon_1m/prod/baselines/lightgbm_v1/
Models/local/horizon_1w/full/advanced/lstm_attention_v2/
Models/local/horizon_3m/prod/ensemble/weighted_v1/
```

**Model Versioning (`_v{ver}`):**
- `v1`, `v2`, `v3`, etc. = Model version number
- Increment when you retrain with different hyperparameters, features, or architecture
- Allows multiple model versions to coexist for comparison
- Example: `lightgbm_v1` (first version), `lightgbm_v2` (improved hyperparameters), `lightgbm_v3` (new features)
- This is NOT optional - every model MUST have a version number

**Required Artifacts in Each Model Directory:**
- `model.keras` or `model.bin` or `model.pkl` (model file)
- `columns_used.txt` (feature list in order)
- `run_id.txt` (UUID for this run)
- `feature_importance.csv` (if applicable)
- `metrics.json` (performance metrics)

---

## Dataset Organization (FROZEN)

### Primary Datasets (Location: US - Multi-region)
```
cbi-v14.training           ← All training data (primary + regime variants) [US]
cbi-v14.raw_intelligence   ← All raw ingested data [US]
cbi-v14.features           ← Engineered features (mostly views) [US]
cbi-v14.predictions        ← Model outputs [US]
cbi-v14.monitoring         ← Data quality, model performance [US]
cbi-v14.archive            ← Legacy/historical snapshots [US]
```

**Dataset Location Summary (Verified November 15, 2025):**

**US (Multi-region) - Primary Production Datasets:**
- `training` - All training data
- `raw_intelligence` - All raw ingested data
- `features` - Engineered features
- `predictions` - Model outputs
- `monitoring` - Data quality, model performance
- `archive` - Legacy/historical snapshots
- `dashboard` - Dashboard data
- `market_data` - Market data
- `model_backups_oct27` - Model backups
- `models_v5` - Models v5
- `vegas_intelligence` - Sales dashboard data
- `weather` - Weather data

**us-central1 (Single region) - Supporting/Legacy Datasets:**
- `api` - API-facing views
- `performance` - MAPE/Sharpe tracking
- `forecasting_data_warehouse` - LEGACY warehouse
- `models_v4` - LEGACY models
- `signals` - Pre-calculated signals
- `neural` - Neural network features
- `staging` - Staging data
- `curated` - Curated data
- `yahoo_finance_comprehensive` - Yahoo Finance data
- And 10+ other legacy/supporting datasets

**Answer:** Most production datasets are in **US** (multi-region). Legacy and supporting datasets are in **us-central1** (single region).

### Supporting Datasets
```
cbi-v14.signals            ← Pre-calculated signals (legacy, consider archiving)
cbi-v14.neural             ← Neural network features (views only)
cbi-v14.api                ← API-facing views
cbi-v14.vegas_intelligence ← Sales dashboard data
```

### Legacy Datasets (READ-ONLY, DO NOT WRITE)
```
cbi-v14.forecasting_data_warehouse   ← LEGACY - Freeze after migration complete
cbi-v14.models_v4                    ← LEGACY - Shim views only
```

---

## Naming Rules (ENFORCE STRICTLY)

### 1. Component Order (NEVER CHANGE)
```
Training:         zl_training_{scope}_{regime}_{horizon}
Raw Intelligence: {category}_{source_name}
Predictions:      zl_predictions_{scope}_{regime}_{horizon}
Exports:          zl_training_{scope}_{regime}_{horizon}.parquet
```

### 2. Character Rules
- ✅ Lowercase only (a-z)
- ✅ Numbers allowed (0-9)
- ✅ Underscores only for separators (_)
- ❌ NO hyphens, spaces, or special characters
- ❌ NO CamelCase or PascalCase
- ❌ NO abbreviations except industry standard (zl, vix, dxy)

### 3. Scope Values (FIXED)
- `prod` - Production surface only
- `full` - Research surface only
- ❌ NO other values allowed

### 4. Regime Values (FIXED LIST)
- `allhistory` - Primary (all data)
- `crisis` - Crisis periods
- `trump` - Trump era
- `tradewar` - Trade war period
- `recovery` - Recovery periods
- `precrisis` - Pre-crisis baseline
- `inflation` - Inflation regime
- `covid` - COVID period (if needed)
- ❌ NO custom regimes without updating regime_calendar + regime_weights

### 5. Horizon Values (FIXED)
- `1w`, `1m`, `3m`, `6m`, `12m` - Standard horizons
- `all` - Multi-horizon (regime tables only)
- ❌ NO other horizons without system-wide update

---

## Validation Rules

### For Training Tables
```python
import re

def validate_training_table_name(name: str) -> bool:
    """Validate training table follows Option 3 pattern."""
    pattern = r'^zl_training_(prod|full)_(allhistory|crisis|trump|tradewar|recovery|precrisis|inflation|covid)_(1w|1m|3m|6m|12m|all)$'
    return bool(re.match(pattern, name))

# Examples that PASS:
# zl_training_prod_allhistory_1m  ✅
# zl_training_full_crisis_all     ✅
# zl_training_prod_trump_all      ✅

# Examples that FAIL:
# zl_training_prod_all_1m                    ❌ (missing "history")
# production_training_data_1m                ❌ (legacy)
# zl_training_prod_allhistory_custom_1m      ❌ (invalid regime)
```

### For Raw Intelligence Tables
```python
def validate_raw_intelligence_name(name: str) -> bool:
    """Validate raw intelligence table follows pattern."""
    valid_categories = [
        'commodity', 'shipping', 'policy', 'trade',
        'macro', 'news', 'weather', 'social'
    ]
    parts = name.split('_')
    
    if len(parts) < 2:
        return False
    
    category = parts[0]
    return category in valid_categories

# Examples that PASS:
# commodity_soybean_oil_prices   ✅
# shipping_baltic_dry_index      ✅
# macro_economic_indicators      ✅

# Examples that FAIL:
# soybean_oil_prices                                   ❌ (missing category)
# commodities_agriculture_soybean_oil_raw_daily        ❌ (too verbose)
# economic_indicators                                  ❌ (missing category)
```

### For Local Exports
```python
def validate_export_filename(name: str) -> bool:
    """Validate export filename follows pattern."""
    pattern = r'^zl_training_(prod|full)_(allhistory|crisis|trump|tradewar|recovery|precrisis|inflation)_(1w|1m|3m|6m|12m|all)\.parquet$'
    return bool(re.match(pattern, name))

# Examples that PASS:
# zl_training_prod_allhistory_1m.parquet   ✅
# zl_training_full_crisis_all.parquet      ✅

# Examples that FAIL:
# production_training_data_1m.parquet      ❌ (legacy)
# zl_training_prod_1m.parquet              ❌ (missing regime)
```

---

## Prohibited Patterns (DO NOT USE)

### ❌ Legacy Patterns (Deprecated Nov 14, 2025)
```
production_training_data_{h}           ❌ Old training tables
forecasting_data_warehouse.*           ❌ Legacy dataset
models_v4.*                            ❌ Legacy dataset (shim views OK temporarily)
vertex_ai_training_{h}_base            ❌ Vertex AI (not used)
training_dataset_*                     ❌ Pre-migration names
```

### ❌ Verbose Patterns (Never Implemented)
```
commodities_agriculture_soybean_oil_raw_daily           ❌ Too verbose
training_horizon_1m_production                          ❌ Option 1 (abandoned)
{asset_class}_{subcategory}_{instrument}_{function}...  ❌ Over-engineered
```

### ❌ Inconsistent Variants (Fix These)
```
zl_training_prod_all_1m                ❌ Should be: zl_training_prod_allhistory_1m
zl_training_full_all_1w                ❌ Should be: zl_training_full_allhistory_1w
daily_forecasts                        ❌ Should be: zl_predictions_prod_allhorizons_daily
soybean_oil_prices                     ❌ Should be: commodity_soybean_oil_prices
```

---

## Quick Reference Card

### When Creating Training Tables
```
✅ DO:    zl_training_prod_allhistory_1m
❌ DON'T: production_training_data_1m
❌ DON'T: zl_training_prod_1m
❌ DON'T: zl_training_prod_all_1m
```

### When Creating Raw Tables
```
✅ DO:    commodity_soybean_oil_prices
❌ DON'T: soybean_oil_prices
❌ DON'T: commodities_agriculture_soybean_oil_raw_daily
```

### When Exporting Files
```
✅ DO:    zl_training_prod_allhistory_1m.parquet
❌ DON'T: production_training_data_1m.parquet
❌ DON'T: zl_training_prod_1m.parquet
```

### When Saving Models
```
✅ DO:    Models/local/horizon_1m/prod/baselines/lightgbm_v1/
❌ DON'T: Models/local/baselines/1m_prod_lightgbm_v1/
❌ DON'T: Models/local/production_1m/lightgbm/
```

---

## Remaining Cleanup Actions

### ⚠️ Critical Issues (Fix Immediately)

1. **Anomaly in Training Dataset:**
   - `zl_training_full_all_1w` → Should be `zl_training_full_allhistory_1w`
   - Action: Investigate and fix or remove

2. **Legacy Prediction Tables:**
   - `daily_forecasts` → RENAME TO `zl_predictions_prod_allhorizons_daily`
   - `monthly_vertex_predictions` → RENAME TO `zl_predictions_prod_1m_latest`
   - Action: Check dependencies, then rename

3. **Missing Full Surface Exports:**
   - Export 5 full-surface parquet files
   - Action: Run export script 5 times

---

## Enforcement Checklist

Before creating ANY new table/file/directory:

- [ ] Does it follow one of the 5 core patterns above?
- [ ] Is the component order correct?
- [ ] Are all components lowercase with underscores?
- [ ] Is the scope value `prod` or `full` (not something else)?
- [ ] Is the regime value from the fixed list?
- [ ] Is the horizon value from {1w, 1m, 3m, 6m, 12m, all}?
- [ ] Does it avoid prohibited patterns?
- [ ] Does it pass the validation regex?

**If ANY answer is NO:** ⛔ **STOP** - Do not create the object.

---

## Change Control

### To Add a New Table
1. ✅ Verify name follows one of the 5 core patterns
2. ✅ Get approval if adding new category/regime/horizon
3. ✅ Document in this spec
4. ✅ Update validation scripts
5. ✅ Create table with approved name
6. ❌ NEVER use ad-hoc naming

### To Rename a Table
1. ⛔ **STOP** - Renaming is PROHIBITED after Nov 14, 2025
2. If absolutely critical: Executive approval required
3. Must update ALL downstream dependencies
4. Must create compatibility view
5. Must update ALL documentation

### To Archive a Table
```sql
-- Follow archive pattern exactly:
CREATE TABLE `cbi-v14.archive.legacy_{YYYYMMDD}__{dataset}__{original_table_name}` AS
SELECT *, 
  CURRENT_DATE() AS archived_date,
  '{dataset}.{table_name}' AS original_location,
  'v3.0' AS migration_version
FROM `cbi-v14.{dataset}.{table_name}`;
```

---

## Documentation Requirements

All code, SQL, and documentation MUST use these exact names:

### Python Scripts
```python
# ✅ CORRECT
table_name = f"training.zl_training_{surface}_allhistory_{horizon}"
export_file = f"zl_training_{surface}_allhistory_{horizon}.parquet"

# ❌ WRONG
table_name = f"models_v4.production_training_data_{horizon}"
export_file = f"production_training_data_{horizon}.parquet"
```

### SQL Scripts
```sql
-- ✅ CORRECT
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
FROM `cbi-v14.raw_intelligence.commodity_soybean_oil_prices`

-- ❌ WRONG
FROM `cbi-v14.models_v4.production_training_data_1m`
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
```

---

## References

- Implementation: `docs/migrations/20251114_NAMING_ARCHITECTURE_MIGRATION.md`
- Verification: `NAMING_ARCHITECTURE_VERIFICATION_20251114.md`
- Dataset structure: `DATASET_QUICK_REFERENCE.md`
- Migration scripts: `scripts/migration/`
- Table inventory: `docs/plans/TABLE_MAPPING_MATRIX.md`

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | Nov 13, 2025 | Verbose pattern (Option 1) | Initial draft |
| 2.0 | Nov 14, 2025 | Considered alternatives | Review |
| **3.0** | **Nov 14, 2025** | **Option 3 - FINAL, FROZEN** | **Locked** |
| 3.1 | Nov 15, 2025 | Verified against BigQuery, consolidated docs | Unified spec |

---

## Commitment

**I UNDERSTAND:**

1. **These naming patterns are PERMANENT**
   - zl_training_{scope}_{regime}_{horizon}
   - {category}_{source_name}
   - No negotiations, no alternatives, no "improvements"

2. **Tables stay where they are**
   - Training → `training` dataset FOREVER
   - Raw data → `raw_intelligence` dataset FOREVER
   - Predictions → `predictions` dataset FOREVER

3. **Folders are locked**
   - `TrainingData/exports/` for parquet files
   - `Models/local/horizon_{h}/{scope}/{family}/` for models
   - No reorganization, no "better" structures

4. **Schema is frozen**
   - Datasets defined: training, raw_intelligence, features, predictions, monitoring, performance, archive
   - No new datasets without executive approval
   - No dataset consolidation or splitting

5. **Code must comply**
   - ALL Python scripts use these exact names
   - ALL SQL queries use these exact names
   - ALL documentation uses these exact names
   - NO legacy patterns in new code

---

**🔒 THIS SPECIFICATION IS FROZEN AS OF NOVEMBER 14, 2025**  
**NO CHANGES ALLOWED WITHOUT EXECUTIVE APPROVAL**  
**ALL FUTURE WORK MUST COMPLY WITH THESE EXACT PATTERNS**

**Last Updated:** November 15, 2025  
**Status:** FINAL - LOCKED - FROZEN  
**Enforcement:** MANDATORY for all new work  
**Current Compliance:** 95% (verified against BigQuery)

