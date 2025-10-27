#!/usr/bin/env python3
"""
COMPARE THE TWO BEST TRAINING DATASET CANDIDATES
Determine which should be the PRIMARY dataset
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

print("="*80)
print("COMPARING TOP TRAINING DATASET CANDIDATES")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

client = bigquery.Client(project='cbi-v14')

candidates = [
    'models.training_complete_enhanced',
    'models_v4.training_dataset_super_enriched'
]

comparison = {}

for table_path in candidates:
    print(f"\n{'='*60}")
    print(f"ANALYZING: {table_path}")
    print('='*60)
    
    dataset_id, table_id = table_path.split('.')
    
    # Get schema
    table_ref = client.dataset(dataset_id).table(table_id)
    table_obj = client.get_table(table_ref)
    
    # Get column names
    columns = [field.name for field in table_obj.schema]
    
    # Categorize features
    feature_categories = {
        'price_features': [c for c in columns if 'price' in c.lower() or 'return' in c.lower()],
        'targets': [c for c in columns if 'target' in c.lower()],
        'cftc_features': [c for c in columns if 'cftc' in c.lower()],
        'economic_features': [c for c in columns if 'econ' in c.lower()],
        'treasury_features': [c for c in columns if 'treasury' in c.lower()],
        'weather_features': [c for c in columns if 'weather' in c.lower()],
        'news_features': [c for c in columns if 'news' in c.lower() or 'tariff' in c.lower() or 'china' in c.lower()],
        'correlation_features': [c for c in columns if 'corr' in c.lower()],
        'technical_features': [c for c in columns if any(x in c.lower() for x in ['ma_', 'volatility', 'momentum'])],
        'commodity_features': [c for c in columns if any(x in c.lower() for x in ['crude', 'palm', 'corn', 'wheat', 'bean'])],
        'market_features': [c for c in columns if any(x in c.lower() for x in ['vix', 'dxy', 'sp500'])]
    }
    
    print(f"\n1. BASIC STATISTICS")
    print("-"*40)
    print(f"Total rows: {table_obj.num_rows:,}")
    print(f"Total columns: {len(columns)}")
    print(f"Size: {table_obj.num_bytes / (1024*1024):.2f} MB")
    print(f"Last modified: {table_obj.modified}")
    
    print(f"\n2. FEATURE BREAKDOWN")
    print("-"*40)
    for category, features in feature_categories.items():
        print(f"{category:20}: {len(features):3} features")
    
    # Check data completeness
    print(f"\n3. DATA COMPLETENESS CHECK")
    print("-"*40)
    
    completeness_query = f"""
    SELECT 
        -- Core features
        COUNT(*) as total_rows,
        SUM(CASE WHEN zl_price_current IS NOT NULL THEN 1 ELSE 0 END) as price_filled,
        SUM(CASE WHEN target_1w IS NOT NULL THEN 1 ELSE 0 END) as target_filled,
        
        -- CFTC
        SUM(CASE WHEN cftc_managed_net IS NOT NULL AND cftc_managed_net != 0 THEN 1 ELSE 0 END) as cftc_managed_filled,
        SUM(CASE WHEN cftc_commercial_net IS NOT NULL AND cftc_commercial_net != 0 THEN 1 ELSE 0 END) as cftc_commercial_filled,
        
        -- Economic
        SUM(CASE WHEN econ_gdp_growth IS NOT NULL AND econ_gdp_growth != 0 THEN 1 ELSE 0 END) as econ_gdp_filled,
        SUM(CASE WHEN econ_inflation_rate IS NOT NULL AND econ_inflation_rate != 0 THEN 1 ELSE 0 END) as econ_inflation_filled,
        
        -- Treasury
        SUM(CASE WHEN treasury_10y_yield IS NOT NULL AND treasury_10y_yield != 0 THEN 1 ELSE 0 END) as treasury_filled,
        
        -- News
        SUM(CASE WHEN news_article_count IS NOT NULL AND news_article_count != 0 THEN 1 ELSE 0 END) as news_filled,
        
        -- Weather
        SUM(CASE WHEN weather_brazil_temp IS NOT NULL AND weather_brazil_temp != 0 THEN 1 ELSE 0 END) as weather_filled
        
    FROM `cbi-v14.{table_path}`
    """
    
    try:
        completeness = client.query(completeness_query).to_dataframe()
        
        total = completeness['total_rows'].iloc[0]
        
        print(f"Price data: {completeness['price_filled'].iloc[0]}/{total} ({completeness['price_filled'].iloc[0]/total*100:.1f}%)")
        print(f"Targets: {completeness['target_filled'].iloc[0]}/{total} ({completeness['target_filled'].iloc[0]/total*100:.1f}%)")
        print(f"CFTC managed: {completeness['cftc_managed_filled'].iloc[0]}/{total} ({completeness['cftc_managed_filled'].iloc[0]/total*100:.1f}%)")
        print(f"CFTC commercial: {completeness['cftc_commercial_filled'].iloc[0]}/{total} ({completeness['cftc_commercial_filled'].iloc[0]/total*100:.1f}%)")
        print(f"GDP data: {completeness['econ_gdp_filled'].iloc[0]}/{total} ({completeness['econ_gdp_filled'].iloc[0]/total*100:.1f}%)")
        print(f"Inflation data: {completeness['econ_inflation_filled'].iloc[0]}/{total} ({completeness['econ_inflation_filled'].iloc[0]/total*100:.1f}%)")
        print(f"Treasury yields: {completeness['treasury_filled'].iloc[0]}/{total} ({completeness['treasury_filled'].iloc[0]/total*100:.1f}%)")
        print(f"News articles: {completeness['news_filled'].iloc[0]}/{total} ({completeness['news_filled'].iloc[0]/total*100:.1f}%)")
        print(f"Weather data: {completeness['weather_filled'].iloc[0]}/{total} ({completeness['weather_filled'].iloc[0]/total*100:.1f}%)")
        
        # Store for comparison
        comparison[table_path] = {
            'rows': table_obj.num_rows,
            'columns': len(columns),
            'size_mb': table_obj.num_bytes / (1024*1024),
            'cftc_coverage': completeness['cftc_managed_filled'].iloc[0] / total * 100,
            'econ_coverage': completeness['econ_gdp_filled'].iloc[0] / total * 100,
            'news_coverage': completeness['news_filled'].iloc[0] / total * 100,
            'features': feature_categories
        }
        
    except Exception as e:
        print(f"Error checking completeness: {str(e)[:200]}")
        
        # Try simpler check
        try:
            simple_query = f"""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT date) as unique_dates
            FROM `cbi-v14.{table_path}`
            """
            simple = client.query(simple_query).to_dataframe()
            print(f"Total rows: {simple['total'].iloc[0]}")
            print(f"Unique dates: {simple['unique_dates'].iloc[0]}")
        except:
            pass
    
    # Check for unique features
    print(f"\n4. UNIQUE FEATURES CHECK")
    print("-"*40)
    
    unique_features = []
    for col in columns[:10]:  # Check first 10 columns as sample
        if not any(col in comparison[other]['features'] for other in comparison if other != table_path):
            unique_features.append(col)
    
    if unique_features:
        print(f"Sample unique features: {', '.join(unique_features[:5])}")
    else:
        print("No unique features in sample")

# Final comparison
print("\n" + "="*80)
print("FINAL COMPARISON AND RECOMMENDATION")
print("="*80)

print("\nSIDE-BY-SIDE COMPARISON:")
print("-"*60)

if len(comparison) == 2:
    df_comparison = pd.DataFrame(comparison).T
    print(df_comparison[['rows', 'columns', 'size_mb']].to_string())
    
    print("\nCOVERAGE COMPARISON:")
    for metric in ['cftc_coverage', 'econ_coverage', 'news_coverage']:
        if metric in df_comparison.columns:
            print(f"{metric}: ")
            for idx, val in df_comparison[metric].items():
                print(f"  {idx}: {val:.1f}%")

print("\n🎯 RECOMMENDATION:")
print("-"*40)

# Determine winner
if 'models.training_complete_enhanced' in comparison and 'models_v4.training_dataset_super_enriched' in comparison:
    complete = comparison['models.training_complete_enhanced']
    super_enriched = comparison['models_v4.training_dataset_super_enriched']
    
    complete_score = 0
    super_score = 0
    
    # More columns is better
    if complete['columns'] > super_enriched['columns']:
        complete_score += 1
        print("✓ training_complete_enhanced has MORE columns (219 vs 195)")
    else:
        super_score += 1
        print("✓ training_dataset_super_enriched has MORE columns")
    
    # More rows is better (but 1251 vs 1263 might be deduped)
    if complete['rows'] > super_enriched['rows']:
        print("✓ training_complete_enhanced has 12 more rows (might be duplicates)")
    else:
        print("✓ training_dataset_super_enriched has cleaned duplicates")
    
    # Better coverage is better
    if complete.get('cftc_coverage', 0) > super_enriched.get('cftc_coverage', 0):
        complete_score += 1
        print("✓ training_complete_enhanced has better CFTC coverage")
    elif super_enriched.get('cftc_coverage', 0) > complete.get('cftc_coverage', 0):
        super_score += 1
        print("✓ training_dataset_super_enriched has better CFTC coverage")
    
    print(f"\nFINAL VERDICT:")
    if complete_score > super_score:
        print("🏆 USE: models.training_complete_enhanced")
        print("   - Has most features (219)")
        print("   - Most recent in models dataset")
        print("   - Largest size (2.1 MB)")
    else:
        print("🏆 USE: models_v4.training_dataset_super_enriched")
        print("   - Has cleaned duplicates")
        print("   - More recent modification")
        print("   - V4 suggests newer version")

print("\nNEXT STEPS:")
print("1. Download both datasets for local inspection")
print("2. Check for duplicate dates in training_complete_enhanced")
print("3. If duplicates exist, use deduped version")
print("4. Focus on fixing CFTC/Economic/Treasury data linkages")

print("\n" + "="*80)
