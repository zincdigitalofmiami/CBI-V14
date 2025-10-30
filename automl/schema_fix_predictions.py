"""
Schema-Fixed Endpoint Trickery for Vertex AI AutoML Predictions
Handles type conversions, date formatting, and NaN values correctly
"""
from google.cloud import aiplatform
from google.cloud import bigquery
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/zincdigital/CBI-V14/logs/schema_fix_predictions.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize clients
aiplatform.init(project='cbi-v14', location='us-central1')
bq_client = bigquery.Client(project='cbi-v14')

# Model IDs from MASTER_TRAINING_PLAN - ALL 4 MODELS
MODEL_INFO = {
    '1W': {
        'id': '575258986094264320',
        'name': 'cbi_v14_automl_pilot_1w',
        'mape': 2.02,
        'days_ahead': 7,
        'existing_endpoint': '7286867078038945792'  # Already deployed!
    },
    '1M': {
        'id': '274643710967283712',
        'name': 'soybean_oil_1m_model_FINAL_20251029_1147',
        'mape': 2.50,  # Estimated, need actual metrics
        'days_ahead': 30
    },
    '3M': {
        'id': '3157158578716934144',
        'name': 'soybean_oil_3m_final_v14_20251029_0808',
        'mape': 2.68,
        'days_ahead': 90
    },
    '6M': {
        'id': '3788577320223113216',
        'name': 'soybean_oil_6m_model_v14_20251028_1737',
        'mape': 2.51,
        'days_ahead': 180
    }
}

def apply_schema_fixes(df):
    """Apply comprehensive schema fixes to match model expectations"""
    logger.info("🔧 Applying schema fixes to input data...")
    
    # Make a copy to avoid modifying original
    df_fixed = df.copy()
    
    # CRITICAL FIX #1: Convert ALL integer columns to STRING
    # Vertex AI exports integers as strings during training dataset creation
    int_columns = df_fixed.select_dtypes(include=['int64', 'Int64']).columns.tolist()
    
    logger.info(f"   Converting {len(int_columns)} integer columns to STRING:")
    for col in int_columns:
        original_dtype = df_fixed[col].dtype
        df_fixed[col] = df_fixed[col].astype(str)
        if int_columns.index(col) < 5:  # Log first 5
            logger.info(f"   ✓ {col}: {original_dtype} → STRING")
    
    if len(int_columns) > 5:
        logger.info(f"   ✓ ... and {len(int_columns) - 5} more integer columns")
    
    # CRITICAL FIX #2: Format dates as 'YYYY-MM-DD' strings
    date_cols = df_fixed.select_dtypes(include=['datetime64']).columns.tolist()
    
    # Also check for 'date' column specifically
    if 'date' in df_fixed.columns and 'date' not in date_cols:
        date_cols.append('date')
    
    for col in date_cols:
        try:
            if df_fixed[col].dtype == 'datetime64[ns]':
                df_fixed[col] = df_fixed[col].dt.strftime('%Y-%m-%d')
            else:
                # Try to parse and format
                df_fixed[col] = pd.to_datetime(df_fixed[col]).dt.strftime('%Y-%m-%d')
            logger.info(f"   ✓ Formatted {col} as 'YYYY-MM-DD' string")
        except Exception as e:
            logger.warning(f"   ⚠️  Could not format {col}: {str(e)}")
    
    # CRITICAL FIX #3: Replace NaN values with None (required by Vertex AI)
    null_count_before = df_fixed.isnull().sum().sum()
    df_fixed = df_fixed.replace({np.nan: None})
    logger.info(f"   ✓ Replaced {null_count_before} NaN values with None")
    
    # CRITICAL FIX #4: Drop all target columns (models don't need them for prediction)
    # Target columns should not be present in prediction input at all
    target_cols = ['target_1w', 'target_1m', 'target_3m', 'target_6m']
    dropped_targets = []
    for col in target_cols:
        if col in df_fixed.columns:
            df_fixed = df_fixed.drop(columns=[col])
            dropped_targets.append(col)
    
    if dropped_targets:
        logger.info(f"   ✓ Dropped {len(dropped_targets)} target columns (not needed for prediction)")
    
    # Log sample of fixed data
    logger.info("\n📋 Sample of schema-fixed data (first 5 columns):")
    for col in list(df_fixed.columns)[:5]:
        val = df_fixed[col].iloc[0]
        dtype = type(val).__name__
        logger.info(f"   {col:30s} | {dtype:10s} | {str(val)[:40]}")
    
    return df_fixed

def get_prediction_input():
    """Get properly formatted input data with correct schema for the model"""
    # Query to get the latest data for prediction
    query = """
    SELECT *
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE date IS NOT NULL
    ORDER BY date DESC
    LIMIT 1
    """
    
    logger.info("📥 Fetching latest data from training dataset...")
    df = bq_client.query(query).to_dataframe()
    logger.info(f"✅ Retrieved data with {len(df.columns)} columns for date: {df['date'].iloc[0]}")
    
    # Apply all schema fixes
    df_fixed = apply_schema_fixes(df)
    
    # Convert to dictionary for prediction
    instance = df_fixed.to_dict('records')[0]
    
    logger.info(f"✅ Prepared prediction instance with {len(instance)} features")
    return instance

def save_predictions_to_bigquery(horizon, prediction_data):
    """Save predictions to BigQuery"""
    table_id = 'cbi-v14.predictions.monthly_vertex_predictions'
    
    # Check if table exists, if not create it
    try:
        bq_client.get_table(table_id)
        logger.info(f"✅ Table {table_id} exists")
    except Exception:
        logger.info(f"📊 Creating new table: {table_id}")
        schema = [
            bigquery.SchemaField("horizon", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("prediction_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("target_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("predicted_price", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("confidence_lower", "FLOAT"),
            bigquery.SchemaField("confidence_upper", "FLOAT"),
            bigquery.SchemaField("mape", "FLOAT"),
            bigquery.SchemaField("model_id", "STRING"),
            bigquery.SchemaField("model_name", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
        ]
        
        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="prediction_date"
        )
        
        bq_client.create_table(table)
        logger.info(f"✅ Created BigQuery table: {table_id}")
    
    # Insert the prediction data
    rows_to_insert = [prediction_data]
    errors = bq_client.insert_rows_json(table_id, rows_to_insert)
    
    if errors == []:
        logger.info(f"✅ Successfully saved {horizon} prediction to BigQuery")
    else:
        logger.error(f"❌ Error inserting data: {errors}")
        raise Exception(f"Failed to insert data: {errors}")

def run_single_model_test(horizon='1W'):
    """Test with a single model before running all"""
    logger.info(f"\n{'='*70}")
    logger.info(f"🧪 TESTING SINGLE MODEL: {horizon}")
    logger.info(f"{'='*70}\n")
    
    if horizon not in MODEL_INFO:
        logger.error(f"❌ Invalid horizon: {horizon}")
        return False
    
    info = MODEL_INFO[horizon]
    model_id = info['id']
    model_name = info['name']
    mape = info['mape']
    days_ahead = info['days_ahead']
    
    # Create temporary endpoint
    endpoint = aiplatform.Endpoint.create(
        display_name=f"test_endpoint_{horizon}_{int(time.time())}"
    )
    logger.info(f"✅ Created test endpoint: {endpoint.display_name}")
    
    try:
        # Get input data with schema fixes
        instance = get_prediction_input()
        
        # Deploy model
        model = aiplatform.Model(f"projects/cbi-v14/locations/us-central1/models/{model_id}")
        logger.info(f"🚀 Deploying {horizon} model ({model_name})...")
        
        deployed_model = endpoint.deploy(
            model=model,
            deployed_model_display_name=f"{horizon}_test",
            machine_type="n1-standard-4",
            min_replica_count=1,
            max_replica_count=1,
            sync=True
        )
        logger.info(f"✅ Model deployed successfully")
        
        # Get prediction
        logger.info(f"🔍 Getting prediction for {horizon} horizon...")
        prediction_response = endpoint.predict(instances=[instance])
        
        # Extract prediction value (handle different response formats)
        raw_prediction = prediction_response.predictions[0]
        logger.info(f"   Raw prediction response: {raw_prediction}")
        
        # AutoML responses can be dict or direct value
        if isinstance(raw_prediction, dict):
            # Try common keys
            if 'value' in raw_prediction:
                prediction_value = raw_prediction['value']
            elif 'predicted_value' in raw_prediction:
                prediction_value = raw_prediction['predicted_value']
            else:
                # Use first numeric value found
                prediction_value = next(v for v in raw_prediction.values() if isinstance(v, (int, float)))
        else:
            prediction_value = raw_prediction
        
        logger.info(f"✅ Prediction received: ${float(prediction_value):.2f}")
        
        # Calculate confidence intervals
        confidence_lower = prediction_value * (1 - (mape / 100))
        confidence_upper = prediction_value * (1 + (mape / 100))
        
        # Calculate dates
        current_date = datetime.now().date()
        target_date = current_date + timedelta(days=days_ahead)
        
        # Save to BigQuery
        prediction_data = {
            "horizon": horizon,
            "prediction_date": current_date.isoformat(),
            "target_date": target_date.isoformat(),
            "predicted_price": float(prediction_value),
            "confidence_lower": float(confidence_lower),
            "confidence_upper": float(confidence_upper),
            "mape": float(mape),
            "model_id": model_id,
            "model_name": model_name,
            "created_at": datetime.now().isoformat()
        }
        
        save_predictions_to_bigquery(horizon, prediction_data)
        
        # Undeploy
        logger.info(f"🧹 Undeploying model...")
        endpoint.undeploy_all()
        logger.info(f"✅ Model undeployed")
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ TEST SUCCESSFUL FOR {horizon} MODEL")
        logger.info(f"{'='*70}\n")
        
        return True
    
    except Exception as e:
        logger.error(f"\n{'='*70}")
        logger.error(f"❌ TEST FAILED FOR {horizon} MODEL")
        logger.error(f"Error: {str(e)}")
        logger.error(f"{'='*70}\n")
        
        # Try to clean up
        try:
            endpoint.undeploy_all()
        except:
            pass
        
        return False
    
    finally:
        # Delete endpoint
        try:
            logger.info(f"🧹 Deleting test endpoint...")
            endpoint.delete()
            logger.info(f"✅ Test endpoint deleted")
        except Exception as e:
            logger.error(f"❌ Error deleting endpoint: {str(e)}")

def run_all_models():
    """Execute endpoint trickery for all models sequentially"""
    logger.info(f"\n{'='*70}")
    logger.info(f"🚀 GETTING PREDICTIONS FROM ALL 4 MODELS")
    logger.info(f"{'='*70}\n")
    
    results = {}
    
    # Get input data once (same for all models)
    instance = get_prediction_input()
    
    # Process each model sequentially
    for horizon, info in MODEL_INFO.items():
            logger.info(f"\n{'-'*70}")
            logger.info(f"Processing {horizon} horizon...")
            logger.info(f"{'-'*70}")
            
            model_id = info['id']
            model_name = info['name']
            mape = info['mape']
            days_ahead = info['days_ahead']
            
            try:
                # Deploy model
                model = aiplatform.Model(f"projects/cbi-v14/locations/us-central1/models/{model_id}")
                logger.info(f"🚀 Deploying model: {model_name}...")
                
                start_time = time.time()
                deployed_model = endpoint.deploy(
                    model=model,
                    deployed_model_display_name=f"{horizon}_model",
                    machine_type="n1-standard-4",
                    min_replica_count=1,
                    max_replica_count=1,
                    sync=True
                )
                deploy_time = time.time() - start_time
                logger.info(f"✅ Model deployed in {deploy_time:.1f} seconds")
                
                # Get prediction
                logger.info(f"🔍 Getting prediction...")
                prediction_response = endpoint.predict(instances=[instance])
                
                # Extract prediction value (handle different response formats)
                raw_prediction = prediction_response.predictions[0]
                logger.info(f"   Raw prediction response: {raw_prediction}")
                
                if isinstance(raw_prediction, dict):
                    if 'value' in raw_prediction:
                        prediction_value = raw_prediction['value']
                    elif 'predicted_value' in raw_prediction:
                        prediction_value = raw_prediction['predicted_value']
                    else:
                        prediction_value = next(v for v in raw_prediction.values() if isinstance(v, (int, float)))
                else:
                    prediction_value = raw_prediction
                
                logger.info(f"✅ Prediction: ${float(prediction_value):.2f}")
                
                # Calculate confidence intervals
                confidence_lower = prediction_value * (1 - (mape / 100))
                confidence_upper = prediction_value * (1 + (mape / 100))
                
                # Calculate dates
                current_date = datetime.now().date()
                target_date = current_date + timedelta(days=days_ahead)
                
                # Save to BigQuery
                prediction_data = {
                    "horizon": horizon,
                    "prediction_date": current_date.isoformat(),
                    "target_date": target_date.isoformat(),
                    "predicted_price": float(prediction_value),
                    "confidence_lower": float(confidence_lower),
                    "confidence_upper": float(confidence_upper),
                    "mape": float(mape),
                    "model_id": model_id,
                    "model_name": model_name,
                    "created_at": datetime.now().isoformat()
                }
                
                save_predictions_to_bigquery(horizon, prediction_data)
                
                # Undeploy immediately
                logger.info(f"🧹 Undeploying model...")
                endpoint.undeploy_all()
                logger.info(f"✅ Model undeployed")
                
                results[horizon] = {
                    "status": "SUCCESS",
                    "prediction": prediction_value,
                    "deploy_time": deploy_time
                }
                
            except Exception as e:
                logger.error(f"❌ Error processing {horizon}: {str(e)}")
                results[horizon] = {
                    "status": "FAILED",
                    "error": str(e)
                }
                
                # Try to undeploy on error
                try:
                    endpoint.undeploy_all()
                except:
                    pass
    
    finally:
        # Delete endpoint
        try:
            logger.info(f"\n🧹 Deleting endpoint...")
            endpoint.delete()
            logger.info(f"✅ Endpoint deleted")
        except Exception as e:
            logger.error(f"❌ Error deleting endpoint: {str(e)}")
    
    # Print summary
    logger.info(f"\n{'='*70}")
    logger.info(f"PROCESS COMPLETE - SUMMARY")
    logger.info(f"{'='*70}")
    for horizon, result in results.items():
        if result["status"] == "SUCCESS":
            logger.info(f"✅ {horizon}: ${result['prediction']:.2f} (deployed in {result['deploy_time']:.1f}s)")
        else:
            logger.error(f"❌ {horizon}: {result['error']}")
    logger.info(f"{'='*70}\n")
    
    return results

if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Run single model test
        horizon = sys.argv[2] if len(sys.argv) > 2 else '1W'
        logger.info(f"🧪 Running single model test for {horizon}...")
        success = run_single_model_test(horizon)
        sys.exit(0 if success else 1)
    else:
        # Run all models
        logger.info("🚀 Running full endpoint trickery process...")
        results = run_all_models()
        
        # Exit with error if any failed
        failures = [h for h, r in results.items() if r["status"] == "FAILED"]
        if failures:
            logger.error(f"Process completed with {len(failures)} failures")
            sys.exit(1)
        else:
            logger.info("Process completed successfully!")
            sys.exit(0)

