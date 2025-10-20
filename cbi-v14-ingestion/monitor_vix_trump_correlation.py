#!/usr/bin/env python3
"""
monitor_vix_trump_correlation.py
Track VIX spikes correlated with Trump posts/announcements
CRITICAL: VIX spike correlation (tariff announcements)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery
import time
import logging
from bigquery_utils import quick_save_to_bigquery
from cache_utils import get_cache

logger = logging.getLogger(__name__)

class VIXTrumpCorrelationMonitor:
    """
    Monitor VIX spikes and correlate with Trump social media/policy announcements
    Provides early warning system for commodity market volatility
    """
    
    def __init__(self):
        self.client = bigquery.Client(project='cbi-v14')
        self.cache = get_cache()
        self.vix_spike_threshold = 5.0  # 5% spike threshold
        self.correlation_window_hours = 2  # Look back 2 hours for Trump activity
        
    def get_current_vix_data(self):
        """Get current VIX data with 1-hour history"""
        try:
            vix = yf.Ticker("^VIX")
            
            # Get intraday data (1 minute intervals for last day)
            vix_data = vix.history(period="1d", interval="1m")
            
            if vix_data.empty:
                logger.warning("No VIX data available")
                return None
            
            current_price = vix_data['Close'].iloc[-1]
            current_time = vix_data.index[-1]
            
            # Calculate 1-hour change
            hour_ago_idx = max(0, len(vix_data) - 60)  # 60 minutes ago
            hour_ago_price = vix_data['Close'].iloc[hour_ago_idx]
            
            pct_change_1hr = ((current_price - hour_ago_price) / hour_ago_price) * 100
            
            return {
                'timestamp': current_time,
                'current_price': current_price,
                'hour_ago_price': hour_ago_price,
                'pct_change_1hr': pct_change_1hr,
                'spike_detected': abs(pct_change_1hr) > self.vix_spike_threshold
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch VIX data: {e}")
            return None
    
    def check_recent_trump_activity(self, lookback_hours=2):
        """
        Check for recent Trump social media posts or policy announcements
        
        Args:
            lookback_hours: Hours to look back for Trump activity
            
        Returns:
            Dict with Trump activity summary
        """
        try:
            # Query for recent Trump social media activity
            social_query = f"""
            SELECT 
                timestamp,
                platform,
                title as content,
                sentiment_score,
                market_relevance
            FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
            WHERE platform = 'reddit'
                AND LOWER(title) LIKE '%trump%'
                AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {lookback_hours} HOUR)
            ORDER BY timestamp DESC
            LIMIT 10
            """
            
            social_results = self.client.query(social_query).to_dataframe()
            
            # Query for recent executive orders/policy announcements
            policy_query = f"""
            SELECT 
                timestamp,
                category,
                text,
                agricultural_impact,
                soybean_relevance
            FROM `cbi-v14.staging.trump_policy_intelligence`
            WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {lookback_hours} HOUR)
                AND agricultural_impact > 0.3
            ORDER BY timestamp DESC
            LIMIT 10
            """
            
            policy_results = self.client.query(policy_query).to_dataframe()
            
            # Analyze activity
            total_posts = len(social_results)
            total_policies = len(policy_results)
            
            # Check for high-impact content
            high_impact_social = social_results[social_results['market_relevance'] == 'high'] if not social_results.empty else pd.DataFrame()
            high_impact_policy = policy_results[policy_results['agricultural_impact'] > 0.7] if not policy_results.empty else pd.DataFrame()
            
            # Calculate tariff mention intensity (based on text content)
            tariff_intensity = 0
            if not policy_results.empty:
                for _, policy in policy_results.iterrows():
                    text_lower = policy['text'].lower() if policy['text'] else ''
                    tariff_intensity += sum(1 for kw in ['tariff', 'trade', 'duty'] if kw in text_lower)
            
            return {
                'social_posts': total_posts,
                'policy_announcements': total_policies,
                'high_impact_social': len(high_impact_social),
                'high_impact_policy': len(high_impact_policy),
                'tariff_intensity': tariff_intensity,
                'latest_social': social_results.iloc[0]['content'] if not social_results.empty else None,
                'latest_policy': policy_results.iloc[0]['text'] if not policy_results.empty else None,
                'activity_detected': total_posts > 0 or total_policies > 0
            }
            
        except Exception as e:
            logger.error(f"Failed to check Trump activity: {e}")
            return {
                'social_posts': 0,
                'policy_announcements': 0,
                'high_impact_social': 0,
                'high_impact_policy': 0,
                'tariff_intensity': 0,
                'latest_social': None,
                'latest_policy': None,
                'activity_detected': False
            }
    
    def log_correlation_event(self, vix_data, trump_activity):
        """
        Log VIX spike + Trump activity correlation event to BigQuery
        
        Args:
            vix_data: VIX price and change data
            trump_activity: Trump social/policy activity data
        """
        try:
            correlation_data = [{
                'vix_spike_time': vix_data['timestamp'],
                'vix_price': vix_data['current_price'],
                'vix_pct_change_1hr': vix_data['pct_change_1hr'],
                'trump_social_posts_2hr': trump_activity['social_posts'],
                'trump_policy_announcements_2hr': trump_activity['policy_announcements'],
                'high_impact_social_posts': trump_activity['high_impact_social'],
                'high_impact_policy_announcements': trump_activity['high_impact_policy'],
                'tariff_keyword_intensity': trump_activity['tariff_intensity'],
                'latest_trump_content': trump_activity['latest_social'] or trump_activity['latest_policy'],
                'correlation_detected': True,
                'correlation_strength': self._calculate_correlation_strength(vix_data, trump_activity),
                'ingestion_timestamp': datetime.now()
            }]
            
            df = pd.DataFrame(correlation_data)
            
            # Use quick_save_to_bigquery for correlation events
            quick_save_to_bigquery(df, 'volatility_data')
            
            logger.info(f"✅ Logged VIX-Trump correlation event: {vix_data['pct_change_1hr']:.2f}% VIX change")
            
        except Exception as e:
            logger.error(f"Failed to log correlation event: {e}")
    
    def _calculate_correlation_strength(self, vix_data, trump_activity):
        """
        Calculate correlation strength score (0.0 to 1.0)
        
        Factors:
        - VIX spike magnitude
        - Trump activity volume
        - High-impact content presence
        - Tariff keyword intensity
        """
        vix_factor = min(abs(vix_data['pct_change_1hr']) / 20.0, 1.0)  # Normalize to 20% max
        activity_factor = min((trump_activity['social_posts'] + trump_activity['policy_announcements']) / 10.0, 1.0)
        impact_factor = (trump_activity['high_impact_social'] + trump_activity['high_impact_policy']) / 5.0
        tariff_factor = min(trump_activity['tariff_intensity'] / 5.0, 1.0)
        
        correlation_strength = (vix_factor * 0.4 + activity_factor * 0.3 + impact_factor * 0.2 + tariff_factor * 0.1)
        
        return min(correlation_strength, 1.0)
    
    def run_single_check(self):
        """
        Run a single correlation check
        
        Returns:
            Dict with check results
        """
        logger.info("Running VIX-Trump correlation check...")
        
        # Get current VIX data
        vix_data = self.get_current_vix_data()
        if not vix_data:
            return {'status': 'error', 'message': 'Failed to fetch VIX data'}
        
        # Check for Trump activity
        trump_activity = self.check_recent_trump_activity(self.correlation_window_hours)
        
        # Determine if correlation event detected
        spike_detected = vix_data['spike_detected']
        activity_detected = trump_activity['activity_detected']
        
        result = {
            'status': 'success',
            'timestamp': datetime.now(),
            'vix_price': vix_data['current_price'],
            'vix_change_1hr': vix_data['pct_change_1hr'],
            'spike_detected': spike_detected,
            'trump_activity': activity_detected,
            'correlation_event': spike_detected and activity_detected
        }
        
        # Log correlation event if detected
        if result['correlation_event']:
            logger.warning(f"🚨 CORRELATION EVENT DETECTED: {vix_data['pct_change_1hr']:.2f}% VIX spike + Trump activity")
            self.log_correlation_event(vix_data, trump_activity)
            
            result['correlation_strength'] = self._calculate_correlation_strength(vix_data, trump_activity)
            result['trump_posts'] = trump_activity['social_posts']
            result['trump_policies'] = trump_activity['policy_announcements']
        
        elif spike_detected:
            logger.info(f"📊 VIX spike detected ({vix_data['pct_change_1hr']:.2f}%) but no recent Trump activity")
        
        elif activity_detected:
            logger.info(f"📱 Trump activity detected but no VIX spike ({vix_data['pct_change_1hr']:.2f}%)")
        
        else:
            logger.debug(f"No correlation event: VIX {vix_data['pct_change_1hr']:.2f}%, Trump activity: {activity_detected}")
        
        return result
    
    def run_continuous_monitoring(self, check_interval_minutes=5):
        """
        Run continuous VIX-Trump correlation monitoring
        
        Args:
            check_interval_minutes: Minutes between checks
        """
        logger.info(f"Starting continuous VIX-Trump correlation monitoring (every {check_interval_minutes} minutes)")
        
        try:
            while True:
                result = self.run_single_check()
                
                if result['status'] == 'success':
                    if result['correlation_event']:
                        print(f"🚨 CORRELATION EVENT: VIX {result['vix_change_1hr']:.2f}% + Trump activity")
                    else:
                        print(f"📊 Check complete: VIX {result['vix_change_1hr']:.2f}%, Activity: {result['trump_activity']}")
                
                # Wait for next check
                time.sleep(check_interval_minutes * 60)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")


def main():
    """Execute VIX-Trump correlation monitoring"""
    monitor = VIXTrumpCorrelationMonitor()
    
    print("=== VIX + TRUMP CORRELATION MONITOR ===")
    print("Tracking VIX spikes correlated with Trump announcements")
    print("=" * 60)
    
    # Run single check
    result = monitor.run_single_check()
    
    if result['status'] == 'success':
        print(f"Current VIX: ${result['vix_price']:.2f}")
        print(f"1-Hour Change: {result['vix_change_1hr']:.2f}%")
        print(f"Spike Detected: {result['spike_detected']}")
        print(f"Trump Activity: {result['trump_activity']}")
        
        if result['correlation_event']:
            print(f"\n🚨 CORRELATION EVENT DETECTED!")
            print(f"Correlation Strength: {result['correlation_strength']:.2f}")
            print(f"Trump Posts (2hr): {result['trump_posts']}")
            print(f"Trump Policies (2hr): {result['trump_policies']}")
        
        print("\n✅ VIX-Trump correlation check completed")
        
        # Uncomment to run continuous monitoring
        # print("\nStarting continuous monitoring (Ctrl+C to stop)...")
        # monitor.run_continuous_monitoring(check_interval_minutes=5)
    
    else:
        print(f"❌ Check failed: {result['message']}")


if __name__ == "__main__":
    main()
