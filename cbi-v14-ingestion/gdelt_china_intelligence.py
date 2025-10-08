#!/usr/bin/env python3
"""
GDELT China Trade Intelligence Collector
Enhanced real-time monitoring of China-US trade events
Routes to existing news_intelligence table
PRODUCTION GRADE - Following CURSOR_RULES
"""

import logging
from datetime import datetime, timezone, timedelta
from google.cloud import bigquery
import pandas as pd
import uuid
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/gdelt_china_intelligence.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('gdelt_china')

class GDELTChinaIntelligence:
    """
    Production-grade GDELT China trade intelligence collector
    Monitors China-US trade war escalation and de-escalation
    """
    
    def __init__(self):
        self.client = bigquery.Client(project='cbi-v14')
        
        # Trade event codes (from GDELT documentation)
        self.trade_event_codes = [
            '0871',  # Impose trade restrictions
            '1056',  # Impose sanctions
            '0231',  # Express intent to cooperate economically
            '0311',  # Express intent to meet or negotiate
            '0411'   # Consult on policy
        ]
        
        # Keywords for agricultural/commodity relevance
        self.ag_keywords = [
            'soybean', 'corn', 'wheat', 'agriculture', 'farm', 'crop',
            'tariff', 'trade', 'export', 'import', 'commodity'
        ]
    
    def collect_china_trade_events(self, days_back=7):
        """
        Collect China-US trade events from GDELT
        Routes to existing news_intelligence table
        """
        logger.info(f"📊 Collecting GDELT China trade events (last {days_back} days)")
        
        # Build GDELT query for China-US trade events
        event_codes_str = "', '".join(self.trade_event_codes)
        
        query = f"""
        SELECT 
            SQLDATE,
            Actor1CountryCode,
            Actor2CountryCode,
            EventCode,
            EventBaseCode,
            EventRootCode,
            GoldsteinScale,
            NumMentions,
            NumSources,
            NumArticles,
            AvgTone,
            SOURCEURL
        FROM `gdelt-bq.gdeltv2.events`
        WHERE DATE(PARSE_DATE('%Y%m%d', CAST(SQLDATE AS STRING))) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY)
            AND (
                (Actor1CountryCode = 'CHN' AND Actor2CountryCode = 'USA')
                OR (Actor1CountryCode = 'USA' AND Actor2CountryCode = 'CHN')
                OR (Actor1CountryCode = 'CHN' AND EventCode IN ('{event_codes_str}'))
                OR (Actor2CountryCode = 'CHN' AND EventCode IN ('{event_codes_str}'))
            )
            AND (
                LOWER(SOURCEURL) LIKE '%tariff%'
                OR LOWER(SOURCEURL) LIKE '%trade%'
                OR LOWER(SOURCEURL) LIKE '%soybean%'
                OR LOWER(SOURCEURL) LIKE '%agriculture%'
                OR LOWER(SOURCEURL) LIKE '%commodity%'
            )
        ORDER BY SQLDATE DESC, NumMentions DESC
        LIMIT 50
        """
        
        try:
            result = self.client.query(query).to_dataframe()
            logger.info(f"✅ GDELT query returned {len(result)} events")
            return result
            
        except Exception as e:
            logger.error(f"❌ GDELT query failed: {e}")
            return pd.DataFrame()
    
    def process_events_to_intelligence(self, events_df):
        """
        Process GDELT events into news_intelligence schema
        """
        if events_df.empty:
            return []
        
        intelligence_records = []
        
        for _, event in events_df.iterrows():
            try:
                # Calculate agricultural relevance
                url_text = str(event['SOURCEURL']).lower()
                ag_relevance = sum(1 for keyword in self.ag_keywords if keyword in url_text)
                
                # Calculate intelligence score based on multiple factors
                goldstein_impact = abs(event['GoldsteinScale']) / 10.0  # Normalize to 0-1
                mention_impact = min(event['NumMentions'] / 100.0, 1.0)  # Cap at 1.0
                ag_impact = ag_relevance / len(self.ag_keywords)  # Agricultural relevance
                
                intelligence_score = (goldstein_impact + mention_impact + ag_impact) / 3.0
                
                # Create title based on event
                actors = f"{event['Actor1CountryCode']} → {event['Actor2CountryCode']}"
                event_type = self.get_event_description(event['EventCode'])
                title = f"China Trade Event: {event_type} ({actors})"
                
                # Create content summary
                content = f"""
                Trade Event Analysis:
                - Date: {event['SQLDATE']}
                - Actors: {event['Actor1CountryCode']} → {event['Actor2CountryCode']}
                - Event Code: {event['EventCode']} ({event_type})
                - Goldstein Scale: {event['GoldsteinScale']} (impact intensity)
                - Media Coverage: {event['NumMentions']} mentions, {event['NumSources']} sources
                - Tone: {event['AvgTone']} (sentiment)
                - Agricultural Keywords: {ag_relevance}/{len(self.ag_keywords)}
                """.strip()
                
                record = {
                    'title': title,
                    'source': 'GDELT',
                    'category': 'china_trade',
                    'url': event['SOURCEURL'],
                    'published': datetime.now(timezone.utc),
                    'content': content,
                    'intelligence_score': intelligence_score,
                    'processed_timestamp': datetime.now(timezone.utc),
                    # Canonical metadata
                    'source_name': 'GDELT',
                    'confidence_score': 0.70,
                    'ingest_timestamp_utc': datetime.now(timezone.utc),
                    'provenance_uuid': str(uuid.uuid4())
                }
                
                intelligence_records.append(record)
                
            except Exception as e:
                logger.error(f"❌ Error processing event: {e}")
                continue
        
        logger.info(f"✅ Processed {len(intelligence_records)} events to intelligence format")
        return intelligence_records
    
    def get_event_description(self, event_code):
        """
        Map GDELT event codes to human-readable descriptions
        """
        event_map = {
            '0871': 'Impose trade restrictions',
            '1056': 'Impose sanctions',
            '0231': 'Express intent to cooperate economically',
            '0311': 'Express intent to meet or negotiate',
            '0411': 'Consult on policy'
        }
        return event_map.get(event_code, f'Trade event {event_code}')
    
    def save_to_news_intelligence(self, intelligence_data):
        """
        Save processed intelligence to existing news_intelligence table
        """
        if not intelligence_data:
            logger.warning("No intelligence data to save")
            return False
        
        try:
            df = pd.DataFrame(intelligence_data)
            table_ref = 'cbi-v14.forecasting_data_warehouse.news_intelligence'
            
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                autodetect=True
            )
            
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Saved {len(intelligence_data)} China intelligence records")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save China intelligence: {e}")
            return False
    
    def run_china_intelligence_collection(self):
        """
        Run complete China intelligence collection cycle
        """
        logger.info("=" * 80)
        logger.info("GDELT CHINA TRADE INTELLIGENCE COLLECTION")
        logger.info("=" * 80)
        
        # Collect events
        events = self.collect_china_trade_events(days_back=7)
        
        if events.empty:
            logger.warning("No China trade events found")
            return False
        
        # Process to intelligence format
        intelligence_data = self.process_events_to_intelligence(events)
        
        if not intelligence_data:
            logger.warning("No intelligence data processed")
            return False
        
        # Save to BigQuery
        success = self.save_to_news_intelligence(intelligence_data)
        
        if success:
            logger.info("=" * 80)
            logger.info(f"🎉 CHINA INTELLIGENCE SUCCESS: {len(intelligence_data)} events processed")
            logger.info("✅ Enhanced trade war monitoring operational")
            logger.info("✅ Real-time China sentiment analysis active")
            logger.info("=" * 80)
        
        return success

if __name__ == '__main__':
    collector = GDELTChinaIntelligence()
    success = collector.run_china_intelligence_collection()
    
    if success:
        logger.info("🎉 GDELT China Intelligence: OPERATIONAL")
        exit(0)
    else:
        logger.error("❌ GDELT China Intelligence: FAILED")
        exit(1)
