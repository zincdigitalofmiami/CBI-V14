#!/usr/bin/env python3
"""
M4 Mac-optimized training configurations.
Provides hyperparameters tuned for Apple Silicon performance.

Key optimizations:
- CPU thread counts (4-6 performance cores)
- Mixed precision for neural nets (FP16/BF16)
- Batch sizes optimized for 16-48GB RAM
- Early stopping and regularization tuned for local training
"""
import os
from typing import Dict, Any, Optional

# Detect system resources
def get_cpu_count() -> int:
    """Get optimal CPU count for M-series chips."""
    import multiprocessing
    total_cores = multiprocessing.cpu_count()
    # M4 has 10 cores (4P + 6E), use 4-6 performance cores
    # Conservative: use 4-6 threads to avoid throttling
    return min(6, max(4, total_cores // 2))

def get_ram_gb() -> int:
    """Detect available RAM (simplified)."""
    try:
        import psutil
        return psutil.virtual_memory().total // (1024**3)
    except:
        # Default assumption
        return 16

# System detection
CPU_COUNT = get_cpu_count()
RAM_GB = get_ram_gb()

# LightGBM/XGBoost configurations
LIGHTGBM_CONFIG = {
    'num_leaves': 31,  # Conservative for M4
    'max_depth': 6,
    'learning_rate': 0.05,
    'n_estimators': 1500,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'min_child_samples': 100,  # Prevent overfitting small regimes
    'num_threads': CPU_COUNT,
    'verbose': -1,
    'objective': 'regression',
    'metric': 'mape',
    'boosting_type': 'dart',  # DART for better generalization
    'drop_rate': 0.1,
    'max_drop': 50,
    'skip_drop': 0.5,
}

XGBOOST_CONFIG = {
    'max_depth': 8,
    'learning_rate': 0.03,
    'n_estimators': 1500,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'min_child_weight': 3,
    'tree_method': 'hist',  # Fast histogram method
    'n_jobs': CPU_COUNT,
    'objective': 'reg:squarederror',
    'booster': 'dart',
    'rate_drop': 0.1,
    'skip_drop': 0.5,
}

# Neural network configurations
def get_neural_config(ram_gb: Optional[int] = None) -> Dict[str, Any]:
    """
    Get neural network config based on available RAM.
    
    Args:
        ram_gb: Available RAM in GB (auto-detected if None)
        
    Returns:
        Dictionary with neural network hyperparameters
    """
    if ram_gb is None:
        ram_gb = RAM_GB
    
    # Batch size scales with RAM
    if ram_gb >= 32:
        batch_size = 512
        sequence_length = 90
    elif ram_gb >= 24:
        batch_size = 256
        sequence_length = 60
    else:  # 16GB
        batch_size = 128
        sequence_length = 30
    
    return {
        'batch_size': batch_size,
        'sequence_length': sequence_length,
        'epochs': 100,
        'learning_rate': 1e-3,
        'optimizer': 'adamw',
        'mixed_precision': True,  # MANDATORY for M4
        'mixed_precision_policy': 'mixed_float16',  # FP16 for Metal
        'gradient_clip_norm': 1.0,
        'early_stopping_patience': 12,
        'early_stopping_restore_best_weights': True,
        'use_mps': True,  # Metal Performance Shaders
    }

# LSTM/GRU specific configs
LSTM_CONFIG = {
    **get_neural_config(),
    'units': 128,
    'dropout': 0.2,
    'recurrent_dropout': 0.1,
    'return_sequences': False,
}

GRU_CONFIG = {
    **get_neural_config(),
    'units': 128,
    'dropout': 0.2,
    'recurrent_dropout': 0.1,
    'return_sequences': False,
}

# Multi-layer LSTM (for advanced models)
MULTI_LAYER_LSTM_CONFIG = {
    **get_neural_config(),
    'layers': [
        {'units': 128, 'dropout': 0.2, 'return_sequences': True},
        {'units': 64, 'dropout': 0.2, 'return_sequences': False},
    ],
    'dense_units': [64, 32],
    'final_dropout': 0.3,
}

# Training split configuration
TRAIN_VAL_SPLIT = {
    'method': 'walk_forward',  # Walk-forward validation (not random)
    'train_months': 12,
    'test_months': 1,
    'step_months': 1,
    'min_train_samples': 100,
}

# Regime weighting (from training plan)
REGIME_WEIGHTS = {
    'trump_2023_2025': 5000,
    'trade_war_2017_2019': 1500,
    'inflation_2021_2022': 1200,
    'crisis_2008': 800,
    'crisis_2020': 500,
    'historical_pre2000': 50,
    'default': 100,
}

# Evaluation thresholds (gates for model promotion)
EVALUATION_THRESHOLDS = {
    'mape_max': {
        '1w': 3.0,   # 3% MAPE for 1 week
        '1m': 4.0,   # 4% MAPE for 1 month
        '3m': 6.0,   # 6% MAPE for 3 months
        '6m': 8.0,   # 8% MAPE for 6 months
        '12m': 12.0, # 12% MAPE for 12 months
    },
    'sharpe_min': {
        '1w': 1.2,
        '1m': 1.0,
        '3m': 0.8,
        '6m': 0.6,
        '12m': 0.5,
    },
    'mape_drift_max': 0.20,  # 20% drift from baseline
}

def get_config_for_model(model_type: str, horizon: Optional[str] = None) -> Dict[str, Any]:
    """
    Get configuration for a specific model type.
    
    Args:
        model_type: One of 'lightgbm', 'xgboost', 'lstm', 'gru', 'multi_lstm'
        horizon: Optional horizon for threshold lookups
        
    Returns:
        Configuration dictionary
    """
    configs = {
        'lightgbm': LIGHTGBM_CONFIG,
        'xgboost': XGBOOST_CONFIG,
        'lstm': LSTM_CONFIG,
        'gru': GRU_CONFIG,
        'multi_lstm': MULTI_LAYER_LSTM_CONFIG,
    }
    
    if model_type not in configs:
        raise ValueError(f"Unknown model type: {model_type}")
    
    config = configs[model_type].copy()
    
    # Add horizon-specific thresholds if provided
    if horizon and horizon in EVALUATION_THRESHOLDS['mape_max']:
        config['target_mape'] = EVALUATION_THRESHOLDS['mape_max'][horizon]
        config['target_sharpe'] = EVALUATION_THRESHOLDS['sharpe_min'][horizon]
    
    return config

def print_system_info():
    """Print detected system configuration."""
    print("="*80)
    print("M4 MAC SYSTEM CONFIGURATION")
    print("="*80)
    print(f"CPU Threads: {CPU_COUNT}")
    print(f"RAM: {RAM_GB} GB")
    print(f"Batch Size (Neural): {get_neural_config()['batch_size']}")
    print(f"Sequence Length: {get_neural_config()['sequence_length']}")
    print(f"Mixed Precision: {get_neural_config()['mixed_precision']}")
    print("="*80)

if __name__ == "__main__":
    print_system_info()
    print("\nLightGBM Config:")
    print(LIGHTGBM_CONFIG)
    print("\nLSTM Config:")
    print(LSTM_CONFIG)

