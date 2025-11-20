#!/bin/bash
# M4 Mac Environment Setup Script
# Creates optimized Conda environment for Apple Silicon with all required libraries

set -e

ENV_NAME="${1:-cbi-m4-training}"
PYTHON_VERSION="3.12"

echo "=========================================="
echo "M4 MAC TRAINING ENVIRONMENT SETUP"
echo "=========================================="
echo "Environment: $ENV_NAME"
echo "Python: $PYTHON_VERSION"
echo ""

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "❌ Conda not found. Please install Miniforge for Apple Silicon:"
    echo "   https://github.com/conda-forge/miniforge"
    exit 1
fi

# Check architecture
ARCH=$(uname -m)
if [ "$ARCH" != "arm64" ]; then
    echo "⚠️  Warning: Not running on Apple Silicon (detected: $ARCH)"
    echo "   This script is optimized for arm64 (M-series chips)"
fi

echo "📦 Creating Conda environment..."
conda create -n "$ENV_NAME" python="$PYTHON_VERSION" -y

echo ""
echo "🔧 Activating environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

echo ""
echo "📥 Installing core scientific stack (arm64 optimized)..."
conda install -y -c conda-forge \
    numpy \
    scipy \
    pandas \
    scikit-learn \
    matplotlib \
    seaborn \
    jupyter \
    ipython

echo ""
echo "📥 Installing Polars (fast columnar processing)..."
pip install polars pyarrow

echo ""
echo "📥 Installing ML frameworks..."
# LightGBM (with OpenMP support)
pip install lightgbm

# XGBoost (with multithreading)
pip install xgboost

# TensorFlow for Mac (Metal GPU support)
pip install tensorflow-macos tensorflow-metal

# PyTorch (optional, with MPS support)
pip install torch torchvision

echo ""
echo "📥 Installing MLflow (model tracking)..."
pip install mlflow

echo ""
echo "📥 Installing Google Cloud libraries..."
pip install google-cloud-bigquery google-cloud-storage

echo ""
echo "📥 Installing utilities..."
pip install \
    psutil \
    tqdm \
    pyyaml \
    python-dotenv

echo ""
echo "✅ Environment setup complete!"
echo ""
echo "To activate:"
echo "  conda activate $ENV_NAME"
echo ""
echo "To verify TensorFlow Metal GPU:"
echo "  python -c 'import tensorflow as tf; print(tf.config.list_physical_devices(\"GPU\"))'"
echo ""
echo "To verify Polars:"
echo "  python -c 'import polars as pl; print(pl.__version__)'"
echo ""







