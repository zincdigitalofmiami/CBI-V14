#!/bin/bash
# Deprecated wrapper kept for backwards compatibility.
# Calls the refreshed crontab_setup.sh installer.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)"

echo "ℹ️  crontab_optimized.sh is now a thin wrapper. Running crontab_setup.sh..."
"$SCRIPT_DIR/crontab_setup.sh" "$@"







