---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# IV30 Calculation Methodology (Future Enablement)
**Date:** November 20, 2025  
**Status:** ⛔ Blocked – CME options not included in current plan  
**Source (once licensed):** DataBento GLBX Options for ZL and ES  
**Output:** `features.iv30_from_options(symbol, date, iv30, obs_count, moneyness_span, quality_flag, asof_source_time)`

---

## Overview

This document describes the methodology for calculating 30-day implied volatility (IV30) from real exchange-traded options data via DataBento GLBX.

> **Important:** CME options are **not** included in the current DataBento plan.  
> The code and methodology are preserved for the day we add an options license.  
> Until then, the IV30 pipeline remains disabled and the Volatility Pillar uses futures-only signals.

**Key Principle:** Entirely derived from real exchange quotes; no "synthetic" data; reproducible.

---

## Data Source

**Provider:** DataBento  
**Dataset:** GLBX.MDP3 (CME Globex Market Data Platform) – requires CME options add-on  
**Schema:** Options OHLCV data  
**Symbols:** ZL (Soybean Oil) and ES (E-mini S&P 500) futures options  
**Frequency:** Daily snapshots (once licensed)

---

## Methodology

### Step 1: Data Collection

1. Query DataBento GLBX options chain for target symbol (ZL or ES)
2. Collect all available calls and puts for the trading day
3. Include: strike prices, bid/ask quotes, volume, open interest, expiry dates

### Step 2: Quality Filtering

Apply guardrails to ensure data quality:

1. **Wide Spread Filter:**
   - Discard quotes where `(ask - bid) / mid_price > 20%`
   - Prevents using illiquid or stale quotes

2. **Stale Timestamp Filter:**
   - Discard quotes older than 5 minutes from market close
   - Ensures quotes reflect current market conditions

3. **Valid Strike Coverage:**
   - Require minimum strike coverage around ATM (±20% moneyness)
   - Ensures sufficient data for volatility surface fitting

### Step 3: Implied Volatility Calculation

For each quality-filtered option:

1. Extract option parameters:
   - Strike price
   - Time to expiry (calculated from expiry date)
   - Option type (Call or Put)
   - Mid price: `(bid + ask) / 2`

2. Calculate implied volatility using Black-Scholes model:
   - Solve for IV that matches market price
   - Use risk-free rate from FRED (e.g., 10-year Treasury)
   - Handle both calls and puts

### Step 4: Volatility Surface Fitting

1. Group IVs by time-to-expiry
2. Filter for options near 30-day maturity (25-35 days)
3. If no exact 30-day options:
   - Interpolate IV curve across maturities
   - Extract IV at exactly 30 days

4. Select ATM (At-The-Money) IV:
   - Find option with moneyness closest to 1.0
   - Use its IV as IV30

### Step 5: Quality Assessment

Assign quality flag based on:

- **`ok`**: 
  - ≥5 observations
  - ATM coverage (±20% moneyness) with ≥3 strikes
  - Moneyness span ≥20%

- **`sparse`**:
  - ≥5 observations but insufficient ATM coverage
  - Moneyness span <20%

- **`fail`**:
  - <5 observations
  - No valid IV calculations
  - Missing spot price or options data

---

## Output Schema

```python
features.iv30_from_options(
    symbol: str,              # 'ZL' or 'ES'
    date: date,               # Trading date
    iv30: float,              # 30-day implied volatility (annualized)
    obs_count: int,           # Number of options used in calculation
    moneyness_span: float,    # Range of moneyness values (max - min)
    quality_flag: str,        # 'ok', 'sparse', or 'fail'
    asof_source_time: str     # ISO timestamp of calculation
)
```

---

## Modeling Choices & Diagnostics

### Interpolation Method

- **Method:** Linear interpolation for time-to-expiry
- **Rationale:** Simple, transparent, avoids overfitting
- **Limitation:** Assumes linear IV term structure (may not hold in all regimes)

### Black-Scholes Assumptions

- **Model:** Standard Black-Scholes-Merton
- **Assumptions:**
  - Constant volatility (violated in reality, but standard for IV extraction)
  - Log-normal price distribution
  - No dividends (futures options)
  - Constant risk-free rate

### Risk-Free Rate

- **Source:** FRED 10-year Treasury rate (DGS10)
- **Rationale:** Standard benchmark for options pricing
- **Alternative:** Could use 3-month T-bill for shorter-term options

---

## Logging & Diagnostics

The calculation script logs:

1. **Daily Statistics:**
   - Number of options collected
   - Number after quality filtering
   - IV30 value and quality flag
   - Moneyness span and observation count

2. **Quality Metrics:**
   - Percentage of days with 'ok' quality
   - Percentage with 'sparse' quality
   - Percentage with 'fail' quality

3. **Data Quality Warnings:**
   - Days with insufficient strike coverage
   - Days with stale quotes
   - Days with missing spot prices

---

## Integration

### Daily Pipeline (future state)

1. **Collection:** Run `calculate_iv30_from_options.py` daily after market close *(disabled until options license is enabled)*
2. **Storage:** Save to `TrainingData/features/iv30_from_options.parquet`
3. **Integration:** Merge into master features table with prefix `iv30_`

### Feature Usage

- **Primary Use:** Daily volatility anchor for quantile calculations and Monte Carlo simulations
- **Secondary Use:** Volatility regime classification
- **Replaces:** VIX backup once options feed is live

---

## Compliance

✅ **Real Sources Only:** All data from DataBento GLBX exchange quotes  
✅ **No Synthetic Data:** No placeholders, no fake values  
✅ **Reproducible:** All calculations documented and logged  
✅ **Transparent:** Modeling choices explicitly stated

---

## Future Enhancements

1. **CME CVOL License:** If/when CME CVOL is licensed, replace this calculation
2. **Advanced Interpolation:** Consider spline or kernel methods for volatility surface
3. **Stochastic Volatility Models:** For more sophisticated IV extraction (if needed)
4. **Multi-Maturity:** Calculate IV for multiple maturities (7d, 30d, 60d, 90d)

---

**Status:** ⛔ Blocked – enable after CME options license is added
