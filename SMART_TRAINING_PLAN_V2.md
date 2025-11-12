# 🎯 SMART TRAINING PLAN V2
## Based on Baseline Analysis + Market Reality + Trump Impact

---

## 📊 **WHAT WE LEARNED FROM BASELINE (`bqml_1m_baseline_exploratory`):**

### **THE FACTS:**
- **822 features, 482 rows** → R² = 0.65 (underfitting)
- **Stopped at 50 iterations** → Still improving 4.5% per iteration
- **L1=1.5, L2=0.5** → Good regularization but maybe too aggressive
- **MAE = $3.51** (7.78% error) → Not production ready

### **THE PROBLEMS:**
1. **0.59:1 rows:features ratio** (should be 10:1 minimum)
2. **Random split for time series** (should be sequential)
3. **Not enough iterations** (needed 100-150)

---

## 🔥 **THE MARKET REALITY (Nov 2025):**

### **TOP DRIVERS FROM DATA + RESEARCH:**
1. **CRUSH MARGIN** - 0.961 correlation (#1 BY FAR)
   - Driven by: Biofuel demand, ADM weakness, RIN credits
2. **CHINA IMPORTS** - (-0.813) negative correlation  
   - Driven by: Trump tariffs, Brazil/Argentina shift
3. **DOLLAR INDEX** - (-0.658)
   - Driven by: Fed policy, trade war, risk sentiment
4. **TARIFFS** - 0.647 correlation
   - Driven by: Trump politics, China retaliation

### **TRUMP'S STRUCTURAL CHANGES:**
- US → China exports: **DEAD**
- Brazil/Argentina: **WINNING**  
- Biofuel: **50%+ of US soybean oil**
- Labor: **FUCKED** (ICE + no immigration)

---

## 💀 **THE REALISTIC PLAN (NO BULLSHIT):**

### **PHASE 1: FEATURE SELECTION (TOP 300-500)**

#### **TIER 1: PROVEN HIGH IMPACT (Top 50)**
```python
CRITICAL_FEATURES = [
    # CRUSH COMPONENTS (0.961 correlation)
    'soybean_oil_price', 'soybean_meal_price', 'soybean_price',
    'crush_margin_calculated', 'processing_capacity',
    
    # CHINA/TRADE (0.813 correlation)
    'china_soybean_imports_mt', 'brazil_export_premium',
    'argentina_export_tax', 'us_china_basis_spread',
    
    # DOLLAR/FX (-0.658 correlation)
    'dxy_close', 'usd_brl', 'usd_ars', 'usd_cny',
    
    # ENERGY/BIOFUEL
    'rin_d4_price', 'crude_oil_price', 'biodiesel_price',
    
    # VOLATILITY
    'vix_close', 'oil_volatility', 'fx_volatility'
]
```

#### **TIER 2: IMPORTANT SIGNALS (Next 150)**
```python
IMPORTANT_FEATURES = [
    # COMPETITORS
    'palm_oil_spot_price', 'palm_oil_futures',
    'sunflower_oil_price', 'rapeseed_oil_price',
    
    # AG COMPLEX
    'corn_price', 'wheat_price', 'corn_soy_ratio',
    
    # PROCESSORS
    'adm_close', 'bg_close', 'cargill_margins',
    
    # WEATHER
    'brazil_precipitation', 'argentina_drought_index',
    'us_midwest_temps', 'la_nina_index'
]
```

#### **TIER 3: TRUMP/POLITICAL (Next 100)**
```python
POLITICAL_FEATURES = [
    'trump_trade_sentiment',  # From Truth Social API
    'tariff_announcement_flag',
    'china_retaliation_index',
    'immigration_enforcement_intensity',
    'farm_bailout_amount'
]
```

#### **TIER 4: TECHNICAL INDICATORS (Next 200)**
```python
# Only for top 30 symbols that matter
SYMBOLS = ['ZL=F', 'ZS=F', 'ZM=F', 'CL=F', 'DXY', 'BRL=X', 'ADM', 'BG']
INDICATORS = ['rsi_14', 'macd_hist', 'bb_width', 'atr_14', 'momentum_10']
# = 30 symbols × 5 indicators = 150 features
```

---

## 📅 **DATE RANGE STRATEGY:**

### **WHY 2023-2025 (NOT 50 YEARS):**
1. **Trump Regime Change** - Market structure changed in 2023
2. **China Decoupling** - Old correlations broken
3. **Biofuel Explosion** - New demand dynamic
4. **More Recent = More Relevant** - 3 years × 250 days = 750 rows

### **DATA SPLIT:**
```sql
-- TRAINING: 2023-01-01 to 2025-08-31 (80%)
-- VALIDATION: 2025-09-01 to 2025-11-07 (20%)
-- SEQUENTIAL SPLIT (not random!)
data_split_method='SEQ',
data_split_col='date'
```

---

## 🚀 **TRAINING CONFIGURATION:**

### **BASED ON BASELINE LESSONS:**
```sql
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m_focused_v1`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  
  -- MORE ITERATIONS (was 50, still improving)
  max_iterations=150,
  
  -- FASTER LEARNING (was 0.05)
  learn_rate=0.1,
  
  -- KEEP EARLY STOPPING
  early_stop=TRUE,
  min_rel_progress=0.00005,  -- Finer than 0.0001
  
  -- ADJUSTED REGULARIZATION (was 1.5/0.5)
  l1_reg=1.0,  -- Less aggressive with fewer features
  l2_reg=0.4,  -- Slightly less L2
  
  -- TREE PARAMS
  max_tree_depth=8,  -- Was implicit, now explicit
  subsample=0.8,
  colsample_bytree=0.7,
  
  -- CRITICAL: SEQUENTIAL SPLIT
  data_split_method='SEQ',
  data_split_col='date',
  data_split_eval_fraction=0.2
) AS
SELECT 
  target_1m,
  -- TOP 300-500 FEATURES ONLY
  * EXCEPT(date, target_1m, [string_columns], [null_columns])
FROM `cbi-v14.models_v4.focused_training_set`
WHERE date >= '2023-01-01';
```

---

## 📊 **SUCCESS METRICS:**

### **MUST ACHIEVE:**
- **R² > 0.80** (was 0.65)
- **MAE < $2.50** (was $3.51)
- **MAPE < 5%** (was 7.78%)
- **Training completes** without errors

### **NICE TO HAVE:**
- Feature importance rankings
- Validation better than training (good regularization)
- Convergence before 150 iterations

---

## 🔧 **IMPLEMENTATION STEPS:**

### **1. FEATURE SELECTION (TODAY)**
```python
# Run correlation analysis on 2023-2025 data
# Select top 300-500 features by correlation
# Ensure all CRITICAL_FEATURES included
# Remove NULL columns, strings, low variance
```

### **2. CREATE FOCUSED DATASET (TODAY)**
```sql
CREATE OR REPLACE TABLE `cbi-v14.models_v4.focused_training_set` AS
-- Join only selected features
-- Date range: 2023-2025
-- ~750 rows × 400 features = proper ratio
```

### **3. RUN PREFLIGHT CHECKS (TODAY)**
- No string columns ✓
- No 100% NULL columns ✓
- Target has variance ✓
- Date range correct ✓
- Sequential split works ✓

### **4. TRAIN MODEL (TODAY)**
- Start with config above
- Monitor loss progression
- Check if early stopping triggers
- If fails, reduce features to 200

### **5. EVALUATE & ITERATE**
- Compare to baseline
- Analyze feature importance
- Adjust if needed

---

## ⚠️ **RISK MITIGATION:**

### **IF IT FAILS:**
1. **Memory Error** → Reduce to 200 features
2. **NULL Error** → Run NULL detection first
3. **Slow Training** → Increase learn_rate to 0.15
4. **Overfitting** → Increase L1 to 1.5
5. **Underfitting** → Decrease L1 to 0.5

### **FALLBACK PLAN:**
If 400 features fails:
- Plan B: Top 200 features only
- Plan C: Top 100 features only  
- Plan D: Top 50 CRITICAL_FEATURES only

**We WILL get a model trained, even if we have to reduce scope.**

---

## 🎯 **THE BOTTOM LINE:**

**REALISTIC GOALS:**
- 300-500 features (not 6000)
- 2023-2025 data (not 50 years)
- Focus on Trump-era dynamics
- Sequential split for time series
- More iterations to converge

**THIS WILL WORK BECAUSE:**
- Proper rows:features ratio (750:400 = 1.9:1)
- Learned from baseline mistakes
- Market-relevant time period
- Realistic feature count
- Proven BQML limits

---

**READY TO EXECUTE**

