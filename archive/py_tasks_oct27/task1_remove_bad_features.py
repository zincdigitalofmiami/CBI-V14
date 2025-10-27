#!/usr/bin/env python3
"""
TASK 1: Remove Bad Features
From MASTER_WORK_LIST - DO NOT DEVIATE
"""

import pandas as pd
import numpy as np
from datetime import datetime

print("="*80)
print("TASK 1: REMOVING BAD FEATURES")
print("="*80)

# Load dataset
df = pd.read_csv('COMPLETE_TRAINING_DATA.csv')
print(f"\nOriginal dataset: {len(df)} rows × {len(df.columns)} columns")

initial_features = len(df.columns) - 1  # Excluding date

# Track what we remove
removal_report = {
    'sparse_features': [],
    'constant_features': [],
    'high_nan_features': []
}

# 1.1: Remove features with <10% coverage
print("\n1.1: Removing features with <10% coverage...")
print("-"*80)

for col in df.columns:
    if col == 'date':
        continue
    
    if df[col].dtype in [np.float64, np.int64]:
        non_zero = (df[col] != 0).sum()
        coverage = (non_zero / len(df)) * 100
    else:
        non_null = df[col].notna().sum()
        coverage = (non_null / len(df)) * 100
    
    if coverage < 10:
        removal_report['sparse_features'].append({
            'feature': col,
            'coverage': coverage,
            'reason': f'Only {coverage:.1f}% coverage'
        })
        print(f"  ❌ Removing {col:40} ({coverage:.1f}% coverage)")
        df = df.drop(columns=[col])

print(f"  Removed {len(removal_report['sparse_features'])} sparse features")

# 1.2: Remove constant features (1 unique value)
print("\n1.2: Removing constant features (1 unique value)...")
print("-"*80)

for col in df.columns:
    if col == 'date':
        continue
    
    unique = df[col].nunique()
    
    if unique == 1:
        sample_val = df[col].dropna().iloc[0] if df[col].notna().any() else 'ALL NaN'
        removal_report['constant_features'].append({
            'feature': col,
            'unique_values': unique,
            'value': sample_val,
            'reason': 'Constant - provides zero information'
        })
        print(f"  ❌ Removing {col:40} (only 1 unique value: {sample_val})")
        df = df.drop(columns=[col])

print(f"  Removed {len(removal_report['constant_features'])} constant features")

# 1.3: Remove features with >95% NaN
print("\n1.3: Removing features with >95% NaN...")
print("-"*80)

for col in df.columns:
    if col == 'date':
        continue
    
    nan_count = df[col].isna().sum()
    nan_pct = (nan_count / len(df)) * 100
    
    if nan_pct > 95:
        removal_report['high_nan_features'].append({
            'feature': col,
            'nan_percentage': nan_pct,
            'reason': f'{nan_pct:.1f}% NaN'
        })
        print(f"  ❌ Removing {col:40} ({nan_pct:.1f}% NaN)")
        df = df.drop(columns=[col])

print(f"  Removed {len(removal_report['high_nan_features'])} high-NaN features")

# 1.4: Save cleaned dataset
print("\n1.4: Saving cleaned dataset...")
print("-"*80)

df.to_csv('CLEANED_TRAINING_DATA.csv', index=False)
print(f"  ✅ Saved to: CLEANED_TRAINING_DATA.csv")
print(f"  Final shape: {len(df)} rows × {len(df.columns)} columns")

# 1.5: Generate removal report
print("\n1.5: Generating removal report...")
print("-"*80)

report_lines = []
report_lines.append("# TASK 1 REMOVAL REPORT")
report_lines.append(f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report_lines.append(f"\n## Summary")
report_lines.append(f"\n- Original features: {initial_features}")
report_lines.append(f"- Final features: {len(df.columns) - 1}")
report_lines.append(f"- Removed: {initial_features - (len(df.columns) - 1)} features")

report_lines.append(f"\n## Sparse Features Removed (<10% coverage)")
report_lines.append(f"\nTotal: {len(removal_report['sparse_features'])}")
for item in removal_report['sparse_features']:
    report_lines.append(f"\n- `{item['feature']}`: {item['reason']}")

report_lines.append(f"\n## Constant Features Removed (1 unique value)")
report_lines.append(f"\nTotal: {len(removal_report['constant_features'])}")
for item in removal_report['constant_features']:
    report_lines.append(f"\n- `{item['feature']}`: {item['reason']}")

report_lines.append(f"\n## High-NaN Features Removed (>95% NaN)")
report_lines.append(f"\nTotal: {len(removal_report['high_nan_features'])}")
for item in removal_report['high_nan_features']:
    report_lines.append(f"\n- `{item['feature']}`: {item['reason']}")

with open('TASK1_REMOVAL_REPORT.md', 'w') as f:
    f.write('\n'.join(report_lines))

print(f"  ✅ Saved to: TASK1_REMOVAL_REPORT.md")

# 1.6: Verify final feature count and coverage stats
print("\n1.6: Verifying final dataset quality...")
print("-"*80)

# Calculate coverage for remaining features
good_features = 0
for col in df.columns:
    if col == 'date':
        continue
    
    if df[col].dtype in [np.float64, np.int64]:
        non_zero = (df[col] != 0).sum()
        coverage = (non_zero / len(df)) * 100
    else:
        non_null = df[col].notna().sum()
        coverage = (non_null / len(df)) * 100
    
    if coverage >= 10:
        good_features += 1

print(f"  ✅ All {good_features} remaining features have ≥10% coverage")

# Check for any remaining issues
issues = []

# Check for any remaining constants
for col in df.columns:
    if col != 'date' and df[col].nunique() == 1:
        issues.append(f"Constant feature still present: {col}")

# Check for any remaining high-NaN
for col in df.columns:
    if col != 'date':
        nan_pct = (df[col].isna().sum() / len(df)) * 100
        if nan_pct > 95:
            issues.append(f"High-NaN feature still present: {col} ({nan_pct:.1f}%)")

if issues:
    print(f"\n  ⚠️ Issues found:")
    for issue in issues:
        print(f"    - {issue}")
else:
    print(f"  ✅ No issues found - dataset is clean")

# Summary
print("\n" + "="*80)
print("TASK 1 COMPLETE ✅")
print("="*80)

total_removed = len(removal_report['sparse_features']) + len(removal_report['constant_features']) + len(removal_report['high_nan_features'])

print(f"\n📊 Summary:")
print(f"  Initial features: {initial_features}")
print(f"  Removed features: {total_removed}")
print(f"  Final features: {len(df.columns) - 1}")
print(f"  Reduction: {(total_removed / initial_features) * 100:.1f}%")

print(f"\n📁 Files created:")
print(f"  • CLEANED_TRAINING_DATA.csv")
print(f"  • TASK1_REMOVAL_REPORT.md")

print(f"\n✅ Ready for TASK 2: Feature Selection")

