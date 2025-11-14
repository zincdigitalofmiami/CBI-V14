#!/bin/bash
# Deprecated wrapper retained for compatibility.
# Delegates to the unified cron installer introduced in November 2025.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)"

echo "ℹ️  enhanced_cron_setup.sh is deprecated. Delegating to crontab_setup.sh..."
"$SCRIPT_DIR/crontab_setup.sh" "$@"
