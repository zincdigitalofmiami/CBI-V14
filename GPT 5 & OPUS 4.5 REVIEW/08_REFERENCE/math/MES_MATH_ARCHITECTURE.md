---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# MES MATH ARCHITECTURE — High-Level Specification

**Status:** Production-ready architecture specification  
**Purpose:** Define compute placement, mathematical methods, and data flow for MES trading cockpit and ZL procurement dashboard  
**Last Updated:** November 19, 2025

---

## 0) COMPUTE PLACEMENT

### BigQuery (Scheduled Jobs, Cheap + Auditable)

**Responsibilities:**
- RTH/ETH sessionization; daily RTH highs/lows
- Swing detection metadata (zig-zag pivots); Fibonacci anchor storage
- Daily feature joins (VIX, rates, COT, policy, weather)
- Dashboard overlay views (pinball bands, force lines, checklists)

**Why BigQuery:**
- Cost-effective for scheduled batch jobs
- Fully auditable SQL transformations
- Real-time dashboard queries
- Centralized data authority

### Mac M4 Pro (Local, Model & Numerics)

**Responsibilities:**
- Monte-Carlo (10k paths) with Brownian-bridge barrier adjustment
- GEX/Gamma-wall surface from CME options OI + Black-76 Greeks
- SHAP aggregation → 4 "force lines" (VIX, Yield, Trump/Policy, COT)
- Health checks / calibration metrics that feed the "Entry Checklist"

**Why Mac:**
- Complex numerical computations (Monte-Carlo, Greeks)
- Model training and inference
- SHAP calculations (TreeSHAP)
- Local compute for sensitive MES calculations

### Round-Trip Data Flow

**Mac → BigQuery:**
- Mac writes derived artifacts back to BQ:
  - `predictions.*` - Forecasts and quantiles
  - `derivatives.*` - Gamma exposure, GEX surfaces
  - `explainability.*` - SHAP values, force lines
  - `signals.*` - Entry checklists, Fibonacci levels

**Dashboard Consumption:**
- Dashboard reads from BigQuery views that join all artifacts
- Real-time updates via scheduled jobs
- No direct Mac access from dashboard

---

## 1) FIBONACCI (Auto-Detection from RTH High/Low + Major Swings)

### Inputs

- `market_data.databento_futures_ohlcv_1m` (MES) / `market_data.databento_futures_ohlcv_1d` (ZL)
- `dim.exchange_sessions` (session calendar)
- ATR-based zig-zag parameters (instrument-specific)

### Method

**RTH Windows:**
1. Tag bars with `session_id` and `is_rth` from `dim.exchange_sessions`
2. For each day/session, compute RTH high/low/close

**Swing Anchors:**
1. Run zig-zag on RTH closes using reversal threshold = `k × ATR₁₄`
   - ZL: Daily ATR₁₄
   - MES: 5-minute ATR
2. This yields the last confirmed swing high and last confirmed swing low

**Levels:**
From the most recent impulse leg (Low→High or High→Low), compute:
- **Retracements:** 23.6%, 38.2%, 50%, 61.8%, 78.6%
- **Extensions:** 127.2%, 161.8% (snap to valid tick)

**Reference:** [Fibonacci retracement conventions](https://en.wikipedia.org/wiki/Fibonacci_retracement)

### Persistence

**Table:** `signals.fib_levels`

**Schema:**
```sql
date DATE,
symbol STRING,
anchor_low FLOAT64,
anchor_high FLOAT64,
leg_dir STRING,  -- 'up' or 'down'
fib_236 FLOAT64,
fib_382 FLOAT64,
fib_500 FLOAT64,
fib_618 FLOAT64,
fib_786 FLOAT64,
ext_1272 FLOAT64,
ext_1618 FLOAT64,
tick_rounding FLOAT64
```

**Refresh:** Recompute on zig-zag confirmation (not every bar) to avoid whipsaw overlays

**Why RTH?** Cleaner microstructure & "human" reference points; ETH kept for context on MES privately

---

## 2) PROBABILITIES: Monte-Carlo (10k Paths) → Tap Probability Per Level

### Goal

For any level `L` and horizon `H` (ZL: 1w/1m; MES intraday: 5/15/60m), estimate:
- **Upper levels:** `Pr(sup_{t≤H} S_t ≥ L)`
- **Supports:** `Pr(inf_{t≤H} S_t ≤ L)`

### Calibration (Per Asset/Horizon)

**Drift:**
- Use model's P50 (pinball median) → implied drift over `H`

**Volatility:**
- Use VIX (from FRED) as primary volatility measure
- Else: realized vol/GARCH(1,1)
- **Note:** VIX is preferred over CVOL for consistency and availability

**Shape:**
- Match tails using quantile set (P10/25/50/75/90)
- Sample via quantile-implied distribution (piecewise linear inverse-CDF)
- Respects asymmetry vs pure lognormal

### Path Generation

1. Generate 10,000 price paths at native bar frequency
2. Use **Brownian-bridge correction** when testing barrier hits between steps
   - Removes discretization bias (standard in barrier MC)
   - **Reference:** [Barrier MC with Brownian-bridge corrections](https://arxiv.org/abs/1201.2995)

### Outputs to Persist

**Table:** `backtesting.mc_touches`

**Schema:**
```sql
date DATE,
symbol STRING,
horizon STRING,  -- '1w', '1m', '5m', '15m', '60m'
level_tag STRING,  -- 'fib_618', 'gamma_wall_1', etc.
level_price FLOAT64,
tap_prob FLOAT64,
tap_prob_ci_low FLOAT64,
tap_prob_ci_high FLOAT64,
exp_time_to_touch FLOAT64,
path_var95 FLOAT64
```

**CI Calculation:**
- Binomial confidence interval: `±1.96√(p(1-p)/N)`
- Where `p` = tap probability, `N` = 10,000 paths

### Dashboard Overlay

- Plot `tap_prob` badges next to each level
- Show pinball bands already locked as overlays

---

## 3) GAMMA WALLS: GEX Zero Line, Walls, Rejection Probability

### Inputs

- End-of-day options OI and settlements for front expiries (ZL, MES/ES)
  - **Source:** CME DataMine/CME EOD options
  - **Note:** DataBento covers futures; for options Greeks compute from CME quotes/OI
- Underlying futures level, time-to-expiry, IV (CVOL proxy or per-strike IV)

### Method

**Per Option (Strike K, Expiry T):**
1. Compute Black-76 gamma `Γ_i`
   - **Reference:** [Black's futures-option framework](https://en.wikipedia.org/wiki/Black_model); [Greeks formulas](https://en.wikipedia.org/wiki/Greeks_(finance))

**Exposure:**
```
GEX(K) = Σ_i Γ_i × OI_i × contract_multiplier
```
- Aggregated over calls & puts
- Assume dealer = contra to public OI

**Surface → Price Grid:**
1. Interpolate `GEX` across price to build continuous exposure curve
2. For each near-term expiry, sum across near expiries with theta weighting
   - Closer expiries get higher weight

**Zero Gamma Line:**
- Price where net `GEX` crosses 0
- Market flips from short-gamma to long-gamma
- **Reference:** [Dealer gamma / zero-gamma concept](https://squeezemetrics.com)

**Walls:**
- Local extrema of `|GEX|` near large OI strikes = dealer walls (support/resistance)

**Rejection Probability (Empirical):**
```
z = |P_0 - K_wall| / (σ_F × √H)
g = |d GEX/dP| / median(|d GEX/dP|)
p_reject = σ(α·g - β·z)
```
- Calibrate `α, β` on historical "first-touch then reverse" events
- `σ()` = sigmoid function

### Outputs

**Table:** `derivatives.gamma_summary`

**Schema:**
```sql
date DATE,
symbol STRING,
expiry DATE,
zero_gamma FLOAT64,
wall_1 FLOAT64,
wall_2 FLOAT64,
wall_strength FLOAT64,
p_reject_wall_1 FLOAT64,
p_reject_wall_2 FLOAT64
```

**Note:** For ZL, options OI can be thinner than ES; still useful around WASDE / RFS headlines

---

## 4) SHAP: 4 Force Lines on Right Axis (VIX, Yield, Trump/Policy, COT)

### Inputs

- Per-prediction SHAP from trained quantile model(s)
- Already in `explainability.shap_values/...`

### Feature → Group Map

**VIX Group:**
- `fred_vix`, realized vol, VIX deltas

**Yield Group:**
- `fred_dgs2`, `fred_dgs10`, spreads

**Trump/Policy Group:**
- Regime flags (2017-19 trade war, 2023-25)
- RFS/RINs, policy/sentiment feeds (ScrapeCreators)

**COT Group:**
- `cftc_net_spec`, `cftc_net_comm`, weekly changes

### Method

**Group Aggregation:**
1. For each date & horizon, sum SHAP across features in the group
2. → Four group contributions (units = predicted return contribution)
3. **Reference:** [SHAP framework supports additivity/grouping](https://arxiv.org/abs/1705.07874)

**Stabilize:**
- 7-day EMA on group lines
- Clip outliers at 1%/99%

**Scale for Plotting:**
- Right-axis scaled to `±2` standard deviations of group contributions

### Persistence

**Table:** `explainability.force_lines`

**Schema:**
```sql
date DATE,
symbol STRING,
horizon STRING,
shap_vix FLOAT64,
shap_yield FLOAT64,
shap_trump FLOAT64,
shap_cot FLOAT64,
shap_sum FLOAT64
```

### Dashboard Overlay

- Four thin lines on the right axis
- Tooltip shows each group's share of last forecast
- Example: "VIX contributed -18 bps to P50"

---

## 5) ENTRY CHECKLIST → EXECUTE (Procurement-Only)

### Six Binary Checks

**1. Model Health:**
- Last 60D quantile coverage within tolerance (e.g., 90% band covers 87-93%)
- Pinball loss improving → **PASS**

**2. Regime Validity:**
- Live regime confidence ≥ 0.7
- Matches model's trained slice → **PASS**

**3. Risk to Budget:**
- `Pr(price ≥ budget_cap)` from MC (1w/1m)
- **Aggressive buy** if ≥ 30% (lock costs)
- **Partial** if 15-30%
- **Defer** if < 15%

**4. Confluence:**
- Price within 0.3σ of a Fib 38.2/61.8
- Aligned with supportive gamma wall (for buys) → **PASS**

**5. Positioning Not Crowded:**
- COT specs not at 90th pct long
- Avoid paying peak optimism → **PASS**

**6. Vol Sanity:**
- VIX < stress threshold
- Quantile width not exploding (>2σ widening) → **PASS**

### Execution Rule

- **6/6** → EXECUTE full tranche
- **4-5/6** → EXECUTE PARTIAL (e.g., 50%) and set ladder at next Fib
- **≤3/6** → WAITLIST; monitor MC tap/force lines

### Persistence

**Table:** `signals.entry_checklist`

**Schema:**
```sql
date DATE,
symbol STRING,
check_model_health BOOL,
check_regime_valid BOOL,
check_budget_risk STRING,  -- 'aggressive', 'partial', 'defer'
check_confluence BOOL,
check_positioning BOOL,
check_vol_sanity BOOL,
tranche_pct FLOAT64,  -- 0-100%
rationale STRING,  -- Top 2 factors from SHAP groups
verdict STRING  -- 'EXECUTE', 'PARTIAL', 'WAIT'
```

**Rendering:** Single EXECUTE button (procurement ticket, not a trade)

---

## 6) TABLES / VIEWS TO ADD

### Fibonacci
- `signals.fib_levels` (daily/session granularity)

### Monte-Carlo Touch
- `backtesting.mc_touches` (per level & horizon)

### Gamma
- `derivatives.options_oi_raw` (ingest)
- `derivatives.gex_surface` (intermediate)
- `derivatives.gamma_summary` (dashboard)

### Force Lines
- `explainability.force_lines` (grouped SHAP)

### Checklist
- `signals.entry_checklist` (booleans, tranche %, rationale)

### API Views (Chris-Facing)
- `api.vw_zl_strategy_overlay` joins:
  - Latest price, pinball bands, Fib levels, MC tap probs, gamma walls, force lines, checklist verdict

**Naming Convention:** All tables prefixed & partitioned by `date`

---

## 7) DATA DEPENDENCIES & INGESTION NOTES

### VIX (Volatility)
- **Source:** FRED VIX (daily)
- **Storage:** `raw_intelligence.sentiment_daily` (via FRED integration)
- **Join:** To `features.master_features` as `fred_vix`
- **Note:** VIX is used instead of CVOL for consistency and availability

### Options OI
- **Source:** CME EOD options (front 3 expiries)
- **Storage:** `derivatives.options_oi_raw`
  - Columns: `strike`, `call_put`, `oi`, `settle`, `expiry`, `multiplier`
- **Processing:** Compute Black-76 Greeks on Mac; push GEX back
- **Reference:** [Black-76 Greeks overview](https://en.wikipedia.org/wiki/Greeks_(finance))

### MES Private
- Keep MES options/greeks local
- Publish only derived overlays to private MES dashboard
- **NOT** published to Chris's dashboard

---

## 8) QA / CALIBRATION (One-Time Setup)

### Fibonacci Robustness
- Validate zig-zag thresholds per instrument
- Optimize `k` vs false-signal rate

### MC Calibration
- Backtest tap probabilities out-of-sample
- Adjust drift/vol mapping (e.g., blend VIX with realized vol)

### Gamma Rejection
- Fit `α, β` using historical first-touch reversals around big OI strikes
- Store calibration version

### SHAP Stability
- Monitor group variance
- If one group dominates persistently, review feature leakage

### Checklist Hit-Rate
- Track average procurement cost vs equal-time baseline per decision class
- Classes: Execute / Partial / Wait

---

## 9) DASHBOARD OVERLAYS (What Chris Sees)

### Main Chart Overlays

1. **Pinball Bands** (locked) on every main chart
2. **Fib Ladder** (current leg) with tap probabilities beside each rung - **Toggleable via checkbox (Default: OFF)**
3. **Gamma:**
   - Zero-gamma line
   - Top 2 walls
   - Rejection probability badges
4. **Force Lines** (VIX, Yield, Trump, COT) on right-axis
5. **Checklist Strip:**
   - 6 lights + EXECUTE (full/partial/no-go)
   - "Why" (top 2 factors pulled from SHAP groups)

---

## REFERENCES

### Methods & Definitions

1. **Fibonacci Retracements:** [Definition & conventional levels](https://en.wikipedia.org/wiki/Fibonacci_retracement)
2. **Black-76:** [Futures options framework](https://en.wikipedia.org/wiki/Black_model) & [Greeks](https://en.wikipedia.org/wiki/Greeks_(finance))
3. **Dealer Gamma:** [Zero-gamma concept](https://squeezemetrics.com)
4. **VIX:** FRED VIX index (volatility measure)
5. **Barrier MC:** [Brownian-bridge corrections](https://arxiv.org/abs/1201.2995)
6. **SHAP:** [Model explainability - grouping/attribution](https://arxiv.org/abs/1705.07874)

---

## ARCHITECTURE SUMMARY

**BigQuery-Centric:**
- Data authority and storage
- Scheduled batch jobs
- Dashboard serving layer

**Mac M4 Pro:**
- Complex numerical computations
- Model training and inference
- SHAP calculations

**Round-Trip:**
- Mac writes artifacts to BigQuery
- Dashboard consumes from BigQuery views
- Clean separation of concerns

**MES Separation:**
- MES calculations private (local Mac)
- Shared drivers (FRED, FX, policy, weather) reused
- Derived overlays published to private MES dashboard only

---

**Last Updated:** November 19, 2025  
**Status:** Production-ready architecture specification  
**Integration:** Slots cleanly into BQ-centric + Mac-training architecture with minimal new plumbing

