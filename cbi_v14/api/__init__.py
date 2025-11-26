"""
API clients and ingestion wrappers for CBI-V14.

This package is the home for all external data source integrations
that land data directly into BigQuery. Each subpackage corresponds
to a specific vendor or API (Databento, FRED, ScrapeCreators, etc.).

Design rules:
- All ingestion functions write to BigQuery (google-cloud-bigquery),
  never to the Mac/local drive as a source of truth.
- Each subpackage owns its tables and schemas (documented in its
  README and/or the central data source reference docs).
- CLI scripts under `scripts/` should import and call these wrappers
  rather than re-implementing ingestion logic.
"""

