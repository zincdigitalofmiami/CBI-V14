#!/usr/bin/env python3
"""
ICE & Trump Effect Intelligence System
Monitors immigration enforcement impacts on agricultural labor
Tracks Trump policy effects on commodity markets and trade
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from google.cloud import bigquery
import json
import time
from datetime import datetime, timedelta
import re

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

class ICETrumpIntelligence:
    """
    Specialized monitoring for ICE enforcement and Trump political effects
    Critical for understanding labor disruption and policy volatility
    """
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.ice_sources = self._build_ice_matrix()
        self.trump_sources = self._build_trump_matrix()
        self.agricultural_regions = self._build_agricultural_regions()
        
    def _build_ice_matrix(self):
        """ICE enforcement monitoring sources"""
        return {
            'official_ice': [
                {'name': 'ICE_News_Releases', 'url': 'https://www.ice.gov/news/releases', 'type': 'scrape', 'priority': 1},
                {'name': 'DHS_Immigration', 'url': 'https://www.dhs.gov/news-releases', 'type': 'scrape', 'priority': 1},
                {'name': 'CBP_Agriculture', 'url': 'https://www.cbp.gov/newsroom', 'type': 'scrape', 'priority': 2}
            ],
            
            'agricultural_labor': [
                {'name': 'Farm_Labor_Organizing', 'url': 'https://www.farmlabororganizing.org/', 'type': 'scrape', 'priority': 1},
                {'name': 'United_Farm_Workers', 'url': 'https://ufw.org/', 'type': 'scrape', 'priority': 1},
                {'name': 'Western_Growers', 'url': 'https://www.wga.com/', 'type': 'scrape', 'priority': 1},
                {'name': 'American_Farm_Bureau', 'url': 'https://www.fb.org/newsroom/', 'type': 'rss', 'priority': 2}
            ],
            
            'immigration_legal': [
                {'name': 'Immigration_Impact', 'url': 'https://immigrationimpact.com/', 'type': 'rss', 'priority': 2},
                {'name': 'Migration_Policy_Institute', 'url': 'https://www.migrationpolicy.org/', 'type': 'scrape', 'priority': 2},
                {'name': 'SPLC_Immigration', 'url': 'https://www.splcenter.org/issues/immigrant-justice', 'type': 'scrape', 'priority': 2}
            ],
            
            'regional_agricultural_news': [
                {'name': 'California_Farm_Bureau', 'url': 'https://www.cfbf.com/news/', 'type': 'rss', 'priority': 1},
                {'name': 'Texas_Agriculture', 'url': 'https://www.texasagriculture.gov/', 'type': 'scrape', 'priority': 1},
                {'name': 'Florida_Agriculture', 'url': 'https://www.fdacs.gov/', 'type': 'scrape', 'priority': 2},
                {'name': 'Georgia_Farm_Bureau', 'url': 'https://www.gfb.org/', 'type': 'rss', 'priority': 2}
            ]
        }
    
    def _build_trump_matrix(self):
        """Trump Effect monitoring sources"""
        return {
            'trump_direct': [
                {'name': 'Truth_Social_Trump', 'url': 'https://truthsocial.com/@realDonaldTrump', 'type': 'scrape', 'priority': 1},
                {'name': 'Trump_Campaign', 'url': 'https://www.donaldjtrump.com/news', 'type': 'scrape', 'priority': 1},
                {'name': 'Save_America_PAC', 'url': 'https://www.winred.com/save-america-joint-fundraising-committee/', 'type': 'scrape', 'priority': 2}
            ],
            
            'trump_policy_analysis': [
                {'name': 'Heritage_Foundation', 'url': 'https://www.heritage.org/agriculture', 'type': 'scrape', 'priority': 1},
                {'name': 'America_First_Policy', 'url': 'https://americafirstpolicy.com/', 'type': 'scrape', 'priority': 1},
                {'name': 'Tax_Foundation_Trade', 'url': 'https://taxfoundation.org/research/all/federal/trade/', 'type': 'rss', 'priority': 1},
                {'name': 'AEI_Trade_Policy', 'url': 'https://www.aei.org/tag/trade-policy/', 'type': 'rss', 'priority': 2}
            ],
            
            'trump_agriculture_impact': [
                {'name': 'Farm_Policy_News', 'url': 'https://www.farmpolicynews.org/', 'type': 'rss', 'priority': 1},
                {'name': 'Agri_Pulse_Policy', 'url': 'https://www.agri-pulse.com/articles/', 'type': 'rss', 'priority': 1},
                {'name': 'DTN_Policy', 'url': 'https://www.dtnpf.com/agriculture/web/ag/news/', 'type': 'scrape', 'priority': 1},
                {'name': 'Successful_Farming_Policy', 'url': 'https://www.agriculture.com/news/policy', 'type': 'rss', 'priority': 2}
            ],
            
            'trump_trade_war': [
                {'name': 'PIIE_Trade_War', 'url': 'https://www.piie.com/research/piie-charts/us-china-trade-war-tariffs-date-chart', 'type': 'scrape', 'priority': 1},
                {'name': 'Trade_War_Monitor', 'url': 'https://www.csis.org/programs/scholl-chair-international-business/trade-war-monitor', 'type': 'scrape', 'priority': 1},
                {'name': 'US_China_Business', 'url': 'https://www.uschina.org/', 'type': 'scrape', 'priority': 2}
            ]
        }
    
    def _build_agricultural_regions(self):
        """Key agricultural regions affected by ICE enforcement"""
        return {
            'california': {
                'crops': ['almonds', 'grapes', 'vegetables', 'fruits'],
                'labor_intensity': 'high',
                'ice_vulnerability': 'high',
                'soybean_relevance': 'low'
            },
            'texas': {
                'crops': ['cotton', 'corn', 'soybeans', 'sorghum'], 
                'labor_intensity': 'medium',
                'ice_vulnerability': 'high',
                'soybean_relevance': 'medium'
            },
            'midwest': {
                'crops': ['corn', 'soybeans', 'wheat'],
                'labor_intensity': 'low',
                'ice_vulnerability': 'low',
                'soybean_relevance': 'high'
            },
            'southeast': {
                'crops': ['soybeans', 'cotton', 'peanuts'],
                'labor_intensity': 'medium', 
                'ice_vulnerability': 'medium',
                'soybean_relevance': 'high'
            }
        }
    
    def monitor_ice_enforcement(self):
        """
        Monitor ICE enforcement actions affecting agricultural labor
        """
        print("Monitoring ICE agricultural enforcement...")
        
        ice_intel = []
        
        for source_category, sources in self.ice_sources.items():
            for source in sources:
                try:
                    headers = {'User-Agent': 'CBI-V14 Agricultural Research Intelligence'}
                    response = requests.get(source['url'], headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for agricultural-related enforcement news
                        articles = soup.find_all(['h1', 'h2', 'h3', 'h4', 'p'], limit=50)
                        
                        for article in articles:
                            text = article.get_text().lower()
                            
                            # Check for agricultural labor keywords
                            agricultural_keywords = ['farm', 'agriculture', 'crop', 'harvest', 'planting', 
                                                   'seasonal worker', 'agricultural employer', 'food processing']
                            
                            if any(keyword in text for keyword in agricultural_keywords):
                                # Check for enforcement keywords
                                enforcement_keywords = ['raid', 'arrest', 'enforcement', 'deportation', 
                                                      'investigation', 'violation', 'penalty']
                                
                                if any(keyword in text for keyword in enforcement_keywords):
                                    ice_intel.append({
                                        'source': source['name'],
                                        'category': source_category,
                                        'text': article.get_text()[:500],  # First 500 chars
                                        'agricultural_impact': self._assess_agricultural_impact(text),
                                        'regional_focus': self._identify_region(text),
                                        'soybean_relevance': self._assess_soybean_relevance(text),
                                        'timestamp': datetime.now(),
                                        'priority': source['priority']
                                    })
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    print(f"ICE monitoring failed for {source['name']}: {e}")
        
        return ice_intel
    
    def monitor_trump_agricultural_effects(self):
        """
        Monitor Trump policy announcements and effects on agriculture
        """
        print("Monitoring Trump Effect on agriculture...")
        
        trump_intel = []
        
        for source_category, sources in self.trump_sources.items():
            for source in sources:
                try:
                    headers = {'User-Agent': 'CBI-V14 Policy Research Intelligence'}
                    response = requests.get(source['url'], headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for agricultural/trade policy content
                        articles = soup.find_all(['h1', 'h2', 'h3', 'p'], limit=30)
                        
                        for article in articles:
                            text = article.get_text().lower()
                            
                            # Trump agricultural policy keywords
                            trump_ag_keywords = ['tariff', 'trade deal', 'china', 'agriculture', 'farm', 
                                               'ethanol', 'biodiesel', 'RFS', 'renewable fuel', 'USMCA',
                                               'immigration', 'H-2A', 'farm bill', 'subsidy', 'export']
                            
                            if any(keyword in text for keyword in trump_ag_keywords):
                                trump_intel.append({
                                    'source': source['name'],
                                    'category': source_category,
                                    'text': article.get_text()[:500],
                                    'policy_impact': self._assess_policy_impact(text),
                                    'commodity_relevance': self._assess_commodity_relevance(text),
                                    'market_direction': self._predict_market_impact(text),
                                    'timestamp': datetime.now(),
                                    'priority': source['priority']
                                })
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    print(f"Trump monitoring failed for {source['name']}: {e}")
        
        return trump_intel
    
    def _assess_agricultural_impact(self, text):
        """Assess how ICE enforcement affects agricultural production"""
        impact_score = 0.0
        
        # High impact indicators
        high_impact = ['raid', 'mass deportation', 'workplace enforcement', 'labor shortage']
        medium_impact = ['investigation', 'audit', 'compliance check']
        
        for keyword in high_impact:
            if keyword in text:
                impact_score += 0.8
        
        for keyword in medium_impact:
            if keyword in text:
                impact_score += 0.4
        
        return min(impact_score, 1.0)
    
    def _identify_region(self, text):
        """Identify which agricultural region is affected"""
        regions = {
            'california': ['california', 'ca', 'central valley', 'salinas'],
            'texas': ['texas', 'tx', 'rio grande valley'],
            'florida': ['florida', 'fl', 'everglades', 'homestead'], 
            'georgia': ['georgia', 'ga', 'vidalia'],
            'midwest': ['iowa', 'illinois', 'indiana', 'ohio', 'michigan'],
            'southeast': ['north carolina', 'south carolina', 'alabama', 'tennessee']
        }
        
        for region, identifiers in regions.items():
            if any(identifier in text for identifier in identifiers):
                return region
        
        return 'unknown'
    
    def _assess_soybean_relevance(self, text):
        """Assess how ICE enforcement affects soybean production specifically"""
        soybean_keywords = ['soybean', 'soy', 'oilseed', 'commodity crop', 'grain']
        processing_keywords = ['processing', 'crushing', 'oil mill', 'elevator', 'export']
        
        relevance = 0.0
        
        # Direct soybean mentions
        for keyword in soybean_keywords:
            if keyword in text:
                relevance += 0.6
        
        # Processing/handling impact
        for keyword in processing_keywords:
            if keyword in text:
                relevance += 0.3
        
        # Regional relevance (Midwest soybean production)
        region = self._identify_region(text)
        if region in ['midwest', 'southeast']:
            relevance += 0.4
        
        return min(relevance, 1.0)
    
    def _assess_policy_impact(self, text):
        """Assess impact level of Trump policy announcements"""
        impact_score = 0.0
        
        # High impact policy areas
        high_impact = ['tariff increase', 'trade war', 'china deal', 'immigration crackdown', 'deportation']
        medium_impact = ['renegotiate', 'review', 'consider', 'study', 'evaluate']
        
        for keyword in high_impact:
            if keyword in text:
                impact_score += 0.8
                
        for keyword in medium_impact:
            if keyword in text:
                impact_score += 0.4
        
        return min(impact_score, 1.0)
    
    def _assess_commodity_relevance(self, text):
        """Assess Trump policy relevance to commodity markets"""
        commodity_keywords = ['soybean', 'corn', 'agriculture', 'farm', 'trade', 'export', 'tariff']
        china_keywords = ['china', 'beijing', 'xi jinping', 'trade deal', 'phase one']
        
        relevance = 0.0
        
        for keyword in commodity_keywords:
            if keyword in text:
                relevance += 0.3
                
        for keyword in china_keywords:
            if keyword in text:
                relevance += 0.5  # China trade is critical for soybeans
        
        return min(relevance, 1.0)
    
    def _predict_market_impact(self, text):
        """Predict bullish/bearish market impact of Trump policies"""
        bullish_indicators = ['china deal', 'trade agreement', 'export increase', 'tariff removal']
        bearish_indicators = ['tariff increase', 'trade war', 'export ban', 'retaliation']
        
        bullish_score = sum(1 for keyword in bullish_indicators if keyword in text)
        bearish_score = sum(1 for keyword in bearish_indicators if keyword in text)
        
        if bullish_score > bearish_score:
            return 'bullish'
        elif bearish_score > bullish_score:
            return 'bearish'
        else:
            return 'neutral'
    
    def hunt_ice_trump_correlations(self):
        """
        Hunt for correlations between ICE enforcement, Trump policies, and commodity prices
        """
        print("Hunting ICE/Trump correlation patterns...")
        
        # Get current price data
        query = f"""
        SELECT date, value as zl_price
        FROM `{PROJECT_ID}.{DATASET_ID}.soy_oil_features`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 180 DAY)
        ORDER BY date
        """
        
        try:
            price_df = self.client.query(query).to_dataframe()
            
            if len(price_df) < 10:
                print("Insufficient price data for correlation analysis")
                return {}
            
            # Collect recent ICE and Trump intelligence
            ice_data = self.monitor_ice_enforcement()
            trump_data = self.monitor_trump_agricultural_effects()
            
            # Analyze patterns
            correlations = {}
            
            if ice_data:
                # ICE enforcement correlation analysis
                ice_df = pd.DataFrame(ice_data)
                daily_ice_impact = ice_df.groupby(
                    ice_df['timestamp'].dt.date
                ).agg({
                    'agricultural_impact': 'mean',
                    'soybean_relevance': 'mean'
                }).reset_index()
                
                # Merge with prices and calculate correlation
                if len(daily_ice_impact) > 3:
                    merged = pd.merge(daily_ice_impact, price_df.assign(date=price_df['date'].dt.date), 
                                    on='date', how='inner')
                    
                    if len(merged) > 2:
                        corr = merged['agricultural_impact'].corr(merged['zl_price'])
                        correlations['ice_enforcement_price'] = {
                            'correlation': corr,
                            'data_points': len(merged),
                            'hunt_value': 'HIGH' if abs(corr) > 0.3 else 'MEDIUM',
                            'hypothesis': 'ICE enforcement → labor shortage → production cost increase → price impact'
                        }
            
            if trump_data:
                # Trump policy correlation analysis  
                trump_df = pd.DataFrame(trump_data)
                daily_trump_impact = trump_df.groupby(
                    trump_df['timestamp'].dt.date
                ).agg({
                    'policy_impact': 'mean',
                    'commodity_relevance': 'mean'
                }).reset_index()
                
                if len(daily_trump_impact) > 3:
                    merged = pd.merge(daily_trump_impact, price_df.assign(date=price_df['date'].dt.date),
                                    on='date', how='inner')
                    
                    if len(merged) > 2:
                        corr = merged['policy_impact'].corr(merged['zl_price'])
                        correlations['trump_policy_price'] = {
                            'correlation': corr,
                            'data_points': len(merged),
                            'hunt_value': 'HIGH' if abs(corr) > 0.3 else 'MEDIUM',
                            'hypothesis': 'Trump policy announcements → trade volatility → commodity price swings'
                        }
            
            return correlations
            
        except Exception as e:
            print(f"ICE/Trump correlation analysis failed: {e}")
            return {}
    
    def continuous_ice_trump_monitoring(self):
        """
        Run continuous monitoring of ICE and Trump effects
        Critical for early warning of labor and trade disruptions
        """
        print("Starting continuous ICE/Trump agricultural monitoring...")
        
        while True:
            try:
                print(f"\n=== ICE/TRUMP INTELLIGENCE CYCLE: {datetime.now()} ===")
                
                # Collect ICE enforcement data
                ice_data = self.monitor_ice_enforcement()
                print(f"ICE enforcement alerts: {len(ice_data)}")
                
                # Collect Trump policy data
                trump_data = self.monitor_trump_agricultural_effects()
                print(f"Trump policy developments: {len(trump_data)}")
                
                # Hunt for correlations
                correlations = self.hunt_ice_trump_correlations()
                print(f"Correlation patterns found: {len(correlations)}")
                
                # Alert on high-impact discoveries
                for correlation_type, data in correlations.items():
                    if data['hunt_value'] == 'HIGH':
                        print(f"HIGH IMPACT CORRELATION: {correlation_type}")
                        print(f"  {data['hypothesis']}")
                        print(f"  Correlation: {data['correlation']:.3f}")
                
                # Save intelligence to BigQuery
                self._save_ice_trump_intel(ice_data + trump_data)
                
                # Sleep for 30 minutes (faster cycle for political developments)
                print("Next ICE/Trump monitoring cycle in 30 minutes...")
                time.sleep(1800)
                
            except Exception as e:
                print(f"ICE/Trump monitoring cycle failed: {e}")
                time.sleep(300)  # 5 minute pause before retry
    
    def _save_ice_trump_intel(self, intel_data):
        """Save ICE and Trump intelligence to BigQuery"""
        if not intel_data:
            return
        
        try:
            df = pd.DataFrame(intel_data)
            
            # Ensure table exists
            schema = [
                bigquery.SchemaField("source", "STRING"),
                bigquery.SchemaField("category", "STRING"),
                bigquery.SchemaField("text", "STRING"),
                bigquery.SchemaField("agricultural_impact", "FLOAT"),
                bigquery.SchemaField("soybean_relevance", "FLOAT"),
                bigquery.SchemaField("timestamp", "TIMESTAMP"),
                bigquery.SchemaField("priority", "INT64"),
            ]
            
            table_ref = f"{PROJECT_ID}.{DATASET_ID}.ice_trump_intelligence"
            
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                schema=schema
            )
            
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()
            
            print(f"Saved {len(df)} ICE/Trump intelligence records to BigQuery")
            
        except Exception as e:
            print(f"ICE/Trump intelligence save failed: {e}")

def main():
    """Execute ICE and Trump agricultural intelligence monitoring"""
    ice_trump = ICETrumpIntelligence()
    
    print("=== ICE & TRUMP AGRICULTURAL INTELLIGENCE ===")
    print("Monitoring immigration enforcement and political policy impacts")
    print("=" * 60)
    
    # Single monitoring cycle
    ice_data = ice_trump.monitor_ice_enforcement()
    trump_data = ice_trump.monitor_trump_agricultural_effects()
    
    print(f"ICE enforcement intelligence: {len(ice_data)} items")
    print(f"Trump policy intelligence: {len(trump_data)} items")
    
    # Hunt for correlations
    correlations = ice_trump.hunt_ice_trump_correlations()
    
    if correlations:
        print(f"\nCORRELATION DISCOVERIES:")
        for correlation_type, data in correlations.items():
            print(f"  {correlation_type}: {data['correlation']:.3f} correlation")
            print(f"    {data['hypothesis']}")
    
    # Uncomment to start continuous monitoring
    # ice_trump.continuous_ice_trump_monitoring()

if __name__ == "__main__":
    main()
