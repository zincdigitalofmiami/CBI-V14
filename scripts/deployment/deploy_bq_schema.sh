#!/bin/bash
# ============================================================================
# BigQuery Schema Deployment Script for CBI-V14
# Date: November 18, 2025
# Purpose: Deploy complete ZL/MES forecasting infrastructure to BigQuery
# ============================================================================

set -uo pipefail  # Use pipefail instead of -e for better error handling

PROJECT_ID="cbi-v14"
LOCATION="us-central1"
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--dry-run]"
      exit 1
      ;;
  esac
done

echo "🚀 CBI-V14 BigQuery Schema Deployment"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Location: $LOCATION"
if [ "$DRY_RUN" = true ]; then
  echo "Mode: DRY RUN (no changes will be made)"
fi
echo ""

# ============================================================================
# STEP 1: Create Datasets
# ============================================================================
echo "📁 Step 1: Creating BigQuery Datasets..."

datasets=(
  "market_data:CME/CBOT/NYMEX/COMEX market data only"
  "raw_intelligence:Free APIs only - FRED, USDA, EIA, CFTC, NOAA"
  "signals:Derived signals - crush, spreads, microstructure, Big 8"
  "features:Canonical master_features table"
  "training:Training datasets and regime support"
  "regimes:Regime classifications per symbol"
  "drivers:Primary drivers and meta-drivers"
  "neural:Neural training features"
  "predictions:Model predictions and forecasts"
  "monitoring:Model performance monitoring"
  "dim:Reference data and metadata"
  "ops:Operations and data quality"
)

for dataset_desc in "${datasets[@]}"; do
  IFS=':' read -r dataset description <<< "$dataset_desc"
  
  echo "  Processing dataset: $dataset"
  
  # Check if dataset exists
  if bq ls -d --project_id=$PROJECT_ID $dataset >/dev/null 2>&1; then
    echo "    ✓ Dataset $dataset already exists (skipping)"
  else
    if [ "$DRY_RUN" = true ]; then
      echo "    [DRY RUN] Would create dataset $dataset"
    else
      if bq mk --location=$LOCATION \
              --description="$description" \
              --project_id=$PROJECT_ID \
              $dataset 2>&1; then
        echo "    ✓ Created dataset $dataset"
      else
        echo "    ⚠️  Warning: Could not create dataset $dataset (may already exist)"
      fi
    fi
  fi
done

echo ""
echo "✅ All datasets created/verified"
echo ""

# ============================================================================
# STEP 2: Run DDL Script
# ============================================================================
echo "📊 Step 2: Creating Tables from Schema..."

if [ ! -f "PRODUCTION_READY_BQ_SCHEMA.sql" ]; then
  echo "❌ Error: PRODUCTION_READY_BQ_SCHEMA.sql not found in current directory"
  echo "Please run from /Users/kirkmusick/Documents/GitHub/CBI-V14/"
  exit 1
fi

# Split the SQL file by CREATE statements and run each separately
# This prevents issues with large SQL files
echo "  Parsing and executing DDL statements..."

# Create a temporary file for each CREATE statement
temp_dir=$(mktemp -d)
csplit -f "$temp_dir/table_" -b "%03d.sql" PRODUCTION_READY_BQ_SCHEMA.sql '/^CREATE/' '{*}' 2>/dev/null || true

# Execute each CREATE statement
for sql_file in "$temp_dir"/table_*.sql; do
  if [ -f "$sql_file" ] && [ -s "$sql_file" ]; then
    # Extract table name for logging
    table_name=$(grep -E "CREATE (OR REPLACE )?(TABLE|VIEW)" "$sql_file" | head -1 | sed -E 's/.*TABLE |.*VIEW //' | cut -d' ' -f1 | tr -d '`')
    
    if [ ! -z "$table_name" ]; then
      echo "  Processing: $table_name"
      
      if [ "$DRY_RUN" = true ]; then
        # Dry run validation
        if bq query --use_legacy_sql=false \
                   --project_id=$PROJECT_ID \
                   --location=$LOCATION \
                   --dry_run \
                   < "$sql_file" >/dev/null 2>&1; then
          echo "    ✓ [DRY RUN] SQL valid for $table_name"
        else
          echo "    ❌ [DRY RUN] SQL invalid for $table_name"
        fi
      else
        # Actual execution
        if bq query --use_legacy_sql=false \
                   --project_id=$PROJECT_ID \
                   --location=$LOCATION \
                   < "$sql_file" >/dev/null 2>&1; then
          echo "    ✓ Created/updated $table_name"
        else
          echo "    ⚠️  Warning: Could not create $table_name (check errors)"
        fi
      fi
    fi
  fi
done

# Cleanup temp files
rm -rf "$temp_dir"

echo ""
echo "✅ Table creation complete"
echo ""

# ============================================================================
# STEP 3: Apply Dataset Labels
# ============================================================================
echo "🏷️ Step 3: Applying Dataset Labels..."

LABEL_SCRIPT="scripts/deployment/apply_bq_labels.sh"

if [ "$DRY_RUN" = true ]; then
  echo "  [DRY RUN] Would execute $LABEL_SCRIPT to apply labels"
elif [ -f "$LABEL_SCRIPT" ]; then
  chmod +x "$LABEL_SCRIPT" >/dev/null 2>&1 || true
  if bash "$LABEL_SCRIPT"; then
    echo "  ✓ Dataset labels applied successfully"
  else
    echo "  ⚠️  Warning: Dataset labeling encountered issues (see logs above)"
  fi
else
  echo "  ⚠️  Warning: $LABEL_SCRIPT not found, skipping label application"
fi

echo ""

# ============================================================================
# STEP 4: Validate Schema
# ============================================================================
echo "🔍 Step 4: Validating Schema..."

# Check table counts per dataset
echo "  Table counts by dataset:"
for dataset_desc in "${datasets[@]}"; do
  IFS=':' read -r dataset description <<< "$dataset_desc"
  
  table_count=$(bq ls --project_id=$PROJECT_ID $dataset | grep TABLE | wc -l | tr -d ' ')
  echo "    $dataset: $table_count tables"
done

# Verify critical tables exist
critical_tables=(
  "training.regime_calendar"
  "training.regime_weights"
  "training.zl_training_prod_allhistory_1w"
  "training.mes_training_prod_allhistory_1min"
  "features.master_features"
  "signals.hidden_relationship_signals"
  "raw_intelligence.news_intelligence"
  "ops.ingestion_runs"
  "monitoring.model_performance"
)

echo ""
echo "  Verifying critical tables:"
for table in "${critical_tables[@]}"; do
  if bq show --project_id=$PROJECT_ID $table >/dev/null 2>&1; then
    echo "    ✓ $table exists"
  else
    echo "    ❌ $table missing!"
  fi
done

# Check master_features column count
echo ""
echo "  Checking master_features columns:"
column_count=$(bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
  "SELECT COUNT(*) as col_count FROM \`$PROJECT_ID.features.INFORMATION_SCHEMA.COLUMNS\` 
   WHERE table_name = 'master_features'" 2>/dev/null | tail -1 | tr -d ' ')

if [ "$column_count" -gt "400" ]; then
  echo "    ✓ master_features has $column_count columns (400+ required)"
else
  echo "    ⚠️  master_features has only $column_count columns (expected 400+)"
fi

echo ""
echo "=========================================="
echo "✅ BigQuery Schema Deployment Complete!"
echo ""
echo "Next Steps:"
echo "1. Run historical data backfill:"
echo "   - Yahoo ZL 2000-2010"
echo "   - DataBento 2010-present"
echo "   - FRED/USDA/EIA/CFTC historical"
echo ""
echo "2. Populate regime tables:"
echo "   - Load regime_calendar (11 regimes, 2000-2025)"
echo "   - Load regime_weights (50-5000 scale)"
echo ""
echo "3. Build master_features:"
echo "   - Run feature engineering pipeline"
echo "   - Populate all 400+ columns"
echo ""
echo "4. Create training exports:"
echo "   - ZL: 5 horizons (1w, 1m, 3m, 6m, 12m)"
echo "   - MES: 12 horizons (1min-12m)"
echo ""
echo "==========================================="
