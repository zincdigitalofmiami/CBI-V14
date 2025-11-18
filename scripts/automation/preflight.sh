#!/usr/bin/env bash
# Preflight checks before any automated job runs
set -euo pipefail

# Check external drive mounted
if [ ! -d "/Volumes/Satechi Hub/Projects/CBI-V14" ]; then
  echo "❌ External drive not mounted"
  exit 64
fi

# Check Python venv exists
VENV_PYTHON="$HOME/Documents/GitHub/CBI-V14/venv/bin/python"
if [ ! -x "$VENV_PYTHON" ]; then
  # Try alternate location
  VENV_PYTHON="/Users/kirkmusick/Documents/GitHub/CBI-V14/venv/bin/python"
  if [ ! -x "$VENV_PYTHON" ]; then
    echo "❌ Python venv missing at expected locations"
    echo "   Create with: python3 -m venv venv && venv/bin/pip install -r requirements_training.txt"
    exit 65
  fi
fi

# Prevent sleep during job execution
caffeinate -ist $$ &

echo "✅ Preflight checks passed"
echo "   Drive: mounted"
echo "   Venv: $VENV_PYTHON"
echo "   Sleep: prevented"

exit 0



