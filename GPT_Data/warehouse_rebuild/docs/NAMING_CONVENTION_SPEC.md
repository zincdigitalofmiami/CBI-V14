# BigQuery Warehouse Naming Convention Specification

**Date**: November 13, 2025  
**Project**: CBI-V14 Soybean Oil Forecasting Platform  
**Version**: 1.0

## Overview

This document defines the institutional-style naming convention for all BigQuery tables and views in the CBI-V14 warehouse. The convention eliminates ambiguous names and supports systematic growth.

## Naming Pattern

All table names follow this pattern:

```
{asset_class}_{subcategory}_{instrument}_{function}_{frequency}_{environment}
```

### Components

1. **asset_class** (required) – Broad grouping
   - `commodities` – Physical commodities (soybean oil, palm oil, corn, etc.)
   - `fx` – Foreign exchange rates
   - `rates` – Interest rates and treasury instruments
   - `equities` – Stock market indices and individual stocks
   - `intelligence` – News, sentiment, policy, weather, social media
   - `training` – Model training datasets
   - `predictions` – Model outputs and forecasts
   - `monitoring` – Data quality, model performance, alerts
   - `archive` – Historical snapshots and legacy data

2. **subcategory** (required) – Domain-specific grouping
   - For commodities: `agriculture`, `energy`, `metals`
   - For intelligence: `weather`, `policy`, `news`, `sentiment`, `fundamental`
   - For training: `horizon`, `regime`
   - For features: `general`, `biofuel`, `volatility`, `macro`
   - For predictions: `signal`, `horizon`

3. **instrument** (required) – Specific entity
   - Examples: `soybean_oil`, `palm_oil`, `corn`, `wheat`, `china_imports`, `vix`, `dxy`
   - For training: `1w`, `1m`, `3m`, `6m`, `12m` (horizons) or `trump_2023_2025`, `pre_crisis_2000_2007` (regimes)
   - For features: `master`, `rin_proxy`, `volatility_metrics`

4. **function** (required) – Purpose of the table
   - `raw` – Unprocessed data from ingestion
   - `enriched` – Cleaned and validated raw data
   - `features` – Engineered features for modeling
   - `training` – Final training datasets with targets
   - `prediction` – Model forecast outputs
   - `metadata` – Schema, lineage, catalog information

5. **frequency** (required) – Data cadence
   - `daily` – Daily time series
   - `weekly` – Weekly aggregations
   - `monthly` – Monthly aggregations
   - `quarterly` – Quarterly aggregations
   - `annual` – Annual aggregations
   - `realtime` – Real-time or intraday data
   - `hourly` – Hourly time series

6. **environment** (optional) – Production vs staging
   - `production` – Live production data
   - `staging` – Testing and development
   - Omit for raw/intelligence tables (assumed production)
   - Include for model outputs (training, predictions, monitoring)

## Naming Rules

1. **All lowercase** – Use lowercase letters only
2. **Underscore separators** – Use underscores (`_`) to separate components
3. **No abbreviations** – Spell out full words unless industry-standard (e.g., `fx` for foreign exchange)
4. **Consistent ordering** – Always follow the pattern order
5. **Descriptive names** – Be specific about what the table contains

## Example Mappings

### Raw Data Tables

| Current Name | New Name | Rationale |
|-------------|----------|-----------|
| `forecasting_data_warehouse.soybean_oil_prices` | `raw_intelligence.commodities_agriculture_soybean_oil_raw_daily` | Commodity (soybean oil) raw daily price feed |
| `forecasting_data_warehouse.soybean_prices` | `raw_intelligence.commodities_agriculture_soybean_raw_daily` | Raw soybean spot prices |
| `forecasting_data_warehouse.corn_prices` | `raw_intelligence.commodities_agriculture_corn_raw_daily` | Raw corn price data |
| `forecasting_data_warehouse.palm_oil_prices` | `raw_intelligence.commodities_agriculture_palm_oil_raw_daily` | Raw palm oil prices |
| `forecasting_data_warehouse.crude_oil_prices` | `raw_intelligence.commodities_energy_crude_oil_raw_daily` | Raw crude oil prices |
| `forecasting_data_warehouse.weather_data` | `raw_intelligence.intelligence_weather_global_raw_daily` | Weather intelligence by location |
| `forecasting_data_warehouse.trump_policy_intelligence` | `raw_intelligence.intelligence_policy_trump_raw_daily` | Raw Trump policy intelligence feed |
| `forecasting_data_warehouse.news_intelligence` | `raw_intelligence.intelligence_news_general_raw_daily` | Raw news sentiment feeds |
| `forecasting_data_warehouse.social_intelligence_unified` | `raw_intelligence.intelligence_sentiment_social_raw_daily` | Unified social media sentiment |
| `forecasting_data_warehouse.vix_daily` | `raw_intelligence.equities_vix_raw_daily` | VIX volatility index |
| `forecasting_data_warehouse.usd_index_prices` | `raw_intelligence.fx_dxy_raw_daily` | USD index (DXY) |
| `forecasting_data_warehouse.treasury_prices` | `raw_intelligence.rates_treasury_raw_daily` | Treasury bond prices |

### Feature Tables

| Current Name | New Name | Rationale |
|-------------|----------|-----------|
| `models_v4.vertex_core_features` | `features.general_master_daily` | Master feature set (core features) |
| `forecasting_data_warehouse.rin_proxy_features_final` | `features.biofuel_rin_proxy_daily` | Feature table for biofuel proxies |
| `yahoo_finance_comprehensive.yahoo_normalized` | `features.commodities_general_yahoo_normalized_daily` | All normalized Yahoo Finance series |
| `models_v4.cftc_daily_filled` | `features.commodities_agriculture_cftc_filled_daily` | Positioning data with missing values filled |

### Training Tables

| Current Name | New Name | Rationale |
|-------------|----------|-----------|
| `models_v4.production_training_data_1m` | `training.horizon_1m_production` | 1-month training dataset, production environment |
| `models_v4.production_training_data_1w` | `training.horizon_1w_production` | 1-week training dataset, production environment |
| `models_v4.production_training_data_3m` | `training.horizon_3m_production` | 3-month training dataset, production environment |
| `models_v4.production_training_data_6m` | `training.horizon_6m_production` | 6-month training dataset, production environment |
| `models_v4.production_training_data_12m` | `training.horizon_12m_production` | 12-month training dataset, production environment |
| `models_v4.trump_rich_2023_2025` | `training.regime_trump_2023_2025_production` | Training set for Trump era regime |
| `models_v4.pre_crisis_2000_2007_historical` | `training.regime_pre_crisis_2000_2007_archive` | Historic regime archive |
| `models_v4.recovery_2010_2016_historical` | `training.regime_recovery_2010_2016_archive` | Historical regime for the recovery era |
| `models_v4.trade_war_2017_2019_historical` | `training.regime_trade_war_2017_2019_archive` | Trade war era training data |
| `models_v4.crisis_2008_historical` | `training.regime_crisis_2008_archive` | Financial crisis era training data |

### Prediction Tables

| Current Name | New Name | Rationale |
|-------------|----------|-----------|
| `predictions.monthly_vertex_predictions` | `predictions.horizon_1m_production` | 1-month horizon predictions |
| `predictions.daily_forecasts` | `predictions.horizon_all_horizons_production` | Multi-horizon daily forecasts |
| `forecasting_data_warehouse.signals_1w` | `predictions.signal_1w_production` | 1-week horizon signals |

### Monitoring Tables

| Current Name | New Name | Rationale |
|-------------|----------|-----------|
| `dashboard.performance_metrics` | `monitoring.model_performance_daily` | Model performance metrics |
| `dashboard.prediction_history` | `monitoring.prediction_history_daily` | Historical prediction tracking |
| `dashboard.regime_history` | `monitoring.regime_history_daily` | Market regime tracking |

## Special Cases

### Views

Views follow the same naming convention but are prefixed with `vw_`:
- `vw_commodities_agriculture_soybean_oil_enriched_daily`
- `vw_features_general_master_daily`

### Archive Tables

Archive tables include a timestamp in the name:
- `archive.legacy_nov12_2025_{original_table_name}`
- `archive.regime_historical_{regime_name}_{date}`

### Backup Tables

Backup tables follow the pattern:
- `archive.backup_{table_name}_{timestamp}`

## Migration Checklist

When renaming a table:

1. ✅ Verify the new name follows the pattern exactly
2. ✅ Check for naming conflicts in the target dataset
3. ✅ Update all downstream dependencies (views, scripts, models)
4. ✅ Create compatibility view with old name pointing to new table
5. ✅ Update documentation and data lineage maps
6. ✅ Test all queries and pipelines
7. ✅ Archive old table after grace period (30 days)

## Validation

To validate a table name:

```python
import re

def validate_table_name(name: str) -> bool:
    """Validate table name follows convention."""
    pattern = r'^[a-z]+_[a-z]+_[a-z_]+_(raw|enriched|features|training|prediction|metadata)_(daily|weekly|monthly|quarterly|annual|realtime|hourly)(_(production|staging))?$'
    return bool(re.match(pattern, name))
```

## References

- See `DATASET_STRUCTURE_DESIGN.md` for dataset organization
- See `DATA_LINEAGE_MAP.md` for table relationships
- See `DEDUPLICATION_RULES.md` for source precedence

