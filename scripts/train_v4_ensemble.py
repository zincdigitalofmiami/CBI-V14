#!/usr/bin/env python3
"""
V4 ENSEMBLE MODEL CREATION
Creates weighted ensemble views combining best models per horizon
"""

from google.cloud import bigquery
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🎯 CREATING V4 ENSEMBLE MODELS")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Ensemble weights (based on expected performance)
# 40% Boosted V3 (proven winner)
# 30% AutoML V4 (if better than DNNs)
# 20% DNN V4 (if 1w/1m exist) or existing DNN (3m/6m)
# 10% ARIMA V4 (time series baseline)
ENSEMBLE_WEIGHTS = {
    'boosted_v3': 0.40,
    'automl_v4': 0.30,
    'dnn': 0.20,
    'arima_v4': 0.10
}

horizons = ['1w', '1m', '3m', '6m']
views_created = []

for horizon in horizons:
    view_name = f"zl_ensemble_{horizon}_v4"
    
    print(f"\n{'='*70}")
    print(f"CREATING ENSEMBLE: {view_name}")
    print(f"Horizon: {horizon}")
    print('='*70)
    
    # Determine which DNN model to use
    if horizon in ['1w', '1m']:
        dnn_model = f"cbi-v14.models_v4.zl_dnn_{horizon}_v4"
    else:
        # Use existing V3 DNN for 3m/6m (they work fine)
        dnn_model = f"cbi-v14.models.zl_dnn_{horizon}_production"
    
    query = f"""
    CREATE OR REPLACE VIEW `cbi-v14.models_v4.{view_name}` AS
    WITH latest_features AS (
        SELECT * EXCEPT(date)
        FROM `cbi-v14.models.training_dataset`
        ORDER BY date DESC
        LIMIT 1
    ),
    predictions AS (
        -- V3 Boosted Tree (40% weight)
        SELECT 
            'boosted_v3' AS model_type,
            {ENSEMBLE_WEIGHTS['boosted_v3']} AS weight,
            p.predicted_target_{horizon} AS prediction
        FROM ML.PREDICT(
            MODEL `cbi-v14.models.zl_boosted_tree_{horizon}_v3`,
            (SELECT * FROM latest_features)
        ) p
        
        UNION ALL
        
        -- V4 AutoML (30% weight)
        SELECT 
            'automl_v4' AS model_type,
            {ENSEMBLE_WEIGHTS['automl_v4']} AS weight,
            p.predicted_target_{horizon} AS prediction
        FROM ML.PREDICT(
            MODEL `cbi-v14.models_v4.zl_automl_{horizon}_v4`,
            (SELECT * FROM latest_features)
        ) p
        
        UNION ALL
        
        -- DNN (20% weight)
        SELECT 
            'dnn' AS model_type,
            {ENSEMBLE_WEIGHTS['dnn']} AS weight,
            p.predicted_target_{horizon} AS prediction
        FROM ML.PREDICT(
            MODEL `{dnn_model}`,
            (SELECT * FROM latest_features)
        ) p
        
        UNION ALL
        
        -- V4 ARIMA (10% weight)
        SELECT 
            'arima_v4' AS model_type,
            {ENSEMBLE_WEIGHTS['arima_v4']} AS weight,
            p.forecast_value AS prediction
        FROM ML.FORECAST(
            MODEL `cbi-v14.models_v4.zl_arima_{horizon}_v4`,
            STRUCT({7 if horizon == '1w' else 30 if horizon == '1m' else 90 if horizon == '3m' else 180} AS horizon)
        ) p
        ORDER BY forecast_timestamp DESC
        LIMIT 1
    )
    SELECT 
        CURRENT_TIMESTAMP() AS timestamp,
        SUM(prediction * weight) AS ensemble_prediction,
        AVG(CASE WHEN model_type = 'boosted_v3' THEN prediction END) AS boosted_v3_pred,
        AVG(CASE WHEN model_type = 'automl_v4' THEN prediction END) AS automl_v4_pred,
        AVG(CASE WHEN model_type = 'dnn' THEN prediction END) AS dnn_pred,
        AVG(CASE WHEN model_type = 'arima_v4' THEN prediction END) AS arima_v4_pred,
        STDDEV(prediction) AS prediction_stddev,
        '{horizon}' AS horizon
    FROM predictions
    """
    
    try:
        print(f"\n🔄 Creating ensemble view...")
        job = client.query(query)
        job.result()
        
        print(f"✅ Created: cbi-v14.models_v4.{view_name}")
        views_created.append(view_name)
        
        # Test the view
        test_query = f"SELECT * FROM `cbi-v14.models_v4.{view_name}` LIMIT 1"
        result = client.query(test_query).to_dataframe()
        
        if not result.empty:
            pred = result['ensemble_prediction'].iloc[0]
            stddev = result['prediction_stddev'].iloc[0]
            print(f"   Ensemble prediction: ${pred:.2f}")
            print(f"   Prediction std dev: ${stddev:.2f}")
            print(f"   Component breakdown:")
            print(f"     - Boosted V3: ${result['boosted_v3_pred'].iloc[0]:.2f}")
            print(f"     - AutoML V4: ${result['automl_v4_pred'].iloc[0]:.2f}")
            print(f"     - DNN: ${result['dnn_pred'].iloc[0]:.2f}")
            print(f"     - ARIMA V4: ${result['arima_v4_pred'].iloc[0]:.2f}")
        
    except Exception as e:
        print(f"❌ Failed to create {view_name}: {str(e)}")
        logger.error(f"Error creating ensemble view {view_name}: {e}")

print("\n" + "=" * 80)
print("📊 ENSEMBLE CREATION SUMMARY")
print("=" * 80)
print()

if views_created:
    print(f"✅ Successfully created {len(views_created)} ensemble views:")
    for view in views_created:
        print(f"   - cbi-v14.models_v4.{view}")
else:
    print("❌ No ensemble views created")

print()
print("=" * 80)
print("💡 ENSEMBLE ARCHITECTURE")
print("=" * 80)
print()
print("Weight Distribution:")
print(f"  - Boosted Tree V3: {ENSEMBLE_WEIGHTS['boosted_v3']*100:.0f}% (proven production model)")
print(f"  - AutoML V4: {ENSEMBLE_WEIGHTS['automl_v4']*100:.0f}% (best possible architecture)")
print(f"  - DNN: {ENSEMBLE_WEIGHTS['dnn']*100:.0f}% (non-linear patterns)")
print(f"  - ARIMA V4: {ENSEMBLE_WEIGHTS['arima_v4']*100:.0f}% (time series trend)")
print()
print("Benefits:")
print("  ✅ Reduces single-model risk")
print("  ✅ Combines strengths of different architectures")
print("  ✅ ARIMA provides time-series stability")
print("  ✅ AutoML captures optimal feature interactions")
print()
print("⚠️  Note: Ensemble weights should be adjusted based on:")
print("    1. AutoML performance (may deserve higher weight if superior)")
print("    2. DNN performance (reduce weight if underperforming)")
print("    3. Market regime (increase ARIMA weight in crisis periods)")
print()
print("=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)












