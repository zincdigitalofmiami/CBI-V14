# CB V14 Page Architecture

Fully AI agentic experience with scenario analysis sliders. Each slider block should sit in a wide row with a mood ring banner on top that turns green when price outlook improves and red when it deteriorates. Apply the mood ring pattern anywhere forecasts drive decision making (all pages where applicable). AI forecast explanations should accompany each major module.

---

## Page 1: Dashboard (Chris's Daily Decision Page)

### Top: Mood Ring & Signal System
- Giant circular indicator (≈ 1/3 page width)
- Confidence meter (0–100%) based on neural network agreement

### Middle: Live Price Intelligence
- Main chart (≈60% width)
  - ZL futures
  - AI-enhanced 30-day projection with confidence bands
  - Critical levels
  - Volume spikes tied to China buying
- Side panel (≈40% width)
  - Real-time drivers: China buying, Brazil weather, crush margins

### Bottom: Procurement Scenarios
- Interactive sliders:
  - Fed rates change in 30 days
  - China relations improve/deteriorate
  - Weather outlook (soy regions) improves/worsens
  - ICE/Labor shortage improves/worsens
- Output table with cost implications
- Risk alerts summary

**Data Sources**
- `zl_data` (authoritative price feed)
- `fed_rates_real_time`
- `tariff_conflicts`
- `china_relations`
- `procurement_signals`
- `china_crushing_margins`
- `storage_capacity`
- `cftc_cot_reports`

---

## Page 2: Sentiment

### Top: Market Mood Ring
- Semicircle gauge (Extremely Bearish → Extremely Bullish)
- Weighted inputs: news sentiment 40%, fund positioning 30%, technicals 20%, weather 10%

### Middle: 16-Category News Grid (4x4)
- Tiles: China Demand, Brazil Infrastructure, US Policy, Biofuels, Palm Oil, Trade Wars, Weather, Processing, etc.
- Click tile → expanded list with impact scores

### Bottom: Narrative Intelligence
- AI summary updated every 4 hours
- Key changes vs yesterday (bullet list with ✓/⚠ markers)

**Data Sources**
- `social_sentiment`
- `google_trends`
- `cftc_cot_reports`
- `news_articles`
- Policy/regulation reference tables

---

## Page 3: Strategy (Chris's Business Intelligence Page)

### Top: Mood Ring + Procurement Timing
- Left panel: Optimal procurement windows
  - Calendar heat map (best/worst buying days)
  - Overlays: economic/trade events, interest rate calls
  - Upcoming market-moving events
  - Social sentiment heat map
  - Trump post tracker vs price reactions
  - Seasonal patterns graph (5-year averages, harvest pressure, Chinese buying seasons, Fed rates)
- Right panel: Contract strategy optimizer
  - Recommendations (e.g., lock %, stay spot, forward contract)
  - Contract comparison table (spot/30d/90d, basis, storage cost)

### Middle: Industry Intelligence (4 columns)
1. **Key Players**
   - Competitor procurement activity (national & Las Vegas)
   - Processor intel (ADM, Bunge, Cargill, etc.)
2. **Pricing Trends**
   - Basis tracker, quality premiums, regional differentials, transport impact
3. **Recent Developments**
   - Critical changes last 7 days with impact tags (HIGH/MED/LOW)
4. **Market Structure**
   - Futures curve, spreads, technical setups, options positioning

### Bottom: Deep Dive Analytics
- **Tab 1: U.S. Production & Storage**
  - Interactive map: production, crush capacity, storage utilization
  - Table: weekly crush rates, oil yield, capacity utilization
- **Tab 2: Global Supply & Demand**
  - Stacked bar S&D by country
  - Ending stocks trend
  - Trade flow animation
- **Tab 3: Soy Complex Value Chain**
  - Flowchart: soy → oil/meal/hulls, downstream uses
  - Profitability calculator
- **Tab 4: Food & Industrial Demand**
  - Restaurant industry health, openings, QSR vs casual trends
  - Competing oils market share & substitution triggers
  - Biodiesel demand curve (RFS, state programs)

### Right Sidebar: Strategy Tools
- Storage cost calculator
- Hedge ratio optimizer
- Basis convergence tracker
- Forward curve analyzer
- Performance metrics (avg purchase vs market, best/worst decisions, YTD savings)
- AI strategy suggestions (e.g., options ideas, timing alerts)

**Data Sources**
- Processor operations (capacity, schedules)
- `usda_wasde_complete`
- `export_sales_weekly`
- `crush_weekly`
- `food_manufacturing`, `restaurant_sales`
- `inter_commodity_spreads`
- Historical price/seasonality tables

---

## Page 4: Trade Intelligence

### Top: Trade Policy Dashboard
- Left panel: Tariff threat matrix (probability/proposed rate by country/commodity + timeline)
- Center: Trump Truth Social/Twitter impact analyzer
  - Real-time parsing
  - Historical correlation metrics
  - Alert system & prediction model
- Right panel: Congressional trade votes
  - Upcoming votes, member positions, impact assessments

### Middle: Global Trade Relations (4 columns)
1. **US–China Relations**
   - Status, purchase commitments, retaliation risk, key indicators
2. **Brazil Competition**
   - Deal tracking, currency edge, infrastructure progress, market share
3. **India/Pakistan Dynamics**
   - Import duties, palm vs soy policies, GMO stance, domestic production
4. **EU/UK Regulations**
   - Deforestation rules, sustainability premiums, conflict impacts, Brexit effects

### Bottom: Deep Dive Intelligence Tabs
- **Tab 1: Tariff Scenario Modeling**
  - Sliders for tariff %, impact on exports/basis/prices, historical examples, mitigation strategies
- **Tab 2: Trade Flow Disruption Map**
  - Animated normal vs disrupted flows, alternative routes
- **Tab 3: Political Intelligence**
  - Decision makers, committee positions, lobbying activity
- **Tab 4: Currency & Competitive Position**
  - FX dashboards, competitive cost matrix, shipping differentials

### Right Sidebar: Trade War Alerts
- Threat level gauge (DEFCON-style)
- Flash updates (last 24h)
- Historical patterns
- Action items for Chris

**Data Sources**
- `china_trade_relations`
- `us_china_phase_deals`
- `brazil_china_agreements`
- `india_import_policies`
- `congressional_ag_committee`
- `farm_bill_negotiations`
- `usd_index`, `brl_real`, `cny_yuan`
- Trump impact sentiment table
- Policy & regulation datasets

---

## Enhanced China & Tariff Focus (Google Marketplace)

### Geopolitical & Trade Relations
- `bigquery-public-data.gdelt_bq.events` → `raw.gdelt_events`
- `federal-election-commission.fec_2024` → `raw.political_influence`
- Functions: `ingest_china_trade_relations`, `ingest_us_china_phase_deals`, `ingest_china_tariff_announcements`, `ingest_china_quota_changes`, `ingest_china_state_media_signals`, `ingest_brazil_china_agreements`, `ingest_ustr_301_updates`, `ingest_wto_dispute_status`

### Weather (Global)
- `noaa-public.ghcn_d.ghcnd_*` → `raw.weather_stations_global`
- `bigquery-public-data.noaa_global_forecast_system` → `raw.weather_forecasts`
- Functions: `ingest_noaa_complete`, `ingest_gfs_forecasts`, `ingest_brazil_inmet`, `ingest_argentina_smn`, `ingest_china_weather_impacts`, `ingest_drought_monitor`

### China Demand Intelligence
- GDELT event monitoring for trade signals (Actor1CountryCode='CHN', EventRootCode in 14/10, GoldsteinScale filters)

### Economic Indicators
- `bls-public-data.cpi_unemployment` → `raw.economic_indicators`
- Functions: `ingest_cpi_food_energy`, `ingest_usd_strength_index`, `ingest_china_gdp_growth`, `ingest_china_cpi_pork`

### Biofuels & Energy
- Functions: `ingest_rfs_mandates`, `ingest_biodiesel_blending_rates`, `ingest_saf_aviation_fuel`, `ingest_renewable_diesel_capacity`, `ingest_crude_oil_correlation`

### U.S. Domestic Market
- Functions: `ingest_usda_wasde_complete`, `ingest_crop_progress_reports`, `ingest_nass_production_estimates`, `ingest_export_sales_weekly`, `ingest_export_inspections`, `ingest_crush_weekly`, `ingest_stocks_quarterly`

### Substitute Products
- Functions: `ingest_palm_oil_complete`, `ingest_sunflower_oil`, `ingest_rapeseed_oil`, `ingest_corn_oil`

### Tariff & Policy Intelligence
- GDELT queries for tariff events (EventCode 0871/1056, Actor codes)
- Functions: `ingest_section_301_tariffs`, `ingest_antidumping_cases`, `ingest_china_retaliatory_tariffs`, `ingest_tariff_exclusions`, `ingest_trade_war_escalation`

### Feature Engineering Concepts
- `features.china_demand_composite`
- `features.tariff_risk_matrix`
- `features.weather_supply_impact`
- `features.procurement_signals_enhanced`

---

## Additional Dashboard Ideas (Selected Focus)

### Page 1 Enhancements
- China Demand Meter
- Tariff risk alert module
- Weather-adjusted price forecast
- Buy/Hold/Wait signal (with dollar impact)

### Page 2 Enhancements (China & Tariff Intelligence)
- China import dashboard
- Tariff timeline & impact tracker
- GDELT trade-war sentiment meter

### Page 3 Strategy Enhancements
- Supply/demand balance
- Substitute oil spreads
- Procurement best practices
- NOAA GFS weather risk maps

---

### Data Source References
- FEC Campaign Finance (trade policy influence)
- Trade Compliance Resource Hub (tariff tracking)
- NOAA GHCN-D, NOAA Global Forecast System (weather)
- GDELT 2 Events (geopolitical events)
- BLS CPI & Unemployment
- Additional trade/tariff trackers linked in brief





