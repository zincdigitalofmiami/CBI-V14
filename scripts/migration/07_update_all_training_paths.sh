#!/bin/bash
# Update all training script paths to new naming convention

REPO_ROOT="/Users/kirkmusick/Documents/GitHub/CBI-V14"

echo "Updating training script paths..."

# Update data paths: production_training_data_{h} → zl_training_prod_allhistory_{h}
find "$REPO_ROOT/src/training" -name "*.py" -type f -exec sed -i '' \
  's|production_training_data_\([^.]*\)\.parquet|zl_training_prod_allhistory_\1.parquet|g' {} \;

# Update model save paths (baselines)
find "$REPO_ROOT/src/training/baselines" -name "*.py" -type f -exec sed -i '' \
  's|Models/local/baselines|Models/local/horizon_{args.horizon}/prod/baselines|g' {} \;

# Update model save paths (advanced)
find "$REPO_ROOT/src/training/advanced" -name "*.py" -type f -exec sed -i '' \
  's|Models/local/advanced|Models/local/horizon_{args.horizon}/prod/advanced|g' {} \;

# Update model save paths (ensemble)
find "$REPO_ROOT/src/training/ensemble" -name "*.py" -type f -exec sed -i '' \
  's|Models/local|Models/local/horizon_{args.horizon}/prod/ensemble|g' {} \;

# Update model save paths (regime)
find "$REPO_ROOT/src/training/regime" -name "*.py" -type f -exec sed -i '' \
  's|Models/local/regime|Models/local/horizon_{args.horizon}/prod/regime|g' {} \;

echo "✅ Path updates complete"
echo "⚠️  NOTE: Manual review needed for f-string paths"

