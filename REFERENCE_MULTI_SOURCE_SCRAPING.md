# Multi-Source Comprehensive Scraping Plan
## Hourly Schedule for ALL Data Sources

**Date:** October 7, 2025  
**Principle:** Route ALL data to EXISTING BigQuery tables - NO NEW TABLES  
**Cost:** $0/month (all free web scraping)  
**Total URLs:** ~120-150 per hour (staggered)

---

## ✅ EXISTING BIGQUERY TABLES (DO NOT CREATE NEW ONES)

```
Core Tables (Data Ingestion):
├── weather_data (9,505 rows)
├── economic_indicators (3,220 rows)
├── currency_data (0 rows - ready for FX)
├── fed_rates (0 rows - ready for Fed data)
├── treasury_prices (136 rows)
├── volatility_data (776 rows)
├── commodity_prices_archive (4,017 rows)
├── soybean_oil_prices (519 rows)
├── soybean_prices (519 rows)
├── soybean_meal_prices (519 rows)
├── corn_prices (519 rows)
├── cotton_prices (519 rows)
├── cocoa_prices (441 rows)
├── milk_prices_archive (326 rows)
├── ice_trump_intelligence (166 rows)
├── news_intelligence (20 rows)
├── social_sentiment (20 rows)
└── intelligence_cycles (0 rows)

Palm Oil Tables (NEED TO CREATE - REQUEST PERMISSION):
├── palm_oil_prices (0 rows - NOT YET CREATED)
└── palm_oil_fundamentals (0 rows - NOT YET CREATED)

Views (Read-Only):
├── soy_oil_features
├── vw_weather_daily
├── vw_economic_daily
└── ... (30+ views - do not modify)
```

---

## 📅 HOURLY SCRAPING SCHEDULE (60-Minute Cycle)

### **Minute 0-6: FX Rates & Front-Month Prices (CRITICAL PATH)**

**Target Table:** `currency_data`

**Sources:**
```python
FX_SOURCES = [
    # Already covered by TradingEconomics scraper:
    ('currency_data', 'https://tradingeconomics.com/currency/usd-myr'),  # Malaysia
    ('currency_data', 'https://tradingeconomics.com/currency/usd-brl'),  # Brazil
    ('currency_data', 'https://tradingeconomics.com/currency/usd-ars'),  # Argentina
    ('currency_data', 'https://tradingeconomics.com/currency/usd-idr'),  # Indonesia
    ('currency_data', 'https://tradingeconomics.com/currency/usd-cny'),  # China
    
    # Additional FX sources (if TE fails):
    ('currency_data', 'https://www.investing.com/currencies/usd-myr'),
    ('currency_data', 'https://finance.yahoo.com/quote/USDBRL=X'),
]
```

**Parser:** Extract bid/ask/mid rate, timestamp  
**Storage Schema:**
```sql
currency_data: timestamp, currency_pair, rate, source_name, confidence_score
```

---

### **Minute 8-12: Futures & Commodity Prices (Barchart/Investing/Yahoo)**

**Target Tables:** 
- `soybean_oil_prices`
- `soybean_prices`
- `soybean_meal_prices`
- `corn_prices`
- `cotton_prices`
- `commodity_prices_archive` (crude oil, diesel)

**Sources:**
```python
FUTURES_SOURCES = [
    # Soybean complex
    ('soybean_oil_prices', 'https://www.barchart.com/futures/quotes/ZL*0/overview'),
    ('soybean_prices', 'https://www.barchart.com/futures/quotes/ZS*0/overview'),
    ('soybean_meal_prices', 'https://www.barchart.com/futures/quotes/ZM*0/overview'),
    
    # Grains
    ('corn_prices', 'https://www.barchart.com/futures/quotes/ZC*0/overview'),
    ('cotton_prices', 'https://www.barchart.com/futures/quotes/CT*0/overview'),
    
    # Energy (for freight/cost proxy)
    ('commodity_prices_archive', 'https://www.investing.com/commodities/brent-oil'),
    ('commodity_prices_archive', 'https://www.investing.com/commodities/crude-oil'),
    ('commodity_prices_archive', 'https://www.investing.com/commodities/heating-oil'),
    
    # Yahoo Finance fallbacks
    ('soybean_oil_prices', 'https://finance.yahoo.com/quote/ZL=F'),
    ('soybean_prices', 'https://finance.yahoo.com/quote/ZS=F'),
]
```

**Parser:** Extract contract, last price, change, volume, open interest  
**Throttling:** 1 req / 5-6s per domain  
**Storage Schema:**
```sql
soybean_oil_prices: time, symbol, open, high, low, close, volume, source_name, confidence_score
```

---

### **Minute 14-18: Macro APIs & FRED (Economic Data)**

**Target Tables:**
- `economic_indicators`
- `fed_rates`
- `treasury_prices`

**Sources:**
```python
MACRO_SOURCES = [
    # FRED indicators (scrape web pages, not API)
    ('fed_rates', 'https://fred.stlouisfed.org/series/FEDFUNDS'),
    ('treasury_prices', 'https://fred.stlouisfed.org/series/DGS10'),  # 10-year yield
    ('economic_indicators', 'https://fred.stlouisfed.org/series/CPIAUCSL'),  # CPI
    ('economic_indicators', 'https://fred.stlouisfed.org/series/PAYEMS'),  # Nonfarm payrolls
    
    # BLS (Bureau of Labor Statistics)
    ('economic_indicators', 'https://www.bls.gov/news.release/ppi.nr0.htm'),  # PPI
    
    # Additional from TradingEconomics (already covered):
    # - US/Brazil/China/Malaysia GDP, industrial production
]
```

**Parser:** Extract latest value, date, series metadata  
**Throttling:** 1 req / 5s (FRED allows scraping per robots.txt)  
**Storage Schema:**
```sql
economic_indicators: time, indicator, value, source_name, confidence_score
fed_rates: time, rate, source_name
treasury_prices: time, yield, source_name
```

---

### **Minute 20-24: Weather Stations (NOAA/INMET/Somar)**

**Target Table:** `weather_data`

**Sources:**
```python
WEATHER_SOURCES = [
    # NOAA stations (US Midwest - soybean belt)
    ('weather_data', 'https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&dataTypes=PRCP,TMAX,TMIN&stations=USC00110072'),  # Illinois
    ('weather_data', 'https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&dataTypes=PRCP,TMAX,TMIN&stations=USW00014819'),  # Iowa
    
    # INMET (Brazil - Mato Grosso)
    ('weather_data', 'https://portal.inmet.gov.br/dadoshistoricos'),  # Already covered by existing script
    
    # Somar Meteorologia (Brazil)
    ('weather_data', 'https://www.somarmeteorologia.com.br/'),
    
    # CONAGUA (Mexico - reservoirs)
    ('economic_indicators', 'https://www.gob.mx/conagua'),  # Reservoir levels → economic indicator
]
```

**Parser:** Extract station_id, lat/lon, precip_mm, temp_max, temp_min, date  
**Aggregation:** Map station → crop polygons (county/municipality)  
**Throttling:** 1 req / 5s per domain  
**Storage Schema:**
```sql
weather_data: date, region, station_id, precip_mm, temp_max, temp_min, source_name, confidence_score
```

---

### **Minute 26-30: Remote Sensing Metadata (MODIS/Sentinel)**

**Target Table:** `economic_indicators` (use for vegetation indices)

**Sources:**
```python
SATELLITE_SOURCES = [
    # MODIS NDVI/EVI (daily vegetation indices)
    ('economic_indicators', 'https://e4ftl01.cr.usgs.gov/MOLT/MOD13Q1.061/'),  # 16-day NDVI
    
    # NASA POWER (ag meteorology)
    ('weather_data', 'https://power.larc.nasa.gov/api/temporal/daily/point'),
    
    # Sentinel-2 (check metadata, not full imagery)
    ('economic_indicators', 'https://scihub.copernicus.eu/dhus/search'),  # Metadata only
]
```

**Note:** Do NOT download full imagery hourly - only check metadata (tile availability, cloud cover)  
**Parser:** Extract tile_id, acquisition_date, cloud_cover, NDVI_mean (if pre-computed)  
**Throttling:** 1 req / 10s (heavy endpoints)  
**Storage Schema:**
```sql
economic_indicators: time, indicator='ndvi_brazil_mato_grosso', value, source_name='MODIS'
```

---

### **Minute 32-36: USDA/CONAB/BAGE Reports (Watcher Mode)**

**Target Table:** `news_intelligence` (for report releases)

**Sources:**
```python
REPORT_SOURCES = [
    # USDA WASDE (monthly report - watch for releases)
    ('news_intelligence', 'https://www.usda.gov/oce/commodity/wasde'),
    
    # NASS (weekly crop progress)
    ('news_intelligence', 'https://www.nass.usda.gov/Publications/State_Crop_Progress_and_Condition/'),
    
    # CONAB (Brazil)
    ('news_intelligence', 'https://www.conab.gov.br/info-agro/safras'),
    
    # BAGE (Argentina)
    ('news_intelligence', 'https://www.argentina.gob.ar/agricultura'),
    
    # Watch TradingEconomics calendar for release times
    ('news_intelligence', 'https://tradingeconomics.com/calendar'),
]
```

**Strategy:** Poll hourly but only ingest when numeric values change from last stored  
**Parser:** Extract report_date, headline, PDF link, key metrics (if table available)  
**Throttling:** 1 req / 6-8s (government sites)  
**Storage Schema:**
```sql
news_intelligence: timestamp, source, category='usda_report', text, source_name='USDA'
```

---

### **Minute 38-42: CFTC Commitments of Traders (COT)**

**Target Table:** `economic_indicators` (use for positioning data)

**Sources:**
```python
COT_SOURCES = [
    # CFTC weekly report (released Friday evenings)
    ('economic_indicators', 'https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm'),
    
    # Parse soybeans, soybean oil, corn positioning
    ('economic_indicators', 'https://www.cftc.gov/dea/futures/deacmesf.htm'),  # CME futures table
]
```

**Frequency:** Weekly (released Fri evening US time), but poll hourly  
**Parser:** Extract commercial_long, commercial_short, managed_money_long, managed_money_short  
**Calculate:** Net positioning, Z-scores vs historical  
**Throttling:** 1 req / 5s  
**Storage Schema:**
```sql
economic_indicators: time, indicator='cftc_soybean_oil_commercial_net', value, source_name='CFTC'
```

---

### **Minute 44-48: Ports & Logistics (Santos/Paranaguá/Rosario)**

**Target Table:** `economic_indicators` (use for port congestion metrics)

**Sources:**
```python
PORT_SOURCES = [
    # Brazil ports (Santos, Paranaguá)
    ('economic_indicators', 'https://www.portodesantos.com.br/'),  # Santos backlog
    ('economic_indicators', 'http://www.portosdoparana.pr.gov.br/'),  # Paranaguá
    
    # Argentina (Rosario)
    ('economic_indicators', 'https://www.enapro.com.ar/'),  # Rosario port authority
    
    # Baltic Dry Index (already covered by TradingEconomics)
    
    # ESALQ freight index (Brazil truck freight)
    ('economic_indicators', 'https://www.cepea.esalq.usp.br/br/consultas-ao-banco-de-dados-do-site.aspx'),
]
```

**Parser:** Extract vessel_count, waiting_days, quay_utilization  
**Throttling:** 1 req / 8-10s (respect local servers)  
**Storage Schema:**
```sql
economic_indicators: time, indicator='santos_port_vessel_queue', value, source_name='PortoSantos'
```

---

### **Minute 50-54: News Aggregation (Reuters/Agweb/FarmProgress)**

**Target Table:** `news_intelligence`

**Sources:**
```python
NEWS_SOURCES = [
    # Ag news outlets
    ('news_intelligence', 'https://www.agweb.com/markets/soybeans'),
    ('news_intelligence', 'https://www.farmprogress.com/'),
    ('news_intelligence', 'https://www.dtnpf.com/agriculture/web/ag/crops/article/2024/10/07/'),
    
    # General news (soybean/palm oil keywords)
    ('news_intelligence', 'https://www.reuters.com/markets/commodities/'),
    ('news_intelligence', 'https://www.bloomberg.com/markets/commodities'),  # If accessible
    
    # Brazil/Argentina ag news
    ('news_intelligence', 'https://www.noticiasagricolas.com.br/'),
    ('news_intelligence', 'https://www.ambito.com/agro'),  # Argentina
]
```

**Parser:** Extract headline, timestamp, snippet, detect entities (China, USDA, palm oil, soybean)  
**Throttling:** 1 req / 5-6s per domain  
**Storage Schema:**
```sql
news_intelligence: timestamp, source, category, text, source_name, confidence_score
```

---

### **Minute 56-59: Social Media & Google Trends**

**Target Table:** `social_sentiment`

**Sources:**
```python
SOCIAL_SOURCES = [
    # Twitter (web search) - use existing script
    # Reddit - already covered by existing social_intelligence.py
    
    # Google Trends (soybean, palm oil, biodiesel keywords)
    ('social_sentiment', 'https://trends.google.com/trends/explore?q=soybean%20prices'),
    ('social_sentiment', 'https://trends.google.com/trends/explore?q=palm%20oil'),
    
    # StockTwits (if accessible)
    ('social_sentiment', 'https://stocktwits.com/symbol/ZL'),
]
```

**Parser:** Extract trend_score, tweet_count, sentiment_aggregate  
**Throttling:** 1 req / 10s (social sites are sensitive)  
**Storage Schema:**
```sql
social_sentiment: timestamp, platform, title, score, comments, sentiment_score, source_name
```

---

## 🔧 IMPLEMENTATION: Master Scheduler Script

**File:** `cbi-v14-ingestion/multi_source_master_scheduler.py`

```python
#!/usr/bin/env python3
"""
Multi-Source Master Scheduler
Orchestrates hourly scraping across all data sources
Routes to EXISTING BigQuery tables ONLY
"""

import time
import random
from datetime import datetime

# Import individual scrapers
from tradingeconomics_scraper import run_scraping_batch as te_scraper
# TODO: Create these scrapers following TE pattern
# from futures_scraper import scrape_futures
# from fred_scraper import scrape_fred
# from weather_scraper import scrape_weather
# from ports_scraper import scrape_ports
# from news_scraper import scrape_news
# from social_scraper import scrape_social

# Master schedule (minute offset: scraper function)
MASTER_SCHEDULE = {
    0: 'fx_and_prices',      # TradingEconomics FX + TE commodity prices
    8: 'futures_barchart',   # Barchart/Investing/Yahoo futures
    14: 'fred_macro',        # FRED + BLS macro indicators
    20: 'weather_stations',  # NOAA/INMET/Somar
    26: 'satellite_metadata',# MODIS/Sentinel metadata checks
    32: 'reports_watcher',   # USDA/CONAB/BAGE
    38: 'cftc_cot',          # Commitments of Traders
    44: 'ports_logistics',   # Santos/Paranaguá/Rosario
    50: 'news_aggregator',   # Reuters/Agweb/FarmProgress
    56: 'social_trends',     # Twitter/Reddit/Google Trends
}

def main():
    """Run scheduled scraping tasks for current hour"""
    current_minute = datetime.now().minute
    
    # Find closest scheduled task
    scheduled_minutes = sorted(MASTER_SCHEDULE.keys())
    closest = min(scheduled_minutes, key=lambda x: abs(x - current_minute))
    
    task_name = MASTER_SCHEDULE[closest]
    
    logger.info(f"Running task: {task_name} at minute {current_minute}")
    
    # Route to appropriate scraper
    # TODO: Implement individual scrapers
    if task_name == 'fx_and_prices':
        te_scraper(closest)  # TradingEconomics scraper already implemented
    elif task_name == 'futures_barchart':
        # scrape_futures()
        logger.info("TODO: Implement futures_scraper.py")
    # ... etc for each task
    
    logger.info(f"Task {task_name} complete")

if __name__ == '__main__':
    main()
```

---

## 🚀 CRON SETUP (One Job Rules Them All)

**Install master scheduler:**
```bash
# One cron job to rule them all
0 * * * * cd /Users/zincdigital/CBI-V14 && python3 cbi-v14-ingestion/multi_source_master_scheduler.py >> /tmp/master_scraper.log 2>&1
```

**What this does:**
- Runs every hour on the hour
- Determines which task to run based on current minute
- Routes data to EXISTING tables only
- Logs everything to `/tmp/master_scraper.log`

---

## 📋 IMPLEMENTATION PRIORITY (Next Steps)

### **Immediate (Already Done):**
- [x] TradingEconomics scraper (50+ URLs) → Minute 0, 2, 10, 14, 20, 25, 30, 50

### **Phase 1 (Next 4-8 hours):**
- [ ] Futures scraper (Barchart/Investing/Yahoo) → Minute 8
- [ ] FRED macro scraper → Minute 14
- [ ] Weather stations scraper (NOAA supplement) → Minute 20

### **Phase 2 (Next 8-16 hours):**
- [ ] Ports/logistics scraper → Minute 44
- [ ] News aggregator → Minute 50
- [ ] Social/trends scraper → Minute 56

### **Phase 3 (Next 16-24 hours):**
- [ ] Satellite metadata checker → Minute 26
- [ ] Reports watcher (USDA/CONAB) → Minute 32
- [ ] CFTC COT scraper → Minute 38

---

## ⚠️ CRITICAL RULES (DO NOT VIOLATE)

1. **NO NEW TABLES:** Route ALL data to 18 existing tables listed above
2. **Throttling:** Minimum 4-6 seconds between requests to same domain
3. **Caching:** 1-hour TTL for FX/prices, 24-hour for reports
4. **Error Handling:** Save raw HTML on failure, confidence_score=0.2
5. **Logging:** All scraping attempts logged with timestamp, URL, status
6. **Budget:** $0/month forever (no paid APIs)
7. **Politeness:** Respect robots.txt, add random jitter (±15s)
8. **Fallbacks:** If primary source blocked, use secondary (TE → Investing → Yahoo)

---

## 💰 TOTAL COST ESTIMATE

| Source Group | URLs/Hour | Domain | Cost |
|-------------|-----------|--------|------|
| TradingEconomics | 50 | TE | $0/month ✅ |
| Futures (Barchart/Investing/Yahoo) | 10 | Multiple | $0/month ✅ |
| FRED + BLS | 6 | .gov | $0/month ✅ |
| Weather stations | 8 | .gov/.br | $0/month ✅ |
| Satellite metadata | 3 | NASA/ESA | $0/month ✅ |
| Reports watchers | 6 | .gov/.br/.ar | $0/month ✅ |
| CFTC COT | 2 | .gov | $0/month ✅ |
| Ports/logistics | 5 | .br/.ar | $0/month ✅ |
| News aggregators | 10 | Multiple | $0/month ✅ |
| Social/trends | 5 | Multiple | $0/month ✅ |
| **TOTAL** | **~105 URLs/hour** | **All free** | **$0/month** ✅ |

**BigQuery cost:** +$0.20/month (storage + queries)  
**Total project cost:** $0.71/month (was $0.51)

---

## 📊 SUCCESS METRICS (After 7 Days)

- [ ] 168 successful hourly cycles (7 days × 24 hours)
- [ ] Palm oil prices in `palm_oil_prices` (need to create table first)
- [ ] FX rates in `currency_data` (>100 rows)
- [ ] Futures prices in soybean tables (>500 rows)
- [ ] Economic indicators expanded (+50% rows)
- [ ] Weather data supplemented with NOAA stations
- [ ] News intelligence growing daily
- [ ] Zero blocking incidents
- [ ] <5% scraping failure rate

---

**Next Action:** Implement remaining scrapers following TradingEconomics pattern  
**Timeline:** 48 hours for full multi-source coverage  
**Budget:** $0/month (all free web scraping)

