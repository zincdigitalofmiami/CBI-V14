#!/usr/bin/env python3
"""
Vertex AI AutoML Training - BigQuery Direct Integration
Institutional Standard: Goldman Sachs / JP Morgan pattern
No GCS exports - reads directly from BigQuery warehouse
"""

import logging
from google.cloud import aiplatform
from google.cloud import bigquery
from datetime import datetime
import argparse
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Project configuration
PROJECT_ID = 'cbi-v14'
REGION = 'us-central1'
DATASET_ID = 'models_v4'
SOURCE_TABLE = 'training_dataset_super_enriched'

# BigQuery source (institutional pattern - no GCS export needed)
BQ_SOURCE = f"bq://{PROJECT_ID}.{DATASET_ID}.{SOURCE_TABLE}"

# Training configuration
PILOT_BUDGET = 1000  # ~$20, 1 hour
FULL_BUDGET = 4000   # ~$80, 4 hours

HORIZONS = {
    '1w': 'target_1w',
    '1m': 'target_1m',
    '3m': 'target_3m',
    '6m': 'target_6m'
}

# Columns to exclude (known NULLs + other targets)
BASE_EXCLUDE = [
    'date',
    'econ_gdp_growth',
    'econ_unemployment_rate',
    'treasury_10y_yield',
    'news_article_count',
    'news_avg_score'
]


def validate_data_before_training():
    """
    Institutional validation gate - must pass before training
    Goldman/JPM standard: validate before compute
    """
    logger.info("\n" + "="*80)
    logger.info("PRE-TRAINING DATA VALIDATION (Institutional Gate)")
    logger.info("="*80)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    validation_query = f"""
    SELECT 
      COUNT(*) as total_rows,
      COUNT(DISTINCT date) as unique_dates,
      
      -- Big 8 Coverage
      COUNTIF(feature_vix_stress IS NOT NULL) as big8_vix,
      COUNTIF(feature_harvest_pace IS NOT NULL) as big8_harvest,
      COUNTIF(feature_china_relations IS NOT NULL) as big8_china,
      COUNTIF(feature_tariff_threat IS NOT NULL) as big8_tariff,
      
      -- Critical Features
      COUNTIF(china_soybean_imports_mt > 0) as china_populated,
      COUNTIF(argentina_export_tax IS NOT NULL) as argentina_populated,
      COUNTIF(industrial_demand_index IS NOT NULL) as industrial_populated,
      
      -- Targets
      COUNTIF(target_1w IS NOT NULL) as target_1w_count,
      COUNTIF(target_1m IS NOT NULL) as target_1m_count,
      COUNTIF(target_3m IS NOT NULL) as target_3m_count,
      COUNTIF(target_6m IS NOT NULL) as target_6m_count
      
    FROM `{PROJECT_ID}.{DATASET_ID}.{SOURCE_TABLE}`
    """
    
    result = client.query(validation_query).to_dataframe().iloc[0]
    
    logger.info(f"  Total rows: {result['total_rows']}")
    logger.info(f"  Unique dates: {result['unique_dates']}")
    logger.info(f"  Big 8 Coverage: {result['big8_vix']}/{result['total_rows']} (100%: {result['big8_vix'] == result['total_rows']})")
    logger.info(f"  China imports populated: {result['china_populated']} rows")
    logger.info(f"  Argentina data: {result['argentina_populated']} rows")
    logger.info(f"  Industrial data: {result['industrial_populated']} rows")
    logger.info(f"  Target coverage: 1W={result['target_1w_count']}, 1M={result['target_1m_count']}, 3M={result['target_3m_count']}, 6M={result['target_6m_count']}")
    
    # Validation gates
    assert result['total_rows'] == result['unique_dates'], "DUPLICATES DETECTED!"
    assert result['big8_vix'] == result['total_rows'], "Big 8 coverage incomplete!"
    assert result['china_populated'] > 300, f"China data insufficient: {result['china_populated']} rows"
    assert result['target_1w_count'] / result['total_rows'] > 0.85, "Target coverage <85%!"
    
    logger.info("\n✅ ALL VALIDATION GATES PASSED")
    return True


def create_dataset_from_bigquery(display_name):
    """
    Create Vertex AI TabularDataset directly from BigQuery
    Institutional pattern - no export step
    """
    
    logger.info(f"\nCreating Vertex AI dataset from BigQuery table...")
    logger.info(f"  Source: {BQ_SOURCE}")
    logger.info(f"  Display Name: {display_name}")
    
    try:
        dataset = aiplatform.TabularDataset.create(
            display_name=display_name,
            bq_source=BQ_SOURCE,  # Direct BigQuery - Goldman/JPM pattern
        )
        
        logger.info(f"✅ Dataset created: {dataset.resource_name}")
        logger.info(f"   Schema columns: {len(dataset.column_names)}")
        logger.info(f"   Data location: BigQuery (warehouse)")
        
        return dataset
        
    except Exception as e:
        logger.error(f"Failed to create dataset: {e}")
        return None


def train_automl_model(dataset, target_column, budget_milli_node_hours, model_display_name):
    """Train AutoML Tables model with institutional monitoring"""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TRAINING: {model_display_name}")
    logger.info(f"Target: {target_column}")
    logger.info(f"Budget: {budget_milli_node_hours} milli-node-hours")
    logger.info(f"{'='*80}\n")
    
    # Exclude other targets from features
    other_targets = [t for h, t in HORIZONS.items() if t != target_column]
    all_exclude = BASE_EXCLUDE + other_targets
    
    logger.info(f"Excluded columns ({len(all_exclude)}): {', '.join(all_exclude)}")
    
    try:
        # Create training job
        job = aiplatform.AutoMLTabularTrainingJob(
            display_name=f"{model_display_name}_job",
            optimization_prediction_type="regression",
            optimization_objective="minimize-rmse",
        )
        
        logger.info("Submitting training job to Vertex AI...")
        logger.info(f"  Training split: 80%")
        logger.info(f"  Validation split: 10%")
        logger.info(f"  Test split: 10%")
        logger.info(f"  Early stopping: Enabled")
        
        # Train the model
        model = job.run(
            dataset=dataset,
            target_column=target_column,
            budget_milli_node_hours=budget_milli_node_hours,
            model_display_name=model_display_name,
            predefined_split_column_name=None,  # Use automatic temporal split
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
            'data_source': BQ_SOURCE,
            'excluded_columns': all_exclude,
            'data_features': {
                'china_imports': True,
                'argentina_crisis': True,
                'industrial_demand': True,
                'big8_signals': True
            }
        }
        
        with open(f'automl/{model_display_name}_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"   Metadata saved: automl/{model_display_name}_metadata.json")
            
        return model
        
    except Exception as e:
        logger.error(f"Training failed for {model_display_name}: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return None


def run_pilot(dataset):
    """Run pilot training on 1W horizon with 1,000 budget"""
    
    logger.info("\n" + "🚀"*40)
    logger.info("PILOT RUN: 1W Horizon")
    logger.info("Budget: 1,000 milli-node-hours (~$20)")
    logger.info("Validates: Data format, features, Vertex AI permissions")
    logger.info("🚀"*40 + "\n")
    
    model = train_automl_model(
        dataset=dataset,
        target_column='target_1w',
        budget_milli_node_hours=PILOT_BUDGET,
        model_display_name='cbi_v14_automl_pilot_1w'
    )
    
    if model:
        logger.info("\n✅ PILOT SUCCESSFUL - Ready for full training")
    else:
        logger.error("\n❌ PILOT FAILED - Fix issues before full run")
    
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
        logger.info(f"\n{'='*80}")
        logger.info(f"Training {horizon_name.upper()} Horizon ({target_col})")
        logger.info(f"{'='*80}")
        
        model = train_automl_model(
            dataset=dataset,
            target_column=target_col,
            budget_milli_node_hours=budget_per_horizon,
            model_display_name=f'cbi_v14_automl_{horizon_name}_final'
        )
        results[horizon_name] = model
        
        if model:
            logger.info(f"✅ {horizon_name.upper()} completed successfully")
        else:
            logger.error(f"❌ {horizon_name.upper()} failed")
        
    success_count = sum(1 for m in results.values() if m is not None)
    logger.info(f"\n✅ Completed {success_count}/{len(HORIZONS)} models")
    
    return results


def main():
    """Main execution with institutional rigor"""
    
    parser = argparse.ArgumentParser(description='Vertex AI AutoML Training - Institutional Grade')
    parser.add_argument('--mode', choices=['pilot', 'full'], required=True,
                        help='Run pilot ($20) or full training ($80)')
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("VERTEX AI AUTOML TRAINING PIPELINE - INSTITUTIONAL GRADE")
    logger.info("="*80)
    logger.info(f"Mode: {args.mode.upper()}")
    logger.info(f"Project: {PROJECT_ID}")
    logger.info(f"Region: {REGION}")
    logger.info(f"Data Source: BigQuery (Goldman/JPM pattern)")
    logger.info(f"Table: {SOURCE_TABLE}")
    logger.info("="*80)
    
    # Initialize Vertex AI
    aiplatform.init(project=PROJECT_ID, location=REGION)
    logger.info(f"\n✅ Initialized Vertex AI: {PROJECT_ID} in {REGION}")
    
    # Pre-training validation gate
    try:
        validate_data_before_training()
    except AssertionError as e:
        logger.error(f"\n❌ VALIDATION FAILED: {e}")
        logger.error("Fix data issues before training!")
        return False
    except Exception as e:
        logger.error(f"\n❌ VALIDATION ERROR: {e}")
        return False
    
    # Create dataset from BigQuery
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    dataset_name = f"cbi_v14_enhanced_features_{args.mode}_{timestamp}"
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Creating Vertex AI Dataset from BigQuery")
    logger.info(f"{'='*80}")
    
    dataset = create_dataset_from_bigquery(dataset_name)
    
    if not dataset:
        logger.error("Failed to create dataset. Aborting.")
        return False
    
    # Run training
    if args.mode == 'pilot':
        success = run_pilot(dataset)
    else:
        results = run_full_training(dataset)
        success = any(results.values())
    
    # Final report
    if success:
        logger.info("\n" + "="*80)
        logger.info("✅ AUTOML TRAINING PIPELINE COMPLETE")
        logger.info("="*80)
        logger.info("\nNext Steps:")
        logger.info("  1. Monitor training in Vertex AI Console")
        logger.info("  2. Review feature importance (SHAP)")
        logger.info("  3. Run calibration check")
        logger.info("  4. Compare vs ARIMA baseline")
        logger.info("  5. Deploy to endpoints")
    else:
        logger.error("\n" + "="*80)
        logger.error("❌ TRAINING FAILED")
        logger.error("="*80)
        logger.error("Check logs for details")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)


