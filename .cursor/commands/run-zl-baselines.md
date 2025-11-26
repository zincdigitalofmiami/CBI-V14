# Run ZL baselines

Use the production trainer (price-level targets, all horizons):

```bash
cd /Users/zincdigital/CBI-V14
python3 scripts/train/train_zl_baselines.py
```

This script:
- Loads horizon-specific ZL training exports from `TrainingData/exports/`.
- Trains LightGBM regression models for 1w/1m/3m/6m/12m.
- Logs metrics and saves models + `BacktestRun` metadata under:
  `TrainingData/models/zl_baselines/`

Ensure data freshness in BigQuery before running (see `/check-bq-freshness`).

