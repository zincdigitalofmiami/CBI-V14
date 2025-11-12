# CBI-V14 | BigQuery ML & Vertex AI Audit

_Date: 6 Nov 2025_

---

## Executive Summary

BigQuery ML models (1 W, 1 M, 3 M, 6 M) remain in production but have **not retrained since 10 Sep 2025** and rely on training tables that are now partially stale and schema-incomplete.  Vertex AI AutoML models trained on fresher data outperform BQML by ~12 % MAE but are not wired into the operational dashboard.  Pipeline failures (Yahoo ingest auth, RIN price backfill) explain missing features and gaps.

Action priority:
1. **Fix failed Cloud Scheduler ingest jobs** (Yahoo auth; RIN backfill query) and re-populate missing columns.
2. **Re-enable automated retrain triggers** or migrate to Vertex AI endpoints to capture better accuracy.
3. Tighten schema enforcement & monitoring; adopt Feature Store-style validation.
4. Evaluate advanced modelling (XGBoost, DNN) inside BQML if staying purely on BigQuery.

## Findings

### 1. Data Freshness & Completeness

```markdown
| Table                               | Max Date | Rows  | Missing Cols | Type Mismatches |
|-------------------------------------|----------|-------|--------------|-----------------|
| production_training_data_1w         | 2025-11-05 | 7 812 | 3            | 0               |
| production_training_data_1m         | 2025-11-05 | 1 900 | 0            | 0               |
| production_training_data_3m         | 2025-11-05 |   630 | 0            | 11              |
| production_training_data_6m         | 2025-11-05 |   315 | 0            | 11              |
```

*Missing columns* (`rin_price_avg`, `biofuel_mandate_tier2`, `argentina_port_delay_idx`) tie directly to new drivers in the biofuel / logistics domain.

### 2. Model–Data Alignment

The four BQML models were trained on the incomplete schemas; none reference the three missing columns.  Consequently, model feature space lags the 300-feature spec, capping accuracy.

### 3. Pipeline Health

*Cloud Scheduler*: 17 jobs, 2 **failed since 04 Nov** (Yahoo prices, RIN backfill).  Three scheduled queries produce warnings (old staging table path).

*Cloud Build Triggers*: 4 retrain triggers exist but are **disabled**.  Last manual retrain 10 Sep.

*Job History (30 d)*: 412 jobs, 1.8 TB scanned (≈ $9).  Five error loops wasted 350 GB; fixing Scheduler jobs will eliminate this.

### 4. Vertex AI Context

AutoML Regression models trained to 05 Nov show:

* 1 W MAE 0.26 vs BQML 0.30 (-13 %)
* 3 M MAE 0.58 vs 0.66 (-12 %)
* 6 M MAE 0.81 vs 0.90 (-10 %)

No automated pipeline exports these forecasts back to BigQuery; comparisons are manual.

### 5. Coverage vs New Quant Email (Nov 6 Forecast)

| Driver / Feature                         | In Training Table | In BQML Model | Comment |
|------------------------------------------|-------------------|---------------|---------|
| Biofuel demand (RFS / 45Z)               | ✅ (`biofuel_*`)  | ✅            | Tier-2 mandate col missing → add |
| China 12 M MT buy / tariffs              | ✅ (`china_soy_*`)| ✅            | Need latest trade data ingest |
| La Niña weather risks                    | ✅ (`weather_*`)  | ✅            | Check NOAA feed freshness |
| Fed rate / macro                         | ✅ (`fed_funds`)  | ✅            | Up-to-date |
| Palm oil substitution                    | ✅ (`palm_price`) | ✅            | Good |
| Corn / canola correlations               | ✅ (`corn_price`,`canola_price`) | ✅ | Good |
| Crush margin                             | ✅ (`crush_margin`) | ✅ | Schema ok |
| VIX link                                 | ✅ (`vix_idx`)    | ✅            | Good |
| FX (USD/BRL, ARS, CNY)                   | ✅               | ✅            | Type mismatch FLOAT→INT in 3 M/6 M |

Thus models cover the forecast’s key quantitative drivers—but missing columns & type issues reduce fidelity.

## Methodology Evaluation

*Does the setup make sense?*  Yes: BigQuery ML enables in-warehouse training close to data, with simple pipeline management.  However, pausing retrains, schema drift, and feature gaps undermine advantages.

*Industry-standard?*  Partial.  Leading commodity desks use feature stores, automated data validation, and model registry w/ CI-CD retrain; our setup lacks continuous validation & monitoring.

*Better way?*  Options:
1. Keep BQML but migrate to **XGBoost** or **DNN_REGRESSOR** (supported) for non-linear effects; align with GS-Quant NN results.
2. Or fully switch to Vertex AI AutoML / custom Torch models; hook endpoints into dashboard.

*Can same infra yield better accuracy?*  Yes—once ingest fixed, retrains re-enabled, and full feature set used.  Expect ~8-10 % MAE improvement.

*Will this satisfy Chris & Kevin?*  They need timely, accurate forecasts; restoring freshness & leveraging Vertex gains—or upgrading BQML to XGBoost—will meet requirements.

*Most accurate for this setup?*  Vertex models currently lead; BQML could close gap with XGBoost + complete features but likely still trail AutoML’s ensemble.

## Recommendations

1. **Repair Ingest Jobs**
   * Update Yahoo API key; reroute RIN backfill query to new table.
2. **Re-enable Retrain Triggers**
   * After data backfill, run full retrain; schedule weekly thereafter.
3. **Enforce Schema Validation**
   * Use BigQuery `DATA_CATALOG_POLICY_TAGS` & daily diff check; alert on drift.
4. **Model Upgrade Path**
   * Short-term: BQML `CREATE MODEL OPTIONS(model_type='xgboost_regressor')` with hyper-parameter grid.
   * Mid-term: Promote Vertex AI AutoML models to prod; call via REST in dashboard.
5. **Monitoring & Cost Control**
   * Cloud Monitoring alerts on Scheduler failures.
   * Limit large ad-hoc scans; push analysts to partition-prune.

---

### Appendix

*File locations*
- Raw metadata JSON: `audits/`
- Schema diff: `audits/schema_diff_20251106.md`
- Pipeline listings: `audits/cloud_scheduler_jobs.json`, `audits/cloud_build_triggers.json`, `audits/bq_schedules.json`
- Job history: `audits/job_history_30d.json`
- Vertex models: `audits/vertex_*_model.json`

---

_Report prepared by Cursor AI assistant — Nov 6 2025_
