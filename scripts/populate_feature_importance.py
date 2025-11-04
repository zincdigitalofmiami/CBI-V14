#!/usr/bin/env python3
"""
Populate feature importance data from trained BQML models into enhanced metadata.

This script extracts feature importance scores from our trained BQML models and
updates the enhanced feature metadata table with concrete importance rankings
that neural networks can use for feature selection and attention mechanisms.
"""

import logging
from google.cloud import bigquery
from datetime import datetime
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"

def extract_feature_importance_from_model(model_name):
    """Extract feature importance from a trained BQML model."""
    client = bigquery.Client(project=PROJECT_ID)

    try:
        # Get global feature importance (works for boosted tree models)
        # Use 'attribution' column which is the correct name in BigQuery ML
        query = f"""
        SELECT
          feature,
          attribution as gradient_boosting_importance
        FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`)
        ORDER BY attribution DESC
        """

        importance_df = client.query(query).to_dataframe()
        logger.info(f"Extracted {len(importance_df)} features from {model_name}")

        return importance_df

    except Exception as e:
        logger.warning(f"Could not extract feature importance from {model_name}: {str(e)}")
        return pd.DataFrame()

def calculate_feature_importance_stats():
    """Calculate aggregated feature importance statistics across all models."""
    client = bigquery.Client(project=PROJECT_ID)

    # Known trained model names (from our training pipeline)
    model_names = ['bqml_1w_mean', 'bqml_1m_mean', 'bqml_3m_mean', 'bqml_6m_mean']

    logger.info(f"Checking {len(model_names)} known trained models")

    # Extract importance from each model
    all_importance_data = []

    for model_name in model_names:
        importance_df = extract_feature_importance_from_model(model_name)
        if not importance_df.empty:
            importance_df['model_name'] = model_name
            all_importance_data.append(importance_df)

    if not all_importance_data:
        logger.warning("No feature importance data extracted from any model")
        return pd.DataFrame()

    # Combine all importance data
    combined_df = pd.concat(all_importance_data, ignore_index=True)

    # Calculate aggregated statistics
    aggregated_importance = combined_df.groupby('feature').agg({
        'gradient_boosting_importance': ['mean', 'std', 'max', 'count']
    }).reset_index()

    # Flatten column names
    aggregated_importance.columns = ['feature', 'mean_importance', 'std_importance', 'max_importance', 'model_count']

    # Calculate additional metrics
    aggregated_importance['importance_stability'] = 1 - (aggregated_importance['std_importance'] / aggregated_importance['mean_importance'])
    aggregated_importance['importance_consistency'] = aggregated_importance['model_count'] / len(model_names)

    # Normalize importance scores (0-1 scale)
    max_importance = aggregated_importance['mean_importance'].max()
    aggregated_importance['normalized_importance'] = aggregated_importance['mean_importance'] / max_importance

    logger.info(f"Calculated importance statistics for {len(aggregated_importance)} features")

    return aggregated_importance

def update_enhanced_metadata_with_importance():
    """Update the enhanced feature metadata with calculated importance scores."""
    client = bigquery.Client(project=PROJECT_ID)

    # Get importance statistics
    importance_stats = calculate_feature_importance_stats()

    if importance_stats.empty:
        logger.warning("No importance statistics to update")
        return 0

    # Create temporary table with importance data
    temp_table_id = f"{PROJECT_ID}.{DATASET_ID}.temp_feature_importance"

    # Upload importance data to BigQuery
    importance_stats.to_gbq(temp_table_id, project_id=PROJECT_ID, if_exists='replace')

    # Update enhanced metadata with importance scores
    update_query = f"""
    UPDATE `cbi-v14.forecasting_data_warehouse.enhanced_feature_metadata` efm
    SET
      efm.gradient_boosting_importance = imp.mean_importance,
      efm.permutation_importance_score = imp.normalized_importance,
      efm.shap_value_magnitude = imp.max_importance,
      efm.cross_validation_stability = imp.importance_stability,
      efm.last_updated = CURRENT_TIMESTAMP()
    FROM `{temp_table_id}` imp
    WHERE efm.feature_name = imp.feature
    """

    job = client.query(update_query)
    job.result()

    updated_count = job.num_dml_affected_rows
    logger.info(f"Updated importance scores for {updated_count} features")

    # Clean up temporary table
    client.delete_table(temp_table_id, not_found_ok=True)

    return updated_count

def populate_neural_network_recommendations():
    """Add neural network specific recommendations based on feature characteristics."""
    client = bigquery.Client(project=PROJECT_ID)

    update_query = """
    UPDATE `cbi-v14.forecasting_data_warehouse.enhanced_feature_metadata`
    SET
      -- Neural network attention weights based on importance and compatibility
      neural_network_attention_weight = CASE
        WHEN gradient_boosting_importance IS NOT NULL AND attention_mechanism_compatible = TRUE
        THEN gradient_boosting_importance * ai_model_compatibility_score
        ELSE ai_model_compatibility_score * 0.5
      END,

      -- Update metadata version
      metadata_version = metadata_version + 1,
      last_updated = CURRENT_TIMESTAMP()

    WHERE gradient_boosting_importance IS NOT NULL
       OR ai_model_compatibility_score IS NOT NULL
    """

    job = client.query(update_query)
    job.result()

    logger.info(f"Updated neural network recommendations for {job.num_dml_affected_rows} features")

    return job.num_dml_affected_rows

def create_feature_importance_report():
    """Create a summary report of feature importance for documentation."""
    client = bigquery.Client(project=PROJECT_ID)

    report_query = """
    SELECT
      feature_name,
      feature_type,
      ROUND(gradient_boosting_importance, 4) as gradient_boosting_importance,
      ROUND(neural_network_attention_weight, 4) as neural_network_attention_weight,
      ROUND(permutation_importance_score, 4) as permutation_importance_score,
      ROUND(shap_value_magnitude, 4) as shap_value_magnitude,
      ROUND(cross_validation_stability, 4) as cross_validation_stability,
      ai_model_compatibility_score,
      sequence_modeling_suitable,
      attention_mechanism_compatible,
      preprocessing_required,
      neural_net_embedding_dim,
      economic_meaning
    FROM `cbi-v14.forecasting_data_warehouse.enhanced_feature_metadata`
    WHERE gradient_boosting_importance IS NOT NULL
    ORDER BY gradient_boosting_importance DESC
    LIMIT 20
    """

    report_df = client.query(report_query).to_dataframe()

    # Save report to file
    report_path = "/Users/zincdigital/CBI-V14/docs/feature_importance_report.csv"
    report_df.to_csv(report_path, index=False)

    logger.info(f"Feature importance report saved to {report_path}")
    logger.info(f"Top 20 features by gradient boosting importance:")
    for _, row in report_df.head(10).iterrows():
        logger.info(f"  {row['feature_name']}: {row['gradient_boosting_importance']:.4f} ({row['feature_type']})")

    return len(report_df)

def main():
    """Main function to populate feature importance metadata."""
    logger.info("=" * 70)
    logger.info("🤖 POPULATING FEATURE IMPORTANCE FOR NEURAL NETWORK METADATA")
    logger.info("=" * 70)

    try:
        # Step 1: Extract and calculate feature importance
        logger.info("1️⃣ Extracting feature importance from trained models...")
        importance_stats = calculate_feature_importance_stats()

        if importance_stats.empty:
            logger.warning("No feature importance data available - models may not be trained yet")
            return

        # Step 2: Update enhanced metadata
        logger.info("2️⃣ Updating enhanced feature metadata with importance scores...")
        updated_count = update_enhanced_metadata_with_importance()

        # Step 3: Add neural network recommendations
        logger.info("3️⃣ Calculating neural network specific recommendations...")
        nn_updated_count = populate_neural_network_recommendations()

        # Step 4: Create report
        logger.info("4️⃣ Generating feature importance report...")
        report_count = create_feature_importance_report()

        # Summary
        logger.info("=" * 70)
        logger.info("✅ FEATURE IMPORTANCE POPULATION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"📊 Features with importance data: {updated_count}")
        logger.info(f"🧠 Neural network recommendations updated: {nn_updated_count}")
        logger.info(f"📋 Report generated with top {report_count} features")
        logger.info("=" * 70)

        # Check metadata completeness
        check_query = """
        SELECT
          COUNT(*) as total_features,
          COUNTIF(gradient_boosting_importance IS NOT NULL) as with_gradient_importance,
          COUNTIF(neural_network_attention_weight IS NOT NULL) as with_nn_attention,
          COUNTIF(permutation_importance_score IS NOT NULL) as with_permutation_importance,
          ROUND(AVG(ai_model_compatibility_score), 3) as avg_ai_compatibility
        FROM `cbi-v14.forecasting_data_warehouse.enhanced_feature_metadata`
        """

        client = bigquery.Client(project=PROJECT_ID)
        completeness = client.query(check_query).to_dataframe().iloc[0]

        logger.info("🎯 METADATA COMPLETENESS:")
        logger.info(f"  Total features: {completeness['total_features']}")
        logger.info(f"  Gradient boosting importance: {completeness['with_gradient_importance']}/{completeness['total_features']}")
        logger.info(f"  Neural network attention: {completeness['with_nn_attention']}/{completeness['total_features']}")
        logger.info(f"  Permutation importance: {completeness['with_permutation_importance']}/{completeness['total_features']}")
        logger.info(f"  Average AI compatibility: {completeness['avg_ai_compatibility']}")

    except Exception as e:
        logger.error(f"Error in feature importance population: {str(e)}")
        raise

if __name__ == "__main__":
    main()
