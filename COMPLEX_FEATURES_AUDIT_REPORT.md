# Complex Features Audit & Population Report

**Date**: November 6, 2025  
**Task**: Populate complex calculation features for new dates (Sep 11 - Nov 6, 2025)  
**Result**: ✅ **PHASE 1 COMPLETE - Basic Population Successful**

---

## Executive Summary

Successfully populated complex features for 57 new dates using simple, production-ready methods:
- ✅ Moving averages: 100% (57/57 rows)
- ✅ Technical indicators (RSI, MACD): 100% (57/57 rows)
- ⚠️ Sentiment features: 39% social, 33% news, 18% Trump policy (expected - sparse data)
- ❌ Crush margin: 0% (source components NULL for new dates - requires separate fix)

---

## Detailed Results

### Features Successfully Populated

#### 1. Moving Averages (100% Complete)
- **ma_7d**: 57/57 rows ✅
- **ma_30d**: 57/57 rows ✅
- **ma_90d**: 57/57 rows ✅
- **Method**: `AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN N PRECEDING AND CURRENT ROW)`
- **Script**: `POPULATE_MOVING_AVERAGES.sql`

#### 2. Technical Indicators (100% Complete)
- **rsi_14**: 57/57 rows ✅ (avg: 47.09 - realistic value)
- **macd_line**: 57/57 rows ✅ (avg: -0.87)
- **macd_signal**: 57/57 rows ✅
- **macd_histogram**: 57/57 rows ✅
- **Method**: Window functions with 13-period RSI, 12/26/9 MACD
- **Script**: `RECALCULATE_TECHNICAL_INDICATORS.sql`
- **Note**: Replaced template values (50.0 for RSI, 0.0 for MACD) with actual calculations

#### 3. Sentiment Features (Sparse - As Expected)
- **social_sentiment_avg**: 22/57 rows (39%) ✅
- **social_sentiment_volatility**: 22/57 rows ✅
- **bullish_ratio / bearish_ratio**: 22/57 rows ✅
- **social_sentiment_7d**: 22/57 rows ✅
- **news_sentiment_avg**: 19/57 rows (33%) ✅
- **news_article_count**: 19/57 rows ✅
- **trump_policy_impact_max**: 10/57 rows (18%) ✅
- **Method**: JOIN with daily aggregation tables
- **Script**: `POPULATE_SENTIMENT_FEATURES.sql`
- **Note**: Sparse coverage is expected - not every trading day has news/social posts

### Features NOT Populated

#### Crush Margin (0% - Needs Separate Fix)
- **crush_margin**: 0/57 rows ❌
- **crush_margin_7d_ma**: 0/57 rows ❌
- **crush_margin_30d_ma**: 0/57 rows ❌
- **Root Cause**: Source components (bean_price_per_bushel, oil_price_per_cwt, meal_price_per_ton) are NULL for new dates
- **Action Required**: Investigate source tables for these components and populate them first
- **Script Ready**: `POPULATE_CRUSH_MARGIN.sql` (formula verified)

---

## Methodology

### Approach: Simple & Production-Ready
Following the decision to use basic methods for Phase 1, all features were populated using:
1. **Window Functions**: AVG(), LAG() for moving averages and technical indicators
2. **Simple JOINs**: Direct joins with daily aggregation tables for sentiment
3. **Standard Formulas**: RSI (14-period), MACD (12/26/9), MA (7/30/90 day)

### What Was NOT Done (Phase 2 - Future)
- ❌ Exponential decay functions for events
- ❌ Source reliability weighting (0.65-0.98)
- ❌ Conviction scoring for sentiment
- ❌ Dynamic regime-based weights
- ❌ Granger causality verification
- ❌ Cross-asset signal boosts

**Rationale**: Phase 1 focuses on getting data current with low-risk, fast methods. Phase 2 will add sophistication after validation.

---

## Scripts Created

| Script | Purpose | Status |
|--------|---------|--------|
| `POPULATE_MOVING_AVERAGES.sql` | Calculate ma_7d, ma_30d, ma_90d | ✅ Executed |
| `POPULATE_CRUSH_MARGIN.sql` | Calculate crush margin (formula verified) | ⚠️ Ready (needs source data) |
| `POPULATE_SENTIMENT_FEATURES.sql` | JOIN sentiment tables | ✅ Executed |
| `RECALCULATE_TECHNICAL_INDICATORS.sql` | RSI/MACD from prices | ✅ Executed |
| `COMPREHENSIVE_FEATURE_POPULATION.sql` | Master script (all steps) | ⚠️ Multi-statement (can't run via CLI) |

---

## Data Sources Audit

### Available & Current
- ✅ `vw_big_eight_signals`: Through Nov 6 (2,137 rows)
- ✅ `soybean_oil_prices`: Through Nov 5 (zl_price_current populated)
- ✅ `social_sentiment_daily`: Through Nov 4 (208 rows)
- ✅ `news_intelligence_daily`: Through Nov 5 (19 rows)
- ✅ `trump_policy_daily`: Through Nov 5 (49 rows)

### Available But Stale
- ⚠️ `rin_prices_daily`: Through Sep 10 only (stale)
- ⚠️ `rfs_mandates_daily`: Through Sep 10 only (stale)

### Missing Data
- ❌ `bean_price_per_bushel`: NULL for new dates (source unknown)
- ❌ `oil_price_per_cwt`: NULL for new dates (source unknown)
- ❌ `meal_price_per_ton`: NULL for new dates (source unknown)

**Recommendation**: Investigate where bean/oil/meal prices come from. May need separate ingestion script or data source.

---

## Execution Log

```
Step 1/4: Moving Averages
  - Script: POPULATE_MOVING_AVERAGES.sql
  - Result: 57 rows updated ✅
  - Duration: ~4 seconds

Step 2/4: Crush Margin
  - Script: POPULATE_CRUSH_MARGIN.sql
  - Result: 0 rows updated ⚠️ (source data NULL)
  - Duration: ~4 seconds

Step 3/4: Sentiment Features
  - Script: POPULATE_SENTIMENT_FEATURES.sql
  - Social: 22 rows updated
  - News: 19 rows updated
  - Trump: 10 rows updated
  - Duration: ~11 seconds

Step 4/4: Technical Indicators
  - Script: RECALCULATE_TECHNICAL_INDICATORS.sql
  - RSI: 57 rows updated ✅
  - MACD: 57 rows updated ✅
  - Duration: ~7 seconds

Total Execution Time: ~26 seconds
```

---

## Validation

### Before Population
| Feature | NULL Count | Coverage |
|---------|-----------|----------|
| ma_7d | 57/57 | 0% |
| ma_30d | 57/57 | 0% |
| crush_margin | 57/57 | 0% |
| social_sentiment_avg | 57/57 | 0% |
| rsi_14 | 0/57 (template 50.0) | 100% |
| macd_line | 0/57 (template 0.0) | 100% |

### After Population
| Feature | NULL Count | Coverage | Notes |
|---------|-----------|----------|-------|
| ma_7d | 0/57 | 100% ✅ | Calculated |
| ma_30d | 0/57 | 100% ✅ | Calculated |
| crush_margin | 57/57 | 0% ❌ | Source data missing |
| social_sentiment_avg | 35/57 | 39% ✅ | Sparse (expected) |
| rsi_14 | 0/57 | 100% ✅ | Avg: 47.09 (realistic) |
| macd_line | 0/57 | 100% ✅ | Avg: -0.87 (realistic) |

---

## Next Steps

### Immediate (Required for Complete Population)
1. **Investigate Crush Margin Components**
   - Find source for bean_price_per_bushel, oil_price_per_cwt, meal_price_per_ton
   - Populate these for new dates
   - Re-run `POPULATE_CRUSH_MARGIN.sql`

2. **Update Other Horizons**
   - Run same scripts for production_training_data_1w
   - Run same scripts for production_training_data_3m
   - Run same scripts for production_training_data_6m

3. **Test Predictions**
   - Verify BQML models can train/predict with updated data
   - Check prediction accuracy with current data

### Phase 2 (Future Enhancement)
- Implement exponential decay functions for event-based features
- Add source reliability weighting and conviction scoring
- Build regime detection and dynamic weights
- Implement Granger causality tests
- Create automated ingestion calculation pipeline

**Reference**: See plan sections for detailed Phase 2 specifications

---

## Success Metrics

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Moving averages populated | 100% | 100% (57/57) | ✅ MET |
| Technical indicators calculated | 100% | 100% (57/57) | ✅ MET |
| Sentiment features joined | Best effort | 18-39% | ✅ MET (sparse expected) |
| Crush margin calculated | 100% | 0% | ❌ BLOCKED (source data) |
| Zero errors in calculations | Yes | Yes | ✅ MET |
| Realistic value ranges | Yes | Yes (RSI 47, MACD -0.87) | ✅ MET |

**Overall Phase 1 Status**: ✅ **SUCCESSFUL** (3/4 features, blocked issue identified)

---

**Created**: November 6, 2025  
**Status**: Phase 1 Complete, Crush Margin investigation required  
**Next**: Update 1w/3m/6m horizons, investigate crush margin sources







