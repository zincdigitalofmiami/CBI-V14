#!/usr/bin/env python3
"""
Comprehensive Audit for 1W Model Training
Checks all prerequisites before training bqml_1w_mean
"""
from google.cloud import bigquery
from datetime import datetime
import sys

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
MODEL_NAME = "bqml_1w_mean"
VIEW_NAME = "train_1w"
TARGET_COL = "target_1w"

client = bigquery.Client(project=PROJECT_ID)

print("="*70)
print("🔍 COMPREHENSIVE 1W TRAINING AUDIT")
print("="*70)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Model: {MODEL_NAME}")
print(f"Training View: {VIEW_NAME}")
print(f"Target: {TARGET_COL}")
print("="*70)

all_checks_passed = True
issues = []
warnings = []

# 1. Check training view exists
print("\n1️⃣  TRAINING VIEW EXISTENCE:")
try:
    query = f"""
    SELECT COUNT(*) as view_exists
    FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.VIEWS`
    WHERE table_name = '{VIEW_NAME}'
    """
    result = client.query(query).to_dataframe()
    if result.iloc[0]['view_exists'] > 0:
        print(f"  ✅ View '{VIEW_NAME}' exists")
    else:
        print(f"  ❌ View '{VIEW_NAME}' does not exist")
        issues.append(f"Training view {VIEW_NAME} missing")
        all_checks_passed = False
except Exception as e:
    print(f"  ❌ Error checking view: {e}")
    issues.append(f"Could not check view existence: {e}")
    all_checks_passed = False

# 2. Check view structure and label leakage
print("\n2️⃣  VIEW STRUCTURE & LABEL LEAKAGE:")
try:
    # Get all columns
    query = f"""
    SELECT column_name, data_type
    FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{VIEW_NAME}'
    ORDER BY ordinal_position
    """
    columns_df = client.query(query).to_dataframe()
    
    # Check target exists
    has_target = TARGET_COL in columns_df['column_name'].values
    if has_target:
        print(f"  ✅ Target column '{TARGET_COL}' present")
    else:
        print(f"  ❌ Target column '{TARGET_COL}' missing")
        issues.append(f"Target column {TARGET_COL} not found in view")
        all_checks_passed = False
    
    # Check for other target columns (label leakage)
    other_targets = ['target_1m', 'target_3m', 'target_6m']
    leakage_cols = [col for col in other_targets if col in columns_df['column_name'].values]
    
    if leakage_cols:
        print(f"  ❌ LABEL LEAKAGE DETECTED: {', '.join(leakage_cols)} present in view")
        issues.append(f"Label leakage: {leakage_cols} found in training view")
        all_checks_passed = False
    else:
        print(f"  ✅ No label leakage (other targets excluded)")
    
    # Check date column exists
    has_date = 'date' in columns_df['column_name'].values
    if has_date:
        print(f"  ✅ Date column present (needed for train/val split)")
    else:
        print(f"  ⚠️  Date column missing (may affect train/val split)")
        warnings.append("Date column missing - train/val split may fail")
    
    # Count features (excluding targets, date, and known exclusions)
    exclusion_cols = {
        'date', TARGET_COL, 'target_1m', 'target_3m', 'target_6m',
        'treasury_10y_yield', 'econ_gdp_growth', 'econ_unemployment_rate',
        'news_article_count', 'news_avg_score',
        'crude_lead1_correlation', 'dxy_lead1_correlation', 'vix_lead1_correlation',
        'palm_lead2_correlation', 'leadlag_zl_price', 'lead_signal_confidence',
        'days_to_next_event', 'post_event_window'
    }
    feature_cols = [col for col in columns_df['column_name'].values 
                    if col not in exclusion_cols]
    feature_count = len(feature_cols)
    
    print(f"  📊 Total columns: {len(columns_df)}")
    print(f"  📊 Feature columns (excluding targets/exclusions): {feature_count}")
    
    if feature_count < 200:
        print(f"  ⚠️  Low feature count ({feature_count} < 200 expected)")
        warnings.append(f"Feature count lower than expected: {feature_count}")
    elif feature_count > 220:
        print(f"  ⚠️  High feature count ({feature_count} > 220 expected)")
        warnings.append(f"Feature count higher than expected: {feature_count}")
    else:
        print(f"  ✅ Feature count in expected range (200-220)")

except Exception as e:
    print(f"  ❌ Error checking structure: {e}")
    issues.append(f"Structure check failed: {e}")
    all_checks_passed = False

# 3. Check data availability and quality
print("\n3️⃣  DATA AVAILABILITY & QUALITY:")
try:
    query = f"""
    SELECT 
      COUNT(*) as total_rows,
      COUNTIF({TARGET_COL} IS NOT NULL) as valid_targets,
      COUNTIF({TARGET_COL} IS NULL) as null_targets,
      MIN({TARGET_COL}) as min_target,
      MAX({TARGET_COL}) as max_target,
      AVG({TARGET_COL}) as avg_target,
      STDDEV({TARGET_COL}) as stddev_target,
      COUNTIF(date < '2025-09-01') as train_rows,
      COUNTIF(date >= '2025-09-01') as val_rows
    FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}`
    """
    stats = client.query(query).to_dataframe().iloc[0]
    
    total_rows = int(stats['total_rows'])
    valid_targets = int(stats['valid_targets'])
    null_targets = int(stats['null_targets'])
    train_rows = int(stats['train_rows'])
    val_rows = int(stats['val_rows'])
    
    print(f"  📊 Total rows: {total_rows:,}")
    print(f"  ✅ Valid targets: {valid_targets:,}")
    print(f"  ⚠️  NULL targets: {null_targets:,}")
    
    if valid_targets < 500:
        print(f"  ❌ INSUFFICIENT DATA: Only {valid_targets} valid targets (<500 minimum)")
        issues.append(f"Insufficient data: {valid_targets} valid targets")
        all_checks_passed = False
    elif valid_targets < 1000:
        print(f"  ⚠️  Low data count ({valid_targets} < 1000 recommended)")
        warnings.append(f"Low target count: {valid_targets}")
    
    print(f"\n  📈 Target Statistics:")
    print(f"     Min: ${stats['min_target']:.2f}")
    print(f"     Max: ${stats['max_target']:.2f}")
    print(f"     Avg: ${stats['avg_target']:.2f}")
    print(f"     StdDev: ${stats['stddev_target']:.2f}")
    
    if stats['min_target'] <= 0:
        print(f"  ⚠️  Negative or zero target values detected")
        warnings.append("Target values include negative or zero")
    
    print(f"\n  📅 Train/Val Split:")
    print(f"     Training rows (before 2025-09-01): {train_rows:,}")
    print(f"     Validation rows (after 2025-09-01): {val_rows:,}")
    
    if train_rows < 400:
        print(f"  ❌ INSUFFICIENT TRAINING DATA: Only {train_rows} training rows")
        issues.append(f"Insufficient training data: {train_rows} rows")
        all_checks_passed = False
    
    if val_rows < 50:
        print(f"  ⚠️  Low validation data: {val_rows} rows (may affect evaluation)")
        warnings.append(f"Low validation set: {val_rows} rows")

except Exception as e:
    print(f"  ❌ Error checking data: {e}")
    issues.append(f"Data quality check failed: {e}")
    all_checks_passed = False

# 4. Check temporal leakage features are excluded
print("\n4️⃣  TEMPORAL LEAKAGE CHECK:")
temporal_leakage_features = [
    'crude_lead1_correlation',
    'dxy_lead1_correlation',
    'vix_lead1_correlation',
    'palm_lead2_correlation',
    'leadlag_zl_price',
    'lead_signal_confidence',
    'days_to_next_event',
    'post_event_window'
]

try:
    query = f"""
    SELECT column_name
    FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{VIEW_NAME}'
    AND column_name IN ({', '.join([f"'{f}'" for f in temporal_leakage_features])})
    """
    leakage_cols_df = client.query(query).to_dataframe()
    
    if len(leakage_cols_df) > 0:
        leakage_found = leakage_cols_df['column_name'].tolist()
        print(f"  ❌ TEMPORAL LEAKAGE DETECTED: {', '.join(leakage_found)} present")
        issues.append(f"Temporal leakage features found: {leakage_found}")
        all_checks_passed = False
    else:
        print(f"  ✅ No temporal leakage features found (all excluded)")
except Exception as e:
    print(f"  ⚠️  Could not check temporal leakage: {e}")
    warnings.append(f"Temporal leakage check incomplete: {e}")

# 5. Check SQL file configuration
print("\n5️⃣  TRAINING SQL FILE CHECK:")
try:
    import pathlib
    sql_file = pathlib.Path(__file__).parent.parent / "bigquery_sql" / "train_bqml_1w_mean.sql"
    
    if sql_file.exists():
        print(f"  ✅ SQL file exists: {sql_file}")
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Check for key configurations
        checks = {
            'model_type': 'BOOSTED_TREE_REGRESSOR' in sql_content,
            'target_column': f"input_label_cols=['{TARGET_COL}']" in sql_content,
            'custom_split': 'data_split_method' in sql_content and 'CUSTOM' in sql_content,
            'is_training': 'is_training' in sql_content,
            'temporal_exclusions': all(leak in sql_content for leak in temporal_leakage_features),
            'view_reference': f'FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}`' in sql_content,
        }
        
        for check_name, passed in checks.items():
            if passed:
                print(f"  ✅ {check_name}: Correct")
            else:
                print(f"  ❌ {check_name}: Missing or incorrect")
                issues.append(f"SQL file missing {check_name}")
                all_checks_passed = False
    else:
        print(f"  ❌ SQL file not found: {sql_file}")
        issues.append(f"SQL file missing: {sql_file}")
        all_checks_passed = False
except Exception as e:
    print(f"  ❌ Error checking SQL file: {e}")
    issues.append(f"SQL file check failed: {e}")
    all_checks_passed = False

# 6. Check if model already exists
print("\n6️⃣  EXISTING MODEL CHECK:")
model_exists = False
try:
    # Try ML.TRIAL_INFO first (for hyperparameter-tuned models)
    query = f"""
    SELECT COUNT(*) as trial_count
    FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
    """
    trial_check = client.query(query).to_dataframe()
    if not trial_check.empty and trial_check.iloc[0]['trial_count'] > 0:
        model_exists = True
        print(f"  ✅ Model '{MODEL_NAME}' exists (hyperparameter-tuned)")
        print(f"     Trials: {int(trial_check.iloc[0]['trial_count'])}")
except Exception:
    # If TRIAL_INFO fails, try TRAINING_INFO (for regular models)
    try:
        query = f"""
        SELECT COUNT(*) as iteration_count
        FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
        """
        train_check = client.query(query).to_dataframe()
        if not train_check.empty:
            model_exists = True
            print(f"  ✅ Model '{MODEL_NAME}' exists (regular training)")
            print(f"     Iterations: {int(train_check.iloc[0]['iteration_count'])}")
    except Exception:
        pass

if model_exists:
    print(f"  ⚠️  Model '{MODEL_NAME}' already exists")
    print(f"     ⚠️  Training will REPLACE existing model")
    warnings.append("Existing model will be replaced")
else:
    print(f"  ✅ Model '{MODEL_NAME}' does not exist (will be created)")

if not model_exists:
    try:
        # Double-check with a different method if first check failed
        pass
    except Exception as e:
        print(f"  ⚠️  Could not verify model status: {e}")
        warnings.append(f"Could not verify existing model: {e}")

# 7. Check residual quantiles (for Phase 2)
print("\n7️⃣  RESIDUAL QUANTILES (Phase 2 Prerequisite):")
try:
    query = f"""
    SELECT horizon, q10_residual, q90_residual, n_samples
    FROM `{PROJECT_ID}.{DATASET_ID}.residual_quantiles`
    WHERE horizon = '1w' AND source = 'vertex_ai_extracted'
    """
    quantiles = client.query(query).to_dataframe()
    
    if len(quantiles) > 0:
        q = quantiles.iloc[0]
        print(f"  ✅ Residual quantiles found for 1w:")
        print(f"     q10: {q['q10_residual']:.4f}")
        print(f"     q90: {q['q90_residual']:.4f}")
        print(f"     Samples: {q['n_samples']:,}")
        
        if q['q10_residual'] >= q['q90_residual']:
            print(f"  ❌ Invalid quantiles (q10 >= q90)")
            issues.append("Invalid residual quantiles (q10 >= q90)")
            all_checks_passed = False
    else:
        print(f"  ⚠️  Residual quantiles not found for 1w")
        warnings.append("Residual quantiles missing (needed for Phase 2)")
except Exception as e:
    print(f"  ⚠️  Could not check residual quantiles: {e}")
    warnings.append(f"Residual quantiles check failed: {e}")

# Summary
print("\n" + "="*70)
print("📋 AUDIT SUMMARY")
print("="*70)

if all_checks_passed and len([i for i in issues if '❌' in str(i) or 'Missing' in str(i)]) == 0:
    print("✅ ALL CRITICAL CHECKS PASSED")
    print("✅ Ready to train 1W model")
else:
    print("❌ CRITICAL ISSUES FOUND")
    print("\n🚨 Critical Issues:")
    for issue in issues:
        print(f"   • {issue}")

if warnings:
    print("\n⚠️  Warnings (non-blocking):")
    for warning in warnings:
        print(f"   • {warning}")

print("\n" + "="*70)
print("Next Steps:")
if all_checks_passed:
    print("  ✅ Run: python3 scripts/execute_phase_1.py")
    print("  OR")
    print(f"  ✅ Run SQL directly: bigquery_sql/train_bqml_1w_mean.sql")
else:
    print("  ❌ Fix critical issues above before training")
    print("  📝 Review errors and update training view/SQL as needed")
print("="*70)

sys.exit(0 if all_checks_passed else 1)


