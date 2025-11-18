# Alpha Vantage NEWS_SENTIMENT Integration - Naming Aligned

**Date**: November 18, 2025  
**Status**: Schema & Script Design  
**Purpose**: Properly integrate Alpha Vantage NEWS_SENTIMENT with CBI-V14 naming conventions

---

## Naming Alignment Review

### Existing Conventions

**Dataset**: `raw_intelligence` ✅ (exists, 7 tables)  
**Table Pattern**: `intelligence_{category}_{source}_raw_daily`  
**Existing Tables**:
- `intelligence_weather_global_raw_daily`
- `intelligence_policy_trump_raw_daily`
- `intelligence_news_general_raw_daily`
- `intelligence_sentiment_social_raw_daily`

**Proposed Tables** (aligned):
- `raw_intelligence.intelligence_news_alpha_raw_daily` (Alpha Vantage NEWS_SENTIMENT raw)
- `raw_intelligence.intelligence_news_alpha_classified_daily` (GPT-classified)
- `signals.hidden_relationship_signals` (daily hidden driver scores)
- `monitoring.alpha_news_cursor` (ingestion cursor)

---

## 1. BigQuery Table Schemas

### 1.1. Raw News from Alpha Vantage

```sql
CREATE TABLE IF NOT EXISTS `cbi-v14.raw_intelligence.intelligence_news_alpha_raw_daily` (
  -- Timestamps
  time_published     TIMESTAMP NOT NULL,
  ingest_timestamp   TIMESTAMP NOT NULL,
  
  -- Content
  headline           STRING,
  summary            STRING,
  url                STRING,
  
  -- Source metadata
  source             STRING,
  source_domain      STRING,
  
  -- Alpha Vantage specific
  tickers            ARRAY<STRING>,
  topics             ARRAY<STRUCT<
    topic STRING,
    relevance_score STRING
  >>,
  overall_sentiment_score  FLOAT64,
  overall_sentiment_label  STRING,
  ticker_sentiment   ARRAY<STRUCT<
    ticker STRING,
    relevance_score STRING,
    ticker_sentiment_score STRING,
    ticker_sentiment_label STRING
  >>,
  
  -- Raw storage for debugging
  raw_json           JSON,
  
  -- Quality flag
  data_quality_flag  STRING
)
PARTITION BY DATE(time_published)
CLUSTER BY source, source_domain
OPTIONS (
  description = 'Raw Alpha Vantage NEWS_SENTIMENT articles (ticker watchlist proxy for ZL intelligence)',
  require_partition_filter = TRUE
);
```

### 1.2. GPT-Classified News (for Hidden Relationship Intelligence)

```sql
CREATE TABLE IF NOT EXISTS `cbi-v14.raw_intelligence.intelligence_news_alpha_classified_daily` (
  -- Timestamps
  time_published           TIMESTAMP NOT NULL,
  classification_timestamp TIMESTAMP NOT NULL,
  
  -- Content (from raw)
  headline                 STRING,
  summary                  STRING,
  url                      STRING,
  source                   STRING,
  
  -- GPT Classification (12-field schema from Idea Generation)
  primary_topic            STRING,              -- One of 40 categories
  hidden_relationships     ARRAY<STRING>,       -- Array of hidden drivers
  region_focus             ARRAY<STRING>,       -- Array of regions
  relevance_to_soy_complex INT64,               -- 0-100
  directional_impact_zl    STRING,              -- bullish/bearish/neutral/mixed/unknown
  impact_strength          INT64,               -- 0-100
  impact_time_horizon_days INT64,               -- Days until impact
  half_life_days           INT64,               -- Days until decay
  mechanism_summary        STRING,              -- Causal chain explanation
  direct_vs_indirect       STRING,              -- direct/indirect/hidden
  subtopics                ARRAY<STRING>,       -- Finer-grained labels
  confidence               INT64,               -- 0-100
  
  -- Bucket classification (for regime-based aggregation)
  bucket                   STRING,              -- One of 10 buckets
  bucket_priority          STRING,              -- P0/P1/P2
  
  -- Quality flag
  data_quality_flag        STRING
)
PARTITION BY DATE(time_published)
CLUSTER BY bucket, primary_topic, directional_impact_zl
OPTIONS (
  description = 'GPT-classified Alpha Vantage news articles for hidden relationship intelligence',
  require_partition_filter = TRUE
);
```

### 1.3. Hidden Relationship Signals (Daily Aggregates)

```sql
CREATE TABLE IF NOT EXISTS `cbi-v14.signals.hidden_relationship_signals` (
  -- Date
  date                                   DATE NOT NULL,
  
  -- Hidden driver scores (from institutional matrix)
  hidden_biofuel_lobbying_pressure       FLOAT64,
  hidden_china_alt_bloc_score            FLOAT64,
  hidden_defense_agri_score              FLOAT64,
  hidden_cbdc_corridor_score             FLOAT64,
  hidden_carbon_arbitrage_score          FLOAT64,
  hidden_port_capacity_lead_index        FLOAT64,
  hidden_pharma_agri_score               FLOAT64,
  hidden_swf_lead_flow_score             FLOAT64,
  hidden_academic_exchange_score         FLOAT64,
  hidden_trump_argentina_backchannel_score FLOAT64,
  
  -- Composite score
  hidden_relationship_composite_score    FLOAT64,
  
  -- Metadata
  rows_contributing                      INT64,
  created_at                             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
OPTIONS (
  description = 'Daily hidden relationship driver scores aggregated from classified news',
  require_partition_filter = FALSE
);
```

### 1.4. Ingestion Cursor (Monitoring)

```sql
CREATE TABLE IF NOT EXISTS `cbi-v14.monitoring.alpha_news_cursor` (
  id                STRING NOT NULL,
  last_time_from    TIMESTAMP NOT NULL,
  updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
OPTIONS (
  description = 'Cursor tracking for Alpha Vantage NEWS_SENTIMENT incremental ingestion'
);

-- Initialize cursor
INSERT INTO `cbi-v14.monitoring.alpha_news_cursor` (id, last_time_from)
VALUES ('alpha_news', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR))
ON CONFLICT (id) DO NOTHING;
```

---

## 2. Ticker Watchlist (ZL Proxies)

### Curated Ticker List

**Purpose**: Alpha Vantage doesn't have ZL (soybean oil futures), so we use equity proxies

**Categories**:

**Ag & Processing / Crush**:
- `ADM` - Archer Daniels Midland (soybean processing, crush)
- `BG` - Bunge (ag commodities, processing)
- `CTVA` - Corteva (seeds, crop protection)
- `AGCO` - Farm machinery
- `DE` - Deere (farm equipment)
- `MOS` - Mosaic (fertilizer - affects input costs)
- `NTR` - Nutrien (fertilizer - affects input costs)

**Biofuel / Feedstock Demand**:
- `DAR` - Darling Ingredients (feedstock, fats, rendering)
- `GEVO` - Gevo (advanced biofuels)
- `MPC` - Marathon Petroleum (renewable diesel/SAF conversions)
- `VLO` - Valero (renewable diesel/SAF conversions)
- `PSX` - Phillips 66 (renewable diesel/SAF conversions)
- `CVX` - Chevron (SAF/biofuel verticals)
- `XOM` - Exxon Mobil (SAF/biofuel verticals)

**Shipping & Logistics** (for palm & soy corridor context):
- `ZIM` - ZIM Integrated Shipping
- `SFL` - Ship Finance (tankers)
- `STNG` - Scorpio Tankers

**Macro / Risk Proxies** (for regime detection):
- `SPY` - S&P 500 ETF (market stress, VIX correlation)
- `XLE` - Energy sector ETF (crude oil correlation)

**Python Constant**:
```python
TICKER_WATCHLIST = [
    # Ag & Processing
    'ADM', 'BG', 'CTVA', 'AGCO', 'DE', 'MOS', 'NTR',
    # Biofuel / Feedstock
    'DAR', 'GEVO', 'MPC', 'VLO', 'PSX', 'CVX', 'XOM',
    # Shipping
    'ZIM', 'SFL', 'STNG',
    # Macro
    'SPY', 'XLE'
]
```

---

## 3. Python Ingestion Script (Naming Aligned)

**File**: `scripts/ingest/collect_alpha_news_sentiment.py`

```python
#!/usr/bin/env python3
"""
Alpha Vantage NEWS_SENTIMENT ingestion for CBI-V14
Aligned with CBI-V14 naming conventions

- Pulls news for curated ticker watchlist (ZL proxies)
- Uses time cursor to avoid duplicate pulls
- Writes to: raw_intelligence.intelligence_news_alpha_raw_daily
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.keychain_manager import get_api_key
import requests
from google.cloud import bigquery
from datetime import datetime, timedelta, timezone
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "cbi-v14"
RAW_DATASET = "raw_intelligence"
RAW_TABLE = "intelligence_news_alpha_raw_daily"
FULL_RAW_TABLE_ID = f"{PROJECT_ID}.{RAW_DATASET}.{RAW_TABLE}"

CURSOR_TABLE_ID = f"{PROJECT_ID}.monitoring.alpha_news_cursor"

# API Configuration
ALPHA_API_KEY = get_api_key('ALPHA_VANTAGE_API_KEY')
ALPHA_ENDPOINT = "https://www.alphavantage.co/query"

# Ticker watchlist (ZL proxies - no ZL direct ticker in Alpha)
TICKER_WATCHLIST = [
    # Ag & Processing
    'ADM', 'BG', 'CTVA', 'AGCO', 'DE', 'MOS', 'NTR',
    # Biofuel / Feedstock
    'DAR', 'GEVO', 'MPC', 'VLO', 'PSX', 'CVX', 'XOM',
    # Shipping
    'ZIM', 'SFL', 'STNG',
    # Macro
    'SPY', 'XLE'
]


def get_bq_client():
    """Get BigQuery client."""
    return bigquery.Client(project=PROJECT_ID)


def ensure_cursor_table(client: bigquery.Client):
    """Ensure monitoring cursor table exists."""
    schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("last_time_from", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    try:
        client.get_table(CURSOR_TABLE_ID)
    except Exception:
        logger.info(f"Creating cursor table: {CURSOR_TABLE_ID}")
        table = bigquery.Table(CURSOR_TABLE_ID, schema=schema)
        client.create_table(table)
        
        # Initialize with 24 hours ago
        initial_cursor = datetime.now(timezone.utc) - timedelta(hours=24)
        rows = [{
            "id": "alpha_news",
            "last_time_from": initial_cursor.isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }]
        client.insert_rows_json(CURSOR_TABLE_ID, rows)


def get_last_time_from(client: bigquery.Client) -> datetime:
    """Get last collection timestamp from cursor table."""
    ensure_cursor_table(client)
    
    query = f"""
    SELECT last_time_from
    FROM `{CURSOR_TABLE_ID}`
    WHERE id = 'alpha_news'
    """
    
    job = client.query(query)
    rows = list(job)
    
    if not rows:
        # Default: 24 hours ago
        return datetime.now(timezone.utc) - timedelta(hours=24)
    
    return rows[0]["last_time_from"]


def update_cursor(client: bigquery.Client, last_time: datetime):
    """Update cursor with new timestamp."""
    # Use MERGE to upsert
    query = f"""
    MERGE `{CURSOR_TABLE_ID}` AS target
    USING (SELECT 'alpha_news' AS id) AS source
    ON target.id = source.id
    WHEN MATCHED THEN
      UPDATE SET 
        last_time_from = TIMESTAMP('{last_time.isoformat()}'),
        updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
      INSERT (id, last_time_from, updated_at)
      VALUES ('alpha_news', TIMESTAMP('{last_time.isoformat()}'), CURRENT_TIMESTAMP())
    """
    
    job = client.query(query)
    job.result()
    logger.info(f"Updated cursor to {last_time}")


def fetch_alpha_news(time_from: datetime) -> list:
    """
    Fetch news from Alpha Vantage NEWS_SENTIMENT API.
    
    Uses ticker watchlist (no topics filter to avoid over-filtering).
    """
    if not ALPHA_API_KEY:
        logger.error("Alpha Vantage API key not found in keychain")
        return []
    
    time_from_str = time_from.strftime("%Y%m%dT%H%M")
    tickers_param = ",".join(TICKER_WATCHLIST)
    
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": tickers_param,
        "time_from": time_from_str,
        "sort": "LATEST",
        "limit": 100,  # Safe limit
        "apikey": ALPHA_API_KEY,
    }
    
    logger.info(f"Fetching Alpha Vantage NEWS_SENTIMENT...")
    logger.info(f"  Tickers: {tickers_param}")
    logger.info(f"  Time from: {time_from_str}")
    
    try:
        response = requests.get(ALPHA_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "feed" not in data:
            logger.warning(f"No 'feed' in response: {list(data.keys())}")
            return []
        
        feed = data["feed"]
        logger.info(f"✅ Retrieved {len(feed)} articles")
        return feed
        
    except Exception as e:
        logger.error(f"Failed to fetch Alpha news: {e}")
        return []


def normalize_article(article: dict, ingested_at: datetime) -> dict:
    """
    Normalize Alpha Vantage article to CBI-V14 schema.
    
    Maps Alpha's structure to our intelligence_news_alpha_raw_daily schema.
    """
    # Parse time_published
    time_published_str = article.get("time_published", "")
    try:
        # Alpha uses format: "20251117T204500"
        time_published = datetime.strptime(time_published_str, "%Y%m%dT%H%M%S")
        time_published = time_published.replace(tzinfo=timezone.utc)
    except Exception:
        time_published = ingested_at
    
    # Extract tickers array
    tickers = [
        t.get("ticker") 
        for t in article.get("ticker_sentiment", []) 
        if t.get("ticker")
    ]
    
    # Extract topics array (preserve structure)
    topics = article.get("topics", [])
    
    # Extract ticker sentiment array (preserve structure)
    ticker_sentiment = article.get("ticker_sentiment", [])
    
    return {
        "time_published": time_published.isoformat(),
        "ingest_timestamp": ingested_at.isoformat(),
        "headline": article.get("title"),
        "summary": article.get("summary"),
        "url": article.get("url"),
        "source": article.get("source"),
        "source_domain": article.get("source_domain"),
        "tickers": tickers,
        "topics": topics,
        "overall_sentiment_score": float(article.get("overall_sentiment_score")) if article.get("overall_sentiment_score") else None,
        "overall_sentiment_label": article.get("overall_sentiment_label"),
        "ticker_sentiment": ticker_sentiment,
        "raw_json": article,
        "data_quality_flag": "ok"
    }


def load_to_bigquery(client: bigquery.Client, rows: list):
    """Load normalized rows to BigQuery."""
    if not rows:
        logger.warning("No rows to insert")
        return
    
    errors = client.insert_rows_json(FULL_RAW_TABLE_ID, rows)
    
    if errors:
        logger.error(f"BigQuery insertion errors: {errors}")
    else:
        logger.info(f"✅ Inserted {len(rows)} rows into {FULL_RAW_TABLE_ID}")


def main():
    """Main ingestion function."""
    logger.info("="*80)
    logger.info("Alpha Vantage NEWS_SENTIMENT Ingestion")
    logger.info("="*80)
    
    client = get_bq_client()
    
    # Get last collection timestamp
    last_time_from = get_last_time_from(client)
    logger.info(f"Last collection: {last_time_from}")
    
    # Fetch new articles
    ingested_at = datetime.now(timezone.utc)
    feed = fetch_alpha_news(last_time_from)
    
    if not feed:
        logger.warning("No new articles")
        return
    
    # Normalize articles
    rows = [normalize_article(a, ingested_at) for a in feed]
    
    # Find max time_published for cursor update
    max_time = max(
        datetime.strptime(a.get("time_published", ""), "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        for a in feed 
        if a.get("time_published")
    )
    
    # Load to BigQuery
    load_to_bigquery(client, rows)
    
    # Update cursor
    update_cursor(client, max_time)
    
    logger.info("="*80)
    logger.info("✅ Collection Complete")
    logger.info(f"   Articles: {len(rows)}")
    logger.info(f"   Next collection from: {max_time}")
    logger.info("="*80)


if __name__ == "__main__":
    main()
```

---

## 4. Aggregation SQL (Daily Scheduled Query)

**Purpose**: Convert classified news → daily hidden relationship signals  
**Schedule**: Daily at 03:00 UTC  
**Target**: `signals.hidden_relationship_signals`

```sql
-- ============================================================================
-- Daily Hidden Relationship Signals Aggregation
-- Source: raw_intelligence.intelligence_news_alpha_classified_daily
-- Target: signals.hidden_relationship_signals
-- Schedule: Daily at 03:00 UTC
-- ============================================================================

DECLARE target_date DATE DEFAULT DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY);

INSERT INTO `cbi-v14.signals.hidden_relationship_signals` (
  date,
  hidden_biofuel_lobbying_pressure,
  hidden_china_alt_bloc_score,
  hidden_defense_agri_score,
  hidden_cbdc_corridor_score,
  hidden_carbon_arbitrage_score,
  hidden_port_capacity_lead_index,
  hidden_pharma_agri_score,
  hidden_swf_lead_flow_score,
  hidden_academic_exchange_score,
  hidden_trump_argentina_backchannel_score,
  hidden_relationship_composite_score,
  rows_contributing
)
WITH base AS (
  SELECT
    DATE(time_published) AS date,
    hidden_relationships,
    relevance_to_soy_complex,
    impact_strength,
    directional_impact_zl
  FROM `cbi-v14.raw_intelligence.intelligence_news_alpha_classified_daily`
  WHERE DATE(time_published) = target_date
    AND relevance_to_soy_complex >= 40   -- Only high-relevance articles
),

-- Expand hidden_relationships array
exploded AS (
  SELECT
    date,
    rel AS relationship,
    impact_strength,
    directional_impact_zl
  FROM base, UNNEST(hidden_relationships) AS rel
),

-- Aggregate by relationship type
rel_agg AS (
  SELECT
    date,
    -- Average impact strength by relationship type
    AVG(CASE WHEN relationship = 'biofuel_lobbying_chain' THEN impact_strength END) AS biofuel_lobbying_raw,
    AVG(CASE WHEN relationship = 'china_alt_bloc_diplomacy' THEN impact_strength END) AS china_alt_bloc_raw,
    AVG(CASE WHEN relationship = 'defense_agri_nexus' THEN impact_strength END) AS defense_agri_raw,
    AVG(CASE WHEN relationship = 'cbdc_corridor_effect' THEN impact_strength END) AS cbdc_corridor_raw,
    AVG(CASE WHEN relationship = 'carbon_market_arbitrage' THEN impact_strength END) AS carbon_arbitrage_raw,
    AVG(CASE WHEN relationship = 'deep_water_port_intel' THEN impact_strength END) AS port_capacity_raw,
    AVG(CASE WHEN relationship = 'pharma_agri_link' THEN impact_strength END) AS pharma_agri_raw,
    AVG(CASE WHEN relationship = 'sovereign_wealth_fund_effect' THEN impact_strength END) AS swf_raw,
    AVG(CASE WHEN relationship = 'educational_exchange_trade_nexus' THEN impact_strength END) AS academic_raw,
    AVG(CASE WHEN relationship = 'trump_argentina_backchannel' THEN impact_strength END) AS trump_argentina_raw
  FROM exploded
  GROUP BY date
),

-- Normalize to 0-1 scale (impact_strength is 0-100)
normalized AS (
  SELECT
    date,
    SAFE_DIVIDE(biofuel_lobbying_raw, 100.0) AS hidden_biofuel_lobbying_pressure,
    SAFE_DIVIDE(china_alt_bloc_raw, 100.0) AS hidden_china_alt_bloc_score,
    SAFE_DIVIDE(defense_agri_raw, 100.0) AS hidden_defense_agri_score,
    SAFE_DIVIDE(cbdc_corridor_raw, 100.0) AS hidden_cbdc_corridor_score,
    SAFE_DIVIDE(carbon_arbitrage_raw, 100.0) AS hidden_carbon_arbitrage_score,
    SAFE_DIVIDE(port_capacity_raw, 100.0) AS hidden_port_capacity_lead_index,
    SAFE_DIVIDE(pharma_agri_raw, 100.0) AS hidden_pharma_agri_score,
    SAFE_DIVIDE(swf_raw, 100.0) AS hidden_swf_lead_flow_score,
    SAFE_DIVIDE(academic_raw, 100.0) AS hidden_academic_exchange_score,
    SAFE_DIVIDE(trump_argentina_raw, 100.0) AS hidden_trump_argentina_backchannel_score
  FROM rel_agg
),

-- Compute weighted composite score
composite AS (
  SELECT
    n.date,
    n.* EXCEPT(date),
    -- Weighted average of non-null scores
    -- Weights: Biofuel & China (1.2), Defense & CBDC & Trump-Argentina (1.0), Others (0.6-0.8)
    (
      COALESCE(hidden_biofuel_lobbying_pressure, 0) * 1.2 +
      COALESCE(hidden_china_alt_bloc_score, 0) * 1.2 +
      COALESCE(hidden_defense_agri_score, 0) * 1.0 +
      COALESCE(hidden_cbdc_corridor_score, 0) * 1.0 +
      COALESCE(hidden_carbon_arbitrage_score, 0) * 0.8 +
      COALESCE(hidden_port_capacity_lead_index, 0) * 0.8 +
      COALESCE(hidden_pharma_agri_score, 0) * 0.6 +
      COALESCE(hidden_swf_lead_flow_score, 0) * 0.8 +
      COALESCE(hidden_academic_exchange_score, 0) * 0.6 +
      COALESCE(hidden_trump_argentina_backchannel_score, 0) * 1.0
    ) / NULLIF(
      (CASE WHEN hidden_biofuel_lobbying_pressure IS NOT NULL THEN 1.2 ELSE 0 END) +
      (CASE WHEN hidden_china_alt_bloc_score IS NOT NULL THEN 1.2 ELSE 0 END) +
      (CASE WHEN hidden_defense_agri_score IS NOT NULL THEN 1.0 ELSE 0 END) +
      (CASE WHEN hidden_cbdc_corridor_score IS NOT NULL THEN 1.0 ELSE 0 END) +
      (CASE WHEN hidden_carbon_arbitrage_score IS NOT NULL THEN 0.8 ELSE 0 END) +
      (CASE WHEN hidden_port_capacity_lead_index IS NOT NULL THEN 0.8 ELSE 0 END) +
      (CASE WHEN hidden_pharma_agri_score IS NOT NULL THEN 0.6 ELSE 0 END) +
      (CASE WHEN hidden_swf_lead_flow_score IS NOT NULL THEN 0.8 ELSE 0 END) +
      (CASE WHEN hidden_academic_exchange_score IS NOT NULL THEN 0.6 ELSE 0 END) +
      (CASE WHEN hidden_trump_argentina_backchannel_score IS NOT NULL THEN 1.0 ELSE 0 END),
      0
    ) AS hidden_relationship_composite_score
  FROM normalized AS n
),

-- Count contributing rows
row_counts AS (
  SELECT
    DATE(time_published) AS date,
    COUNT(*) AS rows_contributing
  FROM `cbi-v14.raw_intelligence.intelligence_news_alpha_classified_daily`
  WHERE DATE(time_published) = target_date
    AND relevance_to_soy_complex >= 40
  GROUP BY date
)

-- Final output
SELECT
  c.date,
  c.hidden_biofuel_lobbying_pressure,
  c.hidden_china_alt_bloc_score,
  c.hidden_defense_agri_score,
  c.hidden_cbdc_corridor_score,
  c.hidden_carbon_arbitrage_score,
  c.hidden_port_capacity_lead_index,
  c.hidden_pharma_agri_score,
  c.hidden_swf_lead_flow_score,
  c.hidden_academic_exchange_score,
  c.hidden_trump_argentina_backchannel_score,
  c.hidden_relationship_composite_score,
  COALESCE(rc.rows_contributing, 0) AS rows_contributing
FROM composite AS c
LEFT JOIN row_counts AS rc USING(date);
```

---

## 5. Integration with Existing Pipeline

### 5.1. Wiring into signals.vw_comprehensive_signal_universe

**Location**: `config/bigquery/bigquery-sql/signals/create_ultimate_signal_views.sql`

**Add to view**:
```sql
-- Add hidden relationship signals
LEFT JOIN `cbi-v14.signals.hidden_relationship_signals` h
  ON h.date = s.date
```

**Add columns**:
```sql
  h.hidden_relationship_composite_score,
  h.hidden_biofuel_lobbying_pressure,
  h.hidden_china_alt_bloc_score,
  h.hidden_trump_argentina_backchannel_score,
  h.hidden_defense_agri_score,
  h.hidden_cbdc_corridor_score,
  h.hidden_carbon_arbitrage_score,
  h.hidden_port_capacity_lead_index,
  h.hidden_pharma_agri_score,
  h.hidden_swf_lead_flow_score,
  h.hidden_academic_exchange_score
```

### 5.2. Wiring into Big 7 / Big 14 Signals

**Update**: `config/bigquery/bigquery-sql/signals/create_big8_signal_views.sql`

**Add to vw_hidden_correlation_big8**:
```sql
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_hidden_correlation_big8` AS
SELECT
  date,
  -- Use hidden_relationship_composite_score as the hidden correlation dimension
  hidden_relationship_composite_score AS hidden_correlation_score,
  
  -- Individual component scores
  hidden_biofuel_lobbying_pressure,
  hidden_china_alt_bloc_score,
  hidden_defense_agri_score,
  
  -- Normalize to z-score for Big 7 integration
  (hidden_relationship_composite_score - AVG(hidden_relationship_composite_score) OVER w365) 
  / NULLIF(STDDEV(hidden_relationship_composite_score) OVER w365, 0) AS feature_hidden_correlation

FROM `cbi-v14.signals.hidden_relationship_signals`
WINDOW w365 AS (ORDER BY date ROWS BETWEEN 365 PRECEDING AND CURRENT ROW)
ORDER BY date DESC;
```

---

## 6. Collection Cadence & Rate Limiting

### Alpha Vantage (Free Tier: 25 calls/day)

**Schedule**: Every 3-4 hours (6-8 calls/day)  
**Per Call**: ~100 articles from ticker watchlist  
**Daily Total**: 600-800 articles  
**Leaves room for**: 17-19 other Alpha calls (commodities, forex, technicals)

**Cadence**:
```
00:00 UTC - Fetch news
04:00 UTC - Fetch news
08:00 UTC - Fetch news
12:00 UTC - Fetch news
16:00 UTC - Fetch news
20:00 UTC - Fetch news
```

### ScrapeCreators (50 calls/minute limit)

**Schedule**: Hourly (high-priority buckets), Every 3 hours (medium), Daily (low)  
**Per Hour**: 38 queries × 10 results = 380 articles  
**Daily Total**: 3,000-5,000 articles (deduplicated)

---

## 7. Summary - Naming Alignment

| Component | Proposed | CBI-V14 Aligned | Status |
|-----------|----------|-----------------|--------|
| Raw table | `alpha_news_raw` | `intelligence_news_alpha_raw_daily` | ✅ Aligned |
| Classified table | `alpha_news_classified` | `intelligence_news_alpha_classified_daily` | ✅ Aligned |
| Signals table | `hidden_relationship_signals` | `hidden_relationship_signals` | ✅ Aligned |
| Cursor table | `alpha_news_cursor` | `alpha_news_cursor` | ✅ Aligned |
| Dataset (raw) | `raw_intelligence` | `raw_intelligence` | ✅ Aligned |
| Dataset (signals) | `signals` | `signals` | ✅ Aligned |
| Dataset (monitoring) | `monitoring` | `monitoring` | ✅ Aligned |

**All naming conventions match CBI-V14 standards ✅**

---

**Next Steps**:
1. Create tables in BigQuery (run DDL)
2. Test Alpha ingestion script
3. Implement GPT classification (separate script)
4. Set up daily aggregation query
5. Run ScrapeCreators with bucket structure

---

**Last Updated**: November 18, 2025  
**Status**: Ready for Implementation  
**Naming**: ✅ Fully Aligned with CBI-V14 Conventions

