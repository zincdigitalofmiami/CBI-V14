# Project Focus Clarification

**Date**: November 18, 2025  
**Status**: Critical Understanding Document

---

## PRIMARY MISSION

**ZL (Soybean Oil Futures) Prediction** is the **ONLY primary target** of this project.

Everything in the system serves one purpose: **Help Chris make better soybean oil procurement decisions**.

---

## SECONDARY / SUPPORTING ELEMENTS

### MES (Micro E-mini S&P 500)
- **Symbol**: MES (NOT ES - ES is only used for correlations)
- **Purpose**: Cross-asset correlations to support ZL models
- **Status**: "Silent hidden" page - NOT to be confused with the main project
- **Usage**: Only for correlation features (VIX, market stress, regime detection)

### ES Data Collection
- **Purpose**: Used ONLY for correlations (e.g., ZL vs VIX, ZL vs market stress)
- **NOT a primary prediction target**
- **Collection**: Minimal - only what's needed for correlation features

---

## DATA COLLECTION PRIORITIES

### HIGH PRIORITY (ZL-Focused)
1. **Commodities**: Soybean, palm oil, corn, wheat, crude oil
2. **Weather**: Brazil, Argentina, US Midwest (crop production)
3. **Trade/Policy**: Tariffs, USDA, CFTC, biofuel mandates
4. **Supply/Demand**: China imports, export taxes, inventories
5. **Economic Indicators**: Fed rates, inflation (affect commodity prices)

### LOW PRIORITY (Correlation Support Only)
1. **ES/MES Data**: Only for correlation features
2. **VIX**: For regime detection
3. **General Financial Markets**: Only if related to commodity correlations

### EXCLUDED
1. **General Tech News**: Not relevant to ZL
2. **Entertainment/Sports**: Not relevant
3. **ES/MES-Specific News**: Unless it helps correlations for ZL
4. **Unrelated Financial News**: IPOs, mergers, corporate earnings (unless commodity-related)

---

## NEWS SENTIMENT FILTERING

The `collect_alpha_vantage_comprehensive.py` script now includes:

### `filter_zl_relevant_articles()` Function
- **Filters articles** to only ZL-relevant content
- **Keeps**: Commodities, weather, trade policy, biofuel, supply/demand, economic indicators
- **Removes**: Tech, entertainment, sports, ES/MES-specific news

### Topics Collected
- `economy_macro`: Macro indicators affecting commodity demand
- `economy_monetary`: Fed rates, monetary policy affecting commodity prices
- **Excluded**: `financial_markets` (too broad, includes ES/MES)
- **Excluded**: `economy_fiscal` (less directly relevant)
- **Excluded**: `energy_transportation` (unless mentions biofuels/commodities)

---

## DOCUMENTATION UPDATES

Any documents that incorrectly emphasize ES as a primary target should be updated to reflect:
- **ZL is PRIMARY**
- **MES/ES is SECONDARY** (correlations only)
- **MES page is "silent hidden"** - not the main project

---

## KEY TAKEAWAYS

1. **Everything serves ZL prediction**
2. **ES/MES is correlation support only**
3. **News filtering focuses on ZL-relevant topics**
4. **General financial market news is filtered out**
5. **MES page exists but is not the main project**

---

**Last Updated**: November 18, 2025  
**Maintained By**: Data Collection Pipeline

