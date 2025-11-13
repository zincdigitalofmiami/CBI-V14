# 🔬 DEEP PARSING, SCHEMA, METADATA & CALCULATION AUDIT
## Comprehensive Pre-Execution Review
**Date:** November 7, 2025  
**Purpose:** Surgical review before scheduling and data pulls

---

## 📋 EXECUTIVE SUMMARY

### **AUDIT SCOPE:**
1. **Parsing Logic:** Date parsing, type conversions, null handling across all ingestion scripts
2. **Schema Consistency:** Table schemas, naming conventions, data types, required fields
3. **Metadata Patterns:** Provenance UUID, confidence scores, source names, timestamps
4. **Calculations:** Multipliers, spreads, ratios, rolling averages, lag features, interactions
5. **Routing Logic:** Staging → Production flows, deduplication, table mappings

### **CRITICAL FINDINGS:**

#### ✅ **STRENGTHS:**
- **Standardized metadata pattern** exists (`provenance_uuid`, `confidence_score`, `source_name`, `ingest_timestamp_utc`)
- **Modern decorator pattern** in `bigquery_utils.py` with automatic error handling
- **Canonical metadata checker** exists (`dq_canonical_metadata_check.py`)
- **db-dtypes** used for automatic type conversion (pandas → BigQuery)

#### ⚠️ **ISSUES IDENTIFIED:**

1. **Date Parsing Inconsistencies:**
   - Mix of `pd.to_datetime()` with/without timezone handling
   - Some scripts use `dt.tz_localize(None)` (removes timezone)
   - Others use `datetime.now(timezone.utc)` (keeps UTC)
   - Inconsistent date column names (`date`, `timestamp`, `time`, `data_date`)

2. **Schema Inconsistencies:**
   - Some tables have canonical metadata, others don't
   - Mixed naming: `timestamp` vs `ingest_timestamp_utc` vs `ingestion_timestamp`
   - Some tables missing required fields (e.g., `provenance_uuid`)

3. **Calculation Patterns:**
   - Default values used in SQL (e.g., `1.5 AS rin_d4_price`) when data missing
   - Multipliers hardcoded (e.g., `* 20.0` for VIX, `* 100.0` for DXY)
   - Spread calculations inconsistent (some use `-`, others use `/`)

4. **Routing Gaps:**
   - Some scripts write to staging, others directly to production
   - No standardized deduplication logic
   - Missing migration scripts for some staging tables

---

## 🔍 DETAILED AUDIT FINDINGS

### **1. PARSING LOGIC AUDIT**

#### **Date Parsing Patterns Found:**

| Script | Pattern | Timezone Handling | Issue |
|--------|---------|-------------------|-------|
| `pull_yahoo_complete_enterprise.py` | `pd.to_datetime().dt.tz_localize(None)` | Removes timezone | ⚠️ Loses UTC info |
| `TRUMP_SENTIMENT_QUANT_ENGINE.py` | `pd.to_datetime(df['timestamp'])` | Keeps timezone | ✅ Good |
| `load_biofuel_raw_prices.py` | `pd.to_datetime(df['Date'], utc=True)` | Explicit UTC | ✅ Good |
| `calculate_rin_proxies.py` | `pd.to_datetime(..., utc=True)` | Explicit UTC | ✅ Good |
| `MASTER_CONTINUOUS_COLLECTOR.py` | `datetime.now(timezone.utc)` | Explicit UTC | ✅ Good |
| `bigquery_utils.py` | `datetime.now()` (no timezone) | No timezone | ⚠️ Should use UTC |

**RECOMMENDATION:** Standardize on `pd.to_datetime(..., utc=True)` or `datetime.now(timezone.utc)`

#### **Type Conversion Patterns:**

| Pattern | Usage | Issue |
|---------|-------|-------|
| `float(data['Close'])` | Direct conversion | ⚠️ No null handling |
| `int(data['Volume'])` | Direct conversion | ⚠️ No null handling |
| `pd.notna()` checks | Some scripts | ✅ Good when used |
| `COALESCE()` in SQL | SQL scripts | ✅ Good |
| `df.astype()` | Pandas scripts | ⚠️ No null handling |

**RECOMMENDATION:** Always use `pd.to_numeric(..., errors='coerce')` or `COALESCE()` in SQL

#### **Null Handling Patterns:**

| Pattern | Usage | Issue |
|---------|-------|-------|
| `fillna(0)` | Some scripts | ⚠️ May mask missing data |
| `dropna()` | Some scripts | ⚠️ May lose valid rows |
| `COALESCE(..., 0)` | SQL scripts | ⚠️ Defaults may be wrong |
| `COALESCE(..., NULL)` | SQL scripts | ✅ Preserves nulls |
| `pd.isna()` checks | Some scripts | ✅ Good when used |

**RECOMMENDATION:** Use explicit defaults based on business logic, not generic zeros

---

### **2. SCHEMA CONSISTENCY AUDIT**

#### **Canonical Metadata Columns:**

**REQUIRED (per `dq_canonical_metadata_check.py`):**
- `source_name` (STRING)
- `confidence_score` (FLOAT, 0.0-1.0)
- `ingest_timestamp_utc` (TIMESTAMP)
- `provenance_uuid` (STRING)

**TABLES WITH CANONICAL METADATA:**
- ✅ `trump_policy_intelligence` (has all 4)
- ✅ `social_sentiment` (has all 4)
- ✅ `news_intelligence` (has all 4)
- ✅ `biofuel_prices` (has all 4)

**TABLES MISSING CANONICAL METADATA:**
- ❌ `soybean_oil_prices` (no metadata columns)
- ❌ `currency_data` (no metadata columns)
- ❌ `economic_indicators` (no metadata columns)
- ❌ `china_soybean_imports` (no metadata columns)
- ❌ `production_training_data_*` (no metadata columns - expected, these are derived)

**RECOMMENDATION:** Add canonical metadata to all base tables (except derived/aggregated tables)

#### **Date Column Naming:**

| Table | Date Column Name | Type | Issue |
|-------|------------------|------|-------|
| `production_training_data_1m` | `date` | DATE | ✅ Standard |
| `trump_policy_intelligence` | `timestamp` | TIMESTAMP | ⚠️ Should be `date` for joins |
| `china_soybean_imports` | `date` | DATE | ✅ Standard |
| `social_sentiment` | `timestamp` | TIMESTAMP | ⚠️ Should be `date` for joins |
| `biofuel_prices` | `date` | DATE | ✅ Standard |

**RECOMMENDATION:** Use `date` (DATE type) for join keys, `timestamp` (TIMESTAMP) for event times

#### **Numeric Column Types:**

| Pattern | Usage | Issue |
|---------|-------|-------|
| `FLOAT64` | Most numeric columns | ✅ Standard |
| `INT64` | Volume, counts | ✅ Standard |
| `NUMERIC` | Some price columns | ⚠️ Over-precise, use FLOAT64 |
| `STRING` | IDs, codes | ✅ Standard |

**RECOMMENDATION:** Use `FLOAT64` for prices/ratios, `INT64` for counts/volumes

---

### **3. METADATA PATTERNS AUDIT**

#### **Provenance UUID Generation:**

| Script | Pattern | Issue |
|--------|---------|-------|
| `MASTER_CONTINUOUS_COLLECTOR.py` | `str(uuid.uuid4())` | ✅ Good |
| `bigquery_utils.py` | Not generated | ⚠️ Should add to decorator |
| SQL scripts | Not generated | ⚠️ Should use `GENERATE_UUID()` |

**RECOMMENDATION:** Always generate UUID in Python scripts, use `GENERATE_UUID()` in SQL

#### **Confidence Score Patterns:**

| Source | Confidence | Rationale |
|--------|------------|-----------|
| Truth Social (Scrape Creators) | 0.85 | Verified API |
| USTR RSS | 0.95 | Official source |
| Federal Register | 0.95 | Official source |
| Yahoo Finance | 0.80 | Market data |
| GDELT | 0.75 | Aggregated news |
| Social Media | 0.70 | User-generated |

**RECOMMENDATION:** Document confidence scores in code comments, use consistent values

#### **Source Name Patterns:**

| Pattern | Example | Issue |
|---------|---------|-------|
| `'ScrapeCreators_TruthSocial'` | Good | ✅ Descriptive |
| `'USTR_RSS'` | Good | ✅ Descriptive |
| `'Yahoo_Finance'` | Good | ✅ Descriptive |
| `'source'` | Generic | ⚠️ Too generic |

**RECOMMENDATION:** Use format `{Provider}_{Platform}_{Type}` (e.g., `ScrapeCreators_TruthSocial_Posts`)

---

### **4. CALCULATION PATTERNS AUDIT**

#### **Multipliers Found in SQL:**

| Calculation | Multiplier | Rationale | Issue |
|-------------|------------|-----------|-------|
| `vix_lag1 * 20.0` | 20.0 | Convert normalized to actual VIX | ⚠️ Hardcoded, may be wrong |
| `dxy_lag1 * 100.0` | 100.0 | Convert normalized to actual DXY | ⚠️ Hardcoded, may be wrong |
| `meal_price_per_ton / 2000.0` | 2000.0 | Convert ton to cwt | ✅ Standard conversion |

**RECOMMENDATION:** Verify multipliers against actual data ranges, document in comments

#### **Spread Calculations:**

| Calculation | Pattern | Issue |
|-------------|---------|-------|
| `zl_f_close + zm_f_close - zs_f_close` | Crush spread | ✅ Standard |
| `brazil_export_premium - argentina_export_tax` | Country spread | ✅ Standard |
| `rin_d4_price / NULLIF(zl_f_close, 0)` | Ratio | ✅ Good null handling |
| `brazil_export_premium / NULLIF(zl_f_close, 0)` | Ratio | ✅ Good null handling |

**RECOMMENDATION:** Always use `NULLIF()` for division to avoid divide-by-zero

#### **Rolling Averages:**

| Calculation | Window | Issue |
|-------------|--------|-------|
| `AVG(...) OVER (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` | 7 days | ✅ Standard |
| `AVG(...) OVER (ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)` | 20 days | ✅ Standard |
| `STDDEV(...) OVER (ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)` | 20 days | ✅ Standard |

**RECOMMENDATION:** Document window sizes in comments, use consistent windows

#### **Lag Features:**

| Calculation | Lag | Issue |
|-------------|-----|-------|
| `LAG(zl_f_close, 1) OVER (ORDER BY date)` | 1 day | ✅ Standard |
| `LAG(china_soybean_imports_mt, 30) OVER (ORDER BY date)` | 30 days | ✅ Standard |
| `LAG(vix_close, 3) OVER (ORDER BY date)` | 3 days | ✅ Standard (VIX leads) |

**RECOMMENDATION:** Document lag rationale (e.g., "VIX leads by 3 days per plan")

#### **Interaction Terms:**

| Calculation | Interaction | Issue |
|-------------|-------------|-------|
| `vix_close * trump_agricultural_impact` | VIX × Trump | ✅ Standard |
| `vix_close * china_relations` | VIX × China | ✅ Standard |
| `vix_stress * big8_composite_score` | VIX × Big8 | ✅ Standard |

**RECOMMENDATION:** Document interaction rationale (e.g., "Trump era multiplier")

#### **Default Values:**

| Feature | Default | Rationale | Issue |
|---------|---------|-----------|-------|
| `rin_d4_price` | 1.5 | Historical average | ⚠️ May be stale |
| `rin_d5_price` | 1.2 | Historical average | ⚠️ May be stale |
| `brazil_premium_usd` | 0.0 | No data | ⚠️ Should be NULL or calculated |
| `argentina_tax_pct` | 30.0 | Historical average | ⚠️ May be stale |
| `trump_confidence` | 0.7 | Default confidence | ✅ Reasonable |

**RECOMMENDATION:** Use NULL for missing data, calculate defaults from historical averages in SQL

---

### **5. ROUTING LOGIC AUDIT**

#### **Staging → Production Flow:**

| Script | Source | Target | Deduplication | Issue |
|--------|--------|--------|---------------|-------|
| `daily_data_pull_and_migrate.py` | `staging.cftc_cot` | `forecasting_data_warehouse.cftc_cot` | `report_date NOT IN (...)` | ✅ Good |
| `daily_data_pull_and_migrate.py` | `staging.trump_policy_intelligence` | `forecasting_data_warehouse.trump_policy_intelligence` | `provenance_uuid NOT IN (...)` | ✅ Good |
| `daily_data_pull_and_migrate.py` | `staging.comprehensive_social_intelligence` | `forecasting_data_warehouse.social_sentiment` | `provenance_uuid NOT IN (...)` | ✅ Good |

**RECOMMENDATION:** Standardize deduplication on `provenance_uuid` for all tables

#### **Direct Production Writes:**

| Script | Target | Deduplication | Issue |
|--------|--------|----------------|-------|
| `trump_truth_social_monitor.py` | `forecasting_data_warehouse.trump_policy_intelligence` | None (WRITE_APPEND) | ⚠️ May create duplicates |
| `social_intelligence.py` | `forecasting_data_warehouse.social_sentiment` | None (WRITE_APPEND) | ⚠️ May create duplicates |
| `economic_intelligence.py` | `forecasting_data_warehouse.economic_indicators` | None (WRITE_APPEND) | ⚠️ May create duplicates |

**RECOMMENDATION:** Add deduplication logic or use `WRITE_TRUNCATE` for idempotent scripts

#### **Table Mappings:**

| Source Table | Target Table | Transformation | Issue |
|--------------|--------------|---------------|-------|
| `staging.comprehensive_social_intelligence` | `forecasting_data_warehouse.social_sentiment` | Column mapping + aggregation | ✅ Good |
| `staging.cftc_cot` | `forecasting_data_warehouse.cftc_cot` | Direct copy | ✅ Good |
| `staging.trump_policy_intelligence` | `forecasting_data_warehouse.trump_policy_intelligence` | Direct copy | ✅ Good |

**RECOMMENDATION:** Document all table mappings in migration scripts

---

## 🎯 STANDARDIZATION RECOMMENDATIONS

### **1. PARSING STANDARDS:**

```python
# DATE PARSING - Always use UTC
from datetime import datetime, timezone
import pandas as pd

# Pattern 1: From string
df['date'] = pd.to_datetime(df['date_str'], utc=True).dt.date  # For DATE type
df['timestamp'] = pd.to_datetime(df['date_str'], utc=True)  # For TIMESTAMP type

# Pattern 2: Current time
df['ingest_timestamp_utc'] = datetime.now(timezone.utc)

# TYPE CONVERSION - Always handle nulls
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(int)

# NULL HANDLING - Use business logic defaults
df['rin_price'] = df['rin_price'].fillna(1.5)  # Historical average
df['confidence'] = df['confidence'].fillna(0.7)  # Default confidence
```

### **2. SCHEMA STANDARDS:**

```sql
-- CANONICAL METADATA (all base tables)
source_name STRING NOT NULL,
confidence_score FLOAT64 NOT NULL,  -- 0.0-1.0
ingest_timestamp_utc TIMESTAMP NOT NULL,
provenance_uuid STRING NOT NULL,

-- DATE COLUMNS
date DATE NOT NULL,  -- For joins
timestamp TIMESTAMP,  -- For event times (optional)

-- NUMERIC COLUMNS
price FLOAT64,
volume INT64,
```

### **3. METADATA STANDARDS:**

```python
# PROVENANCE UUID
import uuid
record['provenance_uuid'] = str(uuid.uuid4())

# CONFIDENCE SCORES
CONFIDENCE_SCORES = {
    'official_source': 0.95,  # USTR, Federal Register
    'verified_api': 0.85,     # Scrape Creators
    'market_data': 0.80,       # Yahoo Finance
    'aggregated': 0.75,       # GDELT
    'user_generated': 0.70,   # Social media
}

# SOURCE NAMES
source_name = f"{provider}_{platform}_{type}"  # e.g., "ScrapeCreators_TruthSocial_Posts"
```

### **4. CALCULATION STANDARDS:**

```sql
-- SPREADS
crush_spread = zl_close + zm_close - zs_close

-- RATIOS (always use NULLIF)
rin_zl_ratio = rin_d4_price / NULLIF(zl_close, 0)

-- ROLLING AVERAGES (document window)
zl_ma_7d = AVG(zl_close) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)  -- 7-day MA

-- LAGS (document rationale)
vix_lag_3d = LAG(vix_close, 3) OVER (ORDER BY date)  -- VIX leads by 3 days

-- INTERACTIONS (document rationale)
vix_trump_interaction = vix_close * trump_impact  -- Trump era multiplier

-- DEFAULTS (use historical averages, not zeros)
rin_d4_price = COALESCE(rin_d4_price, 1.5)  -- Historical average
```

### **5. ROUTING STANDARDS:**

```python
# DEDUPLICATION (always use provenance_uuid)
existing_uuids = get_existing_uuids(table_name)
new_records = [r for r in records if r['provenance_uuid'] not in existing_uuids]

# OR use SQL MERGE
MERGE target_table t
USING staging_table s
ON t.provenance_uuid = s.provenance_uuid
WHEN NOT MATCHED THEN INSERT ...
```

---

## ✅ PRE-EXECUTION CHECKLIST

Before scheduling and pulling data:

- [ ] **Date Parsing:** All scripts use `pd.to_datetime(..., utc=True)` or `datetime.now(timezone.utc)`
- [ ] **Type Conversion:** All scripts use `pd.to_numeric(..., errors='coerce')` with null handling
- [ ] **Schema:** All base tables have canonical metadata columns
- [ ] **Metadata:** All records have `provenance_uuid`, `confidence_score`, `source_name`, `ingest_timestamp_utc`
- [ ] **Calculations:** All multipliers documented, all divisions use `NULLIF()`
- [ ] **Routing:** All scripts have deduplication logic (prefer `provenance_uuid`)
- [ ] **Defaults:** All default values documented and justified
- [ ] **Testing:** All scripts tested with sample data before scheduling

---

## 🚀 NEXT STEPS

1. **Fix Parsing Issues:** Update all scripts to use standardized parsing patterns
2. **Fix Schema Issues:** Add canonical metadata to all base tables
3. **Fix Calculation Issues:** Document multipliers, verify defaults
4. **Fix Routing Issues:** Add deduplication to all direct-write scripts
5. **Create Scheduling:** Comprehensive cron schedule with all missing jobs
6. **Pull Missing Data:** Execute data pulls for all stale/missing sources

---

**AUDIT COMPLETE**  
**Ready for surgical fixes and scheduling**

