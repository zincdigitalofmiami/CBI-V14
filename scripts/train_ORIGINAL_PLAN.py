#!/usr/bin/env python3
"""
ORIGINAL TRAINING PLAN - AS DISCUSSED
Multi-horizon forecasting with ALL model types
Based on MASTER_TRAINING_PLAN.md and previous discussions
"""

from google.cloud import bigquery
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚀 ORIGINAL TRAINING PLAN - COMPREHENSIVE")
print("=" * 80)
print()
print("Based on MASTER_TRAINING_PLAN.md")
print("Multi-horizon: 1w, 1m, 3m, 6m, 12m")
print("Models: LightGBM, DNN, AutoML, ARIMA_PLUS")
print("Data: 4,862 rows with BIG 8 signals")
print()

# Train models as per MASTER PLAN
def train_all_models():
    """Train all models from the MASTER TRAINING PLAN"""
    
    models_to_train = []
    
    # PHASE 3.1: LightGBM Baseline (from MASTER_TRAINING_PLAN.md line 273)
    print("\n" + "="*60)
    print("PHASE 3.1: Training LightGBM Baseline")
    print("="*60)
    
    query = """
    CREATE OR REPLACE MODEL `cbi-v14.models.zl_lightgbm_v1`
    OPTIONS(
        model_type='BOOSTED_TREE_REGRESSOR',
        input_label_cols=['target_1w'],
        data_split_method='SEQ',
        data_split_col='date',
        max_iterations=50,
        early_stop=TRUE,
        min_tree_child_weight=10,
        subsample=0.8,
        max_tree_depth=8
    ) AS
    SELECT * EXCEPT(target_1m, target_3m, target_6m, target_12m)
    FROM `cbi-v14.models.vw_neural_training_dataset_v2`
    WHERE target_1w IS NOT NULL
    """
    
    try:
        job = client.query(query)
        job.result()
        print("✅ Created zl_lightgbm_v1")
        models_to_train.append("zl_lightgbm_v1")
    except Exception as e:
        print(f"❌ Failed: {str(e)[:100]}")
    
    # PHASE 3.2: Neural Network (from MASTER_TRAINING_PLAN.md line 291)
    print("\n" + "="*60)
    print("PHASE 3.2: Training Neural Network")
    print("="*60)
    
    query = """
    CREATE OR REPLACE MODEL `cbi-v14.models.zl_neural_v1`
    OPTIONS(
        model_type='DNN_REGRESSOR',
        hidden_units=[128, 64, 32],
        activation_fn='RELU',
        dropout=0.3,
        batch_size=64,
        learn_rate=0.001,
        optimizer='ADAM',
        input_label_cols=['target_1w'],
        data_split_method='SEQ',
        data_split_col='date',
        max_iterations=100
    ) AS
    SELECT * EXCEPT(target_1m, target_3m, target_6m, target_12m)
    FROM `cbi-v14.models.vw_neural_training_dataset_v2`
    WHERE target_1w IS NOT NULL
    """
    
    try:
        job = client.query(query)
        job.result()
        print("✅ Created zl_neural_v1")
        models_to_train.append("zl_neural_v1")
    except Exception as e:
        print(f"❌ Failed: {str(e)[:100]}")
    
    # PHASE 3.3: AutoML (from MASTER_TRAINING_PLAN.md line 311)
    print("\n" + "="*60)
    print("PHASE 3.3: Training AutoML Ensemble")
    print("="*60)
    
    query = """
    CREATE OR REPLACE MODEL `cbi-v14.models.zl_automl_v1`
    OPTIONS(
        model_type='AUTOML_REGRESSOR',
        budget_hours=1.0,
        input_label_cols=['target_1w']
    ) AS
    SELECT target_1w,
        zl_price_current,
        zl_price_lag1,
        zl_price_lag7,
        feature_vix_stress,
        feature_harvest_pace,
        feature_china_relations,
        feature_biofuel_ethanol,
        corr_zl_crude_30d,
        corr_zl_palm_30d,
        avg_sentiment
    FROM `cbi-v14.models.vw_neural_training_dataset_v2`
    WHERE date >= '2024-01-01'
    AND target_1w IS NOT NULL
    """
    
    try:
        job = client.query(query)
        job.result()
        print("✅ Created zl_automl_v1")
        models_to_train.append("zl_automl_v1")
    except Exception as e:
        print(f"❌ Failed: {str(e)[:100]}")
    
    # Now train multi-horizon models
    print("\n" + "="*60)
    print("MULTI-HORIZON TRAINING")
    print("="*60)
    
    horizons = {
        '1w': 'target_1w',
        '1m': 'target_1m',
        '3m': 'target_3m',
        '6m': 'target_6m',
        '12m': 'target_12m'
    }
    
    for horizon, target in horizons.items():
        print(f"\n--- Training for {horizon} horizon ---")
        
        # LightGBM for each horizon
        model_name = f"zl_lightgbm_{horizon}"
        query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
        OPTIONS(
            model_type='BOOSTED_TREE_REGRESSOR',
            input_label_cols=['{target}'],
            data_split_method='SEQ',
            data_split_col='date',
            max_iterations=100,
            early_stop=TRUE,
            min_tree_child_weight=10,
            subsample=0.85,
            max_tree_depth=10
        ) AS
        SELECT date, {target},
            zl_price_current,
            zl_price_lag1,
            zl_price_lag7,
            zl_price_lag30,
            feature_vix_stress,
            feature_harvest_pace,
            feature_china_relations,
            feature_tariff_threat,
            feature_geopolitical_volatility,
            feature_biofuel_cascade,
            COALESCE(feature_hidden_correlation, 0) as feature_hidden_correlation,
            feature_biofuel_ethanol,
            corr_zl_crude_7d,
            corr_zl_crude_30d,
            corr_zl_palm_7d,
            corr_zl_palm_30d,
            avg_sentiment
        FROM `cbi-v14.models.vw_neural_training_dataset_v2`
        WHERE {target} IS NOT NULL
        """
        
        try:
            job = client.query(query)
            job.result()
            print(f"  ✅ {model_name}")
            models_to_train.append(model_name)
        except Exception as e:
            print(f"  ❌ {model_name}: {str(e)[:50]}")
        
        # DNN for each horizon
        model_name = f"zl_dnn_{horizon}"
        query = f"""
        CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
        OPTIONS(
            model_type='DNN_REGRESSOR',
            hidden_units=[256, 128, 64, 32],
            activation_fn='RELU',
            dropout=0.3,
            batch_size=32,
            learn_rate=0.001,
            optimizer='ADAM',
            input_label_cols=['{target}'],
            data_split_method='SEQ',
            data_split_col='date',
            max_iterations=200
        ) AS
        SELECT date, {target},
            zl_price_current,
            zl_price_lag1,
            zl_price_lag7,
            zl_price_lag30,
            feature_vix_stress,
            feature_harvest_pace,
            feature_china_relations,
            feature_tariff_threat,
            feature_geopolitical_volatility,
            feature_biofuel_cascade,
            COALESCE(feature_hidden_correlation, 0) as feature_hidden_correlation,
            feature_biofuel_ethanol,
            corr_zl_crude_7d,
            corr_zl_crude_30d,
            corr_zl_palm_7d,
            corr_zl_palm_30d,
            avg_sentiment
        FROM `cbi-v14.models.vw_neural_training_dataset_v2`
        WHERE {target} IS NOT NULL
        """
        
        try:
            job = client.query(query)
            job.result()
            print(f"  ✅ {model_name}")
            models_to_train.append(model_name)
        except Exception as e:
            print(f"  ❌ {model_name}: {str(e)[:50]}")
        
        # ARIMA for each horizon (simplified)
        if horizon in ['1w', '1m']:  # ARIMA for shorter horizons
            model_name = f"zl_arima_{horizon}"
            query = f"""
            CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
            OPTIONS(
                model_type='ARIMA_PLUS',
                time_series_timestamp_col='date',
                time_series_data_col='price',
                auto_arima=TRUE,
                auto_arima_max_order=5
            ) AS
            SELECT date, {target} as price
            FROM `cbi-v14.models.vw_neural_training_dataset_v2`
            WHERE {target} IS NOT NULL
            ORDER BY date
            """
            
            try:
                job = client.query(query)
                job.result()
                print(f"  ✅ {model_name}")
                models_to_train.append(model_name)
            except Exception as e:
                print(f"  ❌ {model_name}: {str(e)[:50]}")
    
    return models_to_train

# Main execution
print("\n" + "=" * 80)
print("STARTING ORIGINAL TRAINING PLAN")
print("=" * 80)

models = train_all_models()

print("\n" + "=" * 80)
print("🏁 TRAINING COMPLETE")
print("=" * 80)
print(f"\n✅ Total models trained: {len(models)}")
if models:
    print("\nSuccessfully trained models:")
    for model in models:
        print(f"  • {model}")

print("\n" + "=" * 80)
print("PHASE 4: EVALUATION")
print("=" * 80)

# Evaluate the main model
if 'zl_lightgbm_v1' in models:
    try:
        query = """
        SELECT * FROM ML.EVALUATE(
            MODEL `cbi-v14.models.zl_lightgbm_v1`,
            (SELECT * FROM `cbi-v14.models.vw_neural_training_dataset_v2`
             WHERE date >= '2025-09-01')
        )
        """
        results = list(client.query(query))[0]
        print(f"\nLightGBM v1 Evaluation:")
        print(f"  MAE: {results.get('mean_absolute_error', 'N/A')}")
        print(f"  RMSE: {results.get('mean_squared_error', 'N/A')**0.5 if results.get('mean_squared_error') else 'N/A'}")
    except Exception as e:
        print(f"Evaluation error: {str(e)[:100]}")

print("\n" + "=" * 80)
print("NEXT STEPS (from MASTER_TRAINING_PLAN.md):")
print("=" * 80)
print("1. Deploy best model to API")
print("2. Update dashboard to show forecasts")
print("3. Set up daily retraining")
print("4. Monitor performance")
print()
print("Models are in: cbi-v14.models dataset")
print("Use: SELECT * FROM ML.PREDICT(MODEL `cbi-v14.models.MODEL_NAME`, ...)")
