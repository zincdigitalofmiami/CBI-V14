# GPT‑5 • READ FIRST (CBI‑V14)

**Last Updated:** 2025‑11‑15  
**Region:** `us-central1` only (no cross‑region joins)  
**Datasets (active/canonical):** `raw_intelligence`, `features`, `training`, `predictions`, `monitoring`, `archive`, `api`, `signals`, `neural`, `yahoo_finance_comprehensive`  
**Do Not Change:** Dataset names, region, Option‑3 naming; do not create physical tables unless explicitly instructed.

---

## What matters

1) **Naming (Option‑3) — stable**

- `zl_training_{scope}_{regime}_{horizon}`  
  e.g., `training.zl_training_prod_allhistory_1m`

- `zl_predictions_{scope}_{regime}_{horizon}`  
  e.g., `predictions.zl_predictions_prod_all_latest`

2) **Big‑8 (signals) — authoritative**

- VIX stress
- Harvest pace / weather
- China relations / trade policy
- Tariff probability
- Geopolitical volatility
- Biofuel policy impact
- Hidden correlation / cross‑asset structure
- **ICE/Labor disruption (the 8th pillar)**

3) **Confidence & performance**

- **MAPE** source of truth: `performance.vw_forecast_performance_tracking`  
- **Sharpe (soybean‑specific)** source of truth: `performance.vw_soybean_sharpe_metrics`  
- API must *expose* both via `api.vw_ultimate_adaptive_signal` (see SQL below).

---

## Guardrails for any changes

- **Only** `CREATE OR REPLACE VIEW` in the datasets above.
- **No** new datasets; **no** cross‑region references; **no** hidden temp tables left behind.
- **Join to Big‑8 through** `neural.vw_big_eight_signals` and the **labor detector** view (`neural.vw_chris_priority_regime_detector`).
- **Do not** reintroduce “big seven”—labor/ICE is mandatory.

---

## Where key logic lives (for Cursor & dashboards)

- **Ultimate signal assembly (API baseline):** see “Ultimate Signal Calculation Framework”. If you find `vw_big_seven_signals` in legacy SQL, **replace with** `vw_big_eight_signals` and add labor flags. :contentReference[oaicite:0]{index=0}
- **Dashboard weather/geo views:** heatmaps, anomaly detection, and animation components are already specified for front‑end. :contentReference[oaicite:1]{index=1}
- **Substitution economics (soy vs palm/canola) UI:** dynamic arbitrage + opportunity overlays. :contentReference[oaicite:2]{index=2}
- **News & sentiment buckets:** ready‑to‑wire taxonomy + scoring/half‑life rules (China, Argentina, Brazil, biofuel, chokepoints, labor, etc.). :contentReference[oaicite:3]{index=3}
- **MAPE computation + API surfacing:** definitions, BQ view, and API injection pattern. :contentReference[oaicite:4]{index=4}
- **Soybean‑specific Sharpe (seasonality/regime aware):** BQ view, monitoring, API integration, and UX mapping. :contentReference[oaicite:5]{index=5}

---

## Known gaps to keep in mind

- 2000–2019 backfill exists (BigQuery & external drive) but current training prod tables are 2020+; when building training surfaces, **join the historical spine** and **COALESCE pre‑policy fields** (biofuel/politics) to safe defaults.
- **Weights**: baseline weights come from `training.regime_weights` (50→5000). Adaptive weights are **pre‑calc offline** on the Mac; only publish vetted columns to BQ.

---

## Quick runbooks

- **Expose MAPE/Sharpe in API:** use the view updates provided below.
- **Labor pillar:** create/update `neural.vw_chris_priority_regime_detector` and then ensure `api.vw_ultimate_adaptive_signal` selects the labor flags/driver.
- **Feature surface upgrades:** never widen physical tables in BQ; widen features offline, persist to Parquet, and present via views.

Why these pointers: The API/UX wiring for signal assembly, MAPE, Sharpe, weather/geo and substitution components are already specified in your internal specs. This page anchors new chat agents to the authoritative sources and prevents regressions to “Big 7.”

---

## Cursor quick-reference — Sharpe ratios & where they’re used

- **Calculation:** `performance.vw_soybean_sharpe_metrics` (seasonal‑adjusted Sharpe; crisis/normal regime Sharpe; weather‑driven Sharpe; cumulative return; drawdown; win rate; profit factor; seasonal best). This is the only place Cursor should compute Sharpe.
- **Surfacing (API):** selected fields are joined into `api.vw_ultimate_adaptive_signal` (see SQL above) so the dashboard gets Sharpe/portfolio metrics with every forecast payload.
- **Monitoring:** optional background job updates `performance.soybean_sharpe_historical_tracking` for time‑series charts; thresholds are agricultural‑specific (lower than equities).

**Dashboard usage:**

- Header badges and seasonal advantage indicator read straight from `soybean_adjusted_sharpe`, `win_rate_pct`, `soybean_profit_factor`, and `best_seasonal_period`.
- Seasonal overlays and USDA markers align with the UI spec; wire to the historical Sharpe tracking series if you enable it.

---

## Verification queries (paste-run)

**Confirm Big‑8 + labor is wired**

```
SELECT table_name, view_definition
FROM `cbi-v14.neural.INFORMATION_SCHEMA.VIEWS`
WHERE table_name IN ('vw_big_eight_signals','vw_chris_priority_regime_detector');
```

**API contains MAPE & Sharpe fields**

```
SELECT *
FROM `cbi-v14.api.vw_ultimate_adaptive_signal`
LIMIT 5;
```

**Single-row guarantees (MAPE/Sharpe views)**

```
SELECT COUNT(*) AS rows_mape FROM `cbi-v14.performance.vw_forecast_performance_tracking`;
SELECT COUNT(*) AS rows_sharpe FROM `cbi-v14.performance.vw_soybean_sharpe_metrics`;
```

**No cross-region joins**

Ensure every referenced object is in us-central1 (spot check via INFORMATION_SCHEMA if needed).

---

## Dashboard notes (for devs)

- Weather & anomaly UI: keep the choropleth/anomaly/time-animation scaffolds; use us-central1 data sources.
- Substitution economics panel: the switching-point chart is already spec’d; feed with current ZL/CPO/Canola series from `yahoo_finance_comprehensive` and price parity logic.
- News/Sentiment buckets: wire the classifier to the 16 buckets + heuristics for impact/half-life and shock priors (labor/chokepoints included).

---

## Commit plan (minimal and reversible)

- `docs/GPT-5_READ_FIRST.md` (new)
- `sql/views/neural/vw_chris_priority_regime_detector.sql` (new)
- `sql/views/api/vw_ultimate_adaptive_signal.sql` (updated)

**Commit message:**

```
docs: add GPT‑5_READ_FIRST; neural: add labor detector view; api: surface MAPE & soybean‑Sharpe; enforce Big‑8 usage (labor/ICE included); us-central1 only
```

**Notes on provenance and alignment**

- Ultimate signal assembly and horizon construction come from your “Ultimate Signal Calculation Framework”; this update replaces any `vw_big_seven_signals` dependency with Big‑8 and introduces labor flags/driver for attribution.
- MAPE computation and API exposure pattern follow your MAPE implementation guide; the API section above mirrors that design with CROSS JOIN to a single-row performance view.
- Soybean-specific Sharpe (seasonality/regime aware) is taken from your Sharpe guide and is the only Sharpe source Cursor should reference; API wiring mirrors that spec.
- UI hooks for weather heatmaps/anomalies/time-animation and substitution economics are codified in your dashboard specs and should not be reinvented.
- News/Sentiment taxonomy and event-impact heuristics remain the canonical classifier seed list.



