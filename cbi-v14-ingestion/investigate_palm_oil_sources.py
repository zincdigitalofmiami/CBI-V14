#!/usr/bin/env python3
"""
CBI-V14 Palm Oil Data Source Investigation
48-Hour Timeline: Resolve 15-25% variance gap in soybean oil modeling
"""

import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging
import time
from typing import Dict, List, Any, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PalmOilSourceInvestigator:
    """Investigate alternative palm oil data sources for CBI-V14"""
    
    def __init__(self):
        self.results = {
            'investigation_timestamp': datetime.now().isoformat(),
            'sources_tested': [],
            'viable_sources': [],
            'recommendations': []
        }
    
    def test_bursa_malaysia_options(self) -> Dict[str, Any]:
        """Test Bursa Malaysia data access options"""
        logger.info("🇲🇾 Testing Bursa Malaysia data sources...")
        
        bursa_results = {
            'source': 'Bursa Malaysia',
            'status': 'unknown',
            'endpoints_tested': [],
            'data_available': False,
            'subscription_required': 'unknown'
        }
        
        # Test potential Bursa Malaysia endpoints
        potential_endpoints = [
            'https://api.bursamalaysia.com/market-data/v1',  # Hypothetical
            'https://www.bursamalaysia.com/api',  # Alternative
            'https://api.bursa.com.my',  # Possible variation
        ]
        
        for endpoint in potential_endpoints:
            try:
                logger.info(f"Testing: {endpoint}")
                
                # Test with basic request
                response = requests.get(endpoint, timeout=10)
                
                bursa_results['endpoints_tested'].append({
                    'url': endpoint,
                    'status_code': response.status_code,
                    'response_headers': dict(response.headers),
                    'requires_auth': 'authorization' in response.text.lower()
                })
                
                if response.status_code == 200:
                    logger.info(f"✅ {endpoint}: Accessible")
                    bursa_results['data_available'] = True
                elif response.status_code == 401:
                    logger.info(f"🔐 {endpoint}: Requires authentication")
                    bursa_results['subscription_required'] = True
                else:
                    logger.info(f"❌ {endpoint}: Status {response.status_code}")
                
                time.sleep(1)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"❌ {endpoint}: {str(e)}")
                bursa_results['endpoints_tested'].append({
                    'url': endpoint,
                    'error': str(e)
                })
        
        self.results['sources_tested'].append(bursa_results)
        return bursa_results
    
    def test_alternative_yahoo_symbols(self) -> Dict[str, Any]:
        """Test additional Yahoo Finance palm oil related symbols"""
        logger.info("🔍 Testing alternative Yahoo Finance palm oil symbols...")
        
        yahoo_results = {
            'source': 'Yahoo Finance Alternatives',
            'status': 'testing',
            'symbols_tested': [],
            'viable_symbols': []
        }
        
        # Extended list of potential palm oil related symbols
        test_symbols = [
            # Malaysian palm oil companies
            'IOICORP.KL',  # IOI Corporation
            'SIMEDARBY.KL',  # Sime Darby Plantation
            'GENTING.KL',  # Genting Plantations
            'HAPSENG.KL',  # Hap Seng Plantations
            '5066.KL',  # Sarawak Oil Palms
            
            # Indonesian palm oil
            'AALI.JK',  # Astra Agro Lestari
            'LSIP.JK',  # London Sumatra Indonesia
            
            # Alternative commodity symbols
            'PKO',  # Palm kernel oil
            'PALM',  # Generic palm
            'RBD',  # Refined bleached deodorized palm oil
            
            # ETFs/Funds with palm oil exposure
            'DBA',  # Invesco DB Agriculture Fund
            'CORN',  # Teucrium Corn Fund (may track palm correlations)
        ]
        
        for symbol in test_symbols:
            try:
                logger.info(f"Testing symbol: {symbol}")
                ticker = yf.Ticker(symbol)
                
                # Get basic info
                info = ticker.info
                history = ticker.history(period='5d')
                
                symbol_data = {
                    'symbol': symbol,
                    'name': info.get('shortName', 'Unknown'),
                    'sector': info.get('sector', 'Unknown'),
                    'country': info.get('country', 'Unknown'),
                    'currency': info.get('currency', 'Unknown'),
                    'has_recent_data': not history.empty,
                    'latest_date': str(history.index.max().date()) if not history.empty else None,
                    'latest_price': float(history['Close'].iloc[-1]) if not history.empty else None,
                    'records_available': len(history)
                }
                
                yahoo_results['symbols_tested'].append(symbol_data)
                
                # Check if this could be a viable palm oil proxy
                if not history.empty and (
                    'palm' in info.get('longName', '').lower() or 
                    'plantation' in info.get('longName', '').lower() or
                    info.get('sector', '') == 'Consumer Defensive'
                ):
                    yahoo_results['viable_symbols'].append(symbol_data)
                    logger.info(f"✅ Viable proxy found: {symbol} - {info.get('shortName', 'Unknown')}")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"❌ {symbol}: {str(e)}")
                yahoo_results['symbols_tested'].append({
                    'symbol': symbol,
                    'error': str(e)
                })
        
        self.results['sources_tested'].append(yahoo_results)
        return yahoo_results
    
    def test_investing_com_scraping(self) -> Dict[str, Any]:
        """Test Investing.com palm oil data availability (last resort)"""
        logger.info("🌐 Testing Investing.com palm oil data...")
        
        investing_results = {
            'source': 'Investing.com',
            'status': 'testing',
            'urls_tested': [],
            'scraping_viable': False
        }
        
        # Test Investing.com palm oil pages
        test_urls = [
            'https://www.investing.com/commodities/crude-palm-oil',
            'https://www.investing.com/commodities/palm-oil-futures',
            'https://www.investing.com/commodities/fcpo-futures'
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for url in test_urls:
            try:
                logger.info(f"Testing: {url}")
                
                response = requests.get(url, headers=headers, timeout=10)
                
                url_data = {
                    'url': url,
                    'status_code': response.status_code,
                    'has_price_data': 'price' in response.text.lower() and 'palm' in response.text.lower(),
                    'cloudflare_protection': 'cloudflare' in response.text.lower(),
                    'content_length': len(response.text)
                }
                
                investing_results['urls_tested'].append(url_data)
                
                if response.status_code == 200 and url_data['has_price_data']:
                    logger.info(f"✅ {url}: Contains palm oil price data")
                    if not url_data['cloudflare_protection']:
                        investing_results['scraping_viable'] = True
                else:
                    logger.info(f"❌ {url}: No usable data or protected")
                
                time.sleep(2)  # Respectful rate limiting
                
            except Exception as e:
                logger.warning(f"❌ {url}: {str(e)}")
                investing_results['urls_tested'].append({
                    'url': url,
                    'error': str(e)
                })
        
        self.results['sources_tested'].append(investing_results)
        return investing_results
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on investigation results"""
        logger.info("📋 Generating palm oil data recommendations...")
        
        recommendations = []
        
        # Analyze viable sources
        viable_count = 0
        for source in self.results['sources_tested']:
            if source.get('data_available') or source.get('viable_symbols') or source.get('scraping_viable'):
                viable_count += 1
        
        if viable_count == 0:
            recommendations.extend([
                "🔴 CRITICAL: No viable palm oil data sources found in free/accessible tier",
                "💰 REQUIRES INVESTMENT: Consider paid subscription to:",
                "   - Bursa Malaysia Market Data Services",
                "   - Refinitiv/Reuters commodity feeds", 
                "   - Bloomberg Terminal access",
                "   - S&P Global Platts palm oil assessments",
                "⏰ TIMELINE IMPACT: May exceed 48-hour resolution window"
            ])
        else:
            recommendations.extend([
                f"✅ Found {viable_count} potential data sources",
                "🚀 NEXT STEPS: Implement highest-quality viable source",
                "⏰ TIMELINE: Resolution possible within 48 hours"
            ])
        
        # Add specific technical recommendations
        recommendations.extend([
            "🔧 TECHNICAL REQUIREMENTS:",
            "   - Real-time or daily palm oil futures prices (FCPO)",
            "   - USD/MYR exchange rate (already available)",
            "   - Palm-soy spread calculations",
            "   - Validation against historical correlations",
            "📊 DATA REQUIREMENTS:",
            f"   - Minimum: 30 days recent data",
            f"   - Optimal: Historical data back to 2020",
            f"   - Frequency: Daily (minimum) to real-time (preferred)",
            f"   - Quality: Institutional-grade validation required"
        ])
        
        self.results['recommendations'] = recommendations
        return recommendations
    
    def run_full_investigation(self) -> Dict[str, Any]:
        """Run complete palm oil data source investigation"""
        print("=" * 80)
        print("PALM OIL DATA SOURCE INVESTIGATION - 48 HOUR TIMELINE")
        print("=" * 80)
        print(f"Started: {datetime.now()}")
        print("Objective: Resolve 15-25% variance gap in soybean oil modeling")
        print()
        
        # Run all investigations
        print("🔍 PHASE 1: INVESTIGATING DATA SOURCES")
        print("-" * 50)
        
        bursa_results = self.test_bursa_malaysia_options()
        yahoo_results = self.test_alternative_yahoo_symbols() 
        investing_results = self.test_investing_com_scraping()
        
        print()
        print("📋 PHASE 2: GENERATING RECOMMENDATIONS") 
        print("-" * 50)
        
        recommendations = self.generate_recommendations()
        
        for rec in recommendations:
            print(rec)
        
        print()
        print("=" * 80)
        print("INVESTIGATION COMPLETE")
        print("=" * 80)
        print(f"Completed: {datetime.now()}")
        
        # Save detailed results
        with open(f"/Users/zincdigital/CBI-V14/logs/palm_oil_investigation_{datetime.now().strftime('%Y%m%d_%H%M')}.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        return self.results

if __name__ == "__main__":
    investigator = PalmOilSourceInvestigator()
    results = investigator.run_full_investigation()
    
    # Exit code based on findings
    viable_sources = len([s for s in results['sources_tested'] if s.get('data_available') or s.get('viable_symbols')])
    exit(0 if viable_sources > 0 else 1)









