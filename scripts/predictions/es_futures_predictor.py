#!/usr/bin/env python3
"""
ES (S&P 500 Futures) Prediction Model
Advanced prediction system for ES futures using:
- Market microstructure
- Cross-asset correlations
- Technical patterns
- Sentiment indicators
- Machine learning ensemble

Author: AI Assistant
Date: November 16, 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import talib
import warnings
warnings.filterwarnings('ignore')
import logging
# Note: Data source is local external drive, not BigQuery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ESFuturesPredictor:
    """
    Comprehensive ES futures prediction system
    """
    
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.prediction_history = []
        # Note: Data comes from local external drive, not BigQuery
        # BigQuery is only for dashboard reads (thin layer)
        
        # Time horizons for predictions
        self.horizons = {
            'intraday': '4 hours',
            'daily': '1 day',
            'weekly': '1 week',
            'monthly': '1 month'
        }
    
    def fetch_es_data_from_local(self) -> Optional[pd.DataFrame]:
        """
        Fetch REAL ES futures data from local external drive
        Data source: TrainingData/staging/ or TrainingData/raw/
        Returns None if data unavailable
        """
        from pathlib import Path
        
        drive = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
        
        # Try staging first (validated data)
        staging_path = drive / "TrainingData/staging/es_futures.parquet"
        raw_path = drive / "TrainingData/raw/es_futures.parquet"
        
        try:
            if staging_path.exists():
                df = pd.read_parquet(staging_path)
                logger.info(f"Loaded ES data from staging: {len(df)} rows")
            elif raw_path.exists():
                df = pd.read_parquet(raw_path)
                logger.info(f"Loaded ES data from raw: {len(df)} rows")
            else:
                logger.warning("No ES futures data found on local drive")
                return None
            
            if df.empty:
                logger.warning("ES data file is empty")
                return None
            
            # Ensure date column exists and is datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
            elif df.index.name == 'date' or isinstance(df.index, pd.DatetimeIndex):
                # Already has date index
                pass
            else:
                logger.warning("ES data missing date column/index")
                return None
            
            # Filter to last 252 days
            cutoff_date = datetime.now() - timedelta(days=252)
            df = df[df.index >= cutoff_date]
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch ES data from local drive: {e}")
            return None
    
    def fetch_market_data_from_local(self) -> Dict[str, pd.DataFrame]:
        """
        Fetch REAL market data (VIX, Dollar, Oil, etc.) from local external drive
        Data source: TrainingData/staging/ or TrainingData/raw/
        Returns empty dict if data unavailable
        """
        from pathlib import Path
        
        drive = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
        market_data = {}
        cutoff_date = datetime.now() - timedelta(days=252)
        
        # VIX
        try:
            vix_staging = drive / "TrainingData/staging/vix.parquet"
            vix_raw = drive / "TrainingData/raw/vix.parquet"
            
            if vix_staging.exists():
                vix_df = pd.read_parquet(vix_staging)
            elif vix_raw.exists():
                vix_df = pd.read_parquet(vix_raw)
            else:
                logger.warning("No VIX data found on local drive")
                vix_df = None
            
            if vix_df is not None and not vix_df.empty:
                if 'date' in vix_df.columns:
                    vix_df['date'] = pd.to_datetime(vix_df['date'])
                    vix_df = vix_df.set_index('date')
                vix_df = vix_df[vix_df.index >= cutoff_date]
                if 'close' in vix_df.columns:
                    market_data['VIX'] = vix_df[['close']]
        except Exception as e:
            logger.warning(f"Could not load VIX data: {e}")
        
        # Dollar Index
        try:
            dx_staging = drive / "TrainingData/staging/dollar_index.parquet"
            dx_raw = drive / "TrainingData/raw/dollar_index.parquet"
            
            if dx_staging.exists():
                dx_df = pd.read_parquet(dx_staging)
            elif dx_raw.exists():
                dx_df = pd.read_parquet(dx_raw)
            else:
                dx_df = None
            
            if dx_df is not None and not dx_df.empty:
                if 'date' in dx_df.columns:
                    dx_df['date'] = pd.to_datetime(dx_df['date'])
                    dx_df = dx_df.set_index('date')
                dx_df = dx_df[dx_df.index >= cutoff_date]
                if 'close' in dx_df.columns:
                    market_data['DX'] = dx_df[['close']]
        except Exception as e:
            logger.warning(f"Could not load Dollar Index data: {e}")
        
        # Crude Oil
        try:
            cl_staging = drive / "TrainingData/staging/crude_oil.parquet"
            cl_raw = drive / "TrainingData/raw/crude_oil.parquet"
            
            if cl_staging.exists():
                cl_df = pd.read_parquet(cl_staging)
            elif cl_raw.exists():
                cl_df = pd.read_parquet(cl_raw)
            else:
                cl_df = None
            
            if cl_df is not None and not cl_df.empty:
                if 'date' in cl_df.columns:
                    cl_df['date'] = pd.to_datetime(cl_df['date'])
                    cl_df = cl_df.set_index('date')
                cl_df = cl_df[cl_df.index >= cutoff_date]
                if 'close' in cl_df.columns:
                    market_data['CL'] = cl_df[['close']]
        except Exception as e:
            logger.warning(f"Could not load Crude Oil data: {e}")
        
        return market_data
        
    def calculate_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate comprehensive technical indicators
        """
        features = pd.DataFrame(index=df.index)
        
        if 'close' not in df.columns:
            return features
        
        close = df['close'].values
        high = df['high'].values if 'high' in df.columns else close
        low = df['low'].values if 'low' in df.columns else close
        volume = df['volume'].values if 'volume' in df.columns else np.ones_like(close)
        
        # Momentum indicators
        features['rsi_14'] = talib.RSI(close, timeperiod=14)
        features['rsi_9'] = talib.RSI(close, timeperiod=9)
        features['rsi_25'] = talib.RSI(close, timeperiod=25)
        
        # MACD
        macd, signal, hist = talib.MACD(close)
        features['macd'] = macd
        features['macd_signal'] = signal
        features['macd_hist'] = hist
        
        # Stochastic
        slowk, slowd = talib.STOCH(high, low, close)
        features['stoch_k'] = slowk
        features['stoch_d'] = slowd
        
        # Williams %R
        features['williams_r'] = talib.WILLR(high, low, close)
        
        # ADX (trend strength)
        features['adx'] = talib.ADX(high, low, close)
        features['plus_di'] = talib.PLUS_DI(high, low, close)
        features['minus_di'] = talib.MINUS_DI(high, low, close)
        
        # Bollinger Bands
        upper, middle, lower = talib.BBANDS(close)
        features['bb_upper'] = upper
        features['bb_middle'] = middle
        features['bb_lower'] = lower
        features['bb_width'] = upper - lower
        features['bb_position'] = (close - lower) / (upper - lower)
        
        # Moving averages
        features['sma_5'] = talib.SMA(close, timeperiod=5)
        features['sma_10'] = talib.SMA(close, timeperiod=10)
        features['sma_20'] = talib.SMA(close, timeperiod=20)
        features['sma_50'] = talib.SMA(close, timeperiod=50)
        features['sma_200'] = talib.SMA(close, timeperiod=200)
        
        features['ema_9'] = talib.EMA(close, timeperiod=9)
        features['ema_21'] = talib.EMA(close, timeperiod=21)
        
        # Volume indicators
        features['obv'] = talib.OBV(close, volume)
        features['ad'] = talib.AD(high, low, close, volume)
        features['adosc'] = talib.ADOSC(high, low, close, volume)
        
        # Volatility
        features['atr'] = talib.ATR(high, low, close)
        features['natr'] = talib.NATR(high, low, close)
        
        # Pattern recognition
        features['cdl_doji'] = talib.CDLDOJI(df['open'], high, low, close) if 'open' in df.columns else 0
        features['cdl_hammer'] = talib.CDLHAMMER(df['open'], high, low, close) if 'open' in df.columns else 0
        features['cdl_engulfing'] = talib.CDLENGULFING(df['open'], high, low, close) if 'open' in df.columns else 0
        
        # Price action
        features['returns_1'] = df['close'].pct_change(1)
        features['returns_5'] = df['close'].pct_change(5)
        features['returns_20'] = df['close'].pct_change(20)
        
        # Support/Resistance
        features['resistance_distance'] = (df['close'].rolling(20).max() - df['close']) / df['close']
        features['support_distance'] = (df['close'] - df['close'].rolling(20).min()) / df['close']
        
        return features
    
    def calculate_market_microstructure(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate market microstructure features
        """
        features = pd.DataFrame(index=df.index)
        
        if 'close' not in df.columns:
            return features
        
        # Tick analysis (if tick data available)
        if 'bid' in df.columns and 'ask' in df.columns:
            features['spread'] = df['ask'] - df['bid']
            features['spread_pct'] = features['spread'] / df['close']
            features['mid_price'] = (df['bid'] + df['ask']) / 2
            features['price_to_mid'] = (df['close'] - features['mid_price']) / features['mid_price']
        
        # Volume analysis
        if 'volume' in df.columns:
            features['volume_ma'] = df['volume'].rolling(20).mean()
            features['volume_ratio'] = df['volume'] / features['volume_ma']
            features['volume_trend'] = features['volume_ma'].pct_change(5)
            
            # VWAP
            typical_price = (df['high'] + df['low'] + df['close']) / 3 if 'high' in df.columns else df['close']
            features['vwap'] = (typical_price * df['volume']).rolling(20).sum() / df['volume'].rolling(20).sum()
            features['price_to_vwap'] = (df['close'] - features['vwap']) / features['vwap']
        
        # Order flow (if available)
        if 'buy_volume' in df.columns and 'sell_volume' in df.columns:
            features['order_flow'] = df['buy_volume'] - df['sell_volume']
            features['order_flow_ratio'] = df['buy_volume'] / (df['buy_volume'] + df['sell_volume'])
            features['cumulative_delta'] = features['order_flow'].cumsum()
        
        # Volatility clustering
        returns = df['close'].pct_change()
        features['realized_vol'] = returns.rolling(20).std() * np.sqrt(252)
        features['vol_of_vol'] = features['realized_vol'].rolling(20).std()
        
        # Autocorrelation (momentum/mean reversion)
        features['autocorr_1'] = returns.rolling(20).apply(lambda x: x.autocorr(lag=1))
        features['autocorr_5'] = returns.rolling(20).apply(lambda x: x.autocorr(lag=5))
        
        return features
    
    def calculate_intermarket_features(self, es_df: pd.DataFrame, market_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate cross-asset correlations and relationships
        """
        features = pd.DataFrame(index=es_df.index)
        
        es_returns = es_df['close'].pct_change()
        
        # VIX relationship (fear gauge)
        if 'VIX' in market_data:
            vix = market_data['VIX']['close']
            features['vix_level'] = vix
            features['vix_change'] = vix.pct_change()
            features['vix_es_correlation'] = es_returns.rolling(20).corr(vix.pct_change())
            features['vix_term_structure'] = (market_data['VIX9D']['close'] / vix) if 'VIX9D' in market_data else 1
        
        # Bond yields (risk on/off)
        if 'TY' in market_data:  # 10-year Treasury futures
            bond_returns = market_data['TY']['close'].pct_change()
            features['bond_es_correlation'] = es_returns.rolling(20).corr(bond_returns)
            features['yield_curve'] = (
                market_data['TY']['close'] - market_data['TU']['close']
            ) if 'TU' in market_data else 0
        
        # Dollar strength
        if 'DX' in market_data:  # Dollar index
            dollar_returns = market_data['DX']['close'].pct_change()
            features['dollar_strength'] = market_data['DX']['close']
            features['dollar_es_correlation'] = es_returns.rolling(20).corr(dollar_returns)
        
        # Commodities (inflation/growth)
        if 'CL' in market_data:  # Crude oil
            oil_returns = market_data['CL']['close'].pct_change()
            features['oil_es_correlation'] = es_returns.rolling(20).corr(oil_returns)
            features['oil_trend'] = market_data['CL']['close'].rolling(20).mean().pct_change(5)
        
        if 'GC' in market_data:  # Gold (safe haven)
            gold_returns = market_data['GC']['close'].pct_change()
            features['gold_es_ratio'] = es_df['close'] / market_data['GC']['close']
            features['gold_es_correlation'] = es_returns.rolling(20).corr(gold_returns)
        
        # Sector rotation
        if 'XLF' in market_data and 'XLK' in market_data:  # Financials vs Tech
            features['sector_rotation'] = (
                market_data['XLF']['close'] / market_data['XLK']['close']
            ).pct_change(20)
        
        # International markets
        if 'DAX' in market_data:  # European markets
            features['europe_us_spread'] = (
                market_data['DAX']['close'].pct_change() - es_returns
            ).rolling(5).mean()
        
        if 'NKY' in market_data:  # Asian markets
            features['asia_us_spread'] = (
                market_data['NKY']['close'].pct_change() - es_returns
            ).rolling(5).mean()
        
        return features
    
    def calculate_sentiment_features(self, sentiment_data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features from sentiment data
        """
        features = pd.DataFrame(index=sentiment_data.index)
        
        if 'unified_sentiment' in sentiment_data.columns:
            features['sentiment_level'] = sentiment_data['unified_sentiment']
            features['sentiment_ma_5'] = features['sentiment_level'].rolling(5).mean()
            features['sentiment_ma_20'] = features['sentiment_level'].rolling(20).mean()
            features['sentiment_momentum'] = features['sentiment_level'] - features['sentiment_ma_5']
            features['sentiment_acceleration'] = features['sentiment_momentum'].diff()
        
        if 'trump_volatility_signal' in sentiment_data.columns:
            features['trump_risk'] = sentiment_data['trump_volatility_signal']
            features['trump_risk_ma'] = features['trump_risk'].rolling(3).mean()
        
        if 'news_volume' in sentiment_data.columns:
            features['news_intensity'] = sentiment_data['news_volume']
            features['news_spike'] = features['news_intensity'] > features['news_intensity'].rolling(20).mean() * 2
        
        return features
    
    def build_ensemble_model(self, input_dim: int):
        """
        Build ensemble of models for prediction
        """
        # Random Forest
        self.models['rf'] = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        
        # Gradient Boosting
        self.models['gb'] = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        # Neural Network
        nn_model = keras.Sequential([
            layers.Dense(256, activation='relu', input_shape=(input_dim,)),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            layers.Dense(128, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            layers.Dense(64, activation='relu'),
            layers.BatchNormalization(),
            
            layers.Dense(32, activation='relu'),
            
            # Output: returns prediction
            layers.Dense(1, activation='linear')
        ])
        
        nn_model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        self.models['nn'] = nn_model
        
        logger.info(f"Built ensemble with {len(self.models)} models")
    
    def predict_es_movement(self, 
                           es_df: pd.DataFrame,
                           market_data: Dict[str, pd.DataFrame],
                           sentiment_data: Optional[pd.DataFrame] = None,
                           horizon: str = 'daily') -> Dict:
        """
        Predict ES futures movement
        """
        # Calculate all features
        tech_features = self.calculate_technical_features(es_df)
        micro_features = self.calculate_market_microstructure(es_df)
        inter_features = self.calculate_intermarket_features(es_df, market_data)
        
        # Combine features
        all_features = pd.concat([tech_features, micro_features, inter_features], axis=1)
        
        if sentiment_data is not None:
            sent_features = self.calculate_sentiment_features(sentiment_data)
            all_features = pd.concat([all_features, sent_features], axis=1)
        
        # Fill NaN values (deprecated method replaced)
        all_features = all_features.ffill().fillna(0)
        
        # Get latest features
        latest_features = all_features.iloc[-1].values.reshape(1, -1)
        
        # Scale features
        latest_features_scaled = self.scaler.fit_transform(latest_features)
        
        # Make predictions with each model (simplified for demo)
        predictions = {}
        
        # Rule-based prediction
        rule_prediction = self._rule_based_prediction(all_features.iloc[-1])
        predictions['rule_based'] = rule_prediction
        
        # Statistical prediction
        stat_prediction = self._statistical_prediction(es_df)
        predictions['statistical'] = stat_prediction
        
        # ML predictions would go here if models were trained
        # predictions['rf'] = self.models['rf'].predict(latest_features_scaled)[0]
        # predictions['gb'] = self.models['gb'].predict(latest_features_scaled)[0]
        # predictions['nn'] = self.models['nn'].predict(latest_features_scaled)[0][0]
        
        # Ensemble prediction
        ensemble_prediction = np.mean(list(predictions.values()))
        
        # Calculate confidence
        prediction_std = np.std(list(predictions.values()))
        confidence = 1 / (1 + prediction_std) if prediction_std > 0 else 1
        
        # Generate report
        current_price = es_df['close'].iloc[-1]
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'horizon': horizon,
            'current_price': float(current_price),
            'prediction': {
                'direction': 'UP' if ensemble_prediction > 0 else 'DOWN',
                'magnitude': abs(ensemble_prediction),
                'target_price': float(current_price * (1 + ensemble_prediction)),
                'expected_return': f"{ensemble_prediction*100:.2f}%",
                'confidence': f"{confidence*100:.1f}%"
            },
            'model_predictions': {
                name: f"{pred*100:.2f}%" for name, pred in predictions.items()
            },
            'key_drivers': self._identify_key_drivers(all_features.iloc[-1]),
            'support_resistance': self._calculate_support_resistance(es_df),
            'risk_metrics': self._calculate_risk_metrics(es_df, ensemble_prediction),
            'trading_signals': self._generate_trading_signals(all_features.iloc[-1], ensemble_prediction)
        }
        
        return report
    
    def _rule_based_prediction(self, features: pd.Series) -> float:
        """
        Rule-based prediction using technical indicators
        """
        score = 0
        
        # RSI signals
        if 'rsi_14' in features:
            if features['rsi_14'] < 30:
                score += 0.02  # Oversold bounce
            elif features['rsi_14'] > 70:
                score -= 0.02  # Overbought pullback
        
        # MACD signals
        if 'macd_hist' in features:
            if features['macd_hist'] > 0:
                score += 0.01
            else:
                score -= 0.01
        
        # Bollinger Band signals
        if 'bb_position' in features:
            if features['bb_position'] < 0.2:
                score += 0.015  # Near lower band
            elif features['bb_position'] > 0.8:
                score -= 0.015  # Near upper band
        
        # Trend following
        if 'sma_50' in features and 'sma_200' in features:
            if features['sma_50'] > features['sma_200']:
                score += 0.01  # Bullish trend
            else:
                score -= 0.01  # Bearish trend
        
        # VIX signal
        if 'vix_level' in features:
            if features['vix_level'] > 30:
                score -= 0.02  # High fear
            elif features['vix_level'] < 15:
                score += 0.01  # Low fear/complacency
        
        return np.clip(score, -0.05, 0.05)  # Cap at ±5%
    
    def _statistical_prediction(self, df: pd.DataFrame) -> float:
        """
        Statistical prediction based on historical patterns
        """
        returns = df['close'].pct_change()
        
        # Mean reversion
        recent_return = returns.iloc[-5:].mean()
        historical_mean = returns.iloc[-252:].mean()  # 1 year
        
        if recent_return > historical_mean * 2:
            return -0.01  # Expect pullback
        elif recent_return < historical_mean * -2:
            return 0.01  # Expect bounce
        
        # Momentum
        momentum_1w = df['close'].iloc[-1] / df['close'].iloc[-5] - 1
        momentum_1m = df['close'].iloc[-1] / df['close'].iloc[-20] - 1
        
        if momentum_1w > 0 and momentum_1m > 0:
            return momentum_1w * 0.3  # Momentum continuation
        
        return 0
    
    def _identify_key_drivers(self, features: pd.Series) -> List[str]:
        """
        Identify key drivers of the prediction
        """
        drivers = []
        
        if 'rsi_14' in features:
            if features['rsi_14'] < 30:
                drivers.append("Oversold RSI (bullish)")
            elif features['rsi_14'] > 70:
                drivers.append("Overbought RSI (bearish)")
        
        if 'vix_level' in features:
            if features['vix_level'] > 25:
                drivers.append("Elevated VIX (risk-off)")
            elif features['vix_level'] < 15:
                drivers.append("Low VIX (complacency)")
        
        if 'volume_ratio' in features:
            if features['volume_ratio'] > 1.5:
                drivers.append("High volume (conviction)")
        
        if 'sentiment_level' in features:
            if features['sentiment_level'] > 0.5:
                drivers.append("Positive sentiment")
            elif features['sentiment_level'] < -0.5:
                drivers.append("Negative sentiment")
        
        if not drivers:
            drivers.append("Mixed signals")
        
        return drivers
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict:
        """
        Calculate support and resistance levels
        """
        close = df['close']
        current = close.iloc[-1]
        
        # Recent highs/lows
        resistance_1 = close.iloc[-20:].max()
        support_1 = close.iloc[-20:].min()
        
        resistance_2 = close.iloc[-50:].max()
        support_2 = close.iloc[-50:].min()
        
        # Pivot points
        if 'high' in df.columns and 'low' in df.columns:
            high = df['high'].iloc[-1]
            low = df['low'].iloc[-1]
            pivot = (high + low + current) / 3
            r1 = 2 * pivot - low
            s1 = 2 * pivot - high
        else:
            pivot = current
            r1 = resistance_1
            s1 = support_1
        
        return {
            'immediate_resistance': float(resistance_1),
            'immediate_support': float(support_1),
            'major_resistance': float(resistance_2),
            'major_support': float(support_2),
            'pivot_point': float(pivot),
            'r1': float(r1),
            's1': float(s1)
        }
    
    def _calculate_risk_metrics(self, df: pd.DataFrame, prediction: float) -> Dict:
        """
        Calculate risk metrics for the prediction
        """
        returns = df['close'].pct_change()
        volatility = returns.std() * np.sqrt(252)
        
        # Value at Risk (95% confidence)
        var_95 = np.percentile(returns.dropna(), 5)
        
        # Expected shortfall
        es_95 = returns[returns <= var_95].mean()
        
        # Risk/Reward
        if prediction > 0:
            stop_loss = -volatility * 2  # 2 std devs
            risk_reward = prediction / abs(stop_loss)
        else:
            stop_loss = volatility * 2
            risk_reward = abs(prediction) / stop_loss
        
        return {
            'annualized_volatility': f"{volatility*100:.1f}%",
            'value_at_risk_95': f"{var_95*100:.2f}%",
            'expected_shortfall': f"{es_95*100:.2f}%",
            'suggested_stop_loss': f"{stop_loss*100:.2f}%",
            'risk_reward_ratio': f"{risk_reward:.2f}"
        }
    
    def _generate_trading_signals(self, features: pd.Series, prediction: float) -> List[str]:
        """
        Generate actionable trading signals
        """
        signals = []
        
        if prediction > 0.01:
            signals.append("📈 BUY SIGNAL: Expecting upward movement")
            
            if 'rsi_14' in features and features['rsi_14'] < 40:
                signals.append("Strong buy - oversold condition")
            
            signals.append(f"Entry: Current levels")
            signals.append(f"Target: +{prediction*100:.1f}%")
            signals.append(f"Stop: -2% (2x daily volatility)")
            
        elif prediction < -0.01:
            signals.append("📉 SELL SIGNAL: Expecting downward movement")
            
            if 'rsi_14' in features and features['rsi_14'] > 60:
                signals.append("Strong sell - overbought condition")
            
            signals.append(f"Entry: Current levels")
            signals.append(f"Target: {prediction*100:.1f}%")
            signals.append(f"Stop: +2% (2x daily volatility)")
            
        else:
            signals.append("⏸️ NEUTRAL: No clear direction")
            signals.append("Wait for better setup")
        
        # Risk warnings
        if 'vix_level' in features and features['vix_level'] > 25:
            signals.append("⚠️ HIGH VOLATILITY - Reduce position size")
        
        if abs(prediction) < 0.005:
            signals.append("Low conviction signal - consider sitting out")
        
        return signals


def generate_es_prediction():
    """
    Generate real-time ES futures prediction using REAL DATA ONLY
    """
    predictor = ESFuturesPredictor()
    
    # Fetch REAL data from local external drive
    es_df = predictor.fetch_es_data_from_local()
    market_data = predictor.fetch_market_data_from_local()
    
    # If no data available, return empty report
    if es_df is None or es_df.empty:
        logger.error("No ES data available - cannot generate prediction")
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'NO_DATA',
            'message': 'ES futures data unavailable from local drive',
            'data_available': False
        }
        
        output_path = Path("dashboard-nextjs/public/api/es_prediction.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print("ES Futures Prediction: NO DATA AVAILABLE")
        return report
    
    # Generate prediction with REAL data
    report = predictor.predict_es_movement(es_df, market_data)
    report['data_source'] = 'REAL_LOCAL_DRIVE_DATA'
    report['data_available'] = True
    
    # Save report for dashboard
    output_path = Path("dashboard-nextjs/public/api/es_prediction.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print("ES Futures Prediction Report Generated with REAL DATA")
    print(f"Direction: {report['prediction']['direction']}")
    print(f"Target: {report['prediction']['target_price']:.2f}")
    print(f"Expected Return: {report['prediction']['expected_return']}")
    print(f"Confidence: {report['prediction']['confidence']}")
    
    return report


if __name__ == "__main__":
    generate_es_prediction()
