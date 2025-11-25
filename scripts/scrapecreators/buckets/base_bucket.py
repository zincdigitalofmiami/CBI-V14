"""
Base Bucket Collector
====================

Abstract base class for all news bucket collectors.
Provides common functionality for ScrapeCreator API calls and BigQuery loading.
"""

import os
import requests
import pandas as pd
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    from google.cloud import bigquery
except ImportError:
    bigquery = None
    print("Warning: google-cloud-bigquery not installed")


class BaseBucketCollector(ABC):
    """
    Abstract base class for news bucket collectors.
    
    Subclasses must implement:
        - BUCKET_NAME: str
        - KEYWORDS: List[str]
        - SOURCES: List[str]
        - process_results(): method to handle API response
    """
    
    # API Configuration
    SCRAPECREATOR_API_KEY = os.environ.get("SCRAPECREATOR_API_KEY", "B1TOgQvMVSV6TDglqB8lJ2cirqi2")
    SCRAPECREATOR_BASE_URL = "https://api.scrapecreators.com/v1"
    
    # BigQuery Configuration
    PROJECT_ID = "cbi-v14"
    DATASET_ID = "raw_intelligence"
    TABLE_ID = "news_bucketed"
    
    # Must be defined by subclasses
    BUCKET_NAME: str = None
    KEYWORDS: List[str] = []
    SOURCES: List[str] = []
    
    def __init__(self):
        if self.BUCKET_NAME is None:
            raise ValueError("BUCKET_NAME must be defined in subclass")
        if not self.KEYWORDS:
            raise ValueError("KEYWORDS must be defined in subclass")
        
        self.client = None
        if bigquery:
            try:
                self.client = bigquery.Client(project=self.PROJECT_ID)
            except Exception as e:
                print(f"Warning: Could not initialize BigQuery client: {e}")
    
    @abstractmethod
    def process_results(self, raw_results: List[Dict]) -> pd.DataFrame:
        """
        Process raw API results into a standardized DataFrame.
        
        Must return DataFrame with columns:
            - date: DATE
            - bucket: STRING
            - headline: STRING
            - source: STRING
            - url: STRING
            - sentiment_score: FLOAT64 (optional)
            - relevance_score: FLOAT64 (optional)
            - keywords: ARRAY<STRING> (optional)
            - raw_text: STRING (optional)
        """
        pass
    
    def fetch_news(self, days_back: int = 7) -> List[Dict]:
        """
        Fetch news from ScrapeCreator API.
        
        Args:
            days_back: Number of days to look back (default 7)
        
        Returns:
            List of raw API results
        """
        headers = {
            "Authorization": f"Bearer {self.SCRAPECREATOR_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Build query from keywords
        query = " OR ".join(self.KEYWORDS[:10])  # Limit to avoid query size issues
        
        params = {
            "query": query,
            "from_date": (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d"),
            "to_date": datetime.now().strftime("%Y-%m-%d"),
            "page_size": 100
        }
        
        try:
            response = requests.get(
                f"{self.SCRAPECREATOR_BASE_URL}/news/search",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news: {e}")
            return []
    
    def calculate_relevance(self, text: str) -> float:
        """
        Calculate relevance score based on keyword matches.
        
        Args:
            text: Text to analyze
        
        Returns:
            Float between 0 and 1
        """
        if not text:
            return 0.0
        
        text_lower = text.lower()
        matches = sum(1 for kw in self.KEYWORDS if kw.lower() in text_lower)
        return min(matches / max(len(self.KEYWORDS), 1), 1.0)
    
    def load_to_bigquery(self, df: pd.DataFrame) -> bool:
        """
        Load DataFrame to BigQuery.
        
        Args:
            df: DataFrame with standardized columns
        
        Returns:
            True if successful, False otherwise
        """
        if self.client is None:
            print("BigQuery client not available")
            return False
        
        if df.empty:
            print("No data to load")
            return False
        
        # Ensure bucket column is set
        df["bucket"] = self.BUCKET_NAME
        df["ingestion_ts"] = pd.Timestamp.now()
        
        # Load to BigQuery
        table_ref = f"{self.PROJECT_ID}.{self.DATASET_ID}.{self.TABLE_ID}"
        
        try:
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                schema=[
                    bigquery.SchemaField("date", "DATE"),
                    bigquery.SchemaField("bucket", "STRING"),
                    bigquery.SchemaField("headline", "STRING"),
                    bigquery.SchemaField("source", "STRING"),
                    bigquery.SchemaField("url", "STRING"),
                    bigquery.SchemaField("sentiment_score", "FLOAT64"),
                    bigquery.SchemaField("relevance_score", "FLOAT64"),
                    bigquery.SchemaField("keywords", "STRING", mode="REPEATED"),
                    bigquery.SchemaField("raw_text", "STRING"),
                    bigquery.SchemaField("ingestion_ts", "TIMESTAMP"),
                ]
            )
            
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()
            print(f"✅ Loaded {len(df)} rows to {table_ref}")
            return True
        except Exception as e:
            print(f"❌ Error loading to BigQuery: {e}")
            return False
    
    def run(self, days_back: int = 7) -> bool:
        """
        Main entry point: fetch, process, and load news.
        
        Args:
            days_back: Number of days to look back
        
        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'='*60}")
        print(f"Collecting: {self.BUCKET_NAME}")
        print(f"{'='*60}")
        print(f"Keywords: {', '.join(self.KEYWORDS[:5])}...")
        print(f"Days back: {days_back}")
        
        # Fetch
        print("\n1. Fetching news...")
        raw_results = self.fetch_news(days_back)
        print(f"   Found {len(raw_results)} raw results")
        
        if not raw_results:
            print("   No results found")
            return False
        
        # Process
        print("\n2. Processing results...")
        df = self.process_results(raw_results)
        print(f"   Processed {len(df)} records")
        
        if df.empty:
            print("   No valid records after processing")
            return False
        
        # Load
        print("\n3. Loading to BigQuery...")
        success = self.load_to_bigquery(df)
        
        if success:
            print(f"\n✅ {self.BUCKET_NAME} collection complete")
        else:
            print(f"\n❌ {self.BUCKET_NAME} collection failed")
        
        return success


