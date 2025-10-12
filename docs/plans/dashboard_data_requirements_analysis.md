# Dashboard Data Requirements Analysis (CBI-V14)
_Generated: 2025-10-11_

## Purpose
Map the 4-page dashboard blueprint to existing BigQuery infrastructure and identify gaps before performing view cleanup.

---

## Page 1: Dashboard (Chris's Daily Decision Page)

### Required Data Sources (from blueprint)
| Data Source | Current Status | Location | Notes |
|------------|----------------|----------|-------|
| `zl_data` | ⚠️ NEEDS REBUILD | `forecasting_data_warehouse.soybean_oil_prices` | Yahoo Finance source unreliable; need CME/TradingEconomics |
| `fed_rates_real_time` | ✅ EXISTS | Covered by `vw_fed_rates_realtime` | Check if needed in curated |
| `tariff_conflicts` | ❌ MISSING | — | Need GDELT + USTR ingestion |
| `china_relations` | ⚠️ PARTIAL | `gdelt_china_intelligence` table exists | May need expansion |
| `procurement_signals` | ❌ MISSING | — | Feature engineering required |
| `china_crushing_margins` | ❌ MISSING | — | Need China soybean/meal/oil prices |
| `storage_capacity` | ❌ MISSING | — | USDA data source |
| `cftc_cot_reports` | ❌ MISSING | — | Free CFTC API |

### Required Views/Features
- **Mood ring indicator**: ML model output (confidence 0-100%)
- **30-day AI projection**: Time series forecast with confidence bands
- **Volume spikes**: Annotated with China buying events
- **Interactive sliders**: Fed rates, China relations, weather, ICE/Labor
- **Cost implications table**: Scenario modeling outputs

---

## Page 2: Sentiment

### Required Data Sources
| Data Source | Current Status | Location | Notes |
|------------|----------------|----------|-------|
| `social_sentiment` | ⚠️ NEEDS REBUILD | `forecasting_data_warehouse.social_sentiment` | Reddit-era, needs ScrapeCreators migration |
| `google_trends` | ❌ MISSING | — | pytrends API |
| `cftc_cot_reports` | ❌ MISSING | — | As above |
| `news_articles` | ⚠️ EXISTS | `forecasting_data_warehouse.news_intelligence` | Has 43 rows missing metadata; needs full-article scraping |
| Policy/regulation tables | ❌ MISSING | — | EPA RFS, trade agreements |

### Required Views/Features
- **Market mood gauge**: Weighted composite (news 40%, COT 30%, technicals 20%, weather 10%)
- **16-category news grid**: Requires event categorization taxonomy
- **AI narrative summary**: LLM-generated, 4-hour refresh
- **Delta vs yesterday**: Change detection logic

### News & Geopolitical Sentiment Playbook (Working Checklist)
- **1. China demand levers** — watch Sinograin/COFCO/NDRC/MOF moves; bullish triggers: reserve rebuilds, import quota boosts, crush subsidies. Bearish: biosecurity slowdowns, tighter licenses, reserve releases. *Keywords*: Sinograin, COFCO, NDRC soybean, state reserves, crush margins Dalian.
- **2. Argentina policy & FX** — monitor export taxes, “soy dollar” incentives, Rosario logistics. Bullish: tax hikes, FX carrot removal, strikes. Bearish: tax cuts, FX incentives, IMF liberalization. *Keywords*: sojadólar, retenciones, Rosario strike, CIARA-CEC, Puerto San Lorenzo.
- **3. Brazil policy & infrastructure** — track CONAB/MAPA guidance, BR-163/Santos/Arco Norte logistics. Bullish: licensing hiccups, environmental enforcement, transport bottlenecks. Bearish: Ferrogrão/rail upgrades, port privatizations, BRL strength. *Keywords*: CONAB, MAPA, Santos, Arco Norte, Ferrogrão, Ibama embargo.
- **4. U.S. policy** — tariffs, Farm Bill, RFS, logistics chokepoints. Bullish: higher China tariffs risk, EUDR alignment costs, rail/port strikes, Mississippi draft limits. Bearish: export credit expansion, inspection streamlining, lower RFS volumes. *Keywords*: USTR, RFS volumes, Jones Act waiver, USACE Mississippi, ILWU, STB rail.
- **5. Biofuels policy swings** — mandates tie soy oil to crude. Bullish: Indonesia B35→B40, Brazil blend hikes, US LCFS/SAF/45Z incentives. Bearish: ILUC pushback, weak LCFS credits, crop-based caps. *Keywords*: B40 Indonesia, RenovaBio, CBIO, LCFS, SAF, EPA RVO.
- **6. Palm oil geopolitics** — substitution pressure. Bullish soy: Indonesian/Malaysian levies/bans, labor shortages, ESG hurdles. Bearish soy: levy cuts, bumper output, India duty cuts. *Keywords*: CPO export levy, DMO, MPOB, India edible oil duty.
- **7. Black Sea vegoils & war spillovers** — sunflower flows vs corridor risks. Bullish: corridor disruption, sanctions, port strikes. Bearish: corridor reopenings, insured shipping, sunflower surges. *Keywords*: Black Sea corridor, Danube ports, sunflower oil export, marine insurance.
- **8. Global chokepoints & freight** — Red Sea, Panama, South China Sea. Bullish: Houthi/war risk, canal slot cuts, insurance exclusions. Bearish: reroute subsidies, rainfall recovery, naval escorts. *Keywords*: Panama Canal transit, Bab el-Mandeb, Houthi, war risk premiums.
- **9. Fertilizer & energy sanctions** — input-cost transmission. Bullish: ammonia/potash sanctions, EU gas spikes. Bearish: sanction carve-outs, new supply, cheap gas. *Keywords*: Belarus potash, CF Industries outage, ammonia pipeline, urea tender.
- **10. Animal disease shocks** — meal demand swings. Bullish: disease waves → lower feed use/stockpile policies. Bearish: herd rebuilds increasing feed demand. *Keywords*: ASF China, avian influenza, hog herd, MOA China.
- **11. Trade disputes & quotas** — WTO/AD/CVD/TQ actions. Bullish: antidumping/CVD, SPS barriers. Bearish: bilateral deals, tariff-rate quotas. *Keywords*: antidumping soybean oil, WTO panel, TRQ soybeans, SPS measures.
- **12. ESG/deforestation rules** — EUDR & copycats. Bullish: strict traceability deadlines causing delays. Bearish: phased enforcement or exemptions. *Keywords*: EUDR soy, traceability polygon, due diligence regulation.
- **13. Labor & civil unrest** — strikes/blockades. Bullish: port strikes (Santos/Rosario), trucker protests, farmer blockades. Bearish: settlements guaranteeing throughput. *Keywords*: port strike Santos, Rosario piquete, Gulf export elevators, blockade.
- **14. Cyber/infrastructure shocks** — out-of-band disruptions. Bullish: ransomware at ports/traders, AIS spoofing, customs outages. *Keywords*: ransomware port, terminal outage, customs IT failure, AIS spoofing.
- **15. Regulatory approvals (GM traits/agrochemicals)** — planting/yield uncertainty. Bullish: bans/withdrawals, delayed China approvals. Bearish: rapid approvals, stabilized herbicide regimes. *Keywords*: soy trait approval China, glyphosate ban, CTNBio.
- **16. Macro/FX watch** — USD, BRL, ARS dynamics; capital controls and downgrades. Rule of thumb: USD strength often pressures commodities; BRL/ARS weakness boosts South American exports.
- **Alert buckets for dashboard wiring:** US Regulatory Filings, Political Changes, Tariff Updates, China Relations, Legislation Changes, Biofuel Mandates, Logistics/Chokepoints, ESG/Deforestation, Labor Actions, Fertilizer/Energy, Animal Disease.
- **Event → impact heuristics:** e.g., Indonesia raises CPO levy/B40 → bullish soy oil; Panama Canal transit cuts → bullish Brazil/US Gulf export basis; EUDR enforcement firmed → bullish EU-imported soy; ASF resurgence China → bearish soy meal.
- **Scraper target seeds:** Institutions (USTR, USDA FAS/ERS, EPA, EU Commission, DG TRADE, WTO, MAPA Brazil, CONAB, Ibama, Argentina Economía/AFIP, MOA China, NDRC, Sinograin, COFCO, MPOB, Indonesian Coordinating Ministry of Economic Affairs, RenovaBio/ANP); key ports/routes (Santos, Paranaguá, Rosario, Mississippi, BR-163, Arco Norte, Panama Canal, Suez, Danube, Odessa); thematic hooks (B40, LCFS, SAF, EUDR, antidumping, TRQ, retenciones, sojadólar, port strike, rail strike, export ban, state reserves).
- **Scoring framework (apply in pipeline):** relevance (producer/route/policy × soybean keyword density), directional prior (bullish/bearish/uncertain), conviction (source quality + specificity), half-life (strike < mandate < legislation), cross-asset boost (e.g., oil ↑ + mandate ↑ = soy oil double-bullish).

---

## Page 3: Strategy (Business Intelligence)

### Required Data Sources
| Data Source | Current Status | Location | Notes |
|------------|----------------|----------|-------|
| Processor operations | ❌ MISSING | — | ADM, Bunge, Cargill capacity/schedules |
| `usda_wasde_complete` | ❌ MISSING | — | Monthly S&D balance |
| `export_sales_weekly` | ❌ MISSING | — | USDA FAS (client priority #1) |
| `crush_weekly` | ❌ MISSING | — | NOPA weekly crush report |
| `food_manufacturing` | ❌ MISSING | — | Census/BLS data |
| `restaurant_sales` | ❌ MISSING | — | Bureau of Economic Analysis |
| `inter_commodity_spreads` | ⚠️ PARTIAL | Can derive from prices | Need ZL-ZS, ZL-palm, ZL-crude |
| Historical seasonality | ⚠️ PARTIAL | Price history exists | Need 5-year aggregations |

### Required Views/Features
- **Calendar heat map**: Optimal buying days (ML output)
- **Trump post tracker**: `ice_trump_intelligence` table exists, needs correlation analysis
- **Seasonal patterns**: 5-year rolling averages
- **Contract optimizer**: Spot vs forward strategy (ML-driven)
- **Interactive map**: US production/crush/storage by region
- **Trade flow animation**: Global supply/demand visualization
- **Profitability calculator**: Crush margin, storage cost, basis tools

---

## Page 4: Trade Intelligence

### Required Data Sources
| Data Source | Current Status | Location | Notes |
|------------|----------------|----------|-------|
| `china_trade_relations` | ⚠️ PARTIAL | GDELT table exists | Need Phase One deal tracking |
| `us_china_phase_deals` | ❌ MISSING | — | USTR/USDA historical |
| `brazil_china_agreements` | ❌ MISSING | — | News/GDELT scraping |
| `india_import_policies` | ❌ MISSING | — | Policy monitoring |
| `congressional_ag_committee` | ❌ MISSING | — | FEC Marketplace + congress.gov |
| `farm_bill_negotiations` | ❌ MISSING | — | News scraping |
| `usd_index`, `brl_real`, `cny_yuan` | ⚠️ PARTIAL | `multi_source_collector` has some FX | Need USD/CNY, USD/BRL expansion |
| Trump impact table | ⚠️ EXISTS | `ice_trump_intelligence` | Needs correlation metrics |

### Required Views/Features
- **Tariff threat matrix**: Probability × rate by country/commodity
- **Trump social analyzer**: Real-time parsing + historical correlation
- **Congressional votes tracker**: Upcoming votes + member positions
- **Trade flow disruption map**: Normal vs disrupted routes
- **Currency competitive matrix**: FX impact on US vs Brazil soybean prices
- **DEFCON-style threat gauge**: Composite risk score

---

## Cross-Page Requirements

### Google Marketplace Integrations (from blueprint)
| Dataset | Purpose | Status |
|---------|---------|--------|
| `bigquery-public-data.gdelt_bq.events` | China trade signals, tariff events | ✅ Active ingestion |
| `federal-election-commission.fec_2024` | Political influence on trade policy | ❌ Not integrated |
| `noaa-public.ghcn_d.ghcnd_*` | Global weather stations | ⚠️ NOAA script exists, check coverage |
| `bigquery-public-data.noaa_global_forecast_system` | Weather forecasts | ❌ Not integrated |
| `bls-public-data.cpi_unemployment` | Macro indicators | ❌ Not integrated |

### Mood Ring Pattern (All Pages)
- Requires ML model outputs with confidence scores
- Real-time price outlook (green = improving, red = deteriorating)
- Scenario slider impacts on forecast

### AI Agentic Features
- LLM-generated explanations for forecasts
- Natural language "Why?" answers for all major modules
- 4-hour narrative refresh cycle

---

## Current View Inventory vs Dashboard Needs

### Existing Curated Views (✅ Complete)
1. `curated.vw_economic_daily` → Feeds Page 1 macro drivers
2. `curated.vw_weather_daily` → Feeds Page 1 weather drivers, Page 3 risk maps
3. `curated.vw_volatility_daily` → Feeds Page 2 sentiment (technicals component)
4. `curated.vw_zl_features_daily` → Feeds Page 1 price intelligence
5. `curated.vw_social_intelligence` → Feeds Page 2 sentiment (social component)

### Legacy Views in `forecasting_data_warehouse` (Cleanup Targets)
| View Name | Dashboard Relevance | Action |
|-----------|---------------------|--------|
| `vw_brazil_precip_daily` | Page 3 weather risk maps | Archive to deprecated; covered by `curated.vw_weather_daily` |
| `vw_brazil_weather_summary` | Page 3 weather risk maps | Archive; consolidate into curated view |
| `vw_dashboard_brazil_weather` | Page 1/3 | Archive; rebuild as curated view if needed |
| `vw_dashboard_trump_intel` | Page 4 Trump analyzer | ⚠️ KEEP temporarily; migrate to curated |
| `vw_fed_rates_realtime` | Page 1 Fed slider | ⚠️ KEEP temporarily; migrate to curated |
| `vw_ice_trump_daily` | Page 4 Trump tracker | ⚠️ KEEP temporarily; consolidate with dashboard version |
| `vw_multi_source_intelligence_summary` | Page 2/4 | Archive; superseded by `curated.vw_economic_daily` |
| `vw_news_intel_daily` | Page 2 news grid | ⚠️ KEEP temporarily; migrate to curated |
| `vw_treasury_daily` | Page 1 macro drivers | Archive; covered by `curated.vw_economic_daily` |
| `vw_trump_effect_breakdown` | Page 4 impact analyzer | ⚠️ KEEP temporarily; needs correlation logic added |
| `vw_trump_effect_categories` | Page 4 categorization | ⚠️ KEEP temporarily; taxonomy mapping |
| `vw_trump_intelligence_dashboard` | Page 4 main view | ⚠️ KEEP temporarily; migrate to curated |
| `soy_oil_features` | Page 1 ZL features | Archive; superseded by `curated.vw_zl_features_daily` |

---

## Critical Gaps (Must Build)

### High Priority (Client Focus)
1. **China Export Sales** (`export_sales_weekly`) — Client Priority #1
2. **USDA Crop Progress** (`crop_progress_reports`) — Client Priority #2  
3. **CONAB Brazil Harvest** (`conab_harvest_forecasts`) — Client Priority #2
4. **EPA RFS Biofuel Mandates** (`rfs_mandates`) — Client Priority #3

### High Priority (Dashboard Core)
5. **ZL Price Rebuild** (CME/TradingEconomics → `staging.market_prices`)
6. **CFTC COT Reports** (`cftc_cot_reports`) — Used on Pages 1, 2
7. **USDA WASDE** (`usda_wasde_complete`) — Page 3 S&D analysis
8. **Crush Margins** (derived feature) — Page 1 real-time drivers
9. **Palm Oil Complete** (`palm_oil_complete`) — Substitute tracking

### Medium Priority (Enhanced Intelligence)
10. **Google Trends** (`google_trends`) — Page 2 sentiment
11. **Congressional Votes** (`congressional_ag_committee`) — Page 4
12. **Trade Flow Data** (USDA PSD Online) — Page 3 animation
13. **Restaurant Sales** (`restaurant_sales`) — Page 3 demand
14. **Storage Capacity** (`storage_capacity`) — Page 1 signals

### Low Priority (Nice-to-Have)
15. FEC political influence data
16. NOAA GFS forecast integration
17. BLS CPI food/energy breakdown
18. Processor capacity schedules (proprietary/hard to get)

---

## Recommended Cleanup Strategy

### Phase A: Safe Migrations (Do Now)
1. Archive truly redundant views to `deprecated`:
   - `vw_brazil_precip_daily` (covered by curated.vw_weather_daily)
   - `vw_brazil_weather_summary` (covered)
   - `vw_treasury_daily` (covered by curated.vw_economic_daily)
   - `vw_multi_source_intelligence_summary` (covered)
   - `soy_oil_features` (superseded by curated.vw_zl_features_daily)

2. Test dashboard breakage after archival (verify no code references)

### Phase B: Trump Intel Consolidation (Next)
1. Create `curated.vw_trump_trade_intelligence` consolidating:
   - `vw_dashboard_trump_intel`
   - `vw_ice_trump_daily`
   - `vw_trump_effect_breakdown`
   - `vw_trump_effect_categories`
   - `vw_trump_intelligence_dashboard`
2. Add correlation metrics and impact scoring
3. Point Page 4 dashboard to curated view
4. Archive all 5 legacy Trump views after validation

### Phase C: News & Fed Consolidation (Then)
1. Rebuild `curated.vw_news_intelligence` with full articles
2. Create `curated.vw_fed_monetary_policy` consolidating fed_rates + treasury
3. Archive `vw_news_intel_daily`, `vw_fed_rates_realtime`, `vw_dashboard_brazil_weather`

### Phase D: High-Priority Data Gaps (Parallel)
- Implement China export sales ingestion
- Implement USDA Crop Progress ingestion
- Implement CONAB harvest ingestion
- Implement EPA RFS ingestion
- Rebuild ZL price pipeline (CME primary)

---

## Decision Points for Review

### Question 1: Trump Views
**Should we consolidate all 5 Trump-related views into one `curated.vw_trump_trade_intelligence` now, or wait until after Page 4 dashboard wiring is complete?**

Recommendation: Consolidate now with clear SQL definitions, makes dashboard wiring cleaner.

### Question 2: News Intelligence
**The current `news_intelligence` table has 43 rows with missing metadata and only headlines (not full articles). Should we:**
- A) Clean existing data and continue building on it
- B) Start fresh with ScrapeCreators full-article ingestion (100 articles/topic backfill from Jan 1, 2025)

Recommendation: Option B (fresh start) per earlier discussion about full articles for neural training.

### Question 3: Weather Views
**Three Brazil weather views exist. Do we need Brazil-specific views or is the consolidated `curated.vw_weather_daily` sufficient?**

Recommendation: Consolidated view is sufficient; add `region` filtering in dashboard queries.

### Question 4: Immediate Cleanup
**Can we safely archive these 5 views to `deprecated` right now?**
- `vw_brazil_precip_daily`
- `vw_brazil_weather_summary`
- `vw_treasury_daily`
- `vw_multi_source_intelligence_summary`
- `soy_oil_features`

Recommendation: Yes, IF we first verify no Python scripts or dashboard code reference them (grep check).

---

## Next Steps

1. **User Decision**: Review decision points above
2. **Code Audit**: Grep all Python/JS files for legacy view references
3. **Execute Phase A**: Archive confirmed-redundant views
4. **Build Missing Views**: Trump consolidation, news rebuild
5. **Parallel Track**: Start ingestion for 4 client-priority data sources
6. **Dashboard Wiring**: Map curated views to Page 1-4 components

---

## Notes
- Dashboard requires extensive ML outputs (mood rings, scenario sliders, AI explanations) — separate workstream
- Many "missing" data sources are high-effort (Congressional votes, processor schedules) — prioritize ruthlessly
- Focus should be: (1) Client priorities, (2) Core price/forecast infrastructure, (3) Enhanced intel

