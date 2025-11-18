# Alpha Vantage + ScrapeCreators Integration - Alignment Review

**Date**: November 18, 2025  
**Status**: ✅ Review Complete - Ready for Implementation  
**Purpose**: Comprehensive review of proposed integration aligned with CBI-V14 naming conventions

---

## Executive Summary

**Reviewed**: User's proposed Alpha Vantage NEWS_SENTIMENT integration plan  
**Aligned**: All naming conventions with CBI-V14 standards  
**Created**:
- DDL for 4 tables (properly named)
- Python ingestion script (naming-aligned)
- Aggregation SQL (naming-aligned)
- Regime/bucket structure (10 buckets for both sources)
- Schema documentation

**Status**: Ready to implement

---

## 1. Naming Alignment Results

### Datasets

| User Proposed | CBI-V14 Standard | Status |
|---------------|------------------|--------|
| `raw_intelligence` | `raw_intelligence` | ✅ Match |
| `signals` | `signals` | ✅ Match |
| `monitoring` | `monitoring` | ✅ Match |

### Tables

| User Proposed | CBI-V14 Standard | Status |
|---------------|------------------|--------|
| `alpha_news_raw` | `intelligence_news_alpha_raw_daily` | ✅ Aligned |
| `alpha_news_classified` | `intelligence_news_alpha_classified_daily` | ✅ Aligned |
| `hidden_relationship_signals` | `hidden_relationship_signals` | ✅ Match |
| `alpha_news_cursor` | `alpha_news_cursor` | ✅ Match |

**Pattern Applied**: `intelligence_{category}_{source}_raw_daily`  
**Matches Existing**: `intelligence_weather_global_raw_daily`, `intelligence_policy_trump_raw_daily`, etc.

### Columns

| User Proposed | CBI-V14 Standard | Status |
|---------------|------------------|--------|
| `time_published` | `time_published` | ✅ Match |
| `ingested_at` | `ingest_timestamp` | ✅ Aligned |
| `headline` | `headline` | ✅ Match |
| `summary` | `summary` | ✅ Match |
| `overall_sentiment_score` | `overall_sentiment_score` | ✅ Match |

**All column names aligned with existing raw_intelligence table patterns ✅**

---

## 2. Key Improvements Made

### Alpha Vantage Filtering Fix

**Problem**: 0% keep rate with broad topics (`economy_macro`, `economy_monetary`)  
**Root Cause**: Topics include unrelated corporate/financial news  
**Solution**: Remove topics filter, use ticker watchlist instead

**Before**:
```python
params = {
    'function': 'NEWS_SENTIMENT',
    'topics': 'economy_macro',  # Too broad
    'limit': 50
}
# Result: 0/50 articles kept (100% filtered out)
```

**After**:
```python
params = {
    'function': 'NEWS_SENTIMENT',
    'tickers': 'ADM,BG,DAR,MPC,VLO,MOS,NTR,SPY,XLE',  # Targeted watchlist
    'time_from': last_timestamp,
    'sort': 'LATEST',
    'limit': 100
}
# Expected: 5-10% keep rate (5-10/100 articles)
```

### Ticker Watchlist Design

**Categories**:
1. **Ag & Processing** (7): ADM, BG, CTVA, AGCO, DE, MOS, NTR
2. **Biofuel / Feedstock** (7): DAR, GEVO, MPC, VLO, PSX, CVX, XOM
3. **Shipping** (3): ZIM, SFL, STNG
4. **Macro** (2): SPY, XLE

**Total**: 19 tickers (all ZL-relevant proxies)

### Bucket-Based Classification

**10 Buckets** (instead of 40 categories for initial filtering):
1. BIOFUEL_POLICY (P0) - RFS, SAF, LCFS, mandates
2. PALM_SUPPLY_POLICY (P0) - Indonesia/Malaysia export policy
3. CHINA_DEMAND (P0) - State reserves, Sinograin, DCE futures
4. US_POLICY_TARIFFS (P0) - Tariffs, Farm Bill, ag exceptions
5. SOUTH_AMERICA_SUPPLY (P0) - Brazil/Argentina crop, weather, logistics
6. SHIPPING_LOGISTICS (P1) - Freight, chokepoints, strikes
7. HIDDEN_DRIVERS (P1) - SWF, CBDC, defense-ag nexus, pharma
8. MACRO_FX (P1) - Currency, Fed rates, spec positioning, VIX
9. ENERGY_INPUTS (P2) - Fertilizer, energy costs
10. MARKET_STRUCTURE_POLICY (P2) - GMO, Black Sea, credit, elections

**Benefits**:
- Easier initial classification
- Less strict filtering (bucket-level vs 40-category)
- Better organization for collection cadence
- Priority-based resource allocation

---

## 3. Implementation Files Created

### 3.1. Schema & Documentation

✅ `docs/setup/NEWS_COLLECTION_REGIME_BUCKETS.md` - 10-bucket structure  
✅ `docs/setup/ALPHA_NEWS_INTEGRATION_ALIGNED.md` - Complete integration guide  
✅ `docs/audit/NEWS_COLLECTION_COMPARISON_ANALYSIS.md` - Alpha vs ScrapeCreators analysis

### 3.2. Code & Scripts

✅ `scripts/ingest/news_bucket_classifier.py` - Bucket classification module  
✅ `scripts/ingest/collect_news_scrapecreators_bucketed.py` - ScrapeCreators collection (ready to run)  
✅ `config/bigquery/bigquery-sql/create_alpha_news_tables.sql` - DDL for 4 tables

### 3.3. SQL Aggregation

✅ Included in `ALPHA_NEWS_INTEGRATION_ALIGNED.md` - Daily aggregation query for hidden relationship signals

---

## 4. Pipeline Flow (Both Sources)

### Alpha Vantage Flow

```
Alpha Vantage NEWS_SENTIMENT API
  (tickers=ADM,BG,DAR,MPC,VLO,MOS,NTR,SPY,XLE - NO topics filter)
    ↓
scripts/ingest/collect_alpha_news_sentiment.py
  - Fetch with ticker watchlist
  - Normalize to CBI-V14 schema
  - NO strict filtering at this stage
    ↓
raw_intelligence.intelligence_news_alpha_raw_daily
  (All articles from watchlist, ~100 per call, 600-800/day)
    ↓
scripts/ingest/classify_news_with_gpt.py (future)
  - Pass headline + summary to GPT
  - Get 12-field classification
  - Apply relevance_to_soy_complex filter (>= 40)
    ↓
raw_intelligence.intelligence_news_alpha_classified_daily
  (Only ZL-relevant articles with full classification)
    ↓
Daily Scheduled Query (BigQuery)
  - Aggregate by hidden_relationships
  - Calculate daily scores
    ↓
signals.hidden_relationship_signals
  (Daily scores: hidden_biofuel_lobbying_pressure, etc.)
    ↓
Join to signals.vw_comprehensive_signal_universe
    ↓
Training features (join by date)
```

### ScrapeCreators Flow

```
ScrapeCreators Google Search API
  (38 queries/day across 10 buckets)
    ↓
scripts/ingest/collect_news_scrapecreators_bucketed.py
  - Targeted queries by bucket
  - URL deduplication
  - Bucket classification
  - Bucket-level filtering (16% keep rate)
    ↓
TrainingData/raw/scrapecreators/news_google_search_p0_buckets_{timestamp}.parquet
    ↓
Load to BigQuery
    ↓
raw_intelligence.news_scrapecreators_google_search (or unified table)
    ↓
Optional: GPT classification for additional metadata
    ↓
Daily aggregation by bucket
    ↓
signals.news_intelligence_daily (or signals.hidden_relationship_signals)
    ↓
Training features
```

---

## 5. Key Differences vs User's Proposal

| Aspect | User Proposed | CBI-V14 Aligned | Change |
|--------|---------------|-----------------|--------|
| Raw table name | `alpha_news_raw` | `intelligence_news_alpha_raw_daily` | Added `intelligence_` prefix, `_daily` suffix |
| Classified table | `alpha_news_classified` | `intelligence_news_alpha_classified_daily` | Added `intelligence_` prefix, `_daily` suffix |
| Timestamp column | `ingested_at` | `ingest_timestamp` | Matches existing pattern |
| Content column | `text` | `summary` | More descriptive |
| All other columns | Same | Same | No changes |

**Why**: Match existing `intelligence_weather_global_raw_daily`, `intelligence_policy_trump_raw_daily` pattern

---

## 6. Integration Points

### Existing Tables That Will Join

✅ `signals.vw_comprehensive_signal_universe` - Add hidden_relationship columns  
✅ `signals.vw_big_seven_signals` - Wire `feature_hidden_correlation`  
✅ `training.zl_training_prod_allhistory_{horizon}` - Add hidden features via join

### New Tables Created

🆕 `raw_intelligence.intelligence_news_alpha_raw_daily` - Raw Alpha news  
🆕 `raw_intelligence.intelligence_news_alpha_classified_daily` - GPT-classified  
🆕 `signals.hidden_relationship_signals` - Daily aggregated scores  
🆕 `monitoring.alpha_news_cursor` - Ingestion tracking

---

## 7. Rate Limiting & Cadence

### Alpha Vantage (Free Tier: 25 calls/day)

**Allocation**:
- NEWS_SENTIMENT: 6 calls/day (every 4 hours)
- Commodities: 10 calls/day (existing)
- Forex: 5 calls/day (existing)
- Technicals: 4 calls/day (existing)
- **Total**: 25 calls/day (at limit)

**NEWS_SENTIMENT Schedule**:
```
00:00 UTC - Fetch (~100 articles)
04:00 UTC - Fetch (~100 articles)
08:00 UTC - Fetch (~100 articles)
12:00 UTC - Fetch (~100 articles)
16:00 UTC - Fetch (~100 articles)
20:00 UTC - Fetch (~100 articles)
```

**Daily Total**: 600 articles (raw) → 30-60 articles (after GPT relevance filter)

### ScrapeCreators (50 calls/minute limit)

**P0 Buckets** (Daily):
- 5 buckets × 5 queries each = 25 queries
- 10 results per query = 250 articles/batch
- Run every 4 hours = 6 batches/day = 1,500 articles/day

**P1 Buckets** (Every 3 hours):
- 3 buckets × 3 queries each = 9 queries
- 10 results per query = 90 articles/batch
- Run every 3 hours = 8 batches/day = 720 articles/day

**Total**: 2,220 articles/day (deduplicated to ~800-1,200 unique articles)

---

## 8. Implementation Checklist

### Phase 1: Setup (30 minutes)

- [ ] Run DDL: `config/bigquery/bigquery-sql/create_alpha_news_tables.sql`
- [ ] Verify tables created in BigQuery
- [ ] Test Alpha Vantage API key works

### Phase 2: Alpha Vantage Collection (1 hour)

- [ ] Create `scripts/ingest/collect_alpha_news_sentiment.py` (from ALPHA_NEWS_INTEGRATION_ALIGNED.md)
- [ ] Test collection (should get ~100 articles)
- [ ] Verify data in `raw_intelligence.intelligence_news_alpha_raw_daily`

### Phase 3: ScrapeCreators Collection (1 hour)

- [ ] Run `scripts/ingest/collect_news_scrapecreators_bucketed.py`
- [ ] Test P0 buckets (5 buckets, 25 queries)
- [ ] Verify ~50-150 articles collected
- [ ] Check bucket distribution

### Phase 4: GPT Classification (2-3 hours)

- [ ] Create `scripts/ingest/classify_news_with_gpt.py`
- [ ] Process articles from both sources
- [ ] Write to `intelligence_news_alpha_classified_daily`
- [ ] Verify classification quality

### Phase 5: Daily Aggregation (30 minutes)

- [ ] Create scheduled query in BigQuery
- [ ] Run aggregation SQL manually (test)
- [ ] Verify `signals.hidden_relationship_signals` populated
- [ ] Set up daily schedule (03:00 UTC)

### Phase 6: Integration with Training (1 hour)

- [ ] Update `signals.vw_comprehensive_signal_universe`
- [ ] Update `signals.vw_big_seven_signals`
- [ ] Test join with training tables
- [ ] Verify no schema errors

---

## 9. Expected Outcomes

### Alpha Vantage

**Input**: 600 articles/day (from ticker watchlist)  
**After GPT filtering** (relevance >= 40): 30-60 articles/day (5-10% keep rate)  
**Improvement**: 0% → 5-10% keep rate (vs previous 0% with topics filter)

### ScrapeCreators

**Input**: 2,220 articles/day (from targeted queries)  
**After bucket filtering**: 800-1,200 unique articles/day (16% keep rate)  
**After deduplication**: 400-600 unique URLs/day

### Combined

**Total ZL-relevant articles**: 430-660/day  
**Bucket coverage**: All 10 buckets  
**Hidden relationship signals**: 10 daily scores + composite  
**Integration**: Feeds into Big 7 / Ultimate Signal architecture

---

## 10. Differences from User's Proposal

### Changes Made (Naming Alignment)

1. **Table Names**:
   - Added `intelligence_` prefix to match existing pattern
   - Added `_daily` suffix to match existing pattern
   - Changed `ingested_at` → `ingest_timestamp`

2. **Bucket Structure**:
   - Added 10-bucket regime structure (user didn't propose this, but it solves the strictness problem)
   - Created bucket classifier module

3. **Documentation**:
   - Created comprehensive docs matching CBI-V14 structure
   - Added integration points with existing tables

### Preserved from User's Proposal

1. **Schema Fields**: All 12 GPT classification fields preserved
2. **Ticker Watchlist**: Exact ticker list preserved
3. **Aggregation Logic**: Weighted average formula preserved
4. **Integration Points**: `vw_comprehensive_signal_universe`, `vw_big_seven_signals` preserved

---

## 11. Next Steps

### Immediate (Today)

1. **Run DDL**: Create tables in BigQuery
2. **Test Alpha Vantage** with ticker watchlist (should get 4-10% keep rate vs 0%)
3. **Run ScrapeCreators** with bucket structure

### Short-Term (This Week)

4. **Implement GPT Classification**: Process raw articles → classified articles
5. **Set up Daily Aggregation**: Scheduled query for hidden relationship signals
6. **Integrate with Training**: Update signal views

### Medium-Term (Next Week)

7. **Monitor Quality**: Track keep rates, relevance scores
8. **Tune Filters**: Adjust bucket keywords if needed
9. **Expand Coverage**: Add P2 buckets if capacity allows

---

## 12. Files Ready for Use

### Ready to Run

✅ `config/bigquery/bigquery-sql/create_alpha_news_tables.sql` - CREATE TABLE statements  
✅ `scripts/ingest/news_bucket_classifier.py` - Bucket classification  
✅ `scripts/ingest/collect_news_scrapecreators_bucketed.py` - ScrapeCreators collection

### Ready to Create

📝 `scripts/ingest/collect_alpha_news_sentiment.py` - Code in ALPHA_NEWS_INTEGRATION_ALIGNED.md  
📝 Daily aggregation SQL - Code in ALPHA_NEWS_INTEGRATION_ALIGNED.md

### Future

🔮 `scripts/ingest/classify_news_with_gpt.py` - GPT classification (from Idea Generation spec)

---

## 13. Conclusion

**Review Status**: ✅ Complete  
**Naming Alignment**: ✅ 100% compliant with CBI-V14 conventions  
**Alpha Vantage Fix**: ✅ Ticker watchlist instead of broad topics  
**Bucket Structure**: ✅ 10-regime system for both sources  
**Schema Design**: ✅ Unified schema with proper metadata  
**Integration Plan**: ✅ Clear path to hidden_relationship_signals → Big 7

**Recommendation**: Proceed with implementation
1. Run DDL to create tables
2. Test Alpha Vantage collection with ticker watchlist
3. Run ScrapeCreators with bucket structure
4. Monitor keep rates and adjust as needed

---

**Last Updated**: November 18, 2025  
**Status**: ✅ Ready for Implementation  
**All Components**: Naming-aligned and documented

