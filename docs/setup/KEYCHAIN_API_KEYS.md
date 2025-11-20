---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# API Key Management with macOS Keychain

## Overview

All API keys for CBI-V14 MUST be stored in macOS Keychain for security. This ensures:
- Keys are encrypted by macOS
- No keys in git history or source code
- Keys accessible only to your user account
- Automatic locking after inactivity

## Quick Start

### 1. Store Keys in Keychain

**Option A: Use the helper script** (recommended):
```bash
./scripts/setup/store_keys_in_keychain.sh
```

**Option B: Manual storage**:
```bash
# Store FRED API key
security add-generic-password -a default -s cbi-v14.FRED_API_KEY -w "your_key_here" -U
> FRED requires a 32-character lowercase alphanumeric key with no hyphens. If the key includes uppercase or separators, the API will return HTTP 400. Reference: https://fred.stlouisfed.org/docs/api/fred/

# Store NewsAPI key
security add-generic-password -a default -s cbi-v14.NEWSAPI_KEY -w "your_key_here" -U

# Store ScrapeCreators key
security add-generic-password -a default -s cbi-v14.SCRAPE_CREATORS_API_KEY -w "your_key_here" -U
# See docs/setup/SCRAPECREATORS_API.md for full ScrapeCreators integration guide

# Store DataBento API key (GLBX.MDP3 access)
security add-generic-password -a default -s cbi-v14.DATABENTO_API_KEY -w "your_key_here" -U
> To use with server processes, export to environment at runtime:
> export DATABENTO_API_KEY="$(security find-generic-password -a default -s cbi-v14.DATABENTO_API_KEY -w)"
```

### 2. Use Keys in Python Scripts

```python
from src.utils.keychain_manager import get_api_key

# Retrieve API key
fred_key = get_api_key('FRED_API_KEY')
if not fred_key:
    raise RuntimeError(
        "FRED_API_KEY not found in Keychain. "
        "Store it using: security add-generic-password -a default -s cbi-v14.FRED_API_KEY -w <key> -U"
    )

# Use the key
response = requests.get(f"https://api.example.com/data?api_key={fred_key}")
```

### 3. Verify Keys Are Stored

```bash
# Check if a key exists
security find-generic-password -a default -s cbi-v14.FRED_API_KEY -w

# List all CBI-V14 keys
security dump-keychain | grep cbi-v14
```

## Required API Keys

Store these keys in Keychain:

| Key Name | Description | Usage |
|----------|-------------|-------|
| `FRED_API_KEY` | Federal Reserve Economic Data | Economic indicators |
| `NEWSAPI_KEY` | News API | Sentiment analysis |
| `SCRAPE_CREATORS_API_KEY` | ScrapeCreators | Social media scraping |
| `DATABENTO_API_KEY` | DataBento | Live CME/CBOT/NYMEX/COMEX futures feed |
| `DATABENTO_API_KEY` | DataBento | CME/CBOT/NYMEX/COMEX futures historical + live |

## Migration from Environment Variables

If you have existing scripts using `os.getenv()`, the `get_key()` function provides backward compatibility:

```python
from src.utils.keychain_manager import get_key

# This will try Keychain first, then fall back to environment variable
# (with a warning to migrate to Keychain)
api_key = get_key('FRED_API_KEY')
```

**Note**: The fallback is temporary. All scripts should migrate to Keychain-only access.

## Keychain Utility Functions

### `get_api_key(key_name, account='default')`
Retrieve an API key from Keychain. Returns `None` if not found.

### `set_api_key(key_name, key_value, account='default')`
Store an API key in Keychain. Returns `True` if successful.

### `list_stored_keys()`
List all CBI-V14 keys stored in Keychain.

### `get_key(key_name, default=None)`
Convenience function with fallback to environment variables (for migration).

## Security Best Practices

1. **Never commit keys to git** - Use Keychain only
2. **Never hardcode keys** - Always use `get_api_key()`
3. **Use descriptive error messages** - Tell users how to store missing keys
4. **Rotate keys regularly** - Update keys in Keychain when rotating
5. **Use separate accounts** - If needed, use different account names for different environments

## Troubleshooting

### "Key not found in Keychain"
- Verify the key is stored: `security find-generic-password -a default -s cbi-v14.FRED_API_KEY -w`
- Check the service name matches: `cbi-v14.{KEY_NAME}`
- Ensure you're using the correct account name (default)

### "Permission denied"
- macOS may prompt for Keychain access on first use
- Grant access when prompted
- Check Keychain Access app if issues persist

### "Not running on macOS"
- Keychain access is macOS-only
- For other platforms, use environment variables as fallback (not recommended for production)

## Reference

- Keychain utility: `src/utils/keychain_manager.py`
- Architecture plan: `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` (Security section)
- Setup script: `scripts/setup/store_keys_in_keychain.sh`
