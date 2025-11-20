"""
⚠️ CRITICAL: NO FAKE DATA ⚠️
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
"""

# B3) Mac run_once.py — pivot feature import
# Imports pivot features from BigQuery and merges into local features DataFrame

from google.cloud import bigquery
import pandas as pd

bq = bigquery.Client(project="cbi-v14")

# Fetch pivot math features
pv = bq.query("""
  SELECT 
    date, symbol,
    current_price,
    distance_to_P, distance_to_R1, distance_to_S1, 
    distance_to_R2, distance_to_S2, distance_to_R3, distance_to_S3,
    distance_to_nearest_pivot,
    nearest_pivot_type,
    price_above_P, price_between_R1_R2, price_between_S1_P,
    weekly_pivot_distance, monthly_pivot_distance,
    pivot_confluence_count, pivot_zone_strength,
    price_rejected_R1_twice, price_bouncing_off_S1,
    price_stuck_between_R1_S1_for_3_days,
    weekly_pivot_flip, pivot_confluence_3_or_higher
  FROM `cbi-v14.features.pivot_math_daily`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date, symbol ORDER BY last_updated DESC) = 1
""").to_dataframe()

# Rename columns to feature naming convention (feat_pivot_*)
pv = pv.rename(columns={
    "distance_to_P": "feat_pivot_dP",
    "distance_to_R1": "feat_pivot_dR1",
    "distance_to_S1": "feat_pivot_dS1",
    "distance_to_R2": "feat_pivot_dR2",
    "distance_to_S2": "feat_pivot_dS2",
    "distance_to_R3": "feat_pivot_dR3",
    "distance_to_S3": "feat_pivot_dS3",
    "distance_to_nearest_pivot": "feat_pivot_dNearest",
    "weekly_pivot_distance": "feat_weekly_pivot_dP",
    "monthly_pivot_distance": "feat_monthly_pivot_dP",
    "pivot_confluence_count": "feat_pivot_conf_count",
    "pivot_zone_strength": "feat_pivot_zone_strength",
    "price_above_P": "feat_price_above_P",
    "price_between_R1_R2": "feat_between_R1_R2",
    "price_between_S1_P": "feat_between_S1_P",
    "price_rejected_R1_twice": "feat_reject_R1_twice",
    "price_bouncing_off_S1": "feat_bounce_S1",
    "price_stuck_between_R1_S1_for_3_days": "feat_stuck_R1_S1_3d",
    "weekly_pivot_flip": "feat_weekly_flip",
    "pivot_confluence_3_or_higher": "feat_conf_3_plus",
})

# Example usage: merge into features DataFrame
# features_df = features_df.merge(pv, on=["date", "symbol"], how="left")

print(f"Loaded {len(pv)} pivot feature records")
print(f"Columns: {list(pv.columns)}")

