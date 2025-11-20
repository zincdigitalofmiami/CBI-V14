---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Vegas Intel - Glide API Reference
**SINGLE SOURCE OF TRUTH - LOCKED CONFIGURATION**  
**Last Updated:** November 5, 2025  
**Status:** ✅ OPERATIONAL (5,628 rows loaded)

---

## ⚠️ CRITICAL: GLIDE API IS READ ONLY

**🚨 DO NOT TOUCH ANYTHING IN GLIDE 🚨**

- **Glide Access:** READ ONLY - NO MODIFICATIONS ALLOWED
- **No Writes:** Never write data back to Glide
- **No Deletes:** Never delete records in Glide
- **No Updates:** Never update fields in Glide
- **No Schema Changes:** Never modify table structure in Glide
- **Read Only Queries:** Only query data, never mutate

**Why Read Only:**
- Glide is the source of truth for US Oil Solutions operational data
- Any modifications could break their production workflows
- Dashboard consumes data via BigQuery (read-only copy)
- All modifications must happen in Glide by US Oil Solutions team

**Our Role:** Pull data from Glide → Load to BigQuery → Display in Dashboard (READ ONLY)

---

## Overview

This document provides the complete reference for all 8 Glide API data sources powering the Vegas Intel page. All configuration is **LOCKED** and should not be changed without approval.

**Global Configuration:**
- **Endpoint:** `https://api.glideapp.io/api/function/queryTables`
- **App ID:** `6262JQJdNjhra79M25e4`
- **Bearer Token:** `460c9ee4-edcb-43cc-86b5-929e2bb94351`
- **Access Level:** Business plan or above required
- **Access Mode:** **READ ONLY** (Query only, no writes)
- **Ingestion Script:** `/Users/zincdigital/CBI-V14/cbi-v14-ingestion/ingest_glide_vegas_data.py`

---

## API Request Format (LOCKED - READ ONLY)

All 8 APIs use the **exact same request format**. This is a **READ ONLY** operation - it only queries data from Glide.

### Standard Read-Only Request

```python
import requests

headers = {
    "Authorization": "Bearer 460c9ee4-edcb-43cc-86b5-929e2bb94351",
    "Content-Type": "application/json"
}

payload = {
    "appID": "6262JQJdNjhra79M25e4",
    "queries": [
        {
            "tableName": "<TABLE_ID_HERE>",
            "utc": True
        }
    ]
}

# READ ONLY - This only queries data, does not modify Glide
response = requests.post(
    "https://api.glideapp.io/api/function/queryTables",
    headers=headers,
    json=payload,
    timeout=30
)

data = response.json()
rows = data[0]['rows']  # Extract rows from response (READ ONLY)
```

**⚠️ REMINDER:** This is a query operation only. We never write data back to Glide.

---

## API 1: Restaurants (READ ONLY)

**Purpose:** Individual restaurant details, location, oil usage patterns  
**Table ID:** `native-table-ojIjQjDcDAEOpdtZG5Ao`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_restaurants`  
**Row Count:** 151  
**Feeds:** CustomerRelationshipMatrix, EventDrivenUpsell  
**Access Mode:** **READ ONLY**

### Python Example (READ ONLY)

```python
import requests

# READ ONLY QUERY - No modifications to Glide
r = requests.post(
    "https://api.glideapp.io/api/function/queryTables",
    headers={"Authorization": "Bearer 460c9ee4-edcb-43cc-86b5-929e2bb94351"},
    json={
        "appID": "6262JQJdNjhra79M25e4",
        "queries": [
            {
                "tableName": "native-table-ojIjQjDcDAEOpdtZG5Ao",
                "utc": True
            }
        ]
    }
)

result = r.json()
restaurants = result[0]['rows']  # READ ONLY - just reading data
```

**Key Fields (READ ONLY):**
- Restaurant name, location, current oil usage
- Delivery schedules, scheduling windows
- Usage patterns, baseline consumption

---

## API 2: Casinos (READ ONLY)

**Purpose:** Casino-level data for event coordination  
**Table ID:** `native-table-Gy2xHsC7urEttrz80hS7`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_casinos`  
**Row Count:** 31  
**Feeds:** EventVolumeMultipliers, SalesIntelligenceOverview  
**Access Mode:** **READ ONLY**

### Python Example (READ ONLY)

```python
import requests

# READ ONLY QUERY - No modifications to Glide
r = requests.post(
    "https://api.glideapp.io/api/function/queryTables",
    headers={"Authorization": "Bearer 460c9ee4-edcb-43cc-86b5-929e2bb94351"},
    json={
        "appID": "6262JQJdNjhra79M25e4",
        "queries": [
            {
                "tableName": "native-table-Gy2xHsC7urEttrz80hS7",
                "utc": True
            }
        ]
    }
)

result = r.json()
casinos = result[0]['rows']  # READ ONLY
```

---

## API 3: Fryers (READ ONLY - FOUNDATION DATA)

**Purpose:** Fryer capacity, oil consumption calculations  
**Table ID:** `native-table-r2BIqSLhezVbOKGeRJj8`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_fryers`  
**Row Count:** 421  
**Feeds:** ALL components (foundation for volume calculations)  
**Access Mode:** **READ ONLY**

### Python Example (READ ONLY)

```python
import requests

# READ ONLY QUERY - No modifications to Glide
r = requests.post(
    "https://api.glideapp.io/api/function/queryTables",
    headers={"Authorization": "Bearer 460c9ee4-edcb-43cc-86b5-929e2bb94351"},
    json={
        "appID": "6262JQJdNjhra79M25e4",
        "queries": [
            {
                "tableName": "native-table-r2BIqSLhezVbOKGeRJj8",
                "utc": True
            }
        ]
    }
)

result = r.json()
fryers = result[0]['rows']  # READ ONLY
```

---

## API 4: Export List (READ ONLY)

**Purpose:** Customer export lists for targeted campaigns  
**Table ID:** `native-table-PLujVF4tbbiIi9fzrWg8`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_export_list`  
**Row Count:** 3,176  
**Feeds:** EventDrivenUpsell (AI targeting), CustomerRelationshipMatrix  
**Access Mode:** **READ ONLY**

### Python Example (READ ONLY)

```python
import requests

# READ ONLY QUERY
r = requests.post(
    "https://api.glideapp.io/api/function/queryTables",
    headers={"Authorization": "Bearer 460c9ee4-edcb-43cc-86b5-929e2bb94351"},
    json={
        "appID": "6262JQJdNjhra79M25e4",
        "queries": [
            {
                "tableName": "native-table-PLujVF4tbbiIi9fzrWg8",
                "utc": True
            }
        ]
    }
)

result = r.json()
export_list = result[0]['rows']  # READ ONLY
```

---

## API 5: CSV Scheduled Reports (READ ONLY)

**Purpose:** Automated reporting data, historical trends  
**Table ID:** `native-table-pF4uWe5mpzoeGZbDQhPK`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_scheduled_reports`  
**Row Count:** 28  
**Feeds:** SalesIntelligenceOverview, MarginProtectionAlerts  
**Access Mode:** **READ ONLY**

### Python Example (READ ONLY)

```python
import requests

# READ ONLY QUERY
r = requests.post(
    "https://api.glideapp.io/api/function/queryTables",
    headers={"Authorization": "Bearer 460c9ee4-edcb-43cc-86b5-929e2bb94351"},
    json={
        "appID": "6262JQJdNjhra79M25e4",
        "queries": [
            {
                "tableName": "native-table-pF4uWe5mpzoeGZbDQhPK",
                "utc": True
            }
        ]
    }
)

result = r.json()
scheduled_reports = result[0]['rows']  # READ ONLY
```

---

## API 6: Shifts (READ ONLY)

**Purpose:** Delivery shift scheduling, route optimization  
**Table ID:** `native-table-K53E3SQsgOUB4wdCJdAN`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_shifts`  
**Row Count:** 148  
**Feeds:** EventDrivenUpsell (delivery timing), logistics planning  
**Access Mode:** **READ ONLY**

### Python Example (READ ONLY)

```python
import requests

# READ ONLY QUERY
r = requests.post(
    "https://api.glideapp.io/api/function/queryTables",
    headers={"Authorization": "Bearer 460c9ee4-edcb-43cc-86b5-929e2bb94351"},
    json={
        "appID": "6262JQJdNjhra79M25e4",
        "queries": [
            {
                "tableName": "native-table-K53E3SQsgOUB4wdCJdAN",
                "utc": True
            }
        ]
    }
)

result = r.json()
shifts = result[0]['rows']  # READ ONLY
```

---

## API 7: Shift Casinos (READ ONLY)

**Purpose:** Casino-specific shift scheduling  
**Table ID:** `native-table-G7cMiuqRgWPhS0ICRRyy`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_shift_casinos`  
**Row Count:** 440  
**Feeds:** EventVolumeMultipliers  
**Access Mode:** **READ ONLY**

### Python Example (READ ONLY)

```python
import requests

# READ ONLY QUERY
r = requests.post(
    "https://api.glideapp.io/api/function/queryTables",
    headers={"Authorization": "Bearer 460c9ee4-edcb-43cc-86b5-929e2bb94351"},
    json={
        "appID": "6262JQJdNjhra79M25e4",
        "queries": [
            {
                "tableName": "native-table-G7cMiuqRgWPhS0ICRRyy",
                "utc": True
            }
        ]
    }
)

result = r.json()
shift_casinos = result[0]['rows']  # READ ONLY
```

---

## API 8: Shift Restaurants (READ ONLY)

**Purpose:** Restaurant-specific shift scheduling  
**Table ID:** `native-table-QgzI2S9pWL584rkOhWBA`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_shift_restaurants`  
**Row Count:** 1,233  
**Feeds:** CustomerRelationshipMatrix  
**Access Mode:** **READ ONLY**

### Python Example (READ ONLY)

```python
import requests

# READ ONLY QUERY
r = requests.post(
    "https://api.glideapp.io/api/function/queryTables",
    headers={"Authorization": "Bearer 460c9ee4-edcb-43cc-86b5-929e2bb94351"},
    json={
        "appID": "6262JQJdNjhra79M25e4",
        "queries": [
            {
                "tableName": "native-table-QgzI2S9pWL584rkOhWBA",
                "utc": True
            }
        ]
    }
)

result = r.json()
shift_restaurants = result[0]['rows']  # READ ONLY
```

---

## Data Flow Architecture (READ ONLY)

```
┌─────────────────────────────────────────────────────────────┐
│                  Glide API (READ ONLY)                      │
│         US Oil Solutions Production Data                    │
│              (8 Data Sources - LOCKED)                      │
│                                                             │
│   🚨 DO NOT TOUCH - READ ONLY ACCESS ONLY 🚨               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ (READ ONLY Query)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│         Python Ingestion Script (READ ONLY)                 │
│      ingest_glide_vegas_data.py                             │
│   - READS data from all 8 APIs (NO WRITES)                  │
│   - Sanitizes column names                                   │
│   - Adds metadata (ingested_at, source_table_id)            │
│   - NEVER writes back to Glide                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ (One-way copy)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│               BigQuery Tables (Our Copy)                    │
│       cbi-v14.forecasting_data_warehouse                    │
│   - vegas_restaurants (151 rows)                            │
│   - vegas_casinos (31 rows)                                 │
│   - vegas_fryers (421 rows)                                 │
│   - vegas_export_list (3,176 rows)                          │
│   - vegas_scheduled_reports (28 rows)                       │
│   - vegas_shifts (148 rows)                                 │
│   - vegas_shift_casinos (440 rows)                          │
│   - vegas_shift_restaurants (1,233 rows)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           Dashboard API Routes (READ ONLY)                  │
│         /api/v4/vegas/*                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│          React Components (Vegas Page)                      │
│             Display Only - READ ONLY                        │
└─────────────────────────────────────────────────────────────┘
```

**⚠️ CRITICAL REMINDER:** Data flows ONE WAY ONLY (Glide → BigQuery → Dashboard). We NEVER write back to Glide.

---

## Security & Access Control

**Glide Access Policy:**
- ✅ **Allowed:** Query data via API (READ ONLY)
- ❌ **Forbidden:** Write data to Glide
- ❌ **Forbidden:** Update records in Glide
- ❌ **Forbidden:** Delete records in Glide
- ❌ **Forbidden:** Modify schema in Glide
- ❌ **Forbidden:** Direct access to Glide UI (unless authorized by US Oil Solutions)

**Why These Restrictions:**
- Glide is US Oil Solutions' production system
- Any modifications could break their operational workflows
- They manage their data in Glide
- We only consume a read-only copy for dashboard visualization

**Bearer Token Security:**
- Token: `460c9ee4-edcb-43cc-86b5-929e2bb94351`
- Stored in environment variable: `GLIDE_BEARER_TOKEN`
- Provides READ ONLY access to queryTables endpoint
- Rotate quarterly for security

---

## Troubleshooting

### "Can I update data in Glide?"

**NO.** Glide is READ ONLY. All updates must be done by US Oil Solutions team in their Glide app.

### "Can I fix incorrect data in Glide?"

**NO.** Contact US Oil Solutions to fix data in Glide. We only consume READ ONLY copies.

### "Can I add new fields to Glide tables?"

**NO.** All schema changes must be done by US Oil Solutions team.

### "What if I see wrong data?"

1. **DO NOT** modify Glide
2. Contact US Oil Solutions to fix in Glide
3. Re-run ingestion script to pull updated data
4. BigQuery will reflect Glide changes on next ingestion

---

## Change Log

**November 5, 2025** - Initial READ ONLY configuration
- Locked 8 API data sources (READ ONLY access)
- App ID: `6262JQJdNjhra79M25e4`
- All 8 BigQuery tables created and populated
- 5,628 total rows loaded successfully
- Emphasized READ ONLY access throughout

---

**End of Reference Document**  
**🚨 GLIDE IS READ ONLY - DO NOT TOUCH 🚨**  
**Status:** ✅ LOCKED CONFIGURATION - NO MODIFICATIONS ALLOWED







