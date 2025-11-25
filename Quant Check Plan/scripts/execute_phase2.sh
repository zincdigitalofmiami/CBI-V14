#!/bin/bash
# =============================================================================
# PHASE 2 EXECUTION SCRIPT
# =============================================================================
# Run this script after setting API keys:
#   export DATABENTO_API_KEY="your_key"
#   export FRED_API_KEY="your_key"
#   ./execute_phase2.sh
# =============================================================================

set -e  # Exit on error

echo "=============================================="
echo "CBI-V14 PHASE 2: COMPLETE DATA PULL & FEATURES"
echo "=============================================="
echo ""

# Check API keys
if [ -z "$DATABENTO_API_KEY" ]; then
    echo "❌ ERROR: DATABENTO_API_KEY not set"
    echo "   Get your key from https://databento.com/portal/keys"
    echo "   Run: export DATABENTO_API_KEY=\"your_key\""
    exit 1
fi

if [ -z "$FRED_API_KEY" ]; then
    echo "❌ ERROR: FRED_API_KEY not set"
    echo "   Get your key from https://fred.stlouisfed.org/docs/api/api_key.html"
    echo "   Run: export FRED_API_KEY=\"your_key\""
    exit 1
fi

echo "✅ API keys set"
echo ""

# Change to project directory
cd /Users/zincdigital/CBI-V14

# =============================================================================
# STEP 1: Submit Databento Jobs (Futures + Options)
# =============================================================================
echo "=============================================="
echo "STEP 1: Submitting Databento batch jobs..."
echo "=============================================="
echo "Symbols: ZL.FUT, MES.FUT, ES.FUT, ZS.FUT, ZM.FUT, CL.FUT, HO.FUT"
echo "Options: OZL.OPT, OZS.OPT, OZM.OPT, ES.OPT, MES.OPT"
echo ""

python scripts/ingest/submit_granular_microstructure.py

echo ""
echo "✅ Databento jobs submitted"
echo "⏳ Check status at: https://databento.com/portal/batch/jobs"
echo ""

# =============================================================================
# STEP 2: Pull FRED Data (2010-2025)
# =============================================================================
echo "=============================================="
echo "STEP 2: Pulling FRED economic data..."
echo "=============================================="
echo "Series: VIXCLS, DFF, DGS10, CPIAUCSL, BAMLH0A0HYM2, TEDRATE, BDILCY, etc."
echo ""

python "Quant Check Plan/scripts/collect_fred_data.py"

echo ""
echo "✅ FRED data pulled and loaded to BigQuery"
echo ""

# =============================================================================
# STEP 3: Pull Weather Data (BigQuery Public Datasets)
# =============================================================================
echo "=============================================="
echo "STEP 3: Building weather features from BigQuery Public Data..."
echo "=============================================="

# Run the weather SQL script
bq query --use_legacy_sql=false < bigquery-sql/build_weather_history.sql

echo ""
echo "✅ Weather features built"
echo ""

# =============================================================================
# STEP 4: Verify Data
# =============================================================================
echo "=============================================="
echo "STEP 4: Verifying data in BigQuery..."
echo "=============================================="

echo "Checking FRED data:"
bq query --use_legacy_sql=false "
SELECT 
  series_id, 
  COUNT(*) as rows, 
  MIN(date) as min_date, 
  MAX(date) as max_date
FROM \`cbi-v14.raw_intelligence.fred_economic\`
GROUP BY series_id
ORDER BY series_id
LIMIT 10
"

echo ""
echo "Checking Databento data:"
bq query --use_legacy_sql=false "
SELECT 
  symbol, 
  COUNT(*) as rows, 
  MIN(date) as min_date, 
  MAX(date) as max_date
FROM \`cbi-v14.market_data.databento_futures_ohlcv_1d\`
GROUP BY symbol
ORDER BY symbol
"

echo ""
echo "=============================================="
echo "PHASE 2 STEP 1-4 COMPLETE"
echo "=============================================="
echo ""
echo "NEXT STEPS:"
echo "1. Wait for Databento batch jobs to complete"
echo "2. Download completed jobs from portal"
echo "3. Run: python 'Quant Check Plan/scripts/load_databento_csv.py' /path/to/csvs/"
echo "4. Run feature expansion and retraining"
echo ""

