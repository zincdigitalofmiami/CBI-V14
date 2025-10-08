#!/usr/bin/env python3
"""
Trump-VIX Correlation Intelligence System
Monitors presidential administration market impact via VIX correlation
Uses legal, compliant sources only - NO social media scraping
PRODUCTION GRADE - Following CURSOR_RULES
"""

import logging
import requests
import yfinance as yf
from datetime import datetime, timezone, timedelta
from google.cloud import bigquery
import pandas as pd
import uuid
import json
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/trump_vix_correlation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('trump_vix')

class TrumpVIXCorrelation:
    """
    Production-grade Trump-VIX correlation monitoring
    Uses LEGAL sources only - Federal Register, White House, official channels
    """
    
    def __init__(self):
        self.client = bigquery.Client(project='cbi-v14')
        
        # Fear keywords that correlate with VIX spikes
        self.fear_keywords = [
            'military', 'dissent', 'democrat', 'war', 'conflict',
            'tariff', 'sanctions', 'retaliation', 'crisis', 'emergency',
            'shutdown', 'investigation', 'impeachment', 'lawsuit'
        ]
        
        # Market impact keywords
        self.market_keywords = [
            'trade', 'economy', 'inflation', 'fed', 'interest',
            'dollar', 'china', 'agriculture', 'commodity', 'export'
        ]
    
    def collect_current_vix(self):
        """
        Collect current VIX value for correlation analysis
        """
        try:
            # Get VIX from Yahoo Finance
            vix_ticker = yf.Ticker('^VIX')
            vix_data = vix_ticker.history(period='1d')
            
            if not vix_data.empty:
                current_vix = float(vix_data['Close'].iloc[-1])
                logger.info(f"✅ Current VIX: {current_vix:.2f}")
                return current_vix
            
        except Exception as e:
            logger.error(f"❌ VIX collection failed: {e}")
        
        return None
    
    def collect_federal_register_activity(self):
        """
        Collect recent Federal Register activity (LEGAL source)
        Focus on agricultural, trade, and economic policy
        """
        logger.info("📊 Collecting Federal Register Activity...")
        
        try:
            url = 'https://www.federalregister.gov/api/v1/documents.json'
            params = {
                'per_page': 20,
                'order': 'newest',
                'conditions[publication_date][gte]': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
                'conditions[type][]': ['rule', 'proposed_rule', 'notice']
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get('results', [])
                
                logger.info(f"✅ Federal Register: {len(documents)} recent documents")
                return documents
            else:
                logger.warning(f"❌ Federal Register: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Federal Register error: {e}")
        
        return []
    
    def analyze_policy_market_impact(self, documents, current_vix):
        """
        Analyze policy documents for market impact potential
        """
        if not documents:
            return []
        
        analysis_records = []
        
        for doc in documents:
            try:
                title = doc.get('title', '')
                abstract = doc.get('abstract', '')
                pub_date = doc.get('publication_date', '')
                url = doc.get('html_url', '')
                
                # Combine title and abstract for analysis
                full_text = f"{title} {abstract}".lower()
                
                # Count fear keywords
                fear_score = sum(1 for keyword in self.fear_keywords if keyword in full_text)
                
                # Count market keywords
                market_score = sum(1 for keyword in self.market_keywords if keyword in full_text)
                
                # Calculate potential VIX impact
                total_keywords = fear_score + market_score
                vix_impact_potential = min(total_keywords * 0.1, 1.0)  # Cap at 1.0
                
                # Only include if has market relevance
                if total_keywords > 0:
                    record = {
                        'source': 'federal_register',
                        'category': 'trump_policy_analysis',
                        'text': title,
                        'agricultural_impact': market_score * 0.1,
                        'soybean_relevance': market_score * 0.05,
                        'timestamp': datetime.now(timezone.utc),
                        'priority': 1 if fear_score > 2 else 2,
                        'vix_at_time': current_vix,
                        'fear_keyword_count': fear_score,
                        'market_keyword_count': market_score,
                        'vix_impact_potential': vix_impact_potential
                    }
                    
                    analysis_records.append(record)
                    
                    logger.info(f"📄 Policy: {title[:50]}... (Fear: {fear_score}, Market: {market_score})")
            
            except Exception as e:
                logger.error(f"❌ Error analyzing document: {e}")
                continue
        
        logger.info(f"✅ Analyzed {len(analysis_records)} policy documents")
        return analysis_records
    
    def save_to_trump_intelligence(self, trump_data):
        """
        Save Trump analysis to existing ice_trump_intelligence table
        """
        if not trump_data:
            return False
        
        try:
            df = pd.DataFrame(trump_data)
            table_ref = 'cbi-v14.forecasting_data_warehouse.ice_trump_intelligence'
            
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                autodetect=True
            )
            
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Saved {len(trump_data)} Trump-VIX correlation records")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save Trump intelligence: {e}")
            return False
    
    def run_trump_vix_analysis(self):
        """
        Run complete Trump-VIX correlation analysis
        """
        logger.info("=" * 80)
        logger.info("TRUMP-VIX CORRELATION ANALYSIS")
        logger.info("Using LEGAL sources only (Federal Register, official channels)")
        logger.info("=" * 80)
        
        # Get current VIX
        current_vix = self.collect_current_vix()
        
        if current_vix is None:
            logger.error("❌ Cannot proceed without VIX data")
            return False
        
        # Collect Federal Register activity
        documents = self.collect_federal_register_activity()
        
        if not documents:
            logger.warning("No recent Federal Register activity")
            return False
        
        # Analyze for market impact
        trump_analysis = self.analyze_policy_market_impact(documents, current_vix)
        
        if not trump_analysis:
            logger.warning("No market-relevant policy activity")
            return False
        
        # Save to BigQuery
        success = self.save_to_trump_intelligence(trump_analysis)
        
        if success:
            logger.info("=" * 80)
            logger.info(f"🎉 TRUMP-VIX ANALYSIS SUCCESS: {len(trump_analysis)} policies analyzed")
            logger.info(f"📊 Current VIX: {current_vix:.2f}")
            logger.info("✅ Presidential market impact monitoring operational")
            logger.info("=" * 80)
        
        return success

if __name__ == '__main__':
    analyzer = TrumpVIXCorrelation()
    success = analyzer.run_trump_vix_analysis()
    
    if success:
        logger.info("🎉 Trump-VIX Correlation: OPERATIONAL")
        exit(0)
    else:
        logger.error("❌ Trump-VIX Correlation: FAILED")
        exit(1)
