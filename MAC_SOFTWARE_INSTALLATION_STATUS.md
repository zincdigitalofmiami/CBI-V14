# Mac Software Installation Status - M3 MacBook Air
**Date**: November 7, 2025  
**Purpose**: Verify all required software for Mac training, identify installed packages and issues

---

## Current Installation Status

### ✅ Installed & Working

| Package | Version | Status | Notes |
|---------|---------|--------|-------|
| **Python** | 3.12.8 | ✅ Installed | Compatible with M3 |
| **NumPy** | 1.26.4 | ✅ Installed | Required for TensorFlow |
| **Pandas** | 2.1.4 | ✅ Installed | Data manipulation |
| **Scikit-learn** | 1.7.2 | ✅ Installed | Preprocessing utilities |
| **Google Cloud BigQuery** | 3.14.0 | ✅ Installed | Data access |
| **Google Cloud AI Platform** | 1.38.0 | ✅ Installed | Optional deployment |
| **Google Cloud Storage** | 2.19.0 | ✅ Installed | Optional storage |

### ❌ Missing (Required for Training)

| Package | Status | Issue | Fix |
|---------|--------|-------|-----|
| **TensorFlow** | ❌ Not Installed | Missing | `pip install tensorflow` |
| **TensorFlow Metal** | ❌ Not Installed | Missing | `pip install tensorflow-metal` |
| **Keras** | ❌ Not Installed | Missing | Usually comes with TensorFlow |
| **SHAP** | ❌ Not Installed | Missing | `pip install shap` |

### ⚠️ Potentially Missing (Optional but Recommended)

| Package | Status | Purpose |
|---------|--------|---------|
| **PyYAML** | ✅ Installed | Config files |
| **Click** | ✅ Installed (8.3.0) | CLI interface |
| **types-pytz** | ⚠️ Missing | Required by pandas-stubs (optional) |

---

## Installation Issues & Solutions

### Issue 1: TensorFlow Not Installed

**Status**: ❌ **MISSING**

**Error**:
```
ModuleNotFoundError: No module named 'tensorflow'
```

**Solution**:
```bash
# Install TensorFlow (will also install Keras)
pip install tensorflow

# For M3 Mac, also install Metal plugin
pip install tensorflow-metal
```

**Verification**:
```python
import tensorflow as tf
print(tf.__version__)  # Should show 2.20.0 or later
print(tf.config.list_physical_devices('GPU'))  # Should show Metal GPU
```

**Expected Result**: TensorFlow 2.20.0+ with Metal GPU support

---

### Issue 2: SHAP Not Installed

**Status**: ❌ **MISSING**

**Error**:
```
ModuleNotFoundError: No module named 'shap'
```

**Solution**:
```bash
pip install shap
```

**Verification**:
```python
import shap
print(shap.__version__)  # Should show version number
```

**Expected Result**: SHAP installed for explainability features

---

### Issue 3: TensorFlow Metal Compatibility

**Status**: ⚠️ **NEEDS VERIFICATION**

**M3 Compatibility**:
- TensorFlow Metal supports M3 (Apple Silicon)
- Should work with M3 MacBook Air
- Need to verify after installation

**Installation Order** (Important):
```bash
# 1. Install TensorFlow first
pip install tensorflow

# 2. Then install Metal plugin
pip install tensorflow-metal

# 3. Verify GPU access
python3 -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

**Expected Result**: Metal GPU device visible

---

## Complete Installation Checklist

### Required Packages

```bash
# Core ML/AI packages
pip install tensorflow tensorflow-metal
pip install keras  # Usually comes with TensorFlow, but install explicitly
pip install numpy pandas scikit-learn

# Explainability
pip install shap

# Google Cloud (already installed, but verify)
pip install google-cloud-bigquery google-cloud-storage

# Utilities
pip install pyyaml click  # For config and CLI
```

### Installation Command (All at Once)

```bash
pip install tensorflow tensorflow-metal keras numpy pandas scikit-learn shap pyyaml click
```

---

## Post-Installation Verification

### Step 1: Verify TensorFlow Installation

```python
import tensorflow as tf
print("TensorFlow version:", tf.__version__)
print("Keras version:", tf.keras.__version__)
```

**Expected**: TensorFlow 2.20.0+, Keras 2.20.0+

### Step 2: Verify Metal GPU Access

```python
import tensorflow as tf
print("GPU Devices:", tf.config.list_physical_devices('GPU'))
print("Logical Devices:", tf.config.list_logical_devices('GPU'))
```

**Expected**: Should show Metal GPU device

### Step 3: Test GPU Acceleration

```python
import tensorflow as tf
import numpy as np

# Test GPU matrix multiplication
with tf.device('/GPU:0'):
    a = tf.random.normal([1000, 1000])
    b = tf.random.normal([1000, 1000])
    c = tf.matmul(a, b)
    print("GPU test passed:", c.shape)
```

**Expected**: Matrix multiplication completes successfully

### Step 4: Verify All Packages

```python
# Test all required packages
import tensorflow as tf
import keras
import numpy as np
import pandas as pd
import sklearn
import shap
from google.cloud import bigquery
import yaml
import click

print("✅ All packages imported successfully!")
```

---

## Known Issues & Solutions

### Issue: TensorFlow Metal Installation Fails

**Possible Causes**:
1. macOS version too old (need 12.0+)
2. Xcode command line tools missing
3. Python version incompatible

**Solutions**:
```bash
# Check macOS version
sw_vers  # Should be 12.0 or later

# Install Xcode command line tools
xcode-select --install

# Verify Python version
python3 --version  # Should be 3.9+ (you have 3.12.8 ✅)
```

### Issue: GPU Not Detected After Installation

**Possible Causes**:
1. TensorFlow Metal not installed
2. macOS Metal framework issue
3. TensorFlow version incompatible

**Solutions**:
```bash
# Reinstall TensorFlow Metal
pip uninstall tensorflow-metal
pip install tensorflow-metal

# Verify Metal framework
python3 -c "import Metal; print('Metal available')"  # Should work on macOS
```

### Issue: Memory Errors During Training

**Possible Causes**:
1. 8 GB RAM insufficient for large models
2. Batch size too large
3. Model too complex

**Solutions**:
```python
# Use smaller batch sizes
batch_size = 8  # or 16

# Enable mixed precision
tf.keras.mixed_precision.set_global_policy('mixed_float16')

# Clear memory between models
import gc
del model
gc.collect()
tf.keras.backend.clear_session()
```

---

## Installation Priority

### Priority 1: Critical (Must Install)
1. ✅ **TensorFlow** - Core ML framework
2. ✅ **TensorFlow Metal** - GPU acceleration for M3
3. ✅ **Keras** - High-level API (usually with TensorFlow)
4. ✅ **SHAP** - Explainability features

### Priority 2: Already Installed ✅
1. ✅ NumPy - Installed (1.26.4)
2. ✅ Pandas - Installed (2.1.4)
3. ✅ Scikit-learn - Installed (1.7.2)
4. ✅ Google Cloud BigQuery - Installed (3.14.0)

### Priority 3: Optional (Nice to Have)
1. ⚠️ PyYAML - Config files (not checked yet)
2. ✅ Click - CLI (installed 8.3.0)

---

## Installation Script

Create installation script for easy setup:

```bash
#!/bin/bash
# install_mac_training_dependencies.sh

echo "Installing Mac training dependencies for M3..."

# Core ML packages
pip install tensorflow tensorflow-metal
pip install keras

# Data science packages (some already installed, but ensure latest)
pip install numpy pandas scikit-learn

# Explainability
pip install shap

# Utilities
pip install pyyaml click

# Verify installation
python3 -c "import tensorflow as tf; print('TensorFlow:', tf.__version__)"
python3 -c "import tensorflow as tf; print('GPU:', tf.config.list_physical_devices('GPU'))"

echo "✅ Installation complete!"
```

---

## Current Status Summary

### ✅ Working
- Python 3.12.8
- NumPy 1.26.4
- Pandas 2.1.4
- Scikit-learn 1.7.2
- Google Cloud packages
- Click 8.3.0

### ❌ Missing (Need to Install)
- TensorFlow
- TensorFlow Metal
- Keras (may come with TensorFlow)
- SHAP

### ⚠️ Minor Issues
- types-pytz missing (optional, required by pandas-stubs)

---

## Next Steps

1. **Install Missing Packages**:
   ```bash
   pip install tensorflow tensorflow-metal keras shap pyyaml
   ```

2. **Verify Installation**:
   ```python
   import tensorflow as tf
   print(tf.config.list_physical_devices('GPU'))
   ```

3. **Test GPU Acceleration**:
   - Run simple matrix multiplication test
   - Verify Metal GPU is accessible

4. **Proceed with Training Setup**:
   - Once all packages installed and verified
   - Begin data pipeline setup

---

## Troubleshooting Guide

### If TensorFlow Installation Fails

1. **Check Python version**: `python3 --version` (should be 3.9+)
2. **Check macOS version**: `sw_vers` (should be 12.0+)
3. **Install Xcode tools**: `xcode-select --install`
4. **Try specific version**: `pip install tensorflow==2.20.0`

### If GPU Not Detected

1. **Verify Metal plugin**: `pip show tensorflow-metal`
2. **Check Metal framework**: Should be available on macOS
3. **Reinstall**: `pip uninstall tensorflow-metal && pip install tensorflow-metal`
4. **Check TensorFlow version**: Should be 2.20.0+ for M3 support

### If Memory Issues

1. **Reduce batch size**: Use 8 or 16 instead of 64
2. **Enable mixed precision**: `tf.keras.mixed_precision.set_global_policy('mixed_float16')`
3. **Train sequentially**: One model at a time
4. **Clear memory**: Use `gc.collect()` and `tf.keras.backend.clear_session()`

---

**Status**: Ready to install missing packages. All other dependencies are in place!

