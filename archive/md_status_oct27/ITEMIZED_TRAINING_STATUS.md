# ITEMIZED TRAINING STATUS - COMPLETE BREAKDOWN
**Date:** October 22, 2025  
**Time:** 17:29 UTC

## 🎯 MODELS CURRENTLY TRAINING (2 ACTIVE)

### 1. ⏳ `zl_boosted_tree_signals_v5` 
- **Status:** RUNNING (Job: 5d7cc20e-0137-48ec-845c-0408af548b1b)
- **Type:** BOOSTED_TREE_REGRESSOR
- **Started:** 3 minutes ago
- **Purpose:** Main signal-enhanced model
- **Training on:** ALL features including news

### 2. ⏳ `zl_boosted_tree_high_volatility_v5`
- **Status:** RUNNING (Job: ab6ab93a-ebc3-48e1-a528-ee24d534295f)
- **Type:** BOOSTED_TREE_REGRESSOR
- **Started:** 3 minutes ago
- **Purpose:** High volatility specialist
- **Training on:** Periods where VIX > 25

### 3. ❓ `zl_boosted_tree_crisis_v5`
- **Status:** Unknown (may have failed or completed)
- **Type:** BOOSTED_TREE_REGRESSOR
- **Purpose:** Crisis regime specialist
- **Training on:** CRISIS market regime periods

## 📊 COMPLETE FEATURE LIST (39 FEATURES)

### 1️⃣ PRICE FEATURES (9):
- `zl_price_current` - Current soybean oil price
- `zl_price_lag1` - Price 1 day ago
- `zl_price_lag7` - Price 7 days ago
- `zl_price_lag30` - Price 30 days ago
- `return_1d` - 1-day return
- `return_7d` - 7-day return
- `ma_7d` - 7-day moving average
- `ma_30d` - 30-day moving average
- `volatility_30d` - 30-day volatility

### 2️⃣ VIX FEATURES (7):
- `vix_value` - Current VIX level
- `vix_lag1` - VIX 1 day ago
- `vix_lag7` - VIX 7 days ago
- `vix_change_1d` - VIX 1-day change
- `vix_ma7` - VIX 7-day MA
- `vix_regime` - CRISIS/HIGH_STRESS/ELEVATED/NORMAL
- `vix_crisis_score` - Exponential crisis indicator
- `vix_crisis_flag` - Binary crisis flag (VIX > 25)

### 3️⃣ SENTIMENT FEATURES (5):
- `sentiment_score` - Average sentiment
- `sentiment_volatility` - Sentiment standard deviation
- `sentiment_volume` - Number of posts
- `extreme_negative_count` - Posts with sentiment < -0.5
- `extreme_positive_count` - Posts with sentiment > 0.5

### 4️⃣ TARIFF/POLICY FEATURES (4):
- `tariff_mentions` - Count of tariff mentions
- `china_mentions` - Count of China mentions
- `ag_impact_score` - Agricultural impact score
- `policy_event_count` - Total policy events

### 5️⃣ NEWS FEATURES (3) ⚠️:
- `news_volume` - Number of news articles
- `news_intelligence` - Average intelligence score
- `soybean_news_count` - Soybean-specific news

**⚠️ NEWS DATA ISSUE:**
- News data only covers Oct 4-22, 2025 (13 days)
- Training data spans 2020-2025 (1,263 days)
- Result: 99% of rows have news_volume = 0

### 6️⃣ INTERACTION FEATURES (4):
- `vix_sentiment_interaction` - VIX × (2 - sentiment)
- `tariff_vix_impact` - Tariff mentions × VIX change
- `crisis_panic_score` - Extreme negative × VIX crisis score
- `composite_risk_score` - Weighted combination of all risks

### 7️⃣ OTHER FEATURES (3):
- `market_regime` - CRISIS/TRADE_TENSION/BULLISH/NEUTRAL
- `target_1w` - 1-week ahead target
- `target_1m` - 1-month ahead target
- `target_3m` - 3-month ahead target
- `target_6m` - 6-month ahead target

## 📈 DATA COVERAGE ANALYSIS

| Data Source | Total Records | Date Range | Coverage in Training |
|-------------|--------------|------------|---------------------|
| Price Data | 1,263 | 2020-2025 | 100% |
| VIX | 2,717 | 2014-2025 | 100% (via defaults) |
| Sentiment | 661 | Various | 100% (via defaults) |
| Tariff/Policy | 215 | Various | 100% (via defaults) |
| **News** | 1,905 | Oct 4-22, 2025 | **1% (ISSUE!)** |

## ⚠️ KEY ISSUES IDENTIFIED

### News Data Problem:
- **Only 13 days of news data** (Oct 4-22, 2025)
- **99% of training rows have news = 0**
- This limits the model's ability to learn from news signals
- Solution: Either get historical news data or remove news features

### Market Regime Imbalance:
- 99% NEUTRAL regime
- 1% BULLISH regime
- 0% CRISIS regime
- Crisis model may fail due to no crisis data

## ✅ WHAT'S WORKING

1. **Price features** - Full coverage
2. **VIX features** - Excellent coverage and crisis detection
3. **Sentiment features** - Good coverage with smart defaults
4. **Tariff features** - Sparse but impactful when present
5. **Signal interactions** - Capturing complex relationships

## 🎯 RECOMMENDATIONS

1. **News Data:** Either acquire historical news or remove news features
2. **Crisis Model:** May need synthetic crisis scenarios or historical crisis data
3. **Focus on:** VIX-sentiment interactions which have good coverage

---

**BOTTOM LINE:** 2 models actively training with 39 features. News features included but mostly zeros due to limited historical data.
