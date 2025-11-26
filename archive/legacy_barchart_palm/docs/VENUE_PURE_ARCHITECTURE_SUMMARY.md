---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Venue-Pure Architecture Summary
**Date**: November 18, 2025  
**Strategy**: CME/CBOT/NYMEX/COMEX ONLY + Free APIs  
**Key Insight**: Use CME-native crush/oilshare instead of external palm

---

## Revolutionary Change: CME-Native Substitution Economics

### ❌ Old Approach (External Dependencies)
```
Palm oil (Barchart/ICE) → Substitution driver
Rapeseed, sunflower (World Bank) → Competing oils
NewsAPI, Alpha sentiment → Paid news feeds
```

### ✅ New Approach (Venue-Pure)
```
CME Soybean Oilshare Index (COSI) → Substitution signal
CME Soybean Crush (board + theoretical) → Processing economics
CME CVOL → Implied volatility
Calendar spreads → Carry and stock-use signals
NYMEX Ethanol futures (CU) → Biofuel demand proxy
ScrapeCreator ONLY → Free scraping (no paid news)
```

**Why Better**:
- ✅ No external dependencies (palm, ICE, BMD)
- ✅ Venue-native signals (CME provides the economics)
- ✅ Lower cost (no Barchart subscription)
- ✅ Better data quality (exchange-traded vs scraped)
- ✅ Microstructure available (trades, TBBO, MBP from DataBento)

---

## What's New in Venue-Pure Schema

### 1. ✅ CME Soybean Oilshare Index (COSI1-COSI9)

**Table**: `market_data.cme_indices_eod`
**What**: Ratio of soybean oil price to soybean meal price
**Values**: COSI1 (front month) through COSI9 (9 months out)
**Current**: 43.600% (Dec 2025, Nov 17)
**Collection**: EOD via ScrapeCreator (CME publishes daily)

**Why Critical**:
- Direct substitution signal (oil vs meal demand balance)
- If COSI drops → more meal demand relative to oil → bearish for ZL
- If COSI rises → more oil demand relative to meal → bullish for ZL
- **Replaces need for palm oil**

### 2. ✅ CME Soybean Crush Margins

**Table**: `signals.crush_oilshare_daily`
**Two Crush Values**:
1. **Board Crush**: CME-facilitated spread
2. **Theoretical Crush**: (ZL price × 11 + ZM price × 44) / ZS price - processing cost

**Why Critical**:
- Crush margin = profitability of crushing soybeans
- Wide crush → processors buy more soybeans → bullish for ZL
- Narrow crush → processors slow down → bearish for ZL
- **Direct processing economics, no palm needed**

### 3. ✅ CME CVOL (Implied Volatility)

**Table**: `market_data.cme_indices_eod` + `raw_intelligence.volatility_daily`
**What**: 30-day implied volatility for soybeans
**Current**: 20.9670 (Nov 18, 2025)
**Collection**: EOD via ScrapeCreator

**Why Critical**:
- Market-expected volatility
- High CVOL → crisis regime
- Complements VIX for volatility regime detection

### 4. ✅ Calendar Spreads (Carry Signals)

**Table**: `signals.calendar_spreads_1d`
**Spreads**: M1-M2, M1-M3 for ZL, ZS, ZM, CL, RB, HO
**What**: Front month - next month price difference

**Why Critical**:
- Positive carry (M1 > M2) → tight stocks → bullish
- Negative carry (M1 < M2) → ample stocks → bearish
- **Stock-use signal without external data**

### 5. ✅ Forward Curves (Convenience Yield)

**Table**: `market_data.futures_curve_1d`
**What**: Settlement prices for all contract months (6-12 months out)
**Collection**: EOD from DataBento

**Why Critical**:
- Curve shape (slope, curvature) → market expectations
- Backwardation → tight supply
- Contango → ample supply

### 6. ✅ NYMEX Ethanol Futures (CU)

**Table**: `signals.energy_proxies_daily`
**What**: Denatured fuel ethanol futures (NYMEX)
**Why Critical**:
- On-exchange biofuel proxy
- Ethanol demand competes with biodiesel for mandates
- **Replaces need for external RIN data** (as proxy)

### 7. ✅ Energy Crack Spreads

**Table**: `signals.energy_proxies_daily`
**Calculations**:
- 3-2-1 Crack: (2×RB + 1×HO - 3×CL) / 3
- HO timespread (M1-M2): Renewable diesel tightness proxy

**Why Critical**:
- Crack spread → refinery economics
- HO spread → diesel/renewable diesel demand
- **On-exchange biofuel signal**

### 8. ✅ Microstructure Features

**Table**: `market_data.orderflow_1m`
**From**: DataBento trades, TBBO, MBP-10 schemas
**Features**:
- Spread (bid-ask)
- Depth imbalance (bid size vs ask size)
- Trade imbalance (buyer vs seller initiated)
- Microprice deviation
- 1-minute realized volatility

**Why Critical**:
- Intraday flow signals
- Early warning of reversals
- High-frequency context for daily models

### 9. ✅ CME FX Proxies

**Table**: `market_data.fx_daily`
**CME Futures**: 6L (BRL/USD), USD/CNH
**FRED Fallback**: USD/CNY, USD/ARS (if CME thin)

**Why Critical**:
- BRL → Brazil crush economics
- CNY → China demand
- On-exchange first, FRED second

---

## What's Removed (Cleaner Architecture)

### ❌ External Palm Oil (Barchart/ICE)
**Replaced By**: CME Oilshare Index + Crush Margins
**Why**: CME-native substitution signal is more reliable

### ❌ World Bank Pink Sheet
**Replaced By**: CME crush/oilshare economics
**Why**: Don't need rapeseed/sunflower if we have oilshare

### ❌ NewsAPI / Alpha Sentiment (Paid)
**Replaced By**: ScrapeCreator ONLY (free scraping)
**Sources**: CME Market Insights, government sites, Truth Social

### ❌ Alpha Vantage (Except Free Tier)
**Keep**: Insider transactions (if free)
**Remove**: Paid sentiment, analytics
**Why**: ScrapeCreator can get same data for free

---

## Total: 31 Tables (Venue-Pure)

### market_data (11 tables)
1. `databento_futures_ohlcv_1m` - 29 symbols + spreads
2. `databento_futures_ohlcv_1d` - Daily + settlement
3. `databento_futures_continuous_1d` - Roll-proof continuous
4. `roll_calendar` - Roll dates and back-adj
5. `futures_curve_1d` - Forward curves (6-12 months)
6. `cme_indices_eod` - COSI + CVOL
7. `fx_daily` - CME FX + FRED fallback
8. `orderflow_1m` - Microstructure
9. `yahoo_zl_historical_2000_2010` - Historical bridge

### raw_intelligence (7 tables)
10. `fred_economic` - 60 series (existing)
11. `eia_biofuels` - Granular PADD, RINs
12. `usda_granular` - By destination, by state
13. `weather_segmented` - By area code
14. `weather_weighted` - Production-weighted
15. `cftc_positioning` - COT
16. `policy_events` - Trump scripts (ScrapeCreator)
17. `volatility_daily` - VIX + CVOL + realized

### signals (5 tables)
18. `calendar_spreads_1d` - M1-M2, M1-M3
19. `crush_oilshare_daily` - Board + theoretical
20. `energy_proxies_daily` - Crack, ethanol, spreads
21. `calculated_signals` - Technical indicators
22. `big_eight_live` - Big 8 (15-min refresh)

### features (1 table)
23. `master_features` - Canonical

### regimes (1 table)
24. `market_regimes` - Per symbol

### drivers (2 tables)
25. `primary_drivers`
26. `meta_drivers`

### neural (1 table)
27. `feature_vectors`

### dim (3 tables)
28. `instrument_metadata`
29. `production_weights`
30. `crush_conversion_factors`

### ops (1 table)
31. `data_quality_events`

---

## Cost (Month 12)

| Component | Size | Cost |
|-----------|------|------|
| **CME Data** (all DataBento + indices) | ~600 MB | $0.012 |
| **Free APIs** (FRED/USDA/EIA/CFTC/NOAA) | ~400 MB | $0.008 |
| **ScrapeCreator** (policy/CME indices) | ~200 MB | $0.004 |
| **Calculated** (crush/spreads/signals) | ~800 MB | $0.016 |
| **Master Features** | ~2.5 GB | $0.050 |
| **Other** (regimes/drivers/neural) | ~1.5 GB | $0.030 |
| **TOTAL** | **~6.0 GB** | **$0.12/month** |

**No external subscriptions needed** (Barchart, World Bank, NewsAPI, Alpha paid)

---

## Summary: Why Venue-Pure is Better

**Before** (External Dependencies):
- ❌ Need Barchart for palm ($?)
- ❌ Need World Bank for vegoils
- ❌ Need NewsAPI ($50/month)
- ❌ Need Alpha Vantage paid ($75/month)
- ❌ Data quality issues (scraped prices)
- ❌ Multiple vendors to manage

**After** (Venue-Pure):
- ✅ CME Oilshare Index (COSI) for substitution
- ✅ CME Crush for processing economics
- ✅ CME CVOL for implied volatility
- ✅ Calendar spreads for carry signals
- ✅ NYMEX ethanol for biofuel demand
- ✅ All exchange-traded (reliable)
- ✅ Single vendor (DataBento + CME)
- ✅ ScrapeCreator for free text (no paid news)

**Total External Cost**: $0 (just DataBento plan you already have)

---

## File: VENUE_PURE_SCHEMA.sql

**Ready to deploy**: 31 tables, all venue-pure

**Next Steps**:
1. Deploy schema to BigQuery
2. Create CME scraper for COSI/CVOL (ScrapeCreator)
3. Create crush/oilshare calculator
4. Create calendar spread calculator
5. Create microstructure processor
6. Integrate Trump scripts (already exist!)
7. Wire Big 8 refresh (15-min)

**Ready to execute?**


