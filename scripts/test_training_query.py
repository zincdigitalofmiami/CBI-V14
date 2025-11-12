#!/usr/bin/env python3
"""
Test training query syntax and data validation without actually training
"""
from google.cloud import bigquery
import sys

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"

HORIZONS = [
    {'name': '1w', 'view': 'train_1w', 'target': 'target_1w'},
    {'name': '1m', 'view': 'train_1m', 'target': 'target_1m'},
    {'name': '3m', 'view': 'train_3m', 'target': 'target_3m'},
    {'name': '6m', 'view': 'train_6m', 'target': 'target_6m'},
]

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🧪 TESTING TRAINING QUERIES (Syntax & Data Validation)")
print("="*80)

all_passed = True

for horizon in HORIZONS:
    name = horizon['name']
    view = horizon['view']
    target = horizon['target']
    
    print(f"\n{'='*80}")
    print(f"Testing {name.upper()} horizon...")
    print(f"{'='*80}")
    
    # Test 1: Verify view query structure
    print(f"\n1️⃣  Testing view query structure...")
    try:
        query = f"""
        SELECT 
          COUNT(*) as row_count,
          COUNTIF({target} IS NOT NULL) as valid_targets,
          COUNTIF(date IS NOT NULL) as valid_dates,
          COUNTIF(date < '2024-12-01') as train_count,
          COUNTIF(date >= '2024-12-01') as eval_count
        FROM `{PROJECT_ID}.{DATASET_ID}.{view}`
        WHERE {target} IS NOT NULL
        """
        result = client.query(query).to_dataframe().iloc[0]
        
        print(f"  ✅ View query valid")
        print(f"     Rows: {int(result['row_count']):,}")
        print(f"     Valid targets: {int(result['valid_targets']):,}")
        print(f"     Valid dates: {int(result['valid_dates']):,}")
        print(f"     Train rows: {int(result['train_count']):,}")
        print(f"     Eval rows: {int(result['eval_count']):,}")
        
        if int(result['valid_dates']) < int(result['row_count']):
            print(f"  ⚠️  Some rows have NULL dates")
        
        if int(result['train_count']) == 0:
            print(f"  ❌ No training rows found")
            all_passed = False
        
        if int(result['eval_count']) == 0:
            print(f"  ⚠️  No eval rows found")
        
    except Exception as e:
        print(f"  ❌ View query failed: {str(e)[:200]}")
        all_passed = False
        continue
    
    # Test 2: Test data_split column creation
    print(f"\n2️⃣  Testing data_split column creation...")
    try:
        query = f"""
        SELECT 
          COUNT(*) as total,
          COUNTIF(IF(date < '2024-12-01', 'TRAIN', 'EVAL') = 'TRAIN') as train_count,
          COUNTIF(IF(date < '2024-12-01', 'TRAIN', 'EVAL') = 'EVAL') as eval_count,
          COUNTIF(IF(date < '2024-12-01', 'TRAIN', 'EVAL') IS NULL) as null_split
        FROM `{PROJECT_ID}.{DATASET_ID}.{view}`
        WHERE {target} IS NOT NULL
        """
        result = client.query(query).to_dataframe().iloc[0]
        
        print(f"  ✅ data_split column logic valid")
        print(f"     Total rows: {int(result['total']):,}")
        print(f"     TRAIN: {int(result['train_count']):,}")
        print(f"     EVAL: {int(result['eval_count']):,}")
        print(f"     NULL splits: {int(result['null_split']):,}")
        
        if int(result['null_split']) > 0:
            print(f"  ❌ Found {int(result['null_split'])} rows with NULL data_split")
            all_passed = False
        
    except Exception as e:
        print(f"  ❌ data_split test failed: {str(e)[:200]}")
        all_passed = False
        continue
    
    # Test 3: Test feature selection (excluding temporal leakage)
    print(f"\n3️⃣  Testing feature selection (EXCEPT clause)...")
    try:
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
        
        # Check if columns exist in view
        query = f"""
        SELECT column_name
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{view}'
        """
        columns = client.query(query).to_dataframe()['column_name'].values
        
        found_leakage = [f for f in temporal_leakage if f in columns]
        print(f"  📊 Found {len(found_leakage)}/{len(temporal_leakage)} temporal leakage features in view")
        
        if len(found_leakage) > 0:
            print(f"  ✅ View has temporal leakage (will be excluded in training SQL)")
        
        # Test EXCEPT query
        except_list = [
            'date',
            'treasury_10y_yield',
            'econ_gdp_growth',
            'econ_unemployment_rate',
            'news_article_count',
            'news_avg_score'
        ] + temporal_leakage
        
        # Create a test query with EXCEPT
        query = f"""
        SELECT 
          COUNT(*) as row_count,
          COUNT({target}) as target_count
        FROM (
          SELECT 
            * EXCEPT({', '.join(except_list)}),
            IF(date < '2024-12-01', 'TRAIN', 'EVAL') AS data_split
          FROM `{PROJECT_ID}.{DATASET_ID}.{view}`
          WHERE {target} IS NOT NULL
          LIMIT 10
        )
        """
        result = client.query(query).to_dataframe().iloc[0]
        
        print(f"  ✅ EXCEPT clause valid")
        print(f"     Test rows: {int(result['row_count']):,}")
        
    except Exception as e:
        error_str = str(e)
        print(f"  ❌ Feature selection test failed: {error_str[:300]}")
        
        # Check if it's a column name issue
        if 'not found' in error_str.lower() or 'unknown' in error_str.lower():
            print(f"     This suggests a column in EXCEPT doesn't exist - check SQL file")
        elif 'duplicate' in error_str.lower():
            print(f"     This suggests duplicate column names")
        
        all_passed = False
        continue
    
    # Test 4: Check for data type issues
    print(f"\n4️⃣  Testing data types...")
    try:
        query = f"""
        SELECT 
          column_name,
          data_type
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{view}'
        AND column_name = '{target}'
        """
        result = client.query(query).to_dataframe()
        
        if len(result) > 0:
            dtype = result.iloc[0]['data_type']
            print(f"  ✅ Target column type: {dtype}")
            
            if dtype not in ['FLOAT64', 'FLOAT', 'NUMERIC', 'INT64', 'INTEGER']:
                print(f"  ⚠️  Target type {dtype} may not be optimal for regression")
        else:
            print(f"  ❌ Target column not found")
            all_passed = False
        
    except Exception as e:
        print(f"  ⚠️  Data type check failed: {str(e)[:200]}")

print(f"\n{'='*80}")
print("📋 TEST SUMMARY")
print(f"{'='*80}")

if all_passed:
    print("✅ All tests passed - queries appear valid")
    print("\n✅ Ready to train models:")
    print("   Run: python3 scripts/execute_phase_1.py")
else:
    print("❌ Some tests failed - review errors above")
    print("\n⚠️  Fix issues before training")

print(f"{'='*80}")

sys.exit(0 if all_passed else 1)









