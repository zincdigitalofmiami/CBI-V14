# ScrapeCreators Integration (CBI-V14)

This package defines the structured interface for ingesting topic-segmented
news and policy content from ScrapeCreators (and related feeds) into
BigQuery for the CBI-V14 system.

## Buckets and BigQuery Tables

Each logical bucket has its own raw table in BigQuery under the
`raw_intelligence` dataset. Examples (final names may be refined):

- `raw_intelligence.biofuel_policy`  
  - Biofuel policy and RFS/RIN-related articles.
- `raw_intelligence.china_demand`  
  - China demand/imports and macro demand signals.
- `raw_intelligence.tariffs_trade_policy`  
  - Tariffs, trade war, export bans, sanctions.
- `raw_intelligence.agg_farming`  
  - Planting/harvest, acreage, yields, farming sentiment.
- `raw_intelligence.trump_feed`  
  - Trump-specific feeds (Truth Social + ScrapeCreators keyword-based sources).

All tables should follow a consistent schema, for example:

- `date` (DATE) – publication date (UTC-normalized)  
- `source` (STRING) – ScrapeCreators, TruthSocial, etc.  
- `topic` (STRING) – bucket/topic label  
- `headline` (STRING) – short headline/title  
- `body` (STRING) – full text (or summary, if truncated)  
- `url` (STRING) – canonical URL where applicable  
- `language` (STRING) – language code if available  
- `ingested_at` (TIMESTAMP) – ingestion timestamp  
- `tags` (ARRAY<STRING>) – optional tags (e.g. 'trump', 'epa', 'china')  

The canonical schemas and their documentation should be kept in sync
with the central data-source reference docs (e.g. DATA_SOURCES_REFERENCE
and CALCULATION_INVENTORY in the main repo).

## Responsibilities

- Provide Python functions that:
  - Pull bucket-specific content from ScrapeCreators / Truth Social APIs.
  - Normalize and validate the records.
  - Load the results into the correct BigQuery tables (using
    `google-cloud-bigquery`, never `pandas-gbq`).
- Hide low-level API details from the rest of the codebase; training and
  feature code should depend only on the BigQuery tables produced here.

## Implementation Status

This directory currently defines the high-level interfaces and layout.
Existing low-level bucket collectors live under:

- `scripts/scrapecreators/buckets/biofuel_policy.py`
- `scripts/scrapecreators/buckets/china_demand.py`
- `scripts/scrapecreators/buckets/tariffs_trade_policy.py`
- `scripts/scrapecreators/buckets/base_bucket.py`

As the integration matures, their logic should be gradually wrapped and
centralized through this package so that all ingestion orchestrators
call into `cbi_v14.api.scrapecreators.*` only.

