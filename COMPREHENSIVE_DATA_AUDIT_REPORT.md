# 📋 COMPREHENSIVE DATA AUDIT REPORT
**Date**: November 6, 2025  
**Purpose**: Review ALL data before Yahoo integration  
**Status**: READ ONLY - NO CHANGES MADE

---

## 🎯 EXECUTIVE SUMMARY

### **Current State**:
- ✅ **Production Table**: 1,404 rows, 334 columns, 2020-2025 (5.8 years)
- ✅ **Yahoo Complete**: 314,381 rows, 51 columns, 55 symbols, 2000-2025 (25 years)
- ✅ **RIN Proxies**: 6,475 rows, 14 columns, 2000-2025 (98.8% filled in production)
- ✅ **Biofuel Components**: 6,475 rows, 19 columns, 2000-2025 (canonical source)
- ✅ **Model Performance**: 80.83% MAE improvement (baseline → v2)

### **Key Finding**:
**17 columns ALREADY EXIST** in both Yahoo and Production (technical indicators).  
**31 columns are NEW** from Yahoo (fundamentals, analyst data, news, OHLCV details).

---

## 📊 DATA INVENTORY

### **1. PRODUCTION TABLE** (`cbi-v14.models_v4.production_training_data_1m`)

**Size**:
- Rows: 1,404
- Columns: 334
- Date Range: 2020-01-06 to 2025-11-06 (2,131 days, ~5.8 years)

**Column Categories** (334 total):
1. **Targets** (4): target_1w, target_1m, target_3m, target_6m
2. **Current Price** (2): zl_price_current, zl_volume
3. **Big 8 Features** (8): feature_vix_stress, feature_harvest_pace, etc.
4. **Crush Margin** (6): crush_margin, crush_margin_7d_ma, crush_margin_30d_ma, etc.
5. **China Sentiment** (9): china_mentions, china_posts, china_sentiment, etc.
6. **Brazil Weather** (7): brazil_temperature_c, brazil_precipitation_mm, harvest_pressure, etc.
7. **Trump/Xi Policy** (14): trump_mentions, tariff_mentions, tension_index, etc.
8. **Trade War** (6): china_tariff_rate, trade_war_intensity, etc.
9. **Event Indicators** (14): is_wasde_day, is_fomc_day, event_impact_level, etc.
10. **Cross-Asset Lags** (23): palm_lag1, crude_lag1, vix_lag1, etc.
11. **Correlations** (30): corr_zl_palm_7d, corr_zl_crude_30d, etc.
12. **Technical Indicators** (17): ma_7d, ma_30d, ma_90d, rsi_14, macd_line, bb_upper, atr_14, etc.
13. **Weather (Global)** (21): brazil_temp_c, argentina_conditions_score, us_midwest_flood_days, etc.
14. **Economic Indicators** (9): treasury_10y_yield, gdp_growth, unemployment_rate, etc.
15. **FX Rates** (9): usd_cny_rate, usd_brl_rate, dollar_index, etc.
16. **Social Sentiment** (9): social_sentiment_avg, bullish_ratio, social_volume_7d, etc.
17. **Trump Policy** (9): trump_policy_events, trump_policy_7d, trump_agricultural_impact_30d, etc.
18. **USDA Export Sales** (5): soybean_weekly_sales, china_soybean_sales, etc.
19. **CFTC** (8): cftc_commercial_long, cftc_managed_net, cftc_open_interest, etc.
20. **RIN/RFS Proxies** (6): rin_d4_price, rin_d5_price, rin_d6_price, rfs_mandate_biodiesel, rfs_mandate_advanced, rfs_mandate_total
21. **Biofuel Economics** (10): biodiesel_spread, ethanol_spread, biofuel_crack, biodiesel_margin, ethanol_margin, nat_gas_impact, sugar_ethanol_spread, soy_to_corn_ratio, oil_to_gas_ratio
22. **NULL Logistics** (4): china_weekly_cancellations_mt, argentina_vessel_queue_count, argentina_port_throughput_teu, baltic_dry_index
23. **Misc** (remainder): seasonal factors, time weights, regime indicators, etc.

**RIN/BIOFUEL Coverage** (added Nov 6, 2025):
- rin_d4_price: 1,387/1,404 (98.8%)
- rin_d6_price: 1,387/1,404 (98.8%)
- rin_d5_price: 1,387/1,404 (98.8%)
- rfs_mandate_biodiesel: 1,388/1,404 (98.9%)
- rfs_mandate_advanced: 1,387/1,404 (98.8%)
- rfs_mandate_total: 1,387/1,404 (98.8%)
- biodiesel_spread: 1,387/1,404 (98.8%)
- ethanol_spread: 1,387/1,404 (98.8%)
- biofuel_crack: 1,388/1,404 (98.9%)
- soy_to_corn_ratio: 1,388/1,404 (98.9%)

**NULL Columns** (20 identified, excluded from training):
- social_sentiment_volatility
- news_article_count, news_avg_score, news_sentiment_avg
- china_news_count, biofuel_news_count, tariff_news_count, weather_news_count
- news_intelligence_7d, news_volume_7d
- china_weekly_cancellations_mt
- argentina_vessel_queue_count, argentina_port_throughput_teu
- baltic_dry_index
- heating_oil_price, natural_gas_price, gasoline_price, sugar_price
- icln_price, tan_price, dba_price, vegi_price
- biodiesel_spread_ma30, ethanol_spread_ma30, biodiesel_spread_vol, ethanol_spread_vol

---

### **2. YAHOO FINANCE COMPLETE** (`cbi-v14.yahoo_finance_comprehensive.yahoo_finance_complete_enterprise`)

**Size**:
- Rows: 314,381
- Columns: 51
- Symbols: 55
- Categories: 13
- Date Range: 2000 to 2025 (25+ years of data!)

**Symbols by Category**:
1. **ag_commodity** (5): ZL=F, ZS=F, ZM=F, ZC=F, ZW=F
2. **energy** (5): CL=F, HO=F, RB=F, NG=F, BZ=F
3. **soft_commodity** (4): SB=F, CT=F, KC=F, CC=F
4. **metals** (4): GC=F, SI=F, HG=F, PL=F
5. **fx** (9): DX-Y.NYB, EURUSD=X, JPYUSD=X, GBPUSD=X, AUDUSD=X, CADUSD=X, CNYUSD=X, BRLUSD=X, MXNUSD=X
6. **rates** (5): ^TNX (10Y), ^TYX (30Y), ^FVX (5Y), ^IRX (13W), TLT
7. **equity_index** (3): ^GSPC, ^DJI, ^IXIC
8. **volatility** (1): ^VIX
9. **credit** (2): HYG, LQD
10. **etf_ag** (4): DBA, CORN, SOYB, WEAT
11. **etf_energy** (2): ICLN, TAN
12. **ag_stock** (9): ADM, BG, DAR, TSN, DE, AGCO, CF, MOS, NTR
13. **biofuel_stock** (2): GPRE, REX

**Columns** (51 total):

**OHLCV Data** (8):
- date (INT64 - nanosecond timestamps)
- open, high, low, close, volume
- dividends, stock_splits
- Capital Gains

**Metadata** (4):
- symbol, symbol_name, category, unit

**Technical Indicators** (18):
- ma_7d, ma_30d, ma_50d, ma_90d, ma_100d, ma_200d
- rsi_14
- macd_line, macd_signal, macd_histogram
- bb_middle, bb_upper, bb_lower, bb_width
- atr_14
- volume_ma_20, volume_ratio
- momentum_10, rate_of_change_10

**Analyst Data** (8):
- analyst_target_price (INT64)
- analyst_target_high (INT64)
- analyst_target_low (INT64)
- analyst_recommendation (STRING)
- analyst_count (INT64)
- analyst_rating (INT64)
- analyst_firm (INT64)
- analyst_action (INT64)

**Fundamentals** (8):
- pe_ratio
- forward_pe
- price_to_book
- dividend_yield
- market_cap (INT64)
- beta
- 52week_high
- 52week_low

**News Sentiment** (3):
- news_count_7d
- news_sentiment_avg
- latest_news_date (INT64)

**Row Counts by Category**:
| Category | Symbols | Rows | Earliest | Latest |
|----------|---------|------|----------|--------|
| ag_commodity | 5 | 31,244 | 2000-11-02 | 2025-11-05 |
| energy | 5 | 29,642 | 2000-11-02 | 2025-11-05 |
| soft_commodity | 4 | 25,054 | 2000-11-02 | 2025-11-05 |
| metals | 4 | 24,398 | 2000-11-02 | 2025-11-05 |
| fx | 9 | 52,092 | 2000-11-02 | 2025-11-05 |
| rates | 5 | 30,965 | 2000-11-02 | 2025-11-06 |
| equity_index | 3 | 18,846 | 2000-11-02 | 2025-11-05 |
| volatility | 1 | 6,283 | 2000-11-02 | 2025-11-06 |
| credit | 2 | 10,532 | 2002-08-01 | 2025-11-05 |
| etf_ag | 4 | 14,450 | 2010-05-14 | 2025-11-06 |
| etf_energy | 2 | 8,790 | 2008-04-15 | 2025-11-05 |
| ag_stock | 9 | 50,859 | 2000-11-02 | 2025-11-05 |
| biofuel_stock | 2 | 11,226 | 2000-11-02 | 2025-11-05 |

---

### **3. RIN PROXY FEATURES** (`cbi-v14.yahoo_finance_comprehensive.rin_proxy_features_final`)

**Size**:
- Rows: 6,475
- Columns: 14
- Date Range: 2000-03-01 to 2025-11-06 (25.7 years)

**Columns** (14):
1. date
2. biodiesel_spread_cwt (D4 RIN proxy)
3. biodiesel_margin_pct
4. biodiesel_crack_spread_bu (crush margin for biodiesel)
5. ethanol_spread_bbl (D6 RIN proxy)
6. ethanol_margin_pct
7. ethanol_production_cost_proxy (natural gas price)
8. advanced_biofuel_spread (D5 RIN proxy)
9. soy_corn_ratio (feedstock substitution signal)
10. oil_gas_ratio (energy market dynamics)
11. sugar_ethanol_spread (Brazil flex-fuel arbitrage)
12. rfs_biodiesel_fill_proxy (mandate difficulty indicator)
13. rfs_advanced_fill_proxy (advanced biofuel mandate)
14. rfs_total_fill_proxy (total renewable fuel mandate)

**Data Quality**:
- biodiesel_spread: 6,235/6,475 filled (96.3%)
- ethanol_spread: 6,245/6,475 filled (96.5%)
- biofuel_crack: 6,199/6,475 filled (95.7%)
- All ratios: 100% filled

---

### **4. BIOFUEL COMPONENTS CANONICAL** (`cbi-v14.yahoo_finance_comprehensive.biofuel_components_canonical`)

**Size**:
- Rows: 6,475
- Columns: 19
- Date Range: 2000-03-01 to 2025-11-06

**Columns** (19):
**Raw Prices** (9):
1. soybean_oil_price_cwt
2. soybean_price_cents_bu
3. soybean_meal_price_ton
4. corn_price_cents_bu
5. heating_oil_price_gal
6. gasoline_price_gal
7. natural_gas_price_mmbtu
8. sugar_price_cents_lb
9. crude_oil_price_bbl

**Standardized ($/MT)** (9):
10. soybean_oil_usd_mt
11. soybean_usd_mt
12. soybean_meal_usd_mt
13. corn_usd_mt
14. heating_oil_usd_mt
15. gasoline_usd_mt
16. natural_gas_usd_mmbtu
17. sugar_usd_mt
18. crude_oil_usd_mt

---

## 🔍 COLUMN OVERLAP ANALYSIS

### **Columns ALREADY in Production** (17):
✅ Technical indicators that exist in both:
1. atr_14
2. bb_lower
3. bb_middle
4. bb_upper
5. bb_width
6. date
7. ma_7d
8. ma_30d
9. ma_50d
10. ma_90d
11. ma_100d
12. ma_200d
13. macd_histogram
14. macd_line
15. macd_signal
16. news_sentiment_avg
17. rsi_14

**DECISION**: These columns are **already calculated** in production from existing ZL=F data. Yahoo data provides these for **54 additional symbols** - this is NEW information!

### **NEW Columns from Yahoo** (31):
✅ Columns that DON'T exist in production:
1. 52week_high
2. 52week_low
3. Capital Gains
4. analyst_action
5. analyst_count
6. analyst_firm
7. analyst_rating
8. analyst_recommendation
9. analyst_target_high
10. analyst_target_low
11. analyst_target_price
12. beta
13. category
14. close
15. dividend_yield
16. dividends
17. forward_pe
18. high
19. latest_news_date
20. low
21. market_cap
22. momentum_10
23. news_count_7d
24. open
25. pe_ratio
26. price_to_book
27. rate_of_change_10
28. stock_splits
29. symbol
30. symbol_name
31. unit
32. volume
33. volume_ma_20
34. volume_ratio

---

## 💡 KEY INSIGHTS

### **1. NO DATA DUPLICATION**
- The 17 overlapping columns (technical indicators) are calculated for **ZL=F only** in production
- Yahoo provides these SAME indicators for **54 additional symbols** (ag stocks, ETFs, FX, rates, indices)
- **This is NEW cross-asset signal data**, not duplication!

### **2. MASSIVE NEW INFORMATION**
Yahoo provides:
- **314K rows** vs production's 1.4K rows = **224x more data**
- **25 years** of history vs production's 5.8 years = **4.3x longer**
- **55 symbols** with full technical indicators, fundamentals, analyst data
- **Cross-asset correlations** can be calculated from this rich dataset

### **3. RIN PROXIES WORKING**
- 98.8% coverage in production (1,387/1,404 rows)
- Model improvement: **80.83% MAE reduction**
- RIN proxy features are **CRITICAL** (not "nice to have")

### **4. NULL COLUMNS IDENTIFIED**
- 20 NULL columns detected and excluded from training
- Includes: news counts, logistics data, raw biofuel component prices
- These columns have **schema but no data**

---

## 📋 WHAT'S MISSING (NICE TO HAVE)

Based on the audit, here's what we DON'T have but COULD add:

### **1. Raw Biofuel Component Prices in Production**
**Status**: Schema exists (8 columns) but 100% NULL
**Columns**:
- heating_oil_price
- natural_gas_price
- gasoline_price
- sugar_price
- icln_price
- tan_price
- dba_price
- vegi_price

**Source**: Available in `biofuel_components_raw` table (42,367 rows)
**Decision**: Should we populate these? They're inputs to RIN proxies.

### **2. Advanced Biofuel Features**
**Status**: Schema exists (4 columns) but 100% NULL
**Columns**:
- biodiesel_spread_ma30
- ethanol_spread_ma30
- biodiesel_spread_vol
- ethanol_spread_vol

**Source**: Can be calculated from `rin_proxy_features`
**Decision**: These are moving averages/volatility of the spreads

### **3. Logistics Data**
**Status**: Schema exists but 100% NULL
**Columns**:
- china_weekly_cancellations_mt
- argentina_vessel_queue_count
- argentina_port_throughput_teu
- baltic_dry_index

**Source**: Not available (requires specialized data providers)
**Decision**: Nice to have but not critical (model works without them)

### **4. News Intelligence Counts**
**Status**: Schema exists but 100% NULL
**Columns**:
- china_news_count
- biofuel_news_count
- tariff_news_count
- weather_news_count
- news_intelligence_7d
- news_volume_7d

**Source**: Could be populated from Yahoo `news_count_7d` for relevant symbols
**Decision**: Marginal value (we have news_sentiment_avg)

---

## 🎯 RECOMMENDATIONS

### **MUST HAVE** (Critical for full model):
1. ✅ **Keep current RIN proxies** (98.8% filled, 80% improvement)
2. ✅ **Integrate Yahoo 314K rows** for cross-asset signals
3. ✅ **Add Yahoo fundamentals** (PE, beta, analyst targets) for stocks
4. ✅ **Add Yahoo OHLCV** for all 55 symbols (cross-asset features)

### **SHOULD HAVE** (High value, low effort):
1. ⏳ **Populate raw biofuel prices** (heating oil, gas, sugar) from `biofuel_components_raw`
2. ⏳ **Calculate advanced biofuel features** (spread MA/volatility) from existing proxies
3. ⏳ **Add cross-symbol correlations** from Yahoo data (VIX-ZL, DX-ZL, etc.)

### **NICE TO HAVE** (Optional, lower priority):
1. ⏸️ **Logistics data** (requires paid data sources)
2. ⏸️ **News intelligence counts** (marginal value over sentiment)
3. ⏸️ **Palm oil (FCPO)** (failed to pull, exchange issue)

---

## 📊 FINAL DATA INVENTORY

| Dataset | Rows | Columns | Date Range | Status |
|---------|------|---------|------------|--------|
| **Production** | 1,404 | 334 | 2020-2025 (5.8yr) | ✅ CURRENT |
| **Yahoo Complete** | 314,381 | 51 | 2000-2025 (25yr) | ✅ READY |
| **RIN Proxies** | 6,475 | 14 | 2000-2025 (25.7yr) | ✅ INTEGRATED |
| **Biofuel Canonical** | 6,475 | 19 | 2000-2025 (25.7yr) | ✅ CANONICAL |
| **Total Unique Data** | ~322K | ~400+ | 25+ years | ✅ MASSIVE |

---

## ✅ AUDIT COMPLETE

**Status**: READ ONLY - NO CHANGES MADE  
**Findings**: ALL data sources reviewed and documented  
**Recommendation**: Proceed with Yahoo integration plan  
**Next Step**: Design integration strategy (with user approval)


