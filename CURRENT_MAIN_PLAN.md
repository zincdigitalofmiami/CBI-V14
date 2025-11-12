# 🎯 CURRENT MAIN PLAN - MAC TRAINING STRATEGY
**Date**: November 7, 2025  
**Status**: ACTIVE - This is what we're doing RIGHT NOW  
**Machine**: M4 Mac Mini 16GB (new machine)

---

## ⚡ THE ONE PLAN TO FOCUS ON

**File**: `MAC_TRAINING_EXPANDED_STRATEGY.md`  
**This is THE main plan** - everything else is either outdated, specialized, or for later.

---

## 🎯 WHAT WE'RE DOING

### Strategic Shift: Mac Training Unlocks Everything

**Why Mac Training:**
- ✅ **No Cost Constraints**: Local training = unlimited iterations
- ✅ **No Column Limits**: Can use ALL 9,213+ features (not limited to 1,000 like Vertex AI)
- ✅ **Full Historical Data**: Use ALL 125 years (16,824 rows) with regime weighting
- ✅ **Advanced Features**: SHAP, Monte Carlo, what-if scenarios, ensemble models
- ✅ **Multiple Specialized Models**: Like JPM/GS - different models for different regimes/focuses

**Hardware:**
- **Machine**: M4 Mac Mini 16GB (new machine)
- **RAM**: 16GB (perfect for training)
- **GPU**: M4 GPU with TensorFlow Metal acceleration
- **Storage**: 256GB SSD (use BigQuery for data, external storage if needed)

---

## 📋 THE PLAN STRUCTURE

### 1. Multi-Model Ensemble Approach (JPM/GS Style)

**Tier 1: Regime-Specialized Models**
- Trump 2.0 Model (2023-2025, weight 5,000)
- Trade War Model (2017-2019, weight 1,500)
- Crisis Model (2008-2009, 2020, weight 500-800)
- Inflation Model (2021-2022, weight 1,200)
- Historical Model (Pre-2000, weight 50)

**Tier 2: Feature-Focused Models**
- Neural Signals Model (Big Eight signals)
- Policy Model (Trump sentiment, tariffs)
- Fundamentals Model (Crush margins, China imports)
- Technical Model (Price patterns, momentum)
- Cross-Asset Model (Palm oil, crude, FX)

**Tier 3: Horizon-Specialized Models**
- 1M Horizon: LSTM with 30-day lookback
- 3M Horizon: GRU with 90-day lookback
- 6M Horizon: Deep Feedforward
- 12M Horizon: Transformer (optional)

### 2. Full Dataset Strategy

**Data Architecture:**
- **Rows**: 16,824 (1900-2025, daily)
- **Features**: 9,213+ (all available, no limits)
- **Regime Weights**: 50-5,000 (per regime)
- **Targets**: 4 horizons (1M, 3M, 6M, 12M)

**Regime Weight Implementation:**
- Use Keras `sample_weight` parameter
- Weighted loss function
- Stratified sampling (optional)

### 3. Advanced Features

**SHAP Explainability:**
- Global feature importance rankings
- Per-forecast explanations (waterfall plots)
- Feature interaction effects

**Monte Carlo Uncertainty:**
- P10/P50/P90 prediction intervals
- Dropout at inference (1,000 samples)
- Epistemic uncertainty quantification

**What-If Scenarios:**
- Real-time feature override
- Scenario comparison (baseline vs scenario)
- Strategy page sliders for key drivers

### 4. Implementation Plan

**Phase 1: Data Preparation (Week 1)**
- Create master training table (all 9,500+ features)
- Add regime weights (50-5,000)
- Feature engineering (interactions, lags)

**Phase 2: Model Development (Week 2-3)**
- Build base models (LSTM, GRU, Feedforward)
- Implement regime weighting
- Train specialized models

**Phase 3: Ensemble & Advanced Features (Week 4)**
- Build ensemble (weighted average, stacking)
- Implement SHAP, Monte Carlo, what-if
- Validation & testing

**Phase 4: Deployment (Week 5)**
- Model export (SavedModel format)
- Dashboard integration
- Prediction pipeline

---

## 🚫 WHAT TO IGNORE (For Now)

### Outdated Plans
- ❌ `VERTEX_AI_TRUMP_ERA_PLAN.md` - Vertex AI cloud training (different approach, might do later)
- ❌ `TRUMP_ERA_EXECUTION_PLAN.md` - BQML DART model (42 features, 2023-2025 only - specialized subset)
- ❌ `START_HERE.md` - About fixing stale data (different issue, already handled)

### Specialized Plans (Reference Only)
- `MAC_TRAINING_SETUP_PLAN.md` - Initial setup (already done)
- `MAC_TRAINING_COST_VERIFICATION.md` - Cost analysis (confirmed zero cost)
- `MAC_HARDWARE_VERIFICATION.md` - Hardware check (M4 Mac Mini confirmed)

---

## ✅ WHAT'S READY

### Setup Complete
- ✅ M4 Mac Mini 16GB verified
- ✅ TensorFlow Metal compatibility confirmed
- ✅ Installation scripts created (`install_mac_training_dependencies.sh`)
- ✅ Migration guide created (`migrate_to_new_mac.sh`)

### Documentation Complete
- ✅ `MAC_TRAINING_EXPANDED_STRATEGY.md` - Full strategy (575 lines)
- ✅ `MAC_TRAINING_FULL_VERIFICATION.md` - Feasibility audit
- ✅ `MAC_MINI_M4_EVALUATION.md` - Hardware assessment
- ✅ `MACHINE_REQUIREMENTS_ASSESSMENT.md` - Resource requirements

### Next Steps
1. **Clone repo** on new Mac Mini M4
2. **Install dependencies** (`./install_mac_training_dependencies.sh`)
3. **Test TensorFlow Metal** (GPU acceleration)
4. **Start Phase 1** (Data preparation)

---

## 📊 KEY METRICS & TARGETS

### Model Performance Targets
- **1M Horizon**: MAPE <2%, R² >0.90
- **3M Horizon**: MAPE <4%, R² >0.85
- **6M Horizon**: MAPE <6%, R² >0.75
- **12M Horizon**: MAPE <10%, R² >0.65

### Regime-Specific Performance
- **Trump 2.0 Era**: MAPE <2% (primary focus)
- **Trade War Era**: MAPE <3% (validation)
- **Other Regimes**: MAPE <8% (acceptable)

### Advanced Features
- **SHAP**: Feature importance rankings
- **Monte Carlo**: P10/P90 intervals with 80% coverage
- **What-If**: <2 second response time

---

## 🎯 BOTTOM LINE

**THE MAIN PLAN**: `MAC_TRAINING_EXPANDED_STRATEGY.md`

**What We're Doing**:
- Training on M4 Mac Mini 16GB
- Full dataset (9,213+ features, 125 years)
- Regime-weighted training
- Multi-model ensemble (JPM/GS style)
- Advanced features (SHAP, Monte Carlo, what-if)

**What We're NOT Doing** (Right Now):
- Vertex AI cloud training (different approach)
- BQML DART model (specialized subset)
- Fixing stale data (already handled)

**Status**: Ready to start Phase 1 (Data Preparation)

---

## 📁 FILE STRUCTURE

```
CBI-V14/
├── MAC_TRAINING_EXPANDED_STRATEGY.md  ← MAIN PLAN (read this first!)
├── MAC_TRAINING_FULL_VERIFICATION.md   ← Feasibility audit
├── MAC_MINI_M4_EVALUATION.md           ← Hardware assessment
├── install_mac_training_dependencies.sh ← Setup script
├── migrate_to_new_mac.sh               ← Migration guide
└── vertex-ai/                          ← Neural pipeline (to be built)
    └── neural-pipeline/                ← Future implementation
```

---

**Created**: November 7, 2025  
**Purpose**: Tell Cursor on new machine exactly what to focus on  
**Status**: Active - This is the current main plan

