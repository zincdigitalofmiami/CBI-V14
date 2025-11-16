#!/usr/bin/env python3
"""
REAL DATA ONLY - NO FAKE DATA ALLOWED
This script fetches data from BigQuery or returns None.
"""

from google.cloud import bigquery
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class RealDataFetcher:
    def __init__(self):
        self.client = bigquery.Client(project='cbi-v14')
    
    def fetch_data(self, table_name: str) -> pd.DataFrame:
        """
        Fetch REAL data from BigQuery.
        Returns empty DataFrame if data unavailable.
        """
        try:
            query = f"""
            SELECT *
            FROM `cbi-v14.{table_name}`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            """
            df = self.client.query(query).to_dataframe()
            return df
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            return pd.DataFrame()

# NO FAKE DATA - ONLY REAL DATA OR EMPTY
