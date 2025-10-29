#!/bin/bash
# Monitor training progress

echo "="
echo "TRAINING STATUS"
echo "================================================================"

# Check if training process is running
if pgrep -f "train_ensemble_system.py" > /dev/null; then
    echo "✅ Training is RUNNING"
else
    echo "⏸️ Training is NOT running (may have finished or failed)"
fi

echo ""
echo "Last 30 lines of output:"
echo "----------------------------------------------------------------"
tail -30 training_output.log 2>/dev/null || echo "No log file yet"

echo ""
echo "================================================================"
echo "Files created so far:"
ls -lh SPECIALIST_*.csv specialist_models.pkl 2>/dev/null || echo "No output files yet"

echo ""
echo "To watch live: tail -f training_output.log"

