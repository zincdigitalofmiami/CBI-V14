# CBI-V14 Commodity Forecasting Platform

**Production-grade soybean oil futures forecasting with comprehensive intelligence gathering**

## 🎯 Project Overview

Advanced forecasting system using BigQuery data warehouse, neural networks, and multi-source intelligence collection for soybean oil (ZL) futures trading advantage.

## 📊 Current Data Architecture

### **Factor-Specific Tables (Production Ready)**
- `soybean_oil_prices`: 519 ZL futures rows (PRIMARY TARGET)
- `soybean_meal_prices`: 519 ZM co-product rows  
- `soybean_prices`: 519 ZS raw soybean rows
- `palm_oil_prices`: 421 FCPO substitute rows
- `corn_prices`: 519 ZC competing crop rows
- `cotton_prices`: 519 CT competing crop rows
- `cocoa_prices`: 441 CC soft commodity rows
- `treasury_prices`: 136 ZN interest rate proxy rows
- `weather_data`: 9,505 weather observations (US + Brazil)
- `volatility_data`: 776 IV/HV volatility metrics
- `economic_indicators`: 3,220 macro indicators (FRED)
- `ice_trump_intelligence`: 166 political events
- `feature_metadata`: 29 semantic features (NEW)

### **Semantic Metadata System (NEW)**
- **29 features** with economic context and neural understanding
- **6 categories**: POLICY, COMMODITY, MACRO, WEATHER, SENTIMENT, VOLATILITY
- **8 political features** with impact scores (40-85) and affected commodities
- **9 futures contracts** mapped (ZL, ZM, ZS, FCPO, ZC, CT, CC, ZN, CL)
- **Source reliability scoring** (0.65-0.98) for confidence weighting
- **Geographic context** with top producing countries
- **Natural language aliases** for AI chat interfaces

### **Intelligence Collection System**
- News sentiment monitoring (18 categories)
- Economic indicator tracking (Fed, BLS, Treasury)
- Weather intelligence (NOAA + professional models)
- Social sentiment analysis (Reddit, forums)
- ICE enforcement impact monitoring
- Trump policy effect tracking
- Shipping/logistics intelligence

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8+ with pip
- Google Cloud SDK with BigQuery access
- Project: `cbi-v14`
- BigQuery dataset: `forecasting_data_warehouse`

### **Setup Environment**
```bash
# Clone and setup
git clone [repository-url]
cd CBI-V14

# Install dependencies
pip install -r requirements.txt

# Set up Google Cloud authentication
gcloud auth login
gcloud config set project cbi-v14

# Test BigQuery connection
python3 -c "from google.cloud import bigquery; print('✅ BigQuery connected')"
```

### **Run Intelligence Collection**
```bash
# Start comprehensive data collection
cd cbi-v14-ingestion
python3 run_ingestion.py

# Test feature registry (NEW)
python3 feature_registry.py
```

## 🎉 Recent Accomplishments (Latest Update)

### **Semantic Metadata System (NEW)**
- ✅ **29 features** documented with economic context
- ✅ **8 political features** with impact scores (40-85) and affected commodities
- ✅ **6 enhancement columns** added (policy_impact_score, affected_commodities, source_reliability_score, related_futures_contract, is_crush_component, top_producing_countries)
- ✅ **9 futures contracts** mapped (ZL, ZM, ZS, FCPO, ZC, CT, CC, ZN, CL)
- ✅ **Source reliability scoring** (0.65-0.98) for confidence weighting
- ✅ **Geographic context** with top producing countries
- ✅ **Natural language aliases** for AI chat interfaces
- ✅ **Feature registry Python module** updated to support all enhancements

### **Data Quality Improvements**
- ✅ **Palm oil data** loaded (421 rows, Feb 2024 - Oct 2025)
- ✅ **Ghost tables cleaned** (deleted empty fed_rates, currency_data, intelligence_cycles)
- ✅ **TradingEconomics scraper** fixed and stopped (was returning wrong prices)
- ✅ **Canonical metadata** added to 4 critical tables
- ✅ **Temperature conversion** deferred (too risky for production data)

### **Architecture Enhancements**
- ✅ **Feature registry** with 8 key methods for neural/AI access
- ✅ **Natural language translation** ('interest rates' → fed_funds_rate)
- ✅ **AI explanation generation** for chat interfaces
- ✅ **Cross-asset relationship mapping** (crush margins, substitution dynamics)
- ✅ **Political impact quantification** (trade war = 85, legal challenges = 40)

## 📈 Current Status

### **Data Volume**
- **Total BigQuery tables**: 22 (with data)
- **Total rows**: ~20,000+ across all tables
- **Data sources**: FRED, NOAA, TradingEconomics, Barchart, INMET, White House, ICE
- **Update frequency**: Hourly (TradingEconomics), Daily (FRED, NOAA), Real-time (political events)

### **Feature Coverage**
- **Commodities**: Soybean oil (ZL), soybeans (ZS), soybean meal (ZM), palm oil (FCPO), corn (ZC), cotton (CT), cocoa (CC), treasury (ZN)
- **Macro**: Fed funds rate, 10-year treasury, CPI, dollar index, USD/BRL, USD/CNY
- **Weather**: Temperature, precipitation (US + Brazil)
- **Political**: 8 Trump/ICE categories with impact scoring
- **Sentiment**: News intelligence, social sentiment, ICE/Trump intelligence
- **Volatility**: Implied volatility, IV/HV ratio

### **Neural Network Readiness**
- ✅ **Semantic understanding** - All features have economic context
- ✅ **Impact weighting** - Political features scored 40-85
- ✅ **Reliability scoring** - Source confidence 0.65-0.98
- ✅ **Cross-asset mapping** - Futures contracts and relationships
- ✅ **Geographic context** - Producing countries for each commodity
- ✅ **Natural language** - Chat aliases for AI interfaces

## 🔧 Development

### **Key Files**
- `cbi-v14-ingestion/feature_registry.py` - Semantic metadata access
- `cbi-v14-ingestion/bigquery_utils.py` - Data ingestion utilities
- `cbi-v14-ingestion/run_ingestion.py` - Main collection orchestrator
- `forecast/main.py` - FastAPI forecast service
- `create_intelligence_tables.sql` - BigQuery schema definitions

### **Testing**
```bash
# Test feature registry
python3 cbi-v14-ingestion/feature_registry.py

# Test BigQuery connection
python3 -c "from google.cloud import bigquery; client = bigquery.Client(); print('✅ Connected')"

# Test data ingestion
cd cbi-v14-ingestion
python3 run_ingestion.py
```

## 📁 Project Structure

```
CBI-V14/
├── forecast/                    # FastAPI forecasting service
│   ├── main.py                 # SARIMAX forecast API
│   ├── requirements.txt        # Python dependencies  
│   └── Dockerfile             # Container config
├── cbi-v14-ingestion/         # Intelligence collection system
│   ├── master_intelligence_controller.py  # Central coordinator
│   ├── ice_trump_intelligence.py          # ICE & Trump monitoring
│   ├── multi_source_news.py              # 18-category news monitoring
│   ├── economic_intelligence.py          # Economic data collection
│   ├── social_intelligence.py            # Social sentiment analysis
│   ├── shipping_intelligence.py          # Logistics monitoring
│   ├── intelligence_hunter.py            # Neural correlation discovery
│   ├── load_barchart.py                  # Commodity price ingestion
│   ├── ingest_weather_noaa.py           # Weather data collection
│   └── ingest_volatility.py             # Volatility metrics
├── bigquery_sql/              # SQL feature engineering
├── data/csv/                  # Raw data files (Barchart exports)
├── scripts/                   # Rule enforcement scripts
└── docs/                     # Documentation and architecture
```

## 🔒 Core Rules

### **CRITICAL: NO MOCK DATA EVER**
- All data sources are real BigQuery tables
- No hardcoded arrays or fake data
- Empty states show "No data available" instead of mock content

### **Data Quality Standards**
- Factor-specific tables for neural network training
- Multiple backup sources per data category
- Automated correlation discovery and source hunting
- Real-time monitoring with graceful failure handling

## 🧠 Intelligence Architecture

### **18-Category Monitoring System**
1. China Demand (60% of trade)
2. Brazil Policy (50% of exports)  
3. Argentina Policy (export tax effects)
4. US Policy (Farm Bill, RFS, tariffs)
5. Biofuel Policy (46% of US production)
6. Palm Oil Geopolitics (substitution effects)
7. Weather Intelligence (35-45% price variance)
8. Trade Wars & Disputes
9. Shipping/Logistics (chokepoints)
10. Energy Markets (processing costs)
11. Macro/FX (15-20% variance)
12. Crop Disease (demand effects)
13. ESG/Regulation (EUDR compliance)
14. Labor Unrest (strikes, protests)
15. **ICE Labor Enforcement** (agricultural labor disruption)
16. **Trump Effect** (policy volatility, trade changes)
17. Technology (precision agriculture)
18. Financial Flows (fund positioning)

### **Neural Network Source Discovery**
- Automatic correlation analysis across all data sources
- AI-powered hunting for new data sources based on discovered patterns
- Quality scoring and automatic integration of high-value sources

## 📈 Forecasting Capabilities

### **Current Models**
- **SARIMAX**: Statistical model with weather and economic factors
- **BigQuery ML**: Auto-ARIMA baseline (planned)
- **Neural Networks**: LSTM/Transformer models (development)

### **Features Available**
- Price data: Daily OHLCV for 8 commodities
- Weather factors: Argentina + US precipitation/temperature  
- Technical indicators: SMA_5, SMA_20, volatility
- Volatility metrics: IV/HV ratios, implied volatility
- Economic indicators: Fed rates, employment data
- Sentiment analysis: Multi-source news categorization

## 🛠 Development Commands

```bash
# Check project rules compliance
make check-rules

# Run linting and formatting  
make lint && make format

# Clean build artifacts
make clean

# Test Docker build
docker-compose up --build

# Run intelligence collection
cd cbi-v14-ingestion && python3 master_intelligence_controller.py
```

## 📚 Documentation

- `PROJECT_RULES.md` - Development standards and rules
- `CURSOR_RULES.md` - AI assistant guidelines  
- `INTELLIGENCE_ARCHITECTURE.md` - Intelligence system design
- `CONTRIBUTING.md` - How to contribute
- `plan-detailed.todo` - Detailed implementation plan

## 🎁 Key Achievements (Today)

- ✅ **Factor-based BigQuery architecture** (8 specialized commodity tables)
- ✅ **Real data ingestion** (4,017 rows commodity data, 2,008 weather observations)
- ✅ **Intelligence collection system** (18 categories, 50+ sources)
- ✅ **Neural network correlation discovery** (automated source hunting)
- ✅ **ICE & Trump effect monitoring** (political/labor intelligence)
- ✅ **Production rules enforcement** (NO MOCK DATA compliance)

## 🔜 Next Steps

**Tomorrow's Priority:**
1. Fix forecast service numpy dependency issue
2. Test complete forecast pipeline with real data
3. Create Vite dashboard for intelligence visualization
4. Deploy continuous intelligence monitoring
5. Train neural network models on collected data

---

**Designed for information superiority in commodity markets**  
**Built with production-grade data architecture and comprehensive intelligence gathering**