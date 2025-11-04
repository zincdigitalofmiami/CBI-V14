#!/usr/bin/env python3
"""
Cloud Function: Daily Prediction Monitoring
Runs after forecast generation to check quality, staleness, completeness, and accuracy
"""

import os
import json
import logging
from datetime import datetime, date, timedelta
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project configuration
PROJECT = "cbi-v14"
DATASET = "predictions_uc1"
FORECAST_TABLE = "production_forecasts"
ACCURACY_TABLE = "prediction_accuracy"
MONITORING_TABLE = "monitoring_checks"

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT)


def monitor_predictions(request):
    """
    Cloud Function entry point for daily prediction monitoring.
    
    Args:
        request: Flask request object (for HTTP trigger)
    
    Returns:
        dict: Status and check results
    """
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info(f"🔍 Starting prediction monitoring at {start_time}")
    logger.info("=" * 80)
    
    checks = []
    today = date.today()
    
    try:
        # Check 1: Staleness - Are today's forecasts present?
        logger.info("Check 1: Checking for stale predictions...")
        staleness_check = f"""
        SELECT COUNT(*) as count
        FROM `{PROJECT}.{DATASET}.{FORECAST_TABLE}`
        WHERE forecast_date = CURRENT_DATE()
        """
        result = client.query(staleness_check).to_dataframe()
        forecast_count = int(result.iloc[0]['count'])
        
        if forecast_count == 0:
            checks.append({
                "check_type": "staleness",
                "status": "FAIL",
                "message": "No forecasts generated for today",
                "details": {"forecast_count": 0, "expected": 4}
            })
            logger.error("❌ FAIL: No forecasts for today")
        elif forecast_count < 4:
            checks.append({
                "check_type": "completeness",
                "status": "WARN",
                "message": f"Only {forecast_count}/4 forecasts generated",
                "details": {"forecast_count": forecast_count, "expected": 4}
            })
            logger.warning(f"⚠️ WARN: Only {forecast_count}/4 forecasts")
        else:
            checks.append({
                "check_type": "staleness",
                "status": "PASS",
                "message": "All forecasts present",
                "details": {"forecast_count": forecast_count, "expected": 4}
            })
            logger.info(f"✅ PASS: {forecast_count} forecasts present")
        
        # Check 2: Quality - Are predictions in reasonable range?
        logger.info("Check 2: Checking prediction quality...")
        quality_check = f"""
        SELECT 
          horizon,
          predicted_value,
          CASE 
            WHEN predicted_value < 25 THEN 'FAIL'
            WHEN predicted_value > 90 THEN 'FAIL'
            WHEN predicted_value BETWEEN 45 AND 60 THEN 'PASS'
            ELSE 'WARN'
          END as quality_status
        FROM `{PROJECT}.{DATASET}.{FORECAST_TABLE}`
        WHERE forecast_date = CURRENT_DATE()
        """
        quality_results = client.query(quality_check).to_dataframe()
        
        for _, row in quality_results.iterrows():
            checks.append({
                "check_type": "quality",
                "status": row['quality_status'],
                "message": f"{row['horizon']} forecast: ${row['predicted_value']:.2f}",
                "details": {
                    "horizon": row['horizon'],
                    "predicted_value": float(row['predicted_value'])
                }
            })
            if row['quality_status'] == 'FAIL':
                logger.error(f"❌ FAIL: {row['horizon']} forecast ${row['predicted_value']:.2f} out of range")
            elif row['quality_status'] == 'WARN':
                logger.warning(f"⚠️ WARN: {row['horizon']} forecast ${row['predicted_value']:.2f} unusual")
            else:
                logger.info(f"✅ PASS: {row['horizon']} forecast ${row['predicted_value']:.2f} in range")
        
        # Check 3: Accuracy degradation (if accuracy data exists)
        logger.info("Check 3: Checking accuracy degradation...")
        try:
            accuracy_check = f"""
            WITH recent_mape AS (
              SELECT 
                horizon,
                AVG(absolute_percentage_error) as recent_mape
              FROM `{PROJECT}.{DATASET}.{ACCURACY_TABLE}`
              WHERE forecast_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                AND actual_value IS NOT NULL
              GROUP BY horizon
            ),
            baseline_mape AS (
              SELECT 
                horizon,
                AVG(absolute_percentage_error) as baseline_mape
              FROM `{PROJECT}.{DATASET}.{ACCURACY_TABLE}`
              WHERE forecast_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                AND forecast_date < DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                AND actual_value IS NOT NULL
              GROUP BY horizon
            )
            SELECT 
              r.horizon,
              r.recent_mape,
              b.baseline_mape,
              (r.recent_mape / b.baseline_mape - 1) * 100 as degradation_pct
            FROM recent_mape r
            LEFT JOIN baseline_mape b ON r.horizon = b.horizon
            WHERE r.recent_mape > b.baseline_mape * 1.5  -- 50% worse than baseline
            """
            acc_results = client.query(accuracy_check).to_dataframe()
            
            if not acc_results.empty:
                for _, row in acc_results.iterrows():
                    checks.append({
                        "check_type": "accuracy",
                        "status": "WARN",
                        "message": f"{row['horizon']} MAPE degradation: {row['recent_mape']:.2f}% vs baseline {row['baseline_mape']:.2f}%",
                        "details": {
                            "horizon": row['horizon'],
                            "recent_mape": float(row['recent_mape']),
                            "baseline_mape": float(row['baseline_mape']),
                            "degradation_pct": float(row['degradation_pct'])
                        }
                    })
                    logger.warning(f"⚠️ WARN: {row['horizon']} accuracy degraded by {row['degradation_pct']:.1f}%")
            else:
                logger.info("✅ PASS: No accuracy degradation detected")
        except Exception as acc_error:
            logger.info(f"ℹ️ Accuracy check skipped (insufficient data): {acc_error}")
        
        # Check 4: Check for forecasts older than 24 hours
        logger.info("Check 4: Checking for stale forecasts...")
        stale_check = f"""
        SELECT 
          MAX(created_at) as latest_forecast_time,
          TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(created_at), HOUR) as hours_since_last
        FROM `{PROJECT}.{DATASET}.{FORECAST_TABLE}`
        WHERE forecast_date = CURRENT_DATE()
        """
        stale_result = client.query(stale_check).to_dataframe()
        
        if not stale_result.empty and not stale_result.iloc[0]['latest_forecast_time'] is None:
            hours_since = float(stale_result.iloc[0]['hours_since_last'])
            if hours_since > 24:
                checks.append({
                    "check_type": "staleness",
                    "status": "WARN",
                    "message": f"Last forecast is {hours_since:.1f} hours old",
                    "details": {"hours_since_last": hours_since}
                })
                logger.warning(f"⚠️ WARN: Forecasts are {hours_since:.1f} hours old")
        
        # Store checks in BigQuery
        logger.info("Storing monitoring checks...")
        rows = []
        for i, check in enumerate(checks):
            check_id = f"{today}_{check['check_type']}_{i}"
            rows.append({
                "check_id": check_id,
                "check_date": today.isoformat(),
                "check_type": check['check_type'],
                "status": check['status'],
                "message": check['message'],
                "details": json.dumps(check['details']),
                "created_at": datetime.now().isoformat()
            })
        
        if rows:
            # Convert to BigQuery format
            from google.cloud.bigquery import LoadJobConfig
            job_config = LoadJobConfig(
                write_disposition="WRITE_APPEND",
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                schema=[
                    bigquery.SchemaField("check_id", "STRING"),
                    bigquery.SchemaField("check_date", "DATE"),
                    bigquery.SchemaField("check_type", "STRING"),
                    bigquery.SchemaField("status", "STRING"),
                    bigquery.SchemaField("message", "STRING"),
                    bigquery.SchemaField("details", "JSON"),
                    bigquery.SchemaField("created_at", "TIMESTAMP"),
                ]
            )
            
            # Write to BigQuery
            table_ref = client.dataset(DATASET).table(MONITORING_TABLE)
            job = client.load_table_from_json(rows, table_ref, job_config=job_config)
            job.result()
            logger.info(f"✅ Stored {len(rows)} monitoring checks")
        
        # Count failures and warnings
        failures = [c for c in checks if c['status'] == 'FAIL']
        warnings = [c for c in checks if c['status'] == 'WARN']
        
        # Calculate execution time
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 80)
        logger.info(f"✅ Monitoring complete: {len(checks)} checks, {len(failures)} failures, {len(warnings)} warnings")
        logger.info(f"Completed in {duration:.2f} seconds")
        logger.info("=" * 80)
        
        return {
            "status": "success",
            "checks_run": len(checks),
            "failures": len(failures),
            "warnings": len(warnings),
            "checks": checks,
            "execution_time_seconds": duration,
            "timestamp": end_time.isoformat()
        }
    
    except Exception as e:
        error_msg = f"❌ Monitoring failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
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
        result = monitor_predictions(flask_request)
        return result, 200 if result.get("status") == "success" else 500
    
    print("🧪 Running in test mode. Start Flask server to test.")
    print("   Use: flask run or python -m flask run")
    print("   Then: curl -X POST http://localhost:5000/")

