# 📋 PAGE BUILDOUT ROADMAP

**Date**: November 16, 2025  
**Status**: Active Planning

**Related Plan**: This roadmap is linked to the main execution plan at `docs/execution/25year-data-enrichment/architecture-lock.plan.md`

---

## ✅ COMPLETED PAGES

### 1. Dashboard (Home)
- ✅ Main ZL prediction center
- ✅ All time horizons (1w, 1m, 3m, 6m, 12m)
- ✅ VIX overlay for risk assessment
- ✅ SHAP values explaining predictions
- ✅ Current price and targets
- ✅ Confidence levels

### 2. Legislative
- ✅ Policy/Trump impact microscope on ZL
- ✅ Trump action predictions
- ✅ ZL-specific impact section
- ✅ Historical correlations
- ✅ Procurement alerts for Chris

### 3. Strategy
- ✅ Scenario planning for procurement
- ✅ What-if scenarios
- ✅ If/then decision trees
- ✅ Timing optimization

### 4. Vegas Intel (Kevin Only)
- ✅ Sales intelligence for restaurant upsells
- ✅ Glide app integration
- ✅ Casino event calendar
- ✅ Volume multipliers
- ✅ Upsell opportunities

---

## 🚧 PLANNED PAGES

### 5. Sentiment Page
**Status**: Planned for future buildout  
**Priority**: Medium  
**Target User**: Chris (Procurement Manager)  
**Note**: Basic page structure exists at `dashboard-nextjs/src/app/sentiment/page.tsx` - it currently renders the header (“Quantitative Sentiment Analysis”) and a “Coming Soon” card with no data bindings. All functional requirements below remain outstanding.

**Purpose**: Comprehensive sentiment analysis and breaking news dashboard

**Current implementation snapshot (Nov 2025)**:
- `dashboard-nextjs/src/app/sentiment/page.tsx` only wires in the global `Sidebar`/`Header` components and a placeholder hero section. No hooks or API calls exist yet, so this route is effectively a stub.
- Upstream sentiment processing already runs through `scripts/sentiment/unified_sentiment_neural.py` (aka the UnifiedSentimentNeuralSystem). It ingests policy/news/social/weather/microstructure/technical inputs, produces ensemble scores, regimes, component confidence, and writes `sentiment_dashboard.json` plus `staging/unified_sentiment_neural.parquet`.
- PAGE_BUILDOUT_ROADMAP items below should be implemented by reading those JSON/Parquet outputs (initially from the local drive) and exposing them through a Next.js API layer for the React UI. Keep the architecture aligned with Ultimate Single Signal: price forecasts (ZL cost) flow into the sentiment ROI widgets, and sentiment insights feed back into procurement/strategy pages.

**Features to Include**:
- **Unified Sentiment Scoring**
  - Overall sentiment score (all sources combined)
  - Component breakdown (social, news, analyst, policy, weather, technical)
  - Neural network sentiment analysis
  - Historical sentiment trends

- **Breaking News Feed**
  - Real-time news updates
  - Filtered by relevance to ZL/commodities
  - Sentiment tagging per article
  - Impact assessment

- **Sentiment Sources**
  - Social media sentiment (Truth Social, Facebook, Reddit)
  - Market analyst sentiment
  - News sentiment (financial news APIs)
  - Policy document sentiment
  - Weather/supply sentiment indicators
  - Market microstructure sentiment
  - Technical indicator sentiment

- **Visualizations**
  - Sentiment time series charts
  - Component contribution charts
  - Sentiment regime indicators (very bearish → very bullish)
  - Confidence metrics
  - Correlation with ZL price movements

- **Integration Points**
  - Links to Legislative page (Trump sentiment)
  - Links to Dashboard (sentiment impact on predictions)
  - Links to Strategy page (sentiment-based scenarios)

**Data Sources**:
- `scripts/sentiment/unified_sentiment_neural.py` (already implemented)
- Local drive: `TrainingData/staging/sentiment_*.parquet`
- Real-time APIs: ScrapeCreators, news feeds, social media

**Technical Notes**:
- Will use existing `unified_sentiment_neural.py` system
- Data from local external drive (not BigQuery)
- Real-time updates every 5-15 minutes
- Historical data from backfilled sentiment analysis

**Buildout Timeline**: To be scheduled after core ZL prediction system is stable

---

## 📊 PAGE PRIORITY MATRIX

| Page | Status | Priority | User | Purpose |
|------|--------|----------|------|---------|
| Dashboard | ✅ Complete | P0 | Chris | Main ZL predictions |
| Legislative | ✅ Complete | P0 | Chris | Trump/policy → ZL impact |
| Strategy | ✅ Complete | P1 | Chris | Scenario planning |
| Vegas Intel | ✅ Complete | P1 | Kevin | Sales intelligence |
| Sentiment | 🚧 Planned | P2 | Chris | Sentiment analysis & news |

---

## 🔄 DATA FLOW FOR SENTIMENT PAGE

```
Data Sources → Local Drive → Sentiment Analysis → Dashboard
     ↓              ↓              ↓                  ↓
  APIs/Feeds   TrainingData/   unified_sentiment   Sentiment Page
              staging/         _neural.py
```

---

## 📝 NOTES

- Sentiment page will leverage existing `unified_sentiment_neural.py` infrastructure
- Until the dedicated APIs are in place, keep `/sentiment` hidden from navigation or clearly labeled “Coming Soon” so users know it is non-functional.
- All sentiment data stored on local external drive
- Breaking news will require real-time API integration
- Component breakdown will show contribution of each sentiment source
- Historical patterns will help Chris understand sentiment → ZL correlations

---

**Last Updated**: November 16, 2025  
**Next Review**: After core system stabilization
