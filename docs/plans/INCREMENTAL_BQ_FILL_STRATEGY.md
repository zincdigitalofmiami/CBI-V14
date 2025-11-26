# Incremental BigQuery Fill Strategy

**Date:** November 26, 2025  
**Status:** 📋 Strategy Document  
**Approach:** Start with symbols (raw data), slowly add features

---

## 🎯 EXECUTIVE SUMMARY

**Your Plan:**
1. ✅ Framework must be in place first
2. ✅ Start with symbols (raw data) - little at a time
3. ✅ Slowly add features incrementally

**My Assessment:**
- ✅ **Framework is mostly in place** (schemas exist, scripts exist)
- ⚠️ **Need to verify/standardize** (multiple schema files exist)
- ✅ **Incremental approach is EXCELLENT** (low risk, testable)
- 📋 **Recommended order:** Symbols → Simple features → Complex features

---

## ✅ FRAMEWORK STATUS

### What's Already in Place:

1. **✅ Datasets Defined:**
   - `market_data` - Raw market data (Databento, Yahoo)
   - `raw_intelligence` - Economic, weather, policy data
   - `features` - Calculated features
   - `training` - Training datasets
   - `predictions` - Model predictions
   - All in `us-central1` ✅

2. **✅ Schema Files Exist:**
   - `sql/schemas/PRODUCTION_READY_BQ_SCHEMA.sql`
   - `sql/schemas/COMPLETE_BIGQUERY_SCHEMA.sql`
   - `sql/schemas/FINAL_COMPLETE_BQ_SCHEMA.sql`
   - Multiple versions (need to standardize)

3. **✅ Loading Scripts Exist:**
   - `scripts/migration/load_all_external_drive_data.py`
   - `scripts/migration/load_from_external_drive.py`
   - `scripts/migration/week3_bigquery_load_all.py`

4. **✅ Architecture Plan:**
   - `docs/plans/BIGQUERY_LIVE_FEEDS_ARCHITECTURE_PLAN.md`
   - Clear data flow defined
   - Partitioning/clustering strategy

### What Needs Verification:

1. **⚠️ Schema Standardization:**
   - Multiple schema files exist
   - Need to pick ONE canonical schema
   - Verify tables match architecture plan

2. **⚠️ Table Creation:**
   - Verify tables exist in BigQuery
   - Check partitioning/clustering
   - Verify column names match scripts

3. **⚠️ Data Quality:**
   - MERGE/UPSERT logic (prevent duplicates)
   - Partition expiration settings
   - Data validation checks

---

## 📋 RECOMMENDED INCREMENTAL APPROACH

### Phase 1: Framework Verification (Week 1)

**Goal:** Ensure framework is solid before loading data

**Tasks:**
1. **Pick canonical schema:**
   - Review all schema files
   - Choose ONE (recommend: `PRODUCTION_READY_BQ_SCHEMA.sql`)
   - Document why this one

2. **Verify BigQuery state:**
   ```sql
   -- Check what exists
   SELECT table_schema, table_name, row_count, size_bytes
   FROM `cbi-v14.INFORMATION_SCHEMA.TABLES`
   WHERE table_schema IN ('market_data', 'raw_intelligence', 'features')
   ORDER BY table_schema, table_name;
   ```

3. **Create missing tables:**
   - Start with `market_data` dataset
   - Create core tables (one symbol at a time)
   - Verify partitioning/clustering

4. **Test load script:**
   - Load ONE symbol (ZL) as test
   - Verify data quality
   - Check costs/queries

---

### Phase 2: Symbols First (Weeks 2-4)

**Goal:** Load raw price data for all symbols, one at a time

**Order:**
1. **ZL (Soybean Oil)** - Primary asset
2. **ZS (Soybeans)** - Related
3. **ZM (Soybean Meal)** - Related
4. **ZC (Corn)** - Related
5. **ZW (Wheat)** - Related
6. **6L (BRL/USD)** - FX
7. **6E (EUR/USD)** - FX
8. **CL (Crude Oil)** - Energy
9. **Others** - As needed

**For Each Symbol:**
1. **Create table** (if not exists):
   ```sql
   CREATE TABLE IF NOT EXISTS `cbi-v14.market_data.databento_futures_ohlcv_1m` (
     ts_event TIMESTAMP NOT NULL,
     root STRING NOT NULL,
     symbol STRING NOT NULL,
     open FLOAT64,
     high FLOAT64,
     low FLOAT64,
     close FLOAT64,
     volume INT64,
     ingest_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
   )
   PARTITION BY DATE(ts_event)
   CLUSTER BY root, symbol;
   ```

2. **Load historical data:**
   - Use existing Parquet files
   - Load in date chunks (e.g., 1 year at a time)
   - Use MERGE to prevent duplicates

3. **Verify data:**
   - Check row counts
   - Check date ranges
   - Check for duplicates
   - Check partition pruning

4. **Test queries:**
   - Query by date (partition pruning)
   - Query by symbol (clustering)
   - Verify performance

**Script Pattern:**
```python
def load_symbol_incremental(symbol: str, start_date: str, end_date: str):
    """Load one symbol, one date range at a time."""
    # 1. Read Parquet for date range
    # 2. Transform to BigQuery format
    # 3. MERGE into BigQuery (prevent duplicates)
    # 4. Verify load
    # 5. Log progress
```

---

### Phase 3: Simple Features (Weeks 5-8)

**Goal:** Add basic features incrementally

**Order:**
1. **Returns** (1d, 7d, 30d) - Simple calculation
2. **Moving Averages** (SMA 5, 10, 20, 50, 100) - Window functions
3. **Volatility** (Realized vol 5, 10, 20, 30-day) - STDDEV
4. **RSI** (7, 14 periods) - More complex
5. **MACD** (Line, Signal, Histogram) - Complex

**For Each Feature:**
1. **Create feature table** (if needed):
   ```sql
   CREATE TABLE IF NOT EXISTS `cbi-v14.features.symbol_features_daily` (
     date DATE NOT NULL,
     symbol STRING NOT NULL,
     return_1d FLOAT64,
     return_7d FLOAT64,
     return_30d FLOAT64,
     sma_5 FLOAT64,
     sma_10 FLOAT64,
     -- ... more features
   )
   PARTITION BY date
   CLUSTER BY symbol;
   ```

2. **Calculate in BigQuery SQL:**
   ```sql
   CREATE OR REPLACE TABLE `cbi-v14.features.symbol_features_daily` AS
   WITH daily_prices AS (
     SELECT 
       DATE(ts_event) as date,
       symbol,
       close,
       LAG(close) OVER (PARTITION BY symbol ORDER BY ts_event) as prev_close
     FROM `cbi-v14.market_data.databento_futures_ohlcv_1m`
     WHERE root = 'ZL'
   )
   SELECT 
     date,
     symbol,
     (close - prev_close) / prev_close as return_1d,
     AVG(close) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) as sma_5
   FROM daily_prices;
   ```

3. **Verify features:**
   - Check calculations
   - Check for NULLs
   - Check date alignment

4. **Test joins:**
   - Join features with raw data
   - Verify performance

---

### Phase 4: Complex Features (Weeks 9-12)

**Goal:** Add cross-asset and complex features

**Order:**
1. **Cross-symbol correlations** (ZL-ZS, ZL-ZM, etc.)
2. **FX features** (BRL, CNY, EUR correlations)
3. **Economic features** (FRED data joins)
4. **Weather features** (NOAA data joins)
5. **Regime features** (volatility regimes, trend regimes)

**For Each Feature Type:**
1. **Requires multiple symbols/data sources**
2. **Calculate in BigQuery SQL** (joins, window functions)
3. **Verify cross-asset alignment**
4. **Test performance** (large joins)

---

## 🏗️ FRAMEWORK REQUIREMENTS

### Must-Have Before Starting:

1. **✅ Canonical Schema:**
   - ONE source of truth
   - Documented
   - Version controlled

2. **✅ Table Creation Scripts:**
   - Idempotent (CREATE IF NOT EXISTS)
   - Partitioning/clustering
   - Column types correct

3. **✅ Loading Scripts:**
   - MERGE logic (prevent duplicates)
   - Error handling
   - Progress logging
   - Data validation

4. **✅ Data Quality Checks:**
   - Duplicate detection
   - NULL checks
   - Date range validation
   - Row count verification

5. **✅ Cost Monitoring:**
   - Query cost tracking
   - Storage cost tracking
   - Alert on unexpected costs

---

## 📊 RECOMMENDED SYMBOL LOADING ORDER

### Priority 1: Core ZL Ecosystem
1. **ZL** (Soybean Oil) - Primary asset
2. **ZS** (Soybeans) - Input
3. **ZM** (Soybean Meal) - Byproduct
4. **ZC** (Corn) - Related crop
5. **ZW** (Wheat) - Related crop

### Priority 2: FX (Critical for Export)
6. **6L** (BRL/USD) - Brazil export competitiveness
7. **CNH** (CNY/USD) - China trade
8. **6E** (EUR/USD) - European market

### Priority 3: Energy (Biofuel Link)
9. **CL** (Crude Oil) - Biofuel pricing
10. **HO** (Heating Oil) - Biofuel spread

### Priority 4: Others
11. **ES** (S&P 500) - Risk asset
12. **NQ** (Nasdaq) - Risk asset
13. **Others** - As needed

---

## 🔧 TECHNICAL CONSIDERATIONS

### 1. MERGE vs INSERT

**Use MERGE (Recommended):**
```sql
MERGE `cbi-v14.market_data.databento_futures_ohlcv_1m` AS target
USING source_data AS source
ON target.ts_event = source.ts_event 
   AND target.symbol = source.symbol
   AND target.root = source.root
WHEN MATCHED THEN
  UPDATE SET 
    open = source.open,
    high = source.high,
    -- ... update all columns
WHEN NOT MATCHED THEN
  INSERT (ts_event, root, symbol, open, high, low, close, volume)
  VALUES (source.ts_event, source.root, source.symbol, ...);
```

**Why:**
- Prevents duplicates
- Handles updates
- Idempotent (safe to re-run)

### 2. Incremental Loading

**Load by Date Range:**
```python
def load_symbol_by_date_range(symbol: str, start: str, end: str):
    """Load one symbol, one date range."""
    # Read Parquet for date range
    df = pd.read_parquet(file, filters=[('date', '>=', start), ('date', '<', end)])
    
    # Transform
    df['ts_event'] = pd.to_datetime(df['date'])
    df['root'] = symbol.split('.')[0]
    df['symbol'] = symbol
    
    # MERGE to BigQuery
    # Verify
```

**Benefits:**
- Testable (small chunks)
- Recoverable (if one chunk fails)
- Progress tracking

### 3. Data Validation

**After Each Load:**
```python
def validate_load(table_id: str, expected_rows: int, date_range: tuple):
    """Validate loaded data."""
    query = f"""
    SELECT 
      COUNT(*) as row_count,
      MIN(ts_event) as min_date,
      MAX(ts_event) as max_date,
      COUNT(DISTINCT symbol) as symbol_count
    FROM `{table_id}`
    WHERE DATE(ts_event) BETWEEN '{date_range[0]}' AND '{date_range[1]}'
    """
    result = client.query(query).to_dataframe()
    
    assert result['row_count'].iloc[0] == expected_rows
    assert result['min_date'].iloc[0] >= date_range[0]
    assert result['max_date'].iloc[0] <= date_range[1]
```

---

## ⚠️ RISKS & MITIGATION

### Risk 1: Duplicate Data
**Mitigation:**
- Use MERGE (not INSERT)
- Check for duplicates before load
- Validate after load

### Risk 2: Schema Mismatch
**Mitigation:**
- Standardize schema first
- Validate column types
- Test with small sample

### Risk 3: Cost Overruns
**Mitigation:**
- Monitor query costs
- Use partition pruning
- Load in small chunks
- Set budget alerts

### Risk 4: Data Quality Issues
**Mitigation:**
- Validate after each load
- Check for NULLs
- Check date ranges
- Check row counts

---

## ✅ SUCCESS CRITERIA

### Framework Ready When:
- [ ] Canonical schema chosen and documented
- [ ] All core tables created (or creation scripts ready)
- [ ] Loading scripts tested with ONE symbol
- [ ] MERGE logic verified (no duplicates)
- [ ] Data validation working
- [ ] Cost monitoring in place

### Phase 1 Complete When:
- [ ] ZL loaded and verified
- [ ] Queries work (partition pruning)
- [ ] No duplicates
- [ ] Costs acceptable

### Phase 2 Complete When:
- [ ] All core symbols loaded (ZL, ZS, ZM, ZC, ZW)
- [ ] FX symbols loaded (6L, CNH, 6E)
- [ ] All data validated
- [ ] Ready for features

---

## 📋 NEXT STEPS

1. **Verify Framework:**
   - Review schema files
   - Pick canonical schema
   - Verify BigQuery state

2. **Create Test Table:**
   - Create `market_data.databento_futures_ohlcv_1m`
   - Test with ZL only
   - Verify partitioning/clustering

3. **Load First Symbol:**
   - Load ZL (1 year at a time)
   - Verify data quality
   - Test queries

4. **Iterate:**
   - Add more symbols
   - Add simple features
   - Add complex features

---

## 🎯 MY RECOMMENDATION

**Your approach is EXCELLENT.** Here's why:

✅ **Low Risk:** Incremental = testable, recoverable  
✅ **Cost Control:** Small loads = predictable costs  
✅ **Quality:** Validate each step  
✅ **Learning:** Understand system as you go  

**Framework Status:**
- ✅ Mostly ready (schemas exist, scripts exist)
- ⚠️ Need to standardize (pick ONE schema)
- ⚠️ Need to verify (check BigQuery state)

**Start With:**
1. Pick canonical schema
2. Verify/create core tables
3. Load ZL only (test)
4. Then expand incrementally

**This is the right approach.** 🎯

---

**Last Updated:** November 26, 2025


