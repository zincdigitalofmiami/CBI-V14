---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# DataBento Coverage - Validation Results
**Date**: November 18, 2025  
**API**: db-cSwxrJxRGGbqSBX74iuh9gqPrF4xf  
**Plan**: CME Globex MDP3.0 Standard (Futures + Options)

---

## What DataBento HAS ✅

### Core Futures (14 symbols) - ALL CONFIRMED
- ES, MES, ZL, ZS, ZM, CL, NG, ZC, ZW, RB, HO, GC, SI, HG

### FX Futures (6 pairs) - ALL CONFIRMED
- 6E (EUR/USD), 6B (GBP/USD), 6J (JPY/USD)
- 6C (CAD/USD), 6A (AUD/USD), 6S (CHF/USD)

### Additional AG (2 symbols)
- ZR (Rice), ZO (Oats)

### Livestock (3 symbols)
- LE (Live Cattle), GF (Feeder Cattle), HE (Lean Hogs)

### Energy (2 additional)
- BZ (Brent Crude), QM (E-mini Crude)

### Metals (2 additional)
- PA (Palladium), PL (Platinum)

**TOTAL FROM DATABENTO: 29 symbols** ✅

---

## What DataBento DOES NOT HAVE ❌

### Palm Oil - NOT AVAILABLE
Tested: PO.FUT, FCPO.FUT, PKO.FUT, PALM.FUT
**Result**: All returned "symbology_invalid_request"
**Solution**: Use Barchart/ICE/Yahoo as Fresh Start specifies

### Other Vegetable Oils - NOT AVAILABLE
Tested: RS.FUT (Rapeseed), SUN.FUT (Sunflower)
**Result**: Not available on CME Globex
**Solution**: World Bank Pink Sheet, Alpha Vantage, or ICE Europe

### Softs - MOSTLY NOT AVAILABLE
Tested: CT (Cotton), KC (Coffee), CC (Cocoa), SB (Sugar)
**Result**: Not on CME Globex (traded on ICE)
**Solution**: Not critical for ZL model (skip or use Alpha/Yahoo)

### RIN Prices / Biofuel Data - NOT AVAILABLE
**Reason**: Government data, not market-traded
**Solution**: EIA/EPA as Fresh Start specifies

---

## Final Data Source Mapping

### Use DataBento (29 symbols)

**Primary (5-min collection)**:
- ZL, MES

**Secondary (1-hour collection)**:
- ES, ZS, ZM, CL, NG, ZC, ZW, RB, HO, GC, SI, HG
- 6E, 6B, 6J, 6C, 6A, 6S (FX futures)
- BZ, QM (additional energy)
- PA, PL (additional metals)
- ZR, ZO (rice, oats - optional)
- LE, GF, HE (livestock - optional)

### Use Alternative Sources (Critical Gaps)

**Palm Oil** - Barchart/ICE:
- Prefix: `barchart_palm_`
- Collection: Daily
- Table: `market_data.oils_competing_daily`

**Spot FX** - FRED/Yahoo (if DataBento FX futures insufficient):
- USD/CNY, USD/ARS, USD/MYR (not on CME)
- Prefix: `fred_` or `yahoo_`
- Collection: Daily
- Table: `market_data.fx_spot_daily`

**RINs & Biofuels** - EIA/EPA:
- D4/D6 RIN prices, biodiesel by PADD, ethanol
- Prefix: `eia_`
- Collection: Daily check (weekly actuals)
- Table: `raw_intelligence.eia_biofuels_granular`

**USDA** - USDA NASS/FAS APIs:
- Granular exports (by destination)
- State-level yields
- Prefix: `usda_`
- Collection: Weekly
- Table: `raw_intelligence.usda_granular`

**Weather** - NOAA/INMET/SMN:
- US/BR/AR segmented by area
- Prefix: `weather_`
- Collection: Daily
- Table: `raw_intelligence.weather_segmented`

**Policy/Trump** - ScrapeCreators/NewsAPI:
- Truth Social, White House, USTR
- Prefix: `policy_trump_`
- Collection: Every 15 minutes
- Table: `raw_intelligence.policy_trump_signals`
- **Scripts**: Already exist! (`trump_action_predictor.py`, `zl_impact_predictor.py`)

---

## Expanded Symbol Universe

### Total Symbols to Collect

**From DataBento**: 29 symbols (futures + FX futures)
**From Barchart/ICE**: 1 (palm oil)
**From FRED/Yahoo**: 5+ (spot FX if needed)
**From EIA/EPA**: ~20 series (RINs, biofuels)
**From USDA**: ~50 series (granular ag data)

**Grand Total**: ~100+ data series

---

## Collection Schedule (Updated with Actuals)

### Every 5 Minutes (Primary)
```bash
DataBento: ZL, MES
```

### Every Hour (Secondary)
```bash
DataBento: ES, ZS, ZM, CL, NG, ZC, ZW, RB, HO, GC, SI, HG, 6E, 6B, 6J, 6C, 6A, 6S, BZ, QM, PA, PL
Optional: ZR, ZO, LE, GF, HE
```

### Every 4 Hours
```bash
FRED: 60 macro series (existing, don't touch)
```

### Every 8 Hours
```bash
CFTC: Positioning data
```

### Every 15 Minutes
```bash
News Breaking: ZL critical news
Policy/Trump: Truth Social, White House (EXISTING SCRIPTS!)
```

### Daily
```bash
Weather: US/BR/AR segmented
Palm Oil: Barchart/ICE
Spot FX: USD/CNY, USD/ARS, USD/MYR
EIA Biofuels: Check for updates
Alpha Insider: Biofuel/ag companies
Alpha Analytics: Fixed + sliding windows
```

### Weekly
```bash
USDA: Granular exports, yields
EIA: Biofuel production reports
```

---

## Next Steps

1. ✅ **DataBento validated** - 29 symbols confirmed
2. ✅ **Palm NOT on DataBento** - Use Barchart/ICE as planned
3. ✅ **RINs NOT on DataBento** - Use EIA/EPA as planned
4. ✅ **Trump scripts EXIST** - Integrate into architecture

**Ready to create COMPLETE BigQuery schema** with:
- DataBento tables (29 symbols)
- Alternative source tables (palm, RINs, spot FX, etc.)
- Trump/policy tables (use existing scripts)
- Processing layers (regimes, drivers, signals, Big 8)
- master_features canonical table

**Are you ready for me to create the complete BigQuery DDL with all tables?**


