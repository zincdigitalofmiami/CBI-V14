#!/usr/bin/env python3
"""
TARGETED WEAKNESS SCRAPER
Dynamically fills identified weak areas in training dataset:
1. China demand signals (Client Priority #1)
2. Argentina crisis tracking  
3. Brazil harvest intelligence
4. Biofuel policy/demand

Uses Scrape Creators for Facebook, LinkedIn, Twitter (NO TikTok/Reddit/YouTube)
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timezone
import uuid
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = 'B1TOgQvMVSV6TDglqB8lJ2cirqi2'
client = bigquery.Client(project='cbi-v14')

# TARGETED SOURCES FOR WEAK AREAS
CHINA_SOURCES = {
    'twitter': ['USDAForeignAgSvc', 'CMEGroup', 'Reuters', 'BloombergAgri'],
    'facebook': [
        'https://www.facebook.com/USSoybeanExportCouncil',  # Bangladesh deal!
        'https://www.facebook.com/USDA'
    ]
}

ARGENTINA_SOURCES = {
    'twitter': ['RosarioGrainEx', 'ArgentinaTrade', 'MercadoCentral'],
    'facebook': ['https://www.facebook.com/ArgentinaMinistryAgriculture']
}

BRAZIL_SOURCES = {
    'twitter': ['CONAB_Oficial', 'MinAgriculturaBR', 'ABIOVE'],
    'facebook': ['https://www.facebook.com/MinAgriculturaBR']
}

BIOFUEL_SOURCES = {
    'twitter': ['BiofuelWatch', 'RenewableFuelsAssoc', 'NationalBiodieselBd'],
    'facebook': [
        'https://www.facebook.com/RenewableFuelsAssociation',
        'https://www.facebook.com/NationalBiodieselBoard'
    ]
}

def scrape_facebook_targeted(urls, target_area):
    """Scrape Facebook with cursor pagination for complete coverage"""
    logger.info(f"📘 FACEBOOK: Targeting {target_area}")
    records = []
    
    for fb_url in urls:
        try:
            url = 'https://api.scrapecreators.com/v1/facebook/profile/posts'
            headers = {'x-api-key': API_KEY}
            
            # Initial request
            params = {'url': fb_url}
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('posts', [])
                cursor = data.get('cursor')
                
                page_name = fb_url.split('/')[-1]
                logger.info(f'  ✅ {page_name}: {len(posts)} posts (page 1)')
                
                # Process posts
                for post in posts:
                    text = post.get('text', '')
                    records.append({
                        'platform': 'facebook',
                        'subreddit': None,
                        'title': text[:200] if text else f'{target_area} update',
                        'score': post.get('reactionCount', 0),
                        'comments': post.get('commentCount', 0),
                        'sentiment_score': 0.5,
                        'timestamp': datetime.fromtimestamp(post.get('publishTime', time.time()), tz=timezone.utc),
                        'market_relevance': target_area,
                        'source_name': page_name,
                        'confidence_score': 0.90,
                        'ingest_timestamp_utc': datetime.now(timezone.utc),
                        'provenance_uuid': str(uuid.uuid4())
                    })
                
                # Paginate if cursor available (get MORE data)
                page = 2
                while cursor and page <= 3:  # Get 3 pages max
                    time.sleep(2)
                    params = {'url': fb_url, 'cursor': cursor}
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        more_posts = data.get('posts', [])
                        cursor = data.get('cursor')
                        
                        if more_posts:
                            logger.info(f'  ✅ {page_name}: {len(more_posts)} posts (page {page})')
                            for post in more_posts:
                                text = post.get('text', '')
                                records.append({
                                    'platform': 'facebook',
                                    'subreddit': None,
                                    'title': text[:200] if text else f'{target_area} update',
                                    'score': post.get('reactionCount', 0),
                                    'comments': post.get('commentCount', 0),
                                    'sentiment_score': 0.5,
                                    'timestamp': datetime.fromtimestamp(post.get('publishTime', time.time()), tz=timezone.utc),
                                    'market_relevance': target_area,
                                    'source_name': page_name,
                                    'confidence_score': 0.90,
                                    'ingest_timestamp_utc': datetime.now(timezone.utc),
                                    'provenance_uuid': str(uuid.uuid4())
                                })
                            page += 1
                        else:
                            break
                    else:
                        break
                
                time.sleep(3)  # Rate limiting between sources
                
            else:
                logger.warning(f'  ❌ {fb_url}: HTTP {response.status_code}')
                
        except Exception as e:
            logger.error(f'  ❌ {fb_url}: {e}')
    
    return records

def scrape_twitter_targeted(handles, target_area):
    """Scrape Twitter for targeted intelligence"""
    logger.info(f"🐦 TWITTER: Targeting {target_area}")
    records = []
    
    for handle in handles:
        try:
            url = 'https://api.scrapecreators.com/v1/twitter/user-tweets'
            headers = {'x-api-key': API_KEY}
            params = {'handle': handle}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                tweets_data = data.get('data', {})
                tweets = tweets_data.get('tweets', [])
                
                logger.info(f'  ✅ @{handle}: {len(tweets)} tweets')
                
                for tweet in tweets[:20]:  # Top 20
                    text = tweet.get('text', '')
                    records.append({
                        'platform': 'twitter',
                        'subreddit': None,
                        'title': text[:200] if text else f'{target_area} update',
                        'score': tweet.get('favorite_count', 0),
                        'comments': tweet.get('reply_count', 0),
                        'sentiment_score': 0.5,
                        'timestamp': datetime.now(timezone.utc),
                        'market_relevance': target_area,
                        'source_name': f'@{handle}',
                        'confidence_score': 0.85,
                        'ingest_timestamp_utc': datetime.now(timezone.utc),
                        'provenance_uuid': str(uuid.uuid4())
                    })
                
                time.sleep(2)
                
            else:
                logger.warning(f'  ⚠️ @{handle}: HTTP {response.status_code}')
                
        except Exception as e:
            logger.error(f'  ❌ @{handle}: {e}')
    
    return records

def main():
    """Execute targeted weakness filling"""
    logger.info("=" * 80)
    logger.info("TARGETED WEAKNESS SCRAPER")
    logger.info("Filling: China Demand, Argentina Crisis, Brazil Harvest, Biofuels")
    logger.info("=" * 80)
    
    all_records = []
    
    # 1. CHINA DEMAND (Client Priority #1)
    logger.info("\n🇨🇳 CHINA DEMAND INTELLIGENCE")
    china_fb = scrape_facebook_targeted(CHINA_SOURCES['facebook'], 'china_demand')
    china_tw = scrape_twitter_targeted(CHINA_SOURCES['twitter'], 'china_demand')
    all_records.extend(china_fb)
    all_records.extend(china_tw)
    logger.info(f"   📊 China Total: {len(china_fb) + len(china_tw)} records")
    
    # 2. ARGENTINA CRISIS
    logger.info("\n🇦🇷 ARGENTINA CRISIS TRACKING")
    argentina_tw = scrape_twitter_targeted(ARGENTINA_SOURCES['twitter'], 'argentina_crisis')
    argentina_fb = scrape_facebook_targeted(ARGENTINA_SOURCES['facebook'], 'argentina_crisis')
    all_records.extend(argentina_tw)
    all_records.extend(argentina_fb)
    logger.info(f"   📊 Argentina Total: {len(argentina_tw) + len(argentina_fb)} records")
    
    # 3. BRAZIL HARVEST
    logger.info("\n🇧🇷 BRAZIL HARVEST INTELLIGENCE")
    brazil_tw = scrape_twitter_targeted(BRAZIL_SOURCES['twitter'], 'brazil_harvest')
    brazil_fb = scrape_facebook_targeted(BRAZIL_SOURCES['facebook'], 'brazil_harvest')
    all_records.extend(brazil_tw)
    all_records.extend(brazil_fb)
    logger.info(f"   📊 Brazil Total: {len(brazil_tw) + len(brazil_fb)} records")
    
    # 4. BIOFUEL POLICY/DEMAND
    logger.info("\n🛢️  BIOFUEL POLICY & DEMAND")
    biofuel_tw = scrape_twitter_targeted(BIOFUEL_SOURCES['twitter'], 'biofuel_policy')
    biofuel_fb = scrape_facebook_targeted(BIOFUEL_SOURCES['facebook'], 'biofuel_policy')
    all_records.extend(biofuel_tw)
    all_records.extend(biofuel_fb)
    logger.info(f"   📊 Biofuel Total: {len(biofuel_tw) + len(biofuel_fb)} records")
    
    # SAVE ALL TO BIGQUERY
    if all_records:
        df = pd.DataFrame(all_records)
        
        job = client.load_table_from_dataframe(
            df,
            'cbi-v14.forecasting_data_warehouse.social_sentiment',
            job_config=bigquery.LoadJobConfig(write_disposition='WRITE_APPEND')
        )
        job.result()
        
        logger.info("\n" + "=" * 80)
        logger.info(f"🎉 SUCCESS: {len(all_records)} TOTAL RECORDS SAVED")
        logger.info(f"   🇨🇳 China: {len(china_fb) + len(china_tw)}")
        logger.info(f"   🇦🇷 Argentina: {len(argentina_tw) + len(argentina_fb)}")
        logger.info(f"   🇧🇷 Brazil: {len(brazil_tw) + len(brazil_fb)}")
        logger.info(f"   🛢️  Biofuels: {len(biofuel_tw) + len(biofuel_fb)}")
        logger.info("=" * 80)
        
        return True
    else:
        logger.error("❌ NO RECORDS COLLECTED")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)

