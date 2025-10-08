<!-- ee9b3db8-1265-4f02-88ff-c20241b6d920 f97d9a3b-bafe-4b61-b7f6-62c44646faa6 -->
# Fix Plan: Broken Data Pipelines & Empty Tables

## Scope Confirmed by Owner: FALSE (Awaiting Approval)

## Owner Approval to Rewire: FALSE

## Report Type: Remediation Plan with Research-Backed Solutions

---

## PROBLEM SUMMARY (7 Critical Issues)

###  1. TradingEconomics Scraper Parser BROKEN

- **Evidence:** Returns 1021.0 for ALL commodities (palm, rapeseed, sunflower, soybean)
- **Impact:** Cannot use for real-time price updates
- **Root Cause:** `parse_te_value()` using wrong CSS selectors, not extracting from JavaScript `var model =` JSON

### 2. Currency_Data Table EMPTY (0 rows)

- **Evidence:** Scraper tried FX rates but failed to parse
- **Impact:** Cannot normalize MYR/BRL/ARS prices to USD
- **Root Cause:** Same broken parser issue

### 3. Fed_Rates Table EMPTY (0 rows)  

- **Evidence:** Table exists but no data
- **Impact:** Missing critical macro driver
- **Root Cause:** No active ingestion script OR script not running

### 4. Intelligence_Cycles Table EMPTY (0 rows)

- **Evidence:** Table created but never populated
- **Impact:** No intelligence summary tracking
- **Root Cause:** `master_intelligence_controller.py` exists but not scheduled/running

### 5. News_Intelligence SPARSE (20 rows - test data?)

- **Evidence:** 50+ sources defined, only 20 rows collected
- **Impact:** Missing critical news signals
- **Root Cause:** `multi_source_news.py` not running at scale OR rate-limited/blocked

### 6. Social_Sentiment SPARSE (20 rows)

- **Evidence:** Reddit monitoring defined, minimal data
- **Impact:** Missing sentiment signals
- **Root Cause:** `social_intelligence.py` not running regularly OR API limits

### 7. Canonical Metadata NOT IMPLEMENTED

- **Evidence:** Schema designed but only 4 tables updated
- **Impact:** Inconsistent data quality, no provenance tracking
- **Root Cause:** Partial implementation, 11+ scripts not updated

---

## RESEARCH-BACKED SOLUTIONS

### Solution 1: Fix TradingEconomics Parser

**Technical Approach (from GPT5 testing):**

1. Extract JavaScript `var model = {...}` JSON from `<script>` tags
2. Use symbol mapping: `{'palm-oil': 'PALM:COM', 'rapeseed': 'RAPS:COM', 'sunflower-oil': 'SUNO:COM'}`
3. Match `data['Symbol']` to expected symbol
4. Extract `data['Last']` for price

**Validation (from GPT5):**

- Palm oil: Should return ~1061.0 (not 1021.0)
- Rapeseed: Should return ~453.25
- Sunflower: Should return ~850.0

**Alternative if scraping fails:**

- Use FRED API for some commodities (free, reliable)
- Fall back to manual CSV uploads (Barchart data)
- Consider Alpha Vantage free tier (limited)

### Solution 2: Populate Currency_Data Table

**Options:**

A. Fix TradingEconomics FX scraper (same parser fix as above)

B. Use FRED API directly (more reliable):

   - Series codes: DEXBZUS (USD/BRL), DEXMAUS (USD/MYR), DEXUSAL (ARS/USD)
   - Already have `fred_economic_deployment.py` - extend it

C. Use existing `economic_indicators` table (already has USD/BRL, USD/CNY data)

**Recommendation:** Option C (use existing data) + Option B (add FRED FX as backup)

### Solution 3: Populate Fed_Rates Table

**Root Cause Analysis:**

- Check if `fred_economic_deployment.py` writes to `fed_rates` or `economic_indicators`
- **FOUND:** It writes to `economic_indicators` (fed_funds_rate has 731 rows there)
- **CONCLUSION:** `fed_rates` table is redundant - data already exists elsewhere

**Solution:**

- Create VIEW: `CREATE VIEW fed_rates AS SELECT time, value as rate FROM economic_indicators WHERE indicator='fed_funds_rate'`
- OR: Ignore empty table (data exists in economic_indicators)

### Solution 4: Populate Intelligence_Cycles Table

**Purpose:** Track intelligence collection cycles for monitoring

**Current State:** `master_intelligence_controller.py` has code to save cycles but isn't running

**Solution Options:**

A. Schedule `master_intelligence_controller.py` to run daily

B. Ignore table if not critical (intelligence data already in other tables)

C. Delete table if unused (reduce clutter)

**Recommendation:** Option B or C (not critical, data exists elsewhere)

### Solution 5: Increase News_Intelligence Volume

**Current:** 50+ sources defined, only 20 rows

**Why?** Script probably runs once as test, not scheduled

**Solution:**

1. Schedule `multi_source_news.py` to run every 6 hours
2. Add cron job: `0 */6 * * * python3 multi_source_news.py`
3. Monitor for rate limiting (add delays between sources)
4. Start with 10 highest-priority sources, expand gradually

**Expected:** 50-200 news items per day once fully operational

### Solution 6: Increase Social_Sentiment Volume

**Current:** Reddit monitoring, 20 rows

**Why sparse?** Not running regularly OR limited subreddits

**Solution:**

1. Schedule `social_intelligence.py` to run every 4 hours  
2. Expand subreddits (currently 5, could add 20+ ag-related)
3. Add Twitter/X if API access available (costs $100/month - probably NO)
4. Focus on Reddit (free, reliable)

**Expected:** 50-100 social posts per day

### Solution 7: Complete Canonical Schema Implementation

**Current:** 4 tables updated, 11+ scripts not updated

**Remaining work:**

- Update `fred_economic_deployment.py` - add source_name, confidence_score
- Update `ingest_weather_noaa.py` - add metadata
- Update `ingest_brazil_weather_inmet.py` - add metadata
- Update `ice_trump_intelligence.py` - add provenance_uuid
- Update `multi_source_news.py` - add metadata
- Update `social_intelligence.py` - add metadata
- Update remaining 5+ scripts

**Timeline:** 8-12 hours total (30-60 min per script)

---

## DATA VALIDATION FRAMEWORK (Prevent Future Corruption)

### Add Pre-Insert Validation:

```python
PRICE_RANGES = {
    'PALM_OIL': (700, 1200),      # USD/MT
    'SOYBEAN_OIL': (40, 80),      # cents/lb  
    'RAPESEED_OIL': (400, 600),   # USD/MT
    'SUNFLOWER_OIL': (800, 1100), # USD/MT
    'CRUDE_OIL': (50, 120),       # USD/barrel
}

def validate_price(symbol, price):
    if symbol not in PRICE_RANGES:
        return True  # Unknown commodity, allow
    
    min_price, max_price = PRICE_RANGES[symbol]
    if not (min_price <= price <= max_price):
        raise ValueError(f"{symbol} price {price} outside realistic range {min_price}-{max_price}")
    return True
```

### Add Duplicate Detection:

```python
def check_duplicate(df, table_name):
    # Check if this exact data already exists
    hash_col = df.apply(lambda row: hash(tuple(row)), axis=1)
    duplicates = hash_col.duplicated()
    if duplicates.any():
        logger.warning(f"Found {duplicates.sum()} duplicate rows")
        return df[~duplicates]
    return df
```

---

## 5-TASK REMEDIATION PLAN (Prioritized)

### Task 1: Fix TradingEconomics Parser (CRITICAL)

**Owner:** data-eng

**Hours:** 4-6

**Owner Approval:** REQUIRED

**Steps:**

1. Update `parse_te_value()` to extract from `var model = {...}` JSON
2. Add symbol mapping (PALM:COM, RAPS:COM, SUNO:COM)
3. Add price validation (reject unrealistic values)
4. Test on saved HTML files before deploying
5. Add fallback parsers if JavaScript extraction fails

**Acceptance Criteria:**

- [ ] Palm oil returns different price than rapeseed  
- [ ] Prices within realistic ranges (700-1200 for palm)
- [ ] Test query: prices for 3 commodities are NOT identical
- [ ] Scraper logs show "Found price X using model" messages

**Rollback:** Disable scraper, revert to broken version if worse

**Cost:** $0

---

### Task 2: Schedule Missing Ingestion Scripts

**Owner:** ops

**Hours:** 2-4

**Owner Approval:** REQUIRED

**Steps:**

1. Add cron job for `multi_source_news.py` (every 6 hours)
2. Add cron job for `social_intelligence.py` (every 4 hours)
3. Add cron job for `master_intelligence_controller.py` (daily)
4. Monitor logs for first 48 hours
5. Adjust frequency based on data volume

**Acceptance Criteria:**

- [ ] news_intelligence grows to 50+ rows per day
- [ ] social_sentiment grows to 20+ rows per day  
- [ ] intelligence_cycles gets 1 row per day
- [ ] Cron jobs visible in `crontab -l`

**Rollback:** Remove cron jobs

**Cost:** $0

---

### Task 3: Consolidate Redundant Tables (Clean Architecture)

**Owner:** data-eng

**Hours:** 2-3

**Owner Approval:** REQUIRED

**Analysis:**

- `fed_rates` table EMPTY but data exists in `economic_indicators` (fed_funds_rate, 731 rows)
- `currency_data` table EMPTY but FX data exists in `economic_indicators` (usd_brl_rate, usd_cny_rate, 494 rows each)
- `intelligence_cycles` table EMPTY, may not be needed

**Proposed Actions:**

1. Create VIEWS instead of duplicate tables:

   - `CREATE VIEW fed_rates AS SELECT time, value as rate FROM economic_indicators WHERE indicator='fed_funds_rate'`
   - `CREATE VIEW currency_data AS SELECT time, indicator as pair, value as rate FROM economic_indicators WHERE indicator LIKE '%_rate'`

2. OR: Delete empty tables if not used by Vite dashboard
3. Document which tables are SOURCE vs VIEW

**Acceptance Criteria:**

- [ ] No empty tables (either populated or deleted)
- [ ] Views created if data exists elsewhere
- [ ] Vite dashboard queries still work
- [ ] Documentation updated

**Rollback:** Recreate empty tables if views break dashboard

**Cost:** $0

---

### Task 4: Complete Canonical Schema Rollout

**Owner:** data-eng

**Hours:** 8-12

**Owner Approval:** REQUIRED

**Remaining Scripts to Update (11 total):**

1. fred_economic_deployment.py
2. ingest_weather_noaa.py
3. ingest_brazil_weather_inmet.py  
4. ice_trump_intelligence.py
5. multi_source_news.py
6. social_intelligence.py
7. ingest_volatility.py
8. ingest_executive_orders.py
9. ingest_whitehouse_rss.py
10. intelligence_hunter.py
11. economic_intelligence.py

**Changes per script:**

- Add: `source_name`, `confidence_score`, `ingest_timestamp_utc`, `provenance_uuid`
- Estimated: 30-60 min per script

**Acceptance Criteria:**

- [ ] Sample rows from each table show canonical fields populated
- [ ] Unit tests pass for metadata generation
- [ ] Query: `SELECT COUNT(*) FROM {table} WHERE source_name IS NOT NULL` returns >0

**Rollback:** Canonical fields are additive (won't break existing queries)

**Cost:** $0

---

### Task 5: Build Smart CSV Uploader Tool

**Owner:** dev

**Hours:** 6-8

**Owner Approval:** REQUIRED

**Purpose:** Web UI for drag-drop CSV upload to ANY BigQuery table

**Features:**

1. Local Flask/FastAPI web server (runs on localhost:8000)
2. Drag-drop CSV file upload
3. Auto-detect schema or manual mapping
4. Transform data (add timestamps, metadata, normalize)
5. Preview before upload
6. One-click load to BigQuery

**Tech Stack:**

- Flask or FastAPI (backend)
- Simple HTML/JS frontend (no framework needed)
- Pandas for CSV processing
- BigQuery client for loading

**Acceptance Criteria:**

- [ ] Can upload CSV via browser
- [ ] Auto-detects column types
- [ ] Shows preview of 10 rows
- [ ] Loads to specified BigQuery table
- [ ] Total dev time < 8 hours

**Rollback:** Delete tool if not used

**Cost:** $0 (runs locally)

---

## TOP 5 RISKS & MITIGATIONS

### Risk 1: TradingEconomics Blocks Scraping

**Likelihood:** MEDIUM

**Impact:** HIGH (lose real-time price data)

**Mitigation:**

- Have Barchart CSV backfill ready
- Use FRED API as backup for some data
- Implement polite scraping (already have 1-hour delays)

### Risk 2: Fixing Parser Breaks Other Things

**Likelihood:** LOW

**Impact:** MEDIUM

**Mitigation:**

- Test on saved HTML before deploying
- Keep broken version for rollback
- Deploy during low-usage hours

### Risk 3: Scheduling Too Many Cron Jobs Overloads System

**Likelihood:** LOW

**Impact:** MEDIUM

**Mitigation:**

- Start with 2-3 critical scripts
- Monitor CPU/memory usage
- Stagger execution times (not all at once)

### Risk 4: Canonical Schema Changes Break Dashboard

**Likelihood:** VERY LOW

**Impact:** HIGH

**Mitigation:**

- Changes are ADDITIVE (ADD COLUMN, not DROP/RENAME)
- Test Vite queries after each table update
- Keep old column names intact

### Risk 5: CSV Uploader Security Risk

**Likelihood:** LOW

**Impact:** MEDIUM

**Mitigation:**

- Runs localhost only (not exposed to internet)
- Validate CSV before loading
- Require manual confirmation before BigQuery write

---

## IMMEDIATE ACTIONS (Do This Next)

### Action 1: APPROVE/REJECT This Remediation Plan

**Who:** You (Owner)

**Timeline:** Now

**Decision:** Which tasks to execute? All 5? Prioritize differently?

### Action 2: Fix TradingEconomics Parser (If Approved)

**Who:** Me (execution)

**Timeline:** 30 minutes

**Verification:** Test on saved HTML, verify different prices for each commodity

### Action 3: Schedule News/Social Scripts (If Approved)

**Who:** Me (add cron jobs)

**Timeline:** 15 minutes

**Verification:** Check logs after 24 hours, should see 50+ news rows, 20+ social rows

---

## WHAT I DID NOT FAKE

**PROVEN REAL (Evidence-Based):**

- ✅ Palm oil data: 421 rows loaded from Barchart CSV (avg $916/MT)
- ✅ Weather data: 9,505 rows (NOAA, INMET sources)
- ✅ Economic indicators: 3,220 rows (FRED data)
- ✅ Trump/ICE intelligence: 166 rows (real events)
- ✅ 3 BigQuery ARIMA models (exist and functional)

**BROKEN/INCOMPLETE (Not Fake, Just Not Working):**

- ❌ TradingEconomics scraper (broken parser, not fake data)
- ❌ Empty tables (created but not populated, not fake)
- ⚠️ Sparse tables (scripts exist but not running regularly)

**Documentation Files:**

- Some are accurate (ML_TRAINING_PIPELINE_DISCOVERY.md based on real code audit)
- Some are aspirational (plan.md describes future state)
- None contain fake data - just incomplete implementation

---

## NEXT_STEP_FOR_OWNER

**DECISION REQUIRED:**

1. **Approve Task 1** (Fix TradingEconomics parser)? YES/NO
2. **Approve Task 2** (Schedule missing scripts)? YES/NO
3. **Approve Task 3** (Consolidate redundant tables)? YES/NO
4. **Approve Task 4** (Complete canonical schema)? YES/NO
5. **Approve Task 5** (Build CSV uploader tool)? YES/NO

**OR:**

**Prioritize differently?** (e.g., "Do Task 5 first, then Task 1")

**OR:**

**Reject all and provide different direction?**

---

**NO EXECUTION UNTIL YOU APPROVE. THIS IS A MAP, NOT GPS.**

### To-dos

- [ ] Completed root cause analysis of 7 critical data pipeline issues
- [ ] PROPOSED: Fix TradingEconomics parser to extract from JavaScript var model JSON
- [ ] PROPOSED: Schedule news_intelligence and social_sentiment scripts via cron
- [ ] PROPOSED: Create views for fed_rates and currency_data using existing economic_indicators data
- [ ] PROPOSED: Complete canonical schema rollout to remaining 11 ingestion scripts
- [ ] PROPOSED: Build Smart CSV Uploader web tool for easy data loading