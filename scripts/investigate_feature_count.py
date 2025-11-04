#!/usr/bin/env python3
"""
Investigate why bqml_1w_mean only has 57 features instead of expected ~194
"""
from google.cloud import bigquery
import pandas as pd

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
MODEL_NAME = "bqml_1w_mean"
VIEW_NAME = "train_1w"

client = bigquery.Client(project=PROJECT_ID)

print("="*70)
print("🔍 INVESTIGATING FEATURE COUNT DISCREPANCY")
print("="*70)
print(f"Model: {MODEL_NAME}")
print(f"Training View: {VIEW_NAME}")
print("="*70)

# 1. Get all features in the trained model
print("\n1️⃣  FEATURES IN TRAINED MODEL:")
try:
    query = f"""
    SELECT *
    FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
    ORDER BY ABS(attribution) DESC
    """
    model_features_df = client.query(query).to_dataframe()
    
    if not model_features_df.empty:
        print(f"  📊 Total features in model: {len(model_features_df)}")
        
        # Check column names
        print(f"  📋 Available columns: {', '.join(model_features_df.columns.tolist())}")
        
        # Get feature names (try different possible column names)
        feature_col = None
        for col in ['feature', 'feature_name', 'feature_path']:
            if col in model_features_df.columns:
                feature_col = col
                break
        
        if feature_col:
            model_features = set(model_features_df[feature_col].tolist())
            print(f"\n  ✅ Using column: {feature_col}")
            print(f"  📝 All {len(model_features)} features in model:")
            
            # Show first 20
            for idx, feat in enumerate(sorted(model_features)[:20], 1):
                print(f"     {idx}. {feat}")
            if len(model_features) > 20:
                print(f"     ... and {len(model_features) - 20} more")
            
            # Save full list
            model_features_full = sorted(model_features)
        else:
            print(f"  ❌ Could not identify feature column")
            model_features_full = []
    else:
        print(f"  ❌ No features found in model")
        model_features_full = []
except Exception as e:
    print(f"  ❌ Error getting model features: {e}")
    model_features_full = []

# 2. Get all columns in the training view
print("\n2️⃣  COLUMNS IN TRAINING VIEW:")
try:
    query = f"""
    SELECT column_name, data_type
    FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{VIEW_NAME}'
    ORDER BY ordinal_position
    """
    view_columns_df = client.query(query).to_dataframe()
    
    if not view_columns_df.empty:
        all_view_columns = set(view_columns_df['column_name'].tolist())
        print(f"  📊 Total columns in view: {len(all_view_columns)}")
        
        # Expected exclusions
        expected_exclusions = {
            'date',
            'target_1w',  # Target column
            'target_1m', 'target_3m', 'target_6m',  # Other targets (should be excluded)
            'treasury_10y_yield', 
            'econ_gdp_growth', 
            'econ_unemployment_rate', 
            'news_article_count', 
            'news_avg_score',
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
        }
        
        # Calculate expected feature count
        feature_columns = all_view_columns - expected_exclusions
        expected_count = len(feature_columns)
        
        print(f"  📊 Expected feature count: {expected_count}")
        print(f"     (Total columns: {len(all_view_columns)}, Exclusions: {len(expected_exclusions)})")
        
        print(f"\n  📋 Excluded columns:")
        excluded_found = [col for col in expected_exclusions if col in all_view_columns]
        for col in sorted(excluded_found):
            print(f"     - {col}")
        
        excluded_missing = [col for col in expected_exclusions if col not in all_view_columns]
        if excluded_missing:
            print(f"\n  ⚠️  Expected exclusions NOT in view:")
            for col in sorted(excluded_missing):
                print(f"     - {col}")
        
        # Check what's missing
        if model_features_full:
            model_features_set = set(model_features_full) if isinstance(model_features_full, list) else model_features_full
            feature_columns_set = feature_columns if isinstance(feature_columns, set) else set(feature_columns)
            missing_from_model = feature_columns_set - model_features_set
            extra_in_model = model_features_set - feature_columns_set
            
            print(f"\n  🔍 COMPARISON:")
            print(f"     Expected features: {expected_count}")
            print(f"     Features in model: {len(model_features_full)}")
            print(f"     Missing from model: {len(missing_from_model)}")
            print(f"     Extra in model: {len(extra_in_model)}")
            
            if missing_from_model:
                print(f"\n  ❌ MISSING FEATURES (should be in model but aren't):")
                for idx, feat in enumerate(sorted(missing_from_model)[:30], 1):
                    print(f"     {idx}. {feat}")
                if len(missing_from_model) > 30:
                    print(f"     ... and {len(missing_from_model) - 30} more")
            
            if extra_in_model:
                print(f"\n  ⚠️  EXTRA FEATURES (in model but not in view):")
                for idx, feat in enumerate(sorted(extra_in_model)[:10], 1):
                    print(f"     {idx}. {feat}")
                if len(extra_in_model) > 10:
                    print(f"     ... and {len(extra_in_model) - 10} more")
        else:
            print(f"\n  ⚠️  Cannot compare - model features not available")
            
    else:
        print(f"  ❌ Could not get view columns")
        all_view_columns = set()
except Exception as e:
    print(f"  ❌ Error getting view columns: {e}")
    all_view_columns = set()

# 3. Check training SQL to see what it actually excludes
print("\n3️⃣  TRAINING SQL EXCLUSIONS:")
try:
    import pathlib
    sql_file = pathlib.Path(__file__).parent.parent / "bigquery_sql" / "train_bqml_1w_mean.sql"
    if sql_file.exists():
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        print(f"  📄 SQL file: {sql_file}")
        
        # Check for EXCEPT clause
        if 'EXCEPT' in sql_content:
            print(f"  ✅ EXCEPT clause found")
            
            # Try to extract excluded columns from SQL
            # This is approximate - we'll look for the EXCEPT list
            lines = sql_content.split('\n')
            in_except = False
            excluded_in_sql = []
            
            for line in lines:
                if '* EXCEPT(' in line or 'EXCEPT(' in line:
                    in_except = True
                if in_except:
                    # Extract column names from comments or list
                    if '--' in line:
                        excluded_in_sql.append(line.split('--')[0].strip().rstrip(','))
                    elif line.strip().startswith("'") or line.strip().startswith('`'):
                        excluded_in_sql.append(line.strip().rstrip(','))
                if in_except and line.strip().endswith(')'):
                    break
            
            print(f"  📝 Exclusions found in SQL (approximate): {len(excluded_in_sql)}")
        else:
            print(f"  ⚠️  No EXCEPT clause found")
    else:
        print(f"  ❌ SQL file not found")
except Exception as e:
    print(f"  ⚠️  Error reading SQL file: {e}")

# 4. Check if model was trained with different data
print("\n4️⃣  CHECKING MODEL TRAINING DATA:")
try:
    # Check training info for clues
    query = f"""
    SELECT 
      COUNT(DISTINCT feature) as unique_features,
      COUNT(*) as total_rows
    FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
    """
    train_info = client.query(query).to_dataframe()
    if not train_info.empty:
        print(f"  📊 Training info available")
except Exception as e:
    print(f"  ⚠️  Could not check training info: {e}")

# 5. Summary
print("\n" + "="*70)
print("📋 SUMMARY")
print("="*70)

if model_features_full and 'feature_columns' in locals() and feature_columns:
    model_features_set = set(model_features_full) if isinstance(model_features_full, list) else model_features_full
    feature_columns_set = feature_columns if isinstance(feature_columns, set) else set(feature_columns)
    
    print(f"\nExpected Features: ~{len(feature_columns_set)}")
    print(f"Actual Features in Model: {len(model_features_set)}")
    print(f"Missing: {len(feature_columns_set - model_features_set)} features")
    print(f"Discrepancy: {len(model_features_set) - len(feature_columns_set)}")
    
    print(f"\nPossible Reasons:")
    print(f"  1. Model was trained with fewer features (feature selection)")
    print(f"  2. Many features had constant/zero variance and were dropped")
    print(f"  3. Model was trained on different dataset/view")
    print(f"  4. BQML auto-excluded low-importance features")
    print(f"  5. Some features are NULL/missing in all training rows")

print("="*70)

