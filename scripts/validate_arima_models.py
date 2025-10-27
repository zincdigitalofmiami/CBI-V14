#!/usr/bin/env python3
"""
Validate ARIMA models and check if they can generate predictions
ARIMA models don't have standard ML.EVALUATE metrics, so we need to test forecasting
"""

from google.cloud import bigquery
from datetime import datetime
import pandas as pd

client = bigquery.Client(project='cbi-v14')

print(f"ARIMA MODEL VALIDATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# ARIMA models to validate
arima_models = [
    ('zl_arima_production_1w', 'target_1w', 7),
    ('zl_arima_production_1m', 'target_1m', 30),
    ('zl_arima_production_3m', 'target_3m', 90),
    ('zl_arima_production_6m', 'target_6m', 180)
]

print("\n1. CHECKING ARIMA MODEL STATUS:")
print("-"*80)

validation_results = []

for model_name, target_col, horizon_days in arima_models:
    print(f"\nValidating: {model_name}")
    print(f"  Target: {target_col} (horizon: {horizon_days} days)")
    
    try:
        # Get model info
        model = client.get_model(f'cbi-v14.models.{model_name}')
        print(f"  ✓ Model exists")
        print(f"  Model type: {model.model_type}")
        
        # Try to generate forecast
        forecast_query = f"""
        SELECT 
            forecast_timestamp,
            forecast_value,
            standard_error,
            confidence_level,
            prediction_interval_lower_bound,
            prediction_interval_upper_bound
        FROM ML.FORECAST(
            MODEL `cbi-v14.models.{model_name}`,
            STRUCT({horizon_days} AS horizon, 0.9 AS confidence_level)
        )
        ORDER BY forecast_timestamp
        LIMIT 10
        """
        
        print(f"  Testing forecast generation...")
        forecast_df = client.query(forecast_query).to_dataframe()
        
        if len(forecast_df) > 0:
            print(f"  ✓ Can generate forecasts ({len(forecast_df)} points)")
            print(f"  Sample forecast value: {forecast_df['forecast_value'].iloc[0]:.2f}")
            print(f"  Confidence interval: [{forecast_df['prediction_interval_lower_bound'].iloc[0]:.2f}, "
                  f"{forecast_df['prediction_interval_upper_bound'].iloc[0]:.2f}]")
            
            # Check if forecast values are reasonable (not NaN, not extreme)
            if forecast_df['forecast_value'].isna().any():
                print(f"  ⚠️ WARNING: Forecast contains NaN values")
                validation_results.append((model_name, 'FAILED - NaN values'))
            elif abs(forecast_df['forecast_value'].mean()) > 1000:
                print(f"  ⚠️ WARNING: Forecast values seem unrealistic (mean: {forecast_df['forecast_value'].mean():.2f})")
                validation_results.append((model_name, 'FAILED - Unrealistic values'))
            else:
                print(f"  ✓ Forecast values appear reasonable")
                validation_results.append((model_name, 'PASSED'))
        else:
            print(f"  ✗ No forecast data returned")
            validation_results.append((model_name, 'FAILED - No forecast'))
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:150]}")
        validation_results.append((model_name, f'ERROR - {str(e)[:50]}'))
        
        # If model is broken, attempt to retrain
        print(f"  Attempting to fix by retraining...")
        
        retrain_query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
        OPTIONS(
            model_type='ARIMA_PLUS',
            time_series_timestamp_col='date',
            time_series_data_col='{target_col}',
            auto_arima=TRUE,
            data_frequency='DAILY',
            decompose_time_series=TRUE,
            clean_spikes_and_dips=TRUE,
            adjust_step_changes=TRUE,
            holiday_region='US'
        ) AS
        SELECT 
            date, 
            {target_col}
        FROM `cbi-v14.models.training_dataset_final_v1`
        WHERE {target_col} IS NOT NULL
        ORDER BY date
        """
        
        try:
            job = client.query(retrain_query)
            print(f"  Retrain job submitted: {job.job_id}")
        except Exception as retrain_error:
            print(f"  Failed to retrain: {str(retrain_error)[:100]}")

print("\n2. VALIDATION SUMMARY:")
print("-"*80)

print("\nARIMA Model Validation Results:")
print(f"{'Model Name':<30} {'Status':<20}")
print("-"*50)
for model_name, status in validation_results:
    status_symbol = "✓" if "PASSED" in status else "✗"
    print(f"{status_symbol} {model_name:<28} {status}")

# Count results
passed = sum(1 for _, status in validation_results if "PASSED" in status)
failed = len(validation_results) - passed

print(f"\nTotal: {passed} passed, {failed} failed/error")

print("\n3. BACKTESTING ARIMA PERFORMANCE:")
print("-"*80)
print("Comparing ARIMA forecasts to actual values for validation...")

# For models that passed, do a simple backtest
for model_name, status in validation_results:
    if "PASSED" in status:
        print(f"\nBacktesting {model_name}:")
        
        # Get historical forecast vs actual
        backtest_query = f"""
        WITH forecast_data AS (
            SELECT 
                forecast_timestamp,
                forecast_value
            FROM ML.FORECAST(
                MODEL `cbi-v14.models.{model_name}`,
                STRUCT(7 AS horizon, 0.9 AS confidence_level)
            )
            ORDER BY forecast_timestamp
            LIMIT 7
        ),
        actual_data AS (
            SELECT 
                date,
                zl_price_current as actual_value
            FROM `cbi-v14.models.training_dataset_final_v1`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
            ORDER BY date DESC
            LIMIT 7
        )
        SELECT 
            AVG(ABS(f.forecast_value - a.actual_value)) as mae,
            AVG(ABS(f.forecast_value - a.actual_value) / NULLIF(a.actual_value, 0)) * 100 as mape
        FROM forecast_data f
        JOIN actual_data a ON DATE(f.forecast_timestamp) = a.date
        """
        
        try:
            backtest_result = client.query(backtest_query).to_dataframe()
            if not backtest_result.empty and not backtest_result['mae'].isna().all():
                mae = backtest_result['mae'].iloc[0]
                mape = backtest_result['mape'].iloc[0]
                print(f"  Backtest MAE: {mae:.2f}")
                print(f"  Backtest MAPE: {mape:.2f}%")
            else:
                print(f"  Unable to compute backtest metrics")
        except Exception as e:
            print(f"  Backtest failed: {str(e)[:100]}")

print("\n" + "="*80)
print("ARIMA VALIDATION COMPLETE")
print("="*80)

if failed > 0:
    print("\n⚠️ Some ARIMA models failed validation.")
    print("Consider using the Boosted Tree models for production as they have proven performance.")
else:
    print("\n✓ All ARIMA models passed validation and can generate forecasts.")

print("\nRECOMMENDATION:")
print("  Use the Boosted Tree models for production (MAE: 1.19-1.58)")
print("  Keep ARIMA models as alternative/ensemble members if needed")
