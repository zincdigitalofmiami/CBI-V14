# Alpha Vantage MCP Configuration
**Date**: November 16, 2025  
**Status**: ✅ Configured - Plan75 Premium  
**API Key**: Stored in Keychain

---

## ✅ Configuration Complete

Your Alpha Vantage **Plan75** premium API key has been:
1. ✅ **Stored in macOS Keychain** (`cbi-v14.ALPHA_VANTAGE_API_KEY`)
2. ✅ **Verified** - Key retrieved successfully

---

## MCP Server Setup

### Option 1: Remote Server (Recommended for Quick Start)

Create/edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "alphavantage": {
      "url": "https://mcp.alphavantage.co/mcp?apikey=4D0B52J52L6ZR1QL"
    }
  }
}
```

**⚠️ Security Note**: MCP config files require the API key directly. This file is in your home directory (`~/.cursor/mcp.json`) and is user-specific, but the key is visible in plain text. For maximum security, consider Option 2.

### Option 2: Local Server with Keychain (More Secure)

Create a wrapper script that retrieves the key from Keychain:

**1. Create wrapper script** (`~/.cursor/alphavantage_mcp.sh`):
```bash
#!/bin/bash
# Wrapper script to retrieve Alpha Vantage API key from Keychain
API_KEY=$(security find-generic-password -a "default" -s "cbi-v14.ALPHA_VANTAGE_API_KEY" -w 2>/dev/null)
if [ -z "$API_KEY" ]; then
    echo "Error: Alpha Vantage API key not found in Keychain" >&2
    exit 1
fi
exec uvx av-mcp "$API_KEY"
```

**2. Make it executable**:
```bash
chmod +x ~/.cursor/alphavantage_mcp.sh
```

**3. Install `uv`** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**4. Configure MCP** (`~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "alphavantage": {
      "command": "~/.cursor/alphavantage_mcp.sh"
    }
  }
}
```

---

## Your Plan Details

- **Plan**: Plan75 Premium
- **Rate Limit**: 75 API calls per minute
- **Daily Capacity**: ~108,000 calls/day (if used continuously)
- **Your Needs**: 220-550 calls/day ✅ **More than sufficient**

### What This Means:

✅ **Daily Collection**: Can collect all 50+ indicators for 11 symbols daily  
✅ **Historical Backfill**: Can backfill years of data in hours  
✅ **Real-time Data**: Access to real-time/15-min delayed data  
✅ **Premium Endpoints**: Access to VWAP, bulk quotes, etc.

---

## Testing the Setup

After configuring MCP and restarting Cursor, test it by asking me:

1. **"Get RSI for ZL futures"** - Test technical indicator
2. **"What's the current price of ES futures?"** - Test quote endpoint
3. **"Show me MACD for soybean oil"** - Test another indicator
4. **"What symbol does Alpha Vantage use for S&P 500 futures?"** - Verify ES symbol

---

## Using the Key in Python Scripts

### Retrieve from Keychain:

```python
from src.utils.keychain_manager import get_api_key

# Get Alpha Vantage API key
av_key = get_api_key('ALPHA_VANTAGE_API_KEY')
if not av_key:
    raise RuntimeError(
        "ALPHA_VANTAGE_API_KEY not found in Keychain. "
        "Store it using: security add-generic-password -a default -s cbi-v14.ALPHA_VANTAGE_API_KEY -w <key> -U"
    )

# Use in API calls
url = 'https://www.alphavantage.co/query'
params = {
    'function': 'RSI',
    'symbol': 'ZL',
    'interval': 'daily',
    'time_period': 14,
    'series_type': 'close',
    'apikey': av_key
}
```

---

## Next Steps

1. ✅ **Key stored in Keychain** - Done
2. ⏳ **Configure MCP** - Choose Option 1 or 2 above
3. ⏳ **Restart Cursor** - To load MCP server
4. ⏳ **Test MCP** - Ask me to query Alpha Vantage
5. ⏳ **Verify ES symbol** - Test ES futures symbol
6. ⏳ **Start daily collection** - Implement collection scripts

---

## Collection Script Template

Here's a template for your daily collection script:

```python
#!/usr/bin/env python3
"""
Daily Alpha Vantage Technical Indicators Collection
Collects 50+ indicators for 11 symbols (10 commodities + ES futures)
"""

from src.utils.keychain_manager import get_api_key
import requests
import time
from datetime import datetime

# Get API key from Keychain
API_KEY = get_api_key('ALPHA_VANTAGE_API_KEY')
if not API_KEY:
    raise RuntimeError("ALPHA_VANTAGE_API_KEY not found in Keychain")

# Symbols to collect
SYMBOLS = [
    'ZL', 'ZS', 'ZM', 'ZC', 'ZW',  # Soybean complex + grains
    'CL', 'NG', 'GC', 'CT',        # Energy + metals
    'BRENT',                        # Brent crude
    'ES'                            # S&P 500 futures
]

# Core indicators (20) - Daily
DAILY_INDICATORS = [
    'RSI', 'MACD', 'SMA', 'EMA', 'ADX', 'AROON',
    'BBANDS', 'STOCH', 'CCI', 'MOM', 'ROC', 'OBV',
    'ATR', 'NATR', 'WILLR', 'MFI', 'TRIX', 'ULTOSC', 'DX', 'SAR'
]

# Additional indicators (30) - Weekly
WEEKLY_INDICATORS = [
    'WMA', 'DEMA', 'TEMA', 'TRIMA', 'KAMA', 'MAMA',
    'VWAP', 'MACDEXT', 'STOCHF', 'STOCHRSI',
    # ... add remaining indicators
]

BASE_URL = 'https://www.alphavantage.co/query'

def collect_indicator(symbol, indicator, interval='daily'):
    """Collect a single technical indicator"""
    params = {
        'function': indicator,
        'symbol': symbol,
        'interval': interval,
        'series_type': 'close',
        'apikey': API_KEY
    }
    
    # Add indicator-specific parameters
    if indicator == 'RSI':
        params['time_period'] = 14
    elif indicator == 'MACD':
        params['series_type'] = 'close'
    # ... add other indicator-specific params
    
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        # Process and store data
        return data
    else:
        print(f"Error collecting {indicator} for {symbol}: {response.status_code}")
        return None

# Daily collection (220 requests)
for symbol in SYMBOLS:
    for indicator in DAILY_INDICATORS:
        collect_indicator(symbol, indicator)
        time.sleep(0.8)  # Rate limit: 75/min = 0.8 sec between calls
```

---

## Summary

✅ **Premium Plan75 Active** - 75 calls/minute  
✅ **Key Stored Securely** - In macOS Keychain  
✅ **MCP Ready** - Configure `~/.cursor/mcp.json`  
✅ **Sufficient Capacity** - 220-550 calls/day needed, 108K/day available  

**Next**: Configure MCP, restart Cursor, and start collecting!

---

**Last Updated**: November 16, 2025



