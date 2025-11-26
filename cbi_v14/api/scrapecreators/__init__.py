"""
ScrapeCreators API integration and news bucket ingestion.

This subpackage groups all ScrapeCreators-based collectors that feed
the sentiment and micro-predictor layers (biofuel policy, China demand,
tariffs/trade policy, Trump-specific feeds, etc.).

Key responsibilities:
- Fetch topic-segmented news from ScrapeCreators and related sources.
- Land raw documents into BigQuery `raw_intelligence.*` tables.
- Provide a clean, documented interface for upstream buckets used by
  the sentiment and micro-forecaster pipelines.

Implementation of individual buckets lives in:
- `cbi_v14/api/scrapecreators/trump.py`
- `cbi_v14/api/scrapecreators/buckets.py`

Existing bucket scripts under `scripts/scrapecreators/buckets/` remain
the low-level implementations; this package should become the single
entrypoint for new ingestion orchestration.
"""

