"""
Databento GLBX.MDP3 integration for CBI-V14.

This subpackage defines the structured interface for loading Databento
futures data into BigQuery. It is the canonical home for Databento
client wrappers and BigQuery load helpers.

Current production loader logic lives in:
- scripts/ingest/download_ALL_databento_historical.py

As the codebase evolves, the core functionality from that script should
be refactored into reusable functions here, with the script acting as a
thin CLI wrapper.
"""

from typing import Optional, Sequence

from google.cloud import bigquery


def backfill_daily_ohlcv_to_bigquery(
    bq_client: bigquery.Client,
    roots: Sequence[str],
    start_date: str,
    end_date: Optional[str] = None,
    table_id: str = "cbi-v14.market_data.databento_futures_ohlcv_1d",
    dry_run: bool = False,
) -> int:
    """
    Backfill Databento daily OHLCV data into BigQuery for a set of roots.

    This is a high-level interface intended to mirror the behavior of
    `scripts/ingest/download_ALL_databento_historical.py` for daily data.

    Parameters
    ----------
    bq_client :
        Initialized BigQuery client.
    roots :
        Iterable of futures roots to backfill (e.g., ['ZL', 'ZS', 'ZM', 'CL', 'HO']).
    start_date :
        ISO date string (YYYY-MM-DD) for the backfill start.
    end_date :
        Optional ISO date string (YYYY-MM-DD) for the backfill end. If None,
        implementations may default to "today".
    table_id :
        Fully-qualified BigQuery table ID for the daily OHLCV table.
    dry_run :
        If True, validate parameters without calling Databento or writing to BQ.

    Returns
    -------
    int
        Number of rows ingested (or that would be ingested in dry-run mode).

    Notes
    -----
    The concrete Databento API calls and batch loading logic are currently
    implemented in `scripts/ingest/download_ALL_databento_historical.py`.
    This function exists as a documented entrypoint so that future
    orchestration code can depend on the interface while the internals
    are gradually refactored into this package.
    """
    _ = (roots, start_date, end_date, table_id, dry_run)
    # TODO: Call into refactored ingestion helpers once moved from scripts/.
    return 0


