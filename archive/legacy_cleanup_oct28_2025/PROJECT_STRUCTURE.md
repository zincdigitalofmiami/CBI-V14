# CBI-V14 PROJECT STRUCTURE

## 🎯 CLEANED UP REPO STRUCTURE (October 20, 2025)

### **CORE APPLICATION**
```
forecast/
├── main.py                    # Clean API with academic rigor (6 endpoints)
├── market_signal_engine.py   # Market signal engine with proper calculations
└── requirements.txt          # Python dependencies
```

### **DATA INGESTION (CLEANED)**
```
cbi-v14-ingestion/
├── master_intelligence_controller.py    # Central coordinator
├── economic_intelligence.py             # Economic data collection
├── social_intelligence.py              # Social sentiment analysis
├── multi_source_news.py                # 18-category news monitoring
├── ingest_weather_noaa.py             # Weather data collection
├── ingest_volatility.py               # Volatility metrics
├── ingest_cftc_positioning_REAL.py    # CFTC data (real data)
├── ingest_social_intelligence_comprehensive.py  # Social intelligence
├── feature_registry.py               # Semantic metadata access
├── bigquery_utils.py                 # Data ingestion utilities
└── run_ingestion.py                  # Main collection orchestrator
```

### **BIGQUERY SQL (ORGANIZED)**
```
bigquery_sql/
├── signals/
│   └── create_ultimate_signal_views.sql  # Signal processing views
└── curated_facade/
    ├── vw_commodity_prices_daily.sql
    ├── vw_economic_daily.sql
    ├── vw_social_intelligence.sql
    ├── vw_soybean_oil_features_daily.sql
    ├── vw_volatility_daily.sql
    ├── vw_weather_daily.sql
    ├── vw_weather_global_daily.sql
    └── vw_zl_features_daily.sql
```

### **DASHBOARD (REACT/VITE)**
```
dashboard/
├── src/
│   ├── pages/
│   │   ├── DashboardPage.tsx
│   │   └── SentimentPage.tsx
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── tsconfig.json
```

### **SCRIPTS (ORGANIZED)**
```
scripts/
├── audits/
│   ├── audit_current_state.py
│   ├── audit_fake_data_removal.py
│   └── check_live_data.py
├── ci/
│   └── ci_schema_lint.sh
└── scrapers/
    ├── comprehensive_social_scraper.sh
    └── production_social_scraper.sh
```

### **DOCUMENTATION (CLEANED)**
```
docs/
├── plans/
│   └── CONSOLIDATED_FORWARD_PLAN.md    # Single source of truth
├── audits/
│   └── 2025-10/                        # Current audits
├── operations/
│   ├── END_OF_DAY_SHUTDOWN_CHECKLIST.md
│   ├── EXECUTION_PLAN_VALIDATED.md
│   ├── FORENSIC_AUDIT_V14_FINAL.md
│   ├── scripts/
│   │   └── create_intelligence_tables.sql
│   └── schemas/
│       └── models_vw_master_feature_set_v1.md
├── research/
│   ├── BRAZIL_WEATHER_OPTIONS_ANALYSIS.md
│   └── LOAD_PALM_OIL_CSV.md
├── rules/
│   └── CURSOR_RULES.md
├── governance/
│   └── warehouse_governance.md
├── FEATURE_REGISTRY_README.md
├── REFERENCE_MULTI_SOURCE_SCRAPING.md
└── BLOCKER_FIX_STATUS.md
```

### **DATA (CLEANED)**
```
data/
├── twitter/                    # Social intelligence data
├── facebook/                   # Social intelligence data
├── linkedin/                   # Social intelligence data
├── youtube/                    # Social intelligence data
├── reddit/                     # Social intelligence data
├── tiktok/                     # Social intelligence data
├── truth_social/              # Social intelligence data
└── ingestion_manifest.json    # Data collection manifest
```

### **DELETED BULLSHIT:**
- ❌ `cache/` - 100+ outdated API responses
- ❌ `archive/` - Old audit files (moved to docs/audits)
- ❌ `data/uploads/` - Old CSV uploads
- ❌ `data/snapshots/` - Old snapshots
- ❌ `test.csv` - Test file
- ❌ `latest_signal.json` - Generated file
- ❌ `bigquery_schema_market_prices.json` - Old schema
- ❌ `forecast/main_backup.py` - Backup file
- ❌ `forecast/main_clean.py` - Temporary file
- ❌ `cbi-v14-ingestion/secrets.json` - Should be in Secret Manager
- ❌ `cbi-v14-ingestion/*_FIXED.py` - Fixed versions
- ❌ `cbi-v14-ingestion/trump_*` - Trump-focused bullshit
- ❌ `cbi-v14-ingestion/ice_trump_intelligence.py` - Trump bullshit
- ❌ `cbi-v14-ingestion/monitor_vix_trump_correlation.py` - Trump bullshit

### **CLEAN API ENDPOINTS (ACADEMIC RIGOR):**
- ✅ `/api/v1/market/intelligence` - Comprehensive market intelligence
- ✅ `/api/v1/signals/comprehensive` - All 847+ signals
- ✅ `/api/v1/signals/market-engine` - Market signal engine
- ✅ `/data/prices` - Real commodity price data
- ✅ `/data/features` - Feature metadata for neural networks
- ✅ `/admin/upload-csv` - CSV data upload

### **RESULT:**
**CLEAN, ORGANIZED REPO** with **ACADEMIC RIGOR** and **NO BULLSHIT**!
