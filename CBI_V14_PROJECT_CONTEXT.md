# CBI-V14 PROJECT RULES - READ FIRST

**PASTE THIS AT THE START OF EVERY NEW CLAUDE CONVERSATION**

---

## 🚨 BIGQUERY WHITELISTED TABLES (USE THESE ONLY)

```
✅ weather_data (regions: 'US', 'Argentina', 'Brazil')
✅ volatility_data
✅ news_intelligence
✅ social_sentiment
✅ economic_indicators
✅ ice_trump_intelligence
✅ currency_data
✅ soybean_oil_prices
✅ soybean_oil_forecast
✅ soybean_prices
✅ soybean_meal_prices
✅ treasury_prices
✅ corn_prices
✅ cotton_prices
✅ cocoa_prices
✅ fed_rates
✅ backtest_forecast
✅ intelligence_cycles

ARCHIVES (read-only):
✅ commodity_prices_archive
✅ milk_prices_archive
```

---

## ❌ BANNED TABLE PATTERNS (NEVER CREATE)

```
❌ ANY table ending in: _test, _staging, _backup, _tmp, _validation, _v2
❌ Duplicate "weather" tables (e.g., weather_data_validation)
❌ Generic labels like "data", "temp", "test"
❌ Tables not on whitelist above
```

**If you need a new table: STOP and ask user first**

---

## 📋 EXISTING WEATHER_DATA SCHEMA

**Table:** `weather_data`  
**Purpose:** All weather data from all regions  
**Schema:**
```sql
date        DATE       (required)
region      STRING     (required: 'US', 'Argentina', 'Brazil')
station_id  STRING     (required: 'GHCND:xxx' or 'INMET_xxx')
precip_mm   FLOAT64    (precipitation in millimeters)
temp_max    FLOAT64    (max temperature in °C)
temp_min    FLOAT64    (min temperature in °C)
```

**Current Data:**
- US: 2,672 rows (GHCND:USW00014933, GHCND:USW00094846)
- Argentina: 1,342 rows (GHCND:AR000875760, GHCND:AR000875850)
- Brazil: 0 rows (NEEDS INMET DATA)

**Station ID Prefixes:**
- `GHCND:` = NOAA stations (US, Argentina)
- `INMET_` = Brazilian meteorology stations

---

## 🇧🇷 BRAZIL WEATHER STATIONS (ALREADY DEFINED)

**DO NOT CREATE NEW STATION LISTS - USE THESE:**

```python
INMET_STATIONS = {
    "A901": {"name": "Sorriso", "state": "Mato Grosso", "lat": -12.5446, "lon": -55.7125},
    "A923": {"name": "Sinop", "state": "Mato Grosso", "lat": -11.8653, "lon": -55.5058},
    "A936": {"name": "Alta Floresta", "state": "Mato Grosso", "lat": -9.8709, "lon": -56.0862},
    "A702": {"name": "Campo Grande", "state": "MS", "lat": -20.4427, "lon": -54.6479},
    "A736": {"name": "Dourados", "state": "MS", "lat": -22.2192, "lon": -54.8055}
}
```

**Target:** Add Brazil rows to EXISTING `weather_data` table with `region='Brazil'`

---

## 📁 WHITELISTED FOLDERS ONLY

```
✅ cbi-v14-ingestion/  (data ingestion scripts)
✅ forecast/            (FastAPI service)
✅ bigquery_sql/        (SQL scripts)
✅ dashboard/           (React dashboard)
✅ terraform-deploy/    (infrastructure)

❌ BANNED: tmp/, temp/, backup/, test/, staging/
```

---

## 🔒 DATA SOURCES (APPROVED ONLY)

**✅ ALLOWED:**
- CSV files for historical prices (Barchart exports)
- INMET API/portal (Brazil weather, 2023-2025)
- NOAA GHCND (US/Argentina weather)
- FRED API (economic indicators)
- USDA APIs (agricultural data)
- Government sources only

**❌ BANNED:**
- Polygon.io (unreliable, failures)
- Yahoo Finance (inconsistent)
- Docker (we don't use containers)
- Milk/Dairy data (removed from scope)

---

## 🎯 CRITICAL RULES

### 1. APPEND, NEVER REPLACE
```python
# ✅ CORRECT
job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_APPEND"
)

# ❌ WRONG
job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_TRUNCATE"  # NEVER ON PRODUCTION TABLES
)
```

### 2. CHECK BEFORE CREATE
```bash
# Always check if table exists first
bq ls cbi-v14:forecasting_data_warehouse

# Check against whitelist
# If not on whitelist → STOP and ask user
```

### 3. NO MOCK DATA
```python
# ❌ WRONG
data = {"price": 50.0}  # Placeholder

# ✅ CORRECT
query = "SELECT * FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`"
data = client.query(query).to_dataframe()
```

### 4. PROTECT WORKING FORECAST
```
❌ DO NOT modify: soybean_oil_forecast
❌ DO NOT rename production tables
❌ DO NOT drop tables without explicit confirmation
```

---

## 📊 CURRENT PROJECT STATUS

**Working (Has Data):**
- ✅ ZL Prices: 519 rows (100% coverage)
- ✅ US Weather: 2,672 rows (89%)
- ⚠️ Argentina Weather: 1,342 rows (39% - needs backfill)
- ✅ Economic Indicators: 3,220 rows
- ⚠️ Treasury: 136 rows (26% - sparse)
- ⚠️ Volatility: 2 rows (0.2% - nearly empty)

**Empty (Needs Data):**
- ❌ Brazil Weather: 0 rows (CRITICAL - 50% of global soy production)
- ❌ Social Sentiment: 0 rows
- ❌ Shipping Alerts: 0 rows
- ❌ ICE/Trump Intel: 0 rows

**Phase:** Pre-training (data collection phase)

---

## 🎯 IMMEDIATE PRIORITIES

1. **Brazil Weather** - Add to existing `weather_data` table (no new tables)
2. **Argentina Backfill** - Add more rows to existing `weather_data` table
3. **Volatility Fix** - Add more rows to existing `volatility_data` table
4. **No Model Training** - Until all data pipelines operational

---

## 🚫 BANNED BEHAVIORS

```
❌ Creating _test, _staging, _validation, _tmp tables
❌ Proposing "clean" architectures with new tables
❌ Editing plan.md automatically
❌ Mock/fake/placeholder data
❌ Running DROP TABLE without confirmation
❌ Using Docker
❌ Adding milk/dairy data
```

---

## ✅ REQUIRED BEHAVIORS

```
✅ ls before create
✅ cat before overwrite
✅ bq ls before table operations
✅ Check whitelist before ANY new resource
✅ WRITE_APPEND to existing tables
✅ Real data or explicit "no data" states
✅ Ask when uncertain
```

---

## 📝 SCRIPT STATUS

**Current Scripts (cbi-v14-ingestion/):**
- `ingest_weather_noaa.py` - US/Argentina (working)
- `ingest_weather_inmet.py` - Brazil (ready to run, uses placeholder data until API implemented)
- `ingest_volatility.py` - VIX data (needs fixing)
- `economic_intelligence.py` - FRED/economic data (working)
- `multi_source_news.py` - News collection (test mode)
- `social_intelligence.py` - Social sentiment (not run yet)
- `shipping_intelligence.py` - Logistics (not run yet)
- `ice_trump_intelligence.py` - Policy intel (not run yet)

**All scripts use `safe_load_to_bigquery()` for batch loading**

---

## 🔑 KEY PRINCIPLE

**ONE TABLE PER DATA TYPE. MULTIPLE REGIONS IN SAME TABLE.**

```
✅ CORRECT: weather_data (regions: US, Argentina, Brazil)
❌ WRONG: weather_data_us, weather_data_brazil, weather_data_validation
```

---

**COMMIT THIS FILE. PASTE AT START OF EVERY CLAUDE CONVERSATION.**
Crystal Ball (CBI-V14) — Production Plan
0) What this document is
Single source of truth for how we build, run, and govern a soybean-oil intelligence and forecasting platform that actually ships. It replaces all prior “plan-ish” files. If it’s not here, it’s not a requirement.
For a project of this nature, adopting an agile, iterative approach is far superior to building the entire warehouse infrastructure upfront. Trying to create a complete system with all tables, views, and pipelines from the start is risky, costly, and prone to significant redesigns when business requirements inevitably change. 
A strategic, incremental build process allows you to deliver value quickly, gather crucial feedback, and adapt your design, all while keeping costs in check. 
Order of operations: Step-by-step agile build
Here is the recommended order of operations, focused on delivering the most critical insights first.
Phase 1: Foundation and first use case 
Define a core business objective. Identify the single most valuable insight the procurement dashboard can deliver. For example: "Predict the probability of a 5% increase in soybean oil prices in the next 30 days based on recent market and weather data." This helps define scope and prove value quickly.
Set up foundational infrastructure. Use Terraform to provision your basic Google Cloud environment. This includes:
The project hierarchy (procurement-ingestion, procurement-analytics, etc.).
Core networking.
Initial Cloud Storage buckets (raw, curated).
The main BigQuery dataset (procurement_data).
Implement the first data pipeline. Focus on the data sources essential for your initial objective.
Ingestion (Bronze Layer):
Build a pipeline for market data and one weather source. A Python script on Cloud Run or a simple Dataflow job can fetch and store this data in your raw Cloud Storage bucket.
Implement parsing for scraped data. If market sentiment data is scraped, the same job should include the logic to parse it and store the raw text or HTML in Cloud Storage.
Curate (Silver Layer):
Create a scheduled Dataflow batch job to read the raw data, perform parsing and cleaning, and load it into a curated BigQuery table (e.g., curated_market_data).
For scraped data: This is where the parsing logic is fully applied, standardizing the scraped data and loading it into a new curated table (e.g., curated_sentiment).
Build the initial ML model and reporting.
Analytics (Gold Layer):
Use a BigQuery scheduled query to join the curated data into a feature table for your BQML model.
Train the first BQML autoencoder model for anomaly detection on this initial dataset.
Create a simple dashboard view and connect it to Looker Studio to visualize the anomalies and provide a tangible, early result. 
Phase 2: Expand and refine 
Integrate new data sources. Add the next highest-priority data sources, such as macroeconomic indicators and a second weather source. Re-use your modular pipeline components from Phase 1.
Refine the data model. As you integrate new data, expand your BigQuery schema to incorporate it. Consider creating more granular curated tables and updating your central feature table.
Enhance the ML model. Add the new data to your feature table and retrain the BQML model. This improves its ability to find connections and detect anomalies.
Solicit feedback. Share the updated dashboard with stakeholders. Use their feedback to prioritize the next set of data sources and features. 
Phase 3: Mature and optimize (Ongoing)
Regularly review and optimize. Monitor your BigQuery and Dataflow costs. Refine query logic, adjust worker sizes, and tune your storage lifecycle policies to keep costs low.
Automate governance. As the project scales, automate schema checks, implement robust monitoring with budget alerts, and manage user permissions systematically.
Continue the iterative cycle. For every new insight or feature requested, follow the same agile process: ingest new data, curate, update the model, and deploy new views to the dashboard. 
The agile vs. full build approach for this project
Aspect 
Agile, iterative build (Recommended)
Full, upfront build (Discouraged)
Risk
Low. You test assumptions early and fail fast on a small, contained part of the project. If a data source is unfeasible, you learn quickly.
High. A large, up-front investment can fail spectacularly if requirements change, data quality is poor, or a key assumption is wrong.
Cost
Starts low, scales predictably. You only spend money on the infrastructure and data processing you need, when you need it.
High initial investment. You pay for infrastructure that may go unused or need significant refactoring.
Time to value
Fast. You deliver a functioning, valuable dashboard within weeks.
Slow. You must wait months for the full project to be completed before demonstrating any value.
Flexibility
High. The architecture is designed to evolve. Adding new data sources or changing models is a planned iteration, not a crisis.
Low. Changes late in the project are costly and time-consuming, as they require significant re-engineering.
Stakeholder engagement
High. Regular delivery of new insights keeps stakeholders engaged, builds trust, and provides a continuous feedback loop.
Low. Stakeholders are disengaged during the long development phase and may be resistant to the final product if it doesn't meet expectations.



1) Executive objectives
Primary outcome: cut soybean-oil procurement cost variance via timely, explainable Buy/Wait signals and risk flags usable by non-quants.
Business KPIs
Procurement of soybean oil for U.S. Oil Solutions


Signal hit ratio and drawdown containment (7d/30/90/180d horizons)


Time-to-signal from market-moving events (minutes to hour)


Dashboard SLA (freshness: ZL price ≤ 15 min, macro ≤ 1 day, weather ≤ 24 hours)


Model governance: backtest leakage=0, reproducible runs, versioned artifacts


Non-goals
No autonomous trading. Human-in-the-loop only.


No paid data contracts in Phase 1. Prefer official/free APIs over scraping where possible.



2) Target user experience (what ships)
4-page dashboard
Dashboard: primary signal (Buy/Wait + confidence + drivers), market gauges (Fed funds, 10Y yield, USD, VIX, crude, soy complex, palm oil), breaking news with impact score.


Sentiment: Trump/trade policy impact, Fear-&-Greed composite, ICE/labor/logistics risk.


Strategy: simple scenario sliders (rates, FX, tariffs, weather), hedge playbook blocks, spread regimes (ZL vs FCPO).


Risk: price VaR bands, stress test presets, FX exposures (USD/BRL, USD/CNY, USD/ARS), supplier concentration watchlist.


Signal contract with the user
Clear traffic-light action, stated horizon (7/30d), confidence band, top 3 drivers, and “what would change my mind.”



3) Data architecture (BigQuery-first, simple, enforceable)
Datasets (namespaces)
raw — ingestion landing (untouched, append-only)


staging — normalized features, pivots, unit fixes


curated — dashboard-ready joined views


models — featuresets, predictions, model metrics


bkp — point-in-time backups before destructive ops


deprecated — quarantined legacy artifacts pending deletion


This layered approach is the BigQuery way to keep ingestion, transformation, and serving concerns separate and auditable. Partition on event date; cluster by entity keys to control cost. Reddit+1
Naming convention
Tables: snake_case, no prefixes (e.g., soybean_oil_prices)


Views: vw_[domain]_[purpose]_[granularity] (e.g., vw_economic_daily)


Models: ml_[target]_[horizon]_[algo]_v# (e.g., ml_price_30d_dnn_v1)


Featuresets: ftr_[domain]_[granularity] (staging)


Columns: consistent time keys (time for intraday, date for daily), source_name, confidence_score, and ingest_ts_utc everywhere ingestion touches


Source of truth views (use these, do not duplicate)
vw_zl_features_daily


vw_economic_daily


vw_weather_daily


vw_volatility_daily


Freshness SLO
ZL/ZS/ZM and FX: ≤ 15 minutes


VIX, WTI, DXY, 10Y: ≤ same-day


Weather cropsheds: ≤ 24 hours


FAS Export Sales, CFTC COT: next business day from release



4) Source registry and acquisition policy (phase 1: official > scraped)
Hard rule: use official APIs or clearly permitted endpoints first. Scraping consumer sites like Yahoo/Investing routinely violates ToS; only use as last-ditch fallback with legal review, provenance flags, and throttling. Prefer TradingEconomics’ API if you have a license; otherwise avoid scraping their HTML.
Market & macro
CBOT Soy complex & energy proxies: keep your existing approved pipeline for ZL/ZS/ZM, crude, and DXY where it is contractually permitted. Add provenance.


FRED: Fed Funds, CPI, payrolls, 10Y yields via FRED API (official).


CFTC Commitments of Traders: weekly positioning tables from CFTC site.


USDA FAS Export Sales: weekly soy(-oil/meal/beans) sales from FAS ESR/ESRQS; use the public historical pages and Open Data portal where available. Foreign Agricultural Service+2USDA Apps+2


FX (critical pairs for soy oil)
USD/BRL, USD/CNY, USD/ARS, USD/MYR, USD/IDR. If TradingEconomics API access is licensed, use it; otherwise pivot to central-bank or FX reference sources that allow programmatic access, or a permitted market data API. Avoid scraping Yahoo Finance and Investing.com without explicit permission.
Weather & climate
NOAA NCEI Daily Summaries (PRCP, TMAX, TMIN) for U.S. benchmark regions.


NASA POWER ag meteorology and MODIS NDVI/EVI metadata for crop condition proxies.


Brazil (INMET/CONAB): INMET for stations; CONAB for official crop reports and progress. USDA Apps


Policy & biofuels
EPA Renewable Fuel Standard program updates (RVOs, compliance).


Brazil ANP biodiesel/SVO mandates: ANP portal.


EU: ReFuelEU Aviation and RED III references for SAF demand signals.


Geopolitics, news, lobbying
GDELT 2.1 Events API for trade/geo events and tone.


OpenSecrets API for lobbying spend and recipients in biofuels/energy.


USDA/Reuters/Brazil ag portals for structured news hooks (FAS “Data & Analysis”). Foreign Agricultural Service


Production & trade
FAOSTAT API for global soybean oil production/trade baselines.


Robots.txt & legal
 We will not automate against endpoints that forbid it. Prioritize API keys where available; log source_name, URL, terms link, and a confidence_score for each record.

5) Ingestion orchestration (no heroics, just reliability)
Driver: one hourly coordinator that routes tasks to modular collectors with backoff and jitter. Each collector writes to raw.*, enriches to staging.*, never straight into curated.*.
Minimum controls
Throttle per domain, randomized jitter


Idempotent writes keyed by (date or time, symbol|station|indicator)


Freshness sentinels per source; alert if stale beyond SLO


Persist raw payloads for failures with low confidence flags


Budget guardrails: partition pruning and small, targeted queries



Cost Optimization Best Practices & Tips

For a procurement dashboard focused on identifying opportunities, a daily refresh is often unnecessary and can be costly given the variety of data sources involved. Many of your data sources—like weather patterns and macroeconomic trends—change slowly, while others, like spot prices and sentiment, can fluctuate more rapidly. A balanced, strategic schedule will be most cost-effective. 
Strategic scheduling alternatives to a daily refresh
Rather than a single daily schedule for all data, use a tiered approach based on how frequently each data source changes. This is a form of cost optimization through data freshness management. 
Real-time or hourly updates (for high volatility data)
Use Pub/Sub and a streaming Dataflow job to update BigQuery in near real-time. Use this for data that can change quickly and have an immediate impact on procurement opportunities.
Data sources: Commodity spot prices and sentiment analysis (e.g., social media mentions, news headlines).
Rationale: Immediate price fluctuations and public sentiment shifts are key indicators for short-term opportunities.
Cost savings: Only process changes to this data, rather than re-running a full batch every day. 
Weekly or bi-weekly updates (for moderate volatility data)
Use scheduled Dataflow batch jobs or BigQuery scheduled queries to update on a weekly or bi-weekly cadence.
Data sources: Legislative changes, macroeconomic indicators, VIX, trade relations.
Rationale: These factors change less frequently than market prices, but still require regular monitoring for emerging trends.
Cost savings: Running a job once a week is significantly cheaper than running it every day. 
Bi-monthly or quarterly updates (for low volatility data)
This cadence is appropriate for data that changes seasonally or over longer periods.
Data sources:
Weather data: Focus on major seasonal patterns rather than daily forecasts.
Labor for agriculture: Wage and labor market trends change more slowly.
Harvest rates: Crop data and harvest yields are seasonal.
Rationale: These trends inform long-term strategy rather than tactical day-to-day decisions.
Cost savings: Reduces processing significantly and aligns updates with seasonal business cycles. 
Dynamic or event-driven updates (for maximum cost savings)
For maximum optimization, combine scheduled updates with event-driven triggers.
When to use: For data that only needs an update when a specific event occurs.
How it works: Create Cloud Functions that are triggered by a relevant external event (e.g., an email from a data provider, a file uploaded to Cloud Storage). This initiates a targeted data pipeline for just that change.
Example: If a trade relations agreement changes, an event-driven function can immediately update the relevant data without waiting for the next scheduled job. 
Model retraining strategy
Since model retraining is a significant cost factor, use a combination of automated monitoring and a strategic schedule.
Fixed schedule: Use BQML to retrain your neural network on a quarterly or bi-monthly basis. This incorporates new seasonal data and trends.
Performance-based triggers: Set up monitoring on your model's performance metrics (e.g., accuracy, precision) in BigQuery. Use a Cloud Function or Cloud Monitoring alert to automatically trigger a retraining pipeline only if the model's performance degrades significantly.
Online learning (for anomalies): Use the ML.DETECT_ANOMALIES function in BQML daily on new data without a full retraining. This allows you to catch immediate outliers and flag them for human review, without incurring the high cost of retraining the full model. 
Cost-saving tactics across the board
Optimize BigQuery usage:
Continue to use partitioning, clustering, and materialized views to minimize data scanned.
Switch to Flex slots if you have a predictable, recurring weekly workload for a stable, lower cost than on-demand pricing for that period.
Right-size Dataflow jobs:
Use the smallest machine types that meet your performance needs.
Set maximum worker limits to prevent uncontrolled autoscaling.
Implement FinOps practices:
Use Google Cloud's native billing tools to set budgets and alerts for each of your pipelines.
Regularly clean up old or unused BigQuery tables and Cloud Storage objects using lifecycle management rules. 

Data flow Tips and pipeline structure notes
Your data will follow a layered approach, often referred to as a medallion architecture (bronze, silver, gold), which is a best practice for managing data quality and transformations. 
1. Bronze layer (Raw)
This layer ingests data with minimal processing. It serves as a durable, inexpensive, and replayable storage of the raw source data.
Ingestion tools:
Scraped data: Use a Python script with libraries like BeautifulSoup or Scrapy, running on Cloud Functions or a Cloud Run job.
The scraping job is triggered on a Cloud Scheduler schedule (e.g., weekly or bi-weekly).
The scraped data (raw HTML, JSON, or text) is written directly to a Cloud Storage bucket.
External APIs (e.g., S&P Global, Macroeconomic data): A Cloud Function or Cloud Run job pulls data from APIs and stores the raw JSON or CSV files in Cloud Storage.
Streaming data (e.g., sentiment): A streaming Dataflow job ingests data from Pub/Sub, performing minimal transformations, and writes it to a raw BigQuery table.
Storage: Cloud Storage for scraped and API data, BigQuery for streaming data.
Table/storage structure:
Cloud Storage: Use a folder structure like raw/<data_source>/<scrape_date>/<filename>.
BigQuery: Create raw tables with a schema that matches the source data. Example: raw_dataset.sentiment_raw, raw_dataset.s_and_p_raw. 
2. Silver layer (Curated)
This layer cleans, standardizes, and enriches the raw data, making it reliable and ready for analytics.
Transformation tools:
Dataflow (Batch): A scheduled Dataflow batch job reads the raw data from Cloud Storage, performs parsing and transformation, and writes clean, structured data into BigQuery. For example, it would parse the scraped HTML to extract specific text or table data.
BigQuery Scheduled Queries (ELT): For less frequent or simpler transformations, use scheduled queries to read from the raw BigQuery tables and write into the curated tables.
Storage destination: BigQuery (curated datasets).
Parsing scraped data: The Dataflow batch job will use a Python script containing the parsing logic.
It reads the raw files from Cloud Storage.
Uses a library like BeautifulSoup to navigate the HTML structure and extract the necessary information (e.g., text, tables, links).
Creates a structured record for each data point (e.g., date, source URL, extracted text).
Tables: Curated tables will be partitioned by date and clustered on a relevant key to optimize for later queries.
Example: curated_dataset.sentiment_weekly (partitioned by week_end_date), curated_dataset.weather_by_country (partitioned by report_date, clustered by country_code). 
3. Gold layer (Analytics)
This layer contains final, aggregated data, views, and ML models, optimized for reporting and analysis.
Platform: BigQuery.
Tables:
Feature Table: A partitioned and clustered table containing all the features for your ML model. It's built from the curated tables.
Example: analytics_dataset.ml_features (partitioned by date, clustered by country_code).
Views: Use views to encapsulate business logic and provide a simplified interface for reporting without re-running complex queries.
Aggregated Views: Create views that aggregate data for your dashboard.
Example: analytics_dataset.vw_weekly_trends (aggregates weekly data from curated tables).
Pre-filtered Views: Create views that apply filters for different users or roles, leveraging row-level security.
Example: analytics_dataset.vw_my_data (shows only data relevant to the current user).
ML Model: The trained BQML model is also stored in this layer.
Example: analytics_dataset.soybean_oil_anomaly_model. 
Example flow for scraped legislative data
1. Scrape and store (Bronze)
Action: A Cloud Run job is triggered weekly by Cloud Scheduler.
Process: The job scrapes government websites for legislative changes affecting agriculture.
Result: Raw HTML files are saved to gs://procurement-raw/legislative/<yyyy-mm-dd>/<country_code>_page_1.html. 
2. Parse and curate (Silver)
Action: A scheduled Dataflow batch job is triggered automatically by the completion of the scraping job.
Process: The Dataflow job:
Reads the raw HTML files from Cloud Storage.
Parses the HTML using BeautifulSoup to extract specific bill numbers, dates, and summaries.
Performs validation and data type conversion.
Loads the structured data into curated_dataset.legislative_changes in BigQuery, partitioned by date. 
3. Analyze and model (Gold)
Action: A BigQuery Scheduled Query runs weekly.
Process: The query:
Joins the curated_dataset.legislative_changes with other curated tables (e.g., macroeconomic indicators).
Creates a feature table (analytics_dataset.ml_features) for the ML model.
The BQML model detect_anomalies identifies any unusual legislative changes that correlate with other data points.
View: The reporting team accesses a view, analytics_dataset.vw_legislative_impacts, which joins the anomaly detection results with the original legislative data. 
Best practices for views
Materialize when needed: For frequently accessed, aggregated views, materialize the view into a new table or use a materialized view. This significantly reduces query costs and latency.
Keep logic simple: Views should primarily encapsulate a single, clear piece of business logic or filtering.
Use them for security: Views can be a powerful security tool to hide sensitive columns or apply row-level security.
Manage complexity: Use table functions or stored procedures for highly complex pipelines involving multiple steps to avoid complex, nested views. 
AI responses may include mistakes. Learn more

6) Feature engineering (staging to curated)
Standardized keys and units
Time: UTC; time for intraday, date for daily


Prices in USD/short-ton equivalents where needed; document conversions


Weather aggregated to production regions with 7d/30d windows and a simple, transparent risk score


Core features available to all models
Technicals: SMAs, momentum, realized vol from ZL


Spreads & regimes: ZL vs FCPO, ZL vs ZM/ZS


Macro: Fed Funds, 10Y, DXY, WTI, VIX


FX: USD/BRL, USD/CNY, USD/ARS


Supply/demand: FAS weekly sales, COT net positioning


Weather: precip and temperature windows; NDVI metadata


Policy/sentiment: GDELT event scores, lobbying intensity, RFS/ANP/EU event flags



7) Modeling strategy (BigQuery ML + importable TF for “neurals”)
Phase 1 — Baselines in BigQuery ML
Linear/boosted trees for 7d/30d direction; calibrated probabilities


DNN regressor/classifier in BigQuery ML for nonlinearity on tabular features


All trained and scored inside BigQuery for low-ops, with model artifacts versioned in models.* and results in models.predictions_* Google Cloud+1


Phase 2 — Neural nets where it helps
Train richer architectures in TF outside BQ (for example sequence models for multi-horizon signals), then import the SavedModel into BigQuery ML for SQL-native prediction, or register as a remote model via Vertex AI. This keeps scoring close to the data while preserving MLOps hygiene. Google Cloud+1


Model governance
Walk-forward evaluation, embargo windows, feature drift monitoring


SHAP or permutation importances for driver summaries


Model card per version: training window, featureset hash, backtest metrics, caveats



8) The eight canonical curated views (only these feed the UI)
vw_dashboard_executive — primary signal, gauges, deltas, top drivers


vw_market_indicators_daily — Fed funds, DXY, 10Y, WTI, VIX, palm oil


vw_weather_daily — production-region weather aggregates, risk index


vw_volatility_daily — realized/impl vol composites for ZL


vw_zl_features_daily — joined price features + indicators for modeling


vw_china_market — FAS sales to CN, reserves proxy, tariff flags


vw_policy_biofuel — EPA RFS, ANP, EU SAF/RED events + impact scores


vw_risk_dashboard — VaR bands, stress metrics, FX exposure slices


Non-negotiable rules
These views join from existing foundation views; no hidden logic or hard-coded constants beyond innocuous display labels.


Anything not used by the dashboard is either deprecated or staged for a specific approved UI component.



9) Data quality & monitoring
Four checks we always run
Freshness vs SLO per view (alerts on breach)


Completeness (null ratios over thresholds)


Uniqueness (date/time keys not duplicated)


Distribution shift (simple KS or z-score drift)


Lineage & provenance
For every record: source_name, ingest_ts_utc, and (where relevant) provenance_ref


For every model: dataset lineage, feature registry pointer, and metrics snapshot



10) Security, access, and budget
Principle of least privilege across datasets; read-only to curated.* for dashboards


Rotate API keys; secrets kept outside repo


Cost control: partition pruning, cached extracts for UI, avoid cross-joins; follow Google Cloud’s published guidance on partitioning and clustering to keep scans cheap. Reddit



11) Delivery plan (no heroics, staged, reversible)
Phase A — Foundation (now)
Lock dataset layout and naming


Fix broken weather pipeline (currently 9 days stale) to hit SLO


Validate the three source-of-truth views (economic, weather, ZL features)


Phase B — Dashboard feeds
Stand up the eight curated views in dependency order


Wire the four dashboard pages to curated views only


Put gauges on the home page: Fed funds, 10Y, ZL, ZS, ZM, FCPO, WTI, DXY, VIX, plus breaking-news feed with impact score


Phase C — Modeling
Ship 7d direction baseline with explainability in BigQuery ML


Add 30d horizon and spread regime overlays


Graduate to imported TF model if and only if the baseline earns its keep


Phase D — Hardening
CI rules for naming, DQ gates, and view dependency order


Deprecate and then delete redundant views after two clean weekly cycles



12) Risks and how we neutralize them
ToS violations from scraping → Prioritize official APIs and permissive portals; TradingEconomics/Yahoo/Investing HTML scraping is a last resort with legal review and low-confidence tagging.


Data staleness → SLO monitors with pager notifications; weather fixed first


Model overfitting / leakage → Walk-forward, embargo, and feature registry reviews


Policy shocks → Biofuel tracker wired to EPA/ANP/EU sources, not blogs.


Geopolitical data noise → Use GDELT carefully; aggregate to daily with sentiment bounds and entity filters.



13) What we will not do again
Duplicate existing working views under new names


Point dashboards at anything but curated.*


Merge brittle one-off scrapers without provenance columns


Ship ML without documented drivers and governance



14) Appendix — source specifics you asked to keep, cleaned
FX pairs: USD/BRL, USD/CNY, USD/ARS, USD/MYR, USD/IDR — keep as priority; store bid/ask/mid and timestamp; provenance and confidence required.
Futures & prices: ZL/ZS/ZM and energy proxies via approved, permitted feeds; if you must use fallbacks, mark confidence low and throttle heavily.
Macro: FRED (Fed funds, CPI, payrolls, 10Y); BLS PPI (official releases).
Weather: NOAA NCEI daily summaries (US), NASA POWER; Brazil INMET stations; convert to region aggregates with a transparent weather risk index.
Remote sensing: MODIS NDVI/EVI metadata as cadence checks and seasonal proxies.
USDA/CONAB/BAGE: WASDE and weekly crop progress (USDA); CONAB monthly reports (Brazil); wire release-watchers to trigger ingestion notes. USDA Apps
CFTC COT: weekly net positioning for soybeans/soy oil — compute z-scores.
Ports/logistics: Brazil (Santos/Paranaguá) and Argentina (Rosario) official sites — light-touch metadata; expect fragile HTML, prefer PDFs/CSV when offered.
News & lobbying: USDA FAS “Data & Analysis,” GDELT for event stream, OpenSecrets for lobbying flows tied to biofuels. Foreign Agricultural Service
Policy trackers: EPA RFS updates, ANP, EU ReFuelEU/RED for SAF and biodiesel mandates.
Production/trade: FAOSTAT for long-horizon baselines.
Historical Futures Data

https://www.mrci.com/ohlc/ohlc-01.php

https://portaracqg.com/historical-futures-tick-level-1/

https://tradingeconomics.com/forecast/commodity

https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm

https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm

https://www.cftc.gov/


Comprehensive Free/Public Data Sources:
Market Data: Essential for tracking price movements, trading volumes, and market sentiment. This includes real-time and historical soybean oil futures prices and open interest from CME Group, historical and real-time futures data from, long-term commodity price trends from Macrotrends, and commodity price data via 
Supply & Demand / Crop Yields: Official government reports are foundational. Data will be sourced from USDA WASDE reports for crop production and demand forecasts and USDA NASS for free CSV formatted yield and production data [Contractor's Idea].
Policy & Regulatory: Policy changes, particularly those related to Sustainable Aviation Fuel (SAF) and renewable fuels, have a direct and significant impact on demand and pricing. Relevant data will come from Biofuel Basics (energy.gov) for SAF and biodiesel policy updates, GovTrack.us for legislative data on SAF tax credits, and European Commission press releases regarding directives like the EU's updated Renewable Energy Directive draft.
Weather & Climate: Weather patterns are critical for predicting crop yields and potential supply disruptions. Sources include OpenWeatherMap for forecasts, NOAA for climate data like La Niña probabilities, and additional APIs like Visual Crossing Weather and Weatherbit Ag-Weather for more granular agricultural weather insights [Contractor's Idea].
News & Sentiment: News and social media sentiment provide real-time qualitative insights into market mood and emerging issues. This includes real-time agricultural updates from USDA X (@USDA), market-related news articles via NewsAPI, and regulatory/market impact news from Biofuels International Magazine [Contractor's Idea]. The aim is to analyze sentiment from these sources to influence soybean markets [Contractor's Idea].
Lobbying & Influence: To uncover "obscure correlations" between political activity and market outcomes, data from OpenSecrets.org on biofuel industry lobbying influence will be integrated.
Global Production & Trade: FAOStat will provide macro-level data on global soybean oil production and trade.
Historical Data Integration: A comprehensive historical dataset from 2005 to 2025, including prices, volumes, and production from sources like Google Datasets Marketplace, USDA NASS, and FAOStat, is essential for training AI models, backtesting strategies, and identifying long-term trends.
Enterprise Scalability & Multi-Million Dollar Potential

The AI tool's value proposition extends significantly beyond US Oil Solutions, offering a substantial competitive edge for major industry players. Chris Stacy envisioned the tool benefiting companies like ADM and Wecoa [Meeting w/Chris, 00:43:36]. The system is designed to support multi-user access for Chris's team and scale for enterprise clients such as ADM, which handles 7 million pounds annually, and Premier, with an annual volume of 60 million pounds. For Premier, the potential cost savings could reach millions of dollars annually, underscoring the immense financial upside and value proposition of offering such cost avoidance through the AI tool [Meeting w/Chris, 00:44:30].
The following table summarizes the projected annual cost avoidance and scalability:
Client/Entity
Annual Volume (lbs)
Current Cost Avoidance (Manual/Hunch)
Projected Annual Cost Avoidance (AI-Enabled)
Basis for Projection
US Oil Solutions
7 Million
$250,000 (one-time)
$250,000+
Replicating past success; small price advantage per lb
ADM
7 Million
N/A
Hundreds of Thousands
Scaled from US Oil Solutions' success
Premier
60 Million
N/A
Millions
Scaled from US Oil Solutions' success


C. The "Split The Difference" (STD) Strategy

The AI tool is poised to significantly enhance US Oil Solutions' unique "Split The Difference" (STD) strategy, where a portion of the cost savings achieved through strategic purchasing is shared with customers [Meeting w/Chris, 00:39:14]. By consistently generating substantial cost avoidance, the AI strengthens this value-sharing model, fostering deeper customer loyalty and providing a distinct competitive advantage over market participants who primarily focus on spot market pricing.
The "Split The Difference" strategy, when consistently supported by the AI's ability to generate significant cost avoidance, transforms US Oil Solutions from a mere supplier into a strategic partner for its clients. This shifts the relationship from a transactional focus on the lowest price to a collaborative model centered on shared value. This is a powerful competitive differentiator, as it aligns US Oil Solutions' success directly with its clients' profitability, fostering more resilient business relationships than competitors who might only focus on spot market pricing. This approach could lead to increased market share, higher customer retention, and potentially premium pricing for the value-added service of market intelligence, moving beyond traditional commodity margins.
Furthermore, Chris Stacy's observation that his company maintains higher profit margins compared to competitors due to strategic buying, and his emphasis on the risks associated with buying on the spot market versus anticipating price movements [Meeting w/Chris, 00:45:49, 00:46:56], highlights another critical benefit. The AI's capacity to provide predictive "green lights" enables US Oil Solutions to move away from the inherent volatility and often lower margins of spot market purchasing. By facilitating proactive, informed futures contract purchases, the AI helps lock in favorable prices, significantly reducing exposure to sudden market spikes and ensuring more consistent, higher profit margins. This represents a fundamental shift in procurement strategy, moving from reactive purchasing to strategic, risk-mitigated acquisition, thereby actively optimizing profitability and enhancing the company's financial health and long-term sustainability in a highly competitive market.

VII. Strategic Recommendations & Future Outlook

The development of the "Crystal Ball" AI tool is a strategic imperative that promises to redefine US Oil Solutions' market position and unlock significant value.

Recommendations for Ongoing Refinement & Expansion

Beyond the initial deployment, continuous refinement and expansion will be crucial to maintain the AI's competitive edge. This involves iteratively developing and enhancing the AI's correlation models and conversational capabilities based on ongoing user feedback and evolving market dynamics. A progression from keyword-based sentiment analysis to more sophisticated Natural Language Processing (NLP) is recommended for a nuanced understanding of news and reports. Furthermore, implementing rigorous processes for validating the AI's predictive capabilities against historical data will build confidence in its "green light" signals and ensure its ongoing accuracy.



The "Crystal Ball" AI: Vision, Capabilities, and User Experience

The "Crystal Ball" AI is envisioned as an intelligence amplifier, designed to provide actionable insights and empower strategic decision-making within the soybean oil market.

A. Core Vision & Conversational Intelligence

The central concept behind the AI is that of a "reverse Google search." Instead of passively waiting for a query, the AI proactively synthesizes vast amounts of information to answer complex, forward-looking questions such as "How will SAF policies, lobbying, and weather affect soybean oil prices in 2026?". This metaphor clearly communicates the AI's proactive nature and its ability to connect disparate data points to address strategic inquiries. To ensure broad accessibility for non-technical users, the AI will feature an intuitive conversational interface. Chris Stacy expressed a desire for a broad overview with specific command inputs, and Kirk Musick offered to create a chat interface for easier interaction [Meeting w/Chris, 00:32:10]. This design choice makes powerful AI insights readily available to the entire team.

B. Key Functionalities for Strategic Decision-Making

The AI tool will integrate several key functionalities to provide comprehensive market intelligence:
Market Pulse Indicators (Red/Yellow/Green): The system will translate complex data into simple, actionable signals using a red/yellow/green indicator system. Chris Stacy clarified that the AI is not expected to make purchasing decisions but rather to provide these indicators to support human speculation and risk assessment [Meeting w/Chris, 00:37:12]. These indicators will be based on sentiment analysis, with specific thresholds (e.g., >0.7 score for green/buy, 0.3–0.7 for yellow/hold, <0.3 for red/wait) providing a clear, quantifiable basis for the recommendations.
Comprehensive Price & Trend Analysis: The tool will display historical data spanning 2005–2025, alongside real-time soybean oil prices, trading volumes, and open interest through interactive charts and tables. This foundational data, sourced from entities like CME Group, API Ninjas, and Trading Economics, is crucial for identifying trends and informing predictive analysis [Contractor's Idea].
Advanced Correlation & Predictive Insights: A key differentiator of the "Crystal Ball" AI is its ability to uncover obscure relationships that often elude manual analysis. This includes quantifying the influence of lobbying efforts (e.g., how $1.8 million in biofuel donations to a senator could increase 45Z tax credit odds by 70%, boosting SAF demand by 25%), the impact of SAF policies (e.g., India's 2% SAF target by 2030 potentially increasing U.S. exports by 5%), and the effects of weather risks (e.g., a 65% chance of La Niña cutting Brazil’s soybean yield by 4%). The AI will also track global events like Chinese purchase volumes and renewable fuel policy announcements. Kirk Musick confirmed that a well-trained AI could identify such unconventional correlations, providing a significant competitive advantage [Meeting w/Chris, 00:34:07].
Optional Local Market Intelligence (Las Vegas Reports): While the primary focus is global, the tool can generate optional daily reports on local demand trends in specific regions, such as Las Vegas. This includes insights into local restaurant developments, like the opening of new plant-based "ghost kitchens" driving demand for specific oils, and Yelp trend analysis showing increased mentions of certain oils. It can also track local economic indicators like tourism arrivals and trucking capacity tightness. These granular, micro-level insights demonstrate the tool's versatility and value for regional operations.
The AI's capacity to help the team make informed decisions even when Chris Stacy is unavailable [Meeting w/Chris, 00:29:22] points to its role as a knowledge transfer and succession planning mechanism. Chris Stacy's expertise, currently a blend of research and intuition, is being codified and made accessible through the AI. This mitigates key-person risk and facilitates the onboarding and upskilling of new team members, ensuring that the company's competitive edge is not solely dependent on one individual. The AI effectively acts as a digital mentor, embedding Chris's analytical approach into the system, which supports long-term business resilience and scalability.
Furthermore, the emphasis on identifying "unconventional correlations" [Meeting w/Chris, 00:34:07] or "obscure correlations" signifies a profound capability. These are relationships that human analysts, due to cognitive biases, data overload, or time constraints, would likely miss. By connecting seemingly disparate data points—such as political donations to policy changes, which then impact commodity prices—the AI provides foresight that competitors relying on traditional analysis will lack. This elevates the insights from merely descriptive to truly predictive and strategic, enabling proactive market positioning to capitalize on emerging trends or mitigate risks before they become widely apparent.
The following table summarizes the key functionalities and their strategic impact:
Functionality
Description
Example Output/Insight
Strategic Impact
Conversational Interface
Natural language interaction for complex queries.
"SAF policies boost demand by 25%, prices to $0.48/lb."
Empowers non-technical users; facilitates intuitive access to deep analysis.
Market Pulse Indicators
Color-coded signals (red/yellow/green) for market sentiment and actionability.
"Green light for buy based on >0.7 sentiment score."
Enables rapid decision-making; translates complex data into actionable signals.
Advanced Correlation Analysis
Uncovers hidden relationships between disparate data points.
"Lobbying efforts increase 45Z tax credit odds by 70%, boosting SAF demand."
Uncovers hidden market drivers; provides unique competitive foresight.
Local Market Intelligence
Optional reports on regional demand and economic signals.
"New ghost kitchens drive local demand for avocado oil."
Provides granular regional insights; supports localized procurement strategies.

Updated Source Matrix (snap-in)
Category
Source
Type
Destination (raw/staging)
Notes
Futures/Prices
CME/CBOT ZL/ZS/ZM, Google Datasets
API/Market
raw.prices_* → soybean_oil_prices, etc.
Daily close + intraday as available
Macro
WTI, DXY, 10Y, CPI, VIX
API
economic_indicators (narrow) → staging.ftr_economic_daily
Pivot to wide
Palm oil
Bursa/MPOB proxy
API/CSV
palm_oil_prices
Spread driver
Weather
NOAA, OpenWeather/Visual Crossing/Weatherbit
API
weather_data → staging.ftr_weather_daily
Region-level
Policy
EPA RFS, ANP, EU RED
Scraper/API
raw.policy_events → staging.ftr_biofuel_policy
Status + impact
Harvest
USDA NASS, CONAB, MAGyP
CSV/PDF
raw.harvest_* → staging.ftr_harvest_data
Crop progress, yield
Exports
USDA FAS
CSV
raw.fas_sales
China purchase pace
News
GDELT, Biofuels Intl., USDA posts
API/Scrape
raw.news_* → vw_news_intel_daily
Impact-scored
Social/Political
Scrape Creators (Trump Effect), Truth Social/X
Scrape/API
ice_trump_intelligence
Impact categories
Local ops
LV events JSONL, Yelp/Eater
File/API
raw.local_ops
Optional regional lens


XII. Acceptance Gates (must pass before calling it “live”)
vw_dashboard_executive returns last 30 days; no duplicates; ≤10% null price.


Weather sentinel green (≤2 days stale).


Dashboard renders without custom SQL; indicators move with daily data.


ml_predictions exists and is writable by CI; dashboard shows signals from it (or placeholders until model live).


CI allowlist + DQ gates active; prod write access restricted to CI.



What we are not doing
No duplicate curated views mirroring prod views.


No writes to raw/staging/curated from notebooks or Cursor; only CI.


No model promotion without A/B and significance on live metrics.



C. Empowering Human Speculation

It is crucial to emphasize that the AI is designed as an augmentation tool, not a replacement for human judgment. Chris Stacy explicitly stated that the AI is not expected to make purchasing decisions but rather to provide indicators that support human speculation and risk assessment [Meeting w/Chris, 00:37:12]. Unlike automated trading systems, the "Crystal Ball" AI empowers users with deep, reasoned analyses, supporting strategic speculation and risk assessment even when key personnel are unavailable. This distinction ensures that human expertise and judgment remain central to the decision-making process, with the AI serving as an indispensable analytical partner.
ML / Neural Plan
Phase A (ship now, leak-safe)
Target: 30-day forward return on ZL.


Features: rolling returns/MA/vol; econ (Fed, DXY, WTI, 10Y, VIX); weather_risk_index; spreads.


Models: LightGBM + small GRU; ensemble average; isotonic calibration.


Validation: purged walk-forward with embargo; metrics: hit-rate, IR, RMSE.


Write: models.ml_predictions daily after market close.


Market Pulse Indicators (Red/Yellow/Green): The system will translate complex data into simple, actionable signals using a red/yellow/green indicator system. Chris Stacy clarified that the AI is not expected to make purchasing decisions but rather to provide these indicators to support human speculation and risk assessment [Meeting w/Chris, 00:37:12]. These indicators will be based on sentiment analysis, with specific thresholds (e.g., >0.7 score for green/buy, 0.3–0.7 for yellow/hold, <0.3 for red/wait) providing a clear, quantifiable basis for the recommendations.
Comprehensive Price & Trend Analysis: The tool will display historical data spanning 2005–2025, alongside real-time soybean oil prices, trading volumes, and open interest through interactive charts and tables. This foundational data, sourced from entities like CME Group, API Ninjas, and Trading Economics, is crucial for identifying trends and informing predictive analysis [Contractor's Idea].
Advanced Correlation & Predictive Insights: A key differentiator of the "Crystal Ball" AI is its ability to uncover obscure relationships that often elude manual analysis. This includes quantifying the influence of lobbying efforts (e.g., how $1.8 million in biofuel donations to a senator could increase 45Z tax credit odds by 70%, boosting SAF demand by 25%), the impact of SAF policies (e.g., India's 2% SAF target by 2030 potentially increasing U.S. exports by 5%), and the effects of weather risks (e.g., a 65% chance of La Niña cutting Brazil’s soybean yield by 4%). The AI will also track global events like Chinese purchase volumes and renewable fuel policy announcements. Kirk Musick confirmed that a well-trained AI could identify such unconventional correlations, providing a significant competitive advantage [Meeting w/Chris, 00:34:07].
Optional Local Market Intelligence (Las Vegas Reports): While the primary focus is global, the tool can generate optional daily reports on local demand trends in specific regions, such as Las Vegas. This includes insights into local restaurant developments, like the opening of new plant-based "ghost kitchens" driving demand for specific oils, and Yelp trend analysis showing increased mentions of certain oils. It can also track local economic indicators like tourism arrivals and trucking capacity tightness. These granular, micro-level insights demonstrate the tool's versatility and value for regional operations.
The AI's capacity to help the team make informed decisions even when Chris Stacy is unavailable [Meeting w/Chris, 00:29:22] points to its role as a knowledge transfer and succession planning mechanism. Chris Stacy's expertise, currently a blend of research and intuition, is being codified and made accessible through the AI. This mitigates key-person risk and facilitates the onboarding and upskilling of new team members, ensuring that the company's competitive edge is not solely dependent on one individual. The AI effectively acts as a digital mentor, embedding Chris's analytical approach into the system, which supports long-term business resilience and scalability.
Furthermore, the emphasis on identifying "unconventional correlations" [Meeting w/Chris, 00:34:07] or "obscure correlations" signifies a profound capability. These are relationships that human analysts, due to cognitive biases, data overload, or time constraints, would likely miss. By connecting seemingly disparate data points—such as political donations to policy changes, which then impact commodity prices—the AI provides foresight that competitors relying on traditional analysis will lack. This elevates the insights from merely descriptive to truly predictive and strategic, enabling proactive market positioning to capitalize on emerging trends or mitigate risks before they become widely apparent.
The following table summarizes the key functionalities and their strategic impact:
Functionality
Description
Example Output/Insight
Strategic Impact
Conversational Interface
Natural language interaction for complex queries.
"SAF policies boost demand by 25%, prices to $0.48/lb."
Empowers non-technical users; facilitates intuitive access to deep analysis.
Market Pulse Indicators
Color-coded signals (red/yellow/green) for market sentiment and actionability.
"Green light for buy based on >0.7 sentiment score."
Enables rapid decision-making; translates complex data into actionable signals.
Advanced Correlation Analysis
Uncovers hidden relationships between disparate data points.
"Lobbying efforts increase 45Z tax credit odds by 70%, boosting SAF demand."
Uncovers hidden market drivers; provides unique competitive foresight.
Local Market Intelligence
Optional reports on regional demand and economic signals.
"New ghost kitchens drive local demand for avocado oil."
Provides granular regional insights; supports localized procurement strategies.


C. Empowering Human Speculation

It is crucial to emphasize that the AI is designed as an augmentation tool, not a replacement for human judgment. Chris Stacy explicitly stated that the AI is not expected to make purchasing decisions but rather to provide indicators that support human speculation and risk assessment [Meeting w/Chris, 00:37:12]. Unlike automated trading systems, the "Crystal Ball" AI empowers users with deep, reasoned analyses, supporting strategic speculation and risk assessment even when key personnel are unavailable. This distinction ensures that human expertise and judgment remain central to the decision-making process, with the AI serving as an indispensable analytical partner.

IV. Data Architecture & Intelligence Framework

The foundation of the "Crystal Ball" AI's analytical power rests on a comprehensive and strategically assembled data architecture. This framework details the sourcing, integration, and processing of vast amounts of information.

A. Strategic Data Sourcing: The Foundation of Intelligence

A balanced approach to data sourcing is critical, combining premium, proprietary data with cost-effective public sources to maximize data quality while adhering to budgetary constraints.
Premium Data Sources & Their Unique Value: Access to client-provided premium sources like ProFarmer and Francis-Mustoe is paramount. These platforms offer specialized analyses, real-time commodity insights, and often proprietary reports that are difficult to replicate from public data, providing a significant competitive advantage.
Comprehensive Free/Public Data Sources:
Market Data: Essential for tracking price movements, trading volumes, and market sentiment. This includes real-time and historical soybean oil futures prices and open interest from CME Group, historical and real-time futures data from, long-term commodity price trends from Macrotrends, and commodity price data via 
Supply & Demand / Crop Yields: Official government reports are foundational. Data will be sourced from USDA WASDE reports for crop production and demand forecasts and USDA NASS for free CSV formatted yield and production data [Contractor's Idea].
Policy & Regulatory: Policy changes, particularly those related to Sustainable Aviation Fuel (SAF) and renewable fuels, have a direct and significant impact on demand and pricing. Relevant data will come from Biofuel Basics (energy.gov) for SAF and biodiesel policy updates, GovTrack.us for legislative data on SAF tax credits, and European Commission press releases regarding directives like the EU's updated Renewable Energy Directive draft.
Weather & Climate: Weather patterns are critical for predicting crop yields and potential supply disruptions. Sources include OpenWeatherMap for forecasts, NOAA for climate data like La Niña probabilities, and additional APIs like Visual Crossing Weather and Weatherbit Ag-Weather for more granular agricultural weather insights [Contractor's Idea].
News & Sentiment: News and social media sentiment provide real-time qualitative insights into market mood and emerging issues. This includes real-time agricultural updates from USDA X (@USDA), market-related news articles via NewsAPI, and regulatory/market impact news from Biofuels International Magazine [Contractor's Idea]. The aim is to analyze sentiment from these sources to influence soybean markets [Contractor's Idea].
Lobbying & Influence: To uncover "obscure correlations" between political activity and market outcomes, data from OpenSecrets.org on biofuel industry lobbying influence will be integrated.
Global Production & Trade: FAOStat will provide macro-level data on global soybean oil production and trade.
Historical Data Integration: A comprehensive historical dataset from 2005 to 2025, including prices, volumes, and production from sources like Google Datasets Marketplace, USDA NASS, and FAOStat, is essential for training AI models, backtesting strategies, and identifying long-term trends.
The sheer variety of these data sources—ranging from structured API feeds and CSVs to unstructured PDF reports, social media posts, and web-scraped articles—presents a significant technical undertaking. Each source may have different update frequencies, units of measurement, and data structures. Therefore, robust data cleaning, normalization, and the establishment of a standardized data model are absolutely critical. Without meticulous attention to data quality and consistency, the AI's ability to effectively process and correlate information across these disparate inputs would be severely compromised, leading to unreliable outputs. This necessitates a strong emphasis on data engineering in the initial phase, including continuous validation and pipeline monitoring to maintain data integrity and AI accuracy.



15) Acceptance criteria (what “done” means)
All four pages render off curated.* only, and every tile shows its data age


Freshness SLOs green for 7 consecutive days


Two clean weekly cycles of DQ checks with zero red gates


Signal cards show drivers with documented lineage and model version


A single deprecation PR removes redundant views after validation



16) Footnotes (why this plan is the way it is)
BigQuery layered datasets, partitioning, and clustering are how you keep performance and cost sane and transformations auditable. Reddit


Use Dataform or equivalent SQL-workflow tooling to version and orchestrate transformations; this is the supported path for BQ SQL pipelines. GitHub


BigQuery ML supports DNNs on tabular data and importing TensorFlow models for SQL-native prediction; that’s how we satisfy the “neurals” requirement without bolting on a separate serving stack. Google Cloud+2Google Cloud+2



