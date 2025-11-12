# CBI-V14: Comprehensive Data Ingestion Audit

**Objective:** To create a centralized, authoritative inventory of all data ingestion pipelines, their schedules, sources, and destinations. This document will serve as the single source of truth for our data landscape, ensuring the new Vertex AI build is based on a complete and verified understanding of our assets.

---

| Source Category                | Data Provider / System      | Ingestion Script(s)                                   | Ingestion Mechanism                                     | Destination BigQuery Table(s)                             | Schedule / Frequency |
| ------------------------------ | --------------------------- | ----------------------------------------------------- | ------------------------------------------------------- | --------------------------------------------------------- | -------------------- |
| **Internal (Vegas)**           | Glide (Kevin's System)      | `ingest_glide_vegas_data.py`                            | Glide API (`api.glideapp.io`)                           | `forecasting_data_warehouse.vegas_*` (8 tables)           | Manual / On-demand   |
| **Social & News Intelligence** | Scrape Creator API          | `scrape_creators_full_blast.py`, `trump_truth_social_monitor.py` | REST API (`api.scrapecreators.com`)                   | `forecasting_data_warehouse.trump_policy_intelligence`    | 4-hourly (cron)      |
| **Market Prices**              | Yahoo Finance               | `pull_yahoo_complete_enterprise.py`, `backfill_prices_yf.py` | `yfinance` Python Library                               | `yahoo_finance_comprehensive.all_drivers_224_universe`    | **Daily (cron)**         |
| **Economic**                   | FRED                        | `fred_economic_deployment.py`, `economic_intelligence.py` | FRED REST API (`api.stlouisfed.org`)                    | `forecasting_data_warehouse.economic_indicators`          | Daily (cron)         |
| **Commodities**                | USDA FAS                    | `ingest_usda_export_sales_weekly.py`, `ingest_usda_harvest_real.py` | Web Scrape (`apps.fas.usda.gov`)                        | `forecasting_data_warehouse.china_soybean_imports`, `forecasting_data_warehouse.usda_harvest_progress` | Weekly               |
| **Biofuel**                    | EPA / EIA                   | `ingest_epa_rin_prices.py`, `ingest_epa_rfs_mandates.py`, `ingest_eia_biofuel_real.py` | Web Scrape (`www.epa.gov`, `www.eia.gov`)               | `forecasting_data_warehouse.biofuel_prices`, `forecasting_data_warehouse.rfs_mandates` | Weekly / Monthly     |
| **Sentiment**                  | CFTC                        | `ingest_cftc_positioning_REAL.py`                       | Web Scrape / Direct Download (`www.cftc.gov`)           | `forecasting_data_warehouse.cftc_cot`                     | Weekly               |
| **Weather**                    | INMET, IEM, NOAA            | `unified_weather_scraper.py`, `ingest_brazil_weather_inmet.py`, `ingest_midwest_weather_iem.py` | APIs & Direct Scrapes                                   | `forecasting_data_warehouse.weather_daily`                | Daily (cron)         |
| **Logistics**                  | Web Sources                 | `ingest_baltic_dry_index.py`, `ingest_port_congestion.py`, `ingest_argentina_port_logistics.py` | Web Scrape                                              | `forecasting_data_warehouse.logistics_metrics`            | Daily (cron)         |

---

### Audit Notes:

*   **Scheduling:** The primary scheduling mechanism appears to be `setup_enhanced_cron.sh` and `setup_daily_cron.sh`. These scripts need to be reviewed to confirm the exact frequency of each job.
*   **Centralization:** There are multiple scripts for similar tasks (e.g., several for social media). The audit will identify opportunities to consolidate these into single, more robust pipelines.
*   **Destinations:** Many scripts write to the `forecasting_data_warehouse` dataset. We need to verify that all data is correctly flowing from this warehouse into our `models_v4.vertex_ai_training_*_base` tables (or `production_training_data_*` if migrating). This connection is a potential point of failure.
*   **Manual vs. Automated:** Several key scripts (like the main Yahoo Finance pull) appear to be manual, on-demand processes. A key outcome of this audit will be to identify which of these should be automated.
