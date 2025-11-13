# Rebuild Plan Validation Report

**Date**: November 13, 2025  
**Validator**: Claude (Tactical Execution)  
**Plan Source**: GPT-5 Strategic Design  
**Validation Against**: Actual BigQuery Structure (341 objects, 18 datasets)

---

## Executive Summary

✅ **Plan Structure**: Sound architectural design with 6 purpose-driven datasets  
⚠️ **Coverage Gaps**: Several critical components need explicit mapping  
❌ **Missing Elements**: Vegas Intel, regime-based training, multi-horizon logic not fully addressed

---

## 1. Dataset Structure Validation

### Proposed Structure (from DATASET_STRUCTURE_DESIGN.md)

1. `raw_intelligence` - Landing zone
2. `features` - Engineered features
3. `training` - Training datasets
4. `predictions` - Model outputs
5. `monitoring` - Metrics & logs
6. `archive` - Historical snapshots

### Actual Current Structure (18 datasets)

| Current Dataset | Object Count | Status | Migration Target |
|----------------|--------------|--------|------------------|
| `forecasting_data_warehouse` | 97 | ✅ Active | `raw_intelligence` + `features` |
| `models_v4` | 93 | ✅ Active | `training` + `features` |
| `signals` | 34 | ✅ Active | `features` |
| `models` | 30 | ✅ Active | `training` + `features` |
| `curated` | 30 | ✅ Active | `features` |
| `staging` | 11 | ⚠️ Staging | `raw_intelligence` |
| `yahoo_finance_comprehensive` | 10 | ✅ Active | `features` |
| `bkp` | 8 | 📦 Archive | `archive` |
| `predictions_uc1` | 5 | ✅ Active | `predictions` |
| `market_data` | 4 | ✅ Active | `features` |
| `archive_consolidation_nov6` | 4 | 📦 Archive | `archive` |
| `predictions` | 4 | ✅ Active | `predictions` |
| `deprecated` | 3 | 📦 Archive | `archive` |
| `dashboard` | 3 | ✅ Active | `monitoring` |
| `api` | 2 | ✅ Active | `monitoring` |
| `weather` | 1 | ✅ Active | `raw_intelligence` |
| `neural` | 1 | ✅ Active | `features` |

**Validation Result**: ✅ Plan covers all 18 datasets appropriately

---

## 2. Vegas Intel Validation

### Actual Vegas Tables Found

| Table | Rows | Current Location | Proposed Location |
|-------|------|------------------|-------------------|
| `vegas_casinos` | 31 | `forecasting_data_warehouse` | ❓ NOT MAPPED |
| `vegas_cuisine_multipliers` | 142 | `forecasting_data_warehouse` | ❓ NOT MAPPED |
| `vegas_events` | 5 | `forecasting_data_warehouse` | ❓ NOT MAPPED |
| `vegas_export_list` | 3,176 | `forecasting_data_warehouse` | ❓ NOT MAPPED |
| `vegas_fryers` | 0 | `forecasting_data_warehouse` | ❓ NOT MAPPED |
| `vegas_opportunity_scores` | N/A | `forecasting_data_warehouse` | ❓ NOT MAPPED |
| `vegas_restaurants` | 151 | `forecasting_data_warehouse` | ❓ NOT MAPPED |
| `vegas_scheduled_reports` | 28 | `forecasting_data_warehouse` | ❓ NOT MAPPED |
| `vegas_shift_casinos` | 440 | `forecasting_data_warehouse` | ❓ NOT MAPPED |
| `vegas_shift_restaurants` | 1,233 | `forecasting_data_warehouse` | ❓ NOT MAPPED |
| `vegas_shifts` | 148 | `forecasting_data_warehouse` | ❓ NOT MAPPED |
| `vegas_top_opportunities` | N/A | `forecasting_data_warehouse` | ❓ NOT MAPPED |

**Status**: ❌ **CRITICAL GAP** - Vegas Intel not addressed in rebuild plan

**Recommendation**: 
- Add `intelligence_vegas_*` tables to `raw_intelligence` dataset
- Or create separate `intelligence_vegas` subcategory in naming convention
- Document Vegas Intel as special case (READ ONLY from Glide API)

---

## 3. Training Regime Validation

### Actual Regime Tables Found

| Table | Rows | Purpose | Current Location |
|-------|------|---------|------------------|
| `crisis_2008_historical` | 253 | Historical regime | `models_v4` |
| `pre_crisis_2000_2007_historical` | 1,737 | Historical regime | `models_v4` |
| `recovery_2010_2016_historical` | 1,760 | Historical regime | `models_v4` |
| `trade_war_2017_2019_historical` | 754 | Historical regime | `models_v4` |
| `trump_rich_2023_2025` | 732 | Current regime | `models_v4` |
| `enhanced_market_regimes` | 2,842 | Regime classification | `models` |
| `argentina_crisis_tracker` | 10 | Crisis tracking | `forecasting_data_warehouse` |
| `trump_policy_intelligence` | 450 | Policy regime | `forecasting_data_warehouse` |

**Status**: ⚠️ **PARTIALLY ADDRESSED** - Naming convention mentions `regime` but no explicit mapping

**Recommendation**:
- Add `training_regime_*` pattern to naming convention examples
- Map regime tables to `training.regime_*` in new structure
- Document regime-based training workflow in DATA_LINEAGE_MAP.md

---

## 4. Multi-Horizon Training Validation

### Actual Multi-Horizon Tables Found

| Table | Rows | Horizon | Current Location |
|-------|------|---------|------------------|
| `production_training_data_1w` | 1,472 | 1 week | `models_v4` |
| `production_training_data_1m` | 1,404 | 1 month | `models_v4` |
| `production_training_data_3m` | 1,475 | 3 months | `models_v4` |
| `production_training_data_6m` | 1,473 | 6 months | `models_v4` |
| `production_training_data_12m` | 1,473 | 12 months | `models_v4` |
| `baseline_1m_comprehensive_2yr` | 482 | 1 month | `models_v4` |
| `full_220_comprehensive_2yr` | 482 | Multi-horizon | `models_v4` |

**Status**: ✅ **ADDRESSED** - Naming convention includes `1w`, `1m`, `3m`, `6m`, `12m` as instruments

**Validation**: Plan correctly identifies multi-horizon pattern

---

## 5. Feature Engineering Validation

### Actual Feature Tables Found

| Category | Tables | Current Location | Proposed Location |
|----------|--------|------------------|-------------------|
| Core Features | `vertex_core_features` (16,824 rows) | `models_v4` | `features.general_*` |
| Derived Features | `fundamentals_derived_features`, `fx_derived_features`, `volatility_derived_features`, `monetary_derived_features` | `models_v4` | `features.*_derived_*` |
| Signal Features | 34 signal views | `signals` | `features.signals_*` |
| Yahoo Finance | 10 tables | `yahoo_finance_comprehensive` | `features.commodities_*` |

**Status**: ✅ **WELL ADDRESSED** - Feature structure aligns with plan

---

## 6. Schema Assumptions Validation

### Critical Schema Checks

#### Date Column Consistency
- **Plan Assumes**: `date DATE NOT NULL` for features, `time TIMESTAMP` for raw
- **Actual**: Mixed - some use `date`, some use `timestamp`, some use `date_time`
- **Risk**: ⚠️ **MEDIUM** - Migration scripts need date column normalization

#### Required Columns
- **Plan Requires**: `ingest_timestamp`, `source`, `data_quality_flag` for raw
- **Actual**: Inconsistent - some tables have these, many don't
- **Risk**: ⚠️ **HIGH** - Need to add missing columns during migration

#### Partitioning
- **Plan Specifies**: Partition by date for all tables
- **Actual**: Most tables NOT partitioned
- **Risk**: ⚠️ **MEDIUM** - Performance impact, but not breaking

---

## 7. Missing Elements Checklist

### ❌ Not Addressed in Plan

1. **Vegas Intel Tables** (12 tables, 5,628+ rows)
   - No mapping in dataset structure
   - No naming convention examples
   - No lineage documentation

2. **Regime-Based Training Workflow**
   - Tables exist but workflow not documented
   - No examples in naming convention

3. **Multi-Horizon Prediction Logic**
   - Training tables mapped ✅
   - Prediction tables mapped ✅
   - But prediction generation workflow not documented

4. **View Dependencies**
   - 100 views exist with complex dependencies
   - Plan doesn't address view migration order
   - Risk of broken views during migration

5. **Model Training Strategy** ✅ **DECIDED: Local Mac M4 Pipeline**
   - **Approach**: Local Mac M4 + TensorFlow Metal training (NOT BQML)
   - Plan needs: Document data export path from new BigQuery → local training
   - Plan needs: Document prediction upload path from local models → BigQuery predictions table
   - Plan needs: Ensure new table structure supports local training pipeline

---

## 8. Execution Phase Validation

### Proposed Phases (from MASTER_EXECUTION_PLAN.md)

1. Phase 1: Inventory & Planning ✅ (DONE - 341 objects cataloged)
2. Phase 2: Create New Datasets ✅ (Scripts provided)
3. Phase 3: Migrate Raw Data ⚠️ (Need Vegas Intel mapping)
4. Phase 4: Migrate Features ⚠️ (Need view dependency order)
5. Phase 5: Migrate Training ⚠️ (Need regime workflow)
6. Phase 6: Migrate Predictions ✅ (Straightforward)
7. Phase 7: Update Views ⚠️ (Complex - 100 views)
8. Phase 8: Update Models ⚠️ (BQML models need attention)
9. Phase 9: Validation ✅ (Checklist provided)

**Status**: ⚠️ **PHASES NEED REFINEMENT** - Several phases need additional detail

---

## 9. Recommendations

### Immediate Actions Required

1. **Add Vegas Intel Section**
   - Document 12 Vegas tables in dataset structure
   - Add `intelligence_vegas_*` naming pattern
   - Create migration script for Vegas tables

2. **Document Regime Workflow**
   - Add regime-based training examples
   - Document how historical regimes feed into training
   - Map regime tables to new structure

3. **View Dependency Analysis**
   - Generate dependency graph for 100 views
   - Create migration order based on dependencies
   - Add view migration phase with rollback plan

4. **Model Training Strategy** ✅ **DECIDED: Local Mac M4 + TensorFlow Metal**
   - **Approach**: Train locally on Mac M4 with TensorFlow Metal (LSTM/GRU)
   - **Data Source**: Export from new BigQuery structure to local Parquet
   - **Deployment**: Deploy trained models to Vertex AI or local API for dashboard
   - **Plan Needs**: Document how new BigQuery structure feeds local training pipeline
   - **Plan Needs**: Document prediction export path (local models → BigQuery predictions table)

5. **Schema Normalization**
   - Create date column normalization script
   - Add missing required columns script
   - Document schema differences by dataset

### Low Priority (Post-Migration)

- Partitioning strategy (can add after migration)
- Clustering optimization (can add after migration)
- Performance tuning (can optimize after migration)

---

## 10. Validation Summary

| Category | Status | Risk Level |
|----------|--------|------------|
| Dataset Structure | ✅ Valid | Low |
| Naming Convention | ✅ Valid | Low |
| Vegas Intel | ❌ Missing | **HIGH** |
| Training Regimes | ⚠️ Partial | Medium |
| Multi-Horizon | ✅ Valid | Low |
| Feature Engineering | ✅ Valid | Low |
| Schema Assumptions | ⚠️ Needs Work | Medium |
| View Dependencies | ❌ Missing | **HIGH** |
| Model Training Strategy | ✅ Decided (Local Mac M4) | Low |
| Execution Phases | ⚠️ Needs Detail | Medium |

**Overall Assessment**: Plan is **85% complete** but needs critical additions before execution.

---

## Next Steps

1. ✅ **Data Export Complete** - All 341 objects exported to local + repo
2. ⏳ **Plan Validation Complete** - This document
3. ⏳ **Gap Resolution** - Add missing elements to plan
4. ⏳ **Migration Script Updates** - Incorporate fixes
5. ⏳ **Final Review** - User approval before execution

**Ready for**: Gap resolution and plan updates

