# Comprehensive Parsing & Pipeline Audit
**Date**: November 12, 2025  
**Scope**: External Drive Integration, Data Schema, Computation Flow, Parsing Logic

---

## Executive Summary

**Status**: ⚠️ **CRITICAL ISSUES FOUND** - Action Required

### Critical Findings
1. **🔴 Baltic Dry Index**: Uses MOCK DATA instead of real API calls
2. **🔴 Volatility Ingestion**: Hardcoded path that breaks on current system
3. **🟡 Data Flow**: Ingestion → Warehouse → Production pipeline is correct but needs monitoring
4. **✅ EPA RIN Prices**: Recently hardened with robust parsing (good example)

### Overall Health
- **External Drive**: ✅ Fully functional
- **Data Schema**: ✅ Production tables fresh, historical gaps documented
- **Computation Flow**: ✅ Correct architecture, needs deduplication improvements
- **Parsing Logic**: ⚠️ **3 critical scripts need fixes**

---

## 1. External Drive Pipeline Review

### ✅ **VERIFIED WORKING**
- External drive mounted: `/Volumes/Satechi Hub`
- Repository accessible: Symlink resolves correctly
- Write permissions: Test file creation/removal successful
- Log directory: `Logs/cron/` created and writable

### ⚠️ **ISSUES FOUND**
- **Cron Jobs**: Not installed yet (expected - needs `bash scripts/crontab_setup.sh`)
- **Credentials**: Using ADC instead of explicit `GOOGLE_APPLICATION_CREDENTIALS`
  - **Impact**: May fail in cron context
  - **Fix**: Create `.env.cron` with credentials path

### **Recommendations**
1. Install cron schedule: `bash scripts/crontab_setup.sh`
2. Create `.env.cron` with `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`
3. Re-run diagnostic: `bash scripts/diagnose_local_environment.sh`

---

## 2. Data Schema Review

### ✅ **PRODUCTION TABLES - HEALTHY**
All production training tables are fresh and properly structured:

| Table | Rows | Date Range | Status |
|-------|------|------------|--------|
| `production_training_data_1w` | 6,057 | 2000-2025 | ✅ Fresh (6 days) |
| `production_training_data_1m` | 6,057 | 2000-2025 | ✅ Fresh (6 days) |
| `production_training_data_3m` | 6,057 | 2000-2025 | ✅ Fresh (6 days) |
| `production_training_data_6m` | 6,057 | 2000-2025 | ✅ Fresh (6 days) |
| `production_training_data_12m` | 6,057 | 2000-2025 | ✅ Fresh (6 days) |

**Key Points**:
- ✅ All tables have 25-year history (2000-2025) after recent integration
- ✅ 365% increase in training data (1,301 → 6,057 rows)
- ✅ No date gaps detected
- ✅ Schema consistent across all horizons

### ⚠️ **WAREHOUSE TABLES - KNOWN GAPS**
Some source tables in `forecasting_data_warehouse` have limited history:

| Table | Rows | Date Range | Issue |
|-------|------|------------|-------|
| `soybean_oil_prices` | 6,057 | 2000-2025 | ✅ Complete (recently expanded) |
| `vix_daily` | 2,717 | 2015-2025 | ⚠️ Missing pre-2015 |
| `cftc_cot` | 86 | 2024+ | 🔴 Very limited |
| `baltic_dry_index` | 0 | N/A | 🔴 **MISSING** (mock data issue) |

**Impact**: Regime-specific training (2008 crisis, trade war) has limited feature coverage.

---

## 3. Data Computation Flow Review

### **Architecture**: ✅ **CORRECT**

```
Ingestion Scripts
    ↓
forecasting_data_warehouse.* (source tables)
    ↓
Feature Engineering SQL Views
    ↓
production_training_data_* (training tables)
    ↓
BQML Models
```

### **Current Flow**

1. **Ingestion Layer** (`src/ingestion/*.py`)
   - Scripts fetch from APIs/scrapers
   - Write to `forecasting_data_warehouse.*` tables
   - Use `WRITE_APPEND` disposition

2. **Feature Engineering** (SQL Views)
   - Joins multiple warehouse tables
   - Calculates 290+ features
   - Handles NULLs with COALESCE

3. **Production Tables** (`models_v4.production_training_data_*`)
   - Built from feature engineering views
   - One table per horizon (1w, 1m, 3m, 6m, 12m)
   - Used for BQML training

### ⚠️ **ISSUES IN COMPUTATION**

#### Issue 1: Deduplication Inconsistent
- **EPA RIN**: ✅ Has deduplication (recently added)
- **CFTC**: ⚠️ Checks existing dates but no hash-based dedupe
- **Baltic**: ❌ No deduplication (uses mock data anyway)
- **Volatility**: ❌ No deduplication

**Recommendation**: Add hash-based deduplication to all ingestion scripts.

#### Issue 2: Error Handling Varies
- **EPA RIN**: ✅ Comprehensive error handling with retries
- **CFTC**: ✅ Good error handling
- **Baltic**: ❌ Minimal error handling (mock data)
- **Volatility**: ❌ No error handling

---

## 4. Parsing Logic Review (CRITICAL)

### ✅ **EPA RIN PRICES** - RECENTLY HARDENED

**File**: `src/ingestion/ingest_epa_rin_prices.py`

**Status**: ✅ **PRODUCTION READY** (after recent hardening)

**Improvements Made**:
1. ✅ Robust table detection with multiple strategies
2. ✅ Date parsing with validation
3. ✅ Price extraction with range validation (0.01-10.0)
4. ✅ Deduplication by date before load
5. ✅ Comprehensive logging
6. ✅ Error handling with retries

**Example of Good Parsing**:
```python
# Strong table detection
for table in tables:
    if any(col in str(table.columns).upper() for col in ['D4', 'D5', 'D6', 'WEEK']):
        # Validate and parse
        date = pd.to_datetime(week_str, errors='coerce')
        if pd.isna(date):
            continue  # Skip invalid dates
        
        # Extract prices with validation
        rin_d4 = self._extract_price(row, 'D4')
        if rin_d4 and 0.01 <= rin_d4 <= 10.0:
            rin_data.append({...})
```

**Recommendation**: Use this as a template for other parsers.

---

### 🔴 **BALTIC DRY INDEX** - CRITICAL BUG

**File**: `src/ingestion/ingest_baltic_dry_index.py`

**Status**: 🔴 **USES MOCK DATA** - Not production ready

**Critical Issues**:

1. **Lines 51-58**: Generates fake data instead of API calls
```python
# Mock data structure for now
mock_data = {
    'date': datetime.now().date(),
    'bdi_value': 1250 + (datetime.now().hour * 10),  # Mock BDI value
    'bdi_change': 15.5,
    'bdi_change_pct': 1.25,
    'source': source['name'],
    'timestamp': datetime.utcnow()
}
```

2. **No Real API Integration**: Comments say "For demo purposes" but script is in production

3. **Impact**: 
   - No real shipping cost data in system
   - Missing critical feature for supply chain forecasting
   - Regime training cannot use freight data

**Required Fixes**:
1. Implement real Trading Economics API integration
2. Add Investing.com API as fallback
3. Implement proper error handling
4. Add deduplication
5. Add data validation (BDI range: 300-4000)

**Priority**: 🔴 **CRITICAL** - Blocks supply chain forecasting

---

### 🔴 **VOLATILITY INGESTION** - PATH ISSUE

**File**: `src/ingestion/ingest_volatility.py`

**Status**: 🔴 **HARDCODED PATH** - Won't work on current system

**Critical Issues**:

1. **Line 66**: Hardcoded path to old user directory
```python
vol_file = Path("/Users/zincdigital/CBI-V14/data/csv/historical-prices-10-03-2025.csv")
```

2. **No Path Resolution**: Doesn't use repo root or external drive path

3. **No File Existence Check**: Fails silently if file doesn't exist

4. **No Deduplication**: Will create duplicate records on each run

5. **No Validation**: No range checks on volatility values

**Required Fixes**:
1. Use dynamic path resolution (repo root or external drive)
2. Add file existence check with clear error
3. Add deduplication by (symbol, data_date)
4. Add validation (implied_vol should be 0-200%)
5. Add logging for missing files

**Priority**: 🔴 **HIGH** - Script will fail on current system

---

### ✅ **CFTC POSITIONING** - WELL IMPLEMENTED

**File**: `src/ingestion/ingest_cftc_positioning_REAL.py`

**Status**: ✅ **PRODUCTION READY** (with minor improvements possible)

**Strengths**:
1. ✅ Real API integration (CFTC public reporting)
2. ✅ Multiple endpoint fallbacks (disaggregated → legacy)
3. ✅ Proper date parsing with multiple format handling
4. ✅ Schema validation matches existing table
5. ✅ Error handling with try/except
6. ✅ Logging throughout

**Minor Improvements Needed**:
1. ⚠️ Add hash-based deduplication (currently checks dates but could miss duplicates)
2. ⚠️ Add retry logic for API failures
3. ⚠️ Add validation ranges (position values should be positive)

**Priority**: 🟡 **LOW** - Works well, minor enhancements

---

## 5. Parsing Best Practices (Template)

Based on EPA RIN hardening, here's the recommended pattern:

### **1. Robust Fetching**
```python
def fetch_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30, headers={...})
            response.raise_for_status()
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
```

### **2. Strong Table/Data Detection**
```python
# Use multiple strategies
strategies = [
    lambda t: 'D4' in str(t.columns).upper(),
    lambda t: 'WEEK' in str(t.columns).upper(),
    lambda t: len(t) > 0 and 'date' in str(t.columns).lower()
]

for table in tables:
    if any(strategy(table) for strategy in strategies):
        # Process table
```

### **3. Validation & Range Checks**
```python
# Validate dates
date = pd.to_datetime(date_str, errors='coerce')
if pd.isna(date) or date < pd.Timestamp('2000-01-01'):
    continue  # Skip invalid dates

# Validate prices
price = float(price_str.replace('$', '').replace(',', ''))
if not (0.01 <= price <= 10.0):  # RIN-specific range
    logger.warning(f"Price out of range: {price}")
    continue
```

### **4. Deduplication**
```python
# Before load, check existing
existing_query = f"""
    SELECT DISTINCT date 
    FROM `{table_id}` 
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
"""
existing_dates = set(client.query(existing_query).to_dataframe()['date'].dt.date)

# Filter duplicates
df = df[~df['date'].dt.date.isin(existing_dates)]
```

### **5. Comprehensive Logging**
```python
logger.info(f"Found {len(tables)} candidate tables")
logger.info(f"Parsed {len(rin_data)} valid records")
logger.info(f"After deduplication: {len(df)} new records")
logger.info(f"Loaded {rows_loaded} records to BigQuery")
```

---

## 6. Data Flow Verification

### **Ingestion → Warehouse Flow**: ✅ **VERIFIED**

1. **EPA RIN Prices**:
   - Writes to: `forecasting_data_warehouse.biofuel_prices`
   - Schema: date, rin_d4_price, rin_d5_price, rin_d6_price, ...
   - Status: ✅ Working (recently hardened)

2. **CFTC COT**:
   - Writes to: `forecasting_data_warehouse.cftc_cot`
   - Schema: report_date, commodity, contract_code, managed_money_long, ...
   - Status: ✅ Working

3. **Baltic Dry Index**:
   - Should write to: `forecasting_data_warehouse.freight_logistics`
   - Status: 🔴 **NOT WORKING** (mock data)

4. **Volatility**:
   - Writes to: `forecasting_data_warehouse.volatility_data`
   - Status: 🔴 **WON'T WORK** (hardcoded path)

### **Warehouse → Production Flow**: ✅ **VERIFIED**

Production tables are built via SQL from warehouse sources:
- Uses feature engineering views
- Joins multiple warehouse tables
- Calculates 290+ features
- One table per horizon

**SQL Pattern**:
```sql
SELECT 
  target_1w,
  * EXCEPT(target_1w, target_1m, ...)
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL
```

---

## 7. Critical Action Items

### **IMMEDIATE (This Week)**

1. **Fix Baltic Dry Index** 🔴 **CRITICAL**
   - Remove mock data
   - Implement Trading Economics API
   - Add Investing.com fallback
   - Test with real data

2. **Fix Volatility Ingestion** 🔴 **HIGH**
   - Replace hardcoded path with dynamic resolution
   - Add file existence check
   - Add deduplication
   - Test on current system

3. **Install Cron Schedule** 🟡 **MEDIUM**
   - Run: `bash scripts/crontab_setup.sh`
   - Create `.env.cron` with credentials
   - Verify with diagnostic script

### **SHORT TERM (This Month)**

4. **Add Deduplication to All Scripts**
   - Use EPA RIN pattern as template
   - Add hash-based dedupe where appropriate
   - Test with existing data

5. **Add Monitoring**
   - Track ingestion success rates
   - Alert on parsing failures
   - Monitor data freshness

6. **Backfill Missing Data**
   - CFTC: Only 86 rows (need 52 weeks)
   - Baltic: Currently 0 rows (critical)
   - Historical gaps documented in DATA_GAPS_ANALYSIS

---

## 8. Recommendations Summary

### **Parsing Improvements**
- ✅ EPA RIN: Use as template for other parsers
- 🔴 Baltic: Implement real API integration
- 🔴 Volatility: Fix path and add validation
- 🟡 CFTC: Add hash-based deduplication

### **Pipeline Improvements**
- Add deduplication to all ingestion scripts
- Standardize error handling patterns
- Add comprehensive logging
- Implement retry logic for API calls

### **Monitoring Improvements**
- Track ingestion success/failure rates
- Monitor data freshness (already have `check_stale_data.py`)
- Alert on parsing errors
- Track feature coverage in production tables

---

## 9. Testing Checklist

Before deploying fixes, verify:

- [ ] Baltic Dry Index fetches real data (not mock)
- [ ] Volatility script works with dynamic paths
- [ ] All scripts handle missing files gracefully
- [ ] Deduplication prevents duplicate records
- [ ] Error logging is comprehensive
- [ ] Cron jobs run successfully
- [ ] Data flows correctly: Ingestion → Warehouse → Production

---

**Last Updated**: November 12, 2025  
**Next Review**: After critical fixes implemented

