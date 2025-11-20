---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# CBI-V14 Setup Checklist
**Purpose**: Get data collection and BigQuery running with DataBento-first strategy

---

## Phase 1: Verify Data Sources

### ✅ DataBento (Priority 1)

- [ ] DataBento API key in environment: `echo $DATABENTO_API_KEY`
- [ ] Test DataBento connection:
  ```bash
  python3 -c "import databento as db; client = db.Historical(os.environ['DATABENTO_API_KEY']); print(client.metadata.list_datasets())"
  ```
- [ ] Confirm DataBento plan includes GLBX.MDP3
- [ ] Verify symbols available: ES, MES, ZL, ZS, ZM, CL, NG, ZC, ZW, RB, HO, GC, SI, HG

### ✅ FRED (Priority 2)

- [ ] FRED API key in keychain:
  ```bash
  python3 -c "from src.utils.keychain_manager import get_api_key; print('OK' if get_api_key('FRED_API_KEY') else 'MISSING')"
  ```
- [ ] Test FRED API:
  ```bash
  curl "https://api.stlouisfed.org/fred/series/observations?series_id=DFF&api_key=$(python3 -c 'from src.utils.keychain_manager import get_api_key; print(get_api_key(\"FRED_API_KEY\"))')&limit=1&file_type=json"
  ```

### ✅ Alpha Vantage (Optional)

- [ ] Alpha Vantage API key in keychain:
  ```bash
  python3 -c "from src.utils.keychain_manager import get_api_key; print('OK' if get_api_key('ALPHA_VANTAGE_API_KEY') else 'MISSING')"
  ```
- [ ] Confirm Plan75 (75 calls/minute)

### ✅ Other APIs

- [ ] NOAA API key (if needed)
- [ ] NewsAPI key (if needed)
- [ ] ScrapeCreators key (if needed)

---

## Phase 2: Create BigQuery Tables

### Table 1: `market_data.futures_ohlcv_1m`

```sql
CREATE SCHEMA IF NOT EXISTS market_data
OPTIONS (
  location='us-central1',
  description='Market data from DataBento and other sources'
);

CREATE TABLE market_data.futures_ohlcv_1m (
  ts_event TIMESTAMP NOT NULL,
  root STRING NOT NULL,
  symbol STRING NOT NULL,
  instrument_id INT64,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  volume INT64,
  publisher_id INT64,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(ts_event)
CLUSTER BY root, symbol
OPTIONS (
  partition_expiration_days=365,
  description='DataBento GLBX.MDP3 1-minute OHLCV for futures'
);
```

**Run**:
```bash
bq mk --location=us-central1 --dataset cbi-v14:market_data
bq query --use_legacy_sql=false < scripts/sql/create_futures_ohlcv_table.sql
```

- [ ] Table created
- [ ] Partitioning verified
- [ ] Clustering verified

### Table 2: `raw_intelligence.fred_economic`

```sql
CREATE TABLE raw_intelligence.fred_economic (
  date DATE NOT NULL,
  series_id STRING NOT NULL,
  series_name STRING,
  value FLOAT64,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY series_id
OPTIONS (
  partition_expiration_days=1825,
  description='FRED economic indicators'
);
```

- [ ] Table created

### Table 3: `raw_intelligence.alpha_vantage`

```sql
CREATE TABLE raw_intelligence.alpha_vantage (
  date DATE NOT NULL,
  symbol STRING NOT NULL,
  indicator_type STRING,
  indicator_name STRING,
  value FLOAT64,
  metadata JSON,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY symbol, indicator_type
OPTIONS (
  description='Alpha Vantage technical indicators and options data'
);
```

- [ ] Table created

### Tables 4-7: Other domain tables

- [ ] `raw_intelligence.weather` (NOAA)
- [ ] `raw_intelligence.cftc_positioning` (CFTC)
- [ ] `raw_intelligence.eia_energy` (EIA)
- [ ] `raw_intelligence.news_sentiment` (NewsAPI)

---

## Phase 3: Upload Existing Domain Data

### Upload CFTC (172 MB)

```bash
python3 scripts/upload_cftc_data.py \
  --source "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/cftc" \
  --project cbi-v14 \
  --dataset raw_intelligence \
  --table cftc_positioning
```

- [ ] CFTC data uploaded
- [ ] Row count verified

### Upload FRED (7 MB)

```bash
python3 scripts/upload_fred_data.py \
  --source "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/fred" \
  --project cbi-v14 \
  --dataset raw_intelligence \
  --table fred_economic
```

- [ ] FRED data uploaded
- [ ] Row count verified

### Upload Alpha Vantage (30 MB)

```bash
python3 scripts/upload_alpha_vantage_data.py \
  --source "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/alpha_vantage" \
  --project cbi-v14 \
  --dataset raw_intelligence \
  --table alpha_vantage
```

- [ ] Alpha Vantage data uploaded (if using)

### Upload Weather (2.5 MB)

```bash
python3 scripts/upload_weather_data.py \
  --source "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/noaa" \
  --project cbi-v14 \
  --dataset raw_intelligence \
  --table weather
```

- [ ] Weather data uploaded

---

## Phase 4: Set Up DataBento Live Collection

### Option A: Run on Mac (Testing)

```bash
# Test once
python3 scripts/live/databento_live_poller.py --roots ES,ZL,CL --once

# Run in loop (every 5 minutes)
python3 scripts/live/databento_live_poller.py --roots ES,ZL,CL --interval 300
```

- [ ] Test run successful
- [ ] Data written to `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live/`
- [ ] Parquet files created with date partitions

### Option B: Run on GCP e2-micro (Production)

**1. Create VM**:
```bash
gcloud compute instances create cbi-databento-poller \
  --machine-type=e2-micro \
  --zone=us-central1-a \
  --image-family=debian-11 \
  --image-project=debian-cloud \
  --boot-disk-size=30GB \
  --metadata=startup-script='#!/bin/bash
apt-get update
apt-get install -y python3-pip
pip3 install databento pandas pyarrow google-cloud-storage google-cloud-bigquery'
```

- [ ] VM created in us-central1 (free tier)

**2. SSH and configure**:
```bash
gcloud compute ssh cbi-databento-poller --zone=us-central1-a

# On VM:
export DATABENTO_API_KEY="your_key_here"
echo "export DATABENTO_API_KEY=your_key_here" >> ~/.bashrc

# Copy poller script
# (upload via gcloud compute scp or git clone)

# Test
python3 databento_live_poller.py --roots ES,ZL,CL --once
```

- [ ] Script running on VM
- [ ] Data collecting successfully

**3. Set up cron**:
```bash
crontab -e

# Add:
*/5 * * * * cd /home/user && python3 databento_live_poller.py --roots ES,ZL,CL --once >> databento.log 2>&1
```

- [ ] Cron configured
- [ ] Running every 5 minutes

### Optional: Mirror to BigQuery

```bash
python3 scripts/live/databento_live_poller.py \
  --roots ES,ZL,CL \
  --interval 300 \
  --mirror-bq \
  --gcs-bucket cbi-v14-market-data \
  --bq-project cbi-v14 \
  --bq-dataset market_data
```

- [ ] GCS bucket created (if using)
- [ ] Data mirroring to BigQuery

---

## Phase 5: Set Up Domain Data Collection

### FRED Collection (Every 15 minutes)

```bash
# Test
python3 scripts/ingest/collect_fred_comprehensive.py --dry-run

# Add to cron
*/15 * * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_fred_comprehensive.py >> Logs/fred.log 2>&1
```

- [ ] FRED collector tested
- [ ] Cron configured
- [ ] Data uploading to BigQuery

### Alpha Vantage Collection (Every 15 minutes, if using)

```bash
# Test
python3 scripts/ingest/collect_alpha_vantage_comprehensive.py --dry-run

# Add to cron
*/15 * * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_alpha_vantage_comprehensive.py >> Logs/alpha.log 2>&1
```

- [ ] Alpha collector tested (if using)
- [ ] Cron configured

### Weather Collection (Daily)

```bash
# Test
python3 scripts/ingest/collect_noaa_comprehensive.py --dry-run

# Add to cron
0 6 * * * cd /path/to/CBI-V14 && python3 scripts/ingest/collect_noaa_comprehensive.py >> Logs/weather.log 2>&1
```

- [ ] Weather collector tested
- [ ] Cron configured

### CFTC Collection (Weekly, Friday)

```bash
# Test
python3 scripts/ingest/collect_cftc_comprehensive.py --dry-run

# Add to cron
0 17 * * 5 cd /path/to/CBI-V14 && python3 scripts/ingest/collect_cftc_comprehensive.py >> Logs/cftc.log 2>&1
```

- [ ] CFTC collector tested
- [ ] Cron configured

---

## Phase 6: Verify Data Flow

### Check DataBento Data

```bash
# Check external drive
ls -lh "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live/"
ls -lh "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live/ES/1m/"

# Check BigQuery (if mirroring)
bq query --use_legacy_sql=false "
SELECT 
  root,
  DATE(ts_event) as date,
  COUNT(*) as bars,
  MIN(ts_event) as first_bar,
  MAX(ts_event) as last_bar
FROM market_data.futures_ohlcv_1m
GROUP BY root, date
ORDER BY root, date DESC
LIMIT 20"
```

- [ ] Data on external drive
- [ ] Data in BigQuery (if mirroring)
- [ ] Volume looks correct (~390 bars/day per symbol)

### Check Domain Data

```bash
# FRED
bq query --use_legacy_sql=false "
SELECT series_id, COUNT(*) as count, MAX(date) as latest
FROM raw_intelligence.fred_economic
GROUP BY series_id
ORDER BY series_id"

# CFTC
bq query --use_legacy_sql=false "
SELECT commodity, COUNT(*) as count, MAX(report_date) as latest
FROM raw_intelligence.cftc_positioning
GROUP BY commodity"
```

- [ ] FRED data updating
- [ ] CFTC data present
- [ ] Other domain data present

---

## Phase 7: Monitor Costs

### Check BigQuery Storage

```bash
# Storage by dataset
bq ls --project_id=cbi-v14 --format=json | \
  jq -r '.[] | select(.kind=="bigquery#dataset") | .datasetReference.datasetId' | \
  while read ds; do
    echo "=== $ds ==="
    bq query --use_legacy_sql=false "
    SELECT 
      SUM(size_bytes) / POW(1024, 3) as size_gb,
      COUNT(*) as tables
    FROM \`cbi-v14.$ds.__TABLES__\`"
  done
```

- [ ] Total storage < 2 GB (Month 1)
- [ ] Well under 10 GB free tier

### Check Query Costs

GCP Console → BigQuery → Query History → View Usage

- [ ] Total scanned < 100 GB/month
- [ ] Well under 1 TB free tier

### Check VM Costs

GCP Console → Compute Engine → VM Instances

- [ ] e2-micro in us-central1 (free tier eligible)
- [ ] Uptime < 730 hours/month (should be exactly 730 for always-on)

---

## Phase 8: Update Documentation

- [ ] Update `DATA_SOURCE_STRATEGY.md` with actual symbols used
- [ ] Update `COST_SUMMARY_QUICK_REFERENCE.md` with actual costs
- [ ] Document any deviations from plan
- [ ] Create runbook for common operations

---

## Phase 9: Continuous Monitoring

### Daily Checks

- [ ] DataBento collection running (check logs)
- [ ] FRED/domain data updating
- [ ] BigQuery storage not growing unexpectedly
- [ ] No failed cron jobs

### Weekly Checks

- [ ] CFTC data updated (Friday)
- [ ] Review BigQuery costs
- [ ] Check for data gaps
- [ ] Verify backup to external drive

### Monthly Checks

- [ ] Review total costs (should be < $0.10 for BigQuery)
- [ ] Archive old data if needed
- [ ] Update documentation

---

## Summary

### Minimal Setup (Start Here)

1. ✅ Create BigQuery tables (market_data.futures_ohlcv_1m, raw_intelligence.*)
2. ✅ Upload existing FRED/CFTC domain data (~220 MB)
3. ✅ Set up DataBento live poller (Priority 1 symbols: ES, ZL, CL)
4. ✅ Configure FRED daily collection
5. ✅ Monitor for 1 week

**Cost**: $0.02/month (BigQuery only)

### Standard Setup

1. Everything in Minimal
2. Add all 13 DataBento symbols
3. Add Alpha Vantage collection (if using)
4. Add weather, USDA, EIA, CFTC
5. Mirror DataBento to BigQuery (optional)

**Cost**: $0.03-0.10/month (BigQuery only)

### Next Steps

Review `DATA_SOURCE_STRATEGY.md` and answer:
1. Which DataBento symbols? (7 Priority 1 or all 13?)
2. Mirror to BigQuery or keep on external drive?
3. Which supplementary sources? (Alpha, weather, etc.)
4. Run on Mac or GCP VM?


