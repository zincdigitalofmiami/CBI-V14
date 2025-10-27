# FINAL MODEL TRAINING PLAN

**Date:** October 24, 2025  
**Status:** Ready to Execute  
**Preprocessing:** ✅ COMPLETE (Tasks 1-5)

---

## DATASET STATUS

### ✅ Final Clean Dataset

**Files:**
- `TRAIN_SCALED.csv` - 1,000 rows × 103 columns
- `TEST_SCALED.csv` - 251 rows × 103 columns
- `feature_scaler.pkl` - For production inference

**Features:**
- Total: 98 features
- All verified as real data
- No leakage, no duplicates
- Properly scaled (mean=0, std=1)

**Targets:**
- `target_1w` - 1-week forward return (PRIMARY)
- `target_1m` - 1-month forward return
- `target_3m` - 3-month forward return
- `target_6m` - 6-month forward return

**Quality:**
- Feature/sample ratio: 0.078 (excellent!)
- Date range: 2020-10-21 to 2025-10-13
- Training: 2020-10-21 to 2024-10-11 (1,000 days)
- Test: 2024-10-14 to 2025-10-13 (251 days)

---

## MODEL ARCHITECTURE

### PyTorch Feed-Forward Neural Network

```
Input Layer:  98 features
    ↓
Hidden Layer 1: 256 neurons + ReLU + Dropout(0.3)
    ↓
Hidden Layer 2: 128 neurons + ReLU + Dropout(0.3)
    ↓
Hidden Layer 3: 64 neurons + ReLU + Dropout(0.2)
    ↓
Hidden Layer 4: 32 neurons + ReLU + Dropout(0.2)
    ↓
Output Layer: 1 neuron (regression)
```

**Why this architecture:**
- 4 layers: Captures complex non-linear patterns
- Decreasing size (256→128→64→32): Funnel pattern
- Dropout: Prevents overfitting (0.3 for first 2 layers, 0.2 for last 2)
- ReLU activation: Standard for regression tasks
- Total parameters: ~50,000 (good for 1,000 training samples)

---

## TRAINING CONFIGURATION

### Hyperparameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Optimizer** | Adam | Adaptive learning rates work well for financial data |
| **Learning Rate** | 0.001 | Standard starting point, will adjust if needed |
| **Batch Size** | 32 | Good balance between speed and stability |
| **Epochs** | 100 | With early stopping |
| **Loss Function** | MSE (Mean Squared Error) | Standard for regression |
| **Early Stopping** | Patience=15 | Stop if no improvement for 15 epochs |
| **LR Scheduler** | ReduceLROnPlateau | Reduce LR if validation plateaus |

### Regularization

- **Dropout:** 0.2-0.3 per layer
- **Weight Decay:** 0.0001 (L2 regularization in optimizer)
- **Gradient Clipping:** Max norm = 1.0

---

## VALIDATION STRATEGY

### Initial Holdout Validation

1. **Train on:** 1,000 samples (80%)
2. **Validate on:** 251 samples (20%)
3. **Metrics to track:**
   - Loss (MSE)
   - MAE (Mean Absolute Error)
   - Directional Accuracy
   - R² Score

### Walk-Forward Validation (After baseline)

```
Window 1:  Train [0:900]     → Test [905:925]   (20 days)
Window 2:  Train [50:950]    → Test [955:975]   (20 days)
Window 3:  Train [100:1000]  → Test [1005:1025] (20 days)
...
Total: ~10 windows
```

**Settings:**
- Training window: 900 days
- Test window: 20 days
- Step size: 50 days
- Purge gap: 5 days between train/test

---

## SUCCESS CRITERIA

### Minimum Viable Model (Pass/Fail)

| Metric | Target | Status |
|--------|--------|--------|
| Directional Accuracy | >52% | Better than random (50%) |
| MAE | <0.05 | 5% average error |
| Training completes | Yes | No crashes/errors |
| Loss decreases | Yes | Model is learning |

### Good Model (Production Candidate)

| Metric | Target | Rationale |
|--------|--------|-----------|
| Directional Accuracy | >55% | Actionable trading signal |
| MAE | <0.03 | 3% average error |
| R² Score | >0.1 | Explains some variance |
| Sharpe Ratio* | >1.0 | Risk-adjusted profitability |

*Sharpe calculated as: mean(returns) / std(returns) × sqrt(252)

### Excellent Model (Stretch Goal)

| Metric | Target |
|--------|--------|
| Directional Accuracy | >60% |
| MAE | <0.02 |
| R² Score | >0.3 |
| Sharpe Ratio | >2.0 |

---

## TRAINING PROCESS

### Step 1: Baseline Training (30-45 min)

```python
1. Load TRAIN_SCALED.csv and TEST_SCALED.csv
2. Split into X_train, y_train, X_test, y_test
3. Initialize model with architecture above
4. Train for 100 epochs with early stopping
5. Track: loss, MAE, directional accuracy
6. Save best model checkpoint
7. Generate training curves (loss over epochs)
```

**Output:**
- `baseline_model.pth` - Best model weights
- `training_history.csv` - Metrics per epoch
- `training_curves.png` - Loss/accuracy plots

### Step 2: Baseline Evaluation (10 min)

```python
1. Load best model
2. Predict on test set
3. Calculate all metrics
4. Generate predictions vs actuals plot
5. Analyze errors (residuals)
6. Check for any patterns in errors
```

**Output:**
- `baseline_predictions.csv` - Predictions vs actuals
- `baseline_metrics.json` - All performance metrics
- `prediction_plot.png` - Visualizations

### Step 3: Feature Importance (15 min)

```python
1. Calculate gradient-based feature importance
2. Identify top 20 most important features
3. Identify bottom 20 least important features
4. Consider removing least important for iteration
```

**Output:**
- `feature_importance.csv` - All features ranked
- `feature_importance_plot.png` - Top 20 visualization

### Step 4: Walk-Forward Validation (60-90 min)

```python
1. Set up 10 walk-forward windows
2. For each window:
   - Train model from scratch
   - Predict on test window
   - Calculate metrics
3. Aggregate results across all windows
4. Check for time-based degradation
```

**Output:**
- `walkforward_results.csv` - Metrics per window
- `walkforward_summary.json` - Aggregated stats
- `walkforward_plot.png` - Performance over time

---

## EXPECTED RESULTS (REALISTIC)

### Based on your data quality:

**Optimistic Scenario:**
- Directional Accuracy: 55-58%
- MAE: 0.025-0.035 (2.5-3.5%)
- R²: 0.15-0.25
- Sharpe: 1.2-1.8

**Realistic Scenario:**
- Directional Accuracy: 52-55%
- MAE: 0.030-0.040 (3-4%)
- R²: 0.08-0.15
- Sharpe: 0.8-1.2

**Why realistic expectations matter:**
- Financial markets are noisy
- 50% is random (coin flip)
- 55%+ is actionable for trading
- Small edges compound over time

---

## WHAT TO WATCH FOR

### Good Signs ✅

1. **Training loss decreases smoothly**
   - No erratic jumps
   - Validation follows training

2. **Directional accuracy > 52%**
   - Better than random
   - Consistent across folds

3. **No extreme overfitting**
   - Train/val loss gap < 2x
   - Metrics similar on train/test

4. **Feature importance makes sense**
   - Price features are important
   - Correlations matter
   - Not dominated by noise features

### Red Flags 🚩

1. **Loss increases or plateaus immediately**
   - Learning rate too high
   - Bad initialization
   - Data issues

2. **Extreme overfitting**
   - Train loss → 0, Val loss → ∞
   - Perfect train accuracy, random test
   - Memorizing rather than learning

3. **Directional accuracy = 50%**
   - Not learning signal
   - Just predicting mean/mode
   - Features have no predictive power

4. **Unstable training**
   - Loss jumping around
   - NaN/Inf values
   - Gradient explosions

---

## ITERATION PLAN (If needed)

### If results are poor (<52% accuracy):

**Try these in order:**

1. **Simplify model** (reduce overfitting)
   - Remove 1-2 layers
   - Increase dropout to 0.4-0.5
   - Add more regularization

2. **Adjust learning rate**
   - Try 0.0001 (lower)
   - Try 0.01 (higher)
   - Use learning rate finder

3. **Feature engineering**
   - Remove least important features
   - Add interaction terms
   - Create ensemble features

4. **Different architecture**
   - Try LSTM (sequence model)
   - Try ensemble of smaller models
   - Try different activation functions

---

## FILES THAT WILL BE CREATED

### Training Outputs

```
baseline_model.pth              - Best model weights
training_history.csv            - Epoch-by-epoch metrics
training_curves.png             - Loss/accuracy plots
baseline_predictions.csv        - Predictions vs actuals
baseline_metrics.json           - Performance summary
prediction_plot.png             - Visualization
residuals_plot.png              - Error analysis
feature_importance.csv          - Feature rankings
feature_importance_plot.png     - Top features chart
```

### Walk-Forward Outputs

```
walkforward_results.csv         - Per-window metrics
walkforward_summary.json        - Aggregated stats
walkforward_predictions.csv     - All predictions
walkforward_plot.png            - Performance timeline
```

### Final Report

```
TRAINING_COMPLETE_REPORT.md     - Comprehensive summary
```

---

## ESTIMATED TIMELINE

| Task | Time | Status |
|------|------|--------|
| **Preprocessing (Tasks 1-5)** | 60 min | ✅ DONE |
| Load data & setup | 5 min | ⏳ Next |
| Baseline training | 30-45 min | ⏳ |
| Baseline evaluation | 10 min | ⏳ |
| Feature importance | 15 min | ⏳ |
| Walk-forward validation | 60-90 min | ⏳ |
| Analysis & reporting | 20 min | ⏳ |
| **TOTAL** | **2.5-3 hours** | |

---

## PRODUCTION DEPLOYMENT (After training)

### If model is good (>55% accuracy):

1. **Save production artifacts:**
   - Best model weights
   - Feature scaler
   - Feature list
   - Preprocessing code

2. **Create inference pipeline:**
   - Load new data
   - Apply same preprocessing
   - Scale features
   - Predict
   - Inverse scale predictions

3. **Set up monitoring:**
   - Track prediction accuracy over time
   - Alert if accuracy degrades
   - Retrain monthly

4. **Risk management:**
   - Position size based on prediction confidence
   - Stop-loss based on MAE
   - Max drawdown limits

---

## LIBRARIES AVAILABLE

### ✅ Have:
- PyTorch 2.8.0
- Pandas 2.1.4
- NumPy 1.26.4

### ❌ Don't Have (but don't need):
- scikit-learn
- XGBoost
- LightGBM
- TensorFlow

**Everything we need is available!**

---

## FINAL CHECKLIST BEFORE TRAINING

- [x] Dataset cleaned (Tasks 1-4)
- [x] Features scaled (Task 5)
- [x] Train/test split created
- [x] No data leakage verified
- [x] PyTorch installed and working
- [x] Architecture defined
- [x] Hyperparameters set
- [x] Success criteria defined
- [x] Timeline estimated
- [ ] **START TRAINING** ← You are here

---

## SUMMARY

### What we're building:
**A 4-layer feed-forward neural network to predict 1-week soybean oil futures returns**

### What we have:
- 1,000 training samples
- 251 test samples
- 98 high-quality features
- All data verified and scaled

### What we expect:
- Directional accuracy: 52-58%
- MAE: 0.025-0.040
- Training time: 2.5-3 hours total

### What makes this production-ready:
- ✅ No fake data
- ✅ No data leakage
- ✅ Proper validation
- ✅ Realistic expectations
- ✅ Clear success criteria

---

## 🚀 READY TO START TRAINING

**Command to execute:**
```bash
python3 train_baseline_model.py
```

**This will:**
1. Load scaled training data
2. Initialize PyTorch model
3. Train for 100 epochs
4. Save best model
5. Generate all outputs
6. Print summary report

**Estimated time:** 30-45 minutes

---

**ALL PREPARATION IS COMPLETE. READY TO TRAIN.**

