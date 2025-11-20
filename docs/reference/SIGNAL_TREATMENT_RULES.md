---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Signal Treatment Rules: The 12 Institutional Guidelines

**Date**: November 14, 2025  
**Purpose**: Prevent amateur signal interpretation errors  
**Audience**: AI assistants, junior quants, model developers

---

## Overview

Most forecasting systems fail because they treat signals as numbers on charts instead of **mechanisms with context**. These 12 rules define how professional quant desks interpret market signals.

**Core Principle**: Every signal must be **paired**, **validated**, and **contextualized**. Never trust a signal in isolation.

---

## Rule 1: U.S. Treasury Yield Curve

### What to Watch

| Metric | Calculation | Significance |
|--------|-------------|--------------|
| 10Y-2Y Spread | 10Y yield - 2Y yield | Yield curve slope / recession risk |
| 10Y Absolute | Current 10Y yield | Borrowing costs / dollar strength |
| 2Y Yield | Current 2Y yield | Rate expectations (Fed path) |
| 5Y-5Y Inflation | 5Y forward - 5Y spot | Long-term inflation expectations |

### Good (Bullish Soy)

✅ **Curve steepening** (2Y drops faster than 10Y)
- Means: Fed easing → Dollar weakens → Commodities strengthen
- Mechanism: Lower rates → EM buying power ↑ → Demand ↑

✅ **10Y yields falling**
- Means: Cheaper financing → Weak dollar → Export commodities supported
- Mechanism: Lower cost of carry → Inventory builds → Spot tightness

### Bad (Bearish Soy)

❌ **Curve inversion worsening**
- Means: Recession risk → Demand destruction → Bearish oils
- Mechanism: Industrial slowdown → Biodiesel demand ↓

❌ **10Y spikes quickly**
- Means: Strong dollar → Higher global borrowing → EM crush pain
- Mechanism: Dollar strength → Brazil dumps → Supply glut

### Measurement Rules

**Never use raw levels without context**. Always compute:

```python
# Weekly delta
yield_delta = current_10y - prior_week_10y

# 30-day z-score (regime-relative)
yield_zscore = (current_10y - mean_30d) / std_30d

# Correlation with USD
correlation(yield_delta, usd_delta, window=30)
```

**Critical Pair**: Always check yields **WITH** USD context. 10Y up + USD flat = different signal than 10Y up + USD surging.

---

## Rule 2: VIX (Fear Gauge)

### The Error Most Systems Make

❌ "VIX rising = bearish soy"  
✅ **VIX rising can be bullish, bearish, or noise** - depends on regime

### Good (Sometimes Bullish)

✅ **Moderate VIX rise** (15 → 25)
- Regime: "Risk-aware but not panic"
- Mechanism: Funds rotate OUT of equities INTO commodities as hedges
- Conviction: High (clear rotation signal)

### Bad (Unambiguously Bearish)

❌ **VIX > 30**
- Regime: "Crisis mode"
- Mechanism:
  - Liquidity drains
  - Commodity futures spreads widen
  - Hedgers pull orders
  - Price gaps become erratic
- Conviction: High (risk-off)
- **Confidence: Very Low** (MAPE spikes 3-5x)

### Regime Bands (Mandatory)

| VIX Range | Regime | Treatment | MAPE Impact |
|-----------|--------|-----------|-------------|
| <15 | Complacent | Weak signals, tight bands | 0.7-1.0% |
| 15-25 | Risk-Aware | Moderate signals, normal variance | 1.0-1.8% |
| 25-30 | Stress | Strong signals, wider bands | 2.0-3.5% |
| >30 | Crisis | Very strong direction, chaotic magnitude | 4.0-6.0% |

### Critical Rule

**VIX is a CONVICTION signal (direction), NOT a CONFIDENCE signal (precision).**

```python
# CORRECT
if vix > 25:
    conviction += 30  # High conviction about direction
    confidence_width *= 2.5  # Low confidence about magnitude

# WRONG
if vix > 25:
    forecast_confidence = 0.9  # WRONG! False precision
```

---

## Rule 3: Sentiment (News, Social, USDA)

### The Overfit Trap

Sentiment is the **easiest to overfit** and **easiest to hallucinate**. It must ALWAYS be paired with mechanism.

### Good (High Signal)

✅ **Stable, slow-moving trend** (20-40% weekly change)
- Example: "Argentina drought worsening" held for 3+ weeks
- Mechanism: Weather → production → supply → price

✅ **High signal when tied to mechanism**
- Example: "Brazil drought worsening" = weather signal, not sentiment
- Validation: Pair with GDD, soil moisture, NDVI

### Bad (Noise)

❌ **Single headline spikes**
- AI assistants overreact to one headline
- Must wait for confirmation (2-3 day persistence)

❌ **China rhetoric without action**
- Only matters if tied to:
  - Import quotas ✅
  - Reserve releases ✅
  - Port congestion ✅
  - Diplomatic actions ✅
- Verbal posturing = noise ❌

### Mandatory Pairing Rule

**Sentiment MUST be paired with**:

1. **Fundamental validation**: Check actual data (imports, weather, logistics)
2. **Supply/demand variable**: Is there a mechanism?
3. **Logistics constraint**: Can it physically happen?
4. **Price reaction**: Did related markets move?

```python
# CORRECT
if sentiment_spike and (weather_anomaly or import_surge or freight_spike):
    weight_signal_high()
else:
    down_weight_sentiment()

# WRONG
if sentiment_positive:
    bullish_forecast()  # WRONG! No mechanism check
```

---

## Rule 4: Fed Funds / Interest Rates

### The Regime Principle

**Rates are regimes, not numbers.** The path matters more than the level.

### Good (Bullish Soy)

✅ **Fed cutting or signaling cuts**
- Mechanism:
  - USD weakens
  - BRL/ARS strengthen
  - South American farmers sell LESS aggressively
  - Prices rise

✅ **Fed pause after aggressive hikes**
- Market signal: "Long commodities, short USD" becomes consensus

### Bad (Bearish Soy)

❌ **Rapid rate hikes**
- Mechanism:
  - USD soars
  - Importers reduce buying (China, India)
  - China delays shipments
  - Risk parity funds unwind commodity longs

### Measurement Rules

Track **rate path**, not just the number:

```python
# 1. Dot plot shifts (Fed projections)
fed_path_delta = current_dot_plot - prior_meeting

# 2. Futures-implied cuts/hikes
implied_cuts = fed_funds_futures_curve - current_rate

# 3. Correlate with FX
correlation(rate_changes, [USD_CNY, USD_BRL, USD_ARS])

# 4. Calculate commodity beta
soy_rate_beta = regression(soy_returns ~ fed_rate_changes)
```

**Current Beta**: ~0.35 (soybean oil moves 0.35% for every 1% Fed move)

---

## Rule 5: USD (The Commodity Terminator)

### The Iron Law

**Soybean oil is dollar-denominated. Dollar strong → prices weak. Always.**

### Good (Bullish Soy)

✅ **USD falling vs BRL**
- Mechanism: Brazil exporters hesitate → Less global supply → Soy oil spikes

✅ **USD stable-to-soft vs EM currencies**
- Mechanism: China buys more → Biodiesel mandates tighten → Crush margins rise

### Bad (Bearish Soy)

❌ **USD ripping higher**
- Mechanism:
  - Importer pain (China, India can't afford)
  - Brazil dumps supply (needs USD revenue)
  - Argentina accelerates exports (currency crisis)
  - Margin calls in EM crush plants

### Measurement Priority

**Watch these in order**:

1. **USD/BRL** (most important - Brazil is 40% of exports)
2. **USD/ARS** (second - Argentina is 35% of exports)
3. **DXY 30-day z-score** (overall strength)
4. **USD/CNY** (demand side, less predictive)

**Pair with**:
- CFTC managed money flows
- Crush spread dynamics
- Palm oil substitution signals

---

## Rule 6: Biofuel Policy

### The Critical Reframe

**Policy is NOT text. Policy is VOLUME.**

Systems treat this as "policy text." Wrong. This is **supply/demand shock disguised as regulation**.

### Good (Bullish Soy)

✅ **Indonesia B35 → B40**
- Convert to volume: +X million MT soy oil demand/year
- Mechanism: Domestic mandates → Import demand ↑ → Global tightness

✅ **U.S. 45Z + SAF incentives**
- Convert to volume: Renewable diesel capacity additions
- Track: RD margins, LCFS credit prices

### Bad (Bearish Soy)

❌ **EU biodiesel pushback**
- Mechanism: Blend cuts → Demand destruction → Oversupply

❌ **Weak LCFS prices**
- Signal: California market soft → U.S. biodiesel margins compress

### Measurement Rules

**Convert policy → MT-equivalent demand**:

```python
# Example: Indonesia B40 mandate
biodiesel_volume_increase = (
    indonesia_diesel_consumption * 
    (0.40 - 0.35) *  # B40 - B35
    biodiesel_to_soyoil_ratio
)

# Track mechanism:
- Soybean crush margin
- Renewable diesel margins  
- Crude oil volatility
- LCFS credit curve
```

**Never treat policy as text. Always convert to tons.**

---

## Rule 7: Logistics & Freight

### The Noise Filter

Most freight data is noise. Except these:

### Good (Bullish Soy)

✅ **Real bottlenecks**:
- Panama Canal drought (ships can't pass)
- Mississippi River low levels (barges can't load)
- Santos/Paranaguá congestion (port queues >14 days)
- Argentina port strikes (force majeure)
- Suez disruptions (rerouting adds weeks)

### Bad (Bearish Soy)

❌ **Capacity improvements**:
- BR-163 highway improvements
- Northern Arc rail expansions
- India cutting import duties

### Measurement Rules

**Convert logistics to quantifiable impact**:

```python
# 1. Delay time (days)
avg_port_queue_days = vessel_waiting_time.mean()

# 2. Basis spread impact (USD/MT)
basis_spread = spot_price - futures_price

# 3. Substitution effect
if delay > 14_days:
    palm_oil_substitution_premium = calculate_arb()
```

**Map basis impact → ZL futures via substitution ratio.**

---

## Rule 8: Weather (Brazil, Argentina, U.S.)

### The Physics Rule

**Weather is physics, not sentiment.** Treat it as quantifiable physical constraints.

### Good (Bullish Soy)

✅ **Severe drought in Brazil** (±2σ rainfall deficit)
✅ **Excessive rain in Argentina** (flooding during planting)
✅ **U.S. Midwest planting delays** (>7 days behind 5-year avg)
✅ **Global anomaly detection** (±2σ temperature, GDD deficit)

### Bad (Bearish Soy)

❌ **Strong rainfall recovery** (drought broken)
❌ **Above-trend temps during pod fill** (accelerated maturity)
❌ **Improved soil moisture** (NDVI recovery confirmed)

### Measurement Rules (STRICT)

**Never use single-day anomalies**. Always:

```python
# 1. 7-day rolling composites
rainfall_7d = rolling(rainfall, 7).mean()

# 2. Drought severity index
drought_index = (precip - normal) / std_dev

# 3. Production deviation
yield_impact = (actual_GDD - required_GDD) * sensitivity

# 4. GDD accumulation
cumulative_GDD = sum(max(0, (Tmax + Tmin)/2 - base_temp))
```

**Cross-validate**: NOAA + USDA + NASA NDVI + Local Ag Ministry

---

## Rule 9: CFTC Flows (Managed Money)

### The Canary in the Coal Mine

Positioning data is **forward-looking sentiment with skin in the game**.

### Good (Bullish Soy)

✅ **Commercials buying** (hedgers covering shorts)
✅ **Managed money reducing shorts** (spec capitulation)
✅ **Net-long + open interest rising** (conviction build)

### Bad (Bearish Soy)

❌ **Speculators crowded long** (>80th percentile)
❌ **Open interest collapsing** (longs/shorts both exiting)
❌ **Commercial short hedging spikes** (producers locking in)

### Measurement Rules

```python
# 1. Percentile rank (vs 5-year history)
current_percentile = percentileofscore(historical_net, current_net)

# 2. Weekly deltas (velocity matters)
delta_net = current_net - prior_week_net

# 3. Divergence detection
if (commercial_net > 0) and (managed_money_net < 0):
    alert("Smart money vs dumb money divergence")
```

**Watch for extremes**: >90th percentile long = top, <10th = bottom

---

## Rule 10: Crush Margins (Hidden Driver)

### The Behavior Signal

Crush margins aren't a single number—they're **behavior signals**.

### Good (Bullish Soy Oil)

✅ **U.S. crush margins wide** (crushers running hard)
✅ **Strong domestic demand for oil** (biodiesel, food)
✅ **Meal demand weakening** (supply favors oil)

### Bad (Bearish Soy Oil)

❌ **Crush margins collapse** (crushers idle)
❌ **Meal demand surges** (ASF recovery → more meal, less oil focus)
❌ **Biodiesel margins weaken** (renewable diesel soft)

### Measurement Rules

```python
# 1. 20-30 day EMA (smooth noise)
crush_margin_ema = df['crush_margin'].ewm(span=25).mean()

# 2. ZS/ZM/ZL spread dynamics
spread = (ZS_price - (ZM_price * 0.022 + ZL_price * 0.11))

# 3. FCPO divergence (palm oil competition)
soy_palm_margin = (ZL_crush_margin - FCPO_crush_margin)
```

**Alert if**: Margins invert (negative), or palm spreads widen >$50/MT

---

## Rule 11: Palm Oil Substitution

### The Common Error

**"Palm down = Soy down"** is NOT always true.

### Bullish Soy (Despite Palm Weakness)

✅ **Indonesia/Malaysia export bans** (DMO restrictions)
✅ **Labor shortages** (Malaysian plantations)
✅ **ESG import hurdles** (EU deforestation regs)

### Bearish Soy

❌ **India cuts import duties** (palm becomes cheaper)
❌ **Malaysia bumper output** (production spike)
❌ **High soy:palm ratio** (>2.2 = soy expensive)

### Measurement Rules

**Never use absolute prices**:

```python
# 1. Relative ratio (NOT levels)
soy_palm_ratio = ZL_price / FCPO_price

# 2. Relative volatility spread
vol_spread = volatility(ZL) - volatility(FCPO)

# 3. Freight-adjusted arbitrage
arb_value = (ZL - FCPO) - freight_cost - quality_discount
```

**Integrate friction**: DMO policies, freight, quality spreads

---

## Rule 12: China Demand (Most Important)

### The Action Rule

**China is action, not words.** Rhetoric ≠ imports.

### Good (Bullish Soy)

✅ **Strong weekly import pace** (actual ships arriving)
✅ **Dalian futures premium** (domestic tightness)
✅ **Reserve stockpiling** (state buying confirmed)
✅ **Weak USD/CNY** (yuan strong = buying power ↑)

### Bad (Bearish Soy)

❌ **Lower import licenses** (quotas cut)
❌ **Reserve releases** (state selling confirmed)
❌ **ASF outbreaks** (hog herd ↓ = feed demand ↓)
❌ **CNY weakening aggressively** (buying power ↓)

### Measurement Rules

```python
# 1. Import pace vs seasonal norm
import_zscore = (current_imports - seasonal_avg) / seasonal_std

# 2. Crush margins (domestic crushers)
china_crush_margin = dalian_futures - (import_cost + crushing_cost)

# 3. State reserve actions (directional)
if reserve_action == 'buying':
    bullish_signal()
elif reserve_action == 'selling':
    bearish_signal()

# 4. Hog herd metrics (demand proxy)
feed_demand = hog_inventory * feed_per_hog
```

**Down-weight rhetoric unless paired with real data.**

---

## Integration Rules

### Pairing Requirements (MANDATORY)

Every signal must be paired with at least one validator:

| Primary Signal | Required Pair | Why |
|----------------|---------------|-----|
| USD | EM FX (BRL, ARS, CNY) | Dollar strength means nothing without EM context |
| Fed Rates | USD Index + Yield Curve | Rate changes flow through FX and credit |
| VIX | Liquidity Metrics + Spreads | Fear without illiquidity = noise |
| Sentiment | Fundamental + Cross-Market | Vibes need mechanism validation |
| Biofuel Policy | Volume Calculation | Policy means nothing without MT impact |
| Weather | GDD + Soil + Production | Single anomalies are noise |
| Crush Margins | ZS/ZM/ZL Spread + FCPO | Margins need competitive context |
| China Demand | Import Pace + Reserves | Words need action validation |

### Cross-Asset Confirmation Matrix

```
Signal → Confirm With → Then Check
USD ↑ → BRL↓, ARS↓ → Soy exports ↑ → Bearish
VIX ↑ → Spreads ↑ → Liquidity ↓ → Conviction ↑, Confidence ↓
Fed Cut → USD ↓ → EM buying ↑ → Bullish
Weather ↓ → GDD ↓ → Yield ↓ → Bullish
```

---

## Common Errors to Avoid

### ❌ Single-Signal Trading
```python
# WRONG
if usd_up:
    return bearish()
```
**Why**: No context, no confirmation, no mechanism

### ❌ Absolute Levels Without Z-Score
```python
# WRONG  
if vix > 20:
    return crisis()
```
**Why**: VIX 20 in 2019 ≠ VIX 20 in 2020. Use regime-relative metrics.

### ❌ Sentiment Without Mechanism
```python
# WRONG
if news_sentiment > 0.7:
    return bullish()
```
**Why**: Vibes don't move markets. Mechanism does.

### ❌ Policy as Text
```python
# WRONG
if "biofuel mandate" in policy_text:
    return bullish()
```
**Why**: Must convert to volume impact (MT-equivalent demand)

---

## Validation Checklist

Before trading on any signal, verify:

- [ ] Signal has a **mechanism** (not just correlation)
- [ ] Signal has **cross-asset confirmation**
- [ ] Signal has **regime context** (z-score, not absolute)
- [ ] Signal has **time persistence** (not single-day spike)
- [ ] Signal has **fundamental validation** (real data, not text)
- [ ] **Conviction** and **Confidence** are separated
- [ ] **Historical MAPE** for this regime is known

---

## Conclusion

**The Principle**: Signals are not numbers on charts. They are **mechanisms with context**.

**The Discipline**: Never trade on a signal in isolation. Always pair, validate, and contextualize.

**The Edge**: Amateurs react to headlines. Professionals wait for mechanism confirmation.

---

**Last Updated**: November 14, 2025  
**Status**: INSTITUTIONAL FRAMEWORK  
**Next**: Implement validation layer in signal processing pipeline

