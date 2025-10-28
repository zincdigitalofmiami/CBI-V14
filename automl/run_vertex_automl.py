#!/usr/bin/env python3
"""
Vertex AI AutoML Tables Training Pipeline
Pilot: 1,000 milli-node-hours ($20)
Full: 4,000 milli-node-hours ($80)
"""

from google.cloud import aiplatform
from google.cloud import bigquery
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = 'cbi-v14'
REGION = 'us-central1'
DATASET_ID = 'models_v4'
GCS_SOURCE = 'gs://forecasting-app-raw-data-bucket/automl/enhanced_features_v2_20251028/000000000000.parquet'

# Training configuration
PILOT_BUDGET = 1000  # ~$20, 1 hour
FULL_BUDGET = 4000   # ~$80, 4 hours

HORIZONS = {
    '1w': 'target_1w',
    '1m': 'target_1m',
    '3m': 'target_3m',
    '6m': 'target_6m'
}

def initialize_vertex_ai():
    """Initialize Vertex AI"""
    aiplatform.init(project=PROJECT_ID, location=REGION)
    logger.info(f"Initialized Vertex AI: {PROJECT_ID} in {REGION}")


def create_dataset(display_name):
    """Create Vertex AI Tabular Dataset"""
    
    logger.info(f"Creating Vertex AI dataset: {display_name}")
    
    try:
        dataset = aiplatform.TabularDataset.create(
            display_name=display_name,
            gcs_source=[GCS_SOURCE],
        )
        
        logger.info(f"✅ Dataset created: {dataset.resource_name}")
        return dataset
        
    except Exception as e:
        logger.error(f"Failed to create dataset: {e}")
        return None


def train_automl_model(dataset, target_column, budget_milli_node_hours, model_display_name):
    """Train AutoML Tables model"""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TRAINING: {model_display_name}")
    logger.info(f"Target: {target_column}")
    logger.info(f"Budget: {budget_milli_node_hours} milli-node-hours")
    logger.info(f"{'='*80}\n")
    
    # Exclude columns
    exclude_columns = [
        'date',
        'econ_gdp_growth',
        'econ_unemployment_rate',
        'treasury_10y_yield',
        'news_article_count',
        'news_avg_score',
        # Exclude other target columns
        'target_1w' if target_column != 'target_1w' else '',
        'target_1m' if target_column != 'target_1m' else '',
        'target_3m' if target_column != 'target_3m' else '',
        'target_6m' if target_column != 'target_6m' else '',
    ]
    
    exclude_columns = [col for col in exclude_columns if col]  # Remove empty strings
    
    try:
        # Create training job
        job = aiplatform.AutoMLTabularTrainingJob(
            display_name=f"{model_display_name}_job",
            optimization_prediction_type="regression",
            optimization_objective="minimize-mae",
        )
        
        logger.info("Starting training job...")
        logger.info(f"Excluded columns: {', '.join(exclude_columns)}")
        
        # Train the model
        model = job.run(
            dataset=dataset,
            target_column=target_column,
            budget_milli_node_hours=budget_milli_node_hours,
            model_display_name=model_display_name,
            predefined_split_column_name=None,  # Use automatic split
            training_fraction_split=0.8,
            validation_fraction_split=0.1,
            test_fraction_split=0.1,
            disable_early_stopping=False,
            export_evaluated_data_items=True,
        )
        
        logger.info(f"\n✅ TRAINING COMPLETE: {model_display_name}")
        logger.info(f"   Model resource: {model.resource_name}")
        
        # Save model metadata
        metadata = {
            'model_name': model_display_name,
            'target_column': target_column,
            'budget_used': budget_milli_node_hours,
            'model_resource_name': model.resource_name,
            'training_time': datetime.now().isoformat(),
            'dataset_source': GCS_SOURCE
        }
        
        with open(f'automl/{model_display_name}_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
            
        return model
        
    except Exception as e:
        logger.error(f"Training failed for {model_display_name}: {e}")
        return None


def run_pilot(dataset):
    """Run pilot training on 1W horizon with 1,000 budget"""
    
    logger.info("\n" + "🚀"*40)
    logger.info("PILOT RUN: 1W Horizon")
    logger.info("Budget: 1,000 milli-node-hours (~$20)")
    logger.info("🚀"*40 + "\n")
    
    model = train_automl_model(
        dataset=dataset,
        target_column='target_1w',
        budget_milli_node_hours=PILOT_BUDGET,
        model_display_name='cbi_v14_automl_pilot_1w'
    )
    
    return model is not None


def run_full_training(dataset):
    """Run full training on all horizons with 4,000 budget split across horizons"""
    
    logger.info("\n" + "🔥"*40)
    logger.info("FULL PRODUCTION RUN")
    logger.info("Total Budget: 4,000 milli-node-hours (~$80)")
    logger.info("Split: 1,000 per horizon")
    logger.info("🔥"*40 + "\n")
    
    results = {}
    budget_per_horizon = FULL_BUDGET // len(HORIZONS)
    
    for horizon_name, target_col in HORIZONS.items():
        model = train_automl_model(
            dataset=dataset,
            target_column=target_col,
            budget_milli_node_hours=budget_per_horizon,
            model_display_name=f'cbi_v14_automl_{horizon_name}_final'
        )
        results[horizon_name] = model
        
    success_count = sum(1 for m in results.values() if m is not None)
    logger.info(f"\n✅ Completed {success_count}/{len(HORIZONS)} models")
    
    return results


def main():
    """Main execution"""
    
    import argparse
    parser = argparse.ArgumentParser(description='Vertex AI AutoML Training')
    parser.add_argument('--mode', choices=['pilot', 'full'], required=True,
                        help='Run pilot ($20) or full training ($80)')
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("VERTEX AI AUTOML TRAINING PIPELINE")
    logger.info("="*80)
    
    # Initialize
    initialize_vertex_ai()
    
    # Create dataset
    dataset_name = f"cbi_v14_enhanced_features_{args.mode}_{datetime.now().strftime('%Y%m%d_%H%M')}"
    dataset = create_dataset(dataset_name)
    
    if not dataset:
        logger.error("Failed to create dataset. Aborting.")
        return False
    
    # Run training
    if args.mode == 'pilot':
        success = run_pilot(dataset)
    else:
        results = run_full_training(dataset)
        success = any(results.values())
    
    if success:
        logger.info("\n" + "="*80)
        logger.info("✅ AUTOML TRAINING PIPELINE COMPLETE")
        logger.info("="*80)
    else:
        logger.error("\n" + "="*80)
        logger.error("❌ TRAINING FAILED")
        logger.error("="*80)
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

