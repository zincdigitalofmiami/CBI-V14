# CBI-V14 Ingestion Pipeline Flow Analysis
**Date:** November 12, 2025  
**Last Reviewed:** November 14, 2025  
**Purpose:** Document complete data flow and identify automation gaps

**Note**: BQML deprecated - training now runs locally on Mac M4 via TensorFlow Metal.

---

## Current Data Flow (As Implemented)

### Step 1: Automated Ingestion (Cron → BigQuery)
```
Mac M4 External Drive (Always On)
  ├── Cron Jobs (32 automated, see scripts/crontab_setup.sh)
  │   ├── Daily: Weather, prices, volatility, RIN, Baltic, Argentina
  │   ├── Every 4-6 hours: Social intel, ScrapeCreators, Trump, GDELT
  │   ├── Weekly: CFTC, USDA, EIA, EPA RFS
  │   └── Monthly: China imports, ENSO climate
  │
  └── Ingestion Scripts (src/ingestion/*.py)
      ├── Fetch data from APIs/web sources
      ├── Validate and transform data
      └── Upload to BigQuery Cloud ✅ AUTOMATED
      
      ↓ (Network upload)
      
BigQuery Cloud (cbi-v14 project)
  └── Raw Tables (forecasting_data_warehouse)
      ├── cftc_cot (updated weekly)
      ├── economic_indicators (updated daily)
      ├── weather_data (updated daily)
      ├── freight_logistics (updated daily)
      ├── biofuel_prices (updated daily)
      └── [50+ other tables]
```

**Status:** ✅ FULLY AUTOMATED via cron

---

## Step 2: Data Processing (BigQuery → Training Tables)

```
BigQuery Cloud
  ├── Raw Tables (forecasting_data_warehouse)
  │   
  │   ↓ (SQL JOINs, feature engineering)
  │   
  └── Training Tables (models_v4)
      ├── production_training_data_1w
      ├── production_training_data_1m
      ├── production_training_data_3m
      ├── production_training_data_6m
      └── production_training_data_12m
```

**Status:** ⚠️ **MANUAL** - SQL scripts in `config/bigquery/bigquery-sql/` must be run manually

**Scripts:**
- `config/bigquery/bigquery-sql/PRODUCTION_HORIZON_SPECIFIC/CREATE_PRODUCTION_TRAINING_*.sql`

---

## Step 3: Export to Parquet & Local Training

```
BigQuery Cloud (models_v4 training tables)
  
  ↓ (Manual: python3 scripts/export_training_data.py)
  
External Drive: TrainingData/exports/ (Parquet files)
  
  ↓ (Local Mac M4 Training: TensorFlow Metal LSTM/GRU)
  
Local Models (Mac M4)
  
  ↓ (Upload predictions: python3 scripts/upload_predictions.py)
  
BigQuery Predictions Tables (for dashboard)
```

**Status:** ⚠️ **PARTIALLY AUTOMATED** - Export and training are manual, predictions upload can be automated

---

## 🚨 IDENTIFIED GAP: No Auto-Export

### Current State

**What IS automated:**
- ✅ Data ingestion (cron → BigQuery)
- ✅ Data validation and upload

**What is NOT automated:**
- ❌ BigQuery → External Drive export
- ❌ Training table refresh
- ❌ Local model retraining

### The Problem

When cron jobs ingest fresh data (daily/weekly):
1. Data goes to BigQuery ✅
2. Training tables are NOT updated automatically ❌
3. External drive Parquet files are NOT refreshed ❌
4. Local models train on STALE data ❌

**Example Timeline:**
- Day 1: Export training data (1,404 rows)
- Day 2: Cron ingests fresh data → BigQuery (now 1,405 rows)
- Day 3-7: More fresh data → BigQuery (now 1,450 rows)
- **Training still uses Day 1 export (1,404 rows) - 46 rows behind!**

---

## Proposed Solutions

### Option 1: Weekly Auto-Export (Recommended)

Add to cron schedule:

```bash
# Weekly training data export (Sunday 3 AM)
0 3 * * 0 cd /Users/kirkmusick/Documents/GitHub/CBI-V14 && python3 scripts/export_training_data.py >> Logs/cron/training_export.log 2>&1
```

**Pros:**
- Simple, low overhead
- Training data refreshed weekly
- Captures all week's ingestion

**Cons:**
- Still up to 7 days stale
- Doesn't update training tables (just exports existing)

---

### Option 2: Weekly Rebuild + Export (Better)

```bash
# Weekly: Rebuild training tables + export (Sunday 2 AM)
0 2 * * 0 cd /Users/kirkmusick/Documents/GitHub/CBI-V14 && python3 scripts/rebuild_and_export_training_data.py >> Logs/cron/training_rebuild.log 2>&1
```

This script would:
1. Rebuild training tables in BigQuery (run SQL)
2. Export fresh Parquet files to external drive
3. Log row counts and changes

**Pros:**
- Training tables stay fresh
- External drive stays fresh
- One-step automation

**Cons:**
- Requires new script
- Longer runtime (~5-10 minutes)
- BigQuery costs (~$0.10/week)

---

### Option 3: On-Demand Export Before Training (Manual)

No cron automation, but enforce workflow:

```bash
# Before training, always run:
python3 scripts/export_training_data.py
python3 src/training/train_model.py
```

**Pros:**
- No overhead when not training
- Always uses latest data
- No BigQuery costs until needed

**Cons:**
- Easy to forget
- Manual step required
- Data not immediately available

---

### Option 4: Event-Driven Export (Advanced)

Use BigQuery scheduled queries to trigger export when data changes:

```sql
-- BigQuery Scheduled Query (runs daily)
-- If new data detected, trigger Cloud Function → export script
```

**Pros:**
- Only exports when needed
- Near real-time freshness
- Efficient

**Cons:**
- Complex setup
- Requires Cloud Functions
- Network overhead

---

## Recommended Implementation

### Phase 1: Weekly Auto-Export (Immediate)

Add to `scripts/crontab_setup.sh`:

```bash
# Weekly training data refresh (Sunday 3 AM - after weekend maintenance)
0 3 * * 0 cd $REPO_ROOT && ${ENV_SOURCE}${PYTHON_BIN} scripts/export_training_data.py >> $LOG_DIR/training_export.log 2>&1
```

This ensures:
- Fresh data exported weekly
- External drive stays current
- Minimal overhead
- No additional costs

### Phase 2: Pre-Training Check (Best Practice)

Create wrapper script: `scripts/train_with_fresh_data.sh`

```bash
#!/bin/bash
# Ensures fresh data before training

echo "📊 Checking data freshness..."
python3 scripts/export_training_data.py

echo "🧠 Starting training..."
python3 src/training/train_model.py "$@"
```

---

## Data Freshness Strategy

### For Daily Cron Ingestion

| Data Source | Ingestion Frequency | Export Frequency | Acceptable Lag |
|-------------|---------------------|------------------|----------------|
| Weather, Prices | Daily | Weekly | 7 days OK |
| Social Intel | 4-6 hours | Weekly | 7 days OK |
| CFTC, USDA | Weekly | Weekly | Synchronized |
| China Imports | Monthly | Weekly | Synchronized |

**Rationale:** Training doesn't need daily updates. Weekly refresh captures all ingestion while minimizing overhead.

---

## Proposed Cron Addition

Add this line to `scripts/crontab_setup.sh` in the MAINTENANCE section:

```bash
# --------------------------------------------------------------------
# WEEKLY TRAINING DATA REFRESH
# --------------------------------------------------------------------
# Export fresh training data (Sunday 3 AM - after weekend maintenance)
0 3 * * 0 cd $REPO_ROOT && ${ENV_SOURCE}${PYTHON_BIN} scripts/export_training_data.py >> $LOG_DIR/training_export.log 2>&1
```

This runs:
- **When:** Every Sunday at 3 AM
- **After:** Weekend maintenance (runs at 2 AM Sunday)
- **Duration:** ~2-3 minutes
- **Cost:** $0 (just exports from BigQuery)
- **Result:** Fresh Parquet files for training

---

## Impact Analysis

### Without Auto-Export (Current)

```
Week 1: Export manually → 1,404 rows
Week 2: Cron adds 50 rows → BigQuery has 1,454, but exports still 1,404
Week 3: Cron adds 50 rows → BigQuery has 1,504, but exports still 1,404
Week 4: Cron adds 50 rows → BigQuery has 1,554, but exports still 1,404

Result: Training on data that's 150 rows (1 month) stale
```

### With Weekly Auto-Export (Proposed)

```
Week 1: Auto-export → 1,404 rows
Week 2: Cron adds 50 rows → Auto-export → 1,454 rows
Week 3: Cron adds 50 rows → Auto-export → 1,504 rows
Week 4: Cron adds 50 rows → Auto-export → 1,554 rows

Result: Training on data that's max 7 days old
```

---

## Verification Checklist

After implementing auto-export:

- [ ] Weekly export runs successfully
- [ ] Log file created at `Logs/cron/training_export.log`
- [ ] Parquet files updated in `TrainingData/exports/`
- [ ] File timestamps show weekly refresh
- [ ] Row counts increase with new ingestion
- [ ] No errors in export log

---

## Conclusion

**Gap Identified:** ✅ YES - No automation between cron ingestion and training data export

**Impact:** Training data can become weeks/months stale

**Solution:** Add weekly auto-export to cron schedule

**Effort:** 5 minutes (add 1 line to crontab_setup.sh)

**Benefit:** Always-fresh training data, zero manual intervention

**Recommendation:** Implement immediately

---

## Next Steps

1. **Add weekly export to cron** (1 line in `crontab_setup.sh`)
2. **Reinstall cron** (`bash scripts/crontab_setup.sh`)
3. **Verify next Sunday** (check log and file timestamps)
4. **Create wrapper script** for pre-training export (best practice)

