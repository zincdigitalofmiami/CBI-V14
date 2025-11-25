#!/usr/bin/env python3
"""
TensorFlow CPU Mode Setup Script
Workaround for Metal plugin compatibility issue on M3 MacBook Air

This script configures TensorFlow to run in CPU mode, which is fully functional
for training (just slower than GPU). This is a known compatibility issue with
TensorFlow 2.20.0 + tensorflow-metal 1.2.0 on some M3 systems.
"""

import os
import sys

# Disable Metal plugin to avoid library loading errors
os.environ['TF_METAL_PLUGIN_DISABLE'] = '1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'  # Reduce TensorFlow logging

# Now import TensorFlow
try:
    import tensorflow as tf
    
    # Force CPU only
    tf.config.set_visible_devices([], 'GPU')
    
    print("✅ TensorFlow configured for CPU mode")
    print(f"TensorFlow version: {tf.__version__}")
    print(f"Keras version: {tf.keras.__version__}")
    
    # Test basic operations
    a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
    b = tf.constant([[1.0, 1.0], [0.0, 1.0]])
    c = tf.matmul(a, b)
    print(f"✅ Basic TensorFlow test passed: {c.numpy()}")
    
    # List available devices
    devices = tf.config.list_physical_devices()
    print(f"Available devices: {devices}")
    
    print("\n✅ TensorFlow is ready for training (CPU mode)")
    print("Note: Training will use CPU, which is slower but fully functional.")
    print("Metal GPU acceleration can be addressed separately if needed.")
    
except Exception as e:
    print(f"❌ Error setting up TensorFlow: {e}")
    sys.exit(1)

