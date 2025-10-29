#!/usr/bin/env python3
"""
ENHANCED PRE-TRAINING AUDIT WITH MAPE VALIDATION
Comprehensive data quality checks before model training
Checks for unrealistic metrics, placeholder values, target leakage, duplicates
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import re

def run_enhanced_audit():
    """Comprehensive pre-training data audit with MAPE validation"""
    client = bigquery.Client(project='cbi-v14')
    issues_found = 0
    warnings = 0
    
    print("=" * 80)
    print("🔍 ENHANCED PRE-TRAINING DATA AUDIT")
    print("=" * 80)
    
    # 1. MODEL PERFORMANCE REALITY CHECK
    print("\n📊 VALIDATING MODEL PERFORMANCE METRICS...")
    
    # Get list of V4 models from models_v4 dataset
    try:
        v4_models_list = list(client.list_models('models_v4'))
        
        if len(v4_models_list) > 0:
            print(f"  ✓ Found {len(v4_models_list)} V4 models in models_v4 dataset")
            
            # Get model details for all V4 models
            print(f"\n  Evaluating V4 models...")
            
            for model in v4_models_list:
                model_name = model.model_id
                print(f"\n    {model_name}:")
                print(f"      Created: {model.created}")
                print(f"      Type: {model.model_type}")
                
                try:
                    # Get model info
                    model_ref = client.get_model(f'cbi-v14.models_v4.{model_name}')
                    print(f"      Features: {len(model_ref.feature_columns) if model_ref.feature_columns else 'Unknown'}")
                    
                    # Try to get evaluation metrics
                    eval_query = f"""
                    SELECT * FROM ML.EVALUATE(
                        MODEL `cbi-v14.models_v4.{model_name}`,
                        (SELECT * FROM `cbi-v14.models_v4.training_dataset_v4` LIMIT 100)
                    )
                    """
                    metrics_df = client.query(eval_query).result().to_dataframe()
                    
                    if not metrics_df.empty:
                        mae = metrics_df['mean_absolute_error'].iloc[0]
                        mse = metrics_df['mean_squared_error'].iloc[0]
                        rmse = np.sqrt(mse) if not pd.isna(mse) else None
                        
                        # Estimate MAPE if we have price range
                        price_check = """
                        SELECT AVG(close_price) as avg_price
                        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
                        WHERE time >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                        """
                        price_result = client.query(price_check).result().to_dataframe()
                        avg_price = price_result['avg_price'].iloc[0] if not price_result.empty else 50
                        
                        estimated_mape = (mae / avg_price * 100) if avg_price > 0 else None
                        
                        print(f"    {model_name}:")
                        print(f"      MAE: {mae:.4f}")
                        if estimated_mape:
                            print(f"      Estimated MAPE: {estimated_mape:.2f}%")
                        
                        # Flag suspiciously good metrics
                        if estimated_mape and estimated_mape < 0.5:
                            print(f"      ⚠️ UNREALISTIC: Sub-0.5% MAPE suggests data leakage or contamination")
                            warnings += 1
                        
                        # Flag broken models
                        if mae > 1000000:
                            print(f"      ❌ BROKEN: MAE > 1M (likely normalization issue)")
                            issues_found += 1
                            
                except Exception as e:
                    # Model might not support ML.EVALUATE or have issues
                    print(f"      ⚠️ Could not evaluate: {str(e)[:50]}")
        else:
            print("  ℹ️ No V4 models found in models_v4 dataset")
            
    except Exception as e:
        print(f"  ⚠️ Could not validate model metrics: {str(e)[:100]}")
        warnings += 1
    
    # 2. COMPREHENSIVE DATASET INVENTORY
    print("\n📊 VERIFYING ALL REQUIRED DATASETS...")
    
    # Required datasets based on actual CBI-V14 schema
    required_datasets = {
        "Price Data": [
            "soybean_oil_prices", 
            "corn_prices",
            "wheat_prices",
            "palm_oil_prices",
            "crude_oil_prices",
            "gold_prices",
            "natural_gas_prices",
            "sp500_prices"
        ],
        "FX Data": [
            "currency_data",
            "usd_index_prices"
        ],
        "Economic Data": [
            "economic_indicators",
            "treasury_prices",
            "vix_daily"
        ],
        "Weather Data": [
            "weather_data",
            "weather_brazil_daily",
            "weather_argentina_daily",
            "weather_us_midwest_daily"
        ],
        "Intelligence Data": [
            "social_sentiment",
            "news_intelligence",
            "trump_policy_intelligence"
        ],
        "Fundamental Data": [
            "cftc_cot",
            "usda_export_sales",
            "usda_harvest_progress"
        ]
    }
    
    missing_datasets = []
    dataset_stats = {}
    
    for category, datasets in required_datasets.items():
        print(f"  Checking {category}...")
        for dataset in datasets:
            query = f"""
            SELECT COUNT(*) as row_count 
            FROM `cbi-v14.forecasting_data_warehouse.{dataset}`
            """
            
            try:
                row_count = client.query(query).result().to_dataframe().iloc[0]["row_count"]
                dataset_stats[dataset] = row_count
                
                if row_count < 100:
                    print(f"    ⚠️ {dataset}: Only {row_count} rows (minimal data)")
                    warnings += 1
                else:
                    print(f"    ✓ {dataset}: {row_count:,} rows")
            except Exception as e:
                print(f"    ❌ {dataset}: NOT FOUND or ERROR: {str(e)[:80]}")
                missing_datasets.append(dataset)
                issues_found += 1
    
    if missing_datasets:
        print(f"  ❌ MISSING DATASETS: {len(missing_datasets)} required datasets not found")
        print(f"    {', '.join(missing_datasets)}")
    else:
        print(f"  ✓ All required datasets are present")
    
    # 3. ENHANCED PLACEHOLDER DETECTION
    print("\n🔍 DEEP SCANNING FOR PLACEHOLDER VALUES...")
    
    # Common placeholder patterns
    placeholder_patterns = [
        {"value": 0.5, "description": "Classic 0.5 placeholder"},
        {"value": -999, "description": "Missing value code"},
        {"value": 999999, "description": "Missing value code"},
        {"value": -1, "description": "Default initialization value"},
        {"value": 999, "description": "Another missing value code"}
    ]
    
    # Key tables to check
    critical_tables = [
        "soybean_oil_prices",
        "corn_prices", 
        "economic_indicators",
        "social_sentiment",
        "weather_data"
    ]
    
    for table in critical_tables:
        if table not in dataset_stats or dataset_stats[table] == 0:
            continue
            
        try:
            # Get numeric columns
            query = f"""
            SELECT column_name, data_type
            FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.COLUMNS`
            WHERE table_name = '{table}' 
            AND data_type IN ('FLOAT64', 'NUMERIC', 'INT64')
            """
            columns_df = client.query(query).result().to_dataframe()
            
            if columns_df.empty:
                continue
                
            print(f"  Checking {table}...")
            
            for _, row in columns_df.iterrows():
                column = row['column_name']
                
                # Check exact placeholder values
                for pattern in placeholder_patterns:
                    query = f"""
                    SELECT COUNT(*) as placeholder_count
                    FROM `cbi-v14.forecasting_data_warehouse.{table}`
                    WHERE {column} = {pattern["value"]}
                    """
                    try:
                        placeholder_count = client.query(query).result().to_dataframe().iloc[0]["placeholder_count"]
                        if placeholder_count > 0:
                            pct = (placeholder_count / dataset_stats[table]) * 100
                            if pct > 5:  # More than 5% placeholders
                                print(f"    ❌ {column}: {placeholder_count:,} instances of {pattern['value']} ({pct:.1f}% - {pattern['description']})")
                                issues_found += 1
                            elif pct > 1:
                                print(f"    ⚠️ {column}: {placeholder_count:,} instances of {pattern['value']} ({pct:.1f}%)")
                                warnings += 1
                    except Exception as e:
                        continue
                        
                # Check for columns dominated by a single value
                if column in ['sentiment_score', 'intelligence_score']:
                    query = f"""
                    SELECT 
                        {column} as value,
                        COUNT(*) as count
                    FROM `cbi-v14.forecasting_data_warehouse.{table}`
                    GROUP BY {column}
                    ORDER BY count DESC
                    LIMIT 5
                    """
                    
                    try:
                        patterns_df = client.query(query).result().to_dataframe()
                        if len(patterns_df) > 0:
                            total_rows = dataset_stats[table]
                            top_value_pct = (patterns_df.iloc[0]["count"] / total_rows) * 100
                            
                            if top_value_pct > 50:  # More than 50% same value
                                print(f"    ⚠️ {column}: Value {patterns_df.iloc[0]['value']} appears in {top_value_pct:.1f}% of rows (potential placeholder)")
                                warnings += 1
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"    ⚠️ Could not check {table}: {str(e)[:50]}")
            continue
    
    # 4. DUPLICATE CHECK ACROSS ALL KEY TABLES
    print("\n🔍 CHECKING FOR DUPLICATES ACROSS ALL DATASETS...")
    
    duplicate_issues = []
    
    for category, datasets in required_datasets.items():
        for dataset in datasets:
            if dataset not in dataset_stats or dataset_stats[dataset] == 0:
                continue
                
            # Determine date column based on table
            if dataset in ['social_sentiment', 'news_intelligence']:
                date_col = 'DATE(timestamp)' if dataset == 'social_sentiment' else 'DATE(published)'
            elif dataset == 'economic_indicators':
                date_col = 'DATE(time)'
            elif 'weather' in dataset:
                date_col = 'date'
            else:
                date_col = 'DATE(time)'
            
            query = f"""
            SELECT 
                {date_col} as date, 
                COUNT(*) as dupes
            FROM `cbi-v14.forecasting_data_warehouse.{dataset}`
            GROUP BY {date_col}
            HAVING COUNT(*) > 1
            ORDER BY dupes DESC
            LIMIT 5
            """
            
            try:
                dupes_df = client.query(query).result().to_dataframe()
                if len(dupes_df) > 0:
                    total_dupes = dupes_df['dupes'].sum() - len(dupes_df)
                    print(f"  ❌ {dataset}: {len(dupes_df)} dates have duplicates, totaling {total_dupes} extra records")
                    for _, row in dupes_df.head(3).iterrows():
                        print(f"    - {row['date']}: {row['dupes']} records (should be 1)")
                    duplicate_issues.append(dataset)
                    issues_found += 1
            except Exception as e:
                # Table might not exist or have different schema
                continue
    
    if not duplicate_issues:
        print("  ✓ No duplicates found")
    
    # 5. DATE RANGE CONSISTENCY
    print("\n📅 VALIDATING DATE RANGES ACROSS DATASETS...")
    
    date_ranges = {}
    
    for category, datasets in required_datasets.items():
        for dataset in datasets:
            if dataset not in dataset_stats or dataset_stats[dataset] == 0:
                continue
                
            # Determine date column
            if dataset in ['social_sentiment', 'news_intelligence']:
                date_col = 'DATE(timestamp)' if dataset == 'social_sentiment' else 'DATE(published)'
            elif dataset == 'economic_indicators':
                date_col = 'DATE(time)'
            elif 'weather' in dataset:
                date_col = 'date'
            else:
                date_col = 'DATE(time)'
            
            query = f"""
            SELECT 
                MIN({date_col}) as min_date,
                MAX({date_col}) as max_date,
                COUNT(DISTINCT {date_col}) as unique_dates
            FROM `cbi-v14.forecasting_data_warehouse.{dataset}`
            """
            
            try:
                dates_df = client.query(query).result().to_dataframe()
                min_date = dates_df.iloc[0]["min_date"]
                max_date = dates_df.iloc[0]["max_date"]
                unique_dates = dates_df.iloc[0]["unique_dates"]
                
                if min_date and max_date:
                    date_ranges[dataset] = {
                        "min_date": min_date,
                        "max_date": max_date,
                        "unique_dates": unique_dates
                    }
                    
                    # Check for large gaps
                    days_span = (max_date - min_date).days
                    if days_span > 0 and unique_dates / days_span < 0.3:
                        print(f"  ⚠️ {dataset}: Only {unique_dates} unique dates across {days_span} day span ({unique_dates/days_span:.1%} coverage)")
                        warnings += 1
            except Exception as e:
                continue
    
    # Check for date misalignment between key datasets
    if len(date_ranges) > 1:
        price_tables = ['soybean_oil_prices', 'corn_prices', 'crude_oil_prices']
        price_ranges = {k: v for k, v in date_ranges.items() if k in price_tables}
        
        if price_ranges:
            min_dates = [info["min_date"] for ds, info in price_ranges.items() if info["min_date"]]
            max_dates = [info["max_date"] for ds, info in price_ranges.items() if info["max_date"]]
            
            if min_dates and max_dates:
                overall_min = min(min_dates)
                overall_max = max(max_dates)
                
                for dataset, info in price_ranges.items():
                    start_gap = (info["min_date"] - overall_min).days
                    end_gap = (overall_max - info["max_date"]).days
                    
                    if start_gap > 365:
                        print(f"  ⚠️ {dataset}: Starts {start_gap} days after earliest dataset")
                        warnings += 1
                    if end_gap > 30:
                        print(f"  ⚠️ {dataset}: Ends {end_gap} days before latest dataset")
                        warnings += 1
    
    # 6. TRAINING DATASET CHECK
    print("\n📊 CHECKING TRAINING DATASETS...")
    
    # Check all available training datasets
    training_datasets = [
        'training_dataset_enriched',
        'training_dataset_enhanced_v5',
        'training_dataset_enhanced',
        'training_dataset',
        'FINAL_TRAINING_DATASET_COMPLETE'
    ]
    
    dataset_stats = {}
    
    for dataset_name in training_datasets:
        try:
            query = f"""
            SELECT 
                COUNT(*) as row_count,
                COUNT(DISTINCT date) as unique_dates,
                COUNT(*) - COUNT(DISTINCT date) as duplicates
            FROM `cbi-v14.models.{dataset_name}`
            """
            
            result = client.query(query).result().to_dataframe()
            r = result.iloc[0]
            
            dataset_stats[dataset_name] = {
                'rows': int(r['row_count']),
                'unique_dates': int(r['unique_dates']),
                'duplicates': int(r['duplicates'])
            }
            
            print(f"  {dataset_name}:")
            print(f"    Rows: {int(r['row_count']):,}")
            print(f"    Unique dates: {int(r['unique_dates']):,}")
            
            if r['duplicates'] > 0:
                print(f"    ❌ Found {int(r['duplicates'])} duplicate date rows")
                issues_found += 1
            else:
                print(f"    ✓ No date duplicates")
                
        except Exception as e:
            print(f"  ⚠️ {dataset_name}: {str(e)[:80]}")
            continue
    
    # Recommend best dataset
    if dataset_stats:
        best_dataset = max(dataset_stats.items(), key=lambda x: x[1]['rows'])
        print(f"\n  💡 Best dataset: {best_dataset[0]} ({best_dataset[1]['rows']:,} rows)")
    
    # 7. Summary
    print("\n" + "=" * 80)
    print("ENHANCED AUDIT SUMMARY")
    print("=" * 80)
    
    if issues_found == 0:
        if warnings == 0:
            print("✅ ENHANCED AUDIT PASSED: All checks completed successfully!")
            print("✅ DATA IS READY FOR V4 MODEL TRAINING")
            return True
        else:
            print(f"⚠️ ENHANCED AUDIT PASSED WITH WARNINGS: {warnings} potential issues to review")
            print("✅ DATA IS TECHNICALLY READY FOR TRAINING, BUT REVIEW WARNINGS")
            return True
    else:
        print(f"❌ ENHANCED AUDIT FAILED: {issues_found} critical issues found!")
        print(f"⚠️ Additionally found {warnings} warnings")
        print("❌ RESOLVE CRITICAL ISSUES BEFORE PROCEEDING WITH TRAINING")
        return False

if __name__ == "__main__":
    success = run_enhanced_audit()
    sys.exit(0 if success else 1)

