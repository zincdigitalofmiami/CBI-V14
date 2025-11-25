# CBI-MES Master Plan (Feasible Version)
**Version:** 1.0  
**Date:** November 24, 2025  
**Owner:** ZINC Digital / CBI  
**Status:** Documented for future implementation (after ZL engine complete)

---

## Executive Summary

**MES is NOT ready for implementation yet.**  
- Current MES data: 2,036 rows (2019-05-05 → 2025-11-16)  
- **Required:** Full history from 2010-01-01 → 2025-11-24  
- **Action:** Pull complete MES history from Databento before MES engine build

**VIX Futures (VX.FUT) is NOT available.**  
- VX.FUT trades on CBOE CFE, not CME Globex  
- Subscription: `GLBX.MDP3` (CME only)  
- **Solution:** Use FRED VIX substitutes + calculations for confirmation

**Priority:** ZL engine first, MES engine after ZL is stable.

---

## 1. Purpose & Positioning

The MES subsystem is a private, trader-facing intelligence module within CBI.

**It is:**
- Fully isolated from ZL (soybean oil models)
- Allowed to share only macro/FX/VIX data with ZL (read-only)
- Focused on equity index microstructure and daily/medium-term outlooks
- Powered by local Mac training using features stored in BigQuery

MES is designed to match institutional-grade equity modeling workflows, within the constraints of our current stack (no options surface vendors, no dark pool feeds, no proprietary APIs).

---

## 2. High-Level Architecture

MES has two model families:

### 2.1 Intraday / Special Models (microstructure-focused)
- **Horizons:** 1m, 5m, 15m, 30m, 1h, 4h
- **Main production model for UI:** 1h Special model
- **Purpose:** Drive the Intraday Gauge (direction/volatility/level-hit probabilities)

### 2.2 Daily / Main Models (macro + vol + sentiment)
- **Horizons:** 1d, 7d (1w), 30d (1m), 3m, 6m, 12m
- **Purpose:** Drive the Daily→12M Fan Chart with P10/P50/P90, SHAP drivers and scenarios

### 2.3 Training Location
**All training:**
- Runs exclusively on the Mac (LightGBM / XGBoost / PyTorch)
- Uses data exported from BigQuery feature tables

**BigQuery is:**
- Storage + feature store only
- Never used for training (no BQML, no Vertex training)

---

## 3. MES vs ZL: Hard Separation

**MES:**
- Asset: MES (Micro E-mini S&P) only
- Domain: Equity index microstructure + macro-equity regimes
- Models: Intraday gauge + daily fan chart

**ZL:**
- Asset: Soybean oil futures (ZL)
- Domain: Commodity procurement & biofuel policy regimes

**Rules:**
- MES does not use ZL prices, regimes, features or predictions
- MES and ZL share only:
  - Macro (FRED & related)
  - FX
  - VIX and simple vol metrics
  - Optional shared news buckets (e.g., macro_fx) – read-only
- **No cross-asset joins between MES and ZL are allowed in BigQuery**

---

## 4. Data Requirements

### 4.1 Databento Data (MES Engine)

**Prime Data (Full Depth):**
| Symbol | Schemas | Date Range | Status |
|--------|---------|------------|--------|
| **MES.FUT** | All (ohlcv-1s/1m/1h/1d, bbo-1s/1m, tbbo, mbp-1/10, mbo, statistics) | **2010-01-01 → 2025-11-24** | ⚠️ **Need full history** |

**Supporting Data (Lean Schemas):**
| Symbol | Purpose | Schemas | Date Range | Status |
|--------|---------|---------|------------|--------|
| **ES.FUT** | Flow context (institutional flow) | ohlcv-1m/1h/1d, bbo-1m, statistics | 2010-01-01 → 2025-11-24 | ❌ Need pull |
| **ZQ.FUT** | Fed Funds futures (rate expectations) | ohlcv-1d, statistics | 2010-01-01 → 2025-11-24 | ❌ Need pull |
| **ZT.FUT** | 2-Year Treasury (front-end rates) | ohlcv-1h/1d, statistics | 2010-01-01 → 2025-11-24 | ❌ Need pull |
| **ZN.FUT** | 10-Year Treasury (duration) | ohlcv-1h/1d, statistics | 2010-01-01 → 2025-11-24 | ❌ Need pull |
| **ZB.FUT** | 30-Year Treasury (long duration) | ohlcv-1d, statistics | 2010-01-01 → 2025-11-24 | ❌ Need pull |
| **VX.FUT** | VIX futures (vol term structure) | ❌ **NOT AVAILABLE** | - | ⚠️ **Use FRED substitutes** |

**Critical:** MES.FUT currently only has 2,036 rows (2019-2025). **Need to pull full history from 2010-01-01.**

### 4.2 VIX Alternatives (No VX.FUT)

**Problem:** VX.FUT trades on CBOE CFE (`XCFE.OCELOT`), not CME Globex (`GLBX.MDP3`). Not in current subscription.

**Solution: ✅ Use FRED VIX Substitutes (Now Available)**

| Source | Series | Purpose | Calculation | Status |
|--------|--------|---------|-------------|--------|
| **FRED** | `VIXCLS` | Spot VIX | Base level | ✅ Loaded |
| **FRED** | `VXVCLS` | 3-Month VIX | Term structure | ✅ Loaded |
| **FRED** | `VXOCLS` | Old VXO | Alternative vol | ✅ Loaded |
| **Calculated** | `vix_term_structure` | Term structure ratio | `VXVCLS / VIXCLS` | ✅ Can calculate |
| **Calculated** | `vix_term_slope` | Term structure slope | `VXVCLS - VIXCLS` | ✅ Can calculate |
| **Calculated** | `vix_contango_flag` | Contango regime | `VXVCLS > VIXCLS` | ✅ Can calculate |
| **Calculated** | `vix_backwardation_flag` | Backwardation regime | `VXVCLS < VIXCLS` | ✅ Can calculate |

**Additional Features:**
- Vol risk premium: `VIXCLS - mes_realized_vol_20d`
- VIX percentile vs historical (regime classification)
- VIX momentum (rate of change)

**✅ All VIX data now available from FRED.**

### 4.3 FRED Data (MES Engine)

**✅ Already Have:**
- DGS10, DGS2, DGS30 (Treasury yields)
- FEDFUNDS, DFF (Fed Funds rate)
- T10Y2Y (yield curve spread)
- VIXCLS (VIX spot)
- DTWEXBGS (Dollar index)
- BAMLC0A0CM, BAMLH0A0HYM2 (credit spreads)
- WALCL (Fed balance sheet)

**❌ Need to Add:**
| Series | Purpose | Priority |
|--------|---------|----------|
| **T10YIE** | 10Y Breakeven Inflation (real yields) | 🔴 CRITICAL |
| **NFCI** | Financial Conditions Index | 🟡 HIGH |
| **DEXJPUS** | USD/JPY (carry trade) | 🟢 MEDIUM |
| **VIX9D** | 9-day VIX (term structure) | 🔴 CRITICAL |
| **VIX3M** | 3-month VIX (term structure) | 🔴 CRITICAL |

### 4.4 FX Data (MES Engine)

**Source:** ✅ **FRED FX series (primary source)**

**FX Series from FRED (All Loaded):**
| Series | Purpose | Rows | Date Range | Status |
|--------|---------|------|------------|--------|
| **DEXJPUS** | USD/JPY (carry trade signal) | 3,975 | 2010-2025 | ✅ Loaded |
| **DEXCHUS** | USD/CNY (China FX) | 3,975 | 2010-2025 | ✅ Loaded |
| **DEXUSEU** | EUR/USD (Euro cross) | 3,975 | 2010-2025 | ✅ Loaded |
| **DEXBZUS** | USD/BRL (Brazil FX) | 3,975 | 2010-2025 | ✅ Loaded |
| **DTWEXBGS** | Dollar Index Broad | 3,975 | 2010-2025 | ✅ Loaded |
| **DTWEXAFEGS** | Dollar Index AFE | 3,975 | 2010-2025 | ✅ Loaded |
| **DTWEXEMEGS** | Dollar Index EME | 3,975 | 2010-2025 | ✅ Loaded |

**Note:** FX data comes from FRED, not Databento. Databento FX futures (6E, 6J, 6B) are optional for additional granularity but not required.

---

## 5. Feature Families (Feasible Only)

MES uses the following families – each strictly limited to existing sources:

### 5.1 Microstructure (Intraday only)
- **Source:** Databento TBBO, BBO, MBP-1, MBP-10, statistics, OHLCV-1s/1m
- **Examples:** spread, depth imbalance, trade/quote imbalance, microprice, realized intraday vol

### 5.2 Intraday Technical (Special models)
- **Source:** Python TA over 1m/5m/15m/30m/1h bars
- **Examples:** EMA/SMA, RSI, Bollinger, ATR, short-horizon returns

### 5.3 Macro (Daily)
- **Source:** FRED + existing eco scripts
- **Examples:** fed funds, 2y/10y yields, curve, CPI, unemployment

### 5.4 Volatility (Daily)
- **Source:** FRED VIX family: VIXCLS, VIX9D, VIX3M
- **Derived:** VIX term slope (`VIX3M - VIXCLS`), realized MES vol, vol risk premium

### 5.5 FX (Daily + Intraday Context)
- **Source:** Existing FX ingestion (USDJPY, USDCNH, EURUSD, DXY)
- **Features:** returns, volatility, short-horizon "pressure" measures

### 5.6 Global Indices (Daily Context)
- **Source:** Yahoo/existing scripts (DAX, FTSE, NKD)
- **Features:** daily returns, rolling correlations

### 5.7 Sentiment & News Buckets
- **Source:** Internal news bucket taxonomy (tariffs, china_demand, macro_fx, logistics_shipping, etc.) + NLP + Trump/Fed shock detection
- **Features:** 1d, 3d, 7d bucket intensities; shock flags; global sentiment scores

### 5.8 MES Regimes
- **Derived:** MES realized vol, VIX percentiles, trend slopes and rate-cycle signals
- **Features:** mes_vol_regime, mes_trend_regime, mes_rate_regime

---

## 6. Regime System

MES uses an independent regime calendar with three dimensions:

### 6.1 Volatility Regime
- **Labels:** LOW_VOL, MED_VOL, HIGH_VOL, PANIC_VOL
- **Inputs:** mes_realized_vol_20d, mes_realized_vol_percentile, vix, vix_percentile
- **Rules:** Based on percentile thresholds (see MES_REGIME_CALENDAR_SPEC.md)

### 6.2 Trend Regime
- **Labels:** BULL, BEAR, NEUTRAL
- **Inputs:** mes_trend_slope_50d, mes_close_vs_200d_ma
- **Rules:** Based on slope direction and position relative to 200d MA

### 6.3 Macro Rate Regime
- **Labels:** HIKE_CYCLE, PAUSE_CYCLE, CUT_CYCLE
- **Inputs:** fed_funds_effective, hikes_last_12m, cuts_last_6m
- **Rules:** Based on Fed rate change history

**Full definitions:** See `MES_REGIME_CALENDAR_SPEC.md` (included below)

---

## 7. Training Surfaces

MES defines two training surface families:

### 7.1 Special (Intraday) – 1m, 5m, 15m, 30m, 1h, 4h
- **Inputs:** microstructure, intraday TA, short-term macro/FX context, regimes, sentiment windows
- **Targets:** next-bar direction, volatility, key-level hit probability
- **Tables:** `training_mes.special_1m`, `training_mes.special_5m`, etc.

### 7.2 Main (Daily) – 1d, 1w, 1m, 3m, 6m, 12m
- **Inputs:** daily MES TA, macro, FX, VIX, global indices, sentiment, regimes
- **Targets:** forward returns and P10/P50/P90 paths
- **Tables:** `training_mes.main_1d`, `training_mes.main_1w`, etc.

**Full definitions:** See `MES_TRAINING_SURFACES_SPEC.md` (included below)

---

## 8. Dataflow & UI Integration

**Raw data → Python ingestion → MES feature tables in BigQuery**

**Feature tables → exports → Mac training → prediction tables in BigQuery**

**Vercel MES page reads prediction tables to render:**
- Intraday Gauge (Special 1h model)
- Daily→12M fan chart (Main models)
- Regime strips and scenario text

**Full API contract:** See `MES_DATAFLOW_AND_API_CONTRACT.md` (included below)

---

## 9. Roadmap

MES development is staged:

### v0: TA-only 1h Special model, basic gauge
- Single horizon: 1h Special model
- Features: intraday OHLCV + basic TA (returns, EMA/SMA, RSI, volatility)
- No microstructure, no macro, no FX, no VIX, no regimes, no sentiment
- UI: basic Intraday Gauge only

### v1: Full microstructure features + 1d Main model
- Extend Special models to include microstructure features
- VIX and FX as context
- Introduce Main model for 1d horizon
- UI: Gauge upgraded, optional 1d forecast card

### v2: Regime calendar, multi-horizon fan chart, sentiment integration
- Regime calendar live
- Full Main model family (1d, 1w, 1m, 3m, 6m, 12m)
- Sentiment & news buckets integrated
- UI: Full Daily→12M fan chart, regime strip, scenario text

**Full roadmap:** See `MES_ROADMAP_V0_V2.md` (included below)

---

## 10. Implementation Timeline

**Status:** MES engine is **NOT ready for implementation**

**Prerequisites:**
1. ✅ ZL engine complete and stable
2. ❌ Pull full MES history (2010-2025) from Databento
3. ❌ Pull ES, ZQ, ZT, ZN, ZB from Databento
4. ❌ Add VIX9D, VIX3M, T10YIE, NFCI, DEXJPUS to FRED pull
5. ❌ Create MES engine tables in BigQuery
6. ❌ Build MES feature views
7. ❌ Train MES models

**Estimated Timeline:** 3-4 weeks after ZL engine is complete

---

## 11. Critical Constraints

1. **No VX.FUT** - Use FRED VIX substitutes (VIXCLS, VIX9D, VIX3M) + calculations
2. **No cross-asset joins** - MES and ZL are completely separate
3. **No BigQuery training** - All training on Mac
4. **No new data vendors** - Use only existing sources (Databento, FRED, FX, VIX, news)

---

## 12. Success Criteria

### Data Requirements
- ✅ MES.FUT: Full history 2010-2025 (currently only 2019-2025)
- ✅ Supporting symbols: ES, ZQ, ZT, ZN, ZB pulled and loaded
- ✅ FRED VIX: VIXCLS, VIX9D, VIX3M loaded
- ✅ FRED Macro: T10YIE, NFCI, DEXJPUS loaded

### Feature Requirements
- ✅ Microstructure features calculated from Databento depth data
- ✅ VIX term structure calculated from FRED (VIX3M - VIXCLS)
- ✅ Regime calendar populated and stable
- ✅ Training surfaces built for all horizons

### Model Requirements
- ✅ Special 1h model trained and producing predictions
- ✅ Main multi-horizon models trained (1d, 1w, 1m, 3m, 6m, 12m)
- ✅ Predictions written to BigQuery
- ✅ UI consuming predictions correctly

---

## Appendices

### Appendix A: MES Regime Calendar Specification
See `MES_REGIME_CALENDAR_SPEC.md` (detailed regime rules)

### Appendix B: MES Training Surfaces Specification
See `MES_TRAINING_SURFACES_SPEC.md` (detailed feature definitions)

### Appendix C: MES Dataflow & API Contract
See `MES_DATAFLOW_AND_API_CONTRACT.md` (API endpoints and schemas)

### Appendix D: MES Roadmap v0-v2
See `MES_ROADMAP_V0_V2.md` (detailed implementation steps)

---

**Status:** ✅ **DOCUMENTED - READY FOR FUTURE IMPLEMENTATION**

**Next Action:** Complete ZL engine first, then proceed with MES data pulls and implementation.

