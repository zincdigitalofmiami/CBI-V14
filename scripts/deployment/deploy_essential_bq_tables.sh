#!/bin/bash
# ============================================================================
# Deploy Essential BigQuery Tables for Migration
# Date: November 19, 2025
# Purpose: Create core tables needed for BQ-first ingestion
# ============================================================================

set -euo pipefail

PROJECT_ID="cbi-v14"
LOCATION="us-central1"

echo "🚀 Deploying Essential BigQuery Tables"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Location: $LOCATION"
echo ""

# ============================================================================
# STEP 1: Create GCS Buckets (if not exist)
# ============================================================================
echo "📦 Step 1: Creating GCS Buckets..."

buckets=(
    "cbi-v14-training-exports"
    "cbi-v14-predictions-import"
    "cbi-v14-market-data"
    "cbi-v14-landing"
)

for bucket in "${buckets[@]}"; do
    if gsutil ls -b gs://${bucket} 2>/dev/null; then
        echo "  ✓ Bucket gs://${bucket} already exists"
    else
        echo "  Creating gs://${bucket}..."
        gsutil mb -p ${PROJECT_ID} -c STANDARD -l ${LOCATION} gs://${bucket}
    fi
done

# ============================================================================
# STEP 2: Create Core Tables
# ============================================================================
echo ""
echo "📊 Step 2: Creating Core BigQuery Tables..."

# Create DataBento ingestion table
echo "  Creating raw_intelligence.databento_futures_ohlcv_1m..."
bq query --use_legacy_sql=false --location=${LOCATION} <<EOF
CREATE TABLE IF NOT EXISTS \`${PROJECT_ID}.raw_intelligence.databento_futures_ohlcv_1m\` (
    ts_event TIMESTAMP NOT NULL,
    symbol STRING NOT NULL,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64,
    trades INT64,
    vwap FLOAT64,
    as_of TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) 
PARTITION BY DATE(ts_event) 
CLUSTER BY symbol
OPTIONS(
    description='DataBento 1-minute OHLCV bars - primary ingestion point'
);
EOF

echo "  Creating raw_intelligence.databento_futures_ohlcv_1d..."
bq query --use_legacy_sql=false --location=${LOCATION} <<EOF
CREATE TABLE IF NOT EXISTS \`${PROJECT_ID}.raw_intelligence.databento_futures_ohlcv_1d\` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64,
    open_interest INT64,
    as_of TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) 
PARTITION BY date 
CLUSTER BY symbol
OPTIONS(
    description='DataBento daily OHLCV bars'
);
EOF

# Create roll calendar
echo "  Creating market_data.roll_calendar..."
bq query --use_legacy_sql=false --location=${LOCATION} <<EOF
CREATE TABLE IF NOT EXISTS \`${PROJECT_ID}.market_data.roll_calendar\` (
    root STRING NOT NULL,
    roll_date DATE NOT NULL,
    from_contract STRING NOT NULL,
    to_contract STRING NOT NULL,
    roll_method STRING,
    roll_window_days INT64,
    as_of TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
) 
PARTITION BY roll_date 
CLUSTER BY root
OPTIONS(
    description='Futures contract roll calendar'
);
EOF

# Create master features table (basic version to start)
echo "  Creating features.master_features..."
bq query --use_legacy_sql=false --location=${LOCATION} <<EOF
CREATE TABLE IF NOT EXISTS \`${PROJECT_ID}.features.master_features\` (
    date DATE NOT NULL,
    symbol STRING NOT NULL,
    
    -- Core price features (prefixed)
    databento_open FLOAT64,
    databento_high FLOAT64,
    databento_low FLOAT64,
    databento_close FLOAT64,
    databento_volume INT64,
    
    -- Basic derived features
    returns_1d FLOAT64,
    returns_5d FLOAT64,
    returns_20d FLOAT64,
    vol_realized_5d FLOAT64,
    vol_realized_20d FLOAT64,
    
    -- Macro context (from FRED)
    fred_vix_close FLOAT64,
    fred_dgs10_yield FLOAT64,
    fred_dgs2_yield FLOAT64,
    fred_t10y2y_spread FLOAT64,
    fred_dff FLOAT64,
    
    -- FX (from various sources)
    fx_dxy_level FLOAT64,
    fx_usdbrl FLOAT64,
    fx_eurusd FLOAT64,
    
    -- Regime context
    market_regime STRING,
    training_weight INT64,
    
    -- MES-specific features (NULL for non-MES)
    mes_poc_distance FLOAT64,
    mes_pivot_confluence INT64,
    mes_fib_618_distance FLOAT64,
    
    -- MS-EGARCH features
    ms_egarch_current_regime STRING,
    prob_crash_next_5d FLOAT64,
    mes_zl_correlation FLOAT64,
    
    -- PIT tracking
    as_of TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) 
PARTITION BY date 
CLUSTER BY symbol, market_regime
OPTIONS(
    description='Master feature table - single source for all model features'
);
EOF

# Create ingestion runs tracking
echo "  Creating ops.ingestion_runs..."
bq query --use_legacy_sql=false --location=${LOCATION} <<EOF
CREATE TABLE IF NOT EXISTS \`${PROJECT_ID}.ops.ingestion_runs\` (
    run_id STRING NOT NULL,
    source STRING NOT NULL,
    status STRING NOT NULL,
    rows_processed INT64,
    rows_succeeded INT64,
    rows_failed INT64,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    error_message STRING,
    metadata JSON
) 
PARTITION BY DATE(started_at)
CLUSTER BY source, status
OPTIONS(
    description='Track all data ingestion runs'
);
EOF

# Create data quality monitoring
echo "  Creating monitoring.data_quality_checks..."
bq query --use_legacy_sql=false --location=${LOCATION} <<EOF
CREATE TABLE IF NOT EXISTS \`${PROJECT_ID}.monitoring.data_quality_checks\` (
    check_timestamp TIMESTAMP NOT NULL,
    table_name STRING NOT NULL,
    check_type STRING NOT NULL,
    check_result STRING NOT NULL,
    details JSON,
    rows_checked INT64,
    issues_found INT64
) 
PARTITION BY DATE(check_timestamp)
CLUSTER BY table_name, check_type
OPTIONS(
    description='Data quality check results'
);
EOF

# ============================================================================
# STEP 3: Create API Views
# ============================================================================
echo ""
echo "👁️ Step 3: Creating API Views..."

# ZL Public View
echo "  Creating api.vw_zl_dashboard..."
bq query --use_legacy_sql=false --location=${LOCATION} <<EOF
CREATE OR REPLACE VIEW \`${PROJECT_ID}.api.vw_zl_dashboard\` AS
SELECT 
    date,
    databento_close as current_price,
    returns_1d,
    returns_5d,
    vol_realized_20d,
    fred_vix_close as vix_level,
    fred_t10y2y_spread as yield_curve,
    market_regime,
    training_weight
FROM \`${PROJECT_ID}.features.master_features\`
WHERE symbol = 'ZL'
  AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
ORDER BY date DESC;
EOF

# MES Private View (with access control comment)
echo "  Creating api.vw_mes_private..."
bq query --use_legacy_sql=false --location=${LOCATION} <<EOF
CREATE OR REPLACE VIEW \`${PROJECT_ID}.api.vw_mes_private\` AS
-- Note: Apply Row-Level Security policy after creation
SELECT 
    date,
    databento_close as current_price,
    databento_open as open_price,
    databento_high as high_price,
    databento_low as low_price,
    databento_volume as volume,
    returns_1d,
    returns_5d,
    vol_realized_20d,
    fred_vix_close as vix_level,
    mes_poc_distance,
    mes_pivot_confluence,
    mes_fib_618_distance,
    ms_egarch_current_regime,
    prob_crash_next_5d,
    mes_zl_correlation
FROM \`${PROJECT_ID}.features.master_features\`
WHERE symbol = 'MES'
  AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
ORDER BY date DESC;
EOF

# ============================================================================
# STEP 4: Deploy MES-Specific Tables
# ============================================================================
echo ""
echo "🎯 Step 4: Deploying MES-Specific Tables..."

# Deploy MES tables from our SQL file
if [ -f "config/bigquery/mes_specific_tables.sql" ]; then
    echo "  Running mes_specific_tables.sql..."
    bq query --use_legacy_sql=false --location=${LOCATION} < config/bigquery/mes_specific_tables.sql
else
    echo "  ⚠️  config/bigquery/mes_specific_tables.sql not found"
fi

# ============================================================================
# STEP 5: Verification
# ============================================================================
echo ""
echo "✅ Step 5: Verifying Deployment..."

# Check that essential tables exist
tables_to_check=(
    "raw_intelligence.databento_futures_ohlcv_1m"
    "raw_intelligence.databento_futures_ohlcv_1d"
    "market_data.roll_calendar"
    "features.master_features"
    "ops.ingestion_runs"
    "monitoring.data_quality_checks"
)

echo "  Checking essential tables..."
for table in "${tables_to_check[@]}"; do
    if bq show --format=none ${PROJECT_ID}.${table} 2>/dev/null; then
        echo "    ✓ ${table}"
    else
        echo "    ❌ ${table} - MISSING"
    fi
done

# Check views
echo ""
echo "  Checking API views..."
for view in "api.vw_zl_dashboard" "api.vw_mes_private"; do
    if bq show --format=none ${PROJECT_ID}.${view} 2>/dev/null; then
        echo "    ✓ ${view}"
    else
        echo "    ❌ ${view} - MISSING"
    fi
done

echo ""
echo "=========================================="
echo "🎉 BigQuery Deployment Complete!"
echo ""
echo "Next Steps:"
echo "1. Configure DataBento ingestion to write to raw_intelligence.databento_futures_*"
echo "2. Load external drive data using validation scripts"
echo "3. Fix training table contamination"
echo "4. Run data quality checks"
echo ""
echo "Monitor at: https://console.cloud.google.com/bigquery?project=${PROJECT_ID}"




