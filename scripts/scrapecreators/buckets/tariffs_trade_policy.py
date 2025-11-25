"""
Tariffs & Trade Policy Bucket Collector
======================================

Collects news related to trade wars, tariffs, USTR announcements.
Primary bucket - P0 priority.

Keywords: tariff, trade war, USTR, anti-dumping, Section 301
Sources: USTR.gov, Reuters Trade, Bloomberg Trade
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict

from .base_bucket import BaseBucketCollector


class TariffsTradePolicyCollector(BaseBucketCollector):
    """Collector for tariffs and trade policy news."""
    
    BUCKET_NAME = "tariffs_trade_policy"
    
    KEYWORDS = [
        "tariff", "tariffs", "trade war",
        "USTR", "Section 301", "anti-dumping",
        "countervailing duties", "export tax",
        "import ban", "retaliatory tariff",
        "trade agreement", "trade deal",
        "trade talks", "trade negotiations",
        "WTO dispute", "trade sanctions",
        "agricultural tariff", "soybean tariff",
        "China tariff", "trade retaliation"
    ]
    
    SOURCES = [
        "ustr.gov",
        "reuters.com",
        "bloomberg.com",
        "politico.com",
        "agweb.com"
    ]
    
    def process_results(self, raw_results: List[Dict]) -> pd.DataFrame:
        """
        Process raw API results into standardized DataFrame.
        
        Args:
            raw_results: Raw results from ScrapeCreator API
        
        Returns:
            Standardized DataFrame
        """
        records = []
        
        for result in raw_results:
            try:
                # Extract headline/title
                headline = result.get("title") or result.get("headline") or ""
                
                # Skip if no headline
                if not headline:
                    continue
                
                # Extract date
                date_str = result.get("published_at") or result.get("date")
                if date_str:
                    try:
                        date = pd.to_datetime(date_str).date()
                    except:
                        date = datetime.now().date()
                else:
                    date = datetime.now().date()
                
                # Calculate relevance
                full_text = f"{headline} {result.get('description', '')} {result.get('content', '')}"
                relevance = self.calculate_relevance(full_text)
                
                # Skip low relevance
                if relevance < 0.1:
                    continue
                
                # Extract matched keywords
                matched_keywords = [
                    kw for kw in self.KEYWORDS 
                    if kw.lower() in full_text.lower()
                ]
                
                records.append({
                    "date": date,
                    "bucket": self.BUCKET_NAME,
                    "headline": headline[:500],  # Truncate long headlines
                    "source": result.get("source", {}).get("name", "unknown"),
                    "url": result.get("url", ""),
                    "sentiment_score": result.get("sentiment_score"),  # May be None
                    "relevance_score": relevance,
                    "keywords": matched_keywords,
                    "raw_text": full_text[:2000] if full_text else None,  # Truncate
                })
            except Exception as e:
                print(f"   Warning: Error processing result: {e}")
                continue
        
        return pd.DataFrame(records)


def main():
    """Run the tariffs trade policy collector."""
    collector = TariffsTradePolicyCollector()
    collector.run(days_back=7)


if __name__ == "__main__":
    main()


