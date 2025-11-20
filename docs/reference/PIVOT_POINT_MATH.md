---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# PURE PIVOT POINT MATHEMATICS — Databento-Based

**Status:** Production-ready, Databento-integrated  
**Purpose:** Calculate daily/weekly/monthly/quarterly pivot points for all symbols  
**Source:** `market_data.databento_futures_ohlcv_1d` (Databento daily OHLCV)

---

## ARCHITECTURE

### B1) BigQuery Schema

**View:** `curated.vw_ohlcv_daily`
- Source: `market_data.databento_futures_ohlcv_1d`
- Columns: `date`, `symbol`, `open`, `high`, `low`, `close`, `volume`
- **Updated:** Uses Databento directly (no Yahoo/Alpha fallback)

**Table:** `features.pivot_math_daily`
- One record per symbol per day
- Includes daily, weekly, monthly pivots
- Pure math features (distances, confluence, signals)

### B2) Cloud Function (Gen-2)

**File:** `scripts/features/cloud_function_pivot_calculator.py`
- **Updated:** Uses Databento view instead of Yahoo/Alpha
- Runs daily via Cloud Scheduler
- Calculates all pivot levels and features

**Deploy:**
```bash
gcloud functions deploy compute_pivots \
  --gen2 --region=us-central1 --runtime=python311 --entry-point=handler \
  --memory=512Mi --timeout=120 --trigger-http --no-allow-unauthenticated \
  --set-env-vars="BQ_PROJECT=cbi-v14,SRC_VIEW=cbi-v14.curated.vw_ohlcv_daily,DST_TABLE=cbi-v14.features.pivot_math_daily"
```

**Schedule:** Daily at 05:40 UTC (after market close)

### B3) Mac Feature Import

**File:** `scripts/features/pivot_feature_import.py`
- Imports pivot features from BigQuery
- Renames to `feat_pivot_*` convention
- Merges into local features DataFrame

---

## PIVOT FORMULAS

### Daily Pivots (Standard Formula)

```
P = (H + L + C) / 3
R1 = 2P - L
S1 = 2P - H
R2 = P + (H - L)
S2 = P - (H - L)
R3 = H + 2(P - L)
S3 = L - 2(H - P)
R4 = H + 3(H - L)
S4 = L - 3(H - P)
```

**Midpoints:**
```
M1 = (P + R1) / 2
M2 = (R1 + R2) / 2
M3 = (R2 + R3) / 2
M4 = (R3 + R4) / 2
M5 = (P + S1) / 2
M6 = (S1 + S2) / 2
M7 = (S2 + S3) / 2
M8 = (S3 + S4) / 2
```

### Weekly/Monthly Pivots

Same formula, applied to completed week/month ranges:
- **Weekly:** Prior completed week (Mon-Sun) H, L, C
- **Monthly:** Prior completed calendar month H, L, C

---

## FEATURE NAMING

All features use `feat_pivot_*` prefix:

| Original Column | Feature Name | Description |
|----------------|--------------|-------------|
| `distance_to_P` | `feat_pivot_dP` | Distance to daily pivot |
| `distance_to_R1` | `feat_pivot_dR1` | Distance to R1 resistance |
| `distance_to_S1` | `feat_pivot_dS1` | Distance to S1 support |
| `distance_to_R2` | `feat_pivot_dR2` | Distance to R2 resistance |
| `distance_to_S2` | `feat_pivot_dS2` | Distance to S2 support |
| `distance_to_R3` | `feat_pivot_dR3` | Distance to R3 resistance |
| `distance_to_S3` | `feat_pivot_dS3` | Distance to S3 support |
| `distance_to_nearest_pivot` | `feat_pivot_dNearest` | Distance to nearest pivot level |
| `weekly_pivot_distance` | `feat_weekly_pivot_dP` | Distance to weekly pivot |
| `monthly_pivot_distance` | `feat_monthly_pivot_dP` | Distance to monthly pivot |
| `pivot_confluence_count` | `feat_pivot_conf_count` | Number of pivots within ±1.0¢ (ZL only) |
| `pivot_zone_strength` | `feat_pivot_zone_strength` | Zone strength (1-5) |
| `price_above_P` | `feat_price_above_P` | Boolean: price above daily pivot |
| `price_between_R1_R2` | `feat_between_R1_R2` | Boolean: price between R1 and R2 |
| `price_between_S1_P` | `feat_between_S1_P` | Boolean: price between S1 and P |
| `price_rejected_R1_twice` | `feat_reject_R1_twice` | Signal: R1 rejection pattern |
| `price_bouncing_off_S1` | `feat_bounce_S1` | Signal: S1 bounce pattern |
| `price_stuck_between_R1_S1_for_3_days` | `feat_stuck_R1_S1_3d` | Signal: consolidation pattern |
| `weekly_pivot_flip` | `feat_weekly_flip` | Signal: weekly pivot flip |
| `pivot_confluence_3_or_higher` | `feat_conf_3_plus` | Signal: high confluence |

---

## INITIAL FEATURE IMPORTANCE (Seed Order)

Based on ZL/FCPO/USDBRL commodity experiments (2020–2025), practical starting order:

1. `feat_pivot_dNearest` - Distance to nearest pivot (most predictive)
2. `feat_pivot_dP` - Distance to daily pivot
3. `feat_between_R1_R2` - Price between R1/R2 zone
4. `feat_weekly_pivot_dP` - Weekly pivot distance
5. `feat_monthly_pivot_dP` - Monthly pivot distance
6. `feat_pivot_conf_count` - Confluence count
7. `feat_pivot_zone_strength` - Zone strength
8. `feat_price_above_P` - Above/below pivot
9. `feat_pivot_dR1` - R1 distance
10. `feat_pivot_dS1` - S1 distance
11. `feat_reject_R1_twice` - R1 rejection signal
12. `feat_bounce_S1` - S1 bounce signal
13. `feat_weekly_flip` - Weekly flip signal
14. `feat_stuck_R1_S1_3d` - Consolidation signal
15. `feat_pivot_dR2` - R2 distance
16. `feat_pivot_dS2` - S2 distance
17. `feat_pivot_dR3` - R3 distance
18. `feat_pivot_dS3` - S3 distance

**Note:** Training pipeline should recompute and persist true SHAP ranks on first run.

---

## CHANGES FROM YAHOO/ALPHA VERSION

1. **View Source:** Changed from `features.master_features` (Yahoo/Alpha COALESCE) to `market_data.databento_futures_ohlcv_1d` directly
2. **Column Names:** No prefix needed (Databento columns are `open`, `high`, `low`, `close`, `volume`)
3. **Symbol Support:** Added `MES=F` to default symbols list
4. **Data Quality:** Uses `QUALIFY ROW_NUMBER()` to handle duplicate timestamps

---

## USAGE

### In Training Pipeline

```python
from scripts.features.pivot_feature_import import pv

# Merge pivot features into features DataFrame
features_df = features_df.merge(pv, on=["date", "symbol"], how="left")
```

### In BigQuery Queries

```sql
SELECT 
  p.*,
  f.*
FROM `cbi-v14.features.pivot_math_daily` p
LEFT JOIN `cbi-v14.features.master_features` f
  ON p.date = f.date AND p.symbol = f.symbol
WHERE p.symbol = 'ZL=F'
ORDER BY p.date DESC
```

---

**Last Updated:** November 19, 2025  
**Status:** Production-ready, Databento-integrated  
**Reference:** Pure pivot point mathematics with no visual components

