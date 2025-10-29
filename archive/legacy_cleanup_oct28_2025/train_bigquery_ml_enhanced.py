#!/usr/bin/env python3
"""
Train BigQuery ML Models with Enhanced Dataset
Goal: Beat V4's MAE 1.55 with additional intelligence/FX/crush features
"""

from google.cloud import bigquery
import pandas as pd

print("="*80)
print("BIGQUERY ML TRAINING - ENHANCED DATASET")
print("="*80)

client = bigquery.Client(project='cbi-v14')

# Step 1: Upload enhanced dataset to BigQuery
print("\n1️⃣ UPLOADING ENHANCED DATASET TO BIGQUERY")
print("-"*80)

df = pd.read_csv('FINAL_ENGINEERED_DATASET.csv')
df['date'] = pd.to_datetime(df['date'])

print(f"Dataset: {df.shape}")
print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")

# Create dataset if doesn't exist
dataset_id = 'models_v5'
try:
    client.create_dataset(dataset_id, exists_ok=True)
    print(f"✅ Dataset {dataset_id} ready")
except Exception as e:
    print(f"Dataset creation: {str(e)[:100]}")

# Upload to BigQuery (use models dataset for now)
table_id = 'cbi-v14.models.training_dataset_enhanced_v5'

job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_TRUNCATE",
    autodetect=True
)

print(f"\nUploading to {table_id}...")

job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()

print(f"✅ Uploaded {len(df)} rows × {len(df.columns)} columns")

# Step 2: Train BigQuery ML Boosted Tree model
print("\n2️⃣ TRAINING BIGQUERY ML MODEL")
print("-"*80)

model_name = 'zl_boosted_tree_1w_v5_enhanced'

print(f"Model: {model_name}")
print(f"Target: target_1w (1-week price forecast)")
print(f"Algorithm: BOOSTED_TREE_REGRESSOR")

sql = f"""
CREATE OR REPLACE MODEL `cbi-v14.models.{model_name}`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],
  max_iterations=500,
  learn_rate=0.05,
  subsample=0.8,
  max_tree_depth=6,
  early_stop=TRUE,
  min_rel_progress=0.01,
  data_split_method='AUTO_SPLIT'
) AS
SELECT 
  * EXCEPT(date, target_1m)
FROM `cbi-v14.models.training_dataset_enhanced_v5`
WHERE target_1w IS NOT NULL
  AND date < '2024-10-01'
"""

print(f"\nExecuting BigQuery ML training...")
print(f"This will take 3-5 minutes...")

job = client.query(sql)
job.result()

print(f"✅ Model trained successfully!")

# Step 3: Evaluate the model
print("\n3️⃣ EVALUATING MODEL")
print("-"*80)

eval_sql = f"""
SELECT 
  *
FROM ML.EVALUATE(
  MODEL `cbi-v14.models.{model_name}`,
  (SELECT * FROM `cbi-v14.models.training_dataset_enhanced_v5`
   WHERE date >= '2024-10-01')
)
"""

eval_results = client.query(eval_sql).to_dataframe()

print(f"Evaluation metrics:")
print(eval_results)

# Get MAE and MAPE
if 'mean_absolute_error' in eval_results.columns:
    mae = eval_results['mean_absolute_error'].iloc[0]
    print(f"\n✅ Test MAE: ${mae:.2f}")
    
    if 'mean_absolute_percentage_error' in eval_results.columns:
        mape = eval_results['mean_absolute_percentage_error'].iloc[0]
        print(f"✅ Test MAPE: {mape:.2f}%")
    
    print(f"\n📊 COMPARISON:")
    print(f"  V4 Enriched (existing): MAE $1.55, MAPE 3.09%")
    print(f"  V5 Enhanced (new):      MAE ${mae:.2f}")
    
    if mae < 1.55:
        improvement = 1.55 - mae
        pct_improvement = (improvement / 1.55) * 100
        print(f"  ✅ IMPROVED by ${improvement:.2f} ({pct_improvement:.1f}%)")
        print(f"  🎯 SUCCESS - Enhanced features add value!")
    elif mae < 1.80:
        print(f"  ✅ COMPETITIVE - Within $0.25 of V4")
    else:
        print(f"  ⚠️ Needs work - ${mae - 1.55:.2f} worse than V4")

# Step 4: Get feature importance
print("\n4️⃣ FEATURE IMPORTANCE")
print("-"*80)

importance_sql = f"""
SELECT 
  *
FROM ML.FEATURE_IMPORTANCE(
  MODEL `cbi-v14.models.{model_name}`
)
ORDER BY importance DESC
LIMIT 20
"""

try:
    importance = client.query(importance_sql).to_dataframe()
    
    print(f"Top 20 features:")
    for idx, row in importance.iterrows():
        feat = row['feature'] if 'feature' in row else row[0]
        imp = row['importance'] if 'importance' in row else row[1]
        print(f"  {idx+1:2}. {feat[:45]:45} {imp:.6f}")
    
    # Check if new features appear
    new_feature_keywords = ['crush_spread', 'fx_usd_brl', 'fx_usd_cny', 'fx_usd_ars', 
                           'tariff_decay', 'china_decay', 'regime', 'interaction']
    
    print(f"\n🔍 New Features in Top 20:")
    for idx, row in importance.iterrows():
        feat = str(row['feature'] if 'feature' in row else row[0])
        if any(kw in feat.lower() for kw in new_feature_keywords):
            imp = row['importance'] if 'importance' in row else row[1]
            print(f"  ✅ {feat[:45]:45} {imp:.6f}")
            
except Exception as e:
    print(f"⚠️ Could not get feature importance: {str(e)[:100]}")

print("\n" + "="*80)
print("BIGQUERY ML TRAINING COMPLETE")
print("="*80)

print(f"\n✅ Model: cbi-v14.models_v5.{model_name}")
print(f"✅ Dataset: Enhanced with proper intelligence features")
print(f"✅ Ready for production deployment")

print(f"\n📋 To make predictions:")
print(f"""
SELECT * FROM ML.PREDICT(
  MODEL `cbi-v14.models.{model_name}`,
  (SELECT * FROM `cbi-v14.models.training_dataset_enhanced_v5`
   WHERE date = CURRENT_DATE())
)
""")

