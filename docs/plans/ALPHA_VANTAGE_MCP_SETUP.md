# Alpha Vantage MCP Server Setup for Cursor
**Date**: November 16, 2025  
**Purpose**: Set up Alpha Vantage MCP server for direct API access in Cursor  
**Reference**: https://mcp.alphavantage.co/

---

## What is MCP (Model Context Protocol)?

MCP allows AI assistants (like me in Cursor) to **directly call APIs** without writing code. Instead of:
- Writing Python scripts to call Alpha Vantage
- Managing API keys in code
- Handling responses manually

You can:
- Ask me to query Alpha Vantage directly
- Get real-time data during development
- Test API responses instantly
- Explore data interactively

---

## Setup Instructions

### Step 1: Get Your Alpha Vantage API Key

1. Go to https://www.alphavantage.co/support/#api-key
2. Get your free API key (or premium key if you've subscribed)
3. Copy it to clipboard

### Step 2: Configure Cursor MCP Server

**Option A: Remote Server Connection (Recommended)**

1. Create/edit `~/.cursor/mcp.json`:
```bash
mkdir -p ~/.cursor
nano ~/.cursor/mcp.json
```

2. Add this configuration:
```json
{
  "mcpServers": {
    "alphavantage": {
      "url": "https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY"
    }
  }
}
```

3. Replace `YOUR_API_KEY` with your actual Alpha Vantage API key

**Option B: Local Server Connection**

1. Install `uv` (Python package manager):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create/edit `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "alphavantage": {
      "command": "uvx",
      "args": ["av-mcp", "YOUR_API_KEY"]
    }
  }
}
```

3. Replace `YOUR_API_KEY` with your actual Alpha Vantage API key

### Step 3: Restart Cursor

- Close and reopen Cursor to load the MCP server
- The Alpha Vantage tools will now be available to me (the AI assistant)

---

## What You Can Do With MCP

### ✅ **Ad-Hoc Queries During Development**

Instead of writing scripts, you can ask me:

- "Get the RSI for ZL (soybean oil) futures"
- "Show me MACD for ES futures"
- "What's the current price of crude oil?"
- "Get all technical indicators for ZS (soybeans)"

I'll call the Alpha Vantage API directly and show you the results.

### ✅ **Quick Data Exploration**

- Test API responses before writing collection scripts
- Verify symbol names (ES, ES=F, etc.)
- Check data formats and structures
- Explore available indicators

### ✅ **Interactive Development**

- Ask me to compare indicators across symbols
- Get real-time data during feature engineering
- Test different indicator parameters
- Validate calculations

---

## Available Tools (From MCP Server)

### Time Series Data
- `TIME_SERIES_INTRADAY` - Intraday OHLCV data
- `TIME_SERIES_DAILY` - Daily time series
- `TIME_SERIES_WEEKLY` - Weekly time series
- `TIME_SERIES_MONTHLY` - Monthly time series
- `GLOBAL_QUOTE` - Real-time quotes

### Technical Indicators (50+)
- `RSI`, `MACD`, `SMA`, `EMA`, `WMA`, `DEMA`, `TEMA`
- `ADX`, `AROON`, `BBANDS`, `STOCH`, `CCI`, `MOM`
- `OBV`, `ATR`, `NATR`, `WILLR`, `MFI`, `TRIX`
- `HT_TRENDLINE`, `HT_SINE`, `HT_DCPERIOD`, `HT_PHASOR`
- And 30+ more...

### Commodities
- `WTI` - Crude Oil WTI
- `BRENT` - Crude Oil Brent
- `NATURAL_GAS` - Natural Gas
- `WHEAT`, `CORN`, `COTTON`, `SUGAR`, `COFFEE`
- `ALL_COMMODITIES` - All commodities

### Economic Indicators
- `REAL_GDP`, `TREASURY_YIELD`, `FEDERAL_FUNDS_RATE`
- `CPI`, `INFLATION`, `UNEMPLOYMENT`, `NONFARM_PAYROLL`

### Alpha Intelligence
- `NEWS_SENTIMENT` - News & sentiment analysis
- `EARNINGS` - Earnings data
- `TOP_GAINERS_LOSERS` - Market movers

---

## How MCP Complements Your Daily Collection

### Current Workflow (Automated Scripts)
```
Daily Cron Job → Python Script → Alpha Vantage API → BigQuery
```

### With MCP (Interactive Development)
```
You → Ask Me → MCP Server → Alpha Vantage API → Show Results
```

**MCP is NOT a replacement for automated collection** - it's a **development tool** that makes it easier to:
- Test API calls before writing scripts
- Debug data issues
- Explore new indicators
- Verify symbol names and formats

---

## Example Use Cases

### 1. Verify ES Futures Symbol
**You**: "What's the correct symbol for S&P 500 futures in Alpha Vantage?"

**Me**: *[Calls MCP] "Let me check... ES or ES=F?"*

### 2. Test Technical Indicator
**You**: "Get RSI(14) for ZL futures with daily interval"

**Me**: *[Calls MCP] "Here's the RSI data..."*

### 3. Compare Indicators
**You**: "Compare MACD for ZL, ZS, and ES futures"

**Me**: *[Calls MCP multiple times] "Here's the comparison..."*

### 4. Explore New Indicator
**You**: "What does HT_TRENDLINE show for crude oil?"

**Me**: *[Calls MCP] "HT_TRENDLINE uses Hilbert Transform..."*

---

## Rate Limits Still Apply

⚠️ **Important**: MCP calls count toward your API limit:
- **Free tier**: 25 calls/day
- **Premium**: Based on your plan (Plan30, Plan75, etc.)

**Best Practice**: Use MCP for development/testing, use scripts for production collection.

---

## Security Note

### API Key Storage

**Option A: Remote Server (URL parameter)**
- ✅ Simple setup
- ⚠️ API key visible in config file
- ✅ Works immediately

**Option B: Local Server**
- ✅ API key passed as argument (still visible in config)
- ✅ More control
- ⚠️ Requires `uv` installation

**Recommendation**: 
- Use remote server for quick setup
- Consider migrating API key to Keychain later (see `src/utils/keychain_manager.py`)

---

## Integration with Existing Scripts

MCP doesn't replace your collection scripts - it **complements** them:

### Development Phase (MCP)
- Test API calls interactively
- Verify symbol names
- Explore indicators
- Debug data issues

### Production Phase (Scripts)
- Automated daily collection
- Scheduled cron jobs
- BigQuery ingestion
- Error handling & retries

---

## Next Steps

1. **Set up MCP** using instructions above
2. **Restart Cursor** to load the server
3. **Test it**: Ask me to query Alpha Vantage for a symbol
4. **Verify ES futures symbol**: We need to confirm the correct symbol for ES
5. **Continue with premium subscription**: Still need premium for daily collection (220-550 calls/day)

---

## Troubleshooting

### MCP Server Not Working?

1. **Check config file location**: `~/.cursor/mcp.json`
2. **Verify API key**: Make sure it's correct
3. **Restart Cursor**: Close and reopen completely
4. **Check Cursor logs**: Look for MCP connection errors

### API Calls Failing?

1. **Rate limit**: Check if you've exceeded daily limit
2. **Invalid symbol**: Verify symbol name (ES vs ES=F)
3. **Premium endpoint**: Some endpoints require premium tier

---

## Summary

✅ **MCP Setup**: Add Alpha Vantage MCP server to Cursor config  
✅ **Interactive Queries**: Ask me to query Alpha Vantage directly  
✅ **Development Tool**: Test API calls before writing scripts  
✅ **Complements Scripts**: Doesn't replace automated collection  
⚠️ **Rate Limits**: Still count toward API limits  
✅ **Premium Still Needed**: For daily collection (220-550 calls/day)

---

**Reference**: https://mcp.alphavantage.co/  
**Last Updated**: November 16, 2025



