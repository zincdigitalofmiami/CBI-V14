"""
Extract Feature Importance from Vertex AI Models
Purpose: Leverage $100+ Vertex AI training investment to optimize BQML training
Output: Top 50-100 features per horizon for optimized BQML feature selection
"""

from google.cloud import aiplatform
import json
import pandas as pd
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Vertex AI
aiplatform.init(project="cbi-v14", location="us-central1")

# Vertex AI Model IDs (from existing trained models)
VERTEX_MODELS = {
    "1w": "575258986094264320",  # 2.02% MAPE
    "1m": "274643710967283712",  # 1.98% MAPE
    "3m": "3157158578716934144",  # 2.68% MAPE
    "6m": "3788577320223113216",  # 2.51% MAPE
}

def extract_feature_importance(model_id: str, sample_instances: List[Dict], top_n: int = 100) -> Dict:
    """
    Extract feature importance from Vertex AI model using explain_tabular
    
    Args:
        model_id: Vertex AI model ID
        sample_instances: Sample feature rows to explain (at least 1, ideally 10-50)
        top_n: Number of top features to return
    
    Returns:
        Dict with feature_name, attribution, rank, percentage_contribution
    """
    try:
        model = aiplatform.Model(model_id)
        
        logger.info(f"Extracting feature importance from model {model_id}...")
        
        # Get explanations (SHAP-style attribution)
        explanations = model.explain_tabular(
            instances=sample_instances,
            parameters={
                "sampled_shapley_attribution": {
                    "path_count": 10  # Number of paths for SHAP estimation
                }
            }
        )
        
        # Aggregate attributions across instances (average absolute attribution)
        feature_attributions = {}
        
        for explanation in explanations:
            attributions = explanation.get("attributions", [])
            
            for attribution in attributions:
                feature_name = attribution.get("featureDisplayName") or attribution.get("feature")
                attribution_value = attribution.get("attribution", 0)
                
                if feature_name:
                    if feature_name not in feature_attributions:
                        feature_attributions[feature_name] = []
                    feature_attributions[feature_name].append(abs(attribution_value))
        
        # Calculate average absolute attribution per feature
        feature_scores = {}
        for feature_name, attributions in feature_attributions.items():
            avg_attribution = sum(attributions) / len(attributions)
            feature_scores[feature_name] = avg_attribution
        
        # Sort by attribution (descending)
        sorted_features = sorted(
            feature_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Get top N features
        top_features = sorted_features[:top_n]
        
        # Calculate percentage contribution
        total_attribution = sum(abs(score) for _, score in feature_scores.items())
        
        result = {
            "model_id": model_id,
            "total_features": len(feature_scores),
            "top_features": []
        }
        
        for rank, (feature_name, attribution) in enumerate(top_features, 1):
            pct_contribution = (attribution / total_attribution * 100) if total_attribution > 0 else 0
            
            result["top_features"].append({
                "rank": rank,
                "feature_name": feature_name,
                "attribution": attribution,
                "percentage_contribution": pct_contribution
            })
        
        logger.info(f"Extracted {len(top_features)} top features from model {model_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error extracting feature importance from model {model_id}: {e}")
        return None


def get_sample_instances_from_bigquery(limit: int = 50) -> List[Dict]:
    """
    Get sample feature instances from BigQuery for explanation
    
    Returns:
        List of feature dictionaries (excludes targets, date)
    """
    from google.cloud import bigquery
    
    client = bigquery.Client(project="cbi-v14")
    
    query = """
    SELECT * EXCEPT(date, target_1w, target_1m, target_3m, target_6m)
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
      AND zl_price_current IS NOT NULL
    ORDER BY date DESC
    LIMIT @limit
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("limit", "INT64", limit)
        ]
    )
    
    df = client.query(query, job_config=job_config).to_dataframe()
    
    # Convert DataFrame to list of dicts
    instances = df.to_dict('records')
    
    # Replace NaN with 0.0 (Vertex AI doesn't accept NaN)
    for instance in instances:
        for key, value in instance.items():
            if pd.isna(value):
                instance[key] = 0.0
    
    logger.info(f"Retrieved {len(instances)} sample instances from BigQuery")
    return instances


def main():
    """Extract feature importance for all horizons"""
    
    logger.info("🚀 Starting Vertex AI feature importance extraction...")
    
    # Get sample instances (reuse across all models)
    sample_instances = get_sample_instances_from_bigquery(limit=50)
    
    if not sample_instances:
        logger.error("No sample instances found. Cannot extract feature importance.")
        return
    
    all_results = {}
    
    # Extract for each horizon
    for horizon, model_id in VERTEX_MODELS.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {horizon.upper()} model (ID: {model_id})")
        logger.info(f"{'='*60}")
        
        result = extract_feature_importance(
            model_id=model_id,
            sample_instances=sample_instances,
            top_n=100
        )
        
        if result:
            all_results[horizon] = result
            
            # Save per-horizon results
            output_file = f"config/vertex_feature_importance_{horizon}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"✅ Saved to {output_file}")
            
            # Print top 20 features
            logger.info(f"\n📊 Top 20 Features for {horizon.upper()}:")
            for feat in result["top_features"][:20]:
                logger.info(f"  {feat['rank']:3d}. {feat['feature_name']:40s} | "
                          f"Attribution: {feat['attribution']:8.4f} | "
                          f"Contribution: {feat['percentage_contribution']:5.2f}%")
    
    # Save combined results
    output_file = "config/vertex_feature_importance_all.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    logger.info(f"\n✅ Saved combined results to {output_file}")
    
    # Generate summary report
    logger.info(f"\n{'='*60}")
    logger.info("📋 SUMMARY REPORT")
    logger.info(f"{'='*60}")
    
    for horizon, result in all_results.items():
        if result:
            top_50 = [f["feature_name"] for f in result["top_features"][:50]]
            logger.info(f"\n{horizon.upper()} Top 50 Features:")
            logger.info(f"  Total features analyzed: {result['total_features']}")
            logger.info(f"  Top 50: {', '.join(top_50)}")
    
    logger.info("\n✅ Feature importance extraction complete!")
    logger.info("\n🎯 NEXT STEPS:")
    logger.info("  1. Review top features per horizon")
    logger.info("  2. Identify common high-impact features across horizons")
    logger.info("  3. Update BQML training to use optimized feature set (50-100 features)")
    logger.info("  4. Compare BQML predictions with Vertex predictions for validation")


if __name__ == "__main__":
    main()

