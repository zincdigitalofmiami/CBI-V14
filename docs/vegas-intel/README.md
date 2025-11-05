# Vegas Intel Page - Documentation

**Location:** `/docs/vegas-intel/`  
**Last Updated:** November 5, 2025  
**Status:** ✅ OPERATIONAL - Production Ready

---

## 🚨 CRITICAL: GLIDE IS READ ONLY 🚨

**NEVER TOUCH ANYTHING IN GLIDE - READ ONLY ACCESS ONLY**

- **Glide = US Oil Solutions Production System**
- **Our Access = READ ONLY (Query data only)**
- **NO WRITES** to Glide under any circumstances
- **NO UPDATES** to Glide records
- **NO DELETES** from Glide tables
- **NO SCHEMA CHANGES** in Glide

**Our Role:** Read data from Glide → Copy to BigQuery → Display in dashboard (READ ONLY)

---

## Documentation Index

### Primary Documentation

1. **`VEGAS_GLIDE_API_REFERENCE.md`** - Single source of truth
   - All 8 Glide API endpoints (READ ONLY)
   - Complete Python examples
   - Table IDs and configuration (LOCKED)
   - **⚠️ Emphasizes READ ONLY access throughout**

2. **`HANDOFF_VEGAS_GLIDE_INTEGRATION_NOV5.md`** - Implementation handoff
   - Complete deployment summary
   - Operational instructions
   - Troubleshooting guide
   - Zero-risk deployment details

3. **`VEGAS_INTEL_SALES_PAGE_ARCHITECTURE.md`** - Page design
   - Dashboard component architecture
   - Data flow and API-to-component mapping
   - UI/UX specifications

### Supporting Documentation

4. **`README.md`** (this file) - Documentation index
   - Quick reference guide
   - READ ONLY reminders
   - File organization

---

## Quick Reference

### Glide API Configuration (READ ONLY)

- **Endpoint:** `https://api.glideapp.io/api/function/queryTables`
- **App ID:** `6262JQJdNjhra79M25e4`
- **Bearer Token:** `460c9ee4-edcb-43cc-86b5-929e2bb94351`
- **Access Mode:** **READ ONLY** (Query only, NO WRITES)

### BigQuery Tables (Our Read-Only Copy)

All tables in: `cbi-v14.forecasting_data_warehouse`

| Table | Rows | Purpose |
|-------|------|---------|
| `vegas_restaurants` | 151 | Restaurant master data |
| `vegas_casinos` | 31 | Casino event data |
| `vegas_fryers` | 421 | Fryer capacity (FOUNDATION) |
| `vegas_export_list` | 3,176 | Customer export lists |
| `vegas_scheduled_reports` | 28 | Scheduled reports |
| `vegas_shifts` | 148 | Delivery shifts |
| `vegas_shift_casinos` | 440 | Casino shifts |
| `vegas_shift_restaurants` | 1,233 | Restaurant shifts |

**Total:** 5,628 rows (READ ONLY copy from Glide)

### Ingestion Scripts

**Location:** `/Users/zincdigital/CBI-V14/cbi-v14-ingestion/`

1. **`ingest_glide_vegas_data.py`** - Live ingestion (READ ONLY query)
   ```bash
   python3 ingest_glide_vegas_data.py
   ```
   - Queries data from Glide (READ ONLY)
   - Loads to BigQuery
   - NEVER writes back to Glide

2. **`dryrun_glide_vegas.py`** - Dry run validation (READ ONLY)
   ```bash
   python3 dryrun_glide_vegas.py --dry-run --all
   ```
   - Tests all 8 APIs (READ ONLY)
   - No BigQuery writes in dry run mode

---

## Data Flow (READ ONLY)

```
Glide API (READ ONLY)
    ↓ (Query only - no writes)
Python Ingestion (READ ONLY)
    ↓ (One-way copy)
BigQuery Tables (Our copy)
    ↓
Dashboard APIs
    ↓
React Components (Display only)
```

**⚠️ CRITICAL:** Data flows ONE WAY only. We NEVER write back to Glide.

---

## Access Control

### Allowed Operations

✅ Query data from Glide API (READ ONLY)  
✅ Load queried data to BigQuery  
✅ Display data in dashboard  
✅ Run ingestion scripts (they only READ from Glide)  

### Forbidden Operations

❌ Write data to Glide  
❌ Update records in Glide  
❌ Delete records from Glide  
❌ Modify Glide schema  
❌ Direct Glide UI access (unless authorized by US Oil Solutions)  
❌ Any POST/PUT/DELETE operations to Glide (only GET/query allowed)  

---

## Important Reminders

### If You See Incorrect Data

1. **DO NOT** modify Glide
2. Contact US Oil Solutions team to fix in Glide
3. Re-run ingestion script to pull updated data
4. BigQuery will reflect Glide changes on next ingestion

### If You Need New Fields

1. **DO NOT** modify Glide schema
2. Request changes from US Oil Solutions team
3. They add fields in Glide
4. Re-run ingestion to pull new fields
5. Update BigQuery queries if needed

### If Schema Changes

1. US Oil Solutions makes changes in Glide
2. Re-run ingestion (auto-detect will pick up new schema)
3. Verify new fields in BigQuery
4. Update dashboard queries if needed

---

## Quick Commands

### Verify Tables

```bash
# List all vegas_* tables
bq ls cbi-v14:forecasting_data_warehouse | grep vegas_

# Check row counts
bq query --use_legacy_sql=false "
SELECT table_id, row_count 
FROM \`cbi-v14.forecasting_data_warehouse.__TABLES__\`
WHERE table_id LIKE 'vegas_%'
ORDER BY table_id;
"
```

### Run Ingestion

```bash
cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion
python3 ingest_glide_vegas_data.py
```

### Run Dry Run

```bash
cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion
python3 dryrun_glide_vegas.py --dry-run --all
```

---

## File Organization

```
/docs/vegas-intel/
├── README.md (this file)
├── VEGAS_GLIDE_API_REFERENCE.md (API docs - READ ONLY)
├── HANDOFF_VEGAS_GLIDE_INTEGRATION_NOV5.md (Deployment handoff)
└── VEGAS_INTEL_SALES_PAGE_ARCHITECTURE.md (Page design)
```

---

## Contact & Support

**For Questions About:**

- **Glide API:** See `VEGAS_GLIDE_API_REFERENCE.md`
- **Deployment:** See `HANDOFF_VEGAS_GLIDE_INTEGRATION_NOV5.md`
- **Page Design:** See `VEGAS_INTEL_SALES_PAGE_ARCHITECTURE.md`
- **Data Issues:** Contact US Oil Solutions (Glide data owners)

---

## Final Reminders

🚨 **GLIDE IS READ ONLY** 🚨

- We query data from Glide
- We load that data to BigQuery
- We display data in dashboard
- We NEVER modify Glide
- All Glide changes must be done by US Oil Solutions

**When in doubt: READ ONLY. Never write to Glide.**

---

**Last Updated:** November 5, 2025  
**Status:** Production Ready - READ ONLY access confirmed  
**Data Loaded:** 5,628 rows across 8 tables (READ ONLY copy)

