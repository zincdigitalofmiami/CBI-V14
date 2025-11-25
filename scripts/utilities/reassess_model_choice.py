#!/usr/bin/env python3
"""
Reassess model choice given: 5 years of data, hundreds of features
Should BOOSTED_TREE or LINEAR be better with this much data?
"""
from google.cloud import bigquery

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
client = bigquery.Client(project=PROJECT_ID)

print("="*70)
print("🎯 REASSESSING MODEL CHOICE WITH 5 YEARS OF DATA")
print("="*70)

# Get actual data stats
query = f"""
SELECT 
  COUNT(*) as total_rows,
  COUNTIF(target_1w IS NOT NULL) as rows_with_target,
  MIN(date) as min_date,
  MAX(date) as max_date,
  DATE_DIFF(MAX(date), MIN(date), DAY) as days_span
FROM `{PROJECT_ID}.{DATASET_ID}.training_dataset_super_enriched`
"""
stats = client.query(query).to_dataframe().iloc[0]

total_rows = int(stats['total_rows'])
rows_with_target = int(stats['rows_with_target'])
years = stats['days_span'] / 365.25

print(f"\n📊 YOUR ACTUAL DATA:")
print(f"  • Total rows in dataset: {total_rows:,}")
print(f"  • Rows with target_1w: {rows_with_target:,}")
print(f"  • Date range: {stats['min_date']} to {stats['max_date']}")
print(f"  • Time span: {years:.1f} years")
print(f"  • Features available: ~201")

print(f"\n🔍 CURRENT SITUATION:")
print(f"  • Model trained on: {rows_with_target:,} rows")
print(f"  • Model using: 57 features (out of ~188)")
print(f"  • Performance: 8% MAPE (poor)")
print(f"  • Missing: 131 features (70%)")

print(f"\n📈 WITH 5 YEARS OF DATA:")

print(f"\nBOOSTED_TREE REASSESSMENT:")
print(f"  ✅ 5 years of data is ENOUGH for boosted trees")
print(f"  ✅ Can handle non-linear commodity price relationships")
print(f"  ✅ Should be able to use MORE than 57 features")
print(f"  ⚠️  But current model only uses 57 - why?")
print(f"     → Likely high feature correlation/redundancy")
print(f"     → Model drops correlated features automatically")
print(f"     → This is NORMAL but may exclude useful features")

print(f"\nLINEAR_REGRESSOR REASSESSMENT:")
print(f"  ✅ 5 years of data provides good sample for regularization")
print(f"  ✅ L2 regularization can handle correlated features")
print(f"  ✅ Uses ALL 188 features (no selection)")
print(f"  ⚠️  May miss non-linear patterns (commodity prices are complex)")
print(f"  ⚠️  But if missing features are the issue, this fixes it")

print(f"\n🎯 REVISED RECOMMENDATION:")

if rows_with_target > 2000:
    print(f"\n  → With {rows_with_target:,} rows, BOOSTED_TREE should perform well")
    print(f"     BUT: Current implementation excludes 131 features")
    print(f"\n  → TWO OPTIONS:")
    print(f"\n  OPTION 1: Fix BOOSTED_TREE (keep using it)")
    print(f"     • Issue: Model auto-excludes features due to correlation")
    print(f"     • Solution: Use feature engineering to reduce redundancy")
    print(f"     • Or: Accept that 57 features are the 'best' it found")
    print(f"     • Pro: Better for non-linear relationships")
    print(f"     • Con: Still missing 131 features")
    
    print(f"\n  OPTION 2: Switch to LINEAR_REGRESSOR (your request)")
    print(f"     • Pro: Uses ALL 188 features immediately")
    print(f"     • Pro: L2 regularization handles correlation safely")
    print(f"     • Pro: Faster to test - will show if missing features were the issue")
    print(f"     • Con: May miss some non-linear patterns")
    print(f"     • Cost: Negligible difference ($0.0003 vs $0.000006)")
    
    print(f"\n  💡 RECOMMENDATION:")
    print(f"     Given your 8% MAPE and suspicion about missing features:")
    print(f"     → Try LINEAR_REGRESSOR first (quick test)")
    print(f"     → If MAPE improves significantly → keep it")
    print(f"     → If still poor → BOOSTED_TREE with feature engineering")
else:
    print(f"\n  → With only {rows_with_target:,} rows (<2K), LINEAR may be safer")
    print(f"     → Use L2 regularization to prevent overfitting")

print(f"\n" + "="*70)
print(f"DECISION: LINEAR_REGRESSOR for initial test")
print(f"  Reason: You suspect missing features are causing 8% MAPE")
print(f"  Action: Test with all features, compare to current 8% MAPE")
print(f"  Next: If better → keep linear, if worse → optimize boosted tree")
print("="*70)










