# MES Features - What Actually Moves This Thing
**Date:** November 25, 2025  
**Purpose:** Comprehensive breakdown of MES price drivers, features, and data requirements

---

## The Reality of MES/ES

MES is the most traded futures contract on the planet. It's not some niche commodity - it's the pure distillation of global risk appetite. Every hedge fund, pension fund, central bank, and algo shop in the world touches this market. To forecast it, you need to understand what actually drives institutional flows.

---

## Primary Drivers (Ranked by Real Impact)

### 1. Federal Reserve Policy (40-50% of Price Variance)

**What Matters:**
- Fed Funds Rate (current vs expected path)
- FOMC dot plot expectations
- Fed balance sheet (QE/QT pace)
- Powell speeches and Fed governor comments
- Market pricing of next move (Fed Funds futures)

**Features to Build:**
| Feature | Description |
|---------|-------------|
| `fed_funds_rate` | Current effective rate |
| `fed_funds_expected_1m` | 1-month forward rate from futures |
| `fed_funds_expected_3m` | 3-month forward rate |
| `fed_funds_expected_6m` | 6-month forward rate |
| `fed_rate_surprise` | Actual vs expected at last meeting |
| `fed_pivot_probability` | Market-implied probability of rate cut/hike |
| `fomc_days_until` | Trading days until next FOMC |
| `fomc_drift` | Historical MES behavior pre/post FOMC |
| `qt_pace_monthly` | Balance sheet runoff rate |

**Data Sources:**
- FRED: FEDFUNDS, DFF, WALCL (balance sheet)
- Databento: **ZQ.FUT** (Fed Funds futures) - **ADD THIS**
- CME FedWatch tool data (if accessible)

---

### 2. Treasury Yields & Curve Dynamics (25-30% of Price Variance)

**What Matters:**
- 10-Year yield level and direction
- 2s10s spread (curve shape)
- Real yields (TIPS-implied)
- Term premium
- Yield volatility (MOVE index)

**Features to Build:**
| Feature | Description |
|---------|-------------|
| `yield_10y` | 10-Year Treasury yield |
| `yield_2y` | 2-Year Treasury yield |
| `yield_30y` | 30-Year Treasury yield |
| `yield_2s10s_spread` | Curve slope (inversion signal) |
| `yield_2s10s_momentum_5d` | Curve flattening/steepening speed |
| `yield_10y_momentum_5d` | Rate of change in 10Y |
| `yield_10y_momentum_20d` | Monthly trend |
| `real_yield_10y` | 10Y minus inflation expectations |
| `yield_volatility_20d` | Rolling volatility of 10Y moves |
| `move_index` | Bond market volatility (if available) |
| `term_premium` | Compensation for duration risk |
| `yield_curve_regime` | Steep/flat/inverted classification |

**Data Sources:**
- FRED: DGS10, DGS2, DGS30, T10YIE (breakeven inflation)
- Databento: **ZN.FUT** (10Y), **ZT.FUT** (2Y), **ZB.FUT** (30Y) - **ADD ZT**

---

### 3. Volatility Complex (15-20% of Price Variance)

**What Matters:**
- VIX level (fear gauge)
- VIX term structure (contango = complacency, backwardation = panic)
- VIX of VIX (VVIX) - volatility of volatility
- Realized vs implied vol spread
- Put/call skew
- 0DTE options flow

**Features to Build:**
| Feature | Description |
|---------|-------------|
| `vix_spot` | Current VIX level |
| `vix_percentile_1y` | Where VIX sits vs last year |
| `vix_term_structure` | VX1/VX2 ratio (contango/backwardation) |
| `vix_term_slope` | Steepness of vol curve |
| `vix_momentum_5d` | VIX rate of change |
| `vix_spike_flag` | VIX up >20% in single day |
| `vix_mean_reversion_signal` | VIX >30 historically mean reverts |
| `realized_vol_5d` | Actual MES volatility last 5 days |
| `realized_vol_20d` | Actual MES volatility last 20 days |
| `vol_risk_premium` | VIX minus realized vol (overpriced fear?) |
| `vix_regime` | Low (<15), Normal (15-25), Elevated (25-35), Crisis (>35) |
| `vvix` | Volatility of VIX (if available) |
| `skew_index` | Put/call skew (tail risk pricing) |

**Data Sources:**
- FRED/Yahoo: ^VIX, ^VVIX
- Databento: VX.FUT (VIX futures for term structure) - **NOT AVAILABLE IN SUBSCRIPTION**
- CBOE: Skew index (if accessible)
- **SOLUTION:** Use FRED VIXCLS + VXVCLS (3-month VIX) for term structure

---

### 4. Dollar & Global Liquidity (10-15% of Price Variance)

**What Matters:**
- DXY strength/weakness
- Dollar liquidity conditions
- Cross-border capital flows
- Risk-on/risk-off currency signals

**Features to Build:**
| Feature | Description |
|---------|-------------|
| `dxy_level` | Dollar index |
| `dxy_momentum_5d` | Dollar trend short-term |
| `dxy_momentum_20d` | Dollar trend medium-term |
| `dxy_percentile_1y` | Dollar strength relative to year |
| `usdjpy_level` | Yen as risk barometer |
| `usdjpy_momentum_5d` | Carry trade signal |
| `eurusd_level` | Euro cross |
| `dollar_liquidity_proxy` | TED spread or similar |
| `global_liquidity_index` | Central bank balance sheets combined |

**Data Sources:**
- FRED: DTWEXBGS (broad dollar), DEXJPUS, DEXUSEU
- Already have currency_data table

---

### 5. Credit Conditions (5-10% of Price Variance)

**What Matters:**
- Investment grade spreads
- High yield spreads
- Credit default swap indices
- Financial conditions indices

**Features to Build:**
| Feature | Description |
|---------|-------------|
| `ig_spread` | Investment grade OAS |
| `hy_spread` | High yield OAS |
| `credit_spread_momentum_5d` | Spread widening/tightening |
| `hy_ig_ratio` | Risk appetite in credit |
| `financial_conditions_index` | Chicago Fed NFCI or similar |
| `ted_spread` | Interbank stress |
| `libor_ois_spread` | Banking system stress (or SOFR equivalent) |

**Data Sources:**
- FRED: BAMLC0A0CM (IG), BAMLH0A0HYM2 (HY), NFCI, TEDRATE

---

### 6. Equity Internals & Flows (5-10% of Price Variance)

**What Matters:**
- Breadth (advance/decline)
- Sector rotation
- Size factor (small vs large cap)
- Institutional positioning
- ETF flows

**Features to Build:**
| Feature | Description |
|---------|-------------|
| `spx_breadth` | % stocks above 200 DMA |
| `spx_advance_decline` | A/D line momentum |
| `russell_spx_ratio` | Small cap vs large cap |
| `sector_rotation_signal` | Defensive vs cyclical leadership |
| `spy_flow_5d` | SPY ETF flows |
| `es_open_interest` | ES futures positioning |
| `es_volume_ratio` | Current vs average volume |
| `cot_asset_manager_net` | CFTC positioning (large specs) |
| `put_call_ratio` | Options sentiment |
| `gamma_exposure` | Dealer hedging pressure (if calculable) |

**Data Sources:**
- Databento: ES.FUT statistics (OI, volume)
- CFTC: COT reports for ES
- Yahoo: Sector ETFs for rotation

---

### 7. Macro Momentum & Surprises (5-10% of Price Variance)

**What Matters:**
- Economic data surprises
- PMI momentum
- Earnings growth expectations
- GDP nowcasts

**Features to Build:**
| Feature | Description |
|---------|-------------|
| `economic_surprise_index` | Citi or similar |
| `pmi_manufacturing` | ISM Manufacturing |
| `pmi_services` | ISM Services |
| `pmi_momentum_3m` | PMI trend |
| `nfp_surprise` | Last payrolls vs expectations |
| `cpi_surprise` | Last CPI vs expectations |
| `gdp_nowcast` | Atlanta Fed GDPNow |
| `earnings_growth_expected` | Forward S&P 500 EPS growth |
| `pe_ratio_forward` | Valuation level |
| `equity_risk_premium` | Earnings yield minus real yield |

**Data Sources:**
- FRED: MANEMP, PAYEMS, various macro series
- Atlanta Fed GDPNow (web scrape or API)

---

### 8. Microstructure & Flow Signals (From Databento Depth)

**What Matters:**
- Order flow imbalance
- Depth withdrawal (liquidity gaps)
- Large trade detection
- Momentum ignition patterns
- ES-MES basis arbitrage

**Features to Build:**
| Feature | Description |
|---------|-------------|
| `order_imbalance_1m` | Bid vs ask volume imbalance |
| `order_imbalance_5m` | 5-minute aggregated imbalance |
| `depth_imbalance_l1` | Best bid vs best ask size |
| `depth_imbalance_l5` | Top 5 levels imbalance |
| `depth_withdrawal_flag` | Sudden liquidity drop |
| `large_trade_flow` | Trades >100 contracts direction |
| `microprice` | Size-weighted mid price |
| `microprice_momentum` | Microprice trend |
| `spread_percentile` | Current spread vs typical |
| `es_mes_basis` | Premium/discount between contracts |
| `es_mes_basis_zscore` | Normalized basis for mean reversion |
| `volume_surge_flag` | Volume >2x 20-day average |
| `tick_direction_bias` | Net upticks vs downticks |

**Data Sources:**
- Databento: MES tbbo, mbp-1, mbp-10, mbo
- Databento: ES bbo-1m for basis calculation

---

## Revised MES Supporting Symbols

### Must Have (Add These)

| Symbol | Purpose | Schemas | Priority |
|--------|---------|---------|----------|
| **ZQ.FUT** | Fed Funds futures (rate expectations) | ohlcv-1d, statistics | 🔴 Critical |
| **ZT.FUT** | 2-Year Treasury (front-end rates) | ohlcv-1h/1d, statistics | 🔴 Critical |
| **ZN.FUT** | 10-Year Treasury (duration) | ohlcv-1h/1d, statistics | 🔴 Critical |
| **ZB.FUT** | 30-Year Treasury (long duration) | ohlcv-1d, statistics | 🟡 Important |
| **VX.FUT** | VIX futures (vol term structure) | ohlcv-1h/1d, statistics | ⚠️ **NOT AVAILABLE** (use FRED) |
| **ES.FUT** | E-mini S&P (flow context) | ohlcv-1m/1h/1d, bbo-1m, statistics | 🔴 Critical |

### From FRED (Already Have or Easy to Add)

| Series | Purpose | Status |
|--------|---------|--------|
| FEDFUNDS | Effective Fed Funds Rate | ✅ Have |
| DFF | Daily Fed Funds | ✅ Have |
| DGS2 | 2-Year Treasury Yield | ✅ Have |
| DGS10 | 10-Year Treasury Yield | ✅ Have |
| DGS30 | 30-Year Treasury Yield | ✅ Have |
| T10YIE | 10-Year Breakeven Inflation | ✅ Added |
| BAMLC0A0CM | IG Credit Spread | ✅ Have |
| BAMLH0A0HYM2 | HY Credit Spread | ✅ Have |
| NFCI | Financial Conditions Index | ✅ Added |
| TEDRATE | TED Spread | ✅ Have |
| WALCL | Fed Balance Sheet | ✅ Have |
| DTWEXBGS | Broad Dollar Index | ✅ Have |
| VIXCLS | Spot VIX | ✅ Have |
| VXVCLS | 3-Month VIX | ✅ Added |

---

## Updated MES Engine Pull Specification

### Prime: MES.FUT (Full Depth)

**Schemas:**
- ohlcv-1s, ohlcv-1m, ohlcv-1h, ohlcv-1d
- bbo-1s, bbo-1m
- tbbo, mbp-1, mbp-10, mbo
- statistics

**Split:** Day

### Supporting: Flow & Rates Context

| Symbol | Schemas | Split | Notes |
|--------|---------|-------|-------|
| ES.FUT | ohlcv-1m, ohlcv-1h, ohlcv-1d, bbo-1m, statistics | Month | Flow timing requires 1m |
| ZQ.FUT | ohlcv-1d, statistics | Month | Rate expectations |
| ZT.FUT | ohlcv-1h, ohlcv-1d, statistics | Month | 2Y yield proxy |
| ZN.FUT | ohlcv-1h, ohlcv-1d, statistics | Month | 10Y yield proxy |
| ZB.FUT | ohlcv-1d, statistics | Month | 30Y yield proxy |
| VX.FUT | ohlcv-1h, ohlcv-1d, statistics | Month | Vol term structure - **NOT IN SUBSCRIPTION** |

---

## MES Feature Views Structure

### View 1: features.mes_rates_daily

```sql
-- Fed policy features
fed_funds_rate
fed_funds_expected_1m  -- from ZQ front month
fed_funds_expected_3m  -- from ZQ 3rd month
fed_rate_path_slope    -- steepness of expectations curve

-- Yield features  
yield_2y               -- from ZT or FRED
yield_10y              -- from ZN or FRED
yield_30y              -- from ZB or FRED
yield_2s10s_spread
yield_2s10s_momentum_5d
yield_10y_momentum_5d
yield_10y_momentum_20d
yield_curve_regime     -- steep/flat/inverted

-- Real yields
real_yield_10y         -- 10Y minus breakeven
```

### View 2: features.mes_volatility_daily

```sql
-- VIX spot features
vix_spot
vix_percentile_1y
vix_momentum_5d
vix_regime

-- VIX term structure (from FRED - no VX futures)
vix_3m                 -- VXVCLS
vix_term_structure     -- VXVCLS / VIXCLS ratio
vix_term_slope         -- VXVCLS - VIXCLS
vix_contango_flag      -- term structure > 1.0
vix_backwardation_flag -- term structure < 1.0

-- Realized vol
realized_vol_5d
realized_vol_20d
vol_risk_premium       -- VIX minus realized
```

### View 3: features.mes_flows_daily

```sql
-- ES-MES relationship
es_mes_basis
es_mes_basis_zscore
es_mes_basis_momentum_5d

-- Volume and positioning
es_open_interest
es_oi_change_1d
es_volume_ratio        -- vs 20-day avg
mes_volume_ratio

-- Microstructure (aggregated from intraday)
daily_order_imbalance
daily_depth_imbalance
large_trade_net_flow
```

### View 4: features.mes_credit_daily

```sql
-- Credit spreads
ig_spread
hy_spread
credit_spread_momentum_5d
hy_ig_ratio

-- Financial conditions
nfci
nfci_momentum_5d
ted_spread
```

### View 5: features.mes_macro_daily

```sql
-- Dollar
dxy_level
dxy_momentum_5d
dxy_momentum_20d

-- Economic momentum
gdp_nowcast
pmi_manufacturing
pmi_momentum_3m

-- Valuation context
forward_pe
equity_risk_premium
```

### Master View: features.mes_training_v1

Joins all above views on date, adds:
- Target variables (1d, 7d, 30d returns)
- Regime classifications
- Training weights

---

## BigQuery Tables (MES Engine Updated)

### Prime Tables (11)

```sql
market_data.mes_ohlcv_1s
market_data.mes_ohlcv_1m
market_data.mes_ohlcv_1h
market_data.mes_ohlcv_1d
market_data.mes_bbo_1s
market_data.mes_bbo_1m
market_data.mes_tbbo
market_data.mes_mbp_1
market_data.mes_mbp_10
market_data.mes_mbo
market_data.mes_statistics
```

### Context Tables (5)

```sql
market_data.mes_context_ohlcv_1m   -- ES only
market_data.mes_context_ohlcv_1h   -- ES, ZT, ZN
market_data.mes_context_ohlcv_1d   -- ES, ZT, ZN, ZB, ZQ (all)
market_data.mes_context_statistics -- All supporting symbols
market_data.mes_rates_curve        -- Derived: 2Y, 10Y, 30Y, spreads
```

### Feature Tables (5)

```sql
features.mes_rates_daily
features.mes_volatility_daily
features.mes_flows_daily
features.mes_credit_daily
features.mes_macro_daily
features.mes_training_v1           -- Master training view
```

---

## Implementation Steps for Cursor

### Phase 1: Add Missing FRED Series

**Step 1:** Pull these FRED series into warehouse if not already present:
- DGS2, DGS10, DGS30, T10YIE
- BAMLC0A0CM, BAMLH0A0HYM2
- NFCI, TEDRATE, WALCL

### Phase 2: Update Databento Pull

**Step 2:** Add ZQ.FUT and ZT.FUT to MES engine pull script

**Step 3:** Verify all 5 supporting symbols included: ES, ZQ, ZT, ZN, ZB
- ⚠️ VX.FUT not available in GLBX.MDP3 subscription

### Phase 3: Build Feature Views

**Step 4:** Create `features.mes_rates_daily` with yield curve features

**Step 5:** Create `features.mes_volatility_daily` with VIX term structure (from FRED)

**Step 6:** Create `features.mes_flows_daily` with ES-MES basis

**Step 7:** Create `features.mes_credit_daily` with spread features

**Step 8:** Create `features.mes_macro_daily` with dollar and economic features

**Step 9:** Create master `features.mes_training_v1` joining all feature views

### Phase 4: Validation

**Step 10:** Verify yield curve inversion correctly flags recession periods

**Step 11:** Verify VIX term structure shows backwardation during 2020, 2022 stress

**Step 12:** Verify ES-MES basis is typically -2 to +1 points

**Step 13:** Backtest feature importance on historical MES returns

---

## Summary

**MES is driven by:**
1. **Fed Policy** - Rate level, expectations, balance sheet
2. **Yields** - Curve shape, real yields, rate volatility
3. **Volatility** - VIX level, term structure, realized vs implied
4. **Dollar** - DXY level and momentum
5. **Credit** - IG/HY spreads, financial conditions
6. **Flows** - ES positioning, volume, microstructure

**NOT driven by:**
- ❌ Weather (that's ZL)
- ❌ Crush spreads (that's ZL)
- ❌ China soybean imports (that's ZL)
- ❌ Biodiesel mandates (that's ZL)

**The engines stay completely separate. No cross-contamination.**

---

## Feature Count Summary

| Category | Feature Count | Priority |
|----------|---------------|----------|
| Fed Policy | 9 | 🔴 Critical |
| Treasury/Yields | 12 | 🔴 Critical |
| Volatility | 13 | 🔴 Critical |
| Dollar/FX | 9 | 🟡 High |
| Credit | 7 | 🟡 High |
| Equity Flows | 10 | 🟡 High |
| Macro Surprises | 10 | 🟢 Medium |
| Microstructure | 13 | 🟢 Medium |
| **TOTAL** | **~83** | |

---

**Status:** ✅ **COMPREHENSIVE MES FEATURE SPECIFICATION COMPLETE**

**Next:** After ZL engine stable, implement this specification for MES.

