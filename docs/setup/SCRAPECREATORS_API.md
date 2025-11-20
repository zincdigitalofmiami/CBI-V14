---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# ScrapeCreators API Integration Guide
**Date:** November 17, 2025  
**Purpose:** Truth Social + Policy Data Collection  
**Status:** Active Integration

---

## Overview

**ScrapeCreators** is the API we use for all Truth Social + social media scraping. It's the only upstream source that provides real (non-fake) Trump/policy data without running a headless browser farm.

**Supported Platforms:**
- ✅ Truth Social
- ✅ Facebook
- ✅ Twitter/X
- ✅ LinkedIn
- ❌ Reddit (NOT supported)
- ❌ YouTube (NOT supported)
- ❌ TikTok (NOT supported)

### Why ScrapeCreators?
- ✅ **Real Data**: Authentic Truth Social posts (not synthetic/fake)
- ✅ **No Browser Farm**: REST API eliminates need for headless browsers
- ✅ **Rate Limited**: Built-in rate limiting prevents IP bans
- ✅ **Structured JSON**: Clean, parseable responses
- ✅ **Historical Access**: Can pull historical posts with date ranges

---

## Implementation

### Collector Location
**Script:** `scripts/ingest/collect_policy_trump.py`

This script calls ScrapeCreators' REST endpoints to pull:
- Trump's Truth Social posts (`realDonaldTrump`)
- Key policy accounts (`DonaldJTrumpJr`, `EricTrump`)
- Social Media: Facebook, Twitter/X, LinkedIn (NO Reddit, YouTube, TikTok)
- Aggregated News: NewsAPI, Alpha Vantage News, RSS feeds
- ICE Data: Intercontinental Exchange announcements
- Tariffs: USTR announcements, Section 301 actions
- Executive Orders: White House executive orders, presidential proclamations
- Policy Feeds: USDA announcements, EPA RFS updates, trade news

### API Key Management

**Keychain Storage (macOS):**
```bash
security add-generic-password \
  -a default \
  -s cbi-v14.SCRAPECREATORS_API_KEY \
  -w "<your_api_key>" \
  -U
```

**Script Access:**
The script reads the API key from the macOS keychain using `src.utils.keychain_manager.get_api_key('SCRAPECREATORS_KEY')` with fallback to environment variable `SCRAPECREATORS_KEY`.

**No Hardcoding:**
- ✅ API keys are never committed to source control
- ✅ Keychain is the primary source of truth
- ✅ Environment variables are fallback only

---

## Request Pattern

### API Endpoint
```
POST/GET https://api.scrapecreators.com/v1/truthsocial
```

### Request Headers
```python
headers = {
    'x-api-key': SCRAPECREATORS_API_KEY,
    'Content-Type': 'application/json'
}
```

### Request Parameters
```python
params = {
    'username': 'realDonaldTrump',  # Without @ symbol
    'limit': 100,                    # Max posts per request
    'start_date': '2020-01-01',      # Optional: date range start
    'end_date': '2025-11-17',       # Optional: date range end
    'hashtags': ['trade', 'china'], # Optional: filter by hashtags
}
```

### Rate Limiting
- The script includes `time.sleep(1)` between requests
- ScrapeCreators returns rate-limit headers in responses
- Script logs rate-limit warnings if approaching limits

### Response Format
```json
{
  "posts": [
    {
      "text": "Post content here...",
      "created_at": "2025-11-17T10:30:00Z",
      "likes": 12345,
      "reposts": 567,
      "replies": 89,
      "url": "https://truthsocial.com/@realDonaldTrump/posts/123456",
      "hashtags": ["trade", "china"]
    }
  ],
  "total": 100,
  "next_cursor": "abc123..."
}
```

---

## Data Processing Pipeline

### 1. Collection (`collect_policy_trump.py`)
- Fetches posts from ScrapeCreators API
- Handles pagination automatically
- Applies rate limiting

### 2. Sentiment Classification
Each post is classified for ZL (soybean oil) impact:

**Bullish Keywords:**
- `biofuel`, `ethanol`, `biodiesel`, `renewable`, `mandate`, `RFS`
- `china`, `purchase`, `buy`, `deal`, `agreement`, `trade deal`
- `export`, `demand`, `strong`, `growth`

**Bearish Keywords:**
- `tariff`, `tax`, `ban`, `restriction`, `sanction`, `war`, `conflict`
- `weak`, `decline`, `drop`, `fall`, `recession`, `crisis`

**Sentiment Score:** `-1.0` (bearish) to `+1.0` (bullish)

**Sentiment Class:**
- `bullish`: score > 0.2
- `bearish`: score < -0.2
- `neutral`: otherwise

### 3. Policy Category Tagging
Posts are tagged with policy categories:

- **trade**: `tariff`, `trade`, `china`, `import`, `export`, `soybean`, `agriculture`
- **biofuel**: `biofuel`, `ethanol`, `biodiesel`, `RFS`, `RIN`, `renewable`, `mandate`
- **agriculture**: `farm`, `farmer`, `crop`, `harvest`, `USDA`, `subsidy`
- **energy**: `oil`, `gasoline`, `crude`, `energy`, `pipeline`

### 4. Output Columns (Prefixed)
All columns use `policy_trump_*` prefix except `date` and `timestamp`:

```python
{
    'date': '2025-11-17',
    'timestamp': '2025-11-17T10:30:00Z',
    'policy_trump_text': 'Post content...',
    'policy_trump_username': 'realDonaldTrump',
    'policy_trump_likes': 12345,
    'policy_trump_reposts': 567,
    'policy_trump_replies': 89,
    'policy_trump_url': 'https://...',
    'policy_trump_sentiment_score': 0.45,
    'policy_trump_sentiment_class': 'bullish',
    'policy_trump_bullish_keywords': 3,
    'policy_trump_bearish_keywords': 0,
    'policy_trump_categories': 'trade,biofuel',
}
```

### 5. File Output
**Raw Data:** `TrainingData/raw/policy_trump/policy_trump_YYYYMMDD_HHMM.parquet`

**Staging:** `TrainingData/staging/policy_trump_signals.parquet` (after staging script runs)

---

## Creating New Pulls

### Step 1: Add API Key (if not already)
```bash
security add-generic-password \
  -a default \
  -s cbi-v14.SCRAPECREATORS_API_KEY \
  -w "<your_api_key>" \
  -U
```

### Step 2: Configure Target in Script

Edit `scripts/ingest/collect_policy_trump.py`:

**Add to `TRUTH_SOCIAL_ACCOUNTS` list:**
```python
TRUTH_SOCIAL_ACCOUNTS = [
    'realDonaldTrump',    # Existing
    'DonaldJTrumpJr',     # Existing
    'EricTrump',          # Existing
    'NewAccountName',     # NEW: Add here
]
```

**Add to `POLICY_KEYWORDS` (if new category):**
```python
POLICY_KEYWORDS = {
    'trade': [...],
    'biofuel': [...],
    'agriculture': [...],
    'energy': [...],
    'new_category': ['keyword1', 'keyword2', ...],  # NEW
}
```

**Custom Parsing (if payload differs):**
If the API response structure differs for a new endpoint, add custom parsing in `collect_truth_social_posts()`:

```python
def collect_truth_social_posts(usernames: list, limit: int = 100) -> pd.DataFrame:
    # ... existing code ...
    
    # NEW: Custom handling for specific account
    if username == 'NewAccountName':
        # Custom parsing logic here
        processed = {
            'timestamp': custom_timestamp_parsing(post),
            'text': custom_text_extraction(post),
            # ... other fields
        }
```

### Step 3: Run the Script

**Basic execution:**
```bash
python3 scripts/ingest/collect_policy_trump.py
```

**With date range:**
```bash
python3 scripts/ingest/collect_policy_trump.py \
  --start 2020-01-01 \
  --end 2025-11-17
```

**The script handles:**
- ✅ Pagination automatically
- ✅ Rate limiting (1 second between requests)
- ✅ Error handling and retries
- ✅ Date filtering
- ✅ Deduplication

### Step 4: Promote to Staging

After collection, rerun the staging script:

```bash
python3 scripts/staging/create_staging_files.py
```

This will:
1. Process raw `policy_trump_*.parquet` files
2. Apply `policy_trump_*` prefixes (if not already applied)
3. Merge into `staging/policy_trump_signals.parquet`
4. Prepare for join spec consumption

### Step 5: Update Join Spec

Edit `registry/join_spec.yaml` to add the new join step:

```yaml
- name: "add_policy_trump"
  left: "<<add_alpha_vantage>>"  # Or previous step
  right: "staging/policy_trump_signals.parquet"
  on: ["date"]
  how: "left"
  null_policy:
    allow: true
    fill_method: "ffill"  # Forward fill for policy signals
  tests:
    - expect_rows_preserved
    - expect_columns_prefixed: ["policy_trump_"]
```

### Step 6: Backfill BigQuery

Once staging is updated, backfill BigQuery:

```bash
python3 scripts/migration/week2_backfill_alpha_tables.py
# Or create new backfill script for policy_trump table
```

---

## Modular Architecture

The collector is **modular**, meaning adding a new "pull" just requires:

1. **Config Entry**: Add username/keyword to configuration lists
2. **JSON Mapping**: Map returned JSON fields to `policy_trump_*` columns
3. **Run Script**: Execute collection script

**Everything else is automatic:**
- ✅ Prefixed column naming (`policy_trump_*`)
- ✅ Date filtering
- ✅ Deduplication
- ✅ Parquet writing
- ✅ Error handling
- ✅ Rate limiting

---

## Example: Adding a New Policy Feed

### Scenario: Add USDA FAS Export Sales Feed

**Step 1:** Add to `scrape_policy_feeds()` function:

```python
def scrape_policy_feeds() -> pd.DataFrame:
    # ... existing code ...
    
    # NEW: USDA FAS Export Sales
    try:
        usda_fas_url = 'https://apps.fas.usda.gov/export-sales/h801.htm'
        response = requests.get(usda_fas_url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; CBI-V14-Data-Collector/1.0)'
        })
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Parse USDA FAS announcements
            # ... parsing logic ...
            
            policy_items.append({
                'timestamp': datetime.now(),
                'source': 'USDA_FAS',
                'title': 'Export Sales Report',
                'text': parsed_text,
                'url': usda_fas_url,
            })
    except Exception as e:
        logger.warning(f"Error scraping USDA FAS: {e}")
```

**Step 2:** Run collection:
```bash
python3 scripts/ingest/collect_policy_trump.py
```

**Step 3:** Promote to staging:
```bash
python3 scripts/staging/create_staging_files.py
```

**Result:** New feed automatically flows into `policy_trump_signals.parquet` with proper prefixes.

---

## Troubleshooting

### API Key Not Found
**Error:** `No ScrapeCreators API key found`

**Solution:**
```bash
security add-generic-password \
  -a default \
  -s cbi-v14.SCRAPECREATORS_API_KEY \
  -w "<your_api_key>" \
  -U
```

### Rate Limit Exceeded
**Error:** `API returned 429 Too Many Requests`

**Solution:**
- Script includes automatic rate limiting (`time.sleep(1)`)
- Increase delay if needed: `time.sleep(2)` or `time.sleep(5)`
- Check ScrapeCreators dashboard for rate limit status

### Empty Response
**Error:** `No posts collected`

**Possible Causes:**
- Username doesn't exist on Truth Social
- Date range has no posts
- API key invalid or expired

**Solution:**
- Verify username spelling (no `@` symbol)
- Check date range (widen if needed)
- Test API key with ScrapeCreators dashboard

### Parsing Errors
**Error:** `KeyError: 'text'` or similar

**Solution:**
- Check ScrapeCreators API response format (may have changed)
- Add custom parsing logic for new endpoints
- Log raw response: `logger.debug(f"Response: {response.json()}")`

---

## Integration with Pipeline

### Data Flow
```
ScrapeCreators API
    ↓
collect_policy_trump.py (raw parquet)
    ↓
create_staging_files.py (staging parquet)
    ↓
join_spec.yaml (join with other sources)
    ↓
build_all_features.py (feature engineering)
    ↓
BigQuery backfill (data warehouse)
```

### Join Sequence
Policy/Trump data joins after Alpha Vantage:

```yaml
1. base_prices (Yahoo ZL=F)
2. add_macro (FRED)
3. add_weather (Weather)
4. add_cftc (CFTC)
5. add_usda (USDA)
6. add_eia (EIA)
7. add_alpha_vantage (Alpha Vantage)
8. add_palm (Palm)
9. add_volatility (Volatility/VIX)
10. add_policy_trump (Policy/Trump) ← NEW
```

---

## Best Practices

1. **Always use keychain** for API keys (never hardcode)
2. **Respect rate limits** (1 second between requests minimum)
3. **Handle errors gracefully** (log warnings, continue collection)
4. **Prefix all columns** (`policy_trump_*` except `date`/`timestamp`)
5. **Deduplicate** on `date` + `username` + `text` hash
6. **Forward fill** policy signals (they persist until new announcement)
7. **Log everything** (helps debug issues later)

---

## References

- **ScrapeCreators API Docs:** https://docs.scrapecreators.com/
- **Script Location:** `scripts/ingest/collect_policy_trump.py`
- **Staging Script:** `scripts/staging/create_staging_files.py`
- **Join Spec:** `registry/join_spec.yaml`
- **Keychain Manager:** `src/utils/keychain_manager.py`

---

**Last Updated:** November 17, 2025  
**Maintainer:** CBI-V14 Data Collection Team

