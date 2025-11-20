-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================================================
-- Alpha Vantage NEWS_SENTIMENT Tables for CBI-V14
-- Aligned with CBI-V14 naming conventions
-- ============================================================================
-- Date: November 18, 2025
-- Project: CBI-V14 Soybean Oil Forecasting Platform
-- Purpose: Create tables for Alpha Vantage news collection and hidden relationship intelligence
-- ============================================================================

-- Set project
SET @@project_id = 'cbi-v14';

-- ============================================================================
-- 1. RAW NEWS FROM ALPHA VANTAGE
-- ============================================================================

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
  
  -- Alpha Vantage specific arrays
  tickers            ARRAY<STRING>,
  topics             ARRAY<STRUCT<
    topic STRING,
    relevance_score STRING
  >>,
  ticker_sentiment   ARRAY<STRUCT<
    ticker STRING,
    relevance_score STRING,
    ticker_sentiment_score STRING,
    ticker_sentiment_label STRING
  >>,
  
  -- Sentiment scores
  overall_sentiment_score  FLOAT64,
  overall_sentiment_label  STRING,
  
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

-- ============================================================================
-- 2. GPT-CLASSIFIED NEWS (Hidden Relationship Intelligence)
-- ============================================================================

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

-- ============================================================================
-- 3. HIDDEN RELATIONSHIP SIGNALS (Daily Aggregates)
-- ============================================================================

CREATE TABLE IF NOT EXISTS `cbi-v14.signals.hidden_relationship_signals` (
  -- Date
  date                                   DATE NOT NULL,
  
  -- Hidden driver scores (0-1 scale, normalized from impact_strength)
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
  
  -- Composite score (weighted average)
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

-- ============================================================================
-- 4. MONITORING CURSOR (Incremental Ingestion)
-- ============================================================================

CREATE TABLE IF NOT EXISTS `cbi-v14.monitoring.alpha_news_cursor` (
  id                STRING NOT NULL,
  last_time_from    TIMESTAMP NOT NULL,
  updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
OPTIONS (
  description = 'Cursor tracking for Alpha Vantage NEWS_SENTIMENT incremental ingestion'
);

-- Initialize cursor (24 hours ago)
INSERT INTO `cbi-v14.monitoring.alpha_news_cursor` (id, last_time_from, updated_at)
VALUES ('alpha_news', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR), CURRENT_TIMESTAMP())
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- INDEXES / PERFORMANCE
-- ============================================================================

-- Note: Partitioning and clustering already defined in CREATE TABLE statements
-- No additional indexes needed for BigQuery

-- ============================================================================
-- PERMISSIONS (if needed)
-- ============================================================================

-- Grant permissions to service accounts or users as needed
-- GRANT `roles/bigquery.dataEditor` ON TABLE `cbi-v14.raw_intelligence.intelligence_news_alpha_raw_daily` TO ...

-- ============================================================================
-- COMPLETION
-- ============================================================================

SELECT 'Alpha Vantage NEWS_SENTIMENT tables created successfully' AS status;





