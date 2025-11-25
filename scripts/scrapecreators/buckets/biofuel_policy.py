"""
Biofuel Policy Bucket Collector
==============================

Collects news related to EPA RFS, RVO, biodiesel mandates.
Primary bucket - P0 priority.

Keywords: RFS, RINs, RVO, biodiesel tax credit, 45Z, EPA mandate
Sources: EPA.gov, RFA, EIA, ACE
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict

from .base_bucket import BaseBucketCollector


class BiofuelPolicyCollector(BaseBucketCollector):
    """Collector for biofuel policy news."""
    
    BUCKET_NAME = "biofuel_policy"
    
    KEYWORDS = [
        "RFS", "renewable fuel standard",
        "RINs", "renewable identification number",
        "RVO", "renewable volume obligation",
        "biodiesel tax credit", "45Z",
        "blenders credit", "biodiesel mandate",
        "EPA biofuel", "EPA mandate",
        "biomass-based diesel", "renewable diesel",
        "sustainable aviation fuel", "SAF",
        "small refinery exemption", "SRE",
        "biofuel blending", "E15",
        "ethanol mandate", "biodiesel production"
    ]
    
    SOURCES = [
        "epa.gov",
        "ethanolrfa.org",
        "eia.gov",
        "biodieselmagazine.com",
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
    """Run the biofuel policy collector."""
    collector = BiofuelPolicyCollector()
    collector.run(days_back=7)


if __name__ == "__main__":
    main()


