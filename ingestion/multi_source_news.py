from bigquery_utils import safe_load_to_bigquery
#!/usr/bin/env python3
"""
Multi-Source News Intelligence System
Monitors 50+ sources across 16 categories for soybean oil intelligence
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import feedparser
import time
from datetime import datetime
from google.cloud import bigquery
import json

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"
NEWS_TABLE = "news_intelligence"

class MultiSourceNewsIntel:
    """
    Comprehensive news monitoring across multiple sources and categories
    Designed to get information before competitors
    """
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.sources = self._build_source_matrix()
        self.keywords = self._build_keyword_matrix()
        
    def _build_source_matrix(self):
        """
        Comprehensive matrix of news sources across 16 categories
        Multiple sources per category for redundancy
        """
        return {
            'china_demand': [
                {'name': 'Xinhua_Agriculture', 'url': 'http://www.news.cn/english/', 'type': 'rss'},
                {'name': 'China_Daily_Business', 'url': 'https://www.chinadaily.com.cn/business', 'type': 'scrape'},
                {'name': 'COFCO_News', 'url': 'https://www.cofcointernational.com/en/media/', 'type': 'scrape'},
                {'name': 'AgriMoney_China', 'url': 'https://www.agrimoney.com/news/china/', 'type': 'rss'}
            ],
            
            'brazil_policy': [
                {'name': 'CONAB_Official', 'url': 'https://www.conab.gov.br/ultimas-noticias', 'type': 'scrape'},
                {'name': 'ABIOVE_Stats', 'url': 'https://abiove.org.br/en/statistics/', 'type': 'scrape'},
                {'name': 'Reuters_Brasil', 'url': 'https://www.reuters.com/world/americas/', 'type': 'rss'},
                {'name': 'Globo_Rural', 'url': 'https://g1.globo.com/economia/agronegocios/', 'type': 'scrape'}
            ],
            
            'argentina_policy': [
                {'name': 'Buenos_Aires_Herald', 'url': 'https://buenosairesherald.com/business', 'type': 'rss'},
                {'name': 'CIARA_CEC', 'url': 'https://www.ciaracec.com.ar/', 'type': 'scrape'},
                {'name': 'BCR_Agriculture', 'url': 'https://www.bcr.com.ar/', 'type': 'scrape'},
                {'name': 'Rosario_Board', 'url': 'http://www.bcr.com.ar/', 'type': 'scrape'}
            ],
            
            'us_policy': [
                {'name': 'USDA_News', 'url': 'https://www.usda.gov/media/press-releases', 'type': 'rss'},
                {'name': 'Farm_Progress', 'url': 'https://www.farmprogress.com/', 'type': 'rss'},
                {'name': 'AgWeb_Policy', 'url': 'https://www.agweb.com/news/policy', 'type': 'rss'},
                {'name': 'USTR_Trade', 'url': 'https://ustr.gov/about-us/press-office', 'type': 'scrape'}
            ],
            
            'ice_labor_enforcement': [
                {'name': 'ICE_News', 'url': 'https://www.ice.gov/news', 'type': 'scrape'},
                {'name': 'DHS_Immigration', 'url': 'https://www.dhs.gov/news-releases', 'type': 'scrape'},
                {'name': 'Farm_Labor_News', 'url': 'https://www.farmlabororganizing.org/', 'type': 'scrape'},
                {'name': 'AgDaily_Labor', 'url': 'https://www.agdaily.com/insights/farm-labor/', 'type': 'rss'},
                {'name': 'Western_Growers', 'url': 'https://www.wga.com/', 'type': 'scrape'}
            ],
            
            'trump_effect_agricultural': [
                {'name': 'Trump_Truth_Social', 'url': 'https://truthsocial.com/@realDonaldTrump', 'type': 'scrape'},
                {'name': 'GOP_Agriculture', 'url': 'https://gop.com/issues/agriculture/', 'type': 'scrape'},
                {'name': 'Farm_Bureau_Policy', 'url': 'https://www.fb.org/newsroom/', 'type': 'rss'},
                {'name': 'Politico_Agriculture', 'url': 'https://www.politico.com/agriculture', 'type': 'rss'},
                {'name': 'Roll_Call_Agriculture', 'url': 'https://rollcall.com/news/congress/', 'type': 'scrape'},
                {'name': 'Washington_Examiner_Trade', 'url': 'https://www.washingtonexaminer.com/policy/economy/', 'type': 'rss'}
            ],
            
            'biofuel_policy': [
                {'name': 'EPA_RFS', 'url': 'https://www.epa.gov/renewable-fuel-standard-program', 'type': 'scrape'},
                {'name': 'Biofuels_Digest', 'url': 'https://www.biofuelsdigest.com/', 'type': 'rss'},
                {'name': 'Biodiesel_Magazine', 'url': 'https://biodieselmagazine.com/', 'type': 'rss'},
                {'name': 'RenovaBio_Brasil', 'url': 'https://www.anp.gov.br/', 'type': 'scrape'}
            ],
            
            'palm_oil_geopolitics': [
                {'name': 'MPOB_Malaysia', 'url': 'http://bepi.mpob.gov.my/', 'type': 'scrape'},
                {'name': 'Indonesia_Ministry', 'url': 'https://www.kemenko.go.id/', 'type': 'scrape'},
                {'name': 'Palm_Oil_HQ', 'url': 'https://palmoilhq.com/', 'type': 'rss'},
                {'name': 'Agrimoney_Palm', 'url': 'https://www.agrimoney.com/news/palm-oil/', 'type': 'rss'}
            ],
            
            'shipping_logistics': [
                {'name': 'TradeWinds', 'url': 'https://www.tradewindsnews.com/', 'type': 'rss'},
                {'name': 'Lloyd_List', 'url': 'https://lloydslist.maritimeintelligence.informa.com/', 'type': 'scrape'},
                {'name': 'Panama_Canal', 'url': 'https://www.pancanal.com/', 'type': 'scrape'},
                {'name': 'Baltic_Exchange', 'url': 'https://www.balticexchange.com/', 'type': 'scrape'}
            ],
            
            'weather_agriculture': [
                {'name': 'Weather_Underground_Agriculture', 'url': 'https://www.wunderground.com/agriculture', 'type': 'api'},
                {'name': 'NOAA_Climate', 'url': 'https://www.climate.gov/', 'type': 'scrape'},
                {'name': 'DTN_Progressive', 'url': 'https://www.dtnpf.com/', 'type': 'scrape'},
                {'name': 'Weather_Central', 'url': 'https://www.weathercentral.com/', 'type': 'api'}
            ]
        }
    
    def _build_keyword_matrix(self):
        """
        Advanced keyword matrix for intelligent source filtering
        Based on the 16-category framework
        """
        return {
            'china_demand': ['Sinograin', 'COFCO', 'NDRC', 'state reserves', 'soybean import', 'crush margin', 'Dalian'],
            'brazil_policy': ['CONAB', 'MAPA', 'Santos port', 'Arco Norte', 'Ferrogrão', 'Ibama', 'embargo', 'export tax'],
            'argentina_policy': ['sojadólar', 'retenciones', 'Rosario', 'export tax', 'CIARA-CEC', 'peso', 'IMF'],
            'us_policy': ['USTR', 'RFS', 'renewable fuel', 'export credit', 'Farm Bill', 'USDA', 'tariff'],
            'biofuel_policy': ['B40', 'biodiesel', 'RenovaBio', 'LCFS', 'SAF', 'EPA', 'RVO', 'renewable diesel'],
            'palm_oil': ['CPO', 'export levy', 'DMO', 'MPOB', 'Malaysia', 'Indonesia', 'palm oil'],
            'weather': ['drought', 'precipitation', 'La Niña', 'El Niño', 'crop condition', 'harvest', 'planting'],
            'trade_war': ['tariff', 'trade war', 'WTO', 'antidumping', 'Phase One', 'retaliation'],
            'shipping': ['Panama Canal', 'Suez', 'freight', 'vessel', 'port strike', 'logistics', 'container'],
            'energy': ['natural gas', 'crude oil', 'fertilizer', 'diesel', 'energy cost', 'refining'],
            'macro_fx': ['USD index', 'dollar', 'BRL', 'ARS', 'CNY', 'interest rate', 'inflation', 'Fed'],
            'crop_disease': ['ASF', 'African swine fever', 'hog herd', 'livestock', 'animal disease'],
            'regulation': ['EUDR', 'deforestation', 'traceability', 'ESG', 'sustainability', 'certification'],
            'labor_unrest': ['strike', 'protest', 'blockade', 'union', 'port worker', 'trucker'],
            'technology': ['precision agriculture', 'satellite', 'NDVI', 'crop monitoring', 'AI farming'],
            'financial_flows': ['hedge fund', 'commodity fund', 'ETF', 'index fund', 'positioning', 'COT'],
            
            # NEW CRITICAL CATEGORIES
            'ice_labor_enforcement': [
                'ICE raids', 'immigration enforcement', 'farm labor shortage', 'H-2A visa', 'agricultural workers',
                'deportation', 'labor disruption', 'seasonal workers', 'undocumented workers', 'farm raids',
                'labor costs', 'worker shortage', 'harvest labor', 'planting crews', 'agricultural immigration'
            ],
            
            'trump_effect_agricultural': [
                'Trump tariff', 'Truth Social agriculture', 'MAGA policy', 'America First agriculture',
                'China trade deal', 'USMCA', 'immigration crackdown', 'border policy', 'farm policy',
                'renewable fuel rollback', 'EPA deregulation', 'agriculture secretary', 'farm subsidy',
                'trade negotiation', 'presidential agriculture', 'campaign agriculture', 'rural vote'
            ]
        }
    
    def monitor_all_sources(self):
        """
        Monitor all sources simultaneously for real-time intelligence
        """
        print(f"Starting comprehensive news monitoring: {datetime.now()}")
        
        all_articles = []
        
        for category, sources in self.sources.items():
            print(f"Monitoring {category}: {len(sources)} sources")
            
            for source in sources:
                try:
                    articles = self._extract_from_source(source, category)
                    all_articles.extend(articles)
                    
                    # Rate limiting - be respectful
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Failed to extract from {source['name']}: {e}")
                    # Continue with other sources - redundancy is key
        
        # Process and score all articles
        scored_articles = self._score_articles(all_articles)
        
        # Load to BigQuery
        if scored_articles:
            self._load_news_intelligence(scored_articles)
            print(f"Loaded {len(scored_articles)} intelligence items")
        
        return scored_articles
    
    def _extract_from_source(self, source, category):
        """Extract articles from a single source"""
        articles = []
        
        try:
            if source['type'] == 'rss':
                feed = feedparser.parse(source['url'])
                for entry in feed.entries[:10]:  # Latest 10 articles
                    articles.append({
                        'title': entry.title,
                        'source': source['name'],
                        'category': category,
                        'url': entry.link,
                        'published': entry.get('published', datetime.now()),
                        'content': entry.get('description', '')
                    })
                    
            elif source['type'] == 'scrape':
                # Web scraping with error handling
                headers = {'User-Agent': 'CBI-V14 Intelligence (research purposes)'}
                response = requests.get(source['url'], headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Generic article extraction
                    titles = soup.find_all(['h1', 'h2', 'h3'], limit=20)
                    for title in titles:
                        if any(keyword.lower() in title.text.lower() 
                               for keyword in self.keywords[category]):
                            articles.append({
                                'title': title.text.strip(),
                                'source': source['name'],
                                'category': category,
                                'url': source['url'],
                                'published': datetime.now(),
                                'content': title.text.strip()
                            })
                            
        except Exception as e:
            print(f"Extraction error from {source['name']}: {e}")
            
        return articles
    
    def _score_articles(self, articles):
        """
        Score articles for relevance and potential market impact
        """
        scored = []
        
        for article in articles:
            score = 0.0
            
            # Keyword density scoring
            title_lower = article['title'].lower()
            content_lower = article['content'].lower()
            
            category_keywords = self.keywords.get(article['category'], [])
            keyword_hits = sum(1 for kw in category_keywords 
                             if kw.lower() in title_lower or kw.lower() in content_lower)
            
            score += (keyword_hits / max(len(category_keywords), 1)) * 0.4
            
            # Source quality bonus
            if 'official' in article['source'].lower() or 'government' in article['source'].lower():
                score += 0.3
            elif 'reuters' in article['source'].lower() or 'bloomberg' in article['source'].lower():
                score += 0.2
                
            # Recency bonus
            try:
                pub_time = datetime.strptime(str(article['published'])[:19], '%Y-%m-%d %H:%M:%S')
                hours_old = (datetime.now() - pub_time).total_seconds() / 3600
                if hours_old < 4:  # Very recent
                    score += 0.2
                elif hours_old < 24:  # Recent
                    score += 0.1
            except:
                pass
            
            if score > 0.2:  # Minimum relevance threshold
                article['intelligence_score'] = score
                scored.append(article)
        
        return sorted(scored, key=lambda x: x['intelligence_score'], reverse=True)
    
    def _load_news_intelligence(self, articles):
        """Load scored articles into BigQuery for neural network analysis"""
        if not articles:
            return
            
        df = pd.DataFrame(articles)
        df['processed_timestamp'] = datetime.now()
        
        # Ensure table exists
        self._ensure_news_table()
        
        # Load to BigQuery
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        job = safe_load_to_bigquery(self.client, df, f"{PROJECT_ID}.{DATASET_ID}.{NEWS_TABLE}", job_config)
        job.result()
    
    def _ensure_news_table(self):
        """Create news intelligence table if it doesn't exist"""
        schema = [
            bigquery.SchemaField("title", "STRING"),
            bigquery.SchemaField("source", "STRING"),
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("url", "STRING"),
            bigquery.SchemaField("published", "STRING"),
            bigquery.SchemaField("content", "STRING"),
            bigquery.SchemaField("intelligence_score", "FLOAT"),
            bigquery.SchemaField("processed_timestamp", "TIMESTAMP"),
        ]
        
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{NEWS_TABLE}"
        try:
            self.client.get_table(table_ref)
        except:
            table = bigquery.Table(table_ref, schema=schema)
            self.client.create_table(table)
            print(f"Created news intelligence table: {NEWS_TABLE}")

def main():
    """Run comprehensive news monitoring"""
    intel = MultiSourceNewsIntel()
    
    print("Starting comprehensive news intelligence monitoring...")
    
    # Single monitoring cycle
    articles = intel.monitor_all_sources()
    
    print(f"\nIntelligence Summary:")
    print(f"Total articles: {len(articles)}")
    
    # Show top intelligence by category
    categories = {}
    for article in articles:
        cat = article['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(article)
    
    for category, cat_articles in categories.items():
        best = max(cat_articles, key=lambda x: x['intelligence_score'])
        print(f"{category}: {best['title'][:80]}... (score: {best['intelligence_score']:.2f})")

if __name__ == "__main__":
    main()
