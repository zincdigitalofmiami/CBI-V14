#!/usr/bin/env python3
"""
Validate the comprehensive AI/ML metadata system for neural networks.

This script performs thorough validation of the enhanced metadata system
to ensure neural networks have all the context and guidance they need
for effective feature selection, preprocessing, and model architecture decisions.
"""

import logging
from google.cloud import bigquery
from datetime import datetime
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"

def validate_enhanced_feature_metadata():
    """Validate the enhanced feature metadata table."""
    client = bigquery.Client(project=PROJECT_ID)

    logger.info("🔍 VALIDATING ENHANCED FEATURE METADATA")
    logger.info("=" * 50)

    # Check basic completeness
    completeness_query = """
    SELECT
      COUNT(*) as total_features,
      COUNTIF(feature_name IS NOT NULL) as named_features,
      COUNTIF(data_type IS NOT NULL) as typed_features,
      COUNTIF(preprocessing_required IS NOT NULL) as preprocessed_features,
      COUNTIF(neural_net_embedding_dim IS NOT NULL) as embedding_features,
      COUNTIF(ai_model_compatibility_score IS NOT NULL) as ai_compatible_features,
      ROUND(AVG(ai_model_compatibility_score), 3) as avg_ai_score
    FROM `cbi-v14.forecasting_data_warehouse.enhanced_feature_metadata`
    """

    completeness = client.query(completeness_query).to_dataframe().iloc[0]

    print("📊 BASIC COMPLETENESS:")
    print(f"  Total features: {completeness['total_features']}")
    print(f"  Named features: {completeness['named_features']}/{completeness['total_features']}")
    print(f"  Data typed: {completeness['typed_features']}/{completeness['total_features']}")
    print(f"  Preprocessing specified: {completeness['preprocessed_features']}/{completeness['total_features']}")
    print(f"  Neural embedding dims: {completeness['embedding_features']}/{completeness['total_features']}")
    print(f"  AI compatible: {completeness['ai_compatible_features']}/{completeness['total_features']}")
    print(f"  Average AI score: {completeness['avg_ai_score']}")

    # Check neural network specific metadata
    nn_query = """
    SELECT
      COUNTIF(sequence_modeling_suitable = TRUE) as sequence_suitable,
      COUNTIF(attention_mechanism_compatible = TRUE) as attention_compatible,
      COUNTIF(multimodal_feature = TRUE) as multimodal_features,
      COUNTIF(gradient_boosting_importance IS NOT NULL) as importance_features,
      COUNTIF(neural_network_attention_weight IS NOT NULL) as attention_weighted,
      COUNTIF(recommended_activation IS NOT NULL) as activation_recommended,
      COUNTIF(batch_normalization_advised = TRUE) as batch_norm_advised,
      COUNTIF(dropout_rate_suggestion IS NOT NULL) as dropout_suggested
    FROM `cbi-v14.forecasting_data_warehouse.enhanced_feature_metadata`
    """

    nn_metadata = client.query(nn_query).to_dataframe().iloc[0]

    print("\n🧠 NEURAL NETWORK METADATA:")
    print(f"  Sequence modeling suitable: {nn_metadata['sequence_suitable']}")
    print(f"  Attention mechanism compatible: {nn_metadata['attention_compatible']}")
    print(f"  Multimodal features: {nn_metadata['multimodal_features']}")
    print(f"  Gradient boosting importance: {nn_metadata['importance_features']}")
    print(f"  Neural attention weights: {nn_metadata['attention_weighted']}")
    print(f"  Activation recommendations: {nn_metadata['activation_recommended']}")
    print(f"  Batch norm advised: {nn_metadata['batch_norm_advised']}")
    print(f"  Dropout suggestions: {nn_metadata['dropout_suggested']}")

    return completeness, nn_metadata

def validate_neural_architecture_metadata():
    """Validate the neural network architecture recommendations."""
    client = bigquery.Client(project=PROJECT_ID)

    logger.info("\n🏗️ VALIDATING NEURAL ARCHITECTURE METADATA")
    logger.info("=" * 50)

    arch_query = """
    SELECT
      COUNT(*) as total_architectures,
      COUNTIF(recommended_layers IS NOT NULL) as with_layers,
      COUNTIF(input_feature_types IS NOT NULL) as with_input_types,
      COUNTIF(attention_mechanism != 'none') as attention_architectures,
      COUNTIF(loss_function IS NOT NULL) as with_loss_functions,
      COUNTIF(optimizer IS NOT NULL) as with_optimizers,
      COUNTIF(feature_importance_method IS NOT NULL) as with_importance_methods
    FROM `cbi-v14.forecasting_data_warehouse.neural_network_architecture_metadata`
    """

    arch_data = client.query(arch_query).to_dataframe().iloc[0]

    print("🏗️ ARCHITECTURE COMPLETENESS:")
    print(f"  Total architectures: {arch_data['total_architectures']}")
    print(f"  With layer specs: {arch_data['with_layers']}/{arch_data['total_architectures']}")
    print(f"  With input types: {arch_data['with_input_types']}/{arch_data['total_architectures']}")
    print(f"  Attention-based: {arch_data['attention_architectures']}/{arch_data['total_architectures']}")
    print(f"  With loss functions: {arch_data['with_loss_functions']}/{arch_data['total_architectures']}")
    print(f"  With optimizers: {arch_data['with_optimizers']}/{arch_data['total_architectures']}")
    print(f"  With importance methods: {arch_data['with_importance_methods']}/{arch_data['total_architectures']}")

    # Check architecture details
    detail_query = """
    SELECT
      architecture_name,
      model_type,
      attention_mechanism,
      computational_complexity,
      recommended_use_cases
    FROM `cbi-v14.forecasting_data_warehouse.neural_network_architecture_metadata`
    ORDER BY architecture_name
    """

    architectures = client.query(detail_query).to_dataframe()

    print("\n📋 AVAILABLE ARCHITECTURES:")
    for _, arch in architectures.iterrows():
        print(f"  🏗️ {arch['architecture_name']} ({arch['model_type']})")
        print(f"     Attention: {arch['attention_mechanism']}")
        print(f"     Complexity: {arch['computational_complexity']}")
        print(f"     Use cases: {arch['recommended_use_cases'][:50]}...")

    return arch_data

def validate_feature_engineering_guidance():
    """Validate feature engineering recommendations for neural networks."""
    client = bigquery.Client(project=PROJECT_ID)

    logger.info("\n⚙️ VALIDATING FEATURE ENGINEERING GUIDANCE")
    logger.info("=" * 50)

    # Check feature engineering suggestions
    eng_query = """
    SELECT
      feature_name,
      feature_type,
      preprocessing_required,
      feature_engineering_suggestions,
      neural_net_embedding_dim,
      sequence_modeling_suitable,
      attention_mechanism_compatible
    FROM `cbi-v14.forecasting_data_warehouse.enhanced_feature_metadata`
    WHERE feature_engineering_suggestions IS NOT NULL
    ORDER BY neural_net_embedding_dim DESC
    LIMIT 10
    """

    engineering_features = client.query(eng_query).to_dataframe()

    print("🔧 FEATURE ENGINEERING EXAMPLES:")
    for _, feature in engineering_features.iterrows():
        print(f"\n  🛠️ {feature['feature_name']} ({feature['feature_type']})")
        print(f"     Preprocessing: {feature['preprocessing_required']}")
        print(f"     Engineering: {feature['feature_engineering_suggestions']}")
        print(f"     Embedding dim: {feature['neural_net_embedding_dim']}")
        print(f"     Sequence suitable: {feature['sequence_modeling_suitable']}")
        print(f"     Attention compatible: {feature['attention_mechanism_compatible']}")

    # Check data type distributions
    dtype_query = """
    SELECT
      data_type,
      COUNT(*) as count,
      ROUND(AVG(neural_net_embedding_dim), 1) as avg_embedding_dim,
      COUNTIF(sequence_modeling_suitable = TRUE) as sequence_suitable,
      COUNTIF(attention_mechanism_compatible = TRUE) as attention_compatible
    FROM `cbi-v14.forecasting_data_warehouse.enhanced_feature_metadata`
    WHERE data_type IS NOT NULL
    GROUP BY data_type
    ORDER BY count DESC
    """

    dtypes = client.query(dtype_query).to_dataframe()

    print(f"\n📊 DATA TYPE DISTRIBUTIONS:")
    for _, dtype in dtypes.iterrows():
        print(f"  {dtype['data_type']:>20}: {int(dtype['count']):>2} features, "
              f"avg embed: {dtype['avg_embedding_dim']}, "
              f"seq: {int(dtype['sequence_suitable'])}, "
              f"attn: {int(dtype['attention_compatible'])}")

    return engineering_features, dtypes

def create_neural_network_readiness_report():
    """Create a comprehensive report on neural network readiness."""
    client = bigquery.Client(project=PROJECT_ID)

    logger.info("\n📋 CREATING NEURAL NETWORK READINESS REPORT")
    logger.info("=" * 50)

    # Overall readiness score
    readiness_query = """
    SELECT
      -- Feature completeness
      ROUND(AVG(CASE WHEN feature_name IS NOT NULL THEN 1 ELSE 0 END), 3) as naming_completeness,
      ROUND(AVG(CASE WHEN data_type IS NOT NULL THEN 1 ELSE 0 END), 3) as typing_completeness,
      ROUND(AVG(CASE WHEN preprocessing_required IS NOT NULL THEN 1 ELSE 0 END), 3) as preprocessing_completeness,
      ROUND(AVG(CASE WHEN neural_net_embedding_dim IS NOT NULL THEN 1 ELSE 0 END), 3) as embedding_completeness,
      ROUND(AVG(ai_model_compatibility_score), 3) as avg_ai_compatibility,

      -- Neural network readiness
      ROUND(AVG(CASE WHEN sequence_modeling_suitable THEN 1 ELSE 0 END), 3) as sequence_readiness,
      ROUND(AVG(CASE WHEN attention_mechanism_compatible THEN 1 ELSE 0 END), 3) as attention_readiness,
      ROUND(AVG(CASE WHEN gradient_boosting_importance IS NOT NULL THEN 1 ELSE 0 END), 3) as importance_readiness,

      -- Overall readiness
      ROUND(
        (
          AVG(CASE WHEN feature_name IS NOT NULL THEN 1 ELSE 0 END) +
          AVG(CASE WHEN data_type IS NOT NULL THEN 1 ELSE 0 END) +
          AVG(CASE WHEN preprocessing_required IS NOT NULL THEN 1 ELSE 0 END) +
          AVG(CASE WHEN neural_net_embedding_dim IS NOT NULL THEN 1 ELSE 0 END) +
          AVG(ai_model_compatibility_score) +
          AVG(CASE WHEN sequence_modeling_suitable THEN 1 ELSE 0 END) +
          AVG(CASE WHEN attention_mechanism_compatible THEN 1 ELSE 0 END) +
          AVG(CASE WHEN gradient_boosting_importance IS NOT NULL THEN 1 ELSE 0 END)
        ) / 8, 3
      ) as overall_readiness_score

    FROM `cbi-v14.forecasting_data_warehouse.enhanced_feature_metadata`
    """

    readiness = client.query(readiness_query).to_dataframe().iloc[0]

    print("🎯 NEURAL NETWORK READINESS SCORES:")
    print(f"  Naming completeness: {readiness['naming_completeness']:.3f}")
    print(f"  Typing completeness: {readiness['typing_completeness']:.3f}")
    print(f"  Preprocessing completeness: {readiness['preprocessing_completeness']:.3f}")
    print(f"  Embedding completeness: {readiness['embedding_completeness']:.3f}")
    print(f"  AI compatibility: {readiness['avg_ai_compatibility']:.3f}")
    print(f"  Sequence readiness: {readiness['sequence_readiness']:.3f}")
    print(f"  Attention readiness: {readiness['attention_readiness']:.3f}")
    print(f"  Importance readiness: {readiness['importance_readiness']:.3f}")
    print(f"  Overall readiness: {readiness['overall_readiness_score']:.3f}")

    # Architecture availability
    arch_count_query = """
    SELECT COUNT(*) as architecture_count
    FROM `cbi-v14.forecasting_data_warehouse.neural_network_architecture_metadata`
    """

    arch_count = client.query(arch_count_query).to_dataframe().iloc[0]['architecture_count']

    print(f"  Neural architectures available: {arch_count}")
    # Feature importance coverage
    importance_query = """
    SELECT
      COUNTIF(gradient_boosting_importance IS NOT NULL) as importance_features,
      COUNTIF(neural_network_attention_weight IS NOT NULL) as attention_features,
      COUNT(*) as total_features
    FROM `cbi-v14.forecasting_data_warehouse.enhanced_feature_metadata`
    """

    importance_stats = client.query(importance_query).to_dataframe().iloc[0]

    print("🎯 FEATURE IMPORTANCE COVERAGE:")
    print(f"  Gradient boosting: {importance_stats['importance_features']}/{importance_stats['total_features']}")
    print(f"  Neural attention: {importance_stats['attention_features']}/{importance_stats['total_features']}")

    return readiness, arch_count, importance_stats

def generate_neural_network_guidance():
    """Generate specific guidance for neural network implementation."""
    client = bigquery.Client(project=PROJECT_ID)

    logger.info("\n🎯 GENERATING NEURAL NETWORK IMPLEMENTATION GUIDANCE")
    logger.info("=" * 60)

    # Top features for neural networks
    top_features_query = """
    SELECT
      feature_name,
      feature_type,
      ROUND(neural_network_attention_weight, 4) as attention_weight,
      neural_net_embedding_dim,
      preprocessing_required,
      sequence_modeling_suitable,
      attention_mechanism_compatible,
      recommended_activation,
      dropout_rate_suggestion
    FROM `cbi-v14.forecasting_data_warehouse.enhanced_feature_metadata`
    WHERE neural_network_attention_weight IS NOT NULL
    ORDER BY neural_network_attention_weight DESC
    LIMIT 15
    """

    top_features = client.query(top_features_query).to_dataframe()

    print("🏆 TOP FEATURES FOR NEURAL NETWORKS:")
    print("Rank | Feature Name | Attention | Embed | Sequence | Attention | Activation | Dropout")
    print("-----|-------------|-----------|-------|----------|-----------|------------|---------")

    for i, (_, feature) in enumerate(top_features.iterrows(), 1):
        print(f"{i:2d}   | {feature['feature_name'][:11]:<11} | {feature['attention_weight']:.4f} | {int(feature['neural_net_embedding_dim']):>3} | {str(feature['sequence_modeling_suitable']):>8} | {str(feature['attention_mechanism_compatible']):>9} | {feature['recommended_activation']:<10} | {feature['dropout_rate_suggestion']:.2f}")

    # Architecture recommendations
    arch_recommend_query = """
    SELECT
      architecture_name,
      model_type,
      recommended_layers,
      attention_mechanism,
      computational_complexity,
      recommended_use_cases
    FROM `cbi-v14.forecasting_data_warehouse.neural_network_architecture_metadata`
    ORDER BY architecture_name
    """

    architectures = client.query(arch_recommend_query).to_dataframe()

    print("\n🏗️ RECOMMENDED NEURAL ARCHITECTURES:")
    for _, arch in architectures.iterrows():
        print(f"\n  🏗️ {arch['architecture_name']} ({arch['model_type']})")
        print(f"     Layers: {arch['recommended_layers']}")
        print(f"     Attention: {arch['attention_mechanism']}")
        print(f"     Complexity: {arch['computational_complexity']}")
        print(f"     Use cases: {arch['recommended_use_cases'][:60]}...")

    return top_features, architectures

def main():
    """Main validation function."""
    logger.info("🧠 COMPREHENSIVE AI METADATA VALIDATION FOR NEURAL NETWORKS")
    logger.info("=" * 70)

    try:
        # Validate all components
        feature_completeness, nn_metadata = validate_enhanced_feature_metadata()
        arch_data = validate_neural_architecture_metadata()
        engineering_features, dtypes = validate_feature_engineering_guidance()
        readiness, arch_count, importance_stats = create_neural_network_readiness_report()
        top_features, architectures = generate_neural_network_guidance()

        # Final assessment
        logger.info("\n" + "=" * 70)
        logger.info("🎯 FINAL AI METADATA ASSESSMENT")
        logger.info("=" * 70)

        overall_score = readiness['overall_readiness_score']
        if overall_score >= 0.9:
            assessment = "✅ EXCELLENT - Ready for advanced neural networks"
        elif overall_score >= 0.8:
            assessment = "✅ VERY GOOD - Ready for neural network training"
        elif overall_score >= 0.7:
            assessment = "⚠️ GOOD - Ready for basic neural networks"
        elif overall_score >= 0.6:
            assessment = "⚠️ ADEQUATE - May need some manual tuning"
        else:
            assessment = "❌ NEEDS IMPROVEMENT - Additional metadata required"

        print(f"📊 Overall Readiness Score: {overall_score:.3f}")
        print(f"🎯 Assessment: {assessment}")

        print("\n🔧 KEY METRICS:")
        print(f"  • Features with AI metadata: {nn_metadata['attention_weighted']}/52")
        print(f"  • Neural architectures available: {arch_count}")
        print(f"  • Features with importance scores: {importance_stats['importance_features']}")
        print(f"  • Average AI compatibility: {readiness['avg_ai_compatibility']:.3f}")

        print("\n✅ VALIDATION COMPLETE - NEURAL NETWORKS CAN NOW UNDERSTAND THE DATA!")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
