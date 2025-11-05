#!/usr/bin/env python3
"""
Cloud Function: Daily Forecast Generation
Triggers: Cloud Scheduler (daily at 2 AM ET)
Output: Inserts into cbi-v14.predictions_uc1.production_forecasts

This function executes GENERATE_PRODUCTION_FORECASTS_V3.sql to generate
daily forecasts for all 4 horizons (1W, 1M, 3M, 6M) using BQML models.
"""

import os
import logging
from datetime import datetime, date
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project configuration
PROJECT = "cbi-v14"
DATASET = "predictions_uc1"
TABLE = "production_forecasts"

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT)


def get_sql_file_path():
    """Get the path to the SQL file"""
    # For Cloud Function deployment, SQL is in same directory
    # Try multiple possible locations
    possible_paths = [
        "GENERATE_PRODUCTION_FORECASTS_V3.sql",  # Same directory as main.py in Cloud Function
        os.path.join(os.path.dirname(__file__), "..", "bigquery_sql", "GENERATE_PRODUCTION_FORECASTS_V3.sql"),
        "bigquery_sql/GENERATE_PRODUCTION_FORECASTS_V3.sql",
        "/Users/zincdigital/CBI-V14/bigquery_sql/GENERATE_PRODUCTION_FORECASTS_V3.sql",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found SQL file at: {path}")
            return path
    
    raise FileNotFoundError(f"Could not find GENERATE_PRODUCTION_FORECASTS_V3.sql in any of: {possible_paths}")


def delete_existing_forecasts_for_today():
    """Delete any existing forecasts for today to avoid duplicates"""
    delete_query = f"""
    DELETE FROM `{PROJECT}.{DATASET}.{TABLE}`
    WHERE forecast_date = CURRENT_DATE()
    """
    
    try:
        job = client.query(delete_query)
        job.result()  # Wait for completion
        deleted_count = job.num_dml_affected_rows if hasattr(job, 'num_dml_affected_rows') else 0
        logger.info(f"Deleted {deleted_count} existing forecasts for today")
        return deleted_count
    except Exception as e:
        logger.warning(f"Could not delete existing forecasts (may not exist): {e}")
        return 0


def update_prediction_accuracy():
    """Update accuracy for predictions that have reached their target date"""
    accuracy_query = f"""
    INSERT INTO `{PROJECT}.{DATASET}.prediction_accuracy`
    SELECT 
      GENERATE_UUID() as accuracy_id,
      f.forecast_date,
      f.target_date,
      f.horizon,
      f.predicted_value,
      p.close as actual_value,
      ABS(f.predicted_value - p.close) as absolute_error,
      ABS((f.predicted_value - p.close) / p.close) * 100 as absolute_percentage_error,
      f.predicted_value - p.close as prediction_error,
      CASE 
        WHEN p.close BETWEEN f.lower_bound_80 AND f.upper_bound_80 THEN TRUE
        ELSE FALSE
      END as within_80_ci,
      CASE 
        WHEN f.lower_bound_95 IS NOT NULL AND f.upper_bound_95 IS NOT NULL THEN
          CASE 
            WHEN p.close BETWEEN f.lower_bound_95 AND f.upper_bound_95 THEN TRUE
            ELSE FALSE
          END
        ELSE FALSE
      END as within_95_ci,
      f.model_name,
      DATE_DIFF(f.target_date, f.forecast_date, DAY) as days_ahead,
      CURRENT_TIMESTAMP() as computed_at
    FROM `{PROJECT}.{DATASET}.{TABLE}` f
    INNER JOIN `{PROJECT}.forecasting_data_warehouse.soybean_oil_prices` p
      ON f.target_date = DATE(p.time)
    WHERE f.target_date = CURRENT_DATE()  -- Today's prices match past predictions
      AND NOT EXISTS (
        SELECT 1 FROM `{PROJECT}.{DATASET}.prediction_accuracy` pa
        WHERE pa.forecast_date = f.forecast_date 
          AND pa.target_date = f.target_date
          AND pa.horizon = f.horizon
      )
    """
    
    try:
        job = client.query(accuracy_query)
        job.result()
        updated_count = job.num_dml_affected_rows if hasattr(job, 'num_dml_affected_rows') else 0
        return updated_count
    except Exception as e:
        logger.error(f"Error updating accuracy: {e}")
        raise


def generate_daily_forecasts(request):
    """
    Cloud Function entry point for daily forecast generation.
    
    Args:
        request: Flask request object (for HTTP trigger)
    
    Returns:
        dict: Status and forecast count
    """
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info(f"🚀 Starting daily forecast generation at {start_time}")
    logger.info("=" * 80)
    
    try:
        # Step 1: Delete existing forecasts for today (avoid duplicates)
        deleted = delete_existing_forecasts_for_today()
        
        # Step 2: Read and execute the SQL file
        sql_path = get_sql_file_path()
        logger.info(f"Reading SQL from: {sql_path}")
        
        with open(sql_path, 'r', encoding='utf-8') as f:
            query = f.read()
        
        # Remove comments that might cause issues
        # Keep the query as-is since it's production SQL
        
        logger.info("Executing forecast generation SQL...")
        job = client.query(query, job_config=bigquery.QueryJobConfig(use_legacy_sql=False))
        job.result()  # Wait for completion
        
        if job.errors:
            raise Exception(f"Query job had errors: {job.errors}")
        
        logger.info(f"✅ SQL execution completed in {job.total_bytes_processed / 1024 / 1024:.2f} MB processed")
        
        # Step 3: Verify forecasts were created
        verify_query = f"""
        SELECT 
            COUNT(*) as forecast_count,
            COUNT(DISTINCT horizon) as horizon_count,
            STRING_AGG(DISTINCT horizon ORDER BY horizon) as horizons
        FROM `{PROJECT}.{DATASET}.{TABLE}`
        WHERE forecast_date = CURRENT_DATE()
        """
        
        result = client.query(verify_query).to_dataframe()
        forecast_count = int(result.iloc[0]['forecast_count'])
        horizon_count = int(result.iloc[0]['horizon_count'])
        horizons = result.iloc[0]['horizons']
        
        logger.info(f"Verification: Found {forecast_count} forecasts for {horizon_count} horizons: {horizons}")
        
        # Step 4: Validate results
        if forecast_count == 0:
            raise Exception("❌ No forecasts generated for today")
        
        if forecast_count < 4:
            logger.warning(f"⚠️ Expected 4 forecasts, got {forecast_count}")
        
        if horizon_count != 4:
            logger.warning(f"⚠️ Expected 4 horizons, got {horizon_count}: {horizons}")
        
        # Step 5: Get forecast details for logging
        details_query = f"""
        SELECT 
            horizon,
            predicted_value,
            confidence,
            market_regime,
            model_name
        FROM `{PROJECT}.{DATASET}.{TABLE}`
        WHERE forecast_date = CURRENT_DATE()
        ORDER BY 
            CASE horizon
                WHEN '1W' THEN 1
                WHEN '1M' THEN 2
                WHEN '3M' THEN 3
                WHEN '6M' THEN 4
            END
        """
        
        details = client.query(details_query).to_dataframe()
        logger.info("Generated forecasts:")
        for _, row in details.iterrows():
            logger.info(f"  {row['horizon']}: ${row['predicted_value']:.2f} (confidence: {row['confidence']:.1f}%, regime: {row['market_regime']})")
        
        # Step 6: Update prediction accuracy for predictions that have reached their target date
        logger.info("Updating prediction accuracy for past forecasts...")
        try:
            accuracy_updated = update_prediction_accuracy()
            logger.info(f"✅ Updated accuracy for {accuracy_updated} predictions")
        except Exception as acc_error:
            logger.warning(f"⚠️ Could not update accuracy (may not be needed): {acc_error}")
            accuracy_updated = 0
        
        # Step 7: Calculate execution time
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 80)
        logger.info(f"✅ Successfully generated {forecast_count} forecasts in {duration:.2f} seconds")
        logger.info(f"Completed at {end_time}")
        logger.info("=" * 80)
        
        return {
            "status": "success",
            "forecasts_generated": forecast_count,
            "horizons": horizons,
            "deleted_existing": deleted,
            "accuracy_updated": accuracy_updated,
            "execution_time_seconds": duration,
            "timestamp": end_time.isoformat()
        }
    
    except FileNotFoundError as e:
        error_msg = f"❌ SQL file not found: {e}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        error_msg = f"❌ Forecast generation failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Try to get more details about the error
        try:
            # Check if table exists
            table_ref = client.get_table(f"{PROJECT}.{DATASET}.{TABLE}")
            logger.info(f"Table exists: {table_ref.full_table_id}")
        except NotFound:
            error_msg += " (Table not found)"
        except Exception as check_error:
            logger.error(f"Error checking table: {check_error}")
        
        return {
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }


# For local testing
if __name__ == "__main__":
    from flask import Flask, request as flask_request
    
    app = Flask(__name__)
    
    @app.route("/", methods=["GET", "POST"])
    def test():
        result = generate_daily_forecasts(flask_request)
        return result, 200 if result.get("status") == "success" else 500
    
    print("🧪 Running in test mode. Start Flask server to test.")
    print("   Use: flask run or python -m flask run")
    print("   Then: curl -X POST http://localhost:5000/")

