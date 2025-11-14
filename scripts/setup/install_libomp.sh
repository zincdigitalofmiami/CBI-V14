#!/bin/bash
# Install OpenMP runtime for LightGBM/XGBoost on macOS

set -e

echo "=========================================="
echo "Installing OpenMP (libomp) for LightGBM/XGBoost"
echo "=========================================="
echo ""

# Step 1: Fix Homebrew permissions
echo "Step 1: Fixing Homebrew permissions..."
echo "This requires your password:"
sudo chown -R $(whoami) /opt/homebrew

# Step 2: Install libomp
echo ""
echo "Step 2: Installing libomp..."
brew install libomp

# Step 3: Verify installation
echo ""
echo "Step 3: Verifying installation..."
if [ -f "/opt/homebrew/opt/libomp/lib/libomp.dylib" ]; then
    echo "✅ libomp.dylib found at /opt/homebrew/opt/libomp/lib/libomp.dylib"
else
    echo "⚠️  libomp.dylib not found in expected location"
    echo "Checking alternative locations..."
    find /opt /usr/local -name "libomp.dylib" 2>/dev/null || echo "Not found"
fi

# Step 4: Test Python imports
echo ""
echo "Step 4: Testing Python imports..."
python3 << 'PYEOF'
try:
    import lightgbm as lgb
    print(f"✅ LightGBM {lgb.__version__} - WORKING!")
except Exception as e:
    print(f"❌ LightGBM - FAILED: {e}")

try:
    import xgboost as xgb
    print(f"✅ XGBoost {xgb.__version__} - WORKING!")
except Exception as e:
    print(f"❌ XGBoost - FAILED: {e}")
PYEOF

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="

