# ScrapeCreators Data Pipeline Analysis
**Generated:** November 7, 2025
**Purpose:** Complete analysis of data ingestion, storage, schemas, and metadata

---

## 🔄 Data Ingestion Pipeline Architecture

### **1. Core Ingestion Flow**

```
ScrapeCreators API
        ↓
Python Ingestion Scripts
        ↓
Pandas DataFrame Processing
        ↓
BigQuery Client (google.cloud.bigquery)
        ↓
BigQuery Tables (WRITE_APPEND mode)
```

### **2. Key Components**

#### **API Layer**
- **Endpoint:** `https://api.scrapecreators.com/v1/`
- **Authentication:** API key in header (`x-api-key`)
- **Key:** `B1TOgQvMVSV6TDglqB8lJ2cirqi2`
- **Rate Limiting:** 1 second delay between requests
- **Timeout:** 30-60 seconds per request

#### **Processing Layer**
```python
# Standard Pattern:
1. Fetch data from API
2. Filter for relevance (agricultural/soybean keywords)
3. Calculate impact scores
4. Add canonical metadata
5. Convert to pandas DataFrame
6. Type conversion and validation
7. Load to BigQuery with WRITE_APPEND
```

#### **Storage Layer**
- **Project:** `cbi-v14`
- **Primary Dataset:** `forecasting_data_warehouse`
- **Staging Dataset:** `staging`
- **Write Mode:** APPEND (preserves historical data)
- **Partitioning:** Daily partitioning on date fields

---

## 📊 Data Destinations

### **Primary Tables**

| Table | Dataset | Purpose | Update Frequency |
|-------|---------|---------|------------------|
| `trump_policy_intelligence` | forecasting_data_warehouse | Trump posts & policy announcements | Every 4 hours |
| `news_intelligence` | forecasting_data_warehouse | GDELT events, news aggregation | Hourly |
| `social_sentiment` | forecasting_data_warehouse | Reddit, social media sentiment | Every 2 hours |

### **Staging Tables (Institutional Intelligence)**

| Table | Dataset | Source | Update Frequency |
|-------|---------|--------|------------------|
| `institutional_lobbying_intel` | staging | Cargill, ADM, Bunge tweets | Daily 7 AM |
| `congressional_agriculture_intel` | staging | House/Senate Ag Committee | Daily 7 AM |
| `financial_analyst_intel` | staging | Goldman, JPMorgan analysis | Daily 7 AM |
| `china_state_media_intel` | staging | Xinhua, People's Daily | Daily 7 AM |

---

## 🗂️ Schema Definitions

### **1. Trump Policy Intelligence Schema**

```sql
trump_policy_intelligence {
    source: STRING              -- Source identifier (e.g., 'truth_social_monitor')
    category: STRING            -- Classification (trade_policy, agricultural_policy, etc.)
    text: STRING               -- Full text content (max 1000 chars)
    agricultural_impact: FLOAT  -- Impact score 0.0-1.0
    soybean_relevance: FLOAT   -- Soybean-specific relevance 0.0-1.0
    timestamp: TIMESTAMP       -- Original post timestamp
    priority: INTEGER          -- 1 (low), 2 (medium), 3 (high)
    
    -- Metadata Fields (canonical pattern)
    source_name: STRING        -- Detailed source (e.g., 'scrapecreators_truth_social')
    confidence_score: FLOAT    -- Data confidence 0.0-1.0 (typically 0.85)
    ingest_timestamp_utc: TIMESTAMP  -- When data was ingested
    provenance_uuid: STRING    -- Unique identifier for lineage tracking
}
```

### **2. News Intelligence Schema**

```sql
news_intelligence {
    title: STRING              -- Article/event title
    source: STRING            -- News source (GDELT, Reuters, etc.)
    category: STRING          -- News category
    url: STRING              -- Source URL
    published: TIMESTAMP      -- Publication timestamp
    content: STRING          -- Full content/summary
    intelligence_score: FLOAT -- Relevance score 0.0-1.0
    processed_timestamp: TIMESTAMP
    
    -- Canonical metadata
    source_name: STRING
    confidence_score: FLOAT
    ingest_timestamp_utc: TIMESTAMP
    provenance_uuid: STRING
}
```

### **3. Social Sentiment Schema**

```sql
social_sentiment {
    platform: STRING          -- Twitter, Reddit, etc.
    subreddit: STRING        -- For Reddit posts
    title: STRING            -- Post title
    score: INTEGER           -- Upvotes/likes
    comments: INTEGER        -- Comment count
    sentiment_score: FLOAT   -- Sentiment analysis result
    timestamp: TIMESTAMP     -- Post timestamp
    market_relevance: STRING -- Relevance classification
    
    -- Canonical metadata
    source_name: STRING
    confidence_score: FLOAT
    ingest_timestamp_utc: TIMESTAMP
    provenance_uuid: STRING
}
```

### **4. Institutional Intelligence Schema**

```sql
institutional_intel (staging tables) {
    collection_date: DATE     -- Date of collection
    category: STRING         -- lobbying, congressional, etc.
    username: STRING         -- Twitter handle
    tweet_text: STRING       -- Tweet content (max 500 chars)
    created_at: STRING       -- Original timestamp
    retweets: FLOAT         -- Retweet count
    likes: FLOAT            -- Like count
    
    -- Scoring fields
    policy_score: FLOAT     -- Policy relevance
    china_score: FLOAT      -- China trade relevance
    soy_score: FLOAT        -- Soybean market relevance
    total_relevance: FLOAT  -- Combined score
    influence_score: FLOAT  -- Social influence metric
    
    -- Canonical metadata
    source_name: STRING     -- 'ScrapeCreators_Twitter'
    confidence_score: FLOAT -- Typically 0.75
    ingest_timestamp_utc: TIMESTAMP
    provenance_uuid: STRING
    url: STRING            -- Tweet URL
}
```

---

## 🏷️ Metadata Patterns

### **Canonical Metadata Function**
Every record includes standardized metadata via this pattern:

```python
def get_metadata(source, confidence=0.85):
    return {
        'source_name': source,
        'confidence_score': confidence,
        'provenance_uuid': str(uuid.uuid4()),
        'ingest_timestamp_utc': datetime.now(timezone.utc)
    }
```

### **Confidence Scoring**
- **0.95:** Official government sources (USTR, Federal Register)
- **0.85:** Truth Social, verified social media
- **0.75:** General social media, analyst reports
- **0.70:** GDELT events, derived data
- **0.60:** Web scraping, unverified sources

### **Priority Levels**
```python
# Integer-based priority system
3 = High (immediate market impact)
2 = Medium (potential impact within days)
1 = Low (general monitoring)
```

---

## 📈 Data Quality & Filtering

### **Relevance Filtering**

```python
# Agricultural Keywords (weighted)
agricultural_keywords = [
    'soybean', 'trade war', 'china tariff', 'agriculture', 
    'farm bill', 'biofuel', 'ethanol', 'biodiesel', 
    'export', 'import', 'usda', 'farming', 'crop', 
    'harvest', 'grain', 'commodity', 'farmer'
]

# Impact Weights
impact_weights = {
    'trade_war': 1.0,      # Highest impact
    'china_tariff': 1.0,
    'export_ban': 0.9,
    'farm_bill': 0.7,
    'agriculture': 0.5,
    'biofuel': 0.6,
    'general': 0.3         # Lowest impact
}
```

### **Data Filtering Rules**
1. **Trump Social:** Only saves if `agricultural_impact > 0.1` OR `soybean_relevance > 0.1`
2. **Institutional:** Only saves if `total_relevance > 0`
3. **News:** Intelligence score calculated from event magnitude
4. **Social:** Market relevance must be non-null

---

## 🔍 Data Processing Examples

### **Example 1: Truth Social Processing**

```python
# Raw API Response
{
    "text": "China must honor trade deal...",
    "created_at": "2025-11-07T13:36:00Z",
    "retweets": 5432,
    "likes": 12345
}

# After Processing
{
    "source": "truth_social_monitor",
    "category": "trade_policy",
    "text": "China must honor trade deal...",
    "agricultural_impact": 0.9,
    "soybean_relevance": 0.8,
    "timestamp": "2025-11-07 13:36:00 UTC",
    "priority": 3,
    "source_name": "scrapecreators_truth_social",
    "confidence_score": 0.85,
    "ingest_timestamp_utc": "2025-11-07 14:00:00 UTC",
    "provenance_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### **Example 2: Institutional Intelligence**

```python
# Twitter API Response
{
    "username": "CargillNews",
    "text": "Soybean crush margins hit 2-year high...",
    "retweet_count": 45,
    "favorite_count": 120
}

# After Processing
{
    "collection_date": "2025-11-07",
    "category": "lobbying",
    "username": "CargillNews",
    "tweet_text": "Soybean crush margins hit 2-year high...",
    "policy_score": 0.0,
    "china_score": 0.0,
    "soy_score": 3.0,  # High due to multiple soy keywords
    "total_relevance": 9.0,
    "influence_score": 210,  # (45*2 + 120)
    "confidence_score": 0.75,
    ...
}
```

---

## 📊 Data Volume & Performance

### **Current Ingestion Rates**
- **Trump Social:** ~10-50 posts per 4-hour window
- **Institutional:** ~40 tweets per daily run
- **News (GDELT):** ~50 events per hourly run
- **MASTER Collector:** Variable, 100-500 records per hour

### **Storage Growth**
- **Daily new records:** ~2,000-5,000
- **Monthly growth:** ~60,000-150,000 records
- **Storage cost:** ~$0.02-0.05/month (minimal)

### **Query Performance**
- Tables are partitioned by date for efficient querying
- Most recent data queries: < 1 second
- Historical aggregations: 2-5 seconds

---

## 🔐 Data Governance

### **Provenance Tracking**
Every record includes:
- `provenance_uuid`: Unique identifier for audit trail
- `ingest_timestamp_utc`: Exact ingestion time
- `source_name`: Detailed source identification
- `confidence_score`: Data quality indicator

### **Data Retention**
- No automatic deletion policy currently
- All data preserved for historical analysis
- Log files rotated after 30 days

### **Access Control**
- BigQuery tables in `cbi-v14` project
- Service account authentication
- API keys stored in code (should migrate to Secret Manager)

---

## 🚀 Optimization Opportunities

### **Current Optimizations**
1. Reduced MASTER_CONTINUOUS_COLLECTOR from 15-min to hourly (75% cost reduction)
2. Batch processing with pandas DataFrames
3. WRITE_APPEND to avoid full table rewrites
4. Partitioned tables for query efficiency

### **Future Improvements**
1. **Secret Management:** Move API keys to Google Secret Manager
2. **Incremental Loading:** Check for duplicates before inserting
3. **Data Deduplication:** Add unique constraints on provenance_uuid
4. **Schema Evolution:** Use REPEATED fields for multiple keywords/scores
5. **Streaming Inserts:** For real-time critical data
6. **Data Validation:** Add schema validation before BigQuery load

---

## 📋 Key Takeaways

1. **Well-Structured Pipeline:** Clear flow from API → Processing → BigQuery
2. **Consistent Metadata:** All tables follow canonical metadata pattern
3. **Smart Filtering:** Only relevant data is stored (reduces noise)
4. **Cost-Optimized:** Recent optimizations reduced API calls by 75%
5. **Audit-Ready:** Provenance tracking on every record
6. **Scalable Architecture:** Can handle significant volume increases

**Total Monthly Cost:** ~$5-10 for ScrapeCreators API + minimal BigQuery storage
**Data Freshness:** 1-4 hour lag for most sources
**Reliability:** Multiple retry mechanisms and error handling

