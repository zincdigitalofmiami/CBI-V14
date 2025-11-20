---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# STRATEGY PAGE SCENARIO CARDS — Specification

**Status:** Production-ready specification  
**Page:** `app/strategy/page.tsx`  
**User:** Chris (Procurement Manager)  
**Purpose:** What-if scenario planning for procurement decisions

---

## SCENARIO CARDS (6 Total)

### 1. Volatility Card

**Control:** VIX ± 1–2σ adjustment  
**Effect:** Widens/narrows quantile bands  
**Data Source:** `raw_intelligence.sentiment_daily` (VIX from FRED)  
**Method:**
- Current VIX level → adjust by ±1σ or ±2σ
- Recompute quantile bands (P10/P25/P50/P75/P90) using adjusted volatility
- Monte-Carlo paths use adjusted vol parameter

**Visual:**
- Card shows current VIX level
- Adjustable range: ±2σ from current
- Real-time update of quantile bands on all horizon charts

---

### 2. Biofuel Demand Card

**Control:** EIA biodiesel + RIN D4 Δ%  
**Effect:** Biofuels driver weight adjustment  
**Data Sources:**
- `features.master_features` (EIA biodiesel production)
- `features.master_features` (RIN D4 price changes)

**Method:**
- Adjust biofuel demand driver weight in SHAP response surface
- Post-hoc sensitivity: tilt biofuel features without retraining
- Recompute forecast bands using adjusted driver contribution

**Visual:**
- Card shows current EIA biodiesel production + RIN D4 % change
- Adjustable: ±X% change to biofuel demand weight
- Shows impact on procurement sentiment index

---

### 3. FX Card

**Control:** BRL ±X%, CNY ±X%  
**Effect:** Export competitiveness adjustment  
**Data Sources:**
- `features.master_features` (fred_usd_brl, fred_usd_cny)

**Method:**
- Adjust FX rates by ±X%
- Recompute export competitiveness features
- Apply to SHAP response surface for trade-related features

**Visual:**
- Card shows current BRL and CNY rates
- Separate controls for each currency
- Shows impact on export demand forecasts

---

### 4. Trade Card

**Control:** China weekly export sales shock (percentile toggle)  
**Effect:** Trade policy impact adjustment  
**Data Sources:**
- `features.master_features` (usda_exports_soybeans_net_sales_china)

**Method:**
- Toggle between percentile scenarios (P10/P25/P50/P75/P90)
- Apply shock to China export sales feature
- Recompute trade-related SHAP contributions

**Visual:**
- Card shows current China export sales
- Percentile toggle buttons (P10/P25/P50/P75/P90)
- Shows historical context for each percentile

---

### 5. Weather Card

**Control:** ONI phase toggle + Brazil/Argentina regional tilts  
**Effect:** Weather/supply impact adjustment  
**Data Sources:**
- `features.master_features` (weather_* columns)
- ONI (Oceanic Niño Index) phase data

**Method:**
- Toggle ONI phase: El Niño / Neutral / La Niña
- Adjust Brazil/Argentina regional moisture/temperature
- Recompute weather-related SHAP contributions

**Visual:**
- Card shows current ONI phase
- Toggle buttons: El Niño / Neutral / La Niña
- Regional sliders for Brazil/Argentina moisture/temperature
- Shows impact on South America weather sentiment layer

---

### 6. Substitutes Card

**Control:** Palm oil +/−10%  
**Effect:** Elasticity link applied to ZL baseline  
**Data Sources:**
- `features.master_features` (barchart_palm_* columns)

**Method:**
- Adjust palm oil price by ±10%
- Apply substitution elasticity to ZL demand
- Recompute palm substitution sentiment layer

**Visual:**
- Card shows current palm oil price
- Adjustable range: ±10% from current
- Shows substitution impact on ZL demand

---

## SCENARIO EXECUTION

### How It Works

1. **Each card adjustment:**
   - Writes a scenario key to `predictions.scenario_forecasts` table
   - Recomputes forecast band **without retraining**
   - Uses post-hoc sensitivity and SHAP response surface

2. **Monte-Carlo Re-run:**
   - Instant 5,000-path Monte-Carlo re-run across all horizons
   - Uses adjusted feature values from scenario cards
   - Updates quantile bands (P10/P25/P50/P75/P90)

3. **SHAP Recalculation:**
   - Recomputes SHAP values for adjusted scenario
   - Updates force lines (VIX, Yield, Trump/Policy, COT)
   - Shows which driver becomes #1 under new scenario

4. **Visual Updates:**
   - Recharts redraws every cone chart in real time
   - SHAP overlays update to show new driver rankings
   - Floating box: "Under this scenario: [Driver] becomes #1 driver (+X.XX¢)"

---

## PERSISTENCE

### Scenario Storage

**Table:** `predictions.scenario_forecasts`

**Schema:**
```sql
date DATE,
symbol STRING,
scenario_key STRING,  -- Unique scenario identifier
horizon STRING,  -- '1w', '1m', '3m', '6m', '12m'
pred_price FLOAT64,
lower_68 FLOAT64,
upper_68 FLOAT64,
lower_95 FLOAT64,
upper_95 FLOAT64,
scenario_params JSON,  -- All card adjustments as JSON
shap_vix FLOAT64,
shap_yield FLOAT64,
shap_trump FLOAT64,
shap_cot FLOAT64,
created_at TIMESTAMP
```

### Scenario Key Format

```
{volatility_adj}_{biofuel_adj}_{fx_brl_adj}_{fx_cny_adj}_{trade_percentile}_{oni_phase}_{palm_adj}
```

Example: `vix_+1s_bio_+5pct_fxbrl_-2pct_fxcny_0pct_trade_p75_oni_la_nina_palm_+5pct`

---

## ADDITIONAL FEATURES

### Save Scenario

- **Button:** "Save Scenario"
- **Action:** Saves current card settings to `signals.saved_scenarios`
- **Recall:** Load saved scenarios for quick comparison

### Replay Historical Events

- **Button:** "Replay Feb 2025 Collapse"
- **Action:** Loads historical scenario parameters from past events
- **Examples:**
  - Feb 2025 Phase One Collapse
  - Q1 2025 RIN Surge
  - La Niña 2024 Drought

### Partial Derivatives Table

**Shows:** Sensitivity of forecast to each card adjustment

**Example:**
```
1% RIN hike = +0.47¢ ZL in 3M
VIX +1σ = +2.3% quantile band width
BRL -5% = -1.2¢ ZL in 1M
```

### Walk-Forward Validation

**Shows:** Actual vs simulated for past 12 events

**Comparison:**
- What model predicted with scenario cards
- What actually happened
- Accuracy metrics per scenario type

### Chris's Alpha Tracker

**Shows:** Cumulative $ saved if followed model

**Example:** "+$2.47M saved since Jan 2025"

**Calculation:**
- Compare actual procurement cost vs model-recommended cost
- Track savings from following scenario-based recommendations

---

## DATA SOURCES SUMMARY

| Card | Primary Data Source | Feature Columns |
|------|-------------------|-----------------|
| Volatility | `raw_intelligence.sentiment_daily` | VIX level (from FRED) |
| Biofuel | `features.master_features` | EIA biodiesel, RIN D4 |
| FX | `features.master_features` | `fred_usd_brl`, `fred_usd_cny` |
| Trade | `features.master_features` | `usda_exports_soybeans_net_sales_china` |
| Weather | `features.master_features` | `weather_*` columns, ONI phase |
| Substitutes | `features.master_features` | `barchart_palm_*` columns |

---

## IMPLEMENTATION NOTES

### Post-Hoc Sensitivity

- **No retraining required:** Scenario adjustments use SHAP response surface
- **Fast computation:** <500ms for full scenario recomputation
- **Accurate:** Uses same model, just tilts feature contributions

### SHAP Response Surface

- Pre-computed SHAP values for base scenario
- Scenario adjustments modify feature contributions
- Aggregated to 4 force lines (VIX, Yield, Trump/Policy, COT)

### Monte-Carlo Paths

- 5,000 paths per scenario
- Uses adjusted volatility (from VIX card)
- Uses adjusted drift (from other cards via SHAP)
- Brownian-bridge correction for barrier hits

---

**Last Updated:** November 19, 2025  
**Status:** Production-ready specification  
**Integration:** Works with existing SHAP, Monte-Carlo, and forecast infrastructure

