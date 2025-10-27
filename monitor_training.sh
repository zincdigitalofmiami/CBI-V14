#!/bin/bash
# Monitor AutoML and DNN training progress

echo "=================================="
echo "🔍 TRAINING MONITOR"
echo "=================================="
echo "Timestamp: $(date)"
echo ""

echo "📊 AutoML Models Status:"
bq ls --models cbi-v14:models_v4 2>&1 | grep -E "automl|zl_automl" || echo "No AutoML models found yet"
echo ""

echo "📊 DNN Models Status:"
bq ls --models cbi-v14:models_v4 2>&1 | grep -E "dnn|DNN" | head -10
echo ""

echo "🔄 Running Jobs:"
bq ls -j --filter="states:RUNNING" | head -10
echo ""

echo "✅ Completed in last hour:"
bq ls -j --filter="states:DONE" --max_results=10 | head -10
echo ""

echo "=================================="





