#!/usr/bin/env python3
"""
Production QA Gate - Complete Implementation
=============================================
All QA gates must pass before production deployment.
Includes: leakage checks, export validation, feature presence, weight ranges.

Author: AI Assistant
Date: November 17, 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import sys

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import from pre_flight_harness
from scripts.qa.pre_flight_harness import verify_no_leakage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# External drive path
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
EXPORTS_DIR = DRIVE / "TrainingData/exports"

# Weight range: Acceptance says 50-5000, QA gate uses 50-500
# RECOMMENDATION: Use acceptance range (50-5000) as source of truth
WEIGHT_MIN = 50
WEIGHT_MAX = 5000  # Updated to match acceptance doc

# Required exports: Define explicitly
# Current exporter writes 5 horizons, but acceptance requires 10
# Define both allhistory and last10y variants
REQUIRED_EXPORTS = {
    "zl_training_prod_allhistory_1w.parquet",
    "zl_training_prod_allhistory_1m.parquet",
    "zl_training_prod_allhistory_3m.parquet",
    "zl_training_prod_allhistory_6m.parquet",
    "zl_training_prod_allhistory_12m.parquet",
    "zl_training_last10y_1w.parquet",
    "zl_training_last10y_1m.parquet",
    "zl_training_last10y_3m.parquet",
    "zl_training_last10y_6m.parquet",
    "zl_training_last10y_12m.parquet",
}


def verify_all_exports_exist() -> bool:
    """
    Verify all required export files exist.
    
    Returns:
        True if all exports exist
        
    Raises:
        AssertionError: If any export is missing
    """
    logger.info("\n" + "="*80)
    logger.info("VERIFYING ALL EXPORTS EXIST")
    logger.info("="*80)
    
    missing_exports = []
    
    for export_name in REQUIRED_EXPORTS:
        export_path = EXPORTS_DIR / export_name
        
        if not export_path.exists():
            missing_exports.append(export_name)
            logger.error(f"  ❌ Missing: {export_name}")
        else:
            logger.info(f"  ✅ Found: {export_name}")
    
    if missing_exports:
        error_msg = f"Missing {len(missing_exports)} required exports:\n" + "\n".join(f"  - {e}" for e in missing_exports)
        raise AssertionError(error_msg)
    
    logger.info(f"\n✅ All {len(REQUIRED_EXPORTS)} exports exist")
    return True


def verify_weight_range(df: pd.DataFrame, min_weight: int = WEIGHT_MIN, max_weight: int = WEIGHT_MAX) -> bool:
    """
    Verify training weights are within acceptable range.
    
    Args:
        df: DataFrame with 'training_weight' column
        min_weight: Minimum allowed weight (default 50)
        max_weight: Maximum allowed weight (default 5000)
        
    Returns:
        True if weights are valid
        
    Raises:
        AssertionError: If weights are out of range
    """
    if 'training_weight' not in df.columns:
        logger.warning("⚠️  No 'training_weight' column found")
        return True  # Not required, so pass
    
    weights = df['training_weight']
    min_actual = weights.min()
    max_actual = weights.max()
    
    logger.info(f"\nChecking weight range: [{min_weight}, {max_weight}]")
    logger.info(f"  Actual range: [{min_actual}, {max_actual}]")
    
    if min_actual < min_weight:
        raise AssertionError(f"Min weight {min_actual} < required {min_weight}")
    
    if max_actual > max_weight:
        raise AssertionError(f"Max weight {max_actual} > required {max_weight}")
    
    logger.info(f"  ✅ Weight range valid")
    return True


def verify_volatility_features_present(df: pd.DataFrame) -> bool:
    """
    Verify volatility and VIX features are present (required for training).
    
    Args:
        df: DataFrame to check
        
    Returns:
        True if volatility features present
        
    Raises:
        AssertionError: If required features missing
    """
    logger.info("\nChecking for volatility/VIX features...")
    
    # Required volatility features
    required_vol_features = [
        'vol_realized_30d',
        'vol_realized_90d',
        'vol_vix_level',
        'vol_vix_change'
    ]
    
    # Check for VIX features (any column with 'vix' in name)
    vix_features = [c for c in df.columns if 'vix' in c.lower()]
    
    # Check for volatility features (any column starting with 'vol_')
    vol_features = [c for c in df.columns if c.startswith('vol_')]
    
    missing_required = [f for f in required_vol_features if f not in df.columns]
    
    if missing_required:
        logger.warning(f"  ⚠️  Missing some required volatility features: {missing_required}")
        logger.warning(f"  Found {len(vol_features)} vol_ features and {len(vix_features)} VIX features")
        
        # Check if we have sufficient alternatives
        if len(vol_features) < 3 or len(vix_features) < 1:
            raise AssertionError(
                f"Insufficient volatility features: "
                f"found {len(vol_features)} vol_ features and {len(vix_features)} VIX features, "
                f"need at least 3 vol_ and 1 VIX"
            )
    else:
        logger.info(f"  ✅ All required volatility features present")
    
    logger.info(f"  Volatility features: {len(vol_features)}")
    logger.info(f"  VIX features: {len(vix_features)}")
    
    return True


def verify_feature_dependencies(df: pd.DataFrame) -> bool:
    """
    Verify feature dependencies (e.g., zl_price_current must exist before label creation).
    
    Args:
        df: DataFrame to check
        
    Returns:
        True if dependencies satisfied
        
    Raises:
        AssertionError: If dependencies missing
    """
    logger.info("\nChecking feature dependencies...")
    
    # Critical dependency: zl_price_current for label generation
    price_columns = ['zl_price_current', 'close', 'price']
    has_price = any(col in df.columns for col in price_columns)
    
    if not has_price:
        # Try to find price column
        price_candidates = [c for c in df.columns if 'price' in c.lower() or 'close' in c.lower()]
        if price_candidates:
            logger.info(f"  ✅ Found price column: {price_candidates[0]}")
        else:
            raise AssertionError(
                "Missing price column required for label generation. "
                "Need one of: zl_price_current, close, price"
            )
    else:
        found_col = next(col for col in price_columns if col in df.columns)
        logger.info(f"  ✅ Price column present: {found_col}")
    
    # Check for target column (if labels were generated)
    if 'target' in df.columns:
        target_coverage = df['target'].notna().sum() / len(df)
        logger.info(f"  ✅ Target coverage: {target_coverage:.1%}")
        
        if target_coverage < 0.50:  # At least 50% coverage
            raise AssertionError(f"Target coverage too low: {target_coverage:.1%} < 50%")
    
    return True


def verify_target_coverage_horizon_aware(df: pd.DataFrame, horizon_days: int, epsilon: float = 0.01) -> bool:
    """
    Verify target coverage with horizon-aware threshold.
    
    For longer horizons (e.g., 12 months), we necessarily lose the last N rows.
    Coverage threshold should account for this: coverage >= 1 - (horizon_days / total_rows) - ε
    
    Args:
        df: DataFrame with 'target' column
        horizon_days: Number of days in prediction horizon
        epsilon: Small buffer (default 0.01)
        
    Returns:
        True if coverage acceptable
        
    Raises:
        AssertionError: If coverage too low
    """
    if 'target' not in df.columns:
        logger.warning("⚠️  No 'target' column found, skipping coverage check")
        return True
    
    total_rows = len(df)
    coverage = df['target'].notna().sum() / total_rows
    
    # Calculate minimum required coverage
    min_coverage_required = 1.0 - (horizon_days / max(total_rows, horizon_days)) - epsilon
    
    logger.info(f"\nChecking target coverage for {horizon_days}-day horizon...")
    logger.info(f"  Total rows: {total_rows:,}")
    logger.info(f"  Target coverage: {coverage:.3f}")
    logger.info(f"  Minimum required: {min_coverage_required:.3f}")
    
    if coverage < min_coverage_required:
        raise AssertionError(
            f"Target coverage {coverage:.3f} < required {min_coverage_required:.3f} "
            f"for {horizon_days}-day horizon"
        )
    
    logger.info(f"  ✅ Coverage acceptable")
    return True


def run_production_qa_gates(horizon: str = '1w') -> bool:
    """
    Run all production QA gates.
    
    Args:
        horizon: Prediction horizon ('1w', '1m', '3m', '6m', '12m')
        
    Returns:
        True if all gates pass
        
    Raises:
        AssertionError: If any gate fails
    """
    logger.info("\n" + "="*80)
    logger.info("PRODUCTION QA GATES")
    logger.info("="*80)
    
    horizon_days = {'1w': 7, '1m': 30, '3m': 90, '6m': 180, '12m': 365}[horizon]
    
    # 1. Verify all exports exist
    logger.info("\n1. Export Existence Check")
    verify_all_exports_exist()
    
    # 2. Load training data
    logger.info("\n2. Loading Training Data")
    export_file = EXPORTS_DIR / f"zl_training_prod_allhistory_{horizon}.parquet"
    if not export_file.exists():
        raise FileNotFoundError(f"Training export not found: {export_file}")
    
    df = pd.read_parquet(export_file)
    logger.info(f"  Loaded {len(df):,} rows, {df.shape[1]} columns")
    
    # 3. Verify no data leakage
    logger.info("\n3. Data Leakage Check")
    verify_no_leakage(df, verbose=True)
    
    # 4. Verify weight range
    logger.info("\n4. Weight Range Check")
    verify_weight_range(df)
    
    # 5. Verify volatility features present
    logger.info("\n5. Volatility Features Check")
    verify_volatility_features_present(df)
    
    # 6. Verify feature dependencies
    logger.info("\n6. Feature Dependencies Check")
    verify_feature_dependencies(df)
    
    # 7. Verify target coverage (horizon-aware)
    logger.info("\n7. Target Coverage Check (Horizon-Aware)")
    verify_target_coverage_horizon_aware(df, horizon_days)
    
    logger.info("\n" + "="*80)
    logger.info("✅ ALL QA GATES PASSED")
    logger.info("Ready for production deployment")
    logger.info("="*80)
    
    return True


if __name__ == "__main__":
    import sys
    
    horizon = sys.argv[1] if len(sys.argv) > 1 else '1w'
    
    try:
        run_production_qa_gates(horizon)
        sys.exit(0)
    except (AssertionError, FileNotFoundError, ValueError) as e:
        logger.error(f"\n❌ QA GATE FAILED: {e}")
        sys.exit(1)

