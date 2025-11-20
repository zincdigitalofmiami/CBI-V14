#!/usr/bin/env python3
"""
Calculate IV30 (30-day Implied Volatility) from DataBento GLBX Options
======================================================================

Status: ENABLED for accounts with the CME options add-on (this account).  
If your account does not have the options add-on, IV30 remains disabled and the futures-based pillar is used.

Notes:
- Uses real exchange-traded options (no placeholders).  
- For ZL, use OZL.OPT (parent symbology); ES uses ES.OPT; MES uses MES.OPT.
- See docs/features/IV30_IMPLEMENTATION_SUMMARY.md for details.

Source: DataBento GLBX options for ZL (and ES) - **REQUIRES OPTIONS LICENSE**
Output: features.iv30_from_options(symbol, date, iv30, obs_count, moneyness_span, quality_flag, asof_source_time)

Method: Fit a daily volatility surface from real calls/puts (bid/ask-filtered), 
        roll to constant-maturity 30-day IV.

Guardrails:
- Discard quotes with wide spreads / stale timestamps
- Require minimum strike coverage around ATM (e.g., ±20% moneyness)
- Stamp an asof_source_time and quality_flag ∈ {ok, sparse, fail}

⚠️ CRITICAL: NO FAKE DATA ⚠️
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
import sys
from typing import Dict, Tuple, Optional
from scipy.interpolate import interp1d, CubicSpline
from scipy.optimize import minimize_scalar
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.keychain_manager import get_api_key

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/databento_options"
STAGING_DIR = EXTERNAL_DRIVE / "TrainingData/staging"
FEATURES_DIR = EXTERNAL_DRIVE / "TrainingData/features"
RAW_DIR.mkdir(parents=True, exist_ok=True)
STAGING_DIR.mkdir(parents=True, exist_ok=True)
FEATURES_DIR.mkdir(parents=True, exist_ok=True)

# Symbols to process
SYMBOLS = ['ZL', 'ES', 'MES']  # ZL, ES, and MES futures options
# Note: ZL options use OZL.OPT symbol (not ZL.OPT), ES.OPT and MES.OPT are accessible
OPTIONS_DATA_AVAILABLE = True  # All options are available (ZL via OZL.OPT)

# Quality thresholds
MAX_SPREAD_PCT = 0.20  # Discard if bid-ask spread > 20% of mid price
MAX_STALE_SECONDS = 300  # Discard quotes older than 5 minutes
MIN_MONEYNESS_COVERAGE = 0.20  # Require ±20% moneyness coverage around ATM
MIN_OBSERVATIONS = 5  # Minimum observations for reliable IV calculation

# Target maturity for IV30
TARGET_DAYS_TO_EXPIRY = 30

def get_databento_client():
    """
    Get DataBento Live API client.
    
    IMPORTANT: Use Live API only - Historical API downloads cost money.
    Live API includes historical data via intraday replay (last 24 hours)
    and weekly session replay for GLBX.MDP3 MBO/definition schemas.
    """
    import os
    import subprocess
    
    try:
        import databento as db
    except ImportError:
        logger.error("❌ databento package not installed. Run: pip install databento")
        return None
    
    # Try multiple sources for API key (in order of preference)
    api_key = None
    
    # 1. Try macOS keychain first (most reliable)
    keychain_locations = [
        ("databento", "databento_api_key"),
        ("default", "cbi-v14.DATABENTO_API_KEY"),
    ]
    for account, service in keychain_locations:
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-w", "-a", account, "-s", service],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                api_key = result.stdout.strip()
                logger.debug(f"Found API key in keychain: {account}/{service}")
                break
        except Exception as e:
            logger.debug(f"Keychain lookup failed for {account}/{service}: {e}")
            continue
    
    # 2. Try environment variable
    if not api_key:
        api_key = os.environ.get("DATABENTO_API_KEY")
        if api_key:
            logger.debug("Found API key in environment variable")
    
    # 3. Try keychain manager (may log warnings, so do after direct keychain)
    if not api_key:
        try:
            api_key = get_api_key("DATABENTO_API_KEY")
            if api_key:
                logger.debug("Found API key via keychain manager")
        except:
            pass
    
    # 4. Try file
    if not api_key:
        key_file = Path.home() / ".databento.key"
        if key_file.exists():
            try:
                api_key = key_file.read_text().strip()
                if api_key:
                    logger.debug("Found API key in ~/.databento.key")
            except:
                pass
    
    if not api_key:
        logger.error("❌ DATABENTO_API_KEY not found in any source")
        logger.error("   Set it: security add-generic-password -a databento -s databento_api_key -w 'YOUR_KEY' -U")
        return None
    
    # Validate key format (should be 32 characters starting with 'db-')
    if len(api_key) != 32 or not api_key.startswith('db-'):
        logger.warning(f"⚠️  API key format looks unusual (length: {len(api_key)}, starts with: {api_key[:3]})")
    
    try:
        # Use Live API (not Historical) - Live API includes historical data via replay
        client = db.Live(key=api_key)
        logger.info("✅ DataBento Live client initialized")
        logger.info("   Using Live API with intraday replay for historical data (no download costs)")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to initialize DataBento Live client: {e}")
        logger.error("   Check API key validity at: https://databento.com/portal/api-keys")
        return None

def fetch_options_data(symbol: str, date: str, client) -> pd.DataFrame:
    """
    Fetch options data from DataBento GLBX using Live API with extended historical replay.
    
    IMPORTANT: Uses Live API (not Historical downloads) to avoid download costs.
    CME Globex MDP 3.0 Standard plan includes 15 years of historical data (2010-2025).
    Uses extended replay for historical dates via Live API.
    
    Args:
        symbol: Root symbol (ZL or ES)
        date: Date string (YYYY-MM-DD) - can be any date from 2010-06-06 to present
        client: DataBento Live client
        
    Returns:
        DataFrame with options quotes (calls/puts) including bid/ask
    """
    import pandas as pd
    import time
    from datetime import datetime, timedelta
    
    try:
        # Convert date to timestamp for replay
        target_date = pd.to_datetime(date)
        # Use start of trading day
        # For CME Globex, trading day starts 6:00 PM CT previous day = 00:00 UTC next day
        start_time = target_date.replace(hour=0, minute=0, second=0)
        
        records = []
        replay_completed = False
        error_occurred = False
        
        # Callback to collect records
        def collect_record(record):
            nonlocal records, replay_completed, error_occurred
            
            # Check for errors
            if hasattr(record, 'err'):
                logger.warning(f"Error from gateway: {record.err}")
                error_occurred = True
                return
            
            # Check for system messages
            if hasattr(record, 'msg'):
                if hasattr(record, 'code') and record.code == 3:  # REPLAY_COMPLETED
                    replay_completed = True
                    logger.debug("Replay completed")
                return
            
            # Process records based on schema type
            rec_dict = {
                'ts_event': getattr(record, 'ts_event', None),
                'symbol': getattr(record, 'symbol', None),
                'instrument_id': getattr(record, 'instrument_id', None),
            }
            
            # MBO schema (bid/ask quotes) - prices are in fixed-point (1e-9)
            if hasattr(record, 'bid_px_00') or hasattr(record, 'ask_px_00'):
                if hasattr(record, 'bid_px_00') and record.bid_px_00:
                    rec_dict['bid'] = float(record.bid_px_00) / 1e9
                    rec_dict['bid_size'] = getattr(record, 'bid_size_00', None)
                if hasattr(record, 'ask_px_00') and record.ask_px_00:
                    rec_dict['ask'] = float(record.ask_px_00) / 1e9
                    rec_dict['ask_size'] = getattr(record, 'ask_size_00', None)
                
                # Calculate mid price
                if 'bid' in rec_dict and 'ask' in rec_dict:
                    rec_dict['mid_price'] = (rec_dict['bid'] + rec_dict['ask']) / 2
            
            # OHLCV schema (daily bars)
            elif hasattr(record, 'open') or hasattr(record, 'close'):
                rec_dict['open'] = float(record.open) / 1e9 if hasattr(record, 'open') and record.open else None
                rec_dict['high'] = float(record.high) / 1e9 if hasattr(record, 'high') and record.high else None
                rec_dict['low'] = float(record.low) / 1e9 if hasattr(record, 'low') and record.low else None
                rec_dict['close'] = float(record.close) / 1e9 if hasattr(record, 'close') and record.close else None
                rec_dict['volume'] = getattr(record, 'volume', None)
                
                # Use close as mid price for OHLCV
                if rec_dict['close']:
                    rec_dict['mid_price'] = rec_dict['close']
            
            # Trades schema
            elif hasattr(record, 'price'):
                rec_dict['price'] = float(record.price) / 1e9 if record.price else None
                rec_dict['size'] = getattr(record, 'size', None)
                if rec_dict['price']:
                    rec_dict['mid_price'] = rec_dict['price']
            
            # Open interest (if available in any schema)
            if hasattr(record, 'open_interest'):
                rec_dict['open_interest'] = record.open_interest
            
            # Only add if we have price data
            if 'mid_price' in rec_dict and rec_dict['mid_price']:
                records.append(rec_dict)
        
        # Add callback
        client.add_callback(collect_record)
        
        # Try multiple schemas (MBO may not be authorized, fallback to ohlcv-1d or trades)
        # GLBX.MDP3 Standard plan supports extended historical replay (15 years)
        schemas_to_try = ['ohlcv-1d', 'trades', 'mbo']  # Try ohlcv-1d first (most likely authorized)
        
        subscribed = False
        schema_used = None
        
        for schema_name in schemas_to_try:
            try:
                replay_start = start_time if start_time > pd.Timestamp.now() - pd.Timedelta(days=1) else start_time
                
                # ZL options use OZL.OPT symbol (not ZL.OPT)
                options_symbol = "OZL.OPT" if symbol == "ZL" else f"{symbol}.OPT"
                
                client.subscribe(
                    dataset='GLBX.MDP3',
                    schema=schema_name,
                    stype_in='parent',
                    symbols=options_symbol,  # Options symbology (OZL.OPT for ZL)
                    start=replay_start,  # Replay from start of day (supports full 15-year history)
                )
                logger.info(f"Subscribed to {options_symbol} {schema_name} data for {date}")
                subscribed = True
                schema_used = schema_name
                break
            except Exception as schema_error:
                if 'Not authorized' in str(schema_error) or 'not authorized' in str(schema_error).lower():
                    logger.debug(f"Schema {schema_name} not authorized, trying next...")
                    continue
                else:
                    raise
        
        if not subscribed:
            logger.warning(f"⚠️  Could not subscribe to any authorized schema for {symbol}.OPT")
            try:
                client.stop()
            except:
                pass
            return pd.DataFrame()
        
        try:
            # Start session
            client.start()
            
            # Wait for replay to complete or timeout
            timeout = 60  # 60 second timeout
            start_time_wait = time.time()
            
            while not replay_completed and not error_occurred:
                if time.time() - start_time_wait > timeout:
                    logger.warning(f"Timeout waiting for replay after {timeout} seconds")
                    break
                time.sleep(0.1)  # Small delay to avoid busy waiting
            
            # Stop session
            client.stop()
            
            # Wait a moment for final records
            time.sleep(1)
            
        except Exception as e:
            logger.warning(f"⚠️  Live API subscription failed for {schema_used}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            try:
                client.stop()
            except:
                pass
        
        if not records:
            logger.warning(f"⚠️  No options data found for {symbol} on {date}")
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        
        # Remove duplicates (keep latest for each symbol)
        if 'ts_event' in df.columns:
            df = df.sort_values('ts_event').drop_duplicates(subset=['symbol'], keep='last')
        
        # Parse option details from symbol
        # Format varies: "ZL 250120C005000" or "ES240120C5000" etc.
        df['option_type'] = df['symbol'].str.extract(r'([CP])(\d+)', expand=False)[0]  # C or P
        df['expiry_str'] = df['symbol'].str.extract(r'([CP])(\d{6})', expand=False)[1]  # YYMMDD
        
        # Extract strike price
        strike_match = df['symbol'].str.extract(r'([CP])(\d{6})([CP])(\d+\.?\d*)', expand=False)
        if strike_match[3].notna().any():
            df['strike'] = strike_match[3].astype(float)
        else:
            # Fallback: extract last number sequence
            df['strike'] = df['symbol'].str.extract(r'(\d+\.?\d*)$').astype(float)
        
        logger.info(f"✅ Collected {len(df)} options records for {symbol} on {date}")
        return df
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to fetch options for {symbol} on {date}: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        try:
            client.stop()
        except:
            pass
        return pd.DataFrame()

def filter_quality_quotes(df: pd.DataFrame, spot_price: float, timestamp: datetime) -> pd.DataFrame:
    """
    Filter options quotes based on quality guardrails.
    Uses bid/ask if available, otherwise falls back to high/low.
    
    Args:
        df: Options quotes DataFrame
        spot_price: Current spot/futures price
        timestamp: Current timestamp for staleness check
        
    Returns:
        Filtered DataFrame with quality metrics
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Calculate mid price and spread (prefer bid/ask, fallback to high/low)
    if 'bid' in df.columns and 'ask' in df.columns:
        df['bid'] = pd.to_numeric(df['bid'], errors='coerce')
        df['ask'] = pd.to_numeric(df['ask'], errors='coerce')
        df['mid_price'] = (df['bid'] + df['ask']) / 2
        df['spread'] = df['ask'] - df['bid']
    elif 'high' in df.columns and 'low' in df.columns:
        df['mid_price'] = (df['high'] + df['low']) / 2
        df['spread'] = df['high'] - df['low']
    elif 'close' in df.columns:
        df['mid_price'] = df['close']
        df['spread'] = 0  # No spread info, will filter later
    else:
        logger.warning("⚠️  No price data available for quality filtering")
        return pd.DataFrame()
    
    df['spread_pct'] = df['spread'] / (df['mid_price'] + 1e-10)  # Avoid division by zero
    
    # Filter 1: Discard wide spreads
    df = df[df['spread_pct'] <= MAX_SPREAD_PCT].copy()
    
    # Filter 2: Discard stale timestamps
    if 'ts_event' in df.columns:
        df['ts_event_dt'] = pd.to_datetime(df['ts_event'], unit='ns', errors='coerce')
        if df['ts_event_dt'].notna().any():
            df['age_seconds'] = (timestamp - df['ts_event_dt']).dt.total_seconds()
            df = df[df['age_seconds'] <= MAX_STALE_SECONDS].copy()
    
    # Filter 3: Require valid strike and option type
    df = df[df['strike'].notna()].copy()
    df = df[df['option_type'].isin(['C', 'P'])].copy()
    
    # Filter 4: Require positive prices
    df = df[df['mid_price'] > 0].copy()
    
    # Calculate moneyness
    df['moneyness'] = df['strike'] / spot_price
    
    # Calculate bid-ask tightness (weighting factor)
    if 'bid' in df.columns and 'ask' in df.columns:
        df['bid_ask_tightness'] = 1.0 / (1.0 + df['spread_pct'])  # Tighter = higher weight
    else:
        df['bid_ask_tightness'] = 1.0  # Default weight if no bid/ask
    
    return df

def calculate_iv_from_black_scholes(
    option_price: float,
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    option_type: str
) -> Optional[float]:
    """
    Calculate implied volatility using Black-Scholes model.
    
    Args:
        option_price: Market price of the option
        spot: Current spot/futures price
        strike: Strike price
        time_to_expiry: Time to expiry in years
        risk_free_rate: Risk-free rate (annualized)
        option_type: 'C' for call, 'P' for put
        
    Returns:
        Implied volatility (annualized) or None if calculation fails
    """
    from scipy.stats import norm
    
    if time_to_expiry <= 0 or option_price <= 0:
        return None
    
    def bs_price(vol):
        """Black-Scholes option price."""
        d1 = (np.log(spot / strike) + (risk_free_rate + 0.5 * vol**2) * time_to_expiry) / (vol * np.sqrt(time_to_expiry))
        d2 = d1 - vol * np.sqrt(time_to_expiry)
        
        if option_type == 'C':
            price = spot * norm.cdf(d1) - strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
        else:  # Put
            price = strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) - spot * norm.cdf(-d1)
        
        return price
    
    # Solve for IV using Brent's method
    try:
        result = minimize_scalar(
            lambda vol: abs(bs_price(vol) - option_price),
            bounds=(0.01, 5.0),  # IV between 1% and 500%
            method='bounded'
        )
        
        if result.success and 0.01 <= result.x <= 5.0:
            return result.x
        else:
            return None
    except:
        return None

def parse_expiry_from_symbol(symbol: str) -> Optional[datetime]:
    """
    Parse expiry date from option symbol.
    Formats: "ZL 250120C005000" (YYMMDD), "ES240120C5000", etc.
    
    Returns:
        Expiry datetime or None
    """
    try:
        # Try YYMMDD format (6 digits after C/P)
        match = pd.Series([symbol]).str.extract(r'([CP])(\d{6})', expand=False)
        if match[1].notna().any():
            expiry_str = match[1].iloc[0]
            # Parse YYMMDD
            year = 2000 + int(expiry_str[:2])
            month = int(expiry_str[2:4])
            day = int(expiry_str[4:6])
            return datetime(year, month, day)
    except:
        pass
    return None

def fit_volatility_surface(
    df: pd.DataFrame,
    spot_price: float,
    current_date: datetime
) -> Tuple[Optional[float], int, float, str]:
    """
    Fit volatility surface using cubic spline interpolation and extract 30-day IV.
    Weighted by open interest and bid-ask tightness as recommended.
    
    Args:
        df: Filtered options quotes DataFrame
        spot_price: Current spot/futures price
        current_date: Current date for time-to-expiry calculation
        
    Returns:
        Tuple of (iv30, obs_count, moneyness_span, quality_flag)
    """
    if df.empty:
        return None, 0, 0.0, 'fail'
    
    # Calculate time to expiry for each option
    df['expiry_date'] = df['symbol'].apply(parse_expiry_from_symbol)
    df['days_to_expiry'] = (df['expiry_date'] - current_date).dt.days
    
    # Filter out invalid expiries
    df = df[df['days_to_expiry'] > 0].copy()
    df = df[df['days_to_expiry'] <= 365].copy()  # Within 1 year
    
    if df.empty:
        return None, 0, 0.0, 'fail'
    
    # Calculate IV for each option
    risk_free_rate = 0.05  # 5% risk-free rate (can be fetched from FRED)
    ivs = []
    
    for _, row in df.iterrows():
        iv = calculate_iv_from_black_scholes(
            option_price=row['mid_price'],
            spot=spot_price,
            strike=row['strike'],
            time_to_expiry=row['days_to_expiry'] / 365.0,
            risk_free_rate=risk_free_rate,
            option_type=row['option_type']
        )
        if iv is not None and 0.01 <= iv <= 5.0:  # Reasonable IV bounds
            weight = 1.0
            # Weight by open interest if available
            if 'open_interest' in row and pd.notna(row['open_interest']) and row['open_interest'] > 0:
                weight *= np.log1p(row['open_interest'])  # Log scale to avoid extreme weights
            # Weight by bid-ask tightness
            if 'bid_ask_tightness' in row:
                weight *= row['bid_ask_tightness']
            
            ivs.append({
                'iv': iv,
                'strike': row['strike'],
                'moneyness': row['moneyness'],
                'days_to_expiry': row['days_to_expiry'],
                'weight': weight
            })
    
    if not ivs:
        return None, 0, 0.0, 'fail'
    
    iv_df = pd.DataFrame(ivs)
    
    # Filter for options near 30-day expiry (20-40 day window)
    iv_df_30d = iv_df[
        (iv_df['days_to_expiry'] >= TARGET_DAYS_TO_EXPIRY - 10) &
        (iv_df['days_to_expiry'] <= TARGET_DAYS_TO_EXPIRY + 10)
    ].copy()
    
    if iv_df_30d.empty:
        # Interpolate to 30-day using cubic spline if we have enough data
        if len(iv_df) >= 4:
            # Group by moneyness and interpolate across time
            # Use cubic spline for smooth interpolation
            try:
                # Get unique expiries and average IV per expiry (weighted)
                expiry_groups = iv_df.groupby('days_to_expiry').apply(
                    lambda g: np.average(g['iv'], weights=g['weight'])
                ).reset_index()
                expiry_groups.columns = ['days_to_expiry', 'iv_avg']
                expiry_groups = expiry_groups.sort_values('days_to_expiry')
                
                if len(expiry_groups) >= 2:
                    # Use cubic spline interpolation
                    cs = CubicSpline(
                        expiry_groups['days_to_expiry'],
                        expiry_groups['iv_avg'],
                        bc_type='natural'  # Natural boundary conditions
                    )
                    iv_30d = float(cs(TARGET_DAYS_TO_EXPIRY))
                else:
                    # Fallback to linear
                    interp_func = interp1d(
                        expiry_groups['days_to_expiry'],
                        expiry_groups['iv_avg'],
                        kind='linear',
                        fill_value='extrapolate',
                        bounds_error=False
                    )
                    iv_30d = float(interp_func(TARGET_DAYS_TO_EXPIRY))
            except Exception as e:
                logger.debug(f"Cubic spline interpolation failed: {e}, using linear")
                # Fallback to linear interpolation
                interp_func = interp1d(
                    iv_df['days_to_expiry'],
                    iv_df['iv'],
                    kind='linear',
                    fill_value='extrapolate',
                    bounds_error=False
                )
                iv_30d = float(interp_func(TARGET_DAYS_TO_EXPIRY))
        else:
            return None, len(ivs), 0.0, 'sparse'
    else:
        # Use ATM (moneyness closest to 1.0) for IV30, weighted average if multiple
        iv_df_30d['atm_distance'] = abs(iv_df_30d['moneyness'] - 1.0)
        # Get options within 5% of ATM
        atm_options = iv_df_30d[iv_df_30d['atm_distance'] <= 0.05]
        
        if not atm_options.empty:
            # Weighted average of ATM options
            iv_30d = np.average(atm_options['iv'], weights=atm_options['weight'])
        else:
            # Use closest to ATM
            closest_idx = iv_df_30d['atm_distance'].idxmin()
            iv_30d = iv_df_30d.loc[closest_idx, 'iv']
    
    # Calculate moneyness span
    moneyness_span = iv_df['moneyness'].max() - iv_df['moneyness'].min()
    
    # Check quality
    obs_count = len(ivs)
    atm_coverage = len(iv_df[(iv_df['moneyness'] >= 0.8) & (iv_df['moneyness'] <= 1.2)])
    
    if obs_count < MIN_OBSERVATIONS:
        quality_flag = 'fail'
    elif atm_coverage < 3 or moneyness_span < MIN_MONEYNESS_COVERAGE:
        quality_flag = 'sparse'
    else:
        quality_flag = 'ok'
    
    return iv_30d, obs_count, moneyness_span, quality_flag

def get_spot_price(symbol: str, date: str, client=None) -> Optional[float]:
    """
    Get spot/futures price for a symbol on a given date.
    Tries multiple sources: staging files, DataBento Live API, Yahoo staging.
    
    Args:
        symbol: Root symbol (ZL or ES)
        date: Date string (YYYY-MM-DD)
        client: Optional DataBento Live client for fetching if staging unavailable
        
    Returns:
        Spot price or None
    """
    target_date = pd.to_datetime(date).date()
    
    # Method 1: Try staging files (multiple possible names)
    staging_patterns = [
        f"{symbol.lower()}_daily_aggregated.parquet",
        f"{symbol.lower()}_daily.parquet",
        f"yahoo_{symbol.lower()}.parquet",
        f"es_daily.parquet" if symbol == 'ES' else None,
        f"mes_daily_aggregated.parquet" if symbol == 'ES' else None,
    ]
    
    for pattern in staging_patterns:
        if pattern is None:
            continue
        staging_file = STAGING_DIR / pattern
        if staging_file.exists():
            try:
                df = pd.read_parquet(staging_file)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date']).dt.date
                    row = df[df['date'] == target_date]
                    if not row.empty:
                        # Try different column names for close price
                        price_cols = [
                            'close',
                            'databento_close',
                            f'{symbol.lower()}_close',
                            f'yahoo_{symbol.lower()}_close',
                            'es_close' if symbol == 'ES' else None,
                            'mes_close' if symbol == 'ES' else None,
                        ]
                        for col in price_cols:
                            if col and col in row.columns and pd.notna(row[col].iloc[0]):
                                price = float(row[col].iloc[0])
                                if price > 0:
                                    logger.debug(f"Found spot price from {pattern}: {price}")
                                    return price
            except Exception as e:
                logger.debug(f"Failed to load from {pattern}: {e}")
                continue
    
    # Method 2: Fetch from DataBento Live API if client provided
    if client:
        try:
            import databento as db
            from datetime import datetime
            
            # Use Historical API for metadata/queries (free, no download)
            hist_client = db.Historical(client._key if hasattr(client, '_key') else None)
            
            # Get daily OHLCV for the date
            start_time = pd.to_datetime(date).replace(hour=0, minute=0, second=0)
            end_time = start_time + pd.Timedelta(days=1)
            
            data = hist_client.timeseries.get_range(
                dataset='GLBX.MDP3',
                symbols=[f"{symbol}.FUT"],
                schema='ohlcv-1d',
                start=start_time.strftime('%Y-%m-%d'),
                end=end_time.strftime('%Y-%m-%d'),
                stype_in='parent'
            )
            
            # Convert to DataFrame
            records = []
            for record in data:
                if hasattr(record, 'close'):
                    records.append({
                        'date': pd.to_datetime(record.ts_event, unit='ns').date(),
                        'close': float(record.close) / 1e9 if record.close else None,  # Convert from fixed-point
                    })
            
            if records:
                df = pd.DataFrame(records)
                row = df[df['date'] == target_date]
                if not row.empty and pd.notna(row['close'].iloc[0]):
                    price = float(row['close'].iloc[0])
                    if price > 0:
                        logger.debug(f"Found spot price from DataBento: {price}")
                        return price
        except Exception as e:
            logger.debug(f"Failed to fetch from DataBento: {e}")
    
    logger.warning(f"⚠️  No spot price found for {symbol} on {date}")
    return None

def calculate_iv30_for_date(symbol: str, date: str, client) -> Dict:
    """
    Calculate IV30 for a symbol on a specific date.
    
    Args:
        symbol: Root symbol (ZL or ES)
        date: Date string (YYYY-MM-DD)
        client: DataBento client
        
    Returns:
        Dictionary with IV30 calculation results
    """
    logger.info(f"Calculating IV30 for {symbol} on {date}")

    if not OPTIONS_DATA_AVAILABLE:
        logger.warning(
            "❌ CME options data not available on current plan – IV30 requires CME options add-on."
        )
        return {
            'symbol': symbol,
            'date': date,
            'iv30': None,
            'obs_count': 0,
            'moneyness_span': 0.0,
            'quality_flag': 'fail',
            'asof_source_time': datetime.now().isoformat(),
            'note': 'cme_options_license_required'
        }
    
    # Get spot price (try staging first, then DataBento if needed)
    spot_price = get_spot_price(symbol, date, client)
    if spot_price is None:
        logger.warning(f"⚠️  No spot price available for {symbol} on {date}")
        return {
            'symbol': symbol,
            'date': date,
            'iv30': None,
            'obs_count': 0,
            'moneyness_span': 0.0,
            'quality_flag': 'fail',
            'asof_source_time': datetime.now().isoformat()
        }
    
    # Fetch options data
    options_df = fetch_options_data(symbol, date, client)
    if options_df.empty:
        logger.warning(f"⚠️  No options data for {symbol} on {date}")
        return {
            'symbol': symbol,
            'date': date,
            'iv30': None,
            'obs_count': 0,
            'moneyness_span': 0.0,
            'quality_flag': 'fail',
            'asof_source_time': datetime.now().isoformat()
        }
    
    # Filter quality quotes
    timestamp = pd.to_datetime(date)
    filtered_df = filter_quality_quotes(options_df, spot_price, timestamp)
    
    if filtered_df.empty:
        logger.warning(f"⚠️  No quality quotes for {symbol} on {date} after filtering")
        return {
            'symbol': symbol,
            'date': date,
            'iv30': None,
            'obs_count': 0,
            'moneyness_span': 0.0,
            'quality_flag': 'fail',
            'asof_source_time': datetime.now().isoformat()
        }
    
    # Fit volatility surface and extract IV30
    iv30, obs_count, moneyness_span, quality_flag = fit_volatility_surface(
        filtered_df, spot_price, timestamp
    )
    
    return {
        'symbol': symbol,
        'date': date,
        'iv30': iv30,
        'obs_count': obs_count,
        'moneyness_span': moneyness_span,
        'quality_flag': quality_flag,
        'asof_source_time': datetime.now().isoformat()
    }

def main():
    """Main function to calculate IV30 for all symbols and dates."""
    logger.info("="*80)
    logger.info("IV30 CALCULATION FROM DATABENTO OPTIONS")
    logger.info("="*80)

    if not OPTIONS_DATA_AVAILABLE:
        logger.error("❌ CME options license not enabled – cannot compute IV30.")
        logger.error("   Upgrade DataBento plan with CME options add-on to enable IV30 pipeline.")
        return 1
    
    # Get DataBento client
    client = get_databento_client()
    if not client:
        logger.error("❌ Cannot proceed without DataBento client")
        return 1
    
    # Date range: Full 15 years available (June 6, 2010 - present)
    # CME Globex MDP 3.0 Standard plan includes 15 years of historical data
    end_date = datetime.now().date()
    start_date = datetime(2010, 6, 6).date()  # Historical data starts June 6, 2010
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    logger.info(f"Historical date range: {start_date} to {end_date} (~15 years)")
    logger.info(f"Total days to process: {len(date_range)}")
    
    # Calculate IV30 for each symbol and date
    results = []
    
    for symbol in SYMBOLS:
        logger.info(f"\nProcessing {symbol}...")
        
        for date in date_range:
            date_str = date.strftime('%Y-%m-%d')
            result = calculate_iv30_for_date(symbol, date_str, client)
            results.append(result)
            
            if result['quality_flag'] == 'ok':
                logger.info(f"  ✅ {date_str}: IV30={result['iv30']:.4f}, quality={result['quality_flag']}")
            elif result['quality_flag'] == 'sparse':
                logger.warning(f"  ⚠️  {date_str}: IV30={result['iv30']:.4f}, quality={result['quality_flag']}")
            else:
                logger.debug(f"  ❌ {date_str}: quality={result['quality_flag']}")
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Save to features directory
    output_file = FEATURES_DIR / "iv30_from_options.parquet"
    df.to_parquet(output_file, index=False)
    
    logger.info(f"\n✅ Saved IV30 data: {output_file}")
    logger.info(f"   Rows: {len(df)}")
    logger.info(f"   Quality breakdown:")
    logger.info(f"     ok: {len(df[df['quality_flag'] == 'ok'])}")
    logger.info(f"     sparse: {len(df[df['quality_flag'] == 'sparse'])}")
    logger.info(f"     fail: {len(df[df['quality_flag'] == 'fail'])}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
