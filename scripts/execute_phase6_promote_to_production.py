#!/usr/bin/env python3
"""
PHASE 6: Promote to Production
"""
from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("PHASE 6: PROMOTING TO PRODUCTION")
print("="*80)
print(f"Start Time: {datetime.now().isoformat()}\n")

# Tables to promote
tables_to_promote = [
    ('price_features_v1', 'price_features_production_v1'),
    ('weather_features_v1', 'weather_features_production_v1'),
    ('sentiment_features_v1', 'sentiment_features_production_v1'),
    ('big_eight_signals_v1', 'big_eight_signals_production_v1'),
    ('correlation_features_v1', 'correlation_features_production_v1'),
    ('crush_margins_v1', 'crush_margins_production_v1'),
    ('china_import_tracker_v1', 'china_import_tracker_production_v1'),
    ('brazil_export_lineup_v1', 'brazil_export_lineup_production_v1'),
    ('trump_xi_volatility_v1', 'trump_xi_volatility_production_v1'),
    ('trade_war_impact_v1', 'trade_war_impact_production_v1'),
    ('event_driven_features_v1', 'event_driven_features_production_v1'),
    ('cross_asset_lead_lag_v1', 'cross_asset_lead_lag_production_v1'),
    ('training_dataset_v1', 'training_dataset_production_v1')
]

promoted_count = 0
failed = []

for staging_name, production_name in tables_to_promote:
    print(f"\nPromoting {staging_name} → models.{production_name}")
    
    # Clone staging table to production
    query = f"""
    CREATE OR REPLACE TABLE `cbi-v14.models.{production_name}`
    CLONE `cbi-v14.staging_ml.{staging_name}`
    """
    
    try:
        job = client.query(query)
        result = job.result()
        
        # Get row count
        count_query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.models.{production_name}`"
        row_count = list(client.query(count_query).result())[0].cnt
        
        print(f"   ✅ Promoted - {row_count:,} rows in production")
        promoted_count += 1
        
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:100]}")
        failed.append((staging_name, str(e)))

print("\n" + "="*80)
print(f"PROMOTION COMPLETE: {promoted_count}/{len(tables_to_promote)} succeeded")
print("="*80)

if failed:
    print("\n⚠️  Failed promotions:")
    for name, error in failed:
        print(f"   - {name}: {error[:80]}")
else:
    print("\n✅ All tables promoted to production successfully!")
    print("\n📊 Production Tables:")
    print("   - models.training_dataset_production_v1 (MAIN TRAINING TABLE)")
    print("   - models.price_features_production_v1")
    print("   - models.weather_features_production_v1")
    print("   - models.sentiment_features_production_v1")
    print("   - models.big_eight_signals_production_v1")
    print("   - models.correlation_features_production_v1")
    print("   - models.crush_margins_production_v1")
    print("   - models.china_import_tracker_production_v1")
    print("   - models.brazil_export_lineup_production_v1")
    print("   - models.trump_xi_volatility_production_v1")
    print("   - models.trade_war_impact_production_v1")
    print("   - models.event_driven_features_production_v1")
    print("   - models.cross_asset_lead_lag_production_v1")
    
    print("\n🎯 READY FOR MODEL TRAINING!")
    print("   Use: models.training_dataset_production_v1")














