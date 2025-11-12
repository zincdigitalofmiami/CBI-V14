# Focused Training Pipeline Plan
## 50-100 Feature Optimization Strategy

**Date:** November 2025  
**Goal:** Create optimized training sets with 50-100 features, validate performance, then promote to production models

---

## 🎯 OBJECTIVE

Current production models use 258-300 features. We have **TWO APPROACHES**:

### **APPROACH A: Rich Focused (75-100 Features)** ⭐ RECOMMENDED
1. **Identify top 75-100 features** using data-driven importance rankings
2. **Boost regime-aware features** (FX, Trump policy, ICE, Argentina, tariffs, recent events)
3. **Train rich focused models** with optimized feature sets
4. **Compare performance** vs. current production models
5. **Promote to production** if focused models perform better or equal

**Benefits:** 
- Maximum impact with feature richness
- Captures current market regime (different than a year ago)
- Prioritizes: FX, Trump news/tariffs, ICE/labor, Argentina events, executive orders, deals
- Faster training than 300-feature models
- Better interpretability than full feature set

### **APPROACH B: Explosive (1000+ Features)** 🔥 ALTERNATIVE
1. **Extract maximum features** from 18 high-correlation symbols (1000+ features)
2. **Use DART booster** with aggressive regularization (L1=2.0, L2=1.0)
3. **Column sampling** (colsample_bytree=0.3) - each tree sees 30% of features
4. **Let BQML find the gold** - automatic feature selection via regularization

**Benefits:** Maximum signal extraction, discovers hidden interactions, DART handles overfitting

**This plan focuses on Approach A (Focused), but includes DART configuration as alternative.**

---

## 📋 PIPELINE STAGES

### **STAGE 1: Rich Feature Selection** 
**File:** `bigquery-sql/RICH_FOCUSED_FEATURE_SELECTION.sql` ⭐ USE THIS

**What it does:**
1. Extracts feature importance from existing production models (`bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m`)
2. Aggregates importance scores across all horizons
3. **BOOSTS regime-aware features** (1.2x-1.4x multiplier):
   - FX features: 1.3x boost
   - Trump policy/ICE: 1.4x boost
   - Tariffs/trade: 1.3x boost
   - Argentina: 1.3x boost
   - News/recent events: 1.2x boost
4. Creates ranked list of top 75 features by **boosted** importance
5. **ALWAYS includes rich critical features** (even if not in top 75):
   - **FX (9 features):** dollar_index, usd_cny_rate, usd_brl_rate, usd_ars_rate, fed_funds_rate, treasury_10y_yield, etc.
   - **Trump Policy (9 features):** trump_policy_events, trump_policy_impact_avg/max, trump_policy_7d, trump_events_7d, etc.
   - **ICE Intelligence (6 features):** ice_trump_policy_score, ice_trump_executive_orders, ice_trump_company_deals, etc.
   - **Tariffs (6 features):** trade_war_intensity, china_tariff_rate, tradewar_event_vol_mult, etc.
   - **Argentina (5 features):** argentina_export_tax, argentina_china_sales_mt, argentina_port_congestion, etc.
   - **Recent Events (7 features):** news_intelligence_7d, news_volume_7d, tariff_news_count, etc.
6. Verifies feature availability in production training tables
7. Creates final rich focused feature list (~75-100 features)

**Output Tables:**
- `cbi-v14.models_v4.rich_focused_feature_importance` - Feature rankings (with boosts)
- `cbi-v14.models_v4.rich_focused_feature_list` - Initial feature list (with categories)
- `cbi-v14.models_v4.rich_focused_feature_availability` - Availability check (with categories)
- `cbi-v14.models_v4.rich_focused_feature_list_final` - Final validated list (75-100 features)

**Expected Result:**
- ~75-100 features selected (rich but focused)
- **All regime-aware features included:**
  - FX (9 features): dollar_index, usd_cny_rate, usd_brl_rate, usd_ars_rate, fed_funds_rate, treasury_10y_yield, real_yield, yield_curve, dollar_index_7d_change
  - Trump Policy (9 features): trump_policy_events, trump_policy_impact_avg/max, trump_policy_7d, trump_events_7d, trump_policy_intensity_14d, trump_soybean_sentiment_7d, trump_agricultural_impact_30d, days_since_trump_policy
  - ICE Intelligence (6 features): ice_trump_policy_score, ice_trump_agricultural_mentions, ice_trump_trade_mentions, ice_trump_executive_orders, ice_trump_company_deals, ice_trump_country_deals
  - Tariffs (6 features): trade_war_intensity, trade_war_impact_score, china_tariff_rate, tradewar_event_vol_mult, china_policy_events, china_policy_impact
  - Argentina (6 features): argentina_export_tax, argentina_china_sales_mt, argentina_port_congestion, argentina_vessel_queue, argentina_crisis_score, **arg_crisis_score** (enhanced: vol + debt/GDP)
  - Recent Events (7 features): news_intelligence_7d, news_volume_7d, news_sentiment_avg, china_news_count, tariff_news_count, biofuel_news_count, weather_news_count
- Features verified available in all 4 production tables

---

### **STAGE 2: Create Focused Training Datasets**
**File:** `bigquery-sql/CREATE_FOCUSED_TRAINING_DATASETS.sql`

**What it does:**
1. Creates 4 new training tables with only focused features:
   - `focused_training_data_1w`
   - `focused_training_data_1m`
   - `focused_training_data_3m`
   - `focused_training_data_6m`
2. Selects only the focused features from production tables
3. Filters to recent data (2023-01-01+) for faster training
4. Handles NULLs with COALESCE

**Feature Set (Approximate - will be refined in Stage 1):**
- **Price Features (7):** zl_price_current, zl_price_lag1, zl_price_lag7, return_1d, return_7d, ma_7d, ma_30d
- **Crush Margin (3):** crush_margin, crush_margin_30d_ma, crush_margin_7d_ma
- **China (3):** china_soybean_imports_mt, china_imports_from_us_mt, china_weekly_cancellations_mt
- **Dollar/FX (4):** dollar_index, usd_cny_rate, usd_brl_rate, dollar_index_7d_change
- **Fed/Policy (4):** fed_funds_rate, real_yield, treasury_10y_yield, yield_curve
- **Trade/Tariffs (3):** trade_war_intensity, china_tariff_rate, trump_policy_events
- **Biofuels (2):** feature_biofuel_cascade, feature_biofuel_ethanol
- **Energy (2):** crude_price, wti_7d_change
- **Palm (1):** palm_price, palm_spread
- **VIX/Volatility (5):** vix_level, vix_lag1, vix_lag2, volatility_30d, feature_vix_stress
- **Correlations (4):** corr_zl_vix_7d, corr_zl_vix_30d, corr_zl_palm_7d, corr_zl_crude_7d
- **Big 8 Signals (5):** feature_tariff_threat, feature_china_relations, feature_harvest_pace, feature_geopolitical_volatility, feature_hidden_correlation, big8_composite_score

**Total: ~50-60 core features** (will expand to 75-100 based on importance rankings)

**Output Tables:**
- 4 focused training datasets (one per horizon)
- Each with ~50-100 features (vs. 258-300 in production)

---

### **STAGE 3: Train Focused Models**
**File:** `bigquery-sql/TRAIN_FOCUSED_MODELS.sql`

**What it does:**
1. Trains 4 new focused models:
   - `bqml_focused_1w`
   - `bqml_focused_1m`
   - `bqml_focused_3m`
   - `bqml_focused_6m`
2. Uses optimized hyperparameters with **safety features**:
   - `max_iterations=150` (vs. 100 in production) - **Hard cap prevents runaway training**
   - `subsample=0.85` (vs. default)
   - `max_tree_depth=8` (vs. default)
   - `early_stop=TRUE` - **Auto-stops if no improvement**
   - `min_rel_progress=0.0005` - **Stops if improvement < 0.05% (prevents memorization)**
   - `data_split_eval_fraction=0.2` - **20% validation set for overfitting detection**
3. **Safety Checks:**
   - Training automatically stops if validation loss stops improving
   - BQML monitors for overfitting (validation loss > training loss)
   - Max iterations prevents infinite training loops
4. Evaluates on 2024+ data (same as production evaluation)
5. Compares performance vs. original production models

**Model Configuration (Focused Approach - 50-100 features):**
```sql
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  max_iterations=150,
  subsample=0.85,
  learn_rate=0.1,
  max_tree_depth=8,
  min_tree_child_weight=10,
  early_stop=TRUE,
  min_rel_progress=0.0005,  -- Stop if improvement < 0.05% (safety)
  data_split_method='RANDOM',
  data_split_eval_fraction=0.2  -- 20% validation set
)
```

**Alternative: DART Configuration (For 1000+ features - if we go explosive route):**
```sql
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  booster_type='DART',  -- Dropout for regularization
  dart_normalized_type='FOREST',
  max_iterations=200,
  learn_rate=0.05,
  early_stop=TRUE,
  min_rel_progress=0.0005,  -- Conservative stopping
  l1_reg=2.0,  -- L1 regularization (feature selection)
  l2_reg=1.0,  -- L2 regularization (prevent overfitting)
  subsample=0.7,
  colsample_bytree=0.3,  -- Each tree sees 30% of features
  max_tree_depth=12,
  min_tree_child_weight=10,
  data_split_method='RANDOM',
  data_split_eval_fraction=0.2
)
```

**Output Tables:**
- 4 new focused models
- `cbi-v14.models_v4.focused_model_evaluation` - Performance comparison

**Expected Training Time:**
- ~5-10 minutes per model (faster than 300-feature models)
- Total: ~20-40 minutes for all 4 models

**Safety Features (Auto-Stop Protection):**
- ✅ **Early Stop Enabled:** Training stops if no improvement
- ✅ **Min Progress Threshold:** Stops if improvement < 0.05% (`min_rel_progress=0.0005`)
- ✅ **Validation Split:** 20% of data held out for validation
- ✅ **Max Iterations Cap:** Hard limit at 150 iterations (prevents runaway training)
- ✅ **Automatic Overfitting Detection:** BQML monitors validation loss vs training loss

---

### **STAGE 4: Evaluation & Comparison**
**File:** `bigquery-sql/TRAIN_FOCUSED_MODELS.sql` (includes evaluation)

**What it does:**
1. Evaluates focused models on 2024+ test data
2. Evaluates original production models on same test data
3. Compares metrics:
   - MAE (Mean Absolute Error)
   - RMSE (Root Mean Squared Error)
   - R² (Coefficient of Determination)
   - MAPE (Mean Absolute Percentage Error)

**Success Criteria:**
- ✅ **PROMOTE** if: `focused_mae < original_mae` AND `focused_r2 >= original_r2`
- ⚠️ **CONSIDER** if: `focused_mae <= original_mae * 1.05` AND `focused_r2 >= original_r2 * 0.95`
- ❌ **KEEP ORIGINAL** if: Focused models perform worse

**Expected Results:**
- Focused models should perform **equal or better** (fewer features = less noise)
- Faster training and prediction
- Better interpretability

---

### **STAGE 5: Promote to Production** (OPTIONAL - Only if validated)
**File:** `bigquery-sql/PROMOTE_FOCUSED_TO_PRODUCTION.sql`

**What it does:**
1. **Backs up original models** (logs backup in `production_model_backup_log`)
2. **Replaces production models** with focused versions:
   - `bqml_1w` ← `bqml_focused_1w`
   - `bqml_1m` ← `bqml_focused_1m`
   - `bqml_3m` ← `bqml_focused_3m`
   - `bqml_6m` ← `bqml_focused_6m`
3. Uses same model names (production models are replaced)
4. Validates replacement completed

**⚠️ CRITICAL:** This step **REPLACES** production models. Only run after:
- ✅ Focused models validated to perform equal or better
- ✅ Evaluation results reviewed and approved
- ✅ Backup log created

**Note:** BigQuery doesn't support model renaming, so we use `CREATE OR REPLACE MODEL` with the same name.

---

## 🚀 EXECUTION WORKFLOW

### **Option 1: Automated Pipeline (Recommended)**
```bash
./scripts/run_focused_training_pipeline.sh
```

**What it does:**
1. Runs Stages 1-3 automatically
2. Shows evaluation results
3. **Stops before Stage 5** (promotion) - requires manual approval

### **Option 2: Manual Step-by-Step**
```bash
# Stage 1: Rich Feature Selection (with regime-aware boosting)
bq query --use_legacy_sql=false < bigquery-sql/RICH_FOCUSED_FEATURE_SELECTION.sql

# Stage 2: Create Datasets
bq query --use_legacy_sql=false < bigquery-sql/CREATE_FOCUSED_TRAINING_DATASETS.sql

# Stage 3: Train Models (takes 20-40 minutes)
bq query --use_legacy_sql=false < bigquery-sql/TRAIN_FOCUSED_MODELS.sql

# Review Results
bq query --use_legacy_sql=false \
  "SELECT * FROM \`cbi-v14.models_v4.focused_model_evaluation\` ORDER BY model_name"

# Stage 5: Promote (ONLY IF VALIDATED)
bq query --use_legacy_sql=false < bigquery-sql/PROMOTE_FOCUSED_TO_PRODUCTION.sql
```

---

## 📊 EXPECTED OUTCOMES

### **Feature Reduction:**
- **Before:** 258-300 features per model
- **After:** 75-100 features per model (rich but focused)
- **Reduction:** ~60-70% fewer features
- **Richness:** All regime-aware features included (FX, Trump, ICE, Argentina, tariffs, recent events)

### **Performance Targets:**
- **MAE:** Equal or better than current (~0.40)
- **R²:** Equal or better than current (~0.997)
- **MAPE:** Equal or better than current (~0.76%)

### **Training Benefits:**
- **Faster training:** 5-10 min vs. 10-20 min per model
- **Faster predictions:** Less computation per prediction
- **Better interpretability:** Fewer features = easier to understand
- **Lower risk of overfitting:** Fewer parameters to tune

---

## ⚠️ RISKS & MITIGATION

### **Risk 1: Focused models perform worse**
- **Mitigation:** Keep original models, don't promote
- **Fallback:** Use focused models as ensemble component

### **Risk 2: Missing critical features**
- **Mitigation:** Always include critical features (crush margin, China, dollar, etc.) regardless of ranking
- **Validation:** Feature availability check in Stage 1

### **Risk 3: Production model replacement**
- **Mitigation:** Backup log created before replacement
- **Recovery:** Can retrain original models if needed (data still available)

### **Risk 4: Feature Collinearity** ✅ ADDRESSED
- **Mitigation:** 
  - `CORR_TRIM.sql` removes features with ρ > 0.85
  - De-duplicates policy/trade variants (e.g., china_policy_events vs china_policy_impact)
  - Keeps highest-signal feature per correlation cluster
- **Validation:** Correlation matrix audit before training

### **Risk 5: Scale Dominance** ✅ ADDRESSED
- **Mitigation:**
  - Normalize features to [-1, 1] AFTER boosting
  - Formula: z_score = (feat - mean) / std, then clip to [-1, 1]
  - Prevents boosted features from dominating due to scale
- **Validation:** Feature distribution check post-normalization

### **Risk 6: Lag Misalignment** ✅ ADDRESSED
- **Mitigation:**
  - `LAG_CHECK.sql` verifies t-1 alignment for all event features
  - Use t-1 for all (causal) - features predict future, not current
  - Prevents ghost correlations from lookahead bias
- **Validation:** Lag alignment audit before training

### **Risk 7: Overfitting / Memorization** ✅ ADDRESSED
- **Mitigation:** 
  - `early_stop=TRUE` - Auto-stops when learning plateaus
  - `min_rel_progress=0.0005` - Stops if improvement < 0.05% (prevents memorization)
  - `data_split_eval_fraction=0.2` - 20% validation set monitors overfitting
  - BQML automatically detects when validation loss diverges from training loss
  - Max iterations cap (150) prevents infinite training
- **Monitoring:** Training info shows validation vs training loss - we'll review before promotion

---

## 📈 VALIDATION CHECKLIST

Before promoting to production, verify:

- [ ] Focused models trained successfully (all 4 horizons)
- [ ] Evaluation results show equal or better performance
- [ ] Feature count is 50-100 (not too few, not too many)
- [ ] All critical features included (crush margin, Big 8, etc.)
- [ ] Test set performance validated (2024+ data)
- [ ] Backup log created
- [ ] Manual approval received

---

## 🔄 ROLLBACK PLAN

If focused models underperform:

1. **Keep original models:** Don't run Stage 5
2. **Analyze feature importance:** Review which features were excluded
3. **Iterate:** Add back important excluded features
4. **Retrain:** Create new focused set with adjustments

If production models need restoration:

1. **Retrain original models:** Use full feature set from production tables
2. **Replace models:** Use `CREATE OR REPLACE MODEL` with original config
3. **Verify:** Check predictions match previous behavior

---

## 📝 FILES CREATED

### **Core Pipeline:**
1. **`bigquery-sql/RICH_FOCUSED_FEATURE_SELECTION.sql`** - Rich feature selection with regime-aware boosting ⭐
2. **`bigquery-sql/FOCUSED_FEATURE_SELECTION.sql`** - Basic feature selection (alternative)
3. **`bigquery-sql/CREATE_FOCUSED_TRAINING_DATASETS.sql`** - Dataset creation
4. **`bigquery-sql/TRAIN_FOCUSED_MODELS.sql`** - Model training & evaluation
5. **`bigquery-sql/PROMOTE_FOCUSED_TO_PRODUCTION.sql`** - Production promotion

### **Enhanced Safety & Quality:**
6. **`bigquery-sql/ADD_CRISIS_SCORE.sql`** - Argentina crisis score calculation
7. **`bigquery-sql/CORR_TRIM.sql`** - Correlation trimming (remove ρ > 0.85)
8. **`bigquery-sql/LAG_CHECK.sql`** - Lag alignment verification (t-1 causal)
9. **`bigquery-sql/NORMALIZE_FEATURES.sql`** - Post-boost normalization [-1,1]
10. **`bigquery-sql/CREATE_BOOST_WEIGHTS_LOG.sql`** - Multiplier audit trail

### **Automation:**
11. **`scripts/run_focused_training_pipeline.sh`** - Automated pipeline
12. **`FOCUSED_TRAINING_PLAN.md`** - This document

---

## 🎯 EXECUTION SEQUENCE (ENHANCED - SAFE & AUDITED)

| Step | Action | Validation | Est. Time |
|------|--------|------------|-----------|
| **1** | Run `RICH_FOCUSED_FEATURE_SELECTION.sql` + `ADD_CRISIS_SCORE.sql` | Top 100 includes ≥80% boosted; ρ matrix <0.85 | 10 min |
| **2** | Run `CORR_TRIM.sql` | Remove features with ρ > 0.85 | 5 min |
| **3** | Run `LAG_CHECK.sql` | Verify t-1 alignment for all event features | 5 min |
| **4** | Run `CREATE_BOOST_WEIGHTS_LOG.sql` | Log all multipliers for audit trail | 2 min |
| **5** | Manual inspect output | All regimes represented (FX/policy ≥20%) | 15 min |
| **6** | Generate dataset w/ normalization | Feature count ~100-120; NULL <5% | 20 min |
| **7** | Retrain 1M "rich regime" model | BQML with 200 iter, t-1 lag | 5 min |
| **8** | Compare metrics | MAPE ↓≥10%; Overfit <2.0; SHAP rise 15%+ (FX/policy) | 10 min |
| **9** | Replicate if pass (1W/3M/6M) | Uniform gains; log weights | 15 min |

**Total Estimated Time:** ~87 minutes

### **NEXT STEPS (PRIORITY ORDER):**

1. ✅ **ADD CRISIS_SCORE** → Argentina set (arg_crisis_score)
2. ✅ **RUN CORR_TRIM** → Remove redundant features (ρ > 0.85)
3. ✅ **RUN LAG_CHECK** → Verify t-1 causal alignment
4. ✅ **CREATE BOOST_LOG** → Record all multipliers
5. 🔥 **RUN STEP 1** → Rich feature selection
6. 🔥 **EXECUTE 1M RETRAIN** → Validate gains
7. 🔥 **REPLICATE TO HORIZONS** → Full rollout
8. 🔥 **LOG WEIGHTS** → Audit trail

---

## 🔒 SAFETY FEATURES SUMMARY

**Auto-Stop Protection:**
- ✅ `early_stop=TRUE` - Stops when learning plateaus
- ✅ `min_rel_progress=0.0005` - Stops if improvement < 0.05% (prevents memorization)
- ✅ `max_iterations=150` - Hard cap prevents infinite training
- ✅ `data_split_eval_fraction=0.2` - 20% validation set monitors overfitting
- ✅ BQML automatically detects validation loss divergence

**Before Promotion, We'll Check:**
- Training loss vs validation loss (should be close)
- No signs of overfitting in evaluation metrics
- Performance equal or better than original models

---

**Ready to proceed?** Review the plan, then we can start with Stage 1 (feature selection).

