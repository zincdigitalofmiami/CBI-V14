#!/usr/bin/env python3
"""
Fix Yahoo Finance OHLC Violations
==================================
Fixes High < Low violations by swapping High and Low values.
These are data errors from Yahoo Finance where values are reversed.

Location: TrainingData/raw/yahoo_finance/prices/
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
YAHOO_DIR = EXTERNAL_DRIVE / "TrainingData/raw/yahoo_finance/prices"

def fix_ohlc_violations(file_path: Path) -> tuple:
    """
    Fix OHLC violations in a single file.
    Returns: (fixed_count, total_violations)
    """
    try:
        df = pd.read_parquet(file_path)
        
        # Find High < Low violations
        violations = df['High'] < df['Low']
        violation_count = violations.sum()
        
        if violation_count == 0:
            return (0, 0)
        
        # Fix by swapping High and Low
        df.loc[violations, ['High', 'Low']] = df.loc[violations, ['Low', 'High']].values
        
        # Verify fix
        remaining = (df['High'] < df['Low']).sum()
        if remaining > 0:
            logger.warning(f"  ⚠️  {file_path.name}: {remaining} violations remain after fix")
            return (violation_count - remaining, violation_count)
        
        # Save fixed file
        df.to_parquet(file_path, index=False)
        
        return (violation_count, violation_count)
        
    except Exception as e:
        logger.error(f"  ❌ Error fixing {file_path.name}: {e}")
        return (0, 0)

def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("FIXING YAHOO FINANCE OHLC VIOLATIONS")
    logger.info("="*80)
    
    if not YAHOO_DIR.exists():
        logger.error(f"Yahoo Finance directory not found: {YAHOO_DIR}")
        return 1
    
    total_fixed = 0
    total_violations = 0
    files_fixed = 0
    
    # Process all categories
    categories = ['commodities', 'currencies', 'indices', 'etfs', 'volatility']
    
    for category in categories:
        cat_dir = YAHOO_DIR / category
        if not cat_dir.exists():
            continue
        
        logger.info(f"\nProcessing {category}/...")
        files = list(cat_dir.glob('*.parquet'))
        
        for file_path in files:
            fixed, violations = fix_ohlc_violations(file_path)
            
            if violations > 0:
                files_fixed += 1
                total_fixed += fixed
                total_violations += violations
                logger.info(f"  ✅ {file_path.name}: Fixed {fixed} violations")
    
    logger.info("\n" + "="*80)
    logger.info("FIX SUMMARY")
    logger.info("="*80)
    logger.info(f"Files fixed: {files_fixed}")
    logger.info(f"Violations fixed: {total_fixed}")
    logger.info(f"Total violations found: {total_violations}")
    logger.info("="*80)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
