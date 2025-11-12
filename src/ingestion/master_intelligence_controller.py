#!/usr/bin/env python3
"""
Master Intelligence Controller - Comprehensive Data Collection System
Coordinates all intelligence sources, identifies correlations, hunts new sources
MISSION: Information superiority in soybean oil markets
"""

import pandas as pd
from google.cloud import bigquery
import numpy as np
import time
from datetime import datetime, timedelta
import json
import concurrent.futures
import threading

# Import our intelligence modules
from intelligence_hunter import IntelligenceHunter
from multi_source_news import MultiSourceNewsIntel
from economic_intelligence import EconomicIntelligence
from social_intelligence import SocialIntelligence
from bigquery_utils import safe_load_to_bigquery

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

class MasterIntelligenceController:
    """
    Central command for all intelligence collection
    Coordinates multi-source data gathering and neural network analysis
    """
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
        # Initialize all intelligence modules
        self.hunter = IntelligenceHunter()
        self.news_intel = MultiSourceNewsIntel()
        self.economic_intel = EconomicIntelligence()
        self.social_intel = SocialIntelligence()
        
        # Intelligence coordination
        self.collection_stats = {}
        self.correlation_discoveries = {}
        self.source_quality_rankings = {}
        
    def run_comprehensive_collection(self):
        """
        Run all intelligence collection simultaneously
        Parallel execution for maximum speed and coverage
        """
        print(f"=== MASTER INTELLIGENCE COLLECTION INITIATED ===")
        print(f"Timestamp: {datetime.now()}")
        print("=" * 60)
        
        collection_results = {}
        
        # Execute all intelligence gathering in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            # Submit all intelligence tasks simultaneously
            futures = {
                'news': executor.submit(self._collect_news_intelligence),
                'economic': executor.submit(self._collect_economic_intelligence),
                'social': executor.submit(self._collect_social_intelligence),
                'correlation_hunt': executor.submit(self._hunt_correlations),
                'source_discovery': executor.submit(self._discover_new_sources)
            }
            
            # Collect results as they complete
            for intelligence_type, future in futures.items():
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per module
                    collection_results[intelligence_type] = result
                    print(f"✓ {intelligence_type}: {len(result) if isinstance(result, list) else 'completed'}")
                except Exception as e:
                    print(f"✗ {intelligence_type}: FAILED - {e}")
                    collection_results[intelligence_type] = []
        
        # Analyze cross-source correlations
        self._analyze_cross_intelligence_correlations(collection_results)
        
        # Update intelligence summary
        self._update_intelligence_summary(collection_results)
        
        return collection_results
    
    def _collect_news_intelligence(self):
        """Collect from all news sources"""
        return self.news_intel.monitor_all_sources()
    
    def _collect_economic_intelligence(self):
        """Collect economic data from multiple sources"""
        econ_data = []
        econ_data.extend(self.economic_intel.collect_fed_intelligence())
        econ_data.extend(self.economic_intel.hunt_currency_intelligence())
        return econ_data
    
    def _collect_social_intelligence(self):
        """Collect social media sentiment"""
        social_data = []
        social_data.extend(self.social_intel.monitor_reddit_agriculture())
        return social_data
    
    def _hunt_correlations(self):
        """Hunt for correlations across all data sources"""
        return self.hunter.analyze_existing_correlations()
    
    def _discover_new_sources(self):
        """Discover new data sources based on correlations"""
        correlations = self.hunter.analyze_existing_correlations()
        new_sources = []
        
        for pattern in correlations:
            discovered = self.hunter.hunt_related_sources(pattern)
            new_sources.extend(discovered)
        
        return new_sources
    
    def _analyze_cross_intelligence_correlations(self, collection_results):
        """
        Analyze correlations between different intelligence types
        Identify which combinations provide strongest predictive power
        """
        print("\n=== CROSS-INTELLIGENCE CORRELATION ANALYSIS ===")
        
        cross_correlations = {}
        
        # Example: News sentiment vs Economic indicators
        if collection_results['news'] and collection_results['economic']:
            try:
                # Calculate correlation between news volume and economic stress
                news_volume = len(collection_results['news'])
                economic_indicators = len(collection_results['economic'])
                
                cross_correlations['news_economic'] = {
                    'correlation_hypothesis': 'High news volume indicates economic stress',
                    'news_volume': news_volume,
                    'economic_data_points': economic_indicators,
                    'hunt_recommendation': 'Monitor news volume spikes for economic signals'
                }
            except Exception as e:
                print(f"News-Economic correlation failed: {e}")
        
        # Social sentiment vs Shipping disruptions
        if collection_results['social'] and collection_results['shipping']:
            try:
                social_sentiment = np.mean([item.get('sentiment_score', 0) 
                                          for item in collection_results['social']])
                shipping_issues = len(collection_results['shipping'])
                
                cross_correlations['social_shipping'] = {
                    'correlation_hypothesis': 'Social stress correlates with logistics disruptions',
                    'avg_sentiment': social_sentiment,
                    'shipping_alerts': shipping_issues,
                    'hunt_recommendation': 'Combine social monitoring with logistics tracking'
                }
            except Exception as e:
                print(f"Social-Shipping correlation failed: {e}")
        
        self.correlation_discoveries = cross_correlations
        
        # Print discoveries
        for correlation_type, data in cross_correlations.items():
            print(f"{correlation_type}: {data['correlation_hypothesis']}")
            print(f"  Recommendation: {data['hunt_recommendation']}")
        
        return cross_correlations
    
    def _update_intelligence_summary(self, collection_results):
        """Update comprehensive intelligence summary"""
        summary = {
            'collection_timestamp': datetime.now(),
            'total_sources_monitored': self._count_total_sources(),
            'data_points_collected': self._count_data_points(collection_results),
            'correlation_discoveries': len(self.correlation_discoveries),
            'intelligence_coverage': self._assess_coverage(collection_results),
            'competitive_advantage_score': self._calculate_advantage_score(collection_results)
        }
        
        print(f"\n=== INTELLIGENCE SUMMARY ===")
        print(f"Sources Monitored: {summary['total_sources_monitored']}")
        print(f"Data Points: {summary['data_points_collected']}")
        print(f"Correlations Found: {summary['correlation_discoveries']}")
        print(f"Coverage Score: {summary['intelligence_coverage']}/100")
        print(f"Competitive Advantage: {summary['competitive_advantage_score']}/100")
        
        return summary
    
    def _count_total_sources(self):
        """Count all sources across all intelligence modules"""
        total = 0
        total += len(self.news_intel.sources.get('china_demand', [])) * len(self.news_intel.sources)
        total += len(self.economic_intel.economic_sources.get('us_federal_reserve', [])) * len(self.economic_intel.economic_sources)
        total += len(self.shipping_intel.shipping_sources.get('panama_canal', [])) * len(self.shipping_intel.shipping_sources)
        total += len(self.social_intel.social_sources.get('reddit_agriculture', [])) * len(self.social_intel.social_sources)
        
        return total
    
    def _count_data_points(self, collection_results):
        """Count total data points collected"""
        total = 0
        for intelligence_type, data in collection_results.items():
            if isinstance(data, list):
                total += len(data)
            elif isinstance(data, dict):
                total += len(data)
        return total
    
    def _assess_coverage(self, collection_results):
        """Assess intelligence coverage completeness (0-100)"""
        coverage_score = 0
        
        # News coverage (16 categories)
        news_categories_covered = len(set(item.get('category', '') 
                                        for item in collection_results.get('news', [])))
        coverage_score += (news_categories_covered / 16) * 25
        
        # Economic coverage 
        economic_sources = len(collection_results.get('economic', []))
        coverage_score += min(economic_sources / 10, 1) * 25
        
        # Shipping coverage
        shipping_sources = len(collection_results.get('shipping', []))
        coverage_score += min(shipping_sources / 5, 1) * 25
        
        # Social coverage
        social_sources = len(collection_results.get('social', []))
        coverage_score += min(social_sources / 20, 1) * 25
        
        return min(int(coverage_score), 100)
    
    def _calculate_advantage_score(self, collection_results):
        """Calculate competitive advantage score (0-100)"""
        advantage = 0
        
        # Speed advantage (real-time data collection)
        if collection_results:
            advantage += 20
        
        # Coverage advantage (multiple sources per category)
        coverage = self._assess_coverage(collection_results)
        advantage += (coverage / 100) * 30
        
        # Correlation discovery advantage
        correlation_count = len(self.correlation_discoveries)
        advantage += min(correlation_count * 5, 25)
        
        # Source quality advantage
        advantage += 25  # Baseline for having systematic approach
        
        return min(int(advantage), 100)
    
    def start_continuous_intelligence(self, interval_minutes=15):
        """
        Start continuous intelligence collection
        Runs every 15 minutes for real-time market advantage
        """
        print(f"Starting continuous intelligence collection (every {interval_minutes} minutes)")
        
        while True:
            try:
                # Run comprehensive collection
                results = self.run_comprehensive_collection()
                
                # Save results to BigQuery for neural network analysis
                self._save_intelligence_cycle(results)
                
                # Sleep until next cycle
                print(f"Next collection cycle in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
            except Exception as e:
                print(f"Intelligence cycle failed: {e}")
                # Continue with next cycle - resilience is key
                time.sleep(60)  # 1 minute before retry
    
    def _save_intelligence_cycle(self, results):
        """Save intelligence collection results for neural network analysis"""
        try:
            # Create intelligence summary record
            summary = {
                'cycle_timestamp': datetime.now(),
                'news_items': len(results.get('news', [])),
                'economic_indicators': len(results.get('economic', [])),
                'shipping_alerts': len(results.get('shipping', [])),
                'social_signals': len(results.get('social', [])),
                'correlations_found': len(results.get('correlation_hunt', {})),
                'new_sources': len(results.get('source_discovery', [])),
                'intelligence_json': json.dumps(results, default=str)
            }
            
            # Save to BigQuery for neural network training
            df = pd.DataFrame([summary])
            
            job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
            job = safe_load_to_bigquery(
                self.client, df, f"{PROJECT_ID}.{DATASET_ID}.intelligence_cycles", job_config
            )
            job.result()
            
        except Exception as e:
            print(f"Intelligence cycle save failed: {e}")

def main():
    """Execute master intelligence system"""
    controller = MasterIntelligenceController()
    
    print("MASTER INTELLIGENCE CONTROLLER")
    print("Designed for information superiority in soybean oil markets")
    print("=" * 80)
    
    # Single comprehensive collection cycle
    results = controller.run_comprehensive_collection()
    
    print(f"\n=== COLLECTION COMPLETE ===")
    print("Intelligence system operational and ready for neural network analysis")
    
    # Uncomment to start continuous monitoring (every 15 minutes)
    # controller.start_continuous_intelligence(interval_minutes=15)

if __name__ == "__main__":
    main()
