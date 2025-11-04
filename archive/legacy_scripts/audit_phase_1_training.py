#!/usr/bin/env python3
"""
Phase 1 Training Audit - Comprehensive evaluation report
"""
from google.cloud import bigquery
from datetime import datetime
import pandas as pd
import sys

PROJECT_ID = 'cbi-v14'
DATASET_ID = 'models_v4'
client = bigquery.Client(project=PROJECT_ID)

print("="*60)
print("📊 PHASE 1 TRAINING AUDIT REPORT")
print("="*60)
print(f"Timestamp: {datetime.now().isoformat()}\n")

models = ['bqml_1w_mean', 'bqml_1m_mean', 'bqml_3m_mean', 'bqml_6m_mean']
results = []

for model_name in models:
    print(f"🔍 {model_name}:")
    model_result = {'model': model_name, 'status': 'unknown'}
    
    try:
        # Check model exists by trying to get training info
        # If this works, model exists
        query = f"""
        SELECT COUNT(*) as iteration_count
        FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`)
        """
        train_check = client.query(query).to_dataframe()
        
        if train_check.empty:
            print(f"  ❌ Model not found or training info unavailable")
            model_result['status'] = 'not_found'
            results.append(model_result)
            continue
        
        print(f"  ✅ Model exists")
        
        # Get evaluation metrics on 2024 TEST DATA (not validation split)
        # Map model to target column and view
        target_map = {
            'bqml_1w_mean': ('target_1w', 'train_1w'),
            'bqml_1m_mean': ('target_1m', 'train_1m'),
            'bqml_3m_mean': ('target_3m', 'train_3m'),
            'bqml_6m_mean': ('target_6m', 'train_6m')
        }
        
        target_col, view_name = target_map[model_name]
        
        query = f"""
        SELECT 
          mean_absolute_error AS mae,
          mean_squared_error AS mse,
          SQRT(mean_squared_error) AS rmse,
          r2_score AS r2,
          explained_variance AS ev
        FROM ML.EVALUATE(
          MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`,
          (
            SELECT 
              * EXCEPT(date, treasury_10y_yield, econ_gdp_growth, econ_unemployment_rate, news_article_count, news_avg_score),
              date < '2024-01-01' AS is_training
            FROM `{PROJECT_ID}.{DATASET_ID}.{view_name}`
            WHERE date >= '2024-01-01'  -- TEST SET: 2024 data only
            AND {target_col} IS NOT NULL
          )
        )
        """
        eval_results = client.query(query).to_dataframe()
        
        if not eval_results.empty:
            row = eval_results.iloc[0]
            model_result['mae'] = float(row['mae'])
            model_result['mse'] = float(row['mse'])
            model_result['rmse'] = float(row['rmse'])
            model_result['r2'] = float(row['r2'])
            model_result['explained_variance'] = float(row['ev'])
            
            print(f"  📈 Evaluation Metrics:")
            print(f"     MAE: {row['mae']:.4f}")
            print(f"     RMSE: {row['rmse']:.4f}")
            print(f"     R²: {row['r2']:.4f}")
            print(f"     Explained Variance: {row['ev']:.4f}")
            
            # Quality assessment
            r2_val = float(row['r2'])
            if r2_val > 0.95:
                quality = 'Excellent'
            elif r2_val > 0.90:
                quality = 'Good'
            elif r2_val > 0.85:
                quality = 'Acceptable'
            elif r2_val > 0.50:
                quality = 'Needs Improvement'
            else:
                quality = 'Poor (check data/model)'
            model_result['quality'] = quality
            print(f"     Quality: {quality}")
        else:
            print(f"  ⚠️  No evaluation metrics available")
            model_result['status'] = 'no_eval'
        
        # Get training info (Production-Grade: Safe aggregation)
        query = f"""
        WITH training_data AS (
          SELECT 
            training_run,
            iteration,
            loss,
            eval_loss,
            duration_ms,
            learning_rate
          FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`)
        )
        SELECT
          MAX(iteration) as max_iteration,
          MIN(loss) AS min_train_loss,
          MAX(loss) AS max_train_loss,
          MIN(eval_loss) AS min_eval_loss,
          MAX(eval_loss) AS max_eval_loss,
          COUNT(*) AS total_iterations,
          SUM(duration_ms) / 1000.0 AS total_training_sec
        FROM training_data
        """
        train_info = client.query(query).to_dataframe()
        
        if not train_info.empty:
            row = train_info.iloc[0]
            max_iter = int(row['max_iteration'])
            model_result['iterations'] = max_iter
            model_result['train_loss'] = float(row['min_train_loss'])
            model_result['eval_loss'] = float(row['min_eval_loss'])
            model_result['total_training_sec'] = float(row['total_training_sec'])
            
            print(f"  🔨 Training Info:")
            print(f"     Iterations: {max_iter}/100")
            if max_iter >= 100:
                print(f"     ✅ Training completed (100 iterations)")
            else:
                print(f"     ⚠️  Training stopped early at iteration {max_iter}")
            
            print(f"     Min Train Loss: {row['min_train_loss']:.6f}")
            print(f"     Max Train Loss: {row['max_train_loss']:.6f}")
            print(f"     Min Eval Loss: {row['min_eval_loss']:.6f}")
            print(f"     Max Eval Loss: {row['max_eval_loss']:.6f}")
            print(f"     Total Training Time: {row['total_training_sec']:.1f} seconds")
        else:
            print(f"  ⚠️  No training info available")
        
        # Check feature importance (using correct syntax)
        try:
            query = f"""
            SELECT COUNT(*) as feature_count
            FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`)
            """
            feat_info = client.query(query).to_dataframe()
            if not feat_info.empty:
                feat_count = int(feat_info['feature_count'].iloc[0])
                model_result['feature_importance'] = feat_count
                print(f"  ✅ Feature importance available ({feat_count} features)")
            else:
                model_result['feature_importance'] = 0
                print(f"  ⚠️  No feature importance data")
        except Exception as e:
            error_str = str(e)
            # Feature importance might not be available if enable_global_explain didn't work
            if 'GLOBAL_EXPLAIN' in error_str or 'feature' in error_str.lower():
                model_result['feature_importance'] = 0
                print(f"  ⚠️  Feature importance check failed (may need ML.EXPLAIN_PREDICT instead)")
            else:
                model_result['feature_importance'] = 0
                print(f"  ⚠️  Feature importance check failed: {error_str[:60]}")
        
        model_result['status'] = 'success'
        print()
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
        model_result['status'] = 'error'
        model_result['error'] = str(e)[:200]
        print()
    
    results.append(model_result)

# Summary
print("="*60)
print("📋 SUMMARY")
print("="*60)

success_count = sum(1 for r in results if r['status'] == 'success')
total_count = len(results)

print(f"Models Trained: {success_count}/{total_count}")
print()

if success_count == total_count:
    print("✅ ALL MODELS TRAINED SUCCESSFULLY")
    print("\nTraining Quality:")
    for r in results:
        if r['status'] == 'success':
            quality = r.get('quality', 'Unknown')
            r2 = r.get('r2', 0)
            print(f"  {r['model']}: {quality} (R²={r2:.4f})")
else:
    print("⚠️  SOME MODELS FAILED")
    for r in results:
        if r['status'] != 'success':
            print(f"  ❌ {r['model']}: {r['status']}")

print("="*60)

# Exit code
sys.exit(0 if success_count == total_count else 1)

