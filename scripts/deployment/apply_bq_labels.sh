#!/bin/bash
# ============================================================================
# BigQuery Dataset Labeling Script
# Date: November 18, 2025
# Purpose: Apply tier and category labels to all datasets for organization
# ============================================================================

set -uo pipefail

PROJECT_ID="cbi-v14"

echo "🏷️  Applying BigQuery Dataset Labels"
echo "============================================"
echo "Project: $PROJECT_ID"
echo ""

# Validation
TOTAL_DATASETS=0
LABELED_DATASETS=0
FAILED_DATASETS=0

# ============================================================================
# TIER 1: RAW DATA COLLECTION
# ============================================================================
echo "📊 Tier 1: Raw Data Collection"
echo "--------------------------------------------"

# market_data
echo "  Labeling: market_data"
TOTAL_DATASETS=$((TOTAL_DATASETS + 1))
if bq update --project_id=$PROJECT_ID \
             --set_label tier:raw \
             --set_label category:market \
             --set_label source:databento \
             --set_label data_type:ohlcv \
             market_data 2>&1; then
  echo "    ✓ Labels applied to market_data"
  LABELED_DATASETS=$((LABELED_DATASETS + 1))
else
  echo "    ⚠️  Warning: Could not label market_data"
  FAILED_DATASETS=$((FAILED_DATASETS + 1))
fi

# raw_intelligence
echo "  Labeling: raw_intelligence"
TOTAL_DATASETS=$((TOTAL_DATASETS + 1))
if bq update --project_id=$PROJECT_ID \
             --set_label tier:raw \
             --set_label category:intelligence \
             --set_label source:apis \
             --set_label data_type:fundamental \
             raw_intelligence 2>&1; then
  echo "    ✓ Labels applied to raw_intelligence"
  LABELED_DATASETS=$((LABELED_DATASETS + 1))
else
  echo "    ⚠️  Warning: Could not label raw_intelligence"
  FAILED_DATASETS=$((FAILED_DATASETS + 1))
fi

echo ""

# ============================================================================
# TIER 2: DERIVED/PROCESSED DATA
# ============================================================================
echo "⚙️  Tier 2: Derived/Processed Data"
echo "--------------------------------------------"

# signals
echo "  Labeling: signals"
TOTAL_DATASETS=$((TOTAL_DATASETS + 1))
if bq update --project_id=$PROJECT_ID \
             --set_label tier:derived \
             --set_label category:signals \
             --set_label purpose:trading \
             --set_label data_type:calculated \
             signals 2>&1; then
  echo "    ✓ Labels applied to signals"
  LABELED_DATASETS=$((LABELED_DATASETS + 1))
else
  echo "    ⚠️  Warning: Could not label signals"
  FAILED_DATASETS=$((FAILED_DATASETS + 1))
fi

# regimes
echo "  Labeling: regimes"
TOTAL_DATASETS=$((TOTAL_DATASETS + 1))
if bq update --project_id=$PROJECT_ID \
             --set_label tier:derived \
             --set_label category:classification \
             --set_label purpose:regime \
             --set_label data_type:categorical \
             regimes 2>&1; then
  echo "    ✓ Labels applied to regimes"
  LABELED_DATASETS=$((LABELED_DATASETS + 1))
else
  echo "    ⚠️  Warning: Could not label regimes"
  FAILED_DATASETS=$((FAILED_DATASETS + 1))
fi

# drivers
echo "  Labeling: drivers"
TOTAL_DATASETS=$((TOTAL_DATASETS + 1))
if bq update --project_id=$PROJECT_ID \
             --set_label tier:derived \
             --set_label category:analysis \
             --set_label purpose:drivers \
             --set_label data_type:analytical \
             drivers 2>&1; then
  echo "    ✓ Labels applied to drivers"
  LABELED_DATASETS=$((LABELED_DATASETS + 1))
else
  echo "    ⚠️  Warning: Could not label drivers"
  FAILED_DATASETS=$((FAILED_DATASETS + 1))
fi

echo ""

# ============================================================================
# TIER 3: MACHINE LEARNING
# ============================================================================
echo "🤖 Tier 3: Machine Learning"
echo "--------------------------------------------"

# features
echo "  Labeling: features"
TOTAL_DATASETS=$((TOTAL_DATASETS + 1))
if bq update --project_id=$PROJECT_ID \
             --set_label tier:ml \
             --set_label category:features \
             --set_label purpose:training \
             --set_label data_type:engineered \
             features 2>&1; then
  echo "    ✓ Labels applied to features"
  LABELED_DATASETS=$((LABELED_DATASETS + 1))
else
  echo "    ⚠️  Warning: Could not label features"
  FAILED_DATASETS=$((FAILED_DATASETS + 1))
fi

# training
echo "  Labeling: training"
TOTAL_DATASETS=$((TOTAL_DATASETS + 1))
if bq update --project_id=$PROJECT_ID \
             --set_label tier:ml \
             --set_label category:training \
             --set_label purpose:export \
             --set_label data_type:labeled \
             training 2>&1; then
  echo "    ✓ Labels applied to training"
  LABELED_DATASETS=$((LABELED_DATASETS + 1))
else
  echo "    ⚠️  Warning: Could not label training"
  FAILED_DATASETS=$((FAILED_DATASETS + 1))
fi

# neural
echo "  Labeling: neural"
TOTAL_DATASETS=$((TOTAL_DATASETS + 1))
if bq update --project_id=$PROJECT_ID \
             --set_label tier:ml \
             --set_label category:neural \
             --set_label purpose:training \
             --set_label data_type:vectors \
             neural 2>&1; then
  echo "    ✓ Labels applied to neural"
  LABELED_DATASETS=$((LABELED_DATASETS + 1))
else
  echo "    ⚠️  Warning: Could not label neural"
  FAILED_DATASETS=$((FAILED_DATASETS + 1))
fi

echo ""

# ============================================================================
# TIER 4: PRODUCTION OUTPUT
# ============================================================================
echo "🚀 Tier 4: Production Output"
echo "--------------------------------------------"

# predictions
echo "  Labeling: predictions"
TOTAL_DATASETS=$((TOTAL_DATASETS + 1))
if bq update --project_id=$PROJECT_ID \
             --set_label tier:production \
             --set_label category:forecasts \
             --set_label purpose:serving \
             --set_label data_type:predictions \
             predictions 2>&1; then
  echo "    ✓ Labels applied to predictions"
  LABELED_DATASETS=$((LABELED_DATASETS + 1))
else
  echo "    ⚠️  Warning: Could not label predictions"
  FAILED_DATASETS=$((FAILED_DATASETS + 1))
fi

echo ""

# ============================================================================
# TIER 5: INFRASTRUCTURE/OPERATIONS
# ============================================================================
echo "🔧 Tier 5: Infrastructure/Operations"
echo "--------------------------------------------"

# monitoring
echo "  Labeling: monitoring"
TOTAL_DATASETS=$((TOTAL_DATASETS + 1))
if bq update --project_id=$PROJECT_ID \
             --set_label tier:ops \
             --set_label category:monitoring \
             --set_label purpose:observability \
             --set_label data_type:metrics \
             monitoring 2>&1; then
  echo "    ✓ Labels applied to monitoring"
  LABELED_DATASETS=$((LABELED_DATASETS + 1))
else
  echo "    ⚠️  Warning: Could not label monitoring"
  FAILED_DATASETS=$((FAILED_DATASETS + 1))
fi

# dim
echo "  Labeling: dim"
TOTAL_DATASETS=$((TOTAL_DATASETS + 1))
if bq update --project_id=$PROJECT_ID \
             --set_label tier:ops \
             --set_label category:reference \
             --set_label purpose:metadata \
             --set_label data_type:dimensional \
             dim 2>&1; then
  echo "    ✓ Labels applied to dim"
  LABELED_DATASETS=$((LABELED_DATASETS + 1))
else
  echo "    ⚠️  Warning: Could not label dim"
  FAILED_DATASETS=$((FAILED_DATASETS + 1))
fi

# ops
echo "  Labeling: ops"
TOTAL_DATASETS=$((TOTAL_DATASETS + 1))
if bq update --project_id=$PROJECT_ID \
             --set_label tier:ops \
             --set_label category:operations \
             --set_label purpose:logging \
             --set_label data_type:operational \
             ops 2>&1; then
  echo "    ✓ Labels applied to ops"
  LABELED_DATASETS=$((LABELED_DATASETS + 1))
else
  echo "    ⚠️  Warning: Could not label ops"
  FAILED_DATASETS=$((FAILED_DATASETS + 1))
fi

echo ""

# ============================================================================
# Summary
# ============================================================================
echo "============================================"
echo "LABELING SUMMARY"
echo "============================================"
echo "Total datasets: $TOTAL_DATASETS"
echo "Labeled: $LABELED_DATASETS"
echo "Failed: $FAILED_DATASETS"
echo ""

if [ "$FAILED_DATASETS" -eq 0 ]; then
  echo "✅ ALL DATASETS LABELED SUCCESSFULLY"
  echo ""
  echo "Labels applied:"
  echo "  - tier: raw, derived, ml, production, ops"
  echo "  - category: market, intelligence, signals, etc."
  echo "  - purpose: trading, training, serving, etc."
  echo "  - data_type: ohlcv, calculated, predictions, etc."
  echo ""
  echo "View labeled datasets in BigQuery console or use:"
  echo "  bq ls --project_id=$PROJECT_ID --filter 'labels.tier:ml'"
  exit 0
else
  echo "⚠️  SOME DATASETS COULD NOT BE LABELED"
  echo "This may be because datasets don't exist yet."
  echo "Run this script again after deployment completes."
  exit 1
fi





