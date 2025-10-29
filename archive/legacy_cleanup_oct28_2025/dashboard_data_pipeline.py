#!/usr/bin/env python3
"""
DASHBOARD DATA PIPELINE
Prepares REAL data from V4 models for dashboard consumption.
Stores prediction metadata in BigQuery for dashboard queries.
NO FAKE DATA - Only actual model outputs and calculated metrics.
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardDataPipeline:
    """Pipeline to prepare real V4 model data for dashboard"""
    
    def __init__(self):
        self.client = bigquery.Client(project='cbi-v14')
        self.dashboard_dataset = 'cbi-v14.dashboard'
        self.ensure_dashboard_dataset()
        
    def ensure_dashboard_dataset(self):
        """Create dashboard dataset if it doesn't exist"""
        try:
            self.client.create_dataset(self.dashboard_dataset, exists_ok=True)
            logger.info(f"Dashboard dataset {self.dashboard_dataset} ready")
        except Exception as e:
            logger.error(f"Error creating dashboard dataset: {e}")
            
    def create_prediction_history_table(self):
        """
        Create table to store prediction history with metadata
        """
        schema = [
            bigquery.SchemaField("prediction_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("prediction_timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("input_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("horizon", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("prediction_value", "FLOAT64", mode="REQUIRED"),
            bigquery.SchemaField("lower_68_bound", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("upper_68_bound", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("lower_95_bound", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("upper_95_bound", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("regime", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("vix_current", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("model_version", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("feature_importance", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("accuracy_metrics", "JSON", mode="NULLABLE")
        ]
        
        table_id = f"{self.dashboard_dataset}.prediction_history"
        table = bigquery.Table(table_id, schema=schema)
        
        try:
            table = self.client.create_table(table, exists_ok=True)
            logger.info(f"Prediction history table created: {table_id}")
        except Exception as e:
            logger.error(f"Error creating prediction history table: {e}")
            
    def create_regime_history_table(self):
        """
        Create table to track regime changes over time
        """
        schema = [
            bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("regime", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("vix_current", "FLOAT64", mode="REQUIRED"),
            bigquery.SchemaField("vix_threshold", "FLOAT64", mode="REQUIRED"),
            bigquery.SchemaField("regime_duration_days", "INT64", mode="NULLABLE")
        ]
        
        table_id = f"{self.dashboard_dataset}.regime_history"
        table = bigquery.Table(table_id, schema=schema)
        
        try:
            table = self.client.create_table(table, exists_ok=True)
            logger.info(f"Regime history table created: {table_id}")
        except Exception as e:
            logger.error(f"Error creating regime history table: {e}")
            
    def create_performance_metrics_table(self):
        """
        Create table to track model performance over time
        """
        schema = [
            bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("horizon", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("mae", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("mape", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("rmse", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("directional_accuracy", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("correlation", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("prediction_count", "INT64", mode="NULLABLE"),
            bigquery.SchemaField("regime", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("evaluation_period_days", "INT64", mode="REQUIRED")
        ]
        
        table_id = f"{self.dashboard_dataset}.performance_metrics"
        table = bigquery.Table(table_id, schema=schema)
        
        try:
            table = self.client.create_table(table, exists_ok=True)
            logger.info(f"Performance metrics table created: {table_id}")
        except Exception as e:
            logger.error(f"Error creating performance metrics table: {e}")
            
    def store_prediction_metadata(self, metadata: Dict[str, any]):
        """
        Store prediction metadata in dashboard tables
        """
        prediction_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        prediction_timestamp = datetime.now()
        
        # Extract input date from metadata or use current date
        input_date = datetime.now().date()
        
        # Prepare prediction history records
        prediction_records = []
        
        for horizon in ['1w', '1m', '3m', '6m']:
            if horizon in metadata['predictions'] and metadata['predictions'][horizon] is not None:
                
                # Get confidence intervals if available
                intervals = metadata['confidence_intervals'].get(horizon, {})
                
                record = {
                    'prediction_id': prediction_id,
                    'prediction_timestamp': prediction_timestamp,
                    'input_date': input_date,
                    'horizon': horizon,
                    'prediction_value': metadata['predictions'][horizon],
                    'lower_68_bound': intervals.get('lower_68'),
                    'upper_68_bound': intervals.get('upper_68'),
                    'lower_95_bound': intervals.get('lower_95'),
                    'upper_95_bound': intervals.get('upper_95'),
                    'regime': metadata['regime'].get('regime'),
                    'vix_current': metadata['regime'].get('vix_current'),
                    'model_version': 'v4_enriched',
                    'feature_importance': json.dumps(metadata['feature_importance'].get(horizon, [])),
                    'accuracy_metrics': json.dumps(metadata['historical_accuracy'].get(horizon, {}))
                }
                
                prediction_records.append(record)
                
        # Store prediction records
        if prediction_records:
            df = pd.DataFrame(prediction_records)
            table_id = f"{self.dashboard_dataset}.prediction_history"
            
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
            )
            
            try:
                job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
                job.result()
                logger.info(f"Stored {len(prediction_records)} prediction records")
            except Exception as e:
                logger.error(f"Error storing prediction records: {e}")
                
        # Store regime information
        if metadata['regime'].get('regime'):
            regime_record = {
                'date': input_date,
                'regime': metadata['regime']['regime'],
                'vix_current': metadata['regime']['vix_current'],
                'vix_threshold': metadata['regime']['vix_threshold'],
                'regime_duration_days': None  # Calculate separately
            }
            
            regime_df = pd.DataFrame([regime_record])
            regime_table_id = f"{self.dashboard_dataset}.regime_history"
            
            try:
                job = self.client.load_table_from_dataframe(
                    regime_df, regime_table_id, 
                    job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
                )
                job.result()
                logger.info("Stored regime record")
            except Exception as e:
                logger.error(f"Error storing regime record: {e}")
                
        # Store performance metrics
        performance_records = []
        for horizon, metrics in metadata['historical_accuracy'].items():
            if metrics:
                record = {
                    'date': input_date,
                    'horizon': horizon,
                    'mae': metrics.get('mae'),
                    'mape': metrics.get('mape'),
                    'rmse': metrics.get('rmse'),
                    'directional_accuracy': metrics.get('directional_accuracy'),
                    'correlation': metrics.get('correlation'),
                    'prediction_count': metrics.get('prediction_count'),
                    'regime': metadata['regime'].get('regime'),
                    'evaluation_period_days': metrics.get('period_days', 90)
                }
                performance_records.append(record)
                
        if performance_records:
            perf_df = pd.DataFrame(performance_records)
            perf_table_id = f"{self.dashboard_dataset}.performance_metrics"
            
            try:
                job = self.client.load_table_from_dataframe(
                    perf_df, perf_table_id,
                    job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
                )
                job.result()
                logger.info(f"Stored {len(performance_records)} performance records")
            except Exception as e:
                logger.error(f"Error storing performance records: {e}")
                
    def get_dashboard_data_queries(self) -> Dict[str, str]:
        """
        Return SQL queries for dashboard data retrieval
        """
        queries = {
            'latest_predictions': f"""
                SELECT 
                    horizon,
                    prediction_value,
                    lower_68_bound,
                    upper_68_bound,
                    lower_95_bound,
                    upper_95_bound,
                    regime,
                    prediction_timestamp
                FROM `{self.dashboard_dataset}.prediction_history`
                WHERE prediction_timestamp = (
                    SELECT MAX(prediction_timestamp) 
                    FROM `{self.dashboard_dataset}.prediction_history`
                )
                ORDER BY 
                    CASE horizon 
                        WHEN '1w' THEN 1 
                        WHEN '1m' THEN 2 
                        WHEN '3m' THEN 3 
                        WHEN '6m' THEN 4 
                    END
            """,
            
            'regime_timeline': f"""
                SELECT 
                    date,
                    regime,
                    vix_current,
                    vix_threshold
                FROM `{self.dashboard_dataset}.regime_history`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                ORDER BY date DESC
            """,
            
            'performance_trends': f"""
                SELECT 
                    date,
                    horizon,
                    mape,
                    directional_accuracy,
                    regime
                FROM `{self.dashboard_dataset}.performance_metrics`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                ORDER BY date DESC, horizon
            """,
            
            'feature_importance_latest': f"""
                SELECT 
                    horizon,
                    JSON_EXTRACT_SCALAR(feature_importance, '$[0].feature') as top_feature,
                    JSON_EXTRACT_SCALAR(feature_importance, '$[0].weight') as top_weight,
                    prediction_timestamp
                FROM `{self.dashboard_dataset}.prediction_history`
                WHERE prediction_timestamp = (
                    SELECT MAX(prediction_timestamp) 
                    FROM `{self.dashboard_dataset}.prediction_history`
                )
                AND feature_importance IS NOT NULL
            """,
            
            'prediction_accuracy_by_regime': f"""
                SELECT 
                    regime,
                    horizon,
                    AVG(mape) as avg_mape,
                    AVG(directional_accuracy) as avg_directional_accuracy,
                    COUNT(*) as sample_size
                FROM `{self.dashboard_dataset}.performance_metrics`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                  AND regime IS NOT NULL
                GROUP BY regime, horizon
                ORDER BY regime, horizon
            """
        }
        
        return queries
        
    def initialize_dashboard_infrastructure(self):
        """
        Initialize all dashboard tables and infrastructure
        """
        logger.info("Initializing dashboard infrastructure")
        
        self.create_prediction_history_table()
        self.create_regime_history_table()
        self.create_performance_metrics_table()
        
        logger.info("Dashboard infrastructure initialized")
        
    def test_dashboard_queries(self):
        """
        Test all dashboard queries to ensure they work
        """
        queries = self.get_dashboard_data_queries()
        
        for query_name, query_sql in queries.items():
            try:
                result = self.client.query(query_sql).to_dataframe()
                logger.info(f"Query '{query_name}' executed successfully: {len(result)} rows")
            except Exception as e:
                logger.error(f"Query '{query_name}' failed: {e}")

def main():
    """Initialize dashboard pipeline and test"""
    
    pipeline = DashboardDataPipeline()
    
    # Initialize infrastructure
    pipeline.initialize_dashboard_infrastructure()
    
    # Test queries
    pipeline.test_dashboard_queries()
    
    print("\n" + "="*80)
    print("DASHBOARD DATA PIPELINE INITIALIZED")
    print("="*80)
    print("Tables created:")
    print("  - cbi-v14.dashboard.prediction_history")
    print("  - cbi-v14.dashboard.regime_history") 
    print("  - cbi-v14.dashboard.performance_metrics")
    print("\nReady to store prediction metadata from V4 models")
    print("="*80)

if __name__ == "__main__":
    main()
