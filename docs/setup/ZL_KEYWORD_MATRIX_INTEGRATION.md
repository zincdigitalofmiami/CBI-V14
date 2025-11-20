---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# ZL (Soybean Oil) Institutional-Grade Keyword Matrix Integration

**Date**: November 18, 2025  
**Status**: ✅ Integrated into News Sentiment Collection Pipeline

---

## Overview

The news sentiment collection script (`collect_alpha_vantage_comprehensive.py`) now uses an **institutional-grade keyword matrix** with **40 categories** and **450+ keywords** covering:

- **Direct drivers** (biofuel, palm policy, crop logistics)
- **Indirect drivers** (FX, shipping, weather)
- **Drivers-of-drivers** (defense-agriculture nexus, pharma reciprocity, CBDC)

This matrix is designed to feed:
- **Hidden Relationship Intelligence Module**
- **Ultimate Signal Architecture**
- **Big 7/Big 14 signal expansion**

---

## Matrix Statistics

- **Total Categories**: 40
- **Primary Keywords**: 240
- **Trigger Phrases**: 77 (predictive signals)
- **Agencies**: 4 (EPA, DOE, CARB, ANP Brazil)
- **Total Keywords/Phrases/Agencies**: 321

---

## Category Coverage

### Direct Drivers (ZL ↑/↓)
1. **Biofuel Mandates / SAF / LCFS** (ZL ↑ strong)
2. **Indonesia/Malaysia Palm Policy** (Palm ↑ → ZL ↑)
3. **China Agricultural Demand / State Reserves** (ZL ↑/↓)
4. **Trump / U.S. Policy / Tariffs** (Structural shifts)
5. **Brazil & Argentina Crop + Logistics** (Major supply driver)
6. **Weather (US/Brazil/Argentina)** (Agronomically relevant)
7. **Crush Margins & Processing Capacity** (ZL ↑)
8. **Food Security Policies** (ZL ↑)
9. **Soybean Disease / Pests** (ZL ↑)

### Indirect Drivers
10. **Shipping, Chokepoints, War Risk Insurance** (ZL ↑)
11. **Shipping Freight Rates** (ZL ↑)
12. **Global FX Shifts (BRL, ARS, CNY)** (Origin switching)
13. **Inflation, Rates, Macro Liquidity** (ZL ↑)
14. **Spec Positioning (CFTC)** (Flows drive ZL)
15. **Risk-Off / VIX Surges** (ZL ↓)
16. **Energy Markets (Crude, Diesel)** (Correlation)
17. **Fertilizer & Energy Input Shocks** (ZL ↑)

### Drivers-of-Drivers (Hidden Relationships)
18. **Defense-Agriculture Nexus** (Hidden realignment)
19. **Pharmaceutical Licensing → Agricultural Reciprocity** (ZL ↑)
20. **CBDC + Trade Settlement Channels** (Currency bypass)
21. **Sovereign Wealth Funds** (3-6 month lead)
22. **Biofuel Lobbying Chain** (60-120 day lead)
23. **Carbon Market Arbitrage / EU Deforestation Law (EUDR)** (Origin switching)
24. **Port Construction & Dredging Projects** (6-12 month lead)
25. **Academic / Ag University Cooperation** (Soft diplomacy)

### Policy & Regulatory
26. **U.S. Farm Bill / Commodity Programs** (ZL ↑/↓)
27. **GMO / Agrochemical Policy** (ZL ↑/↓)
28. **U.S.-China Strategic Tensions** (ZL ↑/↓)
29. **Elections / Political Instability** (Policy shifts)

### Supply Chain & Logistics
30. **Labor Strikes (Ports, Trucks, Barge Lines)** (ZL ↑)
31. **South American Trucking / Logistics** (Critical timing)
32. **Port Throughput Indicators** (Predictive)
33. **Infrastructure Failures / Industrial Accidents** (ZL ↑)
34. **Tanker Availability / Clean Tanker Dynamics** (Competition)
35. **Shipping Insurance / Reinsurance** (ZL ↑)

### Market Dynamics
36. **Refinery & RD Capacity Expansions** (ZL ↑)
37. **Black Sea / War Spillovers** (ZL ↑)
38. **Bank Lending / Credit Crunch** (ZL ↓)
39. **Chinese Local Government Financing Vehicles (LGFVs)** (ZL ↓)
40. **Digital Trade, Blockchain, Supply Chain Traceability** (Compliance)

---

## Filtering Logic

The `filter_zl_relevant_articles()` function:

1. **Checks for irrelevant keywords first** (stronger filter):
   - General tech, entertainment, sports
   - Unrelated financial news
   - ES/MES-specific news (unless commodity-related)

2. **Matches against institutional matrix**:
   - **Primary keywords** (strong match)
   - **Trigger phrases** (very strong match - predictive signals)
   - **Agency names** (regulatory/policy context)

3. **Returns filtered DataFrame** with only ZL-relevant articles

---

## Integration Points

### News Sentiment Collection
- **Function**: `fetch_news_sentiment()`
- **Parameter**: `filter_zl_relevant=True` (default)
- **Output**: Articles filtered using institutional matrix

### Main Collection Script
- **Topics Collected**: `economy_macro`, `economy_monetary` (affect commodity prices)
- **Excluded**: `financial_markets` (too broad, includes ES/MES)
- **All articles filtered** through institutional matrix before saving

---

## Example Matches

### ✅ Kept (ZL-Relevant)
- "EPA Announces Final Rule for RFS Volumes, Expanding SAF Credit" → **Biofuel Mandates**
- "Indonesia Export Ban on Palm Oil Due to El Nino Dry Estates" → **Palm Policy**
- "Rosario Port Strike Disrupts Soybean Exports" → **Labor Strikes**
- "Sovereign Wealth Fund Acquires 5% Stake in Agribusiness" → **Sovereign Wealth**
- "Panama Canal Drought Causes Shipping Delays" → **Shipping Chokepoints**

### ❌ Filtered Out (Not Relevant)
- "Tech Startup Raises $100M Series B" → General tech
- "S&P 500 Hits New High" → ES/MES-specific (no commodity context)
- "Movie Premiere Draws Crowds" → Entertainment

---

## Usage

```python
from scripts.ingest.collect_alpha_vantage_comprehensive import fetch_news_sentiment

# Collect ZL-relevant news (automatically filtered)
result = fetch_news_sentiment(topics='economy_macro', filter_zl_relevant=True)

# Access the keyword matrix directly
from scripts.ingest.collect_alpha_vantage_comprehensive import ZL_KEYWORD_MATRIX
print(f"Categories: {len(ZL_KEYWORD_MATRIX)}")
```

---

## Future Enhancements

1. **Relevance Scoring**: Score articles by number of keyword matches
2. **Category Tagging**: Tag articles with matched categories
3. **Effect Direction**: Tag articles with ZL ↑/↓/MIXED effects
4. **Lead Time Indicators**: Flag predictive signals (60-120 day leads)
5. **Hidden Relationship Detection**: Cross-reference multiple categories

---

**Last Updated**: November 18, 2025  
**Maintained By**: Data Collection Pipeline  
**Source**: Institutional-Grade Cross-Domain Keyword Matrix





