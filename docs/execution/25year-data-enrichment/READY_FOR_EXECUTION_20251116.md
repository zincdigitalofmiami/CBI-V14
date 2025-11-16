# 🚀 READY FOR EXECUTION - Morning Start
**Date**: November 16, 2025  
**Status**: ✅ **PHASE 0 COMPLETE** - Ready to begin Phase 1  

---

## ✅ Phase 0 Complete - Setup & Forensic Audit

### Directories Created

**External Drive** (`/Volumes/Satechi Hub/Projects/CBI-V14/`):
- ✅ `TrainingData/raw/` - Immutable source zone
- ✅ `TrainingData/staging/` - Validated, conformed data
- ✅ `TrainingData/features/` - Engineered signals
- ✅ `TrainingData/labels/` - Forward targets
- ✅ `TrainingData/exports/` - Final training parquet files
- ✅ `TrainingData/quarantine/` - Failed validations
- ✅ `registry/` - Configuration files
- ✅ `scripts/{ingest,conform,features,labels,assemble,qa,automation}/`

**Local Repository** (`/Users/kirkmusick/Documents/GitHub/CBI-V14/`):
- ✅ `state/` - Job state tracking
- ✅ `logs/` - Execution logs
- ✅ `registry/` - Local config mirror
- ✅ `scripts/automation/` - Job runners

### Registry Files Created

✅ **feature_registry.json**
- Metadata for 20+ core features
- Reliability scores (0.70-0.99)
- Policy impact ratings (70-100)
- Categories: macro_rates, volatility, currency, commodities, big8_signals

✅ **join_spec.yaml**
- 7 declarative joins with automated tests
- Null handling policies
- Expected test assertions
- Final validation criteria

✅ **data_sources.yaml**
- 8 active data sources configured
- Scheduling (daily/weekly/monthly)
- Template for future sources
- Priority and reliability metadata

### Forensic Audit Results

**Finding**: Existing parquet files have schema incompatibility ('dbdate' type errors)

**Decision**: ✅ **REBUILD FROM SCRATCH** with clean 25-year data

**Gap Analysis**:
- ❌ Historical data (2000-2019) - NEED TO COLLECT
- ❌ FRED macro (30+ series) - NEED TO COLLECT
- ❌ NOAA weather - NEED TO COLLECT
- ❌ CFTC positioning - NEED TO COLLECT
- ❌ USDA crop data - NEED TO COLLECT
- ❌ EIA biofuels - NEED TO COLLECT

---

## 🌅 TOMORROW MORNING: START SEQUENCE

### Pre-Flight Checklist (5 minutes)

```bash
# 1. Verify external drive mounted
ls "/Volumes/Satechi Hub/Projects/CBI-V14/" || echo "❌ Mount external drive first!"

# 2. Add missing Python packages
cd /Users/kirkmusick/Documents/GitHub/CBI-V14
echo "pyyaml>=6.0" >> requirements_training.txt
echo "jinja2>=3.1.0" >> requirements_training.txt
echo "requests>=2.31.0" >> requirements_training.txt
pip install pyyaml jinja2 requests

# 3. Export regime tables from BigQuery
bq extract --location=us-central1 --destination_format=PARQUET \
  'cbi-v14:training.regime_calendar' \
  'gs://cbi-v14-temp/regime_calendar.parquet'

bq extract --location=us-central1 --destination_format=PARQUET \
  'cbi-v14:training.regime_weights' \
  'gs://cbi-v14-temp/regime_weights.parquet'

gsutil cp gs://cbi-v14-temp/regime_*.parquet \
  "/Volumes/Satechi Hub/Projects/CBI-V14/registry/"

# 4. Verify regime files
python3 <<EOF
import pandas as pd
rc = pd.read_parquet('/Volumes/Satechi Hub/Projects/CBI-V14/registry/regime_calendar.parquet')
rw = pd.read_parquet('/Volumes/Satechi Hub/Projects/CBI-V14/registry/regime_weights.parquet')
print(f"✅ Regime calendar: {len(rc)} rows, {rc['regime'].nunique()} regimes")
print(f"✅ Regime weights: {len(rw)} regimes, weight range {rw['weight'].min()}-{rw['weight'].max()}")
EOF
```

**Expected output:**
```
✅ Regime calendar: 9,131 rows, 11 regimes
✅ Regime weights: 11 regimes, weight range 50-5000
```

---

### Phase 1: Data Collection (Start Immediately After Pre-Flight)

**Timeline**: 10-12 hours

**Order of execution:**

1. **FRED Macro Data** (30 minutes - highest priority)
   ```bash
   python3 scripts/ingest/collect_fred_historical.py
   ```
   Expected: ~6,500 rows × 30 columns

2. **Yahoo Finance Historical** (45 minutes - critical for prices)
   ```bash
   python3 scripts/ingest/collect_yahoo_historical.py
   ```
   Expected: 55 symbols × ~6,200 rows each

3. **NOAA Weather** (2-3 hours - API pagination)
   ```bash
   python3 scripts/ingest/collect_noaa_historical.py
   ```
   Expected: 10 stations × 6,500 days

4. **CFTC COT** (30 minutes)
   ```bash
   python3 scripts/backfill/backfill_cftc_cot_historical.py 2006 2025
   ```
   Expected: ~1,000 weekly reports

5. **USDA NASS** (1 hour)
   ```bash
   python3 scripts/ingest/collect_usda_nass.py
   ```

6. **EIA Biofuels** (30 minutes)
   ```bash
   python3 scripts/ingest/collect_eia_biofuels.py
   ```

7. **Validation & Conformance** (1 hour)
   ```bash
   python3 scripts/conform/validate_and_conform.py
   ```
   Moves clean data: raw/ → staging/
   Quarantines bad data: raw/ → quarantine/

**QA Gate**: Must pass POST_COLLECTION and POST_STAGING checks

---

### Phase 2: Feature Engineering (4 hours)

**Single-pass build** - calculate all features ONCE:

```bash
python3 scripts/features/build_all_features.py
```

Output: `TrainingData/features/master_features_2000_2025.parquet`

Then create 10 horizon exports:
- 5 horizons (1w, 1m, 3m, 6m, 12m)
- 2 label types (price, return)
- = 10 files total

**QA Gate**: Must pass POST_FEATURES and POST_ASSEMBLY checks

---

### Phase 3-5: Organization, Upload, Pre-Flight (6 hours)

- Phase 3: Clean file organization
- Phase 4: Upload 100 rows to BigQuery
- Phase 5: Pre-flight MAPE/Sharpe parity check

**QA Gate**: Must pass PRE_TRAINING check before proceeding to Phase 6

---

### Phase 6-7: Training & Automation (14 hours)

- Phase 6: Neural nets, regime classifier, ensemble, SHAP, stress tests
- Phase 7: LaunchAgent automation setup

---

## 📋 EXECUTION CHECKLIST

### Phase 0 (Complete ✅)
- [x] Create directory structure
- [x] Run forensic audit
- [x] Create feature_registry.json
- [x] Create join_spec.yaml
- [x] Create data_sources.yaml

### Phase 1 (Ready to Start)
- [ ] Export regime tables from BigQuery
- [ ] Collect FRED data (30+ series)
- [ ] Collect Yahoo historical (55 symbols)
- [ ] Collect NOAA weather (10+ stations)
- [ ] Collect CFTC COT (2006-2025)
- [ ] Collect USDA NASS
- [ ] Collect EIA biofuels
- [ ] Validate & conform all data
- [ ] Pass POST_COLLECTION gate
- [ ] Pass POST_STAGING gate

### Phase 2 (Pending)
- [ ] Build join executor
- [ ] Execute declarative joins
- [ ] Calculate technical indicators
- [ ] Calculate cross-asset features
- [ ] Calculate volatility features
- [ ] Calculate seasonal features
- [ ] Calculate macro regime features
- [ ] Calculate weather features
- [ ] Add regime columns
- [ ] Add override flags
- [ ] Create 10 horizon exports
- [ ] Pass POST_FEATURES gate
- [ ] Pass POST_ASSEMBLY gate

### Phase 3-5 (Pending)
- [ ] Organize external drive
- [ ] Upload to BigQuery (100 rows)
- [ ] Wire MAPE/Sharpe to API
- [ ] Run pre-flight harness
- [ ] Pass PRE_TRAINING gate

### Phase 6 (Pending)
- [ ] Train DNN (TensorFlow Metal)
- [ ] Train LSTM
- [ ] Build regime classifier
- [ ] Build smooth ensemble
- [ ] Build SHAP grouping
- [ ] Build stress tester
- [ ] Run stress tests

### Phase 7 (Pending)
- [ ] Setup Keychain secrets
- [ ] Create job runner
- [ ] Generate LaunchAgents
- [ ] Install automation
- [ ] Test health check

---

## 🎯 SUCCESS CRITERIA

**By end of execution:**
- ✅ 10 parquet files (6,200+ rows, 300+ features, 2000-2025)
- ✅ 7-11 distinct regimes with weights 50-500
- ✅ MAPE/Sharpe wired to API
- ✅ Neural nets trained and ready
- ✅ Daily automation configured

---

## 📞 MORNING START COMMAND

```bash
# Navigate to workspace
cd /Users/kirkmusick/Documents/GitHub/CBI-V14

# Run pre-flight checklist
cat > run_prefl

ight.sh <<'EOF'
#!/bin/bash
set -e

echo "🚀 STARTING 25-YEAR DATA ENRICHMENT"
echo "===================================="
echo ""

# Check drive
if [ ! -d "/Volumes/Satechi Hub/Projects/CBI-V14" ]; then
  echo "❌ External drive not mounted"
  exit 1
fi
echo "✅ External drive mounted"

# Add packages
pip install pyyaml jinja2 requests

# Export regimes
bq extract --location=us-central1 --destination_format=PARQUET \
  'cbi-v14:training.regime_calendar' 'gs://cbi-v14-temp/regime_calendar.parquet'
bq extract --location=us-central1 --destination_format=PARQUET \
  'cbi-v14:training.regime_weights' 'gs://cbi-v14-temp/regime_weights.parquet'
gsutil cp gs://cbi-v14-temp/regime_*.parquet \
  "/Volumes/Satechi Hub/Projects/CBI-V14/registry/"

echo ""
echo "✅ PRE-FLIGHT COMPLETE - READY TO START PHASE 1"
echo ""
echo "Next: python3 scripts/ingest/collect_fred_historical.py"
EOF

chmod +x run_preflight.sh
./run_preflight.sh
```

---

**PHASE 0 COMPLETE**  
**ALL SETUP DONE**  
**READY FOR MORNING EXECUTION** ✅

See you in the morning! 🌅

