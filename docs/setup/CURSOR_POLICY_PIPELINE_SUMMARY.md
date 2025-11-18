# Policy Pipeline Summary for Cursor

**Last Updated:** November 17, 2025

## Overview

The policy/shock signal collection pipeline (`collect_policy_trump.py`) now ingests data from multiple sources via ScrapeCreators API, Google Search, RSS feeds, and government sources. All data follows a standardized prefix-based schema for downstream joins and model training.

## Data Sources

### ScrapeCreators API Sources
1. **Truth Social** (`/v1/truthsocial/profile` + `/v1/truthsocial/user/posts`)
   - Accounts: realDonaldTrump, DonaldJTrumpJr, EricTrump
   - Uses `handle` parameter
   - Profile validation before post collection

2. **Twitter/X** (`/v1/twitter/user-tweets`)
   - Uses `handle` parameter
   - Returns up to 100 popular tweets per account

3. **Facebook** (`/v1/facebook/profile/posts`)
   - Uses `url` parameter (full Facebook URL)
   - Returns 3 posts per request

4. **LinkedIn** (`/v1/linkedin/profile`)
   - Uses `url` parameter (full LinkedIn profile URL)
   - Returns profile info (posts require separate endpoint)

5. **Bluesky** (`/bluesky/user/posts`)
   - Uses `handle` parameter
   - Handles 404 gracefully (account doesn't exist)

6. **Google Search** (`/v1/google/search`)
   - 106 queries across 21 categories
   - Returns title, description, URL
   - Auto-classifies region, source type, sentiment

### Other Sources
- **RSS Feeds**: Reuters, Bloomberg, CNBC, Agriculture.com, AgWeb
- **NewsAPI**: News aggregation (requires API key)
- **Alpha Vantage News**: News sentiment API
- **ICE**: Intercontinental Exchange announcements
- **USTR**: Trade policy announcements
- **Federal Register**: Executive orders and regulations
- **White House**: Executive orders and presidential actions

## Schema Classification

### Prefix Buckets

Every record is classified into one or more prefix buckets:

- **`policy_*`**: Lobbying, legislation, regulation, executive orders, EPA/USTR/White House
- **`trade_*`**: Country-labeled trade (trade_china, trade_argentina, trade_palm, trade_currency)
- **`biofuel_*`**: RFS/RIN/biodiesel/ethanol spreads and policies
- **`supply_*`**: Farm reports, weather, labor, crop progress
- **`logistics_*`**: River levels, ports, strikes, shipping constraints
- **`macro_*`**: Volatility, FX, rates, Fed comments
- **`market_*`**: Positioning, market-structure, exchange rules/margin
- **`energy_*`**: Crude/refinery/energy shocks

### Required Fields

All records include these `policy_trump_*` prefixed fields:

**Source Identification:**
- `policy_trump_source`: Source identifier (e.g., 'google_search', 'truth_social')
- `policy_trump_source_type`: Type ('news_api', 'rss', 'gov_press', 'social_media', 'google_search')

**Content:**
- `policy_trump_headline`: Article/post title
- `policy_trump_text`: Description/snippet/content
- `policy_trump_url`: Full URL

**Classification:**
- `policy_trump_category`: Original category (e.g., 'policy_lobbying', 'trade_china')
- `policy_trump_prefix_buckets`: Comma-separated buckets (e.g., 'policy', 'trade,biofuel')
- `policy_trump_query`: Query/keyword that triggered collection
- `policy_trump_region`: Region ('US', 'Brazil', 'Argentina', 'China', 'SE_Asia', 'EU', 'Unknown')

**Metadata:**
- `policy_trump_domain`: Source domain
- `policy_trump_confidence`: Credibility score (0.5-1.0)
- `policy_trump_unique_id`: MD5 hash for deduplication
- `policy_trump_language`: Language code (default 'en')

**Sentiment:**
- `policy_trump_sentiment_score`: Sentiment score (-1 to +1)
- `policy_trump_sentiment_class`: 'bullish', 'bearish', 'neutral'
- `policy_trump_bullish_keywords`: Count of bullish keywords
- `policy_trump_bearish_keywords`: Count of bearish keywords
- `policy_trump_categories`: Policy categories detected

**Temporal:**
- `timestamp`: Full timestamp
- `date`: Date for daily joins

## Staging Pipeline

### Function: `create_policy_trump_staging()`

Located in `scripts/staging/create_staging_files.py`:

- Loads raw policy files from `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/policy_trump/`
- Ensures all columns have `policy_trump_*` prefix (except `date`)
- Merges multiple files if present
- Saves to `staging/policy_trump_signals.parquet`

**Run after collection:**
```bash
python3 scripts/staging/create_staging_files.py
```

## Join Specification

### Step: `add_policy_trump`

Located in `registry/join_spec.yaml`:

```yaml
- name: "add_policy_trump"
  left: "<<add_palm>>"
  right: "staging/policy_trump_signals.parquet"
  on: ["date"]
  how: "left"
  null_policy:
    allow: true
    fill_method: "ffill"
  tests:
    - expect_rows_preserved
    - expect_columns_prefixed: ["policy_trump_"]
```

**Join Order:**
1. `base_prices` (Yahoo ZL=F)
2. `add_macro` (FRED)
3. `add_weather`
4. `add_cftc`
5. `add_usda`
6. `add_eia`
7. `add_regimes`
8. `add_alpha_vantage`
9. `add_volatility`
10. `add_palm`
11. **`add_policy_trump`** ← Policy feeds join here

## Manual Sources (Do Not Script)

These sources require manual intervention and are documented in `docs/migration/DATA_COLLECTION_STATUS.md`:

1. **EPA RIN Prices**
   - Status: Script exists but URLs 404
   - Action: Manual download from EPA EMTS dashboard or API access

2. **World Bank Pink Sheet**
   - Status: Script exists but URLs outdated
   - Action: Manual download from World Bank commodity markets page
   - Alternative: `collect_worldbank_alternative.py` uses Open Data API

3. **USDA FAS Export Sales**
   - Status: Script exists but scraping fails
   - Action: API authentication or different scraping approach

**Do not attempt to script these until access is confirmed.**

## Google Search API

### Endpoint
- URL: `https://api.scrapecreators.com/v1/google/search`
- Method: GET
- Parameters: `query` (required), `limit` (optional, default 10)
- Cost: 1 credit per request

### Query Taxonomy

106 queries organized into 21 categories:

- **Policy** (16 queries): lobbying, legislation, regulation
- **Supply** (15 queries): farm reports, labor, weather
- **Trade** (20 queries): China, Argentina, Palm, Currency
- **Logistics** (15 queries): water, port, strike
- **Biofuel** (10 queries): policy, spread
- **Energy** (5 queries): crude
- **Macro** (15 queries): volatility, FX, rates
- **Market** (10 queries): positioning, structure

### Response Structure

```json
{
  "success": true,
  "results": [
    {
      "url": "https://example.com/article",
      "title": "Article Title",
      "description": "Article snippet..."
    }
  ]
}
```

### Classification Logic

1. **Region**: Auto-detected from title + description using keyword matching
2. **Source Type**: Classified from domain (gov_press, social_media, news_api, google_search)
3. **Prefix Buckets**: Mapped from category (policy_* → 'policy', trade_* → 'trade', etc.)
4. **Sentiment**: Rule-based classification using keyword matching
5. **Confidence**: Based on source credibility (government=1.0, premium news=0.95, etc.)
6. **Unique ID**: MD5 hash of URL for deduplication

## API Key Management

All API keys stored in macOS Keychain:

- **ScrapeCreators**: `cbi-v14.SCRAPE_CREATORS_KEY`
- **NewsAPI**: `cbi-v14.NEWSAPI_KEY` (optional)
- **Alpha Vantage**: `cbi-v14.ALPHA_VANTAGE_API_KEY`

Access via `src.utils.keychain_manager.get_api_key('KEY_NAME')`

## Collection Workflow

1. **Run Collection Script:**
   ```bash
   python3 scripts/ingest/collect_policy_trump.py
   ```

2. **Output:**
   - Raw files: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/policy_trump/policy_trump_YYYYMMDD_HHMM.parquet`
   - Includes all sources: Truth Social, Social Media, Google Search, RSS, ICE, Tariffs, Executive Orders

3. **Run Staging:**
   ```bash
   python3 scripts/staging/create_staging_files.py
   ```

4. **Output:**
   - Staging file: `staging/policy_trump_signals.parquet`
   - Ready for join pipeline

5. **Join Pipeline:**
   - Automatically picks up `staging/policy_trump_signals.parquet`
   - Joins on `date` with forward-fill
   - All columns prefixed with `policy_trump_*`

## Alpha Vantage Status

**⚠️ IMPORTANT:** Alpha Vantage collection is running in a separate shell. Do not start another full run.

- Script: `scripts/ingest/collect_alpha_vantage_comprehensive.py`
- Log: `/tmp/alpha_vantage_full_collection.log`
- Once complete: Rerun staging and proceed to join/backfill steps

## Testing Classification

Test classification functions:

```python
from scripts.ingest.collect_policy_trump import (
    classify_category_to_prefix_buckets,
    classify_source_type
)

# Test prefix bucket mapping
buckets = classify_category_to_prefix_buckets('trade_china')
# Returns: ['trade']

# Test source type
source_type = classify_source_type('https://www.usda.gov/news', 'usda.gov')
# Returns: 'gov_press'
```

## Key Files

- **Collection Script**: `scripts/ingest/collect_policy_trump.py`
- **Staging Function**: `scripts/staging/create_staging_files.py` → `create_policy_trump_staging()`
- **Join Spec**: `registry/join_spec.yaml` → `add_policy_trump` step
- **Schema Docs**: `docs/setup/POLICY_SCHEMA_CLASSIFICATION.md`
- **Status**: `docs/migration/DATA_COLLECTION_STATUS.md`

## Critical Rules

1. **All columns must have `policy_trump_*` prefix** (except `date`, `timestamp`)
2. **Every record must have `policy_trump_prefix_buckets`** (comma-separated)
3. **Every record must have `policy_trump_source_type`** (news_api, rss, gov_press, social_media, google_search)
4. **Every record must have `policy_trump_unique_id`** (for deduplication)
5. **Do not script manual sources** (EPA RIN, World Bank Pink Sheet, USDA FAS) until access confirmed
6. **Do not start new Alpha Vantage collection** (already running)

## Next Steps

1. Wait for Alpha Vantage collection to complete
2. Run `create_staging_files.py` to generate all staging files
3. Verify join spec picks up all staging files
4. Run join pipeline tests
5. Proceed to BigQuery backfill

