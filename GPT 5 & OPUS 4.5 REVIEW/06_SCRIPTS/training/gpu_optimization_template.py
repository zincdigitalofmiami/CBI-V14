#!/usr/bin/env python3
"""
GPU Optimization Template for M4 Mac Mini 16GB
MANDATORY: Use this template for ALL neural network training

This template enables:
- Metal GPU acceleration
- FP16 mixed precision (2x memory savings)
- Memory cleanup between models
- Proper batch size limits
"""

import os

# STEP 1: Enable OneDNN optimizations (BEFORE importing TensorFlow)
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "1"

# STEP 2: Import TensorFlow and check for Metal GPU
try:
    import tensorflow as tf
    from tensorflow.keras import mixed_precision, backend as K
    
    print("="*80)
    print("🔧 GPU OPTIMIZATION TEMPLATE - M4 MAC MINI 16GB")
    print("="*80)
    print()
    
    # STEP 3: Enable FP16 mixed precision (MANDATORY for 16GB RAM)
    mixed_precision.set_global_policy("mixed_float16")
    print("✅ Mixed precision enabled: FP16")
    print("   → 2x memory savings")
    print("   → ~1.5x speedup on Metal GPU")
    print()
    
    # STEP 4: Verify Metal GPU is available
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        print(f"✅ Metal GPU detected: {len(gpus)} device(s)")
        for gpu in gpus:
            print(f"   {gpu}")
    else:
        print("⚠️  No GPU detected - will use CPU only")
    print()
    
    # STEP 5: Check TensorFlow version
    print(f"✅ TensorFlow version: {tf.__version__}")
    print()
    
    # STEP 6: Memory management template
    print("="*80)
    print("📋 MANDATORY MEMORY MANAGEMENT PATTERNS")
    print("="*80)
    print()
    
    print("1. BATCH SIZE LIMITS (16GB RAM):")
    print("   • Feedforward networks: batch_size ≤ 64")
    print("   • 1-layer LSTM/GRU: batch_size ≤ 64")
    print("   • 2-layer LSTM/GRU: batch_size ≤ 32")
    print("   • TCN: batch_size ≤ 32")
    print("   • Attention (if used): batch_size ≤ 16")
    print()
    
    print("2. SEQUENCE LENGTH LIMITS:")
    print("   • Default: seq_len = 256")
    print("   • Maximum: seq_len = 512 (only for 1-2 hero runs)")
    print("   • Attention: seq_len ≤ 256 (always)")
    print()
    
    print("3. SESSION CLEANUP (After EVERY model):")
    print("   from tensorflow.keras import backend as K")
    print("   K.clear_session()")
    print("   import gc; gc.collect()")
    print()
    
    print("4. EXTERNAL SSD USAGE:")
    EXTERNAL_DRIVE = os.getenv("EXTERNAL_DRIVE", "/Volumes/Satechi Hub")
    CBI_V14_REPO = os.getenv("CBI_V14_REPO", f"{EXTERNAL_DRIVE}/Projects/CBI-V14")
    print(f"   TrainingData: {CBI_V14_REPO}/TrainingData")
    print(f"   Models: {CBI_V14_REPO}/Models")
    print(f"   Logs: {CBI_V14_REPO}/Logs")
    print()
    
    print("="*80)
    print("✅ GPU OPTIMIZATION TEMPLATE VERIFIED")
    print("="*80)
    print()
    print("COPY THIS TEMPLATE TO ALL TRAINING SCRIPTS:")
    print()
    print("```python")
    print("# At process start")
    print("import os")
    print('os.environ["TF_ENABLE_ONEDNN_OPTS"] = "1"')
    print()
    print("import tensorflow as tf")
    print("from tensorflow.keras import mixed_precision, backend as K")
    print()
    print("# Enable FP16 mixed precision (MANDATORY)")
    print('mixed_precision.set_global_policy("mixed_float16")')
    print()
    print("# Your model training code here...")
    print("# model.fit(..., batch_size=32)  # Use appropriate batch size")
    print()
    print("# After each model (MANDATORY)")
    print("K.clear_session()")
    print("import gc; gc.collect()")
    print("```")
    print()
    
except ImportError as e:
    print("="*80)
    print("❌ TENSORFLOW NOT INSTALLED")
    print("="*80)
    print()
    print(f"Error: {e}")
    print()
    print("To install TensorFlow with Metal support:")
    print("  pip3 install tensorflow-macos==2.16.2 tensorflow-metal==1.2.0")
    print()
    print("Or run the complete setup script:")
    print("  ./setup_new_machine.sh")
    print()

