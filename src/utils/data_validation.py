#!/usr/bin/env python3
"""
CRITICAL DATA VALIDATION FRAMEWORK
Prevents ANY fake/placeholder data from entering the pipeline
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import json

class AlphaDataValidator:
    """Validate all Alpha Vantage data - NO PLACEHOLDERS ALLOWED"""
    
    def __init__(self):
        self.validation_log = []
        self.rejection_count = 0
        self.acceptance_count = 0
    
    def validate_dataframe(self, df, data_type, symbol):
        """
        CRITICAL VALIDATION - Reject ANY suspicious data
        """
        
        print(f"\n{'='*60}")
        print(f"VALIDATING {data_type} for {symbol}")
        print(f"{'='*60}")
        
        # CHECK 1: Not empty
        if df.empty:
            self._reject(f"EMPTY DATAFRAME for {symbol}")
            return False
        
        # CHECK 2: Minimum rows
        min_rows = {
            'daily': 100,      # At least 100 trading days
            'intraday': 1000,  # At least 1000 bars
            'indicators': 100   # At least 100 days of indicators
        }
        
        if len(df) < min_rows.get(data_type, 100):
            self._reject(f"INSUFFICIENT DATA: Only {len(df)} rows for {symbol}")
            return False
        
        # CHECK 3: No placeholder values
        suspicious_values = [
            0.0,          # All zeros
            1.0,          # All ones
            -999.0,       # Common placeholder
            999999.0,     # Common placeholder
            np.nan        # NaN values
        ]
        
        for col in df.select_dtypes(include=[np.number]).columns:
            unique_vals = df[col].nunique()
            
            # Check if column has suspiciously low variance
            if unique_vals == 1:
                self._reject(f"STATIC COLUMN {col}: Only one unique value")
                return False
            
            # Check if column is all NaN
            if df[col].isna().all():
                self._reject(f"ALL NaN in column {col}")
                return False
            
            # Check if column has >50% NaN
            nan_pct = df[col].isna().sum() / len(df)
            if nan_pct > 0.5:
                self._reject(f"HIGH NaN RATE in {col}: {nan_pct:.1%}")
                return False
        
        # CHECK 4: Price validation (OHLC logic)
        if 'open' in df.columns and 'close' in df.columns:
            # Prices should vary
            price_variance = df['close'].std()
            if price_variance < 0.01:
                self._reject(f"NO PRICE VARIANCE: std={price_variance}")
                return False
            
            # High should be >= Low
            if 'high' in df.columns and 'low' in df.columns:
                invalid_bars = df[df['high'] < df['low']]
                if len(invalid_bars) > 0:
                    self._reject(f"INVALID BARS: {len(invalid_bars)} with high < low")
                    return False
        
        # CHECK 5: Date validation
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            
            # No future dates
            if df['date'].max() > pd.Timestamp.now() + timedelta(days=1):
                self._reject(f"FUTURE DATES FOUND: max={df['date'].max()}")
                return False
            
            # No ancient dates (before 1990)
            if df['date'].min() < pd.Timestamp('1990-01-01'):
                self._reject(f"ANCIENT DATES: min={df['date'].min()}")
                return False
        
        # CHECK 6: Technical indicator validation
        if 'RSI_14' in df.columns:
            # RSI must be 0-100
            invalid_rsi = df[(df['RSI_14'] < 0) | (df['RSI_14'] > 100)]
            if len(invalid_rsi) > 0:
                self._reject(f"INVALID RSI: {len(invalid_rsi)} values outside 0-100")
                return False
        
        # CHECK 7: Volume validation
        if 'volume' in df.columns:
            # Volume should not be negative
            if (df['volume'] < 0).any():
                self._reject(f"NEGATIVE VOLUME found")
                return False
            
            # Volume should vary
            if df['volume'].std() == 0:
                self._reject(f"NO VOLUME VARIANCE")
                return False
        
        # CHECK 8: Symbol consistency
        if 'symbol' in df.columns:
            if df['symbol'].nunique() != 1:
                self._reject(f"MULTIPLE SYMBOLS in single file: {df['symbol'].unique()}")
                return False
        
        # CHECK 9: Data freshness (for daily data)
        if data_type == 'daily' and 'date' in df.columns:
            latest_date = df['date'].max()
            days_old = (pd.Timestamp.now() - latest_date).days
            
            # Weekend-aware check
            if pd.Timestamp.now().weekday() < 5:  # Weekday
                if days_old > 3:
                    self._warn(f"STALE DATA: {days_old} days old")
        
        # CHECK 10: Calculate data hash for tracking
        data_hash = self._calculate_hash(df)
        
        # ALL CHECKS PASSED
        self._accept(f"✅ VALID: {symbol} {data_type} - {len(df)} rows, hash={data_hash[:8]}")
        return True
    
    def _reject(self, reason):
        """Log rejection with reason"""
        self.rejection_count += 1
        entry = {
            'timestamp': datetime.now().isoformat(),
            'status': 'REJECTED',
            'reason': reason
        }
        self.validation_log.append(entry)
        print(f"❌ REJECTED: {reason}")
        raise ValueError(f"Data validation failed: {reason}")
    
    def _accept(self, reason):
        """Log acceptance"""
        self.acceptance_count += 1
        entry = {
            'timestamp': datetime.now().isoformat(),
            'status': 'ACCEPTED',
            'reason': reason
        }
        self.validation_log.append(entry)
        print(f"✅ ACCEPTED: {reason}")
    
    def _warn(self, reason):
        """Log warning (doesn't reject)"""
        print(f"⚠️  WARNING: {reason}")
        self.validation_log.append({
            'timestamp': datetime.now().isoformat(),
            'status': 'WARNING',
            'reason': reason
        })
    
    def _calculate_hash(self, df):
        """Calculate hash of dataframe for verification"""
        return hashlib.sha256(
            pd.util.hash_pandas_object(df, index=True).values
        ).hexdigest()
    
    def save_validation_report(self, path):
        """Save validation report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_validations': len(self.validation_log),
            'accepted': self.acceptance_count,
            'rejected': self.rejection_count,
            'log': self.validation_log
        }
        
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Validation Report:")
        print(f"   Accepted: {self.acceptance_count}")
        print(f"   Rejected: {self.rejection_count}")
        print(f"   Report saved: {path}")


class DataIntegrityChecker:
    """Check data integrity across the entire pipeline"""
    
    @staticmethod
    def check_no_placeholders(directory):
        """
        Scan ALL parquet files for placeholder/fake data
        """
        print("\n" + "="*80)
        print("SCANNING FOR PLACEHOLDER DATA")
        print("="*80)
        
        issues = []
        files_checked = 0
        
        for parquet_file in Path(directory).rglob("*.parquet"):
            files_checked += 1
            print(f"\nChecking: {parquet_file.name}")
            
            try:
                df = pd.read_parquet(parquet_file)
                
                # Check for empty
                if df.empty:
                    issues.append(f"EMPTY: {parquet_file}")
                    continue
                
                # Check for placeholder patterns
                for col in df.select_dtypes(include=[np.number]).columns:
                    # All zeros
                    if (df[col] == 0).all():
                        issues.append(f"ALL ZEROS in {col}: {parquet_file}")
                    
                    # All same value
                    if df[col].nunique() == 1:
                        issues.append(f"STATIC {col}: {parquet_file}")
                    
                    # Sequential integers (likely fake)
                    if len(df) > 10:
                        if (df[col][:10] == range(10)).all():
                            issues.append(f"SEQUENTIAL {col}: {parquet_file}")
            
            except Exception as e:
                issues.append(f"ERROR reading {parquet_file}: {e}")
        
        print(f"\n{'='*80}")
        print(f"SCAN COMPLETE: {files_checked} files checked")
        
        if issues:
            print(f"❌ FOUND {len(issues)} ISSUES:")
            for issue in issues:
                print(f"   - {issue}")
            raise ValueError("Placeholder data detected!")
        else:
            print(f"✅ NO PLACEHOLDERS FOUND")
        
        return True


# Usage in collection pipeline:
def validate_before_save(df, symbol, data_type):
    """MUST call before saving any data"""
    validator = AlphaDataValidator()
    
    # This will RAISE if invalid
    validator.validate_dataframe(df, data_type, symbol)
    
    # Only reaches here if valid
    return True





