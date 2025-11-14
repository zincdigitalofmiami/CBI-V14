# Yahoo Finance Data Retrieval - Best Practices Implementation

**Date**: November 6, 2025  
**Purpose**: Safe, compliant, verified data retrieval from Yahoo Finance  

---

## 1. Rate Limiting Strategy

### Implementation:
```python
import time
from datetime import datetime, timedelta

RATE_LIMITS = {
    'per_symbol_delay': 2.0,      # 2 seconds between symbols
    'batch_size': 10,              # Max 10 symbols at once
    'batch_delay': 30.0,           # 30 seconds between batches
    'retry_delay': 60.0,           # 1 minute on error
    'max_retries': 3,              # Max 3 retry attempts
}

def rate_limited_fetch(symbol, delay=2.0):
    """Fetch with rate limiting"""
    time.sleep(delay)
    # ... fetch logic ...
```

### Rationale:
- Prevents being blocked by Yahoo
- Spreads load over time
- Respectful of free API access

---

## 2. Caching Strategy

### Implementation:
```python
import pickle
from pathlib import Path

CACHE_DIR = Path('/Users/zincdigital/CBI-V14/cache/yahoo_finance')
CACHE_EXPIRY_HOURS = 24  # Refresh daily

def get_cached_data(symbol, start_date):
    """Check cache before hitting Yahoo API"""
    cache_file = CACHE_DIR / f"{symbol}_{start_date}.pkl"
    
    if cache_file.exists():
        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if cache_age.total_seconds() < CACHE_EXPIRY_HOURS * 3600:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
    
    return None

def save_to_cache(symbol, start_date, data):
    """Save to cache"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{symbol}_{start_date}.pkl"
    with open(cache_file, 'wb') as f:
        pickle.dump(data, f)
```

### Benefits:
- Avoid re-downloading same historical data
- Faster subsequent runs
- Reduced API calls

---

## 3. Terms of Service Compliance

### Yahoo Finance ToS Key Points:
- ✅ **Personal/Research Use**: Allowed for non-commercial research
- ✅ **Academic/Educational**: Explicitly permitted
- ⚠️ **Commercial Use**: Requires proper licensing
- ❌ **Redistribution**: Cannot redistribute raw Yahoo data
- ❌ **High-frequency**: No automated high-frequency polling

### Our Compliance:
- ✅ Research/academic forecasting platform
- ✅ Rate-limited (2+ seconds between calls)
- ✅ Daily refresh only (not high-frequency)
- ✅ Data processed/transformed (not redistributed raw)
- ✅ Cached to minimize API calls

### Documentation:
- Source attribution: "Market data from Yahoo Finance"
- Disclaimer: "Data provided for research purposes only"
- No raw data redistribution

---

## 4. Data Verification Strategy

### Cross-Verification Sources:
```python
VERIFICATION_SOURCES = {
    'primary': 'Yahoo Finance (yfinance)',
    'verify_against': [
        'TradingEconomics',      # Commercial source (we have access)
        'CME Group (official)',  # Official exchange data
        'Barchart',              # Alternative futures data
        'FRED (economic data)',  # Cross-check macro indicators
    ]
}
```

### Verification Process:
1. **Random Sampling**: Verify 10 random dates per symbol
2. **Recent Data**: Verify last 5 trading days against official CME
3. **Statistical Checks**: 
   - Price ranges within expected bounds
   - Volume patterns consistent
   - No impossible gaps (e.g., price jumps >50% in 1 day without cause)
4. **Cross-Source Delta**: 
   - Yahoo vs TradingEconomics: Allow <0.5% difference
   - Yahoo vs CME official: Must match exactly (or flag)

### Implementation:
```python
def verify_data_quality(df, symbol):
    """Multi-point verification"""
    issues = []
    
    # 1. Check for gaps
    date_range = pd.date_range(df['date'].min(), df['date'].max(), freq='B')
    expected_days = len(date_range)
    actual_days = len(df)
    gap_pct = (expected_days - actual_days) / expected_days * 100
    if gap_pct > 10:
        issues.append(f"⚠️ {gap_pct:.1f}% date gaps")
    
    # 2. Check for outliers
    returns = df['Close'].pct_change()
    outliers = returns[abs(returns) > 0.15]  # >15% daily move
    if len(outliers) > 0:
        issues.append(f"⚠️ {len(outliers)} extreme moves (>15%)")
    
    # 3. Check for duplicate dates
    duplicates = df['date'].duplicated().sum()
    if duplicates > 0:
        issues.append(f"❌ {duplicates} duplicate dates")
    
    # 4. Check for NULL values
    null_counts = df[['Open', 'High', 'Low', 'Close']].isnull().sum()
    if null_counts.sum() > 0:
        issues.append(f"❌ NULL values in OHLC")
    
    # 5. Sanity checks
    if (df['High'] < df['Low']).any():
        issues.append(f"❌ High < Low (impossible)")
    if (df['Close'] > df['High']).any() or (df['Close'] < df['Low']).any():
        issues.append(f"❌ Close outside High/Low range")
    
    return issues
```

---

## 5. Implementation Checklist

### Pre-Flight Checks:
- [ ] Verify yfinance library installed and version
- [ ] Test single symbol pull (ZL=F for 5 days)
- [ ] Verify BigQuery write permissions
- [ ] Check disk space for cache (6,300 rows × 10 symbols = ~63K rows cached)
- [ ] Backup existing production tables

### During Execution:
- [ ] Log every API call with timestamp
- [ ] Monitor rate limit compliance (2+ seconds between calls)
- [ ] Capture and log any errors
- [ ] Verify each symbol before moving to next
- [ ] Random spot-checks against TradingEconomics

### Post-Execution:
- [ ] Compare row counts (expected vs actual)
- [ ] Verify date continuity (no unexpected gaps)
- [ ] Cross-verify 10 random dates against CME/TradingEconomics
- [ ] Check technical indicator calculations (spot check RSI/MACD values)
- [ ] Validate schema alignment with production tables

---

## 6. Error Handling & Rollback

### Error Types:
1. **API Errors** (404, 500, timeout):
   - Retry with exponential backoff
   - Skip symbol if 3 failures
   - Log and continue with other symbols

2. **Data Quality Errors**:
   - Flag but don't reject (log for review)
   - Allow human verification

3. **Schema Errors**:
   - STOP immediately
   - Rollback any partial writes
   - Fix schema mapping before retry

### Rollback Procedure:
```sql
-- If anything goes wrong, restore from backup:
DROP TABLE `cbi-v14.models_v4.production_training_data_1m`;
CREATE TABLE `cbi-v14.models_v4.production_training_data_1m` 
AS SELECT * FROM `cbi-v14.archive_consolidation_nov6.production_1m_backup_20251106`;
```

---

## 7. Attribution & Compliance

### Source Attribution (in BigQuery):
```sql
ALTER TABLE `cbi-v14.models_v4.production_training_data_1m`
ADD COLUMN IF NOT EXISTS data_source_attribution STRING;

UPDATE `cbi-v14.models_v4.production_training_data_1m`
SET data_source_attribution = 'Yahoo Finance (yfinance) - Research use only'
WHERE date >= '2000-01-01';
```

### Disclaimer (in code):
```python
DISCLAIMER = """
Market data provided by Yahoo Finance via yfinance library.
Data is for research and educational purposes only.
Not intended for commercial redistribution.
Please verify critical data points with official exchange sources.
"""
```

---

## 8. Safe Execution Plan

### Phase 1: TEST (Don't touch production)
1. Pull ZL=F data for last 30 days only
2. Calculate all 6 MAs + RSI + MACD
3. Save to `market_data.yahoo_test_zl`
4. Manually verify 5 random dates
5. Check technical indicators match TradingView/official

### Phase 2: STAGING (Full pull, staging table)
1. Pull all symbols (ZL, ZS, ZM, etc.) for 20 years
2. Calculate all technical indicators
3. Save to `market_data.yahoo_finance_20yr_STAGING`
4. Run full verification suite
5. Cross-check 10 random dates vs TradingEconomics

### Phase 3: INTEGRATION (Merge to production)
1. Backup production tables (already done)
2. Create mapping SQL with column name alignment
3. Test merge on 10 rows only
4. Verify merged data quality
5. Execute full merge if test passes

### Phase 4: VALIDATION
1. Check row counts match expected
2. Verify no data loss
3. Spot-check technical indicators
4. Export to Parquet and test local Mac M4 training (BQML deprecated)
5. Document any discrepancies

---

## Ready to Execute?

**Proposed execution**:
- Start with Phase 1 (TEST - 30 days, ZL only)
- Show you results for approval
- Then proceed to full 20-year pull

This keeps us compliant, safe, and verified at every step.

Should I proceed with Phase 1 test?






