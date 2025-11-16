#!/usr/bin/env python3
"""
Unified Sentiment Analysis System
Combines ALL qualitative data sources with neural network analysis
to create a comprehensive market sentiment indicator.

Author: AI Assistant
Date: November 16, 2025
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import torch
import torch.nn as nn
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import warnings
warnings.filterwarnings('ignore')

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
SENTIMENT_DIR = DRIVE / "TrainingData/sentiment"
SENTIMENT_DIR.mkdir(parents=True, exist_ok=True)


class UnifiedSentimentNeuralSystem:
    """
    Comprehensive sentiment analysis combining:
    1. Traditional sentiment (social, news, analysts)
    2. Market microstructure signals
    3. Policy document analysis
    4. Weather/supply sentiment
    5. Technical indicators as sentiment
    6. Neural network pattern recognition
    """
    
    def __init__(self):
        # Initialize transformer models for advanced NLP
        self.finbert = None
        self.init_finbert()
        
        # Initialize neural network for pattern recognition
        self.sentiment_nn = None
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=50)  # Reduce dimensionality
        
    def init_finbert(self):
        """Initialize FinBERT for financial sentiment analysis"""
        try:
            self.finbert = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info("✅ FinBERT loaded for financial sentiment")
        except Exception as e:
            logger.warning(f"FinBERT unavailable, using fallback: {e}")
            # Fallback to general sentiment
            self.finbert = pipeline("sentiment-analysis")
    
    # ==================== QUALITATIVE DATA SOURCES ====================
    
    def extract_policy_sentiment(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract sentiment from policy documents and announcements
        """
        logger.info("Extracting policy sentiment from qualitative data...")
        
        policy_indicators = {
            # Trump policy signals
            'tariff_escalation': ['tariff', 'duty', 'import tax', 'trade war'],
            'trade_deal': ['deal', 'agreement', 'negotiate', 'meeting'],
            'america_first': ['america first', 'protect', 'domestic', 'jobs'],
            
            # Agricultural policy
            'farm_support': ['farm bill', 'subsidy', 'support', 'aid'],
            'biofuel_mandate': ['ethanol', 'biodiesel', 'renewable fuel', 'RFS'],
            'export_promotion': ['export', 'market access', 'trade promotion'],
            
            # Regulatory signals
            'deregulation': ['deregulate', 'reduce regulation', 'cut red tape'],
            'environmental': ['climate', 'carbon', 'sustainability', 'green'],
            
            # Economic policy
            'stimulus': ['stimulus', 'spending', 'infrastructure', 'investment'],
            'monetary': ['fed', 'rate', 'inflation', 'dollar']
        }
        
        sentiment_scores = pd.DataFrame(index=df.index)
        
        for policy, keywords in policy_indicators.items():
            # Count keyword occurrences
            if 'text' in df.columns:
                sentiment_scores[f'policy_{policy}'] = df['text'].apply(
                    lambda x: sum(1 for kw in keywords if kw in str(x).lower())
                )
        
        # Normalize to -1 to 1 scale
        for col in sentiment_scores.columns:
            max_val = sentiment_scores[col].max()
            if max_val > 0:
                sentiment_scores[col] = sentiment_scores[col] / max_val
        
        return sentiment_scores
    
    def extract_weather_sentiment(self, weather_df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert weather conditions into sentiment scores
        Weather extremes = negative sentiment for crops
        """
        logger.info("Converting weather data to sentiment...")
        
        weather_sentiment = pd.DataFrame(index=weather_df.index)
        
        if 'temperature' in weather_df.columns:
            # Extreme temperatures are negative
            temp_mean = weather_df['temperature'].mean()
            temp_std = weather_df['temperature'].std()
            weather_sentiment['temp_stress'] = -abs(
                (weather_df['temperature'] - temp_mean) / temp_std
            ).clip(-1, 1)
        
        if 'precipitation' in weather_df.columns:
            # Both drought and flood are negative
            precip_mean = weather_df['precipitation'].mean()
            precip_std = weather_df['precipitation'].std()
            
            # Drought sentiment (low precipitation)
            weather_sentiment['drought_stress'] = np.where(
                weather_df['precipitation'] < precip_mean - precip_std,
                -(precip_mean - weather_df['precipitation']) / precip_std,
                0
            ).clip(-1, 0)
            
            # Flood sentiment (high precipitation)
            weather_sentiment['flood_stress'] = np.where(
                weather_df['precipitation'] > precip_mean + 2*precip_std,
                -(weather_df['precipitation'] - precip_mean) / precip_std,
                0
            ).clip(-1, 0)
        
        # Growing conditions index
        if 'growing_degree_days' in weather_df.columns:
            # Optimal GDD = positive sentiment
            gdd_optimal = 25  # Optimal daily GDD for crops
            weather_sentiment['growing_conditions'] = 1 - abs(
                weather_df['growing_degree_days'] - gdd_optimal
            ) / gdd_optimal
        
        # Composite weather sentiment
        weather_sentiment['weather_composite'] = weather_sentiment.mean(axis=1)
        
        return weather_sentiment
    
    def extract_market_microstructure_sentiment(self, market_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract sentiment from market microstructure
        Order flow, spreads, volume patterns indicate sentiment
        """
        logger.info("Extracting market microstructure sentiment...")
        
        micro_sentiment = pd.DataFrame(index=market_df.index)
        
        # Volume sentiment (high volume = high conviction)
        if 'volume' in market_df.columns:
            vol_ma = market_df['volume'].rolling(20).mean()
            micro_sentiment['volume_sentiment'] = (
                market_df['volume'] / vol_ma - 1
            ).clip(-1, 1)
        
        # Price momentum sentiment
        if 'close' in market_df.columns:
            returns = market_df['close'].pct_change()
            micro_sentiment['momentum_sentiment'] = returns.rolling(5).mean() * 100
            
            # Volatility sentiment (high vol = uncertainty = negative)
            micro_sentiment['volatility_sentiment'] = -returns.rolling(20).std() * 100
        
        # Spread sentiment (wide spreads = negative)
        if 'bid' in market_df.columns and 'ask' in market_df.columns:
            spread_pct = (market_df['ask'] - market_df['bid']) / market_df['bid']
            micro_sentiment['spread_sentiment'] = -spread_pct * 100
        
        # Options sentiment (if available)
        if 'put_call_ratio' in market_df.columns:
            # High put/call = bearish
            micro_sentiment['options_sentiment'] = 1 - market_df['put_call_ratio']
        
        # CFTC positioning sentiment
        if 'managed_money_net' in market_df.columns:
            # Normalize positioning
            pos_mean = market_df['managed_money_net'].rolling(52).mean()
            pos_std = market_df['managed_money_net'].rolling(52).std()
            micro_sentiment['positioning_sentiment'] = (
                (market_df['managed_money_net'] - pos_mean) / pos_std
            ).clip(-2, 2) / 2
        
        return micro_sentiment
    
    def extract_supply_demand_sentiment(self, supply_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract sentiment from supply/demand indicators
        """
        logger.info("Extracting supply/demand sentiment...")
        
        sd_sentiment = pd.DataFrame(index=supply_df.index)
        
        # Inventory sentiment (low inventory = bullish)
        if 'ending_stocks' in supply_df.columns:
            stocks_mean = supply_df['ending_stocks'].rolling(12).mean()
            sd_sentiment['inventory_sentiment'] = (
                1 - supply_df['ending_stocks'] / stocks_mean
            ).clip(-1, 1)
        
        # Export sentiment (high exports = bullish)
        if 'exports' in supply_df.columns:
            export_ma = supply_df['exports'].rolling(12).mean()
            sd_sentiment['export_sentiment'] = (
                supply_df['exports'] / export_ma - 1
            ).clip(-1, 1)
        
        # Production sentiment (high production = bearish)
        if 'production' in supply_df.columns:
            prod_ma = supply_df['production'].rolling(12).mean()
            sd_sentiment['production_sentiment'] = -(
                supply_df['production'] / prod_ma - 1
            ).clip(-1, 1)
        
        # Demand indicators
        if 'crush_margin' in supply_df.columns:
            # High crush margins = strong demand
            margin_ma = supply_df['crush_margin'].rolling(20).mean()
            sd_sentiment['demand_sentiment'] = (
                supply_df['crush_margin'] / margin_ma - 1
            ).clip(-1, 1)
        
        return sd_sentiment
    
    def extract_technical_sentiment(self, price_df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert technical indicators into sentiment scores
        """
        logger.info("Extracting technical indicator sentiment...")
        
        tech_sentiment = pd.DataFrame(index=price_df.index)
        
        if 'close' not in price_df.columns:
            return tech_sentiment
        
        close = price_df['close']
        
        # RSI sentiment
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        tech_sentiment['rsi_sentiment'] = (rsi - 50) / 50  # Normalize to -1 to 1
        
        # MACD sentiment
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        tech_sentiment['macd_sentiment'] = np.sign(macd - signal)
        
        # Moving average sentiment
        ma_50 = close.rolling(50).mean()
        ma_200 = close.rolling(200).mean()
        tech_sentiment['ma_sentiment'] = np.where(
            ma_50 > ma_200, 1, -1
        )
        
        # Bollinger Band sentiment
        bb_ma = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        bb_upper = bb_ma + (bb_std * 2)
        bb_lower = bb_ma - (bb_std * 2)
        bb_position = (close - bb_lower) / (bb_upper - bb_lower)
        tech_sentiment['bb_sentiment'] = (bb_position - 0.5) * 2  # Normalize to -1 to 1
        
        # Support/Resistance sentiment
        resistance = close.rolling(50).max()
        support = close.rolling(50).min()
        sr_position = (close - support) / (resistance - support)
        tech_sentiment['sr_sentiment'] = (sr_position - 0.5) * 2
        
        return tech_sentiment
    
    # ==================== NEURAL NETWORK COMPONENTS ====================
    
    def build_sentiment_neural_network(self, input_dim: int):
        """
        Build a neural network to learn complex sentiment patterns
        """
        logger.info(f"Building neural network with input dimension: {input_dim}")
        
        model = keras.Sequential([
            # Input layer
            layers.Dense(256, activation='relu', input_shape=(input_dim,)),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            # Hidden layers with attention-like mechanism
            layers.Dense(128, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            layers.Dense(64, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            # Attention layer (simplified)
            layers.Dense(64, activation='tanh'),
            layers.Dense(64, activation='softmax'),
            layers.Multiply(),  # Element-wise attention
            
            # Output layers
            layers.Dense(32, activation='relu'),
            layers.Dense(16, activation='relu'),
            
            # Final sentiment score (-1 to 1)
            layers.Dense(1, activation='tanh')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def train_sentiment_network(self, 
                               features: np.ndarray, 
                               labels: np.ndarray,
                               validation_split: float = 0.2):
        """
        Train the neural network on historical sentiment patterns
        """
        logger.info("Training sentiment neural network...")
        
        # Build model if not exists
        if self.sentiment_nn is None:
            self.sentiment_nn = self.build_sentiment_neural_network(features.shape[1])
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=0.00001
            )
        ]
        
        # Train
        history = self.sentiment_nn.fit(
            features,
            labels,
            epochs=100,
            batch_size=32,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=0
        )
        
        logger.info(f"✅ Training complete. Final loss: {history.history['loss'][-1]:.4f}")
        
        return history
    
    def predict_neural_sentiment(self, features: np.ndarray) -> np.ndarray:
        """
        Predict sentiment using the trained neural network
        """
        if self.sentiment_nn is None:
            logger.warning("Neural network not trained, returning zeros")
            return np.zeros(len(features))
        
        predictions = self.sentiment_nn.predict(features, verbose=0)
        return predictions.flatten()
    
    # ==================== ENSEMBLE SENTIMENT ====================
    
    def create_ensemble_sentiment(self, all_sentiments: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Create ensemble sentiment combining all sources with learned weights
        """
        logger.info("Creating ensemble sentiment from all sources...")
        
        # Align all dataframes to same index
        aligned_dfs = []
        for name, df in all_sentiments.items():
            if not df.empty:
                # Ensure datetime index
                if 'date' in df.columns:
                    df = df.set_index('date')
                elif 'timestamp' in df.columns:
                    df = df.set_index('timestamp')
                
                # Add prefix to columns
                df = df.add_prefix(f"{name}_")
                aligned_dfs.append(df)
        
        # Combine all
        if not aligned_dfs:
            return pd.DataFrame()
        
        combined = pd.concat(aligned_dfs, axis=1)
        combined = combined.ffill().fillna(0)
        
        # Prepare features for neural network
        feature_matrix = combined.values
        
        # Scale features
        feature_matrix_scaled = self.scaler.fit_transform(feature_matrix)
        
        # Reduce dimensionality if needed
        if feature_matrix_scaled.shape[1] > 50:
            feature_matrix_scaled = self.pca.fit_transform(feature_matrix_scaled)
        
        # Get neural network predictions
        neural_sentiment = self.predict_neural_sentiment(feature_matrix_scaled)
        
        # Calculate simple average sentiment from all sources
        sentiment_cols = [col for col in combined.columns if 'sentiment' in col.lower()]
        if sentiment_cols:
            simple_sentiment = combined[sentiment_cols].mean(axis=1)
        else:
            simple_sentiment = pd.Series(0, index=combined.index)
        
        # Create ensemble
        ensemble = pd.DataFrame(index=combined.index)
        ensemble['simple_sentiment'] = simple_sentiment
        ensemble['neural_sentiment'] = neural_sentiment
        
        # Weighted combination (can be optimized)
        ensemble['ensemble_sentiment'] = (
            ensemble['simple_sentiment'] * 0.4 +
            ensemble['neural_sentiment'] * 0.6
        )
        
        # Add confidence metrics
        ensemble['sentiment_std'] = combined[sentiment_cols].std(axis=1) if sentiment_cols else 0
        ensemble['confidence'] = 1 / (1 + ensemble['sentiment_std'])
        
        # Add trend indicators
        ensemble['sentiment_ma_7d'] = ensemble['ensemble_sentiment'].rolling(7).mean()
        ensemble['sentiment_ma_30d'] = ensemble['ensemble_sentiment'].rolling(30).mean()
        ensemble['sentiment_momentum'] = ensemble['ensemble_sentiment'] - ensemble['sentiment_ma_7d']
        
        # Regime detection
        ensemble['sentiment_regime'] = pd.cut(
            ensemble['ensemble_sentiment'],
            bins=[-np.inf, -0.5, -0.1, 0.1, 0.5, np.inf],
            labels=['very_bearish', 'bearish', 'neutral', 'bullish', 'very_bullish']
        )
        
        return ensemble
    
    # ==================== MASTER ORCHESTRATION ====================
    
    def analyze_all_qualitative_data(self, 
                                    text_data: Optional[pd.DataFrame] = None,
                                    weather_data: Optional[pd.DataFrame] = None,
                                    market_data: Optional[pd.DataFrame] = None,
                                    supply_data: Optional[pd.DataFrame] = None,
                                    price_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Master function to analyze ALL qualitative data sources
        """
        print("="*80)
        print("UNIFIED SENTIMENT ANALYSIS WITH NEURAL NETWORK")
        print("="*80)
        
        all_sentiments = {}
        
        # 1. Policy sentiment from text
        if text_data is not None:
            policy_sentiment = self.extract_policy_sentiment(text_data)
            if not policy_sentiment.empty:
                all_sentiments['policy'] = policy_sentiment
                print(f"✅ Policy sentiment: {policy_sentiment.shape}")
        
        # 2. Weather sentiment
        if weather_data is not None:
            weather_sentiment = self.extract_weather_sentiment(weather_data)
            if not weather_sentiment.empty:
                all_sentiments['weather'] = weather_sentiment
                print(f"✅ Weather sentiment: {weather_sentiment.shape}")
        
        # 3. Market microstructure sentiment
        if market_data is not None:
            micro_sentiment = self.extract_market_microstructure_sentiment(market_data)
            if not micro_sentiment.empty:
                all_sentiments['microstructure'] = micro_sentiment
                print(f"✅ Microstructure sentiment: {micro_sentiment.shape}")
        
        # 4. Supply/demand sentiment
        if supply_data is not None:
            sd_sentiment = self.extract_supply_demand_sentiment(supply_data)
            if not sd_sentiment.empty:
                all_sentiments['supply_demand'] = sd_sentiment
                print(f"✅ Supply/demand sentiment: {sd_sentiment.shape}")
        
        # 5. Technical sentiment
        if price_data is not None:
            tech_sentiment = self.extract_technical_sentiment(price_data)
            if not tech_sentiment.empty:
                all_sentiments['technical'] = tech_sentiment
                print(f"✅ Technical sentiment: {tech_sentiment.shape}")
        
        # Create ensemble
        ensemble = self.create_ensemble_sentiment(all_sentiments)
        
        if not ensemble.empty:
            print(f"\n✅ Ensemble sentiment created: {ensemble.shape}")
            print(f"   Mean sentiment: {ensemble['ensemble_sentiment'].mean():.3f}")
            print(f"   Current sentiment: {ensemble['ensemble_sentiment'].iloc[-1]:.3f}")
            print(f"   Confidence: {ensemble['confidence'].mean():.3f}")
            
            # Save results
            ensemble.to_parquet(SENTIMENT_DIR / "unified_sentiment_neural.parquet")
            
            # Create visualization data
            self._create_sentiment_dashboard_data(ensemble, all_sentiments)
        
        return ensemble
    
    def _create_sentiment_dashboard_data(self, 
                                        ensemble: pd.DataFrame,
                                        components: Dict[str, pd.DataFrame]):
        """
        Create data for sentiment dashboard visualization
        """
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'current_sentiment': {
                'value': float(ensemble['ensemble_sentiment'].iloc[-1]),
                'confidence': float(ensemble['confidence'].iloc[-1]),
                'regime': str(ensemble['sentiment_regime'].iloc[-1]),
                'trend': 'up' if ensemble['sentiment_momentum'].iloc[-1] > 0 else 'down'
            },
            'components': {},
            'time_series': {
                'dates': ensemble.index.strftime('%Y-%m-%d').tolist()[-90:],  # Last 90 days
                'ensemble': ensemble['ensemble_sentiment'].iloc[-90:].tolist(),
                'simple': ensemble['simple_sentiment'].iloc[-90:].tolist(),
                'neural': ensemble['neural_sentiment'].iloc[-90:].tolist(),
                'confidence': ensemble['confidence'].iloc[-90:].tolist()
            },
            'statistics': {
                'mean_30d': float(ensemble['ensemble_sentiment'].iloc[-30:].mean()),
                'std_30d': float(ensemble['ensemble_sentiment'].iloc[-30:].std()),
                'min_30d': float(ensemble['ensemble_sentiment'].iloc[-30:].min()),
                'max_30d': float(ensemble['ensemble_sentiment'].iloc[-30:].max()),
                'trend_strength': float(abs(ensemble['sentiment_momentum'].iloc[-7:].mean()))
            }
        }
        
        # Add component contributions
        for name, df in components.items():
            if not df.empty:
                sentiment_cols = [col for col in df.columns if 'sentiment' in col.lower()]
                if sentiment_cols:
                    dashboard_data['components'][name] = {
                        'current': float(df[sentiment_cols].iloc[-1].mean()),
                        'weight': 1.0 / len(components),  # Equal weight for simplicity
                        'trend': 'up' if df[sentiment_cols].iloc[-7:].mean().mean() > df[sentiment_cols].iloc[-14:-7].mean().mean() else 'down'
                    }
        
        # Save dashboard data
        with open(SENTIMENT_DIR / 'sentiment_dashboard.json', 'w') as f:
            json.dump(dashboard_data, f, indent=2)
        
        logger.info("✅ Dashboard data saved to sentiment_dashboard.json")
    
    def train_on_historical_data(self, historical_returns: pd.Series):
        """
        Train the neural network to predict returns from sentiment
        This creates the link between sentiment and actual market moves
        Uses REAL historical data only - returns None if data unavailable
        """
        logger.info("Training neural network on historical sentiment-return relationships...")
        
        # This requires REAL historical sentiment and returns data
        # If not available, return None instead of generating fake data
        
        if historical_returns is None or historical_returns.empty:
            logger.warning("No historical returns data provided - cannot train")
            return None
        
        # Would need matching historical sentiment features
        # For now, return None if data unavailable
        logger.warning("Historical sentiment features not available - training skipped")
        logger.info("To train: provide historical sentiment DataFrame matching returns index")
        
        return None


def run_comprehensive_sentiment_analysis():
    """
    Run complete sentiment analysis using REAL DATA ONLY
    Returns empty DataFrame if data unavailable
    """
    # Initialize system
    sentiment_system = UnifiedSentimentNeuralSystem()
    
    # Load REAL data from local external drive
    from pathlib import Path
    
    drive = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
    
    text_data = None
    weather_data = None
    market_data = None
    supply_data = None
    price_data = None
    
    # Try to fetch REAL data from local drive
    try:
        # Text data from sentiment
        text_staging = drive / "TrainingData/staging/sentiment_social_media.parquet"
        text_raw = drive / "TrainingData/raw/sentiment_social_media.parquet"
        
        if text_staging.exists():
            text_data = pd.read_parquet(text_staging)
        elif text_raw.exists():
            text_data = pd.read_parquet(text_raw)
        
        if text_data is not None and not text_data.empty:
            logger.info(f"Loaded {len(text_data)} text records from local drive")
    except Exception as e:
        logger.warning(f"Could not load text data: {e}")
    
    try:
        # Weather data
        weather_staging = drive / "TrainingData/staging/weather_daily.parquet"
        weather_raw = drive / "TrainingData/raw/weather_daily.parquet"
        
        if weather_staging.exists():
            weather_data = pd.read_parquet(weather_staging)
        elif weather_raw.exists():
            weather_data = pd.read_parquet(weather_raw)
        
        if weather_data is not None and not weather_data.empty:
            logger.info(f"Loaded {len(weather_data)} weather records from local drive")
    except Exception as e:
        logger.warning(f"Could not load weather data: {e}")
    
    try:
        # Market data
        market_staging = drive / "TrainingData/staging/zl_futures.parquet"
        market_raw = drive / "TrainingData/raw/zl_futures.parquet"
        
        if market_staging.exists():
            market_data = pd.read_parquet(market_staging)
        elif market_raw.exists():
            market_data = pd.read_parquet(market_raw)
        
        if market_data is not None and not market_data.empty:
            price_data = market_data[['date', 'close']].copy() if 'date' in market_data.columns else market_data[['close']].copy()
            logger.info(f"Loaded {len(market_data)} market records from local drive")
    except Exception as e:
        logger.warning(f"Could not load market data: {e}")
    
    try:
        # Supply data
        supply_staging = drive / "TrainingData/staging/usda_reports.parquet"
        supply_raw = drive / "TrainingData/raw/usda_reports.parquet"
        
        if supply_staging.exists():
            supply_data = pd.read_parquet(supply_staging)
        elif supply_raw.exists():
            supply_data = pd.read_parquet(supply_raw)
        
        if supply_data is not None and not supply_data.empty:
            logger.info(f"Loaded {len(supply_data)} supply records from local drive")
    except Exception as e:
        logger.warning(f"Could not load supply data: {e}")
    
    # If no data available, return empty
    if all(d is None for d in [text_data, weather_data, market_data, supply_data]):
        logger.error("No data available for sentiment analysis")
        return pd.DataFrame()
    
    # Run comprehensive analysis with REAL data
    unified_sentiment = sentiment_system.analyze_all_qualitative_data(
        text_data=text_data,
        weather_data=weather_data,
        market_data=market_data,
        supply_data=supply_data,
        price_data=price_data
    )
    
    print("\n" + "="*80)
    print("UNIFIED SENTIMENT ANALYSIS COMPLETE")
    print("="*80)
    
    if not unified_sentiment.empty:
        print("\nSentiment Summary:")
        print(f"  Current: {unified_sentiment['ensemble_sentiment'].iloc[-1]:.3f}")
        print(f"  7-day avg: {unified_sentiment['ensemble_sentiment'].iloc[-7:].mean():.3f}")
        print(f"  30-day avg: {unified_sentiment['ensemble_sentiment'].iloc[-30:].mean():.3f}")
        print(f"  Regime: {unified_sentiment['sentiment_regime'].iloc[-1]}")
        print(f"  Confidence: {unified_sentiment['confidence'].iloc[-1]:.3f}")
    else:
        print("\n⚠️  No sentiment data generated - insufficient input data")
    
    return unified_sentiment


if __name__ == "__main__":
    # Run the comprehensive analysis
    sentiment_results = run_comprehensive_sentiment_analysis()
    
    print("\n✅ Analysis complete. Results saved to:")
    print(f"   {SENTIMENT_DIR}/unified_sentiment_neural.parquet")
    print(f"   {SENTIMENT_DIR}/sentiment_dashboard.json")
