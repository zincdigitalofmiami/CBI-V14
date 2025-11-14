#!/bin/bash

# Legacy helper kept for backward compatibility.
# The new end-to-end setup workflow lives in setup_new_machine.sh.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TARGET_SCRIPT="${SCRIPT_DIR}/setup_new_machine.sh"

if [ ! -f "$TARGET_SCRIPT" ]; then
    echo "❌ setup_new_machine.sh not found next to setup_on_new_mac.sh."
    echo "Please pull the latest repository or run the new setup instructions manually."
    exit 1
fi

echo "⚠️  setup_on_new_mac.sh is deprecated."
echo "➡️  Redirecting to setup_new_machine.sh with the same arguments..."
exec "$TARGET_SCRIPT" "$@"



