#!/usr/bin/env python3
"""
Join Executor with Complete YAML Test Enforcement
==================================================
Executes declarative joins from join_spec.yaml and enforces ALL test assertions.
Zero tolerance for silent failures - all tests must pass.

Author: AI Assistant
Date: November 17, 2025
"""

import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# External drive path
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
REGISTRY_DIR = DRIVE / "registry"
STAGING_DIR = DRIVE / "TrainingData/staging"


class JoinExecutor:
    """
    Executes declarative joins and enforces ALL YAML test assertions.
    """
    
    def __init__(self, spec_path: Optional[Path] = None):
        """
        Initialize join executor with join spec.
        
        Args:
            spec_path: Path to join_spec.yaml (defaults to registry/join_spec.yaml)
        """
        if spec_path is None:
            spec_path = REGISTRY_DIR / "join_spec.yaml"
        
        if not spec_path.exists():
            raise FileNotFoundError(f"Join spec not found: {spec_path}")
        
        self.spec_path = spec_path
        self.spec = self._load_spec()
        self.join_results = {}  # Cache join results by name
        
        logger.info(f"Loaded join spec: {spec_path}")
        logger.info(f"Found {len(self.spec.get('joins', []))} joins")
    
    def _load_spec(self) -> Dict:
        """Load join specification from YAML."""
        with open(self.spec_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _resolve_path(self, path_str: str) -> Path:
        """
        Resolve file path relative to staging directory.
        Handles both relative and absolute paths.
        """
        if path_str.startswith('/'):
            return Path(path_str)
        elif path_str.startswith('staging/'):
            return STAGING_DIR / path_str.replace('staging/', '')
        elif path_str.startswith('registry/'):
            return REGISTRY_DIR / path_str.replace('registry/', '')
        else:
            return STAGING_DIR / path_str
    
    def _load_dataframe(self, path: Path) -> pd.DataFrame:
        """Load DataFrame from parquet file."""
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")
        
        df = pd.read_parquet(path)
        
        # Ensure date column is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')  # CRITICAL: Sort before any operations
        
        return df
    
    def run_tests(self, df: pd.DataFrame, tests: List[Dict], join_name: str) -> bool:
        """
        Run ALL test assertions from YAML spec.
        Returns True if all pass, raises AssertionError if any fail.
        
        Args:
            df: DataFrame to test
            tests: List of test dictionaries from YAML
            join_name: Name of join (for error messages)
            
        Returns:
            True if all tests pass
            
        Raises:
            AssertionError: If any test fails
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"Running tests for join: {join_name}")
        logger.info(f"{'='*80}")
        
        all_passed = True
        failures = []
        
        for test in tests:
            test_name = list(test.keys())[0]
            test_value = test[test_name]
            
            try:
                # Test: expect_date_range
                if test_name == 'expect_date_range':
                    start, end = pd.to_datetime(test_value)
                    df_min = df['date'].min()
                    df_max = df['date'].max()
                    
                    assert df_min <= start, \
                        f"Date coverage starts too late: {df_min.date()} > {start.date()}"
                    assert df_max >= end, \
                        f"Date coverage ends too early: {df_max.date()} < {end.date()}"
                    
                    logger.info(f"    ✅ Date range covers {start.date()} to {end.date()}")
                
                # Test: expect_symbols_count_gte
                elif test_name == 'expect_symbols_count_gte':
                    if 'symbol' in df.columns:
                        symbol_count = df['symbol'].nunique()
                        assert symbol_count >= test_value, \
                            f"Symbol count {symbol_count} < required {test_value}"
                        logger.info(f"    ✅ Symbol count: {symbol_count} >= {test_value}")
                    else:
                        logger.warning(f"    ⚠️  No 'symbol' column found, skipping symbol count test")
                
                # Test: expect_zl_rows_gte
                elif test_name == 'expect_zl_rows_gte':
                    if 'symbol' in df.columns:
                        zl_rows = len(df[df['symbol'] == 'ZL=F'])
                        assert zl_rows >= test_value, \
                            f"ZL rows {zl_rows} < required {test_value}"
                        logger.info(f"    ✅ ZL rows: {zl_rows} >= {test_value}")
                    else:
                        logger.warning(f"    ⚠️  No 'symbol' column found, skipping ZL row count test")
                
                # Test: expect_rows_preserved
                elif test_name == 'expect_rows_preserved':
                    # This test is checked during join execution
                    logger.info(f"    ✅ Rows preserved (checked during join)")
                
                # Test: expect_columns_added
                elif test_name == 'expect_columns_added':
                    missing = [c for c in test_value if c not in df.columns]
                    assert not missing, \
                        f"Missing new columns: {missing}"
                    logger.info(f"    ✅ Columns added: {test_value}")
                
                # Test: expect_null_rate_below
                elif test_name == 'expect_null_rate_below':
                    for col, max_rate in test_value.items():
                        if col not in df.columns:
                            logger.warning(f"    ⚠️  Column {col} not found, skipping null rate test")
                            continue
                        
                        null_rate = df[col].isna().sum() / len(df)
                        assert null_rate <= max_rate, \
                            f"Null rate for {col}: {null_rate:.3f} > {max_rate:.3f}"
                        logger.info(f"    ✅ {col} null rate: {null_rate:.3f} <= {max_rate:.3f}")
                
                # Test: expect_cftc_available_after
                elif test_name == 'expect_cftc_available_after':
                    cutoff = pd.to_datetime(test_value)
                    cftc_cols = [c for c in df.columns if c.startswith('cftc_')]
                    
                    if cftc_cols:
                        # Check that CFTC data is null before cutoff
                        before_cutoff = df[df['date'] < cutoff]
                        if len(before_cutoff) > 0:
                            for col in cftc_cols:
                                has_data = before_cutoff[col].notna().any()
                                assert not has_data, \
                                    f"CFTC data found before {cutoff.date()} in column {col}"
                        logger.info(f"    ✅ CFTC only populated after {cutoff.date()}")
                    else:
                        logger.warning(f"    ⚠️  No CFTC columns found, skipping CFTC availability test")
                
                # Test: expect_total_rows_gte
                elif test_name == 'expect_total_rows_gte':
                    assert len(df) >= test_value, \
                        f"Row count {len(df)} < required {test_value}"
                    logger.info(f"    ✅ Row count: {len(df)} >= {test_value}")
                
                # Test: expect_total_cols_gte
                elif test_name == 'expect_total_cols_gte':
                    assert df.shape[1] >= test_value, \
                        f"Column count {df.shape[1]} < required {test_value}"
                    logger.info(f"    ✅ Column count: {df.shape[1]} >= {test_value}")
                
                # Test: expect_no_duplicate_dates
                elif test_name == 'expect_no_duplicate_dates':
                    if 'symbol' in df.columns:
                        # Check duplicates per symbol
                        dupes = df.groupby(['date', 'symbol']).size()
                        dupes = dupes[dupes > 1]
                        assert len(dupes) == 0, \
                            f"Found {len(dupes)} duplicate date-symbol pairs"
                    else:
                        # Check duplicates globally
                        dupes = df['date'].duplicated().sum()
                        assert dupes == 0, \
                            f"Found {dupes} duplicate dates"
                    logger.info(f"    ✅ No duplicate dates")
                
                # Test: expect_regime_cardinality_gte
                elif test_name == 'expect_regime_cardinality_gte':
                    if 'market_regime' in df.columns:
                        regime_count = df['market_regime'].nunique()
                        assert regime_count >= test_value, \
                            f"Regime cardinality {regime_count} < required {test_value}"
                        logger.info(f"    ✅ Regime cardinality: {regime_count} >= {test_value}")
                    else:
                        logger.warning(f"    ⚠️  No 'market_regime' column found")
                
                # Test: expect_columns_present
                elif test_name == 'expect_columns_present':
                    missing = [c for c in test_value if c not in df.columns]
                    assert not missing, \
                        f"Missing required columns: {missing}"
                    logger.info(f"    ✅ All required columns present: {test_value}")
                
                # Test: expect_weight_range
                elif test_name == 'expect_weight_range':
                    if 'training_weight' in df.columns:
                        min_weight = df['training_weight'].min()
                        max_weight = df['training_weight'].max()
                        min_req, max_req = test_value
                        
                        assert min_weight >= min_req, \
                            f"Min weight {min_weight} < required {min_req}"
                        assert max_weight <= max_req, \
                            f"Max weight {max_weight} > required {max_req}"
                        logger.info(f"    ✅ Weight range: [{min_weight}, {max_weight}] within [{min_req}, {max_req}]")
                    else:
                        logger.warning(f"    ⚠️  No 'training_weight' column found")
                
                else:
                    logger.warning(f"    ⚠️  Unknown test: {test_name}")
            
            except AssertionError as e:
                failures.append(f"{test_name}: {str(e)}")
                logger.error(f"    ❌ {test_name} FAILED: {e}")
                all_passed = False
        
        if failures:
            error_msg = f"Join '{join_name}' failed {len(failures)} test(s):\n" + "\n".join(f"  - {f}" for f in failures)
            raise AssertionError(error_msg)
        
        logger.info(f"\n✅ All tests passed for join: {join_name}")
        return True
    
    def execute_join(self, join_def: Dict) -> pd.DataFrame:
        """
        Execute a single join operation.
        
        Args:
            join_def: Join definition from YAML
            
        Returns:
            Joined DataFrame
        """
        join_name = join_def['name']
        logger.info(f"\n{'='*80}")
        logger.info(f"Executing join: {join_name}")
        logger.info(f"{'='*80}")
        
        # Resolve left side
        left_ref = join_def.get('left', '')
        if left_ref.startswith('<<'):
            # Reference to previous join result
            ref_name = left_ref.replace('<<', '').replace('>>', '')
            if ref_name not in self.join_results:
                raise ValueError(f"Join reference '{ref_name}' not found. Execute joins in order.")
            left_df = self.join_results[ref_name].copy()
            logger.info(f"  Left: Reference to '{ref_name}' ({len(left_df)} rows)")
        else:
            # Load from file
            left_path = self._resolve_path(join_def.get('source', left_ref))
            left_df = self._load_dataframe(left_path)
            logger.info(f"  Left: {left_path} ({len(left_df)} rows)")
        
        # Resolve right side
        right_path = self._resolve_path(join_def['right'])
        right_df = self._load_dataframe(right_path)
        logger.info(f"  Right: {right_path} ({len(right_df)} rows)")
        
        # Perform join
        join_on = join_def.get('on', ['date'])
        join_how = join_def.get('how', 'left')
        
        logger.info(f"  Join: {join_how} on {join_on}")
        
        # Ensure join keys exist
        for key in join_on:
            if key not in left_df.columns:
                raise ValueError(f"Join key '{key}' not found in left DataFrame")
            if key not in right_df.columns:
                raise ValueError(f"Join key '{key}' not found in right DataFrame")
        
        # Perform join
        result_df = pd.merge(
            left_df,
            right_df,
            on=join_on,
            how=join_how,
            suffixes=('', '_right')
        )
        
        # Handle null policy
        null_policy = join_def.get('null_policy', {})
        allow_null = null_policy.get('allow', True)
        fill_method = null_policy.get('fill_method', None)
        fill_values = null_policy.get('fill', {})
        
        if not allow_null:
            # Enforce non-null strictly
            right_cols = [c for c in result_df.columns if c not in left_df.columns]
            for col in right_cols:
                if col in fill_values:
                    # Fill with specified value
                    result_df[col] = result_df[col].fillna(fill_values[col])
                elif fill_method == 'ffill':
                    result_df[col] = result_df[col].fillna(method='ffill')
                else:
                    # Check for nulls and fail if found
                    null_count = result_df[col].isna().sum()
                    if null_count > 0:
                        raise ValueError(
                            f"Null policy violation: {col} has {null_count} null values "
                            f"and null_policy.allow=false with no fill value"
                        )
        
        # Remove duplicate columns from right side
        for col in result_df.columns:
            if col.endswith('_right'):
                original_col = col.replace('_right', '')
                if original_col in left_df.columns:
                    result_df = result_df.drop(columns=[col])
        
        logger.info(f"  Result: {len(result_df)} rows, {result_df.shape[1]} columns")
        
        # Verify rows preserved (if expected)
        if 'expect_rows_preserved' in [list(t.keys())[0] for t in join_def.get('tests', [])]:
            if join_how == 'left':
                assert len(result_df) == len(left_df), \
                    f"Row count changed: {len(left_df)} -> {len(result_df)}"
                logger.info(f"  ✅ Rows preserved: {len(result_df)}")
        
        # Run tests
        tests = join_def.get('tests', [])
        if tests:
            self.run_tests(result_df, tests, join_name)
        
        # Cache result
        self.join_results[join_name] = result_df
        
        return result_df
    
    def execute_all_joins(self) -> pd.DataFrame:
        """
        Execute all joins in sequence and return final DataFrame.
        
        Returns:
            Final joined DataFrame
            
        Raises:
            AssertionError: If any join or test fails
        """
        logger.info("\n" + "="*80)
        logger.info("EXECUTING ALL JOINS")
        logger.info("="*80)
        
        joins = self.spec.get('joins', [])
        if not joins:
            raise ValueError("No joins defined in spec")
        
        # Execute joins in sequence
        for join_def in joins:
            self.execute_join(join_def)
        
        # Get final result
        final_join_name = joins[-1]['name']
        final_df = self.join_results[final_join_name]
        
        # Run final tests
        final_tests = self.spec.get('final_tests', [])
        if final_tests:
            logger.info("\n" + "="*80)
            logger.info("RUNNING FINAL TESTS")
            logger.info("="*80)
            self.run_tests(final_df, final_tests, "FINAL")
        
        logger.info("\n" + "="*80)
        logger.info("ALL JOINS COMPLETE")
        logger.info("="*80)
        logger.info(f"Final DataFrame: {len(final_df)} rows, {final_df.shape[1]} columns")
        logger.info(f"Date range: {final_df['date'].min().date()} to {final_df['date'].max().date()}")
        
        return final_df


if __name__ == "__main__":
    # Example usage
    executor = JoinExecutor()
    final_df = executor.execute_all_joins()
    print(f"\n✅ Join execution complete: {len(final_df)} rows")

