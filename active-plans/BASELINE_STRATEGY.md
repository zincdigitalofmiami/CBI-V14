# Local Baseline Training Strategy
**Created**: November 12, 2025  
**Purpose**: Define how to properly baseline ZL forecasting across regimes and horizons

---

## Core Philosophy

**Train on FULL historical data (125 years), not just recent periods.**

Why: Each regime teaches different lessons. Crisis periods show volatility handling, trade wars show policy impact, historical data shows long-term cycles. Truncating to 2023–2025 loses critical information.

---

## Regime-Aware Baseline Approach

### Step 1: Dataset Preparation

Export separate regime datasets WITH full context:

**Primary Datasets** (all exported to `TrainingData/exports/`):
1. `full_history.parquet` - All 125 years, weighted
2. `trump_2_era.parquet` - 2023–2025, weight ×5000
3. `trade_war_era.parquet` - 2017–2019, weight ×1500
4. `inflation_era.parquet` - 2021–2022, weight ×1200
5. `crisis_periods.parquet` - 2008, 2020, weight ×500
6. `historical_baseline.parquet` - Pre-2000, weight ×50

**Feature Sets**:
- Minimal: 42 neural drivers (Trump-focused)
- Standard: 200–290 production features
- Extended: Top 500 features from catalog

### Step 2: Baseline Models

For EACH horizon (1w, 1m, 3m, 6m, 12m), run:

**Tier 1: Statistical Baselines**
- ARIMA (auto-tuned)
- Prophet (with regime-aware changepoints)
- Exponential smoothing
- Naive drift (sanity check)

**Tier 2: Tree-Based Baselines**
- LightGBM DART (mirrors BQML approach)
- XGBoost with regime weighting
- CatBoost (handles categorical regime features)

**Tier 3: Simple Neural Baselines**
- 1-layer LSTM
- 2-layer GRU
- 3-layer dense feedforward

### Step 3: Training Variations

For each baseline model, train BOTH:

**A. Full-History Model**
- Uses `full_history.parquet`
- Applies regime weights (×5000 for Trump era, ×50 for pre-2000)
- Tests: Can the model learn regime shifts?

**B. Regime-Specific Models**
- Train separate model per regime dataset
- Ensemble at inference time (regime detection → select model)
- Tests: Do specialized models beat generalist?

### Step 4: Horizon-Specific Considerations

**1w/1m (Short-term)**:
- Emphasize recent regime (Trump 2.0)
- Higher weight on policy/sentiment features
- Quick reaction to market shifts

**3m/6m (Medium-term)**:
- Balanced regime weighting
- Include seasonal patterns
- Cross-asset correlation features

**12m (Long-term)**:
- Include full historical cycles
- Structural economic features
- Lower weight on short-term noise

---

## Evaluation Protocol

### Holdout Strategy
- **Training**: Up to Dec 2023
- **Validation**: Jan 2024 – Jun 2024
- **Test**: Jul 2024 – Nov 2025 (includes fresh Trump 2.0 data)

### Metrics to Track
| Metric | Threshold | Purpose |
|--------|-----------|---------|
| MAPE | < 0.7% | Beat BQML production |
| R² | > 0.95 | Consistency requirement |
| Max Error | < 5% | Avoid catastrophic failures |
| SHAP Coverage | > 80% | Explainability requirement |
| Regime Accuracy | Track per regime | Ensure no regime blind spots |

### Comparison Matrix
For each baseline:
- Overall metrics (full test set)
- Metrics per regime (Trump 2.0, crisis, normal)
- Metrics per market condition (high vol, low vol, trending, ranging)

---

## MLflow Configuration

### Experiment Structure
```
Models/mlflow/
├── experiments/
│   ├── baselines_statistical/
│   ├── baselines_tree/
│   ├── baselines_neural/
│   └── regime_specific/
└── artifacts/
    ├── models/
    ├── plots/
    └── explanations/
```

### Logging Requirements
Every baseline run logs:
- **Parameters**: model config, dataset used, regime weights
- **Metrics**: MAPE, R², max error (overall + per regime)
- **Artifacts**: 
  - Trained model file
  - Residual plots
  - SHAP summary plot
  - Prediction CSV (actual vs predicted)

---

## Promotion Decision Tree

```
Baseline Model
    ↓
Does it beat BQML MAPE? (< 0.7%)
    ↓ YES
Does it maintain R² > 0.95?
    ↓ YES
SHAP explanations logical?
    ↓ YES
Passes monotonic constraints?
    ↓ YES
Tested across all regimes?
    ↓ YES
    → PROMOTE TO VERTEX AI
    
    ↓ NO (at any step)
    → KEEP AS REFERENCE BASELINE
    → LOG WHY IT FAILED
```

---

## Data Quality Requirements

Before running any baselines, verify:

1. **Ingestion Current**:
   - Run: `./scripts/status_check.sh`
   - Verify: All heavy hitters have recent data
   - Update if needed: `./scripts/run_ultimate_consolidation.sh`

2. **Export Validation**:
   - Check: No NULL columns in critical features
   - Check: Dates continuous (no gaps)
   - Check: Regime labels correct

3. **Feature Consistency**:
   - Same features across all regime exports
   - Same preprocessing applied
   - Same target definition

---

## Implementation Checklist

### Data Preparation
- [ ] Export full_history.parquet (125 years)
- [ ] Export regime-specific datasets (6 files)
- [ ] Validate exports (no NULLs, dates continuous)
- [ ] Document feature schema in `docs/data/BASELINE_MANIFEST.md`

### Baseline Scripts
- [ ] Create `src/training/baselines/statistical.py` (ARIMA, Prophet)
- [ ] Create `src/training/baselines/tree_models.py` (LightGBM, XGBoost)
- [ ] Create `src/training/baselines/simple_neural.py` (LSTM, GRU, Dense)
- [ ] Create `src/training/baselines/regime_ensemble.py` (multi-model blend)

### MLflow Setup
- [ ] Initialize MLflow tracking URI
- [ ] Create experiment structure
- [ ] Add logging wrapper functions
- [ ] Test logging with dummy run

### Evaluation
- [ ] Run all baselines on 1m horizon (pilot)
- [ ] Compare against BQML benchmark
- [ ] Document results
- [ ] Decide on promotion candidates

### Documentation
- [ ] Update `MASTER_EXECUTION_PLAN.md` with results
- [ ] Create `docs/training/BASELINE_RESULTS.md`
- [ ] Update `STRUCTURE.md` if directories change

---

## Success Criteria

We've successfully established local baselines when:

1. ✅ All 6 regime datasets exported and validated
2. ✅ All 3 baseline tiers implemented (statistical, tree, neural)
3. ✅ MLflow logging working for all models
4. ✅ At least one baseline beats BQML on holdout data
5. ✅ Clear promotion criteria documented
6. ✅ Results reproducible (same data = same results)

---

## FAQ

**Q: Why train on full 125 years if Trump broke the market?**  
A: Regime weighting lets us emphasize Trump era (×5000) while still learning from crisis/trade-war patterns. Full history prevents overfitting to one regime.

**Q: Should baselines be horizon-specific or one-size-fits-all?**  
A: Horizon-specific. Each horizon needs different features and time windows.

**Q: Do we baseline each regime separately?**  
A: Yes - compare full-history weighted vs regime-specific models to see which performs better.

**Q: When do we move to advanced architectures?**  
A: Only after simple baselines establish floor. If 1-layer LSTM hits 0.5% MAPE, we know deeper nets can improve. If it's 5%, architecture isn't the issue.

---

**Next Action**: Export datasets and implement Tier 1 baselines (statistical).

