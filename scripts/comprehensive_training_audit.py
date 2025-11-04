#!/usr/bin/env python3
"""
Comprehensive Training Audit for All Horizons (1w, 1m, 3m, 6m)
Identifies all potential issues causing training failures
"""
from google.cloud import bigquery
from datetime import datetime
import sys
import json

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"

HORIZONS = [
    {'name': '1w', 'view': 'train_1w', 'target': 'target_1w', 'model': 'bqml_1w_mean'},
    {'name': '1m', 'view': 'train_1m', 'target': 'target_1m', 'model': 'bqml_1m_mean'},
    {'name': '3m', 'view': 'train_3m', 'target': 'target_3m', 'model': 'bqml_3m_mean'},
    {'name': '6m', 'view': 'train_6m', 'target': 'target_6m', 'model': 'bqml_6m_mean'},
]

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔍 COMPREHENSIVE TRAINING AUDIT - ALL HORIZONS")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Project: {PROJECT_ID}")
print(f"Dataset: {DATASET_ID}")
print("="*80)

all_issues = {}
all_warnings = {}

def check_base_dataset():
    """Check the base training dataset"""
    print("\n" + "="*80)
    print("📊 BASE DATASET CHECK: training_dataset_super_enriched")
    print("="*80)
    
    issues = []
    warnings = []
    
    try:
        # Check if table exists
        query = f"""
        SELECT COUNT(*) as table_exists
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.TABLES`
        WHERE table_name = 'training_dataset_super_enriched'
        """
        result = client.query(query).to_dataframe()
        
        if result.iloc[0]['table_exists'] == 0:
            print("  ❌ Base table 'training_dataset_super_enriched' does not exist")
            issues.append("Base training table missing")
            return issues, warnings
        
        print("  ✅ Base table exists")
        
        # Check row count and basic stats
        query = f"""
        SELECT 
          COUNT(*) as total_rows,
          COUNT(DISTINCT date) as unique_dates,
          MIN(date) as min_date,
          MAX(date) as max_date,
          COUNTIF(target_1w IS NOT NULL) as target_1w_count,
          COUNTIF(target_1m IS NOT NULL) as target_1m_count,
          COUNTIF(target_3m IS NOT NULL) as target_3m_count,
          COUNTIF(target_6m IS NOT NULL) as target_6m_count
        FROM `{PROJECT_ID}.{DATASET_ID}.training_dataset_super_enriched`
        """
        stats = client.query(query).to_dataframe().iloc[0]
        
        print(f"\n  📊 Row Count: {int(stats['total_rows']):,}")
        print(f"  📅 Date Range: {stats['min_date']} to {stats['max_date']}")
        print(f"  📅 Unique Dates: {int(stats['unique_dates']):,}")
        print(f"  ✅ Target 1W: {int(stats['target_1w_count']):,} rows")
        print(f"  ✅ Target 1M: {int(stats['target_1m_count']):,} rows")
        print(f"  ✅ Target 3M: {int(stats['target_3m_count']):,} rows")
        print(f"  ✅ Target 6M: {int(stats['target_6m_count']):,} rows")
        
        if int(stats['total_rows']) < 500:
            issues.append(f"Base table has only {int(stats['total_rows'])} rows (need 500+)")
        
        # Check for NULL values in critical columns
        query = f"""
        SELECT 
          COUNTIF(date IS NULL) as null_dates,
          COUNT(*) as total_rows
        FROM `{PROJECT_ID}.{DATASET_ID}.training_dataset_super_enriched`
        """
        null_check = client.query(query).to_dataframe().iloc[0]
        
        if null_check['null_dates'] > 0:
            issues.append(f"Found {null_check['null_dates']} rows with NULL dates")
        
        # Check column count
        query = f"""
        SELECT COUNT(*) as column_count
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = 'training_dataset_super_enriched'
        """
        col_count = client.query(query).to_dataframe().iloc[0]['column_count']
        print(f"\n  📊 Total Columns: {int(col_count)}")
        
        if int(col_count) < 200:
            warnings.append(f"Column count ({int(col_count)}) lower than expected (200+)")
        
    except Exception as e:
        error_str = str(e)
        print(f"  ❌ Error checking base dataset: {error_str[:300]}")
        issues.append(f"Base dataset check failed: {error_str[:200]}")
    
    return issues, warnings

def check_horizon_view(horizon):
    """Check a specific horizon training view"""
    name = horizon['name']
    view = horizon['view']
    target = horizon['target']
    
    print(f"\n" + "="*80)
    print(f"📊 HORIZON {name.upper()} CHECK: {view}")
    print("="*80)
    
    issues = []
    warnings = []
    
    try:
        # 1. View existence
        query = f"""
        SELECT COUNT(*) as view_exists
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.VIEWS`
        WHERE table_name = '{view}'
        """
        result = client.query(query).to_dataframe()
        
        if result.iloc[0]['view_exists'] == 0:
            print(f"  ❌ View '{view}' does not exist")
            issues.append(f"Training view {view} missing")
            return issues, warnings
        
        print(f"  ✅ View '{view}' exists")
        
        # 2. Column structure
        query = f"""
        SELECT column_name, data_type
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{view}'
        ORDER BY ordinal_position
        """
        columns_df = client.query(query).to_dataframe()
        
        column_names = columns_df['column_name'].values
        
        # Check target exists
        if target not in column_names:
            print(f"  ❌ Target column '{target}' missing")
            issues.append(f"Target column {target} missing")
        else:
            print(f"  ✅ Target column '{target}' present")
        
        # Check for label leakage (other targets)
        other_targets = ['target_1w', 'target_1m', 'target_3m', 'target_6m']
        other_targets.remove(target)
        leakage_cols = [col for col in other_targets if col in column_names]
        
        if leakage_cols:
            print(f"  ❌ LABEL LEAKAGE: {', '.join(leakage_cols)} present")
            issues.append(f"Label leakage: {leakage_cols}")
        else:
            print(f"  ✅ No label leakage (other targets excluded)")
        
        # Check date column
        if 'date' not in column_names:
            print(f"  ❌ Date column missing (required for data_split)")
            issues.append("Date column missing")
        else:
            print(f"  ✅ Date column present")
        
        # Check for temporal leakage features in VIEW (they should be excluded in SQL)
        temporal_leakage = [
            'crude_lead1_correlation',
            'dxy_lead1_correlation',
            'vix_lead1_correlation',
            'palm_lead2_correlation',
            'leadlag_zl_price',
            'lead_signal_confidence',
            'days_to_next_event',
            'post_event_window',
            'event_impact_level',
            'event_vol_mult',
            'tradewar_event_vol_mult'
        ]
        found_leakage = [f for f in temporal_leakage if f in column_names]
        if found_leakage:
            print(f"  ⚠️  Temporal leakage features in VIEW (should be excluded in SQL): {len(found_leakage)}")
            print(f"      Will verify SQL excludes them in SQL check below")
        else:
            print(f"  ✅ No temporal leakage features in view")
        
        # Count features
        exclusion_cols = {
            'date', target, 'target_1w', 'target_1m', 'target_3m', 'target_6m',
            'treasury_10y_yield', 'econ_gdp_growth', 'econ_unemployment_rate',
            'news_article_count', 'news_avg_score'
        }
        exclusion_cols.update(temporal_leakage)
        
        feature_cols = [col for col in column_names if col not in exclusion_cols]
        feature_count = len(feature_cols)
        
        print(f"\n  📊 Total Columns: {len(columns_df)}")
        print(f"  📊 Feature Columns: {feature_count}")
        
        if feature_count < 190:
            warnings.append(f"Low feature count: {feature_count}")
        elif feature_count > 220:
            warnings.append(f"High feature count: {feature_count}")
        
        # 3. Data quality check
        print(f"\n  📈 DATA QUALITY:")
        query = f"""
        SELECT 
          COUNT(*) as total_rows,
          COUNTIF({target} IS NOT NULL) as valid_targets,
          COUNTIF({target} IS NULL) as null_targets,
          MIN({target}) as min_target,
          MAX({target}) as max_target,
          AVG({target}) as avg_target,
          STDDEV({target}) as stddev_target,
          COUNTIF(date < '2024-12-01') as train_rows,
          COUNTIF(date >= '2024-12-01' AND date < '2025-01-01') as eval_rows,
          COUNTIF(date IS NULL) as null_dates
        FROM `{PROJECT_ID}.{DATASET_ID}.{view}`
        """
        stats = client.query(query).to_dataframe().iloc[0]
        
        total_rows = int(stats['total_rows'])
        valid_targets = int(stats['valid_targets'])
        train_rows = int(stats['train_rows'])
        eval_rows = int(stats['eval_rows'])
        null_dates = int(stats['null_dates'])
        
        print(f"    Total Rows: {total_rows:,}")
        print(f"    Valid Targets: {valid_targets:,}")
        print(f"    NULL Targets: {int(stats['null_targets']):,}")
        print(f"    Training Rows (< 2024-12-01): {train_rows:,}")
        print(f"    Eval Rows (2024-12-01 to 2024-12-31): {eval_rows:,}")
        print(f"    NULL Dates: {null_dates:,}")
        
        if total_rows == 0:
            issues.append("View has zero rows")
        elif valid_targets < 500:
            issues.append(f"Insufficient valid targets: {valid_targets} (<500 required)")
        elif valid_targets < 1000:
            warnings.append(f"Low target count: {valid_targets} (<1000 recommended)")
        
        if train_rows < 400:
            issues.append(f"Insufficient training rows: {train_rows} (<400 required)")
        
        if eval_rows < 20:
            warnings.append(f"Low eval rows: {eval_rows} (<20 recommended)")
        
        if null_dates > 0:
            issues.append(f"Found {null_dates} rows with NULL dates (breaks data_split)")
        
        # Check for invalid target values
        if stats['min_target'] is not None:
            if float(stats['min_target']) <= 0:
                warnings.append(f"Target has non-positive values (min: {stats['min_target']})")
        
        # Check data_split column creation
        print(f"\n  🔀 DATA_SPLIT CHECK:")
        query = f"""
        SELECT 
          COUNTIF(date < '2024-12-01') as should_be_train,
          COUNTIF(date >= '2024-12-01') as should_be_eval
        FROM `{PROJECT_ID}.{DATASET_ID}.{view}`
        WHERE {target} IS NOT NULL
        """
        split_check = client.query(query).to_dataframe().iloc[0]
        print(f"    Rows that should be TRAIN: {int(split_check['should_be_train']):,}")
        print(f"    Rows that should be EVAL: {int(split_check['should_be_eval']):,}")
        
        if int(split_check['should_be_train']) == 0:
            issues.append("No training rows found (all dates >= 2024-12-01)")
        if int(split_check['should_be_eval']) == 0:
            warnings.append("No eval rows found (all dates < 2024-12-01)")
        
        # 4. Check for problematic column types
        print(f"\n  🔍 COLUMN TYPE CHECK:")
        query = f"""
        SELECT 
          column_name,
          data_type
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{view}'
        AND data_type IN ('ARRAY', 'STRUCT', 'RECORD', 'BYTES')
        """
        problematic_types = client.query(query).to_dataframe()
        
        if len(problematic_types) > 0:
            print(f"    ⚠️  Found {len(problematic_types)} columns with unsupported types:")
            for _, row in problematic_types.iterrows():
                print(f"       - {row['column_name']}: {row['data_type']}")
            warnings.append(f"Unsupported column types: {problematic_types['column_name'].tolist()}")
        else:
            print(f"    ✅ No unsupported column types")
        
        # 5. Check for duplicate column names (case-insensitive)
        print(f"\n  🔍 DUPLICATE COLUMN CHECK:")
        query = f"""
        SELECT 
          LOWER(column_name) as col_lower,
          COUNT(*) as count
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{view}'
        GROUP BY LOWER(column_name)
        HAVING COUNT(*) > 1
        """
        duplicates = client.query(query).to_dataframe()
        
        if len(duplicates) > 0:
            print(f"    ❌ Found duplicate column names (case-insensitive):")
            for _, row in duplicates.iterrows():
                print(f"       - {row['col_lower']} appears {int(row['count'])} times")
            issues.append("Duplicate column names found (case-insensitive)")
        else:
            print(f"    ✅ No duplicate column names")
        
        # 6. Check reserved keyword usage
        print(f"\n  🔍 RESERVED KEYWORD CHECK:")
        reserved_keywords = ['rows', 'table', 'select', 'from', 'where', 'group', 'order', 'limit', 'join', 'on', 'as']
        reserved_cols = [col for col in column_names if col.lower() in reserved_keywords]
        
        if reserved_cols:
            print(f"    ⚠️  Found columns matching reserved keywords:")
            for col in reserved_cols:
                print(f"       - {col}")
            warnings.append(f"Columns matching reserved keywords: {reserved_cols}")
        else:
            print(f"    ✅ No reserved keyword conflicts")
        
    except Exception as e:
        error_str = str(e)
        print(f"  ❌ Error checking view: {error_str[:300]}")
        issues.append(f"View check failed: {error_str[:200]}")
    
    return issues, warnings

def check_training_sql(horizon):
    """Check the training SQL file for issues"""
    name = horizon['name']
    view = horizon['view']
    target = horizon['target']
    model = horizon['model']
    
    print(f"\n" + "="*80)
    print(f"📄 TRAINING SQL CHECK: train_bqml_{name}_mean.sql")
    print("="*80)
    
    issues = []
    warnings = []
    
    try:
        import pathlib
        sql_file = pathlib.Path(__file__).parent.parent / "bigquery_sql" / f"train_bqml_{name}_mean.sql"
        
        if not sql_file.exists():
            print(f"  ❌ SQL file not found: {sql_file}")
            issues.append(f"SQL file missing: train_bqml_{name}_mean.sql")
            return issues, warnings
        
        print(f"  ✅ SQL file exists")
        
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Check critical configurations
        checks = {
            'DROP MODEL IF EXISTS': 'DROP MODEL IF EXISTS' in sql_content,
            'CREATE MODEL': f'CREATE MODEL' in sql_content and model in sql_content,
            'BOOSTED_TREE_REGRESSOR': 'BOOSTED_TREE_REGRESSOR' in sql_content,
            'input_label_cols': f"input_label_cols=['{target}']" in sql_content,
            'data_split_method CUSTOM': 'data_split_method' in sql_content and "'CUSTOM'" in sql_content,
            'data_split_col': 'data_split_col' in sql_content,
            'IF(date <': "IF(date < '2024-12-01'" in sql_content,
            'FROM view': f"FROM `{PROJECT_ID}.{DATASET_ID}.{view}`" in sql_content,
            'WHERE target IS NOT NULL': f"WHERE {target} IS NOT NULL" in sql_content,
        }
        
        print(f"\n  🔍 Configuration Checks:")
        for check_name, passed in checks.items():
            if passed:
                print(f"    ✅ {check_name}")
            else:
                print(f"    ❌ {check_name}: MISSING or INCORRECT")
                issues.append(f"SQL missing/incorrect: {check_name}")
        
        # Check for temporal leakage exclusions (must include all 11)
        temporal_leakage = [
            'crude_lead1_correlation',
            'dxy_lead1_correlation',
            'vix_lead1_correlation',
            'palm_lead2_correlation',
            'leadlag_zl_price',
            'lead_signal_confidence',
            'days_to_next_event',
            'post_event_window',
            'event_impact_level',
            'event_vol_mult',
            'tradewar_event_vol_mult'
        ]
        
        excluded_count = sum(1 for leak in temporal_leakage if leak in sql_content)
        print(f"\n  🔒 Temporal Leakage Exclusions: {excluded_count}/{len(temporal_leakage)}")
        
        if excluded_count < len(temporal_leakage):
            missing = [leak for leak in temporal_leakage if leak not in sql_content]
            print(f"    ❌ Missing exclusions: {', '.join(missing)}")
            issues.append(f"Temporal leakage features not excluded in SQL: {missing}")
        else:
            print(f"    ✅ All {len(temporal_leakage)} temporal leakage features excluded")
        
        # Check data_split uses correct string values
        if "'TRAIN'" not in sql_content and '"TRAIN"' not in sql_content:
            if "IF(date < '2024-12-01', 'TRAIN', 'EVAL')" in sql_content:
                print(f"    ✅ data_split uses correct TRAIN/EVAL string format")
            else:
                issues.append("data_split may not use correct TRAIN/EVAL string format")
        
    except Exception as e:
        error_str = str(e)
        print(f"  ❌ Error checking SQL file: {error_str[:300]}")
        issues.append(f"SQL file check failed: {error_str[:200]}")
    
    return issues, warnings

def main():
    """Run comprehensive audit"""
    print("\n🔍 Starting comprehensive training audit...\n")
    
    # Check base dataset
    base_issues, base_warnings = check_base_dataset()
    
    all_issues['base_dataset'] = base_issues
    all_warnings['base_dataset'] = base_warnings
    
    # Check each horizon
    for horizon in HORIZONS:
        view_issues, view_warnings = check_horizon_view(horizon)
        sql_issues, sql_warnings = check_training_sql(horizon)
        
        all_issues[horizon['name']] = view_issues + sql_issues
        all_warnings[horizon['name']] = view_warnings + sql_warnings
    
    # Summary
    print("\n" + "="*80)
    print("📋 COMPREHENSIVE AUDIT SUMMARY")
    print("="*80)
    
    total_issues = sum(len(issues) for issues in all_issues.values())
    total_warnings = sum(len(warnings) for warnings in all_warnings.values())
    
    print(f"\n❌ Total Critical Issues: {total_issues}")
    print(f"⚠️  Total Warnings: {total_warnings}")
    
    if total_issues == 0:
        print("\n✅ NO CRITICAL ISSUES FOUND")
        print("✅ All training configurations appear correct")
    else:
        print("\n🚨 CRITICAL ISSUES BY AREA:")
        for area, issues in all_issues.items():
            if issues:
                print(f"\n  {area.upper()}:")
                for issue in issues:
                    print(f"    ❌ {issue}")
    
    if total_warnings > 0:
        print("\n⚠️  WARNINGS BY AREA:")
        for area, warnings in all_warnings.items():
            if warnings:
                print(f"\n  {area.upper()}:")
                for warning in warnings:
                    print(f"    ⚠️  {warning}")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    if total_issues == 0:
        print("  ✅ All checks passed - ready to train")
        print("  Run: python3 scripts/execute_phase_1.py")
    else:
        print("  ❌ Fix critical issues above before training")
        print("  📝 Review each issue and update configuration as needed")
    print("="*80)
    
    sys.exit(0 if total_issues == 0 else 1)

if __name__ == "__main__":
    main()

