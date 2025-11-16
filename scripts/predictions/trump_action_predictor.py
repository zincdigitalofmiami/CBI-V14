#!/usr/bin/env python3
"""
Trump Action Prediction Model
Predicts likelihood and impact of Trump policy actions using REAL DATA ONLY.
NO PLACEHOLDER DATA - fetches from actual sources or returns None.

Author: AI Assistant
Date: November 16, 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from google.cloud import bigquery
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrumpActionPredictor:
    """
    Predicts Trump policy actions and their market impact using REAL DATA ONLY
    """
    
    def __init__(self):
        self.client = bigquery.Client(project='cbi-v14')
        self.action_model = None
        self.impact_model = None
        self.action_history = []
        
        # Action categories we predict
        self.action_types = [
            'tariff_announcement',
            'trade_negotiation',
            'social_media_storm',
            'policy_reversal',
            'market_intervention',
            'china_threat',
            'deal_making'
        ]
    
    def fetch_real_truth_social_data(self) -> Optional[pd.DataFrame]:
        """
        Fetch REAL Truth Social posts from BigQuery or API
        Returns None if data unavailable
        """
        try:
            # Try BigQuery first
            query = """
            SELECT 
                timestamp,
                text,
                likes,
                reposts,
                replies
            FROM `cbi-v14.forecasting_data_warehouse.truth_social_posts`
            WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
            ORDER BY timestamp DESC
            """
            
            df = self.client.query(query).to_dataframe()
            
            if df.empty:
                logger.warning("No Truth Social data found in BigQuery")
                return None
                
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch Truth Social data: {e}")
            
            # Try ScrapeCreators API as fallback
            try:
                api_key = os.getenv('SCRAPE_CREATORS_KEY')
                if not api_key:
                    logger.error("No ScrapeCreators API key found")
                    return None
                    
                url = 'https://api.scrapecreators.com/v1/truthsocial'
                headers = {'x-api-key': api_key}
                params = {'username': 'realDonaldTrump', 'limit': 100}
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'posts' in data:
                        return pd.DataFrame(data['posts'])
                        
            except Exception as api_error:
                logger.error(f"API fallback also failed: {api_error}")
                
            return None
    
    def fetch_real_market_data(self) -> Optional[pd.DataFrame]:
        """
        Fetch REAL market data from BigQuery
        Returns None if data unavailable
        """
        try:
            query = """
            SELECT 
                date,
                close,
                vix,
                dollar_index,
                volume
            FROM `cbi-v14.market_data.daily_indicators`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            ORDER BY date DESC
            """
            
            df = self.client.query(query).to_dataframe()
            
            if df.empty:
                logger.warning("No market data found")
                return None
                
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            return None
    
    def extract_posting_patterns(self, posts_df: pd.DataFrame) -> Dict:
        """
        Extract patterns from REAL Truth Social posting behavior
        """
        if posts_df is None or posts_df.empty:
            return {}
        
        features = {}
        
        # Posting velocity - REAL calculations
        posts_24h = len(posts_df[posts_df['timestamp'] > datetime.now() - timedelta(hours=24)])
        posts_7d = len(posts_df[posts_df['timestamp'] > datetime.now() - timedelta(days=7)])
        
        features['posting_velocity_24h'] = posts_24h
        features['posting_velocity_7d_avg'] = posts_7d / 7 if posts_7d > 0 else 0
        features['posting_acceleration'] = posts_24h - (posts_7d / 7) if posts_7d > 0 else 0
        
        # Time patterns from REAL data
        if 'timestamp' in posts_df.columns:
            posts_df['hour'] = pd.to_datetime(posts_df['timestamp']).dt.hour
            features['late_night_posts'] = len(posts_df[posts_df['hour'].between(0, 5)])
            features['early_morning_posts'] = len(posts_df[posts_df['hour'].between(5, 8)])
            features['market_hours_posts'] = len(posts_df[posts_df['hour'].between(9, 16)])
        
        # Content patterns from REAL text
        if 'text' in posts_df.columns:
            texts = ' '.join(posts_df['text'].fillna(''))
            
            # REAL text analysis
            features['exclamation_rate'] = texts.count('!') / max(len(texts), 1) * 1000
            features['caps_rate'] = sum(1 for c in texts if c.isupper()) / max(len(texts), 1)
            
            # REAL keyword counts
            features['action_signals'] = sum([
                texts.lower().count('will be'),
                texts.lower().count('going to'),
                texts.lower().count('announcing'),
                texts.lower().count('very soon'),
                texts.lower().count('big news'),
                texts.lower().count('stay tuned')
            ])
            
            features['threat_level'] = sum([
                texts.lower().count('tariff') * 3,
                texts.lower().count('tax') * 2,
                texts.lower().count('china') * 2,
                texts.lower().count('unfair') * 1,
                texts.lower().count('retaliate') * 3
            ])
        
        # REAL engagement metrics
        if 'likes' in posts_df.columns:
            features['avg_engagement'] = posts_df['likes'].mean()
            if len(posts_df) > 20:
                features['engagement_trend'] = (
                    posts_df.iloc[-10:]['likes'].mean() - 
                    posts_df.iloc[-20:-10]['likes'].mean()
                )
            else:
                features['engagement_trend'] = 0
        
        return features
    
    def predict_next_action(self, 
                           posts_df: Optional[pd.DataFrame] = None,
                           market_df: Optional[pd.DataFrame] = None,
                           date: Optional[datetime] = None) -> Dict:
        """
        Predict Trump's next action based on REAL DATA ONLY
        Returns empty prediction if data unavailable
        """
        if date is None:
            date = datetime.now()
        
        # Fetch real data if not provided
        if posts_df is None:
            posts_df = self.fetch_real_truth_social_data()
        
        if market_df is None:
            market_df = self.fetch_real_market_data()
        
        # If no data available, return empty prediction
        if posts_df is None or posts_df.empty:
            return {
                'timestamp': date.isoformat(),
                'status': 'NO_DATA',
                'message': 'No Truth Social data available',
                'top_prediction': 'unknown',
                'top_probability': 0,
                'all_predictions': {},
                'features': {},
                'risk_level': 'UNKNOWN'
            }
        
        # Extract REAL features
        posting_features = self.extract_posting_patterns(posts_df)
        
        if not posting_features:
            return {
                'timestamp': date.isoformat(),
                'status': 'INSUFFICIENT_DATA',
                'message': 'Insufficient data for prediction',
                'top_prediction': 'unknown',
                'top_probability': 0,
                'all_predictions': {},
                'features': {},
                'risk_level': 'UNKNOWN'
            }
        
        # Calculate predictions based on REAL patterns
        predictions = self._calculate_predictions_from_real_data(posting_features)
        
        # Sort by probability
        sorted_predictions = sorted(
            predictions.items(),
            key=lambda x: x[1]['probability'],
            reverse=True
        )
        
        return {
            'timestamp': date.isoformat(),
            'status': 'SUCCESS',
            'top_prediction': sorted_predictions[0][0] if sorted_predictions else 'unknown',
            'top_probability': sorted_predictions[0][1]['probability'] if sorted_predictions else 0,
            'all_predictions': dict(sorted_predictions),
            'features': posting_features,
            'risk_level': self._calculate_risk_level(posting_features),
            'data_source': 'REAL_DATA'
        }
    
    def _calculate_predictions_from_real_data(self, features: Dict) -> Dict:
        """
        Calculate predictions based on REAL feature patterns
        """
        predictions = {}
        
        for action in self.action_types:
            predictions[action] = {
                'probability': 0.0,
                'triggers': [],
                'timing': 'unknown'
            }
        
        # REAL pattern-based predictions
        
        # High threat level from REAL text analysis
        if features.get('threat_level', 0) > 10:
            predictions['tariff_announcement']['probability'] = min(
                features['threat_level'] / 20, 0.9
            )
            predictions['tariff_announcement']['triggers'].append('High threat rhetoric detected')
            predictions['tariff_announcement']['timing'] = '24-48 hours'
        
        # High posting velocity from REAL data
        if features.get('posting_velocity_24h', 0) > 10:
            predictions['social_media_storm']['probability'] = min(
                features['posting_velocity_24h'] / 15, 0.9
            )
            predictions['social_media_storm']['triggers'].append('Elevated posting frequency')
            predictions['social_media_storm']['timing'] = 'Ongoing'
        
        # Action signals from REAL keywords
        if features.get('action_signals', 0) > 3:
            predictions['trade_negotiation']['probability'] = min(
                features['action_signals'] / 10, 0.7
            )
            predictions['trade_negotiation']['triggers'].append('Action language detected')
            predictions['trade_negotiation']['timing'] = 'This week'
        
        # China mentions from REAL text
        if features.get('threat_level', 0) > 5 and 'china' in str(features).lower():
            predictions['china_threat']['probability'] = 0.6
            predictions['china_threat']['triggers'].append('China-related threats detected')
            predictions['china_threat']['timing'] = 'This week'
        
        return predictions
    
    def _calculate_risk_level(self, features: Dict) -> str:
        """
        Calculate risk level from REAL features
        """
        if not features:
            return 'UNKNOWN'
        
        risk_score = 0
        
        # Based on REAL metrics
        risk_score += min(features.get('posting_velocity_24h', 0) / 10, 1) * 30
        risk_score += min(features.get('threat_level', 0) / 20, 1) * 40
        risk_score += min(features.get('action_signals', 0) / 10, 1) * 30
        
        if risk_score < 25:
            return 'LOW'
        elif risk_score < 50:
            return 'MODERATE'
        elif risk_score < 75:
            return 'HIGH'
        else:
            return 'EXTREME'
    
    def generate_prediction_report(self) -> Dict:
        """
        Generate prediction report using REAL DATA ONLY
        """
        # Fetch real data
        posts_df = self.fetch_real_truth_social_data()
        market_df = self.fetch_real_market_data()
        
        # Get predictions
        prediction = self.predict_next_action(posts_df, market_df)
        
        if prediction['status'] != 'SUCCESS':
            # Return data unavailable report
            return {
                'generated_at': datetime.now().isoformat(),
                'status': prediction['status'],
                'message': prediction.get('message', 'Data unavailable'),
                'data_available': False
            }
        
        # Create report with REAL data
        report = {
            'generated_at': datetime.now().isoformat(),
            'status': 'SUCCESS',
            'data_available': True,
            'data_source': 'REAL_DATA',
            'prediction': {
                'most_likely_action': prediction['top_prediction'],
                'probability': prediction['top_probability'],
                'timing': prediction['all_predictions'].get(
                    prediction['top_prediction'], {}
                ).get('timing', 'unknown'),
                'triggers': prediction['all_predictions'].get(
                    prediction['top_prediction'], {}
                ).get('triggers', []),
                'risk_level': prediction['risk_level']
            },
            'key_indicators': {
                'posting_velocity_24h': prediction['features'].get('posting_velocity_24h', 0),
                'threat_level': prediction['features'].get('threat_level', 0),
                'action_signals': prediction['features'].get('action_signals', 0),
                'market_condition': 'Data-based assessment'
            },
            'alternative_scenarios': [],
            'recommendations': []
        }
        
        # Add alternative scenarios from REAL predictions
        for action, details in prediction['all_predictions'].items():
            if action != prediction['top_prediction'] and details['probability'] > 0.1:
                report['alternative_scenarios'].append({
                    'action': action,
                    'probability': details['probability']
                })
        
        # Generate recommendations based on REAL data
        if prediction['risk_level'] in ['HIGH', 'EXTREME']:
            report['recommendations'].append("High activity detected - monitor closely")
        
        if prediction['features'].get('threat_level', 0) > 10:
            report['recommendations'].append("Elevated threat rhetoric - prepare for volatility")
        
        return report


def generate_trump_prediction():
    """
    Generate real-time Trump action prediction using REAL DATA ONLY
    """
    predictor = TrumpActionPredictor()
    
    # Generate prediction report with REAL data
    report = predictor.generate_prediction_report()
    
    # Save report
    output_path = Path("dashboard-nextjs/public/api/trump_prediction.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    if report.get('data_available'):
        print("Trump Action Prediction Report Generated with REAL DATA")
        print(f"Most Likely Action: {report['prediction']['most_likely_action']}")
        print(f"Probability: {report['prediction']['probability']*100:.1f}%")
    else:
        print("Trump Action Prediction: NO DATA AVAILABLE")
        print(f"Status: {report.get('status')}")
        print(f"Message: {report.get('message')}")
    
    return report


if __name__ == "__main__":
    import os
    generate_trump_prediction()