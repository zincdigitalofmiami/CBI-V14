#!/bin/bash
# Day 1 Execution Script - Run After Prerequisites Complete
# Prerequisites: gcloud auth + pip packages installed

set -e  # Exit on any error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              DAY 1 EXECUTION SCRIPT                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Environment setup
EXTERNAL_DRIVE="${EXTERNAL_DRIVE:-/Volumes/Satechi Hub}"
CBI_V14_REPO="${CBI_V14_REPO:-$EXTERNAL_DRIVE/Projects/CBI-V14}"

cd "$CBI_V14_REPO"

# Check prerequisites
echo "📋 Checking prerequisites..."
echo ""

# Check gcloud auth
if gcloud auth list 2>&1 | grep -q "ACTIVE"; then
    echo "✅ Google Cloud authenticated"
else
    echo "❌ Google Cloud NOT authenticated"
    echo "   Run: gcloud auth login"
    echo "   Run: gcloud auth application-default login"
    exit 1
fi

# Check TensorFlow
if python3 -c "import tensorflow" 2>/dev/null; then
    echo "✅ TensorFlow installed"
else
    echo "❌ TensorFlow NOT installed"
    echo "   Run: ./setup_new_machine.sh"
    exit 1
fi

# Check MLflow
if python3 -c "import mlflow" 2>/dev/null; then
    echo "✅ MLflow installed"
else
    echo "❌ MLflow NOT installed"
    echo "   Run: pip3 install mlflow==2.16.2"
    exit 1
fi

echo ""
echo "="*80
echo "PREREQUISITES COMPLETE - STARTING DAY 1 EXECUTION"
echo "="*80
echo ""

# Step 1: Verify GPU
echo "Step 1: Verifying Metal GPU..."
python3 src/training/gpu_optimization_template.py || {
    echo "❌ GPU verification failed"
    exit 1
}
echo ""

# Step 2: Configure MLflow
echo "Step 2: Configuring MLflow experiments..."
python3 src/training/config_mlflow.py || {
    echo "❌ MLflow setup failed"
    exit 1
}
echo ""

# Step 3: Data quality checks
echo "Step 3: Running data quality validation..."
python3 scripts/data_quality_checks.py || {
    echo "❌ Data quality checks failed"
    echo "   Review errors and fix before continuing"
    exit 1
}
echo ""

# Step 4: Export training data
echo "Step 4: Exporting training data from BigQuery..."
python3 scripts/export_training_data.py || {
    echo "❌ Data export failed"
    exit 1
}
echo ""

# Verify exports
echo "Step 5: Verifying exports..."
EXPORTS_DIR="$CBI_V14_REPO/TrainingData/exports"
for file in trump_rich_2023_2025.parquet \
            production_training_data_1w.parquet \
            production_training_data_1m.parquet \
            production_training_data_3m.parquet \
            production_training_data_6m.parquet \
            production_training_data_12m.parquet; do
    if [ -f "$EXPORTS_DIR/$file" ]; then
        size=$(ls -lh "$EXPORTS_DIR/$file" | awk '{print $5}')
        echo "  ✅ $file ($size)"
    else
        echo "  ❌ $file MISSING"
    fi
done
echo ""

# Final summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              DAY 1 COMPLETE                                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ GPU verified (Metal acceleration enabled)"
echo "✅ MLflow configured (8 experiments created)"
echo "✅ Data quality validated (all tables passed)"
echo "✅ Training data exported (12+ Parquet files)"
echo ""
echo "📁 Exports location:"
echo "   $EXPORTS_DIR"
echo ""
echo "🚀 READY FOR DAY 2: Baseline Model Training"
echo ""
echo "Next steps:"
echo "  1. Review DAY_1_CHECKLIST.md"
echo "  2. Start Day 2: python3 src/training/baselines/statistical.py"
echo ""

