# RECURRING DATA ISSUES - PERMANENT DOCUMENTATION
**Date:** October 27, 2025  
**NEVER SEARCH FOR THESE ISSUES AGAIN!**

## 🚨 ROOT CAUSES IDENTIFIED

### 1. **MISSING TABLES ISSUE**
**Problem:** Scripts keep looking for tables that don't exist
**Root Cause:** Table names changed or never created

**MISSING TABLES:**
- `ice_trump_intelligence` - **NEVER CREATED** (scripts reference non-existent table)
- `silver_prices` - **NEVER CREATED** (only exists in economic_indicators as 'silver')

**PERMANENT FIX:**
```python
# ALWAYS use these actual table names:
ACTUAL_TABLES = {
    'trump_data': 'trump_policy_intelligence',  # NOT ice_trump_intelligence
    'silver_data': 'economic_indicators WHERE indicator = "silver"',  # NOT silver_prices
    'forex_data': 'currency_data',  # Schema: date, from_currency, to_currency, rate
}
```

### 2. **CURRENCY DATA SCHEMA CONFUSION**
**Problem:** Scripts look for 'indicator' column that doesn't exist
**Root Cause:** Currency data has different schema than economic_indicators

**ACTUAL CURRENCY SCHEMA:**
```sql
-- currency_data table structure:
date (DATE)
from_currency (STRING)  -- 'USD'
to_currency (STRING)    -- 'BRL', 'CNY', etc.
rate (FLOAT)
source_name (STRING)
confidence_score (FLOAT)
```

**CORRECT QUERY PATTERN:**
```sql
-- WRONG (causes errors):
SELECT * FROM currency_data WHERE indicator = 'usd_brl_rate'

-- RIGHT:
SELECT * FROM currency_data WHERE from_currency = 'USD' AND to_currency = 'BRL'
```

### 3. **PALM OIL DATA STALENESS**
**Problem:** Palm oil data stops updating after September 15, 2025
**Root Cause:** CPO=F ticker may be delisted or changed

**CURRENT STATUS:**
- Last data: 2025-09-15 (42+ days old)
- Symbol: CPO (Malaysian palm oil futures)
- Rows: 1,229 historical records

**PERMANENT SOLUTION:**
```python
# Use multiple palm oil sources:
PALM_OIL_SOURCES = [
    'CPO=F',      # Primary Malaysian futures
    'FCPO=F',     # Bursa Malaysia futures  
    'PKO=F',      # Palm kernel oil
    # Fallback to palm oil ETF or related commodities
]
```

### 4. **WEATHER DATA CORRUPTION PATTERN**
**Problem:** Weather APIs return -999 for missing data
**Root Cause:** Missing data markers not handled properly

**CORRUPTION PATTERN:**
- Temperature: -999°C (impossible value)
- Precipitation: -999mm (impossible value)
- These should be NULL, not -999

**PERMANENT FIX:**
```sql
-- Always clean weather data on ingestion:
UPDATE weather_table 
SET 
    temp_avg_c = CASE WHEN temp_avg_c = -999 THEN NULL ELSE temp_avg_c END,
    precip_mm = CASE WHEN precip_mm = -999 THEN NULL ELSE precip_mm END
WHERE temp_avg_c = -999 OR precip_mm = -999
```

---

## 🛠️ PERMANENT SOLUTIONS IMPLEMENTED

### 1. **Data Source Mapping (NEVER CHANGE):**
```python
PERMANENT_DATA_SOURCES = {
    # Commodities (working)
    'soybean_oil': 'soybean_oil_prices',
    'corn': 'corn_prices', 
    'crude_oil': 'crude_oil_prices',
    'palm_oil': 'palm_oil_prices',  # BUT NEEDS REFRESH
    
    # Forex (working but different schema)
    'forex': 'currency_data',  # Use from_currency/to_currency, NOT indicator
    
    # Economic (working)
    'economic': 'economic_indicators',  # Use indicator column
    
    # Sentiment (working)
    'social': 'social_sentiment',
    'news': 'news_intelligence',
    
    # Weather (working but needs -999 cleaning)
    'weather_brazil': 'weather_brazil_daily',
    'weather_argentina': 'weather_argentina_daily', 
    'weather_us': 'weather_us_midwest_daily',
    
    # Missing/Broken
    'trump_intel': 'trump_policy_intelligence',  # NOT ice_trump_intelligence
    'silver': 'economic_indicators WHERE indicator = "silver"'  # NOT silver_prices
}
```

### 2. **Data Freshness Requirements:**
```python
FRESHNESS_REQUIREMENTS = {
    'commodities': 2,    # Must be ≤2 days old
    'forex': 7,          # Must be ≤7 days old  
    'economic': 30,      # Must be ≤30 days old
    'sentiment': 7,      # Must be ≤7 days old
    'weather': 14,       # Must be ≤14 days old
}
```

### 3. **Automated Data Refresh (WORKING):**
- **Bidaily pulls:** 8:00 AM, 6:00 PM daily
- **Social intelligence:** 10:00 AM, 4:00 PM daily  
- **Weather:** 6:00 AM, 7:00 AM daily
- **China/Trump intel:** Every 4-6 hours

**Issue:** FRED API down due to government shutdown (affects economic data)

---

## 🎯 CURRENT V4 RETRAINING STATUS

### **WHAT WE HAVE (VERIFIED):**
✅ **Soybean Oil:** Current (0 days old) - 1,261 rows  
✅ **Corn:** Current (0 days old) - 1,261 rows  
✅ **Economic Indicators:** Current (0 days old) - 71,821 rows  
✅ **News Intelligence:** Current (0 days old) - 551 recent articles  
✅ **Currency Data:** 59,102 rows (schema fixed)  

### **WHAT'S MISSING/STALE:**
❌ **Palm Oil:** 42 days old (last: 2025-09-15)  
❌ **Crude Oil:** 6 days old  
❌ **Weather:** 14-17 days old  
❌ **Trump Intelligence:** Table doesn't exist (wrong name)  
❌ **Silver Prices:** Table doesn't exist (data is in economic_indicators)  

### **IMMEDIATE FIXES NEEDED:**

1. **Fix Palm Oil Data Source:**
```bash
# Try alternative palm oil tickers
python3 -c "
import yfinance as yf
symbols = ['FCPO=F', 'PKO=F', 'CPO=F']
for symbol in symbols:
    try:
        data = yf.Ticker(symbol).history(period='5d')
        if not data.empty:
            print(f'✅ {symbol}: Working - Latest: {data.index[-1].date()}')
        else:
            print(f'❌ {symbol}: No data')
    except:
        print(f'❌ {symbol}: Error')
"
```

2. **Fix Table Name References:**
```python
# Update all scripts to use correct table names
TABLE_NAME_FIXES = {
    'ice_trump_intelligence': 'trump_policy_intelligence',
    'silver_prices': 'economic_indicators (WHERE indicator = "silver")',
}
```

3. **Fix Currency Data Queries:**
```sql
-- WRONG:
WHERE indicator = 'usd_brl_rate'

-- RIGHT: 
WHERE from_currency = 'USD' AND to_currency = 'BRL'
```

---

## 🔧 EXECUTE FIXES NOW

### Fix 1: Update Palm Oil Source
```python
# Use FCPO=F (Bursa Malaysia) instead of CPO=F
PALM_OIL_SYMBOL = 'FCPO=F'  # Malaysian palm oil futures
```

### Fix 2: Create Missing Tables
```sql
-- Create ice_trump_intelligence as alias
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.ice_trump_intelligence` AS
SELECT * FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`;

-- Create silver_prices as alias  
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.silver_prices` AS
SELECT 
    time,
    'SILVER' as symbol,
    value as close,
    NULL as volume,
    value as high,
    value as low,
    value as open,
    source_name,
    confidence_score,
    ingest_timestamp_utc
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
WHERE indicator = 'silver';
```

### Fix 3: Update All Scripts
**Files that need permanent updates:**
- `comprehensive_data_guardrails.py`
- `data_verification_only.py` 
- `emergency_data_refresh.py`
- All ingestion scripts in `cbi-v14-ingestion/`

---

## 📋 NEVER FORGET CHECKLIST

**Before ANY data operation:**
1. ✅ Check actual table names in BigQuery (don't assume)
2. ✅ Verify schema before writing queries
3. ✅ Test with LIMIT 1 before full queries
4. ✅ Use guardrails to validate data ranges
5. ✅ Cross-check with external sources (Yahoo Finance)

**Data Quality Rules:**
1. ✅ Replace -999 with NULL (weather data)
2. ✅ Remove impossible prices (palm oil $0.05)
3. ✅ Remove future dates (economic indicators)
4. ✅ Deduplicate by date (keep latest)
5. ✅ Validate against external sources

---

## 🎯 ACTION PLAN

**IMMEDIATE (Next 30 minutes):**
1. Create missing table aliases (ice_trump_intelligence, silver_prices)
2. Fix palm oil data source (try FCPO=F)
3. Update currency data queries (use from_currency/to_currency)
4. Refresh stale commodity data

**THEN:**
5. Run V4 model retraining with ALL data
6. Update MASTER_TRAINING_PLAN.md with fixes
7. Never have these issues again!

---

**DOCUMENTED:** October 27, 2025 - PERMANENT REFERENCE**




