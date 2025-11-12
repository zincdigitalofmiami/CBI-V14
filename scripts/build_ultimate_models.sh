#!/bin/bash
#
# BUILD ULTIMATE BQML MODELS
# Based on data-driven feature importance
#

set -e

echo "============================================"
echo "🚀 BUILDING ULTIMATE BQML MODELS"
echo "============================================"
echo ""
echo "Models to build:"
echo "1. CRUSH KING - Top 20 high-correlation features"
echo "2. BIG 8 FOCUSED - Your Big 8 signals + heavy hitters"
echo "3. KITCHEN SINK - All 300 features"
echo "4. ENSEMBLE - Weighted combination"
echo ""

# First ensure data is current
echo "📊 Checking data freshness..."
bq query --use_legacy_sql=false "
SELECT 
  MAX(date) as latest_date,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_stale
FROM \`cbi-v14.models_v4.production_training_data_1w\`
"

echo ""
echo "🔨 Building models..."
echo "(This will take 5-10 minutes)"
echo ""

# Run the model building SQL
bq query --use_legacy_sql=false < bigquery-sql/BUILD_ULTIMATE_BQML_MODELS.sql

echo ""
echo "✅ Models created successfully!"
echo ""

# Show comparison results
echo "📊 Model Performance Comparison:"
bq query --use_legacy_sql=false "
SELECT 
  model_name,
  ROUND(mean_absolute_error, 3) as MAE,
  ROUND(r2_score, 3) as R2_Score
FROM \`cbi-v14.models_v4.ultimate_model_comparison\`
ORDER BY mean_absolute_error
"

echo ""
echo "🎯 Latest Ensemble Prediction:"
bq query --use_legacy_sql=false "
SELECT 
  date,
  current_price,
  ensemble_prediction,
  ensemble_pct_change as predicted_change_pct
FROM \`cbi-v14.models_v4.vw_ultimate_ensemble_1w\`
"

echo ""
echo "============================================"
echo "✅ COMPLETE!"
echo "============================================"
echo ""
echo "Dashboard should display:"
echo "1. CRUSH MARGIN (0.96 correlation!)"
echo "2. CHINA IMPORTS (-0.81 correlation!)"
echo "3. DOLLAR/FED (-0.66 correlation)"
echo "4. TARIFFS (0.65 - you were right!)"
echo ""
echo "View predictions: SELECT * FROM \`cbi-v14.models_v4.vw_ultimate_ensemble_1w\`"






