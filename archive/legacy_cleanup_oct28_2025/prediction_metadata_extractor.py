#!/usr/bin/env python3
"""
PREDICTION METADATA EXTRACTOR
Extracts REAL metadata from V4 production models for dashboard integration.
NO FAKE DATA - Only actual model outputs and calculated confidence intervals.
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictionMetadataExtractor:
    """Extract real metadata from V4 production models"""
    
    def __init__(self):
        self.client = bigquery.Client(project='cbi-v14')
        self.v4_models = {
            '1w': 'cbi-v14.models.zl_boosted_tree_1w_v3_enriched',
            '1m': 'cbi-v14.models.zl_boosted_tree_1m_v3_enriched', 
            '3m': 'cbi-v14.models.zl_boosted_tree_3m_v3_enriched',
            '6m': 'cbi-v14.models.zl_boosted_tree_6m_v3_enriched'
        }
        
    def extract_prediction_intervals(self, model_id: str, horizon: str, 
                                   test_data_query: str) -> Dict[str, float]:
        """
        Extract REAL prediction intervals from model residuals
        Uses actual historical prediction errors to calculate confidence bands
        """
        logger.info(f"Extracting prediction intervals for {horizon} model")
        
        # Get actual predictions vs actuals for confidence interval calculation
        query = f"""
        WITH predictions AS (
            SELECT 
                date,
                target_{horizon.replace('w', 'w').replace('m', 'm')} as actual,
                predicted_target_{horizon.replace('w', 'w').replace('m', 'm')} as predicted
            FROM ML.PREDICT(
                MODEL `{model_id}`,
                ({test_data_query})
            )
            WHERE target_{horizon.replace('w', 'w').replace('m', 'm')} IS NOT NULL
        ),
        residuals AS (
            SELECT 
                date,
                actual,
                predicted,
                (predicted - actual) as residual,
                ABS(predicted - actual) as abs_residual
            FROM predictions
        )
        SELECT 
            APPROX_QUANTILES(residual, 100)[OFFSET(16)] as lower_68_residual,  -- 16th percentile
            APPROX_QUANTILES(residual, 100)[OFFSET(84)] as upper_68_residual,  -- 84th percentile  
            APPROX_QUANTILES(residual, 100)[OFFSET(2)] as lower_95_residual,   -- 2.5th percentile
            APPROX_QUANTILES(residual, 100)[OFFSET(97)] as upper_95_residual,  -- 97.5th percentile
            STDDEV(residual) as residual_std,
            COUNT(*) as sample_size
        FROM residuals
        """
        
        result = self.client.query(query).to_dataframe()
        
        if result.empty:
            logger.warning(f"No residual data for {horizon} model")
            return {}
            
        row = result.iloc[0]
        
        intervals = {
            'lower_68_residual': float(row['lower_68_residual']),
            'upper_68_residual': float(row['upper_68_residual']),
            'lower_95_residual': float(row['lower_95_residual']),
            'upper_95_residual': float(row['upper_95_residual']),
            'residual_std': float(row['residual_std']),
            'sample_size': int(row['sample_size'])
        }
        
        logger.info(f"{horizon} intervals: 68% = [{intervals['lower_68_residual']:.2f}, {intervals['upper_68_residual']:.2f}]")
        return intervals
        
    def extract_feature_importance(self, model_id: str, horizon: str) -> List[Dict[str, float]]:
        """
        Extract REAL feature importance from trained V4 model
        Uses BigQuery ML's actual feature importance if available
        """
        logger.info(f"Extracting feature importance for {horizon} model")
        
        # Try to get feature importance from BigQuery ML
        try:
            query = f"""
            SELECT 
                feature,
                importance_weight,
                importance_gain
            FROM ML.FEATURE_IMPORTANCE(MODEL `{model_id}`)
            ORDER BY importance_weight DESC
            LIMIT 10
            """
            
            result = self.client.query(query).to_dataframe()
            
            if not result.empty:
                importance_list = []
                for _, row in result.iterrows():
                    importance_list.append({
                        'feature': str(row['feature']),
                        'weight': float(row['importance_weight']),
                        'gain': float(row.get('importance_gain', 0))
                    })
                logger.info(f"Extracted {len(importance_list)} feature importances for {horizon}")
                return importance_list
                
        except Exception as e:
            logger.warning(f"Could not extract feature importance from BigQuery ML: {e}")
            
        # Fallback: Get feature list from model metadata
        try:
            model = self.client.get_model(model_id)
            feature_names = [field.name for field in model.feature_columns]
            logger.info(f"Model {horizon} has {len(feature_names)} features, but no importance weights available")
            
            # Return feature list without fake importance scores
            return [{'feature': name, 'weight': None, 'gain': None} for name in feature_names[:10]]
            
        except Exception as e:
            logger.error(f"Could not extract feature metadata: {e}")
            return []
            
    def detect_current_regime(self) -> Dict[str, any]:
        """
        Detect current market regime using REAL VIX data
        Returns actual regime classification based on historical VIX percentiles
        """
        logger.info("Detecting current market regime from real VIX data")
        
        query = """
        SELECT 
            vix_current,
            date,
            PERCENTILE_CONT(vix_current, 0.8) OVER (
                ORDER BY date 
                ROWS BETWEEN 365 PRECEDING AND CURRENT ROW
            ) as vix_80th_percentile
        FROM `cbi-v14.models.training_dataset`
        WHERE vix_current IS NOT NULL
        ORDER BY date DESC
        LIMIT 1
        """
        
        result = self.client.query(query).to_dataframe()
        
        if result.empty:
            logger.warning("No VIX data available for regime detection")
            return {'regime': 'unknown', 'vix_current': None, 'vix_threshold': None}
            
        row = result.iloc[0]
        current_vix = float(row['vix_current'])
        vix_threshold = float(row['vix_80th_percentile'])
        
        regime = 'high_vol' if current_vix > vix_threshold else 'low_vol'
        
        regime_data = {
            'regime': regime,
            'vix_current': current_vix,
            'vix_threshold': vix_threshold,
            'detection_date': datetime.now().isoformat()
        }
        
        logger.info(f"Current regime: {regime} (VIX: {current_vix:.2f}, threshold: {vix_threshold:.2f})")
        return regime_data
        
    def calculate_historical_accuracy(self, horizon: str, days_back: int = 90) -> Dict[str, float]:
        """
        Calculate REAL historical accuracy metrics for the past N days
        """
        logger.info(f"Calculating historical accuracy for {horizon} over {days_back} days")
        
        model_id = self.v4_models[horizon]
        
        query = f"""
        WITH recent_data AS (
            SELECT *
            FROM `cbi-v14.models.training_dataset`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY)
              AND target_{horizon.replace('w', 'w').replace('m', 'm')} IS NOT NULL
        ),
        predictions AS (
            SELECT 
                date,
                target_{horizon.replace('w', 'w').replace('m', 'm')} as actual,
                predicted_target_{horizon.replace('w', 'w').replace('m', 'm')} as predicted
            FROM ML.PREDICT(
                MODEL `{model_id}`,
                (SELECT * FROM recent_data)
            )
        )
        SELECT 
            COUNT(*) as prediction_count,
            AVG(ABS(predicted - actual)) as mae,
            AVG(ABS(predicted - actual) / ABS(actual)) * 100 as mape,
            SQRT(AVG(POW(predicted - actual, 2))) as rmse,
            CORR(predicted, actual) as correlation,
            -- Directional accuracy
            AVG(CASE 
                WHEN SIGN(predicted - LAG(actual) OVER (ORDER BY date)) = 
                     SIGN(actual - LAG(actual) OVER (ORDER BY date)) 
                THEN 1.0 ELSE 0.0 
            END) * 100 as directional_accuracy
        FROM predictions
        WHERE actual IS NOT NULL AND predicted IS NOT NULL
        """
        
        result = self.client.query(query).to_dataframe()
        
        if result.empty or result['prediction_count'].iloc[0] == 0:
            logger.warning(f"No recent predictions available for {horizon}")
            return {}
            
        row = result.iloc[0]
        
        accuracy_metrics = {
            'prediction_count': int(row['prediction_count']),
            'mae': float(row['mae']),
            'mape': float(row['mape']),
            'rmse': float(row['rmse']),
            'correlation': float(row['correlation']) if row['correlation'] is not None else 0.0,
            'directional_accuracy': float(row['directional_accuracy']) if row['directional_accuracy'] is not None else 0.0,
            'period_days': days_back
        }
        
        logger.info(f"{horizon} accuracy: MAPE {accuracy_metrics['mape']:.2f}%, Dir Acc {accuracy_metrics['directional_accuracy']:.1f}%")
        return accuracy_metrics
        
    def generate_prediction_with_metadata(self, input_data: pd.DataFrame) -> Dict[str, any]:
        """
        Generate prediction with full REAL metadata for dashboard
        """
        logger.info("Generating prediction with complete metadata")
        
        # Test data query for confidence intervals
        test_data_query = """
        SELECT *
        FROM `cbi-v14.models.training_dataset`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
        """
        
        prediction_metadata = {
            'timestamp': datetime.now().isoformat(),
            'predictions': {},
            'confidence_intervals': {},
            'feature_importance': {},
            'regime': self.detect_current_regime(),
            'historical_accuracy': {}
        }
        
        for horizon, model_id in self.v4_models.items():
            logger.info(f"Processing {horizon} horizon")
            
            # Get prediction
            try:
                # Create temporary table for input
                temp_table = f"cbi-v14.models.temp_metadata_input_{horizon}"
                job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
                job = self.client.load_table_from_dataframe(input_data, temp_table, job_config=job_config)
                job.result()
                
                # Get prediction
                pred_query = f"""
                SELECT predicted_target_{horizon.replace('w', 'w').replace('m', 'm')} as prediction
                FROM ML.PREDICT(
                    MODEL `{model_id}`,
                    (SELECT * FROM `{temp_table}`)
                )
                """
                
                pred_result = self.client.query(pred_query).to_dataframe()
                prediction_value = float(pred_result['prediction'].iloc[0])
                
                # Cleanup temp table
                self.client.delete_table(temp_table)
                
                prediction_metadata['predictions'][horizon] = prediction_value
                
            except Exception as e:
                logger.error(f"Error getting prediction for {horizon}: {e}")
                prediction_metadata['predictions'][horizon] = None
                continue
                
            # Get confidence intervals
            intervals = self.extract_prediction_intervals(model_id, horizon, test_data_query)
            if intervals and prediction_value is not None:
                prediction_metadata['confidence_intervals'][horizon] = {
                    'prediction': prediction_value,
                    'lower_68': prediction_value + intervals['lower_68_residual'],
                    'upper_68': prediction_value + intervals['upper_68_residual'],
                    'lower_95': prediction_value + intervals['lower_95_residual'],
                    'upper_95': prediction_value + intervals['upper_95_residual']
                }
            
            # Get feature importance
            importance = self.extract_feature_importance(model_id, horizon)
            prediction_metadata['feature_importance'][horizon] = importance
            
            # Get historical accuracy
            accuracy = self.calculate_historical_accuracy(horizon)
            prediction_metadata['historical_accuracy'][horizon] = accuracy
            
        return prediction_metadata

def main():
    """Extract metadata from latest data point"""
    
    extractor = PredictionMetadataExtractor()
    
    # Get latest data point
    query = """
    SELECT *
    FROM `cbi-v14.models.training_dataset`
    WHERE CAST(date AS DATE) >= CURRENT_DATE() - 1
    ORDER BY date DESC
    LIMIT 1
    """
    
    client = bigquery.Client(project='cbi-v14')
    latest_data = client.query(query).to_dataframe()
    
    if latest_data.empty:
        print("No recent data available")
        return
        
    # Generate complete metadata
    metadata = extractor.generate_prediction_with_metadata(latest_data)
    
    # Save metadata to file
    output_file = f"prediction_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
        
    print(f"\n{'='*80}")
    print("PREDICTION METADATA EXTRACTED")
    print(f"{'='*80}")
    print(f"Output file: {output_file}")
    print(f"Timestamp: {metadata['timestamp']}")
    print(f"Regime: {metadata['regime']['regime']} (VIX: {metadata['regime']['vix_current']:.2f})")
    
    print(f"\nPredictions:")
    for horizon, pred in metadata['predictions'].items():
        if pred:
            print(f"  {horizon}: ${pred:.2f}")
            
    print(f"\nConfidence Intervals (68%):")
    for horizon, intervals in metadata['confidence_intervals'].items():
        if intervals:
            print(f"  {horizon}: ${intervals['lower_68']:.2f} - ${intervals['upper_68']:.2f}")
            
    print(f"\nRecent Accuracy (90 days):")
    for horizon, acc in metadata['historical_accuracy'].items():
        if acc:
            print(f"  {horizon}: MAPE {acc['mape']:.2f}%, Dir Acc {acc['directional_accuracy']:.1f}%")
            
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
