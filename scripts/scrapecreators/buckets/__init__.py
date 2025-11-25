"""
ScrapeCreator News Bucket Scripts
=================================

Each script in this directory corresponds to a news bucket defined in
NEWS_BUCKET_TAXONOMY.md. Scripts are responsible for:

1. Fetching news from ScrapeCreator API with bucket-specific keywords
2. Scoring/filtering relevance
3. Loading to BigQuery `raw_intelligence.news_bucketed` table

Usage:
    python -m scripts.scrapecreators.buckets.tariffs_trade_policy
    python -m scripts.scrapecreators.buckets.china_demand
    # etc.

API Key:
    Set SCRAPECREATOR_API_KEY environment variable
    or use the key from memory: B1TOgQvMVSV6TDglqB8lJ2cirqi2

BigQuery Target:
    cbi-v14.raw_intelligence.news_bucketed
"""


