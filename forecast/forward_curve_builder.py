#!/usr/bin/env python3
"""
Forward Curve Builder - Linear Interpolation Between Forecast Horizons
Generates smooth daily price curve from 0-180 days using V3 models
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚀 FORWARD CURVE BUILDER - LINEAR INTERPOLATION")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

print("📊 Building continuous forward curve from V3 model forecasts")
print("   - Anchor points: Current, 1W (7d), 1M (30d), 3M (90d), 6M (180d)")
print("   - Method: Linear interpolation between anchor points")
print("   - Output: 181 daily price points (0-180 days)")
print()

# Get current price and all V3 forecasts
print("🔍 Fetching V3 forecast anchor points...")

anchor_query = """
WITH latest_data AS (
    SELECT zl_price_current as current_price
    FROM `cbi-v14.models.training_dataset`
    ORDER BY date DESC
    LIMIT 1
),
forecasts AS (
    SELECT 
        0 AS days,
        'current' AS horizon,
        current_price AS price
    FROM latest_data
    
    UNION ALL
    
    SELECT 
        7 AS days,
        '1w' AS horizon,
        pred.predicted_target_1w AS price
    FROM ML.PREDICT(
        MODEL `cbi-v14.models.zl_boosted_tree_1w_v3`,
        (SELECT * EXCEPT(date) FROM `cbi-v14.models.training_dataset` ORDER BY date DESC LIMIT 1)
    ) pred
    
    UNION ALL
    
    SELECT 
        30 AS days,
        '1m' AS horizon,
        pred.predicted_target_1m AS price
    FROM ML.PREDICT(
        MODEL `cbi-v14.models.zl_boosted_tree_1m_v3`,
        (SELECT * EXCEPT(date) FROM `cbi-v14.models.training_dataset` ORDER BY date DESC LIMIT 1)
    ) pred
    
    UNION ALL
    
    SELECT 
        90 AS days,
        '3m' AS horizon,
        pred.predicted_target_3m AS price
    FROM ML.PREDICT(
        MODEL `cbi-v14.models.zl_boosted_tree_3m_v3`,
        (SELECT * EXCEPT(date) FROM `cbi-v14.models.training_dataset` ORDER BY date DESC LIMIT 1)
    ) pred
    
    UNION ALL
    
    SELECT 
        180 AS days,
        '6m' AS horizon,
        pred.predicted_target_6m AS price
    FROM ML.PREDICT(
        MODEL `cbi-v14.models.zl_boosted_tree_6m_v3`,
        (SELECT * EXCEPT(date) FROM `cbi-v14.models.training_dataset` ORDER BY date DESC LIMIT 1)
    ) pred
)
SELECT * FROM forecasts ORDER BY days
"""

try:
    anchors_df = client.query(anchor_query).to_dataframe()
    
    print("\n✅ Anchor Points Retrieved:")
    for _, row in anchors_df.iterrows():
        print(f"   {row['horizon']:8} (Day {row['days']:3}): ${row['price']:.2f}")
    
    # Build interpolated curve
    print("\n🔄 Building interpolated curve (181 daily points)...")
    
    # Extract anchor prices
    price_current = float(anchors_df[anchors_df['days'] == 0]['price'].iloc[0])
    price_1w = float(anchors_df[anchors_df['days'] == 7]['price'].iloc[0])
    price_1m = float(anchors_df[anchors_df['days'] == 30]['price'].iloc[0])
    price_3m = float(anchors_df[anchors_df['days'] == 90]['price'].iloc[0])
    price_6m = float(anchors_df[anchors_df['days'] == 180]['price'].iloc[0])
    
    # Linear interpolation
    curve = []
    today = datetime.now().date()
    
    for day_num in range(181):
        target_date = today + timedelta(days=day_num)
        
        # Determine which segment and interpolate
        if day_num <= 7:
            # Current to 1W
            ratio = day_num / 7.0
            price = price_current + (price_1w - price_current) * ratio
        elif day_num <= 30:
            # 1W to 1M
            ratio = (day_num - 7) / 23.0
            price = price_1w + (price_1m - price_1w) * ratio
        elif day_num <= 90:
            # 1M to 3M
            ratio = (day_num - 30) / 60.0
            price = price_1m + (price_3m - price_1m) * ratio
        else:
            # 3M to 6M
            ratio = (day_num - 90) / 90.0
            price = price_3m + (price_6m - price_3m) * ratio
        
        curve.append({
            'day_number': day_num,
            'target_date': target_date.strftime('%Y-%m-%d'),
            'forward_price': round(price, 2),
            'days_from_now': day_num
        })
    
    curve_df = pd.DataFrame(curve)
    
    print(f"✅ Curve built: {len(curve_df)} daily points")
    print(f"\n📊 Curve Statistics:")
    print(f"   Start (Day 0):   ${curve_df['forward_price'].iloc[0]:.2f}")
    print(f"   End (Day 180):   ${curve_df['forward_price'].iloc[-1]:.2f}")
    print(f"   Min Price:       ${curve_df['forward_price'].min():.2f}")
    print(f"   Max Price:       ${curve_df['forward_price'].max():.2f}")
    print(f"   Price Change:    ${curve_df['forward_price'].iloc[-1] - curve_df['forward_price'].iloc[0]:.2f}")
    print(f"   % Change:        {((curve_df['forward_price'].iloc[-1] / curve_df['forward_price'].iloc[0]) - 1) * 100:.2f}%")
    
    # Save to BigQuery for API access
    print(f"\n💾 Saving curve to BigQuery...")
    
    table_id = 'cbi-v14.models_v4.forward_curve_v3'
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        schema=[
            bigquery.SchemaField("day_number", "INTEGER"),
            bigquery.SchemaField("target_date", "DATE"),
            bigquery.SchemaField("forward_price", "FLOAT64"),
            bigquery.SchemaField("days_from_now", "INTEGER"),
        ],
    )
    
    # Convert target_date to datetime for BigQuery DATE type
    curve_df['target_date'] = pd.to_datetime(curve_df['target_date'])
    
    job = client.load_table_from_dataframe(curve_df, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Forward curve saved to: {table_id}")
    print(f"   Rows loaded: {len(curve_df)}")
    
    # Sample key points
    print(f"\n📈 Sample Points:")
    sample_days = [0, 7, 30, 90, 180]
    for day in sample_days:
        row = curve_df[curve_df['day_number'] == day].iloc[0]
        print(f"   Day {day:3}: {row['target_date']:%Y-%m-%d} → ${row['forward_price']:.2f}")
    
    print("\n" + "=" * 80)
    print("✅ FORWARD CURVE GENERATION COMPLETE")
    print("=" * 80)
    print(f"\n💡 API Integration:")
    print(f"   Query: SELECT * FROM `{table_id}` ORDER BY day_number")
    print(f"   Endpoint: /api/v4/forward-curve")
    print(f"   Returns: 181 daily price forecasts (0-180 days)")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

