# BigQuery Dependency Manifest
**Generated:** 2025-11-17 17:16:20
**Purpose:** Refactoring checklist for FRESH_START migration

---

## Views Referencing Legacy Tables

**Total:** 12 views

| Dataset | View Name | Legacy Tables Referenced |
|---------|-----------|--------------------------|
| models_v4 | vw_arg_crisis_score | production_training_data, models_v4.production_training_data |
| signals | vw_bear_market_regime | forecasting_data_warehouse.soybean_oil_prices |
| signals | vw_biofuel_policy_intensity | forecasting_data_warehouse.soybean_oil_prices |
| signals | vw_biofuel_substitution_aggregates_daily | forecasting_data_warehouse.soybean_oil_prices |
| signals | vw_geopolitical_aggregates_comprehensive_daily | forecasting_data_warehouse.soybean_oil_prices |
| signals | vw_harvest_pace_signal | forecasting_data_warehouse.soybean_oil_prices |
| signals | vw_hidden_correlation_signal | forecasting_data_warehouse.soybean_oil_prices |
| signals | vw_master_signal_processor | forecasting_data_warehouse.soybean_oil_prices |
| signals | vw_sentiment_price_correlation | forecasting_data_warehouse.soybean_oil_prices |
| signals | vw_supply_glut_indicator | forecasting_data_warehouse.soybean_oil_prices |
| signals | vw_technical_aggregates_comprehensive_daily | forecasting_data_warehouse.soybean_oil_prices |
| signals | vw_trade_war_impact | forecasting_data_warehouse.soybean_oil_prices |

---

## Scheduled Queries (Last 30 Days)

**Total:** 0 queries

No scheduled queries found referencing legacy tables.

---

## Backup Datasets Created

**Total:** 5 backup datasets

- `forecasting_data_warehouse_backup_20251117`
- `models_v4_backup_20251117`
- `training_backup_20251117`
- `features_backup_20251117`
- `raw_intelligence_backup_20251117`

---

## Refactoring Checklist

### Phase 1: View Updates
- [ ] Update all views to reference prefixed tables
- [ ] Test each view after update
- [ ] Verify no broken dependencies

### Phase 2: Scheduled Query Updates
- [ ] Review scheduled queries in Cloud Console
- [ ] Update queries to reference prefixed tables
- [ ] Test scheduled query execution

### Phase 3: Dashboard/API Updates
- [ ] Update dashboard queries
- [ ] Update API endpoints
- [ ] Test end-to-end workflows

