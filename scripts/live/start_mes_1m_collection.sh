#!/bin/bash
# Start MES 1-minute data collection
# This script runs the MES 1-minute collector continuously

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

echo "🚀 Starting MES 1-minute data collection..."
echo "   Collection interval: 60 seconds"
echo "   Output: TrainingData/live/MES/1m/"
echo "   Press Ctrl+C to stop"

# Run with 60-second interval (1 minute)
python3 scripts/live/collect_mes_1m.py --interval 60 --lookback 120

