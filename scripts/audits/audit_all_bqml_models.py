#!/usr/bin/env python3
"""
Comprehensive BigQuery ML Model Audit
Queries BigQuery to get complete details on all trained models:
- Model metadata (creation, training time, type, options)
- Evaluation metrics (MAE, RMSE, R², MAPE)
- Training data statistics
- Training job errors
- Usage in codebase
- Credibility assessment
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configuration
PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
LOCATION = "us-central1"

def get_bigquery_client():
    """Initialize BigQuery client"""
    try:
        client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
        return client
    except Exception as e:
        print(f"❌ Error initializing BigQuery client: {e}")
        sys.exit(1)

def list_all_models(client):
    """List all models in the dataset"""
    try:
        dataset_ref = client.dataset(DATASET_ID)
        models = list(client.list_models(dataset_ref))
        return models
    except NotFound:
        print(f"❌ Dataset {DATASET_ID} not found")
        return []
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return []

def get_model_metadata(client, model_id):
    """Get detailed metadata for a model"""
    try:
        model_ref = client.get_model(model_id)
        return model_ref
    except NotFound:
        return None
    except Exception as e:
        print(f"⚠️  Error getting model {model_id}: {e}")
        return None

def evaluate_model(client, model_id, target_col):
    """Evaluate model and get metrics"""
    try:
        # Get training data query
        training_query = f"""
        SELECT COUNT(*) as row_count,
               MIN(date) as min_date,
               MAX(date) as max_date,
               COUNT(DISTINCT date) as distinct_dates
        FROM `{PROJECT_ID}.{DATASET_ID}.training_dataset_super_enriched`
        WHERE {target_col} IS NOT NULL
        """
        
        training_stats = client.query(training_query).result()
        training_data = next(training_stats)
        
        # Try to evaluate the model
        eval_query = f"""
        SELECT *
        FROM ML.EVALUATE(MODEL `{model_id}`,
          (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.training_dataset_super_enriched` 
           WHERE {target_col} IS NOT NULL))
        """
        
        eval_result = client.query(eval_query).result()
        metrics = next(eval_result)
        
        # Calculate MAPE manually
        mape_query = f"""
        WITH predictions AS (
          SELECT 
            {target_col} as actual,
            predicted_{target_col} as predicted
          FROM ML.PREDICT(MODEL `{model_id}`,
            (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.training_dataset_super_enriched` 
             WHERE {target_col} IS NOT NULL))
        )
        SELECT 
          AVG(ABS((actual - predicted) / NULLIF(actual, 0)) * 100) as mape
        FROM predictions
        WHERE actual != 0
        """
        
        mape_result = client.query(mape_query).result()
        mape_row = next(mape_result)
        mape = mape_row.mape if mape_row.mape else None
        
        return {
            'training_stats': dict(training_data),
            'metrics': dict(metrics),
            'mape': mape
        }
    except Exception as e:
        return {
            'error': str(e),
            'training_stats': None,
            'metrics': None,
            'mape': None
        }

def get_training_job_errors(client, model_id):
    """Check for training job errors in job history"""
    try:
        # Query job history for this model - simplified query
        jobs_query = f"""
        SELECT 
          job_id,
          creation_time,
          state,
          error_result
        FROM `{PROJECT_ID}.region-{LOCATION}.INFORMATION_SCHEMA.JOBS`
        WHERE 
          job_type = 'QUERY'
          AND statement_type = 'CREATE_MODEL'
          AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
        ORDER BY creation_time DESC
        LIMIT 100
        """
        
        jobs = client.query(jobs_query).result()
        errors = []
        model_name = model_id.split('.')[-1]
        
        for job in jobs:
            # Check if job references this model
            job_id = job.job_id
            try:
                job_obj = client.get_job(job_id)
                if model_name in str(job_obj.query):
                    if job_obj.error_result:
                        errors.append({
                            'job_id': job_id,
                            'creation_time': str(job.creation_time),
                            'error': dict(job_obj.error_result) if job_obj.error_result else None,
                            'state': job.state
                        })
            except Exception as e:
                # Skip jobs we can't access
                pass
        
        return errors
    except Exception as e:
        # Return empty list if we can't query - not critical
        return []

def check_model_usage_in_codebase(model_name):
    """Check if model is referenced in codebase"""
    model_refs = []
    
    # Search for model references
    sql_files = list(Path(project_root).rglob("*.sql"))
    py_files = list(Path(project_root).rglob("*.py"))
    md_files = list(Path(project_root).rglob("*.md"))
    
    for file_path in sql_files + py_files + md_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if model_name in content:
                    model_refs.append(str(file_path.relative_to(project_root)))
        except:
            pass
    
    return model_refs

def assess_model_credibility(model_data):
    """Assess if model is credible for future use"""
    issues = []
    strengths = []
    
    # Check if model exists
    if not model_data.get('model'):
        return {
            'credible': False,
            'reason': 'Model does not exist',
            'issues': ['Model not found in BigQuery'],
            'strengths': []
        }
    
    # Check training data
    training_stats = model_data.get('evaluation', {}).get('training_stats')
    if training_stats:
        if training_stats.get('row_count', 0) < 100:
            issues.append(f"Very small training set: {training_stats.get('row_count')} rows")
        elif training_stats.get('row_count', 0) < 500:
            issues.append(f"Small training set: {training_stats.get('row_count')} rows")
        else:
            strengths.append(f"Sufficient training data: {training_stats.get('row_count')} rows")
    
    # Check evaluation metrics
    metrics = model_data.get('evaluation', {}).get('metrics')
    if metrics:
        mae = metrics.get('mean_absolute_error')
        rmse = metrics.get('mean_squared_error', 0) ** 0.5 if metrics.get('mean_squared_error') else None
        r2 = metrics.get('r2_score')
        mape = model_data.get('evaluation', {}).get('mape')
        
        if mae:
            if mae < 1.0:
                strengths.append(f"Excellent MAE: {mae:.4f}")
            elif mae < 2.0:
                strengths.append(f"Good MAE: {mae:.4f}")
            else:
                issues.append(f"High MAE: {mae:.4f}")
        
        if mape:
            if mape < 2.0:
                strengths.append(f"Excellent MAPE: {mape:.2f}%")
            elif mape < 5.0:
                strengths.append(f"Good MAPE: {mape:.2f}%")
            elif mape < 10.0:
                issues.append(f"Moderate MAPE: {mape:.2f}%")
            else:
                issues.append(f"High MAPE: {mape:.2f}%")
        
        if r2:
            if r2 > 0.9:
                strengths.append(f"Excellent R²: {r2:.4f}")
            elif r2 > 0.7:
                strengths.append(f"Good R²: {r2:.4f}")
            elif r2 > 0.5:
                issues.append(f"Moderate R²: {r2:.4f}")
            else:
                issues.append(f"Poor R²: {r2:.4f}")
    
    # Check for errors
    errors = model_data.get('training_errors', [])
    if errors:
        issues.append(f"Training errors found: {len(errors)}")
    
    # Check model age
    model = model_data.get('model')
    if model:
        created = model.created
        age_days = (datetime.now(created.tzinfo) - created).days
        if age_days > 90:
            issues.append(f"Model is {age_days} days old - may need retraining")
        elif age_days > 30:
            issues.append(f"Model is {age_days} days old")
        else:
            strengths.append(f"Recent model: {age_days} days old")
    
    # Determine credibility
    credible = len(issues) == 0 or (len(strengths) > len(issues))
    
    return {
        'credible': credible,
        'issues': issues,
        'strengths': strengths,
        'recommendation': 'USE' if credible else 'REVIEW BEFORE USE'
    }

def format_model_report(model_data):
    """Format model data into readable report"""
    model = model_data.get('model')
    if not model:
        return f"❌ Model not found: {model_data.get('model_id')}\n"
    
    model_id = model_data.get('model_id')
    model_name = model_id.split('.')[-1]
    
    report = []
    report.append("=" * 80)
    report.append(f"MODEL: {model_name}")
    report.append("=" * 80)
    
    # Basic Info
    report.append(f"\n📍 Location: {model_id}")
    report.append(f"📅 Created: {model.created}")
    report.append(f"🔄 Modified: {model.modified}")
    report.append(f"🏷️  Model Type: {model.model_type}")
    report.append(f"📍 Location: {model.location}")
    
    # Model Options
    if model_options := model_data.get('model_options'):
        report.append(f"\n⚙️  Model Options:")
        for key, value in model_options.items():
            report.append(f"   - {key}: {value}")
    
    # Training Data
    training_stats = model_data.get('evaluation', {}).get('training_stats')
    if training_stats:
        report.append(f"\n📊 Training Data:")
        report.append(f"   - Rows: {training_stats.get('row_count', 'N/A')}")
        report.append(f"   - Date Range: {training_stats.get('min_date')} to {training_stats.get('max_date')}")
        report.append(f"   - Distinct Dates: {training_stats.get('distinct_dates', 'N/A')}")
    
    # Evaluation Metrics
    metrics = model_data.get('evaluation', {}).get('metrics')
    if metrics:
        report.append(f"\n📈 Evaluation Metrics:")
        report.append(f"   - MAE: {metrics.get('mean_absolute_error', 'N/A'):.4f}" if metrics.get('mean_absolute_error') else "   - MAE: N/A")
        report.append(f"   - RMSE: {metrics.get('mean_squared_error', 0) ** 0.5:.4f}" if metrics.get('mean_squared_error') else "   - RMSE: N/A")
        report.append(f"   - R²: {metrics.get('r2_score', 'N/A'):.4f}" if metrics.get('r2_score') else "   - R²: N/A")
        report.append(f"   - Explained Variance: {metrics.get('explained_variance_score', 'N/A'):.4f}" if metrics.get('explained_variance_score') else "   - Explained Variance: N/A")
    
    mape = model_data.get('evaluation', {}).get('mape')
    if mape:
        report.append(f"   - MAPE: {mape:.2f}%")
    
    # Errors
    errors = model_data.get('training_errors', [])
    if errors:
        report.append(f"\n⚠️  Training Errors: {len(errors)}")
        for error in errors[:3]:  # Show first 3
            if isinstance(error, dict):
                error_msg = error.get('error', {})
                if isinstance(error_msg, dict):
                    msg = error_msg.get('message', 'N/A')
                else:
                    msg = str(error_msg)
                job_id = error.get('job_id', 'N/A')
                report.append(f"   - Job {job_id}: {msg}")
            else:
                report.append(f"   - {str(error)}")
    
    # Usage
    usage = model_data.get('usage_in_codebase', [])
    if usage:
        report.append(f"\n📝 Used in Codebase ({len(usage)} files):")
        for file in usage[:10]:  # Show first 10
            report.append(f"   - {file}")
    else:
        report.append(f"\n📝 Usage: Not referenced in codebase")
    
    # Credibility Assessment
    credibility = model_data.get('credibility')
    if credibility:
        report.append(f"\n✅ Credibility Assessment:")
        report.append(f"   - Status: {'✅ CREDIBLE' if credibility.get('credible') else '⚠️  REVIEW NEEDED'}")
        report.append(f"   - Recommendation: {credibility.get('recommendation')}")
        
        if credibility.get('strengths'):
            report.append(f"\n   Strengths:")
            for strength in credibility.get('strengths', []):
                report.append(f"     ✅ {strength}")
        
        if credibility.get('issues'):
            report.append(f"\n   Issues:")
            for issue in credibility.get('issues', []):
                report.append(f"     ⚠️  {issue}")
    
    # Purpose (inferred from name)
    report.append(f"\n🎯 Inferred Purpose:")
    if '1w' in model_name.lower():
        report.append("   - 1 Week forecast horizon")
    elif '1m' in model_name.lower():
        report.append("   - 1 Month forecast horizon")
    elif '3m' in model_name.lower():
        report.append("   - 3 Month forecast horizon")
    elif '6m' in model_name.lower():
        report.append("   - 6 Month forecast horizon")
    
    if 'all_features' in model_name.lower():
        report.append("   - Uses all available features")
    elif 'mean' in model_name.lower():
        report.append("   - May use mean imputation or aggregation")
    
    if 'bqml' in model_name.lower():
        report.append("   - BigQuery ML model (BOOSTED_TREE_REGRESSOR)")
    elif 'nn' in model_name.lower() or 'dnn' in model_name.lower():
        report.append("   - Neural Network model")
    elif 'arima' in model_name.lower():
        report.append("   - ARIMA time series model")
    elif 'linear' in model_name.lower():
        report.append("   - Linear regression model")
    
    report.append("")
    
    return "\n".join(report)

def main():
    """Main execution"""
    print("🔍 BigQuery ML Model Audit - Comprehensive Report")
    print("=" * 80)
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    print(f"Location: {LOCATION}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    print()
    
    client = get_bigquery_client()
    
    # List all models
    print("📋 Discovering models...")
    models = list_all_models(client)
    print(f"Found {len(models)} model(s)\n")
    
    if not models:
        print("❌ No models found in dataset")
        return
    
    # Process each model
    all_model_data = []
    
    for model in models:
        model_id = f"{model.project}.{model.dataset_id}.{model.model_id}"
        model_name = model.model_id
        
        print(f"🔍 Analyzing: {model_name}...")
        
        # Get model metadata
        model_obj = get_model_metadata(client, model_id)
        
        # Determine target column
        target_col = None
        if '1w' in model_name.lower():
            target_col = 'target_1w'
        elif '1m' in model_name.lower():
            target_col = 'target_1m'
        elif '3m' in model_name.lower():
            target_col = 'target_3m'
        elif '6m' in model_name.lower():
            target_col = 'target_6m'
        else:
            # Try to infer from model options
            if model_obj and hasattr(model_obj, 'labels') and model_obj.labels:
                target_col = model_obj.labels[0] if isinstance(model_obj.labels, list) else str(model_obj.labels)
        
        # Get evaluation
        evaluation = {}
        if target_col:
            evaluation = evaluate_model(client, model_id, target_col)
        
        # Get training errors
        training_errors = get_training_job_errors(client, model_id)
        
        # Check usage
        usage = check_model_usage_in_codebase(model_name)
        
        # Get model options
        model_options = {}
        if model_obj:
            if hasattr(model_obj, 'options'):
                model_options = dict(model_obj.options) if model_obj.options else {}
        
        # Assess credibility
        model_data = {
            'model_id': model_id,
            'model_name': model_name,
            'model': model_obj,
            'model_options': model_options,
            'evaluation': evaluation,
            'training_errors': training_errors,
            'usage_in_codebase': usage
        }
        
        credibility = assess_model_credibility(model_data)
        model_data['credibility'] = credibility
        
        all_model_data.append(model_data)
    
    # Generate report
    print("\n" + "=" * 80)
    print("COMPREHENSIVE MODEL REPORT")
    print("=" * 80 + "\n")
    
    report_lines = []
    
    # Summary
    credible_count = sum(1 for m in all_model_data if m.get('credibility', {}).get('credible', False))
    report_lines.append(f"📊 SUMMARY")
    report_lines.append(f"Total Models: {len(all_model_data)}")
    report_lines.append(f"Credible for Use: {credible_count}")
    report_lines.append(f"Review Needed: {len(all_model_data) - credible_count}")
    report_lines.append("")
    
    # Individual model reports
    for model_data in all_model_data:
        report_lines.append(format_model_report(model_data))
    
    # Write report
    report_content = "\n".join(report_lines)
    print(report_content)
    
    # Save to file
    report_file = project_root / "docs" / "BQML_MODELS_COMPLETE_AUDIT.md"
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w') as f:
        f.write("# BigQuery ML Models - Complete Audit Report\n\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}\n")
        f.write(f"**Project:** {PROJECT_ID}\n")
        f.write(f"**Dataset:** {DATASET_ID}\n\n")
        f.write("---\n\n")
        f.write(report_content)
    
    print(f"\n✅ Report saved to: {report_file}")
    
    # JSON export
    json_file = project_root / "docs" / "BQML_MODELS_AUDIT_DATA.json"
    json_data = []
    for model_data in all_model_data:
        json_entry = {
            'model_id': model_data.get('model_id'),
            'model_name': model_data.get('model_name'),
            'created': model_data.get('model').created.isoformat() if model_data.get('model') else None,
            'model_type': model_data.get('model').model_type if model_data.get('model') else None,
            'model_options': model_data.get('model_options'),
            'evaluation': model_data.get('evaluation'),
            'training_errors': model_data.get('training_errors'),
            'usage_count': len(model_data.get('usage_in_codebase', [])),
            'credibility': model_data.get('credibility')
        }
        json_data.append(json_entry)
    
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2, default=str)
    
    print(f"✅ JSON data saved to: {json_file}")

if __name__ == "__main__":
    main()

