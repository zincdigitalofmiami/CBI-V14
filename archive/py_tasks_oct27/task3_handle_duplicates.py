#!/usr/bin/env python3
"""
TASK 3: Handle Duplicates
From MASTER_WORK_LIST - Resolve 12 duplicate dates
"""

import pandas as pd
import numpy as np
from datetime import datetime

print("="*80)
print("TASK 3: HANDLE DUPLICATE DATES")
print("="*80)

# Load dataset with selected features
df = pd.read_csv('FINAL_FEATURES_DATASET.csv')
df['date'] = pd.to_datetime(df['date'])

print(f"\nDataset: {len(df)} rows × {len(df.columns)} columns")

# 3.1: Identify duplicate dates
print("\n3.1: Identifying duplicate dates...")
print("-"*80)

duplicate_dates = df[df['date'].duplicated(keep=False)].sort_values('date')
unique_dup_dates = duplicate_dates['date'].unique()

print(f"  Total rows with duplicate dates: {len(duplicate_dates)}")
print(f"  Unique duplicate dates: {len(unique_dup_dates)}")

if len(unique_dup_dates) > 0:
    print(f"\n  Duplicate dates:")
    for date in unique_dup_dates:
        count = (df['date'] == date).sum()
        print(f"    {date.date()}: {count} occurrences")
else:
    print(f"  ✅ No duplicate dates found!")

# 3.2 & 3.3: Investigate duplicates
print("\n3.2-3.3: Investigating duplicate rows...")
print("-"*80)

resolution_decisions = []

for date in unique_dup_dates:
    date_rows = df[df['date'] == date]
    
    print(f"\n  Date: {date.date()} ({len(date_rows)} rows)")
    
    # Check if rows are identical
    if len(date_rows.drop(columns=['date']).drop_duplicates()) == 1:
        print(f"    → Rows are IDENTICAL - will keep first, drop rest")
        resolution_decisions.append({
            'date': date,
            'occurrences': len(date_rows),
            'resolution': 'drop_duplicates',
            'reason': 'Identical rows'
        })
    else:
        # Check which columns differ
        diff_cols = []
        first_row = date_rows.iloc[0]
        for col in date_rows.columns:
            if col == 'date':
                continue
            if not date_rows[col].equals(pd.Series([first_row[col]] * len(date_rows), index=date_rows.index)):
                diff_cols.append(col)
        
        print(f"    → Rows DIFFER in {len(diff_cols)} columns:")
        for col in diff_cols[:5]:
            vals = date_rows[col].values
            print(f"       {col}: {vals}")
        
        if len(diff_cols) > 5:
            print(f"       ... and {len(diff_cols) - 5} more")
        
        # Check if differences are NaN vs values (complementary)
        complementary = True
        for col in diff_cols:
            # If any row has non-NaN and others have NaN, it's complementary
            non_nan_count = date_rows[col].notna().sum()
            if non_nan_count > 0 and non_nan_count < len(date_rows):
                continue
            else:
                complementary = False
                break
        
        if complementary:
            print(f"    → Differences are COMPLEMENTARY (some NaN, some values)")
            print(f"    → Will MERGE by taking first non-NaN value per column")
            resolution_decisions.append({
                'date': date,
                'occurrences': len(date_rows),
                'resolution': 'merge_complementary',
                'reason': f'Complementary data in {len(diff_cols)} columns'
            })
        else:
            print(f"    → Differences are CONFLICTING (different non-NaN values)")
            print(f"    → Will keep FIRST occurrence (most conservative)")
            resolution_decisions.append({
                'date': date,
                'occurrences': len(date_rows),
                'resolution': 'keep_first',
                'reason': f'Conflicting data in {len(diff_cols)} columns'
            })

# 3.4 & 3.5: Apply resolution
print("\n3.4-3.5: Applying resolution strategy...")
print("-"*80)

df_resolved = df.copy()

for decision in resolution_decisions:
    date = decision['date']
    resolution = decision['resolution']
    
    date_mask = df_resolved['date'] == date
    date_rows = df_resolved[date_mask]
    
    if resolution == 'drop_duplicates':
        # Keep first, drop rest
        indices_to_drop = date_rows.index[1:]
        df_resolved = df_resolved.drop(indices_to_drop)
        print(f"  ✅ {date.date()}: Dropped {len(indices_to_drop)} duplicate rows")
        
    elif resolution == 'merge_complementary':
        # Merge by taking first non-NaN value
        merged_row = date_rows.iloc[0].copy()
        for col in date_rows.columns:
            if col == 'date':
                continue
            # Take first non-NaN value
            non_nan_vals = date_rows[col].dropna()
            if len(non_nan_vals) > 0:
                merged_row[col] = non_nan_vals.iloc[0]
        
        # Replace all rows with merged row
        indices_to_drop = date_rows.index[1:]
        df_resolved.loc[date_rows.index[0]] = merged_row
        df_resolved = df_resolved.drop(indices_to_drop)
        print(f"  ✅ {date.date()}: Merged {len(date_rows)} rows into 1")
        
    elif resolution == 'keep_first':
        # Keep first, drop rest
        indices_to_drop = date_rows.index[1:]
        df_resolved = df_resolved.drop(indices_to_drop)
        print(f"  ✅ {date.date()}: Kept first, dropped {len(indices_to_drop)} conflicting rows")

# 3.6: Verify no duplicates remain
print("\n3.6: Verifying no duplicates remain...")
print("-"*80)

remaining_duplicates = df_resolved[df_resolved['date'].duplicated()].shape[0]

if remaining_duplicates == 0:
    print(f"  ✅ No duplicate dates remain")
else:
    print(f"  ❌ WARNING: {remaining_duplicates} duplicate dates still present!")

# 3.7: Document resolution
print("\n3.7: Documenting resolution decisions...")
print("-"*80)

report_lines = []
report_lines.append("# TASK 3 DUPLICATE RESOLUTION REPORT")
report_lines.append(f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

report_lines.append(f"\n## Summary")
report_lines.append(f"\n- Original rows: {len(df)}")
report_lines.append(f"- Rows after resolution: {len(df_resolved)}")
report_lines.append(f"- Rows removed: {len(df) - len(df_resolved)}")
report_lines.append(f"- Duplicate dates found: {len(unique_dup_dates)}")
report_lines.append(f"- Remaining duplicates: {remaining_duplicates}")

report_lines.append(f"\n## Resolution Decisions")
for decision in resolution_decisions:
    report_lines.append(f"\n### {decision['date'].date()}")
    report_lines.append(f"- Occurrences: {decision['occurrences']}")
    report_lines.append(f"- Resolution: {decision['resolution']}")
    report_lines.append(f"- Reason: {decision['reason']}")

with open('TASK3_DUPLICATE_RESOLUTION_REPORT.md', 'w') as f:
    f.write('\n'.join(report_lines))

print(f"  ✅ Saved to: TASK3_DUPLICATE_RESOLUTION_REPORT.md")

# Save resolved dataset
df_resolved = df_resolved.sort_values('date').reset_index(drop=True)
df_resolved.to_csv('DEDUPLICATED_DATASET.csv', index=False)

print("\n" + "="*80)
print("TASK 3 COMPLETE ✅")
print("="*80)

print(f"\n📊 Summary:")
print(f"  Original rows: {len(df)}")
print(f"  Resolved rows: {len(df_resolved)}")
print(f"  Removed rows: {len(df) - len(df_resolved)}")
print(f"  Duplicate dates: {len(unique_dup_dates)}")
print(f"  Remaining duplicates: {remaining_duplicates}")

print(f"\n📁 Files created:")
print(f"  • DEDUPLICATED_DATASET.csv")
print(f"  • TASK3_DUPLICATE_RESOLUTION_REPORT.md")

print(f"\n✅ Ready for TASK 4: Verify No Leakage")

