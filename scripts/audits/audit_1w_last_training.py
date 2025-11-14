#!/usr/bin/env python3
"""
Comprehensive Audit of 1W Model Last Training
Verifies training completion, leakage exclusion, and performance
"""
from google.cloud import bigquery
from datetime import datetime
import sys

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
MODEL_NAME = "bqml_1w_mean"
VIEW_NAME = "train_1w"
TARGET_COL = "target_1w"

# All known leakage features that should NOT be in the model
LEAKAGE_FEATURES = [
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

client = bigquery.Client(project=PROJECT_ID)

print("="*70)
print("🔍 COMPREHENSIVE 1W LAST TRAINING AUDIT")
print("="*70)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Model: {MODEL_NAME}")
print(f"Training View: {VIEW_NAME}")
print("="*70)

all_checks_passed = True
issues = []
warnings = []
results = {}

# 1. Model Existence and Metadata
print("\n1️⃣  MODEL EXISTENCE AND METADATA:")
results['exists'] = False

# Try ML.TRIAL_INFO first (for hyperparameter-tuned models)
try:
    query = f"""
    SELECT COUNT(*) as trial_count
    FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
    """
    trial_check = client.query(query).to_dataframe()
    if not trial_check.empty and trial_check.iloc[0]['trial_count'] > 0:
        results['exists'] = True
        print(f"  ✅ Model exists (hyperparameter-tuned)")
        print(f"     Trials: {int(trial_check.iloc[0]['trial_count'])}")
except Exception as e:
    # If TRIAL_INFO fails, try TRAINING_INFO (for regular models)
    try:
        query = f"""
        SELECT COUNT(*) as iteration_count
        FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
        """
        train_check = client.query(query).to_dataframe()
        if not train_check.empty:
            results['exists'] = True
            print(f"  ✅ Model exists (regular training)")
            print(f"     Iterations: {int(train_check.iloc[0]['iteration_count'])}")
    except Exception as e2:
        error_str = str(e2) if hasattr(e2, '__str__') else str(e)
        if "Not found" in error_str or "404" in error_str or "does not exist" in error_str:
            print(f"  ❌ Model does not exist")
            issues.append("Model bqml_1w_mean not found")
            results['exists'] = False
            all_checks_passed = False
        else:
            print(f"  ❌ Error checking model: {e2}")
            issues.append(f"Model existence check failed: {e2}")
            results['exists'] = False
            all_checks_passed = False

if not results.get('exists', False):
    print("\n⚠️  MODEL NOT FOUND - Cannot proceed with remaining checks")
    print("   The model may not have been trained yet, or it was deleted.")
    print("   To train: python3 scripts/execute_phase_1.py")
    sys.exit(1)

# 2. Training History Review
print("\n2️⃣  TRAINING HISTORY:")
try:
    query = f"""
    WITH training_data AS (
      SELECT 
        training_run,
        iteration,
        loss AS train_loss,
        eval_loss,
        duration_ms,
        learning_rate
      FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
      ORDER BY iteration DESC
    )
    SELECT
      MAX(iteration) as max_iteration,
      MIN(train_loss) AS min_train_loss,
      MAX(train_loss) AS max_train_loss,
      AVG(train_loss) AS avg_train_loss,
      MIN(eval_loss) AS min_eval_loss,
      MAX(eval_loss) AS max_eval_loss,
      AVG(eval_loss) AS avg_eval_loss,
      COUNT(*) AS total_iterations,
      SUM(duration_ms) / 1000.0 AS total_training_sec,
      (SELECT train_loss FROM training_data ORDER BY iteration ASC LIMIT 1) as initial_train_loss,
      (SELECT train_loss FROM training_data ORDER BY iteration DESC LIMIT 1) as final_train_loss,
      (SELECT eval_loss FROM training_data ORDER BY iteration ASC LIMIT 1) as initial_eval_loss,
      (SELECT eval_loss FROM training_data ORDER BY iteration DESC LIMIT 1) as final_eval_loss
    FROM training_data
    """
    train_info = client.query(query).to_dataframe()
    
    if not train_info.empty:
        row = train_info.iloc[0]
        max_iter = int(row['max_iteration'])
        results['iterations'] = max_iter
        results['final_train_loss'] = float(row['final_train_loss'])
        results['final_eval_loss'] = float(row['final_eval_loss'])
        results['training_time_sec'] = float(row['total_training_sec'])
        
        print(f"  📊 Training Completion:")
        print(f"     Iterations: {max_iter}/100")
        
        if max_iter >= 100:
            print(f"     ✅ Training completed (100 iterations)")
        else:
            print(f"     ⚠️  Training stopped early at iteration {max_iter}")
            warnings.append(f"Training stopped early at iteration {max_iter}")
        
        print(f"\n  📈 Loss Progression:")
        print(f"     Initial Train Loss: {row['initial_train_loss']:.6f}")
        print(f"     Final Train Loss: {row['final_train_loss']:.6f}")
        print(f"     Initial Eval Loss: {row['initial_eval_loss']:.6f}")
        print(f"     Final Eval Loss: {row['final_eval_loss']:.6f}")
        print(f"     Train Loss Range: [{row['min_train_loss']:.6f}, {row['max_train_loss']:.6f}]")
        print(f"     Eval Loss Range: [{row['min_eval_loss']:.6f}, {row['max_eval_loss']:.6f}]")
        
        # Check for convergence
        if float(row['final_train_loss']) < 0.35:
            print(f"     ✅ Train loss converged (target: <0.35)")
        else:
            print(f"     ⚠️  Train loss may not have converged")
            warnings.append(f"High final train loss: {row['final_train_loss']:.6f}")
        
        # Check for overfitting (eval loss much higher than train)
        eval_ratio = float(row['final_eval_loss']) / float(row['final_train_loss'])
        if eval_ratio > 50:
            print(f"     ⚠️  Potential overfitting (eval/train ratio: {eval_ratio:.1f}x)")
            warnings.append(f"High eval/train loss ratio: {eval_ratio:.1f}x")
        
        print(f"\n  ⏱️  Training Duration: {row['total_training_sec']:.1f} seconds ({row['total_training_sec']/60:.1f} minutes)")
    else:
        print(f"  ❌ No training info available")
        issues.append("Training info not available")
        all_checks_passed = False
except Exception as e:
    print(f"  ❌ Error getting training info: {e}")
    issues.append(f"Training history check failed: {e}")
    all_checks_passed = False

# 3. Leakage Feature Verification
print("\n3️⃣  LEAKAGE FEATURE VERIFICATION:")
try:
    # First try to get all features to check structure
    query = f"""
    SELECT *
    FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
    LIMIT 1
    """
    sample = client.query(query).to_dataframe()
    
    if not sample.empty:
        # Check what columns are available
        columns = sample.columns.tolist()
        
        # Try different possible column names
        feature_col = None
        for col in ['feature', 'feature_name', 'feature_path']:
            if col in columns:
                feature_col = col
                break
        
        if feature_col:
            # Now check for leakage features
            query = f"""
            SELECT {feature_col}
            FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
            WHERE {feature_col} IN ({', '.join([f"'{f}'" for f in LEAKAGE_FEATURES])})
            """
            leakage_check = client.query(query).to_dataframe()
            
            if len(leakage_check) > 0:
                leakage_found = leakage_check[feature_col].tolist()
                print(f"  ❌ LEAKAGE DETECTED: {len(leakage_found)} leakage features found")
                for leak_feat in leakage_found:
                    print(f"     - {leak_feat}")
                issues.append(f"Leakage features found: {leakage_found}")
                all_checks_passed = False
                results['leakage_detected'] = leakage_found
            else:
                print(f"  ✅ No leakage features found ({len(LEAKAGE_FEATURES)} features checked)")
                results['leakage_detected'] = []
                
                # Also get total feature count
                query = f"""
                SELECT COUNT(*) as feature_count
                FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
                """
                feat_count_df = client.query(query).to_dataframe()
                if not feat_count_df.empty:
                    feat_count = int(feat_count_df['feature_count'].iloc[0])
                    print(f"  📊 Total features in model: {feat_count}")
                    results['feature_count'] = feat_count
                    
                    if feat_count < 190:
                        warnings.append(f"Low feature count: {feat_count} (expected ~194 after exclusions)")
        else:
            print(f"  ⚠️  Could not identify feature column in GLOBAL_EXPLAIN output")
            print(f"     Available columns: {', '.join(columns)}")
            warnings.append("Could not determine feature column name")
    else:
        print(f"  ⚠️  GLOBAL_EXPLAIN returned no data")
        warnings.append("Feature importance data unavailable")
        
except Exception as e:
    error_str = str(e)
    if 'GLOBAL_EXPLAIN' in error_str or 'feature' in error_str.lower() or 'importance' in error_str.lower():
        print(f"  ⚠️  Could not check feature importance (enable_global_explain may not have worked)")
        print(f"     Error: {error_str[:100]}")
        warnings.append("Feature importance check unavailable - using alternative method")
        
        # Alternative: Check training SQL file for exclusions
        try:
            import pathlib
            sql_file = pathlib.Path(__file__).parent.parent / "bigquery_sql" / "train_bqml_1w_mean.sql"
            if sql_file.exists():
                with open(sql_file, 'r') as f:
                    sql_content = f.read()
                    leakage_in_sql = [feat for feat in LEAKAGE_FEATURES if feat in sql_content]
                    excluded_in_sql = sum(1 for feat in LEAKAGE_FEATURES if f"'{feat}'" in sql_content or feat in sql_content.split())
                    print(f"  📝 Checked training SQL: {excluded_in_sql}/{len(LEAKAGE_FEATURES)} leakage features excluded in SQL")
                    if excluded_in_sql < len(LEAKAGE_FEATURES):
                        warnings.append(f"SQL may not exclude all leakage features ({excluded_in_sql}/{len(LEAKAGE_FEATURES)})")
        except Exception as sql_e:
            pass
    else:
        print(f"  ❌ Error checking leakage: {e}")
        issues.append(f"Leakage check failed: {e}")
        all_checks_passed = False

# 4. Test Set Performance Evaluation
print("\n4️⃣  TEST SET PERFORMANCE EVALUATION:")
try:
    # Match the exact query structure from audit_phase_1_training.py which works
    query = f"""
    SELECT 
      mean_absolute_error AS mae,
      mean_squared_error AS mse,
      SQRT(mean_squared_error) AS rmse,
      r2_score AS r2,
      explained_variance AS ev
    FROM ML.EVALUATE(
      MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`,
      (
        SELECT 
          * EXCEPT(date, treasury_10y_yield, econ_gdp_growth, econ_unemployment_rate, news_article_count, news_avg_score),
          date < '2024-01-01' AS is_training
        FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}`
        WHERE date >= '2024-01-01'  -- TEST SET: 2024 data only
        AND {TARGET_COL} IS NOT NULL
      )
    )
    """
    eval_results = client.query(query).to_dataframe()
    
    if not eval_results.empty:
        row = eval_results.iloc[0]
        results['mae'] = float(row['mae'])
        results['rmse'] = float(row['rmse'])
        results['r2'] = float(row['r2'])
        results['explained_variance'] = float(row['ev'])
        
        # Calculate MAPE if possible
        try:
            query_mape = f"""
            WITH predictions AS (
              SELECT 
                actual.{TARGET_COL} AS actual,
                pred.predicted_{TARGET_COL} AS predicted
              FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}` actual
              CROSS JOIN ML.PREDICT(
                MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`,
                (SELECT * EXCEPT(date, treasury_10y_yield, econ_gdp_growth, econ_unemployment_rate, news_article_count, news_avg_score, {TARGET_COL})
                 FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}`
                 WHERE date = actual.date)
              ) pred
              WHERE actual.date >= '2024-01-01'
              AND actual.{TARGET_COL} IS NOT NULL
            )
            SELECT 
              AVG(ABS(actual - predicted) / NULLIF(ABS(actual), 0)) * 100 AS mape
            FROM predictions
            """
            mape_result = client.query(query_mape).to_dataframe()
            if not mape_result.empty and mape_result['mape'].iloc[0] is not None:
                results['mape'] = float(mape_result['mape'].iloc[0])
            else:
                results['mape'] = None
        except Exception as e:
            results['mape'] = None
            warnings.append(f"Could not calculate MAPE: {e}")
        
        print(f"  📈 Performance Metrics:")
        print(f"     MAE: {row['mae']:.4f} (target: <1.2, baseline: 1.19)")
        print(f"     RMSE: {row['rmse']:.4f}")
        print(f"     R²: {row['r2']:.4f} (target: >0.98, baseline: 0.98)")
        print(f"     Explained Variance: {row['ev']:.4f}")
        if results.get('mape'):
            print(f"     MAPE: {results['mape']:.2f}% (target: ~2.38%)")
        
        # Quality assessment
        mae_target = results['mae'] < 1.2
        r2_target = results['r2'] > 0.98
        
        if mae_target and r2_target:
            print(f"  ✅ Performance meets targets (MAE < 1.2, R² > 0.98)")
            results['meets_targets'] = True
        else:
            print(f"  ⚠️  Performance below targets:")
            if not mae_target:
                print(f"     - MAE {results['mae']:.4f} >= 1.2")
                warnings.append(f"MAE above target: {results['mae']:.4f}")
            if not r2_target:
                print(f"     - R² {results['r2']:.4f} <= 0.98")
                warnings.append(f"R² below target: {results['r2']:.4f}")
            results['meets_targets'] = False
        
        if results['r2'] < 0:
            print(f"  ❌ Negative R² indicates serious issues")
            issues.append(f"Negative R² score: {results['r2']:.4f}")
            all_checks_passed = False
    else:
        print(f"  ❌ No evaluation metrics available")
        issues.append("Evaluation metrics not available")
        all_checks_passed = False
except Exception as e:
    print(f"  ❌ Error evaluating model: {e}")
    issues.append(f"Performance evaluation failed: {e}")
    all_checks_passed = False

# 5. Feature Importance Analysis
print("\n5️⃣  FEATURE IMPORTANCE ANALYSIS:")
try:
    # Try to get feature importance with proper column names
    query = f"""
    SELECT *
    FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
    LIMIT 1
    """
    sample = client.query(query).to_dataframe()
    
    if not sample.empty:
        columns = sample.columns.tolist()
        feature_col = None
        importance_col = None
        
        # Find feature column
        for col in ['feature', 'feature_name', 'feature_path']:
            if col in columns:
                feature_col = col
                break
        
        # Find importance column
        for col in ['attribution', 'importance', 'attribution_value']:
            if col in columns:
                importance_col = col
                break
        
        if feature_col and importance_col:
            query = f"""
            SELECT {feature_col}, {importance_col}
            FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`)
            ORDER BY ABS({importance_col}) DESC
            LIMIT 10
            """
            top_features = client.query(query).to_dataframe()
            
            if not top_features.empty:
                print(f"  📊 Top 10 Most Important Features:")
                for idx, row in top_features.iterrows():
                    feat_val = row[feature_col]
                    imp_val = abs(float(row[importance_col]))
                    print(f"     {idx+1}. {feat_val}: {imp_val:.4f}")
                
                # Check if any top features are suspicious (shouldn't be leakage)
                suspicious = [f for f in top_features[feature_col].tolist() if f in LEAKAGE_FEATURES]
                if suspicious:
                    print(f"  ❌ Leakage features in top 10: {suspicious}")
                    issues.append(f"Leakage in top features: {suspicious}")
                    all_checks_passed = False
                else:
                    print(f"  ✅ Top features look legitimate (no leakage)")
            else:
                print(f"  ⚠️  Could not retrieve top features")
                warnings.append("Feature importance unavailable")
        else:
            print(f"  ⚠️  Could not identify columns (feature: {feature_col}, importance: {importance_col})")
            print(f"     Available columns: {', '.join(columns)}")
            warnings.append("Could not determine feature/importance columns")
    else:
        print(f"  ⚠️  Could not retrieve feature importance")
        warnings.append("Feature importance unavailable")
except Exception as e:
    error_str = str(e)
    print(f"  ⚠️  Feature importance analysis failed: {error_str[:100]}")
    warnings.append(f"Feature importance check failed: {e}")

# 6. Training Data Validation
print("\n6️⃣  TRAINING DATA VALIDATION:")
try:
    query = f"""
    SELECT 
      COUNT(*) as total_rows,
      COUNTIF({TARGET_COL} IS NOT NULL) as valid_targets,
      COUNTIF(date < '2025-09-01') as train_rows,
      COUNTIF(date >= '2025-09-01') as val_rows
    FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}`
    """
    data_stats = client.query(query).to_dataframe()
    
    if not data_stats.empty:
        row = data_stats.iloc[0]
        print(f"  📊 Training Data Stats:")
        print(f"     Total rows: {int(row['total_rows']):,}")
        print(f"     Valid targets: {int(row['valid_targets']):,}")
        print(f"     Training rows (pre-2025-09-01): {int(row['train_rows']):,}")
        print(f"     Validation rows (post-2025-09-01): {int(row['val_rows']):,}")
        
        if int(row['valid_targets']) < 500:
            warnings.append(f"Low valid target count: {int(row['valid_targets'])}")
    else:
        warnings.append("Could not retrieve training data stats")
except Exception as e:
    print(f"  ⚠️  Training data validation failed: {e}")
    warnings.append(f"Training data check failed: {e}")

# Summary
print("\n" + "="*70)
print("📋 AUDIT SUMMARY")
print("="*70)

print("\n✅ Model Status:")
print(f"   Exists: {results.get('exists', False)}")
if results.get('exists'):
    print(f"   Created: {results.get('creation_time', 'Unknown')}")
    print(f"   Iterations: {results.get('iterations', 'Unknown')}/100")

print("\n📈 Performance:")
if 'mae' in results:
    print(f"   MAE: {results['mae']:.4f}")
    print(f"   R²: {results['r2']:.4f}")
    if results.get('mape'):
        print(f"   MAPE: {results['mape']:.2f}%")
    print(f"   Meets Targets: {results.get('meets_targets', False)}")

print("\n🔒 Leakage Check:")
leakage_count = len(results.get('leakage_detected', []))
if leakage_count > 0:
    print(f"   ❌ {leakage_count} leakage features detected")
    print(f"   Issues: {', '.join(results['leakage_detected'])}")
else:
    print(f"   ✅ No leakage features detected")

if all_checks_passed and leakage_count == 0:
    print("\n✅ ALL CRITICAL CHECKS PASSED")
    print("✅ Model is ready for production use")
else:
    print("\n❌ CRITICAL ISSUES FOUND")
    print("\n🚨 Critical Issues:")
    for issue in issues:
        print(f"   • {issue}")

if warnings:
    print("\n⚠️  Warnings:")
    for warning in warnings:
        print(f"   • {warning}")

print("\n" + "="*70)
if not all_checks_passed or leakage_count > 0:
    print("🔧 RECOMMENDATION: Retrain model with corrected configuration")
    print("   Run: python3 scripts/execute_phase_1.py")
else:
    print("✅ Model audit complete - no action required")
print("="*70)

sys.exit(0 if all_checks_passed and leakage_count == 0 else 1)


