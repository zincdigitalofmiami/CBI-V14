---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Installing OpenMP (libomp) for LightGBM/XGBoost

## Problem
LightGBM and XGBoost require the OpenMP runtime library (`libomp.dylib`) to function on macOS. Without it, you'll see errors like:
```
Library not loaded: @rpath/libomp.dylib
```

## Solution

### Step 1: Fix Homebrew Permissions
Run this command in your terminal (requires your password):
```bash
sudo chown -R $(whoami) /opt/homebrew
```

### Step 2: Install libomp
```bash
brew install libomp
```

### Step 3: Verify Installation
```bash
# Check if libomp is installed
ls -la /opt/homebrew/opt/libomp/lib/libomp.dylib

# Test Python imports
python3 -c "import lightgbm; print('LightGBM:', lightgbm.__version__)"
python3 -c "import xgboost; print('XGBoost:', xgboost.__version__)"
```

## Alternative: Manual Installation

If Homebrew isn't available or you prefer manual installation:

1. Download libomp from LLVM releases
2. Extract and copy `libomp.dylib` to a location in your library path
3. Set `DYLD_LIBRARY_PATH` environment variable

## After Installation

Once libomp is installed, LightGBM and XGBoost will work correctly. You can verify by running:
```python
import lightgbm as lgb
import xgboost as xgb
print("✅ Both libraries working!")
```

## Troubleshooting

If you still see errors after installation:
1. Verify libomp location: `brew list libomp`
2. Check library path: `echo $DYLD_LIBRARY_PATH`
3. Reinstall LightGBM/XGBoost: `pip3 install --force-reinstall lightgbm xgboost`



