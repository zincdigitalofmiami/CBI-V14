#!/usr/bin/env python3
"""
ES (S&P 500 Futures) Prediction Model - REAL DATA ONLY
NO FAKE DATA - Fetches from BigQuery or returns empty predictions

Author: AI Assistant
Date: November 16, 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Dict, List, Optional
from google.cloud import bigquery
import talib
import warnings
warnings.filterwarnings('ignore')
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ESFuturesPredictor:
    """
    ES futures prediction using REAL DATA ONLY
    """
    
    def __init__(self):
        self.client = bigquery.Client(project='cbi-v14')
        self.models = {}
        
    def fetch_real_es_data(self) -> Optional[pd.DataFrame]:
        """
        Fetch REAL ES futures data from BigQuery
        Returns None if unavailable
        """
        try:
            query = """
            SELECT 
                date,
                open,
                high,
                low,
                close,
                volume
            FROM `cbi-v14.market_data.es_futures`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 252 DAY)
            ORDER BY date DESC
            """
            
            df = self.client.query(query).to_dataframe()
            
            if df.empty:
                logger.warning("No ES futures data found in BigQuery")
                return None
                
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch ES data: {e}")
            return None
    
    def fetch_real_market_data(self) -> Dict[str, pd.DataFrame]:
        """
        Fetch REAL market data from BigQuery
        Returns empty dict if unavailable
        """
        market_data = {}
        
        try:
            # VIX data
            vix_query = """
            SELECT date, close
            FROM `cbi-v14.market_data.vix`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 252 DAY)
            ORDER BY date DESC
            """
            vix_df = self.client.query(vix_query).to_dataframe()
            if not vix_df.empty:
                market_data['VIX'] = vix_df
            
            # Dollar Index
            dx_query = """
            SELECT date, close
            FROM `cbi-v14.market_data.dollar_index`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 252 DAY)
            ORDER BY date DESC
            """
            dx_df = self.client.query(dx_query).to_dataframe()
            if not dx_df.empty:
                market_data['DX'] = dx_df
            
            # Crude Oil
            cl_query = """
            SELECT date, close
            FROM `cbi-v14.market_data.crude_oil`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 252 DAY)
            ORDER BY date DESC
            """
            cl_df = self.client.query(cl_query).to_dataframe()
            if not cl_df.empty:
                market_data['CL'] = cl_df
                
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            
        return market_data
    
    def calculate_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators from REAL data only
        """
        if df is None or df.empty or 'close' not in df.columns:
            return pd.DataFrame()
        
        features = pd.DataFrame(index=df.index)
        
        try:
            close = df['close'].values
            high = df['high'].values if 'high' in df.columns else close
            low = df['low'].values if 'low' in df.columns else close
            volume = df['volume'].values if 'volume' in df.columns else None
            
            # Only calculate if we have enough data
            if len(close) >= 14:
                features['rsi_14'] = talib.RSI(close, timeperiod=14)
            
            if len(close) >= 26:
                macd, signal, hist = talib.MACD(close)
                features['macd'] = macd
                features['macd_signal'] = signal
                features['macd_hist'] = hist
            
            if len(close) >= 20:
                upper, middle, lower = talib.BBANDS(close)
                features['bb_upper'] = upper
                features['bb_middle'] = middle
                features['bb_lower'] = lower
                features['bb_width'] = upper - lower
                
            # Price action from REAL data
            features['returns_1'] = df['close'].pct_change(1)
            features['returns_5'] = df['close'].pct_change(5)
            features['returns_20'] = df['close'].pct_change(20)
            
        except Exception as e:
            logger.error(f"Error calculating technical features: {e}")
            
        return features
    
    def predict_es_movement(self) -> Dict:
        """
        Predict ES movement using REAL DATA ONLY
        Returns empty prediction if data unavailable
        """
        # Fetch real data
        es_df = self.fetch_real_es_data()
        market_data = self.fetch_real_market_data()
        
        if es_df is None or es_df.empty:
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'NO_DATA',
                'message': 'No ES futures data available',
                'data_available': False
            }
        
        # Calculate real features
        tech_features = self.calculate_technical_features(es_df)
        
        if tech_features.empty:
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'INSUFFICIENT_DATA',
                'message': 'Insufficient data for technical analysis',
                'data_available': False
            }
        
        # Get current price
        current_price = float(es_df['close'].iloc[-1])
        
        # Calculate simple predictions from REAL patterns
        prediction = self._calculate_real_prediction(tech_features, es_df)
        
        # Build report
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'SUCCESS',
            'data_available': True,
            'data_source': 'REAL_DATA',
            'horizon': 'daily',
            'current_price': current_price,
            'prediction': prediction,
            'support_resistance': self._calculate_real_support_resistance(es_df),
            'risk_metrics': self._calculate_real_risk_metrics(es_df),
            'trading_signals': self._generate_real_signals(tech_features, prediction),
            'key_drivers': self._identify_real_drivers(tech_features)
        }
        
        return report
    
    def _calculate_real_prediction(self, features: pd.DataFrame, df: pd.DataFrame) -> Dict:
        """
        Calculate prediction from REAL technical patterns
        """
        score = 0.0
        confidence = 0.5
        
        # RSI signals from REAL data
        if 'rsi_14' in features.columns:
            latest_rsi = features['rsi_14'].iloc[-1]
            if pd.notna(latest_rsi):
                if latest_rsi < 30:
                    score += 0.02  # Oversold
                    confidence += 0.1
                elif latest_rsi > 70:
                    score -= 0.02  # Overbought
                    confidence += 0.1
        
        # MACD signals from REAL data
        if 'macd_hist' in features.columns:
            latest_macd = features['macd_hist'].iloc[-1]
            if pd.notna(latest_macd):
                if latest_macd > 0:
                    score += 0.01
                else:
                    score -= 0.01
                confidence += 0.05
        
        # Trend from REAL price action
        if 'returns_20' in features.columns:
            trend = features['returns_20'].iloc[-1]
            if pd.notna(trend):
                score += trend * 0.5  # Follow trend
                confidence += abs(trend) * 2
        
        # Cap predictions at realistic levels
        score = np.clip(score, -0.05, 0.05)
        confidence = np.clip(confidence, 0, 1)
        
        current_price = float(df['close'].iloc[-1])
        
        return {
            'direction': 'UP' if score > 0 else 'DOWN',
            'magnitude': abs(score),
            'target_price': current_price * (1 + score),
            'expected_return': f"{score*100:.2f}%",
            'confidence': f"{confidence*100:.1f}%"
        }
    
    def _calculate_real_support_resistance(self, df: pd.DataFrame) -> Dict:
        """
        Calculate support/resistance from REAL price data
        """
        if df.empty or 'close' not in df.columns:
            return {}
        
        close = df['close']
        current = float(close.iloc[-1])
        
        # Real highs/lows
        resistance_1 = float(close.iloc[-20:].max()) if len(close) >= 20 else current
        support_1 = float(close.iloc[-20:].min()) if len(close) >= 20 else current
        
        resistance_2 = float(close.iloc[-50:].max()) if len(close) >= 50 else resistance_1
        support_2 = float(close.iloc[-50:].min()) if len(close) >= 50 else support_1
        
        # Real pivot points
        if 'high' in df.columns and 'low' in df.columns:
            high = float(df['high'].iloc[-1])
            low = float(df['low'].iloc[-1])
            pivot = (high + low + current) / 3
            r1 = 2 * pivot - low
            s1 = 2 * pivot - high
        else:
            pivot = current
            r1 = resistance_1
            s1 = support_1
        
        return {
            'immediate_resistance': resistance_1,
            'immediate_support': support_1,
            'major_resistance': resistance_2,
            'major_support': support_2,
            'pivot_point': pivot,
            'r1': r1,
            's1': s1
        }
    
    def _calculate_real_risk_metrics(self, df: pd.DataFrame) -> Dict:
        """
        Calculate risk metrics from REAL data
        """
        if df.empty or 'close' not in df.columns:
            return {}
        
        returns = df['close'].pct_change().dropna()
        
        if len(returns) < 20:
            return {'status': 'Insufficient data for risk calculation'}
        
        # Real volatility
        volatility = returns.std() * np.sqrt(252)
        
        # Real VaR
        var_95 = np.percentile(returns, 5)
        
        # Real expected shortfall
        es_95 = returns[returns <= var_95].mean() if len(returns[returns <= var_95]) > 0 else var_95
        
        return {
            'annualized_volatility': f"{volatility*100:.1f}%",
            'value_at_risk_95': f"{var_95*100:.2f}%",
            'expected_shortfall': f"{es_95*100:.2f}%",
            'suggested_stop_loss': f"{-abs(volatility)*2*100:.2f}%",
            'data_points': len(returns)
        }
    
    def _generate_real_signals(self, features: pd.DataFrame, prediction: Dict) -> List[str]:
        """
        Generate signals from REAL data patterns
        """
        signals = []
        
        if not features.empty and prediction.get('direction'):
            if prediction['direction'] == 'UP' and prediction['magnitude'] > 0.01:
                signals.append(f"📈 Bullish signal detected: {prediction['expected_return']}")
            elif prediction['direction'] == 'DOWN' and prediction['magnitude'] > 0.01:
                signals.append(f"📉 Bearish signal detected: {prediction['expected_return']}")
            else:
                signals.append("⏸️ No clear directional signal")
            
            # Add RSI signal if available
            if 'rsi_14' in features.columns:
                rsi = features['rsi_14'].iloc[-1]
                if pd.notna(rsi):
                    if rsi < 30:
                        signals.append(f"Oversold condition (RSI: {rsi:.1f})")
                    elif rsi > 70:
                        signals.append(f"Overbought condition (RSI: {rsi:.1f})")
        else:
            signals.append("Insufficient data for signal generation")
        
        return signals
    
    def _identify_real_drivers(self, features: pd.DataFrame) -> List[str]:
        """
        Identify drivers from REAL feature data
        """
        drivers = []
        
        if not features.empty:
            # Check RSI
            if 'rsi_14' in features.columns:
                rsi = features['rsi_14'].iloc[-1]
                if pd.notna(rsi):
                    if rsi < 30:
                        drivers.append("Oversold RSI (bullish)")
                    elif rsi > 70:
                        drivers.append("Overbought RSI (bearish)")
            
            # Check MACD
            if 'macd_hist' in features.columns:
                macd = features['macd_hist'].iloc[-1]
                if pd.notna(macd):
                    if macd > 0:
                        drivers.append("Positive MACD (bullish)")
                    else:
                        drivers.append("Negative MACD (bearish)")
            
            # Check momentum
            if 'returns_20' in features.columns:
                momentum = features['returns_20'].iloc[-1]
                if pd.notna(momentum):
                    if abs(momentum) > 0.05:
                        drivers.append(f"Strong {20}-day momentum: {momentum*100:.1f}%")
        
        if not drivers:
            drivers.append("No clear technical drivers identified")
        
        return drivers


def generate_es_prediction():
    """
    Generate ES prediction using REAL DATA ONLY
    """
    predictor = ESFuturesPredictor()
    
    # Generate prediction with real data
    report = predictor.predict_es_movement()
    
    # Save report
    output_path = Path("dashboard-nextjs/public/api/es_prediction.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    if report.get('data_available'):
        print("ES Futures Prediction Report Generated with REAL DATA")
        print(f"Current Price: {report.get('current_price', 'N/A')}")
        print(f"Status: {report.get('status')}")
    else:
        print("ES Futures Prediction: NO DATA AVAILABLE")
        print(f"Status: {report.get('status')}")
        print(f"Message: {report.get('message')}")
    
    return report


if __name__ == "__main__":
    generate_es_prediction()
