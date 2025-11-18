# Policy Schema Classification Guide

## Overview

All policy/shock signal data collected via `collect_policy_trump.py` follows a standardized prefix-based schema taxonomy. This ensures downstream joins, models, and dashboards can reason about data by topic, region, source, and sentiment with zero ambiguity.

## Prefix Bucket Taxonomy

Every record is classified into one or more prefix buckets:

### `policy_*`
- **Scope**: Lobbying, legislation, regulation, executive orders, EPA/USTR/White House releases
- **Examples**: 
  - `policy_lobbying`: Biofuel credit lobby, Farm Bill markup
  - `policy_legislation`: Renewable fuel standard legislation, agriculture subsidy bills
  - `policy_regulation`: EPA RFS announcements, CFTC rule changes

### `trade_*`
- **Scope**: Country-labeled trade items
- **Examples**:
  - `trade_china`: China soybean imports, China trade deals
  - `trade_argentina`: Argentina crush rate, Argentina soybean exports
  - `trade_palm`: Indonesian palm tax, Malaysia palm exports
  - `trade_currency`: Brazil real agriculture, FX agriculture impact

### `biofuel_*`
- **Scope**: RFS/RIN/biodiesel/ethanol spreads and policies
- **Examples**:
  - `biofuel_policy`: EPA biofuel announcements, RFS waivers
  - `biofuel_spread`: Petro renewable spread, ethanol gasoline spread

### `supply_*`
- **Scope**: Farm reports, weather, labor, crop progress (co-ops, NASS, USDA)
- **Examples**:
  - `supply_farm_reports`: Soybean yield reports, crop progress reports
  - `supply_labour`: Farm labor strikes, agriculture worker shortages
  - `supply_weather`: Drought soybean, flood corn harvest

### `logistics_*`
- **Scope**: River levels, ports, strikes, shipping constraints
- **Examples**:
  - `logistics_water`: Mississippi river levels, Parana river shipping
  - `logistics_port`: Port congestion agriculture, grain port delays
  - `logistics_strike`: Trucker strikes, rail strikes grain

### `macro_*`
- **Scope**: Volatility, FX, rates, Fed comments
- **Examples**:
  - `macro_volatility`: VIX agriculture, volatility soybean
  - `macro_fx`: Brazil real agriculture, Argentina peso crop
  - `macro_rate`: Fed agriculture, interest rate soybean

### `market_*`
- **Scope**: Positioning, market-structure, exchange rules/margin
- **Examples**:
  - `market_positioning`: CFTC soybean positions, speculator positions
  - `market_structure`: CME rule changes, margin hikes agriculture

### `energy_*`
- **Scope**: Crude/refinery/energy shocks (if not covered by biofuel)
- **Examples**:
  - `energy_crude`: Crude oil agriculture, oil price soybean

## Required Fields for Every Record

All records must include these fields (prefixed with `policy_trump_*`):

### Source Identification
- `policy_trump_source`: Source identifier (e.g., 'google_search', 'truth_social', 'rss')
- `policy_trump_source_type`: Type classification ('news_api', 'rss', 'gov_press', 'social_media', 'google_search')

### Content Fields
- `policy_trump_headline`: Article/post title
- `policy_trump_text`: Description/snippet/content
- `policy_trump_url`: Full URL

### Classification Fields
- `policy_trump_category`: Original category (e.g., 'policy_lobbying', 'trade_china')
- `policy_trump_prefix_buckets`: Comma-separated prefix buckets (e.g., 'policy', 'trade,biofuel')
- `policy_trump_query`: Query/keyword that triggered collection (for Google Search)
- `policy_trump_region`: Region classification ('US', 'Brazil', 'Argentina', 'China', 'SE_Asia', 'EU', 'Unknown')

### Metadata Fields
- `policy_trump_domain`: Source domain (e.g., 'reuters.com', 'usda.gov')
- `policy_trump_confidence`: Credibility score (0.5-1.0 based on source)
- `policy_trump_unique_id`: MD5 hash of URL for deduplication
- `policy_trump_language`: Language code (default 'en')

### Sentiment Fields
- `policy_trump_sentiment_score`: Sentiment score (-1 to +1)
- `policy_trump_sentiment_class`: Sentiment classification ('bullish', 'bearish', 'neutral')
- `policy_trump_bullish_keywords`: Count of bullish keywords found
- `policy_trump_bearish_keywords`: Count of bearish keywords found
- `policy_trump_categories`: Policy categories detected (comma-separated)

### Temporal Fields
- `timestamp`: Full timestamp
- `date`: Date for daily joins

## Classification Logic

### Category → Prefix Bucket Mapping

The `classify_category_to_prefix_buckets()` function maps categories to prefix buckets:

```python
# Policy bucket
if category.startswith('policy_'):
    return ['policy']

# Trade bucket
if category.startswith('trade_'):
    return ['trade']

# Biofuel bucket
if category.startswith('biofuel_'):
    return ['biofuel']

# Supply bucket
if category.startswith('supply_'):
    return ['supply']

# Logistics bucket
if category.startswith('logistics_'):
    return ['logistics']

# Macro bucket
if category.startswith('macro_'):
    return ['macro']

# Market bucket
if category.startswith('market_'):
    return ['market']

# Energy bucket
if category.startswith('energy_'):
    return ['energy']
```

### Source Type Classification

The `classify_source_type()` function determines source type:

- **Government sources** (`.gov`, `whitehouse.gov`, `federalregister.gov`) → `gov_press`
- **Social media** (`twitter.com`, `facebook.com`, `linkedin.com`, `truthsocial.com`) → `social_media`
- **Google Search** → `google_search`
- **Default** → `news_api`

### Region Classification

Regions are auto-detected from content using keyword matching:
- `US`: United States, USA, US, America, American
- `Brazil`: Brazil, Brazilian, Brasil
- `Argentina`: Argentina, Argentine, Argentinian
- `China`: China, Chinese, Beijing
- `SE_Asia`: Indonesia, Malaysia, Thailand, Philippines, Southeast Asia
- `EU`: European Union, EU, Europe, European

## Usage in Downstream Processing

### Filtering by Prefix Bucket

```python
# Get all policy-related records
policy_records = df[df['policy_trump_prefix_buckets'].str.contains('policy', na=False)]

# Get all trade-related records
trade_records = df[df['policy_trump_prefix_buckets'].str.contains('trade', na=False)]

# Get records spanning multiple buckets
multi_bucket = df[df['policy_trump_prefix_buckets'].str.contains(',', na=False)]
```

### Filtering by Region

```python
# Get China-related trade news
china_trade = df[
    (df['policy_trump_region'] == 'China') & 
    (df['policy_trump_prefix_buckets'].str.contains('trade', na=False))
]
```

### Filtering by Source Credibility

```python
# High-confidence sources only
high_confidence = df[df['policy_trump_confidence'] >= 0.9]

# Government sources only
gov_sources = df[df['policy_trump_source_type'] == 'gov_press']
```

### Sentiment Analysis

```python
# Bullish sentiment for ZL
bullish_zl = df[
    (df['policy_trump_sentiment_class'] == 'bullish') &
    (df['policy_trump_sentiment_score'] > 0.2)
]

# Bearish sentiment
bearish = df[df['policy_trump_sentiment_class'] == 'bearish']
```

## Integration with Staging Pipeline

All policy data flows through the same staging pipeline:

1. **Collection**: `collect_policy_trump.py` collects from all sources
2. **Classification**: Records are automatically classified with prefix buckets
3. **Staging**: Data is saved to `staging/policy_trump_signals.parquet`
4. **Joins**: Staging file is joined via `registry/join_spec.yaml`
5. **Training**: Features are extracted for model training

The consistent `policy_trump_*` prefix ensures all fields are recognized by the staging and join steps.

## Multi-Tag Support

Categories can span multiple prefix buckets (comma-separated):
- Example: A biofuel policy announcement might be tagged as `policy,biofuel`
- This allows flexible filtering and analysis across multiple dimensions

## Extending the Schema

To add new categories:

1. Add queries to `SEARCH_QUERIES` dictionary in `collect_policy_trump.py`
2. Ensure category name follows prefix pattern (e.g., `new_category_name`)
3. Update `classify_category_to_prefix_buckets()` if new prefix bucket needed
4. Add region keywords to `REGION_KEYWORDS` if new region needed
5. Add source credibility scores to `SOURCE_CREDIBILITY` if new domain needed

All new records will automatically inherit the classification logic and schema structure.

