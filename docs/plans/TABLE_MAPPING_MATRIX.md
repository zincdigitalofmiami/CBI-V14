# CBI-V14: Table Mapping Matrix

**Last Updated**: November 14, 2025
**Status**: DRAFT

This document outlines the migration plan for all legacy BigQuery tables and views to the new, standardized data architecture.

---

### New Dataset Architecture

| Dataset                | Purpose                                             |
| ---------------------- | --------------------------------------------------- |
| `raw_intelligence`     | Raw, unprocessed source data.                       |
| `features`             | Engineered features for modeling.                   |
| `training`             | Final, versioned training sets.                     |
| `predictions`          | Model outputs and generated signals.                |
| `monitoring`           | Performance metrics, data quality, model registry.  |
| `archive`              | Snapshots and retired legacy objects.               |
| `vegas_intelligence`   | Data for the "Vegas Intel" sales dashboard.         |

---

### Naming Convention

`asset_function_scope_regime_horizon`

-   **asset**: `zl` (Soybean Oil)
-   **function**: `features`, `training`, `predictions`, etc.
-   **scope**: `full` (research), `prod` (production), or model type.
-   **regime**: `crisis`, `tradewar`, `all`, etc.
-   **horizon**: `1w`, `1m`, `3m`, etc.

---

## Migration Mapping

| Legacy Dataset                  | Legacy Table/View Name                          | Type  | New Dataset            | New Table/View Name                                   | Action      | Notes                                                              |
| ------------------------------- | ----------------------------------------------- | ----- | ---------------------- | ----------------------------------------------------- | ----------- | ------------------------------------------------------------------ |
| **api**                         | `current_forecasts`                             | TABLE | `predictions`          | `zl_predictions_prod_all_latest`                      | Migrate     | Current live forecasts.                                            |
|                                 | `vw_market_intelligence`                        | VIEW  | `predictions`          | `vw_zl_market_intelligence`                           | Recreate    | View for market signals.                                           |
| **forecasting_data_warehouse**  | `baltic_dry_index`                              | TABLE | `raw_intelligence`     | `shipping_baltic_dry_index`                           | Migrate     | Baltic Dry Index data.                                             |
|                                 | `biofuel_policy`                                | TABLE | `raw_intelligence`     | `policy_biofuel`                                      | Migrate     | Biofuel policy information.                                        |
|                                 | `china_soybean_imports`                         | TABLE | `raw_intelligence`     | `trade_china_soybean_imports`                         | Migrate     | China's soybean import data.                                       |
|                                 | `crude_oil_prices`                              | TABLE | `raw_intelligence`     | `commodity_crude_oil_prices`                          | Migrate     | Crude oil price data.                                              |
|                                 | `economic_indicators`                           | TABLE | `raw_intelligence`     | `macro_economic_indicators`                           | Migrate     | General macroeconomic indicators.                                  |
|                                 | `feature_metadata`                              | TABLE | `features`             | `feature_metadata`                                    | Migrate     | Metadata for features. Should live with the features.              |
|                                 | `news_intelligence`                             | TABLE | `raw_intelligence`     | `news_sentiments`                                     | Migrate     | Processed news and sentiment data.                                 |
|                                 | `palm_oil_prices`                               | TABLE | `raw_intelligence`     | `commodity_palm_oil_prices`                           | Migrate     | Palm oil price data.                                               |
|                                 | *... (other raw data tables) ...*               | TABLE | `raw_intelligence`     | *`source_name`*                                       | Migrate     | All other raw tables to be migrated.                               |
|                                 | `ai_metadata_summary`                           | VIEW  | `monitoring`           | `vw_ai_metadata_summary`                              | Recreate    | View for AI metadata.                                              |
| **models**                      | `enhanced_market_regimes`                       | TABLE | `features`             | `market_regimes`                                      | Migrate     | Table defining market regimes.                                     |
|                                 | `training_data_complete_all_intelligence`       | TABLE | `training`             | `zl_training_full_all_1w`                             | Migrate     | Example of a comprehensive training table.                         |
|                                 | `vw_crush_margins`                              | VIEW  | `features`             | `vw_zl_crush_margins`                                 | Recreate    | View for calculating crush margins.                                |
|                                 | *... (other feature/training tables) ...*       | TABLE | `features`/`training`  | *`asset_function_scope_regime_horizon`*               | Migrate     | Other tables to be mapped.                                         |
| **models_v4**                   | `crisis_2008_historical`                        | TABLE | `training`             | `zl_training_full_crisis_all`                         | Migrate     | Historical training data for the 2008 crisis.                      |
|                                 | `pre_crisis_2000_2007_historical`               | TABLE | `training`             | `zl_training_full_precrisis_all`                      | Migrate     | Historical training data.                                          |
|                                 | `recovery_2010_2016_historical`                 | TABLE | `training`             | `zl_training_full_recovery_all`                       | Migrate     | Historical training data.                                          |
|                                 | `trade_war_2017_2019_historical`                | TABLE | `training`             | `zl_training_full_tradewar_all`                       | Migrate     | Historical training data.                                          |
|                                 | `trump_rich_2023_2025`                          | TABLE | `training`             | `zl_training_prod_trump_all`                          | Migrate     | Current regime training data.                                      |
|                                 | `production_training_data_1w`                   | TABLE | `training`             | `zl_training_prod_all_1w`                             | Migrate     | Production training data for 1-week horizon.                       |
|                                 | `production_training_data_1m`                   | TABLE | `training`             | `zl_training_prod_all_1m`                             | Migrate     | Production training data for 1-month horizon.                      |
|                                 | `production_training_data_3m`                   | TABLE | `training`             | `zl_training_prod_all_3m`                             | Migrate     | Production training data for 3-month horizon.                      |
|                                 | `production_training_data_6m`                   | TABLE | `training`             | `zl_training_prod_all_6m`                             | Migrate     | Production training data for 6-month horizon.                      |
|                                 | `production_training_data_12m`                  | TABLE | `training`             | `zl_training_prod_all_12m`                            | Migrate     | Production training data for 12-month horizon.                     |
|                                 | `feature_importance_vertex`                     | TABLE | `monitoring`           | `model_feature_importance`                            | Migrate     | Feature importance from Vertex AI models.                          |
| **neural**                      | `vw_big_eight_signals`                          | VIEW  | `features`             | `vw_zl_signals_bigeight`                              | Recreate    | View for the "Big Eight" signals.                                  |
| **predictions_uc1**             | `vegas_scenarios`                               | TABLE | `vegas_intelligence`   | `sales_scenarios`                                     | Migrate     | From VEGAS_INTEL_SALES_PAGE_ARCHITECTURE.md                        |
|                                 | `vegas_tanker_schedule`                         | TABLE | `vegas_intelligence`   | `sales_delivery_schedule`                             | Migrate     | From VEGAS_INTEL_SALES_PAGE_ARCHITECTURE.md                        |
|                                 | `vegas_customer_history`                        | TABLE | `vegas_intelligence`   | `sales_customer_history`                              | Migrate     | From VEGAS_INTEL_SALES_PAGE_ARCHITECTURE.md                        |
| **signals**                     | `vw_comprehensive_signal_universe`              | VIEW  | `features`             | `vw_zl_features_full_all_all`                         | Recreate    | This was the master view of all signals. Becomes the 'full' feature set. |
|                                 | *... (all other `vw_*` views) ...*              | VIEW  | `features`             | `vw_zl_*`                                             | Recreate    | All other signal views will be recreated in the `features` dataset. |
| *Unmapped/Legacy*               | *... (any remaining tables) ...*                | -     | `archive`              | *`legacy_dataset_name`*\_*`table_name`*                | Archive     | Any tables not explicitly mapped will be archived.                 |

---

### Action Plan

1.  **Review & Refine**: The project team will review this DRAFT and refine the mappings.
2.  **Script Development**: A script will be created to perform the `Migrate` and `Recreate` actions.
3.  **Execution**: The migration script will be run in a controlled environment.
4.  **Validation**: Post-migration, data and views will be validated against the old structure.
5.  **Decommission**: Once validated, legacy datasets will be backed up to the `archive` and then decommissioned.
