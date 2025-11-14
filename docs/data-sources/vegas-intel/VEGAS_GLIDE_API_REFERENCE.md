# Vegas Intel - Glide API Reference
**SINGLE SOURCE OF TRUTH - LOCKED CONFIGURATION**  
**Last Updated:** November 5, 2025  
**Status:** ✅ OPERATIONAL (5,628 rows loaded)

---

## Overview

This document provides the complete reference for all 8 Glide API data sources powering the Vegas Intel page. All configuration is **LOCKED** and should not be changed without approval.

**Global Configuration:**
- **Endpoint:** `https://api.glideapp.io/api/function/queryTables`
- **App ID:** `6262JQJdNjhra79M25e4`
- **Bearer Token:** `460c9ee4-edcb-43cc-86b5-929e2bb94351`
- **Access Level:** Business plan or above required
- **Ingestion Script:** `/Users/zincdigital/CBI-V14/cbi-v14-ingestion/ingest_glide_vegas_data.py`

---

## API Request Format (LOCKED)

All 8 APIs use the **exact same request format**. Do not deviate from this structure.

### Standard Request

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

response = requests.post(
    "https://api.glideapp.io/api/function/queryTables",
    headers=headers,
    json=payload,
    timeout=30
)

data = response.json()
rows = data[0]['rows']  # Extract rows from response
```

---

## API 1: Restaurants

**Purpose:** Individual restaurant details, location, oil usage patterns  
**Table ID:** `native-table-ojIjQjDcDAEOpdtZG5Ao`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_restaurants`  
**Row Count:** 151  
**Feeds:** CustomerRelationshipMatrix, EventDrivenUpsell

### Python Example

```python
import requests

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
restaurants = result[0]['rows']
```

**Key Fields:**
- Restaurant name, location, current oil usage
- Delivery schedules, scheduling windows
- Usage patterns, baseline consumption

---

## API 2: Casinos

**Purpose:** Casino-level data for event coordination and high-volume opportunities  
**Table ID:** `native-table-Gy2xHsC7urEttrz80hS7`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_casinos`  
**Row Count:** 31  
**Feeds:** EventVolumeMultipliers, SalesIntelligenceOverview

### Python Example

```python
import requests

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
casinos = result[0]['rows']
```

**Key Fields:**
- Casino events, event calendar
- Restaurant affiliations, premium pricing tolerance
- High-volume opportunity indicators

---

## API 3: Fryers

**Purpose:** Fryer capacity, oil consumption calculations, baseline demand (FOUNDATION DATA)  
**Table ID:** `native-table-r2BIqSLhezVbOKGeRJj8`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_fryers`  
**Row Count:** 421  
**Feeds:** ALL components (foundation for volume calculations)

### Python Example

```python
import requests

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
fryers = result[0]['rows']
```

**Key Fields:**
- Fryer count per restaurant
- Capacity (lb), turns per month
- Base daily gallons, current utilization
- Fryer type (cuisine-based consumption patterns)

---

## API 4: Export List

**Purpose:** Customer export lists for targeted campaigns, upsell opportunities  
**Table ID:** `native-table-PLujVF4tbbiIi9fzrWg8`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_export_list`  
**Row Count:** 3,176  
**Feeds:** EventDrivenUpsell (AI targeting), CustomerRelationshipMatrix

### Python Example

```python
import requests

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
export_list = result[0]['rows']
```

**Key Fields:**
- Customer segments, contact information
- Campaign history, acceptance rates
- Upsell targeting data, customer preferences

---

## API 5: CSV Scheduled Reports

**Purpose:** Automated reporting data, historical trends, performance tracking  
**Table ID:** `native-table-pF4uWe5mpzoeGZbDQhPK`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_scheduled_reports`  
**Row Count:** 28  
**Feeds:** SalesIntelligenceOverview, MarginProtectionAlerts

### Python Example

```python
import requests

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
scheduled_reports = result[0]['rows']
```

**Key Fields:**
- Report schedules, data snapshots
- Trend calculations, alert triggers
- Performance tracking metrics

---

## API 6: Shifts

**Purpose:** Delivery shift scheduling, route optimization, capacity planning  
**Table ID:** `native-table-K53E3SQsgOUB4wdCJdAN`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_shifts`  
**Row Count:** 148  
**Feeds:** EventDrivenUpsell (delivery timing), logistics planning

### Python Example

```python
import requests

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
shifts = result[0]['rows']
```

**Key Fields:**
- Shift times, driver availability
- Delivery capacity, route assignments
- Scheduling constraints, optimization data

---

## API 7: Shift Casinos

**Purpose:** Casino-specific shift scheduling for high-priority deliveries  
**Table ID:** `native-table-G7cMiuqRgWPhS0ICRRyy`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_shift_casinos`  
**Row Count:** 440  
**Feeds:** EventVolumeMultipliers (casino event delivery coordination)

### Python Example

```python
import requests

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
shift_casinos = result[0]['rows']
```

**Key Fields:**
- Casino shift schedules, premium delivery windows
- Event-based capacity, high-priority slots
- Casino-specific routing, timing constraints

---

## API 8: Shift Restaurants

**Purpose:** Restaurant-specific shift scheduling for regular deliveries  
**Table ID:** `native-table-QgzI2S9pWL584rkOhWBA`  
**BigQuery Table:** `cbi-v14.forecasting_data_warehouse.vegas_shift_restaurants`  
**Row Count:** 1,233  
**Feeds:** CustomerRelationshipMatrix (delivery reliability scoring)

### Python Example

```python
import requests

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
shift_restaurants = result[0]['rows']
```

**Key Fields:**
- Restaurant shift schedules, preferred delivery windows
- Scheduling constraints, delivery reliability
- Regular delivery patterns, timing preferences

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Glide API                              │
│              (8 Data Sources - LOCKED)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│         Python Ingestion Script                             │
│      ingest_glide_vegas_data.py                             │
│   - Fetches data from all 8 APIs                            │
│   - Sanitizes column names ($rowID → glide_rowID)           │
│   - Adds metadata (ingested_at, source_table_id)            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│               BigQuery Tables                               │
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
│           Dashboard API Routes                              │
│         /api/v4/vegas/*                                     │
│   - metrics, upsell-opportunities                           │
│   - customers, events, margin-alerts                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│          React Components (Vegas Page)                      │
│   - SalesIntelligenceOverview                               │
│   - EventDrivenUpsell                                       │
│   - CustomerRelationshipMatrix                              │
│   - EventVolumeMultipliers                                  │
│   - MarginProtectionAlerts                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## API-to-Component Mapping

### Dashboard Component Breakdown

**1. SalesIntelligenceOverview**
- **Data Sources:** casinos, scheduled_reports, restaurants
- **Purpose:** High-level metrics dashboard
- **Key Metrics:** Total customers, active opportunities, revenue potential

**2. EventDrivenUpsell**
- **Data Sources:** restaurants, export_list, shifts, fryers
- **Purpose:** Event-based upsell opportunity identification
- **Key Metrics:** Upsell potential, revenue opportunity, AI targeting

**3. CustomerRelationshipMatrix**
- **Data Sources:** restaurants, export_list, shift_restaurants
- **Purpose:** Customer relationship scoring and tracking
- **Key Metrics:** Relationship score, delivery reliability, growth potential

**4. EventVolumeMultipliers**
- **Data Sources:** casinos, shift_casinos, fryers
- **Purpose:** Event volume surge forecasting
- **Key Metrics:** Volume multipliers, casino events, capacity planning

**5. MarginProtectionAlerts**
- **Data Sources:** scheduled_reports, fryers, restaurants
- **Purpose:** Margin risk detection and alerts
- **Key Metrics:** Margin risk, price alerts, revenue protection

---

## Ingestion Schedule

**Current:** Manual execution  
**Recommended:** Daily at 2:00 AM PST  
**Command:** `python3 /Users/zincdigital/CBI-V14/cbi-v14-ingestion/ingest_glide_vegas_data.py`

**Monitoring:**
- Check row counts: `bq query "SELECT COUNT(*) FROM \`cbi-v14.forecasting_data_warehouse.vegas_restaurants\`"`
- Check last ingestion: `bq query "SELECT MAX(ingested_at) FROM \`cbi-v14.forecasting_data_warehouse.vegas_restaurants\`"`

---

## Troubleshooting

### Common Issues

**1. 400 Error - Invalid Field Name**
- **Cause:** Glide API returns column names starting with `$` (e.g., `$rowID`)
- **Solution:** Column sanitization in `save_to_bigquery()` method ($ → glide_)

**2. 401 Error - Authentication Failed**
- **Cause:** Invalid Bearer token
- **Solution:** Verify token: `460c9ee4-edcb-43cc-86b5-929e2bb94351`

**3. Empty Response**
- **Cause:** Incorrect table ID or App ID
- **Solution:** Verify table ID matches this reference document exactly

**4. Timeout**
- **Cause:** Large table (e.g., export_list with 3,176 rows)
- **Solution:** Increase timeout to 60 seconds for large tables

---

## Security Notes

**⚠️ IMPORTANT:**
- Bearer token stored in environment variable: `GLIDE_BEARER_TOKEN`
- Fallback hardcoded in script (temporary - rotate after production deployment)
- Never commit Bearer token to Git
- Rotate token quarterly
- Restrict access to Business plan users only

---

## Change Log

**November 5, 2025** - Initial configuration
- Locked 8 API data sources
- App ID updated to `6262JQJdNjhra79M25e4`
- All 8 BigQuery tables created and populated
- 5,628 total rows loaded successfully

---

**End of Reference Document**  
**Status:** ✅ LOCKED CONFIGURATION - DO NOT MODIFY WITHOUT APPROVAL







