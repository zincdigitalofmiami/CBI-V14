# Training Data Audit Report
**Date**: 2025-11-12 17:18:39

## Production Tables

## Issues

- production_training_data_1w: Error - Cannot compare Timestamp with datetime.date. Use ts == pd.Timestamp(date) or ts.date() == date instead.
- production_training_data_1m: Error - Cannot compare Timestamp with datetime.date. Use ts == pd.Timestamp(date) or ts.date() == date instead.
- production_training_data_3m: Error - Cannot compare Timestamp with datetime.date. Use ts == pd.Timestamp(date) or ts.date() == date instead.
- production_training_data_6m: Error - Cannot compare Timestamp with datetime.date. Use ts == pd.Timestamp(date) or ts.date() == date instead.
- production_training_data_12m: Error - Cannot compare Timestamp with datetime.date. Use ts == pd.Timestamp(date) or ts.date() == date instead.
- soybean_oil_prices: Error - Cannot compare Timestamp with datetime.date. Use ts == pd.Timestamp(date) or ts.date() == date instead.
- production_training_data_1w: 313 date gaps (max: 4.0 days)
- production_training_data_1m: 307 date gaps (max: 6.0 days)
- production_training_data_3m: 294 date gaps (max: 5.0 days)
- production_training_data_6m: 276 date gaps (max: 6.0 days)
- production_training_data_12m: 276 date gaps (max: 6.0 days)

## Recommendations

