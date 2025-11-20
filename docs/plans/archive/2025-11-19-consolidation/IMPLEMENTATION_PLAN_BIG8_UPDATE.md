---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

<!-- 5889752d-95c9-4b72-916a-b4b991fa0bf8 3e67e1a8-f105-4e46-ade4-d8b939edd4f6 -->
# Big 8 Labor Elevation Plan

## Views to Update (all us-central1)

### 1. `neural.vw_chris_priority_regime_detector`

- Add `feature_labor_stress` sourced from existing ICE/labor inputs (`ice_labor_shortage_risk_score`, labor sentiment, port/rail strike feeds)
- Add `labor_override_flag` (TRUE when labor pilllar exceeds threshold)
- Preserve existing Big 4 fields

### 2. `api.vw_ultimate_adaptive_signal`

- Join the detector above instead of the older Big 7 view
- Surface all eight pillars + `labor_override_flag`
- CROSS JOIN:
  - `performance.vw_forecast_performance_tracking` for MAPE metrics
  - `performance.vw_soybean_sharpe_metrics` for Sharpe/portfolio metrics
- Keep existing column names/horizons intact

### 3. `performance.vw_soybean_sharpe_metrics`

- Add optional labor slice:
  - `labor_sharpe_1week` filtered by labor driver or override flag
- Keep existing columns untouched

## Documentation Touch-up

- In the naming architecture plan, list the Big 8 pillars explicitly (VIX, Harvest, China, Tariff, ICE/Labor, Geopolitical, Biofuel, Hidden Correlations) without the old “Big Seven” phrasing

## Guardrails

- No new tables or datasets
- Everything remains in us-central1
- `CREATE OR REPLACE VIEW` only, so changes are reversible

## Verification

- Each view: `SELECT COUNT(*)` sanity check
- `api.vw_ultimate_adaptive_signal` should return exactly one row (latest signal) with new labor fields
- Ensure Sharpe/ MAPEs populate by verifying non-null results

### To-dos

- [x] Audit ingestion pipeline for broken dependencies and imports
- [x] Check BigQuery table references and schema mismatches
- [x] Verify cron job configurations and paths
- [x] Examine data lineage and flow breaks
- [x] Check API keys and authentication issues
- [x] Identify error handling gaps and silent failures
- [x] Update NAMING_ARCHITECTURE_PLAN.md: Remove _v{ver} from Pattern 5, update examples to show no version on first training
- [x] Update model_saver.py: Make version parameter optional (default None), only append version if provided
- [x] Update train_tree.py: Remove version="v001" from save_model_with_metadata calls
- [x] Update tree_models.py: Remove _v001 from model subdirectory paths
- [x] Search and update all other training scripts that use version parameter
- [x] Update quick reference examples in naming plan to show no version on first training
