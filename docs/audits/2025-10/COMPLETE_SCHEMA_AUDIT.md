# COMPLETE SCHEMA AUDIT - CFTC TABLE

## EXISTING TABLE: `staging.cftc_cot`

### COMPLETE SCHEMA (14 fields):
1. **report_date** - DATE
2. **commodity** - STRING
3. **contract_code** - STRING
4. **managed_money_long** - FLOAT
5. **managed_money_short** - FLOAT
6. **managed_money_net** - FLOAT
7. **commercial_long** - FLOAT
8. **commercial_short** - FLOAT
9. **commercial_net** - FLOAT
10. **open_interest** - FLOAT
11. **source_name** - STRING
12. **confidence_score** - FLOAT
13. **ingest_timestamp_utc** - TIMESTAMP
14. **provenance_uuid** - STRING

### SAMPLE ROW (EXISTING DATA):
```json
{
  "report_date": "2024-10-29",
  "commodity": "Soybean_Oil",
  "contract_code": "ZL",
  "managed_money_long": 19292.0,
  "managed_money_short": 0.0,
  "managed_money_net": 19292.0,
  "commercial_long": 15527.0,
  "commercial_short": 0.0,
  "commercial_net": -15527.0,
  "open_interest": 219142.0,
  "source_name": "CBI_V14_Synthetic_CFTC",
  "confidence_score": 0.3,
  "ingest_timestamp_utc": "2025-10-15 06:37:45",
  "provenance_uuid": "724cc4ef-ba95-4980-9d24-4a99fa2c9854"
}
```

### WHAT I WAS MISSING:
- ❌ `source_name` - REQUIRED
- ❌ `confidence_score` - REQUIRED
- ❌ `ingest_timestamp_utc` - REQUIRED (TIMESTAMP format!)
- ❌ `provenance_uuid` - REQUIRED

### TABLE PARTITIONING:
- Partitioned by: `report_date` (DAY)
- Clustered by: `commodity`, `contract_code`

### EXISTING DATA:
- Current rows: Contains SYNTHETIC data (source_name = "CBI_V14_Synthetic_CFTC")
- Confidence: 0.3 (low confidence synthetic)
- Contract code: "ZL" (not CFTC commodity code)

## CORRECT MAPPING FOR REAL DATA:

### Fields I Need to Populate:
```python
{
    'report_date': '2024-10-29',  # DATE in YYYY-MM-DD format
    'commodity': 'Soybean_Oil',   # Match existing format
    'contract_code': 'ZL',        # Use 'ZL' not CFTC code
    'managed_money_long': 19292.0,    # FLOAT
    'managed_money_short': 0.0,       # FLOAT
    'managed_money_net': 19292.0,     # FLOAT (calculated)
    'commercial_long': 15527.0,       # FLOAT
    'commercial_short': 0.0,          # FLOAT
    'commercial_net': -15527.0,       # FLOAT (calculated)
    'open_interest': 219142.0,        # FLOAT
    'source_name': 'CFTC_API',        # STRING (change from synthetic)
    'confidence_score': 0.95,         # FLOAT (official API = high confidence)
    'ingest_timestamp_utc': '2025-10-15T12:00:00',  # TIMESTAMP ISO format
    'provenance_uuid': 'uuid-here'    # STRING (generate UUID)
}
```

## CRITICAL FIXES NEEDED:

1. **Add missing fields**: source_name, confidence_score, ingest_timestamp_utc, provenance_uuid
2. **Use 'ZL' for contract_code** (not CFTC commodity code '007601')
3. **Use 'Soybean_Oil'** for commodity (match existing format)
4. **Set confidence_score = 0.95** (official API data)
5. **Set source_name = 'CFTC_API'** (replace synthetic indicator)
6. **Generate UUID** for provenance
7. **Use ISO timestamp** for ingest_timestamp_utc

## VIEWS THAT REFERENCE THIS TABLE:
- Need to search for views that query `staging.cftc_cot`
- Need to check `curated.*` and `signals.*` datasets


