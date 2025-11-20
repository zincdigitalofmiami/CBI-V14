#!/usr/bin/env python3
"""
ScrapeCreators News Collection with Bucket Classification
Collects ZL-relevant news via Google Search API with 10-bucket regime structure
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.keychain_manager import get_api_key
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import hashlib
from urllib.parse import urlparse
import logging
from typing import Dict, List, Optional
from scripts.ingest.news_bucket_classifier import (
    classify_article_to_bucket,
    filter_article_by_buckets,
    get_p0_p1_buckets,
    BUCKET_KEYWORDS
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Configuration
SCRAPE_CREATORS_KEY = get_api_key('SCRAPE_CREATORS_KEY') or os.getenv('SCRAPE_CREATORS_KEY')
BASE_URL = 'https://api.scrapecreators.com/v1/google/search'
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
OUTPUT_DIR = EXTERNAL_DRIVE / "TrainingData/raw/scrapecreators"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Rate limiting
API_CALL_WAIT_SECONDS = 1.5  # Conservative: 40 calls/minute


# ============================================================================
# BUCKET-ALIGNED SEARCH QUERIES
# ============================================================================

BUCKET_QUERIES = {
    '1_BIOFUEL_POLICY': [
        'EPA renewable fuel standard RFS volumes',
        'SAF sustainable aviation fuel tax credit',
        'LCFS low carbon fuel standard California',
        'biodiesel blend mandate B20 B40',
        'renewable diesel capacity expansion'
    ],
    
    '2_PALM_SUPPLY_POLICY': [
        'Indonesia CPO palm oil export levy tax',
        'Malaysia palm oil supply DMO policy',
        'palm oil export ban Indonesia Malaysia',
        'India edible oil import duty palm'
    ],
    
    '3_CHINA_DEMAND': [
        'China soybean imports state reserves Sinograin',
        'COFCO soybean crush margins China',
        'Dalian soy oil DCE futures China',
        'China food security soybean stockpile',
        'China soybean auction NDRC'
    ],
    
    '4_US_POLICY_TARIFFS': [
        'Trump tariff threat agriculture soybean',
        '301 investigation trade retaliation agriculture',
        'Argentina IMF cooperation agriculture',
        'US Farm Bill commodity programs soybean',
        'agricultural trade exemption policy'
    ],
    
    '5_SOUTH_AMERICA_SUPPLY': [
        'Brazil soybean harvest CONAB yield',
        'Argentina soybean crop weather harvest',
        'Mato Grosso Brazil soybean drought',
        'Rosario Argentina port strike soybean',
        'Brazil Argentina La Nina El Nino soybean',
        'BR-163 Brazil soybean logistics',
        'Brazil soybean barge delay Mississippi'
    ],
    
    '6_SHIPPING_LOGISTICS': [
        'Red Sea Suez Panama Canal disruption shipping',
        'Baltic Dry Index freight rate agriculture',
        'port strike dockworker agriculture grain',
        'tanker rates clean bulk vegetable oil',
        'marine insurance war risk premium shipping'
    ],
    
    '7_HIDDEN_DRIVERS': [
        'sovereign wealth fund agribusiness investment',
        'EU deforestation EUDR palm soy compliance',
        'China Brazil digital yuan settlement agriculture',
        'port dredging grain terminal expansion',
        'pharmaceutical licensing agricultural reciprocity'
    ],
    
    '8_MACRO_FX': [
        'Brazil real BRL depreciation agriculture export',
        'Argentina peso collapse soybean export',
        'Federal Reserve interest rate commodity agriculture',
        'inflation commodity prices agriculture',
        'CFTC managed money positioning soybean',
        'VIX volatility commodity markets'
    ],
    
    '9_ENERGY_INPUTS': [
        'fertilizer nitrogen potash shortage agriculture',
        'ammonia plant outage fertilizer supply',
        'diesel shortage agriculture logistics',
        'crude oil diesel crack spread biofuel'
    ]
}


# Source credibility scoring
SOURCE_CREDIBILITY = {
    'usda.gov': 1.0,
    'epa.gov': 1.0,
    'ustr.gov': 1.0,
    'whitehouse.gov': 1.0,
    'federalregister.gov': 1.0,
    'reuters.com': 0.95,
    'bloomberg.com': 0.95,
    'wsj.com': 0.95,
    'ft.com': 0.95,
    'cnbc.com': 0.90,
    'ap.org': 0.90,
    'agriculture.com': 0.80,
    'agweb.com': 0.80,
    'dtn.com': 0.80,
    'default': 0.50
}


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        return domain
    except:
        return 'unknown'


def get_source_credibility(domain: str) -> float:
    """Get credibility score for domain."""
    # Check exact match
    if domain in SOURCE_CREDIBILITY:
        return SOURCE_CREDIBILITY[domain]
    
    # Check .gov suffix
    if domain.endswith('.gov'):
        return 1.0
    
    # Check partial matches
    for key in SOURCE_CREDIBILITY:
        if key in domain:
            return SOURCE_CREDIBILITY[key]
    
    return SOURCE_CREDIBILITY['default']


def generate_article_id(url: str) -> str:
    """Generate unique article ID from URL."""
    # Normalize URL
    normalized = url.split('?')[0].rstrip('/')
    # Generate MD5 hash
    return hashlib.md5(normalized.encode()).hexdigest()


def collect_google_search_bucketed(
    bucket_name: str,
    queries: List[str],
    results_per_query: int = 10
) -> List[Dict]:
    """
    Collect news via Google Search for a specific bucket.
    
    Args:
        bucket_name: Bucket name (e.g., '1_BIOFUEL_POLICY')
        queries: List of search queries for this bucket
        results_per_query: Number of results per query
    
    Returns:
        List of classified and filtered articles
    """
    if not SCRAPE_CREATORS_KEY:
        logger.warning("No ScrapeCreators API key found")
        return []
    
    bucket_data = BUCKET_KEYWORDS[bucket_name]
    logger.info(f"\n{'='*80}")
    logger.info(f"Collecting: {bucket_name}")
    logger.info(f"Priority: {bucket_data['priority']} | Impact: {bucket_data['impact']} | Lead: {bucket_data['lead_days']}d")
    logger.info(f"Queries: {len(queries)}")
    logger.info(f"{'='*80}")
    
    url_cache = {}  # Deduplicate by URL
    
    for query_idx, query in enumerate(queries, 1):
        logger.info(f"\n  Query {query_idx}/{len(queries)}: '{query}'")
        
        try:
            # Rate limiting
            time.sleep(API_CALL_WAIT_SECONDS)
            
            # Make API call
            headers = {'x-api-key': SCRAPE_CREATORS_KEY}
            params = {
                'query': query,
                'limit': results_per_query
            }
            
            response = requests.get(BASE_URL, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', []) or data.get('data', [])
                
                logger.info(f"    Retrieved: {len(results)} results")
                
                for rank, result in enumerate(results, 1):
                    url = result.get('url', '')
                    if not url:
                        continue
                    
                    # Deduplicate
                    article_id = generate_article_id(url)
                    
                    if article_id in url_cache:
                        # URL seen before - update metadata
                        url_cache[article_id]['seen_count'] += 1
                        url_cache[article_id]['seen_queries'].append(query)
                        url_cache[article_id]['last_seen_at'] = datetime.now()
                        continue
                    
                    # Extract domain and credibility
                    domain = extract_domain(url)
                    credibility = get_source_credibility(domain)
                    
                    # Classify to bucket
                    classification = classify_article_to_bucket(
                        title=result.get('title', ''),
                        description=result.get('description', '') or result.get('snippet', ''),
                        query=query
                    )
                    
                    # Filter: only keep if classification returned and matches bucket
                    if classification and classification['bucket'] == bucket_name:
                        url_cache[article_id] = {
                            'article_id': article_id,
                            'url': url,
                            'url_domain': domain,
                            'title': result.get('title', ''),
                            'description': result.get('description', '') or result.get('snippet', ''),
                            'source_api': 'scrapecreators',
                            'source_domain': domain,
                            'source_credibility': credibility,
                            'source_type': 'government' if domain.endswith('.gov') else 'press',
                            'collected_at': datetime.now(),
                            'collection_date': datetime.now().date(),
                            'collection_method': 'google_search',
                            'bucket': classification['bucket'],
                            'bucket_priority': classification['bucket_priority'],
                            'bucket_impact': classification['bucket_impact'],
                            'bucket_lead_days': classification['bucket_lead_days'],
                            'search_query': query,
                            'search_rank': rank,
                            'match_score': classification['match_score'],
                            'matched_keywords': ','.join(classification['matched_keywords']),
                            'is_zl_relevant': True,
                            'first_seen_at': datetime.now(),
                            'last_seen_at': datetime.now(),
                            'seen_count': 1,
                            'seen_queries': [query]
                        }
                
                logger.info(f"    Kept after filtering: {len([v for v in url_cache.values() if v['seen_queries'][-1] == query])}")
            else:
                logger.warning(f"    Error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"    Exception: {e}")
    
    logger.info(f"\n✅ Bucket {bucket_name} Complete:")
    logger.info(f"   Unique articles: {len(url_cache)}")
    logger.info(f"   Queries executed: {len(queries)}")
    
    return list(url_cache.values())


def main():
    """Collect news from P0 buckets (highest priority)."""
    logger.info("="*80)
    logger.info("SCRAPECREATORS NEWS COLLECTION - BUCKETED")
    logger.info("="*80)
    
    all_articles = []
    
    # Collect P0 buckets only (highest priority)
    p0_buckets = ['1_BIOFUEL_POLICY', '2_PALM_SUPPLY_POLICY', '3_CHINA_DEMAND', 
                  '4_US_POLICY_TARIFFS', '5_SOUTH_AMERICA_SUPPLY']
    
    for bucket_name in p0_buckets:
        if bucket_name not in BUCKET_QUERIES:
            continue
        
        queries = BUCKET_QUERIES[bucket_name]
        articles = collect_google_search_bucketed(bucket_name, queries)
        all_articles.extend(articles)
        
        logger.info(f"   Added {len(articles)} articles from {bucket_name}")
    
    # Save results
    if all_articles:
        df = pd.DataFrame(all_articles)
        
        # Save to parquet
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = OUTPUT_DIR / f"news_google_search_p0_buckets_{timestamp}.parquet"
        df.to_parquet(output_file, index=False)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ COLLECTION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Total articles: {len(df)}")
        logger.info(f"Output file: {output_file}")
        logger.info(f"\n📊 By Bucket:")
        for bucket in df['bucket'].value_counts().items():
            logger.info(f"   {bucket[0]}: {bucket[1]} articles")
        
        logger.info(f"\n📊 By Source Credibility:")
        logger.info(f"   High (0.9-1.0): {len(df[df['source_credibility'] >= 0.9])}")
        logger.info(f"   Medium (0.7-0.9): {len(df[(df['source_credibility'] >= 0.7) & (df['source_credibility'] < 0.9)])}")
        logger.info(f"   Low (<0.7): {len(df[df['source_credibility'] < 0.7])}")
        
        return df
    else:
        logger.warning("No articles collected")
        return None


if __name__ == '__main__':
    result = main()





