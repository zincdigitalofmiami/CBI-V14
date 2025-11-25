#!/usr/bin/env python3
"""
SCRAPE CREATORS FULL ACTIVATION
Facebook, LinkedIn, Twitter (X) - Agriculture/Biofuel/Trade Intelligence
NO TIKTOK, NO REDDIT, NO YOUTUBE
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timezone
import uuid
import time
import logging
import os
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from src.utils.keychain_manager import get_api_key as _get_api
except Exception:
    _get_api = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _resolve_secret(env_name: str, key_name: str):
    val = os.getenv(env_name)
    if val:
        return val
    if _get_api:
        try:
            return _get_api(key_name)
        except Exception:
            return None
    return None

API_KEY = _resolve_secret('SCRAPECREATORS_API_KEY', 'SCRAPECREATORS_API_KEY')
if not API_KEY:
    raise RuntimeError("SCRAPECREATORS_API_KEY not set. Export it or store in Keychain 'cbi-v14.SCRAPECREATORS_API_KEY'.")
PROJECT_ID = 'cbi-v14'
client = bigquery.Client(project=PROJECT_ID)

# FACEBOOK SOURCES (URLs required per API docs)
FACEBOOK_SOURCES = [
    'https://www.facebook.com/AmericanSoybean',
    'https://www.facebook.com/USSoybeanExportCouncil',
    'https://www.facebook.com/NationalCornGrowers',
    'https://www.facebook.com/USDA',
    'https://www.facebook.com/RenewableFuelsAssociation',
    'https://www.facebook.com/USGrainsCouncil',
    'https://www.facebook.com/NationalBiodieselBoard'
]

# TWITTER SOURCES (Handles)
TWITTER_SOURCES = [
    'USDAForeignAgSvc',
    'CMEGroup',
    'USGrainsCouncil',
    'SoyGrowers',
    'BrasilAgro'
]

# LINKEDIN COMPANY PAGES
LINKEDIN_SOURCES = [
    'american-soybean-association',
    'renewable-fuels-association',
    'national-biodiesel-board',
    'brazilian-soybean-growers-association'
]

def scrape_facebook():
    """Scrape Facebook pages using correct API parameters"""
    logger.info("📘 FACEBOOK SCRAPING STARTED")
    records = []
    
    for fb_url in FACEBOOK_SOURCES:
        try:
            url = 'https://api.scrapecreators.com/v1/facebook/profile/posts'
            headers = {'x-api-key': API_KEY}
            params = {'url': fb_url}  # Correct parameter!
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('posts', [])
                logger.info(f'✅ {fb_url.split("/")[-1]}: {len(posts)} posts')
                
                for post in posts:
                    records.append({
                        'source': fb_url.split('/')[-1],
                        'platform': 'facebook',
                        'content': post.get('text', '')[:1000],
                        'sentiment_score': 0.5,
                        'timestamp': datetime.fromtimestamp(post.get('publishTime', 0), tz=timezone.utc) if post.get('publishTime') else datetime.now(timezone.utc),
                        'entity_mentions': []
                    })
                
                time.sleep(2)  # Rate limiting
                
            else:
                logger.warning(f'❌ {fb_url}: {response.status_code} - {response.text[:100]}')
                
        except Exception as e:
            logger.error(f'❌ {fb_url}: {e}')
    
    return records

def scrape_twitter():
    """Scrape Twitter using correct API parameters"""
    logger.info("🐦 TWITTER SCRAPING STARTED")
    records = []
    
    for handle in TWITTER_SOURCES:
        try:
            url = 'https://api.scrapecreators.com/v1/twitter/user-tweets'
            headers = {'x-api-key': API_KEY}
            params = {'handle': handle}  # Correct parameter
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                tweets = data.get('data', {}).get('tweets', [])
                logger.info(f'✅ @{handle}: {len(tweets)} tweets')
                
                for tweet in tweets[:20]:  # Limit to 20
                    records.append({
                        'source': handle,
                        'platform': 'twitter',
                        'content': tweet.get('text', '')[:1000],
                        'sentiment_score': 0.5,
                        'timestamp': datetime.now(timezone.utc),
                        'entity_mentions': []
                    })
                
                time.sleep(2)  # Rate limiting
                
            else:
                logger.warning(f'❌ @{handle}: {response.status_code}')
                
        except Exception as e:
            logger.error(f'❌ @{handle}: {e}')
    
    return records

def scrape_linkedin():
    """Scrape LinkedIn company pages"""
    logger.info("💼 LINKEDIN SCRAPING STARTED")
    records = []
    
    for company in LINKEDIN_SOURCES:
        try:
            url = 'https://api.scrapecreators.com/v1/linkedin/company'
            headers = {'x-api-key': API_KEY}
            params = {'company': company}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f'✅ LinkedIn/{company}: Profile retrieved')
                # LinkedIn API returns profile, not posts directly
                # Would need separate call for posts if available
                
                time.sleep(2)
                
            else:
                logger.warning(f'⚠️  LinkedIn/{company}: {response.status_code}')
                
        except Exception as e:
            logger.error(f'❌ LinkedIn/{company}: {e}')
    
    return records

def save_to_bigquery(records):
    """Save to existing social_sentiment table"""
    if not records:
        logger.warning("No records to save")
        return False
    
    try:
        df = pd.DataFrame(records)
        
        job = client.load_table_from_dataframe(
            df,
            'cbi-v14.forecasting_data_warehouse.social_sentiment',
            job_config=bigquery.LoadJobConfig(write_disposition='WRITE_APPEND')
        )
        job.result()
        
        logger.info(f'✅ SAVED {len(records)} RECORDS TO social_sentiment')
        return True
        
    except Exception as e:
        logger.error(f'❌ BigQuery save failed: {e}')
        return False

def main():
    """Execute full Scrape Creators collection"""
    logger.info("=" * 80)
    logger.info("SCRAPE CREATORS FULL ACTIVATION")
    logger.info("SOURCES: Facebook, LinkedIn, Twitter (X)")
    logger.info("TARGETS: Biofuels, Trade, Argentina, China, Brazil")
    logger.info("=" * 80)
    
    all_records = []
    
    # Facebook
    fb_records = scrape_facebook()
    all_records.extend(fb_records)
    logger.info(f"📘 Facebook: {len(fb_records)} records")
    
    # Twitter
    tw_records = scrape_twitter()
    all_records.extend(tw_records)
    logger.info(f"🐦 Twitter: {len(tw_records)} records")
    
    # LinkedIn
    li_records = scrape_linkedin()
    all_records.extend(li_records)
    logger.info(f"💼 LinkedIn: {len(li_records)} records")
    
    # Save all
    if all_records:
        success = save_to_bigquery(all_records)
        
        logger.info("=" * 80)
        logger.info(f"✅ TOTAL RECORDS: {len(all_records)}")
        logger.info(f"📊 BREAKDOWN: FB={len(fb_records)}, TW={len(tw_records)}, LI={len(li_records)}")
        logger.info("=" * 80)
        
        return success
    else:
        logger.error("❌ NO RECORDS COLLECTED FROM ANY SOURCE")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)

<<<<<<< Updated upstream:src/ingestion/scrape_creators_full_blast.py
=======








>>>>>>> Stashed changes:cbi-v14-ingestion/scrape_creators_full_blast.py
