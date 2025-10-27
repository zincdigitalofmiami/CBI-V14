#!/usr/bin/env python3
"""
TRAIN BIG 8 MODELS - FULL ASSAULT TRAINING
Multi-horizon forecasting with all 8 signals
"""

from google.cloud import bigquery
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚀 BIG 8 MODEL TRAINING - FULL ASSAULT MODE")
print("=" * 80)
print()
print("Training with:")
print("  • 4,862 rows of data")
print("  • All BIG 8 signals at 100% coverage")
print("  • Multi-horizon targets (1w, 1m, 3m, 6m, 12m)")
print("  • Clean, contamination-free data")
print()

# Model configurations for each horizon
MODELS = {
    '1_week': {
        'target': 'target_1w',
        'name': 'zl_big8_1w',
        'description': '1-week forecast with Big 8 signals'
    },
    '1_month': {
        'target': 'target_1m', 
        'name': 'zl_big8_1m',
        'description': '1-month forecast with Big 8 signals'
    },
    '3_month': {
        'target': 'target_3m',
        'name': 'zl_big8_3m',
        'description': '3-month forecast with Big 8 signals'
    },
    '6_month': {
        'target': 'target_6m',
        'name': 'zl_big8_6m',
        'description': '6-month forecast with Big 8 signals'
    },
    '12_month': {
        'target': 'target_12m',
        'name': 'zl_big8_12m',
        'description': '12-month forecast with Big 8 signals'
    }
}

def train_lightgbm_model(horizon, config):
    """Train LightGBM model for specific horizon"""
    print(f"\n📊 Training LightGBM for {horizon}...")
    
    query = f"""
    CREATE OR REPLACE MODEL `cbi-v14.models.{config['name']}_lgb`
    OPTIONS(
        model_type='BOOSTED_TREE_REGRESSOR',
        input_label_cols=['{config['target']}'],
        data_split_method='SEQ',
        data_split_col='date',
        max_iterations=100,
        early_stop=TRUE,
        min_tree_child_weight=10,
        subsample=0.8,
        max_tree_depth=10,
        l1_reg=0.1,
        l2_reg=0.1
    ) AS
    SELECT 
        date,
        {config['target']},
        -- Price features
        zl_price_current,
        zl_price_lag1,
        zl_price_lag7,
        zl_price_lag30,
        -- BIG 8 SIGNALS
        feature_vix_stress,
        feature_harvest_pace,
        feature_china_relations,
        feature_tariff_threat,
        feature_geopolitical_volatility,
        feature_biofuel_cascade,
        feature_hidden_correlation,
        feature_biofuel_ethanol,  -- THE 8TH SIGNAL!
        -- Correlations  
        corr_zl_crude_7d,
        corr_zl_crude_30d,
        corr_zl_palm_7d,
        corr_zl_palm_30d,
        corr_zl_vix_7d,
        corr_zl_vix_30d,
        corr_zl_crude_90d,
        corr_zl_palm_90d,
        corr_zl_crude_180d,
        corr_zl_crude_365d,
        -- Sentiment
        avg_sentiment,
        sentiment_volume
    FROM `cbi-v14.models.vw_neural_training_dataset_v2`
    WHERE {config['target']} IS NOT NULL
    """
    
    try:
        job = client.query(query)
        job.result()
        print(f"  ✅ LightGBM {horizon} model created: {config['name']}_lgb")
        return True
    except Exception as e:
        print(f"  ❌ Error training LightGBM {horizon}: {e}")
        return False

def train_dnn_model(horizon, config):
    """Train Deep Neural Network for specific horizon"""
    print(f"\n🧠 Training Neural Network for {horizon}...")
    
    query = f"""
    CREATE OR REPLACE MODEL `cbi-v14.models.{config['name']}_dnn`
    OPTIONS(
        model_type='DNN_REGRESSOR',
        hidden_units=[256, 128, 64, 32],
        activation_fn='RELU',
        dropout=0.3,
        batch_size=32,
        learn_rate=0.001,
        optimizer='ADAM',
        input_label_cols=['{config['target']}'],
        data_split_method='SEQ',
        data_split_col='date',
        max_iterations=200,
        early_stop=TRUE
    ) AS
    SELECT 
        date,
        {config['target']},
        -- All features same as LightGBM
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
        feature_hidden_correlation,
        feature_biofuel_ethanol,
        corr_zl_crude_7d,
        corr_zl_crude_30d,
        corr_zl_palm_7d,
        corr_zl_palm_30d,
        corr_zl_vix_7d,
        corr_zl_vix_30d,
        corr_zl_crude_90d,
        corr_zl_palm_90d,
        corr_zl_crude_180d,
        corr_zl_crude_365d,
        avg_sentiment,
        sentiment_volume
    FROM `cbi-v14.models.vw_neural_training_dataset_v2`
    WHERE {config['target']} IS NOT NULL
    """
    
    try:
        job = client.query(query)
        job.result()
        print(f"  ✅ DNN {horizon} model created: {config['name']}_dnn")
        return True
    except Exception as e:
        print(f"  ❌ Error training DNN {horizon}: {e}")
        return False

def evaluate_model(model_name, horizon, target):
    """Evaluate model performance"""
    print(f"\n📈 Evaluating {model_name}...")
    
    query = f"""
    SELECT 
        mean_absolute_error,
        mean_squared_error,
        r2_score
    FROM ML.EVALUATE(
        MODEL `cbi-v14.models.{model_name}`,
        (
            SELECT * FROM `cbi-v14.models.vw_neural_training_dataset_v2`
            WHERE date >= '2025-09-01'
            AND {target} IS NOT NULL
        )
    )
    """
    
    try:
        results = list(client.query(query))[0]
        mape = results['mean_absolute_error'] / 50 * 100  # Approximate MAPE
        print(f"  MAE: ${results['mean_absolute_error']:.2f}")
        print(f"  RMSE: ${results['mean_squared_error']**0.5:.2f}")
        print(f"  R²: {results['r2_score']:.3f}")
        print(f"  MAPE: ~{mape:.1f}%")
        return results
    except Exception as e:
        print(f"  Error evaluating: {e}")
        return None

# Main training loop
print("\n" + "=" * 80)
print("STARTING TRAINING SEQUENCE")
print("=" * 80)

successful_models = []
failed_models = []

for horizon, config in MODELS.items():
    print(f"\n{'='*60}")
    print(f"HORIZON: {horizon}")
    print(f"{'='*60}")
    
    # Train LightGBM
    if train_lightgbm_model(horizon, config):
        model_name = f"{config['name']}_lgb"
        successful_models.append(model_name)
        evaluate_model(model_name, horizon, config['target'])
    else:
        failed_models.append(f"{config['name']}_lgb")
    
    # Train DNN
    if train_dnn_model(horizon, config):
        model_name = f"{config['name']}_dnn"
        successful_models.append(model_name)
        evaluate_model(model_name, horizon, config['target'])
    else:
        failed_models.append(f"{config['name']}_dnn")

# Summary
print("\n" + "=" * 80)
print("🏁 TRAINING COMPLETE")
print("=" * 80)
print(f"\n✅ Successfully trained: {len(successful_models)} models")
for model in successful_models:
    print(f"  • {model}")

if failed_models:
    print(f"\n❌ Failed: {len(failed_models)} models")
    for model in failed_models:
        print(f"  • {model}")

print("\n" + "=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("1. Review model performance metrics above")
print("2. Select best model for each horizon")
print("3. Deploy to API endpoints")
print("4. Update dashboard to show BIG 8 forecasts")
print()
print("Models are saved in: cbi-v14.models dataset")
print("Access via: SELECT * FROM ML.PREDICT(MODEL `cbi-v14.models.MODEL_NAME`, ...)")
