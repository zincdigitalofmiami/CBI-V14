#!/usr/bin/env python3
"""
BigQuery ML AUTOML_REGRESSOR Training
No SDK installation needed - runs entirely in BigQuery
Cost: ~$10-25 total for all horizons
"""

from google.cloud import bigquery
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = 'cbi-v14'
DATASET_ID = 'models_v4'

HORIZONS = {
    '1w': 'target_1w',
    '1m': 'target_1m', 
    '3m': 'target_3m',
    '6m': 'target_6m'
}

# Columns to exclude from training
EXCLUDE_COLS = [
    'date',
    'econ_gdp_growth',
    'econ_unemployment_rate',
    'treasury_10y_yield', 
    'news_article_count',
    'news_avg_score'
]

def train_automl_model(horizon_name, target_col):
    """Train BigQuery ML AUTOML_REGRESSOR model"""
    
    client = bigquery.Client(project=PROJECT_ID)
    
    model_name = f"automl_{horizon_name}_v14"
    
    # Exclude other targets from features
    other_targets = [t for h, t in HORIZONS.items() if t != target_col]
    all_exclude = EXCLUDE_COLS + other_targets
    
    query = f"""
    CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`
    OPTIONS(
        model_type='AUTOML_REGRESSOR',
        input_label_cols=['{target_col}'],
        budget_hours=1.0,
        optimization_objective='MINIMIZE_MAE'
    ) AS
    SELECT * EXCEPT({', '.join(all_exclude)})
    FROM `{PROJECT_ID}.{DATASET_ID}.enhanced_features_automl`
    WHERE {target_col} IS NOT NULL
    AND date <= '2024-10-31'
    """
    
    logger.info(f"Starting AutoML for {horizon_name} ({target_col})...")
    logger.info(f"  Model: {model_name}")
    logger.info(f"  Budget: 1 hour")
    
    try:
        job = client.query(query)
        job.result()
        
        logger.info(f"✅ {horizon_name} AutoML complete!")
        
        # Get evaluation metrics
        eval_query = f"""
        SELECT *
        FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`)
        """
        
        eval_result = client.query(eval_query).to_dataframe()
        logger.info(f"  MAE: {eval_result['mean_absolute_error'].iloc[0]:.4f}")
        logger.info(f"  MAPE: {eval_result['mean_absolute_percentage_error'].iloc[0]:.2f}%")
        logger.info(f"  R²: {eval_result['r2_score'].iloc[0]:.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed {horizon_name}: {e}")
        return False


def main():
    """Train AutoML models for all horizons"""
    
    logger.info("="*80)
    logger.info("BIGQUERY ML AUTOML TRAINING")
    logger.info("="*80)
    logger.info("Using: AUTOML_REGRESSOR")
    logger.info("Cost: ~$10-25 total")
    logger.info("No SDK installation needed!")
    logger.info("")
    
    results = {}
    
    for horizon_name, target_col in HORIZONS.items():
        success = train_automl_model(horizon_name, target_col)
        results[horizon_name] = success
        logger.info("")
    
    # Summary
    success_count = sum(results.values())
    logger.info("="*80)
    logger.info(f"COMPLETED: {success_count}/{len(HORIZONS)} models")
    logger.info("="*80)
    
    if success_count == len(HORIZONS):
        logger.info("\n✅ ALL AUTOML MODELS TRAINED SUCCESSFULLY")
        logger.info("\nNext steps:")
        logger.info("  1. Run forecast validation")
        logger.info("  2. Compare with ARIMA baselines")
        logger.info("  3. Deploy best models")
    else:
        logger.error(f"\n⚠️ Only {success_count}/{len(HORIZONS)} models succeeded")
    
    return success_count == len(HORIZONS)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)


