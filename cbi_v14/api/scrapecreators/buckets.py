"""
Topic bucket ingestion wrappers for ScrapeCreators-based feeds.

This module defines high-level entrypoints for each of the major news
and policy buckets used by the sentiment and micro-predictor layers.

Existing bucket implementations live under `scripts/scrapecreators/buckets/`.
Over time, their logic should be centralized behind these functions so
that ingestion orchestrators only call into `cbi_v14.api.scrapecreators`.
"""

from typing import Optional, Sequence

from google.cloud import bigquery


def ingest_biofuel_policy_to_bigquery(
    bq_client: bigquery.Client,
    table_id: str = "cbi-v14.raw_intelligence.biofuel_policy",
    *,
    max_items: Optional[int] = None,
    dry_run: bool = False,
) -> int:
    """
    Ingest biofuel policy / RFS / RIN-related articles into BigQuery.

    Parameters
    ----------
    bq_client :
        Initialized BigQuery client.
    table_id :
        Fully-qualified BigQuery table ID where records will be written.
    max_items :
        Optional cap on the number of items to ingest in a single run.
    dry_run :
        If True, validate without writing to BigQuery.

    Returns
    -------
    int
        Number of records ingested (or that would be ingested in dry-run).
    """
    _ = (table_id, max_items, dry_run)
    # TODO: wrap scripts/scrapecreators/buckets/biofuel_policy.py logic here.
    return 0


def ingest_china_demand_to_bigquery(
    bq_client: bigquery.Client,
    table_id: str = "cbi-v14.raw_intelligence.china_demand",
    *,
    max_items: Optional[int] = None,
    dry_run: bool = False,
) -> int:
    """
    Ingest China demand/import-related articles into BigQuery.
    """
    _ = (table_id, max_items, dry_run)
    # TODO: wrap scripts/scrapecreators/buckets/china_demand.py logic here.
    return 0


def ingest_tariffs_trade_policy_to_bigquery(
    bq_client: bigquery.Client,
    table_id: str = "cbi-v14.raw_intelligence.tariffs_trade_policy",
    *,
    max_items: Optional[int] = None,
    dry_run: bool = False,
) -> int:
    """
    Ingest tariffs/trade-policy articles into BigQuery.
    """
    _ = (table_id, max_items, dry_run)
    # TODO: wrap scripts/scrapecreators/buckets/tariffs_trade_policy.py logic here.
    return 0


