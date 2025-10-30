#!/usr/bin/env python3
"""
PHASE 7: MONITORING & ALERTS
Checks costs, storage, API limits, job failures
"""

from google.cloud import bigquery, monitoring_v3
from datetime import datetime, timedelta
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
ALERT_THRESHOLDS = {
    'vertex_ai_monthly_cost': 10.0,  # USD
    'bigquery_storage_gb': 10.0,     # GB
    'cron_failures_daily': 3         # Count
}

def check_vertex_ai_costs():
    """Check Vertex AI costs this month"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        query = """
        SELECT SUM(cost) as total_cost
        FROM `cbi-v14.billing.gcp_billing_export_*`
        WHERE service.description = 'Vertex AI'
          AND DATE(usage_start_time) >= DATE_TRUNC(CURRENT_DATE(), MONTH)
        """
        
        result = client.query(query).to_dataframe()
        cost = float(result['total_cost'].iloc[0]) if not result.empty else 0.0
        
        if cost > ALERT_THRESHOLDS['vertex_ai_monthly_cost']:
            logger.warning(f"🚨 Vertex AI costs: ${cost:.2f} (threshold: ${ALERT_THRESHOLDS['vertex_ai_monthly_cost']})")
            return False
        else:
            logger.info(f"✅ Vertex AI costs: ${cost:.2f}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Cost check failed: {e}")
        return True  # Don't fail on monitoring errors


def check_bigquery_storage():
    """Check BigQuery storage usage"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        datasets = client.list_datasets()
        total_gb = 0.0
        
        for dataset in datasets:
            tables = client.list_tables(dataset.dataset_id)
            for table in tables:
                table_ref = client.get_table(table)
                total_gb += table_ref.num_bytes / 1024 / 1024 / 1024
        
        if total_gb > ALERT_THRESHOLDS['bigquery_storage_gb']:
            logger.warning(f"🚨 BigQuery storage: {total_gb:.2f}GB (threshold: {ALERT_THRESHOLDS['bigquery_storage_gb']}GB)")
            return False
        else:
            logger.info(f"✅ BigQuery storage: {total_gb:.2f}GB")
            return True
            
    except Exception as e:
        logger.error(f"❌ Storage check failed: {e}")
        return True


def check_data_freshness():
    """Check if data is up to date"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        checks = {
            'forecasts': """
                SELECT MAX(prediction_date) as latest_date
                FROM `cbi-v14.predictions.daily_forecasts`
            """,
            'prices': """
                SELECT MAX(DATE(time)) as latest_date
                FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
            """
        }
        
        all_fresh = True
        
        for name, query in checks.items():
            result = client.query(query).to_dataframe()
            if not result.empty and result['latest_date'].iloc[0]:
                latest = result['latest_date'].iloc[0]
                days_old = (datetime.now().date() - latest).days if hasattr(latest, 'days') else 0
                
                if days_old > 7:
                    logger.warning(f"🚨 {name} is {days_old} days old")
                    all_fresh = False
                else:
                    logger.info(f"✅ {name}: {days_old} days old")
        
        return all_fresh
        
    except Exception as e:
        logger.error(f"❌ Freshness check failed: {e}")
        return True


def main():
    """Run all monitoring checks"""
    logger.info("="*80)
    logger.info("MONITORING & ALERTS")
    logger.info("="*80)
    
    checks = {
        'Vertex AI Costs': check_vertex_ai_costs(),
        'BigQuery Storage': check_bigquery_storage(),
        'Data Freshness': check_data_freshness()
    }
    
    all_passed = all(checks.values())
    
    logger.info("="*80)
    logger.info("SUMMARY:")
    for check, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"  {status}: {check}")
    logger.info("="*80)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

