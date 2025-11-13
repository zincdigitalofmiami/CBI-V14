# Training Data Audit Report
**Date**: 2025-11-12 17:19:05

## Production Tables

### 1w
- Date range: 2020-01-02 to 2025-11-06
- Rows: 1,472
- Features: 299
- Has historical: False

### 1m
- Date range: 2020-01-06 to 2025-11-06
- Rows: 1,404
- Features: 443
- Has historical: False

### 3m
- Date range: 2020-01-02 to 2025-11-06
- Rows: 1,475
- Features: 299
- Has historical: False

### 6m
- Date range: 2020-01-02 to 2025-11-06
- Rows: 1,473
- Features: 299
- Has historical: False

### 12m
- Date range: 2020-01-02 to 2025-11-06
- Rows: 1,473
- Features: 300
- Has historical: False

## Issues

- production_training_data_1w: Missing historical data (starts 2020-01-02)
- production_training_data_1m: Missing historical data (starts 2020-01-06)
- production_training_data_3m: Missing historical data (starts 2020-01-02)
- production_training_data_6m: Missing historical data (starts 2020-01-02)
- production_training_data_12m: Missing historical data (starts 2020-01-02)
- production_training_data_12m: 256 NULL targets (17.4%)
- production_training_data_1w: 313 date gaps (max: 4.0 days)
- production_training_data_1m: 307 date gaps (max: 6.0 days)
- production_training_data_3m: 294 date gaps (max: 5.0 days)
- production_training_data_6m: 276 date gaps (max: 6.0 days)
- production_training_data_12m: 276 date gaps (max: 6.0 days)

## Recommendations

- Rebuild production_training_data_1w with 2000-2025 date range
- Rebuild production_training_data_1m with 2000-2025 date range
- Rebuild production_training_data_3m with 2000-2025 date range
- Rebuild production_training_data_6m with 2000-2025 date range
- Rebuild production_training_data_12m with 2000-2025 date range
