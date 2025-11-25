# VIX Alternatives for MES Engine
**Date:** November 24, 2025  
**Status:** ✅ Documented - VIX9D/VIX3M not in FRED, use alternative calculations

---

## Problem

**VX.FUT (VIX Futures) is NOT available:**
- VX.FUT trades on CBOE CFE (`XCFE.OCELOT`), not CME Globex (`GLBX.MDP3`)
- Current subscription: `GLBX.MDP3` (CME only)
- **Solution:** Use FRED VIX substitutes + calculations

**VIX9D and VIX3M are NOT in FRED:**
- These are CBOE proprietary indices, not FRED series
- FRED only has `VIXCLS` (spot VIX)
- **Solution:** Use alternative calculations for term structure

---

## Available VIX Data

| Source | Series | Status | Date Range | Purpose |
|--------|--------|--------|------------|---------|
| **FRED** | `VIXCLS` | ✅ Loaded | 2010-01-04 → 2025-11-21 | Spot VIX (S&P 500) |
| **FRED** | `VXOCLS` | ✅ Loaded | 2010-01-04 → 2025-11-21 | Old VXO (S&P 100) |
| **FRED** | `VXVCLS` | ✅ Loaded | 2010-01-04 → 2025-11-21 | **3-Month VIX** (term structure) |
| **CBOE** | VIX9D | ❌ Not in FRED | N/A | Not needed (have VXVCLS) |
| **Databento** | VX.FUT | ❌ Not in subscription | N/A | Not needed (have VXVCLS) |

---

## VIX Term Structure Calculation

**✅ We now have VXVCLS (3-Month VIX) from FRED!**

This allows us to calculate proper VIX term structure:

```sql
-- VIX term structure (proper calculation)
vix_term_structure = vxv_close / vix_close  -- 3M VIX / Spot VIX

-- When ratio > 1.0: Contango (normal, complacent market)
-- When ratio < 1.0: Backwardation (panic, elevated fear)
-- When ratio >> 1.0: Extreme contango (very complacent)
-- When ratio << 1.0: Extreme backwardation (panic selling)
```

**Additional calculations using realized volatility:**

### Option 1: Realized Vol vs VIX (Vol Risk Premium)

```sql
-- Calculate vol risk premium (proxy for term structure)
vol_risk_premium = vix_close - realized_vol_20d

-- When vol_risk_premium > 0: Market pricing more fear than actual (contango-like)
-- When vol_risk_premium < 0: Market complacent relative to actual (backwardation-like)
```

### Option 2: VIX Percentile-Based Regime

```sql
-- Use VIX percentile to infer term structure regime
vix_percentile_1y = PERCENT_RANK() OVER (ORDER BY vix_close) -- last 1 year

-- High percentile (90+) = backwardation regime (panic)
-- Low percentile (<40) = contango regime (complacency)
```

### Option 3: VIX Momentum as Term Structure Proxy

```sql
-- VIX rate of change approximates term structure slope
vix_momentum_5d = (vix_close - LAG(vix_close, 5)) / LAG(vix_close, 5)

-- Positive momentum = steepening (backwardation developing)
-- Negative momentum = flattening (contango developing)
```

### Option 4: Historical VIX Pattern Matching

```sql
-- Compare current VIX to historical patterns
-- During 2020 crash: VIX spiked to 80+, then mean-reverted
-- During 2022: VIX elevated 20-30 range
-- Use these patterns to infer term structure state
```

---

## Recommended MES VIX Features

**Primary VIX Features (from FRED):**

1. **`vix_close`** - Spot VIX level (✅ Have)
2. **`vxv_close`** - 3-Month VIX (✅ Have) - **KEY for term structure**
3. **`vxo_close`** - Old VXO (✅ Have) - Alternative volatility measure
4. **`vix_term_structure`** - VXVCLS / VIXCLS ratio (✅ Can calculate)
5. **`vix_term_slope`** - VXVCLS - VIXCLS (absolute difference)
6. **`vix_contango_flag`** - VXVCLS > VIXCLS (1 if contango, 0 if backwardation)
7. **`vix_backwardation_flag`** - VXVCLS < VIXCLS (1 if backwardation, 0 if contango)

**Additional VIX Features:**

8. **`vix_percentile_1y`** - VIX percentile vs last year
9. **`vix_percentile_3y`** - VIX percentile vs last 3 years
10. **`vix_momentum_5d`** - VIX rate of change (5-day)
11. **`vix_momentum_20d`** - VIX rate of change (20-day)
12. **`vix_regime`** - LOW/MED/HIGH/PANIC based on percentile
13. **`vol_risk_premium`** - VIX minus realized MES vol (20d)
14. **`vix_spike_flag`** - VIX up >20% in single day
15. **`vix_mean_reversion_signal`** - VIX >30 historically mean reverts

**✅ We now have proper VIX term structure via VXVCLS!**

---

## Implementation

**In `features.mes_volatility_daily` view:**

```sql
-- VIX spot features
vix_spot = vix_close
vxv_3m = vxv_close  -- 3-Month VIX
vxo_old = vxo_close  -- Old VXO (S&P 100)

-- VIX term structure (PROPER CALCULATION)
vix_term_structure = SAFE_DIVIDE(vxv_close, vix_close)  -- 3M / Spot ratio
vix_term_slope = vxv_close - vix_close  -- Absolute difference
vix_contango_flag = CASE WHEN vxv_close > vix_close THEN 1 ELSE 0 END
vix_backwardation_flag = CASE WHEN vxv_close < vix_close THEN 1 ELSE 0 END

-- VIX percentile features
vix_percentile_1y = PERCENT_RANK() OVER (ORDER BY vix_close ROWS BETWEEN 252 PRECEDING AND CURRENT ROW)
vix_percentile_3y = PERCENT_RANK() OVER (ORDER BY vix_close ROWS BETWEEN 756 PRECEDING AND CURRENT ROW)
vix_momentum_5d = (vix_close - LAG(vix_close, 5)) / LAG(vix_close, 5)
vix_momentum_20d = (vix_close - LAG(vix_close, 20)) / LAG(vix_close, 20)

-- VIX regime
vix_regime = CASE
    WHEN vix_percentile_1y < 0.4 THEN 'LOW_VOL'
    WHEN vix_percentile_1y < 0.7 THEN 'MED_VOL'
    WHEN vix_percentile_1y < 0.9 THEN 'HIGH_VOL'
    ELSE 'PANIC_VOL'
END

-- Vol risk premium
vol_risk_premium = vix_close - mes_realized_vol_20d

-- VIX spike detection
vix_spike_flag = CASE WHEN (vix_close - LAG(vix_close, 1)) / LAG(vix_close, 1) > 0.2 THEN 1 ELSE 0 END

-- Mean reversion signal
vix_mean_reversion_signal = CASE WHEN vix_close > 30 THEN 1 ELSE 0 END
```

---

## Summary

**What we have:**
- ✅ `VIXCLS` (spot VIX) from FRED
- ✅ `VXVCLS` (3-Month VIX) from FRED - **KEY for term structure**
- ✅ `VXOCLS` (Old VXO) from FRED - Alternative volatility measure
- ✅ Realized MES volatility (from Databento)
- ✅ Historical VIX patterns

**What we don't have (and don't need):**
- ❌ VIX9D (not in FRED, not needed - have VXVCLS)
- ❌ VIX3M (not in FRED, not needed - have VXVCLS)
- ❌ VX.FUT (not in subscription, not needed - have VXVCLS)

**Solution:**
- ✅ **Use VXVCLS for proper VIX term structure calculation**
- ✅ Calculate `vix_term_structure = VXVCLS / VIXCLS`
- ✅ This provides institutional-grade term structure signal
- ✅ No additional data sources required

---

**Status:** ✅ **PROPER VIX TERM STRUCTURE AVAILABLE - READY FOR MES IMPLEMENTATION**

**Update:** VXVCLS (3-Month VIX) is now available from FRED, providing proper term structure calculation without needing VX.FUT or VIX3M.

