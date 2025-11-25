# News Bucket Taxonomy (v1.0)

Strategic news segmentation for CBI-V14 ZL forecasting platform. News is organized into market-aligned buckets similar to weather/location segmentation, enabling direct dashboard queries without parsing.

---

## Quick Reference

```sql
-- Dashboard query pattern (no parsing required)
SELECT * FROM `cbi-v14.raw_intelligence.news_bucketed` 
WHERE bucket = 'tariffs_trade_policy'
  AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY date DESC;
```

---

## Primary Buckets (Direct Market Drivers)

### 1. `tariffs_trade_policy`

| Attribute | Value |
|-----------|-------|
| **Focus** | Trade wars, tariffs, USTR announcements |
| **Impact** | Direct price impact via export competitiveness |
| **Priority** | P0 - Highest |
| **Sources** | USTR.gov, Reuters Trade, Bloomberg Trade |

**Keywords/Signals:**
- tariff, tariffs, trade war, anti-dumping
- USTR, Section 301, countervailing duties
- export tax, import ban, retaliatory
- trade agreement, trade deal, trade talks
- WTO dispute, trade sanctions

**Dashboard Use Case:**
- Trade policy alerts
- Tariff rate tracker
- Policy timeline visualization

---

### 2. `china_demand`

| Attribute | Value |
|-----------|-------|
| **Focus** | China purchases, cancellations, import policies |
| **Impact** | Largest soybean importer - demand signal |
| **Priority** | P0 - Highest |
| **Sources** | Xinhua, COFCO announcements, USDA FAS |

**Keywords/Signals:**
- China imports, China purchases, China cancellations
- Sinograin, COFCO, China reserves
- Dalian commodity exchange, DCE
- soybean crush (China), swine herd
- Phase 1 deal, China tariffs

**Dashboard Use Case:**
- China demand tracker
- Purchase/cancellation alerts
- Import volume charts

---

### 3. `biofuel_policy`

| Attribute | Value |
|-----------|-------|
| **Focus** | EPA RFS, RVO, biodiesel mandates |
| **Impact** | 40% of US soybean oil goes to biofuels |
| **Priority** | P0 - Highest |
| **Sources** | EPA.gov, RFA, EIA, ACE |

**Keywords/Signals:**
- RFS, RINs, RVO, renewable fuel standard
- biodiesel tax credit, 45Z, blenders credit
- EPA mandate, biomass-based diesel
- renewable diesel, sustainable aviation fuel
- small refinery exemption, SRE

**Dashboard Use Case:**
- RFS mandate tracker
- RIN price visualization
- Policy calendar

---

### 4. `brazil_harvest`

| Attribute | Value |
|-----------|-------|
| **Focus** | Brazil harvest updates, export logistics |
| **Impact** | Largest soybean exporter - supply competition |
| **Priority** | P0 - Highest |
| **Sources** | Conab, IBGE, AgRural, Reuters Commodities |

**Keywords/Signals:**
- Conab, Brazil harvest, Mato Grosso
- harvest delay, replanting, Brazil basis
- Paranagua, Santos port, Brazil exports
- safrinha, safra, Brazil crush
- ABIOVE, Aprosoja

**Dashboard Use Case:**
- Brazil harvest progress
- Export pace tracker
- Basis monitoring

---

### 5. `palm_oil_substitution`

| Attribute | Value |
|-----------|-------|
| **Focus** | Palm oil prices, Indonesia/Malaysia policy |
| **Impact** | Direct competitor/substitute for soybean oil |
| **Priority** | P0 - Highest |
| **Sources** | MPOB, GAPKI, Reuters Palm Oil |

**Keywords/Signals:**
- CPO, crude palm oil, palm oil
- Indonesia export ban, export levy
- B35 mandate, B40, palm biodiesel
- Malaysia inventory, MPOB data
- palm-soy spread, substitution

**Dashboard Use Case:**
- Palm oil price tracker
- Indonesia/Malaysia policy alerts
- Substitution spread charts

---

## Secondary Buckets (Supporting Context)

### 6. `crush_margins`

| Attribute | Value |
|-----------|-------|
| **Focus** | Processing economics, crush spreads |
| **Impact** | Processor profitability drives demand |
| **Priority** | P1 - High |
| **Sources** | NOPA, USDA NASS, CME |

**Keywords/Signals:**
- crush spread, board crush
- meal demand, oil share
- NOPA crush report, crush capacity
- processing margins, crush plants
- soybean meal, soybean oil ratio

**Dashboard Use Case:**
- Crush margin tracker
- NOPA report alerts
- Oil share visualization

---

### 7. `logistics_shipping`

| Attribute | Value |
|-----------|-------|
| **Focus** | Mississippi river, Panama canal, freight |
| **Impact** | Transport costs affect basis and competitiveness |
| **Priority** | P1 - High |
| **Sources** | USACE, ACP, Freightos |

**Keywords/Signals:**
- Mississippi river levels, low water
- Panama canal, transit delays
- barge freight, rail strike
- Gulf port, export elevator
- PNW exports, vessel lineup

**Dashboard Use Case:**
- River level tracker
- Freight rate charts
- Port congestion alerts

---

### 8. `macro_fx`

| Attribute | Value |
|-----------|-------|
| **Focus** | USD strength, BRL/CNY moves, Fed policy |
| **Impact** | Dollar strength suppresses ag exports |
| **Priority** | P1 - High |
| **Sources** | FRED, Fed, Bloomberg FX |

**Keywords/Signals:**
- strong dollar, dollar index, DXY
- real weakness, BRL, Brazilian real
- Fed pivot, FOMC, rate decision
- inflation, CPI, PCE
- emerging markets, CNY, yuan

**Dashboard Use Case:**
- Dollar index tracker
- FX correlation charts
- Fed policy timeline

---

## Additional Buckets (Contextual)

### 9. `argentina_policy`

| Attribute | Value |
|-----------|-------|
| **Focus** | Export taxes, currency, policy changes |
| **Impact** | #3 soybean exporter - supply disruptions |
| **Priority** | P2 - Medium |

**Keywords/Signals:**
- Argentina export tax, retenciones
- peso devaluation, currency controls
- Argentina harvest, Rosario
- Argentina drought, La Niña

---

### 10. `weather_crop_conditions`

| Attribute | Value |
|-----------|-------|
| **Focus** | Drought, floods, harvest impacts |
| **Impact** | Yield and quality impacts |
| **Priority** | P2 - Medium |

**Keywords/Signals:**
- drought, excessive heat, flooding
- crop conditions, yield forecast
- planting progress, harvest progress
- ENSO, La Niña, El Niño
- soil moisture, SPEI

---

### 11. `trump_policy`

| Attribute | Value |
|-----------|-------|
| **Focus** | Truth Social, executive orders |
| **Impact** | Policy uncertainty, trade rhetoric |
| **Priority** | P2 - Medium |

**Keywords/Signals:**
- Truth Social, executive order
- tariff announcement, trade deal
- China trade, farm bailout
- USDA aid, MFP payment

---

### 12. `energy_crude_link`

| Attribute | Value |
|-----------|-------|
| **Focus** | Crude oil, heating oil, biodiesel link |
| **Impact** | Biodiesel margin tied to diesel prices |
| **Priority** | P2 - Medium |

**Keywords/Signals:**
- crude oil, WTI, Brent
- heating oil, ULSD, diesel
- OPEC, production cuts
- energy prices, refinery

---

### 13. `institutional_intel`

| Attribute | Value |
|-----------|-------|
| **Focus** | Cargill, ADM, Bunge signals |
| **Impact** | Major crushers set market tone |
| **Priority** | P3 - Low |

**Keywords/Signals:**
- Cargill, ADM, Bunge, LDC
- crush capacity, plant expansion
- earnings, guidance, outlook
- commodity trading, ABCD

---

### 14. `labor_enforcement`

| Attribute | Value |
|-----------|-------|
| **Focus** | ICE raids, farm labor shortages |
| **Impact** | Processing capacity impacts |
| **Priority** | P3 - Low |

**Keywords/Signals:**
- ICE raid, E-Verify
- farm labor shortage, H-2A
- meatpacking, processing plant
- labor strike, walkout

---

### 15. `legislation`

| Attribute | Value |
|-----------|-------|
| **Focus** | Farm Bill, agricultural policy |
| **Impact** | Long-term policy framework |
| **Priority** | P3 - Low |

**Keywords/Signals:**
- Farm Bill, USDA funding
- crop insurance, commodity programs
- conservation, CRP
- agricultural appropriations

---

### 16. `regulatory_compliance`

| Attribute | Value |
|-----------|-------|
| **Focus** | EUDR, sustainability, certifications |
| **Impact** | Market access requirements |
| **Priority** | P3 - Low |

**Keywords/Signals:**
- EUDR, deforestation regulation
- sustainability certification
- ISCC, RSPO, zero-deforestation
- carbon intensity, CI score

---

## BigQuery Table Schema

```sql
CREATE TABLE `cbi-v14.raw_intelligence.news_bucketed` (
  date DATE NOT NULL,
  bucket STRING NOT NULL,
  headline STRING,
  source STRING,
  url STRING,
  sentiment_score FLOAT64,
  relevance_score FLOAT64,
  keywords ARRAY<STRING>,
  raw_text STRING,
  ingestion_ts TIMESTAMP
)
PARTITION BY date
CLUSTER BY bucket, source;
```

---

## ScrapeCreator Script Mapping

| Bucket | Script | API Endpoint |
|--------|--------|--------------|
| `tariffs_trade_policy` | `scripts/scrapecreators/buckets/tariffs_trade_policy.py` | ScrapeCreator + USTR RSS |
| `china_demand` | `scripts/scrapecreators/buckets/china_demand.py` | ScrapeCreator + Xinhua |
| `biofuel_policy` | `scripts/scrapecreators/buckets/biofuel_policy.py` | ScrapeCreator + EPA RSS |
| `brazil_harvest` | `scripts/scrapecreators/buckets/brazil_harvest.py` | ScrapeCreator + Conab |
| `palm_oil_substitution` | `scripts/scrapecreators/buckets/palm_oil_substitution.py` | ScrapeCreator + MPOB |
| `crush_margins` | `scripts/scrapecreators/buckets/crush_margins.py` | ScrapeCreator + NOPA |
| `logistics_shipping` | `scripts/scrapecreators/buckets/logistics_shipping.py` | ScrapeCreator |
| `macro_fx` | `scripts/scrapecreators/buckets/macro_fx.py` | ScrapeCreator + FRED |

---

## Feature Aggregation

For training, news buckets are aggregated to daily features:

```sql
-- Example: Daily news feature aggregation
SELECT
  date,
  COUNTIF(bucket = 'tariffs_trade_policy') AS tariff_news_count,
  COUNTIF(bucket = 'china_demand') AS china_news_count,
  AVG(IF(bucket = 'tariffs_trade_policy', sentiment_score, NULL)) AS tariff_sentiment_avg,
  AVG(IF(bucket = 'china_demand', sentiment_score, NULL)) AS china_sentiment_avg
FROM `cbi-v14.raw_intelligence.news_bucketed`
GROUP BY date;
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-24 | Initial taxonomy with 16 buckets |

