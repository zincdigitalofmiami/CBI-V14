"""
Feature engineering utilities for CBI-V14.

This package contains reusable feature builders that operate on
DataFrames and are agnostic to where the data comes from (BigQuery,
Parquet, etc.). Ingestion and persistence are handled elsewhere.

Initial modules focus on high-signal domains such as palm oil, with
ZL-specific helpers, to keep training scripts thin and consistent.
"""

