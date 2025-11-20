---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# 🔍 L1 Regularization Analysis: Baseline Model

**Model**: `bqml_1m_baseline_exploratory`  
**Current L1**: `0.2`  
**Features**: ~1,500-2,000 (exploratory/discovery model)

---

## 📊 Current Configuration

```sql
l1_reg=0.2,        -- Current setting
l2_reg=0.1,
max_iterations=50,
learn_rate=0.05,
early_stop=TRUE
```

**Feature Count**:
- Base production: ~300 features
- Yahoo symbols: ~1,540 features (220 symbols × 7 indicators)
- Correlations: ~200 features
- Interactions: ~50 features
- **Total: ~1,500-2,000 features**

---

## 🎯 Comparison with Other Models

| Model | Features | L1 | Result | Assessment |
|-------|----------|----|--------|------------|
| **V2** | 334 | 0.1 | ✅ MAE $0.027 | Good for small feature set |
| **V4** | 422 | 1.0 | ✅ MAE $0.031 | Good for medium feature set |
| **V3** | 422 | 15.0 | ❌ MAE $7.65 | Too aggressive |
| **Baseline** | **1,500-2,000** | **0.2** | ❓ **Too low?** | **Needs analysis** |

---

## ⚠️ Problem: L1=0.2 May Be Too Low

### Why This Could Be a Problem

1. **Feature Count**: 1,500-2,000 features is **3-5x more** than V4 (422 features)
2. **Regularization Scale**: L1=0.2 is only **2x V2's 0.1**, but features are **4-6x more**
3. **Risk of Overfitting**: With so many features and low regularization, model might:
   - Overfit to noise
   - Not prune irrelevant features effectively
   - Struggle to identify truly important features

### What We Learned from V2/V3/V4

**Key Insight**: More features typically need **more regularization**, not less.

- **V2**: 334 features, L1=0.1 → ✅ Worked
- **V4**: 422 features, L1=1.0 → ✅ Worked (10x V2's L1 for 1.26x features)
- **Baseline**: 1,500-2,000 features, L1=0.2 → ❓ **Only 2x V2's L1 for 4-6x features!**

**Math Check**:
- V2: 334 features, L1=0.1 → **L1 per feature ≈ 0.0003**
- V4: 422 features, L1=1.0 → **L1 per feature ≈ 0.0024** (8x more)
- Baseline: 1,500 features, L1=0.2 → **L1 per feature ≈ 0.00013** (less than V2!)

---

## 💡 Recommended L1 Values

### Option 1: Conservative (Recommended for Discovery)
```sql
l1_reg=1.0,  -- Same as V4, proven to work
```

**Why**: 
- V4 proved L1=1.0 works well for feature selection
- Baseline has 3-4x more features, so same L1 should still be reasonable
- Won't be too aggressive (unlike V3's 15.0)

### Option 2: Moderate (Balanced)
```sql
l1_reg=2.0,  -- 2x V4, accounts for more features
```

**Why**:
- Accounts for 3-4x more features than V4
- Still moderate (not extreme like V3's 15.0)
- Should prune noise while keeping signal

### Option 3: Aggressive (Maximum Feature Selection)
```sql
l1_reg=5.0,  -- Aggressive but not extreme
```

**Why**:
- For discovery model, you want to find the truly important features
- With 1,500-2,000 features, aggressive pruning might help
- Still 3x less than V3's failed 15.0

---

## 🎯 Recommendation

### For Discovery/Exploratory Model: **L1=1.0 to 2.0**

**Recommended**: **L1=1.5** (balanced approach)

```sql
l1_reg=1.5,  -- Balanced: accounts for more features without being extreme
```

**Reasoning**:
1. ✅ **Proven range**: V4's L1=1.0 worked, so 1.5 is safe
2. ✅ **Accounts for scale**: 1,500 features is 3-4x V4's 422
3. ✅ **Not too aggressive**: Still 10x less than V3's failed 15.0
4. ✅ **Discovery goal**: Will prune noise while keeping important features

### Comparison

| L1 Value | Assessment | Use Case |
|----------|------------|----------|
| **0.2** (current) | ⚠️ **Too low** | Might overfit, won't prune enough |
| **1.0** | ✅ Good | Proven with V4, safe choice |
| **1.5** | ✅ **Best** | Balanced for discovery model |
| **2.0** | ✅ Good | More aggressive pruning |
| **5.0** | ⚠️ Aggressive | Maximum feature selection |
| **15.0** | ❌ Too high | Will fail like V3 |

---

## 📈 Expected Impact

### With L1=0.2 (Current - Too Low)
- ❌ May not prune enough features (keeps 1,200-1,500 features)
- ❌ Risk of overfitting
- ❌ Harder to identify truly important features
- ❌ Longer training time (more features to process)

### With L1=1.5 (Recommended)
- ✅ Prunes to ~300-500 most important features
- ✅ Better feature selection
- ✅ Faster training
- ✅ Clearer feature importance rankings
- ✅ Less overfitting risk

---

## 🔧 Suggested Fix

**Change line 1740** from:
```sql
l1_reg=0.2,
```

**To**:
```sql
l1_reg=1.5,  -- Balanced for 1,500-2,000 feature discovery model
```

**Or** if you want to be more conservative:
```sql
l1_reg=1.0,  -- Same as V4, proven safe
```

---

## ✅ Conclusion

**Current L1=0.2 is TOO LOW** for a model with 1,500-2,000 features.

**Recommended**: **L1=1.5** (or at minimum L1=1.0)

This will:
- ✅ Properly prune irrelevant features
- ✅ Identify truly important features
- ✅ Reduce overfitting risk
- ✅ Match the scale of the feature set

**The baseline model is for discovery** - you want to find which features matter. L1=0.2 won't prune enough to make that clear. L1=1.5 will give you a cleaner signal.

---

_Analysis based on lessons learned from V2, V3, and V4 models_






