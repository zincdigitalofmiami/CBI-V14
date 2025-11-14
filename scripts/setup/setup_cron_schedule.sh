#!/bin/bash
# Legacy entry point retained for automation scripts.
# Delegates to the unified cron installer.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)"

echo "ℹ️  setup_cron_schedule.sh delegates to crontab_setup.sh"
"$SCRIPT_DIR/crontab_setup.sh" "$@"
