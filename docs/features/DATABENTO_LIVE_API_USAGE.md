---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# DataBento Usage: Historical + Live (CME MDP 3.0)
**Date:** November 20, 2025  
**Summary:** Historical CME data (2010→present) is included with your plan. Live CME is included in the monthly fee. No per‑GB or per‑message charges for standard usage.

---

## 1) Historical Data (15 Years)

**YES — It’s included.**  
**NO — You do NOT pay extra for historical downloads.**

If your plan includes CME Globex MDP 3.0, you automatically get full historical archives for:
- OHLCV (1m / 1h / 1d)
- Trades
- MBP (market‑by‑price)
- TBBO (top of book)
- Other standard GLBX.MDP3 schemas

As long as you stay within the plan and aren’t using an add‑on dataset, historical backfills from 2010 → present cost $0.00.

---

## 2) Live Data (Real‑Time CME)

Your plan includes real‑time CME MDP 3.0 access:
- No per‑message fees
- No per‑GB fees
- Reasonable rate limits

You pay the plan fee (e.g., $179/mo), nothing extra for standard live usage.

Implementation options (both included):
- Intraday replay via Live API (from a timestamp) for quick backfills
- Extended historical (2010→present) via Historical/Live where supported by schema

---

## 3) Not Included (Add‑Ons / Extra Cost)

These are not part of the base CME MDP 3.0 plan:
- **CME Options**: separate add‑on/license (needed for true options‑based IV30)
- **CVOL indices**: sold by CME via DataMine (not in DataBento plans)
- **Non‑CME datasets**: e.g., ICE, Euronext, certain palm oil/OTC FX datasets
- **Extremely heavy API usage**: only if you grossly exceed plan caps

Typical plan caps (for reference; you’re far below):
- >5M messages/month
- >10GB/day cloud usage
- >100k API calls/day

Standard ingestion (5‑minute cron, daily backfills) stays well under limits.

---

## 4) Volatility Implications (Options Add‑On Conditional)

- If the CME options add‑on is ENABLED (this account):
  - ✅ ZL/ES/MES option chains via parent symbology (`OZL.OPT`, `ES.OPT`, `MES.OPT`, etc.)
  - ✅ IV30 / IV surface / skew are available to compute
  - ❌ CVOL benchmark is not used (discontinued)

- If the options add‑on is NOT enabled:
  - ❌ No option chains (e.g., `ES.OPT` resolves to error)
  - ❌ No IV30 / IV surface / skew / dealer gamma
  - ❌ No CVOL benchmark (discontinued)

What we **can** and **should** run right now (all included, real data):

- Realized volatility (1m/5m intraday + 5/10/20/60/120-day daily)
- Parkinson / Garman-Klass / Yang-Zhang estimators
- Range-based and vol-of-vol signals
- VIX (FRED), FX vol (BRL/CNY), CL vol, rates vol
- Regime overlays (vol regime calendar, crush spread vol, oilshare vol)

Effect on architecture:

- Big 8 Volatility Pillar runs futures + macro vol for robustness, with optional options‑based IV30 overlay where entitled
- All existing models / dashboards stay online
- If options add-on is off, IV30 remains disabled; CVOL is discontinued regardless of add‑on

---

## 5) Quick Implementation Snippets

### Client Initialization
```python
import databento as db

# Live client
client = db.Live(key=api_key)
```

### Subscribing with Replay
```python
# Subscribe with start time for intraday replay (historical → present)
client.subscribe(
    dataset='GLBX.MDP3',
    schema='mbo',
    stype_in='parent',
    symbols='ZL.FUT',
    start='2025-11-20T00:00:00',
)

# Start session
client.start()

# Collect records
for record in client:
    # Process records
    pass

# Stop session
client.stop()
```

---

## 6) Key Handling (No Plaintext)

- Store via macOS Keychain (preferred) or server env var
- Never commit keys to the repo
- Example (Keychain):
  - security add-generic-password -a default -s cbi-v14.DATABENTO_API_KEY -w '<key>' -U
  - export DATABENTO_API_KEY="$(security find-generic-password -a default -s cbi-v14.DATABENTO_API_KEY -w)"

---

## 7) Final Answer

- Does the 15 years of historical CME data cost extra? **NO — included**
- Does live CME market data cost beyond the monthly plan? **NO — included**
- What might cost extra? **CME options add-on, CVOL indices, non‑CME venues, extreme overages**
- Can we compute IV30/CVOL right now? **NO — options license required**
- Can we run a futures-only volatility pillar? **YES — fully covered**

You’re safe to run: daily historical backfills during testing, 5‑minute real‑time ingestion, and BigQuery batch loads — without incurring per‑call/GB charges.

Internal note: We still follow the project’s cost guardrail (no unapproved historical pulls outside the plan), even though DataBento does not charge extra for historical under this plan.

---

## References

- DataBento Live API Docs: https://docs.databento.com/live
- Intraday Replay: https://docs.databento.com/live/intraday-replay
- Weekly Replay: https://docs.databento.com/live/intraday-replay#weekly-session-replay

---

**Status:** ✅ Updated to use Live API only
