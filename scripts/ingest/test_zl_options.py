#!/usr/bin/env python3
"""
Test ZL Options Collection (OZL symbol)
========================================

Test if ZL options are accessible via OZL symbol (as shown in Databento catalog).
Previously tried ZL.OPT which failed - now testing OZL parent symbology.

⚠️ CRITICAL: NO FAKE DATA ⚠️
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
"""

import sys
from pathlib import Path
import subprocess
import os
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def get_api_key():
    """Get DataBento API key."""
    keychain_locations = [
        ("databento", "databento_api_key"),
        ("default", "cbi-v14.DATABENTO_API_KEY"),
    ]
    for account, service in keychain_locations:
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-w", "-a", account, "-s", service],
                capture_output=True, text=True, check=True
            )
            api_key = result.stdout.strip()
            if api_key:
                return api_key
        except:
            continue
    
    api_key = os.environ.get("DATABENTO_API_KEY")
    if api_key:
        return api_key
    
    key_file = Path.home() / ".databento.key"
    if key_file.exists():
        return key_file.read_text().strip()
    
    return None

def test_ozl_options():
    """Test OZL options access."""
    try:
        import databento as db
    except ImportError:
        logger.error("❌ databento package not installed")
        return False
    
    api_key = get_api_key()
    if not api_key:
        logger.error("❌ API key not found")
        return False
    
    # Use Historical API for timeseries queries
    client = db.Historical(key=api_key)
    
    # Test 1: Try OZL.OPT parent symbology
    logger.info("Testing OZL.OPT (parent symbology)...")
    try:
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            schema='definition',
            stype_in='parent',
            symbols=['OZL.OPT'],
            start='2024-01-01',
            end='2024-01-02',
        )
        df = data.to_df()
        if not df.empty:
            logger.info(f"✅ OZL.OPT works! Found {len(df)} definitions")
            logger.info(f"   Sample symbols: {df['symbol'].head(5).tolist()}")
            return True
        else:
            logger.warning("⚠️  OZL.OPT returned empty (might need different date range)")
    except Exception as e:
        logger.warning(f"⚠️  OZL.OPT failed: {e}")
    
    # Test 2: Try OZL parent symbology (without .OPT)
    logger.info("\nTesting OZL (parent symbology, no .OPT)...")
    try:
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            schema='definition',
            stype_in='parent',
            symbols=['OZL'],
            start='2024-01-01',
            end='2024-01-02',
        )
        df = data.to_df()
        if not df.empty:
            logger.info(f"✅ OZL works! Found {len(df)} definitions")
            logger.info(f"   Sample symbols: {df['symbol'].head(5).tolist()}")
            # Filter for options
            if 'security_type' in df.columns:
                options = df[df['security_type'] == 'OOF']
                logger.info(f"   Options (OOF): {len(options)} contracts")
            return True
        else:
            logger.warning("⚠️  OZL returned empty")
    except Exception as e:
        logger.warning(f"⚠️  OZL failed: {e}")
    
    # Test 3: Try raw symbol OZL
    logger.info("\nTesting raw symbol OZL...")
    try:
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            schema='definition',
            stype_in='raw_symbol',
            symbols=['OZL'],
            start='2024-01-01',
            end='2024-01-02',
        )
        df = data.to_df()
        if not df.empty:
            logger.info(f"✅ Raw OZL works! Found {len(df)} definitions")
            logger.info(f"   Sample symbols: {df['symbol'].head(5).tolist()}")
            return True
    except Exception as e:
        logger.warning(f"⚠️  Raw OZL failed: {e}")
    
    # Test 4: Try getting all OZL options definitions for recent date
    logger.info("\nTesting OZL options definitions for recent date...")
    try:
        recent_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            schema='definition',
            stype_in='parent',
            symbols=['OZL'],
            start=recent_date,
            end=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        )
        df = data.to_df()
        if not df.empty:
            logger.info(f"✅ Found {len(df)} OZL definitions")
            if 'security_type' in df.columns:
                options = df[df['security_type'] == 'OOF']
                logger.info(f"   Options contracts: {len(options)}")
                if len(options) > 0:
                    logger.info(f"   Sample option symbols: {options['symbol'].head(10).tolist()}")
                    return True
    except Exception as e:
        logger.error(f"❌ Error testing OZL options: {e}")
    
    return False

if __name__ == '__main__':
    logger.info("🧪 Testing ZL Options Access (OZL symbol)")
    logger.info("=" * 60)
    
    success = test_ozl_options()
    
    if success:
        logger.info("\n✅ ZL Options are accessible!")
        logger.info("   Update IV30 calculation script to use OZL instead of ZL.OPT")
    else:
        logger.warning("\n⚠️  ZL Options may not be accessible with current plan")
        logger.info("   Check Databento plan details for options add-on requirements")

