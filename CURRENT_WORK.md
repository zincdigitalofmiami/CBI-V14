# Current Work Status

**Last Updated**: November 14, 2025  
**Status**: ✅ Migration Complete, Ready for Training  
**Phase**: Post-Migration Testing & Validation

---

## 🎯 Current Focus

**Migration to local-first architecture COMPLETE**:
- All training tables migrated to new naming convention
- All Python scripts updated
- Regime weights optimized (research-based)
- Prediction upload pipeline created
- Documentation framework established

**Next**: End-to-end workflow testing and Phase 5 SQL updates

---

## ✅ Completed Work (November 14, 2025)

### Naming Architecture Migration

**Phase 1: Archive** ✅
- 10 legacy tables archived to `archive.legacy_20251114__models_v4__*`
- All data preserved with metadata
- Safe rollback available

**Phase 2: Datasets** ✅
- All 7 required datasets verified:
  - archive, raw_intelligence, features, training, predictions, monitoring, vegas_intelligence

**Phase 3: Training Tables** ✅
- 10 training tables created with new naming
- 5 production surface: `training.zl_training_prod_allhistory_{1w|1m|3m|6m|12m}`
- 5 full surface: `training.zl_training_full_allhistory_{1w|1m|3m|6m|12m}`
- 2 regime tables: `regime_calendar` (13,102 rows), `regime_weights` (11 rows)

**Phase 4: Python Scripts** ✅
- 15 scripts updated to new naming convention:
  - Export: `scripts/export_training_data.py`
  - Upload: `scripts/upload_predictions.py` (NEW)
  - Training: 13 scripts (baselines, advanced, ensemble, regime)
  - Prediction: 2 scripts

**Phase 6: Shim Views** ✅
- 5 backward compatibility views created
- 30-day grace period before removal

### Critical Fixes

**Regime Weights** ✅
- Fixed: 0.5-1.5 → 50-5000 (1000x correction)
- Research-based: recency bias + importance weighting
- Trump era: 5000 (100x historical weight)
- Documentation: `scripts/migration/REGIME_WEIGHTS_RESEARCH.md`

**Upload Pipeline** ✅
- Created: `scripts/upload_predictions.py`
- Function: Walks Models/local/, uploads to BigQuery
- Auto-creates: `predictions.vw_zl_{h}_latest` views
- Dashboard-ready: Vercel reads from views

**Architecture Documentation** ✅
- Updated: `GPT5_READ_FIRST.md` (local-first, no Vertex/BQML)
- Created: 4 institutional framework documents
- Verified: 100% alignment with specification

### Data Exports

**All 5 horizons exported** ✅:
- `zl_training_prod_allhistory_1w.parquet` (1.4 MB, 1,472 rows)
- `zl_training_prod_allhistory_1m.parquet` (2.7 MB, 1,404 rows)
- `zl_training_prod_allhistory_3m.parquet` (1.3 MB, 1,475 rows)
- `zl_training_prod_allhistory_6m.parquet` (1.2 MB, 1,473 rows)
- `zl_training_prod_allhistory_12m.parquet` (1.2 MB, 1,473 rows)

---

## 📋 Active Tasks

### Immediate (This Week)

1. **End-to-End Workflow Testing**
   - Test: Export → Train → Predict → Upload
   - Verify: Predictions appear in BigQuery
   - Validate: Dashboard can read from views
   - Status: Ready to execute

2. **Baseline Training (Day 2 of Master Plan)**
   - Train statistical baselines (ARIMA, Prophet)
   - Train tree baselines (LightGBM, XGBoost)
   - Train simple neural (LSTM, GRU)
   - Log all to MLflow
   - Status: Scripts ready, hardware configured

3. **Conviction vs Confidence Implementation**
   - Add ensemble variance calculation
   - Add quantile regression models
   - Separate conviction from confidence metrics
   - Status: Framework documented, code pending

### Next Phase (Phase 5)

4. **SQL File Updates**
   - Update `ULTIMATE_DATA_CONSOLIDATION.sql`
   - Update feature view builders
   - Update prediction queries
   - Status: Pending (Python migration complete)

5. **Model Metadata Enhancement**
   - Ensure all models save complete artifacts
   - Add feature drift tracking
   - Add run_id correlation
   - Status: Basic structure in place, enhancements pending

---

## 🏗️ Architecture Summary

### Core Workflow

```
BigQuery (Storage) 
    ↓ Export
Mac M4 (Training - TensorFlow Metal)
    ↓ Local Inference  
Mac M4 (Predictions)
    ↓ Upload
BigQuery (predictions.vw_zl_{h}_latest)
    ↓ API Read
Vercel Dashboard (UI)
```

**Key Points**:
- NO Vertex AI for training or inference
- NO BQML training (BigQuery = storage only)
- 100% local compute on Mac M4
- Cloud only for storage (BigQuery) and UI (Vercel)

### Datasets (8 Total)

| Dataset | Purpose | Object Count |
|---------|---------|--------------|
| raw_intelligence | Raw ingestion | 40+ tables |
| features | Engineered features | Views only |
| training | Training matrices | 12 tables |
| predictions | Model outputs | Per-model tables |
| monitoring | Performance tracking | 6 tables |
| vegas_intelligence | Sales intel | 10 tables |
| archive | Legacy snapshots | 10+ tables |
| yahoo_finance_comprehensive | Historical data | Unchanged |

---

## 📊 Feature Inventory

### Production Surface (~290 Features)

**By Category**:
- Price & Technical: ~40 features
- Cross-Asset: ~60 features (palm, crude, VIX, SPX, DXY, treasuries, metals, grains)
- Macro & Rates: ~40 features (GDP, CPI, Fed, yield curve, risk-free)
- Policy & Trade: ~30 features (Trump, biofuel, CFTC, China, USDA)
- Weather & Shipping: ~40 features (Brazil, Argentina, US, GDD, freight)
- News & Sentiment: ~30 features (FinBERT, social, geopolitical)
- Seasonality: ~25 features (harvest cycles, policy cycles)
- Correlations & Spreads: ~25 features (soy-palm, crush, cross-asset)

**Total**: ~290 features (varies slightly by horizon: 1w=275, 1m=274, 3m=268, 6m=258, 12m=similar)

### Full Surface (1,948+ Features)

Includes all production features PLUS:
- Extended technical indicators
- Additional cross-asset correlations
- Granular weather metrics
- Policy sub-components
- Interaction terms
- Regime-specific features

**Status**: Tables created, rebuild pending from ULTIMATE_DATA_CONSOLIDATION.sql

---

## 🎓 Training Enhancements (November 2025)

### Data Quality Improvements
- ✅ **25 years integrated**: 2000-2025 (was 3 years)
- ✅ **6,057 ZL rows**: 365% increase in training data
- ✅ **338K+ pre-2020 rows**: Full market cycle coverage
- ✅ **Zero duplicates**: Complete deduplication in training tables
- ✅ **Complete validation**: Timestamp, value, metadata checks

### Regime-Based Training
- ✅ **11 regimes defined**: From historical_pre2000 to trump_2023_2025
- ✅ **Optimized weights**: 50-5000 scale (research-based)
- ✅ **Recency bias**: Trump era 100x historical weight
- ✅ **Sample compensation**: Small but critical periods amplified
- ✅ **Gradient impact**: Multiplicative scale affects loss functions

### Model Architecture
- ✅ **Baselines**: ARIMA, Prophet, LightGBM, XGBoost, LSTM, GRU
- ✅ **Advanced**: Multi-layer LSTM/GRU, TCN, CNN-LSTM, Tiny Transformers
- ✅ **Regime-specific**: Crisis, trade war, inflation specialists
- ✅ **Ensemble**: Regime-aware meta-learner
- ⏳ **Quantile**: Uncertainty quantification (planned)

### Hardware Optimization
- ✅ **Metal GPU**: TensorFlow Metal acceleration
- ✅ **FP16 mixed precision**: Memory efficiency for 16GB RAM
- ✅ **Sequential training**: Prevents thermal throttling
- ✅ **External SSD**: Model and checkpoint storage
- ✅ **Memory management**: Session cleanup, gradient checkpointing

---

## 🔧 Scripts & Tools

### Core Workflow Scripts
- `scripts/export_training_data.py` - BigQuery → Parquet (supports --surface, --horizon)
- `scripts/upload_predictions.py` - Local predictions → BigQuery (NEW)
- `src/prediction/generate_local_predictions.py` - Local inference only
- `src/prediction/send_to_dashboard.py` - Dashboard integration

### Training Scripts (All Updated)

**Baselines** (6 files):
- `train_tree.py` - LightGBM, XGBoost
- `train_simple_neural.py` - LSTM, GRU  
- `train_statistical.py` - ARIMA, Prophet
- `tree_models.py` - Polars-based tree training
- `statistical.py` - Polars-based statistical
- `neural_baseline.py` - Sequential neural models

**Advanced** (5 files):
- `attention_model.py` - Attention mechanisms
- `cnn_lstm_model.py` - CNN-LSTM hybrid
- `multi_layer_lstm.py` - Deep LSTM/GRU
- `tcn_model.py` - Temporal convolutional networks
- `tiny_transformer.py` - Lightweight transformers

**Regime & Ensemble** (2 files):
- `regime_classifier.py` - Crisis/bull/bear/normal detection
- `regime_ensemble.py` - Regime-aware model blending

### Migration Scripts (8 files)
- `archive_legacy_tables.py` - Phase 1
- `02_verify_datasets.py` - Phase 2
- `03_create_new_training_tables.py` - Phase 3
- `04_create_regime_tables.sql` - Regime setup
- `05_create_shim_views.py` - Phase 6
- `06_update_training_scripts.py` - Phase 4 helper
- `08_update_all_training_scripts.py` - Phase 4 automation
- `run_migration.py` - Full migration orchestrator

---

## 📖 Documentation Framework (NEW)

### Institutional Quant Methodology

**Core Concepts**:
- `docs/reference/CONVICTION_VS_CONFIDENCE.md` - Directional vs precision distinction
- `docs/reference/SIGNAL_TREATMENT_RULES.md` - 12 professional guidelines
- `docs/reference/CURSOR_MASTER_INSTRUCTION_SET.md` - Post-move audit protocol
- `docs/reference/INSTITUTIONAL_FRAMEWORK_INDEX.md` - Central navigation

**Key Insight**: Crisis = high conviction (direction clear) + low confidence (wide error bands)

### Migration Documentation

- `docs/migrations/20251114_NAMING_ARCHITECTURE_MIGRATION.md` - Execution log
- `scripts/migration/PHASE_1_3_COMPLETION_REPORT.md` - Detailed status
- `scripts/migration/REGIME_WEIGHTS_RESEARCH.md` - Weight optimization research
- `ARCHITECTURE_ALIGNMENT_COMPLETE.md` - Verification proof

### Planning Documentation

- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - 7-day institutional plan
- `docs/plans/REGIME_BASED_TRAINING_STRATEGY.md` - Regime methodology
- `docs/plans/TABLE_MAPPING_MATRIX.md` - Legacy → new mappings
- `docs/plans/NAMING_CONVENTION_SPEC.md` - Naming standards

---

## 🔍 Known Issues & Limitations

### Current Limitations
- ⚠️ Full surface tables (1,948+ features) are placeholders - need rebuild
- ⚠️ Phase 5 SQL files not yet updated
- ⚠️ Confidence intervals not yet implemented (conviction/confidence separation)
- ⚠️ Automated post-move audits not yet built

### Not Issues (By Design)
- ✅ No Vertex AI - Local training by design
- ✅ No BQML training - BigQuery storage only by design
- ✅ Sequential model training - Hardware constraint (16GB RAM)
- ✅ FP16 precision - Memory optimization

---

## 📈 Success Metrics

### Data Quality
- ✅ Zero timestamp gaps in raw layer
- ✅ Zero duplicate rows in training tables
- ✅ Zero null targets in training data
- ✅ 100% metadata coverage (source, ingest_timestamp, provenance_uuid)

### Migration Quality
- ✅ 10/10 tables archived successfully
- ✅ 7/7 datasets verified
- ✅ 12/12 new tables created
- ✅ 15/15 scripts updated
- ✅ 5/5 horizons exported

### Code Quality
- ✅ Zero old naming patterns in active code
- ✅ Zero Vertex AI references in training scripts
- ✅ All scripts use new naming convention
- ✅ All models save to version directories
- ✅ No linter errors

---

## 🚀 Next Steps

### Immediate (This Week)

1. **End-to-End Test**
   - Run full workflow: export → train → predict → upload
   - Verify predictions in BigQuery
   - Test dashboard reading from views
   - Document results

2. **Baseline Training**
   - Train 1-2 models per horizon
   - Validate Metal GPU performance
   - Log all metrics to MLflow
   - Compare MAPE to BQML reference (0.7-1.3%)

3. **Monitoring Validation**
   - Test MAPE calculation
   - Test Sharpe calculation
   - Verify regime classification
   - Validate dashboard APIs

### Near-Term (Next 1-2 Weeks)

4. **Phase 5: SQL Updates**
   - Update `ULTIMATE_DATA_CONSOLIDATION.sql`
   - Rebuild full surface tables (1,948+ features)
   - Update feature view builders
   - Update prediction queries

5. **Confidence Implementation**
   - Add ensemble variance calculation
   - Implement quantile regression
   - Add MAPIE conformal prediction
   - Update dashboard to show conviction + confidence separately

6. **Automated Audits**
   - Implement trigger detection (VIX >25, USD/BRL >3%, etc.)
   - Build post-move audit automation
   - Create monitoring dashboard
   - Set up alerts

---

## 📁 File Organization

### Production Code (Use These)
```
scripts/
├── export_training_data.py        ✅ Current export
├── upload_predictions.py          ✅ Current upload
└── migration/                     ✅ Migration complete

src/training/
├── baselines/                     ✅ All updated
├── advanced/                      ✅ All updated
├── ensemble/                      ✅ All updated
└── regime/                        ✅ All updated

src/prediction/
├── generate_local_predictions.py  ✅ Local inference
└── send_to_dashboard.py           ✅ BigQuery upload
```

### Legacy (Reference Only)
```
archive/                           ❌ Do not use
legacy/                            ❌ Do not use
vertex-ai/                         ❌ No longer used
docs/plans/archive/                ❌ Old plans
```

---

## 🎓 Institutional Framework

### The Critical Distinction: Conviction vs Confidence

**Conviction** (direction clarity):
- Increases in crisis (VIX >25)
- Based on signal strength
- Use for: model selection, ensemble weighting

**Confidence** (forecast precision):
- Decreases in crisis (MAPE ↑)
- Based on model variance
- Use for: position sizing, error bands

**Documentation**: `docs/reference/CONVICTION_VS_CONFIDENCE.md`

**Status**: Framework documented, code implementation pending

### The 12 Signal Treatment Rules

1. **Treasury Curve** - Changes over levels, pair with USD
2. **VIX** - Regime bands, conviction ≠ confidence
3. **Sentiment** - Mechanism required, no vibes
4. **Fed Funds** - Path over level, track FX impact
5. **USD** - BRL/ARS critical, pair with CFTC
6. **Biofuel Policy** - Convert to volume (MT), not text
7. **Logistics** - Real bottlenecks only
8. **Weather** - Physics (GDD, 7-day), not single anomalies
9. **CFTC** - Percentile rank, divergence detection
10. **Crush Margins** - Behavior signals, not levels
11. **Palm Substitution** - Relative ratio, freight-adjusted
12. **China Demand** - Action over rhetoric, imports over talk

**Documentation**: `docs/reference/SIGNAL_TREATMENT_RULES.md`

### Post-Move Audit Protocol

**Triggers**: VIX >25, USD/BRL >3%, ZL >2%, drought >+2σ, USDA reports, policy announcements

**Mandatory Sequence**:
1. Raw Layer (5-10 min) - Integrity validation
2. Curated Layer (10-15 min) - Aggregation checks
3. Training Layer (5-10 min) - Feature alignment
4. Prediction Layer (15-20 min) - Upload + MAPE/Sharpe
5. Dashboard (5 min) - View resolution

**Documentation**: `docs/reference/CURSOR_MASTER_INSTRUCTION_SET.md`

---

## 💡 Recent Insights

### Regime Weights Research
- Applied ML research on importance weighting
- Multiplicative weight update methods
- Sample compensation for imbalanced data
- Result: Trump era dominates gradients (~40-50% effective weight despite <6% of rows)

### Local-First Benefits
- Full control over training process
- Zero cloud compute costs
- No Vertex AI black box
- Faster iteration cycles
- Better debugging capabilities

### Conviction/Confidence Separation
- Industry-standard distinction
- Prevents false precision in crises
- Proper risk management
- Institutional credibility

---

## 🎯 Success Criteria

### Migration Success ✅
- [x] All tables using new naming convention
- [x] All scripts updated
- [x] Regime weights optimized
- [x] Upload pipeline created
- [x] Documentation aligned
- [x] Zero legacy naming in active code

### Training Readiness ✅
- [x] Data exported (5/5 horizons)
- [x] Training scripts ready
- [x] Metal GPU configured
- [x] MLflow tracking set up
- [x] Model save structure defined

### Production Readiness ⏳
- [x] Prediction generation script ready
- [x] Upload pipeline created
- [ ] End-to-end test complete
- [ ] Dashboard integration verified
- [ ] Monitoring operational
- [ ] Confidence intervals implemented

---

## 📞 Key Contacts

**Project Owner**: Chris Musick  
**Developer**: Kirk Musick  
**AI Assistants**: GPT-5 (design), Claude (execution)

---

## 🗂️ Quick Links

**Start Here**:
- `GPT5_READ_FIRST.md` - Architecture guide
- `README.md` - Project overview
- `INSTITUTIONAL_FRAMEWORK_COMPLETE.md` - Framework summary

**Planning**:
- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - 7-day plan
- `docs/plans/TABLE_MAPPING_MATRIX.md` - Table mappings

**Migration**:
- `docs/migrations/20251114_NAMING_ARCHITECTURE_MIGRATION.md` - Execution log
- `scripts/migration/PHASE_1_3_COMPLETION_REPORT.md` - Status

**Framework**:
- `docs/reference/CONVICTION_VS_CONFIDENCE.md` - Core concept
- `docs/reference/SIGNAL_TREATMENT_RULES.md` - 12 rules
- `docs/reference/CURSOR_MASTER_INSTRUCTION_SET.md` - Audit protocol

---

**Status**: Migration complete, ready for training and testing  
**Next**: End-to-end workflow validation, then baseline model training

