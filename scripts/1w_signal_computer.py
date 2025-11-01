#!/usr/bin/env python3
"""
1W Signal Computer (Offline, No Vertex Endpoint)
Computes: volatility_score_1w, delta_1w_vs_spot, momentum_1w_7d, short_bias_score_1w
Also computes rolled 1W forecast path (7-day ahead) for gate blending
"""

import json
import logging
import numpy as np
from datetime import datetime, timedelta
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"

def get_price_history(days=30):
    """Get recent price history for signal computation"""
    logger.info(f"Fetching price history ({days} days)...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT 
      DATE(time) as date,
      close as price
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
    ORDER BY date ASC
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        raise ValueError("No price history found")
    
    logger.info(f"Fetched {len(df)} price points")
    return df

def compute_volatility_score(prices_df):
    """Compute annualized volatility (rolling 7-day)"""
    prices = prices_df['price'].values
    returns = np.diff(prices) / prices[:-1]
    
    # 7-day rolling volatility
    if len(returns) >= 7:
        window_returns = returns[-7:]
        volatility = np.std(window_returns) * np.sqrt(252)  # Annualized
        volatility_score = min(1.0, volatility / 0.5)  # Normalize to 0-1
    else:
        volatility_score = 0.5  # Default
    
    logger.info(f"Volatility score: {volatility_score:.3f}")
    return float(volatility_score)

def compute_delta_vs_spot(prices_df):
    """Compute delta: (1W forecast - spot) / spot"""
    current_price = prices_df['price'].iloc[-1]
    
    # Simple 1W forecast: 7-day average trend
    if len(prices_df) >= 7:
        recent_prices = prices_df['price'].iloc[-7:].values
        trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        forecast_1w = current_price * (1 + trend)
    else:
        forecast_1w = current_price
    
    delta = (forecast_1w - current_price) / current_price
    
    logger.info(f"Delta vs spot: {delta:.3f}")
    return float(delta)

def compute_momentum_7d(prices_df):
    """Compute 7-day price momentum"""
    if len(prices_df) >= 7:
        price_today = prices_df['price'].iloc[-1]
        price_7d_ago = prices_df['price'].iloc[-7]
        momentum = (price_today - price_7d_ago) / price_7d_ago
    else:
        momentum = 0.0
    
    logger.info(f"Momentum 7d: {momentum:.3f}")
    return float(momentum)

def compute_short_bias_score(prices_df):
    """Compute short-term bias indicator"""
    # Simplified: based on recent trend
    if len(prices_df) >= 3:
        recent_trend = (prices_df['price'].iloc[-1] - prices_df['price'].iloc[-3]) / prices_df['price'].iloc[-3]
        # Negative trend = short bias
        short_bias = max(0.0, -recent_trend)  # 0-1 scale
    else:
        short_bias = 0.5
    
    logger.info(f"Short bias score: {short_bias:.3f}")
    return float(short_bias)

def compute_rolled_forecast_7d(prices_df):
    """Compute rolled 1W forecast path (7-day ahead)"""
    current_price = prices_df['price'].iloc[-1]
    
    # Simple forecast: use recent trend extrapolated
    if len(prices_df) >= 7:
        recent_prices = prices_df['price'].iloc[-7:].values
        daily_change = np.mean(np.diff(recent_prices) / recent_prices[:-1])
        
        # Extrapolate 7 days
        forecast_path = []
        for i in range(7):
            forecast_price = current_price * (1 + daily_change * (i + 1))
            forecast_path.append(float(forecast_price))
    else:
        # No history - use current price
        forecast_path = [float(current_price)] * 7
    
    logger.info(f"Rolled forecast 7d: {forecast_path}")
    return forecast_path

def write_signals_to_bigquery(signals, rolled_forecast, as_of_timestamp):
    """Write signals to BigQuery"""
    logger.info("Writing signals to BigQuery...")
    
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.forecasting_data_warehouse.signals_1w"
    
    rows = []
    
    # Write individual signals
    for signal_name, signal_value in signals.items():
        if signal_name != 'rolled_forecast_7d':
            rows.append({
                'as_of_timestamp': as_of_timestamp,
                'signal_name': signal_name,
                'signal_value': signal_value,
                'rolled_forecast_7d_json': None,
                'model_version': 'offline_v1',
                'source': 'offline'
            })
    
    # Write rolled forecast as JSON
    rows.append({
        'as_of_timestamp': as_of_timestamp,
        'signal_name': 'rolled_forecast_7d',
        'signal_value': None,
        'rolled_forecast_7d_json': json.dumps(rolled_forecast),  # PATCH 3: JSON string
        'model_version': 'offline_v1',
        'source': 'offline'
    })
    
    # Delete existing rows for this timestamp (idempotency)
    delete_query = f"""
    DELETE FROM `{table_id}`
    WHERE as_of_timestamp = TIMESTAMP('{as_of_timestamp}')
    """
    
    try:
        client.query(delete_query).result()
        logger.info(f"Deleted existing rows for {as_of_timestamp}")
    except Exception as e:
        logger.warning(f"Delete query failed (table may not exist yet): {e}")
    
    # Insert new rows
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        raise ValueError(f"BigQuery insert errors: {errors}")
    
    logger.info(f"Inserted {len(rows)} signal rows")
    return len(rows)

def main():
    logger.info("=" * 80)
    logger.info("1W SIGNAL COMPUTER")
    logger.info("=" * 80)
    
    try:
        # Get price history
        prices_df = get_price_history(days=30)
        
        # Compute signals
        volatility_score = compute_volatility_score(prices_df)
        delta_vs_spot = compute_delta_vs_spot(prices_df)
        momentum_7d = compute_momentum_7d(prices_df)
        short_bias = compute_short_bias_score(prices_df)
        rolled_forecast = compute_rolled_forecast_7d(prices_df)
        
        signals = {
            'volatility_score_1w': volatility_score,
            'delta_1w_vs_spot': delta_vs_spot,
            'momentum_1w_7d': momentum_7d,
            'short_bias_score_1w': short_bias
        }
        
        # Write to BigQuery
        # Use UTC timestamp in ISO format (BigQuery TIMESTAMP() accepts this)
        as_of_timestamp = datetime.utcnow().isoformat() + 'Z'  # Add Z for UTC clarity
        row_count = write_signals_to_bigquery(signals, rolled_forecast, as_of_timestamp)
        
        logger.info("=" * 80)
        logger.info("✅ SIGNAL COMPUTATION COMPLETE")
        logger.info(f"Signals: {signals}")
        logger.info(f"Rows written: {row_count}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ SIGNAL COMPUTATION FAILED")
        logger.error(f"Error: {e}")
        logger.error("=" * 80)
        raise

if __name__ == "__main__":
    main()

