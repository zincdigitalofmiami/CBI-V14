---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# IV30 (Options‑Based) Implementation Status
**Date:** November 20, 2025  
**Status:** ✅ ACTIVE – CME options add‑on ENABLED (ES/MES + Soy Complex via OZL/OZS/OZM). ❌ CVOL not included.

---

## CURRENT STATUS

CME options on futures are licensed on this account.  
This covers ES/MES and the soybean complex (OZS, OZM, OZL), plus FX/Rates per entitlement.

### What This Means:

- ✅ **ES/MES/ZS/ZM/ZL IV30:** Can be calculated (options chains available)
- ❌ **CVOL:** Not available (CME DataMine only)
- ✅ **Options Surface:** Available for entitled products (strikes/expirations)

---

IV30 scripts are enabled for entitled products.  
Options collection jobs may be scheduled post‑close with quality guardrails.

---

## WHAT YOU CAN COMPUTE NOW (VALID, OPTIONS‑FREE)
Using only futures + agency data you already have:

- Realized volatility: RV(5/10/20/60‑day); intraday RV for MES microstructure
- Futures‑based vol proxies: Parkinson, Garman‑Klass, Rogers‑Satchell, Yang‑Zhang
- Volatility regimes: ZL/MES/cross‑asset regime classification
- Macro vol overlay: VIX (FRED), DXY/FX vol, rates (DGS10/DFF) vol
- Crush/oilshare vol: ZL/ZM/ZS spread vol, crush margin vol

These are real, exchange‑based/agency series. No placeholders. Often highly predictive for ZL.

---

## Quality Guardrails

### 1. Spread Filter
- **Rule:** Discard if `(ask - bid) / mid_price > 20%`
- **Purpose:** Remove illiquid or stale quotes

### 2. Staleness Filter
- **Rule:** Discard quotes older than 5 minutes
- **Purpose:** Ensure quotes reflect current market conditions

### 3. Strike Coverage
- **Rule:** Require ±20% moneyness coverage around ATM
- **Purpose:** Ensure sufficient data for reliable IV calculation

### 4. Quality Flags
- **`ok`**: ≥5 observations, good ATM coverage, moneyness span ≥20%
- **`sparse`**: ≥5 observations but insufficient coverage
- **`fail`**: <5 observations or calculation failed

---

## WHAT YOU CANNOT COMPUTE TODAY (STILL OUT OF SCOPE)

- ❌ CVOL (CME benchmark index)
- ✅ IV30/surface/skew are available (options add‑on enabled)

### Ongoing:
- Schedule options jobs with prudent rate limits; maintain futures‑based vol pillar as a parallel/backup signal

---

## CONSEQUENCES FOR CBI‑V14

- No model/pipeline breaks
- Big8 stays intact; volatility pillar uses futures‑derived vol + VIX
- Regime classifier and price forecasts continue to work

---

## CLEAN SUBSTITUTE: FUTURES‑BASED VOL PILLAR

Volatility inputs (all real):
- VIX (FRED)
- Realized Vol (ZL 5/10/20/60‑day)
- Parkinson HL / Garman‑Klass / RS / Yang‑Zhang
- Vol regime (from regime calendar)
- CL volatility (energy linkage)
- BRL/CNY volatility (FX pressure)

---

## IF YOU WANT IV30/CVOL LATER

Option A: Add CME options via DataBento (add‑on) → unlocks chains/surface/IV30  
Option B: CME DataMine (official CVOL + option history) → more expensive  
Option C: Broker feed (live options only) → not suitable for 25‑year window

---

## Compliance

✅ **Real Sources Only:** All data from DataBento GLBX exchange quotes  
✅ **No Synthetic Data:** No placeholders, no fake values  
✅ **Reproducible:** All calculations documented and logged  
✅ **Transparent:** Modeling choices explicitly stated in methodology doc

---

## RECOMMENDATION (FINAL)

For now:
- Use realized vol family + futures‑based proxies + VIX/FX/rates vol + regime scoring alongside options‑based IV30 where available

If CVOL is licensed later via CME DataMine:
- Add CVOL features; no pipeline disruption needed—add as a new feature domain.

---

**Status:** ⛔ Blocked (options required). Futures‑based volatility pillar is ACTIVE.

---

## Provider Coverage Snapshot (for context)

- Asset classes: **Futures**; **Options on futures** (options require add‑on; not in current plan)
- Venues: **CME, CBOT, NYMEX, COMEX** (CME Globex MDP 3.0)
- Available history (futures): **~15 years** (2010‑06‑06 → present)
- Symbol universe (provider‑wide): **650,000+** instruments (your plan covers futures subset)

---

## References

- DataBento examples — Algo trading / Machine learning (Python)
  - https://databento.com/docs/examples/algo-trading/machine-learning?historical=python&live=python&reference=python
- DataBento venues & datasets — GLBX MDP 3.0 (CME/CBOT/NYMEX/COMEX)
  - https://databento.com/docs/venues-and-datasets/glbx-mdp3?historical=python&live=python&reference=python

### Find Options-on-Futures Datasets (How-To)
- DataBento guide: https://databento.com/docs/examples/options/options-on-futures-introduction/finding-an-options-on-futures-dataset?historical=python&live=python&reference=python

Quick verification snippet (definitions via parent symbology):
```python
import databento as db

client = db.Historical(api_key)
syms = ["ES.OPT", "MES.OPT", "OZL.OPT", "OZS.OPT", "OZM.OPT"]

data = client.timeseries.get_range(
    dataset="GLBX.MDP3",
    schema="definition",
    stype_in="parent",
    symbols=syms,
    start="2025-01-01",
    end="2025-11-20",
)
df = data.to_df()
print(df[["raw_symbol", "security_type", "underlying", "expiration", "strike_price"]].head())
```

CLI helper: `scripts/reference/verify_options_access.py` validates access and reports counts for ES/MES/OZL/OZS/OZM.
