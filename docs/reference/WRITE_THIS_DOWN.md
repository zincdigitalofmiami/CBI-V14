# 📝 WRITE THIS DOWN - OFFICIAL PRODUCTION SYSTEM

**Date**: November 5, 2025  
**Print This Page and Keep It Handy**

---

## PRODUCTION BQML MODELS
```
cbi-v14.models_v4.bqml_1w
cbi-v14.models_v4.bqml_1m
cbi-v14.models_v4.bqml_3m
cbi-v14.models_v4.bqml_6m
```

## PRODUCTION TRAINING DATASETS (ALL INGESTION GOES HERE)
```
cbi-v14.models_v4.production_training_data_1w
cbi-v14.models_v4.production_training_data_1m
cbi-v14.models_v4.production_training_data_3m
cbi-v14.models_v4.production_training_data_6m
```

## INGESTION SCRIPTS TO UPDATE
```
scripts/hourly_prices.py → production_training_data_*
scripts/daily_weather.py → production_training_data_*
ingestion/ingest_social_intelligence_comprehensive.py → production_training_data_*
ingestion/backfill_trump_intelligence.py → production_training_data_*
ingestion/ingest_market_prices.py → production_training_data_*
ingestion/ingest_cftc_positioning_REAL.py → production_training_data_*
ingestion/ingest_usda_harvest_api.py → production_training_data_*
ingestion/ingest_eia_biofuel_real.py → production_training_data_*
```

## API KEYS
```
FRED: dc195c8658c46ee1df83bcd4fd8a690b
NOAA: rxoLrCxYOlQyWvVjbBGRlMMhIRElWKZi
Scrape Creators: B1TOgQvMVSV6TDglqB8lJ2cirqi2
```

## DO NOT USE
```
❌ training_dataset_super_enriched (11 columns - BROKEN)
❌ Any _ARCHIVED_* tables
❌ Any *_backup tables
```

## FEATURE COUNT
- **Total**: 290 features per dataset
- **Used by Models**: 258-274 features (some NULL cols excluded)

## PERFORMANCE
- **MAE**: 0.297 (1M model)
- **R²**: 0.987
- **MAPE**: <1%

---

**NEXT STEPS:**
1. Update datasets with Nov 4-5 data
2. Connect all ingestion scripts
3. Verify predictions use correct datasets

**FILES UPDATED:**
- ✅ CBI_V14_COMPLETE_EXECUTION_PLAN.md
- ✅ OFFICIAL_PRODUCTION_SYSTEM.md
- ✅ QUICK_REFERENCE.txt
- ✅ Memory saved







