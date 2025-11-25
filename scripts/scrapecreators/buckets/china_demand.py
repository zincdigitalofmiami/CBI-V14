"""
China Demand Bucket Collector
============================

Collects news related to China purchases, cancellations, import policies.
Primary bucket - P0 priority.

Keywords: China imports, Sinograin, COFCO, soybean cancellations, Dalian
Sources: Xinhua, COFCO announcements, USDA FAS
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict

from .base_bucket import BaseBucketCollector


class ChinaDemandCollector(BaseBucketCollector):
    """Collector for China demand news."""
    
    BUCKET_NAME = "china_demand"
    
    KEYWORDS = [
        "China imports", "China purchases",
        "China soybean", "China cancellation",
        "Sinograin", "COFCO",
        "China reserves", "state reserves",
        "Dalian commodity", "DCE soybean",
        "China crush", "China swine",
        "Phase 1 deal", "China ag purchases",
        "China US soybeans", "China Brazil soybeans",
        "Chinese demand", "China buying",
        "China meal demand", "China oil imports"
    ]
    
    SOURCES = [
        "xinhuanet.com",
        "reuters.com",
        "fas.usda.gov",
        "agrimoney.com",
        "successful-farming.com"
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
                headline = result.get("title") or result.get("headline") or ""
                
                if not headline:
                    continue
                
                date_str = result.get("published_at") or result.get("date")
                if date_str:
                    try:
                        date = pd.to_datetime(date_str).date()
                    except:
                        date = datetime.now().date()
                else:
                    date = datetime.now().date()
                
                full_text = f"{headline} {result.get('description', '')} {result.get('content', '')}"
                relevance = self.calculate_relevance(full_text)
                
                if relevance < 0.1:
                    continue
                
                matched_keywords = [
                    kw for kw in self.KEYWORDS 
                    if kw.lower() in full_text.lower()
                ]
                
                records.append({
                    "date": date,
                    "bucket": self.BUCKET_NAME,
                    "headline": headline[:500],
                    "source": result.get("source", {}).get("name", "unknown"),
                    "url": result.get("url", ""),
                    "sentiment_score": result.get("sentiment_score"),
                    "relevance_score": relevance,
                    "keywords": matched_keywords,
                    "raw_text": full_text[:2000] if full_text else None,
                })
            except Exception as e:
                print(f"   Warning: Error processing result: {e}")
                continue
        
        return pd.DataFrame(records)


def main():
    """Run the China demand collector."""
    collector = ChinaDemandCollector()
    collector.run(days_back=7)


if __name__ == "__main__":
    main()


