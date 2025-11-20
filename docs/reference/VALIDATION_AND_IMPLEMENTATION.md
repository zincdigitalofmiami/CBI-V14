---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# CBI-V14 Validation & Implementation Plan
**Date**: November 18, 2025  
**Status**: Pre-Implementation Validation Required  
**Purpose**: Triple-check DataBento capabilities before any code changes

---

## CRITICAL: Validation Phase (MUST DO FIRST)

### Step 1: Verify DataBento Subscription

**Run this command** to verify your DataBento access:

```bash
export DATABENTO_API_KEY="$(security find-generic-password -a default -s cbi-v14.DATABENTO_API_KEY -w 2>/dev/null)"

python3 <<EOF
import databento as db
import os

api_key = os.environ.get('DATABENTO_API_KEY')
if not api_key:
    print('ERROR: DATABENTO_API_KEY not in keychain')
    print('Store it: security add-generic-password -a default -s cbi-v14.DATABENTO_API_KEY -w YOUR_KEY -U')
    exit(1)

client = db.Historical(api_key)

# List all datasets
print('='*80)
print('AVAILABLE DATASETS')
print('='*80)
datasets = client.metadata.list_datasets()
for ds in datasets:
    print(f'  {ds}')

# Check GLBX.MDP3 specifically
print('\n' + '='*80)
print('GLBX.MDP3 DETAILS')
print('='*80)
try:
    schemas = client.metadata.list_schemas('GLBX.MDP3')
    print(f'Available schemas: {schemas}')
    
    range_info = client.metadata.get_dataset_range('GLBX.MDP3')
    print(f'Start: {range_info.get("start")}')
    print(f'End: {range_info.get("end")}')
    
    # Check specific symbols
    print('\n' + '='*80)
    print('SYMBOL VERIFICATION (Sample)')
    print('='*80)
    test_symbols = ['ZL.FUT', 'ES.FUT', 'MES.FUT']
    for sym in test_symbols:
        try:
            data = client.timeseries.get_range(
                dataset='GLBX.MDP3',
                symbols=[sym],
                stype_in='parent',
                schema='ohlcv-1d',
                start='2024-01-01',
                end='2024-01-05',
                limit=5
            )
            df = data.to_df() if hasattr(data, 'to_df') else data
            print(f'  ✅ {sym}: {len(df)} records')
        except Exception as e:
            print(f'  ❌ {sym}: {e}')
    
except Exception as e:
    print(f'ERROR: {e}')

print('\n' + '='*80)
print('VALIDATION COMPLETE')
print('='*80)
EOF
```

**Expected Output**:
- ✅ List of datasets (should include GLBX.MDP3)
- ✅ Schemas: ohlcv-1m, ohlcv-1d, trades, tbbo, etc.
- ✅ Date range: 2010-06-06 to present
- ✅ All test symbols return data

**If ANY of these fail, STOP and contact DataBento support before proceeding.**

---

### Step 2: Validate ALL 13 Symbols

**Run this to check all required symbols**:

```bash
export DATABENTO_API_KEY="$(security find-generic-password -a default -s cbi-v14.DATABENTO_API_KEY -w)"

python3 <<EOF
import databento as db
import os

api_key = os.environ.get('DATABENTO_API_KEY')
client = db.Historical(api_key)

# All 13 symbols from universe
symbols = [
    'ES.FUT',   # S&P 500 E-mini
    'MES.FUT',  # Micro E-mini S&P 500
    'ZL.FUT',   # Soybean Oil
    'ZS.FUT',   # Soybeans
    'ZM.FUT',   # Soybean Meal
    'CL.FUT',   # WTI Crude
    'NG.FUT',   # Natural Gas
    'ZC.FUT',   # Corn
    'ZW.FUT',   # Wheat
    'RB.FUT',   # RBOB Gasoline
    'HO.FUT',   # Heating Oil
    'GC.FUT',   # Gold
    'SI.FUT',   # Silver
    'HG.FUT',   # Copper
]

print('='*80)
print('VALIDATING ALL 13 SYMBOLS')
print('='*80)

success = []
failed = []

for sym in symbols:
    try:
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            symbols=[sym],
            stype_in='parent',
            schema='ohlcv-1d',
            start='2024-11-01',
            end='2024-11-15',
            limit=10
        )
        df = data.to_df() if hasattr(data, 'to_df') else data
        success.append(f'{sym}: {len(df)} records')
        print(f'  ✅ {sym}: {len(df)} records')
    except Exception as e:
        failed.append(f'{sym}: {str(e)[:100]}')
        print(f'  ❌ {sym}: {str(e)[:100]}')

print('\n' + '='*80)
print('RESULTS')
print('='*80)
print(f'Success: {len(success)}/14')
print(f'Failed: {len(failed)}/14')

if failed:
    print('\n⚠️  FAILED SYMBOLS:')
    for f in failed:
        print(f'  {f}')
    print('\n🛑 DO NOT PROCEED until all symbols validate')
else:
    print('\n✅ ALL SYMBOLS VALIDATED - OK TO PROCEED')
EOF
```

**Required Result**: ALL 13 symbols must return data

---

### Step 3: Check DataBento Rate Limits

**Verify your plan includes**:
- ✅ GLBX.MDP3 access
- ✅ Unlimited API calls (or sufficient quota)
- ✅ 1-minute OHLCV schema
- ✅ Parent symbology support

**Contact DataBento if**:
- Rate limits are too low for 5-min pulls on 3 symbols
- Historical data starts after 2010-06-06
- Any symbols return 403/404 errors

---

### Step 4: Validate FX Coverage (DataBento vs Yahoo)

DataBento offers **futures-based FX** (e.g., 6E for EUR/USD futures), NOT spot FX.

**Check if available**:

```bash
export DATABENTO_API_KEY="$(security find-generic-password -a default -s cbi-v14.DATABENTO_API_KEY -w)"

python3 <<EOF
import databento as db
import os

api_key = os.environ.get('DATABENTO_API_KEY')
client = db.Historical(api_key)

fx_futures = [
    '6E.FUT',  # EUR/USD futures
    '6B.FUT',  # GBP/USD futures
    '6J.FUT',  # JPY/USD futures
    '6A.FUT',  # AUD/USD futures
    '6C.FUT',  # CAD/USD futures
]

print('='*80)
print('FX FUTURES VALIDATION')
print('='*80)

available = []
not_available = []

for sym in fx_futures:
    try:
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            symbols=[sym],
            stype_in='parent',
            schema='ohlcv-1d',
            start='2024-11-01',
            end='2024-11-05',
            limit=5
        )
        available.append(sym)
        print(f'  ✅ {sym}: Available')
    except Exception as e:
        not_available.append(sym)
        print(f'  ❌ {sym}: Not available')

print('\n' + '='*80)
if available:
    print('✅ Use DataBento for FX futures:', ', '.join(available))
if not_available:
    print('⚠️  Use Yahoo for spot FX (DataBento doesnt have):', ', '.join(not_available))
EOF
```

**Decision**:
- If DataBento has FX futures: Use DataBento
- If not: Use Yahoo for spot FX (EUR/USD, GBP/USD, etc.)

---

## Implementation Phase (After Validation Passes)

### Phase 1: Create BigQuery Tables (Schema Lock-Down)

**DO THIS FIRST** - Schema changes after data ingestion are painful.

```bash
# Review all table schemas
cat <<SQL > /tmp/create_tables.sql
-- All CREATE TABLE statements from PRODUCTION_DATA_ARCHITECTURE.md
-- Copy from Part 3: BigQuery Schema

-- Table 1: market_data.futures_ohlcv_1m
CREATE TABLE market_data.futures_ohlcv_1m (...);

-- Table 2: Keep existing raw_intelligence.fred_economic
-- DO NOT MODIFY

-- Table 3: raw_intelligence.weather_segmented
CREATE TABLE raw_intelligence.weather_segmented (...);

-- Table 4-10: All other tables
...
SQL

# Execute (after review)
bq query --use_legacy_sql=false < /tmp/create_tables.sql
```

**Validate tables created**:
```bash
bq ls market_data
bq ls raw_intelligence
bq ls regimes
bq ls drivers
bq ls drivers_of_drivers
bq ls signals
bq ls neural
```

---

### Phase 2: Set Up Collection Scripts

#### Script 1: `scripts/live/databento_collector_primary.py`

**Purpose**: 5-minute collection for ZL, MES, ES

```python
#!/usr/bin/env python3
"""
DataBento Primary Symbols Collector (5-minute pulls)
Collects ZL, MES, ES every 5 minutes
"""
import os
import databento as db
from google.cloud import bigquery
from datetime import datetime, timedelta

SYMBOLS = ['ZL.FUT', 'MES.FUT', 'ES.FUT']
PRIORITY_TIER = 1  # Primary symbols

def collect_and_upload():
    api_key = os.environ.get('DATABENTO_API_KEY')
    client = db.Historical(api_key)
    bq = bigquery.Client(project='cbi-v14')
    
    # Get last 10 minutes of data (overlap for safety)
    end = datetime.now()
    start = end - timedelta(minutes=10)
    
    for symbol in SYMBOLS:
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            symbols=[symbol],
            stype_in='parent',
            schema='ohlcv-1m',
            start=start.strftime('%Y-%m-%dT%H:%M:%S'),
            end=end.strftime('%Y-%m-%dT%H:%M:%S'),
        )
        
        df = data.to_df()
        if df.empty:
            continue
        
        # Add priority tier and metadata
        df['priority_tier'] = PRIORITY_TIER
        df['collection_timestamp'] = datetime.now()
        df['root'] = symbol.replace('.FUT', '')
        
        # Upload to BigQuery
        table_id = 'cbi-v14.market_data.futures_ohlcv_1m'
        job = bq.load_table_from_dataframe(df, table_id)
        job.result()
        
        print(f'✅ {symbol}: {len(df)} bars uploaded')

if __name__ == '__main__':
    collect_and_upload()
```

**Cron**:
```bash
*/5 * * * * cd /path/to/CBI-V14 && python3 scripts/live/databento_collector_primary.py >> Logs/databento_primary.log 2>&1
```

#### Script 2: `scripts/live/databento_collector_secondary.py`

**Purpose**: 1-hour collection for 11 secondary symbols

```python
#!/usr/bin/env python3
"""
DataBento Secondary Symbols Collector (1-hour pulls)
"""
# Similar to primary, but with:
SYMBOLS = ['ZS.FUT', 'ZM.FUT', 'CL.FUT', 'NG.FUT', 'ZC.FUT', 
           'ZW.FUT', 'RB.FUT', 'HO.FUT', 'GC.FUT', 'SI.FUT', 'HG.FUT']
PRIORITY_TIER = 2  # Secondary symbols
```

**Cron**:
```bash
0 * * * * cd /path/to/CBI-V14 && python3 scripts/live/databento_collector_secondary.py >> Logs/databento_secondary.log 2>&1
```

#### Script 3: Keep Existing FRED (DON'T TOUCH)

```bash
# Existing cron - don't modify
*/15 * * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_fred_comprehensive.py >> Logs/fred.log 2>&1
```

#### Script 4: `scripts/ingest/collect_weather_comprehensive.py`

**Purpose**: Daily weather for US/BR/AR with area code segmentation

```python
#!/usr/bin/env python3
"""
Weather collection with area code segmentation
"""
import argparse
from google.cloud import bigquery

# Area codes for each country
AREA_CODES = {
    'US': {
        'IL': 'Illinois (corn/soy)',
        'IN': 'Indiana (corn/soy)',
        'IA': 'Iowa (corn/soy)',
        # ... all corn/soy belt states
    },
    'BR': {
        'MG': 'Minas Gerais (soybean)',
        'GO': 'Goiás (soybean)',
        'MT': 'Mato Grosso (soybean)',
        # ... all Brazilian soybean states
    },
    'AR': {
        'BA': 'Buenos Aires (soybean)',
        'SF': 'Santa Fe (soybean)',
        'CO': 'Córdoba (soybean)',
        # ... all Argentine soybean provinces
    }
}

def collect_weather(countries):
    # Collect for each area code
    for country in countries:
        for area_code, description in AREA_CODES[country].items():
            # Collect weather data for this specific area
            # Upload to raw_intelligence.weather_segmented
            pass
```

**Cron**:
```bash
0 6 * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_weather_comprehensive.py --countries US,BR,AR --segment-by-area >> Logs/weather.log 2>&1
```

#### Script 5: `scripts/ingest/collect_news_breaking.py`

**Purpose**: 15-minute collection for breaking news on critical symbols

```python
#!/usr/bin/env python3
"""
Breaking news collector (15-minute pulls for critical symbols)
Buckets by topic, regime, correlation
"""
# Collect news mentioning ZL, ES, CL
# Bucket by:
# - topic_bucket (biofuel_policy, china_demand, weather, etc.)
# - regime (bull, bear, crisis, normal)
# - correlation_group (zl_soy_complex, crude_energy, macro)
# Upload to raw_intelligence.news_bucketed
```

**Cron**:
```bash
*/15 * * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_news_breaking.py --symbols ZL,ES,CL --priority critical >> Logs/news_breaking.log 2>&1
```

#### Script 6: `scripts/ingest/collect_cftc_comprehensive.py`

**Purpose**: 8-hour pulls for CFTC positioning

**Cron**:
```bash
0 */8 * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_cftc_comprehensive.py >> Logs/cftc.log 2>&1
```

---

### Phase 3: Set Up Processing Layers

#### Layer 1: Regime Classification

```bash
# Hourly regime classification
0 * * * * cd /path/to/CBI-V14 && python3 scripts/processing/classify_regimes.py >> Logs/regimes.log 2>&1
```

#### Layer 2: Driver Identification

```bash
# Daily driver analysis
0 3 * * * cd /path/to/CBI-V14 && python3 scripts/processing/identify_drivers.py >> Logs/drivers.log 2>&1
```

#### Layer 3: Meta-Driver Tracking

```bash
# Daily meta-driver analysis
0 4 * * * cd /path/to/CBI-V14 && python3 scripts/processing/track_meta_drivers.py >> Logs/meta_drivers.log 2>&1
```

#### Layer 4: Signal Calculation

```bash
# Hourly signal calculation
0 * * * * cd /path/to/CBI-V14 && python3 scripts/processing/calculate_signals.py >> Logs/signals.log 2>&1
```

#### Layer 5: Feature Vector Assembly

```bash
# Daily feature vector assembly
0 5 * * * cd /path/to/CBI-V14 && python3 scripts/processing/assemble_features.py >> Logs/features.log 2>&1
```

---

## Final Validation Checklist

Before going live:

### DataBento Validation
- [ ] All 13 symbols validated
- [ ] 1-minute OHLCV schema confirmed
- [ ] Rate limits sufficient for 5-min primary pulls
- [ ] Historical data available from 2010
- [ ] FX coverage verified (futures vs spot)

### BigQuery Schema
- [ ] All tables created with correct partitioning
- [ ] All tables clustered correctly
- [ ] Partition expiration set (365 days for 1m data)
- [ ] Existing FRED table NOT modified

### Collection Scripts
- [ ] Primary collector (5-min: ZL, MES, ES)
- [ ] Secondary collector (1-hr: 11 symbols)
- [ ] FRED collector (existing, NOT touched)
- [ ] Weather collector (daily, segmented by area)
- [ ] CFTC collector (8-hour pulls)
- [ ] News breaking (15-min for critical symbols)
- [ ] News general (1-hour for all)

### Processing Layers
- [ ] Regime classification (hourly)
- [ ] Driver identification (daily)
- [ ] Meta-driver tracking (daily)
- [ ] Signal calculation (hourly)
- [ ] Feature assembly (daily)

### Monitoring
- [ ] Cron jobs configured
- [ ] Log files created
- [ ] Error alerting set up
- [ ] Cost monitoring enabled

---

## Emergency Rollback Plan

If anything breaks:

1. **Stop all new cron jobs**:
```bash
crontab -e
# Comment out new jobs with #
```

2. **Revert to existing FRED-only collection**:
```bash
# Keep only:
*/15 * * * * python3 scripts/ingest/collect_fred_comprehensive.py
```

3. **Don't delete BigQuery tables** (they cost almost nothing empty)

4. **Review logs**:
```bash
tail -100 Logs/databento_primary.log
tail -100 Logs/databento_secondary.log
```

---

## Next Steps

1. **Run validation scripts** (Steps 1-4 above)
2. **If ALL validations pass**: Proceed with implementation
3. **If ANY validation fails**: STOP and resolve before proceeding
4. **Create tables** (Phase 1)
5. **Deploy collectors** (Phase 2, one at a time)
6. **Deploy processors** (Phase 3, after collectors stable)
7. **Monitor for 1 week** before adding more complexity

**DO NOT SKIP VALIDATION**


