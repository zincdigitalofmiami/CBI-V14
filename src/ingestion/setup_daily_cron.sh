#!/bin/bash
# Wrapper retained for backwards compatibility with older runbooks.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

"$ROOT_DIR/scripts/crontab_setup.sh" "$@"
