// Archived on 2025-10-13. See CONSOLIDATED_FORWARD_PLAN.md for the active plan.

# Dashboard Data Requirements Analysis (CBI-V14)
_Generated: 2025-10-11_

## Purpose
Map the 4-page dashboard blueprint to existing BigQuery infrastructure and identify gaps before performing view cleanup.

---

## Page 1: Dashboard (Chris's Daily Decision Page)

### Required Data Sources (from blueprint)
| Data Source | Current Status | Location | Notes |
|------------|----------------|----------|-------|
| `zl_data` | ⚠️ NEEDS REBUILD | `forecasting_data_warehouse.soybean_oil_prices` | Yahoo Finance source unreliable; need CME/TradingEconomics |
| `fed_rates_real_time` | ✅ EXISTS | Covered by `vw_fed_rates_realtime` | Check if needed in curated |
| `tariff_conflicts` | ❌ MISSING | — | Need GDELT + USTR ingestion |
| `china_relations` | ⚠️ PARTIAL | `gdelt_china_intelligence` table exists | May need expansion |
| `procurement_signals` | ❌ MISSING | — | Feature engineering required |
| `china_crushing_margins` | ❌ MISSING | — | Need China soybean/meal/oil prices |
| `storage_capacity` | ❌ MISSING | — | USDA data source |
| `cftc_cot_reports` | ❌ MISSING | — | Free CFTC API |

### Required Views/Features
- Mood ring indicator, 30-day AI projection, volume spikes, scenario sliders, cost table.

## Page 2: Sentiment
... (archived content retained)






