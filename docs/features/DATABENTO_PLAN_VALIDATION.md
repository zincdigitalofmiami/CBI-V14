---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# DataBento Plan Validation
**Date:** November 20, 2025  
**Plan:** CME Globex MDP 3.0 Standard  
**Status:** ✅ Validated — Futures + CME Options Add‑On ENABLED on this account. ❌ CVOL not included.

---

## Plan Details

### ✅ Confirmed Access
- **Dataset:** GLBX.MDP3 (CME Globex Market Data Platform 3.0)
- **Historical Coverage:** 15 years (June 6, 2010 - present)
- **Products:** 
  - ✅ All **futures** on CME, CBOT, NYMEX, COMEX
  - ✅ **CME Options on futures** (ES/MES/ZL/ZS/ZM/FX, Treasuries) — add‑on enabled for this account
- **Access Method:** Live API with extended historical replay
- **Cost:** No download charges (included in Standard subscription)

### ✅ Options Access (Enabled)
- Options on futures are accessible (parent symbology):
  - ES.OPT, MES.OPT
  - OZL.OPT (Soybean Oil), OZS.OPT (Soybeans), OZM.OPT (Soybean Meal)
  - Treasury and FX options per entitlement
- Impact: IV30, options surfaces, skew are available to compute.
- ❌ **CVOL indices:** Sold by CME via DataMine (not in DataBento plans)

---

## Available Schemas (Futures Only)

### Futures-Relevant Schemas
- ✅ **ohlcv-1d** - Daily OHLCV bars
- ✅ **ohlcv-1h** - Hourly bars
- ✅ **ohlcv-1m** - 1-minute bars
- ✅ **trades** - Trade data
- ✅ **mbo** - Market-by-order (bid/ask quotes) - **For futures only**
- ✅ **tbbo** - Top-of-book (best bid/offer)
- ✅ **statistics** - Market statistics
- ✅ **definition** - Contract definitions (for futures contracts)

### ✅ Options Schemas (Available with add‑on)
- Options data (definitions, trades, OHLCV where supported) is accessible via GLBX.MDP3 using `stype_in='parent'`.
- Examples: `definition`, `ohlcv-1d`, `trades`, `mbo` (where supported by venue/schema)
- ❌ **CVOL indices:** Not available (requires CME DataMine)

---

## Historical Data Access

### Method: Historical Access (Included)
- **No Extra Cost:** Historical futures data is included with the CME MDP 3.0 plan
- **Coverage:** Full 15 years (2010‑06‑06 to present) for **futures only**
- **Implementation:**
  - Preferred: Live API extended replay with a historical `start` timestamp
  - Also available: Historical endpoints for included datasets (no extra charge under plan limits)
- **Example (Futures):**
  ```python
  client.subscribe(
      dataset='GLBX.MDP3',
      schema='ohlcv-1d',
      symbols='ZL.FUT',  # Futures symbol, NOT ZL.OPT
      start='2010-06-06T00:00:00',  # Full 15-year history available
  )
  ```
- **Note:** Options backfills and live pulls use the enabled add‑on on this account.

### Important Notes
- ✅ Historical futures data is included; Live API replay recommended for simplicity
- ✅ Historical API endpoints for included datasets are allowed under plan limits
- ❌ Options backfills require options add‑on; CVOL requires CME DataMine
- ✅ 15 years of data available (futures only)

---

## Validation Results

### ✅ Dataset Access
- GLBX.MDP3: Available
- All required schemas: Available
- Historical range: ~15 years confirmed

### ✅ API Key Handling (No Plaintext)
- Store in macOS Keychain or server env; never commit keys
- Example (Keychain):
  - security add-generic-password -a default -s cbi-v14.DATABENTO_API_KEY -w '<key>' -U
  - export DATABENTO_API_KEY="$(security find-generic-password -a default -s cbi-v14.DATABENTO_API_KEY -w)"

### ✅ Connection
- Live API: ✅ Working
- Historical API (metadata): ✅ Working
- Authentication: ✅ Successful

---

## Implementation Status

### ✅ Completed (Futures-Only)
1. Live API client initialization
2. Extended historical replay support for futures
3. Futures data fetching (OHLCV, trades, MBO)
4. Realized volatility calculations (RV 5/10/20/60/120-day)
5. Futures-based volatility proxies (Parkinson, Garman-Klass, Yang-Zhang)
6. VIX integration (from FRED) for macro volatility overlay

### ✅ Options Status (Enabled)
1. ✅ **ES/MES/ZL/ZS/ZM/FX IV30:** Enabled (compute via options chains)
2. ❌ **CVOL calculation:** BLOCKED (requires CME DataMine)
3. ✅ **Options surface modeling:** Enabled for entitled products

### ✅ Active Volatility Pillar (Futures-Based)
The system uses **futures-only** volatility measures:
- Realized volatility (multiple horizons)
- Futures-based estimators (Parkinson, GK, YZ)
- VIX overlay (from FRED)
- Volatility regimes (from regime calendar)
- Cross-asset volatility (CL, BRL, CNY)

---

## Usage

### Futures Data Collection
```bash
# Collect futures OHLCV data
python3 scripts/ingest/collect_databento_futures.py

# Calculate volatility features (futures-based)
python3 scripts/features/feature_calculations.py
```

### Historical Backfill (Futures Only)
The system supports full 15‑year historical backfill for **futures**:
- Start date: 2010-06-06
- End date: Present
- All dates accessible via Live API extended replay
- **Note:** Options backfill requires separate options license

---

**Status:** ✅ Plan validated for futures + options add‑on. ❌ CVOL remains out‑of‑scope.
