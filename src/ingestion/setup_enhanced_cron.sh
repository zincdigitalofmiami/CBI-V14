#!/bin/bash
# Wrapper retained for historical scripts; delegates to main cron installer.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

"$ROOT_DIR/scripts/crontab_setup.sh" "$@"













