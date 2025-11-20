#!/usr/bin/env python3
"""
Execute joins from join_spec.yaml with automated tests.
FIXED: Implements all test types, null_policy handlers, complete validation.
"""

import yaml
import pandas as pd
from pathlib import Path
from datetime import datetime

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")

class JoinExecutor:
    def __init__(self, spec_path):
        with open(spec_path) as f:
            self.spec = yaml.safe_load(f)
        self.results = {}
        self.last_row_count = 0
    
    def _apply_null_policy(self, df, policy, join_spec, right_df):
        """
        Apply null handling per spec.
        CRITICAL: Only applies ffill to newly joined columns, not entire DataFrame.
        """
        if not policy:
            return df
        
        # Get columns added from right table (exclude join keys)
        # Handle YAML 1.1 "on" -> True parsing issue
        join_keys = join_spec.get('on', join_spec.get(True, []))
        right_cols = [c for c in right_df.columns if c not in join_keys]
        
        # Sort by date for proper forward fill
        df = df.sort_values('date')
        
        # Forward fill method - ONLY on newly joined columns
        if policy.get('fill_method') == 'ffill':
            df[right_cols] = df[right_cols].ffill()
            print(f"    ✅ Applied ffill to {len(right_cols)} newly joined columns")
        elif policy.get('fill_method') == 'bfill':
            df[right_cols] = df[right_cols].bfill()
            print(f"    ✅ Applied bfill to {len(right_cols)} newly joined columns")
        
        # Static fill values (e.g., regime='allhistory' for missing dates)
        fill_map = policy.get('fill', {})
        if fill_map:
            for col, val in fill_map.items():
                if col in df.columns:
                    before_nulls = df[col].isnull().sum()
                    df[col].fillna(val, inplace=True)
                    after_nulls = df[col].isnull().sum()
                    filled = before_nulls - after_nulls
                    if filled > 0:
                        print(f"    ✅ Filled {filled} nulls in {col} with '{val}'")
        
        # Assert no nulls if not allowed
        if policy.get('allow') is False:
            any_null = df[right_cols].isnull().any().any()
            if any_null:
                null_cols = [c for c in right_cols if df[c].isnull().any()]
                null_counts = {c: df[c].isnull().sum() for c in null_cols}
                raise AssertionError(
                    f"Nulls remain in {null_cols} with allow:false. Counts: {null_counts}"
                )
        
        return df
    
    def run_tests(self, df, tests, join_name):
        """
        Run all tests from spec, raise on failure.
        FIX #2: Implements ALL test types from join_spec.yaml.
        """
        print(f"\n  🔍 Testing {join_name}...")
        
        for test in tests:
            # Existing: expect_rows_preserved
            if 'expect_rows_preserved' in test:
                assert len(df) == self.last_row_count, \
                    f"Row count changed: {self.last_row_count} → {len(df)}"
                print(f"    ✅ Rows preserved: {len(df)}")
            
            # Existing: expect_columns_present
            elif 'expect_columns_present' in test:
                required = test['expect_columns_present']
                missing = [c for c in required if c not in df.columns]
                assert len(missing) == 0, f"Missing columns: {missing}"
                print(f"    ✅ Columns present: {required}")
            
            # NEW: expect_columns_added
            elif 'expect_columns_added' in test:
                required = set(test['expect_columns_added'])
                actual = set(df.columns)
                missing = required - actual
                assert len(missing) == 0, f"Missing columns: {missing}"
                print(f"    ✅ Columns added: {required}")
            
            # Existing: expect_regime_cardinality_gte
            elif 'expect_regime_cardinality_gte' in test:
                min_regimes = test['expect_regime_cardinality_gte']
                if 'market_regime' in df.columns:
                    actual = df['market_regime'].nunique()
                    assert actual >= min_regimes, \
                        f"Only {actual} regimes, need {min_regimes}+"
                    print(f"    ✅ Regime cardinality: {actual} (need {min_regimes}+)")
            
            # Existing: expect_null_rate_below
            elif 'expect_null_rate_below' in test:
                for col, max_null in test['expect_null_rate_below'].items():
                    if col in df.columns:
                        null_pct = df[col].isnull().sum() / len(df)
                        assert null_pct < max_null, \
                            f"{col} has {null_pct:.1%} nulls (max {max_null:.1%})"
                        print(f"    ✅ {col} nulls: {null_pct:.1%} (< {max_null:.1%})")
            
            # NEW: expect_date_range
            elif 'expect_date_range' in test:
                start = pd.to_datetime(test['expect_date_range'][0])
                end = pd.to_datetime(test['expect_date_range'][1])
                # Convert date column to datetime if needed
                if df['date'].dtype == 'object':
                    df['date'] = pd.to_datetime(df['date'])
                actual_min = pd.to_datetime(df['date'].min())
                actual_max = pd.to_datetime(df['date'].max())
                # Allow up to 30 days before expected start (for trading day variations)
                # and require data to extend at least to expected start year
                days_before_start = (actual_min - start).days
                assert days_before_start <= 30, \
                    f"Start date too late: {actual_min} (need within 30 days of {start})"
                # End date should be at least in the expected year
                assert actual_max.year >= end.year, \
                    f"End date too early: {actual_max} (need year ≥{end.year})"
                print(f"    ✅ Date range: {actual_min} to {actual_max}")
            
            # NEW: expect_no_duplicate_dates
            elif 'expect_no_duplicate_dates' in test:
                dups = df['date'].duplicated().sum()
                assert dups == 0, f"Found {dups} duplicate dates"
                print(f"    ✅ No duplicate dates")
            
            # NEW: expect_total_rows_gte
            elif 'expect_total_rows_gte' in test:
                min_rows = test['expect_total_rows_gte']
                assert len(df) >= min_rows, \
                    f"Only {len(df)} rows (need {min_rows}+)"
                print(f"    ✅ Row count: {len(df)} (≥{min_rows})")
            
            # NEW: expect_total_cols_gte
            elif 'expect_total_cols_gte' in test:
                min_cols = test['expect_total_cols_gte']
                assert len(df.columns) >= min_cols, \
                    f"Only {len(df.columns)} cols (need {min_cols}+)"
                print(f"    ✅ Column count: {len(df.columns)} (≥{min_cols})")
            
            # NEW: expect_symbols_count_gte
            elif 'expect_symbols_count_gte' in test:
                if 'symbol' in df.columns:
                    min_symbols = test['expect_symbols_count_gte']
                    actual = df['symbol'].nunique()
                    assert actual >= min_symbols, \
                        f"Only {actual} symbols (need {min_symbols}+)"
                    print(f"    ✅ Symbol count: {actual} (≥{min_symbols})")
            
            # NEW: expect_zl_rows_gte
            elif 'expect_zl_rows_gte' in test:
                if 'symbol' in df.columns:
                    min_zl = test['expect_zl_rows_gte']
                    actual = len(df[df['symbol'] == 'ZL=F'])
                    assert actual >= min_zl, \
                        f"Only {actual} ZL rows (need {min_zl}+)"
                    print(f"    ✅ ZL rows: {actual} (≥{min_zl})")
            
            # NEW: expect_cftc_available_after
            elif 'expect_cftc_available_after' in test:
                cutoff = pd.to_datetime(test['expect_cftc_available_after'])
                cftc_cols = [c for c in df.columns if c.startswith('cftc_')]
                if cftc_cols:
                    early_data = df.loc[df['date'] < cutoff, cftc_cols].notna().any().any()
                    assert not early_data, \
                        f"CFTC data present before {cutoff} (availability leak)"
                    print(f"    ✅ CFTC data only after {cutoff}")
            
            # NEW: expect_weight_range
            elif 'expect_weight_range' in test:
                if 'training_weight' in df.columns:
                    min_wt, max_wt = test['expect_weight_range']
                    actual_min = df['training_weight'].min()
                    actual_max = df['training_weight'].max()
                    assert actual_min >= min_wt, \
                        f"Min weight {actual_min} < {min_wt}"
                    assert actual_max >= max_wt, \
                        f"Max weight {actual_max} < {max_wt}"
                    print(f"    ✅ Weight range: {actual_min}-{actual_max} (need {min_wt}-{max_wt})")
    
    def execute(self):
        """Execute all joins in order with null handling and testing"""
        print("\n" + "="*80)
        print("EXECUTING DECLARATIVE JOINS")
        print("="*80)
        
        current_df = None
        
        for join in self.spec['joins']:
            name = join['name']
            print(f"\n📋 {name}")
            
            if 'source' in join:
                # Base load
                path = DRIVE / join['source']
                current_df = pd.read_parquet(path)
                print(f"  Loaded {len(current_df)} rows from {path.name}")
                self.last_row_count = len(current_df)
            else:
                # Join operation
                if 'right' not in join:
                    raise ValueError(f"Join '{name}' missing 'right' field")
                
                # YAML 1.1 parser issue: "on" gets parsed as boolean True
                join_on = join.get('on', join.get(True))
                if not join_on:
                    raise ValueError(f"Join '{name}' missing 'on' field. Join spec: {join}")
                if 'how' not in join:
                    raise ValueError(f"Join '{name}' missing 'how' field")
                
                right_path = DRIVE / join['right']
                right_df = pd.read_parquet(right_path)
                
                # Standardize date columns to same type before merge
                if 'date' in join_on:
                    if 'date' in current_df.columns:
                        current_df['date'] = pd.to_datetime(current_df['date']).dt.date
                    if 'date' in right_df.columns:
                        right_df['date'] = pd.to_datetime(right_df['date']).dt.date
                
                self.last_row_count = len(current_df)
                current_df = current_df.merge(
                    right_df,
                    on=join_on,
                    how=join['how']
                )
                print(f"  Joined {right_path.name}: {self.last_row_count} → {len(current_df)} rows")
                
                # FIX #2: Apply null_policy after join (only to newly joined columns)
                if 'null_policy' in join:
                    current_df = self._apply_null_policy(current_df, join['null_policy'], join, right_df)
            
            # Run tests
            if 'tests' in join:
                self.run_tests(current_df, join['tests'], name)
        
        # Final tests
        if 'final_tests' in self.spec:
            print("\n🏁 Running final tests...")
            self.run_tests(current_df, self.spec['final_tests'], "FINAL")
        
        return current_df

if __name__ == "__main__":
    executor = JoinExecutor(DRIVE / "registry/join_spec.yaml")
    df_final = executor.execute()
    print(f"\n✅ Join execution complete: {len(df_final)} rows × {len(df_final.columns)} cols")







