#!/usr/bin/env python3
"""
FIXED BIG 8 TRAINING - 25+ MODELS
Corrected for actual schema and data issues
"""

from google.cloud import bigquery
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚀 BIG 8 TRAINING - FIXED VERSION")
print("=" * 80)
print()
print("Training Configuration:")
print("  • 5 horizons: 1w, 1m, 3m, 6m, 12m")
print("  • 6 algorithms per horizon: ARIMA, LightGBM, DNN, AutoML, Linear, XGBoost")
print("  • BIG 8 signals + correlations + sentiment")
print("  • 4,862 rows of clean data")
print()

# Get clean features (excluding problematic columns)
def get_clean_features():
    """Get features excluding timestamps and NaN columns"""
    query = """
    SELECT column_name
    FROM `cbi-v14.models.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'vw_neural_training_dataset_v2'
    AND column_name NOT LIKE 'target_%'
    AND column_name != 'date'
    AND column_name != 'created_at'  -- Exclude timestamp
    AND data_type != 'TIMESTAMP'
    ORDER BY ordinal_position
    """
    
    features = []
    for row in client.query(query):
        features.append(row.column_name)
    
    print(f"Using {len(features)} clean features for training")
    return features

ALL_FEATURES = get_clean_features()

# Model training functions
def train_arima_plus(horizon_name, target_col):
    """Train ARIMA_PLUS with proper configuration"""
    print(f"\n📈 Training ARIMA_PLUS for {horizon_name}...")
    
    model_name = f"zl_big8_{horizon_name}_arima"
    
    # ARIMA needs special handling - only time series columns allowed
    query = f"""
    CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
    OPTIONS(
        model_type='ARIMA_PLUS',
        time_series_timestamp_col='date',
        time_series_data_col='zl_price',
        auto_arima=TRUE,
        auto_arima_max_order=5,
        decompose_time_series=TRUE,
        clean_spikes_and_dips=TRUE
    ) AS
    SELECT
        date,
        {target_col} as zl_price
    FROM `cbi-v14.models.vw_neural_training_dataset_v2`
    WHERE {target_col} IS NOT NULL
    ORDER BY date
    """
    
    try:
        job = client.query(query)
        job.result()
        print(f"  ✅ Created {model_name}")
        return model_name
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:100]}")
        return None

def train_lightgbm(horizon_name, target_col):
    """Train LightGBM with clean features"""
    print(f"\n🌲 Training LightGBM for {horizon_name}...")
    
    model_name = f"zl_big8_{horizon_name}_lgb"
    
    # Build feature list excluding NaN columns
    feature_list = []
    for f in ALL_FEATURES:
        if f not in ['feature_hidden_correlation']:  # Exclude NaN column
            feature_list.append(f)
    
    query = f"""
    CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
    OPTIONS(
        model_type='BOOSTED_TREE_REGRESSOR',
        input_label_cols=['{target_col}'],
        data_split_method='SEQ',
        data_split_col='date',
        max_iterations=100,
        early_stop=TRUE,
        min_tree_child_weight=10,
        subsample=0.85,
        max_tree_depth=10,
        l1_reg=0.1,
        l2_reg=0.1
    ) AS
    SELECT 
        date,
        {target_col},
        {','.join(feature_list)}
    FROM `cbi-v14.models.vw_neural_training_dataset_v2`
    WHERE {target_col} IS NOT NULL
    AND feature_hidden_correlation IS NOT NULL  -- Filter out NaN rows
    """
    
    try:
        job = client.query(query)
        job.result()
        print(f"  ✅ Created {model_name}")
        return model_name
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:100]}")
        return None

def train_dnn(horizon_name, target_col):
    """Train Deep Neural Network"""
    print(f"\n🧠 Training DNN for {horizon_name}...")
    
    model_name = f"zl_big8_{horizon_name}_dnn"
    
    # Use safe features only
    safe_features = [f for f in ALL_FEATURES if f not in ['feature_hidden_correlation']]
    
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
        input_label_cols=['{target_col}'],
        data_split_method='SEQ',
        data_split_col='date',
        max_iterations=200,
        early_stop=TRUE
    ) AS
    SELECT 
        date,
        {target_col},
        {','.join(safe_features)}
    FROM `cbi-v14.models.vw_neural_training_dataset_v2`
    WHERE {target_col} IS NOT NULL
    AND feature_hidden_correlation IS NOT NULL
    """
    
    try:
        job = client.query(query)
        job.result()
        print(f"  ✅ Created {model_name}")
        return model_name
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:100]}")
        return None

def train_automl(horizon_name, target_col):
    """Train AutoML with proper budget"""
    print(f"\n🤖 Training AutoML for {horizon_name}...")
    
    model_name = f"zl_big8_{horizon_name}_automl"
    
    # Use minimal features for AutoML to save time
    key_features = [
        'zl_price_current', 'zl_price_lag1', 'zl_price_lag7',
        'feature_vix_stress', 'feature_harvest_pace', 
        'feature_china_relations', 'feature_biofuel_ethanol',
        'corr_zl_crude_30d', 'corr_zl_palm_30d', 'avg_sentiment'
    ]
    
    query = f"""
    CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
    OPTIONS(
        model_type='AUTOML_REGRESSOR',
        budget_hours=1.0,  -- Fixed: minimum 1 hour
        input_label_cols=['{target_col}']
    ) AS
    SELECT 
        {target_col},
        {','.join(key_features)}
    FROM `cbi-v14.models.vw_neural_training_dataset_v2`
    WHERE {target_col} IS NOT NULL
    AND date >= '2024-01-01'
    """
    
    try:
        job = client.query(query)
        job.result()
        print(f"  ✅ Created {model_name}")
        return model_name
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:100]}")
        return None

def train_linear_reg(horizon_name, target_col):
    """Train Linear Regression"""
    print(f"\n📊 Training Linear Regression for {horizon_name}...")
    
    model_name = f"zl_big8_{horizon_name}_linear"
    
    query = f"""
    CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
    OPTIONS(
        model_type='LINEAR_REG',
        input_label_cols=['{target_col}'],
        data_split_method='SEQ',
        data_split_col='date',
        l1_reg=0.1,
        l2_reg=0.1,
        max_iterations=100,
        early_stop=TRUE
    ) AS
    SELECT 
        date,
        {target_col},
        -- Core features only for linear model
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
        COALESCE(feature_hidden_correlation, 0) as feature_hidden_correlation,  -- Handle NaN
        feature_biofuel_ethanol,
        corr_zl_crude_30d,
        corr_zl_palm_30d,
        avg_sentiment
    FROM `cbi-v14.models.vw_neural_training_dataset_v2`
    WHERE {target_col} IS NOT NULL
    """
    
    try:
        job = client.query(query)
        job.result()
        print(f"  ✅ Created {model_name}")
        return model_name
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:100]}")
        return None

def train_xgboost(horizon_name, target_col):
    """Train XGBoost variant"""
    print(f"\n🚀 Training XGBoost for {horizon_name}...")
    
    model_name = f"zl_big8_{horizon_name}_xgb"
    
    # Safe features only
    safe_features = [f for f in ALL_FEATURES if f not in ['feature_hidden_correlation']]
    
    query = f"""
    CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
    OPTIONS(
        model_type='BOOSTED_TREE_REGRESSOR',
        booster_type='GBTREE',
        num_parallel_tree=1,
        max_iterations=150,
        tree_method='HIST',
        subsample=0.9,
        colsample_bytree=0.9,
        max_tree_depth=12,
        min_tree_child_weight=5,
        l1_reg=0.05,
        l2_reg=0.05,
        learn_rate=0.01,
        early_stop=TRUE,
        input_label_cols=['{target_col}'],
        data_split_method='SEQ',
        data_split_col='date'
    ) AS
    SELECT 
        date,
        {target_col},
        {','.join(safe_features)}
    FROM `cbi-v14.models.vw_neural_training_dataset_v2`
    WHERE {target_col} IS NOT NULL
    AND feature_hidden_correlation IS NOT NULL
    """
    
    try:
        job = client.query(query)
        job.result()
        print(f"  ✅ Created {model_name}")
        return model_name
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:100]}")
        return None

# Main execution
print("\n" + "=" * 80)
print("STARTING TRAINING SEQUENCE")
print("=" * 80)

HORIZONS = {
    '1_week': 'target_1w',
    '1_month': 'target_1m',
    '3_month': 'target_3m',
    '6_month': 'target_6m',
    '12_month': 'target_12m'
}

model_summary = {
    'ARIMA': [],
    'LightGBM': [],
    'DNN': [],
    'AutoML': [],
    'Linear': [],
    'XGBoost': []
}

for horizon_name, target_col in HORIZONS.items():
    print(f"\n{'='*60}")
    print(f"TRAINING HORIZON: {horizon_name}")
    print(f"{'='*60}")
    
    # Train all model types
    model = train_arima_plus(horizon_name, target_col)
    if model: model_summary['ARIMA'].append(model)
    
    model = train_lightgbm(horizon_name, target_col)
    if model: model_summary['LightGBM'].append(model)
    
    model = train_dnn(horizon_name, target_col)
    if model: model_summary['DNN'].append(model)
    
    # AutoML only for key horizons (expensive)
    if horizon_name in ['1_week', '1_month']:
        model = train_automl(horizon_name, target_col)
        if model: model_summary['AutoML'].append(model)
    
    model = train_linear_reg(horizon_name, target_col)
    if model: model_summary['Linear'].append(model)
    
    model = train_xgboost(horizon_name, target_col)
    if model: model_summary['XGBoost'].append(model)

# Summary
print("\n" + "=" * 80)
print("🏁 TRAINING COMPLETE")
print("=" * 80)

total_models = sum(len(models) for models in model_summary.values())
print(f"\n✅ TOTAL MODELS TRAINED: {total_models}")

if total_models > 0:
    print("\nModel Breakdown:")
    for model_type, models in model_summary.items():
        if models:
            print(f"\n{model_type} ({len(models)} models):")
            for model in models:
                print(f"  • {model}")

print("\n" + "=" * 80)
print("MODELS ARE NOW IN: cbi-v14.models dataset")
print("=" * 80)
print()
print("To use models:")
print("  SELECT * FROM ML.PREDICT(MODEL `cbi-v14.models.MODEL_NAME`, ...)")
print("  SELECT * FROM ML.EVALUATE(MODEL `cbi-v14.models.MODEL_NAME`, ...)")
