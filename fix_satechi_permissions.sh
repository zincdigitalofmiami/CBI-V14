#!/bin/bash
# Fix permissions on Satechi Hub external drive
# Run this script with: bash fix_satechi_permissions.sh

echo "🔧 Fixing permissions on Satechi Hub external drive..."
echo "   This requires your password for sudo access"
echo ""

sudo chown -R $(whoami):staff "/Volumes/Satechi Hub"
sudo chmod -R u+w "/Volumes/Satechi Hub"

if [ $? -eq 0 ]; then
    echo "✅ Permissions fixed successfully!"
    echo "   You can now run setup_new_machine.sh"
else
    echo "❌ Failed to fix permissions"
    exit 1
fi

