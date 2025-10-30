# CBI-V14 COMPLETE IMPLEMENTATION SCAFFOLD
**Date:** October 30, 2025  
**Status:** EXECUTION IN PROGRESS  
**Goal:** Deliver fully functional dashboard with all promised features

---

## 🎯 **EXECUTIVE SUMMARY**
Current dashboard shows stale/empty data despite claims of completion. This scaffold implements:
- All advanced visualizations promised in conversations
- Complete data pipeline with fresh feeds
- AI-driven intelligence layer with SHAP explanations
- Chris-focused business intelligence in plain English

---

## 📋 **CURRENT STATE AUDIT**
### ❌ **BROKEN/MISSING (Must Fix First)**
- Big-8 feature table: 17 days stale (Oct 13 vs Oct 30)
- Predictions table: 0 rows (completely empty)
- Breaking news table: doesn't exist
- Feature refresh pipeline: never successfully executed
- Forward curve: shows "temporarily unavailable"

### ✅ **WORKING (Preserve)**
- Hourly price feeds: live (latest: 2025-10-30T14:05)
- Dashboard layout: sidebar, headers, basic structure
- API routes: fixed to point at correct tables (but tables empty)
- Cron configuration: scheduled but not tested

---

## 🚀 **PHASE 1: CORE DATA PIPELINE (ETA: 45 min)**

### 1.1 Fix Feature Refresh Pipeline
- [ ] Fix import path in `refresh_features_pipeline.py`
- [ ] Execute pipeline to update Big-8 table to today
- [ ] Verify 209+ features with latest date = 2025-10-30
- [ ] Write success manifest to `logs/feature_refresh_manifest.json`

### 1.2 Populate Predictions Table
- [ ] Run `automl/quick_endpoint_predictions.py` for all 4 horizons
- [ ] Verify `predictions.daily_forecasts` has 4 rows dated today
- [ ] Test forecast API routes return live JSON with prediction_date = 2025-10-30

### 1.3 Create Breaking News Pipeline
- [ ] Create `forecasting_data_warehouse.breaking_news_hourly` table
- [ ] Build `scripts/hourly_news.py` with GDELT + Gemini AI summarizer
- [ ] Backfill last 24h of headlines
- [ ] Test `/api/v4/breaking-news` returns live summaries

### 1.4 Verify Core Dashboard
- [ ] All forecast cards show today's predictions
- [ ] Big-8 bars reflect today's features
- [ ] Breaking news shows live headlines
- [ ] No "temporarily unavailable" messages

---

## 🎨 **PHASE 2: ADVANCED VISUALIZATIONS (ETA: 2 hours)**

### 2.1 "Why Prices Are Moving" - SHAP Driver Analysis
- [ ] Create `scripts/calculate_shap_drivers.py`
- [ ] Build API route `/api/v4/price-drivers`
- [ ] Create React component `PriceDrivers.tsx`
- [ ] Display top 10 drivers with dollar impacts in plain English
- [ ] Example: "China demand up 12% → +$2.34/bu impact"

### 2.2 Substitution Economics Calculator
- [ ] Create API route `/api/v4/substitution-economics`
- [ ] Build React component `SubstitutionEconomics.tsx`
- [ ] Chart: Soy oil vs Palm oil vs Canola cost curves
- [ ] Show switching points with transport costs
- [ ] Diamond markers at optimal substitution prices

### 2.3 Risk Radar Visualization
- [ ] Create API route `/api/v4/risk-radar`
- [ ] Build React component `RiskRadar.tsx`
- [ ] 6-axis radar: Price volatility, FX risk, Weather risk, Supply tightness, Demand shock, Policy risk
- [ ] Real-time data from existing features
- [ ] Color-coded risk levels (green/yellow/red)

### 2.4 Currency Impact Waterfall
- [ ] Create API route `/api/v4/currency-waterfall`
- [ ] Build React component `CurrencyWaterfall.tsx`
- [ ] Waterfall chart: Base price → USD/BRL → USD/CNY → USD/ARS → Final price
- [ ] Show positive/negative FX impacts with colors

### 2.5 Procurement Timing Optimizer
- [ ] Create API route `/api/v4/procurement-timing`
- [ ] Build React component `ProcurementOptimizer.tsx`
- [ ] Chart: Price forecast + VIX overlay + optimal buy windows
- [ ] Green zones = buy opportunities, Red zones = wait periods
- [ ] Confidence intervals and expected savings

### 2.6 Biofuel Mandate Analyzer
- [ ] Create API route `/api/v4/biofuel-mandates`
- [ ] Build React component `BiofuelMandates.tsx`
- [ ] Chart: Mandate percentage vs soybean oil price correlation
- [ ] Policy event markers with price impact annotations
- [ ] EPA RFS timeline integration

---

## 🧠 **PHASE 3: AI INTELLIGENCE LAYER (ETA: 1 hour)**

### 3.1 Ensemble Meta-Learner
- [ ] Create `scripts/train_ensemble_meta_learner.py`
- [ ] LightGBM stacker combining 1W/1M/3M/6M predictions
- [ ] Target: <1.8% MAPE (better than individual models)
- [ ] Performance-based weighting with regime detection

### 3.2 SHAP Feature Importance Engine
- [ ] Build `scripts/calculate_shap_contributions.py`
- [ ] Real-time SHAP values for latest prediction
- [ ] Convert technical features to business language
- [ ] Example: "feature_china_imports_3m" → "China buying surge"

### 3.3 Breaking News AI Summarizer
- [ ] Integrate Gemini Pro API in `hourly_news.py`
- [ ] Fetch GDELT headlines → AI summary → sentiment score
- [ ] Focus on soybean oil price relevance
- [ ] Store: headline, summary, sentiment, relevance_score

### 3.4 Regime-Aware Model Selection
- [ ] Detect volatility regimes (VIX > 25 = high vol)
- [ ] Switch between models based on market conditions
- [ ] Calm markets: use 6M model, Volatile: use 1W model
- [ ] Display active regime on dashboard

---

## 🎪 **PHASE 4: DASHBOARD INTEGRATION (ETA: 30 min)**

### 4.1 Layout Enhancement (Preserve Existing)
```
[HEADER - Keep unchanged]
[SIDEBAR - Keep unchanged]

[ROW 1] Forward Curve (full width) - FIX "temporarily unavailable"
[ROW 2] Forecast Cards 1W/1M/3M/6M (equal width) - WORKING
[ROW 3] Breaking News + AI Analysis (full width) - ENHANCE
[ROW 4] VIX Gauge + Market Drivers (40%/60%) - WORKING
[ROW 5] "Why Prices Are Moving" Cards (full width) - ADD NEW
[ROW 6] Advanced Analytics Carousel (full width) - ADD NEW
  └── Panel 1: Substitution Economics
  └── Panel 2: Risk Radar  
  └── Panel 3: Currency Waterfall
  └── Panel 4: Biofuel Mandates
[ROW 7] Big-8 Signals (full width) - WORKING
[ROW 8] Procurement Timing Optimizer (full width) - ADD NEW
```

### 4.2 Component Integration
- [ ] Mount `PriceDrivers.tsx` in ROW 5
- [ ] Create `AdvancedAnalyticsCarousel.tsx` for ROW 6
- [ ] Mount `ProcurementOptimizer.tsx` in ROW 8
- [ ] Fix Forward Curve data connection
- [ ] Enhance Breaking News with AI summaries

### 4.3 API Integration
- [ ] All new components use SWR for data fetching
- [ ] Consistent error handling (503 = red banner)
- [ ] Loading states for all components
- [ ] Refresh intervals: 15min for analytics, 1hr for news

### 4.4 Styling & UX
- [ ] Consistent color scheme (blue = bullish, red = bearish)
- [ ] Professional chart styling with Recharts
- [ ] Responsive design for all new components
- [ ] Smooth transitions and loading animations

---

## 🛡️ **PHASE 5: SAFEGUARDS & MONITORING (ETA: 15 min)**

### 5.1 Data Freshness Monitoring
- [ ] Extend smoke test to cover all new APIs
- [ ] Red banner if any feed > 3 days stale
- [ ] Automated alerts for pipeline failures
- [ ] Daily health check reports

### 5.2 Performance Monitoring
- [ ] API response time monitoring
- [ ] BigQuery query cost tracking
- [ ] Vertex AI usage alerts
- [ ] Dashboard load time optimization

### 5.3 Error Handling
- [ ] Graceful degradation for failed components
- [ ] Fallback data sources where possible
- [ ] User-friendly error messages
- [ ] Automatic retry logic for transient failures

---

## 📊 **SUCCESS METRICS**

### Data Pipeline Health
- [ ] Big-8 features updated twice daily (latest date = today)
- [ ] All 4 forecast horizons refreshed monthly
- [ ] Breaking news updated hourly
- [ ] Zero "temporarily unavailable" messages

### Dashboard Functionality  
- [ ] All 8+ visualization components working
- [ ] Sub-3-second load times for all APIs
- [ ] Mobile responsive design
- [ ] Zero JavaScript errors in console

### Business Intelligence Quality
- [ ] SHAP drivers in plain English (not technical features)
- [ ] Dollar impact calculations accurate
- [ ] Regime detection working (VIX-based switching)
- [ ] Ensemble MAPE < 1.8% (better than individual models)

---

## ⚡ **EXECUTION PRIORITY**

**IMMEDIATE (Next 1 hour):**
1. Fix feature refresh pipeline
2. Populate predictions table
3. Create breaking news table
4. Verify dashboard shows live data

**TODAY (Next 4 hours):**
1. Build all advanced visualization APIs
2. Create React components
3. Integrate into dashboard layout
4. Deploy and test end-to-end

**THIS WEEK:**
1. Monitor data pipeline stability
2. Optimize query performance
3. Add advanced AI features
4. Polish UX and styling

---

## 🚨 **CRITICAL SUCCESS FACTORS**

1. **No Layout Disruption**: All new features added below existing components
2. **Real Data Only**: Zero fake/placeholder values, 503 errors instead
3. **Plain English**: Convert all technical features to business language
4. **Performance**: Sub-3-second API responses, efficient BigQuery queries
5. **Reliability**: Automated monitoring, graceful error handling
6. **Cost Control**: Monitor Vertex AI usage, optimize BigQuery queries

---

*This scaffold serves as the single source of truth for implementation. Each checkbox will be marked as completed with timestamps and verification notes.*
