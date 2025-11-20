# BigQuery Live Feeds Architecture Plan - CBI-V14

**Date:** January 2025  
**Status:** Implementation Plan  
**Purpose:** Complete architecture for BigQuery setup → Live feeds → Training → Dashboard

---

## 🎯 EXECUTIVE SUMMARY

**Complete Data Flow:**
```
External APIs → BigQuery (Live Feeds) → Local Mac (Training) → BigQuery (Predictions) → Dashboard (Vercel)
```

**Key Components:**
1. **BigQuery Setup** - Schemas, partitioning, clustering for time-series data
2. **Live Data Feeds** - Real-time ingestion from Databento, FRED, NewsAPI
3. **Training Export** - Efficient export from BigQuery to local Parquet
4. **Dashboard Integration** - BigQuery → Next.js/Vercel read-only access

**Cost:** ~$0.04-0.09/month (essentially free)

---

## 📊 PHASE 1: BIGQUERY SETUP

### 1.1 Schema Design

**Raw Data Layer** (`market_data` dataset):
```sql
-- Databento futures OHLCV (1-minute bars)
CREATE TABLE `cbi-v14.market_data.databento_futures_ohlcv_1m` (
  ts_event TIMESTAMP NOT NULL,
  root STRING NOT NULL,
  symbol STRING NOT NULL,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  volume INT64,
  ingest_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(ts_event)
CLUSTER BY root, symbol
OPTIONS(
  description="Databento 1-minute OHLCV bars, partitioned by date, clustered by root/symbol"
);

-- FRED economic indicators
CREATE TABLE `cbi-v14.market_data.fred_economic_indicators` (
  series_id STRING NOT NULL,
  date DATE NOT NULL,
  value FLOAT64,
  ingest_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY series_id;
```

**Curated Features Layer** (`features` dataset):
```sql
-- Curated features for training
CREATE TABLE `cbi-v14.features.curated_features_daily` (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  -- Price features
  databento_close FLOAT64,
  databento_volume INT64,
  -- Technical indicators (computed in-house from Databento OHLCV)
  rsi_14 FLOAT64,
  macd FLOAT64,
  -- Economic features
  fred_fed_funds_rate FLOAT64,
  fred_vix FLOAT64,
  -- Derived features
  returns_1d FLOAT64,
  volatility_30d FLOAT64,
  -- Metadata
  feature_hash STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol;
```

**Training Data Layer** (`training` dataset):
```sql
-- Training tables (already exist, verify structure)
-- training.zl_training_prod_allhistory_1w
-- training.zl_training_prod_allhistory_1m
-- training.zl_training_prod_allhistory_3m
-- training.zl_training_prod_allhistory_6m
-- training.zl_training_prod_allhistory_12m
```

**Predictions Layer** (`predictions` dataset):
```sql
-- Model predictions
CREATE TABLE `cbi-v14.predictions.zl_predictions_prod_allhistory_1w` (
  date DATE NOT NULL,
  horizon STRING NOT NULL,
  predicted_value FLOAT64,
  confidence_interval_lower FLOAT64,
  confidence_interval_upper FLOAT64,
  model_version STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY horizon;
```

### 1.2 Partitioning Strategy

**Best Practice:** Partition by DATE for time-series data
- **Raw data:** `PARTITION BY DATE(ts_event)` or `PARTITION BY date`
- **Benefits:** 
  - Query only relevant partitions (cost savings)
  - Automatic partition expiration (data retention)
  - Faster queries (partition pruning)

**Clustering Strategy:**
- **Raw data:** `CLUSTER BY root, symbol` (frequently filtered)
- **Features:** `CLUSTER BY symbol` (asset-specific queries)
- **Predictions:** `CLUSTER BY horizon` (horizon-specific queries)

### 1.3 Cost Optimization

**Storage:**
- Use MERGE/UPSERT (not append-only) to prevent duplicates
- Set partition expiration: `ALTER TABLE ... SET OPTIONS(partition_expiration_days=365)`
- Current storage: ~0.70 GB → $0.01/month

**Queries:**
- Always filter by date partition: `WHERE date >= '2020-01-01'`
- Use clustering for frequently filtered columns
- Limit query date ranges
- Free tier: 1 TB/month scanned → $0.00

**Ingestion:**
- Batch loads: FREE (unlimited)
- Streaming inserts: FREE (first 2 TB/month)
- Current usage: ~6 GB/month → $0.00

---

## 📥 PHASE 2: LIVE DATA FEEDS

### 2.1 Databento Live Feed

**Script:** `scripts/live/databento_live_poller.py` (already exists)

**Enhancement for BigQuery:**
```python
#!/usr/bin/env python3
"""
Enhanced Databento live poller with BigQuery streaming
"""
from google.cloud import bigquery
from google.cloud import storage
import databento as db
from src.utils.keychain_manager import get_api_key

def stream_to_bigquery(rows, table_id):
    """Stream data to BigQuery."""
    client = bigquery.Client(project='cbi-v14')
    table = client.get_table(table_id)
    
    errors = client.insert_rows_json(table, rows)
    if errors:
        print(f"❌ BigQuery errors: {errors}")
        return False
    return True

def main():
    # Get Databento API key
    api_key = get_api_key('DATABENTO_API_KEY')
    client = db.Historical(api_key)
    
    # Poll for new data
    while True:
        # Fetch latest 1-minute bars
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            symbols=['ZL.FUT'],
            schema='ohlcv-1m',
            start='2025-01-20T00:00:00',
            end='2025-01-20T23:59:59'
        )
        
        # Convert to BigQuery format
        rows = []
        for row in data:
            rows.append({
                'ts_event': row['ts_event'],
                'root': 'ZL',
                'symbol': row['symbol'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            })
        
        # Stream to BigQuery
        if rows:
            success = stream_to_bigquery(
                rows,
                'cbi-v14.market_data.databento_futures_ohlcv_1m'
            )
            if success:
                print(f"✅ Streamed {len(rows)} rows to BigQuery")
        
        time.sleep(60)  # Poll every minute

if __name__ == "__main__":
    main()
```

**Cron Setup:**
```bash
# Every 5 minutes
*/5 * * * * cd /path/to/CBI-V14 && python3 scripts/live/databento_live_poller.py --roots ZL,ES,CL
```

### 2.2 FRED Live Feed

**Script:** `scripts/ingest/collect_fred_comprehensive.py` (already exists)

**Enhancement:** Ensure it writes to BigQuery:
```python
# Verify it writes to: cbi-v14.market_data.fred_economic_indicators
# If not, add BigQuery upload logic
```

### 2.3 NewsAPI Live Feed

**Script:** `scripts/ingest/collect_news_sentiment.py` (create if needed)

```python
#!/usr/bin/env python3
"""
Collect news sentiment → BigQuery
"""
from google.cloud import bigquery
from src.utils.keychain_manager import get_api_key
import newsapi

def collect_sentiment():
    """Collect news sentiment and upload to BigQuery."""
    api_key = get_api_key('NEWSAPI_KEY')
    client = bigquery.Client(project='cbi-v14')
    
    # Collect news
    articles = newsapi.get_everything(
        q='soybean oil OR ZL futures',
        language='en',
        sort_by='publishedAt'
    )
    
    rows = []
    for article in articles:
        rows.append({
            'date': article['publishedAt'].date(),
            'title': article['title'],
            'sentiment_score': analyze_sentiment(article['content']),
            'source': article['source']['name']
        })
    
    # Upload to BigQuery
    table = client.get_table('cbi-v14.market_data.news_sentiment')
    errors = client.insert_rows_json(table, rows)
    
    if not errors:
        print(f"✅ Uploaded {len(rows)} news sentiment rows")
```

### 2.4 Idempotent Pipeline Pattern

**Use MERGE for upserts:**
```sql
MERGE INTO `cbi-v14.market_data.databento_futures_ohlcv_1m` AS target
USING staging_table AS source
ON target.ts_event = source.ts_event 
   AND target.symbol = source.symbol
WHEN MATCHED THEN
  UPDATE SET
    open = source.open,
    high = source.high,
    low = source.low,
    close = source.close,
    volume = source.volume
WHEN NOT MATCHED THEN
  INSERT (ts_event, root, symbol, open, high, low, close, volume)
  VALUES (source.ts_event, source.root, source.symbol, 
          source.open, source.high, source.low, source.close, source.volume);
```

**Benefits:**
- Safe to re-run (idempotent)
- No duplicates
- Updates existing records
- Handles failures gracefully

---

## 📤 PHASE 3: TRAINING DATA EXPORT

### 3.1 Export Script (Already Exists)

**Script:** `scripts/export_training_data.py`

**Current Implementation:**
- Exports from `training.zl_training_{surface}_allhistory_{horizon}`
- Saves to `TrainingData/exports/zl_training_{surface}_allhistory_{horizon}.parquet`
- Handles date column conversion

**Enhancement for Large Datasets:**
```python
def export_training_data_incremental(horizon: str, surface: str = "prod", 
                                     start_date: str = None, end_date: str = None):
    """
    Export training data incrementally (for large datasets).
    
    Args:
        horizon: One of '1w', '1m', '3m', '6m', '12m'
        surface: 'prod' or 'full'
        start_date: Start date (YYYY-MM-DD) - if None, exports all
        end_date: End date (YYYY-MM-DD) - if None, exports all
    """
    client = bigquery.Client(project='cbi-v14')
    table_ref = f"{PROJECT_ID}.training.zl_training_{surface}_allhistory_{horizon}"
    
    # Build query with date filter
    query = f"SELECT * FROM `{table_ref}`"
    if start_date or end_date:
        conditions = []
        if start_date:
            conditions.append(f"date >= '{start_date}'")
        if end_date:
            conditions.append(f"date <= '{end_date}'")
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY date"
    
    # Export in chunks (for very large datasets)
    df = client.query(query).to_dataframe()
    
    # Save to parquet
    output_file = f"TrainingData/exports/zl_training_{surface}_allhistory_{horizon}.parquet"
    df.to_parquet(output_file, index=False, engine='pyarrow')
    
    print(f"✅ Exported {len(df):,} rows to {output_file}")
```

### 3.2 Scheduled Export

**Cron Job:**
```bash
# Daily export at 3 AM
0 3 * * * cd /path/to/CBI-V14 && python3 scripts/export_training_data.py --surface prod --horizon all
```

### 3.3 Data Quality Validation

**Before Export:**
```bash
# Run data quality checks
python3 scripts/data_quality_checks.py

# Verify BigQuery tables
python3 scripts/verify_bigquery_tables.py
```

---

## 🎨 PHASE 4: DASHBOARD INTEGRATION

### 4.1 BigQuery → Vercel Connection

**Already Implemented:** `dashboard-nextjs/src/lib/bigquery.ts`

**Current Setup:**
- Uses `GOOGLE_APPLICATION_CREDENTIALS_BASE64` in Vercel
- Falls back to ADC locally
- Region: `us-central1`

**Verify Configuration:**
```bash
# In Vercel dashboard, ensure these env vars are set:
GCP_PROJECT_ID=cbi-v14
GOOGLE_APPLICATION_CREDENTIALS_BASE64=<base64-encoded-service-account-json>
```

### 4.2 Dashboard Queries

**Optimized Query Pattern:**
```typescript
// dashboard-nextjs/src/app/api/forecast/[horizon]/route.ts
export async function GET(request: Request, { params }: { params: { horizon: string } }) {
  const { horizon } = params;
  
  // Optimized query with date filter (partition pruning)
  const query = `
    SELECT 
      date,
      predicted_value,
      confidence_interval_lower,
      confidence_interval_upper,
      model_version
    FROM \`cbi-v14.predictions.zl_predictions_prod_allhistory_${horizon}\`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    ORDER BY date DESC
    LIMIT 100
  `;
  
  const client = getBigQueryClient();
  const [rows] = await client.query({
    query,
    location: 'us-central1',
  });
  
  return Response.json(rows);
}
```

**Cost Control:**
- Always filter by date partition
- Use LIMIT for pagination
- Cache results (5-minute refresh)
- Monitor query costs

### 4.3 Real-Time Data Refresh

**Strategy:**
- Dashboard polls BigQuery every 5 minutes
- Use Next.js API routes with caching
- Incremental updates (only fetch new data)

**Implementation:**
```typescript
// dashboard-nextjs/src/app/api/live-data/route.ts
export async function GET() {
  const query = `
    SELECT 
      ts_event,
      close,
      volume
    FROM \`cbi-v14.market_data.databento_futures_ohlcv_1m\`
    WHERE ts_event >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
      AND root = 'ZL'
    ORDER BY ts_event DESC
  `;
  
  const client = getBigQueryClient();
  const [rows] = await client.query({ query, location: 'us-central1' });
  
  return Response.json(rows, {
    headers: {
      'Cache-Control': 'public, s-maxage=300', // 5-minute cache
    },
  });
}
```

---

## 🔄 PHASE 5: COMPLETE WORKFLOW

### 5.1 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL DATA SOURCES                        │
├─────────────────────────────────────────────────────────────────┤
│  Databento (Futures)  │  FRED (Economic)                        │
│  NewsAPI (Sentiment)  │  (Technical indicators computed in-house)│
└───────────────────────┴─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              LIVE DATA FEEDS (Every 5 minutes)                  │
├─────────────────────────────────────────────────────────────────┤
│  scripts/live/databento_live_poller.py                         │
│  scripts/ingest/collect_fred_comprehensive.py                 │
│  scripts/ingest/collect_news_sentiment.py                      │
│  (Technical indicators computed in BigQuery from Databento OHLCV)│
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BIGQUERY (us-central1)                       │
├─────────────────────────────────────────────────────────────────┤
│  Raw Layer:                                                     │
│    - market_data.databento_futures_ohlcv_1m                     │
│    - market_data.fred_economic_indicators                       │
│    - market_data.news_sentiment                                 │
│                                                                 │
│  Curated Layer:                                                 │
│    - features.curated_features_daily                           │
│                                                                 │
│  Training Layer:                                                │
│    - training.zl_training_prod_allhistory_1w                   │
│    - training.zl_training_prod_allhistory_1m                    │
│    - training.zl_training_prod_allhistory_3m                   │
│    - training.zl_training_prod_allhistory_6m                    │
│    - training.zl_training_prod_allhistory_12m                   │
│                                                                 │
│  Predictions Layer:                                            │
│    - predictions.zl_predictions_prod_allhistory_1w             │
│    - predictions.zl_predictions_prod_allhistory_1m              │
│    - predictions.zl_predictions_prod_allhistory_3m              │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              TRAINING DATA EXPORT (Daily 3 AM)                   │
├─────────────────────────────────────────────────────────────────┤
│  scripts/export_training_data.py                                │
│  → TrainingData/exports/zl_training_prod_allhistory_*.parquet │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              LOCAL MAC M4 TRAINING                              │
├─────────────────────────────────────────────────────────────────┤
│  src/training/baselines/train_tree.py                          │
│  src/training/baselines/train_simple_neural.py                 │
│  → Models/local/{model}/                                       │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              PREDICTIONS UPLOAD                                  │
├─────────────────────────────────────────────────────────────────┤
│  scripts/upload_predictions.py                                  │
│  → predictions.zl_predictions_prod_allhistory_*                 │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              DASHBOARD (Vercel)                                  │
├─────────────────────────────────────────────────────────────────┤
│  dashboard-nextjs/src/app/api/forecast/[horizon]/route.ts      │
│  → Reads from predictions.* tables                              │
│  → Displays forecasts, charts, metrics                          │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Implementation Checklist

**Phase 1: BigQuery Setup**
- [ ] Create/verify raw data tables (partitioned, clustered)
- [ ] Create/verify curated features tables
- [ ] Create/verify training tables
- [ ] Create/verify predictions tables
- [ ] Set partition expiration policies
- [ ] Configure IAM roles and permissions

**Phase 2: Live Data Feeds**
- [ ] Enhance Databento poller with BigQuery streaming
- [ ] Verify FRED collector writes to BigQuery
- [ ] Create NewsAPI collector
- [ ] Compute technical indicators in BigQuery from Databento OHLCV
- [ ] Set up cron jobs (every 5 minutes)
- [ ] Implement idempotent MERGE patterns
- [ ] Add error handling and retry logic
- [ ] Set up monitoring and alerting

**Phase 3: Training Data Export**
- [ ] Verify export script works
- [ ] Test incremental export for large datasets
- [ ] Set up daily cron job (3 AM)
- [ ] Add data quality validation before export
- [ ] Test export → training pipeline

**Phase 4: Dashboard Integration**
- [ ] Verify BigQuery connection in Vercel
- [ ] Test API routes with real queries
- [ ] Optimize queries (partition pruning, clustering)
- [ ] Implement caching (5-minute refresh)
- [ ] Add query cost monitoring
- [ ] Test end-to-end: BigQuery → Dashboard

**Phase 5: Complete Workflow**
- [ ] Test complete flow: Live feeds → BigQuery → Export → Training → Predictions → Dashboard
- [ ] Monitor costs (should be ~$0.04-0.09/month)
- [ ] Set up alerts for failures
- [ ] Document all processes

---

## 💰 COST ESTIMATE

**Monthly Costs:**
- **Storage:** $0.01/month (0.70 GB)
- **Ingestion:** $0.00/month (FREE - under 2 TB)
- **Queries:** $0.00/month (FREE - under 1 TB scanned)
- **Total:** **$0.01-0.09/month** (essentially free)

**Cost Controls:**
- Use MERGE (not append-only) to prevent storage growth
- Always filter by date partition
- Use clustering for frequently filtered columns
- Monitor query costs in BigQuery console

---

## 🔒 SECURITY & IAM

**Service Accounts:**
- **Data Collector SA:** BigQuery Data Editor, Storage Object Admin
- **Training SA:** BigQuery Data Viewer, Storage Object Viewer
- **Dashboard SA:** BigQuery Data Viewer (read-only)

**API Keys:**
- All stored in macOS Keychain
- Retrieved via `src/utils/keychain_manager.py`
- Never hardcoded in code

**Access Control:**
- Dashboard: Read-only to `predictions.*` and public views
- Training: Read-only to `training.*`
- Collectors: Write to `market_data.*` and `features.*`

---

## 📚 NEXT STEPS

1. **Review this plan** - Verify it matches your requirements
2. **Create BigQuery tables** - Use SQL scripts in `config/bigquery/bigquery-sql/`
3. **Enhance live feed scripts** - Add BigQuery streaming
4. **Test export pipeline** - Verify training data export works
5. **Test dashboard connection** - Verify Vercel can read from BigQuery
6. **Deploy incrementally** - Start with one data source, then expand

---

**This plan provides a complete architecture for BigQuery → Live Feeds → Training → Dashboard. All components are based on existing codebase patterns and best practices.**
