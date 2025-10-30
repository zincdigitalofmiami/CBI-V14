#!/usr/bin/env python3
"""
Materialize ALL feature views to avoid correlated subquery issues
"""
from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("MATERIALIZING ALL FEATURE VIEWS")
print("="*80)
print(f"Start Time: {datetime.now().isoformat()}\n")

# List of all views to materialize
feature_views = [
    ('neural', 'vw_big_eight_signals', 'big_eight_signals_v1'),
    ('models', 'vw_correlation_features', 'correlation_features_v1'),
    ('models', 'vw_seasonality_features', 'seasonality_features_v1'),
    ('models', 'vw_crush_margins', 'crush_margins_v1'),
    ('models', 'vw_china_import_tracker', 'china_import_tracker_v1'),
    ('models', 'vw_brazil_export_lineup', 'brazil_export_lineup_v1'),
    ('models', 'vw_trump_xi_volatility', 'trump_xi_volatility_v1'),
    ('signals', 'vw_trade_war_impact', 'trade_war_impact_v1'),
    ('models', 'vw_event_driven_features', 'event_driven_features_v1'),
    ('models', 'vw_cross_asset_lead_lag', 'cross_asset_lead_lag_v1')
]

total = len(feature_views)
success_count = 0
failed = []

for idx, (dataset, view_name, table_name) in enumerate(feature_views, 1):
    print(f"\n[{idx}/{total}] Materializing {dataset}.{view_name} → staging_ml.{table_name}")
    
    query = f"""
    CREATE OR REPLACE TABLE `cbi-v14.staging_ml.{table_name}`
    PARTITION BY DATE_TRUNC(date, MONTH)
    CLUSTER BY date
    OPTIONS(
        description="Materialized from {dataset}.{view_name} - Version 1",
        labels=[("source_view", "{view_name}"), ("version", "v1"), ("environment", "staging")]
    )
    AS
    SELECT * FROM `cbi-v14.{dataset}.{view_name}`
    WHERE date IS NOT NULL
    """
    
    try:
        job = client.query(query)
        result = job.result()
        
        # Get row count
        count_query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.staging_ml.{table_name}`"
        row_count = list(client.query(count_query).result())[0].cnt
        
        print(f"   ✅ Success - {row_count:,} rows")
        success_count += 1
        
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:100]}")
        failed.append((dataset, view_name, str(e)))

print("\n" + "="*80)
print(f"MATERIALIZATION COMPLETE: {success_count}/{total} succeeded")
print("="*80)

if failed:
    print("\n⚠️  Failed views:")
    for dataset, view, error in failed:
        print(f"   - {dataset}.{view}: {error[:80]}")
else:
    print("\n✅ All feature views materialized successfully!")












