#!/bin/bash
# ============================================
# FOCUSED TRAINING PIPELINE
# Run feature selection → training → evaluation → promotion
# ============================================

set -e  # Exit on error

PROJECT_ID="cbi-v14"
DATASET_ID="models_v4"

echo "🚀 Starting Rich Focused Training Pipeline"
echo "=========================================="
echo ""

# Step 0: Pre-flight checks
echo "🔍 Step 0: Pre-flight Checks..."
echo "  - Adding crisis score..."
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
  < bigquery-sql/ADD_CRISIS_SCORE.sql

echo "  - Creating boost weights log..."
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
  < bigquery-sql/CREATE_BOOST_WEIGHTS_LOG.sql

# Step 1: Rich Feature Selection (with regime-aware boosting)
echo "📊 Step 1: Rich Feature Selection (FX, Trump, ICE, Argentina, Tariffs, Recent Events)..."
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
  < bigquery-sql/RICH_FOCUSED_FEATURE_SELECTION.sql

if [ $? -ne 0 ]; then
  echo "❌ Feature selection failed"
  exit 1
fi
echo "✅ Feature selection complete"
echo ""

# Step 1.5: Correlation trimming and lag checks
echo "🔍 Step 1.5: Quality Checks..."
echo "  - Correlation trimming (remove ρ > 0.85)..."
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
  < bigquery-sql/CORR_TRIM.sql

echo "  - Lag alignment check (verify t-1 causal)..."
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
  < bigquery-sql/LAG_CHECK.sql

# Step 2: Create Rich Focused Training Datasets
echo "📦 Step 2: Creating Rich Focused Training Datasets (75-100 features)..."
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
  < bigquery-sql/CREATE_FOCUSED_TRAINING_DATASETS.sql

if [ $? -ne 0 ]; then
  echo "❌ Dataset creation failed"
  exit 1
fi
echo "✅ Focused datasets created"
echo ""

# Step 3: Train Focused Models
echo "🎯 Step 3: Training Focused Models..."
echo "   This may take 10-20 minutes..."
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
  < bigquery-sql/TRAIN_FOCUSED_MODELS.sql

if [ $? -ne 0 ]; then
  echo "❌ Model training failed"
  exit 1
fi
echo "✅ Models trained"
echo ""

# Step 4: Review Evaluation Results
echo "📈 Step 4: Evaluation Results..."
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
  "SELECT * FROM \`$PROJECT_ID.$DATASET_ID.focused_model_evaluation\` ORDER BY model_name"

echo ""
echo "======================================"
echo "✅ Pipeline Complete!"
echo ""
echo "Next Steps:"
echo "1. Review evaluation results above"
echo "2. If focused models outperform, run:"
echo "   bq query --use_legacy_sql=false < bigquery-sql/PROMOTE_FOCUSED_TO_PRODUCTION.sql"
echo "3. Verify production models updated"
echo ""

