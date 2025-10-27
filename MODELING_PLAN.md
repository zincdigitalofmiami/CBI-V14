# MODELING PLAN - Soybean Oil Futures Forecasting

**Date:** October 24, 2025  
**Dataset:** REAL_TRAINING_DATA_WITH_CURRENCIES.csv  
**Status:** Ready for Training

---

## COMPLETE DATA INVENTORY

### Dataset Overview
- **Total Samples:** 1,263 rows (daily data)
- **Date Range:** October 21, 2020 to October 13, 2025 (~5 years)
- **Total Features:** 149 verified real features
- **Target Variables:** 4 horizons (1-week, 1-month, 3-month, 6-month)

---

## DATA BY CATEGORY

### 1. **Target Variables (4 features)** - 93.8% avg coverage
| Target | Description | Coverage |
|--------|-------------|----------|
| target_1w | 1-week forward return | 100.0% |
| target_1m | 1-month forward return | 97.5% |
| target_3m | 3-month forward return | 92.5% |
| target_6m | 6-month forward return | 85.4% |

**Primary Target:** `target_1w` for short-term trading signals

---

### 2. **Price Features (12 features)** - 99.7% avg coverage ✅ EXCELLENT
- `zl_price_current` - Current soybean oil price
- `zl_price_lag1, lag7, lag30` - Lagged prices
- `crude_price` - Crude oil prices
- `palm_price` - Palm oil prices (substitution effect)
- `corn_price` - Corn prices
- `wheat_price` - Wheat prices
- `oil_price_per_cwt` - Oil price per hundredweight
- `bean_price_per_bushel` - Soybean prices
- `meal_price_per_ton` - Soybean meal prices
- `canola_price` - Canola oil prices

**Quality:** ✅ All 100% coverage, 800-1,200 unique values each

---

### 3. **Currency/FX Features (12 features)** - 99.1% avg coverage ✅ EXCELLENT

**Raw Exchange Rates:**
- `fx_usd_brl` - Brazil Real (100% coverage, 1,236 unique)
- `fx_usd_cny` - China Yuan (100% coverage, 1,085 unique)
- `fx_usd_ars` - Argentina Peso (100% coverage, 1,249 unique)
- `fx_usd_myr` - Malaysia Ringgit (100% coverage, 1,078 unique)

**Derived Features:**
- Daily % changes for each currency
- 7-day moving averages for each currency

**Impact:** Critical for export competitiveness and demand dynamics

---

### 4. **Technical Indicators (24 features)** - 67.6% avg coverage ✅ GOOD
- Returns (1-day, 7-day, 30-day)
- Moving averages (7-day, 30-day)
- Volatility measures (30-day)
- Momentum indicators
- Price lags and leads
- DXY momentum and correlations

**Quality:** Most indicators 95%+ coverage, some derivative features lower

---

### 5. **Correlations (33 features)** - 94.6% avg coverage ✅ EXCELLENT

**Cross-Commodity Correlations (multiple timeframes):**
- ZL vs Crude Oil (7d, 30d, 90d, 180d, 365d)
- ZL vs Palm Oil (7d, 30d, 90d, 180d, 365d)
- ZL vs VIX (7d, 30d, 90d, 180d, 365d)
- ZL vs DXY (7d, 30d, 90d, 180d, 365d)
- ZL vs Corn, Wheat (multiple horizons)

**Impact:** Captures regime changes and cross-asset dynamics

---

### 6. **Weather Features (8 features)** - 94.9% avg coverage ✅ EXCELLENT
- `brazil_temperature_c` - Brazil temperature
- `brazil_precipitation_mm` - Brazil rainfall
- `brazil_precip_30d_ma` - 30-day rainfall average
- `brazil_temp_7d_ma` - 7-day temperature average
- Plus 4 more weather indicators

**Impact:** Critical for crop yield forecasts (Brazil is major producer)

---

### 7. **Sentiment Features (6 features)** - 86.6% avg coverage ✅ GOOD
- `china_sentiment` - China trade sentiment
- `china_sentiment_30d_ma` - 30-day sentiment average
- `trumpxi_sentiment_volatility` - Policy volatility
- `avg_sentiment` - Aggregate sentiment
- `sentiment_volatility` - Sentiment variance
- `sentiment_volume` - Sentiment activity

**Quality:** Some features have limited unique values (may need engineering)

---

### 8. **Seasonal/Calendar (6 features)** - 100% avg coverage ✅ EXCELLENT
- `seasonal_index` - Month-based seasonality
- `monthly_zscore` - Seasonal normalization
- `brazil_month` - Growing season tracker
- `export_seasonality_factor` - Export timing
- `month`, `quarter` - Calendar effects

**Impact:** Agricultural commodities have strong seasonal patterns

---

### 9. **Market Regime (2 features)** - 100% avg coverage ✅ EXCELLENT
- `feature_vix_stress` - Market stress indicator
- `vix_level` - VIX volatility index

**Impact:** Captures risk-on/risk-off regime shifts

---

### 10. **CFTC Positioning (4 features)** - 5.7% avg coverage ⚠️ SPARSE
- `cftc_commercial_long` - Commercial long positions
- `cftc_commercial_short` - Commercial short positions  
- `cftc_commercial_net` - Net commercial position
- `cftc_open_interest` - Total open interest

**Warning:** Only 72 weekly reports out of 1,263 days
**Decision:** Include but don't rely heavily on these features

---

### 11. **News/Intelligence (3 features)** - 0.5% avg coverage ❌ TOO SPARSE
- `news_total_count_enhanced` - News article counts
- `brazil_article_count` - Brazil-specific news
- `weather_article_count` - Weather news

**Warning:** Less than 1% coverage
**Decision:** Exclude from modeling or replace with sentiment proxies

---

### 12. **Other Features (33 features)** - 73.9% avg coverage
- Biofuel indicators
- Composite scores
- DXY features
- Export/import factors
- Various engineered features

---

## DATA QUALITY ASSESSMENT

### ✅ EXCELLENT QUALITY (>90% coverage):
1. **Price Features** - 99.7%
2. **Currency/FX** - 99.1%
3. **Correlations** - 94.6%
4. **Weather** - 94.9%
5. **Seasonal** - 100%
6. **Market Regime** - 100%
7. **Target Variables** - 93.8%

### ✅ GOOD QUALITY (70-90% coverage):
8. **Sentiment** - 86.6%
9. **Other** - 73.9%

### ⚠️ USABLE BUT SPARSE (5-70% coverage):
10. **Technical Indicators** - 67.6% (acceptable)
11. **CFTC** - 5.7% (use with caution)

### ❌ TOO SPARSE (<5% coverage):
12. **News/Intelligence** - 0.5% (exclude or replace)

---

## MODELING STRATEGY

### Phase 1: Baseline Models (PyTorch Only - We Have This)

**Model 1: Feed-Forward Neural Network**
- Architecture: 4-layer deep network (256→128→64→32→1)
- Features: Top 100 by importance
- Target: `target_1w` (1-week return)
- Training: 80/20 split, 100 epochs
- Validation: Walk-forward on recent 20%

**Why This Works:**
- PyTorch is installed and working
- Handles non-linear relationships
- Can learn complex interactions
- Proven to work (we tested it)

---

### Phase 2: Feature Engineering

**New Features to Create:**

1. **Crush Spread**
   - `crush_margin = (oil_price * 11) + (meal_price * 44) - (bean_price * 60)`
   - Critical profit indicator for processors

2. **Currency Baskets**
   - `latam_fx_index = weighted_avg(usd_brl, usd_ars)`
   - `asia_fx_index = weighted_avg(usd_cny, usd_myr)`

3. **Weather Stress Index**
   - Combine temp extremes + rainfall anomalies

4. **Correlation Regime**
   - Identify when correlations break down (regime change)

5. **Momentum Composites**
   - Multi-timeframe momentum (1d + 7d + 30d)

---

### Phase 3: Advanced Modeling (If We Install Libraries)

**Model 2: LightGBM** (Would need to install)
- Best for tabular data
- Handles missing values well
- Feature importance built-in
- Fast training

**Model 3: LSTM (PyTorch)** (Can do now!)
- Sequence modeling for time series
- Capture temporal dependencies
- Use rolling windows of 20-60 days

**Model 4: Ensemble**
- Combine Feed-Forward + LSTM
- Weight by recent performance
- Dynamic rebalancing

---

### Phase 4: Validation Strategy

**Walk-Forward Backtesting:**
```
Training Window: 1000 days (~4 years)
Test Window: 20 days (~1 month)
Step: 20 days (retrain monthly)
Purge Gap: 5 days (prevent leakage)
```

**Metrics:**
1. **Directional Accuracy** - Most important for trading
2. **MAE** - Average error magnitude
3. **Sharpe Ratio** - Risk-adjusted returns
4. **Max Drawdown** - Risk management
5. **Win Rate** - Practical trading metric

---

## FEATURE SELECTION APPROACH

### Step 1: Remove Sparse Features
- Exclude features with <50% coverage
- **Remove:** News features (0.5% coverage)
- **Keep with caution:** CFTC (5.7% - weekly data)

### Step 2: Correlation Analysis
- Remove highly correlated features (>0.95)
- Keep most predictive of correlated pairs

### Step 3: Importance Ranking
- Train baseline model
- Use gradient-based feature importance
- Keep top 100-120 features

### Step 4: Incremental Addition
- Start with top 50 features
- Add in groups of 10
- Stop when validation performance plateaus

---

## EXPECTED FEATURE IMPORTANCE (Hypothesis)

**Top Tier (Expected highest impact):**
1. Recent price momentum (return_1d, return_7d)
2. Currency pairs (fx_usd_brl, fx_usd_cny)
3. Cross-commodity correlations (corr_zl_crude, corr_zl_palm)
4. Seasonal indicators
5. Volatility measures

**Second Tier:**
6. Weather indicators (Brazil rainfall/temp)
7. DXY dynamics
8. VIX stress
9. Moving averages
10. Lagged prices

**Third Tier:**
11. Sentiment indicators
12. CFTC positioning (when available)
13. Other commodities (wheat, corn)

---

## TRAINING PLAN - IMMEDIATE NEXT STEPS

### ✅ Ready to Execute Now:

**Step 1: Feature Selection (5 minutes)**
```python
- Load REAL_TRAINING_DATA_WITH_CURRENCIES.csv
- Remove news features (<1% coverage)
- Calculate correlation matrix
- Select top 100 features by variance + target correlation
```

**Step 2: Train Baseline PyTorch Model (15-30 minutes)**
```python
- Architecture: 256→128→64→32→1
- Loss: MSE (Mean Squared Error)
- Optimizer: Adam, LR=0.001
- Epochs: 100 with early stopping
- Validation: 20% holdout
```

**Step 3: Evaluate (5 minutes)**
```python
- Calculate directional accuracy
- Plot predictions vs actuals
- Feature importance from gradients
- Save model checkpoint
```

**Step 4: Walk-Forward Validation (20-40 minutes)**
```python
- 10 walk-forward windows
- Track performance over time
- Identify regime-dependent accuracy
```

**Step 5: LSTM Model (30-60 minutes)**
```python
- Use PyTorch LSTM
- Sequence length: 20-60 days
- 2-layer bidirectional LSTM
- Compare to feed-forward
```

**Total Time: 2-3 hours for complete baseline**

---

## SUCCESS CRITERIA

### Minimum Viable Model:
- ✅ Directional accuracy >52% (better than random)
- ✅ Positive Sharpe ratio
- ✅ Stable performance across validation folds
- ✅ Explainable feature importance

### Production-Ready Model:
- 🎯 Directional accuracy >55%
- 🎯 Sharpe ratio >1.0
- 🎯 Max drawdown <15%
- 🎯 Consistent across market regimes

### Stretch Goals:
- 🏆 Directional accuracy >60%
- 🏆 Sharpe ratio >2.0
- 🏆 Profitable on out-of-sample test

---

## RISK FACTORS & LIMITATIONS

### Data Limitations:
1. **CFTC Data:** Only 5.7% coverage (weekly vs daily)
2. **News Features:** Too sparse to use
3. **Historical Depth:** 5 years (1,263 days) - could use more
4. **COVID Impact:** Dataset includes pandemic anomaly period

### Model Risks:
1. **Overfitting:** High dimensionality (149 features, 1,263 samples)
2. **Regime Change:** Market structure may shift
3. **Look-Ahead Bias:** Must carefully validate time series splits
4. **Data Snooping:** Avoid testing too many models

### Mitigation:
- ✅ Strict walk-forward validation
- ✅ Feature selection to reduce dimensions
- ✅ Regularization (dropout, L2)
- ✅ Out-of-sample final test set (never touched until final)

---

## LIBRARIES AVAILABLE

**Currently Installed:**
- ✅ PyTorch 2.8.0 (Deep learning)
- ✅ Pandas 2.1.4 (Data manipulation)
- ✅ NumPy 1.26.4 (Numerical computing)

**Not Installed (Would Need to Install):**
- ❌ scikit-learn (for classical ML)
- ❌ LightGBM (gradient boosting)
- ❌ XGBoost (gradient boosting)
- ❌ statsmodels (ARIMA, statistical models)

**Decision:** 
- Start with PyTorch (already works)
- Can install others if needed, but PyTorch is sufficient

---

## RECOMMENDED APPROACH

### IMMEDIATE: Start with PyTorch
1. **Feed-Forward NN** - Proven to work, fast to train
2. **LSTM** - Better for sequences, capture temporal patterns
3. **Ensemble** - Combine both for robustness

### LATER: Expand if needed
4. Install scikit-learn for feature selection tools
5. Install LightGBM if we need interpretable tree models
6. Add statistical baselines (ARIMA) for comparison

---

## DELIVERABLES

### Training Outputs:
1. ✅ Trained model (.pth file)
2. ✅ Predictions CSV (actual vs predicted)
3. ✅ Feature importance ranking
4. ✅ Performance metrics report
5. ✅ Validation charts (predictions, errors, feature importance)

### Production Assets:
6. ✅ Model inference script
7. ✅ Feature preprocessing pipeline
8. ✅ Performance monitoring dashboard
9. ✅ Backtesting results

---

## NEXT COMMAND

Ready to start training. Should I:

**Option A:** Train baseline Feed-Forward Neural Network (15-30 min)
**Option B:** Do final feature selection first, then train (20-40 min)
**Option C:** Build LSTM model for time series (30-60 min)
**Option D:** All of the above in sequence (2-3 hours)

**Recommendation:** Option D - Complete baseline suite

---

## FILE MANIFEST

**Data Files:**
- `REAL_TRAINING_DATA_WITH_CURRENCIES.csv` - Main dataset (1,263 rows × 149 features)
- `REAL_TRAINING_DATA_BACKUP.csv` - Backup without currencies
- `DATA_MANIFEST.csv` - Dataset metadata
- `VERIFIED_FEATURES.csv` - Feature quality report

**Documentation:**
- `EMERGENCY_DATA_AUDIT.md` - What happened with fake data
- `MODELING_PLAN.md` - This document

**BigQuery Backups:**
- `cbi-v14.models.training_data_with_currencies_verified`
- `cbi-v14.models.training_complete_enhanced`
- Plus 7 other training dataset versions

---

**READY TO TRAIN - ALL DATA VERIFIED AND BACKED UP**

