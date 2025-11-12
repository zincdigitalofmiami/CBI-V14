# 📋 PLAN: bqml_1m_v3 - Optimized with High-Impact Features
**Date**: November 6, 2025  
**Status**: READ ONLY - PLANNING PHASE  
**Purpose**: Add 110 high-correlation features + optimize hyperparameters

---

## 🎯 OBJECTIVE

**Test whether adding high-correlation cross-asset features improves beyond current 80.83%**

Compare:
- **v2**: 334 features, 1,404 rows, 80.83% improvement, R²=0.9941
- **v3**: 444 features, 1,404 rows, optimized BQML config
- **Expected**: 85-92% total improvement (v2's 80% + another 5-12%)

---

## 📊 WHAT'S IN V3

### **Current v2 Features** (334):
- ZL price + volume
- Big 8 signals
- Crush margin (0.961 corr - #1!)
- RIN/biofuel proxies (21 features, -0.60 corr)
- China sentiment
- Trump policy
- Weather (Brazil, Argentina, US)
- CFTC positioning
- Economic indicators (rates, GDP, CPI)
- FX rates (some)
- Correlations (existing ZL-based)
- Social sentiment
- Event indicators
- Seasonal factors

### **NEW Features for v3** (110 additional):

#### **TIER 1: Ultra-High Correlation ETFs** (4 × 10 = 40 features)
**SOYB** (Soybean ETF, 0.92 corr):
```
1. soyb_close
2. soyb_ma_7d
3. soyb_ma_30d
4. soyb_ma_200d
5. soyb_rsi_14
6. soyb_macd_line
7. soyb_bb_upper
8. soyb_bb_width
9. soyb_atr_14
10. soyb_momentum_10
```

**CORN** (Corn ETF, 0.88 corr):
```
11-20. Same 10 features as SOYB
```

**WEAT** (Wheat ETF, 0.82 corr):
```
21-30. Same 10 features
```

**Rationale**: These ETFs track the actual commodities with high liquidity. Their technicals capture trader sentiment better than futures alone.

#### **TIER 2: Ag Stock Fundamentals** (5 stocks × 5 = 25 features)
**ADM** (0.78 corr - largest US crusher):
```
31. adm_close
32. adm_pe_ratio (valuation signal)
33. adm_beta (risk sensitivity)
34. adm_analyst_target (price target)
35. adm_market_cap (company size)
```

**BG** (Bunge, 0.76 corr - global crusher/trader):
```
36-40. Same 5 features
```

**NTR** (Nutrien, 0.72 corr - fertilizer = planting intentions):
```
41-45. Same 5 features
```

**DAR** (Darling, 0.72 corr - rendered fats compete with soy oil):
```
46-50. Same 5 features
```

**TSN** (Tyson, 0.68 corr - meal demand for livestock):
```
51-55. Same 5 features
```

**Rationale**: Stock prices incorporate forward-looking information (earnings, guidance, analyst research). PE ratios show sector valuation regime. Analyst targets show professional forecasts.

#### **TIER 3: Energy & Industrial Demand** (5 symbols × 5 = 25 features)
**BZ=F** (Brent Crude, 0.75 corr - global benchmark):
```
56. brent_close
57. brent_rsi_14
58. brent_macd_line
59. brent_ma_30d
60. brent_ma_200d
```

**HG=F** (Copper, 0.65 corr - industrial demand "Dr. Copper"):
```
61-65. Same 5 features
```

**NG=F** (Natural Gas, 0.62 corr - ethanol production cost):
```
66. natgas_close
67. natgas_rsi_14
68. natgas_ma_30d
69. natgas_momentum_10
70. natgas_rate_of_change_10
```

**CF** (CF Industries, 0.68 corr - fertilizer/ag input costs):
```
71-75. Same 5 features as ADM
```

**MOS** (Mosaic, 0.70 corr - fertilizer demand):
```
76-80. Same 5 features
```

**Rationale**: Energy costs affect biofuel economics. Industrial demand (copper) signals global growth. Fertilizer stocks show planting economics.

#### **TIER 4: Dollar Drivers** (4 FX × 5 = 20 features)
**DX-Y.NYB** (Dollar Index, -0.658 corr - export competitiveness):
```
81. dxy_close
82. dxy_rsi_14
83. dxy_macd_line
84. dxy_ma_30d
85. dxy_ma_200d
```

**BRLUSD=X** (Brazil Real, -0.60 corr - competitor currency):
```
86. brlusd_close
87. brlusd_rsi_14
88. brlusd_ma_30d
89. brlusd_momentum_10
90. brlusd_rate_of_change_10
```

**CNYUSD=X** (China Yuan, -0.50 corr - buyer currency):
```
91-95. Same 5 features
```

**MXNUSD=X** (Mexico Peso, -0.45 corr - regional trade):
```
96-100. Same 5 features
```

**Rationale**: Dollar strength directly affects US export prices. Brazil/Argentina currency weakness makes their exports cheaper (competition). China currency affects buying power.

#### **BONUS: VIX & Credit** (2 × 5 = 10 features)
**^VIX** (Volatility, 0.398 corr - risk regime):
```
101. vix_close (already have vix_level, but add Yahoo version for comparison)
102. vix_rsi_14
103. vix_ma_30d
104. vix_macd_line
105. vix_bb_upper
```

**HYG** (High Yield Credit, -0.58 corr - risk appetite):
```
106. hyg_close
107. hyg_rsi_14
108. hyg_ma_30d
109. hyg_macd_line
110. hyg_bb_width
```

**Rationale**: VIX shows market stress (affects all commodities). Credit spreads show risk appetite (tight = bullish, wide = bearish).

---

## 🔧 OPTIMIZED HYPERPARAMETERS

### **Current v2 Config**:
```sql
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m_v2`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1m'],
  max_iterations=100,
  learn_rate=0.1,
  early_stop=FALSE,
  l1_reg=0.1,
  l2_reg=0.1
) AS SELECT...
```

**What's missing**: No DART, no sampling, default tree depth, no parallel trees

### **Proposed v3 Config** (JP Morgan-caliber):
```sql
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m_v3`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1m'],
  
  -- ============================================
  -- CORE ALGORITHM OPTIMIZATION
  -- ============================================
  booster_type='DART',              -- NEW: Dropout Additive Regression Trees
                                     -- Prevents overfitting with 444 features
                                     -- Adds dropout between tree iterations
  
  tree_method='HIST',                -- NEW: Histogram-based splitting
                                     -- Faster for 400+ features
                                     -- More memory efficient
  
  -- ============================================
  -- TRAINING ITERATIONS
  -- ============================================
  max_iterations=150,                -- INCREASED from 100
                                     -- More features = need more trees
                                     -- Balanced: not too slow, not underfitted
  
  learn_rate=0.05,                   -- DECREASED from 0.1
                                     -- Slower learning = better convergence
                                     -- Prevents overshooting with 444 features
  
  early_stop=FALSE,                  -- KEEP: Run full iterations for stability
  
  -- ============================================
  -- REGULARIZATION (Prevent Overfitting)
  -- ============================================
  l1_reg=0.15,                       -- INCREASED from 0.1
                                     -- Lasso regularization
                                     -- Pushes weak features to 0
  
  l2_reg=0.15,                       -- INCREASED from 0.1
                                     -- Ridge regularization
                                     -- Shrinks all coefficients
  
  min_split_loss=0.02,               -- NEW: Minimum gain to create split
                                     -- Prevents tiny meaningless splits
  
  -- ============================================
  -- TREE STRUCTURE
  -- ============================================
  max_tree_depth=10,                 -- NEW: INCREASED from default 6
                                     -- Deeper trees capture interactions
                                     -- E.g., (DXY × BRL/USD) × crude_rsi
  
  min_tree_child_weight=5,           -- NEW: Leaf regularization
                                     -- Requires 5+ samples per leaf
                                     -- Prevents overfitting to outliers
  
  -- ============================================
  -- SAMPLING (Ensemble Diversity)
  -- ============================================
  subsample=0.8,                     -- NEW: Use 80% of rows per tree
                                     -- Each tree sees different data
                                     -- Reduces overfitting
  
  colsample_bytree=0.7,              -- NEW: Use 70% of features per tree
                                     -- Forces trees to use different features
                                     -- Increases ensemble diversity
                                     -- Lower than subsample for 444 features
  
  num_parallel_tree=3,               -- NEW: Build 3 trees per iteration
                                     -- Ensemble within ensemble
                                     -- Like Random Forest + Boosting
  
  -- ============================================
  -- DART-SPECIFIC OPTIONS
  -- ============================================
  dart_normalized_type='FOREST',    -- NEW: Normalize over all trees
                                     -- vs 'TREE' (per-tree normalization)
                                     -- Better for large ensembles
  
  -- ============================================
  -- BQML ENHANCEMENTS
  -- ============================================
  enable_global_explain=TRUE,        -- NEW: Get feature importance
                                     -- SHAP-like values
                                     -- For daily email "key drivers"
  
  data_split_method='RANDOM',        -- NEW: Random train/eval split
                                     -- vs sequential (time-based)
                                     -- Better for cross-validation
  
  data_split_eval_fraction=0.2       -- NEW: Hold out 20% for validation
                                     -- ~280 rows for evaluation
                                     -- Prevents overfitting
) AS
SELECT 
  target_1m,
  * EXCEPT([...all exclusions including NULL columns...])
FROM `cbi-v14.models_v4.production_training_data_1m`
WHERE target_1m IS NOT NULL
  AND date >= '2020-01-01';
```

### **Hyperparameter Comparison**:

| Parameter | v2 (Current) | v3 (Proposed) | Rationale |
|-----------|--------------|---------------|-----------|
| **booster_type** | GBTREE (default) | **DART** | Dropout regularization for 444 features |
| **tree_method** | AUTO | **HIST** | Faster for large feature sets |
| **max_iterations** | 100 | **150** | More features need more trees |
| **learn_rate** | 0.1 | **0.05** | Slower = better convergence |
| **l1_reg** | 0.1 | **0.15** | Stronger Lasso for feature selection |
| **l2_reg** | 0.1 | **0.15** | Stronger Ridge for stability |
| **max_tree_depth** | 6 (default) | **10** | Capture complex interactions |
| **subsample** | 1.0 (default) | **0.8** | Row sampling prevents overfitting |
| **colsample_bytree** | 1.0 (default) | **0.7** | Feature sampling for diversity |
| **num_parallel_tree** | 1 (default) | **3** | Ensemble boost |
| **enable_global_explain** | FALSE | **TRUE** | Get feature importance |
| **data_split_eval_fraction** | N/A | **0.2** | Built-in validation set |

---

## 📐 SCHEMA COMPARISON

### **v2 Schema** (334 columns):
```
= Base features (300)
+ Yahoo technical indicators (11): ma_50d, ma_100d, ma_200d, Bollinger, ATR
+ RIN/biofuel features (23): proxies, spreads, margins, ratios
= 334 total
```

### **v3 Schema** (444 columns):
```
= v2 features (334)
+ TIER 1 ETFs (40): SOYB, CORN, WEAT (close, MAs, RSI, MACD, Bollinger, ATR)
+ TIER 2 Ag Stocks (25): ADM, BG, NTR, DAR, TSN (close, PE, beta, analyst target, market cap)
+ TIER 3 Energy/Industrial (25): Brent, Copper, NG, CF, MOS (close, RSI, MACD, MAs, momentum)
+ TIER 4 Dollar/FX (20): DXY, BRL/USD, CNY/USD, MXN/USD (close, RSI, MACD, MAs, momentum)
= 444 total

BQML will auto-select top ~350 most important features
```

### **Feature Details**:

**TIER 1 Features** (Ultra-high corr 0.82-0.92):
| Symbol | Corr | Features Added |
|--------|------|----------------|
| SOYB | 0.92 | close, ma_7d, ma_30d, ma_200d, rsi_14, macd_line, bb_upper, bb_width, atr_14, momentum_10 |
| CORN | 0.88 | Same 10 features |
| WEAT | 0.82 | Same 10 features |
| (DBA skipped - not in dataset) | - | - |

**TIER 2 Features** (High corr 0.72-0.78):
| Symbol | Corr | Features Added |
|--------|------|----------------|
| ADM | 0.78 | close, pe_ratio, beta, analyst_target_price, market_cap |
| BG | 0.76 | Same 5 features |
| NTR | 0.72 | Same 5 features |
| DAR | 0.72 | Same 5 features |
| TSN | 0.68 | Same 5 features |

**TIER 3 Features** (Moderate-high corr 0.62-0.75):
| Symbol | Corr | Features Added |
|--------|------|----------------|
| BZ=F (Brent) | 0.75 | close, rsi_14, macd_line, ma_30d, ma_200d |
| HG=F (Copper) | 0.65 | Same 5 features |
| NG=F (Nat Gas) | 0.62 | close, rsi_14, ma_30d, momentum_10, rate_of_change_10 |
| CF | 0.68 | close, pe_ratio, beta, analyst_target, market_cap |
| MOS | 0.70 | Same 5 features |

**TIER 4 Features** (Dollar drivers -0.50 to -0.658):
| Symbol | Corr | Features Added |
|--------|------|----------------|
| DX-Y.NYB | -0.658 | close, rsi_14, macd_line, ma_30d, ma_200d |
| BRLUSD=X | -0.60 | close, rsi_14, ma_30d, momentum_10, rate_of_change_10 |
| CNYUSD=X | -0.50 | Same 5 features |
| MXNUSD=X | -0.45 | Same 5 features |

**VIX & Credit**:
| Symbol | Corr | Features Added |
|--------|------|----------------|
| ^VIX | 0.398 | close (as vix_yahoo), rsi_14, ma_30d, macd_line, bb_upper |
| HYG | -0.58 | close, rsi_14, ma_30d, macd_line, bb_width |

---

## 🧮 TRAINING CONFIGURATION

### **Data**:
- **Source**: `production_training_data_1m` (current, 1,404 rows)
- **Date Range**: 2020-01-01 to 2025-11-06 (5.8 years)
- **Features**: 444 (after adding 110 new)
- **NULL Exclusions**: ~25 columns (automated scan)
- **Usable Features**: ~419 (444 - 25 NULLs)

### **Validation**:
- **Hold-out Window**: 2024-01-01 to 2025-11-06 (same as v2 for comparison)
- **Hold-out Size**: ~365 days
- **Training Size**: ~1,039 rows (2020-2023)
- **Built-in Split**: 20% additional eval split within training data

### **Training Time**:
- **v2**: 7 minutes (100 iterations, 334 features)
- **v3 Expected**: 12-15 minutes (150 iterations, 444 features, DART slower than GBTREE)

---

## 📈 EXPECTED OUTCOMES

### **Scenario 1: Further Improvement** (Best Case)
- **v2 MAE**: $0.23 (80.83% vs baseline)
- **v3 MAE**: $0.20-0.22 (85-90% vs baseline)
- **Incremental gain**: 5-10% on top of v2
- **Mechanism**: High-corr ETFs + ag stock fundamentals capture regime shifts

### **Scenario 2: Same Performance** (Neutral)
- **v3 MAE**: $0.23 (matches v2)
- **Incremental gain**: 0%
- **Interpretation**: BQML already captured signal with existing 334 features
- **Value**: Confirms we're not missing critical drivers

### **Scenario 3: Slight Degradation** (Unlikely but possible)
- **v3 MAE**: $0.24-0.25 (still 78-79% vs baseline)
- **Cause**: Overfitting from too many features
- **Mitigation**: DART regularization + sampling should prevent this
- **Action**: Stick with v2 if this happens

---

## 🔬 VALIDATION METRICS TO COMPARE

| Metric | v2 (Baseline) | v3 (Target) | Comparison |
|--------|---------------|-------------|------------|
| **MAE** | $0.2298 | ≤$0.22 | v3 better or equal |
| **MSE** | 0.2289 | ≤0.22 | v3 better or equal |
| **R²** | 0.9941 | ≥0.9941 | v3 maintains or improves |
| **Median AE** | $0.115 | ≤$0.12 | Consistency check |
| **Training Time** | 7 min | 12-15 min | Acceptable tradeoff |
| **Features Used** | ~314 (after NULL exclusions) | ~419 | 33% more features |
| **Feature Importance** | N/A | Top 20 from SHAP | New insight |

**Success Criteria**:
- ✅ **MAE ≤$0.25** (maintain v2 performance minimum)
- ✅ **R² ≥0.993** (maintain high variance explanation)
- ✅ **No overfitting** (eval loss ≤ train loss × 1.2)

---

## 📋 EXECUTION PLAN (READ ONLY)

### **Step 1: Schema Expansion** (Add 110 columns)
```sql
ALTER TABLE `cbi-v14.models_v4.production_training_data_1m`
ADD COLUMN IF NOT EXISTS soyb_close FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_ma_7d FLOAT64,
-- ... (repeat for all 110 features)
ADD COLUMN IF NOT EXISTS hyg_bb_width FLOAT64;
```

**Estimated time**: 2-3 minutes

### **Step 2: Data Integration** (Populate 110 columns)
**Approach**: Extract from `yahoo_finance_complete_enterprise` and UPDATE production

**For each symbol**:
```sql
UPDATE `cbi-v14.models_v4.production_training_data_1m` t
SET 
  soyb_close = y.close,
  soyb_ma_7d = y.ma_7d,
  soyb_ma_30d = y.ma_30d,
  -- ...all 10 features...
FROM (
  SELECT 
    DATE(TIMESTAMP_MICROS(CAST(date AS INT64))) as date,
    close, ma_7d, ma_30d, ma_200d, rsi_14, macd_line,
    bb_upper, bb_width, atr_14, momentum_10
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_finance_complete_enterprise`
  WHERE symbol = 'SOYB'
) y
WHERE t.date = y.date;
```

**Repeat for**: CORN, WEAT, ADM, BG, NTR, DAR, TSN, BZ=F, HG=F, NG=F, CF, MOS, DX-Y.NYB, BRLUSD=X, CNYUSD=X, MXNUSD=X, ^VIX, HYG

**Estimated time**: 15-20 minutes (18 symbols × ~1 min each)

### **Step 3: NULL Scan** (Identify new NULL columns)
Run Python scan to find any 100% NULL columns in the 110 new features

**Expected**: Most should be 90%+ filled (only gaps for IPO dates, ETF launch dates)

**Estimated time**: 2 minutes

### **Step 4: Train v3** (DO NOT EXECUTE - just planning)
```sql
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m_v3`
OPTIONS([...optimized config above...])
AS
SELECT 
  target_1m,
  * EXCEPT([...all NULL columns + exclusions...])
FROM `cbi-v14.models_v4.production_training_data_1m`
WHERE target_1m IS NOT NULL AND date >= '2020-01-01';
```

**Estimated time**: 12-15 minutes

### **Step 5: Evaluation & Comparison**
```sql
-- Compare v2 vs v3
WITH v2_metrics AS (
  SELECT 'v2' as model, * 
  FROM ML.EVALUATE(MODEL `bqml_1m_v2`, ...)
),
v3_metrics AS (
  SELECT 'v3' as model, *
  FROM ML.EVALUATE(MODEL `bqml_1m_v3`, ...)
)
SELECT * FROM v2_metrics
UNION ALL
SELECT * FROM v3_metrics;
```

**Estimated time**: 2 minutes

### **Step 6: Feature Importance Analysis**
```sql
-- Get top features from v3
SELECT 
  feature,
  importance_gain,
  importance_weight
FROM ML.FEATURE_INFO(MODEL `bqml_1m_v3`)
ORDER BY importance_gain DESC
LIMIT 20;
```

**Interpretation**: Should see RIN proxies, SOYB, CORN, ADM, DXY in top 20

---

## ⏱️ TOTAL EXECUTION TIME

| Phase | Time | Cumulative |
|-------|------|------------|
| Schema expansion | 3 min | 3 min |
| Data integration | 20 min | 23 min |
| NULL scan | 2 min | 25 min |
| Training v3 | 15 min | 40 min |
| Evaluation | 2 min | 42 min |
| **TOTAL** | **~45 minutes** | - |

---

## 🎯 SUCCESS CRITERIA

**v3 is successful if**:
- ✅ MAE ≤$0.22 (better than v2's $0.23)
- ✅ R² ≥0.9941 (matches or beats v2)
- ✅ Feature importance shows new features in top 30
- ✅ No overfitting (eval loss < train loss × 1.2)
- ✅ Predictions reasonable (no outliers, smooth distribution)

**v3 is acceptable if**:
- ✅ MAE ≤$0.25 (within 10% of v2)
- ✅ R² ≥0.993 (close to v2)

**v3 fails if**:
- ❌ MAE >$0.25 (worse than v2)
- ❌ R² <0.99 (significant degradation)
- ❌ Overfitting detected (eval >> train)

**If v3 fails**: Revert to v2, investigate feature selection

---

## 💡 EXPECTED INSIGHTS FROM v3

### **Feature Importance** (what we'll learn):
1. **Do ETF technicals beat commodity futures?** (SOYB vs ZL)
2. **Do ag stock fundamentals predict prices?** (ADM PE ratio, analyst targets)
3. **Which dollar driver matters most?** (DXY vs BRL vs CNY)
4. **Is copper really "Dr. Copper"?** (Industrial demand signal)
5. **Do credit spreads predict commodity moves?** (HYG vs ZL correlation)

### **Incremental Value**:
- If SOYB ranks top 10 → ETFs better than futures for signal
- If ADM PE ranks top 20 → Fundamentals add value
- If DXY RSI ranks high → Technical FX matters more than spot
- If new features NOT in top 50 → We're not missing much with v2

---

## 🚀 RECOMMENDATION

### **My Proposal**:

1. ✅ **Execute v3 plan** (add 110 features + optimize hyperparameters)
2. ✅ **Compare v3 vs v2** objectively
3. ✅ **Deploy the BETTER model** to production (replace bqml_1m)
4. ✅ **Document learnings** for v4/full backfill

**Why**: 
- Low risk (only 45 minutes)
- High learning (confirms which features matter)
- Objective comparison (data-driven decision)
- Incremental approach (v2 → v3 → full backfill)

**Alternative**: Skip v3, go straight to full 6.3K-row backfill with all features

---

**STATUS**: ✅ PLAN COMPLETE - READY FOR YOUR REVIEW  
**EXECUTION**: ⏳ AWAITING YOUR APPROVAL  
**ESTIMATED TIME**: 45 minutes for v3  
**EXPECTED OUTCOME**: 85-92% improvement vs baseline (if features add value)







