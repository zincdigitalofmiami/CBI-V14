#!/bin/bash
#
# Train with Fresh Data - Best Practice Wrapper
# Ensures training data is current before training begins
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧠 TRAIN WITH FRESH DATA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if export files exist
EXPORT_DIR="$REPO_ROOT/TrainingData/exports"
if [[ ! -d "$EXPORT_DIR" ]] || [[ -z "$(ls -A "$EXPORT_DIR" 2>/dev/null)" ]]; then
    echo "⚠️  No training data found on external drive"
    echo "📥 Running initial export..."
    python3 "$REPO_ROOT/scripts/export_training_data.py"
else
    # Check age of export files
    NEWEST_FILE=$(find "$EXPORT_DIR" -name "*.parquet" -type f -print0 | xargs -0 ls -t | head -1)
    if [[ -n "$NEWEST_FILE" ]]; then
        FILE_AGE_DAYS=$(( ($(date +%s) - $(stat -f %m "$NEWEST_FILE")) / 86400 ))
        
        echo "📊 Training data status:"
        echo "   Latest export: $(basename "$NEWEST_FILE")"
        echo "   Age: $FILE_AGE_DAYS days old"
        
        if [[ $FILE_AGE_DAYS -gt 1 ]]; then
            echo "⚠️  Training data is >1 day old"
            echo "📥 Refreshing from BigQuery..."
            python3 "$REPO_ROOT/scripts/export_training_data.py"
        else
            echo "✅ Training data is fresh (<1 day old)"
        fi
    else
        echo "📥 Running export..."
        python3 "$REPO_ROOT/scripts/export_training_data.py"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 STARTING TRAINING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Pass all arguments to training script
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <training_script> [args...]"
    echo ""
    echo "Examples:"
    echo "  $0 src/training/train_simple_lstm.py --horizon=1m"
    echo "  $0 vertex-ai/deployment/train_local_deploy_vertex.py --horizon=1m"
    exit 1
fi

# Run the training script with all arguments
"$@"

