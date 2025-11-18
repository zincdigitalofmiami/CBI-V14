# CBI-V14 Data Sources Reference
**Date**: November 17, 2025  
**Status**: Reference Document - Data Source Catalog  
**Purpose**: Comprehensive catalog of data sources, APIs, and scraping endpoints for CBI-V14

---

## Overview

This document catalogs all known data sources, APIs, and scraping endpoints that could be used for CBI-V14. Sources are organized by category with notes on:
- Current usage status
- Authentication requirements
- Data availability
- Integration notes

**Note**: This is a reference catalog. Not all sources are currently integrated. Review security considerations (especially hardcoded API keys) before implementing.

---

## Weather and Climate Data Sources

### INMET (Brazil National Institute of Meteorology)

**API Endpoints**:
- Base API: `https://apitempo.inmet.gov.br/estacao/{start}/{end}/{station_id}`
- Token endpoint: `https://apitempo.inmet.gov.br/token`
- Station listings:
  - `https://apitempo.inmet.gov.br/estacoes`
  - `https://apitempo.inmet.gov.br/estacao/dados-estacao`
  - `https://apitempo.inmet.gov.br/estacoes/T/A/,,/A/`
  - `https://portal.inmet.gov.br/api/estacoes/automaticas`

**Portal**: `https://portal.inmet.gov.br/`

**GitHub Wrapper**: `https://github.com/gregomelo/brazil_weather_data` (Python wrapper for Brazil weather data)

**Status**: Reference - Not currently integrated  
**Authentication**: Token-based (obtain from token endpoint)  
**Use Case**: Brazil crop weather data, temperature, precipitation

---

### Argentina SMN (National Weather Service)

**Data Endpoint**:
- Hourly text data: `https://ssl.smn.gob.ar/dpd/descarga_opendata.php?file=observaciones/datohorario{station_id}.txt`

**Status**: Reference - Not currently integrated  
**Authentication**: None (open data)  
**Use Case**: Argentina weather observations for crop forecasting

---

### NOAA (National Oceanic and Atmospheric Administration)

**CDO API**:
- Base: `https://www.ncei.noaa.gov/cdo-web/api/v2/data`
- Documentation: `https://www.ncdc.noaa.gov/cdo-web/webservices/v2`
- Token portal: `https://www.ncdc.noaa.gov/cdo-web/token`

**NOMADS GFS**:
- GFS filter: `https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl`

**Status**: ⚠️ **PARTIALLY INTEGRATED** - Token found in codebase  
**Authentication**: Header `token: {noaa_token}`  
**Current Usage**: `unified_weather_scraper.py`  
**Security Note**: Token hardcoded - needs migration to Keychain

---

### Copernicus (ECMWF) CDS API

**API**: `https://cds.climate.copernicus.eu/api`

**Status**: Reference - Not currently integrated  
**Authentication**: CDS API key required  
**Use Case**: European climate reanalysis data

---

### Meteomatics API

**API**: `https://api.meteomatics.com`

**Status**: Reference - Not currently integrated  
**Authentication**: API key required (commercial service)  
**Use Case**: High-resolution weather forecasts

---

## Economic, Rates, and Macro Data Sources

### FRED (Federal Reserve Economic Data)

**API Endpoints**:
- Base: `https://api.stlouisfed.org/fred/`
- Series observations: `https://api.stlouisfed.org/fred/series/observations`
- API key docs: `https://fred.stlouisfed.org/docs/api/api_key.html`

**Status**: ✅ **INTEGRATED** - Active usage  
**Authentication**: Query param `api_key={key}`  
**Current Usage**: 
- `fred_economic_deployment.py`
- `multi_source_collector.py`
**Security Note**: ⚠️ API key hardcoded - needs migration to Keychain

---

### Federal Reserve Resources

**Fed Speeches**: `https://www.federalreserve.gov/newsevents/speech/`  
**FOMC Calendars**: `https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm`  
**NY Fed Rates JSON**: `https://markets.newyorkfed.org/api/rates/all/latest.json`

**Status**: Reference - Not currently integrated  
**Authentication**: None (public data)  
**Use Case**: Monetary policy signals, interest rate tracking

---

### US Treasury

**Fiscal Data API**: `https://api.fiscaldata.treasury.gov/services/api/v1/`  
**Treasury Auctions**: `https://www.treasurydirect.gov/auctions/`  
**TreasuryDirect**: `https://www.treasurydirect.gov/`

**Status**: Reference - Not currently integrated  
**Authentication**: None (public API)  
**Use Case**: Government debt, auction data

---

### BLS (Bureau of Labor Statistics)

**API**: `https://api.bls.gov/publicAPI/v2/`

**Status**: Reference - Not currently integrated  
**Authentication**: API key (free registration)  
**Use Case**: Employment, inflation data

---

### Central Banks

**ECB SDW REST**: `https://sdw-wsrest.ecb.europa.eu/service/`  
**Banco Central do Brasil (SGS)**: `https://www3.bcb.gov.br/sgspub/`  
**PBOC (People's Bank of China)**: `http://www.pbc.gov.cn/en/`  
**BCRA (Argentina Central Bank)**: `http://www.bcra.gob.ar/`

**Status**: Reference - Not currently integrated  
**Authentication**: Varies by bank  
**Use Case**: International monetary policy, exchange rates

---

### Economic Calendars

- TradingEconomics: `https://tradingeconomics.com/calendar`
- ForexFactory: `https://www.forexfactory.com/calendar`
- Investing.com: `https://www.investing.com/economic-calendar/`
- MarketWatch: `https://www.marketwatch.com/economy-politics/calendar`

**Status**: Reference - Not currently integrated  
**Authentication**: None (public)  
**Use Case**: Economic event tracking, announcement dates

---

## Market Prices and Trading Data

### TradingEconomics API

**API Base**: `https://api.tradingeconomics.com`  
**Indicators Docs**: `https://docs.tradingeconomics.com/documentation/indicators/`

**Status**: ⚠️ **PARTIALLY INTEGRATED** - Environment variable usage  
**Authentication**: Query param `c={client}:{api_key}` (from env vars)  
**Current Usage**: `ingest_market_prices.py`  
**Security Note**: Uses environment variables (good practice)

---

### Polygon.io API

**API Base**: `https://api.polygon.io`  
**Aggregates Docs**: `https://polygon.io/docs/stocks/get_v2_aggs_tickerstocksTicker_rangemultipliertimespan_fromto`

**Status**: ⚠️ **PARTIALLY INTEGRATED** - Environment variable usage  
**Authentication**: Query param `apiKey={key}` (from env vars)  
**Current Usage**: `ingest_market_prices.py`  
**Security Note**: Uses environment variables (good practice)

---

### Alpha Vantage

**API Format**: `https://www.alphavantage.co/query?...&apikey={key}`

**Status**: ⚠️ **KEY STORED** - Confirm actual usage  
**Authentication**: Query param `apikey`  
**Current Usage**: Key found in `multi_source_collector.py` but usage unclear  
**Security Note**: ⚠️ API key hardcoded - needs migration to Keychain

---

## Trade, Policy, and News Sources

### Federal Register

**API**: `https://www.federalregister.gov/api/v1/documents.json`

**Status**: Reference - Not currently integrated  
**Authentication**: None (public API)  
**Use Case**: Federal regulations, policy announcements

---

### Government Agency News

**ICE News Releases**: `https://www.ice.gov/news/releases`  
**DHS News Releases**: `https://www.dhs.gov/news-releases`  
**CBP Newsroom**: `https://www.cbp.gov/newsroom`

**Status**: Reference - Not currently integrated  
**Authentication**: None (public)  
**Use Case**: Immigration policy, border enforcement (labor market impacts)

---

### Farm Organizations and Policy

**Farm Labor Organizing**: `https://www.farmlabororganizing.org/`  
**United Farm Workers**: `https://ufw.org/`  
**Western Growers**: `https://www.wga.com/`  
**Farm Bureau**: `https://www.fb.org/newsroom/`  
**Immigration Impact**: `https://immigrationimpact.com/`  
**Migration Policy Institute**: `https://www.migrationpolicy.org/`  
**SPLC Immigrant Justice**: `https://www.splcenter.org/issues/immigrant-justice`  
**California Farm Bureau**: `https://www.cfbf.com/news/`  
**Texas Agriculture**: `https://www.texasagriculture.gov/`  
**Florida Agriculture**: `https://www.fdacs.gov/`  
**Georgia Farm Bureau**: `https://www.gfb.org/`

**Status**: Reference - Not currently integrated  
**Authentication**: None (public websites)  
**Use Case**: Labor policy, immigration impacts on agriculture

---

### Think Tanks and Trade Policy

**Heritage Foundation Agriculture**: `https://www.heritage.org/agriculture`  
**America First Policy**: `https://americafirstpolicy.com/`  
**Tax Foundation Trade**: `https://taxfoundation.org/research/all/federal/trade/`  
**AEI Trade Policy**: `https://www.aei.org/tag/trade-policy/`  
**PIIE Trade War Chart**: `https://www.piie.com/research/piie-charts/us-china-trade-war-tariffs-date-chart`  
**CSIS Trade War Monitor**: `https://www.csis.org/programs/scholl-chair-international-business/trade-war-monitor`  
**US-China Business Council**: `https://www.uschina.org/`

**Status**: Reference - Not currently integrated  
**Authentication**: None (public websites)  
**Use Case**: Trade policy analysis, China-US trade relations

---

### Campaign and Political Sources

**Trump Campaign News**: `https://www.donaldjtrump.com/news`  
**WinRed Fundraising**: `https://www.winred.com/save-america-joint-fundraising-committee/`

**Status**: Reference - Not currently integrated  
**Authentication**: None (public)  
**Use Case**: Political signals, policy direction

---

### Agriculture and Commodities Media

**AgWeb Soybeans**: `https://www.agweb.com/news/crops/soybeans`  
**Farm Progress**: `https://www.farmprogress.com/soybeans`  
**Agriculture.com Markets**: `https://www.agriculture.com/markets-commodities`  
**Agrimoney News**: `https://www.agrimoney.com/news/grains-oilseeds/`  
**World Grain**: `https://www.world-grain.com/`  
**CONAB (Brazil)**: `https://www.conab.gov.br/ultimas-noticias`  
**ABIOVE (Brazil)**: `https://abiove.org.br/en/statistics/`  
**Agrimoney China**: `https://www.agrimoney.com/news/china/`  
**Reuters Commodities**: `https://www.reuters.com/business/commodities/`

**Status**: Reference - Not currently integrated  
**Authentication**: None (public websites)  
**Use Case**: Commodity news, market sentiment, Brazil/Argentina crop updates

---

### Biofuels

**EIA Biodiesel Production**: `https://www.eia.gov/biofuels/biodiesel/production/`

**Status**: Reference - Not currently integrated  
**Authentication**: None (public)  
**Use Case**: Biofuel demand, SAF policy impacts

---

## Social Media and Sentiment Sources

### Truth Social

**User Profile**: `https://truthsocial.com/@realDonaldTrump`  
**Post URLs**: `https://truthsocial.com/@realDonaldTrump/{post_id}`

**ScrapeCreators API**:
- Base: `https://api.scrapecreators.com/v1/truthsocial`
- Post endpoint: `https://api.scrapecreators.com/v1/truthsocial/post`
- Facebook endpoint: `https://api.scrapecreators.com/v1/facebook/post`

**Status**: ✅ **INTEGRATED** - Active usage  
**Authentication**: Header `x-api-key: {key}`  
**Current Usage**:
- `trump_truth_social_monitor.py`
- `trump_post_discovery.py`
- `social_intelligence.py`
- `trump_broad_collector.py`
**Security Note**: ⚠️ API key hardcoded - needs migration to Keychain

---

### Facebook Pages

**American Soybean Association**: `https://www.facebook.com/AmericanSoybeanAssociation/`  
**Department of Labor**: `https://www.facebook.com/departmentoflabor`  
**USDA**: `https://www.facebook.com/USDA`

**Status**: Reference - ScrapeCreators API available for Facebook  
**Authentication**: Via ScrapeCreators API  
**Use Case**: Social sentiment, policy announcements

---

### Reddit

**Agriculture Subreddit JSON**: `https://www.reddit.com/r/agriculture.json`

**Status**: Reference - Not currently integrated  
**Authentication**: None (public JSON feed)  
**Use Case**: Community sentiment, discussion trends

---

## Shipping, Ports, and Logistics

### MarineTraffic

**Data**: `https://www.marinetraffic.com/en/data/`

**Status**: Reference - Not currently integrated  
**Authentication**: API key required (commercial service)  
**Use Case**: Shipping capacity, port congestion, supply chain disruptions

---

## China Soybean Import Data Alternatives

**Note**: Direct China import data is difficult to obtain. These sources track China's soybean purchasing patterns:

### News and Analysis Sources

- **Reuters** (Oct 2025): Tracks monthly imports; Sep 2025 at ~12.9 mmt (+13% YoY) from South America, no U.S. buys since May
  - URL: `https://www.reuters.com/world/china/us-soybean-farmers-deserted-by-big-buyer-china-scramble-other-importers-2025-10-03/`

- **Bloomberg** (Sep 2025): First time since 1990s no U.S. soy buys at harvest start
  - URL: `https://www.bloomberg.com/news/articles/2025-09-19/china-seeks-trade-edge-by-shunning-us-soy-in-first-since-1990s`

- **DTN Progressive Farmer**: FAS data shows no purchases since May 2025
  - URL: `https://www.dtnpf.com/agriculture/web/ag/news/article/2025/09/29/china-soybean-users-see-breakthrough`

- **AgWeb**: Low prices ($8/bushel) due to absent China buys
  - URL: `https://www.agweb.com/news/crops/soybeans/8-soybeans-thats-reality-some-farmers-china-remains-absent-buying`

- **Farm Action/Soygrowers**: Export gaps analysis, 34% duty on U.S. soy
  - URLs: 
    - `https://farmaction.us/china-stopped-buying-u-s-soybeans-the-real-problem-started-decades-ago/`
    - `https://soygrowers.com/news-releases/soybeans-without-a-buyer-the-export-gap-hurting-u-s-farms/`

**Status**: Reference - Manual monitoring recommended  
**Use Case**: Track China import patterns, trade policy impacts

---

## South American Soybean Harvest/Planting Progress

### Analysis and Data Sources

- **Farmdoc Daily**: Record 2024/25 harvest (55% global supply); USDA/Conab estimate disparities
  - URL: `https://farmdocdaily.illinois.edu/2025/03/record-soybean-harvest-in-south-america-and-favorable-outlook-for-exports.html`

- **Hedgepoint Global**: 2024/25 Brazil record expected; Argentina high yields
  - URL: `https://hedgepointglobal.com/en/blog/progress-of-corn-and-soybean-crops-in-brazil-and-argentina`

- **USDA FAS Reports**: Brazil 2025/26 planting, Paraguay data (PDF downloads)
  - URLs:
    - `https://apps.fas.usda.gov/newgainapi/api/Report/DownloadReportByFileName?fileName=Grain%2520and%2520Feed%2520Update_Brasilia_Brazil_BR2025-0023`
    - `https://apps.fas.usda.gov/newgainapi/api/Report/DownloadReportByFileName?fileName=Grain%2520and%2520Feed%2520Annual_Brasilia_Brazil_BR2025-0009.pdf`
    - `https://apps.fas.usda.gov/newgainapi/api/Report/DownloadReportByFileName?fileName=Oilseeds%2Band%2BProducts%2BUpdate_Brasilia_Brazil_BR2025-0017.pdf`

- **Purdue Ag**: U.S. harvest starts with no China buys; Brazil export records
  - URL: `https://ag.purdue.edu/commercialag/home/resource/2025/09/u-s-soybean-harvest-starts-with-no-sign-of-chinese-buying-as-brazil-sets-export-record/`

- **OCJ**: South American updates; USDA Brazil projections
  - URL: `https://ocj.com/category/2024-2025-south-american-update/`

**Status**: Reference - Manual monitoring or web scraping  
**Use Case**: Harvest progress, planting data, supply forecasts

---

## Security Considerations

### ⚠️ Hardcoded API Keys Detected

The following API keys are currently hardcoded in the codebase and should be migrated to macOS Keychain:

1. **ScrapeCreators API Key**
   - Files: `trump_truth_social_monitor.py`, `trump_post_discovery.py`, `social_intelligence.py`, `trump_broad_collector.py`
   - Action: Migrate to Keychain using `src/utils/keychain_manager.py`

2. **FRED API Key**
   - Files: `fred_economic_deployment.py`, `multi_source_collector.py`
   - Action: Migrate to Keychain

3. **NOAA CDO Token**
   - Files: `unified_weather_scraper.py`
   - Action: Migrate to Keychain

4. **Alpha Vantage API Key**
   - Files: `multi_source_collector.py`
   - Action: Confirm usage, then migrate to Keychain if needed

### ✅ Good Practices (Environment Variables)

The following APIs use environment variables (good practice, but consider Keychain for production):

- **TradingEconomics**: Uses `TRADINGECONOMICS_API_KEY` and `TRADINGECONOMICS_CLIENT` env vars
- **Polygon.io**: Uses `POLYGON_API_KEY` env var

**Recommendation**: Migrate all API keys to macOS Keychain for consistency and security. See `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` Security section for Keychain usage.

---

## Integration Priority Recommendations

### High Priority (Currently Used)
1. ✅ FRED API - Economic data (migrate key to Keychain)
2. ✅ ScrapeCreators API - Social media (migrate key to Keychain)
3. ✅ NOAA CDO - Weather data (migrate token to Keychain)
4. ⚠️ TradingEconomics - Market prices (consider Keychain migration)
5. ⚠️ Polygon.io - Market data (consider Keychain migration)

### Medium Priority (Reference Sources)
1. INMET (Brazil) - Crop weather data
2. Argentina SMN - Weather observations
3. USDA FAS Reports - South American crop data
4. Federal Register API - Policy tracking
5. Economic calendars - Event tracking

### Low Priority (Manual Monitoring)
1. China import data (news sources)
2. South American harvest progress (news/analysis)
3. Farm organization websites (policy signals)
4. Think tank publications (trade policy)

---

## Data Source Integration Notes

### Web Scraping Considerations

Many sources listed are public websites requiring web scraping rather than APIs:
- Use `src/ingestion/web_scraper.py` or `src/ingestion/advanced_scraper_base.py` as base classes
- Respect robots.txt and rate limits
- Implement retry logic and error handling
- Store scraped data in `raw_intelligence` dataset

### API Integration Pattern

For new API integrations:
1. Store API keys in macOS Keychain (see `src/utils/keychain_manager.py`)
2. Create ingestion script in `scripts/ingest/` or `src/ingestion/`
3. Store raw data in appropriate BigQuery dataset
4. Create feature engineering pipeline if needed
5. Document in this reference file

### Data Quality Requirements

All data sources must:
- Use REAL data only (no fake/placeholder data)
- Validate data quality before ingestion
- Handle missing data gracefully
- Log ingestion status and errors

---

## References

- Current Architecture: `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md`
- Keychain Manager: `src/utils/keychain_manager.py`
- Web Scraper Base: `src/ingestion/advanced_scraper_base.py`
- Security Guidelines: See Security section in `TRAINING_MASTER_EXECUTION_PLAN.md`

---

**Last Updated**: November 17, 2025  
**Status**: Reference document - Data source catalog



