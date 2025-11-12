#!/bin/bash
# Mac Training Dependencies Installation Script
# For M3 MacBook Air - Complete Setup

set -e  # Exit on error

echo "=========================================="
echo "Mac Training Dependencies Installation"
echo "M3 MacBook Air - Complete Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
echo ""

# Check if pip is available
echo "Checking pip..."
python3 -m pip --version
echo ""

# Upgrade pip first
echo "Upgrading pip..."
python3 -m pip install --upgrade pip
echo ""

# Install core ML/AI packages
echo "Installing TensorFlow and TensorFlow Metal..."
python3 -m pip install tensorflow tensorflow-metal
echo ""

# Install Keras (usually comes with TensorFlow, but install explicitly)
echo "Installing Keras..."
python3 -m pip install keras
echo ""

# Install data science packages (ensure latest versions)
echo "Installing data science packages..."
python3 -m pip install --upgrade numpy pandas scikit-learn
echo ""

# Install explainability
echo "Installing SHAP..."
python3 -m pip install shap
echo ""

# Install utilities
echo "Installing utilities..."
python3 -m pip install pyyaml click
echo ""

# Install optional but recommended
echo "Installing optional packages..."
python3 -m pip install types-pytz  # For pandas-stubs
echo ""

# Verify installations
echo "=========================================="
echo "Verifying Installations..."
echo "=========================================="
echo ""

echo "Testing TensorFlow..."
python3 -c "import tensorflow as tf; print('✅ TensorFlow:', tf.__version__)" || echo "❌ TensorFlow failed"

echo "Testing TensorFlow Metal GPU..."
python3 -c "import tensorflow as tf; gpus = tf.config.list_physical_devices('GPU'); print('✅ GPU Devices:', gpus if gpus else 'No GPU found')" || echo "❌ GPU check failed"

echo "Testing Keras..."
python3 -c "import keras; print('✅ Keras:', keras.__version__)" || echo "❌ Keras failed"

echo "Testing NumPy..."
python3 -c "import numpy as np; print('✅ NumPy:', np.__version__)" || echo "❌ NumPy failed"

echo "Testing Pandas..."
python3 -c "import pandas as pd; print('✅ Pandas:', pd.__version__)" || echo "❌ Pandas failed"

echo "Testing Scikit-learn..."
python3 -c "import sklearn; print('✅ Scikit-learn:', sklearn.__version__)" || echo "❌ Scikit-learn failed"

echo "Testing SHAP..."
python3 -c "import shap; print('✅ SHAP:', shap.__version__)" || echo "❌ SHAP failed"

echo "Testing PyYAML..."
python3 -c "import yaml; print('✅ PyYAML: OK')" || echo "❌ PyYAML failed"

echo "Testing Google Cloud BigQuery..."
python3 -c "from google.cloud import bigquery; print('✅ BigQuery: OK')" || echo "❌ BigQuery failed"

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify GPU access: python3 -c \"import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))\""
echo "2. Test GPU acceleration with a simple matrix multiplication"
echo "3. Proceed with data pipeline setup"

