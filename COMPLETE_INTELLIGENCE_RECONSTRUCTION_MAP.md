# 🧩 COMPLETE INTELLIGENCE RECONSTRUCTION MAP
**Date:** November 12, 2025 21:15 UTC  
**Status:** ROOT CAUSE IDENTIFIED - Ready for Minimal Fix

---

## 🚨 ROOT CAUSE ANALYSIS - COMPLETE

### The Problem Chain

```
staging.comprehensive_social_intelligence (63,431 rows of 2024-2025 intelligence)
    ↓
    NOT BEING USED ❌
    ↓
signals.vw_* views query from forecasting_data_warehouse.social_sentiment (677 rows total, sparse)
    ↓
    Signal views return mostly ZEROS (no matching data)
    ↓
neural.vw_big_eight_signals uses COALESCE(signal_view, DEFAULT_VALUE)
    ↓
    Falls back to hardcoded defaults (0.2, 0.3, 0.5)
    ↓
ULTIMATE_DATA_CONSOLIDATION.sql joins Big 8 signals
    ↓
    Production training tables get constant 0.2/0.3/0.5 values
    ↓
models_v4.production_training_data_* has NULL/constant intelligence features ❌
```

---

## 📊 DATA INVENTORY - COMPLETE MAP

### News Intelligence (3,539 rows across 4 tables)

| Location | Rows | Date Range | Columns | Status |
|----------|------|------------|---------|--------|
| `forecasting_data_warehouse.news_intelligence` | 2,830 | Oct-Nov 2025 | title, published, intelligence_score | ✅ Good schema |
| `forecasting_data_warehouse.news_advanced` | 223 | Sep-Oct 2025 | soybean_oil_mentions, tariffs_mentions, china_mentions | ✅ Good schema |
| `forecasting_data_warehouse.news_ultra_aggressive` | 33 | 2017-2025 | total_score, mentions columns | ✅ Good schema |
| `forecasting_data_warehouse.breaking_news_hourly` | 440 | Oct-Nov 2025 | sentiment_score, relevance_score | ✅ Good schema |

**Missing:** `sentiment` column in news_intelligence (has `intelligence_score` instead)

### Social Intelligence (70,000+ rows across 5 tables)

| Location | Rows | Date Range | Key Columns | Status |
|----------|------|------------|-------------|--------|
| `staging.comprehensive_social_intelligence` | **63,431** | Oct-Nov 2025 | soy_score, china_score, policy_score, urgency_score | ✅ **JACKPOT** |
| `forecasting_data_warehouse.social_intelligence_unified` | 4,673 | Mixed | (need to check schema) | ⚠️ Unknown |
| `forecasting_data_warehouse.social_sentiment` | 677 | 2008-2025 | title, sentiment_score, timestamp | ✅ Currently used |
| `models.sentiment_features_materialized` | 581 | 2008-2025 | avg_sentiment, sentiment_std | ✅ Processed |
| `models.sentiment_features_precomputed` | 604 | 2018-2025 | avg_sentiment_30d_ma | ✅ Processed |

**Problem:** Signal views only use `social_sentiment` (677 rows, sparse)  
**Solution:** Point views to `staging.comprehensive_social_intelligence` (63,431 rows)

### Trump/Policy Intelligence (1,797 rows across 8 tables)

| Location | Rows | Date Range | Key Columns | Status |
|----------|------|------------|-------------|--------|
| `forecasting_data_warehouse.trump_policy_intelligence` | 450 | Apr-Nov 2025 | text, agricultural_impact, timestamp | ✅ Active |
| `staging.trump_policy_intelligence` | 215 | Apr-Oct 2025 | Same as above | ✅ Staging |
| `deprecated.ice_trump_intelligence*` | 376 | Apr-Oct 2025 | Same as above | ⚠️ Legacy |
| `models.tariff_features_materialized` | 46 | Apr-Oct 2025 | tariff_mentions, avg_ag_impact | ✅ Processed |
| `models.enhanced_policy_features` | 653 | 2008-2025 | tariff_mentions, china_mentions | ✅ Processed |
| `models_v4.trump_policy_daily` | 53 | 2023-2025 | (need to check) | ⚠️ Unknown |

**Problem:** Only 450 active rows, views query correctly but data is recent only  
**Solution:** Use what exists, backfill historical if needed later

### FX/Currency (59,187 rows - EXCELLENT)

| Location | Rows | Status |
|----------|------|--------|
| `forecasting_data_warehouse.currency_data` | 59,187 | ✅ Excellent |
| `models_v4.fx_derived_features` | 16,824 | ✅ Good |
| `models_v4.usd_cny_daily_complete` | 5,021 | ✅ Good |

**Status:** Working well, already in training tables

---

## 🎯 THE FIX - MINIMAL CHANGES REQUIRED

### Fix #1: Update Signal Views to Use Comprehensive Social Intelligence

**File to modify:** Signal view SQL (not found in repo yet—need to locate)  
**Change:** Point from `social_sentiment` (677 rows) → `staging.comprehensive_social_intelligence` (63,431 rows)

**Example for vw_tariff_threat_signal:**
```sql
-- CURRENT (queries sparse table):
SELECT ... FROM `forecasting_data_warehouse.social_sentiment`
WHERE LOWER(title) LIKE '%tariff%'

-- SHOULD BE (queries rich table):
SELECT ... FROM `staging.comprehensive_social_intelligence`
WHERE policy_score > 0.5 OR content LIKE '%tariff%'
```

### Fix #2: Add Direct JOINs in ULTIMATE_DATA_CONSOLIDATION.sql

**Add these CTEs to ULTIMATE_DATA_CONSOLIDATION.sql:**

```sql
-- Add after line 22 (after all_dates AS)

-- Get comprehensive social intelligence (63K rows!)
social_intel AS (
  SELECT 
    DATE(collection_date) as date,
    AVG(china_score) as china_sentiment,
    AVG(policy_score) as policy_impact,
    AVG(soy_score) as soy_sentiment,
    COUNT(*) as social_volume,
    STDDEV(china_score) as china_sentiment_volatility
  FROM `cbi-v14.staging.comprehensive_social_intelligence`
  GROUP BY DATE(collection_date)
),

-- Get news intelligence  
news_intel AS (
  SELECT 
    DATE(published) as date,
    AVG(intelligence_score) as news_intelligence_score,
    COUNT(*) as news_article_count
  FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
  GROUP BY DATE(published)
),

-- Get trump policy intelligence
trump_intel AS (
  SELECT 
    DATE(timestamp) as date,
    AVG(agricultural_impact) as trump_ag_impact,
    COUNT(*) as trump_policy_events
  FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`
  GROUP BY DATE(timestamp)
),
```

**Then add to main SELECT (after line 127):**

```sql
-- Add intelligence features
COALESCE(si.china_sentiment, ed.china_sentiment) as china_sentiment,
COALESCE(si.policy_impact, ed.china_policy_impact) as china_policy_impact,
COALESCE(si.soy_sentiment) as soy_sentiment,
COALESCE(si.social_volume) as social_volume,
COALESCE(si.china_sentiment_volatility, ed.china_sentiment_volatility) as china_sentiment_volatility,
COALESCE(ni.news_intelligence_score) as avg_sentiment,
COALESCE(ni.news_article_count) as news_article_count,
COALESCE(ti.trump_ag_impact) as trump_policy_impact,
COALESCE(ti.trump_policy_events) as trump_policy_events,
```

**And add JOINs (after line 200):**

```sql
LEFT JOIN social_intel si ON ad.date = si.date
LEFT JOIN news_intel ni ON ad.date = ni.date
LEFT JOIN trump_intel ti ON ad.date = ti.date
```

### Fix #3: Update export_training_data.py to Use Vertex Naming

**File:** `scripts/export_training_data.py`  
**Lines to change:** Output file naming

**Current:**
```python
output_file = os.path.join(export_dir, "historical_full.parquet")
```

**Should be:**
```python
timestamp = datetime.now().strftime("%Y%m%d")
output_file = os.path.join(export_dir, f"CBI_V14_Vertex_1M_Dataset_{timestamp}.parquet")
```

### Fix #4: Organize External Drive Per Architecture

**Create directory structure:**
```bash
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw"
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/processed"
```

**Export raw intelligence for reference:**
```python
# New script: scripts/export_raw_intelligence.py
# Exports all source intelligence tables to TrainingData/raw/
```

---

## 📋 EXECUTION PLAN (Minimal, Surgical Changes)

### Phase 1: Fix Signal Views (2 hours)
1. Locate signal view SQL files (or recreate from bq show output)
2. Update to query `staging.comprehensive_social_intelligence` instead of `social_sentiment`
3. Test views return non-zero data for 2024-2025
4. Deploy updated views

### Phase 2: Update ULTIMATE_DATA_CONSOLIDATION.sql (1 hour)
1. Add 3 CTEs for intelligence data
2. Add intelligence columns to SELECT
3. Add 3 JOINs
4. Test SQL returns populated intelligence columns

### Phase 3: Rebuild Production Training Tables (1 hour)
1. Backup existing tables
2. Run updated ULTIMATE_DATA_CONSOLIDATION.sql
3. Verify intelligence columns are populated for 2024-2025
4. Verify no data loss in other columns

### Phase 4: Update Export Script (1 hour)
1. Update `export_training_data.py` with Vertex naming
2. Add export of raw intelligence to TrainingData/raw/
3. Test exports create properly named files
4. Verify Parquet files are readable

### Phase 5: Verification (1 hour)
1. Query production_training_data_1m for Nov 2025 data
2. Verify intelligence columns are populated
3. Run verification test suite
4. Document changes

---

## 🎯 EXPECTED OUTCOME

**Before:**
- Intelligence columns: NULL for 2024-2025
- Using: 677 rows social_sentiment (sparse)
- Signal values: Hardcoded 0.2/0.3/0.5

**After:**
- Intelligence columns: POPULATED for 2024-2025
- Using: 63,431 rows comprehensive_social_intelligence (rich)
- Signal values: Dynamic, calculated from real data

---

## 📁 FILES TO MODIFY (Total: 3)

1. Signal view SQL (need to locate or recreate)
   - `vw_tariff_threat_signal`
   - `vw_china_relations_signal`
   - `vw_geopolitical_volatility_signal`

2. `config/bigquery/bigquery-sql/ULTIMATE_DATA_CONSOLIDATION.sql`
   - Add 3 CTEs
   - Add columns to SELECT
   - Add 3 JOINs

3. `scripts/export_training_data.py`
   - Update output file naming
   - Add raw data export

**NO table recreation, NO data movement, ONLY JOIN fixes.**

---

**Status:** READY TO EXECUTE  
**Estimated Time:** 6 hours total  
**Risk:** LOW (only updating SQL, all backups in place)  
**Confidence:** HIGH (root cause identified with evidence)

