# Schema Fix Implementation Guide

## Problem Statement

Vertex AI AutoML models are failing during prediction with schema mismatch errors:
- Type mismatches (models expecting STRING where INT is provided)
- Date formatting issues (need 'YYYY-MM-DD' string format)
- NaN value handling (must be converted to None)

## Solution Overview

Three-step approach to fix schema issues:

### Step 1: Validate Schema
```bash
cd /Users/zincdigital/CBI-V14/automl
python validate_schema.py
```

This will:
- Analyze current dataset schema
- Identify type mismatches
- Generate detailed report in `schema_validation_report.json`

### Step 2: Test with Single Model
```bash
python schema_fix_predictions.py --test 1W
```

This will:
- Apply all schema fixes
- Test deployment with 1W model only
- Verify prediction works end-to-end
- Save to BigQuery if successful

### Step 3: Run All Models
```bash
python schema_fix_predictions.py
```

This will:
- Deploy each model sequentially
- Get predictions with proper schema
- Save to `cbi-v14.predictions.daily_forecasts`
- Undeploy immediately to minimize costs

## Key Schema Fixes Applied

### Fix #1: String Conversion
```python
# Convert specific columns to STRING (as model expects)
string_cols = ['zl_volume', 'zl_open_interest']
for col in string_cols:
    df[col] = df[col].astype(str)
```

### Fix #2: Date Formatting
```python
# Format dates as 'YYYY-MM-DD' strings
for col in date_cols:
    df[col] = df[col].dt.strftime('%Y-%m-%d')
```

### Fix #3: NaN Handling
```python
# Replace NaN with None (Vertex AI requirement)
df = df.replace({np.nan: None})
```

### Fix #4: Target Columns
```python
# Set targets to None (prevent leakage)
for target_col in ['target_1w', 'target_1m', 'target_3m', 'target_6m']:
    df[target_col] = None
```

## Output Schema

Predictions saved to `cbi-v14.predictions.daily_forecasts`:
```
horizon           STRING    (e.g., '1W', '3M', '6M')
prediction_date   DATE      (when prediction was made)
target_date       DATE      (what date is being predicted)
predicted_price   FLOAT     (model prediction)
confidence_lower  FLOAT     (lower bound based on MAPE)
confidence_upper  FLOAT     (upper bound based on MAPE)
mape              FLOAT     (model's MAPE performance)
model_id          STRING    (Vertex AI model ID)
model_name        STRING    (model display name)
created_at        TIMESTAMP (when row was created)
```

## Cost Estimate

- **Single model test:** ~$0.10-$0.15 (5-10 min deployment)
- **All 3 models:** ~$0.40-$0.60 (15-25 min total)
- Monthly run: **$0.60/month**

## Troubleshooting

### Schema validation fails
```bash
# Check BigQuery connection
gcloud auth application-default login

# Verify dataset exists
bq ls cbi-v14:models_v4
```

### Test deployment fails
```bash
# Check logs
tail -f /Users/zincdigital/CBI-V14/logs/schema_fix_predictions.log

# Verify model IDs
gcloud ai models list --region=us-central1 --project=cbi-v14
```

### Prediction format error
- Check `schema_validation_report.json` for specific column issues
- Add any problematic columns to `string_conversion_cols` list
- Re-run with `--test` flag

## Success Criteria

✅ Schema validator shows 0 critical issues
✅ Single model test completes without errors
✅ Prediction saved to BigQuery
✅ All models complete successfully
✅ Dashboard can query predictions

## Next Steps After Success

1. Update MASTER_TRAINING_PLAN.md with completion status
2. Configure monthly cron job for automated predictions
3. Update dashboard API routes to read from BigQuery
4. Monitor costs in Google Cloud Console

## Files Created

- `validate_schema.py` - Schema validation tool
- `schema_fix_predictions.py` - Main prediction script with fixes
- `schema_validation_report.json` - Validation output (generated)
- `SCHEMA_FIX_README.md` - This file

## Contact

Issues? Check:
1. Log file: `/Users/zincdigital/CBI-V14/logs/schema_fix_predictions.log`
2. Validation report: `schema_validation_report.json`
3. MASTER_TRAINING_PLAN.md for current status

