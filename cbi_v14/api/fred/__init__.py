"""
FRED (Federal Reserve Economic Data) integration for CBI-V14.

This subpackage defines the interfaces for collecting macroeconomic
series from FRED and landing them into BigQuery.

Existing collectors live under:
- scripts/ingest/collect_fred_comprehensive.py
- related Quant Check Plan docs (FX_DATA_SOURCE_CLARIFICATION, etc.).

Over time, FRED collection logic should be centralized here so that
ingestion orchestration and feature builders have a single, well-
documented entrypoint for macro series.
"""

from typing import Optional, Sequence

from google.cloud import bigquery


def ingest_fred_series_to_bigquery(
    bq_client: bigquery.Client,
    series_ids: Sequence[str],
    table_id: str = "cbi-v14.macro.fred_series",
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    dry_run: bool = False,
) -> int:
    """
    Ingest selected FRED series into a BigQuery table.

    Parameters
    ----------
    bq_client :
        Initialized BigQuery client.
    series_ids :
        List of FRED series identifiers to pull.
    table_id :
        Target BigQuery table for normalized FRED data.
    start_date, end_date :
        Optional ISO date strings (YYYY-MM-DD) bounding the ingest.
    dry_run :
        If True, perform parameter validation but do not call FRED or write to BQ.

    Returns
    -------
    int
        Number of records ingested (or that would be ingested in dry-run).

    Notes
    -----
    Concrete implementation should wrap the existing collectors in
    `scripts/ingest/collect_fred_comprehensive.py` and ensure all
    schema details are documented in the central data-source reference.
    """
    _ = (series_ids, table_id, start_date, end_date, dry_run)
    # TODO: Implement using existing FRED collector logic.
    return 0


