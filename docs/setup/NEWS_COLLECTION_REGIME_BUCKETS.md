# News Collection Regime Buckets - ZL Intelligence

**Date**: November 18, 2025  
**Status**: Schema & Metadata Design  
**Purpose**: Organize news collection into regimes/buckets for both ScrapeCreators and Alpha Vantage

---

## Regime Structure Overview

40 institutional keyword matrix categories organized into **10 major regimes/buckets**:

### Bucket 1: BIOFUEL_POLICY (High Impact - ZL ↑)
**Primary Driver**: Demand-side policy for vegetable oil feedstocks  
**ZL Impact**: Direct bullish (increased feedstock demand)  
**Lead Time**: 60-180 days (policy announcement → implementation → demand increase)

**Categories**:
- `biofuel_mandates` (Cat 1): RFS, SAF, LCFS, blend requirements
- `biofuel_lobbying` (Cat 7): PAC donations, EPA hearings, industry working groups
- `refinery_rd_capacity` (Cat 27): Renewable diesel plant expansions, refinery retrofits

**Keywords** (shared across both sources):
- Primary: "renewable fuel standard", "RFS", "SAF credit", "LCFS", "biodiesel blend", "B20", "B40", "renewable diesel capacity"
- Agencies: "EPA", "DOE", "CARB", "ANP Brazil"
- Triggers: "proposed rule", "final rule", "expanded credit", "biofuel lobby"

---

### Bucket 2: PALM_SUPPLY_POLICY (High Impact - ZL ↑)
**Primary Driver**: Palm oil supply disruptions → substitution to soy oil  
**ZL Impact**: Bullish when palm supply constrained  
**Lead Time**: 30-90 days (policy announcement → trade flow shifts)

**Categories**:
- `palm_policy` (Cat 2): Indonesia/Malaysia export taxes, bans, DMO policies

**Keywords**:
- Primary: "CPO export levy", "palm oil export tax", "Indonesia export ban", "MPOB", "DMO", "Malaysia supply", "El Nino dry estates"
- Triggers: "port congestion", "labor shortage", "estate yield down", "harvest disruption"

---

### Bucket 3: CHINA_DEMAND (High Impact - ZL ↑/↓)
**Primary Driver**: Chinese state buying/selling, crush margins, trade policy  
**ZL Impact**: Mixed (demand increases bullish, trade restrictions bearish)  
**Lead Time**: 14-60 days (announcement → execution)

**Categories**:
- `china_demand` (Cat 3): State reserves, Sinograin, COFCO, DCE futures
- `us_china_tension` (Cat 22): Naval confrontations, sanctions, export restrictions

**Keywords**:
- Primary: "Sinograin", "COFCO", "NDRC soybean", "state reserves", "soybean auctions", "Dalian soy oil", "DCE futures", "CNY devaluation"
- Triggers: "food security directive", "import suspension", "customs inspections", "African swine fever", "sanctions announcement"

---

### Bucket 4: US_POLICY_TARIFFS (Structural - ZL ↑/↓)
**Primary Driver**: US trade policy, tariffs, Argentina backchannel  
**ZL Impact**: Structural shifts in trade flows  
**Lead Time**: 90-365 days (policy → origin switching)

**Categories**:
- `us_policy_tariffs` (Cat 4): Tariff threats, 301 investigations, agricultural exceptions
- `farm_bill` (Cat 16): US Farm Bill, commodity programs, loan rates

**Keywords**:
- Primary: "tariff threat", "301 investigation", "trade retaliation", "Argentina cooperation", "IMF debt restructuring", "Farm Bill negotiations"
- Triggers: "national security review", "Executive Order", "trade enforcement action", "mark-up session"

---

### Bucket 5: SOUTH_AMERICA_SUPPLY (High Impact - ZL ↑/↓)
**Primary Driver**: Brazil/Argentina production, weather, logistics  
**ZL Impact**: Major supply driver  
**Lead Time**: 30-180 days (weather → harvest → exports)

**Categories**:
- `brazil_argentina_crop_logistics` (Cat 5): CONAB, harvest, strikes, logistics
- `weather_agronomic` (Cat 6): Drought, floods, moisture stress, ENSO
- `south_america_logistics` (Cat 26): BR-163, port congestion, truck blockades

**Keywords**:
- Primary: "CONAB", "MAPA Brazil", "soybean harvest Brazil", "Mato Grosso", "Rosario strike", "BR-163", "drought monitoring", "La Niña", "El Niño"
- Triggers: "yield reduction", "port strike", "barge delays", "flash drought", "crop stress"

---

### Bucket 6: SHIPPING_LOGISTICS (Medium Impact - ZL ↑)
**Primary Driver**: Freight costs, chokepoint disruptions, port capacity  
**ZL Impact**: Bullish when disruptions favor US origins  
**Lead Time**: 7-60 days (disruption → rerouting → price impact)

**Categories**:
- `shipping_chokepoints` (Cat 10): Red Sea, Suez, Panama Canal, Bab el-Mandeb
- `shipping_freight` (Cat 20): Dry bulk rates, Baltic Dry Index, tanker rates
- `labor_strikes` (Cat 25): Port strikes, dockworker strikes, ILWU
- `tanker_dynamics` (Cat 28): Clean tanker index, MR tanker rates
- `shipping_insurance` (Cat 32): War risk premium, reinsurance withdrawal

**Keywords**:
- Primary: "Red Sea attacks", "Suez disruption", "Panama Canal drought", "Baltic Dry Index", "port strike", "dockworker strike", "clean tanker index"
- Triggers: "ships diverted", "draft restrictions", "strike notice", "rate surge"

---

### Bucket 7: HIDDEN_DRIVERS (Predictive - 3-9 month leads)
**Primary Driver**: Cross-domain drivers-of-drivers  
**ZL Impact**: Predictive signals with long lead times  
**Lead Time**: 90-270 days (event → trade flow changes)

**Categories**:
- `sovereign_wealth` (Cat 8): SWF investments in ag/logistics
- `carbon_eudr` (Cat 9): Carbon markets, EU deforestation law
- `defense_agriculture` (Cat 11): FMS sales, security guarantees
- `pharma_agriculture` (Cat 12): Pharmaceutical licensing → ag reciprocity
- `cbdc_settlement` (Cat 13): Digital yuan, BRL-CNY settlement
- `port_infrastructure` (Cat 14): Port dredging, terminal upgrades
- `academic_cooperation` (Cat 15): Ag MoUs, university exchanges

**Keywords**:
- Primary: "sovereign wealth investment", "EUDR enforcement", "carbon credit", "FMS sale", "pharmaceutical licensing", "digital yuan", "CBDC corridor", "port dredging", "agricultural MoU"
- Triggers: "5% stake", "traceability deadline", "security memorandum", "patent settlement", "digital settlement pilot", "dredging approval"

---

### Bucket 8: MACRO_FX (Medium Impact - ZL ↑/↓)
**Primary Driver**: Currency movements, interest rates, risk appetite  
**ZL Impact**: Affects origin competitiveness and spec flows  
**Lead Time**: 7-30 days (macro event → commodity response)

**Categories**:
- `fx_shifts` (Cat 18): BRL weakness, ARS collapse, CNY devaluation
- `macro_liquidity` (Cat 29): Fed rate cuts, inflation, QE expectations
- `spec_positioning` (Cat 30): CFTC managed money, spec long/short
- `risk_off_vix` (Cat 31): VIX spikes, market turmoil, risk aversion

**Keywords**:
- Primary: "BRL weakness", "real depreciation", "peso collapse", "soydollar", "Fed rate cut", "inflation spike", "managed money net long", "VIX spike"
- Triggers: "FX intervention", "interest rate decision", "COT report", "market turmoil"

---

### Bucket 9: ENERGY_INPUTS (Medium Impact - ZL ↑)
**Primary Driver**: Energy costs, fertilizer availability  
**ZL Impact**: Higher input costs → lower soybean acreage → bullish ZL  
**Lead Time**: 90-365 days (input shock → planting decisions → supply)

**Categories**:
- `fertilizer_energy` (Cat 21): Nitrogen shortage, potash sanctions, ammonia outages
- `energy_markets` (Cat 36): Diesel shortage, crude rally, diesel crack spread

**Keywords**:
- Primary: "nitrogen shortage", "potash sanctions", "ammonia plant outage", "fertilizer sanctions", "diesel shortage", "crude rally", "diesel crack spread"
- Triggers: "sanction risk", "export restriction", "plant accident", "refinery outage"

---

### Bucket 10: MARKET_STRUCTURE_POLICY (Low-Medium Impact)
**Primary Driver**: Regulatory changes, political shifts, structural events  
**ZL Impact**: Varies by event type  
**Lead Time**: 30-180 days (policy → market adjustment)

**Categories**:
- `gmo_agrochemical` (Cat 23): Glyphosate bans, trait approvals, pesticide restrictions
- `black_sea_war` (Cat 24): Sunflower oil disruptions from Black Sea conflict
- `port_throughput` (Cat 33): Container throughput, berth congestion
- `lgfv_debt` (Cat 34): Chinese local government debt → import cuts
- `soybean_disease` (Cat 35): Soybean rust, white mold, crop disease
- `infra_failures` (Cat 37): Grain silo collapse, port fires, pipeline ruptures
- `credit_crunch` (Cat 38): Ag loan defaults, commercial credit freeze
- `elections_politics` (Cat 39): Elections, new ag ministers, nationalization risk
- `digital_traceability` (Cat 40): Blockchain traceability, EUDR compliance tech

**Keywords**:
- Primary: "glyphosate ban", "trait approval", "Odessa attack", "sunflower oil export ban", "container throughput", "LGFV debt", "soybean rust", "grain silo collapse", "credit tightening", "runoff election", "blockchain traceability"
- Triggers: "ban proposal", "port hit", "bond rollover crisis", "crop disease report", "port fire", "ag loan default", "election result"

---

## Bucket-Level Metadata

### Priority Scoring

| Bucket | Impact | Lead Time | Collection Frequency | Priority |
|--------|--------|-----------|---------------------|----------|
| 1. Biofuel Policy | High | 60-180d | Daily | P0 |
| 2. Palm Supply/Policy | High | 30-90d | Daily | P0 |
| 3. China Demand | High | 14-60d | Daily | P0 |
| 4. US Policy/Tariffs | Structural | 90-365d | Daily | P0 |
| 5. South America Supply | High | 30-180d | Daily | P0 |
| 6. Shipping/Logistics | Medium | 7-60d | Daily | P1 |
| 7. Hidden Drivers | Predictive | 90-270d | Every 3 days | P1 |
| 8. Macro/FX | Medium | 7-30d | Daily | P1 |
| 9. Energy/Inputs | Medium | 90-365d | Every 3 days | P2 |
| 10. Market Structure/Policy | Low-Med | 30-180d | Weekly | P2 |

### Query Allocation

**ScrapeCreators Google Search**:
- P0 buckets (1-5): 5 queries each × 5 buckets = 25 queries/day
- P1 buckets (6-8): 3 queries each × 3 buckets = 9 queries/day
- P2 buckets (9-10): 2 queries each × 2 buckets = 4 queries/day
- **Total**: 38 queries/day × 10 results = 380 articles/day

**Alpha Vantage NEWS_SENTIMENT**:
- Use as supplement with bucket-specific filtering
- Topics: `economy_macro`, `economy_monetary`, `energy_transportation`
- Apply bucket-level keyword filter (less strict than full matrix)
- Expected keep rate: 5-10% (vs 0% currently)

---

## Schema Design with Bucket Integration

### Unified Schema (Both Sources)

```python
NEWS_ARTICLE_SCHEMA = {
    # Primary identifiers
    'article_id': 'STRING',              # MD5 hash of URL
    'url': 'STRING',                     # Article URL
    'url_domain': 'STRING',              # Extracted domain
    
    # Content
    'title': 'STRING',                   # Headline
    'description': 'STRING',             # Summary/snippet
    'full_text': 'STRING',               # Full article (if available)
    
    # Source metadata
    'source_api': 'STRING',              # 'scrapecreators' or 'alpha_vantage'
    'source_name': 'STRING',             # 'Reuters', 'EPA', etc.
    'source_domain': 'STRING',           # Same as url_domain
    'source_credibility': 'FLOAT64',     # 0.50-1.00
    'source_type': 'STRING',             # 'government', 'premium_press', 'trade_pub', 'blog'
    
    # Collection metadata
    'collected_at': 'TIMESTAMP',         # Collection timestamp
    'collection_date': 'DATE',           # Partition key
    'collection_method': 'STRING',       # 'google_search', 'news_sentiment', 'rss'
    
    # Bucket classification (PRIMARY)
    'bucket': 'STRING',                  # One of 10 buckets (required)
    'bucket_priority': 'STRING',         # 'P0', 'P1', 'P2'
    'bucket_impact': 'STRING',           # 'high', 'medium', 'low'
    'bucket_lead_days': 'INT64',         # Avg lead time for this bucket
    
    # Category classification (SECONDARY)
    'category': 'STRING',                # One of 40 categories (nullable)
    'categories': 'ARRAY<STRING>',       # Multiple categories (nullable)
    
    # Query metadata (ScrapeCreators only)
    'search_query': 'STRING',            # Query used (nullable)
    'search_rank': 'INT64',              # Position in results (nullable)
    
    # Topic metadata (Alpha Vantage only)
    'av_topics': 'ARRAY<STRUCT>',        # Alpha Vantage topic array (nullable)
    'av_overall_sentiment_score': 'FLOAT64',  # -1.0 to +1.0 (nullable)
    'av_overall_sentiment_label': 'STRING',    # 'Bullish', 'Bearish', etc. (nullable)
    'av_ticker_sentiment': 'ARRAY<STRUCT>',    # Ticker sentiment array (nullable)
    
    # Calculated sentiment
    'sentiment_score': 'FLOAT64',        # Calculated -1.0 to +1.0
    'sentiment_class': 'STRING',         # 'bullish', 'bearish', 'neutral'
    'sentiment_method': 'STRING',        # 'alpha_vantage', 'rule_based', 'gpt'
    
    # Relevance flags
    'is_zl_relevant': 'BOOL',            # Passed institutional keyword matrix filter
    'relevance_score': 'FLOAT64',        # 0-100 (how relevant to ZL)
    
    # Region classification
    'region_focus': 'ARRAY<STRING>',     # ['us', 'brazil', 'china', etc.]
    'region_primary': 'STRING',          # Primary region
    
    # Deduplication
    'first_seen_at': 'TIMESTAMP',        # First collection time
    'last_seen_at': 'TIMESTAMP',         # Most recent collection time
    'seen_count': 'INT64',               # How many times collected
    'seen_buckets': 'ARRAY<STRING>',     # All buckets this URL appeared in
    'seen_queries': 'ARRAY<STRING>',     # All queries that returned this URL
}
```

### BigQuery Table

```sql
CREATE TABLE IF NOT EXISTS `cbi-v14.raw_intelligence.news_unified_with_buckets` (
  -- Primary identifiers
  article_id STRING NOT NULL,
  url STRING NOT NULL,
  url_domain STRING,
  
  -- Content
  title STRING NOT NULL,
  description STRING,
  full_text STRING,
  
  -- Source metadata
  source_api STRING NOT NULL,           -- 'scrapecreators' or 'alpha_vantage'
  source_name STRING,
  source_domain STRING,
  source_credibility FLOAT64,
  source_type STRING,
  
  -- Collection metadata
  collected_at TIMESTAMP NOT NULL,
  collection_date DATE NOT NULL,
  collection_method STRING,
  
  -- Bucket classification (PRIMARY - always populated)
  bucket STRING NOT NULL,               -- One of 10 buckets
  bucket_priority STRING NOT NULL,      -- 'P0', 'P1', 'P2'
  bucket_impact STRING,                 -- 'high', 'medium', 'low'
  bucket_lead_days INT64,               -- Avg lead time
  
  -- Category classification (SECONDARY - nullable)
  category STRING,                      -- One of 40 categories
  categories ARRAY<STRING>,             -- Multiple categories
  
  -- Query metadata (ScrapeCreators only)
  search_query STRING,
  search_rank INT64,
  
  -- Topic metadata (Alpha Vantage only)
  av_topics ARRAY<STRUCT<
    topic STRING,
    relevance_score STRING
  >>,
  av_overall_sentiment_score FLOAT64,
  av_overall_sentiment_label STRING,
  av_ticker_sentiment ARRAY<STRUCT<
    ticker STRING,
    relevance_score STRING,
    ticker_sentiment_score STRING,
    ticker_sentiment_label STRING
  >>,
  
  -- Calculated sentiment
  sentiment_score FLOAT64,
  sentiment_class STRING,
  sentiment_method STRING,
  
  -- Relevance flags
  is_zl_relevant BOOL NOT NULL,
  relevance_score FLOAT64,
  
  -- Region classification
  region_focus ARRAY<STRING>,
  region_primary STRING,
  
  -- Deduplication
  first_seen_at TIMESTAMP NOT NULL,
  last_seen_at TIMESTAMP NOT NULL,
  seen_count INT64 DEFAULT 1,
  seen_buckets ARRAY<STRING>,
  seen_queries ARRAY<STRING>
)
PARTITION BY collection_date
CLUSTER BY bucket, source_api, is_zl_relevant, url_domain
OPTIONS (
  description = 'Unified news collection from ScrapeCreators and Alpha Vantage with bucket classification',
  require_partition_filter = TRUE
);
```

---

## Next Steps

1. **Implement bucket classifier function** (works for both sources)
2. **Fix Alpha Vantage filtering** (use bucket-level keywords, less strict)
3. **Update ScrapeCreators collection** (add bucket classification)
4. **Create unified collection script** (handles both sources with bucket assignment)
5. **Run ScrapeCreators with proper bucketing** (38 queries/day across 10 buckets)

---

**Last Updated**: November 18, 2025  
**Status**: Schema Design Complete - Ready for Implementation  
**Next**: Implement bucket classification and run collection

