---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# 📋 PAGE BUILDOUT ROADMAP

**Date**: November 19, 2025 (CORRECTED)  
**Status**: Active Planning  
**Architecture**: 5 PAGES TOTAL - FINAL

**Related Plan**: This roadmap is linked to the main execution plan at `docs/execution/25year-data-enrichment/architecture-lock.plan.md`

---

## 🎯 FINAL ARCHITECTURE - 5 PAGES

### 1. Dashboard – Chris's Daily Money Screen
**Status**: ✅ Complete (needs SHAP overlay upgrade)  
**User**: Chris (Procurement Manager)  
**Purpose**: Daily decisions - the only screen Chris opens every morning

**Current Features**:
- ✅ Main ZL prediction center
- ✅ All time horizons (1w, 1m, 3m, 6m, 12m)
- ✅ VIX overlay for risk assessment
- ✅ SHAP values explaining predictions
- ✅ Current price and targets
- ✅ Confidence levels

**Required Upgrades**:
- 🚧 **SHAP Overlays on All Charts**: Live, animated SHAP force lines on every horizon chart
  - Top 4 drivers (RINs, Tariff, Weather, Crush) as glowing force lines
  - Right Y-axis scaled -2 to +2 (SHAP impact in cents/lb)
  - Floating legend: "Today's Top Drivers → +18.4¢ total lift"
  - Bold + pulsing glow when driver is #1 contributor
- 🚧 **Full-width 1-month chart** with:
  - Thick white line = actual ZL price (Databento)
  - Glowing orange line = 1-month predicted path
  - Shaded probability cone (68% & 95% from Monte Carlo)
  - Vertical walk-forward lines (past predictions vs actual)
  - Floating badges: RINs change, Tariff risk, Drought Z, Crush margin
- 🚧 **4 smaller horizon charts** (1w, 3m, 6m, 12m) - same style, stacked
- 🚧 **Top-right**: Giant procurement traffic light + one-line briefing ("BUY 40% Q2 – RINs +180% driving +9.3% in 90d")
- 🚧 **Bottom**: Live SHAP beeswarm + "If you locked today: +$2.47M alpha YTD"

**Data Sources**:
- `predictions.vw_zl_latest` (all horizons)
- `market_data.databento_futures_ohlcv_1d` (ZL continuous)
- `models_v4.shap_daily` (top 10 drivers)
- `raw_intelligence.sentiment_daily` (procurement_sentiment_index)

**Tech Stack**: Next.js 15 + Recharts only (NO TradingView), Dark mode, Loads <500ms

---

### 2. Sentiment – Market Mood (9-Layer Engine)
**Status**: ✅ Complete  
**User**: Chris  
**Purpose**: Market mood analysis using 9-layer sentiment architecture

**Features** (Already Implemented):
- ✅ 9-layer sentiment system (Core ZL, Biofuel, Tariffs, Weather, Palm, Energy, Macro, ICE, COT)
- ✅ Procurement Sentiment Index (traffic light driver)
- ✅ Pinball triggers (tariff, RIN moon, drought, Trump storm, spec blowoff)
- ✅ See `docs/reference/SENTIMENT_ARCHITECTURE_REFERENCE.md` for full details

**Note**: This page is production-ready. No changes needed.

---

### 3. Strategy – Chris's What-If Playground
**Status**: ✅ Complete (needs SHAP overlay upgrade)  
**User**: Chris  
**Purpose**: Business intelligence / what-if war room

**Current Features**:
- ✅ Scenario planning for procurement
- ✅ What-if scenarios
- ✅ If/then decision trees
- ✅ Timing optimization

**Required Upgrades**:
- 🚧 **6 Scenario Cards** (NOT sliders - cards with click-to-adjust):
  - **Volatility Card**: VIX ± 1–2σ (widens/narrows quantile bands)
  - **Biofuel Demand Card**: EIA biodiesel + RIN D4 Δ% (biofuels driver weight)
  - **FX Card**: BRL ±X%, CNY ±X% (export competitiveness)
  - **Trade Card**: China weekly export sales shock (percentile toggle)
  - **Weather Card**: ONI phase toggle (El Niño/La Niña) + Brazil/Argentina regional moisture/temperature tilts
  - **Substitutes Card**: Palm oil +/−10% (elasticity link applied to ZL baseline)
- 🚧 **On any card adjustment** → instant 5,000-path Monte Carlo re-run across all horizons
- 🚧 **Recharts redraws every cone in real time** with SHAP overlays
- 🚧 **SHAP Overlays on What-If Charts**:
  - Same 4-driver SHAP force lines (right Y-axis)
  - Color intensity = absolute SHAP impact
  - Floating box: "Under this scenario: Tariff shock becomes #1 driver (+24.1¢)"
  - Toggle button: "Show SHAP Forces" (on by default)
- 🚧 **Shows optimal procurement volume % and exact $ outcome** vs doing nothing
- 🚧 **"Save Scenario" + "Replay Feb 2025 Collapse"** buttons
- 🚧 **Partial derivatives table**: "1% RIN hike = +0.47¢ ZL in 3M"
- 🚧 **Walk-forward validation**: Actual vs simulated for past 12 events
- 🚧 **"Chris's Alpha Tracker"**: Cumulative $ saved if followed model (+$2.47M since Jan)

**Data Sources**:
- `raw_intelligence.sentiment_daily` (Big 4 layers)
- `predictions.vw_zl_latest` (Monte Carlo paths)
- `models_v4.shap_daily` (for SHAP recomputation)

---

### 4. Trade Intelligence – Geopolitical Nuke Room
**Status**: 🚧 Needs Rebuild (formerly "Legislative")  
**User**: Chris  
**Purpose**: Geopolitical risk - "how the fuck did you know that" page

**Focus**: Trump, EPA, Argentina, China, Venezuela, lobbying, tariffs, hidden connections

**Required Features**:
- 🚧 **Top gauge**: Current Geopolitical Risk (-1.5 to +1.5)
- 🚧 **Force-directed graph** (D3/Recharts):
  - Nodes = Trump, Milei, Xi, Maduro, EPA, ASA lobbyists
  - Edges = real correlations (e.g., Venezuela debt payments → Argentina soy reroute → US crush -11%)
- 🚧 **"Latest Hidden Driver" card**: Neural net finds non-obvious links from `news_articles`
  - Example: "Milei advisor lobbied ASA for $20B bailout → +0.18 ZL correlation"
- 🚧 **Real-time news feed** ranked by predicted ZL impact
- 🚧 **Timeline of every tariff/biofuel event** with exact 30-day ZL move
- 🚧 **SHAP Overlays on Geopolitical Timeline Chart**:
  - Full-width historical chart (past 24 months ZL price)
  - Every major event as vertical colored bar
  - SHAP force overlay for 30-day period AFTER each event
  - 4 glowing lines showing which driver dominated the move
  - Hover tooltip: "Trump tariff threat → +38.2¢ ZL lift (86% of total move)"
- 🚧 **Correlation matrix heatmap**: Big 4 + Venezuela Debt (0.12), Argentina Tax Drop (-0.15)
- 🚧 **"Mind-Blown Score"**: Neural surprise metric (0-10 non-obviousness)

**Data Sources**:
- `raw_intelligence.news_articles` (latest biofuel/EPA/Argentina/China/Venezuela)
- `policy_trump_signals` (tariff scores)
- `features.master_features` (neural embeddings for dot-connecting)

**Goal**: Make Chris whisper "holy shit" every single visit

---

### 5. Vegas Intel – Kevin-Only Upsell Machine
**Status**: ✅ Complete  
**User**: Kevin (Sales) - **100% SEPARATE, NO MES**  
**Purpose**: Restaurant upsell weapon via Glide connection

**Features**:
- ✅ Sales intelligence for restaurant upsells
- ✅ Glide app integration (casino traffic + events)
- ✅ Casino event calendar
- ✅ Volume multipliers
- ✅ Upsell opportunities

**Layout**:
- Top counter: "Upsell Opportunities Today: 52 · Potential +$1.41M"
- Interactive Vegas map: every restaurant = dot
  - Size = today's volume multiplier
  - Color = ZL forecast (green = price dropping = margin expanding)
- Click any dot → modal:
  - "MGM Grand Buffet – Volume 3.1x today (Convention) – ZL forecast -21% in 6mo → +46% margin if switch to soy blend → $94K opportunity"
  - "Send Proposal" button (pre-filled email/SMS)
- Bottom: Kevin's running commission total + "Call Script of the Day"

**Data Sources**:
- Glide casino traffic API (volume multipliers)
- `predictions.vw_zl_latest` (ZL forecast)
- Internal restaurant accounts

**Note**: **ZERO MES. ZERO OVERLAP.** This is 100% separate from MES trading.

---

### 6. MES Trading (Hidden Page - Kirk Only)
**Status**: 🚧 Hidden/Internal  
**User**: Kirk (Developer) - **NOT part of main dashboard**  
**Purpose**: Personal MES trading cockpit with 4 hypertuned gauges

**Note**: This is a separate, hidden page for Kirk's personal MES trading. NOT part of the 5 main pages. NOT connected to Vegas Intel.

**Gauge Architecture**: 4 massive top gauges (-1.0 to +1.0) using production-tested models verified against 2025 live trading P&L

**The 4 Gauges:**
1. **5-Minute Execution Gauge** - Regime-Switched LightGBM + Orderflow Delta (Sharpe 3.8)
2. **15-Minute Swing Gauge** - CatBoost + Higher-Timeframe Alignment (Sharpe 4.1)
3. **1-Hour Macro Gauge** - Bayesian Structural Time Series + Macro Regressors (Sharpe 2.9)
4. **4-Hour Institutional Bias Gauge** - Temporal Fusion Transformer (Sharpe 3.4)

**Execute Button Logic:**
```
execute = (5min > +0.65) AND (15min > +0.60) AND (1hour > +0.30) AND (4hour > +0.20)
```

**Live Performance (2025 YTD):**
- Hit rate: 74.3%
- Average winner: +0.91%
- Average loser: -0.34%
- Profit factor: 4.8

**Complete Layout:**
- **Top Row:** 4 massive gauges (-1.0 to +1.0) - see gauge math below
- **Live Ticker Bar:** Pinned top - price, imbalance, momentum Z, VIX/DXY/10Y
- **Main Chart (60% height):** 5-min candles + 15-min overlay with:
  - Auto Fibonacci pullbacks (0.236-0.786) + extensions (1.272-2.618) with live tap probabilities (Toggleable, Default: OFF)
  - Daily/weekly/monthly/quarterly pivots + R1/R2/S1/S2
  - Gamma flip levels + dealer walls
  - Volume delta histogram + cumulative delta
  - News vertical lines (FOMC, CPI, Trump) with reaction cones
  - 60-min probability cone (68%/95%)
  - SHAP force lines (VIX, Yield, Trump, COT) on right Y-axis
- **Context Row:** 4 mini-charts (1H/4H/8H/24H) with EMA ribbon, fib grid, cycles, gamma, SHAP
- **Macro Row:** 5 charts (7D/30D/3M/6M/12M) with pivots, fibs, cyclicals, Kalman trend
- **Right Rail:** Live Fibonacci target table with probabilities + gamma wall odds
- **Bottom-Right:** Calculus panel (velocity, acceleration, jerk, divergence) + entry checklist → pulsing EXECUTE button

**See:** `docs/reference/MES_GAUGE_MATH.md` for complete gauge formulas, model specifications, layout details, and implementation

---

## 📊 PAGE PRIORITY MATRIX

| Page | Status | Priority | User | Purpose |
|------|--------|----------|------|---------|
| Dashboard | ✅ Complete | P0 | Chris | Daily decisions - morning screen |
| Sentiment | ✅ Complete | P0 | Chris | Market mood (9-layer engine) |
| Strategy | ✅ Complete | P1 | Chris | What-if war room |
| Trade Intelligence | 🚧 Rebuild | P1 | Chris | Geopolitical risk |
| Vegas Intel | ✅ Complete | P1 | Kevin | Restaurant upsells (NO MES) |
| MES Trading | 🚧 Hidden | Internal | Kirk | Personal trading (separate) |

---

## 🚧 PLANNED UPGRADES

### SHAP Overlays (Required for Dashboard + Strategy + Trade Intelligence)

**Component**: `components/ShapOverlay.tsx` (reusable)

**Implementation**:
- Add second Y-axis (right side) scaled -2 to +2 (SHAP impact in cents/lb)
- Overlay 4 glowing force lines (top 4 drivers from `models_v4.shap_daily`):
  1. RINs momentum (orange)
  2. Geopolitical tariff score (red when negative)
  3. South America weather anomaly (blue)
  4. Crush margin proxy (green)
- Each line: `strokeWidth 3`, `dot={false}`, `animationDuration 800ms`
- Tooltip on hover: "RINs +180% → +11.2¢ contribution to 1mo forecast"
- Floating legend box: "Today's Top Drivers → +18.4¢ total lift"
- When driver is #1 contributor → bold + pulsing glow

**Data Source**: `cbi-v14.models_v4.shap_daily` (date, horizon, feature_name, shap_value_cents)

**Pages Requiring SHAP Overlays**:
1. **Dashboard**: All 5 charts (1M main + 4 horizon minis)
2. **Strategy**: All Monte Carlo cone charts (update on card adjustment)
3. **Trade Intelligence**: Historical timeline chart (30-day SHAP after each event)

---

## 📝 CURSOR PROMPTS FOR BUILDING

### Dashboard Prompt
```markdown
Build the ULTIMATE Dashboard page for CBI-V14 – the procurement quant war room.

Page: app/dashboard/page.tsx (Next.js 15 + Tailwind + Recharts)

Live BQ sources:
- predictions.vw_zl_latest (horizon, pred_price, lower_68, upper_68, confidence)
- models_v4.shap_daily (top 10 drivers for 6m forecast)
- market_data.databento_futures_ohlcv_1d (ZL continuous)
- raw_intelligence.sentiment_daily (procurement_index for traffic light)

Layout:
- Hero: 5 prediction cards (1w-12m) with bold price, % move, confidence halo, mini SHAP waterfall
- Main: Full-width Recharts AreaChart (ZL price + VIX overlay + 1M Monte Carlo fan with probability density)
- Right: "Chris's Briefing" auto-text (e.g., "ZL +9.3% in 90d. RINs +180% driver. Procure 40% Q2.")
- Bottom: Big 4 heatmap (RINs/Tariffs/Weather/Crush corr matrix) + live P&L tracker

SHAP Overlays: Add ShapOverlay component to all 5 charts with top 4 drivers as glowing force lines.

Load <500ms. Dark mode. Quant as fuck.
```

### Strategy Prompt
```markdown
Build the Strategy page – Chris adjusts scenario cards, the future obeys.

Page: app/strategy/page.tsx

6 scenario cards (NOT sliders - interactive cards with click-to-adjust):
- Volatility Card: VIX ± 1–2σ (widens/narrows quantile bands)
- Biofuel Demand Card: EIA biodiesel + RIN D4 Δ% (biofuels driver weight)
- FX Card: BRL ±X%, CNY ±X% (export competitiveness)
- Trade Card: China weekly export sales shock (percentile toggle)
- Weather Card: ONI phase toggle (El Niño/La Niña) + Brazil/Argentina regional moisture/temperature tilts
- Substitutes Card: Palm oil +/−10% (elasticity link applied to ZL baseline)

On any card adjustment → instant 5,000-path Monte Carlo re-run across all horizons
→ Recharts redraws every cone in real time with SHAP overlays
→ Shows optimal procurement volume % and exact $ outcome vs doing nothing

SHAP Overlays: Update ShapOverlay component when cards adjust. Show which driver becomes #1 under new scenario.

Add "Save Scenario" + "Replay Feb 2025 Collapse" button
Partial derivatives table: "1% RIN hike = +0.47¢ ZL in 3M"
Walk-forward validation: Actual vs simulated for past 12 events
"Chris's Alpha Tracker": +$2.47M saved since Jan

This is where Chris stress-tests million-dollar procurement decisions.
```

### Trade Intelligence Prompt
```markdown
Build Trade Intelligence page – this is the "how the fuck did you know that" page.

Page: app/trade-intelligence/page.tsx

Focus: Trump, EPA, Argentina, China, Venezuela, lobbying, tariffs, hidden connections.

Features:
- Top gauge: Current Geopolitical Risk (-1.5 to +1.5)
- Force-directed graph (D3/Recharts): nodes = Trump, Milei, Xi, Maduro, EPA, ASA lobbyists
  - Edges = real correlations (e.g., Venezuela debt payments → Argentina soy reroute → US crush -11%)
- "Latest Hidden Driver" card: neural net finds non-obvious links from news_articles
  - Example: "Milei advisor lobbied ASA for $20B bailout → +0.18 ZL correlation"
- Real-time news feed ranked by predicted ZL impact (from `zl_impact_predictor.py` output)
- Timeline of every tariff/biofuel event with exact 30-day ZL move

SHAP Overlays: Full-width historical chart (past 24 months) with SHAP force overlay for 30-day period AFTER each event.
Hover tooltip: "Trump tariff threat → +38.2¢ ZL lift (86% of total move)"

Correlation matrix heatmap: Big 4 + Venezuela Debt (0.12), Argentina Tax Drop (-0.15)
"Mind-Blown Score": Neural surprise metric (0-10 non-obviousness)

Make Chris whisper "holy shit" every single visit.
```

### Vegas Intel Prompt
```markdown
Build Vegas Intel – Kevin-only page. Zero MES. Zero overlap.

Page: app/vegas-intel/page.tsx (middleware: only kevin@ email)

Sources:
- **Glide API** (live data on restaurants in Vegas):
  - Restaurants they serve
  - Amount of oil delivered to restaurants
  - Fryer capacities
  - Volume multipliers (casino traffic + events)
- `predictions.vw_zl_latest` (ZL forecast - NOT zl_impact, which is for Trump actions)
- Internal restaurant accounts

**CRITICAL**: Use `predictions.vw_zl_latest` for ZL price forecasts. Do NOT use `zl_impact_predictor.py` output here - that's specifically for Trump action impacts on Trade Intelligence page.

Layout:
- Top counter: "Upsell Opportunities Today: 52 · Potential +$1.41M"
- Interactive Vegas map: every restaurant = dot
  - Size = today's volume multiplier
  - Color = ZL forecast (green = price dropping = margin expanding)
- Click any dot → modal:
  "MGM Grand Buffet – Volume 3.1x today (Convention) – ZL forecast -21% in 6mo → +46% margin if switch to soy blend → $94K opportunity"
  + "Send Proposal" button (pre-filled email/SMS)
- Bottom: Kevin's running commission total + "Call Script of the Day"

This page prints money and bonus checks.
```

### MES Trading Prompt
```markdown
Build my FINAL MES live trading cockpit with 4 massive top gauges using hypertuned models verified against 2025 live trading P&L.

Page: app/mes/page.tsx (Next.js 15 + Recharts + react-gauge-chart)
**Fibonacci levels must be toggleable via a checkbox (default off).**

PINNED TOP ROW – 4 massive gauges (-1.0 to +1.0):

GAUGE 1: 5-MIN EXECUTION (largest)
- Model: Regime-Switched LightGBM + Orderflow Delta
- Formula: 0.60 × LGBM_regime + 0.25 × volume_delta_jerk + 0.15 × fib_gamma_confluence
- Edge: Sharpe 3.8 (live 2024-2025)

GAUGE 2: 15-MIN SWING (primary trigger)
- Model: CatBoost + Higher-Timeframe Alignment Filter
- Formula: 0.75 × CatBoost + 0.25 × 1H_alignment_bonus
- Edge: Sharpe 4.1 (highest of all)

GAUGE 3: 1-HOUR MACRO
- Model: Bayesian Structural Time Series (BSTS) + Macro Regressors
- Formula: 0.80 × BSTS_posterior + 0.20 × VIX_regime_penalty
- Edge: Sharpe 2.9

GAUGE 4: 4-HOUR INSTITUTIONAL BIAS
- Model: Temporal Fusion Transformer (TFT)
- Formula: 1.00 × TFT_75th_quantile
- Edge: Sharpe 3.4

EXECUTE BUTTON: Only fires when (5min > +0.65) AND (15min > +0.60) AND (1hour > +0.30) AND (4hour > +0.20)

Live hit rate 2025 YTD: 74.3% with profit factor 4.8

Data Sources:
- market_data.databento_futures_ohlcv_1m (MES 1-minute bars)
- market_data.databento_futures_ohlcv_5m (MES 5-minute bars)
- market_data.databento_futures_ohlcv_15m (MES 15-minute bars)
- market_data.databento_futures_ohlcv_1h (MES 1-hour bars)
- market_data.databento_futures_ohlcv_4h (MES 4-hour bars)
- options.gamma_exposure (gamma walls)
- raw_intelligence.sentiment_daily (VIX regime, Trump sentiment)
- features.master_features (COT data, yield curve)

API Route: app/api/gauges/live/route.ts (runs every 60 seconds)

This is the math that survived 2025. Nothing else comes close.
```

---

## 📝 NOTES

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

### Architecture Rules
- **5 PAGES TOTAL** - No more, no less
- **MES is separate** - Hidden page for Kirk only, NOT part of main dashboard
- **Vegas Intel is 100% separate** - NO MES, NO overlap with trading
- **Trade Intelligence** (not "Legislative") - Focus on geopolitical risk
- **NO status report headers** - Remove any "What We're Doing" boilerplate
- **SHAP overlays required** on Dashboard, Strategy, and Trade Intelligence charts

### Data Sources
- All sentiment data from `raw_intelligence.sentiment_daily` (9-layer engine)
- SHAP data from `models_v4.shap_daily`
- Predictions from `predictions.vw_zl_latest`
- Market data from `market_data.databento_futures_ohlcv_1d`

### Tech Stack
- Next.js 15 + Tailwind + Recharts (NO TradingView)
- Dark mode by default
- Load times <500ms
- Real-time updates every 5-15 minutes

---

**Related Plans & References**:
- `docs/plans/MASTER_PLAN.md` – Main execution plan and architecture
- `docs/reference/MES_GAUGE_MATH.md` – MES trading cockpit specifications
- `docs/reference/MES_MATH_ARCHITECTURE.md` – MES math architecture (Fibonacci, Monte-Carlo, Gamma, SHAP)
- `docs/reference/STRATEGY_SCENARIO_CARDS.md` – Strategy page scenario cards
- `docs/reference/FIBONACCI_MATH.md` – Fibonacci calculations
- `docs/reference/PIVOT_POINT_MATH.md` – Pivot point calculations
- `docs/reference/SENTIMENT_ARCHITECTURE_REFERENCE.md` – Sentiment architecture

**Last Updated**: November 19, 2025 (CORRECTED)  
**Next Review**: After SHAP overlay implementation
